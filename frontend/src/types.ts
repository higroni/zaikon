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
