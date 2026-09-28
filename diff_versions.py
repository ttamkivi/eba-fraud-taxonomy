#!/usr/bin/env python3
"""What changed between two versions, and what the EBA's annex does not say.

    python3 diff_versions.py 6.0 7.0                 # one annual cycle
    python3 diff_versions.py 3.1 7.0                 # any two versions
    python3 diff_versions.py 5.0 6.0 --undocumented  # only what the annex leaves out
    python3 diff_versions.py 6.0 7.0 --json

Entries are matched on code. Codes are global and follow the concept, so a rename,
a move to another dimension and a move to another high-level classification all
show up as what they are, not as a deletion plus an addition.

For two consecutive versions the report also reconciles the text against that
version's annex, in both directions: changes visible in the text that the annex
does not declare, and changes the annex declares that the text does not show.
That set is not a criticism of the drafting; many definitions are quotations, and
quoted sources reword their own pages between years. It is the reason a
machine-readable diff is worth having.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "build"))
from parse import norm  # noqa: E402

REVIEW = {"reworded", "redefined"}


def load(v):
    p = os.path.join("versions", v, "taxonomy.json")
    if not os.path.exists(p):
        sys.exit(f"no transcription for version {v} (expected {p})")
    return json.load(open(p, encoding="utf-8"))


def index(tax):
    out = {}
    for dim, block in tax["dimensions"].items():
        if dim == "modus":
            for g in block["high_level_classifications"]:
                out[g["code"]] = ("high-level classification", g, None)
                for m in g["modi"]:
                    out[m["code"]] = ("modus", m, g["code"])
            out[block["catch_all"]["code"]] = ("modus", block["catch_all"], None)
        else:
            for x in block["values"]:
                out[x["code"]] = (dim, x, None)
    return out


def sources_key(e):
    return [(norm(s.get("attribution")), s.get("url")) for s in e.get("sources", [])]


def compare(a, b):
    ia, ib = index(a), index(b)
    rows = []
    for c in sorted(set(ib) - set(ia)):
        rows.append({"change_type": "added", "code": c, "dimension": ib[c][0], "name": ib[c][1]["name"]})
    retired = {}
    for dim, block in b["dimensions"].items():
        for r in block.get("retired", []) + block.get("retired_high_level_classifications", []):
            retired[r["code"]] = r
    for c in sorted(set(ia) - set(ib)):
        r = retired.get(c, {})
        rows.append({"change_type": r.get("reason", "retired"), "code": c, "dimension": ia[c][0],
                     "name": ia[c][1]["name"], **({"superseded_by": r["superseded_by"]} if r.get("superseded_by") else {})})
    for c in sorted(set(ia) & set(ib)):
        (da, ea, ga), (db, eb, gb) = ia[c], ib[c]
        base = {"code": c, "dimension": db, "name": eb["name"]}
        if da != db:
            rows.append({**base, "change_type": "moved", "from": da})
        if ea["name"] != eb["name"]:
            rows.append({**base, "change_type": "renamed", "from": ea["name"]})
        if ga != gb and da == db == "modus":
            rows.append({**base, "change_type": "regrouped", "from": ga, "to": gb})
        if norm(ea.get("definition")) != norm(eb.get("definition")):
            rows.append({**base, "change_type": "reworded"})
        elif sources_key(ea) != sources_key(eb):
            rows.append({**base, "change_type": "source_updated"})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("from_version")
    ap.add_argument("to_version")
    ap.add_argument("--undocumented", action="store_true", help="only changes the target version's annex does not declare")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    a, b = load(args.from_version), load(args.to_version)
    rows = compare(a, b)

    block = next((x for x in b["changes"] if x["version"] == args.to_version
                  and x.get("previous") == args.from_version), None)
    rec = block.get("reconciliation") if block else None
    undocumented = {(o["code"], o["change_type"]) for o in rec["not_in_annex"]} if rec else set()
    for r in rows:
        if rec is not None:
            r["in_annex"] = (r["code"], r["change_type"]) not in undocumented
    if args.undocumented:
        if rec is None:
            sys.exit("--undocumented needs two consecutive versions: an annex only describes one cycle")
        rows = [r for r in rows if not r["in_annex"]]

    if args.json:
        out = {"from": args.from_version, "to": args.to_version, "changes": rows}
        if rec is not None:
            out["declared_but_not_visible"] = rec["in_annex_not_visible_in_text"]
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    print(f"EBA Fraud Taxonomy: {args.from_version} to {args.to_version}\n")
    counts = {}
    for r in rows:
        counts[r["change_type"]] = counts.get(r["change_type"], 0) + 1
    print(", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "no changes")
    print()
    order = ["added", "retired", "split", "moved", "renamed", "regrouped", "reworded", "source_updated"]
    for ct in order:
        these = [r for r in rows if r["change_type"] == ct]
        if not these:
            continue
        print(f"{ct}:")
        for r in these:
            flag = "*" if rec is not None and not r["in_annex"] else " "
            extra = ""
            if ct == "moved":
                extra = f"  {r['from']} -> {r['dimension']}"
            elif ct == "renamed":
                extra = f"  was '{r['from']}'"
            elif ct == "regrouped":
                extra = f"  {r['from']} -> {r['to']}"
            elif r.get("superseded_by"):
                extra = f"  -> {', '.join(r['superseded_by'])}"
            print(f" {flag} {r['code']}  {r['dimension']:26} {r['name']}{extra}")
        print()
    if rec is not None:
        if any(not r["in_annex"] for r in rows):
            print(f"* not declared in the {args.to_version} annex")
        if rec["in_annex_not_visible_in_text"]:
            print("\nDeclared in the annex but not visible in the text:")
            for r in rec["in_annex_not_visible_in_text"]:
                print(f"   {r['code']}  {r['change_type']:10} {r['name']}")
    review = [r for r in rows if r["change_type"] in REVIEW]
    if review:
        print(f"\n{len(review)} entr{'y' if len(review) == 1 else 'ies'} need a human read before adopting "
              f"{args.to_version}: the definition text differs, and this tool cannot tell a cosmetic rewording "
              f"from a change of meaning.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
