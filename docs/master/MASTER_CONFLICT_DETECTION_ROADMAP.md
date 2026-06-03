# MASTER_CONFLICT_DETECTION_ROADMAP

Ovaj dokument definise sta nedostaje u zAIkon stack-u da bi sistem mogao
robustno da otkriva nesaglasnosti nacrta sa postojecim zakonima, pravilnicima,
naredbama, strategijama i drugim aktima, bez dodavanja novog backend koda za
svaki pojedinacni primer.

Dokument je orijentisan na use case provere nacrta: korisnik unese nacrt,
izabere korpus, sistem pronalazi relevantne postojece norme, izdvaja tvrdnje iz
nacrta i korpusa, poredi ih, proizvodi citirane nalaze i omogucava pravniku da
prihvati, odbije ili dotera nalaz.

## Cilj

Sistem treba da predje sa pojedinacnih, usko kodiranih checkera na opsti sloj za
normativno razumevanje i poredjenje.

Minimalni cilj:

- nacrt i korpus se prevode u uporedive normativne tvrdnje;
- slicne tvrdnje se povezuju kroz reference, semanticku pretragu i pravni graf;
- genericki checkeri porede subjekte, radnje, objekte, rokove, uslove,
  izuzetke, nadleznosti, zabrane, dozvole, obaveze i vremensko vazenje;
- svaki nalaz ima citat iz nacrta, citat iz korpusa, tip konflikta, nivo rizika,
  objasnjenje, preporuku i confidence;
- nova pravila se pretezno dodaju kroz konfiguraciju, ontologiju, prompt
  sablone i evaluacione primere, a ne kroz ad hoc Python klase.

## Trenutno stanje

Postojeci stack vec ima korisne osnove:

- import lokalnih PDF, DOCX i TXT dokumenata;
- normalizaciju srpske cirilice u latinicu za internu obradu;
- parser pravne strukture;
- canonical JSON kao runtime model;
- Akoma Ntoso export kao interoperabilni format;
- ekstrakciju i razresavanje referenci;
- keyword/vector/structure/reference indexing;
- draft review pipeline;
- nalaze, odluke pravnika i izvestaje;
- GUI koji prikazuje tok obrade i artefakte po fazama.

Najveca trenutna rupa je sto checkeri uglavnom rade na povrsinskim signalima u
tekstu. Primer konflikta oko obelezavanja drveca je implementiran kao usko
kodirana logika: zna za konkretnu radnju, konkretan tip subjekta i konkretan
obrazac. To je korisno kao dokaz koncepta, ali nije skalabilan model.

## Procesni Workflow Koji Takodje Treba Podrzati

Otkrivanje nesaglasnosti ne sme biti ograniceno samo na poredjenje clanova.
Pravni workflow pripreme zakona ima procesne kapije, uloge i pratece artefakte.
Ako sistem zeli da podrzi realan rad ministarstva ili pravnog tima, mora da zna
gde se nacrt nalazi u proceduri i koje provere jos nedostaju.

Inicijalni workflow koji treba modelovati:

1. `drafting_and_ria`
   - resorno ministarstvo formira radnu grupu;
   - izradjuje se nacrt;
   - priprema se analiza efekata propisa, ako je primenljiva.
2. `public_consultation`
   - nacrt se objavljuje za javni uvid;
   - prikupljaju se primedbe i predlozi;
   - prati se minimalno trajanje javne rasprave i izvestaj o sprovedenoj
     raspravi.
3. `official_opinions`
   - Republicki sekretarijat za zakonodavstvo proverava ustavnost, pravni
     sistem i pravno-tehnicku redakciju;
   - Ministarstvo finansija proverava fiskalne efekte i budzetsku odrzivost;
   - Ministarstvo za evropske integracije proverava uskladjenost sa pravom EU.
4. `eu_alignment_package`
   - izjava o uskladjenosti;
   - tabela uskladjenosti po odredbama domaceg propisa i relevantnih EU akata;
   - misljenje MEI i otvorene primedbe.
5. `government_committees`
   - nadlezni odbori Vlade razmatraju tekst i pratece materijale;
   - evidentira se da li postoje uslovi za sednicu Vlade.
6. `government_adoption`
   - Vlada utvrdjuje tekst kao Predlog zakona.
7. `parliamentary_review`
   - Narodna skupstina prima Predlog zakona;
   - nadlezni odbori ponovo proveravaju ustavnost, zakonodavni kvalitet i EU
     uskladjenost;
   - tekst ide u plenarnu raspravu i glasanje.

Ovaj proces ne treba hardkodovati kao vecnu istinu. Rokovi, obavezni organi,
izuzeci i prateci dokumenti moraju biti verzionisani i vezani za vazeci izvor
pravila, jer se poslovnici, metodologije i institucionalna praksa mogu menjati.

## Sta Fali

### 1. Normativni model tvrdnji

CanonicalDocument trenutno cuva pravnu strukturu i tekst, ali ne cuva masinski
uporedive normativne tvrdnje. Bez toga sistem ne zna da su sledece recenice
uporedive:

- "Obelezavanje stabala vrsi ovlasceno pravno lice."
- "Obelezavanje drveca moze da radi svaki gradjanin."

Potrebno je uvesti entitet `NormativeAssertion`:

```json
{
  "assertion_id": "uuid",
  "document_id": "uuid",
  "document_version_id": "uuid",
  "legal_unit_id": "uuid",
  "source_path": "article:2/paragraph:1",
  "assertion_type": "obligation | prohibition | permission | competence | definition | deadline | sanction | exception | repeal | condition",
  "modality": "must | must_not | may | is_authorized | is_defined_as | ceases_to_apply",
  "actor": {
    "raw": "ovlasceno pravno lice",
    "canonical": "authorized_legal_entity",
    "actor_class": "authorized_entity",
    "specificity": 0.82
  },
  "action": {
    "raw": "obelezavanje drveca",
    "canonical": "mark_tree"
  },
  "object": {
    "raw": "drvece",
    "canonical": "tree"
  },
  "condition": {
    "raw": "pre sece",
    "canonical": "before_cutting"
  },
  "deadline": {
    "value": 30,
    "unit": "day",
    "start_event": "receipt_of_request",
    "end_event": "decision_issued"
  },
  "exception": {
    "raw": null,
    "canonical": null
  },
  "jurisdiction": "RS",
  "domain": "forestry",
  "valid_from": "date|null",
  "valid_to": "date|null",
  "source_quote": "Originalni citat",
  "confidence": 0.86,
  "extraction_method": "rules | llm | hybrid"
}
```

Ovaj model je srce sistema. Svi kasniji checkeri treba da porede ove tvrdnje,
a ne samo sirov tekst.

### 2. Ontologija i pravni recnik

Sistem mora znati da su "gradjanin", "fizicko lice", "svako lice",
"ovlasceno pravno lice", "strucna sluzba" i "nadlezni organ" razlicite klase
subjekata, i da jedna klasa moze biti sira ili uza od druge.

Potrebno je dodati `LegalOntology` kao konfigurabilni sloj:

- kanonski nazivi aktera: `citizen`, `natural_person`, `legal_entity`,
  `authorized_legal_entity`, `competent_authority`, `ministry`;
- hijerarhiju sirine: `any_person` > `natural_person` > `citizen`,
  `legal_entity` > `authorized_legal_entity`;
- sinonime i morfoloske varijante;
- kanonske radnje: `mark_tree`, `issue_decision`, `submit_request`,
  `perform_inspection`, `keep_registry`;
- kanonske objekte: `tree`, `forest_land`, `request`, `decision`,
  `permit`, `registry`;
- domenske recnike po oblasti: sumarstvo, rad, porezi, urbanizam, javne
  nabavke;
- mapiranje iz srpskog teksta u kanonske slotove;
- verzionisanje ontologije, jer promena recnika moze promeniti nalaze.

Ontologija treba da bude ucitavana iz YAML/JSON fajlova, ne iz Python koda.

### 3. Ekstrakcija slotova iz normi

Nedostaje pipeline korak koji iz pravnih jedinica izvlaci slotove:

- ko je subjekt;
- sta radi ili ne sme da radi;
- nad cim se radnja vrsi;
- pod kojim uslovima;
- u kom roku;
- od kog dogadjaja rok tece;
- koje telo je nadlezno;
- koji izuzetak menja pravilo;
- koja sankcija sledi;
- koji clan stavlja pravilo van snage.

Potrebni koraci:

1. `extract_normative_assertions`
2. `normalize_legal_slots`
3. `link_assertions_to_references`
4. `store_assertion_index`

Ekstrakcija treba da bude hibridna:

- regex i parseri za stabilne obrasce, kao rokove i reference;
- LLM extractor za slozenije recenice;
- validator koji proverava da LLM izlaz ima citat i legal_unit_id;
- confidence scoring po slotu, ne samo po celoj tvrdnji.

### 4. Genericki konflikt checkeri

Umesto checkera koji zna samo za "obelezavanje drveca", treba uvesti
konfigurabilan `ConflictEngine`. On prima tvrdnje iz nacrta, kandidat tvrdnje iz
korpusa i set pravila poredjenja.

Tipovi konflikata nisu ograniceni na nekoliko primera. Kompletan katalog je u
`MASTER_CONFLICT_TAXONOMY.md` i ukljucuje, izmedju ostalog:

- hijerarhiju i pravni osnov;
- nadleznost i institucije;
- aktere, adresate i opseg lica;
- modalitete obaveza, zabrana, dozvola i prava;
- radnju, predmet regulacije i materijalni opseg;
- rokove, vreme i vazenje;
- uslove, izuzetke i posebne rezime;
- definicije, terminologiju i klasifikacije;
- reference i upucivanja;
- finansije, takse, naknade i budzet;
- sankcije, mere i nadzor;
- postupak, prava stranaka i pravne lekove;
- podatke, registre, transparentnost i poverljivost;
- EU uskladjivanje;
- procesnu usaglasenost;
- unutrasnju konzistentnost nacrta.

Primeri `authority_scope_conflict`, `deadline_mismatch` i
`competence_conflict` sluze samo kao prvi regression primeri. Oni nisu scope
engine-a.

Za svaki tip konflikta treba definisati:

- ulazne slotove;
- prag slicnosti za action/object;
- pravilo prioriteta izvora;
- logicu konflikta;
- poruku za korisnika;
- preporuku;
- minimalni dokaz koji mora postojati.

### 5. Pravna hijerarhija i prioritet izvora

Da bi sistem znao sta je "nesaglasnost", mora znati odnos dokumenata:

- zakon ima vecu snagu od pravilnika;
- pravilnik ne sme prosiriti ovlascenje mimo zakona;
- strategija cesto nije direktno obavezujuca kao zakon;
- naredba moze biti vremenski i situaciono ogranicena;
- noviji akt ili posebni akt moze imati prednost u odredjenim okolnostima.

Potrebno je dodati `LegalSourcePriority`:

```json
{
  "document_type": "law",
  "rank": 100,
  "binding_force": "binding",
  "can_define_rights_and_obligations": true,
  "can_delegate_to_lower_act": true
}
```

I `ConflictContext`:

```json
{
  "draft_document_type": "rulebook",
  "corpus_document_type": "law",
  "relation": "lower_act_against_higher_act",
  "domain": "forestry",
  "conflict_policy": "strict"
}
```

Bez ovog sloja sistem moze naci razliku, ali ne zna da li je razlika pravno
problematicna.

### 6. Verzije, vazenje i precisceni tekst

Za ozbiljno otkrivanje nesaglasnosti nije dovoljno znati da tekst postoji u
korpusu. Treba znati da li je vazece pravo.

Nedostaje:

- ekstrakcija datuma objave;
- `effective_from`, `valid_from`, `valid_to`;
- prepoznavanje izmena i dopuna;
- povezivanje izmenjenog clana sa osnovnim aktom;
- preciscena verzija dokumenta;
- detekcija odredbi koje prestaju da vaze;
- prioritet novijeg i posebnog propisa.

Bez toga sistem ce proizvoditi lazne nalaze protiv nevazece ili zastarele
odredbe.

### 7. Bolja identifikacija dokumenata

Korisnik je vec naglasio da se ne treba oslanjati na filename. To je kljucno za
ovaj use case.

Potrebno je iz teksta dokumenta izvuci:

- naslov;
- tip akta;
- donosilac;
- pravni osnov;
- sluzbeni glasnik;
- datum objave;
- datum stupanja na snagu;
- oblast;
- vezu sa osnovnim aktom ako je dokument izmena/dopuna;
- nivo pravne snage.

Ovo treba da postane poseban artefakt `document_metadata_extraction`, sa
confidence vrednostima i upozorenjima.

### 8. Candidate generation za poredjenje

Nije realno porediti svaku tvrdnju iz nacrta sa svakom tvrdnjom iz korpusa.
Treba generisati kandidate:

- direktno preko reference iz nacrta;
- preko istog action/object slot para;
- preko istog kanonskog termina;
- preko pravnog grafa;
- preko semanticke slicnosti citata;
- preko domenskog recnika;
- preko istog clana zakona ako je navedeno u nacrtu.

Potrebno je dodati `retrieve_conflict_candidates`, poseban od opste pretrage.
Opsta hybrid search je korisna, ali konflikt detekcija treba strukturisan,
obrazlozen candidate set.

### 9. Evidence model bogatiji od jednog JSON polja

Nalaz trenutno moze da sadrzi evidence kao fleksibilni JSON. Za ozbiljan rad
treba standardizovati dokaz:

```json
{
  "finding_id": "uuid",
  "draft_assertion_id": "uuid",
  "corpus_assertion_id": "uuid",
  "draft_quote": "...",
  "corpus_quote": "...",
  "draft_path": "article:1/paragraph:1",
  "corpus_path": "article:45/paragraph:3",
  "slot_diffs": [
    {
      "slot": "actor",
      "draft_value": "citizen",
      "corpus_value": "authorized_legal_entity",
      "relation": "broader_than_allowed"
    }
  ],
  "retrieval_trace": {
    "method": "reference+semantic",
    "scores": {}
  },
  "confidence": 0.82
}
```

GUI onda moze tacno da prikaze koja faza nije dobro radila: ekstrakcija,
normalizacija slotova, retrieval kandidata, conflict rule ili generisanje
objasnjenja.

### 10. Rule pack i DSL

Da se ne bi backend menjao za svaki novi primer, pravila treba pomeriti u
konfiguraciju.

Primer YAML pravila:

```yaml
id: deadline_mismatch_default
finding_type: deadline_mismatch
enabled: true
applies_when:
  assertion_type: deadline
  same_action: true
  same_object: true
compare:
  slot: deadline.value
  operator: not_equal
  normalize_units: true
risk:
  default: high
message:
  title: "Rok u nacrtu nije usaglasen sa vazecim propisom"
  explanation_template: >
    Nacrt propisuje rok od {draft.deadline.value} {draft.deadline.unit},
    dok relevantna odredba iz korpusa propisuje
    {corpus.deadline.value} {corpus.deadline.unit}.
  recommendation_template: >
    Proveriti da li nacrt ima poseban pravni osnov za izmenu roka; ako nema,
    uskladiti rok sa relevantnim propisom.
evidence_required:
  - draft_quote
  - corpus_quote
  - slot_diffs
```

Backend treba da ucita rule pack i izvrsava genericke operatore. Novi primer se
onda dodaje kao pravilo, sinonim ili evaluacioni case, a ne kao nova klasa.

### 11. LLM kao extractor i objasnjivac, ne kao sudija

LLM treba koristiti za:

- predlaganje normativnih tvrdnji iz slozenih recenica;
- mapiranje teksta u slotove;
- prepoznavanje parafraza;
- generisanje razumljivog objasnjenja nalaza;
- predlog izmene nacrta.

LLM ne treba da bude jedini izvor odluke da konflikt postoji.

Svaki LLM izlaz mora imati:

- JSON schema validation;
- citat iz pravne jedinice;
- legal_unit_id;
- confidence;
- oznaku `needs_expert_review` ako su slotovi nesigurni;
- replay artefakt prompta i odgovora, bez tajnih vrednosti.

### 12. Evaluacioni skup i regression harness

Da se sistem ne vraca na backend razvoj za svaki primer, treba uvesti zlatni set
test primera:

- input nacrt;
- izabrani korpus;
- ocekivani nalazi;
- ocekivani tip konflikta;
- citat iz nacrta;
- citat iz korpusa;
- minimalni slot diff;
- prihvatljiv false positive/false negative prag.

Primeri koji moraju biti u setu:

- ovlasceno lice vs svaki gradjanin;
- 15 dana vs 30 dana;
- ministarstvo vs nadlezni organ;
- dozvoljeno vs zabranjeno;
- izuzetak uveden bez osnova;
- definicija istog termina sa drugim znacenjem;
- upucivanje na nevazeci clan;
- podzakonski akt propisuje novu obavezu bez zakonskog osnova.

Ovaj set treba da se pokrece kroz `pytest` i kroz E2E UI test. Svaka promena
promptova, ontologije, parsiranja ili rule packa mora pokazati sta se promenilo
u nalazima.

### 13. Procedural compliance model

Za realan zakonodavni workflow treba dodati poseban model za procesnu proveru.
Ovo je odvojeno od normativnih konflikata, ali mora biti vidljivo u istom UI
lancu obrade.

Predlozeni entitet `ProcedureCase`:

```json
{
  "procedure_case_id": "uuid",
  "draft_review_id": "uuid",
  "draft_title": "Nacrt zakona o ...",
  "proposer": "Ministarstvo ...",
  "procedure_type": "government_bill | parliamentary_bill | regulation | rulebook",
  "current_stage": "official_opinions",
  "domain": "forestry",
  "eu_relevance": "yes | no | unknown",
  "budget_impact": "yes | no | unknown",
  "status": "in_progress",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

Predlozeni entitet `ProcessArtifact`:

```json
{
  "artifact_id": "uuid",
  "procedure_case_id": "uuid",
  "artifact_type": "ria | public_debate_program | public_debate_report | rsz_opinion | finance_opinion | mei_opinion | eu_alignment_statement | eu_alignment_table | committee_conclusion",
  "source_uri": "file:///...",
  "title": "Misljenje Ministarstva finansija",
  "issuer": "Ministarstvo finansija",
  "issued_at": "date|null",
  "status": "missing | submitted | positive | negative | conditional | not_required",
  "content_text": "Extracted text",
  "metadata": {},
  "confidence": 0.9
}
```

Za `eu_alignment_statement` treba parsirati najmanje sledeca polja:

- organ drzavne uprave ili drugi ovlasceni predlagac;
- naziv propisa;
- veza sa SSP/Prelaznim sporazumom ili drugim relevantnim izvorom;
- stepen uskladjenosti sa primarnim, sekundarnim i ostalim izvorima prava EU;
- razlozi za delimicnu uskladjenost ili neusklađenost;
- rok za postizanje potpune uskladjenosti;
- informacija da li postoje relevantni EU propisi;
- informacija o prevodima i konsultantima.

Predlozeni entitet `ProcessRequirement`:

```json
{
  "requirement_id": "uuid",
  "procedure_type": "government_bill",
  "stage": "official_opinions",
  "required_artifact_type": "rsz_opinion",
  "required_when": {
    "document_type": "law",
    "proposer_type": "government"
  },
  "source_reference": {
    "title": "Poslovnik Vlade",
    "article": "to_validate",
    "url": "to_validate"
  },
  "valid_from": "date|null",
  "valid_to": "date|null",
  "severity_if_missing": "high"
}
```

Predlozeni entitet `InstitutionalOpinion`:

```json
{
  "opinion_id": "uuid",
  "procedure_case_id": "uuid",
  "institution": "RSZ | MF | MEI | government_committee | parliament_committee",
  "opinion_status": "positive | negative | conditional | missing | unclear",
  "summary": "Kratak sazetak misljenja",
  "open_remarks": [
    {
      "remark_id": "uuid",
      "target_path": "article:4/paragraph:2",
      "remark_type": "legal_technical | fiscal | eu_alignment | constitutional | procedural",
      "content_text": "Primedba",
      "resolved": false
    }
  ],
  "source_artifact_id": "uuid"
}
```

Ovaj sloj omogucava nalaze kao:

- nedostaje analiza efekata propisa;
- javna rasprava nije evidentirana ili traje krace od propisanog minimuma;
- nema izvestaja o javnoj raspravi;
- nema misljenja RSZ;
- misljenje Ministarstva finansija je uslovno ili negativno;
- nacrt ima fiskalni efekat, ali nema finansijsko obrazlozenje;
- nacrt dira EU materiju, ali nema izjavu ili tabelu uskladjenosti;
- tabela uskladjenosti ne pokriva clan koji uvodi novu obavezu;
- primedba MEI/RSZ nije razresena u novoj verziji nacrta;
- Vlada ne bi trebalo da utvrdi predlog dok postoje blokirajuce procesne
  primedbe.

### 14. Process rule pack

Kao i konfliktna pravila, procesna pravila treba da budu konfiguracija.

Primer:

```yaml
id: government_bill_requires_rsz_opinion
finding_type: missing_process_artifact
enabled: true
applies_when:
  procedure_type: government_bill
  document_type: law
stage: official_opinions
requires:
  artifact_type: rsz_opinion
risk:
  default: high
message:
  title: "Nedostaje misljenje Republickog sekretarijata za zakonodavstvo"
  explanation_template: >
    Pre utvrdjivanja Predloga zakona potrebno je evidentirati misljenje
    Republickog sekretarijata za zakonodavstvo ili oznaciti pravni osnov zbog
    koga ono nije potrebno.
  recommendation_template: >
    Pribaviti misljenje RSZ, povezati ga sa predmetom i razresiti eventualne
    otvorene primedbe.
evidence_required:
  - procedure_case
  - required_artifact_type
  - source_reference
```

Primer za javnu raspravu:

```yaml
id: public_consultation_minimum_duration
finding_type: procedural_deadline_issue
enabled: true
applies_when:
  stage: public_consultation
compare:
  observed_duration_days: ">= configured_minimum_days"
configured_values:
  minimum_days:
    value: 20
    source_reference: "to_validate_against_current_rules"
risk:
  default: medium
```

Vazno: vrednost `20` ne sme biti magic number u kodu. Treba da dodje iz
verzionisanog process rule packa sa izvorom i periodom vazenja.

### 15. EU alignment support

Za MEI workflow nije dovoljno proveriti da postoji dokument. Potrebno je
modelovati odnos domacih odredaba i EU izvora.

Predlozeni entitet `AlignmentMatrixRow`:

```json
{
  "row_id": "uuid",
  "procedure_case_id": "uuid",
  "domestic_legal_unit_id": "uuid",
  "domestic_path": "article:5",
  "eu_source_title": "Directive ...",
  "eu_source_article": "Article 7",
  "alignment_status": "fully_aligned | partially_aligned | not_aligned | not_applicable | unclear",
  "comment": "Obrazlozenje",
  "source_artifact_id": "uuid"
}
```

Potrebni checkeri:

- domaci clan nema red u tabeli uskladjenosti;
- red u tabeli nema validan EU izvor;
- tabela nema CELEX oznaku kada se poziva na sekundarni izvor EU;
- red ne mapira EU clan/stav/tacku na domaci clan/stav/tacku;
- status uskladjenosti je `partially_aligned` ili `not_aligned`, ali nema
  obrazlozenja;
- red oznacen kao `not_transposable` nema obrazlozenje;
- predvidjeni datum potpune uskladjenosti nedostaje kada status nije potpuno
  uskladjen;
- tekst nacrta je promenjen posle misljenja MEI, ali tabela nije osvezena;
- MEI misljenje ima otvorene primedbe koje nisu vezane za nalaze ili izmene.

Parser tabele uskladjenosti treba da podrzi standardnu logiku redova:

- izvor EU: naziv akta, CELEX, clan/stav/podstav/tacka/aneks;
- domaci propis: clan/stav/tacka i sadrzina domace odredbe;
- status: potpuno uskladjeno, delimicno uskladjeno, neusklađeno,
  neprenosivo;
- razlog za delimicnu uskladjenost, neusklađenost ili neprenosivost;
- predvidjeni datum potpune uskladjenosti;
- napomena.

Ovo je poseban `AlignmentMatrixRow` extractor, ne obican document parser.

## Predlozene Pipeline Promene

### Corpus import

Dodati korake posle `convert_to_canonical_json`:

1. `extract_document_metadata`
2. `extract_normative_assertions`
3. `normalize_legal_slots`
4. `link_assertions_to_references`
5. `build_assertion_index`
6. `build_ontology_links`

### Draft review

Dodati korake posle `retrieve_relevant_law`:

1. `extract_draft_assertions`
2. `normalize_draft_slots`
3. `retrieve_conflict_candidates`
4. `run_conflict_engine`
5. `rank_and_group_findings`
6. `generate_cited_explanations`

Pipeline trace u GUI treba da prikaze svaki od ovih outputa posebno.

### Procedure compliance review

Dodati poseban lanac koji moze da se pokrene samostalno ili kao deo draft
review-a:

1. `create_procedure_case`
2. `classify_procedure_type`
3. `collect_process_artifacts`
4. `extract_process_metadata`
5. `extract_institutional_opinions`
6. `extract_eu_alignment_matrix`
7. `load_process_rule_pack`
8. `run_process_compliance_rules`
9. `link_process_findings_to_draft_units`
10. `generate_process_readiness_report`

Ovaj lanac treba da odgovori na pitanje: "Da li je predmet spreman za sledecu
proceduralnu kapiju?"

## Predlozeni Moduli

### `ontology`

Odgovoran za:

- ucitavanje pravnog recnika;
- sinonime;
- hijerarhiju aktera;
- kanonske radnje i objekte;
- domenske profile;
- verzionisanje recnika.

### `assertions`

Odgovoran za:

- ekstrakciju normativnih tvrdnji;
- validaciju LLM/rule izlaza;
- normalizaciju slotova;
- skladištenje assertion indeksa.

### `conflicts`

Odgovoran za:

- generisanje kandidata za poredjenje;
- rule pack loader;
- DSL operatore;
- konflikt engine;
- evidence builder;
- risk scoring.

### `evaluation`

Odgovoran za:

- gold test cases;
- regression report;
- merenje precision/recall po tipu konflikta;
- diff izmedju dve verzije rule packa, ontologije ili promptova.

### `procedure`

Odgovoran za:

- model predmeta kroz faze pripreme zakona;
- pratece procesne artefakte;
- zvanicna misljenja;
- javnu raspravu;
- RIA status;
- EU alignment paket;
- process rule pack;
- readiness report za sledecu fazu.

## Minimalni Backend API Dodaci

Da GUI moze da sluzi za tjuning bez stalnog debugovanja fajlova, potrebni su
endpointi:

- `GET /api/v1/ontology`
- `POST /api/v1/ontology/reload`
- `GET /api/v1/assertions?document_id=...`
- `GET /api/v1/draft-reviews/{id}/assertions`
- `GET /api/v1/draft-reviews/{id}/conflict-candidates`
- `GET /api/v1/draft-reviews/{id}/conflict-trace`
- `GET /api/v1/conflicts/types`
- `GET /api/v1/conflicts/types/{finding_type}`
- `POST /api/v1/evaluation/run`
- `GET /api/v1/evaluation/runs/{id}`
- `POST /api/v1/procedure-cases`
- `GET /api/v1/procedure-cases/{id}`
- `POST /api/v1/procedure-cases/{id}/artifacts`
- `POST /api/v1/procedure-cases/{id}/run`
- `GET /api/v1/procedure-cases/{id}/readiness-report`
- `GET /api/v1/procedure-rules`

Ovi endpointi nisu novi user workflow, nego instrumentacija da se vidi zasto je
sistem nesto nasao ili propustio.

## GUI Tjuning Ekrani

Postojeci GUI vec ima osnovni tok. Za ovaj use case treba dodati:

- ekran ili tab "Procedura" sa fazama: nacrt/RIA, javna rasprava, misljenja,
  EU paket, odbori Vlade, sednica Vlade, Skupstina;
- checklist potrebnih artefakata po fazi;
- status misljenja RSZ, Ministarstva finansija i MEI;
- prikaz otvorenih primedaba po instituciji;
- gate readiness indikator: "spremno", "blokirano", "nedostaje dokument",
  "potrebna ekspertska odluka";
- tab "Tvrdnje" za svaki dokument i nacrt;
- slot diff prikaz: actor/action/object/deadline/condition/exception;
- candidate list pre svakog nalaza;
- prikaz zasto je kandidat odbacen;
- filter nalaza po tipu konflikta i confidence;
- oznaku faze koja je verovatno kriva: extraction, normalization, retrieval,
  rule, explanation;
- evaluacioni ekran sa gold primerima i rezultatima.

Korisniku mora biti jasno da li sistem nije nasao konflikt zato sto:

- nije izvukao tekst;
- nije parsirao clan;
- nije izvukao normativnu tvrdnju;
- nije prepoznao sinonim;
- nije pronasao relevantan zakon;
- rule pack nema pravilo;
- confidence je bio prenizak.

## Prioriteti Implementacije

### Faza 1: Osnova za genericke konflikte

- Dodati `NormativeAssertion` model.
- Dodati ekstrakciju rokova, aktera, radnji i objekata.
- Dodati YAML ontology za osnovne aktere i radnje.
- Dodati assertion artifacts u corpus import i draft review.
- Dodati `conflict_type_registry` za sve tipove iz
  `MASTER_CONFLICT_TAXONOMY.md`.
- Dodati rule family fajlove za sve kategorije, makar deo pravila u pocetku
  radio u `needs_expert_review` rezimu.
- Dodati evidence slot diff.

Ova faza treba da dokaze da engine nije ogranicen na hard-coded primere:
prethodni primeri su samo smoke testovi za pipeline.

### Faza 2: Proceduralni skeleton

- Dodati `ProcedureCase`, `ProcessArtifact`, `InstitutionalOpinion` i
  `ProcessRequirement`.
- Dodati procesni rule pack za osnovne kapije.
- Dodati GUI tab "Procedura".
- Dodati nalaze za nedostajuce procesne artefakte.
- Dodati rucni unos/status za misljenja i javnu raspravu, dok automatska
  ekstrakcija ne sazri.

Ova faza odmah donosi vrednost: korisnik vidi ne samo da li je tekst nacrta
sporan, nego i da li predmet moze dalje u proceduru.

### Faza 3: Rule pack engine

- Uvesti rule DSL.
- Prebaciti postojece checkere gde ima smisla u rule pack.
- Dodati konfigurabilne risk i message template-e.
- Dodati hot reload rule packa u dev modu.
- Dodati GUI debug prikaz primenjenih pravila.

### Faza 4: Verzije i pravna snaga

- Ekstrakcija Sluzbenog glasnika i datuma.
- Model vazenja dokumenata.
- Veza izmene/dopune sa osnovnim aktom.
- Hijerarhija pravne snage po tipu akta.
- Conflict policy za zakon/pravilnik/naredbu/strategiju.

### Faza 5: LLM-assisted extraction

- Schema-bound LLM extractor za normativne tvrdnje.
- Prompt verzionisanje.
- Replay artefakti.
- Human correction loop za assertion slotove.
- Ucenje iz prihvacenih/odbijenih nalaza kao evaluacioni input, ne kao
  automatska promena prava.

### Faza 6: EU alignment automation

- Import i parsiranje tabela uskladjenosti.
- Veza domaci clan - EU clan.
- Promena nacrta posle MEI misljenja kao trigger za ponovno uskladjivanje.
- Nalazi za nepokrivene clanove i otvorene MEI primedbe.

### Faza 7: Evaluaciona disciplina

- Gold suite za svaku oblast.
- Precision/recall report po tipu konflikta.
- E2E test koji prolazi kroz import, proveru nacrta, nalaze, odluke i izvestaj.
- Regression diff za promene u parseru, ontologiji, rule packu i promptovima.

## Tehnicki Principi

- Canonical JSON ostaje runtime model; Akoma Ntoso ostaje import/export i
  interoperabilnost.
- Interni tekst i indeksi ostaju normalizovana srpska latinica.
- LLM nikada ne proizvodi necitiran konacan zakljucak.
- Svaki nalaz mora imati najmanje jedan citat iz nacrta i jedan citat iz
  korpusa, osim cisto internih drafting nalaza.
- Svaki konflikt mora imati strukturisan `slot_diff`.
- Pravila, recnici i promptovi moraju biti verzionisani.
- Nova oblast prava se dodaje prvo kroz ontology/rule/evaluation pack, tek onda
  kroz backend kod ako genericki engine nije dovoljan.

## Definicija Zavrsenosti

Use case se smatra podrzanim kada za novi primer korisnik moze da uradi sledece
bez programerske intervencije:

1. ubaci dokumente u korpus;
2. pokrene extraction trace;
3. vidi tvrdnje izvucene iz korpusa;
4. unese nacrt;
5. vidi tvrdnje izvucene iz nacrta;
6. vidi kandidate koji su poredjeni;
7. dobije nalaz sa citatima i slot diffom;
8. ako nalaza nema, vidi u kojoj fazi je lanac zakazao;
9. doda sinonim ili rule pack izmenu;
10. ponovo pokrene isti evaluation case i vidi promenu rezultata.
11. vidi procesni status predmeta;
12. vidi da li nedostaju RIA, javna rasprava, misljenja ili EU dokumenti;
13. vidi koje institucionalne primedbe nisu razresene;
14. dobije readiness report za sledecu fazu procedure.

Tek tada sistem prestaje da zavisi od toga da se za svaki novi primer dodaje
novi backend checker.

## Inicijalni Izvori Koje Treba Verzionisati

Ovo nisu runtime dependency linkovi, nego polazne tacke koje treba pretvoriti u
verzionisane process rule pack izvore:

- Poslovnik Vlade Republike Srbije, za faze rada Vlade, pribavljanje misljenja
  i javnu raspravu:
  https://www.gs.gov.rs/extfile/sr/1261/Poslovnik%20Vlade.pdf
- Smernice i metodologija za analizu efekata propisa, za RIA obaveze i pragove.
  Pocetna tacka:
  https://rsjp.gov.rs/sr/vesti/uredba-o-metodologiji-izrade-dokumenata-javnih-politika-i-uredba-o-sprovodjenju-analize-efekata-propisa/
- Pravila i obrasci Ministarstva za evropske integracije, za izjavu o
  uskladjenosti i tabelu uskladjenosti:
  https://www.mei.gov.rs/srl/dokumenta/nacionalna-dokumenta/instrumenti-za-uskladjivanje-propisa/
- Zakljucak o usvajanju obrazaca i metodoloskih uputstava za popunjavanje
  instrumenata za uskladjivanje propisa Republike Srbije sa propisima Evropske
  unije, "Sl. glasnik RS", br. 34/2010. Sekundarni mirror koji je koristan za
  strukturu polja i istorijski kontekst; aktuelnost uvek proveriti prema
  vazecim MEI/PIS izvorima:
  http://demo.paragraf.rs/demo/combined/Old/t/t2010_05/t05_0348.htm
- Poslovnik Narodne skupstine i pravila odbora, za skupstinsku fazu.
  Pocetna tacka za workflow:
  https://www.parlament.gov.rs/akti/put-zakona.1053.html

Tokom implementacije svaka konkretna vrednost, kao minimalno trajanje javne
rasprave ili obaveznost odredjenog misljenja, mora imati `source_reference`,
`valid_from`, `valid_to` i status validacije.
