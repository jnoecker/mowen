# Changelog

All notable changes to mowen will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-03-17

### Added - Authorship Verification
- General Imposters Method (Koppel & Winter 2014) for open-set authorship verification
- Unmasking (Koppel & Schler 2004) for authorship verification via iterative feature elimination
- Non-answer calibration with dual-threshold INCONCLUSIVE support
- Verification badges (VERIFIED / REJECTED / INCONCLUSIVE) in CLI and web UI
- `verdict` field in CLI JSON output for unambiguous verification status

### Added - Evaluation
- PAN-standard metrics: EER, c@1, F_0.5u, Brier score
- Cross-genre evaluation protocol (`cross_genre_evaluate()`)
- Topic-controlled evaluation protocol (`topic_controlled_evaluate()`)
- CLI `--train-genre` / `--test-genre` flags for cross-genre experiments
- CLI `--topic-controlled` flag for topic-controlled experiments

### Added - Analysis Methods
- Contrastive learning analysis method with optional linear projection
- LLM zero-shot prompting analysis method (requires API key)
- R-Drop regularization for MLP classifier
- Eder's Delta (2015) analysis method
- Mahalanobis distance analysis method

### Added - Event Drivers
- SELMA instruction-tuned embedding driver (e5-mistral-7b-instruct)
- Perplexity / surprisal feature extraction from causal language models
- GNN syntactic embedding driver via dependency graph convolution
- Leave-K-Out N-gram driver
- Truncated Frequency driver
- Reaction Time driver (English Lexicon Project data)

### Added - Distance Functions
- PPM compression distance (Teahan & Harper 2003)
- Normalized Compression Distance (NCD)
- Kendall Tau-B rank correlation distance
- Stamatatos' distance

### Added - Event Cullers
- Craig's Zeta culler for distinctive feature selection

### Added - Style Change Detection
- Paragraph-level style change detection module (`detect_style_changes()`)
- CLI `detect-changes` command
- Server API endpoint: `POST /api/v1/style-change/`

### Added - Infrastructure
- 15 literature-based stylometry presets
- Benchmark validation suite (70+ tests against canonical corpora)
- `lower_is_better` and `verification_threshold` fields on `ExperimentResponse` schema

### Changed
- CLI verification JSON output now uses `verdict` field ("VERIFIED" / "REJECTED" / "INCONCLUSIVE") instead of separate `verified` / `inconclusive` fields
- Style change normalization uses 0.0 (no change) when all distances are equal, instead of 0.5
- PPM fallback probability now uses observed alphabet size instead of hardcoded max(alphabet_size, 256)
- Perplexity driver returns NaN features for empty/very short text instead of zeros
- Mahalanobis distance now warns when falling back to pseudo-inverse due to singular covariance matrix
- GNN embeddings driver now logs warnings for high out-of-vocabulary token rates
- Contrastive learning validates that projection_dim <= feature dimension

### Fixed
- Server now validates that distance_function is provided for analysis methods that require it

## [1.0.0] - 2026-02-17

Initial release. See README.md for full feature list.
