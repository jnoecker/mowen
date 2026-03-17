<p align="center">
  <img src="docs/logo.png" alt="mowen" width="256" />
</p>

<h1 align="center">mowen (墨紋)</h1>

<p align="center"><strong>Authorship attribution toolkit</strong></p>

mowen is a modular framework for identifying who wrote a document based on
stylometric analysis. It provides a configurable pipeline of text
canonicization, feature extraction, event culling, distance measurement, and
machine-learning classification — usable as a Python library, CLI, or
full-stack web application.

mowen is a clean-room Python successor to
[JGAAP](https://github.com/evllabs/JGAAP), the Java Graphical Authorship
Attribution Program.

## Features

- **95 pipeline components** across 5 stages, all pluggable via a registry system
- **34 event drivers** — character/word n-grams, skip-grams, sorted n-grams, POS tags, NER, Porter stemmer, syllables, function words, WordNet definitions, transformer embeddings, and more
- **22 distance functions** — cosine, Manhattan, KL divergence, chi-square, Keselj weighted, cross-entropy, Hellinger, and more
- **15 analysis methods** — nearest neighbor, KNN, SVM, Random Forest, Logistic Regression, MLP, Burrows' Delta, Markov Chain, Bagging NN, Thin Cross-Entropy, and more
- **14 event cullers** and **10 canonicizers** for feature selection and text normalization
- **20 bundled sample corpora** — Federalist Papers, Shakespeare, Brontë Sisters, Pauline Epistles, Homer, Russian Literature, State of the Union, and 13 AAAC benchmark problems
- **6 stylometry presets** — Burrows' Delta, Cosine Delta, Character N-gram Profile, Function Words, Multi-Feature SVM, and Transformer Embeddings
- **Leave-one-out and k-fold cross-validation** with precision, recall, F1, and confusion matrix
- **Multi-language support** — pluggable tokenizer framework with Chinese segmentation (jieba) and function word lists for 10 languages
- **4 document loaders** — plain text, PDF, DOCX, HTML
- JGAAP CSV compatibility for existing experiment files
- React web UI with experiment builder and results viewer
- REST API with OpenAPI docs at `/docs`
- Docker deployment

## Quick start

### Python library

```bash
pip install -e core/
```

```python
from mowen import Pipeline, PipelineConfig, Document

known = [
    Document(text="The government must be strong.", author="Hamilton"),
    Document(text="Factions are controlled by diversity.", author="Madison"),
]
unknown = [Document(text="The federal union requires power.")]

config = PipelineConfig(
    event_drivers=[{"name": "word_ngram", "params": {"n": 2}}],
    distance_function={"name": "cosine"},
    analysis_method={"name": "nearest_neighbor"},
)

results = Pipeline(config).execute(known, unknown)
print(results[0].top_author)  # "Hamilton"
```

### Cross-validation

```python
from mowen import leave_one_out, PipelineConfig, Document

docs = [
    Document(text="...", author="Hamilton"),
    Document(text="...", author="Madison"),
    # ... more documents with known authors
]
config = PipelineConfig(
    event_drivers=[{"name": "character_ngram", "params": {"n": 3}}],
    distance_function={"name": "cosine"},
    analysis_method={"name": "nearest_neighbor"},
)
result = leave_one_out(docs, config)
print(f"Accuracy: {result.accuracy:.1%}")
print(f"Macro F1: {result.macro_f1:.4f}")
```

### CLI

```bash
pip install -e cli/
```

```bash
# Run an attribution experiment
mowen run -d docs.csv -e word_ngram -e character_ngram:n=3 --distance cosine

# Evaluate accuracy via leave-one-out cross-validation
mowen evaluate -d corpus.csv -e character_ngram:n=3 --distance cosine --mode loo

# Evaluate with k-fold and export results
mowen evaluate -d corpus.csv -e word_events --mode kfold -k 10 --output-csv results.csv

# List all available components
mowen list-components
mowen list-components event-drivers --json
```

### Web UI & API

```bash
pip install -e server/
mowen-server
```

Open http://localhost:8000. API docs at http://localhost:8000/docs.

### Docker

```bash
docker compose up
```

Serves the full app at http://localhost:8000 with data persisted in a Docker volume.

## Project structure

```
core/       Python library (mowen)
  src/mowen/
    pipeline.py          Pipeline orchestrator
    evaluation.py        Cross-validation and metrics
    types.py             Core data types (Document, Event, Histogram, ...)
    canonicizers/        10 text preprocessors
    event_drivers/       34 feature extractors
    event_cullers/       14 feature selectors
    distance_functions/  22 distance/similarity metrics
    analysis_methods/    15 classifiers
    tokenizers/          Pluggable word segmentation (whitespace, jieba)
    document_loaders/    File format readers (txt, pdf, docx, html)
    data/                Function word lists + 20 sample corpora
    compat/              JGAAP CSV import

cli/        Command-line interface (mowen-cli)
server/     FastAPI backend + static frontend serving (mowen-server)
web/        React/TypeScript frontend
tests/      658 tests (pytest)
scripts/    Corpus build scripts
```

## Development

```bash
# Install all packages in development mode
pip install -e core/ -e cli/ -e server/

# Run tests
python -m pytest tests/

# Lint
ruff check core/ cli/ server/ tests/
```

See [docs/ONBOARDING.md](docs/ONBOARDING.md) for the full developer setup guide.

## Optional dependencies

The core library has no required dependencies. Optional features:

| Extra | Install | Enables |
|-------|---------|---------|
| `nlp` | `pip install 'mowen[nlp]'` | POS tagging, NER (spaCy) |
| `transformers` | `pip install 'mowen[transformers]'` | Transformer embeddings (HuggingFace) |
| `chinese` | `pip install 'mowen[chinese]'` | Chinese word segmentation (jieba) |
| `wordnet` | `pip install 'mowen[wordnet]'` | WordNet definition events (NLTK) |
| `pdf` | `pip install 'mowen[pdf]'` | PDF document loading (pdfplumber) |
| `docx` | `pip install 'mowen[docx]'` | DOCX document loading (python-docx) |
| `html` | `pip install 'mowen[html]'` | HTML document loading (BeautifulSoup) |
| `all` | `pip install 'mowen[all]'` | Everything above |

## License

MIT — see [LICENSE](LICENSE).

Copyright 2026 John Noecker Jr.
