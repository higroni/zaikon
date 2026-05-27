import type {
  AssistantMessage,
  CorpusRecord,
  DocumentRecord,
  DraftReviewRecord,
  FindingRecord,
  ImportJobRecord,
  JsonValue,
  LocalFilesystemBrowseResponse,
  ReportRecord,
  SearchResult
} from "./types";

export const DEFAULT_API_BASE =
  import.meta.env.VITE_ZAIKON_API_BASE ?? "http://127.0.0.1:8100";

export class ApiError extends Error {
  status: number;
  body: string;

  constructor(status: number, body: string) {
    super(`API zahtev nije uspeo (${status})`);
    this.status = status;
    this.body = body;
  }
}

function buildUrl(base: string, path: string, query?: Record<string, string | undefined>) {
  const url = new URL(path, base.endsWith("/") ? base : `${base}/`);
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value) url.searchParams.set(key, value);
  });
  return url.toString();
}

export async function apiRequest<T>(
  base: string,
  path: string,
  init: RequestInit = {},
  query?: Record<string, string | undefined>
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(buildUrl(base, path, query), { ...init, headers });
  const text = await response.text();
  if (!response.ok) throw new ApiError(response.status, text);
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export const Api = {
  health: (base: string) => apiRequest<JsonValue>(base, "health"),
  localRoots: (base: string) =>
    apiRequest<LocalFilesystemBrowseResponse>(base, "api/v1/local-filesystem/roots"),
  browseLocalPath: (base: string, path: string, mode: "folder" | "file") =>
    apiRequest<LocalFilesystemBrowseResponse>(
      base,
      "api/v1/local-filesystem/browse",
      {},
      { path, mode }
    ),
  listCorpora: (base: string) => apiRequest<CorpusRecord[]>(base, "api/v1/corpora"),
  createCorpus: async (base: string, body: object) => {
    const response = await apiRequest<{ corpus?: CorpusRecord } & CorpusRecord>(base, "api/v1/corpora", {
      method: "POST",
      body: JSON.stringify(body)
    });
    return response.corpus ?? response;
  },
  importFolder: (base: string, corpusId: string, body: object) =>
    apiRequest<JsonValue>(base, `api/v1/corpora/${corpusId}/import-folder`, {
      method: "POST",
      body: JSON.stringify(body)
    }),
  listImportJobs: (base: string, corpusId: string) =>
    apiRequest<ImportJobRecord[]>(base, `api/v1/corpora/${corpusId}/import-jobs`),
  importJobReport: async (base: string, jobId: string) => {
    const response = await apiRequest<{ report?: JsonValue } & Record<string, JsonValue>>(base, `api/v1/import-jobs/${jobId}/report`);
    return response.report ?? response;
  },
  importJobArtifacts: (base: string, jobId: string) =>
    apiRequest<string[]>(base, `api/v1/import-jobs/${jobId}/artifacts`),
  importJobArtifact: (base: string, jobId: string, artifactName: string) =>
    apiRequest<JsonValue>(base, `api/v1/import-jobs/${jobId}/artifacts/${artifactName}`),
  listDocuments: (base: string, corpusId?: string) =>
    apiRequest<DocumentRecord[]>(base, "api/v1/documents", {}, { corpus_id: corpusId }),
  getDocument: (base: string, documentId: string) =>
    apiRequest<DocumentRecord>(base, `api/v1/documents/${documentId}`),
  hybridSearch: (base: string, body: object) =>
    apiRequest<{ results?: SearchResult[]; [key: string]: unknown }>(base, "api/v1/search/hybrid", {
      method: "POST",
      body: JSON.stringify(body)
    }),
  createDraftReview: async (base: string, body: object) => {
    const response = await apiRequest<{ draft_review?: DraftReviewRecord } & DraftReviewRecord>(base, "api/v1/draft-reviews", {
      method: "POST",
      body: JSON.stringify(body)
    });
    return response.draft_review ?? response;
  },
  createDraftReviewFromFile: async (base: string, body: object) => {
    const response = await apiRequest<{ draft_review?: DraftReviewRecord } & DraftReviewRecord>(base, "api/v1/draft-reviews/from-file", {
      method: "POST",
      body: JSON.stringify(body)
    });
    return response.draft_review ?? response;
  },
  listDraftReviews: (base: string) => apiRequest<DraftReviewRecord[]>(base, "api/v1/draft-reviews"),
  getDraftReview: async (base: string, runId: string) => {
    const response = await apiRequest<{ draft_review?: DraftReviewRecord; findings?: FindingRecord[]; artifacts?: Record<string, JsonValue>; content_text?: string } & DraftReviewRecord>(base, `api/v1/draft-reviews/${runId}`);
    return response.draft_review
      ? { ...response.draft_review, findings: response.findings, artifacts: response.artifacts, content_text: response.content_text }
      : response;
  },
  runDraftReview: async (base: string, runId: string) => {
    const response = await apiRequest<{ draft_review?: DraftReviewRecord; findings?: FindingRecord[] } & DraftReviewRecord>(base, `api/v1/draft-reviews/${runId}/run`, { method: "POST" });
    return response.draft_review ? { ...response.draft_review, findings: response.findings } : response;
  },
  draftArtifacts: (base: string, runId: string) =>
    apiRequest<string[]>(base, `api/v1/draft-reviews/${runId}/artifacts`),
  draftArtifact: (base: string, runId: string, artifactName: string) =>
    apiRequest<JsonValue>(base, `api/v1/draft-reviews/${runId}/artifacts/${artifactName}`),
  draftFindings: (base: string, runId: string) =>
    apiRequest<FindingRecord[]>(base, `api/v1/draft-reviews/${runId}/findings`),
  listFindings: (base: string, query?: Record<string, string | undefined>) =>
    apiRequest<FindingRecord[]>(base, "api/v1/findings", {}, query),
  getFinding: (base: string, findingId: string) =>
    apiRequest<FindingRecord>(base, `api/v1/findings/${findingId}`),
  updateFindingDecision: async (base: string, findingId: string, body: object) => {
    const response = await apiRequest<{ finding?: FindingRecord } & FindingRecord>(base, `api/v1/findings/${findingId}/review-decision`, {
      method: "PATCH",
      body: JSON.stringify(body)
    });
    return response.finding ?? response;
  },
  createReport: async (base: string, body: object) => {
    const response = await apiRequest<{ report?: ReportRecord } & ReportRecord>(base, "api/v1/reports", {
      method: "POST",
      body: JSON.stringify(body)
    });
    return response.report ?? response;
  },
  listReports: (base: string) => apiRequest<ReportRecord[]>(base, "api/v1/reports"),
  createAssistantSession: async (base: string, body: object) => {
    const response = await apiRequest<{ session?: { session_id?: string; id?: string }; session_id?: string; id?: string; [key: string]: unknown }>(base, "api/v1/assistant/sessions", {
      method: "POST",
      body: JSON.stringify(body)
    });
    return response.session ?? response;
  },
  sendAssistantMessage: async (base: string, sessionId: string, body: object) => {
    const response = await apiRequest<{ assistant_message?: AssistantMessage; retrieval_results?: SearchResult[] } & AssistantMessage>(base, `api/v1/assistant/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify(body)
    });
    return response.assistant_message
      ? { ...response.assistant_message, retrieval_results: response.retrieval_results }
      : response;
  },
  assistantMessages: (base: string, sessionId: string) =>
    apiRequest<AssistantMessage[]>(base, `api/v1/assistant/sessions/${sessionId}/messages`),
  listAdminDataTypes: (base: string) =>
    apiRequest<Record<string, string>>(base, "api/v1/admin/data/types"),
  purgeAdminData: (base: string, types: string[]) =>
    apiRequest<{ deleted?: Record<string, number>; message?: string }>(base, "api/v1/admin/data/purge", {
      method: "POST",
      body: JSON.stringify({ types })
    }),
  restoreAdminData: async (base: string, file: File) => {
    const body = new FormData();
    body.set("file", file);
    return apiRequest<{ restored?: Record<string, number>; message?: string }>(
      base,
      "api/v1/admin/data/restore",
      {
        method: "POST",
        body
      }
    );
  },
  backupAdminData: (base: string) => fetch(buildUrl(base, "api/v1/admin/data/backup")),
  backupUrl: (base: string) => buildUrl(base, "api/v1/admin/data/backup")
};
