# Golden Corpus

The files in this package pin the §13 golden corpus as the cross-language
wire-format contract. The committed values in `golden_hashes.json` are expected
to fail when the IR, manifest JSON, diagnostics, shape projection, or snapshot
hashing changes.

Only regenerate the corpus when the wire format changes intentionally. Regenerate
with:

```bash
python -m tests.golden.regenerate --update
```

Review the resulting `tests/golden/golden_hashes.json` diff as part of the
format change.
