# ZAIKON - Domain-Driven Design Architecture

**Version**: 1.0  
**Last Updated**: 2026-06-06  
**Status**: DDD Architecture Specification

---

## Pregled

Ovaj dokument definiše Domain-Driven Design (DDD) arhitekturu za ZAIKON sistem, sa fokusom na:
- **Bounded Contexts** - Jasno definisane granice domena
- **Aggregates** - Konzistentne jedinice podataka
- **Domain Events** - Komunikacija između konteksta
- **Value Objects** - Immutable objekti bez identiteta
- **Repositories** - Pristup agregatima
- **Domain Services** - Biznis logika koja ne pripada entitetima

---

## 1. Bounded Contexts (Ograničeni Konteksti)

### 1.1 Legal Document Management Context

**Odgovornost**: Upravljanje pravnim dokumentima, parsing, ekstrakcija strukture

**Aggregates**:
- `Document` (Aggregate Root)
  - `LegalUnit` (Entity)
  - `Assertion` (Entity)

**Value Objects**:
- `DocumentMetadata` (filename, title, type, language)
- `LegalUnitReference` (unit_type, number, title)
- `AssertionContent` (type, content, entities)

**Domain Events**:
- `DocumentImported`
- `DocumentParsed`
- `LegalUnitsExtracted`
- `AssertionsExtracted`

**Repositories**:
- `DocumentRepository`
- `LegalUnitRepository`
- `AssertionRepository`

**Domain Services**:
- `LegalParserService` - Parsing pravnih dokumenata
- `TextExtractionService` - Ekstrakcija teksta iz PDF/DOCX
- `StructureAnalysisService` - Analiza strukture dokumenta

---

### 1.2 Corpus Management Context

**Odgovornost**: Upravljanje korpusima, verzionisanje, parametrizacija

**Aggregates**:
- `Corpus` (Aggregate Root)
  - `CorpusRun` (Entity)
  - `Document` (Reference to Document Context)

**Value Objects**:
- `CorpusMetadata` (name, domain_id, language, status)
- `RunParameters` (param_set_id, ontology_set_id, conflict_rule_set_id)
- `RunStatistics` (documents_processed, legal_units_extracted, assertions_extracted)

**Domain Events**:
- `CorpusCreated`
- `CorpusRunStarted`
- `CorpusRunCompleted`
- `CorpusRunFailed`

**Repositories**:
- `CorpusRepository`
- `CorpusRunRepository`

**Domain Services**:
- `CorpusImportService` - Import dokumenata u korpus
- `CorpusIndexingService` - Indeksiranje korpusa
- `CorpusExportService` - Export "knowledge sets"

---

### 1.3 Knowledge Representation Context

**Odgovornost**: Ontologije, embeddings, semantička pretraga

**Aggregates**:
- `OntologySet` (Aggregate Root)
  - `OntologyTerm` (Entity)

- `Embedding` (Aggregate Root)
  - `Vector` (Value Object)

**Value Objects**:
- `OntologyMetadata` (version, name, language, description)
- `TermDefinition` (name, term, rule, type)
- `VectorRepresentation` (vector, model, dimensions)

**Domain Events**:
- `OntologySetCreated`
- `OntologyTermAdded`
- `EmbeddingsGenerated`
- `IndexUpdated`

**Repositories**:
- `OntologySetRepository`
- `OntologyTermRepository`
- `EmbeddingRepository` (Qdrant)

**Domain Services**:
- `EmbeddingGenerationService` - Generisanje embeddings
- `SemanticSearchService` - Semantička pretraga
- `OntologyMatchingService` - Matching termina sa tekstom

---

### 1.4 Conflict Detection Context

**Odgovornost**: Detekcija konflikata, pravila, scoring

**Aggregates**:
- `ConflictRuleSet` (Aggregate Root)
  - `ConflictRule` (Entity)

- `Finding` (Aggregate Root)
  - `ConflictEvidence` (Value Object)
  - `Resolution` (Entity)

**Value Objects**:
- `RuleSetMetadata` (version, name, description)
- `RuleDefinition` (type, pattern, severity)
- `ConflictScore` (similarity, severity, confidence)
- `ResolutionDecision` (status, decision, comment)

**Domain Events**:
- `ConflictRuleSetCreated`
- `ConflictDetected`
- `FindingCreated`
- `ResolutionApplied`

**Repositories**:
- `ConflictRuleSetRepository`
- `ConflictRuleRepository`
- `FindingRepository`
- `ResolutionRepository`

**Domain Services**:
- `ConflictDetectionService` - Detekcija konflikata
- `RuleMatchingService` - Matching pravila
- `SeverityCalculationService` - Računanje težine konflikta

---

### 1.5 Draft Review Context

**Odgovornost**: Analiza nacrta propisa, generisanje izveštaja

**Aggregates**:
- `DraftReview` (Aggregate Root)
  - `DraftDocument` (Reference to Document Context)
  - `Finding` (Reference to Conflict Detection Context)
  - `ReviewArtifact` (Entity)

**Value Objects**:
- `ReviewMetadata` (draft_id, corpus_id, param_set_id, status)
- `ReviewProgress` (started_at, ended_at, phase)
- `ArtifactData` (artifact_type, data, created_at)

**Domain Events**:
- `DraftReviewStarted`
- `DraftParsed`
- `ConflictsDetected`
- `ReviewCompleted`
- `ReportGenerated`

**Repositories**:
- `DraftReviewRepository`
- `DraftArtifactRepository`

**Domain Services**:
- `DraftAnalysisService` - Analiza nacrta
- `ReportGenerationService` - Generisanje izveštaja
- `ComparisonService` - Poređenje sa korpusom

---

### 1.6 Configuration Management Context

**Odgovornost**: Parametri, verzionisanje konfiguracija

**Aggregates**:
- `ParamSet` (Aggregate Root)
  - `LLMConfig` (Value Object)
  - `EmbeddingConfig` (Value Object)
  - `SearchConfig` (Value Object)

**Value Objects**:
- `LLMConfig` (model, temperature, max_tokens)
- `EmbeddingConfig` (model, chunk_size, chunk_overlap)
- `SearchConfig` (vector_weight, keyword_weight, graph_weight, top_k)

**Domain Events**:
- `ParamSetCreated`
- `ConfigurationUpdated`

**Repositories**:
- `ParamSetRepository`

**Domain Services**:
- `ConfigurationValidationService` - Validacija konfiguracije
- `ConfigurationComparisonService` - Poređenje konfiguracija

---

## 2. Aggregate Design Patterns

### 2.1 Document Aggregate

```python
class Document(AggregateRoot):
    """
    Aggregate Root za pravni dokument
    """
    def __init__(self, id: UUID, corpus_id: UUID, metadata: DocumentMetadata):
        self.id = id
        self.corpus_id = corpus_id
        self.metadata = metadata
        self._legal_units: List[LegalUnit] = []
        self._domain_events: List[DomainEvent] = []
    
    def add_legal_unit(self, unit: LegalUnit) -> None:
        """Dodaj pravnu jedinicu"""
        self._legal_units.append(unit)
        self._domain_events.append(LegalUnitAdded(self.id, unit.id))
    
    def extract_assertions(self, service: AssertionExtractionService) -> None:
        """Ekstraktuj asercije iz svih pravnih jedinica"""
        for unit in self._legal_units:
            assertions = service.extract(unit)
            unit.add_assertions(assertions)
        self._domain_events.append(AssertionsExtracted(self.id))
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Vrati domain events"""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
```

### 2.2 Corpus Aggregate

```python
class Corpus(AggregateRoot):
    """
    Aggregate Root za korpus
    """
    def __init__(self, id: UUID, metadata: CorpusMetadata):
        self.id = id
        self.metadata = metadata
        self._runs: List[CorpusRun] = []
        self._domain_events: List[DomainEvent] = []
    
    def start_run(self, params: RunParameters) -> CorpusRun:
        """Pokreni novi run"""
        run = CorpusRun(
            id=uuid4(),
            corpus_id=self.id,
            parameters=params,
            status=RunStatus.RUNNING
        )
        self._runs.append(run)
        self._domain_events.append(CorpusRunStarted(self.id, run.id))
        return run
    
    def complete_run(self, run_id: UUID, statistics: RunStatistics) -> None:
        """Završi run"""
        run = self._find_run(run_id)
        run.complete(statistics)
        self._domain_events.append(CorpusRunCompleted(self.id, run_id))
    
    def _find_run(self, run_id: UUID) -> CorpusRun:
        """Pronađi run po ID"""
        for run in self._runs:
            if run.id == run_id:
                return run
        raise ValueError(f"Run {run_id} not found")
```

### 2.3 Finding Aggregate

```python
class Finding(AggregateRoot):
    """
    Aggregate Root za nalaz konflikta
    """
    def __init__(self, id: UUID, review_id: UUID, evidence: ConflictEvidence):
        self.id = id
        self.review_id = review_id
        self.evidence = evidence
        self._resolution: Optional[Resolution] = None
        self._domain_events: List[DomainEvent] = []
    
    def apply_resolution(self, decision: ResolutionDecision, user: str) -> None:
        """Primeni rezoluciju"""
        if self._resolution is not None:
            raise ValueError("Resolution already applied")
        
        self._resolution = Resolution(
            id=uuid4(),
            finding_id=self.id,
            decision=decision,
            user=user,
            timestamp=datetime.utcnow()
        )
        self._domain_events.append(ResolutionApplied(self.id, decision))
    
    def update_resolution(self, decision: ResolutionDecision, user: str) -> None:
        """Ažuriraj rezoluciju"""
        if self._resolution is None:
            raise ValueError("No resolution to update")
        
        self._resolution.update(decision, user)
        self._domain_events.append(ResolutionUpdated(self.id, decision))
```

---

## 3. Value Objects

### 3.1 DocumentMetadata

```python
@dataclass(frozen=True)
class DocumentMetadata:
    """Value Object za metadata dokumenta"""
    filename: str
    title: str
    type: DocumentType
    language: Language
    
    def __post_init__(self):
        if not self.filename:
            raise ValueError("Filename cannot be empty")
        if not self.title:
            raise ValueError("Title cannot be empty")
```

### 3.2 ConflictScore

```python
@dataclass(frozen=True)
class ConflictScore:
    """Value Object za scoring konflikta"""
    similarity: float  # 0.0 - 1.0
    severity: Severity
    confidence: float  # 0.0 - 1.0
    
    def __post_init__(self):
        if not 0.0 <= self.similarity <= 1.0:
            raise ValueError("Similarity must be between 0 and 1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
    
    def is_significant(self) -> bool:
        """Da li je konflikt značajan"""
        return self.similarity > 0.7 and self.confidence > 0.6
```

### 3.3 VectorRepresentation

```python
@dataclass(frozen=True)
class VectorRepresentation:
    """Value Object za vektor reprezentaciju"""
    vector: Tuple[float, ...]  # Immutable tuple
    model: str
    dimensions: int
    
    def __post_init__(self):
        if len(self.vector) != self.dimensions:
            raise ValueError(f"Vector length {len(self.vector)} != dimensions {self.dimensions}")
    
    def cosine_similarity(self, other: 'VectorRepresentation') -> float:
        """Računaj cosine similarity"""
        if self.dimensions != other.dimensions:
            raise ValueError("Vectors must have same dimensions")
        
        dot_product = sum(a * b for a, b in zip(self.vector, other.vector))
        norm_a = math.sqrt(sum(a * a for a in self.vector))
        norm_b = math.sqrt(sum(b * b for b in other.vector))
        
        return dot_product / (norm_a * norm_b)
```

---

## 4. Domain Events

### 4.1 Event Definitions

```python
@dataclass(frozen=True)
class DomainEvent:
    """Base class za sve domain events"""
    event_id: UUID
    occurred_at: datetime
    aggregate_id: UUID

@dataclass(frozen=True)
class DocumentImported(DomainEvent):
    """Event: Dokument je importovan"""
    corpus_id: UUID
    filename: str
    language: Language

@dataclass(frozen=True)
class AssertionsExtracted(DomainEvent):
    """Event: Asercije su ekstraktovane"""
    document_id: UUID
    assertion_count: int

@dataclass(frozen=True)
class ConflictDetected(DomainEvent):
    """Event: Konflikt je detektovan"""
    review_id: UUID
    draft_assertion_id: UUID
    corpus_assertion_id: UUID
    rule_id: UUID
    score: ConflictScore

@dataclass(frozen=True)
class CorpusRunCompleted(DomainEvent):
    """Event: Corpus run je završen"""
    corpus_id: UUID
    run_id: UUID
    statistics: RunStatistics
```

### 4.2 Event Handlers

```python
class DocumentImportedHandler:
    """Handler za DocumentImported event"""
    
    def __init__(self, 
                 parser_service: LegalParserService,
                 embedding_service: EmbeddingGenerationService):
        self.parser_service = parser_service
        self.embedding_service = embedding_service
    
    async def handle(self, event: DocumentImported) -> None:
        """Obradi event"""
        # 1. Parse dokument
        document = await self.parser_service.parse(event.aggregate_id)
        
        # 2. Generiši embeddings
        await self.embedding_service.generate_for_document(document.id)
        
        # 3. Publish novi event
        await self.publish(DocumentParsed(
            event_id=uuid4(),
            occurred_at=datetime.utcnow(),
            aggregate_id=document.id,
            legal_unit_count=len(document.legal_units)
        ))
```

---

## 5. Repositories

### 5.1 Repository Interface

```python
class Repository(ABC, Generic[T]):
    """Base repository interface"""
    
    @abstractmethod
    async def get(self, id: UUID) -> Optional[T]:
        """Pronađi aggregate po ID"""
        pass
    
    @abstractmethod
    async def save(self, aggregate: T) -> None:
        """Sačuvaj aggregate"""
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> None:
        """Obriši aggregate"""
        pass
```

### 5.2 Document Repository

```python
class DocumentRepository(Repository[Document]):
    """Repository za Document aggregate"""
    
    def __init__(self, db: Database, event_bus: EventBus):
        self.db = db
        self.event_bus = event_bus
    
    async def get(self, id: UUID) -> Optional[Document]:
        """Pronađi dokument"""
        row = await self.db.fetch_one(
            "SELECT * FROM documents WHERE id = ?", (str(id),)
        )
        if not row:
            return None
        
        # Reconstruct aggregate
        document = Document(
            id=UUID(row['id']),
            corpus_id=UUID(row['corpus_id']),
            metadata=DocumentMetadata(
                filename=row['filename'],
                title=row['title'],
                type=DocumentType(row['type']),
                language=Language(row['language'])
            )
        )
        
        # Load legal units
        units = await self._load_legal_units(document.id)
        for unit in units:
            document.add_legal_unit(unit)
        
        return document
    
    async def save(self, document: Document) -> None:
        """Sačuvaj dokument"""
        # Save aggregate
        await self.db.execute(
            """INSERT OR REPLACE INTO documents 
               (id, corpus_id, filename, title, type, language)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(document.id), str(document.corpus_id),
             document.metadata.filename, document.metadata.title,
             document.metadata.type.value, document.metadata.language.value)
        )
        
        # Save legal units
        for unit in document._legal_units:
            await self._save_legal_unit(unit)
        
        # Publish domain events
        for event in document.get_domain_events():
            await self.event_bus.publish(event)
```

---

## 6. Domain Services

### 6.1 Conflict Detection Service

```python
class ConflictDetectionService:
    """Domain service za detekciju konflikata"""
    
    def __init__(self,
                 rule_repository: ConflictRuleRepository,
                 assertion_repository: AssertionRepository,
                 embedding_repository: EmbeddingRepository,
                 scoring_service: SeverityCalculationService):
        self.rule_repository = rule_repository
        self.assertion_repository = assertion_repository
        self.embedding_repository = embedding_repository
        self.scoring_service = scoring_service
    
    async def detect_conflicts(self,
                               draft_review: DraftReview,
                               rule_set_id: UUID) -> List[Finding]:
        """Detektuj konflikte između nacrta i korpusa"""
        findings = []
        
        # 1. Load rules
        rules = await self.rule_repository.get_by_set(rule_set_id)
        
        # 2. Load draft assertions
        draft_assertions = await self.assertion_repository.get_by_document(
            draft_review.draft_document_id
        )
        
        # 3. For each draft assertion
        for draft_assertion in draft_assertions:
            # Find similar corpus assertions
            candidates = await self._find_candidates(draft_assertion)
            
            # Check each rule
            for rule in rules:
                for corpus_assertion in candidates:
                    if self._matches_rule(draft_assertion, corpus_assertion, rule):
                        # Calculate score
                        score = await self.scoring_service.calculate(
                            draft_assertion, corpus_assertion, rule
                        )
                        
                        # Create finding
                        finding = Finding(
                            id=uuid4(),
                            review_id=draft_review.id,
                            evidence=ConflictEvidence(
                                draft_assertion_id=draft_assertion.id,
                                corpus_assertion_id=corpus_assertion.id,
                                rule_id=rule.id,
                                score=score
                            )
                        )
                        findings.append(finding)
        
        return findings
    
    async def _find_candidates(self, assertion: Assertion) -> List[Assertion]:
        """Pronađi kandidate za poređenje"""
        # Use semantic search
        embedding = await self.embedding_repository.get_by_assertion(assertion.id)
        similar = await self.embedding_repository.search_similar(
            embedding.vector, top_k=10, threshold=0.25
        )
        
        # Load assertions
        candidates = []
        for emb in similar:
            assertion = await self.assertion_repository.get(emb.assertion_id)
            candidates.append(assertion)
        
        return candidates
```

---

## 7. Application Services (Use Cases)

### 7.1 Import Corpus Use Case

```python
class ImportCorpusUseCase:
    """Application service za import korpusa"""
    
    def __init__(self,
                 corpus_repository: CorpusRepository,
                 document_repository: DocumentRepository,
                 import_service: CorpusImportService,
                 event_bus: EventBus):
        self.corpus_repository = corpus_repository
        self.document_repository = document_repository
        self.import_service = import_service
        self.event_bus = event_bus
    
    async def execute(self, request: ImportCorpusRequest) -> ImportCorpusResponse:
        """Izvršiimport korpusa"""
        # 1. Create corpus
        corpus = Corpus(
            id=uuid4(),
            metadata=CorpusMetadata(
                name=request.name,
                domain_id=request.domain_id,
                language=request.language,
                status=CorpusStatus.IMPORTING
            )
        )
        await self.corpus_repository.save(corpus)
        
        # 2. Start corpus run
        run = corpus.start_run(
            RunParameters(
                param_set_id=request.param_set_id,
                ontology_set_id=request.ontology_set_id,
                conflict_rule_set_id=request.conflict_rule_set_id
            )
        )
        await self.corpus_repository.save(corpus)
        
        # 3. Import documents
        documents = await self.import_service.import_folder(
            corpus_id=corpus.id,
            folder_path=request.folder_path
        )
        
        # 4. Complete run
        statistics = RunStatistics(
            documents_processed=len(documents),
            legal_units_extracted=sum(len(d.legal_units) for d in documents),
            assertions_extracted=sum(
                len(u.assertions) for d in documents for u in d.legal_units
            )
        )
        corpus.complete_run(run.id, statistics)
        await self.corpus_repository.save(corpus)
        
        return ImportCorpusResponse(
            corpus_id=corpus.id,
            run_id=run.id,
            statistics=statistics
        )
```

### 7.2 Search Corpus Use Case

```python
class SearchCorpusUseCase:
    """Application service za pretragu korpusa i chatbot funkcionalnost"""
    
    def __init__(self,
                 corpus_repository: CorpusRepository,
                 assertion_repository: AssertionRepository,
                 embedding_repository: EmbeddingRepository,
                 retrieval_service: RetrievalService,
                 llm_service: LLMService):
        self.corpus_repository = corpus_repository
        self.assertion_repository = assertion_repository
        self.embedding_repository = embedding_repository
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
    
    async def execute(self, request: SearchCorpusRequest) -> SearchCorpusResponse:
        """Pretraži korpus i generiši odgovor"""
        # 1. Validate corpus exists
        corpus = await self.corpus_repository.get(request.corpus_id)
        if not corpus:
            raise ValueError(f"Corpus {request.corpus_id} not found")
        
        # 2. Perform hybrid search (semantic + keyword + graph)
        search_results = await self.retrieval_service.search(
            query=request.query,
            corpus_id=request.corpus_id,
            top_k=request.top_k or 10,
            filters=request.filters
        )
        
        # 3. Rerank results for precision
        reranked_results = await self.retrieval_service.rerank(
            query=request.query,
            results=search_results,
            top_k=request.top_k or 5
        )
        
        # 4. Generate AI response with citations (if chatbot mode)
        ai_response = None
        if request.generate_answer:
            context = self._build_context(reranked_results)
            ai_response = await self.llm_service.generate_answer(
                query=request.query,
                context=context,
                language=corpus.metadata.language
            )
        
        # 5. Build response
        return SearchCorpusResponse(
            query=request.query,
            results=[
                SearchResult(
                    assertion_id=r.assertion_id,
                    document_id=r.document_id,
                    legal_unit_id=r.legal_unit_id,
                    text=r.text,
                    relevance_score=r.score,
                    citation=r.citation
                )
                for r in reranked_results
            ],
            ai_answer=ai_response,
            total_results=len(search_results)
        )
    
    def _build_context(self, results: List[SearchResult]) -> str:
        """Izgradi kontekst za LLM"""
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[{i}] {result.citation}\n{result.text}\n"
            )
        return "\n".join(context_parts)
```

### 7.3 Analyze Draft Use Case

```python
class AnalyzeDraftUseCase:
    """Application service za analizu nacrta"""
    
    def __init__(self,
                 draft_review_repository: DraftReviewRepository,
                 document_repository: DocumentRepository,
                 conflict_detection_service: ConflictDetectionService,
                 report_generation_service: ReportGenerationService):
        self.draft_review_repository = draft_review_repository
        self.document_repository = document_repository
        self.conflict_detection_service = conflict_detection_service
        self.report_generation_service = report_generation_service
    
    async def execute(self, request: AnalyzeDraftRequest) -> AnalyzeDraftResponse:
        """Analiziraj nacrt"""
        # 1. Create draft review
        review = DraftReview(
            id=uuid4(),
            metadata=ReviewMetadata(
                draft_id=request.draft_id,
                corpus_id=request.corpus_id,
                param_set_id=request.param_set_id,
                status=ReviewStatus.ANALYZING
            )
        )
        await self.draft_review_repository.save(review)
        
        # 2. Parse draft
        draft_document = await self.document_repository.get(request.draft_id)
        if not draft_document:
            raise ValueError(f"Draft {request.draft_id} not found")
        
        # 3. Detect conflicts
        findings = await self.conflict_detection_service.detect_conflicts(
            review, request.conflict_rule_set_id
        )
        
        # 4. Save findings
        for finding in findings:
            review.add_finding(finding)
        await self.draft_review_repository.save(review)
        
        # 5. Generate report
        report = await self.report_generation_service.generate(review)
        
        # 6. Complete review
        review.complete()
        await self.draft_review_repository.save(review)
        
        return AnalyzeDraftResponse(
            review_id=review.id,
            findings_count=len(findings),
            report=report
        )
```

---

## 8. Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  (FastAPI Controllers, REST API, WebSocket)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Use Cases, Application Services, DTOs)                     │
│  - ImportCorpusUseCase                                       │
│  - SearchCorpusUseCase                                       │
│  - AnalyzeDraftUseCase                                       │
│  - GenerateReportUseCase                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  (Aggregates, Entities, Value Objects, Domain Services)      │
│  - Document, Corpus, Finding (Aggregates)                    │
│  - ConflictDetectionService (Domain Service)                 │
│  - DocumentMetadata, ConflictScore (Value Objects)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  (Repositories, External Services, Database)                 │
│  - SQLite (Documents, Assertions, Findings)                  │
│  - Qdrant (Embeddings, Semantic Search)                      │
│  - Ollama (LLM Integration)                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Folder Structure (DDD)

```
backend/
├── zaikon/
│   ├── domain/                          # Domain Layer
│   │   ├── __init__.py
│   │   ├── common/                      # Shared kernel
│   │   │   ├── base.py                  # AggregateRoot, Entity, ValueObject
│   │   │   ├── events.py                # DomainEvent base
│   │   │   └── exceptions.py            # Domain exceptions
│   │   │
│   │   ├── document/                    # Document Context
│   │   │   ├── aggregates.py            # Document aggregate
│   │   │   ├── entities.py              # LegalUnit, Assertion
│   │   │   ├── value_objects.py         # DocumentMetadata, etc.
│   │   │   ├── events.py                # DocumentImported, etc.
│   │   │   ├── services.py              # LegalParserService
│   │   │   └── repository.py            # DocumentRepository interface
│   │   │
│   │   ├── corpus/                      # Corpus Context
│   │   │   ├── aggregates.py            # Corpus aggregate
│   │   │   ├── entities.py              # CorpusRun
│   │   │   ├── value_objects.py         # CorpusMetadata, RunParameters
│   │   │   ├── events.py                # CorpusRunStarted, etc.
│   │   │   ├── services.py              # CorpusImportService
│   │   │   └── repository.py            # CorpusRepository interface
│   │   │
│   │   ├── knowledge/                   # Knowledge Representation Context
│   │   │   ├── aggregates.py            # OntologySet, Embedding
│   │   │   ├── entities.py              # OntologyTerm
│   │   │   ├── value_objects.py         # VectorRepresentation
│   │   │   ├── events.py                # EmbeddingsGenerated, etc.
│   │   │   ├── services.py              # EmbeddingGenerationService
│   │   │   └── repository.py            # OntologySetRepository interface
│   │   │
│   │   ├── conflict/                    # Conflict Detection Context
│   │   │   ├── aggregates.py            # ConflictRuleSet, Finding
│   │   │   ├── entities.py              # ConflictRule, Resolution
│   │   │   ├── value_objects.py         # ConflictScore, RuleDefinition
│   │   │   ├── events.py                # ConflictDetected, etc.
│   │   │   ├── services.py              # ConflictDetectionService
│   │   │   └── repository.py            # ConflictRuleSetRepository interface
│   │   │
│   │   ├── review/                      # Draft Review Context
│   │   │   ├── aggregates.py            # DraftReview
│   │   │   ├── entities.py              # ReviewArtifact
│   │   │   ├── value_objects.py         # ReviewMetadata, ReviewProgress
│   │   │   ├── events.py                # DraftReviewStarted, etc.
│   │   │   ├── services.py              # DraftAnalysisService
│   │   │   └── repository.py            # DraftReviewRepository interface
│   │   │
│   │   └── config/                      # Configuration Context
│   │       ├── aggregates.py            # ParamSet
│   │       ├── value_objects.py         # LLMConfig, EmbeddingConfig
│   │       ├── events.py                # ConfigurationUpdated
│   │       └── repository.py            # ParamSetRepository interface
│   │
│   ├── application/                     # Application Layer
│   │   ├── __init__.py
│   │   ├── use_cases/
│   │   │   ├── import_corpus.py         # ImportCorpusUseCase
│   │   │   ├── search_corpus.py         # SearchCorpusUseCase
│   │   │   ├── analyze_draft.py         # AnalyzeDraftUseCase
│   │   │   ├── generate_report.py       # GenerateReportUseCase
│   │   │   └── ...
│   │   ├── dtos/                        # Data Transfer Objects
│   │   │   ├── requests.py              # Request DTOs
│   │   │   └── responses.py             # Response DTOs
│   │   └── services/                    # Application Services
│   │       └── event_bus.py             # Event Bus
│   │
│   ├── infrastructure/                  # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── persistence/
│   │   │   ├── sqlite/                  # SQLite implementations
│   │   │   │   ├── document_repository.py
│   │   │   │   ├── corpus_repository.py
│   │   │   │   └── ...
│   │   │   └── qdrant/                  # Qdrant implementations
│   │   │       └── embedding_repository.py
│   │   ├── external/                    # External services
│   │   │   ├── ollama_client.py         # Ollama integration
│   │   │   └── stanza_client.py         # Stanza NER
│   │   └── event_bus/
│   │       └── in_memory_event_bus.py   # Event bus implementation
│   │
│   └── api/                             # Presentation Layer
│       ├── __init__.py
│       ├── routers/                     # FastAPI routers
│       │   ├── corpus.py
│       │   ├── draft_reviews.py
│       │   └── ...
│       └── dependencies.py              # Dependency injection
```

---

## 10. Dependency Injection

```python
# backend/zaikon/api/dependencies.py

from functools import lru_cache
from zaikon.domain.document.repository import DocumentRepository
from zaikon.infrastructure.persistence.sqlite.document_repository import SQLiteDocumentRepository
from zaikon.application.use_cases.import_corpus import ImportCorpusUseCase

@lru_cache()
def get_document_repository() -> DocumentRepository:
    """Get document repository instance"""
    return SQLiteDocumentRepository(
        db=get_database(),
        event_bus=get_event_bus()
    )

@lru_cache()
def get_import_corpus_use_case() -> ImportCorpusUseCase:
    """Get import corpus use case"""
    return ImportCorpusUseCase(
        corpus_repository=get_corpus_repository(),
        document_repository=get_document_repository(),
        import_service=get_corpus_import_service(),
        event_bus=get_event_bus()
    )

# Usage in FastAPI router
@router.post("/corpora/import")
async def import_corpus(
    request: ImportCorpusRequest,
    use_case: ImportCorpusUseCase = Depends(get_import_corpus_use_case)
):
    response = await use_case.execute(request)
    return response
```

---

## 11. Testing Strategy

### 11.1 Unit Tests (Domain Layer)

```python
# tests/domain/document/test_document_aggregate.py

def test_document_add_legal_unit():
    """Test adding legal unit to document"""
    # Arrange
    document = Document(
        id=uuid4(),
        corpus_id=uuid4(),
        metadata=DocumentMetadata(
            filename="test.txt",
            title="Test Document",
            type=DocumentType.ZAKON,
            language=Language.SR
        )
    )
    
    unit = LegalUnit(
        id=uuid4(),
        document_id=document.id,
        reference=LegalUnitReference(
            unit_type="clan",
            number="1",
            title="Test Article"
        )
    )
    
    # Act
    document.add_legal_unit(unit)
    
    # Assert
    assert len(document._legal_units) == 1
    assert document._legal_units[0] == unit
    
    events = document.get_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], LegalUnitAdded)
```

### 11.2 Integration Tests (Application Layer)

```python
# tests/application/test_import_corpus_use_case.py

@pytest.mark.asyncio
async def test_import_corpus_use_case():
    """Test import corpus use case"""
    # Arrange
    corpus_repo = InMemoryCorpusRepository()
    document_repo = InMemoryDocumentRepository()
    import_service = MockCorpusImportService()
    event_bus = InMemoryEventBus()
    
    use_case = ImportCorpusUseCase(
        corpus_repository=corpus_repo,
        document_repository=document_repo,
        import_service=import_service,
        event_bus=event_bus
    )
    
    request = ImportCorpusRequest(
        name="Test Corpus",
        domain_id=uuid4(),
        language=Language.SR,
        folder_path="/test/path",
        param_set_id=uuid4(),
        ontology_set_id=uuid4(),
        conflict_rule_set_id=uuid4()
    )
    
    # Act
    response = await use_case.execute(request)
    
    # Assert
    assert response.corpus_id is not None
    assert response.statistics.documents_processed > 0
    
    # Verify corpus was saved
    corpus = await corpus_repo.get(response.corpus_id)
    assert corpus is not None
    assert corpus.metadata.name == "Test Corpus"
```

---

## 12. Migration Plan (Current → DDD)

### Faza 1: Refactor Domain Layer (2 weeks)

1. **Week 1**: Create domain model
   - Define aggregates, entities, value objects
   - Implement domain events
   - Create repository interfaces

2. **Week 2**: Implement domain services
   - ConflictDetectionService
   - LegalParserService
   - EmbeddingGenerationService

### Faza 2: Refactor Application Layer (1 week)

1. Create use cases
   - ImportCorpusUseCase
   - AnalyzeDraftUseCase
   - GenerateReportUseCase

2. Implement event bus
   - In-memory event bus
   - Event handlers

### Faza 3: Refactor Infrastructure Layer (2 weeks)

1. **Week 1**: Implement repositories
   - SQLite repositories
   - Qdrant repository

2. **Week 2**: External services
   - Ollama client
   - Stanza client

### Faza 4: Update Presentation Layer (1 week)

1. Update FastAPI routers
2. Implement dependency injection
3. Update API documentation

### Faza 5: Testing & Migration (1 week)

1. Write unit tests
2. Write integration tests
3. Migrate existing data
4. Deploy to production

**Total: 7 weeks**

---

## Zaključak

DDD arhitektura za ZAIKON donosi:

1. **Jasne granice** - Bounded contexts sa jasnim odgovornostima
2. **Konzistentnost** - Aggregates garantuju konzistentnost podataka
3. **Fleksibilnost** - Lako dodavanje novih funkcionalnosti
4. **Testabilnost** - Jasna separacija slojeva
5. **Maintainability** - Kod organizovan po domenima
6. **Scalability** - Mogućnost mikroservisne arhitekture

Sledeći koraci:
1. Review DDD arhitekture sa timom
2. Kreiranje proof-of-concept za jedan bounded context
3. Postepena migracija postojećeg koda
4. Continuous refactoring i poboljšanje