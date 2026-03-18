# mowen-cli

Command-line interface for [mowen](https://pypi.org/project/mowen/), the authorship attribution toolkit.

## Install

```bash
pip install mowen-cli
```

This installs the `mowen` command and the core library.

## Usage

```bash
# Run an attribution experiment
mowen run -d docs.csv -e word_ngram -e character_ngram:n=3 --distance cosine

# Evaluate accuracy via leave-one-out cross-validation
mowen evaluate -d corpus.csv -e character_ngram:n=3 --distance cosine --mode loo

# Evaluate with k-fold and export results
mowen evaluate -d corpus.csv -e word_events --mode kfold -k 10 --output-csv results.csv

# Cross-genre evaluation (CSV needs genre column: filepath,author,genre)
mowen evaluate -d corpus.csv -e character_ngram:n=3 --distance cosine --train-genre formal --test-genre informal

# Topic-controlled evaluation (requires topic metadata)
mowen evaluate -d corpus.csv -e word_events --distance cosine --topic-controlled

# Detect style changes within a document
mowen detect-changes document.txt -e character_ngram:n=3 --distance cosine --threshold 0.5

# List all available pipeline components
mowen list-components
mowen list-components event-drivers --json
```

The CSV manifest format is one row per document: `filepath,author` (leave author empty for unknown documents).

## Documentation

See the [mowen repository](https://github.com/jnoecker/mowen) for full documentation, the web UI, and the REST API server.

## License

MIT — Copyright 2026 John Noecker Jr.
