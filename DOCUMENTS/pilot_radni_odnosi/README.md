# Pilot Korpus - Radni Odnosi i Zapošljavanje

## 📊 Osnovne Informacije

- **Oblast**: VII - Radni Odnosi i Zapošljavanje
- **Broj dokumenata**: 235 PDF fajlova
- **Izvor**: `D:\POSAO\OllamaProjects\LEGALFILES\zakoni_pdf\VII RADNI ODNOSI I ZAPOŠLJAVANJE`
- **Datum kreiranja**: 2026-06-03
- **Naming konvencija**: `radni_odnosi_XXXX_originalname.pdf`

## 🎯 Cilj Pilot Projekta

Ovaj pilot korpus služi za:
1. **Testiranje performansi** ZAIKON sistema sa realnim pravnim dokumentima
2. **Identifikaciju tipičnih konflikata** u oblasti radnih odnosa
3. **Optimizaciju RAG parametara** za pravne dokumente
4. **Merenje kvaliteta** detekcije konflikata i Q&A funkcionalnosti
5. **Procenu hardverskih zahteva** za skaliranje na pun korpus (7,053 dokumenata)

## 📋 Tipovi Dokumenata

Korpus sadrži različite tipove pravnih akata:
- **Zakoni** - Osnovni zakonski propisi
- **Uredbe** - Podzakonski akti Vlade
- **Pravilnici** - Detaljni propisi ministarstava
- **Odluke** - Pojedinačni akti
- **Strategije** - Dugoročni planski dokumenti

## 🔍 Očekivani Tipovi Konflikata

U oblasti radnih odnosa očekuju se sledeći tipovi konflikata:

### 1. Definicioni Konflikti
- Različite definicije "radnog odnosa"
- Različite definicije "zaposlenog"
- Konfliktne definicije "radnog vremena"

### 2. Konflikti Nadležnosti
- Nadležnost Ministarstva rada vs Ministarstva privrede
- Nadležnost republičkih vs pokrajinskih organa
- Nadležnost inspekcije rada

### 3. Proceduralni Konflikti
- Različiti postupci za zasnivanje radnog odnosa
- Konfliktne procedure za otkaz
- Različiti rokovi za žalbe

### 4. Konflikti Prava i Obaveza
- Konfliktna prava zaposlenih
- Konfliktne obaveze poslodavaca
- Suprotstavljeni uslovi rada

### 5. Sankcioni Konflikti
- Različite kazne za iste prekršaje
- Konfliktni iznosi novčanih kazni
- Suprotstavljene mere inspekcije

## 📈 Plan Testiranja

### Faza 1: Import i Ekstrakcija (Dan 1-3)
```bash
# Pokrenuti import kroz frontend ili API
POST /api/corpus/import
{
  "folder_path": "DOCUMENTS/pilot_radni_odnosi",
  "corpus_name": "Pilot - Radni Odnosi"
}
```

**Očekivani rezultati**:
- Uspešan import svih 235 dokumenata
- Ekstrakcija normativnih tvrdnji
- Kreiranje vektorskog indeksa
- Mapiranje međusobnih referenci

### Faza 2: Analiza Korpusa (Dan 4-5)
```bash
# Statistička analiza
GET /api/corpus/analysis?corpus_id=<id>
```

**Metrike za praćenje**:
- Prosečna dužina dokumenta
- Broj normativnih tvrdnji po dokumentu
- Broj referenci između dokumenata
- Distribucija po tipu akta

### Faza 3: Detekcija Konflikata (Dan 6-8)
```bash
# Pokrenuti detekciju konflikata
POST /api/conflicts/detect
{
  "corpus_id": "<id>",
  "rules": ["all"]
}
```

**Očekivani rezultati**:
- Lista detektovanih konflikata
- Kategorizacija po tipu konflikta
- Severity scoring
- Reference na izvorne dokumente

### Faza 4: Q&A Testiranje (Dan 9-10)
```bash
# Test upiti
POST /api/query
{
  "question": "Koji su uslovi za zasnivanje radnog odnosa?",
  "corpus_id": "<id>"
}
```

**Test upiti**:
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

### Faza 5: Evaluacija i Optimizacija (Dan 11-14)
- Manuelna verifikacija 50 random konflikata
- Izračunavanje precision/recall/F1
- Testiranje različitih RAG parametara
- Identifikacija novih pravila konflikata
- Dokumentovanje nalaza

## ⚙️ Preporučeni RAG Parametri za Testiranje

### Baseline (Default)
```python
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
SEARCH_SEMANTIC_WEIGHT = 0.7
SEARCH_BM25_WEIGHT = 0.3
SEARCH_TOP_K = 10
```

### Optimizovano za Pravne Dokumente
```python
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
SEARCH_SEMANTIC_WEIGHT = 0.6
SEARCH_BM25_WEIGHT = 0.4
SEARCH_TOP_K = 15
```

### Eksperimentalno
```python
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
SEARCH_SEMANTIC_WEIGHT = 0.5
SEARCH_BM25_WEIGHT = 0.5
SEARCH_TOP_K = 20
```

## 📊 Metrike za Praćenje

### Performanse
- **Import vreme**: Vreme potrebno za import svih dokumenata
- **Memorija**: Peak memorija tokom importa
- **Disk**: Veličina vektorskog indeksa
- **Query vreme**: Prosečno vreme odgovora na upit

### Kvalitet
- **Precision**: Tačnost detektovanih konflikata
- **Recall**: Pokrivenost stvarnih konflikata
- **F1 Score**: Harmonijska sredina precision i recall
- **Answer Quality**: Kvalitet odgovora na test upite (1-5)

### Ciljevi
- ✅ Import vreme: < 2 sata
- ✅ Query vreme: < 5 sekundi
- ✅ Precision: > 70%
- ✅ Recall: > 60%
- ✅ F1 Score: > 65%
- ✅ Answer Quality: > 3.5/5

## 🚀 Sledeći Koraci

Nakon uspešnog pilot projekta:

1. **Skaliranje na 500 dokumenata** (+265 iz drugih oblasti)
2. **Skaliranje na 1,000 dokumenata** (+500)
3. **Implementacija novih pravila** konflikata
4. **Optimizacija performansi**
5. **Finalno skaliranje na 7,053 dokumenata**

## 📝 Beleške

- Svi dokumenti su preimenovani sa prefiksom `radni_odnosi_XXXX_` da bi se izbegla duplikacija imena
- Originalna imena su sačuvana u sufiksu
- Dokumenti su kopirani, originali ostaju netaknuti
- Encoding problema sa ćiriličnim nazivima foldera rešen korišćenjem wildcard-a

## 🔗 Reference

- **Strategija dokumenta**: `CORPUS_STRATEGY.md`
- **Glavni projekat**: `IMPLEMENTATION_SUMMARY.md`
- **API dokumentacija**: `docs/master/MASTER_API_ENDPOINTS.md`
- **Conflict taxonomy**: `docs/master/MASTER_CONFLICT_TAXONOMY.md`

---

**Status**: ✅ Pilot korpus pripremljen i spreman za import
**Datum**: 2026-06-03
**Autor**: Bob (AI Assistant)