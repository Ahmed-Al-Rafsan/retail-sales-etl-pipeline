# Engineering decisions

| Decision | Rationale | Trade-off |
|---|---|---|
| Local pandas batch | Fits this small CSV and keeps execution inspectable | Loads data into memory |
| Pure transform function | Separates business rules from file I/O and supports focused tests | Single module while scope remains small |
| Quarantine invalid numeric rows | Preserves evidence without inventing sales values | Requires a later review/correction process |
| Keep every applicable reason | Multiple defects should be visible together | Reason text is currently fixed in code |
| Deduplicate before normalisation | Only source-equivalent records count as duplicates | Semantically equivalent text can remain distinct |
| Fresh output directory | Prevents accidental overwrite of earlier evidence | Caller selects run names; no scheduler |
| Summary written after verification | Provides a simple completion marker | Entire output set is not an atomic transaction |
| Keep source and notebook | Makes project origins and learning progression visible | Notebook and CLI have documented behavioral differences |

## Changes from the supplied notebook

The command-line version validates schema, handles malformed/fractional/non-finite quantity instead of failing an Int64 conversion, records multiple reasons, retains raw rejected values, exports duplicates, and produces a hashed run summary. Deduplication happens before filling ShippingState; the notebook fills first. The supplied dataset produces the same 53 accepted and 3 rejected records under both implementations.

These additions were implemented with AI assistance. Review the code and tests before describing them in an interview. Their presence demonstrates a portfolio implementation, not professional production experience.
