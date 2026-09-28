# Derivations

A derivation is a local vocabulary that maps onto this taxonomy instead of replacing it.

Not every institution can adopt the full granularity at once. A domestic scheme may run five categories today; a market moving onto the taxonomy may want a staged transition rather than a single cut-over. The usual outcome is that each party invents its own mapping privately, and the results stop being comparable, which is the problem the taxonomy exists to solve.

The sharpest version of this is the selection burden on the person handling the case. Classifying against the full taxonomy means choosing a method from fourteen, then a modus from twenty-three across ten groups, then an initiator, then optional labels from sixty-seven. An analyst working a queue will not do that carefully on every case, and an institution will not fund the time. What happens instead is that a single habitual value gets picked, which is worse than a coarse but honest one, because it looks like data.

A derivation is the honest answer to that: let the human choose from a short list that fits the work, and let the mapping carry the value up to the full vocabulary. The precision that matters for cross-institution exchange is preserved in the mapping rather than demanded from the analyst. Where a machine assigns the classification instead, the same mapping is what keeps its output comparable with everyone else's.

A derivation makes that mapping explicit and traceable. The local vocabulary can be as coarse as its owner needs, as long as every local value declares what it maps to here. Two institutions using different derivations of the same source can still be reconciled; two institutions using private mappings cannot.

## Rules

1. **Do not redefine or renumber source codes.** A derivation refers to them; it never changes them.
2. **Every local value maps to at least one source code**, with a stated relation.
3. **Declare the source version.** A derivation is valid against one version of the taxonomy, and must be rechecked when a new version takes effect.
4. **A derivation is not a fork.** If a local value cannot be expressed as a relation to any source code, that is a gap in the taxonomy and belongs in the EBA's annual change-request process, not in a private extension.

## Relations

Borrowed from SKOS mapping vocabulary, which is the established way to relate concept schemes.

| Relation | Meaning |
|---|---|
| `exact` | The local value and the source code mean the same thing. |
| `broader` | The local value is wider than the source codes it lists, and covers all of them. |
| `narrower` | The local value is a subset of a single source code. |
| `related` | Associated but not a subset or superset. Use sparingly; it cannot be reconciled automatically. |

`broader` is the common case for a simplified entry-level set, and it is the one that behaves well: counts roll up from source codes to local values without loss. `narrower` does not roll up and needs care, because two institutions can subdivide the same source code differently.

## Shape

See `example-simplified-set.json` in this directory. Minimum fields:

```json
{
  "derivation_of": { "taxonomy": "EBA Fraud Taxonomy", "version": "7.0" },
  "name": "...",
  "maintainer": "...",
  "mappings": [
    { "local_code": "...", "local_name": "...", "relation": "broader", "maps_to": ["T0019"] }
  ]
}
```

## Reconciling across a version change

When a source code is split, a derivation that mapped to it should be updated to map to the successors. `changes` and `dimensions.<name>.retired` in `taxonomy.json` carry what is needed: the retired code, its `superseded_by` list, and `derived_from` on each successor. A derivation mapping to a retired code is not automatically wrong, but it is pinned to the older version until it is rechecked.
