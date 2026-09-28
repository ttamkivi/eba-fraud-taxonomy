#!/usr/bin/env python3
"""Read a classification record under a different taxonomy version.

A record arrives stamped with a version that is not the one you run. This resolves
each code against the target version using lineage.json, and says what the
resolution cost.

    python3 migrate.py example-case.json --to 5.0
    python3 migrate.py --explain T0095

Every result carries a fidelity: exact (safe), widening (safe, coarser),
narrowing (ambiguous, needs a human or the source case), unresolved. Unknown codes
are widened, never dropped and never guessed. The stored record is never rewritten.
"""
import argparse
import json
import os
import sys

RANK = {"exact": 0, "widening": 1, "narrowing": 2, "unresolved": 3}
FIELDS = {"method_code": "method", "modus_code": "modus", "initiator_code": "initiator",
          "payment_instrument_code": "payment_instrument"}


def load_lineage():
    return json.load(open("lineage.json", encoding="utf-8"))


def vkey(v):
    return [int(x) for x in v.split(".")]


def successors(lineage, code, target):
    """Follow superseded_by through every split up to the target version."""
    out, stack = [], [code]
    while stack:
        c = stack.pop()
        rec = lineage["codes"][c]
        if target in rec["versions"]:
            out.append(c)
            continue
        for ev in rec["events"]:
            if ev.get("superseded_by") and vkey(ev["version"]) <= vkey(target):
                stack += ev["superseded_by"]
    return sorted(set(out))


def group_in(lineage, code, version):
    """The high-level classification a modus sat in, in the version it was read from."""
    tax = json.load(open(os.path.join("versions", version, "taxonomy.json"), encoding="utf-8"))
    for g in tax["dimensions"]["modus"]["high_level_classifications"]:
        if any(m["code"] == code for m in g["modi"]):
            return g["code"], g["name"]
    return None, None


def resolve(lineage, code, source, target, field_dim=None):
    rec = lineage["codes"].get(code)
    if rec is None:
        return {"code": code, "fidelity": "unresolved",
                "note": "Not a code in any transcribed version. Keep it as received; do not drop it and do not "
                        "substitute a sibling."}
    here = rec["versions"].get(target)
    if here:
        out = {"code": code, "name": here["name"], "dimension": here["dimension"], "fidelity": "exact"}
        if field_dim and here["dimension"] != field_dim:
            out["note"] = (f"Same concept, same code. It was classified as a {field_dim} under {source} and is a "
                           f"{here['dimension']} under {target}. Keep it in the field it was classified in; count it "
                           f"by code.")
        was = rec["versions"].get(source)
        if was and was["name"] != here["name"]:
            out["renamed"] = {"from": was["name"], "to": here["name"]}
        return out
    if vkey(target) > vkey(source):
        succ = successors(lineage, code, target)
        name = rec["versions"].get(source, {}).get("name")
        if succ:
            return {"code": code, "name": name, "fidelity": "narrowing" if len(succ) > 1 else "exact",
                    "candidates": [{"code": c, **lineage["codes"][c]["versions"][target]} for c in succ],
                    "note": f"Split before {target}. The record cannot say which successor applies, because the "
                            f"distinction was added after it was classified. Keep it at this level or re-classify "
                            f"from the source case; for counting, the successors sum back to it."}
        return {"code": code, "name": name, "fidelity": "unresolved", "retired_in": rec.get("retired_in"),
                "note": f"Retired in {rec.get('retired_in')} with no successor. The record stays valid under {source}."}
    # the record is newer than the reader: widen
    for d in rec.get("derived_from", []):
        if target in lineage["codes"][d["code"]]["versions"]:
            return {"code": code, "fidelity": "widening", "widened_to": d["code"],
                    "name": lineage["codes"][d["code"]]["versions"][target]["name"],
                    "note": f"{code} does not exist in {target}. It was split from {d['code']}, which does."}
    if rec["kind"] == "entry" and rec["versions"].get(source, {}).get("dimension") == "modus":
        gc, gn = group_in(lineage, code, source)
        if gc and target in lineage["codes"][gc]["versions"]:
            return {"code": code, "fidelity": "widening", "widened_to": gc, "name": gn,
                    "note": f"{code} does not exist in {target}. Widened to its high-level classification."}
    tax = json.load(open(os.path.join("versions", target, "taxonomy.json"), encoding="utf-8"))
    dim = rec["versions"].get(source, {}).get("dimension")
    if dim and dim not in tax["dimensions"]:
        return {"code": code, "fidelity": "unresolved",
                "note": f"The {dim} dimension does not exist in {target}. Keep the value as received; a {target} "
                        f"reader has nowhere to put it."}
    return {"code": code, "fidelity": "unresolved",
            "note": f"{code} does not exist in {target} and has no predecessor there. Keep it as received."}


def migrate(lineage, record, target):
    source = record.get("taxonomy_version")
    if not source:
        sys.exit("record has no taxonomy_version: it cannot be interpreted safely")
    report = {"from_version": source, "to_version": target, "fields": {}, "overall": "exact"}
    for field, dim in FIELDS.items():
        if field in record:
            r = resolve(lineage, record[field], source, target, dim)
            report["fields"][field] = r
            report["overall"] = max(report["overall"], r["fidelity"], key=RANK.get)
    if "labels_tags_codes" in record:
        rs = [resolve(lineage, c, source, target, "labels_tags") for c in record["labels_tags_codes"]]
        report["fields"]["labels_tags_codes"] = rs
        for r in rs:
            report["overall"] = max(report["overall"], r["fidelity"], key=RANK.get)
    if source != target:
        report["note"] = (f"The stored record keeps taxonomy_version {source}. Reading it under {target} is a "
                          "read-time operation; rewriting the stamp would destroy the evidence of what was assessed.")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record", nargs="?")
    ap.add_argument("--to", help="target taxonomy version (default: latest)")
    ap.add_argument("--explain", metavar="CODE", help="print one code's full history")
    args = ap.parse_args()
    lineage = load_lineage()
    if args.explain:
        rec = lineage["codes"].get(args.explain)
        print(json.dumps(rec if rec else {"code": args.explain, "status": "unknown"}, indent=2, ensure_ascii=False))
        return 0
    if not args.record:
        ap.print_help()
        return 2
    record = json.load(open(args.record, encoding="utf-8"))
    report = migrate(lineage, record, args.to or lineage["versions"][-1])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall"] in ("exact", "widening") else 1


if __name__ == "__main__":
    sys.exit(main())
