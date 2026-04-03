export type ParamValue = string | number | boolean | null;

// Documents
export interface DocumentResponse {
  id: number;
  title: string;
  author_name: string | null;
  file_type: string;
  original_filename: string;
  char_count: number;
  created_at: string;
  updated_at: string;
}

// Sample corpora
export interface SampleCorpusInfo {
  id: string;
  name: string;
  description: string;
  num_known: number;
  num_unknown: number;
  num_authors: number;
}

export interface SampleCorpusImportResponse {
  known_corpus: CorpusResponse;
  unknown_corpus: CorpusResponse;
}

// Corpora
export interface CorpusResponse {
  id: number;
  name: string;
  description: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}

// Pipeline components
export interface ParamInfo {
  name: string;
  type: string;
  default: ParamValue;
  description: string;
  min_value: number | null;
  max_value: number | null;
  choices: ParamValue[] | null;
}

export interface ComponentInfo {
  name: string;
  display_name: string;
  description: string;
  params: ParamInfo[] | null;
  numeric: boolean | null;
}

// Experiments
export interface ComponentSpec {
  name: string;
  params: Record<string, ParamValue>;
}

export interface ExperimentConfig {
  canonicizers: ComponentSpec[];
  event_drivers: ComponentSpec[];
  event_cullers: ComponentSpec[];
  distance_function: ComponentSpec | null;
  analysis_method: ComponentSpec;
}

export interface ExperimentCreate {
  name: string;
  config: ExperimentConfig;
  known_corpus_ids: number[];
  unknown_corpus_ids: number[];
}

export interface ExperimentResponse {
  id: number;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  config: ExperimentConfig;
  progress: number;
  error_message: string | null;
  lower_is_better: boolean;
  verification_threshold: number | null;
  known_corpus_ids: number[];
  unknown_corpus_ids: number[];
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface RankingEntry {
  author: string;
  score: number;
}

export interface ExperimentResultResponse {
  unknown_document: DocumentResponse;
  rankings: RankingEntry[];
  lower_is_better: boolean;
  verification_threshold: number | null;
}
