#!/usr/bin/env python3
"""Move a classification record between taxonomy versions.

Answers the practical question a consumer faces once the taxonomy is republished:
a record arrives stamped with a version that is not the one you run. This resolves
it using the lineage recorded in taxonomy.json, and is explicit about what the
resolution cost.

    python3 migrate.py example-case.json --to 7.0
    python3 migrate.py --explain D009

Every result carries a fidelity: exact (safe), widening (safe, coarser),
narrowing (ambiguous, needs a human or the source case). Unknown codes are
widened, never dropped and never guessed.
"""
import argparse
import json
import sys

DIMENSIONS = ["method", "modus", "initiator", "labels_tags", "payment_instrument"]


def load(path="taxonomy.json"):
    return json.load(open(path, encoding="utf-8"))


def index(tax):
    """code -> (dimension, entry, state)."""
    idx = {}
    for dim in DIMENSIONS:
        block = tax["dimensions"][dim]
        if dim == "modus":
            for group in block["high_level_classifications"]:
                for m in group["modi"]:
                    idx[m["code"]] = (dim, m, "active")
            ca = block["catch_all"]
            idx[ca["code"]] = (dim, ca, "active")
        else:
            for v in block["values"]:
                idx[v["code"]] = (dim, v, "active")
        for r in block.get("retired", []):
            idx[r["code"]] = (dim, r, "retired")
    return idx


def group_of(tax, code):
    for group in tax["dimensions"]["modus"]["high_level_classifications"]:
        for m in group["modi"]:
            if m["code"] == code:
                return group
    return None


def resolve(tax, idx, code):
    """Resolve one code against the version held in taxonomy.json."""
    if code not in idx:
        return {"code": code, "status": "unknown", "fidelity": "unresolved",
                "note": "Not present in this version. Widen it against the version that issued the record; "
                        "do not drop it and do not substitute a sibling code."}

    dim, entry, state = idx[code]

    if state == "active":
        out = {"code": code, "name": entry["name"], "dimension": dim,
               "status": "active", "fidelity": "exact"}
        if entry.get("last_change_type") == "recited":
            out["note"] = ("Definition was re-cited in %s from a different source. Meaning unchanged, so this "
                           "is still an exact match and needs no re-classification." % entry["last_modified_in"])
        if entry.get("derived_from"):
            out["predecessor"] = entry["derived_from"]["code"]
            out["note_forward"] = ("A consumer that predates %s will not know this code. It widens to %s."
                                   % (entry["introduced_in"], entry["derived_from"]["code"]))
        if entry.get("moved_from"):
            out["moved_from"] = entry["moved_from"]
        return out

    successors = entry.get("superseded_by", [])
    if not successors:
        return {"code": code, "name": entry["name"], "dimension": dim, "status": "retired",
                "fidelity": "unresolved",
                "note": "Retired in %s with no successor. Records already classified with it stay valid under "
                        "their own version." % entry.get("retired_in")}

    return {"code": code, "name": entry["name"], "dimension": dim, "status": "retired",
            "retired_in": entry.get("retired_in"), "reason": entry.get("reason"),
            "candidates": [{"code": c, "name": idx[c][1]["name"]} for c in successors if c in idx],
            "fidelity": "narrowing",
            "note": "This code was %s in %s. The record cannot say which successor applies, because the "
                    "distinction was added after it was classified. Keep it at this level, or re-classify from "
                    "the source case. For counting, the successors sum back to this code."
                    % (entry.get("reason"), entry.get("retired_in"))}


def migrate(tax, record, target):
    idx = index(tax)
    source = record.get("taxonomy_version", "unstated")
    report = {"from_version": source, "to_version": target, "fields": {}, "overall": "exact"}
    rank = {"exact": 0, "widening": 1, "narrowing": 2, "unresolved": 3}

    fields = [("method_code", "method"), ("modus_code", "modus"),
              ("initiator_code", "initiator"), ("payment_instrument_code", "payment_instrument")]
    for code_field, _ in fields:
        if code_field in record:
            r = resolve(tax, idx, record[code_field])
            report["fields"][code_field] = r
            if rank[r["fidelity"]] > rank[report["overall"]]:
                report["overall"] = r["fidelity"]
    if "labels_tags_codes" in record:
        rs = [resolve(tax, idx, c) for c in record["labels_tags_codes"]]
        report["fields"]["labels_tags_codes"] = rs
        for r in rs:
            if rank[r["fidelity"]] > rank[report["overall"]]:
                report["overall"] = r["fidelity"]

    if source != target and source != "unstated":
        report["note"] = ("The stored record keeps taxonomy_version %s. Interpretation under %s is a read-time "
                          "operation; rewriting the stamp would destroy the only evidence of what was actually "
                          "assessed at the time." % (source, target))
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record", nargs="?", help="path to a classification record")
    ap.add_argument("--to", help="target taxonomy version")
    ap.add_argument("--explain", metavar="CODE", help="explain how one code resolves")
    ap.add_argument("--taxonomy", default="taxonomy.json")
    args = ap.parse_args()

    tax = load(args.taxonomy)

    if args.explain:
        print(json.dumps(resolve(tax, index(tax), args.explain), indent=2, ensure_ascii=False))
        return 0

    if not args.record:
        ap.print_help()
        return 2

    record = json.load(open(args.record, encoding="utf-8"))
    report = migrate(tax, record, args.to or tax["version"])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["overall"] in ("exact", "widening") else 1


if __name__ == "__main__":
    sys.exit(main())
