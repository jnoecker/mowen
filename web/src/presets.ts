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
