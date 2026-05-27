# zAIkon E2E

Automatizovani UI scenario koristi set PDF-ova iz foldera:

```text
D:\POSAO\OllamaProjects\ZAIKON\DOCUMENTS\šumarstvo
```

Scenario prolazi kroz:

- kreiranje korpusa i import lokalnog foldera,
- pregled import artefakata i traga obrade,
- listu dokumenata, detalj dokumenta i Akoma link,
- hybrid search sa relevantnim šumarskim upitima,
- kreiranje i pokretanje provere nacrta,
- pregled nalaza i odluku recenzenta kada nalaz postoji,
- generisanje DOCX i PDF izveštaja,
- assistant sesiju sa pitanjem i citatima.

## Pokretanje

Prvo pokreni aplikaciju iz root foldera projekta:

```bat
startserver.bat
```

Zatim u `frontend` folderu:

```bat
npm run e2e:ui
```

Ovo otvara Chromium u headed režimu sa usporenim koracima, da možeš da gledaš tok testa.

Za brzi regression test:

```bat
npm run e2e:regression
```

Ako test treba da koristi drugi folder ili drugi API/UI host:

```bat
set "ZAIKON_E2E_FORESTRY_DIR=D:\neki\drugi\folder"
set "ZAIKON_E2E_API_BASE=http://127.0.0.1:8100"
set "ZAIKON_E2E_UI_BASE=http://127.0.0.1:5173"
npm run e2e:ui
```

Ako Playwright browser nije instaliran:

```bat
npm run e2e:install
```
