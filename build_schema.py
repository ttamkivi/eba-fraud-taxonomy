#!/usr/bin/env python3
"""Regenerate schema.json from taxonomy.json. Run after any edit to taxonomy.json."""
import json

import sys, os
VERSION = sys.argv[1] if len(sys.argv) > 1 else None
SRC = os.path.join("versions", VERSION, "taxonomy.json") if VERSION else "taxonomy.json"
tax = json.load(open(SRC))
dims = tax["dimensions"]


def names(vals):
    return [v["name"] for v in vals]


def codes(vals):
    return [v["code"] for v in vals]


methods = dims["method"]["values"]
initiators = dims["initiator"]["values"]
instruments = dims["payment_instrument"]["values"]
modi = [m for g in dims["modus"]["high_level_classifications"] for m in g["modi"]]
catch_all_modus = dims["modus"]["catch_all"]
catch_all_method = next(v for v in methods if v.get("is_catch_all"))

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "EBA Fraud Taxonomy: fraud case classification record",
    "description": (
        f"Validates one fraud-case classification against the EBA Fraud Taxonomy v{tax['version']}. "
        "This schema fixes the shape of a record. The permitted values are versioned data in taxonomy.json; "
        "the enums below are generated from it by build_schema.py and must not be edited by hand."
    ),
    "type": "object",
    "required": ["taxonomy_version", "method_code", "modus_code", "initiator_code"],
    "properties": {
        "taxonomy_version": {
            "type": "string",
            "const": tax["version"],
            "description": "Taxonomy version the record was classified under. Always store it: modi are added, split and retired between versions.",
        },
        "method_code": {
            "type": "string",
            "enum": codes(methods),
            "description": "Method (how): attack vector or first point of contact, as an opaque code. Canonical machine value.",
        },
        "method": {
            "type": "string",
            "enum": names(methods),
            "description": "Optional display label for method_code. Not a source of truth.",
        },
        "method_new_description": {
            "type": "string",
            "description": f"Required free text when method_code is {catch_all_method['code']} ({catch_all_method['name']}).",
        },
        "modus_code": {
            "type": "string",
            "enum": codes(modi) + [catch_all_modus["code"]],
            "description": "Modus (what): the fraudster's action leading to loss via a payment transaction, as an opaque code. Canonical machine value.",
        },
        "modus": {
            "type": "string",
            "enum": names(modi) + [catch_all_modus["name"]],
            "description": "Optional display label for modus_code. Not a source of truth.",
        },
        "modus_new_description": {
            "type": "string",
            "description": f"Required free text when modus_code is {catch_all_modus['code']} ({catch_all_modus['name']}).",
        },
        "initiator_code": {
            "type": "string",
            "enum": codes(initiators),
            "description": "Initiator (who): who initiated the affected payment transaction, as an opaque code. Canonical machine value.",
        },
        "initiator": {
            "type": "string",
            "enum": names(initiators),
            "description": "Optional display label for initiator_code. Not a source of truth.",
        },
        "labels_tags_codes": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
            "description": (
                "Labels/tags (what else) as codes. Optional and deliberately unconstrained: the taxonomy states that "
                "the listed labels are suggestions and PSPs may add their own. Values starting with 'L' followed by "
                "three digits should resolve to taxonomy.json; anything else is institution-specific."
            ),
        },
        "labels_tags": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
            "description": "Optional display labels for labels_tags_codes.",
        },
        "payment_instrument_code": {
            "type": "string",
            "enum": codes(instruments),
            "description": "Payment instrument (optional): account-to-account or card, as an opaque code.",
        },
        "payment_instrument": {
            "type": "string",
            "enum": names(instruments),
            "description": "Optional display label for payment_instrument_code.",
        },
    },
    "allOf": [
        {
            "if": {"properties": {"method_code": {"const": catch_all_method["code"]}}, "required": ["method_code"]},
            "then": {"required": ["method_new_description"]},
        },
        {
            "if": {"properties": {"modus_code": {"const": catch_all_modus["code"]}}, "required": ["modus_code"]},
            "then": {"required": ["modus_new_description"]},
        },
    ],
    "additionalProperties": True,
}

DST = os.path.join("versions", VERSION, "schema.json") if VERSION else "schema.json"
with open(DST, "w") as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"{DST} written: methods={len(methods)} modi={len(modi)}+1 initiators={len(initiators)} instruments={len(instruments)}")
