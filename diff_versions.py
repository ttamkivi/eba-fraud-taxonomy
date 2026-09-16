#!/usr/bin/env python3
"""Compare two transcribed versions and report what actually changed.

    python3 diff_versions.py 6.0 7.0
    python3 diff_versions.py 6.0 7.0 --undocumented

Entries are matched on code, not name, so a rename shows up as a rename rather
than as a deletion plus an addition. Changes are classified with the same
vocabulary the taxonomy files use (see change_types in taxonomy.json), and the
distinction that matters most is redefined against recited: only the first can
require re-classifying stored records.

--undocumented lists changes this repository found that the official annex for
the target version does not mention. That set is not a criticism of the drafting;
definitions are quotations, and quoted sources reword their own pages between
years. It is the reason a machine-readable diff is worth having.
"""
import argparse
import json
import os
import sys

DIMS = ["method", "modus", "initiator", "labels_tags", "payment_instrument"]
FIELDS = ["name", "definition", "source", "source_url", "example", "examples", "possible_labels_tags"]


def load(version):
    path = os.path.join("versions", version, "taxonomy.json")
    if not os.path.exists(path):
        sys.exit(f"no transcription for version {version} (expected {path})")
    return json.load(open(path, encoding="utf-8"))


def entries(tax):
    """code -> (dimension, entry), active entries only."""
    out = {}
    for dim in DIMS:
        block = tax["dimensions"][dim]
        if dim == "modus":
            vals = [m for g in block["high_level_classifications"] for m in g["modi"]]
            vals.append(block["catch_all"])
        else:
            vals = block["values"]
        for v in vals:
            out[v["code"]] = (dim, v)
    return out


def classify(old, new):
    """What kind of change is this?"""
    if old.get("name") != new.get("name"):
        return "renamed"
    same_def = old.get("definition") == new.get("definition")
    same_src = (old.get("source") == new.get("source")
                and old.get("source_url") == new.get("source_url"))
    if same_def and same_src:
        return "metadata"
    # An explicit declaration in the data wins over inference.
    if new.get("last_change_type") in {"recited", "redefined"}:
        return new["last_change_type"]
    if same_def and not same_src:
        return "recited"
    # The definition text differs and nothing declares why. A machine cannot tell a
    # cosmetic rewording from a change of meaning, so say only what is known.
    return "text-changed"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("from_version")
    ap.add_argument("to_version")
    ap.add_argument("--undocumented", action="store_true",
                    help="only changes the target version's own annex does not mention")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    a, b = load(args.from_version), load(args.to_version)
    ea, eb = entries(a), entries(b)

    # Codes the target version's annex accounts for.
    documented = set()
    for block in b.get("changes", []):
        if block["version"] != args.to_version:
            continue
        for rec in block["records"]:
            documented.update(rec.get("from", []))
            documented.update(rec.get("to", []))

    added, removed, changed = [], [], []
    for code in sorted(set(ea) | set(eb)):
        if code not in ea:
            dim, e = eb[code]
            added.append({"change_type": "added", "dimension": dim, "code": code, "name": e["name"]})
        elif code not in eb:
            dim, e = ea[code]
            rec = {"change_type": "retired", "dimension": dim, "code": code, "name": e["name"]}
            for r in b["dimensions"][dim].get("retired", []):
                if r["code"] == code:
                    rec["change_type"] = r.get("reason", "retired")
                    rec["superseded_by"] = r.get("superseded_by", [])
            removed.append(rec)
        else:
            (dim, old), (_, new) = ea[code], eb[code]
            kind = classify(old, new)
            if kind == "metadata":
                continue
            rec = {"change_type": kind, "dimension": dim, "code": code, "name": new["name"],
                   "documented_in_annex": code in documented}
            for f in ["definition", "source", "source_url", "name"]:
                if old.get(f) != new.get(f):
                    rec.setdefault("fields", []).append(f)
            changed.append(rec)

    if args.undocumented:
        changed = [c for c in changed if not c["documented_in_annex"]]

    if args.json:
        print(json.dumps({"from": args.from_version, "to": args.to_version,
                          "added": added, "removed": removed, "changed": changed}, indent=2, ensure_ascii=False))
        return 0

    print(f"EBA Fraud Taxonomy: {args.from_version} to {args.to_version}\n")
    counts = {}
    for c in changed:
        counts[c["change_type"]] = counts.get(c["change_type"], 0) + 1
    print(f"added {len(added)}, removed {len(removed)}, changed in place {len(changed)} "
          f"({', '.join(f'{v} {k}' for k, v in sorted(counts.items())) or 'none'})\n")

    for title, rows in [("Added", added), ("Removed", removed)]:
        if rows:
            print(f"{title}:")
            for r in rows:
                extra = ""
                if r.get("superseded_by"):
                    extra = f"  -> {', '.join(r['superseded_by'])}"
                print(f"  [{r['change_type']:9}] {r['code']:6} {r['dimension']:18} {r['name']}{extra}")
            print()

    if changed:
        print("Changed in place:")
        for r in changed:
            flag = " " if r["documented_in_annex"] else "*"
            print(f" {flag}[{r['change_type']:9}] {r['code']:6} {r['dimension']:18} {r['name']}"
                  f"  ({', '.join(r.get('fields', []))})")
        if any(not r["documented_in_annex"] for r in changed):
            print("\n  * not mentioned in the target version's own annex")

    review = [r for r in changed if r["change_type"] in {"redefined", "text-changed"}]
    if review:
        print(f"\n{len(review)} entr{'y' if len(review) == 1 else 'ies'} need a human read before adopting "
              f"{args.to_version}: the definition text differs.")
        print("  'redefined' is declared in the data and means meaning changed, so stored records may need "
              "re-classifying.\n  'text-changed' means only that the wording differs. This tool cannot tell a "
              "cosmetic rewording from a\n  change of meaning, and does not guess. Re-citations need no action.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
