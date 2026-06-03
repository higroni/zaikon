import { useCallback, useEffect, useState } from "react";
import { Activity, AlertCircle, CheckCircle, Loader2, Play, RefreshCw } from "lucide-react";
import { Api, ApiError, DEFAULT_API_BASE } from "../api";
import type { EvaluationRunResponse, GoldCase, RequestState } from "../types";

interface MetricsCardProps {
  title: string;
  value: number | undefined;
  format?: "percentage" | "number";
  color?: "green" | "yellow" | "red" | "blue";
}

function MetricsCard({ title, value, format = "percentage", color = "blue" }: MetricsCardProps) {
  const colorStyles = {
    green: { background: "#e8f5e9", borderColor: "#81c784", color: "#2e7d32" },
    yellow: { background: "#fff9e6", borderColor: "#ffd54f", color: "#f57f17" },
    red: { background: "#ffebee", borderColor: "#e57373", color: "#c62828" },
    blue: { background: "var(--primary-soft)", borderColor: "#a8d5cb", color: "var(--primary)" }
  };

  const formattedValue = value !== undefined
    ? format === "percentage"
      ? `${(value * 100).toFixed(1)}%`
      : value.toString()
    : "N/A";

  return (
    <div style={{
      padding: "var(--space-3)",
      borderRadius: "var(--radius)",
      border: "2px solid",
      ...colorStyles[color]
    }}>
      <div style={{ fontSize: "13px", fontWeight: 500, opacity: 0.75 }}>{title}</div>
      <div style={{ fontSize: "28px", fontWeight: 700, marginTop: "8px" }}>{formattedValue}</div>
    </div>
  );
}

interface ConfusionMatrixProps {
  matrix: Array<{ expected?: string; detected?: string; count?: number }> | undefined;
}

function ConfusionMatrix({ matrix }: ConfusionMatrixProps) {
  if (!matrix || matrix.length === 0) {
    return <div style={{ color: "var(--text-muted)", fontSize: "13px" }}>Nema podataka</div>;
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "var(--surface)" }}>
            <th style={{
              border: "1px solid var(--border)",
              padding: "var(--space-2) var(--space-3)",
              textAlign: "left",
              fontSize: "13px",
              fontWeight: 600
            }}>
              Očekivano
            </th>
            <th style={{
              border: "1px solid var(--border)",
              padding: "var(--space-2) var(--space-3)",
              textAlign: "left",
              fontSize: "13px",
              fontWeight: 600
            }}>
              Detektovano
            </th>
            <th style={{
              border: "1px solid var(--border)",
              padding: "var(--space-2) var(--space-3)",
              textAlign: "right",
              fontSize: "13px",
              fontWeight: 600
            }}>
              Broj
            </th>
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, idx) => (
            <tr key={idx} style={{ transition: "background 0.2s" }}
                onMouseEnter={(e) => e.currentTarget.style.background = "var(--surface)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
              <td style={{
                border: "1px solid var(--border)",
                padding: "var(--space-2) var(--space-3)",
                fontSize: "13px"
              }}>
                {row.expected || "N/A"}
              </td>
              <td style={{
                border: "1px solid var(--border)",
                padding: "var(--space-2) var(--space-3)",
                fontSize: "13px"
              }}>
                {row.detected || "N/A"}
              </td>
              <td style={{
                border: "1px solid var(--border)",
                padding: "var(--space-2) var(--space-3)",
                fontSize: "13px",
                textAlign: "right",
                fontFamily: "monospace"
              }}>
                {row.count || 0}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EvaluationDashboard() {
  const [apiBase] = useState(DEFAULT_API_BASE);
  const [goldCases, setGoldCases] = useState<GoldCase[]>([]);
  const [goldCasesState, setGoldCasesState] = useState<RequestState>("idle");
  const [evaluationResult, setEvaluationResult] = useState<EvaluationRunResponse | null>(null);
  const [evaluationState, setEvaluationState] = useState<RequestState>("idle");
  const [error, setError] = useState<string | null>(null);

  const loadGoldCases = useCallback(async () => {
    setGoldCasesState("loading");
    setError(null);
    try {
      const cases = await Api.listGoldCases(apiBase);
      setGoldCases(cases);
      setGoldCasesState("success");
    } catch (err) {
      setGoldCasesState("error");
      setError(err instanceof ApiError ? err.message : "Greška pri učitavanju gold cases");
    }
  }, [apiBase]);

  const runEvaluation = useCallback(async () => {
    setEvaluationState("loading");
    setError(null);
    try {
      const result = await Api.runEvaluation(apiBase);
      setEvaluationResult(result);
      setEvaluationState("success");
    } catch (err) {
      setEvaluationState("error");
      setError(err instanceof ApiError ? err.message : "Greška pri pokretanju evaluacije");
    }
  }, [apiBase]);

  useEffect(() => {
    loadGoldCases();
  }, [loadGoldCases]);

  const metrics = evaluationResult?.overall_metrics;
  const results = evaluationResult?.results || [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontSize: "24px", fontWeight: 700, color: "var(--text)" }}>Evaluacija Sistema</h2>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
            Testiranje detekcije konflikata na gold case setovima
          </p>
        </div>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <button
            onClick={loadGoldCases}
            disabled={goldCasesState === "loading"}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-2)",
              padding: "var(--space-2) var(--space-3)",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              cursor: goldCasesState === "loading" ? "not-allowed" : "pointer",
              opacity: goldCasesState === "loading" ? 0.5 : 1,
              transition: "all 0.2s"
            }}
            onMouseEnter={(e) => {
              if (goldCasesState !== "loading") {
                e.currentTarget.style.background = "#e0e0e0";
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "var(--surface)";
            }}
          >
            {goldCasesState === "loading" ? (
              <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
            ) : (
              <RefreshCw size={18} />
            )}
            Osveži
          </button>
          <button
            onClick={runEvaluation}
            disabled={evaluationState === "loading" || goldCases.length === 0}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-2)",
              padding: "var(--space-2) var(--space-3)",
              background: "var(--primary)",
              color: "white",
              border: "none",
              borderRadius: "var(--radius)",
              cursor: (evaluationState === "loading" || goldCases.length === 0) ? "not-allowed" : "pointer",
              opacity: (evaluationState === "loading" || goldCases.length === 0) ? 0.5 : 1,
              transition: "all 0.2s"
            }}
            onMouseEnter={(e) => {
              if (evaluationState !== "loading" && goldCases.length > 0) {
                e.currentTarget.style.background = "#0f675e";
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "var(--primary)";
            }}
          >
            {evaluationState === "loading" ? (
              <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
            ) : (
              <Play size={18} />
            )}
            Pokreni Evaluaciju
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="status-pill error" style={{ width: "100%", height: "auto", padding: "var(--space-3)" }}>
          <AlertCircle size={20} style={{ flexShrink: 0 }} />
          <div>
            <strong>Greška</strong>
            <p style={{ marginTop: "4px", fontSize: "13px" }}>{error}</p>
          </div>
        </div>
      )}

      {/* Gold Cases Summary */}
      <section className="panel">
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-3)" }}>
          <Activity size={20} style={{ color: "var(--primary)" }} />
          <h3 style={{ fontSize: "18px", fontWeight: 600 }}>Gold Cases</h3>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "var(--space-3)" }}>
          <MetricsCard
            title="Ukupno Test Slučajeva"
            value={goldCases.length}
            format="number"
            color="blue"
          />
          <MetricsCard
            title="Očekivanih Konflikata"
            value={goldCases.reduce((sum, c) => sum + (c.expected_conflicts?.length || 0), 0)}
            format="number"
            color="yellow"
          />
          <MetricsCard
            title="Status"
            value={goldCasesState === "success" ? 1 : 0}
            format="number"
            color={goldCasesState === "success" ? "green" : "red"}
          />
        </div>
      </section>

      {/* Overall Metrics */}
      {metrics && (
        <section className="panel">
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-3)" }}>
            <CheckCircle size={20} style={{ color: "#4caf50" }} />
            <h3 style={{ fontSize: "18px", fontWeight: 600 }}>Ukupne Metrike</h3>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "var(--space-3)", marginBottom: "var(--space-4)" }}>
            <MetricsCard
              title="Precision"
              value={metrics.precision}
              color={
                metrics.precision && metrics.precision >= 0.8
                  ? "green"
                  : metrics.precision && metrics.precision >= 0.6
                  ? "yellow"
                  : "red"
              }
            />
            <MetricsCard
              title="Recall"
              value={metrics.recall}
              color={
                metrics.recall && metrics.recall >= 0.8
                  ? "green"
                  : metrics.recall && metrics.recall >= 0.6
                  ? "yellow"
                  : "red"
              }
            />
            <MetricsCard
              title="F1 Score"
              value={metrics.f1_score}
              color={
                metrics.f1_score && metrics.f1_score >= 0.8
                  ? "green"
                  : metrics.f1_score && metrics.f1_score >= 0.6
                  ? "yellow"
                  : "red"
              }
            />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "var(--space-3)" }}>
            <MetricsCard
              title="True Positives"
              value={metrics.true_positives}
              format="number"
              color="green"
            />
            <MetricsCard
              title="False Positives"
              value={metrics.false_positives}
              format="number"
              color="red"
            />
            <MetricsCard
              title="False Negatives"
              value={metrics.false_negatives}
              format="number"
              color="yellow"
            />
          </div>
        </section>
      )}

      {/* Confusion Matrix */}
      {metrics?.confusion_matrix && (
        <section className="panel">
          <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "var(--space-3)" }}>Confusion Matrix</h3>
          <ConfusionMatrix matrix={metrics.confusion_matrix} />
        </section>
      )}

      {/* Per-Type Metrics */}
      {metrics?.per_type_metrics && Object.keys(metrics.per_type_metrics).length > 0 && (
        <section className="panel">
          <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "var(--space-3)" }}>Metrike po Tipu Konflikta</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            {Object.entries(metrics.per_type_metrics).map(([type, typeMetrics]) => (
              <div key={type} style={{
                borderLeft: "4px solid var(--primary)",
                paddingLeft: "var(--space-3)"
              }}>
                <div style={{ fontWeight: 600, color: "var(--text)", marginBottom: "var(--space-2)" }}>{type}</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "var(--space-3)" }}>
                  <div style={{ fontSize: "13px" }}>
                    <span style={{ color: "var(--text-muted)" }}>Precision:</span>{" "}
                    <span style={{ fontFamily: "monospace", fontWeight: 600 }}>
                      {typeMetrics.precision !== undefined
                        ? `${(typeMetrics.precision * 100).toFixed(1)}%`
                        : "N/A"}
                    </span>
                  </div>
                  <div style={{ fontSize: "13px" }}>
                    <span style={{ color: "var(--text-muted)" }}>Recall:</span>{" "}
                    <span style={{ fontFamily: "monospace", fontWeight: 600 }}>
                      {typeMetrics.recall !== undefined
                        ? `${(typeMetrics.recall * 100).toFixed(1)}%`
                        : "N/A"}
                    </span>
                  </div>
                  <div style={{ fontSize: "13px" }}>
                    <span style={{ color: "var(--text-muted)" }}>F1:</span>{" "}
                    <span style={{ fontFamily: "monospace", fontWeight: 600 }}>
                      {typeMetrics.f1_score !== undefined
                        ? `${(typeMetrics.f1_score * 100).toFixed(1)}%`
                        : "N/A"}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Individual Results */}
      {results.length > 0 && (
        <section className="panel">
          <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "var(--space-3)" }}>Rezultati po Test Slučaju</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            {results.map((result, idx) => (
              <div
                key={idx}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius)",
                  padding: "var(--space-3)",
                  transition: "background 0.2s"
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "var(--surface)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, color: "var(--text)" }}>{result.title || result.case_id}</div>
                    <div style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
                      Detektovano: {result.detected_conflicts?.length || 0} | Očekivano:{" "}
                      {result.expected_conflicts?.length || 0}
                    </div>
                  </div>
                  <div
                    style={{
                      padding: "4px 12px",
                      borderRadius: "12px",
                      fontSize: "13px",
                      fontWeight: 500,
                      ...(result.status === "pass"
                        ? { background: "#e8f5e9", color: "#2e7d32" }
                        : result.status === "fail"
                        ? { background: "#ffebee", color: "#c62828" }
                        : { background: "#fff9e6", color: "#f57f17" })
                    }}
                  >
                    {result.status === "pass" ? "✓ Pass" : result.status === "fail" ? "✗ Fail" : "⚠ Warning"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// Made with Bob
