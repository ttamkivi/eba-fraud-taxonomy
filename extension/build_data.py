#!/usr/bin/env python3
"""Generate extension/taxonomy-data.js from the repository's taxonomy.json.

The extension carries only names and codes, so it stays small and runs offline.
Run from the repository root:  python3 extension/build_data.py
`node extension/test/run.js` fails if the generated file is out of date.
"""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "taxonomy.json"
OUT = ROOT / "extension" / "taxonomy-data.js"


def active(values):
    return [v for v in values if v.get("status", "active") == "active"]


def build():
    raw = SRC.read_bytes()
    t = json.loads(raw)
    d = t["dimensions"]
    modus, hlc_of = {}, {}
    for hlc in d["modus"]["high_level_classifications"]:
        if hlc.get("status", "active") != "active":
            continue
        for m in active(hlc.get("modi", [])):
            modus[m["name"]] = m["code"]
            hlc_of[m["name"]] = hlc["name"]
    catch_all = d["modus"]["catch_all"]
    modus[catch_all["name"]] = catch_all["code"]
    # The catch-all has no high-level classification in the PDF. This label is the plugin's own wording,
    # kept for parity with the Python reference rules; it is not EBA text.
    hlc_of[catch_all["name"]] = "Not covered by the taxonomy"
    data = {
        "taxonomy": t["taxonomy"],
        "version": t["version"],
        "published": t["published"],
        "effective": t["effective_from"],
        "publisher": t["publisher"],
        "licence": t["license"]["name"],
        "sha": hashlib.sha256(raw).hexdigest()[:12],
        "dims": ["method", "modus", "initiator", "instrument", "labels"],
        "multi": ["labels"],
        "newModus": catch_all["name"],
        "codes": {
            "method": {v["name"]: v["code"] for v in active(d["method"]["values"])},
            "modus": modus,
            "initiator": {v["name"]: v["code"] for v in active(d["initiator"]["values"])},
            "instrument": {v["name"]: v["code"] for v in active(d["payment_instrument"]["values"])},
            "labels": {v["name"]: v["code"] for v in active(d["labels_tags"]["values"])},
        },
        "hlcOf": hlc_of,
    }
    head = ("/* EBA Fraud Taxonomy v%s: names and codes, generated from taxonomy.json by extension/build_data.py. "
            "Do not edit by hand. Taxonomy content: Euro Banking Association (CC BY 4.0). */\n" % t["version"])
    return head + "globalThis.EBA_TAXONOMY = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))
