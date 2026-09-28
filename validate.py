#!/usr/bin/env python3
"""Integrity checks across every transcribed version. Exit code 1 on any failure.

    python3 validate.py
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, "build")
from parse import norm  # noqa: E402

problems, warnings = [], []
fail, warn = problems.append, warnings.append

VERSIONS = sorted((os.path.basename(os.path.dirname(p)) for p in glob.glob("versions/*/taxonomy.json")),
                  key=lambda v: [int(x) for x in v.split(".")])
CODE = re.compile(r"^T\d{4}$")
lineage = json.load(open("lineage.json", encoding="utf-8"))
registry = json.load(open("build/codes.json", encoding="utf-8"))


def entries(tax):
    """(dimension, entry) for every active entry, groups included as dimension 'modus_group'."""
    d = tax["dimensions"]
    out = []
    for dim, block in d.items():
        if dim == "modus":
            for g in block["high_level_classifications"]:
                out.append(("modus_group", g))
                out += [("modus", m) for m in g["modi"]]
            out.append(("modus", block["catch_all"]))
        else:
            out += [(dim, v) for v in block["values"]]
    return out


def reassembles(e):
    """The definition plus its sources must be exactly the PDF cell, word for word."""
    text = e.get("pdf_text", "")
    for s in e.get("sources", []):
        for part in (s.get("attribution"), s.get("url")):
            if part and part not in text:
                return f"source part not verbatim in pdf_text: {part[:50]}"
    rest = norm(text)
    for s in e.get("sources", []):
        for part in (s.get("url"), s.get("attribution")):
            if part:
                rest = rest.replace(norm(part), " ", 1)
    rest_words = rest.split()
    want = norm(e.get("definition", "")).split()
    # every definition word appears in order in the cell, and nothing but source words is left over
    it = iter(rest_words)
    if not all(w in it for w in want):
        return "definition is not a word-for-word extract of pdf_text"
    left = len(rest_words) - len(want)
    markers = len(re.findall(r"\b(definition based on the following source|sources?)\b", rest))
    if left > markers * 6 + 2:
        return f"pdf_text has {left} words that are neither definition nor source"
    return None


all_codes_seen = {}
for v in VERSIONS:
    tax = json.load(open(f"versions/{v}/taxonomy.json", encoding="utf-8"))
    schema = json.load(open(f"versions/{v}/schema.json", encoding="utf-8"))
    if tax["version"] != v:
        fail(f"{v}: file declares version {tax['version']}")
    ents = entries(tax)
    codes = [e["code"] for _, e in ents]
    for c in codes:
        if not CODE.match(c):
            fail(f"{v}: malformed code {c}")
    dup = {c for c in codes if codes.count(c) > 1}
    if dup:
        fail(f"{v}: duplicate codes {sorted(dup)}")
    for dim in {d for d, _ in ents}:
        ns = [norm(e["name"]) for d, e in ents if d == dim]
        dn = {n for n in ns if ns.count(n) > 1}
        if dn:
            fail(f"{v}: duplicate names in {dim}: {sorted(dn)}")
    labels = {e["code"] for d, e in ents if d == "labels_tags"}
    vocab = set(tax["change_types"])
    for g in tax["dimensions"]["modus"]["high_level_classifications"]:
        for m in g["modi"]:
            if m["group_code"] != g["code"]:
                fail(f"{v}: {m['code']} group_code {m['group_code']} != {g['code']}")
            if len(m["possible_labels_tags_codes"]) != len(m["possible_labels_tags"]):
                fail(f"{v}: {m['code']} possible labels do not all resolve")
            for c in m["possible_labels_tags_codes"]:
                if c not in labels:
                    fail(f"{v}: {m['code']} references {c}, not a label in this version")
            if m.get("possible_labels_tags_unmatched"):
                warn(f"{v}: {m['name']}: the PDF lists a possible label that is not a label in this version: "
                     f"'{m['possible_labels_tags_unmatched']}'")
    for d, e in ents:
        if d != "modus_group":
            why = reassembles(e)
            if why:
                fail(f"{v} {e['code']} {e['name']}: {why}")
        if e.get("status") != "active":
            fail(f"{v} {e['code']}: status must be 'active'")
        intro = e.get("introduced_in")
        if intro != "<=3.1" and intro not in VERSIONS:
            fail(f"{v} {e['code']}: introduced_in '{intro}'")
        if e.get("last_change_type") and e["last_change_type"] not in vocab:
            fail(f"{v} {e['code']}: last_change_type '{e['last_change_type']}' not in change_types")
        for df in e.get("derived_from", []):
            if df["code"] not in lineage["codes"]:
                fail(f"{v} {e['code']}: derived_from unknown code {df['code']}")
        # lineage agrees with this file
        rec = lineage["codes"].get(e["code"])
        if not rec or v not in rec["versions"]:
            fail(f"{v} {e['code']}: missing from lineage.json")
        elif norm(rec["versions"][v]["name"]) != norm(e["name"]):
            fail(f"{v} {e['code']}: name differs from lineage.json")
        all_codes_seen[e["code"]] = (v, d, e["name"])
    active = set(codes)
    for dim, block in tax["dimensions"].items():
        for r in block.get("retired", []) + block.get("retired_high_level_classifications", []):
            if r["code"] in active:
                fail(f"{v}: {r['code']} is both active and retired")
            if r.get("reason") not in vocab:
                fail(f"{v}: retired {r['code']} reason '{r.get('reason')}' not in change_types")
            for s in r.get("superseded_by", []):
                if s not in active:
                    fail(f"{v}: retired {r['code']} superseded_by {s}, which is not active in {v}")
    for b in tax["changes"]:
        for r in b["declared"]:
            if r["change_type"] not in vocab:
                fail(f"{v}: changes {b['version']} uses unknown change_type {r['change_type']}")
            if None in (r.get("from_codes") or []) + (r.get("to_codes") or []):
                fail(f"{v}: changes {b['version']} has an unresolved code in a {r['change_type']} record")

    # schema in sync
    d = tax["dimensions"]
    modi = [m for g in d["modus"]["high_level_classifications"] for m in g["modi"]]
    expect = {"method_code": [x["code"] for x in d["method"]["values"]],
              "modus_code": [x["code"] for x in modi] + [d["modus"]["catch_all"]["code"]],
              "initiator_code": [x["code"] for x in d["initiator"]["values"]]}
    if "payment_instrument" in d:
        expect["payment_instrument_code"] = [x["code"] for x in d["payment_instrument"]["values"]]
    for prop, want in expect.items():
        if schema["properties"].get(prop, {}).get("enum") != want:
            fail(f"{v}: schema.json enum '{prop}' out of sync (run build_schema.py)")
    if schema["properties"]["taxonomy_version"]["const"] != v:
        fail(f"{v}: schema taxonomy_version const is wrong")
    print(f"{v}: methods={len(d['method']['values'])} modi={len(modi)}+1 "
          f"groups={len(d['modus']['high_level_classifications'])} initiators={len(d['initiator']['values'])} "
          f"labels={len(d['labels_tags']['values'])} "
          f"instruments={len(d['payment_instrument']['values']) if 'payment_instrument' in d else '-'}")

# a code means one concept: never two dimensions in one version, and every registry code is used
for c, rec in lineage["codes"].items():
    for v, where in rec["versions"].items():
        if not os.path.exists(f"versions/{v}/taxonomy.json"):
            fail(f"lineage: {c} claims version {v}, which is not transcribed")
unused = set(registry["codes"]) - set(lineage["codes"])
if unused:
    fail(f"build/codes.json has codes no version uses: {sorted(unused)}")

# root copies
latest = VERSIONS[-1]
for f in ("taxonomy.json", "schema.json"):
    if open(f, encoding="utf-8").read() != open(f"versions/{latest}/{f}", encoding="utf-8").read():
        fail(f"{f} is not a copy of versions/{latest}/{f}")

# example record validates against its own version's schema
try:
    import jsonschema
    ex = json.load(open("example-case.json", encoding="utf-8"))
    jsonschema.validate(ex, json.load(open(f"versions/{ex['taxonomy_version']}/schema.json", encoding="utf-8")))
except ImportError:
    warn("jsonschema not installed; example-case.json not validated")
except Exception as exc:  # noqa: BLE001
    fail(f"example-case.json: {exc}")

# derivations resolve against their declared version
for path in sorted(glob.glob("derivations/*.json")):
    der = json.load(open(path, encoding="utf-8"))
    v = der["derivation_of"]["version"]
    active = {e["code"] for _, e in entries(json.load(open(f"versions/{v}/taxonomy.json", encoding="utf-8")))}
    for m in der["mappings"]:
        for c in m["maps_to"]:
            if c not in active:
                fail(f"{path}: {m['local_code']} maps to {c}, not a code in {v}")
        if m["relation"] == "exact" and len(m["maps_to"]) != 1:
            fail(f"{path}: {m['local_code']} is 'exact' but maps to {len(m['maps_to'])} codes")

# house rule: no em dashes in anything this repository authors (the EBA's own text is exempt)
authored = (glob.glob("*.md") + glob.glob("*.py") + glob.glob("build/*.py") + glob.glob("build/*.json")
            + glob.glob("build/transitions/*.json") + glob.glob("derivations/*") + ["example-case.json"])
for f in authored:
    n = open(f, encoding="utf-8").read().count(chr(0x2014))
    if n:
        fail(f"{f} contains {n} em dash(es)")

for w in warnings:
    print("WARN:", w)
for p in problems:
    print("FAIL:", p)
if problems:
    sys.exit(1)
print(f"OK: {len(VERSIONS)} versions, {len(lineage['codes'])} codes, all integrity checks passed")
