import React, { useEffect, useState } from "react";
import { Api, DEFAULT_API_BASE } from "../api";
import type { EmbeddingConfig } from "../types";
import { AlertCircle, CheckCircle } from "lucide-react";

const POPULAR_EMBEDDING_MODELS = [
  { name: "BAAI/bge-m3", dimensions: 1024, description: "Multilingual, 100+ languages" },
  { name: "BAAI/bge-large-en-v1.5", dimensions: 1024, description: "English, high quality" },
  { name: "BAAI/bge-base-en-v1.5", dimensions: 768, description: "English, balanced" },
  { name: "BAAI/bge-small-en-v1.5", dimensions: 384, description: "English, fast" },
  { name: "sentence-transformers/all-MiniLM-L6-v2", dimensions: 384, description: "Fast, general purpose" },
  { name: "sentence-transformers/all-mpnet-base-v2", dimensions: 768, description: "High quality, general" },
  { name: "intfloat/e5-large-v2", dimensions: 1024, description: "E5 family, large" },
  { name: "intfloat/e5-base-v2", dimensions: 768, description: "E5 family, base" }
];

export const EmbeddingSettings: React.FC = () => {
  const [apiBase] = useState(DEFAULT_API_BASE);
  const [config, setConfig] = useState<EmbeddingConfig>({
    embedding_model: "BAAI/bge-m3",
    embedding_dimensions: 1024,
    embedding_batch_size: 128,
    embedding_device: "cuda",
    embedding_precision: "fp16"
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
      const data = await Api.getEmbeddingConfig(apiBase);
      setConfig(data);
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to load embedding configuration"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);
      await Api.updateEmbeddingConfig(apiBase, config);
      setMessage({ type: "success", text: "Embedding configuration saved successfully" });
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to save embedding configuration"
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "var(--space-5)" }}>
        <div style={{ color: "var(--text-muted)" }}>Loading embedding configuration...</div>
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
            <h2>Embedding Model Configuration</h2>
            <p>Podešavanja za embedding model koji konvertuje tekst u vektore</p>
          </div>
        </div>

        <div className="form-grid">
          {/* Model Name */}
          <label>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span>Model Name</span>
              <button
                type="button"
                onClick={() => setCustomModel(!customModel)}
                style={{ 
                  width: "auto", 
                  height: "28px", 
                  padding: "0 8px", 
                  fontSize: "12px",
                  background: "transparent",
                  border: "none",
                  color: "var(--primary)",
                  cursor: "pointer"
                }}
              >
                {customModel ? "Use preset" : "Custom model"}
              </button>
            </div>
            {customModel ? (
              <input
                type="text"
                value={config.embedding_model}
                onChange={(e) => setConfig({ ...config, embedding_model: e.target.value })}
                placeholder="e.g., BAAI/bge-m3"
              />
            ) : (
              <select
                value={config.embedding_model}
                onChange={(e) => {
                  const selectedModel = POPULAR_EMBEDDING_MODELS.find(m => m.name === e.target.value);
                  setConfig({ 
                    ...config, 
                    embedding_model: e.target.value,
                    embedding_dimensions: selectedModel?.dimensions || config.embedding_dimensions
                  });
                }}
              >
                {POPULAR_EMBEDDING_MODELS.map((model) => (
                  <option key={model.name} value={model.name}>
                    {model.name} - {model.description}
                  </option>
                ))}
              </select>
            )}
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              {customModel ? "HuggingFace model identifier" : "Popular embedding models"}
            </p>
          </label>

          {/* Dimensions */}
          <label>
            Embedding Dimensions
            <input
              type="number"
              value={config.embedding_dimensions}
              onChange={(e) =>
                setConfig({ ...config, embedding_dimensions: parseInt(e.target.value) || 1024 })
              }
              min={128}
              max={4096}
              step={128}
            />
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Vector dimensions (128-4096, typically 768 or 1024)
            </p>
          </label>

          {/* Batch Size */}
          <label>
            Batch Size
            <input
              type="number"
              value={config.embedding_batch_size}
              onChange={(e) =>
                setConfig({ ...config, embedding_batch_size: parseInt(e.target.value) || 128 })
              }
              min={1}
              max={512}
            />
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Number of texts to process in parallel (1-512)
            </p>
          </label>

          {/* Device */}
          <label>
            Device
            <select
              value={config.embedding_device}
              onChange={(e) => setConfig({ ...config, embedding_device: e.target.value })}
            >
              <option value="cuda">CUDA (GPU)</option>
              <option value="cpu">CPU</option>
            </select>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Hardware device for model inference
            </p>
          </label>

          {/* Precision */}
          <label>
            Precision
            <select
              value={config.embedding_precision}
              onChange={(e) => setConfig({ ...config, embedding_precision: e.target.value })}
            >
              <option value="fp16">FP16 (Half Precision)</option>
              <option value="fp32">FP32 (Full Precision)</option>
            </select>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Floating point precision (FP16 is faster, FP32 is more accurate)
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
          <strong style={{ color: "var(--primary)" }}>ℹ️ About Embedding Models</strong>
          <ul style={{ marginTop: "8px", paddingLeft: "20px", fontSize: "13px", color: "#0f675e" }}>
            <li>Embedding models convert text into numerical vectors for semantic search</li>
            <li>BAAI/bge-m3 is a multilingual model supporting 100+ languages</li>
            <li>Higher dimensions provide more nuanced representations but require more memory</li>
            <li>GPU (CUDA) is recommended for faster processing of large document sets</li>
            <li>FP16 precision reduces memory usage by ~50% with minimal accuracy loss</li>
          </ul>
        </div>
      </div>
    </>
  );
};

// Made with Bob
