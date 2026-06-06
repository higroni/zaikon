# ZAIKON - Complete System Regeneration Package

This folder contains complete documentation for regenerating the ZAIKON AI-assisted legislative compliance review platform from scratch.

## 📚 Documentation Files

### 1. [COMPLETE_SYSTEM_PROMPT.md](COMPLETE_SYSTEM_PROMPT.md)
**Main regeneration prompt** - Complete system specification including:
- Project overview and core functionality
- Technology stack and architecture
- Pipeline architecture with detailed chains
- Data models and database schema
- API endpoints overview
- Critical implementation details
- Common pitfalls to avoid
- File structure
- Implementation phases
- Testing strategy
- Performance considerations
- Deployment instructions

**Use this as**: Primary reference for understanding the complete system architecture and requirements.

### 2. [CONFLICT_TYPES_SPECIFICATION.md](CONFLICT_TYPES_SPECIFICATION.md)
**Complete conflict detection specification** - Defines all 127 conflict types:
- 8 conflict categories with detailed descriptions
- Detection logic for each conflict type
- Severity levels (Critical, High, Medium, Low)
- **Serbian language examples for every conflict type**
- Detection algorithm pseudocode

**Use this as**: Reference for implementing the conflict detection system with all 127 types and understanding real-world Serbian legal conflicts.

### 3. [DATA_IMPORT_PROCESS.md](DATA_IMPORT_PROCESS.md)
**Data import and processing pipeline** - Detailed explanation of how documents are processed:
- Step-by-step import process (file detection → text extraction → parsing → assertion extraction → indexing)
- Technologies used: PyMuPDF, python-docx, Stanza, BAAI/bge-m3, Qdrant
- Embedding generation process (1024 dimensions)
- Ontology system and auto-tuning mechanism
- NER (Named Entity Recognition) with Stanza
- Data storage formats and rationale (SQLite, Qdrant, JSON)
- Performance optimizations (batch processing, caching)
- Complete data flow diagrams

**Use this as**: Understanding how the system processes documents, generates embeddings, uses ontology, and why specific technologies were chosen.

### 4. [API_SPECIFICATION.md](API_SPECIFICATION.md)
**Complete API documentation** - All REST endpoints:
- Corpus management endpoints
- Draft review endpoints
- Configuration endpoints
- Search and query endpoints
- Health and status endpoints
- Request/response examples
- Error handling
- Pagination and filtering

**Use this as**: API contract for frontend-backend integration and testing.

### 5. [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
**Step-by-step implementation guide** - Practical instructions:
- Prerequisites and setup
- Phase-by-phase implementation (15 days)
- Code examples for each component
- Database initialization
- Pipeline implementation
- Testing procedures
- Deployment instructions
- Troubleshooting guide

**Use this as**: Hands-on guide for building the system step by step.

### 6. [USER_SCENARIOS.md](USER_SCENARIOS.md)
**User scenarios and use cases** - Real-world usage examples:
- Use Case 1: Intelligent search and chatbot assistant
- Use Case 2: Compliance checking and conflict detection
- Step-by-step user journeys for non-technical users (lawyers, legislators)
- UI mockups and interaction flows
- Benefits for different user types
- Common mistakes and how the system handles them

**Use this as**: Understanding how end-users interact with the system and what problems it solves for them.

### 7. [LLM_INTEGRATION.md](LLM_INTEGRATION.md)
**AI models integration guide** - Complete guide for all AI models in ZAIKON:
- **Deo 1**: Embedding and Reranker models (mandatory)
  - BAAI/bge-m3 (1024 dimensions, 3.2GB VRAM)
  - BAAI/bge-reranker-v2-m3 (2.1GB VRAM)
  - Configuration and optimization
- **Deo 2**: LLM integration with Ollama (optional)
  - Recommended models for Serbian (Mistral 7B, Llama 3.1 8B)
  - Model selection for RTX 5070 Ti (16GB VRAM)
  - 5 phases of LLM usage
- **Deo 3**: Complete configuration for all models
  - Admin panel mockups
  - All configurable parameters
- **Deo 4**: Hybrid search strategy
  - Vector (45%) + Keyword (35%) + Graph (20%)
  - Tested optimal weights
  - Performance: ~140ms per query
  - Total VRAM: 11.6GB / 16GB (72.5%)

**Use this as**: Understanding how to integrate and configure all AI models (embeddings, reranker, NER, LLM) and hybrid search strategy.

### 8. [DOMAIN_MODEL.md](DOMAIN_MODEL.md)
**Domain model and component architecture** - Complete entity relationship model:
- **12 Core Entities**: Domain, Corpus, Document, LegalUnit, Assertion, Ontology, DraftReview, DraftUnit, DraftAssertion, Finding, ConflictRule, Embedding
- **Entity Relationship Diagram** with ASCII art visualization
- **Detailed descriptions** of each entity with attributes and examples
- **Relationships** between entities (1:1, 1:N, N:M) with cardinalities
- **Data flow examples**: Import corpus, Draft review, Semantic search
- **Storage mapping**: SQLite tables, Qdrant collections, JSON files
- **API endpoints mapping** for each entity
- **Design decisions** and rationale
- **Scalability considerations** and caching strategies

**Use this as**: Understanding the complete data model, how entities relate to each other, and how data flows through the system.

### 9. [DOMAIN_MODEL_V2.md](DOMAIN_MODEL_V2.md)
**Refined domain model (V2)** - Simplified architecture with unified entities:
- **Unified Document/LegalUnit/Assertion** - Single entities with `is_draft` flag (40% less code)
- **Ontology as Dictionary** - Simplified from N:M to 1:N with Domain
- **Independent ConflictSet** - Reusable across domains (N:M relationship)
- **Flexible Finding** - Connects any 2 assertions (draft vs corpus, draft vs draft, corpus vs corpus)
- **Combined Resolution** - Merged Resolution and Decision into single entity
- **Serbian Language Support** - Parser handles Latin and Cyrillic
- **Hybrid Search** - Vector (45%) + Keyword (35%) + Graph (20%)

**Use this as**: Understanding the refined architecture with less duplication and more flexibility.

### 10. [DOMAIN_MODEL_V3.md](DOMAIN_MODEL_V3.md) ⭐ **LATEST**
**Production-ready domain model (V3)** - Versioning and parameterization:
- **NEW: OntologySet** - Versioned ontology instances (v1.0, v2.0, etc.)
- **NEW: OntologyTerm** - Individual ontology objects (terms, rules)
- **NEW: ConflictRuleSet** - Versioned conflict rule sets (renamed from ConflictSet)
- **NEW: ParamSet** - Parameter tracking (LLM temp, ontology version, weights, etc.)
- **NEW: CorpusRun** - Run tracking with parameters for reproducibility
- **Export/Import** - Export complete "knowledge sets" for migration
- **corpus_run_id** - Added to Document, LegalUnit, Assertion, Embedding for tracking
- **A/B Testing** - Compare different parameter configurations
- **Rollback** - Return to previous versions of ontology/rules

**Use this as**: Production-ready architecture with versioning, parameterization, and export/import capabilities. **Use this for new implementations.**

### 11. [DDD_ARCHITECTURE.md](DDD_ARCHITECTURE.md) ⭐ **NEW**
**Domain-Driven Design architecture** - Complete DDD specification:
- **6 Bounded Contexts**: Document Management, Corpus Management, Knowledge Representation, Conflict Detection, Draft Review, Configuration
- **Aggregates**: Document, Corpus, OntologySet, ConflictRuleSet, Finding, DraftReview, ParamSet
- **Value Objects**: DocumentMetadata, ConflictScore, VectorRepresentation, etc.
- **Domain Events**: DocumentImported, ConflictDetected, CorpusRunCompleted, etc.
- **Domain Services**: ConflictDetectionService, LegalParserService, EmbeddingGenerationService
- **Application Services (Use Cases)**:
  - **ImportCorpusUseCase** - Import and index legal documents
  - **SearchCorpusUseCase** - Search corpus and chatbot functionality
  - **AnalyzeDraftUseCase** - Analyze draft and detect conflicts
- **Layered Architecture**: Presentation → Application → Domain → Infrastructure
- **Complete folder structure** for DDD implementation
- **Migration plan**: 7-week roadmap from current to DDD architecture

**Use this as**: Blueprint for refactoring ZAIKON to Domain-Driven Design architecture with clear bounded contexts, aggregates, and domain events.

### 12. [LESSONS_LEARNED.md](LESSONS_LEARNED.md)
**Lessons learned and best practices** - Critical knowledge from development:
- **Top 5 Critical Errors** that cost the most time:
  - StoreAssertionsStep in wrong chain (4h)
  - JSON instead of SQLite (6h)
  - Cyrillic not supported (2h)
  - Batch size too large (2h)
  - Artifact validation too strict (3h)
- **Top 5 Optimizations** discovered through testing:
  - Hybrid search 45-35-20 weights (best balance)
  - Batch processing (10x faster)
  - Parallel execution (2x faster search)
  - Caching (45x faster repeated queries)
  - Database indexing (100x faster queries)
- **Best Practices** for algorithms and procedures
- **Testing strategies** (unit, integration, performance)
- **Deployment guidelines**
- **Monitoring and maintenance**
- **Checklist for next iteration**

**Use this as**: Avoiding common mistakes, applying proven optimizations, and following best practices discovered during development. **Read this FIRST** before starting implementation to save 20+ hours of debugging time.

---

## 🚀 Quick Start

### For AI Assistants (Claude, ChatGPT, etc.)

**Prompt to use**:
```
I need to build the ZAIKON system - an AI-assisted legislative compliance review platform.

Please read and understand these documents in order:
1. LESSONS_LEARNED.md - CRITICAL: Read this FIRST to avoid common mistakes and save 50+ hours
2. DOMAIN_MODEL.md - for understanding entities and their relationships
3. COMPLETE_SYSTEM_PROMPT.md - for overall architecture
4. USER_SCENARIOS.md - for understanding user needs and use cases
5. DATA_IMPORT_PROCESS.md - for understanding data processing pipeline
6. LLM_INTEGRATION.md - for AI models setup (embeddings, reranker, LLM, hybrid search)
7. IMPLEMENTATION_GUIDE.md - for step-by-step instructions
8. CONFLICT_TYPES_SPECIFICATION.md - for conflict detection details
9. API_SPECIFICATION.md - for API implementation

Start with Phase 1 from the Implementation Guide and proceed systematically through all phases.
```

### For Human Developers

1. **Read** `LESSONS_LEARNED.md` **FIRST** - Critical mistakes and best practices (saves 50+ hours!)
2. **Read** `DOMAIN_MODEL.md` - Understand all entities and their relationships
3. **Read** `COMPLETE_SYSTEM_PROMPT.md` to understand the system
4. **Read** `USER_SCENARIOS.md` to understand user needs and workflows
5. **Read** `DATA_IMPORT_PROCESS.md` to understand data processing
6. **Read** `LLM_INTEGRATION.md` to understand AI models setup (embeddings, reranker, LLM, hybrid search)
7. **Follow** `IMPLEMENTATION_GUIDE.md` for step-by-step implementation
8. **Reference** `CONFLICT_TYPES_SPECIFICATION.md` when implementing conflict detection
9. **Use** `API_SPECIFICATION.md` for API development and testing

---

## 🎯 System Overview

**ZAIKON** is an AI-assisted platform that helps legal professionals analyze draft regulations against existing legal corpus to detect conflicts, inconsistencies, and compliance issues.

### Core Features
- **Corpus Management**: Import and index legal documents (TXT, PDF, DOCX)
- **Document Parsing**: Extract legal structure (articles, paragraphs, sections)
- **Assertion Extraction**: Identify normative statements from legal text
- **Conflict Detection**: Detect 127 types of legal conflicts across 8 categories
- **Draft Review**: Analyze draft regulations against corpus
- **Findings Report**: Generate detailed conflict reports with recommendations

### Technology Stack
- **Backend**: FastAPI (Python 3.12), SQLAlchemy, SQLite
- **Frontend**: React 18, TypeScript, Vite
- **Vector Store**: Qdrant (embedded mode)
- **Embeddings**: BAAI/bge-m3 (1024 dimensions)
- **Reranker**: BAAI/bge-reranker-v2-m3
- **NLP**: Stanza 1.9.2 (Serbian language)
- **Document Processing**: PyMuPDF 1.24.13, python-docx 1.1.2
- **Deep Learning**: PyTorch 2.5.1
- **LLM**: Ollama (optional, for advanced features)

---

## 📋 Implementation Phases

### Phase 1: Core Infrastructure (Days 1-3)
- Project setup
- Configuration management
- Database schema
- Pipeline base classes

### Phase 2: Document Processing (Days 4-5)
- Legal document parser (Latin/Cyrillic support)
- Text extraction (TXT, PDF, DOCX)
- Document normalization

### Phase 3: Corpus Management (Days 6-8)
- Corpus CRUD operations
- File-by-file import pipeline
- Assertion extraction
- Indexing (keyword, vector, structure)

### Phase 4: Draft Review (Days 9-11)
- Draft parsing
- Draft assertion extraction
- Conflict detection algorithm
- Finding storage

### Phase 5: Conflict Detection (Days 12-13)
- 127 conflict types implementation
- Slot-based matching
- Candidate scoring
- Severity calculation

### Phase 6: Frontend (Days 14-15)
- React application setup
- Corpus management UI
- Draft review interface
- Findings display

---

## 🔑 Critical Implementation Details

### 1. Assertion Storage
**CRITICAL**: `StoreAssertionsStep` must be in the per-file processing chain, NOT in the main import chain.

```python
# CORRECT: Inside ProcessFilesWithProgressStep._process_single_file()
steps = [
    ExtractTextStep(),
    NormalizeTextStep(),
    IdentifyLegalDocumentsStep(),
    ParseLegalStructureStep(),
    ConvertToCanonicalJsonStep(),
    ExtractNormativeAssertionsStep(),
    StoreAssertionsStep(),  # ← HERE
    # ... more steps
]
```

### 2. Database Paths
Always use centralized database path from settings:
```python
from zaikon.core.config import settings
db_path = settings.database_path  # "data/zaikon.db"
```

### 3. Artifact Validation
Always validate artifacts before use:
```python
artifact = context.get_artifact("normative_assertions")
if not artifact:
    # Handle missing artifact
    return context
```

### 4. Unicode Handling
Always specify UTF-8 encoding:
```python
with open(file, "r", encoding="utf-8") as f:
    text = f.read()
```

---

## 🧪 Testing

### Unit Tests
```bash
cd backend
pytest tests/unit/
```

### Integration Tests
```bash
cd backend
pytest tests/integration/
```

### System Tests
```bash
# Import test corpus
python scripts/import_test_corpus.py

# Create test draft
python scripts/create_test_draft.py

# Verify conflict detection
python scripts/verify_conflicts.py
```

---

## 📊 Database Schema

### Core Tables
- `corpora` - Corpus collections
- `corpus_documents` - Legal documents
- `corpus_assertions` - Extracted assertions
- `draft_reviews` - Draft review sessions
- `draft_artifacts` - Pipeline artifacts
- `findings` - Detected conflicts
- `import_file_progress` - Import tracking

---

## 🔍 Conflict Detection

### 8 Categories, 127 Types
1. **Normative Conflicts** (16 types) - Contradictory obligations, prohibitions, permissions
2. **Temporal Conflicts** (15 types) - Deadline conflicts, retroactive application
3. **Hierarchical Conflicts** (18 types) - Constitutional violations, law hierarchy
4. **Procedural Conflicts** (16 types) - Conflicting procedures, requirements
5. **Scope Conflicts** (17 types) - Jurisdictional overlaps, coverage conflicts
6. **Penalty Conflicts** (14 types) - Conflicting sanctions, fines
7. **Definitional Conflicts** (16 types) - Inconsistent terminology, definitions
8. **Implementation Conflicts** (15 types) - Resource allocation, timeline conflicts

### Detection Algorithm
1. Find candidate corpus assertions (similarity > 0.25)
2. Require action or deadline match
3. Apply conflict rules
4. Calculate severity
5. Generate findings with recommendations

---

## 🚨 Common Pitfalls

### ❌ WRONG
```python
# Adding StoreAssertionsStep to main chain
FileByFileImportChain(steps=[
    ...,
    ProcessFilesWithProgressStep(),
    StoreAssertionsStep(),  # ← WRONG!
])
```

### ✅ CORRECT
```python
# StoreAssertionsStep is already in per-file chain
# Inside ProcessFilesWithProgressStep._process_single_file()
steps = [
    ...,
    ExtractNormativeAssertionsStep(),
    StoreAssertionsStep(),  # ← CORRECT!
]
```

---

## 📞 Support

For questions or issues during implementation:
1. **Check `LESSONS_LEARNED.md` FIRST** - Most common issues are documented here
2. **Check `DOMAIN_MODEL.md`** - Understand entity relationships and data flow
3. Check `COMPLETE_SYSTEM_PROMPT.md` for architecture details
4. Review `USER_SCENARIOS.md` for user requirements and workflows
5. Review `DATA_IMPORT_PROCESS.md` for data processing pipeline
6. Review `LLM_INTEGRATION.md` for AI models setup and hybrid search
7. Follow `IMPLEMENTATION_GUIDE.md` for step-by-step instructions
8. Consult `CONFLICT_TYPES_SPECIFICATION.md` for conflict detection
9. Reference `API_SPECIFICATION.md` for API details

---

## 📝 License

This documentation is provided for system regeneration purposes.

---

## 🎓 Learning Path

### For Beginners
1. **Start with `LESSONS_LEARNED.md`** - Learn from mistakes (CRITICAL!)
2. **Read `DOMAIN_MODEL.md`** - Understand all entities and relationships
3. Read `COMPLETE_SYSTEM_PROMPT.md` - understand the big picture
4. Read `USER_SCENARIOS.md` - understand what users need
5. Read `DATA_IMPORT_PROCESS.md` - understand how data flows through the system
6. Read `LLM_INTEGRATION.md` - understand AI models setup (embeddings, reranker, LLM, hybrid search)
7. Read `IMPLEMENTATION_GUIDE.md` Phase 1 - set up the project
8. Follow each phase sequentially
9. Test after each phase

### For Experienced Developers
1. **Read `LESSONS_LEARNED.md`** - Critical mistakes and optimizations (saves 50+ hours!)
2. **Read `DOMAIN_MODEL.md`** - Quick overview of entities and data flow
3. Skim `COMPLETE_SYSTEM_PROMPT.md` - get architecture overview
4. Review `USER_SCENARIOS.md` - understand user workflows
5. Review `DATA_IMPORT_PROCESS.md` - understand data processing technologies
6. Review `LLM_INTEGRATION.md` - understand AI models and hybrid search
7. Jump to specific sections in `IMPLEMENTATION_GUIDE.md`
8. Reference `API_SPECIFICATION.md` and `CONFLICT_TYPES_SPECIFICATION.md` as needed
9. Implement in parallel where possible

---

## 🔄 Version History

- **v1.2** (2024-06-06) - Added domain model and extended lessons learned
  - **NEW**: Domain model with 12 core entities and relationship diagram
  - **NEW**: Extended lessons learned with debugging, caching, and UI lessons (50h savings)
  - Complete entity descriptions with examples
  - Data flow examples and storage mapping
  - Design decisions and scalability considerations
  
- **v1.1** (2024-06-06) - Added lessons learned and best practices
  - Lessons learned document with critical mistakes and optimizations
  - Updated LLM integration guide with hybrid search strategy (45-35-20 weights)
  - Updated README with proper document ordering (lessons learned first!)
  
- **v1.0** (2024-06-06) - Initial complete documentation package
  - Complete system prompt
  - User scenarios and use cases
  - 127 conflict types specification with Serbian examples
  - Data import process documentation
  - AI models integration guide (embeddings, reranker, NER, LLM)
  - Full API documentation
  - Step-by-step implementation guide

---

**Ready to build ZAIKON? Start with `LESSONS_LEARNED.md` to avoid common mistakes, then `DOMAIN_MODEL.md` to understand the data model, then proceed to `COMPLETE_SYSTEM_PROMPT.md`!**