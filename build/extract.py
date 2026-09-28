#!/usr/bin/env python3
"""Extract one EBA Fraud Taxonomy PDF into build/extracted/<version>.json.

    python3 build/extract.py path/to/EBA_..._v5.0.pdf

This is the only step that reads a PDF, and the only step that needs pdfplumber
(pip install pdfplumber). Its output is committed, so everything downstream runs
without the PDFs. The output is deliberately raw: cell text exactly as the table
holds it, with line breaks collapsed and URLs re-joined where the PDF wrapped
them. Interpretation (splitting sources, examples, qualifiers) happens in
build/build.py, where it can be checked against this text.
"""
import json
import os
import re
import sys

import pdfplumber

SECTIONS = [
    (r"^method \(how\)", "method"),
    (r"^modus \(what\)", "modus"),
    (r"^initiator \(who\)", "initiator"),
    (r"^labels?[/ ]tags?\b", "labels_tags"),
    (r"^payment instrument \(optional\)", "payment_instrument"),
]
COLUMN_HEADERS = {"name of method", "name of modus", "name of the modus", "high-level description",
                  "example", "definition", "possible labels/tags*", "possible labels/tags"}
DESCRIPTION_ROW = (r"^describes ", r"^can be freely chosen", r"^optional element to identify")
CHAPTERS = [
    ("introduction", r"Introduction to the EBA Fraud Taxonomy"),
    ("version_history", r"EBA Fraud Taxonomy: version history"),
    ("contents", r"Contents"),
    ("dimensions_in_a_fraud_scenario", r"Dimensions to be considered in a fraud scenario"),
    ("description_of_dimensions", r"Description of fraud type dimensions[^\n]*"),
    ("definition_of_fraud", r"Definition of fraud"),
    ("_method", r"Method \(how\)"),
    ("_modus", r"Modus \(what\)"),
    ("_initiator", r"Initiator \(who\)"),
    ("_labels_tags", r"Labels/tags[^\n]*"),
    ("_payment_instrument", r"Payment instrument \(optional\)"),
]
TAIL_CHAPTERS = [
    ("review_and_updating_process", r"Review and updating process"),
    ("items_deleted", r"Items that have been deleted from the EBA Fraud Taxonomy"),
    ("annex", r"Annex[^\n]*"),
]


def rejoin_urls(s):
    # The PDF wraps long URLs; the wrap leaves a space after '-', '/', '_' or '.' inside the URL.
    pat = re.compile(r"(https?://\S*[-/_.])\s+([\w%#?=&./~()-]+)")
    prev = None
    while prev != s:
        prev = s
        s = pat.sub(lambda m: m.group(1) + m.group(2) if not m.group(2)[:1].isupper() else m.group(0), s, count=1)
        s = re.sub(r"(https?://\S+)\s+(%[0-9A-F]{2}\S*)", r"\1\2", s, count=1)
    return s


def clean(s):
    s = (s or "").replace("­", "")
    s = re.sub(r"\s+", " ", s).strip()
    return rejoin_urls(s)


def page_body(text):
    lines = [ln for ln in (text or "").splitlines()
             if not re.search(r"EBA_20\d{6}_EBA_Fraud_Taxonomy|© Euro Banking Association", ln)]
    return "\n".join(lines)


def metadata(pdf):
    first = page_body(pdf.pages[0].extract_text())
    all1 = pdf.pages[0].extract_text() or ""
    meta = {}
    m = re.search(r"Version\s+(\d+\.\d+)", first)
    meta["version"] = m.group(1) if m else None
    m = re.search(r"Classification:\s*(.+)", first)
    meta["classification"] = m.group(1).strip() if m else None
    m = re.search(r"(\d{1,2} \w+ 20\d\d)", first)
    meta["date_on_cover"] = m.group(1) if m else None
    m = re.search(r"(EBA_20\d{6}_EBA_Fraud_Taxonomy_\S+)", all1)
    meta["document_reference"] = m.group(1) if m else None
    m = re.search(r"©[^\n]+", all1)
    meta["copyright_line"] = m.group(0).strip() if m else None
    return meta


def chapters(pdf):
    full = "\n".join(page_body(p.extract_text()) for p in pdf.pages)
    heads = []
    for key, title in CHAPTERS + TAIL_CHAPTERS:
        for m in re.finditer(r"^\s*(?:\d{1,2}\.\s+)?(" + title + r")\s*$", full, re.M):
            heads.append((m.start(), m.end(), key, m.group(1)))
    # keep the last occurrence of each heading (the first is often the contents page)
    last = {}
    for h in heads:
        last[h[2]] = h
    ordered = sorted(last.values())
    out = {}
    for i, (s, e, key, title) in enumerate(ordered):
        end = ordered[i + 1][0] if i + 1 < len(ordered) else len(full)
        if not key.startswith("_"):  # table chapters are captured as entries, not as text
            out[key] = {"heading": title, "text": full[e:end].strip()}
    return out


def tables(pdf, stop_page):
    section = None
    groups, entries, descriptions = [], [], {}
    last = None
    gbuf = None
    for pn, page in enumerate(pdf.pages):
        if stop_page is not None and pn >= stop_page:
            break
        for table in page.extract_tables():
            for row in table:
                cells = [clean(c) for c in row]
                ne = [(i, c) for i, c in enumerate(cells) if c]
                if not ne:
                    continue
                first = ne[0][1]
                low = first.lower()
                sec = next((s for pat, s in SECTIONS if re.match(pat, low)), None)
                if sec and len(ne) == 1 and len(first) < 80:
                    section, last = sec, None
                    continue
                if section is None:
                    continue
                if len(ne) == 1 and re.match("|".join(DESCRIPTION_ROW), low):
                    descriptions.setdefault(section, first)
                    continue
                if low.startswith("high-level classification"):
                    rest = first.split(":", 1)[1].strip() if ":" in first else ""
                    gbuf = [rest] if rest else []
                    last = None
                    continue
                if gbuf is not None and len(ne) == 1 and low not in COLUMN_HEADERS:
                    gbuf.append(first)
                    continue
                if gbuf is not None:
                    groups.append({"raw": " ".join(gbuf), "page": pn + 1})
                    gbuf = None
                if all(c.lower() in COLUMN_HEADERS for _, c in ne):
                    continue
                if cells[0]:
                    e = {"dim": section, "name": cells[0], "cells": [c for i, c in ne if i > 0], "page": pn + 1}
                    if section == "modus":
                        e["group_raw"] = groups[-1]["raw"] if groups else None
                    entries.append(e)
                    last = e
                elif last is not None and len(ne) >= 1 and not (section == "modus" and len(ne) == 1):
                    # a row continued from the previous page or cell
                    for k, (_, c) in enumerate(ne):
                        if k < len(last["cells"]):
                            last["cells"][k] = (last["cells"][k] + " " + c).strip()
                        else:
                            last["cells"].append(c)
                    last.setdefault("continued_on", []).append(pn + 1)
                else:
                    # a free-standing note row inside a section (kept, never silently dropped)
                    notes = descriptions.setdefault("_notes", [])
                    if first not in notes:
                        notes.append(first)
    return groups, entries, descriptions


def extract(path):
    pdf = pdfplumber.open(path)
    stop = None
    for pn, p in enumerate(pdf.pages):
        t = p.extract_text() or ""
        if pn > 8 and re.search(r"^\s*(\d+\.\s+)?(Review and updating process|Items that have been deleted)|^\s*Annex\b",
                                t, re.M | re.I):
            stop = pn
            break
    groups, entries, descriptions = tables(pdf, stop)
    return {
        "source_file": os.path.basename(path),
        "pages": len(pdf.pages),
        "metadata": metadata(pdf),
        "dimension_descriptions": descriptions,
        "high_level_classification_blocks": groups,
        "entries": entries,
        "chapters": chapters(pdf),
    }


def main():
    for path in sys.argv[1:]:
        out = extract(path)
        v = out["metadata"]["version"]
        dst = os.path.join(os.path.dirname(__file__), "extracted", f"{v}.json")
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
            f.write("\n")
        from collections import Counter
        print(f"{v}: {dict(Counter(e['dim'] for e in out['entries']))}, "
              f"{len(out['high_level_classification_blocks'])} classification blocks, "
              f"chapters={sorted(out['chapters'])} -> {dst}")


if __name__ == "__main__":
    main()
