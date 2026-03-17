# Developer Onboarding Guide

Everything you need to go from a clean machine to running mowen and making
changes.

## Prerequisites

- **Python 3.11+** (3.12 or 3.14 also work)
- **Node.js 22+** and npm (only needed for frontend development)
- **Git**
- **Docker** (optional, for containerized deployment)

## Setup

### 1. Clone and install

```bash
git clone https://github.com/jnoecker/mowen.git
cd mowen

# Install all three packages in editable mode
pip install -e core/ -e cli/ -e server/
```

This gives you the `mowen` library, the `mowen` CLI command, and the
`mowen-server` command.

### 2. Verify

```bash
# Run tests
python -m pytest tests/

# Check the CLI works
mowen list-components

# Start the server
mowen-server
# Open http://localhost:8000
```

You should see 658+ tests passing and the web UI loading.

### 3. Optional dependencies

Most event drivers work with zero dependencies. Some require extras:

```bash
# spaCy for POS tagging and NER
pip install 'core/[nlp]'
python -m spacy download en_core_web_sm

# Chinese word segmentation
pip install 'core/[chinese]'

# WordNet definitions
pip install 'core/[wordnet]'
python -c "import nltk; nltk.download('wordnet')"

# All optional deps at once
pip install 'core/[all]'
```

### 4. Frontend development (optional)

```bash
cd web/
npm install
npm run dev    # Vite dev server at http://localhost:5173
```

Run `mowen-server` in a separate terminal so the frontend can hit the API.

## Project layout

```
mowen/
├── core/                    Python library (mowen)
│   └── src/mowen/
│       ├── pipeline.py      Pipeline orchestrator
│       ├── evaluation.py    Cross-validation and metrics
│       ├── types.py         Document, Event, Histogram, Attribution, etc.
│       ├── registry.py      Generic Registry[T] for component discovery
│       ├── parameters.py    ParamDef and Configurable mixin
│       ├── exceptions.py    Exception hierarchy
│       ├── canonicizers/    Text preprocessors (10)
│       ├── event_drivers/   Feature extractors (34)
│       ├── event_cullers/   Feature selectors (14)
│       ├── distance_functions/  Distance metrics (22)
│       ├── analysis_methods/    Classifiers (15)
│       ├── tokenizers/      Word segmentation (whitespace, jieba)
│       ├── document_loaders/  File format readers
│       ├── data/            Function word lists (10 languages)
│       └── compat/          JGAAP CSV import
├── cli/                     CLI (mowen-cli, typer-based)
│   └── src/mowen_cli/main.py
├── server/                  FastAPI REST API (mowen-server)
│   └── src/mowen_server/
│       ├── main.py          App factory, CORS, SPA serving
│       ├── config.py        Settings (env vars with MOWEN_ prefix)
│       ├── db.py            SQLAlchemy engine/session
│       ├── models.py        ORM models
│       ├── schemas.py       Pydantic request/response schemas
│       ├── runner.py        Background experiment execution
│       ├── storage.py       Document file storage
│       └── routers/         API endpoints
├── web/                     React/TypeScript frontend (Vite)
├── tests/                   pytest test suite (658+)
├── scripts/                 Corpus build scripts
└── JGAAP/                   Reference Java implementation (gitignored)
```

## Architecture

### Pipeline

The core abstraction is a 5-stage pipeline:

```
Text → Canonicize → Extract Events → Cull → Build Histograms → Analyze
```

1. **Canonicizers** normalize text (lowercase, strip punctuation, etc.)
2. **Event drivers** extract features (n-grams, POS tags, word lengths, etc.)
3. **Event cullers** filter features (top-N, IQR, information gain, etc.)
4. **Distance functions** measure dissimilarity between histograms
5. **Analysis methods** classify unknown documents by author

There's also a **numeric path** for transformer embeddings that bypasses
steps 3-4 and feeds dense vectors directly to sklearn classifiers.

### Registry pattern

Every component type has a registry. Components register themselves with a
decorator:

```python
@event_driver_registry.register("my_driver")
class MyDriver(EventDriver):
    display_name = "My Driver"
    description = "Does something."

    def create_event_set(self, text: str) -> EventSet:
        ...
```

The pipeline instantiates components by registry name:

```python
config = PipelineConfig(
    event_drivers=[{"name": "my_driver", "params": {"n": 3}}],
    ...
)
```

### Tokenizer framework

Word-based event drivers delegate tokenization to a pluggable `Tokenizer`.
All word drivers accept a `tokenizer` parameter (default: `"whitespace"`).
Set it to `"jieba"` for Chinese text.

### Evaluation

`leave_one_out()` and `k_fold()` in `evaluation.py` wrap the pipeline to
perform cross-validation. They return an `EvaluationResult` with accuracy,
per-author precision/recall/F1, and a confusion matrix.

## Common tasks

### Add a new event driver

1. Create `core/src/mowen/event_drivers/my_driver.py`
2. Subclass `EventDriver`, implement `create_event_set()`
3. Register with `@event_driver_registry.register("my_driver")`
4. Import in `event_drivers/__init__.py`
5. Add tests in `tests/`

Same pattern for canonicizers, cullers, distance functions, and analysis
methods.

### Add a new tokenizer

1. Create `core/src/mowen/tokenizers/my_tokenizer.py`
2. Subclass `Tokenizer`, implement `tokenize()`
3. Register with `@tokenizer_registry.register("my_tokenizer")`
4. Import in `tokenizers/__init__.py`

### Add a function word list

Drop a text file (one word per line, `#` comments allowed) in
`core/src/mowen/data/function_words/<language>.txt`. It becomes available
as `function_words` driver with `language=<language>`.

### Add or rebuild sample corpora

20 sample corpora are bundled under `core/src/mowen/data/sample_corpora/`.
The 7 non-AAAC corpora (Federalist Papers, Shakespeare, etc.) are sourced
from Project Gutenberg and can be rebuilt:

```bash
python scripts/build_sample_corpora.py
```

To add a new corpus, add a directory with `.txt` files under
`sample_corpora/` and add an entry to `manifest.json` with `id`, `name`,
`description`, `known`, and `unknown` arrays.

### Run a single test file

```bash
python -m pytest tests/test_event_drivers.py -x -v
```

### Lint and type-check

```bash
ruff check core/ cli/ server/ tests/
mypy core/src/mowen/
```

## Server configuration

Environment variables (all prefixed `MOWEN_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MOWEN_DATABASE_URL` | `sqlite:///{home}/.mowen/data.db` | Database connection string |
| `MOWEN_UPLOAD_DIR` | `~/.mowen/documents` | Document file storage path |
| `MOWEN_HOST` | `127.0.0.1` | Bind address |
| `MOWEN_PORT` | `8000` | Port number |
| `MOWEN_MAX_UPLOAD_BYTES` | `52428800` (50 MB) | Upload size limit |
| `MOWEN_CORS_ORIGINS` | `["*"]` | Allowed CORS origins |

## Troubleshooting

**Tests fail with "table has no column"**: The SQLite test database schema
is out of date. Delete any `*.db` files in your temp directory and re-run.

**spaCy model not found**: Run `python -m spacy download en_core_web_sm`
after installing `mowen[nlp]`.

**Import errors for optional drivers**: Drivers that require optional deps
(spaCy, jieba, NLTK, transformers) raise clear `ImportError` messages with
install instructions. They don't prevent the rest of mowen from loading.

**Server CORS issues**: Default is `allow_origins=["*"]`. For production,
set `MOWEN_CORS_ORIGINS` to your frontend's actual origin.
