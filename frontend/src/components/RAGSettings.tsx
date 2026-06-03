import React, { useEffect, useState } from "react";
import { Api, DEFAULT_API_BASE } from "../api";
import type { RAGConfig } from "../types";
import { AlertCircle, CheckCircle } from "lucide-react";

export const RAGSettings: React.FC = () => {
  const [apiBase] = useState(DEFAULT_API_BASE);
  const [config, setConfig] = useState<RAGConfig>({
    chunking_strategy: "semantic",
    chunk_size: 500,
    chunk_overlap: 50,
    search_type: "hybrid",
    search_semantic_weight: 0.7,
    search_bm25_weight: 0.3,
    search_top_k: 10
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await Api.getRAGConfig(apiBase);
      setConfig(data);
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to load RAG configuration"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);
      await Api.updateRAGConfig(apiBase, config);
      setMessage({ type: "success", text: "RAG configuration saved successfully" });
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to save RAG configuration"
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "var(--space-5)" }}>
        <div style={{ color: "var(--text-muted)" }}>Loading RAG configuration...</div>
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

      {/* Chunking Configuration */}
      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Document Chunking</h2>
            <p>Podešavanja za deljenje dokumenata na manje delove</p>
          </div>
        </div>

        <div className="form-grid">
          {/* Chunking Strategy */}
          <label>
            Chunking Strategy
            <select
              value={config.chunking_strategy}
              onChange={(e) => setConfig({ ...config, chunking_strategy: e.target.value })}
            >
              <option value="semantic">Semantic (Sentence-based)</option>
              <option value="fixed">Fixed Size</option>
            </select>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Semantic preserves sentence boundaries, Fixed uses character count
            </p>
          </label>

          {/* Chunk Size */}
          <label>
            Chunk Size
            <input
              type="number"
              value={config.chunk_size}
              onChange={(e) =>
                setConfig({ ...config, chunk_size: parseInt(e.target.value) || 500 })
              }
              min={100}
              max={2000}
              step={50}
            />
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Target size in characters (100-2000)
            </p>
          </label>

          {/* Chunk Overlap */}
          <label>
            Chunk Overlap
            <input
              type="number"
              value={config.chunk_overlap}
              onChange={(e) =>
                setConfig({ ...config, chunk_overlap: parseInt(e.target.value) || 50 })
              }
              min={0}
              max={500}
              step={10}
            />
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Overlap between consecutive chunks in characters (0-500)
            </p>
          </label>
        </div>
      </section>

      {/* Search Configuration */}
      <section className="panel">
        <div className="section-head">
          <div>
            <h2>Search Configuration</h2>
            <p>Podešavanja za pretragu i rangiranje rezultata</p>
          </div>
        </div>

        <div className="form-grid">
          {/* Search Type */}
          <label>
            Search Type
            <select
              value={config.search_type}
              onChange={(e) => setConfig({ ...config, search_type: e.target.value })}
            >
              <option value="hybrid">Hybrid (Semantic + Keyword)</option>
              <option value="semantic">Semantic Only</option>
              <option value="keyword">Keyword Only (BM25)</option>
            </select>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Hybrid combines semantic understanding with keyword matching
            </p>
          </label>

          {/* Semantic Weight */}
          {config.search_type === "hybrid" && (
            <label>
              Semantic Weight: {config.search_semantic_weight.toFixed(2)}
              <input
                type="range"
                value={config.search_semantic_weight}
                onChange={(e) =>
                  setConfig({ ...config, search_semantic_weight: parseFloat(e.target.value) })
                }
                min={0}
                max={1}
                step={0.05}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                <span>0.0 (Less semantic)</span>
                <span>1.0 (More semantic)</span>
              </div>
            </label>
          )}

          {/* BM25 Weight */}
          {config.search_type === "hybrid" && (
            <label>
              BM25 Weight: {config.search_bm25_weight.toFixed(2)}
              <input
                type="range"
                value={config.search_bm25_weight}
                onChange={(e) =>
                  setConfig({ ...config, search_bm25_weight: parseFloat(e.target.value) })
                }
                min={0}
                max={1}
                step={0.05}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                <span>0.0 (Less keyword)</span>
                <span>1.0 (More keyword)</span>
              </div>
              <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "8px" }}>
                Note: Weights should sum to 1.0 for balanced results
              </p>
            </label>
          )}

          {/* Top K */}
          <label>
            Top K Results
            <input
              type="number"
              value={config.search_top_k}
              onChange={(e) =>
                setConfig({ ...config, search_top_k: parseInt(e.target.value) || 10 })
              }
              min={1}
              max={100}
            />
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Number of top results to retrieve (1-100)
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
          <strong style={{ color: "var(--primary)" }}>ℹ️ About RAG Configuration</strong>
          <ul style={{ marginTop: "8px", paddingLeft: "20px", fontSize: "13px", color: "#0f675e" }}>
            <li><strong>Chunking:</strong> Breaks documents into smaller, searchable pieces</li>
            <li><strong>Semantic chunking:</strong> Respects sentence boundaries for better context</li>
            <li><strong>Overlap:</strong> Prevents information loss at chunk boundaries</li>
            <li><strong>Hybrid search:</strong> Combines semantic similarity with keyword matching</li>
            <li><strong>Semantic weight:</strong> Controls importance of meaning-based matching</li>
            <li><strong>BM25 weight:</strong> Controls importance of exact keyword matches</li>
          </ul>
        </div>
      </div>
    </>
  );
};

// Made with Bob
