# mowen (墨紋) — Project Summary

## What It Is

mowen is a full-stack authorship attribution toolkit — a modular framework for identifying who wrote a document based on computational stylometric analysis. It provides a configurable five-stage pipeline (canonicization, feature extraction, event culling, distance measurement, classification), usable as a Python library, command-line tool, REST API, or web application with an interactive experiment builder.

mowen is a clean-room Python successor to JGAAP (the Java Graphical Authorship Attribution Program), a tool I co-authored that has been used in published forensic linguistics casework including the identification of J.K. Rowling as Robert Galbraith and authorship analysis in Chevron v. Donziger.

Published on PyPI as three packages: `mowen` (core library), `mowen-cli`, and `mowen-server`.

## By the Numbers

- **113 pipeline components** across 5 stages: 41 event drivers, 26 distance functions, 21 analysis methods, 15 event cullers, 10 canonicizers
- **790+ tests** (pytest), plus a 70-experiment parallel validation suite against the original JGAAP
- **20 bundled sample corpora** including the Federalist Papers, Shakespeare, Brontë Sisters, Pauline Epistles, Homer (Iliad vs. Odyssey), Russian literature, and 13 AAAC benchmark problems
- **15 stylometry presets** based on published research spanning classic stylometry, modern neural approaches, authorship verification, and forensic best practices
- **~13,000 lines** of Python and TypeScript/CSS
- **10 natural languages** supported via pluggable tokenizers and function word lists
- **4 document formats**: plain text, PDF, DOCX, HTML

## Tech Stack

### Core Library (`mowen`)
- **Python 3.12+**, zero required dependencies
- Generic `Registry[T]` pattern with decorator-based component registration
- Optional extras gated behind pip extras: spaCy (POS/NER), HuggingFace Transformers (embeddings), jieba (Chinese segmentation), NLTK (WordNet), pdfplumber, python-docx, BeautifulSoup
- Two execution paths: discrete (EventSet → Histogram → distance → classifier) and numeric (transformer/SELMA/perplexity/GNN embeddings → sklearn classifier directly)
- Authorship verification via General Imposters Method and Unmasking with calibrated non-answer support
- Style change detection for identifying authorship boundaries within documents
- Cross-validation via `leave_one_out()`, `k_fold()`, `cross_genre_evaluate()`, and `topic_controlled_evaluate()`
- PAN-standard metrics: accuracy, F1, EER, c@1, F_0.5u, Brier score, AUROC, MRR

### CLI (`mowen-cli`)
- Typer-based CLI with commands: `run`, `evaluate`, `list-components`, `convert-jgaap`, `detect-changes`
- JGAAP CSV compatibility for importing existing experiment files

### Server (`mowen-server`)
- FastAPI REST API with OpenAPI docs
- SQLAlchemy ORM with SQLite (configurable to any SQL backend)
- Background experiment execution with real-time progress tracking
- Serves the built frontend as a static SPA

### Frontend (`web/`)
- React 19, TypeScript 5.9, Vite 8
- TanStack React Query for data fetching, Zustand for state management
- CSS Modules architecture with design token system
- 7-step experiment builder wizard with preset configurations
- Real-time results viewer with performance metrics and score distribution visualizations

### Infrastructure
- Docker deployment (multi-stage build: Node frontend → Python backend)
- GitHub Actions CI/CD: tests on tag push, automated PyPI publishing via trusted publishing (OIDC)
- Monorepo with three independently installable Python packages

## Architecture Decisions

**Registry pattern for all components.** Every pipeline stage (canonicizers, event drivers, cullers, distance functions, analysis methods) uses the same generic `Registry[T]` with `@registry.register("name")` decorators. Adding a new component is: write one file, subclass the base, decorate, import in `__init__.py`. No config files, no factory boilerplate.

**Zero required dependencies in core.** The library works with nothing but the Python standard library. Optional capabilities (NLP, transformers, Chinese, PDF) are lazy-imported and gated behind pip extras, so the base install is fast and the import error messages tell users exactly what to install.

**Discrete and numeric execution paths.** Traditional stylometry uses discrete event sets and histogram-based distance functions. Modern approaches use dense embeddings from transformer models. Rather than forcing everything through one paradigm, the pipeline detects numeric mode automatically when a transformer embedding driver is selected and routes to sklearn classifiers, skipping the histogram/distance stages entirely.

**Event cullers see only known documents.** A deliberate design choice to prevent data leakage — unknown documents cannot influence feature selection. This matches proper experimental methodology but differs from some naive implementations.

**CSS Modules, not CSS-in-JS.** All visual styling lives in `.module.css` files and a shared design token system (`variables.css`). No inline React `style={{}}` objects. The design language ("Surreal Gentle Magic") uses SVG turbulence noise for texture, translucent glass-edge borders, and Cormorant Garamond serif typography.

## JGAAP Validation

Systematic parallel comparison against the original Java implementation across 70 experiments covering 15 event drivers, 22 distance functions, and 4 analysis methods:

| Result | Count | Percentage |
|--------|-------|------------|
| Exact match (to float epsilon, ~1e-14) | 32 | 45.7% |
| Same rankings, different absolute scores | 29 | 41.4% |
| Different rankings | 7 | 10.0% |
| Missing from one system | 2 | 2.9% |

**Every divergence is documented and traced to a specific root cause:**
- 6 corrected JGAAP bugs (missing sqrt in Euclidean distance, divide-by-zero in Burrows' Delta, case-sensitive function word matching, etc.)
- 7 intentional formula differences where mowen follows the published mathematical definition and JGAAP used a non-standard variant
- 3 default parameter differences (configurable to match)
- Minor Unicode handling differences (Python full Unicode vs. Java 16-bit char)

No unexplained discrepancies. The core pipeline — tokenization, histogram construction, relative frequency computation, nearest-neighbor aggregation — is faithful to JGAAP to float epsilon precision.

## Sample Corpora

All bundled corpora are import-and-run ready (2+ known authors, held-out unknowns):

| Corpus | Known | Unknown | What It Tests |
|--------|-------|---------|---------------|
| Federalist Papers | 74 (Hamilton/Madison/Jay) | 12 disputed | The canonical stylometry problem |
| Shakespeare vs. Contemporaries | 8 plays | 4 (incl. Henry VIII) | Cross-author drama attribution |
| Brontë Sisters | 26 chapters | 6 held out | Same-genre sibling distinction |
| The Homeric Question | 43 books | 6 held out | Iliad vs. Odyssey single-author hypothesis |
| Pauline Epistles | 8 (Paul + Pastoral) | 3 disputed | Ancient text attribution in translation |
| Russian Literature | 27 chapters | 4 held out | Cross-cultural stylometry on translations |
| State of the Union | 7 addresses | 3 held out | Presidential speech attribution |
| AAAC Problems A–M | 264 total | 98 total | Standardized benchmark suite |

Sourced from Project Gutenberg (public domain) via a reproducible build script.

---

Copyright 2026 John Noecker Jr.
