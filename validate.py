#!/usr/bin/env python3
"""Integrity checks for taxonomy.json and schema.json. Exit code 1 on any failure."""
import json
import os
import re
import sys

problems = []
warnings = []


def fail(msg):
    problems.append(msg)


def warn(msg):
    warnings.append(msg)


import glob as _glob

VERSION = sys.argv[1] if len(sys.argv) > 1 else None
if VERSION is None:
    # no argument: check every transcribed version, then root consistency
    versions = sorted(os.path.basename(os.path.dirname(p))
                      for p in _glob.glob("versions/*/taxonomy.json"))
    import subprocess
    rc = 0
    for v in versions:
        print(f"=== {v} ===")
        rc |= subprocess.call([sys.executable, __file__, v])
    latest = max(versions, key=lambda v: [int(x) for x in v.split(".")])
    root = open("taxonomy.json", encoding="utf-8").read()
    if root != open(f"versions/{latest}/taxonomy.json", encoding="utf-8").read():
        print(f"FAIL: taxonomy.json differs from versions/{latest}/taxonomy.json "
              f"(root must be a copy of the latest published version)")
        rc |= 1
    else:
        print(f"OK: taxonomy.json matches versions/{latest}/taxonomy.json")
    sys.exit(rc)

tax = json.load(open(f"versions/{VERSION}/taxonomy.json", encoding="utf-8"))
schema = json.load(open(f"versions/{VERSION}/schema.json", encoding="utf-8"))
dims = tax["dimensions"]

# ---- collect entries -------------------------------------------------------
methods = dims["method"]["values"]
initiators = dims["initiator"]["values"]
labels = dims["labels_tags"]["values"]
instruments = dims["payment_instrument"]["values"]
groups = dims["modus"]["high_level_classifications"]
modi = [m for g in groups for m in g["modi"]]
catch_all = dims["modus"]["catch_all"]
retired = dims["modus"].get("retired", [])

label_names = {v["name"] for v in labels}
all_entries = methods + initiators + labels + instruments + modi + [catch_all] + retired

# ---- codes: present, unique, well-formed -----------------------------------
codes = [e.get("code") for e in all_entries]
for e in all_entries:
    if not e.get("code"):
        fail(f"missing code: {e.get('name')}")
dupes = {c for c in codes if c and codes.count(c) > 1}
if dupes:
    fail(f"duplicate codes: {sorted(dupes)}")
pattern = re.compile(r"^(M\d{2}|I\d{2}|D\d{3}|L\d{3}|P\d{2}|D-RETIRED-\d{2})$")
for c in codes:
    if c and not pattern.match(c):
        fail(f"malformed code: {c}")
for g in groups:
    if not re.match(r"^G\d{2}$", g.get("code", "")):
        fail(f"malformed group code on: {g['name']}")

# ---- names unique within each dimension ------------------------------------
for dim_name, values in [("method", methods), ("initiator", initiators),
                         ("labels_tags", labels), ("payment_instrument", instruments),
                         ("modus", modi)]:
    names = [v["name"] for v in values]
    d = {n for n in names if names.count(n) > 1}
    if d:
        fail(f"duplicate names in {dim_name}: {sorted(d)}")

# ---- every possible_labels_tags reference resolves to a real label ---------
for m in modi:
    for ref in m.get("possible_labels_tags", []):
        if ref not in label_names:
            fail(f"modus '{m['name']}' references unknown label/tag '{ref}'")

# ---- modus group_code matches enclosing group ------------------------------
for g in groups:
    for m in g["modi"]:
        if m.get("group_code") != g["code"]:
            fail(f"modus '{m['name']}' group_code {m.get('group_code')} != {g['code']}")

# ---- lineage: derived_from / superseded_by are consistent -------------------
retired_by_code = {r["code"]: r for r in retired}
modus_by_code = {m["code"]: m for m in modi}
for m in modi:
    df = m.get("derived_from")
    if df:
        if df["code"] not in retired_by_code:
            fail(f"'{m['name']}' derived_from unknown retired code {df['code']}")
        elif m["code"] not in retired_by_code[df["code"]].get("superseded_by", []):
            fail(f"retired {df['code']} does not list {m['code']} in superseded_by")
for r in retired:
    for sc in r.get("superseded_by", []):
        if sc not in modus_by_code:
            fail(f"retired {r['code']} superseded_by unknown modus code {sc}")

# ---- schema enums match data exactly ---------------------------------------
def names_of(vals):
    return [v["name"] for v in vals]


def codes_of(vals):
    return [v["code"] for v in vals]


expect = {
    "method": names_of(methods),
    "method_code": codes_of(methods),
    "initiator": names_of(initiators),
    "initiator_code": codes_of(initiators),
    "modus": names_of(modi) + [catch_all["name"]],
    "modus_code": codes_of(modi) + [catch_all["code"]],
    "payment_instrument": names_of(instruments),
    "payment_instrument_code": codes_of(instruments),
}
for prop, want in expect.items():
    got = schema["properties"].get(prop, {}).get("enum")
    if got != want:
        fail(f"schema.json enum for '{prop}' is out of sync with taxonomy.json (run build_schema.py)")

if schema["properties"]["taxonomy_version"]["const"] != tax["version"]:
    fail("schema taxonomy_version const != taxonomy.json version")

# ---- no em dashes anywhere (house rule) -------------------------------------
for fname in (_glob.glob("*.md") + _glob.glob("*.py") + _glob.glob("*.json")
              + _glob.glob("versions/*/*.json") + _glob.glob("derivations/*") + ["LICENSE"]):
    try:
        txt = open(fname, encoding="utf-8").read()
    except FileNotFoundError:
        warn(f"{fname} not found")
        continue
    em_dash = chr(0x2014)
    if em_dash in txt:
        n = txt.count(em_dash)
        fail(f"{fname} contains {n} em dash(es)")

# ---- lifecycle metadata on every entry -------------------------------------
VALID_CHANGE_TYPES = set(tax["change_types"])
for e in methods + initiators + labels + instruments + modi:
    if e.get("status") != "active":
        fail(f"{e.get('code')} {e.get('name')}: status must be 'active' (retired entries live in the retired array)")
    intro = e.get("introduced_in")
    if not intro:
        fail(f"{e.get('code')} {e.get('name')}: missing introduced_in")
    elif intro != "<=6.0" and intro not in {v["version"] for v in tax["version_history"]}:
        fail(f"{e.get('code')}: introduced_in '{intro}' is not a known version or '<=6.0'")
    lct = e.get("last_change_type")
    if lct and lct not in VALID_CHANGE_TYPES:
        fail(f"{e.get('code')}: last_change_type '{lct}' not in change_types vocabulary")
    if lct and not e.get("last_modified_in"):
        fail(f"{e.get('code')}: has last_change_type but no last_modified_in")

for dim_name in ["method", "initiator", "labels_tags", "payment_instrument", "modus"]:
    if "retired" not in dims[dim_name]:
        fail(f"dimension '{dim_name}' has no retired array (use [] if nothing is retired)")
for r in retired:
    for required in ["code", "name", "status", "retired_in", "reason", "dimension"]:
        if required not in r:
            fail(f"retired entry {r.get('code')}: missing {required}")
    if r.get("status") != "retired":
        fail(f"retired entry {r.get('code')}: status must be 'retired'")
    if r.get("reason") not in VALID_CHANGE_TYPES:
        fail(f"retired entry {r.get('code')}: reason '{r.get('reason')}' not in change_types vocabulary")

# ---- changes array is internally consistent --------------------------------
known_codes = {e["code"] for e in methods + initiators + labels + instruments + modi}
known_codes.add(catch_all["code"])
known_codes |= {r["code"] for r in retired}
known_codes |= {g["code"] for g in groups}
seen_versions = set()
for block in tax.get("changes", []):
    seen_versions.add(block["version"])
    if block["version"] not in {v["version"] for v in tax["version_history"]}:
        fail(f"changes block for unknown version {block['version']}")
    for rec in block["records"]:
        if rec["change_type"] not in VALID_CHANGE_TYPES:
            fail(f"changes {block['version']}: unknown change_type '{rec['change_type']}'")
        for c in rec.get("from", []) + rec.get("to", []):
            if c not in known_codes:
                fail(f"changes {block['version']}: references unknown code '{c}'")
        for c in rec.get("successor_notes", {}):
            if c not in rec.get("to", []):
                fail(f"changes {block['version']}: successor_note for {c} which is not in 'to'")
if tax["version"] not in seen_versions:
    warn(f"no changes block for the current version {tax['version']}")

# ---- derivations resolve to real codes -------------------------------------
import glob
import os

VALID_RELATIONS = {"exact", "broader", "narrower", "related"}
for path in sorted(glob.glob("derivations/*.json")):
    try:
        der = json.load(open(path, encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"{path}: not valid JSON ({exc})")
        continue
    src = der.get("derivation_of", {})
    if src.get("version") != tax["version"]:
        # A derivation is valid against one version only; it is not this version's problem.
        continue
    for mapping in der.get("mappings", []):
        if mapping.get("relation") not in VALID_RELATIONS:
            fail(f"{path}: mapping '{mapping.get('local_code')}' has invalid relation '{mapping.get('relation')}'")
        targets = mapping.get("maps_to", [])
        if not targets:
            fail(f"{path}: mapping '{mapping.get('local_code')}' maps to nothing")
        for c in targets:
            if c not in known_codes:
                fail(f"{path}: mapping '{mapping.get('local_code')}' references unknown code '{c}'")
        if mapping.get("relation") == "exact" and len(targets) != 1:
            fail(f"{path}: mapping '{mapping.get('local_code')}' is 'exact' but maps to {len(targets)} codes")

# ---- example record validates ---------------------------------------------
try:
    import jsonschema

    example = json.load(open("example-case.json"))
    if example.get("taxonomy_version") == VERSION:
        jsonschema.validate(example, schema)
    else:
        warn(f"example-case.json is pinned to {example.get('taxonomy_version')}, not {VERSION}; skipped")
except ImportError:
    warn("jsonschema not installed; skipped example validation")
except FileNotFoundError:
    warn("example-case.json not found; skipped example validation")
except Exception as e:  # noqa: BLE001
    fail(f"example-case.json failed schema validation: {e}")

# ---- report ---------------------------------------------------------------
print(f"methods={len(methods)} modi={len(modi)}(+1 catch-all) groups={len(groups)} "
      f"initiators={len(initiators)} labels={len(labels)} instruments={len(instruments)} "
      f"retired={len(retired)}")
for w in warnings:
    print("WARN:", w)
for p in problems:
    print("FAIL:", p)
if problems:
    sys.exit(1)
print("OK: all integrity checks passed")
