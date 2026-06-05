# Pipeline Timeout Fix - Implementation Report

**Date**: 2026-06-05  
**Status**: ✅ **IMPLEMENTED**

---

## 🎯 Problem

Draft review pipeline se zaglavljuje na velikim dokumentima (89 stranica) bez timeout mehanizma:
- Status ostaje `running` 30+ minuta
- Nema automatskog timeout-a
- Nema progress tracking-a
- Bottleneck: **Step 13: Hybrid Search** sa velikim query-jem

---

## ✅ Rešenje Implementirano

### 1. Timeout Konfiguracija

**File**: [`backend/zaikon/core/config.py`](../../backend/zaikon/core/config.py)

Dodati novi parametri:
```python
# Pipeline Timeout Settings
pipeline_step_timeout: int = 300  # 5 minutes per step
pipeline_total_timeout: int = 600  # 10 minutes total
pipeline_enable_timeout: bool = True
```

**Environment Variables**:
- `ZAIKON_PIPELINE_STEP_TIMEOUT` - Timeout po koraku (default: 300s)
- `ZAIKON_PIPELINE_TOTAL_TIMEOUT` - Ukupan timeout (default: 600s)
- `ZAIKON_PIPELINE_ENABLE_TIMEOUT` - Enable/disable (default: True)

### 2. Timeout Mehanizam

**File**: [`backend/zaikon/pipeline/chains.py`](../../backend/zaikon/pipeline/chains.py)

**Implementirano**:
- `PipelineTimeoutError` exception class
- Time tracking za svaki korak
- Time tracking za ukupan pipeline
- Warning logging za spore korake
- Graceful failure sa detaljnim error messages

**Key Features**:
```python
# Per-step timing
step_start_time = time.time()
context = step.run(context)
step_elapsed = time.time() - step_start_time

# Total pipeline timeout check
elapsed = time.time() - pipeline_start_time
if elapsed > total_timeout:
    raise PipelineTimeoutError(...)
```

### 3. Error Handling

**File**: [`backend/zaikon/modules/draft_reviews/service.py`](../../backend/zaikon/modules/draft_reviews/service.py)

**Implementirano**:
- Catch `PipelineTimeoutError` posebno
- Sačuvaj timings u metadata
- Postavi status na `failed` sa detaljima
- Log error sa pipeline_run_id

**Metadata Structure**:
```json
{
  "error": "Pipeline timeout: ...",
  "error_type": "timeout",
  "timings": {
    "load_content": 0.05,
    "normalize_text": 0.02,
    "classify_document": 1.23,
    "parse_legal_structure": 2.45,
    "canonicalize": 0.15,
    "extract_draft_assertions": 3.67,
    "extract_references": 1.89,
    "extract_corpus_assertions": 0.12,
    "evaluate_conflicts": 5.43,
    "resolve_references": 2.11,
    "run_checkers": 4.56,
    "hybrid_search": 52.34,
    "attach_evidence": 0.23,
    "save_results": 0.45,
    "total": 74.70
  }
}
```

---

## 🧪 Testiranje

### Test Script

**File**: [`scripts/test_pipeline_timeout.py`](../../scripts/test_pipeline_timeout.py)

**Funkcionalnost**:
1. Kreira draft review sa malim test dokumentom
2. Pokreće pipeline
3. Meri vreme izvršavanja
4. Prikazuje performance breakdown
5. Verifikuje da timeout radi

**Pokretanje**:
```powershell
python scripts/test_pipeline_timeout.py
```

### Test Scenariji

1. **Small Document** (10 linija)
   - Očekivano: Završi za <30s
   - Timeout: Ne bi trebalo da se desi

2. **Medium Document** (20-30 stranica)
   - Očekivano: Završi za 1-3 minute
   - Timeout: Ne bi trebalo da se desi

3. **Large Document** (89 stranica)
   - Očekivano: Može trajati 5-10 minuta
   - Timeout: Može se desiti ako hybrid search traje >5min

---

## 📊 Performance Insights

### Bottleneck Identifikovan

**Step 13: Hybrid Search** (`_retrieve_related_corpus_units`)
- Poziva se sa **celim dokumentom** kao query
- Embedding model cold start: 50-120s
- Veliki query (168K karaktera): dodatnih 30-60s
- **Total**: 80-180s samo za ovaj korak

### Optimizacije za Buduće

1. **Chunking Strategy**
   - Ne slati ceo dokument kao query
   - Koristiti samo naslove članaka + prvi paragraf
   - Ili: Top 10 najvažnijih delova

2. **Embedding Cache**
   - Cache embeddings za često korišćene upite
   - Smanjiti cold start overhead

3. **Parallel Processing**
   - Paralelizovati neke korake (npr. checkers)
   - Koristiti async/await gde je moguće

---

## 🔧 Konfiguracija

### Development (Default)
```python
pipeline_step_timeout = 300  # 5 minutes
pipeline_total_timeout = 600  # 10 minutes
pipeline_enable_timeout = True
```

### Production (Recommended)
```python
pipeline_step_timeout = 180  # 3 minutes
pipeline_total_timeout = 300  # 5 minutes
pipeline_enable_timeout = True
```

### Testing/Debug
```python
pipeline_step_timeout = 600  # 10 minutes
pipeline_total_timeout = 1200  # 20 minutes
pipeline_enable_timeout = False  # Disable for debugging
```

---

## 📝 Logging

### Step Timing
```
[pipeline_run_id] Running step extract_draft_assertions
[pipeline_run_id] Completed step extract_draft_assertions in 3.67s
```

### Timeout Warning
```
[pipeline_run_id] WARNING: Step hybrid_search took 320.5s (timeout: 300s)
```

### Timeout Error
```
[pipeline_run_id] ERROR: Pipeline timeout: Pipeline total timeout (600s) exceeded after 625.3s
```

### Performance Summary
```
[pipeline_run_id] ===== PERFORMANCE SUMMARY =====
[pipeline_run_id] hybrid_search                : 320.50s ( 51.2%)
[pipeline_run_id] evaluate_conflicts           :  85.30s ( 13.6%)
[pipeline_run_id] run_checkers                 :  45.20s (  7.2%)
[pipeline_run_id] ...
[pipeline_run_id] total                        : 625.30s (100.0%)
[pipeline_run_id] ==============================
```

---

## ✅ Success Criteria

- [x] Timeout konfiguracija dodana u [`config.py`](../../backend/zaikon/core/config.py)
- [x] Timeout mehanizam implementiran u [`PipelineChain`](../../backend/zaikon/pipeline/chains.py)
- [x] Error handling u [`draft_reviews/service.py`](../../backend/zaikon/modules/draft_reviews/service.py)
- [x] Test script kreiran: [`test_pipeline_timeout.py`](../../scripts/test_pipeline_timeout.py)
- [x] Dokumentacija kompletna
- [ ] Testiranje sa malim dokumentom
- [ ] Testiranje sa srednjim dokumentom
- [ ] Testiranje sa velikim dokumentom
- [ ] Validacija timeout behavior-a

---

## 🚀 Sledeći Koraci

### Prioritet 1: Testiranje
1. Pokrenuti backend server
2. Testirati sa [`test_pipeline_timeout.py`](../../scripts/test_pipeline_timeout.py)
3. Verifikovati da timeout radi
4. Testirati sa različitim veličinama dokumenata

### Prioritet 2: Optimizacija Hybrid Search
1. Implementirati chunking strategiju
2. Koristiti samo ključne delove dokumenta
3. Dodati embedding cache
4. Meriti performance improvement

### Prioritet 3: Progress Tracking
1. Dodati progress callback u `PipelineContext`
2. Emitovati progress events
3. Prikazati progress u frontend-u
4. Omogućiti cancellation

---

## 📁 Izmenjeni Fajlovi

1. [`backend/zaikon/core/config.py`](../../backend/zaikon/core/config.py) - Timeout settings
2. [`backend/zaikon/pipeline/chains.py`](../../backend/zaikon/pipeline/chains.py) - Timeout mehanizam
3. [`backend/zaikon/modules/draft_reviews/service.py`](../../backend/zaikon/modules/draft_reviews/service.py) - Error handling
4. [`scripts/test_pipeline_timeout.py`](../../scripts/test_pipeline_timeout.py) - Test script (NEW)
5. [`DOCUMENTS/pilot_radni_odnosi/PIPELINE_TIMEOUT_FIX.md`](PIPELINE_TIMEOUT_FIX.md) - Dokumentacija (NEW)

---

**Pripremio**: Bob (AI Assistant)  
**Workspace**: `D:/POSAO/OllamaProjects/ZAIKON`  
**Datum**: 2026-06-05  
**Status**: ✅ **READY FOR TESTING**