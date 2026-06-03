import { useCallback, useEffect, useState } from "react";
import { AlertCircle, CheckCircle, Loader2, RefreshCw, SlidersHorizontal, ToggleLeft, ToggleRight } from "lucide-react";
import { Api, ApiError, DEFAULT_API_BASE } from "../api";
import type { ConflictRule, RequestState } from "../types";

interface RuleCardProps {
  rule: ConflictRule;
  onToggle: (ruleId: string, enabled: boolean) => void;
  isSaving: boolean;
}

function RuleCard({ rule, onToggle, isSaving }: RuleCardProps) {
  const severityStyles = {
    critical: { background: "#ffebee", color: "#c62828", borderColor: "#e57373" },
    high: { background: "#fff3e0", color: "#e65100", borderColor: "#ffb74d" },
    medium: { background: "#fff9e6", color: "#f57f17", borderColor: "#ffd54f" },
    low: { background: "#e3f2fd", color: "#1565c0", borderColor: "#64b5f6" }
  };

  const categoryStyles = {
    authority_scope: { background: "#f3e5f5", borderColor: "#ce93d8" },
    competence: { background: "#e8eaf6", borderColor: "#9fa8da" },
    deadline: { background: "#e0f7fa", borderColor: "#80deea" },
    definition: { background: "#e0f2f1", borderColor: "#80cbc4" },
    permission: { background: "#e8f5e9", borderColor: "#81c784" },
    obligation: { background: "#f1f8e9", borderColor: "#aed581" },
    reference: { background: "#fff8e1", borderColor: "#ffd54f" },
    sanction: { background: "#fce4ec", borderColor: "#f48fb1" }
  };

  const severity = (rule.severity || "medium") as keyof typeof severityStyles;
  const category = (rule.category || "authority_scope") as keyof typeof categoryStyles;

  return (
    <div style={{
      borderRadius: "var(--radius)",
      border: "2px solid",
      padding: "var(--space-3)",
      ...(categoryStyles[category] || { background: "var(--surface)", borderColor: "var(--border)" })
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "var(--space-2)" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "4px" }}>
            <h4 style={{ fontWeight: 600, color: "var(--text)" }}>{rule.conflict_type}</h4>
            <span style={{
              padding: "2px 8px",
              borderRadius: "12px",
              fontSize: "11px",
              fontWeight: 500,
              border: "1px solid",
              ...(severityStyles[severity] || { background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" })
            }}>
              {rule.severity}
            </span>
          </div>
          <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>{rule.description}</p>
        </div>
        <button
          onClick={() => onToggle(rule.rule_id || "", !rule.enabled)}
          disabled={isSaving}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
            padding: "6px 12px",
            borderRadius: "var(--radius)",
            border: "none",
            cursor: isSaving ? "not-allowed" : "pointer",
            opacity: isSaving ? 0.5 : 1,
            transition: "all 0.2s",
            ...(rule.enabled
              ? { background: "#4caf50", color: "white" }
              : { background: "#bdbdbd", color: "#424242" })
          }}
          onMouseEnter={(e) => {
            if (!isSaving) {
              e.currentTarget.style.background = rule.enabled ? "#388e3c" : "#9e9e9e";
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = rule.enabled ? "#4caf50" : "#bdbdbd";
          }}
        >
          {rule.enabled ? (
            <>
              <ToggleRight size={18} />
              <span style={{ fontSize: "13px", fontWeight: 500 }}>Aktivno</span>
            </>
          ) : (
            <>
              <ToggleLeft size={18} />
              <span style={{ fontSize: "13px", fontWeight: 500 }}>Neaktivno</span>
            </>
          )}
        </button>
      </div>
      {rule.operators && rule.operators.length > 0 && (
        <div style={{ marginTop: "var(--space-2)", paddingTop: "var(--space-2)", borderTop: "1px solid var(--border)" }}>
          <div style={{ fontSize: "11px", fontWeight: 500, color: "var(--text-muted)", marginBottom: "var(--space-1)" }}>Operatori:</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
            {rule.operators.map((op, idx) => (
              <span
                key={idx}
                style={{
                  padding: "2px 8px",
                  background: "white",
                  border: "1px solid var(--border)",
                  borderRadius: "4px",
                  fontSize: "11px",
                  fontFamily: "monospace",
                  color: "var(--text)"
                }}
              >
                {op}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function ConflictRulesTuning() {
  const [apiBase] = useState(DEFAULT_API_BASE);
  const [rules, setRules] = useState<ConflictRule[]>([]);
  const [rulesState, setRulesState] = useState<RequestState>("idle");
  const [savingRuleId, setSavingRuleId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>("all");
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [filterEnabled, setFilterEnabled] = useState<string>("all");

  const loadRules = useCallback(async () => {
    setRulesState("loading");
    setError(null);
    try {
      const loadedRules = await Api.listConflictRules(apiBase);
      setRules(loadedRules);
      setRulesState("success");
    } catch (err) {
      setRulesState("error");
      setError(err instanceof ApiError ? err.message : "Greška pri učitavanju pravila");
    }
  }, [apiBase]);

  const toggleRule = useCallback(
    async (ruleId: string, enabled: boolean) => {
      setSavingRuleId(ruleId);
      setError(null);
      setSuccessMessage(null);
      try {
        const updatedRule = await Api.updateConflictRule(apiBase, ruleId, { enabled });
        setRules((prev) =>
          prev.map((r) => (r.rule_id === ruleId ? { ...r, enabled: updatedRule.enabled } : r))
        );
        setSuccessMessage(`Pravilo ${enabled ? "aktivirano" : "deaktivirano"}`);
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Greška pri ažuriranju pravila");
      } finally {
        setSavingRuleId(null);
      }
    },
    [apiBase]
  );

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  const categories = Array.from(new Set(rules.map((r) => r.category).filter(Boolean)));
  const severities = Array.from(new Set(rules.map((r) => r.severity).filter(Boolean)));

  const filteredRules = rules.filter((rule) => {
    if (filterCategory !== "all" && rule.category !== filterCategory) return false;
    if (filterSeverity !== "all" && rule.severity !== filterSeverity) return false;
    if (filterEnabled === "enabled" && !rule.enabled) return false;
    if (filterEnabled === "disabled" && rule.enabled) return false;
    return true;
  });

  const enabledCount = rules.filter((r) => r.enabled).length;
  const disabledCount = rules.length - enabledCount;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontSize: "24px", fontWeight: 700, color: "var(--text)" }}>Podešavanje Pravila Konflikata</h2>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
            Upravljanje aktivnim pravilima za detekciju konflikata
          </p>
        </div>
        <button
          onClick={loadRules}
          disabled={rulesState === "loading"}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
            padding: "var(--space-2) var(--space-3)",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            cursor: rulesState === "loading" ? "not-allowed" : "pointer",
            opacity: rulesState === "loading" ? 0.5 : 1,
            transition: "all 0.2s"
          }}
          onMouseEnter={(e) => {
            if (rulesState !== "loading") {
              e.currentTarget.style.background = "#e0e0e0";
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "var(--surface)";
          }}
        >
          {rulesState === "loading" ? (
            <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
          ) : (
            <RefreshCw size={18} />
          )}
          Osveži
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="status-pill error" style={{ width: "100%", height: "auto", padding: "var(--space-3)" }}>
          <AlertCircle size={20} style={{ flexShrink: 0 }} />
          <div>
            <strong>Greška</strong>
            <p style={{ marginTop: "4px", fontSize: "13px" }}>{error}</p>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="status-pill success" style={{ width: "100%", height: "auto", padding: "var(--space-3)" }}>
          <CheckCircle size={20} style={{ flexShrink: 0 }} />
          <div>
            <strong>Uspešno</strong>
            <p style={{ marginTop: "4px", fontSize: "13px" }}>{successMessage}</p>
          </div>
        </div>
      )}

      {/* Statistics */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "var(--space-3)" }}>
        <div className="panel">
          <div style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-muted)" }}>Ukupno Pravila</div>
          <div style={{ fontSize: "28px", fontWeight: 700, color: "var(--text)", marginTop: "8px" }}>{rules.length}</div>
        </div>
        <div style={{
          background: "#e8f5e9",
          borderRadius: "var(--radius)",
          border: "2px solid #81c784",
          padding: "var(--space-3)"
        }}>
          <div style={{ fontSize: "13px", fontWeight: 500, color: "#2e7d32" }}>Aktivna Pravila</div>
          <div style={{ fontSize: "28px", fontWeight: 700, color: "#1b5e20", marginTop: "8px" }}>{enabledCount}</div>
        </div>
        <div style={{
          background: "var(--surface)",
          borderRadius: "var(--radius)",
          border: "2px solid var(--border)",
          padding: "var(--space-3)"
        }}>
          <div style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-muted)" }}>Neaktivna Pravila</div>
          <div style={{ fontSize: "28px", fontWeight: 700, color: "var(--text)", marginTop: "8px" }}>{disabledCount}</div>
        </div>
      </div>

      {/* Filters */}
      <section className="panel">
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-3)" }}>
          <SlidersHorizontal size={20} style={{ color: "var(--text-muted)" }} />
          <h3 style={{ fontSize: "18px", fontWeight: 600 }}>Filteri</h3>
        </div>
        <div className="form-grid">
          <label>
            Kategorija
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
            >
              <option value="all">Sve kategorije</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </label>
          <label>
            Ozbiljnost
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
            >
              <option value="all">Sve ozbiljnosti</option>
              {severities.map((sev) => (
                <option key={sev} value={sev}>
                  {sev}
                </option>
              ))}
            </select>
          </label>
          <label>
            Status
            <select
              value={filterEnabled}
              onChange={(e) => setFilterEnabled(e.target.value)}
            >
              <option value="all">Svi statusi</option>
              <option value="enabled">Samo aktivna</option>
              <option value="disabled">Samo neaktivna</option>
            </select>
          </label>
        </div>
      </section>

      {/* Rules List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
        {rulesState === "loading" ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "var(--space-5)" }}>
            <Loader2 size={32} style={{ animation: "spin 1s linear infinite", color: "var(--primary)" }} />
          </div>
        ) : filteredRules.length === 0 ? (
          <div style={{ textAlign: "center", padding: "var(--space-5)", color: "var(--text-muted)" }}>
            Nema pravila koja odgovaraju filterima
          </div>
        ) : (
          filteredRules.map((rule) => (
            <RuleCard
              key={rule.rule_id}
              rule={rule}
              onToggle={toggleRule}
              isSaving={savingRuleId === rule.rule_id}
            />
          ))
        )}
      </div>
    </div>
  );
}

// Made with Bob
