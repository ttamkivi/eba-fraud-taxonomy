# Changelog

Changes to this repository. Changes to the taxonomy itself are recorded by the EBA and mirrored in each version's `changes`.

## 0.3.0 (2026-09-28)

Every public version, verbatim, with one code per concept across all of them. **This release renumbers every code**; see "Global codes" below and `build/crosswalk-0.2.json`.

**All public versions.** `versions/` now holds 3.1 (27 October 2022), 4.0 (7 June 2023) and 5.0 (5 June 2024) alongside 6.0 and 7.0. Versions 2.0 and 3.0 were Closed User Group and are not reproduced; the 3.0 cycle is recorded from Annex I of the public 3.1 document.

**Verbatim text, rebuilt from the PDFs.** 0.2 shortened or paraphrased a third of its definitions (32 of 110 in 7.0 carried `abridged: true`, and some unflagged ones were reworded too). That made a text diff between versions meaningless, because every paraphrase looks like a change. Every version is now generated from its PDF by `build/`: definitions are the EBA's text, sources are cut out into a `sources` list, and the whole cell is kept in `pdf_text`. `validate.py` checks that every definition and its sources reassemble word for word into the cell. `abridged`, `source`, `source_url` and `source_url_2` are gone; `sources` replaces the last three. `build_v6.py` is gone, because 6.0 is no longer derived from 7.0.

**Global codes.** One series, `T0001` to `T0125`, across every dimension and the high-level classifications. A concept keeps its code when it is renamed, moved to another dimension, or moved to another high-level classification; only a split or merge creates new codes. 0.2 used one series per dimension, so a concept that changed dimension had to change code, and the full history shows that happens in four of the five content cycles. `build/codes.json` freezes the assignment: a rebuild never renumbers, and new codes are only appended. This renumbering breaks the 0.2 promise that codes never change. It was done because the project is still a draft with no known adopters, and 0.2 codes map one-to-one through the crosswalk.

**Model fixes found by testing against the history:**

- `moved` keeps the code. A split may cross dimensions ("Card lost or stolen", a modus in 4.0, became the labels "Card lost" and "Card stolen" in 5.0).
- New change types: `regrouped` (a modus moves to another high-level classification: three did in 5.0), `structure_changed` (5.0 added the payment instrument dimension), and two observed-only types, `reworded` and `source_updated`, kept apart from the EBA's declared `redefined` and `recited`.
- High-level classifications have codes and a lifecycle, and can be retired ("Card fraud", 5.0).
- Dimensions can be absent from a version: payment instrument does not exist before 5.0.

**Lineage and reconciliation.** `lineage.json` records, for every code, where the concept sat and what it was called in each version, and every change to it. Each version's `changes` block holds the annex's declarations, the changes observed in the text, and a reconciliation in both directions. Across four public cycles: 14, 22, 10 and 13 changes are not declared in the annex, including three renames and one split; nothing the annexes declare is missing from the text.

**Tools rewritten for the new model.** `diff_versions.py` compares any two versions; for consecutive versions it marks what the annex leaves out. `migrate.py` resolves codes through `lineage.json` in both directions, across moves and multi-step splits, and reports a dimension the reader's version does not have. `validate.py` checks every version and the consistency between them. `example-case.json` and `derivations/example-simplified-set.json` use the new codes.

**Two corrections to 0.2's findings.** The 6.0 to 7.0 diff now finds 13 changes the annex does not declare, not 12; the earlier figure was measured against paraphrased text. And the claim that "card fraud was merged into payment fraud in an earlier version" is more precisely: in 5.0 the high-level classification "Card fraud" was abolished, four of its modi moved to labels/tags (one of them split in two), and three moved to a new classification, "First party fraud".

## 0.2.0 (2026-09-16)

Adds the version currently in force and the means to compare versions.

- `versions/6.0/taxonomy.json`: full transcription of EBA Fraud Taxonomy v6.0 (18 June 2025), the version in force until 31 December 2026. 14 methods, 21 modi, 3 initiators, 65 labels/tags, 2 payment instruments.
- `versions/7.0/` alongside it; `taxonomy.json` and `schema.json` at the root are now copies of the latest published version, and `validate.py` enforces that they match.
- `diff_versions.py`: compares two versions by code, classifies each change, and flags changes the target version's annex does not mention.
- `build_v6.py`: the derivation of 6.0 from 7.0 plus verified reverse deltas, kept so the transcription is auditable rather than asserted. Every delta was checked against text extracted from both official PDFs.
- `validate.py` and `build_schema.py` take an optional version argument; with none, `validate.py` checks all versions.
- `diff_versions.py` follows cross-dimension moves. Previously a concept that changed dimension (and therefore code) was reported as an unrelated retirement plus an unrelated addition, hiding the link a consumer most needs. "Romance fraud" moving from labels/tags to modus in 7.0 now reports as one `moved` record.

**Coverage of the change vocabulary is partial, by circumstance.** The 6.0 to 7.0 transition exercises `added`, `retired`, `split`, `moved` and `recited`. It does not exercise `merged`, `renamed` or `redefined`, and it changes nothing structural: the ten high-level classifications, the three initiators, the two payment instruments and all fourteen method names are identical across both versions. The mechanism is therefore designed but tested against one transition only. Versions 1.0 to 5.0 would test the rest, and the EBA has stated that card fraud was merged into payment fraud in an earlier version, which is exactly the untested case.

**Code scheme corrected before adoption.** The retired modus carried the code `D-RETIRED-01`, which encoded its status into its identifier. That breaks as soon as a version exists in which the entry is active, which is exactly what 6.0 is. It is now `D024`. This is a renumbering, which the stability rule otherwise forbids; it was done at 0.2.0 with no known adopters, and is not expected to happen again.

Finding recorded in the README: the v7.0 annex accounts for four entries that changed in place, and the diff finds sixteen, so twelve are unmentioned. The cause is benign (quoted sources reword their own pages) but it means the annex cannot be relied on as a complete record of textual change.

## 0.1.0 (2026-09-16)

First community draft, transcribed from EBA Fraud Taxonomy v7.0 (3 June 2026).

- `taxonomy.json`: all five dimensions (14 methods, 23 modi in 10 high-level classifications plus a catch-all, 3 initiators, 67 labels/tags, 2 payment instruments), fraud definition, objectives, version history, the v6 to v7 change log, review process.
- Opaque codes on every entry (M, D, G, I, L, P namespaces). Codes are stable once published and never reused.
- Lifecycle metadata on every entry: `status`, `introduced_in`, and `last_modified_in` / `last_change_type` where applicable. A `retired` array on every dimension.
- `change_types` vocabulary (added, retired, split, merged, renamed, moved, redefined, recited) and a machine-diffable `changes` array replacing the prose change log.
- Lineage record for the modus retired in v7.0 ("Emotional manipulation", `D-RETIRED-01`), `derived_from` on its three successors, and `moved_from` on "Romance fraud", which was also promoted from labels/tags.
- `derivations/` convention for declaring a local or simplified vocabulary that stays traceable to this one.
- `schema.json` for validating case records, generated by `build_schema.py`.
- `validate.py` integrity checks.
- `compatibility` block stating the forward and backward rules for consumers running different versions, including the rule that an unrecognised code is widened, never dropped and never guessed.
- `migrate.py` resolves a record across versions and reports fidelity (`exact`, `widening`, `narrowing`), exiting non-zero when a result needs human judgement.
- Shortened third-party quotations flagged `abridged: true`; see `definitions_note` in `taxonomy.json`.

Known limitations of this draft:

- Some third-party definitions are shortened relative to the PDF's verbatim quotation. The PDF governs. A follow-up pass to restore every quotation verbatim is recommended before any official adoption.
- `introduced_in` is `<=6.0` throughout. Versions 1.0 to 5.0 have not been transcribed, so the version in which an entry first appeared is not established and has not been guessed. Transcribing 5.0 and earlier would close this.
- The 5.0 to 6.0 change set is not transcribed, so `diff_versions.py` cannot flag undocumented changes for that transition.
- Not yet reviewed by the Euro Banking Association.
