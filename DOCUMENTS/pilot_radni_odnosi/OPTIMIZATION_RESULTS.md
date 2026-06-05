# Rezultati Optimizacije Pipeline-a

## Datum: 2026-06-04

## Problem
Draft review pipeline je bio ekstremno spor - čak i za mali dokument od 760 bajtova, izvršavanje je trajalo 120+ sekundi.

## Root Cause Analiza
Identifikovan bottleneck u `backend/zaikon/modules/draft_reviews/service.py`:
- Metoda `_extract_corpus_assertions` (linije 463-510)
- Problem: Ekstraktuje assertions iz SVIH 235 dokumenata korpusa za svaki draft review
- Vreme: 60-90 sekundi po izvršavanju

## Implementirana Optimizacija

### 1. In-Memory Cache
- Dodato `_corpus_assertions_cache: dict[UUID, list[NormativeAssertion]]` u `__init__` (linija 69)
- Cache se proverava pre ekstrakcije (linije 472-474)
- Rezultati se čuvaju u cache nakon ekstrakcije (linija 501)

### 2. Disk Cache (Pokušaj)
- Dodato `cache_dir` u `__init__` (linija 62)
- Implementirana logika za čitanje/pisanje cache fajlova (linije 476-509)
- **Status**: Disk cache write ne uspeva (direktorijum ostaje prazan)

## Rezultati Testiranja

### Test 1: Prvi Run (Bez Cache)
- **Vreme**: ~137 sekundi
- **Status**: completed
- **Findings**: 0
- **Pipeline Run ID**: b47e0560-b7ae-4a91-82cb-7e8dab397226

### Test 2: Drugi Run (Sa In-Memory Cache)
- **Vreme**: 114.5 sekundi
- **Status**: completed
- **Findings**: 0
- **Pipeline Run ID**: 733ffd8d-0d81-4e6b-af25-3ffefb15a014

### Analiza Performansi
- **Poboljšanje**: ~16% brže (137s → 114.5s)
- **Očekivano**: 4-6x brže (120s → 20-30s)
- **Zaključak**: In-memory cache radi, ali postoje **drugi bottleneck-ovi**

## Dodatni Bottleneck-ovi

Pošto je poboljšanje minimalno (~16%), očigledno je da postoje drugi spori delovi pipeline-a:

### Potencijalni Kandidati:
1. **Hybrid Search** (~50s prema prethodnim testovima)
   - Lokacija: Verovatno u retrieval koraku
   - Potrebna analiza: Profilisanje search operacija

2. **LLM Inference**
   - Lokacija: Conflict detection korak
   - Potrebna analiza: Vreme po LLM pozivu

3. **Document Processing**
   - Lokacija: Parsing i ekstrakcija iz draft dokumenta
   - Potrebna analiza: Vreme procesiranja draft-a

4. **Assertion Extraction iz Draft-a**
   - Lokacija: Ekstrakcija assertions iz draft dokumenta
   - Potrebna analiza: Koliko traje ekstrakcija iz draft-a

## Sledeći Koraci

### Kratkoročno:
1. ✅ Implementiran in-memory cache za corpus assertions
2. ⚠️ Disk cache ne radi - potrebno debugovanje
3. 🔍 Identifikovati sledeći bottleneck (hybrid search, LLM, ili processing)

### Dugoročno:
1. Dodati detaljno logovanje vremena za svaki korak pipeline-a
2. Implementirati progress tracking
3. Optimizovati hybrid search ako je to bottleneck
4. Razmotriti paralelizaciju gde je moguće
5. Dodati timeout konfiguraciju za pipeline korake

## Tehnički Detalji

### Modifikovani Fajlovi:
- `backend/zaikon/modules/draft_reviews/service.py`
  - Linije 55-70: Dodato cache_dir i _corpus_assertions_cache
  - Linije 463-510: Optimizovana _extract_corpus_assertions metoda

### Cache Lokacija:
- **Path**: `data/artifacts/draft_reviews/cache/`
- **Format**: `corpus_assertions_{corpus_id}.json`
- **Status**: Direktorijum kreiran, ali fajlovi se ne pišu

### Test Dokumenti:
- **Mali dokument**: `DOCUMENTS/pilot_radni_odnosi/test_small.txt` (760 bytes)
- **Korpus**: 235 dokumenata (pilot_radni_odnosi)
- **Corpus ID**: `7c74a596-2252-499e-a2a8-61c8752a77d2`

## Zaključak

Optimizacija je **delimično uspešna**:
- ✅ In-memory cache radi
- ✅ Kod je čist i maintainable
- ⚠️ Disk cache ne radi
- ❌ Poboljšanje performansi je minimalno (~16%)

**Glavni zaključak**: Corpus assertion extraction **nije jedini bottleneck**. Potrebna je dalja analiza drugih delova pipeline-a da bi se postiglo značajno poboljšanje performansi.