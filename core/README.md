# mowen

Core Python library for authorship attribution.

This package provides the pipeline engine, all built-in components (canonicizers,
event drivers, event cullers, distance functions, analysis methods), evaluation
utilities (cross-validation, metrics), and the tokenizer framework.

## Install

```bash
pip install -e .            # core only (no optional deps)
pip install -e '.[nlp]'     # + spaCy POS/NER
pip install -e '.[all]'     # everything
```

## Usage

```python
from mowen import Pipeline, PipelineConfig, Document, leave_one_out

# Attribution
results = Pipeline(config).execute(known_docs, unknown_docs)

# Cross-validation
eval_result = leave_one_out(docs, config)
print(eval_result.accuracy, eval_result.macro_f1)
```

See the [root README](../README.md) for full documentation.
