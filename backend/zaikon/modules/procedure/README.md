# Procedure Compliance Module

Ovaj modul prati nacrt kroz faze zakonodavnog postupka i proverava procesnu usaglašenost.

## Komponente

### Schemas (`schemas.py`)

- **ProcedureCase**: Predmet kroz faze pripreme zakona
- **ProcessArtifact**: Procesni dokumenti (RIA, mišljenja, tabele usklađenosti)
- **ProcessRequirement**: Definicija obaveznih artefakata po fazi
- **InstitutionalOpinion**: Mišljenja RSZ, MF, MEI, odbora
- **AlignmentMatrixRow**: Red u tabeli usklađenosti sa EU
- **ReadinessReport**: Izveštaj spremnosti za sledeću fazu

### Service (`service.py`)

- **ProcedureComplianceService**: Glavni servis za procesnu proveru
  - `create_procedure_case()`: Kreira novi predmet
  - `add_artifact()`: Dodaje procesni dokument
  - `generate_readiness_report()`: Generiše izveštaj spremnosti

## Workflow faze

1. **drafting_and_ria**: Izrada nacrta i RIA/AEP
2. **public_consultation**: Javna rasprava
3. **official_opinions**: Zvanična mišljenja (RSZ, MF, MEI)
4. **eu_alignment_package**: EU paket usklađenosti
5. **government_committees**: Odbori Vlade
6. **government_adoption**: Usvajanje od strane Vlade
7. **parliamentary_review**: Skupštinska procedura

## Obavezni artefakti

### Government Bill - Official Opinions

- **rsz_opinion**: Mišljenje RSZ (obavezno za zakone)
- **finance_opinion**: Mišljenje MF (kada postoji budžetski uticaj)
- **mei_opinion**: Mišljenje MEI (kada je relevantno za EU)

### EU Alignment Package

- **eu_alignment_statement**: Izjava o usklađenosti
- **eu_alignment_table**: Tabela usklađenosti

### Public Consultation

- **public_debate_program**: Program javne rasprave
- **public_debate_report**: Izveštaj o javnoj raspravi

## Readiness Status

- **ready**: Spremno za sledeću fazu
- **blocked**: Blokirano (nedostaju kritični artefakti ili nerazrešena negativna mišljenja)
- **incomplete**: Nepotpuno (nedostaju neki artefakti)
- **needs_expert**: Potrebna ekspertska odluka

## Primer upotrebe

```python
from zaikon.modules.procedure.service import ProcedureComplianceService
from uuid import uuid4

service = ProcedureComplianceService()

# Kreiranje predmeta
case = service.create_procedure_case(
    draft_review_id=uuid4(),
    draft_title="Nacrt zakona o šumama",
    proposer="Ministarstvo poljoprivrede",
    procedure_type="government_bill",
    domain="forestry",
    eu_relevance="yes",
    budget_impact="no",
)

# Dodavanje artefakata
rsz_opinion = service.add_artifact(
    procedure_case_id=case.procedure_case_id,
    artifact_type="rsz_opinion",
    title="Mišljenje RSZ",
    issuer="Republički sekretarijat za zakonodavstvo",
    status="positive",
)

# Generisanje izveštaja spremnosti
report = service.generate_readiness_report(
    procedure_case=case,
    artifacts=[rsz_opinion],
    opinions=[],
)

print(f"Status: {report.readiness_status}")
print(f"Missing: {report.missing_artifacts}")
print(f"Blocking: {report.blocking_issues}")
```

## TODO

- [ ] Učitavanje process requirements iz YAML/JSON fajlova
- [ ] Parser za tabele usklađenosti
- [ ] Ekstrakcija metapodataka iz mišljenja
- [ ] Automatska detekcija trajanja javne rasprave
- [ ] Povezivanje primedbi sa draft findings
- [ ] Verzionisanje procesnih pravila