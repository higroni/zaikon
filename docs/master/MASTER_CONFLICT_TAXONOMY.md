# MASTER_CONFLICT_TAXONOMY

Ovaj dokument je katalog tipova nesaglasnosti koje zAIkon conflict engine mora
da podrzi. Katalog nije ogranicen na primere koje je korisnik naveo. Primeri
kao "svaki gradjanin vs ovlasceno lice", "15 dana vs 30 dana" i "kontrolu hrane
vrsi gradjevinska inspekcija" sluze samo kao rani regression primeri.

Svaki tip konflikta iz ovog dokumenta treba da postoji u engine-u kao rule
definition ili kao rule family. Neki tipovi mogu u prvoj verziji da rade sa
statusom `needs_expert_review` ako nedostaje dovoljno podataka, ali moraju biti
modelovani u engine-u, evidence modelu i GUI trace-u.

## Engine Principi

Svaki konflikt mora imati:

- `finding_type`;
- `rule_id`;
- `rule_version`;
- draft assertion;
- corpus assertion ili procedural requirement;
- citat iz nacrta;
- citat iz korpusa/procesnog izvora, osim za interne drafting nalaze;
- `slot_diffs`;
- confidence;
- oznaku da li je nalaz automatski, heuristicki ili zahteva eksperta.

Rule engine mora da podrzi tri rezima:

- `blocking`: konflikt je dovoljno jasan i sprecava sledecu fazu bez eksperta;
- `warning`: postoji rizik, ali treba pravna potvrda;
- `needs_expert_review`: engine zna kategoriju problema, ali nema dovoljno
  dokaza za automatsku ocenu.

## Slotovi Koje Engine Mora Da Razume

Minimalni slotovi:

- `source_rank`
- `document_type`
- `validity`
- `actor`
- `actor_domain`
- `competence`
- `action`
- `object`
- `object_domain`
- `modality`
- `right_holder`
- `obligation_bearer`
- `condition`
- `exception`
- `deadline`
- `deadline_start_event`
- `deadline_end_event`
- `calendar_type`
- `territorial_scope`
- `personal_scope`
- `material_scope`
- `amount`
- `sanction`
- `procedure_stage`
- `required_artifact`
- `institutional_opinion`
- `eu_source`
- `alignment_status`
- `reference_target`

## A. Hijerarhija I Pravni Osnov

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `source_hierarchy_conflict` | Nizi akt uredjuje suprotno visem aktu. | Pravilnik daje pravo koje zakon izricito ne dozvoljava. | source_rank, modality, action, object |
| `ultra_vires_conflict` | Predlagac/donosilac uredjuje materiju za koju nema ovlascenje. | Ministar pravilnikom uvodi novu obavezu bez zakonskog ovlascenja. | actor, source_rank, competence, legal_basis |
| `delegation_missing` | Nacrt se oslanja na delegirano ovlascenje koje ne postoji. | "Ministar blize uredjuje..." bez clana zakona koji delegira. | competence, reference_target |
| `delegation_exceeded` | Podzakonski akt prelazi granice delegacije. | Zakon ovlascuje tehnicka pravila, pravilnik uvodi kazne. | legal_basis, action, sanction |
| `reserved_matter_conflict` | Materija se moze urediti samo zakonom, a uredjuje se nizim aktom. | Pravilnik ogranicava pravo gradjana. | source_rank, right, restriction |
| `lex_specialis_conflict` | Nacrt ignorise poseban propis koji ima prednost. | Opsti rok menja poseban rok iz posebnog zakona. | domain, source_priority, deadline |
| `lex_posterior_conflict` | Nacrt koristi zastarelu normu i ignorise kasniji akt. | Poziva se na staru verziju zakona. | valid_from, valid_to, reference_target |
| `constitutional_alignment_risk` | Odredba je potencijalno protiv ustavnog prava ili nacela. | Ogranicenje prava bez osnova/proporcionalnosti. | right, restriction, legal_basis |

## B. Nadleznost I Institucionalni Konflikti

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `competence_conflict` | Nadleznost je data pogresnom organu. | Kontrolu hrane vrsi inspekcija ministarstva gradjevine. | actor, actor_domain, object, object_domain |
| `wrong_inspection_authority` | Pogresna inspekcija obavlja nadzor. | Gradjevinska inspekcija kontrolise zdravstvenu ispravnost hrane. | actor, inspection_type, object_domain |
| `missing_competent_authority` | Propis stvara obavezu/proceduru bez nadleznog organa. | "Podnosi se zahtev" ali nije receno kome. | action, object, actor |
| `overlapping_competence_conflict` | Dva organa imaju istu nadleznost bez razgranicenja. | Dve inspekcije donose istu meru. | actors, action, condition |
| `competence_transfer_conflict` | Nadleznost se prenosi bez pravnog osnova. | Ministarstvo prenosi javno ovlascenje privatnom subjektu. | actor_from, actor_to, legal_basis |
| `local_vs_republic_competence_conflict` | Mesaju se republicka, pokrajinska i lokalna nadleznost. | Lokalni organ odlucuje o republickoj dozvoli. | jurisdiction, actor, object |
| `independent_body_competence_conflict` | Nacrt zadire u nadleznost nezavisnog tela. | Ministarstvo preuzima nadzor koji pripada nezavisnom organu. | actor, body_type, competence |
| `appeal_authority_conflict` | Zalba se upucuje pogresnom drugostepenom organu. | Zalba na inspekcijsko resenje ide organu koji nije nadlezan. | remedy, actor, procedure_stage |

## C. Akteri, Adresati I Opseg Lica

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `authority_scope_conflict` | Nacrt siri krug ovlascenih lica. | Svaki gradjanin moze da radi posao rezervisan za ovlasceno lice. | actor, action, object |
| `obligation_bearer_changed` | Obaveza se prebacuje na drugo lice. | Obavezu vodjenja evidencije ima gradjanin umesto operatora. | obligation_bearer, action |
| `right_holder_changed` | Pravo dobija ili gubi pogresna kategorija lica. | Pravo korisnika dobija lice koje zakon ne prepoznaje. | right_holder, right |
| `personal_scope_expanded` | Nacrt obuhvata siri krug lica od zakona. | Obaveza vazi za sve privredne subjekte, zakon samo za operatere. | personal_scope |
| `personal_scope_narrowed` | Nacrt suzava krug lica mimo zakona. | Izuzima kategoriju koju zakon ukljucuje. | personal_scope, exception |
| `protected_category_conflict` | Nacrt nepovoljno tretira zasticenu kategoriju. | Razlicito pravilo bez opravdanja. | actor_class, right, condition |
| `representative_authority_conflict` | Pogresno lice potpisuje, izjavljuje ili zastupa. | Izjavu daje lice bez ovlascenja. | actor, competence, artifact_type |

## D. Modaliteti: Obaveze, Zabrane, Dozvole I Prava

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `permission_vs_prohibition_conflict` | Nacrt dozvoljava ono sto corpus zabranjuje. | Dozvoljava se radnja koja je zabranjena zakonom. | modality, action, object |
| `obligation_vs_discretion_conflict` | Obavezna radnja postaje diskreciona. | Organ "moze" umesto "duzan je". | modality, actor, action |
| `discretion_vs_obligation_conflict` | Diskreciono ovlascenje postaje obaveza bez osnova. | Organ mora doneti meru koju zakon ostavlja kao mogucnost. | modality, actor, action |
| `right_removed_conflict` | Nacrt ukida ili suzava pravo priznato visim aktom. | Stranka nema pravo uvida ili zalbe. | right, right_holder |
| `prohibition_removed_conflict` | Nacrt izostavlja vazecu zabranu. | Zabrana prodaje pod uslovom nestaje u podzakonskom aktu. | modality, action |
| `new_obligation_without_basis` | Nacrt uvodi novu obavezu bez pravnog osnova. | Nova evidencija, prijava ili taksa bez zakonskog osnova. | modality, action, legal_basis |
| `conflicting_obligations` | Dve obaveze se ne mogu istovremeno ispuniti. | Jedna norma nalaze objavu, druga poverljivost istog podatka. | action, condition, object |
| `impossible_obligation` | Obaveza je objektivno neizvrsiva. | Rok pre dogadjaja od kog rok tece. | deadline, condition |

## E. Radnja, Predmet Regulacije I Materijalni Opseg

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `action_scope_mismatch` | Radnja nije ista kao u corpus odredbi. | Nadzor se zamenjuje izdavanjem dozvole. | action |
| `object_scope_expanded` | Nacrt siri predmet regulacije. | Pravilo za hranu siri se na sve proizvode. | object, material_scope |
| `object_scope_narrowed` | Nacrt suzava predmet regulacije. | Zakon obuhvata sve sume, nacrt samo privatne sume. | object, material_scope |
| `territorial_scope_conflict` | Teritorijalno vazenje nije uskladjeno. | Republika vs teritorija opstine. | territorial_scope |
| `domain_mismatch_conflict` | Odredba koristi pogresnu oblast za predmet. | Gradjevinska pravila za bezbednost hrane. | domain, object_domain |
| `threshold_mismatch` | Pragovi i uslovi kvantiteta se ne slazu. | 10 hektara vs 5 hektara. | amount, unit, condition |
| `category_classification_conflict` | Pogresna klasifikacija stvari, lica ili postupka. | Otpad klasifikovan kao proizvod. | object_class, definition |

## F. Rokovi, Vreme I Vaznost

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `deadline_mismatch` | Rok se razlikuje. | 15 dana vs 30 dana. | deadline.value, deadline.unit |
| `deadline_start_event_mismatch` | Rok tece od pogresnog dogadjaja. | Od prijema zahteva vs od dopune zahteva. | deadline_start_event |
| `deadline_end_event_mismatch` | Rok se odnosi na pogresan zavrsetak radnje. | Donosenje resenja vs dostavljanje resenja. | deadline_end_event |
| `calendar_type_mismatch` | Mesaju se kalendarski i radni dani. | 15 dana vs 15 radnih dana. | calendar_type |
| `deadline_missing` | Nacrt izostavlja rok koji corpus propisuje. | Organ odlucuje bez roka. | deadline |
| `deadline_added_without_basis` | Nacrt uvodi rok bez osnova ili suprotno corpus-u. | Novi prekluzivni rok za pravo stranke. | deadline, right |
| `retroactivity_conflict` | Nacrt ima nedozvoljeno povratno dejstvo. | Primena na okoncane postupke. | valid_from, condition |
| `effective_date_conflict` | Stupanje na snagu nije uskladjeno. | Prekratak vacatio legis bez razloga. | effective_from |
| `validity_period_conflict` | Period vazenja je pogresan ili izostavljen. | Naredba vazi neograniceno iako treba privremeno. | valid_to, document_type |
| `transitional_period_conflict` | Prelazni rezim nije uskladjen. | Stari postupci se prekidaju protivno zakonu. | transitional_rule |

## G. Uslovi, Izuzeci I Posebni Rezim

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `condition_added_conflict` | Nacrt dodaje uslov koji zakon ne predvidja. | Pravo zavisi od dodatne potvrde. | condition, right |
| `condition_removed_conflict` | Nacrt uklanja uslov iz zakona. | Dozvola bez zakonom trazenog ispunjenja uslova. | condition |
| `condition_mismatch` | Uslov je drugacije formulisan. | "Pre sece" vs "posle prijave". | condition |
| `exception_added_conflict` | Nacrt uvodi izuzetak bez osnova. | Od zabrane se izuzima nova kategorija. | exception |
| `exception_removed_conflict` | Nacrt uklanja izuzetak koji zakon priznaje. | Poseban rezim za mala gazdinstva nestaje. | exception |
| `cumulative_vs_alternative_conflict` | "i" se menja u "ili" ili obrnuto. | Potrebna dva uslova postaju alternativna. | condition_logic |
| `threshold_condition_conflict` | Prag uslova se menja. | Iznos, povrsina, broj zaposlenih, kolicina. | threshold |

## H. Definicije, Terminologija I Klasifikacije

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `definition_conflict` | Isti termin ima drugacije znacenje. | "Operator" definisan drugacije nego u zakonu. | term, definition |
| `undefined_term` | Nacrt koristi kljucni termin bez definicije. | "Nadlezni organ" bez odredjenja. | term |
| `reserved_term_misuse` | Koristi se termin rezervisan za drugi institut. | "Dozvola" umesto "saglasnost". | term, domain |
| `terminology_inconsistent` | Isti pojam se naziva razlicito. | "Subjekat", "operator", "korisnik" za isto lice. | term_cluster |
| `translation_alignment_conflict` | Prevod EU termina nije uskladjen. | EU termin preuzet suprotno standardnom prevodu. | eu_term, domestic_term |
| `classification_definition_conflict` | Definicija menja pravnu klasifikaciju. | Hrana tretirana kao roba opste namene. | object_class |
| `abbreviation_conflict` | Skracenica se uvodi za pogresan ili nejasan pojam. | Ista skracenica za dva organa. | abbreviation |

## I. Reference I Upucivanja

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `reference_missing` | Ciljana odredba ne postoji. | Poziv na clan 99 koji ne postoji. | reference_target |
| `reference_stale` | Upucivanje vodi na prestalu ili izmenjenu normu. | Stari zakon ili clan koji je brisan. | validity, reference_target |
| `reference_ambiguous` | Upucivanje ima vise mogucih ciljeva. | "zakon kojim se uredjuje..." bez preciziranja. | reference_target |
| `reference_wrong_target` | Upucivanje vodi na pogresan clan/stav/tacku. | Clan govori o drugoj materiji. | reference_target, action |
| `reference_scope_mismatch` | Upucivanje je presiroko ili preusko. | "shodno se primenjuje ceo zakon" umesto konkretnih clanova. | material_scope |
| `circular_reference` | Norme kruzno upucuju jedna na drugu bez sadrzaja. | Clan A na B, B na A. | reference_graph |
| `external_reference_unavailable` | Spoljni dokument nije identifikovan ili nije dostupan. | "u skladu sa standardom" bez oznake standarda. | external_source |
| `official_gazette_reference_mismatch` | Broj glasnika ne odgovara aktu. | Pogresan broj Sl. glasnika. | publication_metadata |

## J. Finansije, Takse, Naknade I Budzet

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `budget_impact_missing` | Nacrt stvara trosak bez fiskalne procene. | Nova obaveza organa bez obrazlozenja sredstava. | budget_impact |
| `fee_without_legal_basis` | Taksa/naknada uvedena bez osnova. | Pravilnik uvodi novu naknadu. | amount, legal_basis |
| `fee_amount_mismatch` | Iznos ili raspon nije uskladjen. | Naknada veca od zakonskog maksimuma. | amount, range |
| `funding_source_missing` | Ne navodi se izvor finansiranja. | Nova agencija ili registar bez izvora sredstava. | funding_source |
| `state_aid_risk` | Moguci rizik drzavne pomoci. | Selektivna subvencija bez osnova. | beneficiary, amount, condition |
| `budget_classification_conflict` | Pogresna budzetska klasifikacija ili nadleznost. | Prihod ide pogresnom nivou vlasti. | budget_account, jurisdiction |

## K. Sankcije, Mere I Nadzor

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `sanction_without_basis` | Sankcija uvedena bez zakonskog osnova. | Pravilnik propisuje kaznu. | sanction, source_rank |
| `sanction_amount_mismatch` | Kazna je van zakonskog raspona. | 500.000 din umesto maksimuma 100.000. | sanction.amount |
| `sanction_type_mismatch` | Pogresan tip sankcije ili mere. | Zabrana rada umesto novcane kazne. | sanction.type |
| `double_sanction_risk` | Ista radnja kaznjena dvostruko bez razgranicenja. | Prekrsaj i mera za isti osnov. | action, sanction |
| `missing_enforcement_measure` | Postoji obaveza bez mehanizma nadzora ili mere. | Nema organa koji proverava ispunjenje. | action, competence |
| `disproportionate_sanction_risk` | Sankcija deluje nesrazmerno cilju. | Mala povreda, drasticna mera. | sanction, risk |
| `inspection_measure_conflict` | Inspekcijska mera nije u skladu sa zakonom. | Inspektor naredjuje meru koju zakon ne poznaje. | inspection_type, measure |

## L. Postupak, Prava Stranaka I Pravni Lekovi

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `appeal_right_missing` | Nacrt izostavlja zalbu ili pravni lek gde je potreban. | Resenje bez prava zalbe. | remedy, procedure |
| `appeal_deadline_mismatch` | Rok za zalbu se ne slaze. | 8 dana vs 15 dana. | remedy, deadline |
| `due_process_risk` | Stranka nema izjasnjenje, uvid ili obrazlozenje. | Odluka bez prava izjasnjenja. | party_right |
| `burden_of_proof_conflict` | Teret dokazivanja je pogresno prebacen. | Stranka dokazuje cinjenice koje organ pribavlja. | burden |
| `silence_of_administration_conflict` | Cutanje uprave reseno suprotno sistemskom propisu. | Smatra se odbijenim umesto usvojenim. | procedure_outcome |
| `service_delivery_conflict` | Dostavljanje nije uskladjeno sa pravilima postupka. | Elektronsko dostavljanje bez uslova. | delivery_method |
| `administrative_fee_conflict` | Taksa u postupku nije uskladjena. | Trazena taksa za pravo koje je oslobodjeno. | fee, procedure |

## M. Podaci, Registri, Transparentnost I Poverljivost

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `personal_data_basis_missing` | Obrada podataka bez pravnog osnova/svrhe. | Registar trazi JMBG bez osnova. | personal_data, purpose |
| `data_minimization_risk` | Prikuplja se vise podataka nego sto je potrebno. | Svi licni podaci za jednostavnu prijavu. | data_fields, purpose |
| `confidentiality_vs_publication_conflict` | Jedna norma nalaze objavu, druga poverljivost. | Objavljuje se poslovna tajna. | disclosure, confidentiality |
| `registry_competence_conflict` | Pogresan organ vodi registar. | Registar hrane vodi nenadlezno telo. | registry, actor |
| `retention_period_conflict` | Rok cuvanja podataka nije uskladjen. | Cuva se trajno bez osnova. | retention |
| `access_to_information_conflict` | Ogranicava se pristup informacijama bez osnova. | Podaci javnog znacaja oznaceni kao nejavni. | access_right |

## N. EU Uskladjivanje

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `eu_alignment_statement_missing` | Nedostaje izjava o uskladjenosti. | Predlog nema izjavu. | required_artifact |
| `eu_alignment_table_missing` | Nedostaje tabela uskladjenosti. | EU relevantan propis bez tabele. | required_artifact |
| `eu_celex_missing` | Tabela nema CELEX oznaku. | Sekundarni izvor naveden bez CELEX-a. | eu_source |
| `eu_row_unmapped` | EU odredba nema domacu odredbu ili objasnjenje. | Prazna kolona domace odredbe. | alignment_row |
| `domestic_article_uncovered_by_alignment` | Novi domaci clan nije pokriven tabelom. | Clan menjan posle MEI misljenja. | domestic_path |
| `partial_alignment_without_reason` | Delimicna uskladjenost bez razloga. | Status delimicno, obrazlozenje prazno. | alignment_status |
| `non_alignment_without_plan` | Neuskladjenost bez plana/roka. | Nema datuma potpune uskladjenosti. | deadline |
| `not_transposable_without_reason` | Neprenosivo bez obrazlozenja. | Oznaka "neprenosivo" bez razloga. | alignment_status |
| `eu_term_translation_conflict` | Pogresan prevod EU termina. | Standardni termin zamenjen domacim pogresnim pojmom. | eu_term |
| `eu_effective_sanction_missing` | EU akt trazi delotvornu/srazmernu sankciju, domaci propis je nema. | Nema mere za povredu. | eu_requirement, sanction |
| `gold_plating_risk` | Domaci propis uvodi strozi zahtev bez obrazlozenja. | Dodatni tereti mimo direktive. | domestic_requirement, eu_requirement |
| `alignment_stale_after_draft_change` | Tabela nije azurirana posle izmene nacrta. | Promenjen clan, tabela stara. | artifact_version |

## O. Procesna Usaglasenost

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `ria_missing` | Nedostaje analiza efekata propisa. | Nema AEP/RIA artefakta. | required_artifact |
| `ria_incomplete` | Analiza efekata ne pokriva potrebna pitanja. | Nema budzetskog ili privrednog efekta. | artifact_fields |
| `public_consultation_missing` | Javna rasprava nije sprovedena ili evidentirana. | Nema programa/poziva. | procedure_stage |
| `public_consultation_duration_short` | Javna rasprava traje krace od propisanog minimuma. | 10 dana umesto 20. | deadline, stage |
| `public_consultation_report_missing` | Nema izvestaja o raspravi. | Komentari nisu obradjeni. | required_artifact |
| `official_opinion_missing` | Nedostaje obavezno misljenje. | Nema RSZ/MF/MEI misljenja. | institution, artifact |
| `negative_opinion_unresolved` | Negativno misljenje nije razreseno. | RSZ primedbe otvorene. | opinion_status |
| `conditional_opinion_unresolved` | Uslovno pozitivno misljenje nije ispraceno. | MF uslov nije ispunjen. | opinion_status |
| `fiscal_assessment_missing` | Postoji fiskalni efekat bez misljenja/obrazlozenja. | Nova obaveza troska. | budget_impact |
| `committee_gate_not_ready` | Predmet nije spreman za odbor/sednicu. | Nedostaju obavezni prilozi. | procedure_stage |
| `parliamentary_material_incomplete` | Skupstinski materijal nije kompletan. | Predlog bez obrazlozenja ili priloga. | required_artifact |

## P. Unutrasnja Konzistentnost Nacrta

| Finding type | Opis | Primer | Ključni slotovi |
| --- | --- | --- | --- |
| `internal_norm_conflict` | Dve odredbe nacrta su medjusobno suprotne. | Jedna dozvoljava, druga zabranjuje. | modality, action |
| `internal_duplicate_provision` | Ista odredba se ponavlja bez potrebe. | Dva clana sa istim tekstom. | source_quote |
| `internal_definition_conflict` | Termin je dvaput razlicito definisan. | "Operator" u clanu 2 i 5 razlicito. | term |
| `numbering_structure_error` | Numeracija ili hijerarhija je neispravna. | Preskocen clan/stav/tacka. | structure |
| `transitional_final_clause_missing` | Nedostaju prelazne/zavrsne odredbe gde su potrebne. | Izmene bez prelaznog rezima. | document_type |
| `repeal_clause_conflict` | Odredba o prestanku vazenja je nejasna ili pogresna. | Prestaje clan koji ne postoji. | repeal_target |
| `effective_clause_missing` | Nedostaje odredba o stupanju na snagu. | Nema zavrsnog clana. | effective_from |
| `drafting_style_warning` | Pravno-tehnicki problem bez direktnog konflikta. | Neodredjene formulacije, pasiv bez subjekta. | text_quality |

## Q. Implementaciona Pravila Za Engine

Svaki finding type iz ove taksonomije mora biti registrovan u
`conflict_type_registry`. Trenutni rule pack je
`backend/zaikon/rules/conflicts/registry.json`; ako se uvede YAML parser, isti
schema moze da predje u `registry.yaml`.
Aktivna slot-based pravila za prvu verziju nalaze se u
`backend/zaikon/rules/conflicts/active_rules.json`.

Minimalna struktura registry zapisa:

```yaml
finding_type: competence_conflict
category: competence
default_severity: high
required_slots:
  - actor
  - action
  - object
  - domain
operators:
  - wrong_domain_for_object
evidence_required:
  - draft_quote
  - corpus_quote
  - slot_diffs
fallback_mode: needs_expert_review
```

Za svaki tip treba imati:

- rule definition;
- schema test;
- najmanje jedan pozitivan evaluation primer;
- najmanje jedan negativan evaluation primer;
- GUI label i opis;
- report template.

## R. Prioritet Bez Suzenja Scope-a

Prioritet nije isto sto i scope. Scope engine-a je ceo katalog. Redosled
implementacije je samo praktican:

1. prvo slotovi i operatori koji otkljucavaju najveci broj konflikata;
2. zatim rule definitions za sve tipove;
3. onda punjenje evaluation primera po kategoriji;
4. na kraju ukljucivanje automatskog rezima za tipove koji imaju dovoljno dobar
   precision/recall.

Ako rule postoji, ali nema dovoljno podataka, engine mora da vrati jasan trace:

- `not_evaluated_missing_slot`;
- `not_evaluated_no_candidate`;
- `needs_expert_review_low_confidence`;
- `not_applicable_by_source_rank`;
- `not_applicable_by_procedure_type`.

Tako sistem ne cuti kada ne ume da odluci.
