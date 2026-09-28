#!/usr/bin/env python3
"""Regenerate versions/<v>/schema.json from versions/<v>/taxonomy.json.

    python3 build_schema.py          # every version, and the root copy of the latest
    python3 build_schema.py 5.0      # one version

The schema fixes the shape of one fraud-case classification record. Permitted codes
are generated from the taxonomy file and must not be edited by hand.
"""
import glob
import json
import os
import shutil
import sys


def codes(vals):
    return [v["code"] for v in vals]


def names(vals):
    return [v["name"] for v in vals]


def build(version):
    tax = json.load(open(os.path.join("versions", version, "taxonomy.json"), encoding="utf-8"))
    dims = tax["dimensions"]
    methods = dims["method"]["values"]
    initiators = dims["initiator"]["values"]
    modi = [m for g in dims["modus"]["high_level_classifications"] for m in g["modi"]]
    catch_all_modus = dims["modus"]["catch_all"]
    catch_all_method = next(v for v in methods if v.get("is_catch_all"))
    instruments = dims.get("payment_instrument", {}).get("values")

    props = {
        "taxonomy_version": {
            "type": "string",
            "const": tax["version"],
            "description": "Taxonomy version the record was classified under. Always store it: entries are added, "
                           "split, moved and retired between versions.",
        },
        "method_code": {"type": "string", "enum": codes(methods),
                        "description": "Method (how) as a code. Canonical machine value."},
        "method": {"type": "string", "enum": names(methods),
                   "description": "Optional display label for method_code. Not a source of truth."},
        "method_new_description": {"type": "string",
                                   "description": f"Required free text when method_code is {catch_all_method['code']} "
                                                  f"({catch_all_method['name']})."},
        "modus_code": {"type": "string", "enum": codes(modi) + [catch_all_modus["code"]],
                       "description": "Modus (what) as a code. Canonical machine value."},
        "modus": {"type": "string", "enum": names(modi) + [catch_all_modus["name"]],
                  "description": "Optional display label for modus_code. Not a source of truth."},
        "modus_new_description": {"type": "string",
                                  "description": f"Required free text when modus_code is {catch_all_modus['code']} "
                                                 f"({catch_all_modus['name']})."},
        "initiator_code": {"type": "string", "enum": codes(initiators),
                           "description": "Initiator (who) as a code. Canonical machine value."},
        "initiator": {"type": "string", "enum": names(initiators),
                      "description": "Optional display label for initiator_code. Not a source of truth."},
        "labels_tags_codes": {
            "type": "array", "items": {"type": "string"}, "uniqueItems": True,
            "description": "Labels/tags (what else) as codes. Deliberately unconstrained: the taxonomy states that its "
                           "labels are suggestions and PSPs may add their own. Values of the form T followed by four "
                           "digits should resolve to taxonomy.json; anything else is institution-specific.",
        },
        "labels_tags": {"type": "array", "items": {"type": "string"}, "uniqueItems": True,
                        "description": "Optional display labels for labels_tags_codes."},
    }
    if instruments:
        props["payment_instrument_code"] = {"type": "string", "enum": codes(instruments),
                                            "description": "Payment instrument (optional) as a code."}
        props["payment_instrument"] = {"type": "string", "enum": names(instruments),
                                       "description": "Optional display label for payment_instrument_code."}

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"EBA Fraud Taxonomy {tax['version']}: fraud case classification record",
        "description": f"Validates one fraud-case classification against the EBA Fraud Taxonomy v{tax['version']}. "
                       "The permitted codes are generated from taxonomy.json by build_schema.py.",
        "type": "object",
        "required": ["taxonomy_version", "method_code", "modus_code", "initiator_code"],
        "properties": props,
        "allOf": [
            {"if": {"properties": {"method_code": {"const": catch_all_method["code"]}}, "required": ["method_code"]},
             "then": {"required": ["method_new_description"]}},
            {"if": {"properties": {"modus_code": {"const": catch_all_modus["code"]}}, "required": ["modus_code"]},
             "then": {"required": ["modus_new_description"]}},
        ],
        "additionalProperties": True,
    }
    dst = os.path.join("versions", version, "schema.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"{dst}: methods={len(methods)} modi={len(modi)}+1 initiators={len(initiators)} "
          f"instruments={len(instruments) if instruments else 'n/a'}")


def main():
    versions = sys.argv[1:] or sorted((os.path.basename(os.path.dirname(p)) for p in glob.glob("versions/*/taxonomy.json")),
                                      key=lambda v: [int(x) for x in v.split(".")])
    for v in versions:
        build(v)
    if not sys.argv[1:]:
        shutil.copyfile(os.path.join("versions", versions[-1], "schema.json"), "schema.json")
        print(f"schema.json: copy of versions/{versions[-1]}/schema.json")


if __name__ == "__main__":
    main()
