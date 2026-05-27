import { FormEvent, ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  Check,
  ClipboardCheck,
  Database,
  Download,
  FileDown,
  FileText,
  FolderInput,
  ListChecks,
  Loader2,
  MessageSquare,
  Play,
  RefreshCw,
  Search,
  Send,
  Settings,
  ShieldAlert,
  SlidersHorizontal,
  Trash2,
  Upload,
  X
} from "lucide-react";
import { Api, ApiError, DEFAULT_API_BASE } from "./api";
import type {
  AssistantMessage,
  CorpusRecord,
  DocumentRecord,
  DraftReviewRecord,
  FindingRecord,
  ImportJobRecord,
  JsonValue,
  LegalUnitRecord,
  LocalFilesystemBrowseResponse,
  LocalFilesystemEntry,
  ReportRecord,
  RequestState,
  SearchResult,
  TraceStage
} from "./types";

type RouteId = "corpora" | "documents" | "search" | "draft-reviews" | "findings" | "reports" | "assistant" | "settings";

const routes: Array<{ id: RouteId; label: string; icon: ReactNode }> = [
  { id: "corpora", label: "Korpusi", icon: <Database size={18} /> },
  { id: "documents", label: "Dokumenti", icon: <FileText size={18} /> },
  { id: "search", label: "Pretraga", icon: <Search size={18} /> },
  { id: "draft-reviews", label: "Provera nacrta", icon: <ClipboardCheck size={18} /> },
  { id: "findings", label: "Nalazi", icon: <ListChecks size={18} /> },
  { id: "reports", label: "Izveštaji", icon: <FileDown size={18} /> },
  { id: "assistant", label: "Asistent", icon: <MessageSquare size={18} /> },
  { id: "settings", label: "Podešavanja", icon: <Settings size={18} /> }
];

const routePaths: Record<RouteId, string> = {
  corpora: "/corpora",
  documents: "/documents",
  search: "/search",
  "draft-reviews": "/draft-reviews",
  findings: "/findings",
  reports: "/reports",
  assistant: "/assistant",
  settings: "/settings"
};

function routeFromPath(pathname: string): RouteId {
  const normalized = pathname === "/" ? "/corpora" : pathname.replace(/\/+$/, "");
  const match = routes.find((route) => routePaths[route.id] === normalized);
  return match?.id ?? "corpora";
}

const artifactPhases = [
  ["source_files", "Ulazni fajlovi"],
  ["text_extraction", "Ekstrakcija teksta"],
  ["document_classification", "Klasifikacija dokumenta"],
  ["canonical_document", "Kanonski model"],
  ["legal_units", "Pravne jedinice"],
  ["references", "Reference"],
  ["resolved_references", "Razrešene reference"],
  ["indexing", "Indeksiranje"],
  ["checker_findings", "Nalazi provere"],
  ["review_report", "Izveštaj"]
];

const importPhases = [
  {
    id: "source-files",
    label: "Ulazni fajlovi",
    artifacts: ["source_file_manifest"],
    summaryKey: "source_files"
  },
  {
    id: "text-extraction",
    label: "Ekstrakcija teksta",
    artifacts: ["extracted_documents", "normalized_documents"],
    summaryKey: "extracted_documents"
  },
  {
    id: "document-classification",
    label: "Klasifikacija dokumenta",
    artifacts: ["identified_documents"],
    summaryKey: "identified_documents"
  },
  {
    id: "legal-parsing",
    label: "Parser pravne strukture",
    artifacts: ["parsed_legal_documents", "extracted_definitions"],
    summaryKey: "parsed_legal_documents"
  },
  {
    id: "canonical-model",
    label: "Kanonski model",
    artifacts: ["canonical_documents"],
    summaryKey: "canonical_documents"
  },
  {
    id: "references",
    label: "Reference",
    artifacts: ["extracted_references", "resolved_references", "reference_graph_report"],
    summaryKey: "resolved_references"
  },
  {
    id: "indexing",
    label: "Indeksiranje",
    artifacts: ["keyword_index_report", "vector_index_report", "structure_index_report"],
    summaryKey: "index_reports"
  },
  {
    id: "storage",
    label: "Smeštanje dokumenata",
    artifacts: ["stored_documents_report"],
    summaryKey: "storage_report"
  }
];

function asArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object" && Array.isArray((value as { items?: unknown }).items)) {
    return (value as { items: T[] }).items;
  }
  if (value && typeof value === "object" && Array.isArray((value as { results?: unknown }).results)) {
    return (value as { results: T[] }).results;
  }
  return [];
}

function recordId(record: { id?: string; [key: string]: unknown }, key: string) {
  return String(record[key] ?? record.id ?? "");
}

function toJson(value: unknown): JsonValue {
  if (value === undefined) return null;
  return JSON.parse(JSON.stringify(value)) as JsonValue;
}

function errorMessage(error: unknown) {
  if (error instanceof TypeError && error.message.includes("fetch")) {
    return "Backend nije dostupan. Proveri da FastAPI sluša na API bazi iz gornjeg polja.";
  }
  if (error instanceof ApiError) return `${error.message}: ${error.body || "nema tela odgovora"}`;
  if (error instanceof Error) return error.message;
  return String(error);
}

function nestedId(value: unknown, objectKey: string, idKey: string) {
  const record = value as Record<string, unknown>;
  const nested = record?.[objectKey] as Record<string, unknown> | undefined;
  return String(nested?.[idKey] ?? record?.[idKey] ?? record?.id ?? "");
}

export function buildSearchTrace(query: string, response: { results?: SearchResult[]; [key: string]: unknown }): TraceStage[] {
  const results = asArray<SearchResult>(response.results ?? response);
  return [
    { id: "query", label: "Upit", status: "done", summary: query, data: { query } },
    {
      id: "retrieval",
      label: "Hybrid retrieval",
      status: "done",
      summary: `${results.length} pogodaka iz leksičke i semantičke pretrage.`,
      data: toJson(response)
    },
    {
      id: "ranking",
      label: "Rangiranje i citati",
      status: results.length ? "done" : "warning",
      summary: results.length ? "Rezultati su spremni za pregled citata i score breakdown." : "Nema rezultata za podešavanje upita.",
      data: toJson(results.slice(0, 5))
    }
  ];
}

export function buildDraftTrace(detail: DraftReviewRecord, artifacts: string[] = [], findings: FindingRecord[] = []): TraceStage[] {
  const status = String(detail.status ?? "created");
  const names = new Set(artifacts);
  return [
    {
      id: "draft-input",
      label: "Ulaz nacrta",
      status: "done",
      summary: detail.source_uri ? `Učitan lokalni izvor: ${detail.source_uri}` : "Nacrt unet kao tekst.",
      data: toJson({ title: detail.title, source_uri: detail.source_uri, selected_corpus_id: detail.selected_corpus_id })
    },
    ...artifactPhases.map(([artifact, label]) => ({
      id: artifact,
      label,
      status: names.has(artifact) || detail.artifacts?.[artifact] ? "done" : status === "failed" ? "error" : "pending",
      summary:
        artifact === "checker_findings"
          ? `${findings.length} nalaza povezano sa proverom.`
          : names.has(artifact) || detail.artifacts?.[artifact]
            ? `Output faze je dostupan kao ${artifact}.`
            : "Faza još nema vidljiv output.",
      artifactName: artifact,
      data: toJson(detail.artifacts?.[artifact] ?? null)
    })) as TraceStage[]
  ];
}

export function ReviewDecisionControls({
  disabled,
  onDecision
}: {
  disabled?: boolean;
  onDecision: (decision: string, note: string) => void;
}) {
  const [note, setNote] = useState("");
  const decisions = [
    ["accepted", "Prihvati", <Check size={16} />],
    ["rejected", "Odbaci", <X size={16} />],
    ["partial", "Delimično", <SlidersHorizontal size={16} />],
    ["needs_expert_review", "Ekspert", <Activity size={16} />]
  ] as const;
  return (
    <div className="decision-box">
      <textarea
        aria-label="Napomena recenzenta"
        value={note}
        onChange={(event) => setNote(event.target.value)}
        placeholder="Napomena recenzenta"
      />
      <div className="button-row">
        {decisions.map(([value, label, icon]) => (
          <button key={value} type="button" disabled={disabled} onClick={() => onDecision(value, note)}>
            {icon}
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function RetrievalResultCard({ result, index }: { result: SearchResult; index: number }) {
  return (
    <article className="result-card">
      <div className="result-head">
        <strong>{result.title ?? result.citation ?? result.path ?? result.filename ?? `Rezultat ${index + 1}`}</strong>
        <span className="badge">score {formatScore(result.score)}</span>
      </div>
      <p>{result.excerpt ?? result.text ?? result.content_text ?? "Nema prikazanog citata."}</p>
      <div className="score-grid">
        <span>Leksički: {formatScore(result.lexical_score ?? result.metadata?.lexical_score)}</span>
        <span>Semantički: {formatScore(result.semantic_score ?? result.metadata?.semantic_score)}</span>
        <span>Jedinica: {result.legal_unit_id ?? "-"}</span>
      </div>
    </article>
  );
}

function formatScore(value: unknown) {
  return typeof value === "number" ? value.toFixed(3) : "-";
}

function AppShell({
  route,
  setRoute,
  children
}: {
  route: RouteId;
  setRoute: (route: RouteId) => void;
  children: ReactNode;
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">zA</span>
          <div>
            <strong>zAIkon</strong>
            <span>Pravna obrada</span>
          </div>
        </div>
        <nav aria-label="Glavna navigacija">
          {routes.map((item) => (
            <button
              key={item.id}
              type="button"
              className={item.id === route ? "nav-button active" : "nav-button"}
              onClick={() => setRoute(item.id)}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
      <main className="workspace">
        {children}
      </main>
    </div>
  );
}

function ApiStatus({ apiBase, setApiBase }: { apiBase: string; setApiBase: (value: string) => void }) {
  const [state, setState] = useState<RequestState>("idle");
  const [message, setMessage] = useState("Nije provereno");

  async function check() {
    setState("loading");
    try {
      await Api.health(apiBase);
      setMessage("API dostupan");
      setState("success");
    } catch (error) {
      setMessage(errorMessage(error));
      setState("error");
    }
  }

  useEffect(() => {
    void check();
  }, []);

  return (
    <header className="api-settings">
      <label>
        API baza
        <input value={apiBase} onChange={(event) => setApiBase(event.target.value)} />
      </label>
      <div className={`status-pill ${state}`}>
        {state === "loading" ? <Loader2 className="spin" size={16} /> : <Activity size={16} />}
        <span>{message}</span>
        <button type="button" className="icon-button" title="Proveri API" onClick={check}>
          <RefreshCw size={16} />
        </button>
      </div>
    </header>
  );
}

function PageHeader({ title, subtitle, icon }: { title: string; subtitle: string; icon: ReactNode }) {
  return (
    <div className="page-header">
      <div className="page-title">
        {icon}
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>
    </div>
  );
}

function TracePanel({
  stages,
  onArtifactOpen
}: {
  stages: TraceStage[];
  onArtifactOpen?: (artifactName: string) => void;
}) {
  return (
    <section className="trace-panel" aria-label="Trag obrade">
      <div className="section-head">
        <div>
          <h2>Trag obrade</h2>
          <p>Jedan dokument ili upit kroz faze, output i tačku za podešavanje.</p>
        </div>
      </div>
      {stages.length === 0 ? (
        <EmptyState text="Pokreni import, pretragu ili proveru da bi se prikazao trag obrade." />
      ) : (
        <ol className="trace-list">
          {stages.map((stage, index) => (
            <li key={stage.id} className={`trace-stage ${stage.status}`}>
              <span className="trace-index">{index + 1}</span>
              <div>
                <div className="trace-title">
                  <strong>{stage.label}</strong>
                  <span className="badge">{stage.status}</span>
                </div>
                <p>{stage.summary}</p>
                {stage.artifactName ? (
                  <button type="button" className="link-button" onClick={() => onArtifactOpen?.(stage.artifactName!)}>
                    Učitaj i prikaži output faze
                  </button>
                ) : null}
                <ArtifactPreview value={stage.data} />
                {stage.data ? <JsonPreview value={stage.data} label="Debug JSON" /> : null}
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function ArtifactPreview({ value }: { value: unknown }) {
  const record = value as { name?: string; artifact_type?: string; payload?: unknown } | null;
  if (!record || typeof record !== "object" || !("payload" in record)) return null;
  const payload = record.payload;
  const items = Array.isArray(payload) ? payload : [];
  const first = items[0] as Record<string, unknown> | undefined;
  const text = String(first?.content_text ?? first?.title ?? first?.filename ?? "");
  return (
    <div className="artifact-preview">
      <strong>{record.name ?? record.artifact_type ?? "Artefakt"}</strong>
      <span>{Array.isArray(payload) ? `${payload.length} stavki` : "objekat"}</span>
      {text ? <p>{text.slice(0, 420)}</p> : null}
    </div>
  );
}

function JsonPreview({ value, label = "JSON" }: { value: JsonValue | unknown; label?: string }) {
  return (
    <details className="json-preview">
      <summary>{label}</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="empty-state">{text}</div>;
}

function CorpusPicker({
  corpora,
  selectedCorpusId,
  onSelect
}: {
  corpora: CorpusRecord[];
  selectedCorpusId: string;
  onSelect: (corpusId: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [sortBy, setSortBy] = useState("newest");
  const pageSize = 10;
  const duplicateNames = useMemo(() => {
    const counts = new Map<string, number>();
    corpora.forEach((corpus) => {
      const name = String(corpus.name ?? "").trim().toLowerCase();
      if (name) counts.set(name, (counts.get(name) ?? 0) + 1);
    });
    return counts;
  }, [corpora]);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const matches = !normalized ? corpora : corpora.filter((corpus) => {
      const id = recordId(corpus, "corpus_id").toLowerCase();
      const name = String(corpus.name ?? "").toLowerCase();
      return id.includes(normalized) || name.includes(normalized);
    });
    return [...matches].sort((left, right) => compareCorpora(left, right, sortBy));
  }, [corpora, query, sortBy]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const visible = filtered.slice(safePage * pageSize, safePage * pageSize + pageSize);

  useEffect(() => {
    setPage(0);
  }, [query, sortBy, corpora.length]);

  return (
    <div className="picker">
      <div className="picker-controls">
        <label>
          Pretraga korpusa
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Naziv ili corpus_id"
          />
        </label>
        <label>
          Sortiraj po
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="newest">Najnovije prvo</option>
            <option value="oldest">Najstarije prvo</option>
            <option value="name-asc">Naziv A-Z</option>
            <option value="name-desc">Naziv Z-A</option>
          </select>
        </label>
      </div>
      <div className="picker-meta">
        <span>{filtered.length} rezultata</span>
        <span>Strana {safePage + 1}/{pageCount}</span>
      </div>
      {visible.length ? (
        <div className="corpus-table compact-list" role="table" aria-label="Lista korpusa">
          <div className="corpus-row corpus-head" role="row">
            <span role="columnheader">Ime</span>
            <span role="columnheader">Datum kreiranja</span>
            <span role="columnheader">Status</span>
          </div>
          {visible.map((corpus) => {
            const id = recordId(corpus, "corpus_id");
            const isActive = id === selectedCorpusId;
            const name = String(corpus.name ?? "").trim();
            const isDuplicate = Boolean(name && (duplicateNames.get(name.toLowerCase()) ?? 0) > 1);
            return (
              <button
                key={id}
                type="button"
                className={isActive ? "corpus-row active" : "corpus-row"}
                onClick={() => onSelect(id)}
                role="row"
                title={`corpus_id: ${id}`}
                aria-label={`${name || "Korpus bez imena"}, kreiran ${formatDate(corpus.created_at)}, corpus_id ${id}`}
              >
                <strong role="cell">
                  {name || "-"}
                  {isDuplicate ? <span className="duplicate-badge">isti naziv</span> : null}
                </strong>
                <span role="cell">{formatDate(corpus.created_at)}</span>
                <span role="cell">{String(corpus.status ?? "active")}</span>
              </button>
            );
          })}
        </div>
      ) : (
        <EmptyState text="Nema korpusa za zadatu pretragu." />
      )}
      <div className="pager">
        <button type="button" disabled={safePage === 0} onClick={() => setPage((current) => Math.max(0, current - 1))}>
          Prethodna
        </button>
        <button type="button" disabled={safePage >= pageCount - 1} onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))}>
          Sledeća
        </button>
      </div>
    </div>
  );
}

function CorpusChoice({
  corpora,
  selectedCorpusId,
  onSelect,
  inputName,
  label,
  allowEmpty = false
}: {
  corpora: CorpusRecord[];
  selectedCorpusId: string;
  onSelect: (corpusId: string) => void;
  inputName: string;
  label: string;
  allowEmpty?: boolean;
}) {
  const selectedCorpus = useMemo(
    () => corpora.find((corpus) => recordId(corpus, "corpus_id") === selectedCorpusId),
    [corpora, selectedCorpusId]
  );
  return (
    <div className="corpus-choice">
      <input type="hidden" name={inputName} value={selectedCorpusId} />
      <div className="section-head">
        <div>
          <h2>{label}</h2>
          <p>{selectedCorpusId || "Korpus nije izabran"}</p>
        </div>
        {allowEmpty ? (
          <button type="button" onClick={() => onSelect("")}>
            Bez korpusa
          </button>
        ) : null}
      </div>
      {selectedCorpus ? (
        <SelectedCorpusSummary corpus={selectedCorpus} corpusId={selectedCorpusId} />
      ) : null}
      {corpora.length ? (
        <CorpusPicker corpora={corpora} selectedCorpusId={selectedCorpusId} onSelect={onSelect} />
      ) : (
        <EmptyState text="Nema učitanih korpusa." />
      )}
    </div>
  );
}

function SelectedCorpusSummary({ corpus, corpusId }: { corpus: CorpusRecord; corpusId: string }) {
  return (
    <div className="selected-corpus-summary">
      <span>
        <strong>Ime</strong>
        {corpus.name ?? "-"}
      </span>
      <span>
        <strong>Status</strong>
        {String(corpus.status ?? "active")}
      </span>
      <span>
        <strong>ID</strong>
        {corpusId}
      </span>
    </div>
  );
}

function formatDate(value: unknown) {
  if (!value) return "-";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("sr-Latn-RS", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(date);
}

function compareCorpora(left: CorpusRecord, right: CorpusRecord, sortBy: string) {
  const leftName = String(left.name ?? "").localeCompare(String(right.name ?? ""), "sr-Latn");
  const leftDate = Date.parse(String(left.created_at ?? "")) || 0;
  const rightDate = Date.parse(String(right.created_at ?? "")) || 0;
  if (sortBy === "oldest") return leftDate - rightDate;
  if (sortBy === "name-asc") return leftName;
  if (sortBy === "name-desc") return -leftName;
  return rightDate - leftDate;
}

function ErrorBox({ message }: { message?: string }) {
  if (!message) return null;
  return <div className="error-box">{message}</div>;
}

function LoadingButton({ loading, children }: { loading: boolean; children: ReactNode }) {
  return (
    <button type="submit" disabled={loading}>
      {loading ? <Loader2 className="spin" size={16} /> : null}
      {children}
    </button>
  );
}

function PathPicker({
  apiBase,
  name,
  label,
  mode,
  placeholder,
  required
}: {
  apiBase: string;
  name: string;
  label: string;
  mode: "folder" | "file";
  placeholder?: string;
  required?: boolean;
}) {
  const [value, setValue] = useState("");
  const [open, setOpen] = useState(false);
  const [browserState, setBrowserState] = useState<LocalFilesystemBrowseResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadRoots() {
    setLoading(true);
    setError("");
    try {
      setBrowserState(await Api.localRoots(apiBase));
      setOpen(true);
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function browse(path: string) {
    setLoading(true);
    setError("");
    try {
      setBrowserState(await Api.browseLocalPath(apiBase, path, mode));
      setOpen(true);
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  function choose(entry: LocalFilesystemEntry) {
    if (entry.is_dir) {
      if (mode === "folder") {
        setValue(entry.path);
      }
      void browse(entry.path);
      return;
    }
    setValue(entry.path);
    setOpen(false);
  }

  return (
    <div className="path-picker">
      <label>
        {label}
        <div className="path-input-row">
          <input
            name={name}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder={placeholder}
            required={required}
          />
          <button type="button" onClick={() => (open ? setOpen(false) : loadRoots())}>
            <FolderInput size={16} />
            Browse
          </button>
        </div>
      </label>
      <ErrorBox message={error} />
      {open ? (
        <div className="filesystem-browser">
          <div className="section-head">
            <div>
              <h3>{browserState?.current_path || "Root"}</h3>
              <p>{mode === "folder" ? "Izaberi folder ili uđi u podfolder." : "Izaberi fajl ili uđi u folder."}</p>
            </div>
            <div className="button-row">
              {browserState?.parent_path ? (
                <button type="button" onClick={() => browse(browserState.parent_path!)}>
                  ..
                </button>
              ) : null}
              {mode === "folder" && browserState?.current_path ? (
                <button type="button" onClick={() => { setValue(browserState.current_path); setOpen(false); }}>
                  Izaberi ovaj folder
                </button>
              ) : null}
            </div>
          </div>
          {loading ? <EmptyState text="Učitavam..." /> : null}
          <div className="filesystem-list">
            {(browserState?.entries ?? []).map((entry) => (
              <button key={entry.path} type="button" onClick={() => choose(entry)}>
                <span>{entry.is_dir ? "Folder" : "Fajl"}</span>
                <strong>{entry.name}</strong>
                <small>{entry.is_dir ? entry.path : `${formatBytes(entry.size_bytes)} · ${entry.path}`}</small>
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function formatBytes(value: number | null | undefined) {
  if (!value) return "0 B";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function CorporaPage({ apiBase }: { apiBase: string }) {
  const [corpora, setCorpora] = useState<CorpusRecord[]>([]);
  const [importJobs, setImportJobs] = useState<ImportJobRecord[]>([]);
  const [selectedCorpusId, setSelectedCorpusId] = useState("");
  const [state, setState] = useState<RequestState>("idle");
  const [error, setError] = useState("");
  const [report, setReport] = useState<JsonValue | null>(null);
  const [trace, setTrace] = useState<TraceStage[]>([]);
  const [artifactOutput, setArtifactOutput] = useState<JsonValue | null>(null);
  const [jobId, setJobId] = useState("");

  async function loadCorpora() {
    setState("loading");
    setError("");
    try {
      const result = asArray<CorpusRecord>(await Api.listCorpora(apiBase));
      setCorpora(result);
      setSelectedCorpusId((current) => current || recordId(result[0] ?? {}, "corpus_id"));
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  useEffect(() => {
    void loadCorpora();
  }, [apiBase]);

  async function createCorpus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      await Api.createCorpus(apiBase, {
        name: form.get("name"),
        description: form.get("description")
      });
      await loadCorpora();
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  async function importFolder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    setError("");
    setReport(null);
    setArtifactOutput(null);
    const form = new FormData(event.currentTarget);
    try {
      const response = await Api.importFolder(apiBase, String(form.get("corpus_id")), {
        corpus_id: form.get("corpus_id"),
        folder_uri: form.get("folder_uri")
      });
      const id = nestedId(response, "import_job", "import_job_id");
      setJobId(id);
      const artifacts = id ? await Api.importJobArtifacts(apiBase, id).catch(() => []) : [];
      const nextReport = id ? await Api.importJobReport(apiBase, id).catch(() => (response as { report?: unknown }).report ?? response) : (response as { report?: unknown }).report ?? response;
      setReport(toJson(nextReport));
      setTrace(buildImportTrace(response, nextReport, artifacts));
      await loadImportJobs(String(form.get("corpus_id")));
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  async function loadImportJobs(corpusId = selectedCorpusId) {
    if (!corpusId) return;
    setError("");
    try {
      setImportJobs(asArray<ImportJobRecord>(await Api.listImportJobs(apiBase, corpusId)));
    } catch (error) {
      setError(errorMessage(error));
    }
  }

  async function loadImportJob(job: ImportJobRecord) {
    const id = recordId(job, "import_job_id");
    if (!id) return;
    setState("loading");
    setError("");
    setArtifactOutput(null);
    try {
      const [nextReport, artifacts] = await Promise.all([
        Api.importJobReport(apiBase, id),
        Api.importJobArtifacts(apiBase, id).catch(() => [])
      ]);
      setJobId(id);
      setReport(toJson(nextReport));
      setTrace(buildImportTrace({ import_job: job, report: nextReport }, nextReport, artifacts));
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  async function openArtifact(name: string) {
    if (!jobId) return;
    setError("");
    try {
      const output = await Api.importJobArtifact(apiBase, jobId, name);
      setArtifactOutput(output);
      setTrace((current) =>
        current.map((stage) =>
          stage.artifactName === name
            ? {
                ...stage,
                status: "done",
                summary: `Output faze je učitan iz artefakta ${name}.`,
                data: toJson(output)
              }
            : stage
        )
      );
    } catch (error) {
      setError(errorMessage(error));
    }
  }

  return (
    <>
      <PageHeader title="Korpusi" subtitle="Uvoz lokalnih foldera i pregled reporta import pipeline-a." icon={<Database size={24} />} />
      <div className="content-grid two">
        <section className="panel">
          <div className="section-head">
            <h2>Lista korpusa</h2>
            <button type="button" onClick={loadCorpora}>
              <RefreshCw size={16} />
              Osveži
            </button>
          </div>
          <ErrorBox message={error} />
          {corpora.length ? (
            <CorpusPicker corpora={corpora} selectedCorpusId={selectedCorpusId} onSelect={setSelectedCorpusId} />
          ) : (
            <EmptyState text="Nema učitanih korpusa." />
          )}
          <form onSubmit={createCorpus} className="form-grid">
            <label>
              Naziv
              <input name="name" defaultValue="Šumarstvo" required />
            </label>
            <label>
              Opis
              <input name="description" placeholder="Interni korpus propisa" />
            </label>
            <LoadingButton loading={state === "loading"}>Kreiraj korpus</LoadingButton>
          </form>
        </section>
        <section className="panel">
          <div className="section-head">
            <h2>Import foldera</h2>
            <FolderInput size={18} />
          </div>
          <form onSubmit={importFolder} className="form-grid">
            <input type="hidden" name="corpus_id" value={selectedCorpusId} />
            <PathPicker
              apiBase={apiBase}
              name="folder_uri"
              label="Lokalni folder"
              mode="folder"
              placeholder="D:\\POSAO\\OllamaProjects\\ZAIKON\\DOCUMENTS\\šumarstvo"
              required
            />
            <LoadingButton loading={state === "loading"}>Pokreni import</LoadingButton>
          </form>
          <ErrorBox message={error} />
          {report ? <JsonPreview value={report} label="Import report" /> : null}
          {artifactOutput ? <JsonPreview value={artifactOutput} label="Output artefakta" /> : null}
        </section>
      </div>
      <section className="panel">
        <div className="section-head">
          <h2>Import poslovi</h2>
          <button type="button" onClick={() => loadImportJobs()}>
            <RefreshCw size={16} />
            Učitaj poslove
          </button>
        </div>
        {importJobs.length ? (
          <div className="list">
            {importJobs.map((job) => {
              const id = recordId(job, "import_job_id");
              return (
                <button key={id} type="button" className={id === jobId ? "list-item active" : "list-item"} onClick={() => loadImportJob(job)}>
                  <strong>{job.status ?? "import"} · {job.supported_files ?? 0}/{job.total_files ?? 0} fajlova</strong>
                  <span>{id}</span>
                </button>
              );
            })}
          </div>
        ) : (
          <EmptyState text="Izaberi korpus i učitaj import poslove, ili pokreni novi import." />
        )}
      </section>
      <TracePanel stages={trace} onArtifactOpen={openArtifact} />
    </>
  );
}

function buildImportTrace(response: unknown, report: unknown, artifacts: string[]): TraceStage[] {
  const reportRecord = report as { summary?: Record<string, unknown>; artifact_names?: string[]; index_reports?: unknown; storage_report?: unknown };
  const artifactSet = new Set([...(artifacts ?? []), ...(reportRecord.artifact_names ?? [])]);
  const summary = reportRecord.summary ?? {};
  return [
    { id: "folder", label: "Folder i fajlovi", status: "done", summary: "Backend je primio folder i pokrenuo import posao.", data: toJson(response) },
    ...importPhases.map((phase) => {
      const availableArtifacts = phase.artifacts.filter((artifact) => artifactSet.has(artifact));
      const summaryValue =
        phase.summaryKey === "index_reports"
          ? reportRecord.index_reports
          : phase.summaryKey === "storage_report"
            ? reportRecord.storage_report
            : phase.summaryKey === "source_files"
              ? (report as { source_files?: unknown }).source_files ?? summary
              : summary[phase.summaryKey];
      return {
        id: phase.id,
        label: phase.label,
        status: availableArtifacts.length ? "done" : summaryValue ? "done" : "warning",
        summary: availableArtifacts.length
          ? `Output faze: ${availableArtifacts.join(", ")}.`
          : summaryValue
            ? "Faza ima podatke u import reportu."
            : "Nema outputa za ovu fazu u odgovoru.",
        artifactName: availableArtifacts[0],
        data: toJson({ summary: summaryValue ?? null, artifacts: availableArtifacts })
      } satisfies TraceStage;
    }),
    {
      id: "report",
      label: "Import report",
      status: "done",
      summary: "Sažetak import posla za tuning parsera, klasifikacije i indeksa.",
      artifactName: artifactSet.has("import_report") ? "import_report" : undefined,
      data: toJson(report)
    }
  ];
}

function DocumentsPage({ apiBase }: { apiBase: string }) {
  const [corpusId, setCorpusId] = useState("");
  const [corpora, setCorpora] = useState<CorpusRecord[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selected, setSelected] = useState<DocumentRecord | null>(null);
  const [state, setState] = useState<RequestState>("idle");
  const [error, setError] = useState("");

  async function loadCorporaForDocuments() {
    setError("");
    try {
      const result = asArray<CorpusRecord>(await Api.listCorpora(apiBase));
      setCorpora(result);
      setCorpusId((current) => current || recordId(result[0] ?? {}, "corpus_id"));
    } catch (error) {
      setError(errorMessage(error));
    }
  }

  useEffect(() => {
    void loadCorporaForDocuments();
  }, [apiBase]);

  async function loadDocuments(event?: FormEvent) {
    event?.preventDefault();
    setState("loading");
    setError("");
    try {
      const result = asArray<DocumentRecord>(await Api.listDocuments(apiBase, corpusId || undefined));
      setDocuments(result);
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  async function openDocument(document: DocumentRecord) {
    const id = recordId(document, "document_id");
    if (!id) return;
    setState("loading");
    try {
      setSelected(await Api.getDocument(apiBase, id));
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  const trace = useMemo(() => (selected ? buildDocumentTrace(selected) : []), [selected]);
  const selectedCorpus = useMemo(() => corpora.find((corpus) => recordId(corpus, "corpus_id") === corpusId), [corpora, corpusId]);

  return (
    <>
      <PageHeader title="Dokumenti" subtitle="Pregled propisa i drugih dokumenata bez oslanjanja na filename." icon={<FileText size={24} />} />
      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Izbor korpusa</h2>
            <p>{corpusId || "Nijedan korpus nije izabran"}</p>
          </div>
          <button type="button" onClick={loadCorporaForDocuments}>
            <RefreshCw size={16} />
            Osveži korpuse
          </button>
        </div>
        {selectedCorpus ? (
          <SelectedCorpusSummary corpus={selectedCorpus} corpusId={corpusId} />
        ) : null}
        {corpora.length ? (
          <CorpusPicker corpora={corpora} selectedCorpusId={corpusId} onSelect={setCorpusId} />
        ) : (
          <EmptyState text="Nema učitanih korpusa." />
        )}
        <form onSubmit={loadDocuments} className="toolbar">
          <LoadingButton loading={state === "loading"}>Učitaj dokumente iz izabranog korpusa</LoadingButton>
        </form>
        <ErrorBox message={error} />
        <div className="master-detail documents-master-detail">
          <div className="list">
            {documents.length ? documents.map((document) => {
              const id = recordId(document, "document_id");
              const selectedId = selected ? recordId(selected, "document_id") : "";
              return (
                <button
                  key={id}
                  type="button"
                  className={id === selectedId ? "list-item active" : "list-item"}
                  onClick={() => openDocument(document)}
                >
                  <strong>{document.title ?? id}</strong>
                  <span>{document.document_type ?? document.type ?? "neklasifikovano"}</span>
                </button>
              );
            }) : <EmptyState text="Učitaj listu dokumenata." />}
          </div>
          <DocumentDetail document={selected} apiBase={apiBase} />
        </div>
      </section>
      <TracePanel stages={trace} />
    </>
  );
}

function buildDocumentTrace(document: DocumentRecord): TraceStage[] {
  const units = document.legal_units ?? [];
  return [
    { id: "classification", label: "Klasifikacija", status: document.document_type || document.type ? "done" : "warning", summary: String(document.document_type ?? document.type ?? "Tip nije određen."), data: toJson(document) },
    { id: "canonical", label: "Kanonski model", status: document.canonical_json ? "done" : "warning", summary: document.canonical_json ? "Kanonski JSON je dostupan." : "Kanonski JSON nije vraćen u detalju.", data: toJson(document.canonical_json ?? null) },
    { id: "units", label: "Pravne jedinice", status: units.length ? "done" : "warning", summary: `${units.length} jedinica u stablu dokumenta.`, data: toJson(units) },
    { id: "akoma", label: "Akoma Ntoso", status: "done", summary: "Export link je dostupan iz detalja dokumenta." }
  ];
}

function DocumentDetail({ document, apiBase }: { document: DocumentRecord | null; apiBase: string }) {
  if (!document) return <EmptyState text="Izaberi dokument za detalj." />;
  const id = recordId(document, "document_id");
  return (
    <div className="detail-pane">
      <div className="section-head">
        <div>
          <h2>{document.title ?? id}</h2>
          <p>{document.document_type ?? document.type ?? "Tip nije određen"}</p>
        </div>
        {id ? (
          <a className="button-link" href={`${apiBase}/api/v1/documents/${id}/akoma-ntoso`} target="_blank" rel="noreferrer">
            <Download size={16} />
            Akoma
          </a>
        ) : null}
      </div>
      <LegalUnitTree units={document.legal_units ?? []} />
      <JsonPreview value={toJson(document)} label="Detalj dokumenta" />
    </div>
  );
}

function LegalUnitTree({ units }: { units: LegalUnitRecord[] }) {
  if (!units.length) return <EmptyState text="Nema pravnih jedinica u odgovoru." />;
  return (
    <ul className="unit-tree">
      {units.map((unit) => (
        <li key={recordId(unit, "legal_unit_id") || unit.label}>
          <strong>{unit.label ?? unit.title ?? unit.unit_type}</strong>
          {unit.text ? <p>{unit.text}</p> : null}
          {unit.children?.length ? <LegalUnitTree units={unit.children} /> : null}
        </li>
      ))}
    </ul>
  );
}

function SearchPage({ apiBase }: { apiBase: string }) {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [trace, setTrace] = useState<TraceStage[]>([]);
  const [corpora, setCorpora] = useState<CorpusRecord[]>([]);
  const [selectedCorpusId, setSelectedCorpusId] = useState("");
  const [state, setState] = useState<RequestState>("idle");
  const [error, setError] = useState("");

  async function loadCorporaForSearch() {
    setError("");
    try {
      setCorpora(asArray<CorpusRecord>(await Api.listCorpora(apiBase)));
    } catch (error) {
      setError(errorMessage(error));
    }
  }

  useEffect(() => {
    void loadCorporaForSearch();
  }, [apiBase]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    setError("");
    const form = new FormData(event.currentTarget);
    const query = String(form.get("query") ?? "");
    try {
      const response = await Api.hybridSearch(apiBase, {
        query,
        corpus_id: String(form.get("corpus_id") ?? "") || undefined,
        top_k: Number(form.get("top_k") ?? 10)
      });
      const nextResults = asArray<SearchResult>(response.results ?? response);
      setResults(nextResults);
      setTrace(buildSearchTrace(query, response));
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  return (
    <>
      <PageHeader title="Pretraga" subtitle="Hybrid retrieval sa citatima i score breakdown-om." icon={<Search size={24} />} />
      <section className="panel">
        <form onSubmit={submit} className="search-form">
          <label>
            Upit
            <input name="query" defaultValue="šume evidencija" required />
          </label>
          <label>
            top_k
            <input name="top_k" type="number" min="1" max="50" defaultValue="10" />
          </label>
          <input type="hidden" name="corpus_id" value={selectedCorpusId} />
          <LoadingButton loading={state === "loading"}>Pretraži</LoadingButton>
        </form>
        <CorpusChoice
          corpora={corpora}
          selectedCorpusId={selectedCorpusId}
          onSelect={setSelectedCorpusId}
          inputName="corpus_id_picker"
          label="Korpus za pretragu"
          allowEmpty
        />
        <ErrorBox message={error} />
        <div className="results-grid">
          {results.length ? results.map((result, index) => <RetrievalResultCard key={`${result.legal_unit_id ?? index}`} result={result} index={index} />) : <EmptyState text="Nema rezultata za prikaz." />}
        </div>
      </section>
      <TracePanel stages={trace} />
    </>
  );
}

function DraftReviewsPage({ apiBase }: { apiBase: string }) {
  const [reviews, setReviews] = useState<DraftReviewRecord[]>([]);
  const [selected, setSelected] = useState<DraftReviewRecord | null>(null);
  const [corpora, setCorpora] = useState<CorpusRecord[]>([]);
  const [selectedCorpusId, setSelectedCorpusId] = useState("");
  const [findings, setFindings] = useState<FindingRecord[]>([]);
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [artifactOutput, setArtifactOutput] = useState<JsonValue | null>(null);
  const [state, setState] = useState<RequestState>("idle");
  const [runMessage, setRunMessage] = useState("");
  const [error, setError] = useState("");

  async function loadReviews() {
    setState("loading");
    setError("");
    try {
      setReviews(asArray<DraftReviewRecord>(await Api.listDraftReviews(apiBase)));
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  async function loadCorporaForDrafts() {
    setError("");
    try {
      const result = asArray<CorpusRecord>(await Api.listCorpora(apiBase));
      setCorpora(result);
      setSelectedCorpusId((current) => current || recordId(result[0] ?? {}, "corpus_id"));
    } catch (error) {
      setError(errorMessage(error));
    }
  }

  useEffect(() => {
    void loadReviews();
    void loadCorporaForDrafts();
  }, [apiBase]);

  async function createReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    setError("");
    setRunMessage("Kreiram proveru nacrta...");
    setArtifactOutput(null);
    const form = new FormData(event.currentTarget);
    try {
      const response = await Api.createDraftReview(apiBase, {
        title: form.get("title"),
        content_text: form.get("content_text"),
        selected_corpus_id: form.get("selected_corpus_id") || undefined
      });
      const runId = recordId(response, "pipeline_run_id");
      setSelected(response);
      setRunMessage("Provera je kreirana. Pokrećem analizu nacrta...");
      await Api.runDraftReview(apiBase, runId);
      setRunMessage("Analiza je završena. Učitavam nalaze i artefakte...");
      await hydrateReview(runId);
      await loadReviews();
      setRunMessage("Provera je završena.");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
      setRunMessage("");
    }
  }

  async function createFromFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    setError("");
    setRunMessage("Učitavam fajl i kreiram proveru nacrta...");
    setArtifactOutput(null);
    const form = new FormData(event.currentTarget);
    try {
      const response = await Api.createDraftReviewFromFile(apiBase, {
        title: form.get("title"),
        source_uri: form.get("source_uri"),
        selected_corpus_id: form.get("selected_corpus_id") || undefined,
        file_type: form.get("file_type") || undefined
      });
      const runId = recordId(response, "pipeline_run_id");
      setSelected(response);
      setRunMessage("Provera je kreirana. Pokrećem analizu nacrta...");
      await Api.runDraftReview(apiBase, runId);
      setRunMessage("Analiza je završena. Učitavam nalaze i artefakte...");
      await hydrateReview(runId);
      await loadReviews();
      setRunMessage("Provera je završena.");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
      setRunMessage("");
    }
  }

  async function hydrateReview(runId: string) {
    if (!runId) return;
    const [detail, nextArtifacts, nextFindings] = await Promise.all([
      Api.getDraftReview(apiBase, runId),
      Api.draftArtifacts(apiBase, runId).catch(() => []),
      Api.draftFindings(apiBase, runId).catch(() => [])
    ]);
    setSelected(detail);
    setArtifacts(nextArtifacts);
    setFindings(nextFindings);
    setState("success");
  }

  async function runSelected() {
    if (!selected) return;
    setState("loading");
    setError("");
    setRunMessage("Pokrećem analizu nacrta...");
    setArtifactOutput(null);
    try {
      const id = recordId(selected, "pipeline_run_id");
      await Api.runDraftReview(apiBase, id);
      setRunMessage("Analiza je završena. Učitavam nalaze i artefakte...");
      await hydrateReview(id);
      await loadReviews();
      setRunMessage("Provera je završena.");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
      setRunMessage("");
    }
  }

  async function openArtifact(name: string) {
    if (!selected) return;
    setArtifactOutput(await Api.draftArtifact(apiBase, recordId(selected, "pipeline_run_id"), name));
  }

  const trace = useMemo(() => (selected ? buildDraftTrace(selected, artifacts, findings) : []), [selected, artifacts, findings]);

  return (
    <>
      <PageHeader title="Provera nacrta" subtitle="Jedan nacrt prati se od ulaza, preko ekstrakcije, do nalaza i artefakata." icon={<ClipboardCheck size={24} />} />
      <section className="panel">
        <CorpusChoice
          corpora={corpora}
          selectedCorpusId={selectedCorpusId}
          onSelect={setSelectedCorpusId}
          inputName="selected_corpus_id_picker"
          label="Korpus za proveru nacrta"
        />
      </section>
      <div className="content-grid two">
        <section className="panel">
          <div className="section-head">
            <h2>Novi nacrt iz teksta</h2>
          </div>
          <form onSubmit={createReview} className="form-grid">
            <label>
              Naslov
              <input name="title" defaultValue="Nacrt" required />
            </label>
            <input type="hidden" name="selected_corpus_id" value={selectedCorpusId} />
            <label>
              Tekst
              <textarea name="content_text" defaultValue={"NACRT\n\nČlan 1.\nPostupak se sprovodi u skladu sa članom 2. Zakona o šumama."} required />
            </label>
            <LoadingButton loading={state === "loading"}>Kreiraj i pokreni proveru</LoadingButton>
          </form>
        </section>
        <section className="panel">
          <div className="section-head">
            <h2>Novi nacrt iz fajla</h2>
          </div>
          <form onSubmit={createFromFile} className="form-grid">
            <label>
              Naslov
              <input name="title" defaultValue="Nacrt iz fajla" required />
            </label>
            <input type="hidden" name="selected_corpus_id" value={selectedCorpusId} />
            <PathPicker
              apiBase={apiBase}
              name="source_uri"
              label="source_uri"
              mode="file"
              placeholder="C:\\putanja\\nacrt.docx"
              required
            />
            <label>
              Tip fajla
              <select name="file_type" defaultValue="">
                <option value="">Auto</option>
                <option value="docx">DOCX</option>
                <option value="pdf">PDF</option>
                <option value="txt">TXT</option>
              </select>
            </label>
            <LoadingButton loading={state === "loading"}>Kreiraj iz fajla i pokreni</LoadingButton>
          </form>
        </section>
      </div>
      {state === "loading" && runMessage ? (
        <div className="progress-panel" aria-live="polite">
          <div className="progress-meta">
            <strong>{runMessage}</strong>
            <span>Molim sačekaj...</span>
          </div>
          <div className="progress-track indeterminate">
            <span />
          </div>
        </div>
      ) : null}
      <section className="panel">
        <div className="section-head">
          <h2>Pokretanja</h2>
          <button type="button" onClick={loadReviews} disabled={state === "loading"}>
            <RefreshCw size={16} />
            Osveži
          </button>
        </div>
        <ErrorBox message={error} />
        <div className="master-detail">
          <div className="list">
            {reviews.length ? reviews.map((review) => {
              const id = recordId(review, "pipeline_run_id");
              return (
                <button key={id} type="button" className="list-item" disabled={state === "loading"} onClick={() => hydrateReview(id)}>
                  <strong>{review.title ?? id}</strong>
                  <span>{review.status ?? "created"}</span>
                </button>
              );
            }) : <EmptyState text="Nema pokretanja." />}
          </div>
          <div className="detail-pane">
            {selected ? (
              <>
                <div className="section-head">
                  <div>
                    <h2>{selected.title ?? recordId(selected, "pipeline_run_id")}</h2>
                    <p>{selected.status ?? "created"}</p>
                  </div>
                  <div className="button-row">
                    <button type="button" onClick={runSelected} disabled={state === "loading"}>
                      {state === "loading" ? <Loader2 className="spin" size={16} /> : <Play size={16} />}
                      Ponovo pokreni
                    </button>
                    <a className="button-link" href={`${apiBase}/api/v1/draft-reviews/${recordId(selected, "pipeline_run_id")}/akoma-ntoso`} target="_blank" rel="noreferrer">
                      <Download size={16} />
                      Akoma
                    </a>
                  </div>
                </div>
                <ArtifactTabs artifacts={artifacts} onOpen={openArtifact} />
                {artifactOutput ? <JsonPreview value={artifactOutput} label="Output artefakta" /> : null}
                <FindingsMiniList findings={findings} />
              </>
            ) : (
              <EmptyState text="Izaberi pokretanje provere." />
            )}
          </div>
        </div>
      </section>
      <TracePanel stages={trace} onArtifactOpen={openArtifact} />
    </>
  );
}

function ArtifactTabs({ artifacts, onOpen }: { artifacts: string[]; onOpen: (artifact: string) => void }) {
  if (!artifacts.length) return <EmptyState text="Nema artefakata za ovo pokretanje." />;
  return (
    <div className="artifact-tabs">
      {artifacts.map((artifact) => (
        <button key={artifact} type="button" onClick={() => onOpen(artifact)}>
          {artifact}
        </button>
      ))}
    </div>
  );
}

function FindingsMiniList({ findings }: { findings: FindingRecord[] }) {
  return (
    <div className="mini-list">
      <h3>Nalazi</h3>
      {findings.length ? findings.map((finding) => (
        <div key={recordId(finding, "finding_id")} className="mini-row">
          <div className="finding-head">
            <strong>{finding.title ?? finding.category ?? "Nalaz"}</strong>
            <span className="badge">{finding.risk_level ?? finding.severity ?? finding.status ?? "-"}</span>
          </div>
          {finding.explanation || finding.message ? <p>{finding.explanation ?? finding.message}</p> : null}
          {finding.recommendation ? <p><strong>Preporuka:</strong> {finding.recommendation}</p> : null}
          <FindingEvidence finding={finding} />
        </div>
      )) : <EmptyState text="Nema nalaza za ovo pokretanje." />}
    </div>
  );
}

function FindingEvidence({ finding }: { finding: FindingRecord }) {
  const evidence = finding.evidence as Record<string, unknown> | undefined;
  if (!evidence) return null;
  const conflicts = asArray<Record<string, unknown>>(evidence.corpus_conflicts);
  const relatedUnits = conflicts.length ? conflicts : asArray<Record<string, unknown>>(evidence.related_legal_units);
  return (
    <div className="finding-evidence">
      {typeof evidence.draft_quote === "string" ? (
        <blockquote>
          <strong>Nacrt:</strong> {evidence.draft_quote}
        </blockquote>
      ) : null}
      {relatedUnits.length ? (
        <div className="evidence-list">
          <strong>Relevantno iz korpusa:</strong>
          {relatedUnits.slice(0, 3).map((unit, index) => (
            <blockquote key={`${unit.legal_unit_id ?? index}`}>
              {unit.path ? <span>{String(unit.path)}</span> : null}
              {unit.quote ? String(unit.quote) : String(unit.content_text ?? "")}
            </blockquote>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function FindingsPage({ apiBase }: { apiBase: string }) {
  const [findings, setFindings] = useState<FindingRecord[]>([]);
  const [selected, setSelected] = useState<FindingRecord | null>(null);
  const [page, setPage] = useState(0);
  const [state, setState] = useState<RequestState>("idle");
  const [error, setError] = useState("");
  const pageSize = 10;
  const pageCount = Math.max(1, Math.ceil(findings.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const visibleFindings = findings.slice(safePage * pageSize, safePage * pageSize + pageSize);

  async function load(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const form = event?.currentTarget ? new FormData(event.currentTarget) : undefined;
    setState("loading");
    setError("");
    try {
      setFindings(asArray<FindingRecord>(await Api.listFindings(apiBase, {
        pipeline_run_id: String(form?.get("pipeline_run_id") ?? "") || undefined,
        status: String(form?.get("status") ?? "") || undefined
      })));
      setPage(0);
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  useEffect(() => {
    void load();
  }, [apiBase]);

  async function selectFinding(finding: FindingRecord) {
    const id = recordId(finding, "finding_id");
    setSelected(id ? await Api.getFinding(apiBase, id) : finding);
  }

  async function decide(decision: string, note: string) {
    if (!selected) return;
    setState("loading");
    try {
      const updated = await Api.updateFindingDecision(apiBase, recordId(selected, "finding_id"), {
        status: decision,
        review_note: note
      });
      setSelected(updated);
      await load();
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  return (
    <>
      <PageHeader title="Nalazi" subtitle="Review odluke za prihvatanje, odbijanje, delimičnu obradu i ekspertizu." icon={<ListChecks size={24} />} />
      <section className="panel">
        <form onSubmit={load} className="toolbar">
          <label>
            pipeline_run_id
            <input name="pipeline_run_id" />
          </label>
          <label>
            Status
            <input name="status" placeholder="open, accepted..." />
          </label>
          <LoadingButton loading={state === "loading"}>Filtriraj</LoadingButton>
        </form>
        <ErrorBox message={error} />
        <div className="picker-meta">
          <span>{findings.length} nalaza</span>
          <span>Strana {safePage + 1}/{pageCount}</span>
        </div>
        <div className="master-detail">
          <div className="table-with-pager">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Naslov</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Odluka</th>
                </tr>
              </thead>
              <tbody>
                {visibleFindings.map((finding) => (
                  <tr key={recordId(finding, "finding_id")} onClick={() => selectFinding(finding)}>
                    <td>{finding.title ?? finding.category ?? recordId(finding, "finding_id")}</td>
                    <td>{finding.risk_level ?? finding.severity ?? "-"}</td>
                    <td>{finding.status ?? "-"}</td>
                    <td>{finding.review_decision ?? finding.review_note ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {findings.length ? (
              <div className="pager">
                <button type="button" disabled={safePage === 0} onClick={() => setPage((current) => Math.max(0, current - 1))}>
                  Prethodna
                </button>
                <button type="button" disabled={safePage >= pageCount - 1} onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))}>
                  Sledeća
                </button>
              </div>
            ) : (
              <EmptyState text="Nema nalaza za prikaz." />
            )}
          </div>
          <FindingDetailDrawer finding={selected} onDecision={decide} loading={state === "loading"} />
        </div>
      </section>
    </>
  );
}

function FindingDetailDrawer({
  finding,
  onDecision,
  loading
}: {
  finding: FindingRecord | null;
  onDecision: (decision: string, note: string) => void;
  loading: boolean;
}) {
  if (!finding) return <EmptyState text="Izaberi nalaz za detalj i odluku." />;
  return (
    <aside className="detail-pane">
      <h2>{finding.title ?? "Nalaz"}</h2>
      <p>{finding.message ?? finding.explanation ?? finding.recommendation ?? "Nema opisa."}</p>
      <ReviewDecisionControls disabled={loading} onDecision={onDecision} />
      <JsonPreview value={toJson(finding)} label="Detalj nalaza" />
    </aside>
  );
}

function ReportsPage({ apiBase }: { apiBase: string }) {
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [query, setQuery] = useState("");
  const [formatFilter, setFormatFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortBy, setSortBy] = useState("newest");
  const [page, setPage] = useState(0);
  const [state, setState] = useState<RequestState>("idle");
  const [error, setError] = useState("");
  const pageSize = 10;
  const filteredReports = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const filtered = reports.filter((report) => {
      const reportFormat = String(report.report_format ?? report.format ?? "").toLowerCase();
      const status = String(report.status ?? "spreman").toLowerCase();
      const haystack = [
        recordId(report, "report_id"),
        String(report.pipeline_run_id ?? ""),
        String(report.title ?? ""),
        reportFormat,
        status
      ].join(" ").toLowerCase();
      return (
        (!normalized || haystack.includes(normalized)) &&
        (!formatFilter || reportFormat === formatFilter) &&
        (!statusFilter || status === statusFilter)
      );
    });
    return [...filtered].sort((left, right) => compareReports(left, right, sortBy));
  }, [reports, query, formatFilter, statusFilter, sortBy]);
  const pageCount = Math.max(1, Math.ceil(filteredReports.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const visibleReports = filteredReports.slice(safePage * pageSize, safePage * pageSize + pageSize);

  useEffect(() => {
    setPage(0);
  }, [query, formatFilter, statusFilter, sortBy, reports.length]);

  async function loadReports() {
    setState("loading");
    try {
      setReports(asArray<ReportRecord>(await Api.listReports(apiBase)));
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  useEffect(() => {
    void loadReports();
  }, [apiBase]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      await Api.createReport(apiBase, {
        pipeline_run_id: form.get("pipeline_run_id"),
        report_format: form.get("report_format")
      });
      await loadReports();
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  return (
    <>
      <PageHeader title="Izveštaji" subtitle="Generisanje Markdown, DOCX i PDF izveštaja iz pipeline run-a." icon={<FileDown size={24} />} />
      <section className="panel">
        <form onSubmit={create} className="toolbar">
          <label>
            pipeline_run_id
            <input name="pipeline_run_id" required />
          </label>
          <label>
            Format
            <select name="report_format" defaultValue="docx">
              <option value="markdown">Markdown</option>
              <option value="docx">DOCX</option>
              <option value="pdf">PDF</option>
            </select>
          </label>
          <LoadingButton loading={state === "loading"}>Generiši</LoadingButton>
        </form>
        <ErrorBox message={error} />
      </section>
      <section className="panel">
        <div className="section-head">
          <h2>Lista izveštaja</h2>
          <button type="button" onClick={loadReports}>
            <RefreshCw size={16} />
            Osveži
          </button>
        </div>
        <div className="report-controls">
          <label>
            Search
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="report_id, pipeline_run_id, naslov..." />
          </label>
          <label>
            Format
            <select value={formatFilter} onChange={(event) => setFormatFilter(event.target.value)}>
              <option value="">Svi</option>
              <option value="markdown">Markdown</option>
              <option value="docx">DOCX</option>
              <option value="pdf">PDF</option>
            </select>
          </label>
          <label>
            Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">Svi</option>
              <option value="spreman">Spreman</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </label>
          <label>
            Sortiraj po
            <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
              <option value="newest">Najnovije prvo</option>
              <option value="oldest">Najstarije prvo</option>
              <option value="format-asc">Format A-Z</option>
              <option value="title-asc">Naslov A-Z</option>
            </select>
          </label>
        </div>
        <div className="picker-meta">
          <span>{filteredReports.length} izveštaja</span>
          <span>Strana {safePage + 1}/{pageCount}</span>
        </div>
        <div className="table-with-pager">
          <table className="data-table">
            <thead>
              <tr>
                <th>Naslov</th>
                <th>Format</th>
                <th>Status</th>
                <th>Datum</th>
                <th>Pipeline run</th>
                <th>Download</th>
              </tr>
            </thead>
            <tbody>
              {visibleReports.map((report) => {
                const id = recordId(report, "report_id");
                return (
                  <tr key={id}>
                    <td>{report.title ?? id}</td>
                    <td>{report.report_format ?? report.format ?? "-"}</td>
                    <td>{report.status ?? "spreman"}</td>
                    <td>{formatDate(report.created_at)}</td>
                    <td title={String(report.pipeline_run_id ?? "")}>{shortId(report.pipeline_run_id)}</td>
                    <td>
                      <a className="table-link" href={`${apiBase}/api/v1/reports/${id}/download`} target="_blank" rel="noreferrer">
                        Preuzmi
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filteredReports.length ? (
            <div className="pager">
              <button type="button" disabled={safePage === 0} onClick={() => setPage((current) => Math.max(0, current - 1))}>
                Prethodna
              </button>
              <button type="button" disabled={safePage >= pageCount - 1} onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))}>
                Sledeća
              </button>
            </div>
          ) : (
            <EmptyState text="Nema izveštaja za zadate filtere." />
          )}
        </div>
      </section>
    </>
  );
}

function compareReports(left: ReportRecord, right: ReportRecord, sortBy: string) {
  const leftDate = Date.parse(String(left.created_at ?? "")) || 0;
  const rightDate = Date.parse(String(right.created_at ?? "")) || 0;
  if (sortBy === "oldest") return leftDate - rightDate;
  if (sortBy === "format-asc") {
    return String(left.report_format ?? left.format ?? "").localeCompare(String(right.report_format ?? right.format ?? ""), "sr-Latn");
  }
  if (sortBy === "title-asc") {
    return String(left.title ?? "").localeCompare(String(right.title ?? ""), "sr-Latn");
  }
  return rightDate - leftDate;
}

function shortId(value: unknown) {
  const text = String(value ?? "");
  return text.length > 12 ? `${text.slice(0, 8)}...` : text || "-";
}

function AssistantPage({ apiBase }: { apiBase: string }) {
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [trace, setTrace] = useState<TraceStage[]>([]);
  const [corpora, setCorpora] = useState<CorpusRecord[]>([]);
  const [selectedCorpusId, setSelectedCorpusId] = useState("");
  const [state, setState] = useState<RequestState>("idle");
  const [error, setError] = useState("");

  async function loadCorporaForAssistant() {
    setError("");
    try {
      setCorpora(asArray<CorpusRecord>(await Api.listCorpora(apiBase)));
    } catch (error) {
      setError(errorMessage(error));
    }
  }

  useEffect(() => {
    void loadCorporaForAssistant();
  }, [apiBase]);

  async function createSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    const form = new FormData(event.currentTarget);
    try {
      const response = await Api.createAssistantSession(apiBase, {
        title: form.get("title"),
        selected_corpus_id: selectedCorpusId || undefined
      });
      setSessionId(String(response.session_id ?? response.id ?? ""));
      setMessages([]);
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sessionId) return;
    setState("loading");
    setError("");
    const form = new FormData(event.currentTarget);
    const content = String(form.get("content") ?? "");
    try {
      const response = await Api.sendAssistantMessage(apiBase, sessionId, { content_text: content });
      const history = await Api.assistantMessages(apiBase, sessionId).catch(() => [...messages, { role: "user", content_text: content }, response]);
      setMessages(history);
      setTrace(buildAssistantTrace(content, response));
      event.currentTarget.reset();
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  return (
    <>
      <PageHeader title="Asistent" subtitle="Pitanje, retrieved citati i odgovor u istom toku." icon={<Bot size={24} />} />
      <div className="content-grid two">
        <section className="panel">
          <h2>Sesija</h2>
          <form onSubmit={createSession} className="form-grid">
            <label>
              Naslov
              <input name="title" defaultValue="Analiza propisa" />
            </label>
            <LoadingButton loading={state === "loading"}>Kreiraj sesiju</LoadingButton>
          </form>
          <p className="muted">Aktivna sesija: {sessionId || "nema"}</p>
          <ErrorBox message={error} />
        </section>
        <section className="panel">
          <CorpusChoice
            corpora={corpora}
            selectedCorpusId={selectedCorpusId}
            onSelect={setSelectedCorpusId}
            inputName="assistant_corpus_id"
            label="Korpus za asistenta"
            allowEmpty
          />
        </section>
        <section className="panel">
          <h2>Poruka</h2>
          <form onSubmit={sendMessage} className="form-grid">
            <textarea name="content" placeholder="Postavi pravno pitanje..." required />
            <button type="submit" disabled={!sessionId || state === "loading"}>
              <Send size={16} />
              Pošalji
            </button>
          </form>
        </section>
      </div>
      <section className="panel">
        <h2>Istorija</h2>
        <div className="message-list">
          {messages.length ? messages.map((message, index) => (
            <article key={`${message.id ?? index}`} className={`message ${message.role ?? "assistant"}`}>
              <strong>{message.role ?? "assistant"}</strong>
              <p>{message.content ?? message.content_text ?? message.answer ?? ""}</p>
              <CitationList value={message.citations ?? message.retrieval_results} />
            </article>
          )) : <EmptyState text="Kreiraj sesiju i pošalji pitanje." />}
        </div>
      </section>
      <TracePanel stages={trace} />
    </>
  );
}

function SettingsPage({
  apiBase,
  setApiBase
}: {
  apiBase: string;
  setApiBase: (value: string) => void;
}) {
  return (
    <>
      <PageHeader title="Podešavanja" subtitle="Lokalna konfiguracija GUI aplikacije i veza sa backend API-jem." icon={<Settings size={24} />} />
      <div className="content-grid two">
        <section className="panel">
          <ApiStatus apiBase={apiBase} setApiBase={setApiBase} />
        </section>
        <AdminDataPanel apiBase={apiBase} />
      </div>
    </>
  );
}

const fallbackDataTypes: Record<string, string> = {
  corpora: "korpusi i njihovi importovani dokumenti",
  import_jobs: "import poslovi, reporti i import artefakti",
  documents: "importovani dokumenti i SQLite mirror",
  draft_reviews: "provere nacrta, artefakti i nalazi",
  findings: "nalazi provere nacrta",
  reports: "generisani izveštaji",
  uploads: "upload folder",
  vector_index: "lokalni vektorski indeks"
};

function AdminDataPanel({ apiBase }: { apiBase: string }) {
  const [dataTypes, setDataTypes] = useState<Record<string, string>>(fallbackDataTypes);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [confirmMode, setConfirmMode] = useState<"purge" | "restore" | null>(null);
  const [restoreFile, setRestoreFile] = useState<File | null>(null);
  const [state, setState] = useState<RequestState>("idle");
  const [backupState, setBackupState] = useState<RequestState>("idle");
  const [backupProgress, setBackupProgress] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Api.listAdminDataTypes(apiBase)
      .then(setDataTypes)
      .catch(() => setDataTypes(fallbackDataTypes));
  }, [apiBase]);

  const selectedLabels = selectedTypes.map((type) => dataTypes[type] ?? type);

  function toggleType(type: string) {
    setSelectedTypes((current) =>
      current.includes(type) ? current.filter((item) => item !== type) : [...current, type]
    );
  }

  async function purgeSelected() {
    setState("loading");
    setError("");
    setMessage("");
    try {
      const response = await Api.purgeAdminData(apiBase, selectedTypes);
      setMessage(formatAdminResult(response.message ?? "Podaci su obrisani.", response.deleted));
      setSelectedTypes([]);
      setConfirmMode(null);
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  async function restoreDump() {
    if (!restoreFile) return;
    setState("loading");
    setError("");
    setMessage("");
    try {
      const response = await Api.restoreAdminData(apiBase, restoreFile);
      setMessage(formatAdminResult(response.message ?? "Dump je importovan.", response.restored));
      setRestoreFile(null);
      setConfirmMode(null);
      setState("success");
    } catch (error) {
      setError(errorMessage(error));
      setState("error");
    }
  }

  async function downloadBackup() {
    setBackupState("loading");
    setBackupProgress(0);
    setError("");
    setMessage("Pravim backup dump. Ovo može da potraje kod većih korpusa...");
    try {
      const response = await Api.backupAdminData(apiBase);
      if (!response.ok) {
        throw new ApiError(response.status, await response.text());
      }
      const filename = filenameFromDisposition(response.headers.get("Content-Disposition")) ?? `zaikon-data-dump-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "")}.zip`;
      const total = Number(response.headers.get("Content-Length") ?? "0");
      const reader = response.body?.getReader();
      const chunks: BlobPart[] = [];
      let received = 0;
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value) {
            chunks.push(value);
            received += value.length;
            if (total > 0) setBackupProgress(Math.round((received / total) * 100));
          }
        }
      } else {
        chunks.push(new Uint8Array(await response.arrayBuffer()));
      }
      const blob = new Blob(chunks, { type: "application/zip" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setBackupProgress(100);
      setBackupState("success");
      setMessage(`Backup je spreman i preuzimanje je pokrenuto: ${filename}`);
    } catch (error) {
      setBackupState("error");
      setBackupProgress(null);
      setError(errorMessage(error));
    }
  }

  return (
    <section className="panel danger-panel">
      <div className="section-head">
        <div>
          <h2>Upravljanje podacima</h2>
          <p>Backup, restore i selektivno brisanje lokalnih podataka.</p>
        </div>
        <ShieldAlert size={18} />
      </div>
      <div className="admin-actions">
        <button type="button" onClick={downloadBackup} disabled={backupState === "loading"}>
          {backupState === "loading" ? <Loader2 className="spin" size={16} /> : <Download size={16} />}
          {backupState === "loading" ? "Backup u toku" : "Backup baze"}
        </button>
        <label className="file-action">
          <Upload size={16} />
          Import dumpa
          <input
            type="file"
            accept=".zip,application/zip"
            onChange={(event) => {
              const file = event.currentTarget.files?.[0] ?? null;
              setRestoreFile(file);
              if (file) setConfirmMode("restore");
              event.currentTarget.value = "";
            }}
          />
        </label>
      </div>
      {backupState === "loading" ? (
        <div className="progress-panel" aria-live="polite">
          <div className="progress-meta">
            <strong>Backup se priprema</strong>
            <span>{backupProgress === null || backupProgress === 0 ? "ZIP se pravi na serveru..." : `${backupProgress}%`}</span>
          </div>
          <div className="progress-track">
            <span style={{ width: `${backupProgress ?? 12}%` }} />
          </div>
        </div>
      ) : null}
      <div className="checkbox-grid" role="group" aria-label="Tipovi podataka za brisanje">
        {Object.entries(dataTypes).map(([type, label]) => (
          <label key={type} className="check-row">
            <input
              type="checkbox"
              checked={selectedTypes.includes(type)}
              onChange={() => toggleType(type)}
            />
            <span>
              <strong>{label}</strong>
              <small>{type}</small>
            </span>
          </label>
        ))}
      </div>
      <button
        type="button"
        className="danger-button"
        disabled={!selectedTypes.length || state === "loading"}
        onClick={() => setConfirmMode("purge")}
      >
        <Trash2 size={16} />
        Obriši izabrane podatke
      </button>
      {message ? <div className="success-box">{message}</div> : null}
      <ErrorBox message={error} />
      {confirmMode === "purge" ? (
        <ConfirmDialog
          title="Potvrda brisanja podataka"
          confirmLabel="Da, obriši"
          danger
          loading={state === "loading"}
          onCancel={() => setConfirmMode(null)}
          onConfirm={purgeSelected}
        >
          <p>Biće obrisani sledeći tipovi podataka:</p>
          <ul>
            {selectedLabels.map((label) => <li key={label}>{label}</li>)}
          </ul>
          <p>Ova akcija se ne može poništiti osim ako prethodno napraviš backup.</p>
        </ConfirmDialog>
      ) : null}
      {confirmMode === "restore" && restoreFile ? (
        <ConfirmDialog
          title="Potvrda importa dumpa"
          confirmLabel="Da, importuj i prepiši"
          danger
          loading={state === "loading"}
          onCancel={() => {
            setRestoreFile(null);
            setConfirmMode(null);
          }}
          onConfirm={restoreDump}
        >
          <p>Dump fajl:</p>
          <p><strong>{restoreFile.name}</strong></p>
          <p>Import će prepisati postojeće artefakte, upload folder, SQLite mirror i lokalni vektorski indeks sadržajem iz dumpa.</p>
        </ConfirmDialog>
      ) : null}
    </section>
  );
}

function filenameFromDisposition(disposition: string | null) {
  if (!disposition) return null;
  const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utfMatch) return decodeURIComponent(utfMatch[1]);
  const match = disposition.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? null;
}

function ConfirmDialog({
  title,
  children,
  confirmLabel,
  danger,
  loading,
  onCancel,
  onConfirm
}: {
  title: string;
  children: ReactNode;
  confirmLabel: string;
  danger?: boolean;
  loading?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="modal-backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
        <h2 id="confirm-title">{title}</h2>
        <div className="confirm-body">{children}</div>
        <div className="button-row">
          <button type="button" onClick={onCancel} disabled={loading}>
            Odustani
          </button>
          <button type="button" className={danger ? "danger-button" : undefined} onClick={onConfirm} disabled={loading}>
            {loading ? <Loader2 className="spin" size={16} /> : null}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

function formatAdminResult(message: string, counts?: Record<string, number>) {
  const entries = Object.entries(counts ?? {});
  if (!entries.length) return message;
  return `${message} ${entries.map(([key, value]) => `${key}: ${value}`).join(", ")}`;
}

function buildAssistantTrace(query: string, message: AssistantMessage): TraceStage[] {
  const citations = message.citations ?? message.retrieval_results ?? [];
  return [
    { id: "question", label: "Pitanje", status: "done", summary: query, data: { query } },
    { id: "retrieval", label: "Pronalaženje citata", status: "done", summary: "Backend je vratio citate ili retrieval metadata.", data: toJson(citations) },
    { id: "answer", label: "Odgovor", status: "done", summary: String(message.answer ?? message.content_text ?? message.content ?? "").slice(0, 160), data: toJson(message) }
  ];
}

function CitationList({ value }: { value: unknown }) {
  const citations = asArray<SearchResult>(value);
  if (!citations.length) return null;
  return (
    <div className="citation-list">
      {citations.map((citation, index) => (
        <span key={`${citation.legal_unit_id ?? index}`}>{citation.citation ?? citation.title ?? citation.legal_unit_id ?? `Citat ${index + 1}`}</span>
      ))}
    </div>
  );
}

export function App() {
  const [route, setRouteState] = useState<RouteId>(() => routeFromPath(window.location.pathname));
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE);
  const setRoute = useCallback((nextRoute: RouteId) => {
    setRouteState(nextRoute);
    const nextPath = routePaths[nextRoute];
    if (window.location.pathname !== nextPath) {
      window.history.pushState(null, "", nextPath);
    }
  }, []);

  useEffect(() => {
    const handlePopState = () => setRouteState(routeFromPath(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  return (
    <AppShell route={route} setRoute={setRoute}>
      {route === "corpora" ? <CorporaPage apiBase={apiBase} /> : null}
      {route === "documents" ? <DocumentsPage apiBase={apiBase} /> : null}
      {route === "search" ? <SearchPage apiBase={apiBase} /> : null}
      {route === "draft-reviews" ? <DraftReviewsPage apiBase={apiBase} /> : null}
      {route === "findings" ? <FindingsPage apiBase={apiBase} /> : null}
      {route === "reports" ? <ReportsPage apiBase={apiBase} /> : null}
      {route === "assistant" ? <AssistantPage apiBase={apiBase} /> : null}
      {route === "settings" ? <SettingsPage apiBase={apiBase} setApiBase={setApiBase} /> : null}
    </AppShell>
  );
}
