import type { ExperimentConfig } from './types';

export interface Preset {
  id: string;
  name: string;
  description: string;
  citation: string;
  config: ExperimentConfig;
}

/**
 * Pre-configured experiment pipelines following state-of-the-art
 * stylometry best practices.
 */
export const PRESETS: Preset[] = [
  {
    id: 'burrows-delta',
    name: "Burrows' Delta",
    description:
      'The foundational stylometric method. Z-score normalized frequencies of the most frequent words, measured by Manhattan distance. The standard baseline for authorship attribution.',
    citation: 'Burrows (2002)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'word_events', params: { tokenizer: 'whitespace' } },
      ],
      event_cullers: [
        { name: 'most_common', params: { n: 150 } },
      ],
      distance_function: { name: 'manhattan', params: {} },
      analysis_method: { name: 'burrows_delta', params: {} },
    },
  },
  {
    id: 'cosine-delta',
    name: 'Cosine Delta',
    description:
      'The most robust Delta variant. Uses z-score normalized word frequencies with cosine distance, shown to outperform the original across languages and text lengths.',
    citation: 'Evert et al. (2017)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'word_events', params: { tokenizer: 'whitespace' } },
      ],
      event_cullers: [
        { name: 'most_common', params: { n: 300 } },
      ],
      distance_function: { name: 'cosine', params: {} },
      analysis_method: { name: 'nearest_neighbor', params: {} },
    },
  },
  {
    id: 'char-ngram',
    name: 'Character N-gram Profile',
    description:
      'Character 4-grams capture sub-word patterns like morphology, punctuation habits, and spelling preferences. Consistently top-performing in PAN shared tasks.',
    citation: 'Stamatatos (2013), Kestemont (2014)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
      ],
      event_drivers: [
        { name: 'character_ngram', params: { n: 4 } },
      ],
      event_cullers: [
        { name: 'most_common', params: { n: 2500 } },
      ],
      distance_function: { name: 'cosine', params: {} },
      analysis_method: { name: 'nearest_neighbor', params: {} },
    },
  },
  {
    id: 'function-words',
    name: 'Function Word Analysis',
    description:
      'Uses closed-class function words (pronouns, prepositions, conjunctions) as features. Topic-independent and linguistically motivated — captures unconscious stylistic choices.',
    citation: 'Mosteller & Wallace (1964), Argamon (2007)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'function_words', params: { language: 'english', tokenizer: 'whitespace' } },
      ],
      event_cullers: [],
      distance_function: { name: 'cosine', params: {} },
      analysis_method: { name: 'nearest_neighbor', params: {} },
    },
  },
  {
    id: 'ensemble-svm',
    name: 'Multi-Feature SVM',
    description:
      'Combines character trigrams and word bigrams for broad stylistic coverage, classified with a support vector machine. Represents the competition-winning "combine and classify" paradigm.',
    citation: 'Halvani et al. (2016), PAN shared tasks',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
        { name: 'normalize_whitespace', params: {} },
        { name: 'strip_numbers', params: {} },
      ],
      event_drivers: [
        { name: 'character_ngram', params: { n: 3 } },
        { name: 'word_ngram', params: { n: 2, tokenizer: 'whitespace' } },
      ],
      event_cullers: [
        { name: 'most_common', params: { n: 500 } },
      ],
      distance_function: null,
      analysis_method: { name: 'svm', params: {} },
    },
  },
  {
    id: 'transformer',
    name: 'Transformer Embeddings',
    description:
      'Modern neural approach using sentence-transformer embeddings with SVM classification. Captures deep semantic and syntactic patterns. Requires the transformers extra.',
    citation: 'Fabien et al. (2020), Reimers & Gurevych (2019)',
    config: {
      canonicizers: [
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'transformer_embeddings', params: { model_name: 'sentence-transformers/all-MiniLM-L6-v2', max_length: 512 } },
      ],
      event_cullers: [],
      distance_function: null,
      analysis_method: { name: 'svm', params: {} },
    },
  },
  {
    id: 'selma',
    name: 'SELMA Embeddings',
    description:
      'Zero-shot instruction-tuned embeddings optimized for stylistic similarity. Uses e5-mistral-7b-instruct with a style-retrieval instruction prefix. Best cross-genre method from the CrossNews benchmark. Requires the transformers extra and significant GPU memory.',
    citation: 'Ma et al. (2025), Wang et al. (2024)',
    config: {
      canonicizers: [
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'selma_embeddings', params: {} },
      ],
      event_cullers: [],
      distance_function: null,
      analysis_method: { name: 'svm', params: {} },
    },
  },
  {
    id: 'eders-delta',
    name: "Eder's Delta",
    description:
      "Eder's modification of Burrows' Delta using the most frequent words with z-score normalization. Designed to be more robust on shorter texts and more stable across corpus sizes than the original Delta. Widely used in computational literary studies.",
    citation: 'Eder (2011)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'word_events', params: { tokenizer: 'whitespace' } },
      ],
      event_cullers: [
        { name: 'most_common', params: { n: 200 } },
      ],
      distance_function: { name: 'manhattan', params: {} },
      analysis_method: { name: 'eders_delta', params: {} },
    },
  },
  {
    id: 'pan-cngdist',
    name: 'PAN cngdist Baseline',
    description:
      'The surprisingly competitive PAN shared task baseline: character 4-gram profiles compared with cosine distance. Placed 5th at PAN 2023, outperforming most neural submissions. An "embarrassingly simple" but remarkably effective method.',
    citation: 'Stamatatos et al. (PAN 2023)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
      ],
      event_drivers: [
        { name: 'character_ngram', params: { n: 4 } },
      ],
      event_cullers: [
        { name: 'most_common', params: { n: 3000 } },
      ],
      distance_function: { name: 'cosine', params: {} },
      analysis_method: { name: 'nearest_neighbor', params: {} },
    },
  },
  {
    id: 'compression-verification',
    name: 'Compression Verification (PPM)',
    description:
      'Compression-based authorship analysis using Prediction by Partial Matching. Measures cross-entropy between character-level models of two texts. Theoretically motivated: if two texts compress well together, they share statistical regularities. No feature engineering required.',
    citation: 'Teahan & Harper (2003), PAN baselines',
    config: {
      canonicizers: [],
      event_drivers: [
        { name: 'word_events', params: {} },
      ],
      event_cullers: [],
      distance_function: { name: 'ppm', params: { order: 5 } },
      analysis_method: { name: 'nearest_neighbor', params: {} },
    },
  },
  {
    id: 'forensic-verification',
    name: 'Forensic Verification',
    description:
      'Conservative Imposters configuration for forensic casework where false positives are costly. Uses calibration to abstain on borderline cases (scores in [0.35, 0.65] are reported as INCONCLUSIVE). Higher iteration count for more stable results.',
    citation: 'Koppel & Winter (2014), Seidman (2013)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'character_ngram', params: { n: 4 } },
      ],
      event_cullers: [
        { name: 'most_common', params: { n: 1000 } },
      ],
      distance_function: { name: 'cosine', params: {} },
      analysis_method: {
        name: 'imposters',
        params: {
          n_iterations: 200,
          feature_subset_ratio: 0.5,
          random_seed: 42,
          calibration_low: 0.35,
          calibration_high: 0.65,
        },
      },
    },
  },
  {
    id: 'cross-genre',
    name: 'Cross-Genre Robust',
    description:
      'Optimized for attribution across different text genres (e.g., articles vs. tweets, formal vs. informal). Uses function words as features — the most genre-independent stylistic signal — with contrastive centroid matching.',
    citation: 'Ma et al. (AAAI 2025), Argamon (2007)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'function_words', params: { language: 'english', tokenizer: 'whitespace' } },
      ],
      event_cullers: [],
      distance_function: null,
      analysis_method: { name: 'contrastive', params: {} },
    },
  },
  {
    id: 'perplexity-profile',
    name: 'Perplexity Profile',
    description:
      'Captures author-specific predictability patterns by extracting statistical moments (mean, variance, skewness, kurtosis) of per-token surprisal from a causal language model. Different authors produce text with different predictability signatures. Requires the transformers extra.',
    citation: 'Basani & Chen (PAN 2025), Sun et al. (PAN 2025)',
    config: {
      canonicizers: [
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'perplexity', params: { model_name: 'gpt2' } },
      ],
      event_cullers: [],
      distance_function: null,
      analysis_method: { name: 'svm', params: {} },
    },
  },
  {
    id: 'general-imposters',
    name: 'General Imposters Method',
    description:
      'The dominant authorship verification method. Compares the unknown document against both candidate and "imposter" authors across random feature subsets. Score = fraction of iterations where the candidate is closer than any imposter.',
    citation: 'Koppel & Winter (2014)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'character_ngram', params: { n: 4 } },
      ],
      event_cullers: [
        { name: 'most_common', params: { n: 1000 } },
      ],
      distance_function: { name: 'cosine', params: {} },
      analysis_method: { name: 'imposters', params: { n_iterations: 100, feature_subset_ratio: 0.5, random_seed: 42 } },
    },
  },
  {
    id: 'unmasking',
    name: 'Unmasking',
    description:
      'Classic authorship verification via iterative feature elimination. Trains linear SVMs, removes the most discriminative features each round, and measures accuracy degradation. A fast drop in accuracy indicates same-author texts. Requires scikit-learn.',
    citation: 'Koppel & Schler (2004)',
    config: {
      canonicizers: [
        { name: 'unify_case', params: {} },
        { name: 'normalize_whitespace', params: {} },
      ],
      event_drivers: [
        { name: 'word_events', params: { tokenizer: 'whitespace' } },
      ],
      event_cullers: [],
      distance_function: null,
      analysis_method: { name: 'unmasking', params: { n_features: 250, n_eliminate: 6, n_iterations: 10, random_seed: 42 } },
    },
  },
];
