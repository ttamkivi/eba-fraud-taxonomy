# EBA Fraud Taxonomy, machine-readable

A JSON transcription of every public version of the Euro Banking Association's **EBA Fraud Taxonomy**: the common vocabulary for categorising payment fraud, maintained by the EBA's Expert Group on Payment Fraud-related Topics (EGPF) since 2020. Five versions are here, 3.1 (October 2022) to 7.0 (June 2026), with one code for each concept across all of them.

The official taxonomy is published as a PDF, once a year. Every institution that integrates it re-types the same tables into its own systems and repeats the work each June. Each of those transcriptions is private, unverified and subtly different from the others, which quietly undermines the comparability the taxonomy exists to create. And because each one starts from the latest PDF, none of them can say what changed.

This repository does that transcription once, in the open, for every version, so it can be checked instead of repeated.

> **Which version do I need?** Anything running in production today is on **6.0**. **7.0** was published on 3 June 2026 and takes effect on **1 January 2027**. Both are in `versions/`, with 3.1, 4.0 and 5.0 for records classified under them.

**What it gives you**

- **Every public version as JSON**, the EBA's text verbatim, each definition with its cited sources separated out and the full PDF cell kept alongside so it can be checked.
- **One code per concept, across versions and dimensions.** A concept keeps its code when it is renamed, when it moves to another dimension, and when it moves to another high-level classification. Stored records survive all three without migration.
- **The history of every code**, in `lineage.json`: where the concept sat and what it was called in each version, and every change to it.
- **A reconciliation of each annual cycle against the EBA's own annex**, in both directions: what changed but is not declared, and what is declared but not visible.
- **Rules for consumers on different versions**, and `migrate.py` to apply them: a record classified under one version can be read under another without being rejected or silently mangled.
- **A validation schema per version**, and a path for simplified local vocabularies that stay reconcilable with everyone else's.

**Status: governed by the EBA, version 0.3.0.** This repository is governed by the Euro Banking Association, which holds the intellectual property in the taxonomy. It is maintained by volunteers in the EBA working group, and the technical implementation is done by an outsourced build partner. The PDF remains the authoritative text, and this repository defers to it wherever the two differ.

```bash
python3 validate.py               # every version, every cross-version check
python3 diff_versions.py 6.0 7.0  # what changed in one cycle, and what the annex omits
python3 diff_versions.py 3.1 7.0  # across any span
python3 migrate.py example-case.json --to 6.0
```

## Files

| File | Purpose |
|---|---|
| `versions/<v>/taxonomy.json` | One file per published version: 3.1, 4.0, 5.0, 6.0, 7.0. Generated; do not edit by hand. |
| `versions/<v>/schema.json` | The record schema for that version, generated from its taxonomy file. |
| `taxonomy.json`, `schema.json` | Copies of the latest version (7.0) at the root. `validate.py` enforces that they match. |
| `lineage.json` | Every code across every version, and every change to it. Generated. |
| `example-case.json` | A 7.0 record that validates against its schema. |
| `validate.py` | Integrity checks within and across versions. Exit code 1 on failure. |
| `diff_versions.py` | What changed between two versions, and what the annex does not declare. |
| `migrate.py` | Reads a record under another version and reports the fidelity of the result. |
| `build_schema.py` | Regenerates the schemas. |
| `build/` | How the versions are made, so the transcription is auditable rather than asserted. See section 4. |
| `derivations/` | How to declare a local or simplified vocabulary that stays traceable to this one. |
| `CHANGELOG.md` | Changes to this repository. Changes to the taxonomy are in each version's `changes`. |
| `LICENSE` | CC BY 4.0. |

## 1. Legal

**Source.** Euro Banking Association, *EBA Fraud Taxonomy*, versions 3.1 (27 October 2022), 4.0 (7 June 2023), 5.0 (5 June 2024), 6.0 (18 June 2025) and 7.0 (3 June 2026). Each file records its document reference under `source_document`.

**Licence.** From version 3.1 onwards the EBA Fraud Taxonomy is licensed by the Euro Banking Association under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) and stated to be available to any interested party. This repository is a derivative work under the same licence. Attribution for the taxonomy content belongs to the Euro Banking Association. Versions 2.0 and 3.0 were classified Closed User Group and are not reproduced here. What is said about the 3.0 cycle comes from Annex I of the public 3.1 document, which describes it.

**Changes made** (CC BY 4.0 requires that these be stated): the PDF's tables were restructured into JSON; line breaks were collapsed and URLs the PDF wrapped across lines were re-joined; each definition's source attributions were cut out into a separate `sources` list, with the full cell kept in `pdf_text`; codes, lifecycle fields and lineage were added. No definition was reworded, shortened or merged. Nothing was added to the taxonomy's content, and no entry was removed.

**Conditions carried over from the EBA's own usage terms.** Users acknowledge the annual review process and the expectation that an updated version is implemented effective 1 January following that cycle, save emergency updates; and adhere to the objective of a common pan-European fraud vocabulary without limitation on payment instrument type.

**Third-party definitions.** Many definitions are quotations from external sources (national fraud reporting bodies, Europol, the FBI, EAST, industry glossaries), cited exactly as the EBA cites them. Those quotations remain the property of their authors. Preserve the attributions in any downstream use.

**Two different EBAs.** The taxonomy is published by the Euro Banking Association, a payments industry association. Its initiator definitions are taken from the Guidelines on fraud reporting under PSD2 issued by the *European Banking Authority*, the EU regulator. They are unrelated organisations that share an acronym.

**Regulatory status.** The taxonomy is aligned with the PSD2 fraud reporting guidelines. The Payment Services Regulation (PSR) and PSD3 have been politically agreed but not yet published in the Official Journal; the EBA has indicated the taxonomy will be reviewed once they are. Do not describe these files as PSR-aligned.

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

An emergency change process exists for regulatory changes or fast-moving fraud developments. Each version's own wording of this process is in its file under `chapters.review_and_updating_process`.

### What this means for an implementation

- **Store the version with every record.** `taxonomy_version` is required in every schema. Entries are added, split, moved and retired between versions; a record's codes are only fully interpretable against the version it was classified under.
- **Store codes, not names.** Names change between versions (fifteen renames in four cycles); codes do not.
- **Labels/tags are open.** The taxonomy states that its labels are suggestions and PSPs may choose their own. The schemas therefore do not constrain `labels_tags_codes`. Codes of the form `T` plus four digits should resolve here; anything else is institution-specific.
- **First party fraud is internal-only.** From 5.0 the PDF states that the high-level classification "First party fraud" is included for exploration and internal reporting, not for fraud intelligence sharing. Respect that boundary in any cross-institution exchange.
- **Propose changes through the EBA, not here.** Additions to the taxonomy's content belong in the EGPF's annual change-request process. This repository tracks what the EBA publishes; it does not fork the taxonomy.

## 3. Technical

### Structure

```
versions/7.0/taxonomy.json
  dimensions
    method              14 values (one is the "New method" catch-all)
    modus               10 high-level classifications holding 23 modi, plus the
                        "New fraud type" catch-all; retired[] and
                        retired_high_level_classifications[]
    initiator            3 values
    labels_tags         67 values (open-ended in the schema)
    payment_instrument   2 values (from 5.0 onwards; absent before)
  changes               one block per cycle from 3.0: what the annex declares,
                        what was observed, and the reconciliation between them
  chapters              the introduction, fraud definition and review process,
                        verbatim
```

Every entry carries `code`, `name`, `definition`, `sources` (each an `attribution` and, where the PDF gives one, a `url`), lifecycle fields, and `pdf_page` and `pdf_text`. Modi also carry `group_code`, `possible_labels_tags` and `possible_labels_tags_codes`. Where the PDF appends a qualifier to a name, such as "First party (optional element relevant, in particular, to card fraud)", the qualifier is in `name_qualifier`.

### Codes

**One series, `T0001` to `T0125`, across every dimension and the high-level classifications.** A code identifies a concept, not a slot. It is assigned the first time the concept appears, and it follows the concept:

- renamed: same code ("Romance scam" became "Romance fraud" in 6.0: `T0095` throughout)
- moved to another dimension: same code (`T0095` was a label/tag until 6.0 and is a modus from 7.0)
- moved to another high-level classification: same code, different `group_code`
- split or merged: new codes for the successors, each carrying `derived_from`

Codes are opaque on purpose. A readable value in a machine field can bias a reviewer before they have read the definition, and both the name and the dimension of a concept change between versions, so neither can be in the identifier. Once assigned, a code is never renumbered or reused. `build/codes.json` is the registry that enforces this: rebuilding never renumbers, and a new code is only ever appended.

Release 0.2 of this repository used one series per dimension (`M01`, `D001`, `L001` and so on). That scheme broke on the most common kind of change: a concept moving between dimensions had to change code. `build/crosswalk-0.2.json` maps every 0.2 code to its 0.3 code.

### Versioning and lifecycle

Every entry carries `status`, `introduced_in` and, where it has changed, `last_modified_in` and `last_change_type`. Entries that have been renamed, moved, regrouped or split carry `renamed_from`, `moved_from`, `regrouped_from` or `derived_from`. `introduced_in` is `<=3.1` for anything already present in 3.1, the earliest public version; `declared_introduced_in` is `3.0` where the annex printed in 3.1 says so. Retired entries keep their code and move to a `retired` array, with `superseded_by` where there are successors.

The change vocabulary, in `change_types`:

| Type | Consumer impact |
|---|---|
| `added` | Add the entry. |
| `retired` | Stop using it for new records. Existing records stay valid under their own version. |
| `split` | One entry becomes several, possibly in a different dimension. Predecessor carries `superseded_by`, successors carry `derived_from`. |
| `merged` | Several become one. The survivor carries `derived_from`. |
| `renamed` | Code unchanged. Display labels change. |
| `moved` | Same concept, different dimension. **Code unchanged.** The entry carries `moved_from`. |
| `regrouped` | A modus moved to another high-level classification. Code unchanged, `group_code` changes. |
| `redefined` | The EBA declares the definition updated, usually as a "clarification". It does not say whether the meaning changed: review. |
| `recited` | The EBA declares the definition replaced with one from a different source. |
| `reworded` | Observed, not declared: the definition text differs and the annex is silent. Needs a human read. |
| `source_updated` | Observed, not declared: the definition is unchanged but its cited source or link changed. |
| `structure_changed` | A change to the taxonomy rather than an entry: a dimension, chapter or attribute added. |

`redefined` and `recited` come from the annex; `reworded` and `source_updated` come from comparing the text. Keeping them apart is the point: the first two are what the EBA intended, the second two are what an implementer will actually see.

### Working across versions

Adopters do not all move on the same day, so a consumer will receive records classified under a version other than the one it runs. That is normal traffic, not an error.

**Reading an older record on a newer version.** Resolve its codes. Codes still present read directly, in whatever dimension they now sit. A retired code is found in the `retired` arrays, and `superseded_by` gives the successors. Do not rewrite the stored record: interpret it at read time and keep the original version stamp, which is the only evidence of what was actually assessed.

**Reading a newer record on an older version.** An unrecognised code must not be discarded and must not be treated as invalid. Widen it: follow `derived_from` to a predecessor the consumer knows, or fall back to the high-level classification. **Widen, never drop and never guess.**

**A code that moved.** A 6.0 record carries Romance fraud (`T0095`) in `labels_tags_codes`; a 7.0 record carries it in `modus_code`. Keep each record's code where it was classified. When counting across versions, count the code, not the field.

| Fidelity | Meaning |
|---|---|
| `exact` | One code to one code. Includes renames and moves, which keep the code. |
| `widening` | A finer code read as a coarser one. Safe: counts roll up without loss. |
| `narrowing` | One code maps to several finer ones. Not automatically resolvable. Keep it coarse or re-classify from the source case. |
| `unresolved` | Retired with no successor, or a dimension the reader's version does not have. Keep it as received. |

```bash
python3 migrate.py record.json --to 7.0   # exits 1 if the result needs a human
python3 migrate.py --explain T0095        # one code's full history
```

Three cases from the real history, all handled:

- A 4.0 record with modus "Card lost or stolen" (`T0042`) read under 7.0 narrows to two labels, "Card lost" (`T0113`) and "Card stolen" (`T0114`). The split crossed dimensions.
- A 7.0 record with modus "Romance fraud" (`T0095`) read under 6.0 is exact. The code is a label/tag there, and the result says so.
- A 7.0 record with "Support a friend or family member fraud" (`T0121`) read under 6.0 widens to "Emotional manipulation" (`T0027`), the modus it was split from.

Each version has its own schema, pinned to that version. A consumer that must accept several versions should select the schema by `taxonomy_version` rather than loosen one schema to accept everything.

### What five years of change cycles show

Every cycle from 3.1 to 7.0 was compared entry by entry and reconciled against that version's annex (`diff_versions.py A B --undocumented`, or `changes[].reconciliation` in any file):

| Cycle | Changes in the text | Not declared in the annex |
|---|---|---|
| 3.1 to 4.0 | 34 | 14 |
| 4.0 to 5.0 | 48 | 22 |
| 5.0 to 6.0 | 34 | 10 |
| 6.0 to 7.0 | 25 | 13 |

Nothing the annexes declare is missing from the text. The gap runs the other way. What the history shows:

1. **Entries move between dimensions in four of the five content cycles.** Method to label/tag in 3.0 and 6.0, modus to label/tag in 3.0 and 5.0, label/tag to modus in 7.0: six concepts in the public versions alone. A code scheme with one series per dimension breaks every year, which is why 0.3 replaced it.
2. **Some concepts change more than once.** Romance was the label/tag "Romance scam" (3.0), then "Romance fraud" (6.0), then a modus (7.0). "Social media compromise" was added as a method in 3.0 and moved to labels/tags in 6.0. First party has been an initiator (from 3.0), a label/tag (deleted in 5.0) and a high-level classification (from 5.0).
3. **The deletion register starts at 7.0.** 7.0 added a chapter, *Items that have been deleted*, which lists one item. The public versions retired five: the method "Man in the middle" (4.0), the high-level classification "Card fraud", the modus "Card lost or stolen" and the label/tag "First party" (all 5.0), and "Emotional manipulation" (7.0).
4. **One split was described as a move.** The 5.0 annex lists "Card lost" and "Card stolen" among items moved from modus to labels/tags. In 4.0 they were one modus, "Card lost or stolen". No successor rule is stated, so a trend series on the 4.0 modus has nowhere to go.
5. **Three renames are not declared.** "Fraudulent use of cryptocurrency" became "crypto currency" (4.0); "E-mail contact" became "Email contact" and "E-mail compromise" became "Email compromise" (6.0).
6. **Definitions move more than names.** Most definitions are quotations, and quoted sources rewrite their own pages. The text of "Safe account fraud" changed in every public cycle, and in 7.0 the undeclared change turns "encourage you to transfer" into "pressure you to transfer".
7. **The structure changed once.** 5.0 added a whole dimension, payment instrument. A format that hard-codes four dimensions would have broken in 2024.
8. **Some cross-references do not resolve.** Modi list "possible labels/tags" that are not labels in the same version: a generic "Physical proximity credential theft" where only two variants are defined (4.0 onwards), and "Shock call" where the label is "Shock calls" (6.0). These are kept as found, under `possible_labels_tags_unmatched`, and `validate.py` reports them.

None of this is careless drafting. The annex is a guide to intended changes, written for a human reader, and it is good at that. It is not a complete record of textual change, and an implementer who diffs definitions will see more movement than it predicts. That is the argument for a form that can be diffed.

### Local and simplified variants

Not every institution can adopt full granularity at once, and the usual result is private mappings that cannot be compared between institutions. `derivations/` documents how to declare a coarser local vocabulary that maps onto this one with stated relations (`exact`, `broader`, `narrower`, `related`, following SKOS mapping conventions). A derivation never redefines or renumbers a source code.

### Example record

```json
{
  "taxonomy_version": "7.0",
  "method_code": "T0011", "method": "Phone contact",
  "modus_code": "T0019", "modus": "Safe account fraud",
  "initiator_code": "T0049", "initiator": "Customer",
  "labels_tags_codes": ["T0065", "T0080"],
  "labels_tags": ["Fake bank / financial institution", "Impersonation"],
  "payment_instrument_code": "T0115", "payment_instrument": "Account-to-account transaction"
}
```

## 4. How the versions are built

The versions are generated, not typed. The pipeline is in `build/`, and every step can be rerun:

| Step | File | What it does |
|---|---|---|
| 1 | `build/extract.py` | Reads one PDF with pdfplumber and writes `build/extracted/<v>.json`: every table cell as the PDF holds it. The only step that needs the PDFs. |
| 2 | `build/parse.py` | Splits each cell into definition, sources, examples and name qualifier. Every part is cut out of the cell verbatim. |
| 3 | `build/transitions/<v>.json` | Curated. What each version's annex declares, in the change vocabulary, and the identity links a name match cannot find (a rename, a move, a split). Each record says whether the annex states it (`in_annex`). |
| 4 | `build/build.py` | Assigns and freezes codes, carries identity through renames, moves and splits, compares consecutive versions, reconciles them with the annexes, and writes `versions/`, `lineage.json` and the crosswalk. |

```bash
python3 build/extract.py EBA_..._v7.0.pdf   # only when a PDF changes; needs pdfplumber
python3 build/build.py
python3 build_schema.py
python3 validate.py                         # jsonschema needed for the example check
```

`validate.py` proves the transcription rather than trusting it: every definition plus its sources must reassemble, word for word, into the PDF cell it came from.

### Adding a new version

1. Run `build/extract.py` on the new PDF.
2. Write `build/transitions/<v>.json` from its annex, one record per declared change. Add identity links for any rename or move the annex does not state; the build output lists every addition and retirement, which is where they show up.
3. Add the version to `VERSIONS` and `EFFECTIVE` in `build/build.py`, then build, generate schemas and validate.
4. Read `diff_versions.py <previous> <new> --undocumented` before adopting: it lists what the annex leaves out.
5. Recheck anything in `derivations/` that maps to a split or retired code.

## Contact and corrections

Errors of transcription against the PDF should be reported as issues against this repository. Proposed changes to the taxonomy's content should go to the Euro Banking Association through its annual review process.
