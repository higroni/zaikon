import React, { useEffect, useState } from "react";
import { Api, DEFAULT_API_BASE } from "../api";
import type { RerankerConfig } from "../types";
import { AlertCircle, CheckCircle } from "lucide-react";

const POPULAR_RERANKER_MODELS = [
  { name: "BAAI/bge-reranker-v2-m3", description: "Multilingual, state-of-the-art" },
  { name: "BAAI/bge-reranker-large", description: "English, high accuracy" },
  { name: "BAAI/bge-reranker-base", description: "English, balanced" },
  { name: "cross-encoder/ms-marco-MiniLM-L-6-v2", description: "Fast, MS MARCO trained" },
  { name: "cross-encoder/ms-marco-MiniLM-L-12-v2", description: "Accurate, MS MARCO trained" }
];

export const RerankerSettings: React.FC = () => {
  const [apiBase] = useState(DEFAULT_API_BASE);
  const [config, setConfig] = useState<RerankerConfig>({
    reranker_model: "BAAI/bge-reranker-v2-m3",
    reranker_batch_size: 32,
    reranker_device: "cuda",
    reranking_enabled: true,
    reranking_top_n: 10
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [customModel, setCustomModel] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await Api.getRerankerConfig(apiBase);
      setConfig(data);
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to load reranker configuration"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);
      await Api.updateRerankerConfig(apiBase, config);
      setMessage({ type: "success", text: "Reranker configuration saved successfully" });
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to save reranker configuration"
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "var(--space-5)" }}>
        <div style={{ color: "var(--text-muted)" }}>Loading reranker configuration...</div>
      </div>
    );
  }

  return (
    <>
      {message && (
        <div className={`status-pill ${message.type}`} style={{ width: "100%", height: "auto", padding: "var(--space-3)", marginBottom: "var(--space-4)" }}>
          {message.type === "success" ? <CheckCircle size={20} style={{ flexShrink: 0 }} /> : <AlertCircle size={20} style={{ flexShrink: 0 }} />}
          <div>
            <strong>{message.type === "success" ? "Uspešno" : "Greška"}</strong>
            <p style={{ marginTop: "4px", fontSize: "13px" }}>{message.text}</p>
          </div>
        </div>
      )}

      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Reranker Model Configuration</h2>
            <p>Podešavanja za reranker model koji poboljšava relevantnost rezultata</p>
          </div>
        </div>

        <div className="form-grid">
          {/* Enable Reranking Toggle */}
          <label style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "var(--space-3)", background: "var(--surface-muted)", borderRadius: "var(--radius)" }}>
            <div>
              <div style={{ fontWeight: "700", marginBottom: "4px" }}>Enable Reranking</div>
              <div style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: "normal" }}>
                Use reranker to improve search result relevance
              </div>
            </div>
            <input
              type="checkbox"
              checked={config.reranking_enabled}
              onChange={(e) => setConfig({ ...config, reranking_enabled: e.target.checked })}
              style={{ width: "auto", marginLeft: "var(--space-3)" }}
            />
          </label>

          {/* Model Name */}
          <label>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span>Model Name</span>
              <button
                type="button"
                onClick={() => setCustomModel(!customModel)}
                disabled={!config.reranking_enabled}
                style={{ 
                  width: "auto", 
                  height: "28px", 
                  padding: "0 8px", 
                  fontSize: "12px",
                  background: "transparent",
                  border: "none",
                  color: config.reranking_enabled ? "var(--primary)" : "var(--text-soft)",
                  cursor: config.reranking_enabled ? "pointer" : "not-allowed"
                }}
              >
                {customModel ? "Use preset" : "Custom model"}
              </button>
            </div>
            {customModel ? (
              <input
                type="text"
                value={config.reranker_model}
                onChange={(e) => setConfig({ ...config, reranker_model: e.target.value })}
                disabled={!config.reranking_enabled}
                placeholder="e.g., BAAI/bge-reranker-v2-m3"
              />
            ) : (
              <select
                value={config.reranker_model}
                onChange={(e) => setConfig({ ...config, reranker_model: e.target.value })}
                disabled={!config.reranking_enabled}
              >
                {POPULAR_RERANKER_MODELS.map((model) => (
                  <option key={model.name} value={model.name}>
                    {model.name} - {model.description}
                  </option>
                ))}
              </select>
            )}
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              {customModel ? "HuggingFace model identifier" : "Popular reranker models"}
            </p>
          </label>

          {/* Batch Size */}
          <label>
            Batch Size
            <input
              type="number"
              value={config.reranker_batch_size}
              onChange={(e) =>
                setConfig({ ...config, reranker_batch_size: parseInt(e.target.value) || 32 })
              }
              min={1}
              max={256}
              disabled={!config.reranking_enabled}
            />
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Number of query-document pairs to process in parallel (1-256)
            </p>
          </label>

          {/* Device */}
          <label>
            Device
            <select
              value={config.reranker_device}
              onChange={(e) => setConfig({ ...config, reranker_device: e.target.value })}
              disabled={!config.reranking_enabled}
            >
              <option value="cuda">CUDA (GPU)</option>
              <option value="cpu">CPU</option>
            </select>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Hardware device for model inference
            </p>
          </label>

          {/* Top N */}
          <label>
            Top N Results
            <input
              type="number"
              value={config.reranking_top_n}
              onChange={(e) =>
                setConfig({ ...config, reranking_top_n: parseInt(e.target.value) || 10 })
              }
              min={1}
              max={100}
              disabled={!config.reranking_enabled}
            />
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Number of top results to rerank (1-100)
            </p>
          </label>

          {/* Save Button */}
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            style={{ justifySelf: "start" }}
          >
            {saving ? "Saving..." : "Save Configuration"}
          </button>
        </div>
      </section>

      {/* Info Panel */}
      <div className="status-pill" style={{ width: "100%", height: "auto", padding: "var(--space-3)", background: "var(--primary-soft)", borderColor: "#a8d5cb" }}>
        <div>
          <strong style={{ color: "var(--primary)" }}>ℹ️ About Reranking</strong>
          <ul style={{ marginTop: "8px", paddingLeft: "20px", fontSize: "13px", color: "#0f675e" }}>
            <li>Reranking refines initial search results by computing precise relevance scores</li>
            <li>BAAI/bge-reranker-v2-m3 is a cross-encoder model for accurate ranking</li>
            <li>Reranking is more computationally expensive than initial retrieval</li>
            <li>Top N controls how many initial results are reranked (balance speed vs quality)</li>
            <li>GPU acceleration is highly recommended for reranking operations</li>
          </ul>
        </div>
      </div>
    </>
  );
};

// Made with Bob
