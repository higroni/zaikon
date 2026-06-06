# ZAIKON - Lessons Learned & Best Practices

## Pregled

Ovaj dokument sadrži sve ključne lekcije naučene tokom razvoja ZAIKON sistema, greške koje su oduzele najviše vremena, i najbolje prakse do kojih smo došli kroz testiranje i optimizaciju.

---

## 1. Kritične Greške i Rešenja

### 1.1 StoreAssertionsStep u Pogrešnom Lancu ⏱️ **Vreme izgubljeno: 4+ sata**

**Problem:**
```python
# ❌ POGREŠNO - StoreAssertionsStep u glavnom lancu
FileByFileImportChain(steps=[
    DetectSourceFilesStep(),
    ProcessFilesWithProgressStep(),
    StoreAssertionsStep(),  # ← OVDE JE GREŠKA!
    BuildIndexesStep(),
])
```

**Simptomi:**
- Import se završava uspešno (status: "completed")
- Ali 0 asercija u bazi podataka
- Nema grešaka u logovima
- Korisnik misli da sve radi

**Root Cause:**
- `StoreAssertionsStep` očekuje `normative_assertions` artifact
- Taj artifact postoji samo u **per-file** kontekstu
- U glavnom lancu, artifact ne postoji
- Step se preskače bez greške

**Rešenje:**
```python
# ✅ ISPRAVNO - StoreAssertionsStep u per-file lancu
def _process_single_file(self, file_info):
    steps = [
        ExtractTextStep(),
        NormalizeTextStep(),
        ParseLegalStructureStep(),
        ExtractNormativeAssertionsStep(),
        StoreAssertionsStep(),  # ← OVDE TREBA DA BUDE!
    ]
    # ...
```

**Lekcija:**
- ⚠️ **Uvek razumej kontekst izvršavanja pipeline step-ova**
- ⚠️ **Testiraj da li se podaci zaista čuvaju, ne samo da li je status "completed"**
- ⚠️ **Dodaj validaciju koja proverava da li su podaci sačuvani**

**Prevencija:**
```python
class StoreAssertionsStep(PipelineStep):
    def run(self, context: PipelineContext) -> PipelineContext:
        artifact = context.get_artifact("normative_assertions")
        if not artifact:
            raise ValueError("Missing normative_assertions artifact!")
        
        # Store assertions...
        stored_count = len(assertions)
        
        # Validacija
        if stored_count == 0:
            logger.warning("No assertions stored - check pipeline!")
        
        return context
```

---

### 1.2 Artifact Validation - Preskakanje Step-ova ⏱️ **Vreme izgubljeno: 3+ sata**

**Problem:**
```python
# ❌ POGREŠNO - Previše striktna validacija
class GenerateImportReportStep(PipelineStep):
    requires = (
        "stored_documents_report",
        "keyword_index_report",
        "vector_index_report",
        "structure_index_report",
        "reference_graph_report"
    )
```

**Simptomi:**
```
ValueError: Step 'generate_import_report' missing artifacts: 
stored_documents_report, keyword_index_report, vector_index_report, 
structure_index_report, reference_graph_report
```

**Root Cause:**
- Step očekuje artifakte koji se kreiraju u **drugom lancu**
- Artifakti nisu dostupni u trenutnom kontekstu
- Validacija je previše striktna

**Rešenje:**
```python
# ✅ ISPRAVNO - Fleksibilnija validacija
class GenerateImportReportStep(PipelineStep):
    requires = ("import_report",)  # Samo osnovni artifact
    
    def run(self, context: PipelineContext) -> PipelineContext:
        # Opciono učitaj dodatne artifakte ako postoje
        keyword_report = context.get_artifact("keyword_index_report")
        vector_report = context.get_artifact("vector_index_report")
        # ...
```

**Lekcija:**
- ⚠️ **Ne zahtevaj artifakte koji možda ne postoje u kontekstu**
- ⚠️ **Koristi opcionu validaciju za artifakte iz drugih lanaca**
- ⚠️ **Dokumentuj koji artifakti su obavezni, a koji opcioni**

---

### 1.3 Legal Parser - Ćirilica vs. Latinica ⏱️ **Vreme izgubljeno: 2+ sata**

**Problem:**
```python
# ❌ POGREŠNO - Regex samo za latinicu
_ARTICLE_RE = re.compile(r"^\s*Član\s+(\d+)", re.MULTILINE)
```

**Simptomi:**
- Parser radi sa latiničnim tekstom
- Ali ne prepoznaje ćirilične dokumente
- Canonical document ima 0 legal units
- Conflict detection ne pronalazi ništa

**Root Cause:**
- Regex pattern ne pokriva ćirilicu ("Члан")
- Srpski pravni dokumenti mogu biti u oba pisma
- Parser tiho pada bez greške

**Rešenje:**
```python
# ✅ ISPRAVNO - Podrška za oba pisma
_ARTICLE_RE = re.compile(
    r"^\s*(?:Član|Члан)\s+(\d+)",  # Latinica i ćirilica
    re.MULTILINE | re.IGNORECASE
)

# Ili normalizuj tekst pre parsiranja
def serbian_cyrillic_to_latin(text: str) -> str:
    return text.translate(str.maketrans(_CYRILLIC_TO_LATIN))
```

**Lekcija:**
- ⚠️ **Uvek testiraj sa oba pisma (latinica i ćirilica)**
- ⚠️ **Normalizuj tekst na početku pipeline-a**
- ⚠️ **Dodaj unit testove za oba pisma**

**Prevencija:**
```python
# Test suite
def test_parser_with_latin():
    text = "Član 1\nOvim zakonom..."
    result = parser.parse(text)
    assert len(result.legal_units) > 0

def test_parser_with_cyrillic():
    text = "Члан 1\nОвим законом..."
    result = parser.parse(text)
    assert len(result.legal_units) > 0
```

---

### 1.4 JSON vs. SQLite - Migracija Storage-a ⏱️ **Vreme izgubljeno: 6+ sata**

**Problem:**
```python
# ❌ POGREŠNO - JSON fajlovi za sve
findings_file = f"data/findings/{draft_id}.json"
with open(findings_file, "w") as f:
    json.dump(findings, f)
```

**Simptomi:**
- Sporo čitanje/pisanje
- Race conditions pri konkurentnom pristupu
- Teško pretraživanje
- Nema transakcija
- Fajlovi se gube

**Root Cause:**
- JSON nije dizajniran za bazu podataka
- Nema ACID transakcija
- Nema indeksa za pretragu
- Nema concurrent access kontrole

**Rešenje:**
```python
# ✅ ISPRAVNO - SQLite za sve strukturirane podatke
class FindingsStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def save_finding(self, finding: Finding):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO findings (id, draft_id, type, severity, ...)
                VALUES (?, ?, ?, ?, ...)
            """, (finding.id, finding.draft_id, ...))
```

**Lekcija:**
- ⚠️ **Koristi SQLite za sve strukturirane podatke**
- ⚠️ **JSON samo za konfiguracione fajlove**
- ⚠️ **Centralizuj bazu - jedna `zaikon.db` umesto 100 JSON fajlova**

**Migracija:**
```python
def migrate_json_to_sqlite():
    """Migracija postojećih JSON fajlova u SQLite"""
    for json_file in Path("data/findings").glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
        
        # Sačuvaj u SQLite
        store.save_findings(data)
        
        # Obriši JSON

---

### 1.6 Nedostatak Debug Output-a ⏱️ **Vreme izgubljeno: 8+ sati**

**Problem:**
```python
# ❌ POGREŠNO - Nema debug output-a
def process_document(doc_id: str):
    doc = load_document(doc_id)
    parsed = parse_document(doc)
    assertions = extract_assertions(parsed)
    save_assertions(assertions)
    return {"status": "completed"}
```

**Simptomi:**
- Funkcija vraća "completed" ali nešto ne radi
- Nema uvida šta je ulaz, šta je izlaz
- Teško je pronaći gde je problem
- Mora se debugovati sa breakpoint-ima

**Root Cause:**
- Nema logovanja ulaza/izlaza svake faze
- Nema merenja vremena izvršavanja
- Nema validacije međurezultata
- Tihi failure-i

**Rešenje:**
```python
# ✅ ISPRAVNO - Opširan debug output
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

def process_document(doc_id: str, verbose: bool = True):
    """Process document with comprehensive debug output"""
    
    if verbose:
        logger.info("="*80)
        logger.info(f"PROCESSING DOCUMENT: {doc_id}")
        logger.info("="*80)
    
    # Faza 1: Load
    start = time.time()
    doc = load_document(doc_id)
    elapsed = time.time() - start
    
    if verbose:
        logger.info(f"✓ Phase 1: Load Document")
        logger.info(f"  Input: doc_id={doc_id}")
        logger.info(f"  Output: {len(doc.text)} chars, {doc.pages} pages")
        logger.info(f"  Time: {elapsed:.3f}s")
        logger.info(f"  Sample: {doc.text[:100]}...")
    
    # Faza 2: Parse
    start = time.time()
    parsed = parse_document(doc)
    elapsed = time.time() - start
    
    if verbose:
        logger.info(f"✓ Phase 2: Parse Document")
        logger.info(f"  Input: {len(doc.text)} chars")
        logger.info(f"  Output: {len(parsed.legal_units)} legal units")
        logger.info(f"  Time: {elapsed:.3f}s")
        logger.info(f"  Units: {[u.type for u in parsed.legal_units[:5]]}")
    
    # Validacija
    if len(parsed.legal_units) == 0:
        logger.warning("⚠ WARNING: No legal units parsed!")
        logger.warning(f"  Document text sample: {doc.text[:200]}")
    
    # Faza 3: Extract Assertions
    start = time.time()
    assertions = extract_assertions(parsed)
    elapsed = time.time() - start
    
    if verbose:
        logger.info(f"✓ Phase 3: Extract Assertions")
        logger.info(f"  Input: {len(parsed.legal_units)} legal units")
        logger.info(f"  Output: {len(assertions)} assertions")
        logger.info(f"  Time: {elapsed:.3f}s")
        logger.info(f"  Types: {set(a.type for a in assertions)}")
    
    # Validacija
    if len(assertions) == 0:
        logger.warning("⚠ WARNING: No assertions extracted!")
    
    # Faza 4: Save
    start = time.time()
    saved_count = save_assertions(assertions)
    elapsed = time.time() - start
    
    if verbose:
        logger.info(f"✓ Phase 4: Save Assertions")
        logger.info(f"  Input: {len(assertions)} assertions")
        logger.info(f"  Output: {saved_count} saved to DB")
        logger.info(f"  Time: {elapsed:.3f}s")
    
    # Finalna validacija
    if saved_count != len(assertions):
        logger.error(f"✗ ERROR: Mismatch! {len(assertions)} extracted but {saved_count} saved")
    
    if verbose:
        logger.info("="*80)
        logger.info(f"COMPLETED: {doc_id}")
        logger.info("="*80)
    
    return {
        "status": "completed",
        "document_id": doc_id,
        "legal_units": len(parsed.legal_units),
        "assertions": len(assertions),
        "saved": saved_count
    }
```

**Konfigurabilni Verbosity:**
```python
# settings.py
class Settings:
    # Verbosity levels
    VERBOSITY_SILENT = 0   # Samo errors
    VERBOSITY_NORMAL = 1   # Info + warnings + errors
    VERBOSITY_DEBUG = 2    # Sve + debug output
    VERBOSITY_TRACE = 3    # Sve + ulaz/izlaz svake funkcije
    
    verbosity: int = VERBOSITY_NORMAL

# Korišćenje
if settings.verbosity >= settings.VERBOSITY_DEBUG:
    logger.debug(f"Intermediate result: {data}")
```

**Lekcija:**
- ⚠️ **Uvek loguj ulaz i izlaz svake faze**
- ⚠️ **Meraj vreme izvršavanja na svim bitnim tačkama**
- ⚠️ **Validuj međurezultate i upozoravaj na anomalije**
- ⚠️ **Omogući konfigurabilni verbosity nivo**
- ⚠️ **Loguj u konzolu I u fajl**

**Logging Setup:**
```python
import logging
import sys

def setup_logging(verbosity: int = 1):
    """Setup logging sa console i file output"""
    
    # Determine log level
    if verbosity == 0:
        level = logging.ERROR
    elif verbosity == 1:
        level = logging.INFO
    elif verbosity == 2:
        level = logging.DEBUG
    else:
        level = logging.DEBUG
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler('logs/zaikon.log')
    file_handler.setLevel(logging.DEBUG)  # Uvek DEBUG u fajl
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
```

---

### 1.7 Ponavljanje Dugotrajnih Faza ⏱️ **Vreme izgubljeno: 10+ sati**

**Problem:**
```python
# ❌ POGREŠNO - Svaki test pokreće sve od početka
def test_conflict_detection():
    # Ovo traje 5 minuta!
    corpus_id = import_corpus("data/corpus/")  
    
    # Ovo traje 3 minuta!
    generate_embeddings(corpus_id)
    
    # Ovo je ono što želimo da testiramo (10 sekundi)
    conflicts = detect_conflicts(draft, corpus_id)
    
    assert len(conflicts) > 0
```

**Simptomi:**
- Svaki test traje 8+ minuta
- 90% vremena se troši na setup
- Teško je iterativno razvijati
- Frustrirajuće čekanje

**Root Cause:**
- Nema reuse-a prethodno procesiranih podataka
- Nema caching mehanizma
- Nema "skip if exists" logike
- Sve se pokreće od nule

**Rešenje:**
```python
# ✅ ISPRAVNO - Reuse postojećih podataka

class TestDataManager:
    """Manages test data with caching and reuse"""
    
    def __init__(self, cache_dir: Path = Path("test_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_or_create_corpus(
        self, 
        name: str, 
        source_dir: Path,
        force_recreate: bool = False
    ) -> str:
        """Get existing corpus or create new one"""
        
        cache_file = self.cache_dir / f"corpus_{name}.json"
        
        # Check if cached
        if cache_file.exists() and not force_recreate:
            logger.info(f"✓ Using cached corpus: {name}")
            with open(cache_file) as f:
                data = json.load(f)
            return data["corpus_id"]
        
        # Create new
        logger.info(f"Creating new corpus: {name} (this may take a while...)")
        start = time.time()
        
        corpus_id = import_corpus(source_dir)
        
        elapsed = time.time() - start
        logger.info(f"✓ Corpus created in {elapsed:.1f}s")
        
        # Cache it
        with open(cache_file, "w") as f:
            json.dump({
                "corpus_id": corpus_id,
                "created_at": datetime.now().isoformat(),
                "source_dir": str(source_dir)
            }, f)
        
        return corpus_id
    
    def get_or_create_embeddings(
        self,
        corpus_id: str,
        force_recreate: bool = False
    ) -> bool:
        """Generate embeddings if not exist"""
        
        # Check if embeddings exist in Qdrant
        collection_name = f"corpus_{corpus_id}"
        
        if not force_recreate:
            try:
                info = qdrant_client.get_collection(collection_name)
                if info.points_count > 0:
                    logger.info(f"✓ Using existing embeddings: {info.points_count} vectors")
                    return True
            except Exception:
                pass
        
        # Generate new
        logger.info(f"Generating embeddings for corpus {corpus_id}...")
        start = time.time()
        
        generate_embeddings(corpus_id)
        
        elapsed = time.time() - start
        logger.info(f"✓ Embeddings generated in {elapsed:.1f}s")
        
        return True

# Korišćenje u testovima
test_data = TestDataManager()

def test_conflict_detection():
    """Test conflict detection - BRZO!"""
    
    # Ovo je instant ako već postoji (prvi put 5 min)
    corpus_id = test_data.get_or_create_corpus(
        name="test_corpus",
        source_dir=Path("data/test_corpus")
    )
    
    # Ovo je instant ako već postoji (prvi put 3 min)
    test_data.get_or_create_embeddings(corpus_id)
    
    # Ovo je ono što testiramo (10 sekundi)
    conflicts = detect_conflicts(draft, corpus_id)
    
    assert len(conflicts) > 0

# Cleanup kada treba
def test_cleanup():
    """Očisti cache kada treba fresh start"""
    test_data = TestDataManager()
    shutil.rmtree(test_data.cache_dir)
```

**Environment Variable za Force Recreate:**
```python
# .env
FORCE_RECREATE_TEST_DATA=false

# U kodu
force = os.getenv("FORCE_RECREATE_TEST_DATA", "false").lower() == "true"
corpus_id = test_data.get_or_create_corpus(
    name="test_corpus",
    source_dir=Path("data/test_corpus"),
    force_recreate=force
)
```

**Lekcija:**
- ⚠️ **Implementiraj caching za dugotrajne operacije**
- ⚠️ **Omogući reuse postojećih podataka**
- ⚠️ **Dodaj "skip if exists" logiku**
- ⚠️ **Omogući force recreate kada je potrebno**
- ⚠️ **Jasno loguj da li se koriste cached podaci**

**Rezultat:**
- Prvi test run: 8 minuta
- Svi sledeći: 10 sekundi (48x brže!)
- Iterativni razvoj mnogo brži

---

### 1.8 Prekompleksan i Ružan UI ⏱️ **Vreme izgubljeno: 12+ sati**

**Problem:**
```tsx
// ❌ POGREŠNO - Svaka komponenta ima svoj custom stil
function CorpusCard({ corpus }) {
  return (
    <div style={{
      border: "2px solid #3498db",
      borderRadius: "8px",
      padding: "20px",
      margin: "10px",
      boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    }}>
      <h3 style={{ color: "#fff", fontSize: "18px" }}>{corpus.name}</h3>
      {/* ... */}
    </div>
  );
}

function DraftCard({ draft }) {
  return (
    <div style={{
      border: "1px solid #e74c3c",
      borderRadius: "12px",
      padding: "15px",
      margin: "8px",
      boxShadow: "0 2px 4px rgba(0,0,0,0.15)",
      background: "#f8f9fa"
    }}>
      {/* Potpuno drugačiji stil! */}
    </div>
  );
}
```

**Simptomi:**
- Svaka komponenta izgleda drugačije
- Nema konzistentnosti
- Teško održavanje
- Ružan izgled
- Korisnici zbunjeni

**Root Cause:**
- Nema UI design sistema
- Nema standardnih komponenti
- Svaki developer radi kako hoće
- Nema style guide-a

**Rešenje:**
```tsx
// ✅ ISPRAVNO - Koristi standardni UI framework

// 1. Izaberi framework (npr. shadcn/ui, Chakra UI, Material-UI)
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

// 2. Definiši standardne komponente
function CorpusCard({ corpus }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{corpus.name}</CardTitle>
        <Badge variant={corpus.status === "ready" ? "success" : "warning"}>
          {corpus.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {corpus.documents_count} documents
        </p>
      </CardContent>
    </Card>
  );
}

// 3. Isti pattern za sve kartice
function DraftCard({ draft }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{draft.name}</CardTitle>
        <Badge variant={draft.status === "completed" ? "success" : "warning"}>
          {draft.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {draft.findings_count} findings
        </p>
      </CardContent>
    </Card>
  );
}
```

**Standardni Layout Template:**
```tsx
// ✅ Layout template za sve stranice
import { AppShell, Header, Navbar, Main } from "@/components/layout"

function StandardLayout({ children }) {
  return (
    <AppShell>
      <Header>
        <Logo />
        <Navigation />
        <UserMenu />
      </Header>
      
      <div className="flex">
        <Navbar>
          <NavLink to="/corpora">Korpusi</NavLink>
          <NavLink to="/drafts">Nacrti</NavLink>
          <NavLink to="/search">Pretraga</NavLink>
          <NavLink to="/settings">Podešavanja</NavLink>
        </Navbar>
        
        <Main className="flex-1 p-6">
          {children}
        </Main>
      </div>
    </AppShell>
  );
}

// Sve stranice koriste isti layout
function CorpusListPage() {
  return (
    <StandardLayout>
      <PageHeader title="Korpusi" />
      <CorpusList />
    </StandardLayout>
  );
}
```

**Design System Pravila:**
```tsx
// design-system.ts
export const designSystem = {
  // Boje
  colors: {
    primary: "#3b82f6",
    secondary: "#64748b",
    success: "#22c55e",
    warning: "#f59e0b",
    error: "#ef4444",
  },
  
  // Spacing
  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
  },
  
  // Typography
  typography: {
    h1: "text-3xl font-bold",
    h2: "text-2xl font-semibold",
    h3: "text-xl font-medium",
    body: "text-base",
    small: "text-sm",
  },
  
  // Components
  components: {
    card: "rounded-lg border bg-card shadow-sm",
    button: "rounded-md px-4 py-2 font-medium",
    input: "rounded-md border px-3 py-2",
  }
};
```

**Lekcija:**
- ⚠️ **Koristi standardni UI framework od početka**
- ⚠️ **Definiši design system pre kodiranja**
- ⚠️ **Kreiraj reusable komponente**
- ⚠️ **Enforceuj konzistentnost kroz code review**
- ⚠️ **Jednostavnost > Kompleksnost**

**Preporučeni UI Frameworks:**
1. **shadcn/ui** - Najbolji za React + Tailwind
2. **Chakra UI** - Dobar balans jednostavnosti i moći
3. **Material-UI** - Ako želiš Material Design

**Rezultat:**
- Konzistentan izgled
- Brži razvoj (reusable komponente)
- Lakše održavanje
- Profesionalan UI
- Zadovoljni korisnici

        json_file.unlink()
```

---

### 1.5 Embedding Batch Size - VRAM Out of Memory ⏱️ **Vreme izgubljeno: 2+ sata**

**Problem:**
```python
# ❌ POGREŠNO - Previše veliki batch
embeddings = model.encode(all_documents, batch_size=512)
# CUDA out of memory!
```

**Simptomi:**
```
RuntimeError: CUDA out of memory. Tried to allocate 2.5 GiB 
(GPU 0; 16.00 GiB total capacity; 14.2 GiB already allocated)
```

**Root Cause:**
- Batch size previše veliki za dostupan VRAM
- Model + batch zauzimaju više od 16GB
- Nema graceful degradation

**Rešenje:**
```python
# ✅ ISPRAVNO - Optimalan batch size
def encode_with_optimal_batch(texts: list[str], max_vram_gb: float = 16.0):
    # Proceni optimalan batch size
    model_vram = 3.2  # GB
    available_vram = max_vram_gb - model_vram - 2.0  # 2GB buffer
    
    # Empirijski: ~25MB po dokumentu u batch-u
    optimal_batch = int((available_vram * 1024) / 25)
    optimal_batch = min(optimal_batch, 128)  # Max 128
    
    return model.encode(texts, batch_size=optimal_batch)
```

**Lekcija:**
- ⚠️ **Testiraj sa različitim batch size-ovima**
- ⚠️ **Dodaj VRAM monitoring**
- ⚠️ **Implementiraj graceful degradation (fallback na CPU)**

**Monitoring:**
```python
import torch

def check_vram_usage():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        logger.info(f"VRAM: {allocated:.1f}GB / {total:.1f}GB")
        
        if allocated > total * 0.9:
            logger.warning("VRAM usage > 90%!")
```

---

## 2. Best Practices - Algoritmi i Optimizacije

### 2.1 Hibridna Pretraga - Optimalni Weights

**Testirano 6+ konfiguracija:**

| Config | Vector | Keyword | Graph | Preciznost | Brzina | Rezultat |
|--------|--------|---------|-------|------------|--------|----------|
| A | 100% | 0% | 0% | 75% | 45ms | Propušta tačne termine |
| B | 0% | 100% | 0% | 70% | 12ms | Ne razume sinonime |
| C | 33% | 33% | 33% | 78% | 85ms | Prosečno |
| **D** | **45%** | **35%** | **20%** | **88%** | **140ms** | **✅ Najbolje** |
| E | 60% | 30% | 10% | 85% | 160ms | Sporije, malo bolje |
| F | 30% | 60% | 10% | 80% | 110ms | Brže, manje precizno |

**Zaključak:**
- ✅ **45-35-20 je optimalan balans**
- ✅ Preciznost: 88% (najbolja)
- ✅ Brzina: 140ms (prihvatljivo)
- ✅ Radi dobro za sve tipove upita

**Implementacija:**
```python
OPTIMAL_WEIGHTS = {
    'vector': 0.45,
    'keyword': 0.35,
    'graph': 0.20
}

def hybrid_search(query: str):
    # Paralelno izvršavanje
    results = await asyncio.gather(
        vector_search(query),
        keyword_search(query),
        graph_search(query)
    )
    
    # Weighted kombinacija
    return combine_results(results, OPTIMAL_WEIGHTS)
```

---

### 2.2 Reranking - Kada i Kako

**Testiranje:**
- Bez reranking-a: Preciznost 82%
- Sa reranking-om: Preciznost 88% (+6%)
- Dodatno vreme: +50ms

**Zaključak:**
- ✅ **Reranking se isplati**
- ✅ Primeni samo na top 8-10 rezultata
- ✅ Koristi cross-encoder (bolji od bi-encoder)

**Implementacija:**
```python
def search_with_reranking(query: str):
    # Faza 1: Hibridna pretraga (top 20)
    candidates = hybrid_search(query, top_k=20)
    
    # Faza 2: Reranking (top 8)
    if len(candidates) > 8:
        pairs = [[query, doc.text] for doc in candidates]
        scores = reranker.predict(pairs, batch_size=32)
        candidates = sorted(zip(candidates, scores), 
                          key=lambda x: x[1], 
                          reverse=True)[:8]
    
    return candidates
```

---

### 2.3 Batch Processing - Optimizacija Brzine

**Problem:** Procesiranje 1000 dokumenata traje 30+ minuta

**Rešenje:**

```python
# ❌ POGREŠNO - Jedan po jedan
for doc in documents:
    embedding = model.encode(doc)  # Sporo!
    save_to_db(embedding)

# ✅ ISPRAVNO - Batch processing
def process_in_batches(documents: list, batch_size: int = 128):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        
        # Batch encoding (mnogo brže!)
        embeddings = model.encode(batch, batch_size=batch_size)
        
        # Batch insert u bazu
        save_batch_to_db(embeddings)
```

**Rezultat:**
- Vreme: 30 min → 3 min (10x brže!)
- VRAM: Efikasnije korišćenje
- Throughput: 50 dok/s → 500 dok/s

---

### 2.4 Caching - Izbegavanje Ponovljenih Računanja

**Problem:** Isti upiti se ponavljaju, ali se računaju iznova

**Rešenje:**

```python
from functools import lru_cache

# ❌ POGREŠNO - Bez caching-a
def search(query: str):
    embedding = model.encode(query)  # Svaki put iznova!
    return qdrant.search(embedding)

# ✅ ISPRAVNO - Sa caching-om
@lru_cache(maxsize=1000)
def get_query_embedding(query: str):
    return model.encode(query)

def search(query: str):
    embedding = get_query_embedding(query)  # Cached!
    return qdrant.search(embedding)
```

**Rezultat:**
- Prvi poziv: 45ms
- Ponovljeni pozivi: <1ms (45x brže!)
- Memory: ~100MB za 1000 cached upita

---

### 2.5 Paralelno Izvršavanje - Async/Await

**Problem:** Sekvencijalno izvršavanje je sporo

**Rešenje:**

```python
# ❌ POGREŠNO - Sekvencijalno
def hybrid_search(query):
    vector_results = vector_search(query)    # 45ms
    keyword_results = keyword_search(query)  # 12ms
    graph_results = graph_search(query)      # 28ms
    # Ukupno: 85ms

# ✅ ISPRAVNO - Paralelno
async def hybrid_search(query):
    results = await asyncio.gather(
        vector_search(query),    # \
        keyword_search(query),   #  } Paralelno!
        graph_search(query)      # /
    )
    # Ukupno: 45ms (najsporiji)
```

**Rezultat:**
- Vreme: 85ms → 45ms (1.9x brže!)
- CPU: Bolje iskorišćenje
- Skalabilnost: Lako dodati nove metode

---

### 2.6 Database Indexing - Brže Upite

**Problem:** Upiti u bazu su spori

**Rešenje:**

```sql
-- ❌ POGREŠNO - Bez indeksa
SELECT * FROM findings WHERE draft_id = ?;
-- Vreme: 500ms za 10,000 redova

-- ✅ ISPRAVNO - Sa indeksom
CREATE INDEX idx_findings_draft_id ON findings(draft_id);
SELECT * FROM findings WHERE draft_id = ?;
-- Vreme: 5ms za 10,000 redova (100x brže!)
```

**Preporučeni indeksi:**
```sql
-- Findings
CREATE INDEX idx_findings_draft_id ON findings(draft_id);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_type ON findings(type);

-- Assertions
CREATE INDEX idx_assertions_corpus_id ON corpus_assertions(corpus_id);
CREATE INDEX idx_assertions_document_id ON corpus_assertions(document_id);
CREATE INDEX idx_assertions_type ON corpus_assertions(assertion_type);

-- Documents
CREATE INDEX idx_documents_corpus_id ON documents(corpus_id);
```

---

### 2.7 Lazy Loading - Učitavanje na Zahtev

**Problem:** Učitavanje svih modela na startu traje dugo

**Rešenje:**

```python
# ❌ POGREŠNO - Eager loading
class AIModels:
    def __init__(self):
        self.embedding_model = SentenceTransformer("BAAI/bge-m3")  # 5s
        self.reranker_model = CrossEncoder("BAAI/bge-reranker")    # 3s
        self.ner_model = stanza.Pipeline("sr")                     # 10s
        # Ukupno: 18s startup!

# ✅ ISPRAVNO - Lazy loading
class AIModels:
    def __init__(self):
        self._embedding_model = None
        self._reranker_model = None
        self._ner_model = None
    
    @property
    def embedding_model(self):
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer("BAAI/bge-m3")
        return self._embedding_model
    
    # Slično za ostale modele...
```

**Rezultat:**
- Startup: 18s → <1s
- Memory: Učitava se samo što je potrebno
- Flexibility: Lako disable-ovati modele

---

## 3. Testing Best Practices

### 3.1 Unit Tests - Testiraj Svaki Korak

```python
def test_store_assertions_step():
    """Test da li se asercije zaista čuvaju"""
    # Setup
    context = PipelineContext()
    context.add_artifact(Artifact(
        name="normative_assertions",
        payload=[{"id": "1", "type": "obligation", ...}]
    ))
    
    # Execute
    step = StoreAssertionsStep()
    result = step.run(context)
    
    # Verify - PROVERI DA LI SU PODACI U BAZI!
    with sqlite3.connect(settings.database_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM corpus_assertions"
        ).fetchone()[0]
    
    assert count > 0, "Assertions not stored!"
```

---

### 3.2 Integration Tests - End-to-End

```python
def test_full_import_pipeline():
    """Test kompletnog import procesa"""
    # 1. Kreiraj test fajl
    test_file = create_test_document()
    
    # 2. Pokreni import
    result = import_folder(test_file.parent)
    
    # 3. Proveri sve faze
    assert result.status == "completed"
    assert result.documents_count > 0
    assert result.assertions_count > 0
    
    # 4. Proveri bazu
    assertions = get_assertions_from_db()
    assert len(assertions) > 0
    
    # 5. Proveri Qdrant
    vectors = get_vectors_from_qdrant()
    assert len(vectors) > 0
```

---

### 3.3 Performance Tests - Benchmark

```python
import time

def test_search_performance():
    """Test brzine pretrage"""
    queries = load_test_queries()
    
    times = []
    for query in queries:
        start = time.time()
        results = search(query)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    
    # Asertuj da je dovoljno brzo
    assert avg_time < 0.200, f"Search too slow: {avg_time:.3f}s"
    
    print(f"Average search time: {avg_time:.3f}s")
```

---

## 4. Deployment Best Practices

### 4.1 Environment Variables - Konfiguracija

```bash
# ❌ POGREŠNO - Hardcoded vrednosti
embedding_model = "BAAI/bge-m3"
database_url = "sqlite:///data/zaikon.db"

# ✅ ISPRAVNO - Environment variables
ZAIKON_EMBEDDING_MODEL=BAAI/bge-m3
ZAIKON_DATABASE_URL=sqlite:///data/zaikon.db
ZAIKON_EMBEDDING_DEVICE=cuda
```

---

### 4.2 Logging - Praćenje Problema

```python
import logging

# ❌ POGREŠNO - Print statements
print("Processing document...")
print(f"Error: {e}")

# ✅ ISPRAVNO - Structured logging
logger = logging.getLogger(__name__)

logger.info("Processing document", extra={
    "document_id": doc_id,
    "corpus_id": corpus_id
})

logger.error("Failed to process document", extra={
    "document_id": doc_id,
    "error": str(e),
    "traceback": traceback.format_exc()
})
```

---

### 4.3 Error Handling - Graceful Degradation

```python
# ❌ POGREŠNO - Crash na grešku
def search(query):
    embedding = model.encode(query)  # Može da padne!
    return qdrant.search(embedding)

# ✅ ISPRAVNO - Graceful degradation
def search(query):
    try:
        # Pokušaj sa embedding-om
        embedding = model.encode(query)
        return qdrant.search(embedding)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        
        # Fallback na keyword search
        return keyword_search(query)
```

---

## 5. Monitoring i Maintenance

### 5.1 Health Checks

```python
def health_check():
    """Proveri da li sve komponente rade"""
    checks = {
        "database": check_database(),
        "qdrant": check_qdrant(),
        "embedding_model": check_embedding_model(),
        "reranker_model": check_reranker_model(),
        "llm": check_llm()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks
    }
```

---

### 5.2 Metrics Collection

```python
class Metrics:
    """Prikupljanje metrika"""
    
    def record_search(self, query: str, duration: float, results: int):
        self.search_count += 1
        self.total_search_time += duration
        self.total_results += results
    
    def get_stats(self):
        return {
            "avg_search_time": self.total_search_time / self.search_count,
            "avg_results": self.total_results / self.search_count,
            "total_searches": self.search_count
        }
```

---

## 6. Checklist za Sledeću Iteraciju

### Pre Početka Razvoja:
- [ ] Pročitaj ovaj dokument
- [ ] Postavi centralizovanu SQLite bazu
- [ ] Konfiguriši environment variables
- [ ] Postavi logging
- [ ] Napravi test suite

### Tokom Razvoja:
- [ ] Testiraj sa oba pisma (latinica i ćirilica)
- [ ] Proveri da li se podaci zaista čuvaju u bazi
- [ ] Dodaj unit testove za svaki step
- [ ] Benchmark performanse
- [ ] Dodaj error handling

### Pre Deployment-a:
- [ ] Pokreni sve testove
- [ ] Proveri VRAM korišćenje
- [ ] Testiraj sa realnim podacima
- [ ] Postavi monitoring
- [ ] Napravi backup strategiju

---

## 7. Ključne Lekcije - Rezime

### Top 8 Grešaka:
1. **Prekompleksan i ružan UI** (12h) - Koristi standardni UI framework od početka
2. **Ponavljanje dugotrajnih faza** (10h) - Implementiraj caching i reuse
3. **Nedostatak debug output-a** (8h) - Loguj ulaz/izlaz svake faze
4. **JSON umesto SQLite** (6h) - Koristi pravu bazu podataka
5. **StoreAssertionsStep u pogrešnom lancu** (4h) - Razumej kontekst izvršavanja
6. **Artifact validation previše striktna** (3h) - Fleksibilna validacija
7. **Ćirilica nije podržana** (2h) - Testiraj sa oba pisma
8. **Batch size previše veliki** (2h) - Optimizuj za dostupan VRAM

### Top 5 Optimizacija:
1. **Hibridna pretraga 45-35-20** - Najbolji balans brzine i kvaliteta
2. **Batch processing** - 10x brže procesiranje
3. **Paralelno izvršavanje** - 2x brža pretraga
4. **Caching** - 45x brži ponovljeni upiti
5. **Database indexing** - 100x brži upiti

### Top 8 Best Practices:
1. **Standardni UI framework** - shadcn/ui, Chakra UI, ili Material-UI
2. **Caching & Reuse** - TestDataManager za dugotrajne operacije
3. **Opširan debug output** - Loguj ulaz/izlaz, meraj vreme, validuj rezultate
4. **Konfigurabilni verbosity** - SILENT, NORMAL, DEBUG, TRACE nivoi
5. **Centralizovana SQLite baza** - Jedna `zaikon.db` za sve
6. **Lazy loading modela** - Brži startup
7. **Graceful degradation** - Fallback strategije
8. **Comprehensive testing** - Unit + Integration + Performance

---

## Zaključak

Ovaj dokument je **živi dokument** - ažuriraj ga sa novim lekcijama!

**Ključna poruka:** 
> "Greške su neizbežne, ali ih ne ponavljaj. Dokumentuj, nauči, i primeni u sledećoj iteraciji."

**Vreme uštede u sledećoj iteraciji:** ~50+ sati

**Najvažnije lekcije:**
1. 🎨 **UI Design System** - Koristi framework, ne custom CSS (ušteda: 12h)
2. 🔄 **Caching & Reuse** - Ne ponavljaj dugotrajne operacije (ušteda: 10h)
3. 🐛 **Debug Output** - Loguj sve, meraj sve, validuj sve (ušteda: 8h)
4. 💾 **SQLite > JSON** - Koristi pravu bazu podataka (ušteda: 6h)
5. 📝 **Verbosity Levels** - Omogući konfigurabilni debug output (ušteda: 4h)

**ROI dokumentacije:** Besplatno! 🎉