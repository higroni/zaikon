# LLM Module

Owns LLM-assisted behavior.

LLM roles:

- intent parsing
- query planning
- query expansion
- Serbian-language explanations
- drafting suggestions
- citation guard

LLM output must be grounded in retrieved evidence.

Current MVP behavior:

- deterministic intent parsing, query expansion, answer generation, and revision
  suggestions are always available
- Ollama provider calls are available behind `ZAIKON_LLM_USE_PROVIDER=true`
- when provider output is unavailable, grounded deterministic answers remain the
  fallback
- generated answers include citation guard metadata; ungrounded answers are
  marked when no citations are available

