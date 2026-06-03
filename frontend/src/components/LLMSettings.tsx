import { useCallback, useEffect, useState } from "react";
import { AlertCircle, Bot, CheckCircle, Loader2, RefreshCw, Save } from "lucide-react";
import { Api, ApiError, DEFAULT_API_BASE } from "../api";
import type { LLMConfig, OllamaModel, RequestState } from "../types";
import { EmbeddingSettings } from "./EmbeddingSettings";
import { RerankerSettings } from "./RerankerSettings";
import { RAGSettings } from "./RAGSettings";

type SubTab = "llm" | "embedding" | "reranker" | "rag";

export function LLMSettings() {
  const [apiBase] = useState(DEFAULT_API_BASE);
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("llm");
  const [config, setConfig] = useState<LLMConfig>({
    llm_use_provider: false,
    llm_base_url: "http://localhost:11434",
    llm_model: "mistral:latest",
    llm_temperature: 0.1,
    llm_top_p: 0.9,
    llm_max_tokens: 2048,
    llm_context_window: 32768,
    llm_system_prompt: ""
  });
  const [availableModels, setAvailableModels] = useState<OllamaModel[]>([]);
  const [loadState, setLoadState] = useState<RequestState>("idle");
  const [saveState, setSaveState] = useState<RequestState>("idle");
  const [modelsState, setModelsState] = useState<RequestState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadConfig = useCallback(async () => {
    setLoadState("loading");
    setError(null);
    try {
      const response = await Api.getLLMConfig(apiBase);
      setConfig(response);
      setLoadState("success");
    } catch (err) {
      setLoadState("error");
      setError(err instanceof ApiError ? err.message : "Greška pri učitavanju konfiguracije");
    }
  }, [apiBase]);

  const loadModels = useCallback(async () => {
    if (!config.llm_use_provider) return;
    
    setModelsState("loading");
    try {
      const models = await Api.getOllamaModels(apiBase, config.llm_base_url);
      setAvailableModels(models);
      setModelsState("success");
    } catch (err) {
      setModelsState("error");
      setAvailableModels([]);
    }
  }, [apiBase, config.llm_base_url, config.llm_use_provider]);

  const saveConfig = useCallback(async () => {
    setSaveState("loading");
    setError(null);
    setSuccessMessage(null);
    try {
      await Api.updateLLMConfig(apiBase, config);
      setSaveState("success");
      setSuccessMessage("Konfiguracija uspešno sačuvana");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setSaveState("error");
      setError(err instanceof ApiError ? err.message : "Greška pri čuvanju konfiguracije");
    }
  }, [apiBase, config]);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  useEffect(() => {
    if (config.llm_use_provider) {
      loadModels();
    }
  }, [config.llm_use_provider, loadModels]);

  const subTabs: { id: SubTab; label: string }[] = [
    { id: "llm", label: "LLM Provider" },
    { id: "embedding", label: "Embedding Model" },
    { id: "reranker", label: "Reranker" },
    { id: "rag", label: "RAG Config" }
  ];

  return (
    <>
      {/* Sub-tabs */}
      <div style={{ 
        display: "flex", 
        gap: "32px", 
        borderBottom: "1px solid var(--border)",
        marginBottom: "var(--space-4)"
      }}>
        {subTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveSubTab(tab.id)}
            style={{
              background: "transparent",
              padding: "12px 4px",
              border: "none",
              borderBottom: activeSubTab === tab.id ? "2px solid var(--primary)" : "none",
              cursor: "pointer",
              fontWeight: activeSubTab === tab.id ? "650" : "normal",
              color: activeSubTab === tab.id ? "var(--primary)" : "var(--text-muted)",
              transition: "all 0.2s"
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* LLM Provider Tab */}
      {activeSubTab === "llm" && (
        <>
          {/* Messages */}
          {error && (
            <div className="status-pill error" style={{ width: "100%", height: "auto", padding: "var(--space-3)", marginBottom: "var(--space-4)" }}>
              <AlertCircle size={20} style={{ flexShrink: 0 }} />
              <div>
                <strong>Greška</strong>
                <p style={{ marginTop: "4px", fontSize: "13px" }}>{error}</p>
              </div>
            </div>
          )}

          {successMessage && (
            <div className="status-pill success" style={{ width: "100%", height: "auto", padding: "var(--space-3)", marginBottom: "var(--space-4)" }}>
              <CheckCircle size={20} style={{ flexShrink: 0 }} />
              <div>
                <strong>Uspešno</strong>
                <p style={{ marginTop: "4px", fontSize: "13px" }}>{successMessage}</p>
              </div>
            </div>
          )}

          {/* Main Settings */}
          <section className="panel">
            <div className="section-head">
              <div>
                <h2>LLM Provider Konfiguracija</h2>
                <p>Podešavanja za Ollama LLM provider</p>
              </div>
            </div>

            <div className="form-grid">
              {/* Enable/Disable LLM */}
              <label style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontWeight: "700", marginBottom: "4px" }}>Koristi LLM Provider</div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: "normal" }}>
                    Ako je isključeno, sistem koristi deterministički fallback
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.llm_use_provider}
                  onChange={(e) => setConfig({ ...config, llm_use_provider: e.target.checked })}
                  style={{ width: "auto", marginLeft: "var(--space-3)" }}
                />
              </label>

              {/* Ollama Server URL */}
              <label>
                Ollama Server URL
                <input
                  type="text"
                  value={config.llm_base_url}
                  onChange={(e) => setConfig({ ...config, llm_base_url: e.target.value })}
                  disabled={!config.llm_use_provider}
                  placeholder="http://localhost:11434"
                />
              </label>

              {/* Model Selection */}
              <label>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span>Model</span>
                  <button
                    type="button"
                    onClick={loadModels}
                    disabled={!config.llm_use_provider || modelsState === "loading"}
                    style={{ 
                      width: "auto", 
                      height: "28px", 
                      padding: "0 8px", 
                      fontSize: "12px",
                      display: "flex",
                      alignItems: "center",
                      gap: "4px"
                    }}
                  >
                    {modelsState === "loading" ? (
                      <Loader2 size={14} className="spin" />
                    ) : (
                      <RefreshCw size={14} />
                    )}
                    Osveži
                  </button>
                </div>
                {availableModels.length > 0 ? (
                  <select
                    value={config.llm_model}
                    onChange={(e) => setConfig({ ...config, llm_model: e.target.value })}
                    disabled={!config.llm_use_provider}
                  >
                    {availableModels.map((model) => (
                      <option key={model.name} value={model.name}>
                        {model.name} ({(model.size / 1024 / 1024 / 1024).toFixed(1)} GB)
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={config.llm_model}
                    onChange={(e) => setConfig({ ...config, llm_model: e.target.value })}
                    disabled={!config.llm_use_provider}
                    placeholder="mistral:latest"
                  />
                )}
                {modelsState === "error" && (
                  <p style={{ fontSize: "12px", color: "var(--warning)", marginTop: "4px" }}>
                    Nije moguće učitati modele. Proverite da li Ollama server radi.
                  </p>
                )}
              </label>

              {/* Temperature */}
              <label>
                Temperature: {config.llm_temperature.toFixed(2)}
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.llm_temperature}
                  onChange={(e) => setConfig({ ...config, llm_temperature: parseFloat(e.target.value) })}
                  disabled={!config.llm_use_provider}
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                  <span>Deterministički (0.0)</span>
                  <span>Kreativno (2.0)</span>
                </div>
              </label>

              {/* Top P */}
              <label>
                Top P: {(config.llm_top_p ?? 0.9).toFixed(2)}
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={config.llm_top_p ?? 0.9}
                  onChange={(e) => setConfig({ ...config, llm_top_p: parseFloat(e.target.value) })}
                  disabled={!config.llm_use_provider}
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                  <span>Fokusirano (0.0)</span>
                  <span>Raznovrsno (1.0)</span>
                </div>
              </label>

              {/* Max Tokens */}
              <label>
                Maksimalan Broj Tokena
                <input
                  type="number"
                  value={config.llm_max_tokens}
                  onChange={(e) => setConfig({ ...config, llm_max_tokens: parseInt(e.target.value) || 2048 })}
                  disabled={!config.llm_use_provider}
                  min="256"
                  max="8192"
                  step="256"
                />
                <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
                  Preporučeno: 2048-4096 za balans između brzine i kvaliteta
                </p>
              </label>

              {/* Context Window */}
              <label>
                Context Window
                <input
                  type="number"
                  value={config.llm_context_window ?? 32768}
                  onChange={(e) => setConfig({ ...config, llm_context_window: parseInt(e.target.value) || 32768 })}
                  disabled={!config.llm_use_provider}
                  min="2048"
                  max="131072"
                  step="2048"
                />
                <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
                  Maksimalna dužina konteksta u tokenima (zavisi od modela)
                </p>
              </label>

              {/* System Prompt */}
              <label>
                Sistemski Prompt (Opciono)
                <textarea
                  value={config.llm_system_prompt || ""}
                  onChange={(e) => setConfig({ ...config, llm_system_prompt: e.target.value })}
                  disabled={!config.llm_use_provider}
                  rows={4}
                  placeholder="Ti si pravni asistent specijalizovan za srpsko zakonodavstvo..."
                  style={{ fontFamily: "monospace", fontSize: "13px" }}
                />
                <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
                  Dodatne instrukcije za LLM model
                </p>
              </label>

              {/* Save Button */}
              <button
                type="button"
                onClick={saveConfig}
                disabled={saveState === "loading"}
                style={{ justifySelf: "start" }}
              >
                {saveState === "loading" ? (
                  <Loader2 size={18} className="spin" />
                ) : (
                  <Save size={18} />
                )}
                Sačuvaj Podešavanja
              </button>
            </div>
          </section>

          {/* Info Box */}
          <div className="status-pill" style={{ width: "100%", height: "auto", padding: "var(--space-3)", background: "var(--primary-soft)", borderColor: "#a8d5cb" }}>
            <Bot size={20} style={{ flexShrink: 0, color: "var(--primary)" }} />
            <div>
              <strong style={{ color: "var(--primary)" }}>Napomena o LLM Provideru</strong>
              <ul style={{ marginTop: "8px", paddingLeft: "20px", fontSize: "13px", color: "#0f675e" }}>
                <li>Sistem radi i bez LLM-a koristeći deterministički fallback</li>
                <li>LLM poboljšava prirodnost odgovora ali zahteva Ollama server</li>
                <li>Svi odgovori su "grounded" - bazirani na korpusu dokumenata</li>
                <li>Citation guard proverava da LLM ne "halucinira"</li>
              </ul>
            </div>
          </div>
        </>
      )}

      {/* Embedding Tab */}
      {activeSubTab === "embedding" && <EmbeddingSettings />}

      {/* Reranker Tab */}
      {activeSubTab === "reranker" && <RerankerSettings />}

      {/* RAG Tab */}
      {activeSubTab === "rag" && <RAGSettings />}
    </>
  );
}

// Made with Bob
