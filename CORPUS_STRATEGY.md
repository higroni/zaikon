# ZAIKON - Strategija za Rad sa Velikim Korpusom Pravnih Dokumenata

## 📊 Analiza Korpusa

### Trenutno Stanje
- **Lokacija**: `D:\POSAO\OllamaProjects\LEGALFILES\zakoni_pdf`
- **Ukupno dokumenata**: 7,053 PDF fajlova
- **Struktura**: 12 glavnih kategorija pravnih oblasti
- **Format**: Strukturirani PDF dokumenti sa metapodacima u manifest.csv

### Kategorije Korpusa
1. **I - Državno Uređenje** (Ustav, državna organizacija)
2. **II - Odbrана, Vojska i Unutrašnji Poslovi**
3. **III - Pravosuđe, Kazneno Zakonodavstvo**
4. **IV - Javni Prihodi**
5. **V - Monetarni Sistem, Finansije**
6. **VI - Svojinski i Obligacioni Odnosi**
7. **VII - Radni Odnosi i Zapošljavanje**
8. **VIII - Razvoj**
9. **IX - Opšti Privredni Propisi**
10. **X - Dobra od Opšteg Interesa i Životna Sredina**
11. **XI - Trgovina, Turizam, Ugostiteljstvo**
12. **XII - Građevinarstvo i Komunalne Delatnosti**

---

## 🎯 Strategija Implementacije

### FAZA 1: Pilot Projekat (2-4 nedelje)

#### 1.1 Izbor Pilot Korpusa
**Preporuka: 100-200 dokumenata iz 2-3 povezane oblasti**

**Predložene oblasti za pilot**:
- **Opcija A (Šumarstvo + Životna Sredina)**: 
  - X - Dobra od Opšteg Interesa i Životna Sredina
  - Fokus na zakone o šumama, zaštiti prirode
  - ~150 dokumenata
  - **Prednost**: Već imate test dokumente iz ove oblasti

- **Opcija B (Građevinarstvo + Prostorno Planiranje)**:
  - XII - Građevinarstvo i Komunalne Delatnosti
  - ~200 dokumenata
  - **Prednost**: Visok stepen međusobnih referenci i potencijalnih konflikata

- **Opcija C (Radni Odnosi)**:
  - VII - Radni Odnosi i Zapošljavanje
  - ~150 dokumenata
  - **Prednost**: Česte izmene, mnogo podzakonskih akata

#### 1.2 Ciljevi Pilot Projekta
1. **Testiranje performansi** sistema sa realnim korpusom
2. **Identifikacija tipičnih konflikata** u odabranoj oblasti
3. **Optimizacija RAG parametara** za pravne dokumente
4. **Merenje kvaliteta** odgovora i detekcije konflikata
5. **Procena hardverskih zahteva** za pun korpus

---

### FAZA 2: Analiza i Optimizacija (1-2 nedelje)

#### 2.1 Preliminarna Analiza Korpusa

**Zadaci**:
```python
# Pseudo-kod za analizu
1. Ekstrakcija metapodataka iz manifest.csv
2. Analiza distribucije dokumenata po kategorijama
3. Identifikacija najčešćih tipova akata (Zakon, Uredba, Pravilnik, Odluka)
4. Mapiranje međusobnih referenci između dokumenata
5. Analiza temporalne distribucije (godine donošenja)
```

**Alati za analizu**:
- Koristiti postojeći `folder_import` pipeline step
- Dodati statistički modul za analizu korpusa
- Generisati izveštaj o strukturi korpusa

#### 2.2 Identifikacija Novih Pravila Konflikata

**Metod**:
1. **Automatska detekcija** potencijalnih konflikata na pilot korpusu
2. **Manuelna verifikacija** top 50 detektovanih konflikata
3. **Kategorizacija** novih tipova konflikata
4. **Kreiranje gold cases** za nove tipove konflikata
5. **Implementacija** novih pravila u `active_rules.json`

**Očekivani novi tipovi konflikata**:
- Konflikti između različitih nivoa propisa (Zakon vs Uredba vs Pravilnik)
- Temporalni konflikti (stariji vs noviji propisi)
- Konflikti nadležnosti između ministarstava
- Konflikti između republičkih i pokrajinskih propisa

---

### FAZA 3: Skaliranje na Pun Korpus (2-3 nedelje)

#### 3.1 Postepeno Uvođenje

**Strategija postepenog skaliranja**:
```
Iteracija 1: 200 dokumenata (pilot)
Iteracija 2: 500 dokumenata (+300)
Iteracija 3: 1,000 dokumenata (+500)
Iteracija 4: 2,000 dokumenata (+1,000)
Iteracija 5: 5,000 dokumenata (+3,000)
Iteracija 6: 7,053 dokumenata (pun korpus)
```

**Razlozi za postepeno skaliranje**:
- Monitoring performansi na svakom nivou
- Identifikacija bottleneck-ova
- Optimizacija pre nego što postane problem
- Mogućnost rollback-a ako nešto ne radi

#### 3.2 Batch Processing

**Preporuka**: Procesirati dokumente u batch-evima od 100-200 dokumenata

```python
# Pseudo-kod
for batch in corpus.batches(size=100):
    job_id = import_batch(batch)
    monitor_progress(job_id)
    if success:
        continue
    else:
        log_error_and_retry(batch)
```

---

## 💻 Hardverski Zahtevi i Optimizacija

### Trenutni Hardware
**Potrebno**: Specifikacije vašeg računara
- CPU: ?
- RAM: ?
- GPU: ?
- Disk: ?

### Procena Zahteva za Pun Korpus

#### Scenario A: Lokalni Ollama (Preporučeno za Početak)
```
Model: llama3.2:3b (default)
Embedding: BAAI/bge-m3 (768 dim)
Reranker: BAAI/bge-reranker-v2-m3

Procenjeni zahtevi:
- RAM: 16GB minimum, 32GB preporučeno
- Disk: 50GB za vektore + 20GB za dokumente
- GPU: Opciono, ali ubrzava 3-5x
- Vreme procesiranja: ~10-15 sati za pun korpus (bez GPU)
```

#### Scenario B: Cloud Embedding + Lokalni LLM
```
Embedding: OpenAI text-embedding-3-large (3072 dim)
LLM: Lokalni Ollama llama3.2:3b

Prednosti:
- Brže procesiranje (paralelizacija)
- Bolji kvalitet embeddings-a
- Manji lokalni zahtevi

Mane:
- Troškovi API poziva (~$50-100 za pun korpus)
- Zavisnost od interneta
```

#### Scenario C: Potpuno Cloud Rešenje
```
Embedding: OpenAI text-embedding-3-large
LLM: GPT-4o-mini ili Claude 3.5 Sonnet
Reranker: Cohere rerank-v3

Prednosti:
- Najbolji kvalitet
- Najbrže procesiranje
- Bez lokalnih zahteva

Mane:
- Visoki troškovi (~$200-500 za pun korpus)
- Privacy concerns za osetljive dokumente
```

### Preporuka za Vaš Slučaj

**Hibridni Pristup (Najbolji odnos cena/kvalitet)**:
1. **Embedding**: Lokalni BAAI/bge-m3 (besplatno, dovoljno dobar)
2. **LLM**: Lokalni Ollama llama3.2:3b za većinu zadataka
3. **LLM (kompleksni zadaci)**: Cloud GPT-4o-mini samo za složene analize
4. **Reranker**: Lokalni BAAI/bge-reranker-v2-m3

---

## ⚙️ Optimizacija RAG Parametara

### Trenutni Default Settings

```python
# Iz config.py
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIMENSIONS = 1024

RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RERANKER_ENABLED = True

CHUNKING_STRATEGY = "semantic"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

SEARCH_TYPE = "hybrid"
SEARCH_SEMANTIC_WEIGHT = 0.7
SEARCH_BM25_WEIGHT = 0.3
SEARCH_TOP_K = 10
```

### Preporučene Izmene za Pravne Dokumente

#### 1. Chunking Parametri
```python
# Pravni dokumenti imaju duge rečenice i složenu strukturu
CHUNK_SIZE = 800  # Povećati sa 500 na 800
CHUNK_OVERLAP = 100  # Povećati sa 50 na 100

# Razlog: Pravni članci često zahtevaju više konteksta
```

#### 2. Search Parametri
```python
# Pravni dokumenti zahtevaju precizno keyword matching
SEARCH_SEMANTIC_WEIGHT = 0.6  # Smanjiti sa 0.7
SEARCH_BM25_WEIGHT = 0.4  # Povećati sa 0.3
SEARCH_TOP_K = 15  # Povećati sa 10

# Razlog: Pravni termini moraju biti tačno pronađeni (BM25)
# ali i semantički slični (embedding)
```

#### 3. Reranker Parametri
```python
RERANKER_ENABLED = True  # Obavezno za pravne dokumente
RERANKER_TOP_K = 5  # Dodati: koliko rezultata nakon rerankinga

# Razlog: Reranker značajno poboljšava preciznost
```

### Eksperimentalna Optimizacija

**Plan testiranja**:
1. Kreirati 20-30 test upita za pilot korpus
2. Testirati različite kombinacije parametara
3. Meriti precision@k i recall@k
4. Odabrati najbolju konfiguraciju

**Parametri za testiranje**:
```python
# Test Matrix
chunk_sizes = [500, 800, 1000]
overlaps = [50, 100, 150]
semantic_weights = [0.5, 0.6, 0.7]
top_k_values = [10, 15, 20]

# Ukupno: 3 × 3 × 3 × 3 = 81 kombinacija
# Testirati top 10-15 kombinacija
```

---

## 🔍 Preliminarna Istraživanja Korpusa

### Zadatak 1: Statistička Analiza

**Cilj**: Razumeti strukturu i karakteristike korpusa

**Metrike za prikupljanje**:
1. **Distribucija po kategorijama**
   - Broj dokumenata po kategoriji
   - Prosečna dužina dokumenta po kategoriji
   
2. **Distribucija po tipu akta**
   - Zakoni, Uredbe, Pravilnici, Odluke, Strategije
   - Prosečna dužina po tipu
   
3. **Temporalna analiza**
   - Distribucija po godinama donošenja
   - Identifikacija najčešće menjanih zakona
   
4. **Analiza referenci**
   - Broj referenci po dokumentu
   - Najčešće referencirani dokumenti
   - Graf međusobnih referenci

**Implementacija**:
```python
# Kreirati novi modul: backend/zaikon/modules/corpus_analysis/
# - service.py: Funkcije za analizu
# - schemas.py: Pydantic modeli za rezultate
# - README.md: Dokumentacija

# API endpoint: GET /api/corpus/analysis
```

### Zadatak 2: Identifikacija Konfliktnih Oblasti

**Cilj**: Pronaći oblasti sa najviše potencijalnih konflikata

**Metod**:
1. Pokrenuti detekciju konflikata na pilot korpusu
2. Analizirati rezultate po kategorijama
3. Identifikovati "hot spots" - oblasti sa mnogo konflikata
4. Prioritizovati te oblasti za detaljniju analizu

**Očekivani rezultati**:
- Top 10 najkonfliktnih oblasti
- Tipovi konflikata po oblastima
- Preporuke za nova pravila

### Zadatak 3: Kvalitativna Analiza Uzorka

**Cilj**: Manuelna verifikacija kvaliteta sistema

**Metod**:
1. Odabrati 50 random dokumenata iz pilot korpusa
2. Manuelno identifikovati konflikte
3. Uporediti sa automatski detektovanim konfliktima
4. Izračunati precision, recall, F1 score
5. Analizirati false positives i false negatives

---

## 📋 Akcioni Plan - Korak po Korak

### Nedelja 1-2: Priprema i Pilot

**Dan 1-2: Setup i Konfiguracija**
- [ ] Odabrati pilot korpus (100-200 dokumenata)
- [ ] Kopirati pilot dokumente u `DOCUMENTS/pilot/`
- [ ] Ažurirati RAG parametre prema preporukama
- [ ] Testirati import pipeline na 10 dokumenata

**Dan 3-5: Import Pilot Korpusa**
- [ ] Pokrenuti batch import pilot korpusa
- [ ] Monitorovati performanse (vreme, memorija)
- [ ] Verifikovati kvalitet ekstrakcije
- [ ] Kreirati izveštaj o importu

**Dan 6-7: Preliminarna Analiza**
- [ ] Pokrenuti statistič ku analizu pilot korpusa
- [ ] Identifikovati tipične strukture dokumenata
- [ ] Mapirati međusobne reference
- [ ] Dokumentovati nalaze

**Dan 8-10: Detekcija Konflikata**
- [ ] Pokrenuti detekciju konflikata na pilot korpusu
- [ ] Analizirati top 50 detektovanih konflikata
- [ ] Manuelno verifikovati 20 konflikata
- [ ] Izračunati precision/recall

**Dan 11-14: Optimizacija**
- [ ] Testirati različite RAG parametre
- [ ] Identifikovati nove tipove konflikata
- [ ] Kreirati gold cases za nove tipove
- [ ] Implementirati nova pravila konflikata

### Nedelja 3-4: Skaliranje

**Dan 15-17: Batch 2 (500 dokumenata)**
- [ ] Import dodatnih 300 dokumenata
- [ ] Monitoring performansi
- [ ] Verifikacija kvaliteta
- [ ] Optimizacija ako potrebno

**Dan 18-21: Batch 3 (1,000 dokumenata)**
- [ ] Import dodatnih 500 dokumenata
- [ ] Testiranje Q&A funkcionalnosti
- [ ] Testiranje conflict detection
- [ ] Kreiranje izveštaja

**Dan 22-28: Evaluacija i Odluka**
- [ ] Analiza rezultata do sada
- [ ] Procena troškova za pun korpus
- [ ] Odluka o nastavku (lokalno vs cloud)
- [ ] Plan za finalno skaliranje

### Nedelja 5-6: Pun Korpus (Opciono)

**Dan 29-35: Finalno Skaliranje**
- [ ] Import preostalih dokumenata u batch-evima
- [ ] Kontinuirani monitoring
- [ ] Finalna optimizacija
- [ ] Kreiranje kompletnog izveštaja

**Dan 36-42: Produkcijska Priprema**
- [ ] Testiranje na realnim use case-ovima
- [ ] Kreiranje dokumentacije za korisnike
- [ ] Setup backup i recovery procedura
- [ ] Finalno testiranje performansi

---

## 🎓 Use Case Scenariji

### Scenario 1: Q&A Sistem

**Primer upita**:
```
"Koji su uslovi za dobijanje dozvole za sečenje šume?"
"Koje su kazne za nepoštovanje zakona o zaštiti životne sredine?"
"Kako se vrši postupak izdavanja građevinske dozvole?"
```

**Potrebne komponente**:
- RAG sistem za pronalaženje relevantnih odredbi
- LLM za generisanje odgovora
- Citation tracking za reference na izvorne dokumente

**Metrike kvaliteta**:
- Accuracy: Da li je odgovor tačan?
- Completeness: Da li su pokriveni svi aspekti?
- Citations: Da li su navedeni ispravni izvori?

### Scenario 2: Provera Usaglašenosti Predloga Zakona

**Proces**:
1. Upload predloga zakona (PDF/DOCX)
2. Ekstrakcija normativnih tvrdnji
3. Poređenje sa postojećim korpusom
4. Detekcija konflikata
5. Generisanje izveštaja

**Tipovi konflikata za proveru**:
- Direktne kontradikcije sa postojećim zakonima
- Konflikti nadležnosti
- Proceduralni konflikti
- Temporalni konflikti (rokovi)
- Definicioni konflikti

**Output**:
- PDF izveštaj sa detaljnom analizom
- Lista detektovanih konflikata sa referencama
- Preporuke za izmene
- Vizualizacija konfliktnih oblasti

---

## 💰 Procena Troškova

### Scenario A: Potpuno Lokalno (Preporučeno za Početak)

**Jednokratni troškovi**:
- Hardware upgrade (ako potrebno): $0-500
- Vreme razvoja: 40-60 sati

**Operativni troškovi**:
- Električna energija: ~$5-10/mesec
- Održavanje: 2-4 sata/mesec

**Ukupno za prvu godinu**: $100-700

### Scenario B: Hibridno (Cloud Embedding)

**Jednokratni troškovi**:
- OpenAI API setup: $0
- Vreme razvoja: 40-60 sati

**Operativni troškovi**:
- Embedding API: $50-100 (jednokratno za pun korpus)
- Reranking API: $20-40/mesec (za upite)
- Električna energija: $5-10/mesec

**Ukupno za prvu godinu**: $300-600

### Scenario C: Potpuno Cloud

**Jednokratni troškovi**:
- API setup: $0
- Vreme razvoja: 30-40 sati

**Operativni troškovi**:
- Embedding: $100-200 (jednokratno)
- LLM API: $200-500/mesec (zavisno od upotrebe)
- Reranking: $50-100/mesec

**Ukupno za prvu godinu**: $2,500-7,500

---

## 🚀 Finalne Preporuke

### Kratkoročno (Sledeća 2 nedelje)

1. **Počnite sa pilot projektom** od 100-200 dokumenata
2. **Koristite default settings** za početak
3. **Fokusirajte se na jednu oblast** (npr. šumarstvo)
4. **Merite sve metrike** (vreme, memorija, kvalitet)
5. **Dokumentujte sve probleme** i rešenja

### Srednjoročno (Sledeća 2 meseca)

1. **Postepeno skalirajte** do 1,000-2,000 dokumenata
2. **Optimizujte RAG parametre** na osnovu rezultata
3. **Implementirajte nova pravila** konflikata
4. **Razvijte Q&A funkcionalnost**
5. **Kreirajte evaluation framework**

### Dugoročno (6+ meseci)

1. **Skaliranje na pun korpus** (7,053 dokumenata)
2. **Produkcijska deployment**
3. **Kontinuirano učenje** i poboljšanje
4. **Integracija sa drugim sistemima**
5. **Automatsko ažuriranje** korpusa

### Kritični Faktori Uspeha

✅ **Započnite malo** - Ne pokušavajte odmah sa punim korpusom
✅ **Merite sve** - Bez metrika ne možete optimizovati
✅ **Iterativno poboljšavajte** - Svaka iteracija donosi nova saznanja
✅ **Dokumentujte** - Vaša buduća verzija će vam biti zahvalna
✅ **Budite realistični** - 7,000 dokumenata je ozbiljan zadatak

---

## 📞 Sledeći Koraci

**Odmah**:
1. Odaberite pilot korpus (koja oblast?)
2. Proverite hardverske specifikacije
3. Odlučite: lokalno vs cloud vs hibrid?

**Ova nedelja**:
1. Setup pilot projekta
2. Prvi import test (10 dokumenata)
3. Verifikacija kvaliteta

**Sledeća nedelja**:
1. Pun pilot import (100-200 dokumenata)
2. Prva analiza rezultata
3. Identifikacija problema

---

**Pitanja za razmatranje**:
1. Koja oblast prava vas najviše interesuje za pilot?
2. Kakve su specifikacije vašeg računara?
3. Da li imate budžet za cloud servise?
4. Koji use case je prioritet: Q&A ili conflict detection?
5. Koliko vremena možete posvetiti projektu nedeljno?

**Kontakt za podršku**: Nastavite sa pitanjima, tu sam da pomognem! 🚀