# Validation evidence

Validated on 6 November 2026 using Python 3.12.14, pandas 2.2.3 and NumPy 2.3.5.

- All 10 automated tests passed. See [captured test output](test-results.txt).
- The supplied notebook was executed from a clean temporary directory.
- Its accepted CSV equals the new CLI accepted CSV when parsed with pandas.
- Both implementations reject OrderIDs 10046, 10012 and 10038.
- Raw 58 = duplicate 2 + accepted 53 + rejected 3.
- CSV and JSON row counts were read back and verified for all three groups.
- Two separate CLI runs produced byte-identical data exports and summaries.
- Existing output directories are refused.

Tests cover schema failure, an empty source, malformed/fractional/non-finite quantities, non-finite price, multiple rejection reasons, retained unknown discount, shipping fallback, invalid-date behavior and repeatable exports.

GitHub-hosted CI has not yet been run. No scale, latency or production benchmark was performed. Passing these tests demonstrates the documented cases; it does not prove every possible input is supported.
