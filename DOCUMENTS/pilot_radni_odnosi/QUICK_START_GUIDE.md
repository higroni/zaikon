# 🚀 Quick Start Guide - Pilot Korpus Testiranje

**Datum**: 2026-06-03  
**Corpus ID**: `7c74a596-2252-499e-a2a8-61c8752a77d2`  
**Status**: Faza 1 ✅ | Faza 2 ⚠️ Zahteva Qdrant

---

## ⚡ Problem Identifikovan

**Root Cause**: Qdrant server nije pokrenut, što blokira sve search funkcionalnosti.

```
❌ Qdrant server: http://localhost:6333 - NOT RUNNING
✅ Backend API: http://127.0.0.1:8100 - RUNNING
✅ Frontend: http://127.0.0.1:5173 - RUNNING
✅ Corpus imported: 235 documents - READY
```

---

## 🔧 Rešenje - Pokretanje Qdrant-a

### Opcija 1: Docker (Preporučeno)
```bash
# Pokrenuti Qdrant u Docker kontejneru
docker run -p 6333:6333 -p 6334:6334 \
    -v d:/POSAO/OllamaProjects/ZAIKON/data/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### Opcija 2: Standalone Binary
```bash
# Preuzeti Qdrant binary sa https://github.com/qdrant/qdrant/releases
# Pokrenuti:
./qdrant --storage-path ./data/qdrant_storage
```

### Opcija 3: Python Embedded Mode
Ako Qdrant podržava embedded mode kroz Python client, backend bi trebalo automatski da ga pokrene.

---

## ✅ Verifikacija

Nakon pokretanja Qdrant-a:

```bash
# 1. Proveriti Qdrant health
curl http://localhost:6333/

# 2. Listati kolekcije
curl http://localhost:6333/collections

# 3. Proveriti korpus kolekciju
curl http://localhost:6333/collections/7c74a596-2252-499e-a2a8-61c8752a77d2
```

Očekivani output:
```json
{
  "title": "qdrant - vector search engine",
  "version": "1.x.x"
}
```

---

## 🧪 Pokretanje Testova

Kada je Qdrant aktivan:

### 1. Q&A Test (Automatski)
```bash
python scripts/test_qa_pilot.py
```

**Očekivani rezultati**:
- Search Success Rate: > 90%
- Average Response Time: < 5s
- 5-10 relevantnih rezultata po upitu

### 2. Manuelno Testiranje (Frontend)

Otvoriti: http://127.0.0.1:5173

**Test Upiti** (iz README.md):
1. "Koji su uslovi za zasnivanje radnog odnosa?"
2. "Kakve su obaveze poslodavca prema zaposlenom?"
3. "Koji su razlozi za otkaz ugovora o radu?"
4. "Koliko iznosi minimalna zarada?"
5. "Koja su prava zaposlenog na godišnji odmor?"
6. "Kako se vrši inspekcijski nadzor?"
7. "Koje su kazne za nepoštovanje zakona o radu?"
8. "Kako se rešavaju radni sporovi?"
9. "Šta je radno vreme i kako se određuje?"
10. "Koja su prava trudnica i porodilja?"

**Ocenjivanje** (za svaki upit):
- Relevantnost rezultata: 1-5
- Broj relevantnih rezultata: 0-10
- Vreme odgovora: < 5s = ✅

---

## 📊 Očekivani Rezultati

### Faza 1 - Import ✅ ZAVRŠENO
- ✅ 235 dokumenata importovano
- ✅ 45,397 pravnih jedinica ekstrahovano
- ✅ 4 indeksa kreirana
- ✅ 78.3% referenci razrešeno

### Faza 2 - Q&A Testiranje ⏳ PENDING
**Kada se Qdrant pokrene**:
- Search Success Rate: > 90%
- Average Response Time: < 5s
- Average Results per Query: 5-10
- Answer Quality: > 3.5/5

### Faza 3 - Conflict Detection ⏳ PENDING
**Kroz Draft Review proces**:
- Detected Conflicts: 50-200
- Conflict Types: 8 tipova
- Precision: > 70%
- Recall: > 60%

---

## 🐛 Troubleshooting

### Problem: Qdrant se ne pokreće
```bash
# Proveriti da li port 6333 nije zauzet
netstat -ano | findstr :6333

# Ako jeste, zaustaviti proces ili promeniti port u config.py
```

### Problem: Search i dalje timeout-uje
```bash
# Proveriti backend logove
Get-Content backend-dev.log -Tail 50

# Restartovati backend
# (zaustaviti startserver.bat i ponovo pokrenuti)
```

### Problem: Nema rezultata u search-u
```bash
# Proveriti da li kolekcija postoji
curl http://localhost:6333/collections/7c74a596-2252-499e-a2a8-61c8752a77d2

# Ako ne postoji, možda treba re-import
# (obrisati korpus i ponovo importovati)
```

---

## 📁 Važni Fajlovi

### Izvještaji
- `DOCUMENTS/pilot_radni_odnosi/PHASE1_REPORT.md` - Kompletan izvještaj Faze 1
- `DOCUMENTS/pilot_radni_odnosi/PHASE2_STATUS.md` - Status i problemi Faze 2
- `DOCUMENTS/pilot_radni_odnosi/phase1_analysis_report.json` - JSON podaci

### Skripte
- `scripts/test_qa_pilot.py` - Automatski Q&A test
- `scripts/analyze_corpus_api.py` - Analiza korpusa
- `scripts/list_corpora.py` - Lista svih korpusa

### Konfiguracija
- `backend/zaikon/core/config.py` - Backend konfiguracija
- `backend/data/artifacts/corpus/corpora.json` - Korpus metadata
- `data/qdrant_storage/` - Qdrant lokalni storage

---

## 🎯 Sledeći Koraci

1. **Pokrenuti Qdrant** (Docker ili standalone)
2. **Verifikovati konekciju** (curl testovi)
3. **Pokrenuti Q&A testove** (automatski ili manuelno)
4. **Dokumentovati rezultate**
5. **Započeti Fazu 3** (Conflict Detection)

---

## 📞 Dodatna Pomoć

Ako problemi perzistiraju:

1. **Proveriti logove**:
   ```bash
   Get-Content backend-dev.log -Tail 100
   Get-Content backend-dev.err.log -Tail 100
   ```

2. **Proveriti Qdrant logove** (ako je u Docker-u):
   ```bash
   docker logs <container_id>
   ```

3. **Testirati direktno kroz Python**:
   ```python
   from qdrant_client import QdrantClient
   client = QdrantClient(url="http://localhost:6333")
   print(client.get_collections())
   ```

---

**Pripremio**: Bob (AI Assistant)  
**Workspace**: `D:/POSAO/OllamaProjects/ZAIKON`  
**Datum**: 2026-06-03