# EBA Fraud Taxonomy, machine-readable

A JSON transcription of the Euro Banking Association's **EBA Fraud Taxonomy v7.0** (published 3 June 2026, effective 1 January 2027): the common vocabulary for categorising payment fraud, maintained by the EBA's Expert Group on Payment Fraud-related Topics (EGPF) since 2020.

The official taxonomy is published as a PDF. Every institution that integrates it re-types the same tables into its own systems, and repeats that work each June when a new version is released. Each of those transcriptions is private, unverified, and subtly different from the others, which quietly undermines the comparability the taxonomy exists to create.

This repository does that transcription once, in the open, so it can be checked instead of repeated.

> **Which version do I need?** 7.0 is the latest published version but does not take effect until **1 January 2027**. Anything running in production today is on **6.0**. Both are in `versions/`.

**What it gives you**

- **The full v7.0 content as JSON**, every entry with its definition and source citation, ready to load rather than re-type.
- **Stable identifiers.** The PDF has names only. Names change between versions; these codes do not, so stored records survive a rename without migration.
- **A validation schema** for a classification record, generated from the data so the two cannot drift apart.
- **Version lineage that survives a split.** When a category is divided, a trend series keyed on the old code continues as the sum of its successors instead of dropping to zero.
- **Rules for consumers on different versions**, so a record classified under one version can be read under another without being rejected or silently mangled.
- **A path for simplified local vocabularies** that stay reconcilable with everyone else's, instead of each institution inventing a private mapping.
- **A real diff between versions.** Run `diff_versions.py 6.0 7.0` and see exactly what moved, including the changes the annex does not list.

**Status: community draft, version 0.1.0.** Voluntary work by users of the taxonomy, prepared for the Euro Banking Association. This is not an EBA publication. It is offered to the EBA and to other users of the taxonomy as a basis for discussion; if the EBA chooses to publish an official machine-readable distribution, that will supersede this file. Until then, the PDF is the sole authoritative text and this repository defers to it wherever the two differ.

```bash
python3 validate.py              # check every version, and that root matches the latest
python3 diff_versions.py 6.0 7.0 # what changed between versions
```

Sections 1 to 3 below cover the legal position, what the annual change cycle means for an implementation, and the technical detail. Start at section 3 if you only want to use the files.

## Files

| File | Purpose |
|---|---|
| `versions/<v>/taxonomy.json` | One transcription per published version. Currently **6.0** (in force until 31 December 2026) and **7.0** (effective 1 January 2027). |
| `versions/<v>/schema.json` | The record schema for that version, generated from its taxonomy file. |
| `taxonomy.json`, `schema.json` | Copies of the latest published version (7.0), kept at the root for convenience. `validate.py` enforces that they match. |
| `schema.json` | JSON Schema (2020-12) for validating a single fraud-case classification record. Generated from `taxonomy.json`; do not edit by hand. |
| `example-case.json` | A record that validates against `schema.json`. |
| `build_schema.py` | Regenerates `schema.json` from `taxonomy.json`. |
| `validate.py` | Integrity checks: code uniqueness, cross-references, lineage consistency, schema drift, example validation. Exit code 1 on failure. |
| `migrate.py` | Resolves a classification record across taxonomy versions and reports the fidelity of the result. |
| `diff_versions.py` | Reports what actually changed between two versions, and which of it the official annex does not mention. |
| `build_v6.py` | How the 6.0 transcription was derived, kept so the derivation is auditable. |
| `derivations/` | How to declare a local or simplified vocabulary that stays traceable to this one, with a worked example. |
| `CHANGELOG.md` | Changes to this repository (not to the taxonomy itself; that is in `taxonomy.json` under `version_history` and `changes`). |
| `LICENSE` | CC BY 4.0. |

## 1. Legal

**Source.** Euro Banking Association, *EBA Fraud Taxonomy, Version 7.0*, 3 June 2026. Classification: Public. Document reference `EBA_20260603_EBA_Fraud_Taxonomy_(Fraud_Type_Categorisation)_v7.0`.

**Licence.** The EBA Fraud Taxonomy is licensed by the Euro Banking Association under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) and is stated to be available to any interested party. This repository is a derivative work under the same licence. Attribution for the taxonomy content belongs to the Euro Banking Association.

**Changes made** (CC BY 4.0 requires that these be stated): the PDF's tables were restructured into JSON; opaque codes were added to every entry; a lineage record was added for the modus retired in v7.0; some third-party quotations were shortened and are flagged `abridged: true`; one label spelled two ways in the PDF was normalised (see `spelling_note` in `taxonomy.json`). Nothing was added to the taxonomy's content, and no entry was removed.

**Conditions carried over from the EBA's own usage terms.** Users acknowledge the annual review process and the expectation that an updated version is implemented effective 1 January following that cycle, save emergency updates; and adhere to the objective of a common pan-European fraud vocabulary without limitation on payment instrument type.

**Third-party definitions.** Many individual definitions are quotations from external sources (national fraud reporting bodies, Europol, the FBI, EAST, industry glossaries), each cited with `source` and `source_url` exactly as the EBA cites them. Those quotations remain the property of their authors. Preserve the attributions in any downstream use.

**Two different EBAs.** The taxonomy is published by the Euro Banking Association, a payments industry association. Its `initiator` definitions are taken from the Guidelines on fraud reporting under PSD2 issued by the *European Banking Authority*, the EU regulator. They are unrelated organisations that share an acronym.

**Regulatory status.** The taxonomy is aligned with the PSD2 fraud reporting guidelines. The Payment Services Regulation (PSR) and PSD3 have been politically agreed but not yet published in the Official Journal; the EBA has indicated the taxonomy will be reviewed once they are. Do not describe this file as PSR-aligned.

## 2. Operational

### How the taxonomy changes

| When | What happens |
|---|---|
| October | EBA opens the annual consultation. EGPF members and organisations with usage rights submit change requests on a standard form. |
| Second week of January | Deadline for change requests to method, modus or initiator. |
| Early April | Deadline for change requests to labels/tags, with proposed name and definition. |
| Mid-January to mid-April | EGPF reviews submissions. Non-member submitters are invited to the relevant meeting. |
| May | EBA Board adopts the updated version. |
| June | EBA communicates the new version. |
| By end of December | Six-month implementation lead time; the new version is effective 1 January. |

An emergency change process exists for regulatory changes or fast-moving fraud developments.

### What this means for an implementation

- **Store the version with every record.** `taxonomy_version` is required in `schema.json`. Modi are added, split and retired between versions; a record classified under v6.0 cannot be assumed valid under v7.0 without review.
- **Use codes, not names, as the stored value.** See section 3. Names change; codes do not.
- **Labels/tags are open.** The taxonomy states that its labels are suggestions and that PSPs may choose their own to fit internal reporting. `schema.json` therefore does not constrain `labels_tags_codes` to the listed values. Codes of the form `L` plus three digits should resolve to `taxonomy.json`; anything else is institution-specific.
- **First party fraud is internal-only.** The PDF states that the high-level classification "First party fraud" is included for exploration and internal reporting, not for fraud intelligence sharing. Respect that boundary in any cross-institution exchange.
- **Propose changes through the EBA, not here.** Additions to the taxonomy's content belong in the EGPF's annual change-request process described above. This repository will track what the EBA publishes; it will not fork the taxonomy.

## 3. Technical

### Structure

```
taxonomy.json
  dimensions
    method              14 values, codes M01..M14 (M14 is the "New method" catch-all)
    modus               23 values, codes D001..D023, grouped under 10 high-level
                        classifications G01..G10; catch-all D999 "New fraud type";
                        retired[] holds entries removed in past versions
    initiator            3 values, codes I01..I03
    labels_tags         67 values, codes L001..L067 (open-ended in the schema)
    payment_instrument   2 values, codes P01..P02
```

Every entry carries `code`, `name`, `definition`, and where the PDF gives them `source`, `source_url`, `example` or `examples`. Modi also carry `group_code` and `possible_labels_tags`. Entries whose quoted definition is shortened carry `abridged: true`.

### Codes

Codes are opaque on purpose (`D014`, not `romance_fraud`). A readable value in a machine field can bias a reviewer before they have read the definition, and names can change between versions while identifiers must not. Once published, a code is never renumbered or reused.

### Versioning and lifecycle

The taxonomy changes once a year, and the changes are not all the same kind. Treating them as one undifferentiated "new version" is what forces every consumer to re-read the whole document each June. This repository models them explicitly.

Every entry carries `status`, `introduced_in`, and where it has changed, `last_modified_in` and `last_change_type`. Retired entries keep their code forever, move to their dimension's `retired` array, and are never reused, so a code permanently identifies a concept rather than a slot.

`change_types` in `taxonomy.json` defines the vocabulary:

| Type | Consumer impact |
|---|---|
| `added` | Add the entry. |
| `retired` | Stop using it for new records. Existing records stay valid under their own version. |
| `split` | One entry becomes several. Predecessor carries `superseded_by`, successors carry `derived_from`. |
| `merged` | Several become one. The survivor carries `derived_from`. |
| `renamed` | Code unchanged, so stored records need no migration. Display labels change. |
| `moved` | Same concept, different dimension. The code changes, because namespaces are per dimension. Entry carries `moved_from`. |
| `redefined` | The meaning changed. **The only type that can require re-classifying existing records.** |
| `recited` | Definition text swapped for an equivalent from a different source. Meaning unchanged, no work required. |

The last two are the distinction that saves the most effort. v7.0 re-cited four definitions from different sources without changing any meaning; a consumer diffing on text alone would treat those as substantive and review them for nothing.

`changes` holds one block per version with records typed by that vocabulary, so a consumer can diff programmatically rather than reading an annex.

**Worked example, v7.0.** `D-RETIRED-01` ("Emotional manipulation") was split into `D008`, `D009` and `D010`. A trend series keyed on the retired code continues as the sum of its successors instead of dropping to zero at the version boundary. `D009` ("Romance fraud") additionally carries `moved_from`, because it existed as a label/tag before becoming a modus: one real change, two lineage facts, both recorded.

**A stated gap.** `introduced_in` is `"<=6.0"` for every entry that predates v7.0. The exact version in which those entries first appeared cannot be established from the v7.0 PDF alone and has not been guessed. Backfilling it requires the earlier published versions.

### Working across versions

Adopters do not all move on the same day. The taxonomy is republished annually with a six-month lead time, so a consumer will receive records classified under a version other than the one it runs. That is normal traffic, not an error, and the repository is designed for it.

Codes are the unit of compatibility. A code is assigned once and never renumbered or reused, so it denotes the same concept in every version it appears in, and any two versions can be related through the lineage fields rather than by matching names, which breaks at every rename.

**Reading an older record on a newer version.** Resolve its codes. Ones that still exist read directly. A retired code is found in its dimension's `retired` array, and `superseded_by` gives the successors. Do not rewrite the stored record: interpret it at read time and keep the original version stamp, which is the only evidence of what was actually assessed.

**Reading a newer record on an older version.** An unrecognised code must not be discarded and must not be treated as invalid. Widen it: follow `derived_from` to a predecessor the consumer knows, or fall back to the high-level classification group. **Widen, never drop and never guess.** Dropping loses a case from every downstream count; guessing a sibling invents data. Widening loses precision but is never wrong, and it is recorded.

Every resolution reports a fidelity:

| Fidelity | Meaning |
|---|---|
| `exact` | One code to one code. Safe both directions. Includes entries whose definition was only `recited`, since that does not change meaning. |
| `widening` | Several codes roll up into one coarser code. Safe: counts aggregate without loss. This is what keeps a trend series continuous across a split. |
| `narrowing` | One code maps to several finer ones. Not automatically resolvable; the finer distinction was not in the original record. Keep it coarse or re-classify from the source case. |

`migrate.py` implements this:

```bash
python3 migrate.py record.json --to 7.0   # resolve a record, exit 1 if it needs a human
python3 migrate.py --explain D009          # how one code resolves in both directions
```

`schema.json` pins exactly one version deliberately, so validation is unambiguous about what a record claims to be. A consumer that must accept several versions should keep one generated schema per version and select on `taxonomy_version`, rather than loosening one schema to accept everything. Tag each release so earlier schemas stay retrievable.

This repository currently carries 7.0 only, and the codes in it are assigned here: the EBA's PDF does not define codes. So there is no earlier code table to map from yet. The mechanism is defined now and demonstrated against the 6.0 to 7.0 change, so it is in place before it is needed. Transcribing 6.0 would make the mapping concrete in both directions.

### What actually changes between versions

Running `python3 diff_versions.py 6.0 7.0` on the two transcriptions gives:

```
added 6, removed 2, changed in place 16 (12 recited, 4 text-changed)
```

The annex to v7.0 describes eight changes: one modus split into three, three new labels, one label moved to the modus section, and four definitions re-cited from different sources. All of that is real and correctly documented.

The diff finds **sixteen entries changed in place, eleven of which the annex does not mention.** The largest single pattern is an attribution change: the Australian source cited as "National Anti-Scam Centre" throughout 6.0 is cited as "ScamWatch" throughout 7.0, affecting five entries, with one also changing its article title from "Threats and extortion scams" to "Threat scams". Several cited URLs changed. Four definitions differ in wording.

This is not sloppy drafting. Most definitions in the taxonomy are quotations from external bodies, and those bodies rewrite their own pages between June and June. The EBA re-quotes the current text, which is the right thing to do. The consequence is simply that **the annex is a guide to intended changes, not a complete record of textual ones**, and an implementer diffing on definition text will see more movement than the changelog predicts.

That is the argument for keeping the content in a form that can be diffed. `diff_versions.py --undocumented` lists only the changes the annex does not cover.

A caveat the tool states in its own output: it reports `text-changed` where the definition differs but nothing declares why, because a machine cannot tell a cosmetic rewording from a change of meaning. Two of the four are visibly cosmetic (`Malware` moves quotation marks; `Pure account takeover` modernises "computer criminal" to "cyber criminal"). The tool does not guess, and neither does the data.

### Local and simplified variants

Not every institution can adopt full granularity at once, and the usual result is private mappings that are not comparable between institutions. `derivations/` documents how to declare a coarser local vocabulary that maps onto this one with stated relations (`exact`, `broader`, `narrower`, `related`, following SKOS mapping conventions), so that two parties on different local sets can still be reconciled. A derivation never redefines or renumbers a source code. If a local value cannot be expressed as a relation to any source code, that is a gap in the taxonomy and belongs in the EBA's change-request process rather than a private extension.

### Example record

```json
{
  "taxonomy_version": "7.0",
  "method_code": "M09",  "method": "Phone contact",
  "modus_code": "D001",  "modus": "Safe account fraud",
  "initiator_code": "I01",  "initiator": "Customer",
  "labels_tags_codes": ["L021", "L037"],
  "labels_tags": ["Fake bank / financial institution", "Impersonation"],
  "payment_instrument_code": "P01",  "payment_instrument": "Account-to-account transaction"
}
```

### Checking and regenerating

```bash
python3 validate.py              # every version; exits 1 on any failure
python3 validate.py 7.0          # one version
python3 build_schema.py 7.0      # regenerate that version's schema after editing its taxonomy
python3 diff_versions.py 6.0 7.0 # what changed, and what the annex omits
```

`validate.py` requires the `jsonschema` package for the example-record check and skips it with a warning if the package is absent.

### Updating to a new taxonomy version

1. Add new entries with the next free code in the relevant namespace, `status: "active"` and `introduced_in` set to the new version. Never reuse a code, and never renumber an existing one.
2. Move removed entries to their dimension's `retired` array with `status: "retired"`, `retired_in`, a `reason` from `change_types`, and `superseded_by` where there are successors. Set `derived_from` on each successor.
3. For entries that changed in place, set `last_modified_in` and `last_change_type`. Distinguish `redefined` from `recited` honestly: the first costs consumers a re-classification review, the second costs them nothing.
4. Append a block to `changes` with one typed record per change, and append to `version_history`.
5. Update `version`, `published` and `effective_from`.
6. Run `build_schema.py`, then `validate.py`.
7. Recheck anything in `derivations/` that maps to a retired or split code.
8. During the six-month lead time consumers may need to accept both the outgoing and incoming version; `schema.json` pins one version by design, so tag the previous release.

## Contact and corrections

Errors of transcription against the PDF should be reported as issues against this repository. Proposed changes to the taxonomy's content should go to the Euro Banking Association through its annual review process.
