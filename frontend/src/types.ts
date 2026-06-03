export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
export type JsonRecord = Record<string, JsonValue>;

export type RequestState = "idle" | "loading" | "success" | "error";

export type TraceStatus = "pending" | "running" | "done" | "warning" | "error";

export interface TraceStage {
  id: string;
  label: string;
  status: TraceStatus;
  summary: string;
  data?: JsonValue;
  artifactName?: string;
}

export interface CorpusRecord {
  id?: string;
  corpus_id?: string;
  name?: string;
  description?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface ImportJobRecord {
  import_job_id?: string;
  corpus_id?: string;
  folder_uri?: string;
  status?: string;
  total_files?: number;
  supported_files?: number;
  unsupported_files?: number;
  started_at?: string;
  completed_at?: string;
  [key: string]: unknown;
}

export interface DocumentRecord {
  id?: string;
  document_id?: string;
  title?: string;
  document_type?: string;
  type?: string;
  corpus_id?: string;
  status?: string;
  version_id?: string;
  document_version_id?: string;
  canonical_json?: JsonValue;
  legal_units?: LegalUnitRecord[];
  [key: string]: unknown;
}

export interface LegalUnitRecord {
  id?: string;
  legal_unit_id?: string;
  label?: string;
  title?: string;
  unit_type?: string;
  text?: string;
  children?: LegalUnitRecord[];
  [key: string]: unknown;
}

export interface SearchResult {
  document_id?: string;
  legal_unit_id?: string;
  title?: string;
  text?: string;
  content_text?: string;
  excerpt?: string;
  citation?: string;
  filename?: string;
  path?: string;
  score?: number;
  semantic_score?: number;
  lexical_score?: number;
  metadata?: JsonRecord;
  [key: string]: unknown;
}

export interface FindingRecord {
  id?: string;
  finding_id?: string;
  pipeline_run_id?: string;
  status?: string;
  severity?: string;
  category?: string;
  title?: string;
  message?: string;
  recommendation?: string;
  review_decision?: string;
  reviewer_note?: string;
  review_note?: string;
  risk_level?: string;
  finding_type?: string;
  explanation?: string;
  evidence?: JsonRecord;
  citations?: JsonValue;
  [key: string]: unknown;
}

export interface DraftReviewRecord {
  id?: string;
  pipeline_run_id?: string;
  title?: string;
  status?: string;
  source_uri?: string;
  content_text?: string;
  selected_corpus_id?: string;
  artifacts?: Record<string, JsonValue>;
  findings?: FindingRecord[];
  [key: string]: unknown;
}

export interface ReportRecord {
  id?: string;
  report_id?: string;
  pipeline_run_id?: string;
  title?: string;
  format?: string;
  report_format?: string;
  status?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface AssistantMessage {
  id?: string;
  role?: "user" | "assistant" | string;
  content?: string;
  content_text?: string;
  answer?: string;
  citations?: JsonValue;
  retrieval_results?: SearchResult[];
  metadata?: JsonRecord;
  [key: string]: unknown;
}

export interface LocalFilesystemEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size_bytes?: number | null;
}

export interface LocalFilesystemBrowseResponse {
  current_path: string;
  parent_path?: string | null;
  entries: LocalFilesystemEntry[];
}

export interface GoldCase {
  case_id?: string;
  title?: string;
  description?: string;
  draft_text?: string;
  corpus_documents?: string[];
  expected_conflicts?: Array<{
    conflict_type?: string;
    severity?: string;
    [key: string]: unknown;
  }>;
  [key: string]: unknown;
}

export interface EvaluationMetrics {
  precision?: number;
  recall?: number;
  f1_score?: number;
  true_positives?: number;
  false_positives?: number;
  false_negatives?: number;
  per_type_metrics?: Record<string, {
    precision?: number;
    recall?: number;
    f1_score?: number;
  }>;
  confusion_matrix?: Array<{
    expected?: string;
    detected?: string;
    count?: number;
  }>;
  [key: string]: unknown;
}

export interface EvaluationResult {
  case_id?: string;
  title?: string;
  status?: string;
  detected_conflicts?: FindingRecord[];
  expected_conflicts?: Array<{
    conflict_type?: string;
    severity?: string;
    [key: string]: unknown;
  }>;
  metrics?: EvaluationMetrics;
  [key: string]: unknown;
}

export interface EvaluationRunResponse {
  results?: EvaluationResult[];
  overall_metrics?: EvaluationMetrics;
  timestamp?: string;
  [key: string]: unknown;
}

export interface ConflictRule {
  rule_id?: string;
  conflict_type?: string;
  category?: string;
  severity?: string;
  description?: string;
  enabled?: boolean;
  operators?: string[];
  [key: string]: unknown;
}

export interface LLMConfig {
  llm_use_provider: boolean;
  llm_base_url: string;
  llm_model: string;
  llm_temperature: number;
  llm_top_p?: number;
  llm_max_tokens: number;
  llm_context_window?: number;
  llm_system_prompt?: string;
  [key: string]: unknown;
}

export interface OllamaModel {
  name: string;
  size: number;
  modified_at: string;
  [key: string]: unknown;
}

export interface EmbeddingConfig {
  embedding_model: string;
  embedding_dimensions: number;
  embedding_batch_size: number;
  embedding_device: string;
  embedding_precision: string;
  [key: string]: unknown;
}

export interface RerankerConfig {
  reranker_model: string;
  reranker_batch_size: number;
  reranker_device: string;
  reranking_enabled: boolean;
  reranking_top_n: number;
  [key: string]: unknown;
}

export interface RAGConfig {
  chunking_strategy: string;
  chunk_size: number;
  chunk_overlap: number;
  search_type: string;
  search_semantic_weight: number;
  search_bm25_weight: number;
  search_top_k: number;
  [key: string]: unknown;
}
