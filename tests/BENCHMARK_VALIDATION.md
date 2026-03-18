# Benchmark Validation Report

## Overview

This report documents mowen's performance across its full feature set using
bundled sample corpora.  Unlike the [JGAAP validation](JGAAP_VALIDATION.md)
which compares against an external reference, this suite validates that all
methods produce sensible results and establishes regression baselines.

## Running the Benchmark

```bash
python tests/benchmark_validation.py
```

Requires no external tools.  Takes ~30 minutes due to LOO cross-validation
on the Federalist Papers (74 documents).

## What It Tests

### 1. Metric Computation (3 tests)
- Perfect predictions yield accuracy=1.0, c@1=1.0, F_0.5u=1.0, Brier>0.9
- Non-answer predictions correctly boost c@1 (the Penas & Rodrigo formula)
- EER is low for well-separated author scores

### 2. PPM/NCD Correlation (1 test)
- Both compression-based distances agree on relative ordering (similar texts
  are closer than dissimilar texts)

### 3. Style Change Detection (1 test)
- Splicing Hamilton and Madison texts produces detectable boundaries

### 4. Preset Baselines on Federalist Papers (LOO)
These are regression baselines — exact numbers may vary slightly across
Python versions but should remain in the expected range.

| Preset | Accuracy | Macro F1 | c@1 | Brier |
|--------|----------|----------|-----|-------|
| Burrows' Delta | 91.9% | 0.811 | 0.919 | 0.854 |
| Cosine Delta | 93.2% | 0.890 | 0.932 | 0.102 |
| Char 4-gram | 90.5% | 0.869 | 0.905 | 0.194 |
| Function Words | 95.9% | 0.965 | 0.960 | 0.068 |

### 5. Verification Methods on Federalist Papers

| Method | Accuracy | EER | c@1 | Brier |
|--------|----------|-----|-----|-------|
| General Imposters (LOO) | 94.6% | 0.019 | 0.946 | 0.955 |
| Unmasking (LOO) | 68.9% | 0.334 | 0.689 | 0.311 |
| Imposters + calibration | 94.6% | 0.019 | 0.946 | 0.955 |

Notable: Imposters achieves the **lowest EER (0.019)** of any method,
confirming its strength as a verification method.  Unmasking with small
parameters (n_features=100, n_iterations=5) is weaker but still above
chance.

### 6. New Distance Functions

| Distance | Accuracy (LOO) |
|----------|---------------|
| PPM (order=5) | 67.6% |

PPM is functional but slower than cosine-based methods.  Best used for
forensic verification where compression-based similarity is theoretically
motivated.

### 7. AAAC Problem A (13 authors, LOO)

| Method | Accuracy | Notes |
|--------|----------|-------|
| Nearest Neighbor | 10.5% | Above random (7.7%) |
| KNN (k=3) | 10.5% | Same as NN |
| SVM | 34.2% | Significantly better |
| Contrastive | 7.9% | Near random (no projection) |

SVM substantially outperforms distance-based methods on this many-author
problem, consistent with the literature.

## Key Findings

1. **Function Words is the most accurate preset** on the Federalist Papers
   (95.9%), consistent with Mosteller & Wallace (1964).

2. **Imposters has the best verification performance** (EER=0.019),
   confirming Koppel & Winter (2014).

3. **SVM substantially outperforms distance-based methods** on many-author
   problems (34.2% vs 10.5% on AAAC-A with 13 authors).

4. **All PAN-standard metrics compute correctly** — c@1, F_0.5u, Brier, EER
   produce expected values on synthetic inputs.

5. **Style change detection works** — Hamilton/Madison spliced documents
   produce detectable boundaries.

6. **PPM and NCD agree on relative distances** — both compression-based
   methods rank text similarity consistently.
