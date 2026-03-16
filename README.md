# mowen (墨紋)

**Authorship attribution toolkit**

mowen is a modular authorship attribution framework for identifying who wrote a
document based on stylometric analysis. It provides a configurable pipeline of
text canonicization, feature extraction, event culling, distance measurement,
and machine-learning classification -- usable as a Python library, CLI, or
full-stack web application.

## Features

- Pluggable pipeline: canonicizers, event drivers, event cullers, distance functions, analysis methods
- 10 canonicizers (case folding, whitespace normalization, punctuation handling, Smash I, ...)
- 35 event drivers (character/word n-grams, skip-grams, POS tags, NER, Porter stemmer, syllables, function words, WordNet definitions, transformer embeddings, ...)
- 14 event cullers (most/least common, IQR, information gain, MAD, index of dispersion, weighted variance, ...)
- 22 distance functions (cosine, Manhattan, KL divergence, chi-square, Keselj weighted, cross-entropy, WED, ...)
- 15 analysis methods (nearest neighbor, SVM, Random Forest, Bagging NN, Thin Cross-Entropy, Burrows' Delta, MLP, ...)
- 4 document loaders (plain text, PDF, DOCX, HTML)
- Leave-one-out and k-fold cross-validation with precision/recall/F1 metrics
- JGAAP CSV compatibility for existing experiment files
- React-based web UI with experiment management
- REST API with OpenAPI docs
- Single-binary Docker deployment

## Quick start

### Python library

```bash
pip install mowen
```

```python
from mowen import Pipeline, PipelineConfig, Document

known = [
    Document(text="...", author="Alice", title="sample_a.txt"),
    Document(text="...", author="Bob", title="sample_b.txt"),
]
unknown = [Document(text="...", title="mystery.txt")]

config = PipelineConfig(
    event_drivers=[{"name": "word_ngram", "params": {"n": 2}}],
    distance_function={"name": "cosine"},
    analysis_method={"name": "nearest_neighbor"},
)

results = Pipeline(config).execute(known, unknown)
for r in results:
    print(r.unknown_document.title, "->", r.rankings[0].author)
```

### CLI

```bash
pip install mowen-cli
```

```bash
# Run an attribution experiment
mowen run -d docs.csv -e word_ngram -e character_ngram:n=3 --distance cosine

# Evaluate accuracy via leave-one-out cross-validation
mowen evaluate -d corpus.csv -e character_ngram:n=3 --distance cosine --mode loo

# List available components
mowen list-components
mowen list-components event-drivers
```

### Web UI

```bash
pip install mowen-server
mowen-server
```

Open http://localhost:8000 in your browser.

### Docker

```bash
docker compose up
```

The app is served at http://localhost:8000 with data persisted in a Docker volume.

## Project structure

```
core/       Python library (mowen)
cli/        Command-line interface (mowen-cli)
server/     FastAPI backend + static frontend serving (mowen-server)
web/        React/TypeScript frontend
```

## License

MIT -- see [LICENSE](LICENSE).
