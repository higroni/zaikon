# MASTER_CONFLICT_DETECTION_ACTION_PLAN

Ovaj dokument je tehnicki akcioni plan za dodavanje naprednog otkrivanja
nesaglasnosti u zAIkon. Naslanja se na
`MASTER_CONFLICT_DETECTION_ROADMAP.md`, ali je namerno operativniji: sta se
gradi, kojim redom, u kojim modulima, koji podaci su potrebni i kako se meri da
li sistem stvarno radi.

Glavni cilj je da se novi primeri nesaglasnosti ne resavaju pisanjem novog
hard-coded backend checkera, vec kroz kombinaciju:

- strukturisanih normativnih tvrdnji;
- pravne ontologije i recnika;
- konfigurabilnih rule packova;
- LLM ekstrakcije pod strogom JSON semom;
- gold/evaluation seta;
- review feedback-a pravnika.

## Kratka Dijagnoza Trenutnog Stack-a

Trenutno vec postoji:

- import PDF/DOCX/TXT dokumenata;
- normalizacija cirilice u latinicu;
- parser pravne strukture;
- canonical JSON;
- SQLite mirror za dokumente;
- retrieval po pravnim jedinicama;
- draft review pipeline;
- nalazi i review odluke;
- React GUI sa trace prikazom.

Nedostaje:

- masinski model normativnih tvrdnji;
- ontologija aktera, radnji, objekata, institucija i oblasti;
- genericki engine za poredjenje slotova;
- rule pack DSL;
- procesni compliance modul;
- strukturisan evidence/slot diff;
- evaluacioni dataset sa pozitivnim i negativnim primerima;
- alati za tjuning bez izmene Python koda.

## Ciljna Arhitektura

Dodati cetiri nova backend modula:

1. `ontology`
   - ucitava pravni recnik iz YAML/JSON fajlova;
   - normalizuje aktere, radnje, objekte, oblasti, institucije i inspekcije;
   - drzi hijerarhije sirine i nadleznosti.

2. `assertions`
   - iz pravnih jedinica izvlaci normativne tvrdnje;
   - cuva slotove: actor, action, object, modality, deadline, condition,
     exception, competence, sanction, validity;
   - pravi assertion index za corpus i draft.

3. `conflicts`
   - generise kandidate za poredjenje;
   - ucitava rule pack;
   - izvrsava genericke konflikt operatore;
   - pravi `Finding` sa slot diffom i citatima.

4. `procedure`
   - modeluje faze pripreme zakona;
   - prati RIA/AEP, javnu raspravu, zvanicna misljenja i EU alignment paket;
   - pravi readiness report za sledecu proceduralnu kapiju.

Postojeci `checkers` modul ostaje, ali treba vremenom da postane adapter preko
`conflicts` engine-a. Postojeci hard-coded checkeri ostaju kao fallback i kao
regression zastita dok genericki engine ne sazri.

## Faza 0: Stabilizacija Osnove

Trajanje: 1-2 dana.

Zadaci:

- ocistiti mojibake u postojecim backend stringovima gde postoje;
- dodati `docs/master/MASTER_CONFLICT_DETECTION_ROADMAP.md` i ovaj dokument u
  commit;
- dodati smoke test za primer:
  - "Obelezavanje drveca moze da radi svaki gradjanin";
  - corpus odredba: "ovlasceno preduzece/lice";
- dodati smoke test za primer:
  - "rok 15 dana";
  - corpus odredba: "rok 30 dana";
- dodati smoke test za primer pogresne nadleznosti:
  - "kontrolu hrane vrsi inspekcija ministarstva gradjevine";
  - corpus: nadleznost sanitarne/veterinarske/poljoprivredne inspekcije.

Izlaz:

- trenutni sistem ima poznate regression primere;
- znamo sta sada prolazi, sta pada, i sta novi engine mora da popravi.

## Faza 1: Ontology Pack

Trajanje: 3-5 dana.

### Novi fajlovi

```text
backend/zaikon/modules/ontology/
  __init__.py
  schemas.py
  service.py
  README.md
backend/zaikon/rules/ontology/
  base_sr.yaml
  forestry.yaml
  food_safety.yaml
  government_procedure.yaml
```

### Minimalni `base_sr.yaml`

```yaml
version: 0.1.0
language: sr
actors:
  any_person:
    labels: ["svako lice", "bilo koje lice", "svaki gradjanin", "gradjanin"]
    broader_than: ["natural_person", "citizen"]
  citizen:
    labels: ["gradjanin", "fizicko lice"]
  authorized_entity:
    labels: ["ovlasceno lice", "ovlasceno pravno lice", "ovlasceno preduzece"]
  competent_authority:
    labels: ["nadlezni organ", "nadlezno ministarstvo"]
actions:
  inspect:
    labels: ["kontrolise", "vrsi kontrolu", "obavlja nadzor", "inspekcijski nadzor"]
  mark_tree:
    labels: ["obelezavanje drveca", "obelezavanje stabala"]
objects:
  food:
    labels: ["hrana", "namirnice", "prehrambeni proizvodi"]
  tree:
    labels: ["drvo", "drvece", "stablo", "stabla"]
domains:
  food_safety:
    labels: ["hrana", "bezbednost hrane", "veterinarski", "sanitarni"]
  construction:
    labels: ["gradjevina", "gradjevinski", "urbanizam"]
```

### Servis

`OntologyService` treba da podrzi:

- `normalize_text_term(value)`;
- `match_actor(text)`;
- `match_action(text)`;
- `match_object(text)`;
- `match_domain(text)`;
- `is_broader_actor(draft_actor, corpus_actor)`;
- `is_wrong_domain(actor_domain, object_domain)`;
- `reload()`.

### API

Dodati:

- `GET /api/v1/ontology`
- `POST /api/v1/ontology/reload`
- `GET /api/v1/ontology/terms?query=...`

### Testovi

- sinonimi za aktere;
- sirina aktera: `any_person` je siri od `authorized_entity`;
- domeni: `construction` nije kompatibilan sa `food_safety` za kontrolu hrane;
- latinizacija radi pre match-a.

## Faza 2: Normative Assertions

Trajanje: 5-8 dana.

### Novi modeli

```python
class NormativeAssertion(BaseModel):
    assertion_id: UUID
    document_id: str | None = None
    pipeline_run_id: UUID | None = None
    corpus_id: UUID | None = None
    legal_unit_id: str
    source_path: str
    assertion_type: str
    modality: str | None = None
    actor: LegalSlot | None = None
    action: LegalSlot | None = None
    object: LegalSlot | None = None
    domain: LegalSlot | None = None
    deadline: DeadlineSlot | None = None
    condition: LegalSlot | None = None
    exception: LegalSlot | None = None
    sanction: SanctionSlot | None = None
    source_quote: str
    confidence: float
    slot_confidence: dict[str, float]
    extraction_method: str
```

### Skladistenje

Za MVP koristiti SQLite tabele:

```sql
CREATE TABLE normative_assertions (
  assertion_id TEXT PRIMARY KEY,
  corpus_id TEXT,
  document_id TEXT,
  pipeline_run_id TEXT,
  legal_unit_id TEXT NOT NULL,
  source_path TEXT,
  assertion_type TEXT NOT NULL,
  modality TEXT,
  actor_json TEXT,
  action_json TEXT,
  object_json TEXT,
  domain_json TEXT,
  deadline_json TEXT,
  condition_json TEXT,
  exception_json TEXT,
  sanction_json TEXT,
  source_quote TEXT NOT NULL,
  confidence REAL NOT NULL,
  slot_confidence_json TEXT NOT NULL,
  extraction_method TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

Napomena: moze biti novi `SQLiteAssertionStore`, umesto sirenja postojeceg
`SQLiteDocumentStore`, da granice ostanu ciste.

### Ekstraktori

Implementirati hibridno:

1. `RuleBasedAssertionExtractor`
   - rokovi: `u roku od 15 dana`, `najkasnije u roku od`, `u roku od osam dana`;
   - modaliteti: `duzan je`, `mora`, `ne sme`, `zabranjeno je`, `moze`,
     `ovlascen je`, `nadlezan je`;
   - nadleznost: obrasci `kontrolu ... vrsi ...`, `nadzor nad ... vrsi ...`;
   - definicije: `u daljem tekstu:`;
   - prestanak vazenja: `prestaje da vazi`.

2. `OntologySlotNormalizer`
   - mapira raw slotove u canonical slotove;
   - dodaje domain i specificity;
   - daje confidence.

3. `LLMAssertionExtractor`
   - samo iza feature flag-a;
   - schema-bound JSON;
   - ne sme da proizvede tvrdnju bez `source_quote` i `legal_unit_id`;
   - cuva prompt/output artefakt za replay.

### Pipeline integracija

Corpus import:

- posle `convert_to_canonical_json` dodati:
  - `extract_normative_assertions`;
  - `normalize_legal_slots`;
  - `store_assertions`.

Draft review:

- posle `convert_to_canonical_json` dodati:
  - `extract_draft_assertions`;
  - `normalize_draft_slots`;
  - `store_draft_assertions`.

Artefakti:

- `normative_assertions`
- `normalized_assertions`
- `assertion_store_report`

### API

- `GET /api/v1/assertions?document_id=...`
- `GET /api/v1/assertions?corpus_id=...`
- `GET /api/v1/draft-reviews/{id}/assertions`

### Testovi

- rok 15/30 dana;
- pogresna nadleznost za kontrolu hrane;
- ovlasceno lice vs svaki gradjanin;
- zabrana vs dozvola;
- primer bez konflikta kao negativan test.

## Faza 3: Candidate Retrieval Za Konflikte

Trajanje: 3-5 dana.

Postojeci retrieval je dobar za korisnicku pretragu, ali konflikt engine treba
strukturisane kandidate.

### Novi servis

`ConflictCandidateService`:

- za svaku draft assertion tvrdnju pronalazi corpus assertions;
- scoring kombinuje:
  - isti action;
  - isti object;
  - isti domain;
  - direktna referenca;
  - isti ili kompatibilan actor;
  - semanticka slicnost source_quote;
  - pravna hijerarhija dokumenta.

### Model

```json
{
  "candidate_id": "uuid",
  "draft_assertion_id": "uuid",
  "corpus_assertion_id": "uuid",
  "score": 0.84,
  "match_reasons": ["same_action", "same_object", "same_domain"],
  "reject_reasons": [],
  "retrieval_method": "assertion_slot_match+semantic"
}
```

### Artefakti/API

- artefakt `conflict_candidates`;
- `GET /api/v1/draft-reviews/{id}/conflict-candidates`.

### Acceptance

Za svaki gold primer mora da postoji relevantan corpus kandidat u top 5. Ako
kandidat nije pronadjen, problem nije u rule engine-u, nego u extraction ili
candidate retrieval fazi.

## Faza 4: Conflict Rule Engine

Trajanje: 7-10 dana.

### Novi fajlovi

```text
backend/zaikon/modules/conflicts/
  __init__.py
  schemas.py
  service.py
  rule_loader.py
  operators.py
  evidence.py
  README.md
backend/zaikon/rules/conflicts/
  registry.json
  active_rules.json
  hierarchy.yaml
  competence.yaml
  actor_scope.yaml
  modality.yaml
  material_scope.yaml
  deadlines.yaml
  conditions_exceptions.yaml
  definitions_terminology.yaml
  references.yaml
  finance_budget.yaml
  sanctions_enforcement.yaml
  procedure_rights.yaml
  data_registers_transparency.yaml
  eu_alignment.yaml
  internal_consistency.yaml
```

### Minimalni operatori

- `equals`
- `not_equal`
- `greater_than`
- `less_than`
- `broader_than_allowed`
- `narrower_than_required`
- `wrong_domain_for_object`
- `modality_opposes`
- `source_rank_lower_than`
- `delegation_missing`
- `scope_expanded`
- `scope_narrowed`
- `condition_added`
- `condition_removed`
- `exception_added`
- `exception_removed`
- `reference_missing`
- `reference_stale`
- `validity_not_active`
- `amount_out_of_range`
- `required_artifact_missing`
- `opinion_unresolved`
- `alignment_row_incomplete`
- `missing_required_slot`
- `requires_explanation_when_status`

### Comprehensive rule pack

Implementation note: MVP code currently uses `registry.json` to avoid adding a
YAML parser dependency; the same schema can later be represented as YAML.

Engine scope nije ogranicen na prva tri korisnicka primera. Svi tipovi iz
`MASTER_CONFLICT_TAXONOMY.md` moraju biti registrovani u
`backend/zaikon/rules/conflicts/registry.json`.

Prvi tehnicki cilj nije da svi tipovi odmah imaju visok automatski confidence,
nego da svi postoje u engine-u kao rule definitions sa jasnim statusom:

- `active_auto`: moze automatski da proizvodi nalaz;
- `active_warning`: proizvodi nalaz kao warning;
- `needs_expert_review`: zna kategoriju, ali zahteva pravnika;
- `not_evaluated_missing_data`: rule postoji, ali nema potrebne slotove;
- `not_applicable`: rule nije primenljiv za taj document/procedure context.

Minimalne rule family grupe:

- hijerarhija i pravni osnov;
- nadleznost i institucije;
- akteri/adresati/opseg lica;
- modaliteti obaveza, zabrana, dozvola i prava;
- radnja, predmet regulacije i materijalni opseg;
- rokovi, vreme i vazenje;
- uslovi, izuzeci i posebni rezimi;
- definicije, terminologija i klasifikacije;
- reference i upucivanja;
- finansije, takse, naknade i budzet;
- sankcije, mere i nadzor;
- postupak, prava stranaka i pravni lekovi;
- podaci, registri, transparentnost i poverljivost;
- EU uskladjivanje;
- procesna usaglasenost;
- unutrasnja konzistentnost nacrta.

Primeri `authority_scope_conflict`, `deadline_mismatch` i
`competence_conflict` su samo pocetni regression smoke testovi za proveru da
pipeline radi end-to-end. Ne predstavljaju granicu scope-a.

### Evidence

Svaki nalaz mora imati:

```json
{
  "draft_assertion_id": "uuid",
  "corpus_assertion_id": "uuid",
  "draft_quote": "...",
  "corpus_quote": "...",
  "draft_path": "article:1",
  "corpus_path": "article:45/paragraph:3",
  "slot_diffs": [
    {
      "slot": "actor",
      "draft_value": "any_person",
      "corpus_value": "authorized_entity",
      "relation": "broader_than_allowed"
    }
  ],
  "rule_id": "authority_scope_conflict.default",
  "rule_version": "0.1.0",
  "candidate_score": 0.84,
  "confidence": 0.78
}
```

### Integracija sa postojecim nalazima

`FindingRecord.evidence` trenutno moze da primi fleksibilni JSON. Za MVP
koristiti to polje, ali standardizovati oblik. Kasnije dodati posebnu tabelu
`finding_evidence`.

### API

- `GET /api/v1/conflicts/types`
- `GET /api/v1/conflicts/types/{finding_type}`
- `POST /api/v1/conflicts/reload`
- `GET /api/v1/conflict-rules`
- `POST /api/v1/conflict-rules/reload`
- `GET /api/v1/draft-reviews/{id}/conflict-trace`

## Faza 5: Procedure Compliance Modul

Trajanje: 7-12 dana.

### Novi fajlovi

```text
backend/zaikon/modules/procedure/
  __init__.py
  schemas.py
  service.py
  artifact_extractor.py
  rule_loader.py
  readiness.py
  README.md
backend/zaikon/rules/procedure/
  government_bill.yaml
  eu_alignment.yaml
  public_consultation.yaml
```

### Modeli

- `ProcedureCase`
- `ProcessArtifact`
- `ProcessRequirement`
- `InstitutionalOpinion`
- `AlignmentMatrixRow`
- `ReadinessReport`

### Minimalni workflow

1. korisnik kreira procedure case iz draft review-a;
2. korisnik dodaje dokumente: RIA, izvestaj javne rasprave, misljenje RSZ,
   misljenje MF, misljenje MEI, izjava, tabela uskladjenosti;
3. sistem ekstraktuje tekst i klasifikuje artefakt;
4. rule pack proverava sta nedostaje i sta blokira sledecu fazu;
5. GUI prikazuje proceduralni readiness.

### Prva procesna pravila

- nedostaje RIA/AEP kada je obavezna ili nije oznaceno da nije obavezna;
- javna rasprava traje krace od konfigurisanog minimuma;
- nema izvestaja o javnoj raspravi;
- nema misljenja RSZ;
- nema misljenja MF kada postoji fiskalni efekat;
- nema MEI izjave/tabele kada je `eu_relevance=yes`;
- tabela uskladjenosti nema CELEX ili nema mapiranje domace odredbe;
- otvorena primedba RSZ/MEI/MF nije razresena.

### API

- `POST /api/v1/procedure-cases`
- `GET /api/v1/procedure-cases`
- `GET /api/v1/procedure-cases/{id}`
- `POST /api/v1/procedure-cases/{id}/artifacts`
- `POST /api/v1/procedure-cases/{id}/run`
- `GET /api/v1/procedure-cases/{id}/readiness-report`

### GUI

Dodati ekran `Procedura`:

- faze kao timeline;
- checklist dokumenata;
- upload/local path browse;
- status svakog misljenja;
- otvorene primedbe;
- readiness: spremno, blokirano, nedostaje, ekspert;
- link ka povezanim draft findings.

## Faza 6: GUI Za Tjuning

Trajanje: 5-8 dana.

Dodati u postojece ekrane:

### Dokumenti

- tab `Tvrdnje`;
- tabela assertiona po clanu;
- filter po actor/action/object/deadline/domain;
- confidence i raw/canonical prikaz.

### Provera nacrta

- trace faze:
  - extracted draft assertions;
  - normalized slots;
  - conflict candidates;
  - fired rules;
  - rejected candidates;
  - findings.
- klik na nalaz pokazuje slot diff.

### Nalazi

- filter po `finding_type`;
- filter po `rule_id`;
- filter po confidence;
- prikaz "verovatno zakazala faza":
  - extraction;
  - ontology;
  - candidate retrieval;
  - rule;
  - explanation.

### Podesavanja

- reload ontology;
- reload conflict rules;
- reload procedure rules;
- prikaz verzija rule/ontology packova.

## Faza 7: Evaluation Harness

Trajanje: 5-8 dana.

### Novi fajlovi

```text
backend/zaikon/modules/evaluation/
  __init__.py
  schemas.py
  service.py
  runner.py
  metrics.py
backend/zaikon/rules/evaluation/
  gold_cases.json
```

### Format gold primera

```yaml
id: food_competence_conflict_001
domain: food_safety
draft:
  title: Nacrt pravilnika o kontroli hrane
  text: |
    Clan 1.
    Kontrolu hrane vrsi inspekcija ministarstva nadleznog za gradjevinu.
corpus:
  documents:
    - source_uri: fixtures/food_safety_law.txt
expected_findings:
  - finding_type: competence_conflict
    risk_level: high
    must_include_draft_terms: ["kontrolu hrane", "gradjevinu"]
    must_include_corpus_terms: ["hrana", "nadlezna inspekcija"]
    slot_diffs:
      - slot: actor_domain
        relation: wrong_domain_for_object
negative_findings: []
```

### Metrike

- candidate recall@5;
- finding precision;
- finding recall;
- slot accuracy;
- citation coverage;
- false positive rate;
- expert acceptance rate;
- regression diff po rule pack verziji.

### API

- `POST /api/v1/evaluation/run`
- `GET /api/v1/evaluation/cases`

## Podaci Potrebni Za Treniranje I Tjuning

U ovoj fazi "treniranje" ne treba shvatiti prvenstveno kao fine-tuning LLM-a.
Najveca vrednost dolazi iz kvalitetnog gold seta, ontologije, rule packa i
review feedback-a. Fine-tuning dolazi kasnije, ako se sakupi dovoljno oznacenih
primera.

### 1. Korpus vazecih propisa

Potrebno:

- zakoni po oblastima;
- pravilnici, naredbe, uredbe, strategije;
- verzije i izmene/dopune;
- precisceni tekst kada postoji;
- Sluzbeni glasnik broj i datum;
- valid_from/valid_to;
- dokument tip i pravna snaga.

Minimalno za prve oblasti:

- sumarstvo;
- hrana/bezbednost hrane;
- gradjevina/urbanizam;
- finansije/budzet;
- EU alignment primeri.

### 2. Anotirane pravne jedinice

Za svaki dokument treba rucno oznaciti reprezentativan uzorak:

- clan/stav/tacka;
- actor;
- action;
- object;
- modality;
- deadline;
- condition;
- exception;
- domain;
- competence;
- sanction;
- definition;
- source_quote.

Po oblasti je za pocetak dovoljno 100-200 pravnih jedinica, ako su dobro
odabrane. Cilj nije velika kolicina nego pokrivanje obrazaca.

### 3. Parovi nacrt-korpus sa ocekivanim nalazima

Najvazniji tuning dataset.

Za svaki primer:

- nacrt;
- relevantni corpus dokumenti;
- ocekivani tip konflikta;
- citat iz nacrta;
- citat iz korpusa;
- slot diff;
- nivo rizika;
- objasnjenje zasto jeste konflikt;
- negativni primeri koji lice, ali nisu konflikt.

Prvi comprehensive set treba da pokrije svaku kategoriju iz
`MASTER_CONFLICT_TAXONOMY.md`.

Minimum po kategoriji:

- 10 pozitivnih primera;
- 10 negativnih ili "lookalike" primera;
- 3 primera sa nepotpunim podacima koji treba da zavrse kao
  `needs_expert_review` ili `not_evaluated_missing_slot`.

Za finding type-ove koji su visokog rizika, kao nadleznost, pravni osnov,
sankcije, rokovi, pravni lekovi i EU alignment, cilj treba da bude najmanje 20
pozitivnih i 20 negativnih primera po tipu.

### 4. Ontology seed podaci

Potrebno za svaku oblast:

- institucije;
- inspekcije;
- nadleznosti;
- sinonimi;
- skracenice;
- akteri i klase aktera;
- radnje;
- objekti regulisanja;
- hijerarhije: siri/uzi pojam;
- zabranjene ili sumnjive kombinacije domena.

Primer za pogresnu nadleznost:

```yaml
institutions:
  construction_ministry:
    labels: ["ministarstvo gradjevine", "ministarstvo nadlezno za gradjevinu"]
    domains: ["construction"]
  agriculture_ministry:
    labels: ["ministarstvo poljoprivrede"]
    domains: ["food_safety", "agriculture"]
inspections:
  construction_inspection:
    labels: ["gradjevinska inspekcija"]
    domains: ["construction"]
  veterinary_inspection:
    labels: ["veterinarska inspekcija"]
    domains: ["food_safety"]
objects:
  food:
    labels: ["hrana", "namirnice"]
    expected_domains: ["food_safety"]
```

### 5. Procesni dokumenti

Za procedure module:

- primer RIA/AEP izvestaja;
- program javne rasprave;
- izvestaj o javnoj raspravi;
- misljenja RSZ;
- misljenja Ministarstva finansija;
- misljenja MEI;
- izjave o uskladjenosti;
- tabele uskladjenosti;
- zakljucci odbora Vlade;
- skupstinski materijali.

Za svaki artifact treba oznaciti:

- tip dokumenta;
- instituciju izdavaoca;
- datum;
- status: positive, negative, conditional, missing, unclear;
- otvorene primedbe;
- na koje clanove se primedbe odnose.

### 6. EU alignment podaci

Potrebno:

- popunjene tabele uskladjenosti;
- prazni obrasci;
- EU akti sa CELEX oznakama;
- parovi EU odredba - domaca odredba;
- status: potpuno/delimicno/neuskladjeno/neprenosivo;
- razlozi za delimicnu uskladjenost;
- planirani rok potpune uskladjenosti.

Ovo je poseban dataset, jer je tabela polustrukturisan dokument, a ne obican
pravni tekst.

### 7. Human feedback iz aplikacije

Svaka odluka pravnika treba da se cuva kao tuning signal:

- accepted;
- rejected;
- partial;
- needs_expert_review;
- komentar pravnika;
- ispravan tip konflikta ako je sistem promasio;
- ispravni slotovi ako je extraction promasio;
- nedostajuci sinonim ili pravilo.

Ovo ne treba automatski da menja pravila. Treba da puni queue za pregled i da
ulazi u evaluation dataset posle validacije.

### 8. Negativni primeri

Bez negativnih primera sistem ce imati mnogo false positive nalaza.

Potrebno:

- nacrt sa istim rokom kao zakon;
- nacrt sa razlicitim rokom, ali posebnim pravnim osnovom;
- nacrt sa drugim organom koji je stvarno nadlezan po posebnom propisu;
- tekst koji pominje hranu i gradjevinu, ali ne propisuje nadleznost;
- javna rasprava koja nije obavezna zbog izuzetka;
- EU tabela koja nema red jer EU akt nije relevantan.

## Kada Ima Smisla Fine-Tuning LLM-a

Ne odmah.

Prvo treba skupiti:

- najmanje 500-1000 validiranih assertion extraction primera;
- najmanje 300-500 validiranih konflikt parova;
- najmanje 100 procesnih artefakata sa oznacenim poljima;
- stabilnu ontologiju i rule pack.

Pre fine-tuning-a treba probati:

- bolji prompt;
- few-shot primere;
- schema validation;
- ontology-assisted extraction;
- reranking;
- human correction loop.

Fine-tuning ima smisla tek ako LLM stalno gresi u istim obrascima koje prompt i
ontologija ne popravljaju.

## Comprehensive Engine Scope

Conflict engine mora da obuhvati kompletan katalog iz
`MASTER_CONFLICT_TAXONOMY.md`. Implementacija moze biti fazna, ali scope nije
fazan: od prvog uvodjenja engine-a svi finding type-ovi moraju postojati u
registry-ju, imati GUI label, report label, evidence contract i makar jedan
evaluation placeholder.

Tri ranija primera ostaju samo smoke test:

- `authority_scope_conflict`: svaki gradjanin vs ovlasceno lice;
- `deadline_mismatch`: 15 dana vs 30 dana;
- `competence_conflict`: hranu kontrolise gradjevinska inspekcija.

Oni sluze da dokazemo da pipeline radi bez hard-coded checkera. Posle toga se
ne dodaju konflikti ad hoc, nego se popunjavaju rule family fajlovi iz cele
taksonomije.

## Redosled Implementacije

1. Dodati `ontology` modul i osnovne YAML fajlove.
2. Dodati `assertions` modele, store i rule-based extractor.
3. Integrisati assertion extraction u corpus import i draft review artefakte.
4. Dodati API i GUI prikaz assertiona.
5. Dodati conflict candidate retrieval.
6. Dodati `conflicts` engine, registry i rule family fajlove za celu
   taksonomiju.
7. Aktivirati auto rezim za rule-ove koji imaju dovoljno slotova i testova.
8. Zameniti hard-coded `CorpusAuthorityConflictChecker` generickim rule-om.
9. Dodati procedure module skeleton i proceduralni GUI tab.
10. Dodati evaluation harness za sve kategorije iz taksonomije.
11. Dodati feedback loop iz review odluka u evaluation queue.

## Definition of Done Za Comprehensive Conflict Engine v1

Prva verzija comprehensive engine-a je gotova kada:

- korisnik importuje korpus iz foldera;
- sistem iz korpusa prikaze tvrdnje;
- korisnik unese nacrt;
- sistem prikaze tvrdnje iz nacrta;
- sistem prikaze kandidate koji su poredjeni;
- engine ima registrovane sve finding type-ove iz
  `MASTER_CONFLICT_TAXONOMY.md`;
- sistem pronadje smoke konflikte bez posebnog Python checkera;
- za tipove koje ne moze automatski da oceni, sistem vrati trace razlog:
  `not_evaluated_missing_slot`, `not_evaluated_no_candidate`,
  `needs_expert_review_low_confidence` ili `not_applicable`;
- svaki nalaz ima citat iz nacrta, citat iz korpusa i slot diff;
- korisnik u GUI vidi da li je problem u extraction, ontology, candidate
  retrieval ili rule fazi;
- regression test moze da se pusti na cistoj bazi;
- novo pravilo ili sinonim moze da se doda u YAML i testira bez backend
  izmene.
