#!/usr/bin/env python3
"""Build every published version from its extracted PDF text.

    python3 build/build.py

Reads   build/extracted/<v>.json    raw cell text per version (from build/extract.py)
        build/transitions/<v>.json  curated: what each version's annex declares, plus the
                                    identity links a name match cannot find
        build/codes.json            the frozen code registry
Writes  versions/<v>/taxonomy.json  one file per version
        lineage.json                the history of every code across all versions
        build/codes.json            only to append codes for concepts seen for the first time
        build/crosswalk-0.2.json    old per-dimension codes (repository 0.2) to global codes

Nothing here rewords the EBA's text. Definitions and sources are cut out of the PDF
cell verbatim (build/parse.py), and the build fails if the parts do not reassemble
into the cell.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from parse import bullets, match_labels, norm, split_name, split_sources  # noqa: E402

VERSIONS = ["3.1", "4.0", "5.0", "6.0", "7.0"]
DIMENSIONS = ["method", "modus", "initiator", "labels_tags", "payment_instrument"]
# Effective dates are stated in each version's own introduction ("came/will come into effect on 1 January").
EFFECTIVE = {"3.1": "2023-01-01", "4.0": "2024-01-01", "5.0": "2025-01-01", "6.0": "2026-01-01", "7.0": "2027-01-01"}
GROUP = "high_level_classification"
ENTRY = "entry"

problems = []


def fail(msg):
    problems.append(msg)


def key(kind, dimension, name):
    return (kind, dimension, norm(name))


# --------------------------------------------------------------------------- snapshot
def parse_group_block(raw):
    text = raw.strip()
    m = (re.match(r"^[“\"](.+?)[”\"]\s*(\(continued\))?\s*:\s*(.*)$", text)
         or re.match(r"^([^:“\"]{3,140}?)\s*(\(continued\))?\s*:\s*(.*)$", text))
    if not m:
        cont = bool(re.search(r"\(continued\)", text))
        return re.sub(r"\s*\(continued\)\s*$", "", text).strip("“”\" "), None, cont
    return m.group(1).strip(), m.group(3).strip(), bool(m.group(2))


def snapshot(v):
    x = json.load(open(os.path.join(HERE, "extracted", f"{v}.json"), encoding="utf-8"))
    groups, catch_group = [], None
    for b in x["high_level_classification_blocks"]:
        name, definition, continued = parse_group_block(b["raw"])
        if norm(name).startswith("tag line for new fraud type"):
            catch_group = name
            continue
        existing = next((g for g in groups if norm(g["name"]) == norm(name)), None)
        if existing is None:
            groups.append({"name": name, "definition": definition or "", "pdf_page": b["page"], "_continued": continued})
        elif existing["_continued"] and not continued:
            existing.update(definition=definition or "", pdf_page=b["page"], _continued=False)
    label_names = [split_name(e["name"])[0] for e in x["entries"] if e["dim"] == "labels_tags"]
    entries = []
    for e in x["entries"]:
        name, qualifier = split_name(e["name"])
        text = e["cells"][0] if e["cells"] else ""
        rest = " ".join(e["cells"][1:])
        definition, sources = split_sources(text)
        out = {"dimension": e["dim"], "name": name, "pdf_name": e["name"], "definition": definition,
               "sources": sources, "pdf_text": text, "pdf_page": e["page"]}
        if qualifier:
            out["name_qualifier"] = qualifier
        if e["dim"] == "modus":
            out["_group"] = None
            if e.get("group_raw"):
                gname = parse_group_block(e["group_raw"])[0]
                out["_group"] = None if norm(gname).startswith("tag line") else gname
            found, leftover = match_labels(rest, label_names) if rest else ([], "")
            out["possible_labels_tags"] = found
            if leftover:
                out["possible_labels_tags_pdf"] = rest
                out["possible_labels_tags_unmatched"] = leftover
        elif rest:
            out["examples"] = bullets(rest)
        entries.append(out)
        # verbatim check: every part must be a substring of the cell
        for s in sources:
            for part in (s["attribution"], s["url"]):
                if part and part not in text:
                    fail(f"{v} {name}: source part not found verbatim in cell: {part[:60]}")
    return {"raw": x, "groups": groups, "entries": entries, "catch_all_group": catch_group}


# --------------------------------------------------------------------------- codes
def load_registry():
    path = os.path.join(HERE, "codes.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {"format": "T followed by four digits", "next": 1, "codes": {}}


def registry_lookup(reg, first_version, k):
    for code, r in reg["codes"].items():
        if r["first_version"] == first_version and tuple(r["key"]) == tuple(k):
            return code
    return None


def new_code(reg, first_version, k, name):
    code = registry_lookup(reg, first_version, k)
    if code:
        return code
    code = "T%04d" % reg["next"]
    reg["next"] += 1
    reg["codes"][code] = {"first_version": first_version, "key": list(k), "first_name": name}
    return code


# --------------------------------------------------------------------------- build
def items_in_order(snap):
    """(kind, dimension, name, obj) in a fixed, document-independent order."""
    out = []
    for dim in DIMENSIONS:
        if dim == "modus":
            for g in snap["groups"]:
                out.append((GROUP, "modus", g["name"], g))
                for e in snap["entries"]:
                    if e["dimension"] == "modus" and e["_group"] and norm(e["_group"]) == norm(g["name"]):
                        out.append((ENTRY, "modus", e["name"], e))
            for e in snap["entries"]:
                if e["dimension"] == "modus" and not e["_group"]:
                    out.append((ENTRY, "modus", e["name"], e))
        else:
            for e in snap["entries"]:
                if e["dimension"] == dim:
                    out.append((ENTRY, dim, e["name"], e))
    return out


def load_transitions(v):
    path = os.path.join(HERE, "transitions", f"{v}.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def main():
    reg = load_registry()
    snaps = {v: snapshot(v) for v in VERSIONS}
    transitions = {v: load_transitions(v) for v in ["3.0"] + VERSIONS}

    code_of = {}        # (v, key) -> code
    obj_of = {}         # (v, code) -> (kind, dimension, name, obj)
    events = {}         # code -> list of events
    retired = {}        # code -> dict
    derived = {}        # code -> list of derived_from records

    def ev(code, e):
        events.setdefault(code, []).append(e)

    prev_v = None
    for v in VERSIONS:
        snap = snaps[v]
        items = items_in_order(snap)
        links = {}
        consumed = set()
        split_from = {}
        t = transitions[v]
        if prev_v and t:
            for r in t["records"]:
                ct = r["change_type"]
                kind = GROUP if r["kind"] == GROUP else ENTRY
                if ct in ("renamed", "moved"):
                    for f, to in zip(r["from"], r["to"]):
                        src = (prev_v, key(kind, r["dimension"], f))
                        dst = key(kind, r.get("dimension_to", r["dimension"]), to)
                        if src not in code_of:
                            fail(f"{v} transition {ct}: '{f}' not found in {prev_v}")
                            continue
                        links[dst] = code_of[src]
                        consumed.add(code_of[src])
                elif ct == "split":
                    src = (prev_v, key(kind, r["dimension"], r["from"][0]))
                    if src not in code_of:
                        fail(f"{v} split: '{r['from'][0]}' not found in {prev_v}")
                        continue
                    for to in r["to"]:
                        split_from.setdefault(key(kind, r.get("dimension_to", r["dimension"]), to), []).append(code_of[src])
                    consumed.add(code_of[src])
        present = set()
        for kind, dim, name, obj in items:
            k = key(kind, dim, name)
            code = None
            if k in links:
                code = links[k]
            elif prev_v and (prev_v, k) in code_of and code_of[(prev_v, k)] not in consumed:
                code = code_of[(prev_v, k)]
            else:
                code = new_code(reg, v, k, name)
                ev(code, {"version": v, "change_type": "added" if prev_v else "present",
                          **({"dimension": dim} if prev_v else {})})
            if k in split_from:
                for src in split_from[k]:
                    derived.setdefault(code, []).append({"code": src, "relation": "split_from", "in_version": v})
            if code in present:
                fail(f"{v}: code {code} assigned twice ({name})")
            present.add(code)
            code_of[(v, k)] = code
            obj_of[(v, code)] = (kind, dim, name, obj)
        # retirements
        if prev_v:
            for (pv, k), code in list(code_of.items()):
                if pv != prev_v or code in present:
                    continue
                kind, dim, name, obj = obj_of[(prev_v, code)]
                succ = [c for kk, srcs in split_from.items() for s in srcs if s == code
                        for c in [code_of[(v, kk)]]]
                retired[code] = {"code": code, "name": name, "kind": kind, "dimension": dim,
                                 "retired_in": v, "last_version": prev_v,
                                 "reason": "split" if succ else "retired"}
                if succ:
                    retired[code]["superseded_by"] = succ
                ev(code, {"version": v, "change_type": "split" if succ else "retired",
                          **({"superseded_by": succ} if succ else {})})
        prev_v = v

    # group codes for modi
    def group_code(v, obj):
        g = obj.get("_group")
        return code_of.get((v, key(GROUP, "modus", g))) if g else None

    # ------------------------------------------------------------ observed changes
    observed = {}
    for a, b in zip(VERSIONS, VERSIONS[1:]):
        rows = []
        codes_a = {c for (vv, c) in obj_of if vv == a}
        codes_b = {c for (vv, c) in obj_of if vv == b}
        for c in sorted(codes_b - codes_a):
            kind, dim, name, obj = obj_of[(b, c)]
            rows.append({"code": c, "change_type": "added", "kind": kind, "dimension": dim, "name": name,
                         **({"derived_from": [d["code"] for d in derived.get(c, []) if d["in_version"] == b]}
                            if any(d["in_version"] == b for d in derived.get(c, [])) else {})})
        for c in sorted(codes_a - codes_b):
            r = retired[c]
            rows.append({"code": c, "change_type": r["reason"], "kind": r["kind"], "dimension": r["dimension"],
                         "name": r["name"], **({"superseded_by": r["superseded_by"]} if "superseded_by" in r else {})})
        for c in sorted(codes_a & codes_b):
            ka, da, na, oa = obj_of[(a, c)]
            kb, db, nb, ob = obj_of[(b, c)]
            base = {"code": c, "kind": kb, "dimension": db, "name": nb}
            if da != db:
                rows.append({**base, "change_type": "moved", "dimension_from": da})
            if norm(na) != norm(nb) or na != nb and norm(na) == norm(nb):
                rows.append({**base, "change_type": "renamed", "name_from": na,
                             **({"typographic_only": True} if norm(na) == norm(nb) else {})})
            if kb == ENTRY and db == "modus" and da == "modus":
                ga, gb = group_code(a, oa), group_code(b, ob)
                if ga != gb:
                    rows.append({**base, "change_type": "regrouped", "group_from": ga, "group_to": gb})
            if norm(oa.get("definition")) != norm(ob.get("definition")):
                sa = [(norm(s["attribution"]), s["url"]) for s in oa.get("sources", [])]
                sb = [(norm(s["attribution"]), s["url"]) for s in ob.get("sources", [])]
                rows.append({**base, "change_type": "reworded", "sources_changed": sa != sb})
            elif [s["url"] for s in oa.get("sources", [])] != [s["url"] for s in ob.get("sources", [])] or \
                    [norm(s["attribution"]) for s in oa.get("sources", [])] != [norm(s["attribution"]) for s in ob.get("sources", [])]:
                rows.append({**base, "change_type": "source_updated"})
            meta = []
            if oa.get("name_qualifier") != ob.get("name_qualifier"):
                meta.append("name_qualifier")
            if [norm(x) for x in oa.get("examples", [])] != [norm(x) for x in ob.get("examples", [])]:
                meta.append("examples")
            if [norm(x) for x in oa.get("possible_labels_tags", [])] != [norm(x) for x in ob.get("possible_labels_tags", [])]:
                meta.append("possible_labels_tags")
            if meta:
                rows.append({**base, "change_type": "attributes_changed", "fields": meta})
        observed[b] = rows

    # ------------------------------------------------------------ declared (annex) records, resolved to codes
    declared = {}
    for v in ["3.0"] + VERSIONS:
        t = transitions[v]
        if not t:
            continue
        pv = t["previous"]
        out = []
        for r in t["records"]:
            kind = GROUP if r["kind"] == GROUP else ENTRY
            rr = {k: r[k] for k in r if k not in ("from", "to")}
            if r.get("from"):
                rr["from"] = r["from"]
                if pv in VERSIONS:
                    fc = [code_of.get((pv, key(kind, r["dimension"], n))) for n in r["from"]]
                    if None in fc:
                        fail(f"{v} declared {r['change_type']}: unresolved 'from' {r['from']}")
                    rr["from_codes"] = fc
            if r.get("to"):
                rr["to"] = r["to"]
                tv = v if v in VERSIONS else "3.1"
                tdim = r.get("dimension_to", r["dimension"])
                tc = [code_of.get((tv, key(kind, tdim, n))) for n in r["to"]]
                if None in tc:
                    fail(f"{v} declared {r['change_type']}: unresolved 'to' {r['to']} in {tv}")
                rr["to_codes"] = tc
            out.append(rr)
        declared[v] = out

    # ------------------------------------------------------------ reconcile observed against declared
    FACET = {"added": {"added", "split"}, "retired": {"retired"}, "split": {"split"}, "moved": {"moved"},
             "renamed": {"renamed"}, "regrouped": {"regrouped"}, "reworded": {"redefined", "recited"},
             "source_updated": {"recited", "redefined"}}
    reconciliation = {}
    for v in VERSIONS[1:]:
        dec = [r for r in declared.get(v, []) if r.get("in_annex", True)]
        covered = {}
        for r in dec:
            for c in (r.get("to_codes") or []) + (r.get("from_codes") or []):
                covered.setdefault(c, set()).add(r["change_type"])
        not_in_annex, typographic = [], []
        for o in observed[v]:
            if o.get("typographic_only"):
                typographic.append(o)
                continue
            if o["change_type"] == "attributes_changed":
                continue
            want = FACET.get(o["change_type"], set())
            if not (covered.get(o["code"], set()) & want):
                not_in_annex.append(o)
        seen = {}
        for o in observed[v]:
            seen.setdefault(o["code"], set()).add(o["change_type"])
        in_annex_not_observed = []
        INV = {"redefined": {"reworded", "source_updated", "attributes_changed"},
               "recited": {"reworded", "source_updated"},
               "renamed": {"renamed"}, "moved": {"moved"}, "regrouped": {"regrouped"},
               "added": {"added"}, "retired": {"retired", "split"}, "split": {"split", "added", "moved"}}
        for r in dec:
            if r["change_type"] not in INV or r.get("scope"):
                continue
            for c in r.get("to_codes") or r.get("from_codes") or []:
                if c and not (seen.get(c, set()) & INV[r["change_type"]]):
                    in_annex_not_observed.append({"code": c, "change_type": r["change_type"],
                                                  "name": (obj_of.get((v, c)) or obj_of.get((VERSIONS[VERSIONS.index(v) - 1], c)))[2]})
        reconciliation[v] = {"not_in_annex": not_in_annex, "in_annex_not_visible_in_text": in_annex_not_observed,
                             "typographic_renames": typographic}

    # ------------------------------------------------------------ declared introductions from the 3.0 annex
    declared_intro = {}
    for r in declared.get("3.0", []):
        if r["change_type"] in ("added", "moved"):
            for c in r.get("to_codes") or []:
                if c:
                    declared_intro[c] = "3.0"

    # ------------------------------------------------------------ write versions
    change_types = json.load(open(os.path.join(HERE, "change_types.json"), encoding="utf-8"))
    common = json.load(open(os.path.join(HERE, "common.json"), encoding="utf-8"))
    for v in VERSIONS:
        write_version(v, snaps[v], code_of, obj_of, events, observed, declared, reconciliation, retired,
                      derived, declared_intro, group_code, change_types, common, transitions)

    write_lineage(code_of, obj_of, observed, retired, derived, declared_intro, reconciliation)
    write_crosswalk(code_of)
    with open(os.path.join(HERE, "codes.json"), "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=1, ensure_ascii=False)
        f.write("\n")

    # root copies of the latest version
    latest = VERSIONS[-1]
    src = open(os.path.join(ROOT, "versions", latest, "taxonomy.json"), encoding="utf-8").read()
    open(os.path.join(ROOT, "taxonomy.json"), "w", encoding="utf-8").write(src)

    for v in VERSIONS[1:]:
        r = reconciliation[v]
        print(f"{VERSIONS[VERSIONS.index(v) - 1]} -> {v}: observed {len(observed[v])} changes, "
              f"{len(r['not_in_annex'])} not in the annex, {len(r['in_annex_not_visible_in_text'])} declared but not visible")
    if problems:
        print("\n".join("FAIL: " + p for p in problems))
        sys.exit(1)
    print(f"OK: {len(reg['codes'])} codes, {len(retired)} retired")


# --------------------------------------------------------------------------- output helpers
def version_history(snap):
    text = snap["raw"]["chapters"].get("version_history", {}).get("text", "")
    out = []
    for m in re.finditer(r"Version\s+(\d+\.\d+)\s+(\d{1,2} \w+ 20\d\d)", text):
        out.append({"version": m.group(1), "date": m.group(2)})
    return out


def iso(date):
    import datetime
    return datetime.datetime.strptime(date, "%d %B %Y").date().isoformat()


def lifecycle(code, v, obj_of, observed, declared, derived, declared_intro):
    upto = VERSIONS[:VERSIONS.index(v) + 1]
    first = next(x for x in upto if (x, code) in obj_of)
    out = {"status": "active", "introduced_in": "<=3.1" if first == "3.1" else first}
    if code in declared_intro:
        out["declared_introduced_in"] = declared_intro[code]
    last = None
    renamed_from, moved_from, regrouped_from = [], [], []
    for x in upto[1:]:
        dec_types = {}
        for r in declared.get(x, []):
            for c in (r.get("to_codes") or []):
                dec_types.setdefault(c, set()).add(r["change_type"])
        for o in observed.get(x, []):
            if o["code"] != code or o["change_type"] in ("added", "attributes_changed"):
                continue
            if o["change_type"] == "renamed":
                renamed_from.append({"name": o["name_from"], "in_version": x})
            if o["change_type"] == "moved":
                moved_from.append({"dimension": o["dimension_from"], "in_version": x})
            if o["change_type"] == "regrouped":
                regrouped_from.append({"group_code": o["group_from"], "in_version": x})
            ct = o["change_type"]
            if ct in ("reworded", "source_updated"):
                d = dec_types.get(code, set()) & {"redefined", "recited"}
                ct = sorted(d)[0] if d else ("reworded" if ct == "reworded" else "source_updated")
            last = (x, ct)
    if last:
        out["last_modified_in"], out["last_change_type"] = last
    if renamed_from:
        out["renamed_from"] = renamed_from
    if moved_from:
        out["moved_from"] = moved_from
    if regrouped_from:
        out["regrouped_from"] = regrouped_from
    df = [d for d in derived.get(code, []) if VERSIONS.index(d["in_version"]) <= VERSIONS.index(v)]
    if df:
        out["derived_from"] = df
    return out


def entry_out(code, obj, v, obj_of, observed, declared, derived, declared_intro, gc=None, catch_all=False):
    e = {"code": code, "name": obj["name"]}
    if obj.get("name_qualifier"):
        e["name_qualifier"] = obj["name_qualifier"]
    e["definition"] = obj["definition"]
    if obj["sources"]:
        e["sources"] = [{k: s[k] for k in ("attribution", "url") if s.get(k)} for s in obj["sources"]]
    if "examples" in obj:
        e["examples"] = obj["examples"]
    if obj["dimension"] == "modus" and not catch_all:
        e["group_code"] = gc
        e["possible_labels_tags"] = obj["possible_labels_tags"]
        if obj.get("possible_labels_tags_unmatched"):
            e["possible_labels_tags_pdf"] = obj["possible_labels_tags_pdf"]
            e["possible_labels_tags_unmatched"] = obj["possible_labels_tags_unmatched"]
    if catch_all:
        e["is_catch_all"] = True
    if obj["dimension"] == "initiator" and obj.get("name_qualifier", "").startswith("optional"):
        e["optional"] = True
    e.update(lifecycle(code, v, obj_of, observed, declared, derived, declared_intro))
    e["pdf_page"] = obj["pdf_page"]
    e["pdf_text"] = obj["pdf_text"]
    return e


def write_version(v, snap, code_of, obj_of, events, observed, declared, reconciliation, retired, derived,
                  declared_intro, group_code, change_types, common, transitions):
    raw = snap["raw"]
    hist = version_history(snap)
    published = next((iso(h["date"]) for h in hist if h["version"] == v), None)
    meta = raw["metadata"]
    dims = {}
    descriptions = raw["dimension_descriptions"]
    labels_codes = {}
    for dim in DIMENSIONS:
        present = [(c, obj_of[(vv, c)]) for (vv, c) in obj_of if vv == v and obj_of[(vv, c)][1] == dim]
        if not present:
            continue
        block = {"label": common["dimension_labels"][dim], "definition": descriptions.get(dim)}
        ret = [dict(r) for r in retired.values()
               if r["dimension"] == dim and VERSIONS.index(r["retired_in"]) <= VERSIONS.index(v)]
        if dim == "modus":
            groups = []
            for g in snap["groups"]:
                gc = code_of[(v, key(GROUP, "modus", g["name"]))]
                gl = lifecycle(gc, v, obj_of, observed, declared, derived, declared_intro)
                modi = []
                for c, (kind, d, name, obj) in present:
                    if kind == ENTRY and group_code(v, obj) == gc:
                        modi.append(entry_out(c, obj, v, obj_of, observed, declared, derived, declared_intro, gc))
                groups.append({"code": gc, "name": g["name"], "definition": g["definition"], **gl,
                               "pdf_page": g["pdf_page"], "modi": modi})
            block["high_level_classifications"] = groups
            ca = [(c, o) for c, o in present if o[0] == ENTRY and not o[3].get("_group")]
            if ca:
                c, (kind, d, name, obj) = ca[0]
                block["catch_all"] = entry_out(c, obj, v, obj_of, observed, declared, derived, declared_intro,
                                               catch_all=True)
            block["retired"] = [r for r in ret if r["kind"] == ENTRY]
            block["retired_high_level_classifications"] = [r for r in ret if r["kind"] == GROUP]
        else:
            vals = []
            for c, (kind, d, name, obj) in present:
                vals.append(entry_out(c, obj, v, obj_of, observed, declared, derived, declared_intro,
                                      catch_all=(dim == "method" and name.lower().startswith("new method"))))
                if dim == "labels_tags":
                    labels_codes[norm(name)] = c
            block["values"] = vals
            block["retired"] = ret
        for r in block["retired"] + block.get("retired_high_level_classifications", []):
            r["status"] = "retired"
            r.pop("dimension", None)
        dims[dim] = block
    # resolve possible labels to codes
    for g in dims["modus"]["high_level_classifications"]:
        for m in g["modi"]:
            m["possible_labels_tags_codes"] = [labels_codes[norm(n)] for n in m["possible_labels_tags"]]

    blocks = []
    for tv in ["3.0"] + VERSIONS[:VERSIONS.index(v) + 1]:
        t = transitions.get(tv)
        if not t:
            continue
        b = {"version": tv, "previous": t["previous"], "source": t["source"]}
        if t.get("sources_last_checked"):
            b["sources_last_checked"] = t["sources_last_checked"]
        b["declared"] = declared.get(tv, [])
        if t.get("other"):
            b["other"] = t["other"]
        if tv in reconciliation:
            b["observed"] = observed[tv]
            b["reconciliation"] = reconciliation[tv]
        blocks.append(b)

    out = {
        "taxonomy": "EBA Fraud Taxonomy",
        "version": v,
        "published": published,
        "effective_from": EFFECTIVE[v],
        "publisher": common["publisher"],
        "publisher_body": common["publisher_body"],
        "classification": meta["classification"],
        "license": common["license"],
        "source_document": {
            "reference": meta["document_reference"],
            "pages": raw["pages"],
            "copyright_line": meta["copyright_line"],
            "note": common["source_note"],
        },
        "version_history": [{"version": h["version"], "date": iso(h["date"])} for h in hist],
        "code_scheme": common["code_scheme"],
        "change_types": change_types,
        "compatibility": common["compatibility"],
        "lifecycle_note": common["lifecycle_note"],
        "definitions_note": common["definitions_note"],
        "dimensions": dims,
        "changes": blocks,
        "chapters": raw["chapters"],
    }
    if v == "7.0" or "Fake prize" in json.dumps(dims):
        pass
    os.makedirs(os.path.join(ROOT, "versions", v), exist_ok=True)
    with open(os.path.join(ROOT, "versions", v, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")


def write_lineage(code_of, obj_of, observed, retired, derived, declared_intro, reconciliation):
    codes = sorted({c for (_, c) in obj_of})
    out = {"note": "Every code across every transcribed version. 'versions' shows where the concept sat and what it "
                   "was called in each; 'events' is what changed between consecutive versions, as observed in the "
                   "text, with 'in_annex' saying whether that version's own annex records it.",
           "versions": VERSIONS, "codes": {}}
    for c in codes:
        per = {}
        for v in VERSIONS:
            if (v, c) in obj_of:
                kind, dim, name, obj = obj_of[(v, c)]
                per[v] = {"dimension": dim, "name": name}
        kind = next(obj_of[(v, c)][0] for v in VERSIONS if (v, c) in obj_of)
        evs = []
        for v in VERSIONS[1:]:
            missing = {(o["code"], o["change_type"]) for o in reconciliation[v]["not_in_annex"]}
            for o in observed[v]:
                if o["code"] == c and o["change_type"] != "attributes_changed":
                    e = {"version": v, **{k: o[k] for k in o if k not in ("code", "kind", "name", "dimension")}}
                    if not o.get("typographic_only"):
                        e["in_annex"] = (c, o["change_type"]) not in missing
                    evs.append(e)
        rec = {"kind": kind, "versions": per, "events": evs}
        if c in declared_intro:
            rec["declared_introduced_in"] = declared_intro[c]
        if c in retired:
            rec["retired_in"] = retired[c]["retired_in"]
        if c in derived:
            rec["derived_from"] = derived[c]
        out["codes"][c] = rec
    with open(os.path.join(ROOT, "lineage.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")


def write_crosswalk(code_of):
    """Map the per-dimension codes of repository release 0.2 (M01, D001, L001, ...) to global codes."""
    out = {"note": "Repository release 0.2 used one code series per dimension (M, D, G, I, L, P). 0.3 replaced them "
                   "with one global series, so that a concept keeps its code when it moves between dimensions. "
                   "This table maps every 0.2 code to its 0.3 code.", "versions": {}}
    for v in ("6.0", "7.0"):
        try:
            old = json.loads(subprocess.check_output(["git", "-C", ROOT, "show", f"7b627e8:versions/{v}/taxonomy.json"],
                                                     stderr=subprocess.DEVNULL))
        except subprocess.CalledProcessError:
            p = os.path.join(HERE, "legacy-0.2", v, "taxonomy.json")
            if not os.path.exists(p):
                continue
            old = json.load(open(p, encoding="utf-8"))
        m = {}
        d = old["dimensions"]
        for dim in DIMENSIONS:
            if dim == "modus":
                for g in d["modus"]["high_level_classifications"]:
                    m[g["code"]] = code_of.get((v, key(GROUP, "modus", g["name"])))
                    for x in g["modi"]:
                        m[x["code"]] = code_of.get((v, key(ENTRY, "modus", x["name"])))
                ca = d["modus"]["catch_all"]
                m[ca["code"]] = code_of.get((v, key(ENTRY, "modus", split_name(ca["name"])[0])))
                for r in d["modus"].get("retired", []):
                    m[r["code"]] = code_of.get(("6.0", key(ENTRY, "modus", r["name"])))
            else:
                for x in d[dim]["values"]:
                    m[x["code"]] = code_of.get((v, key(ENTRY, dim, x["name"])))
        missing = [k for k, val in m.items() if val is None]
        if missing:
            fail(f"crosswalk {v}: no global code for 0.2 codes {missing}")
        out["versions"][v] = dict(sorted(m.items()))
    with open(os.path.join(HERE, "crosswalk-0.2.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
