# PRIMER – amt-runner

Arbeitsplan für das Repo `amt-runner` (Wrapper `run_amt.py`, der AMT.engine klont und auf eine Turtle-Datei anwendet). Wird zu Beginn jedes Chats komplett hochgeladen und am Ende zurückgeschrieben. Teil A gilt immer, Teil B ist die Übersicht, Teil C sind die Schritte, Teil D sind offene Punkte.

Die Schrittnummern gelten für dieses Repo. Im Primer von `amt-engine` heißt der Schritt, der dieses Repo auf das Muster bringt, S2; hier ist es S1.

---

## Teil A – Immer gültig

### A1 Ausgangslage

| Was | Wo | Rolle |
|---|---|---|
| Wrapper | `run_amt.py` | das Produkt: klont die Engine nach `.amt-cache/`, installiert deren Pakete, ruft `amt.runner` auf (Version 0.2.0) |
| Beispiele | `animals`, `PotterAttributionExample`, `SKOSconceptExample`, `subsumption-demo` (je `.ttl` und `.md`) | Eingaben, aus `amt-engine/examples/` kopiert |
| Dev-Pipeline | `main.py`, `py/` | Wartungsschritte `meta` und `tests` (seit S1), nicht Teil des Produkts |
| Tests | `tests/` | 11 Offline-Tests (seit S1) |
| Engine | `amt-engine` | wird zur Laufzeit geklont; eigenes Primer-Dokument dort |
| Erzeugt | `.amt-cache/`, `out/`, `build/` | alles ignoriert, nie committen |

**Befunde** (alle am 2026-10-26 geprüft, Stand `bab9ea8`; Engine beim Prüfen bei `41620dd`, inzwischen `b42b27b`):

- Das Repo hatte 11 Commits und keine Tags. Es gab keine Versionsangabe im Code; die Versionen 0.1.0 (2026-05-05) und 0.2.0 (2026-08-29) sind aus der Historie rekonstruiert. Seit S5 tragen die Commits `fc8d18d` und `445904c` die Tags `v0.1.0` und `v0.2.0`.
- `run_amt.py` braucht nur die Standardbibliothek. Die Pakete der Engine (`rdflib`, `pyshacl`, `pyvis`) kommen zur Laufzeit aus `requirements.txt` des Engine-Klons; die feste Liste im Skript ist nur der Rückfall für ältere Refs.
- Sieben von acht kopierten Beispieldateien sind byte-identisch mit `amt-engine/examples/`. `subsumption-demo.md` weicht gewollt ab (Befehle `python run_amt.py …` statt `python -m amt.runner …`, ein Absatz zu `out/run-…`).
- Ein End-to-End-Lauf (`python run_amt.py animals.ttl`, Linux, Python 3.13, Engine von GitHub) erzeugt wie in der README beschrieben 106 abgeleitete Kanten und sechs Ausgabedateien.
- Das Layout in der README nannte nur `animals.ttl` und `subsumption-demo.ttl`, obwohl auch die Potter- und SKOS-Beispiele im Repo liegen. Das Pin-Beispiel nannte noch `a50822c`. Beides korrigiert in S1.
- `LICENSE` nannte „NFDI4Objects | Research Software Engineering Projects“, die der Engine „Florian Thiery | LEIZA | NFDI4Objects“. Geklärt in S3 (A4).
- Das Repo `amt-runner` und der Befehl `amt-runner` der Engine heißen gleich und meinen Verschiedenes: das eine klont und installiert, das andere ist die Pipeline selbst.
- Die Fehler aus 0.2.0 (veralteter lokaler Branch im flachen Klon, Tag oder SHA nicht im flachen Verlauf) waren nicht durch Tests abgedeckt. S1 legt sie fest; die Tests schlagen an, wenn man das Nachladen der Historie oder das Auschecken von `origin/<ref>` entfernt (geprüft per Mutation).

### A2 Zielbild

```
python run_amt.py input.ttl [--ref R] [--update] [--minimal] [engine flags]
   │
   ├─► .amt-cache/amt-engine   (git clone --depth 1, dann detached auf origin/<ref>)
   ├─► pip install -r <engine>/requirements.txt   (einmal, Fingerabdruck)
   └─► python -m amt.runner input.ttl -o out/run-<Zeitstempel>/    →  out/latest

python main.py        meta ─► tests        →  build/pipeline_report.txt
```

Eigenschaften, die das Repo haben muss:

1. `run_amt.py` bleibt eine einzelne Datei, die nur die Standardbibliothek importiert; Nutzer kopieren sie in eigene Projekte.
2. `python main.py --strict` endet mit Exit-Code 0, ohne Netzwerk.
3. `__version__` in `run_amt.py`, `CITATION.cff`, `CHANGELOG.md` und `py/amt_runner_dev_utils.py` stimmt überein; sonst bricht `meta` ab.
4. Die Auflösung eines Refs (Branch, Tag, SHA außerhalb des flachen Verlaufs, `--update`, unbekannter Ref) ist durch Tests abgedeckt.
5. Das Verhalten von `run_amt.py` für Nutzer ist gegenüber 0.2.0 unverändert.

### A3 Querschnittsregeln

- `run_amt.py` importiert nichts außer der Standardbibliothek und nichts aus `py/`.
- Beispiele werden kopiert, nicht referenziert. Die Kopien stammen aus `amt-engine/examples/`; Änderungen entstehen dort und werden hierher übernommen.
- Laufzeit-Ausgaben behalten ihre Uhr (`out/run-<Zeitstempel>/`); die Regel „keine Uhr“ gilt für Repo-Inhalte. `RELEASE` und `RELEASE_DATE` stehen in `py/amt_runner_dev_utils.py`.
- Zweimal laufen lassen, `git status` bleibt beim zweiten Mal sauber.
- `main.py` und die Tests brauchen kein Netzwerk; der Engine-Ersatz in den Tests ist ein lokales Git-Repo.
- **Pro Repo genau eine `requirements.txt`**, ohne `requirements-dev.txt`. Was ein Repo zur Entwicklung braucht, steht in derselben Datei, mit Kommentar.
- Code, Kommentare, README, CHANGELOG, CITATION.cff: British English. `PRIMER.md` ist Deutsch.
- Befehle für Windows `cmd`, je Zeile ein Befehl, keine Fortsetzungszeichen.
- Ein Thema pro Chat. (Am 2026-10-26 wurden `amt-engine` und `amt-runner` ausnahmsweise im selben Chat bearbeitet, mit je eigenem Patch-ZIP.)
- `PATCH-README.md` begleitet ein Patch-ZIP und gehört nicht ins Repo; sie steht in `.gitignore` (so auch in `amt-engine` seit `b42b27b`).
- Änderungen an `run_amt.py` brauchen einen Eintrag im `CHANGELOG.md` und, wenn sie Verhalten ändern, einen Test.

### A4 Beschlusslage

| Frage | Beschluss | seit |
|---|---|---|
| Reihenfolge der Repos | `amt-engine` zuerst, danach `amt-runner` | 2026-10-26 |
| Orchestrator-Vertrag | `main.py` ist ein dünner Dev-Orchestrator neben `run_amt.py`; `run_amt.py` bleibt das Produkt und wird nicht umgebaut | 2026-10-26 |
| Uhr im Output | Laufzeit-Ausgaben behalten ihre Zeitstempel (`out/run-<Zeitstempel>`) | 2026-10-26 |
| Versionierung | Konstante `__version__ = "0.2.0"` in `run_amt.py`, kein `--version`-Flag (ein Flag würde sonst nicht mehr an die Engine durchgereicht) | 2026-10-26 |
| CHANGELOG | Keep a Changelog, rückwirkend rekonstruiert (0.1.0 und 0.2.0); Datum = Commit, der die Änderung geliefert hat; keine Tags | 2026-10-26 |
| Dev-Schritte | `meta` und `tests` im Standardlauf; die Netz-Schritte `smoke` und `drift` sind eigene Verben (`--only`), nie im Standardlauf und nie über `--from` oder `--skip` (S2) | 2026-10-26 |
| Netz-CI | `.github/workflows/network.yml`: wöchentlich (sonntags) und auf Abruf, Ubuntu, Python 3.13, `--strict`; nie bei Push | 2026-10-26 |
| Drift-Vergleich | nach Dateiname, Zeilenenden normalisiert; `subsumption-demo.md` weicht gewollt ab; nur in der Engine vorhandene Beispiele werden genannt, zählen aber nicht | 2026-10-26 |
| Namensgleichheit | Repo und Skript behalten ihre Namen; die README erklärt den Unterschied zum Engine-Befehl `amt-runner` | 2026-10-26 |
| Standard-Ref der Engine | bleibt `main` (Entscheidung am 2026-10-26); die README zeigt `--ref v0.3.1` als Beispiel für reproduzierbare Läufe | 2026-10-26 |
| `requirements.txt` | genau eine Datei pro Repo; hier nur Kommentar (Laufzeit = Standardbibliothek) plus `pytest` für die Entwicklung | 2026-10-26 |
| Engine-Pin | Standard bleibt `main`; das README-Beispiel zeigt `41620dd`; Pin auf Tags erst nach S5 (engine) | 2026-10-26 |
| Ort des Pipeline-Reports | `build/pipeline_report.txt`, ignoriert | 2026-10-26 |
| `pytest` aus der Engine-`requirements.txt` | darf mitinstalliert werden (Engine-S6); keine zweite Liste im Runner | 2026-10-26 |
| Versionen der GitHub Actions | `checkout@v5`, `setup-python@v6`, `upload-artifact@v6` (alle Node 24, geprüft an `action.yml`), wie in `amt-engine` | 2026-10-26 |
| CI-Matrix | Ubuntu und Windows, Python 3.10 und 3.13; Auslöser Push auf `main`, Pull Request und manuell; nur `python main.py --strict` (meta, tests; ohne Netz), kein Smoke-Lauf | 2026-10-26 |
| Autoren in `CITATION.cff` | Florian Thiery (ORCID 0000-0002-3246-3531) und Allard W. Mees (ORCID 0000-0002-7634-5342), beide LEIZA; ersetzt den Vorschlag „nur Thiery“ | 2026-10-26 |
| Rechteinhaber in `LICENSE` | „Florian Thiery \| LEIZA \| Research Squirrel Engineers Network“, wie in `amt-engine` | 2026-10-26 |
| Bedeutung von `RELEASE_DATE` | Datum des Commits, der die Version geliefert hat (0.2.0: 2026-08-29, 0.2.1: 2026-10-26) | 2026-10-26 |
| Tags und Releases | `v0.1.0` und `v0.2.0` als annotierte Tags auf `fc8d18d` und `445904c`, ohne GitHub-Release; `v0.2.1` ist das erste Release (keine Verhaltensänderung außer der Konstante `__version__`) | 2026-10-26 |
| DOI | Concept-DOI `10.5281/zenodo.23669557` steht in `CITATION.cff` und README; Version 0.2.1 trägt `10.5281/zenodo.23669558` | 2026-10-26 |
| Zenodo | GitHub-Zenodo-Anbindung ist eingeschaltet; nur das Release `v0.2.1` wird archiviert | 2026-10-26 |

Jede Zeile bekommt ein Datum. Vorschläge heißen `Vorschlag` und werden in dem Schritt bestätigt, in dem sie zuerst wirken. Überholte Beschlüsse werden mit neuem Datum und Grund umgeschrieben, nicht gelöscht.

### A5 Was in welchem Chat hochgeladen wird

`PRIMER.md` plus ein Bundle der Quellen, ohne erzeugte Dateien:

```cmd
robocopy . %TEMP%\amt-runner-bundle /E /XD .git .venv build out .amt-cache __pycache__ .pytest_cache
```

```cmd
powershell -NoProfile -Command "Compress-Archive -Path $env:TEMP\amt-runner-bundle\* -DestinationPath amt-runner-bundle.zip -Force"
```

`robocopy` meldet bei Erfolg Exit-Code 1; das ist kein Fehler. Nicht hochladen: `.venv/`, `.git/`, `.amt-cache/`, `out/`, `build/`.

Kommt der Chat mit GitHub-Zugriff, reicht es, den Stand zu klonen; der Upload entfällt dann.

### A6 IRI-Landkarte

Entfällt: Das Repo veröffentlicht kein RDF. Die Beispieldateien sind Eingaben und stammen aus der Engine.

---

## Teil B – Schrittübersicht

| ID | Schritt | Repo | hängt ab von | Status |
|---|---|---|---|---|
| S0 | Festlegungen: Version, Dev-Schritte, requirements, Engine-Pin | amt-runner | – | erledigt 2026-10-26 |
| S1 | Skeleton: `PRIMER.md`, `main.py`, `py/`, `tests/`, `CHANGELOG.md`, `CITATION.cff`, `requirements.txt`, README | amt-runner | S0 | erledigt 2026-10-26 |
| S2 | Netz-Schritte `smoke` und `drift` (eigene Verben, nie im Standardlauf) | amt-runner | S1 | erledigt 2026-10-26 |
| S3 | `CITATION.cff` und `LICENSE`: Autorenliste und Rechteinhaber klären | amt-engine, amt-runner | S1 | erledigt 2026-10-26 |
| S4 | CI: GitHub Action mit `python main.py --strict` bei Push und Pull Request | amt-runner | S1 | erledigt 2026-10-26 |
| S5 | Tags `v0.1.0`, `v0.2.0` setzen, Release 0.2.1, Zenodo-DOI | amt-runner | S3, S4 | erledigt 2026-10-26 |

S2 bis S5 sind erledigt. Offen bleiben die Punkte in Teil D.

Status ist `offen`, `erledigt <Datum>` oder `hinfällig`. Schritt-IDs werden nie umnummeriert.

---

## Teil C – Die Schritte

## S1 – Skeleton für amt-runner

**Ziel:** Das Repo trägt Plan, Entwicklungs-Pipeline, Tests, Änderungsprotokoll und Zitierangabe, ohne dass sich das Verhalten von `run_amt.py` ändert.

**Uploads:** `PRIMER.md` und das Bundle aus A5 (oder GitHub-Klon).

**Inhalt:**

- `run_amt.py`: eine Zeile, `__version__ = "0.2.0"`. Sonst nichts.
- `main.py` mit `--list`, `--only`, `--from`, `--skip`, `--dry-run`, `--strict`; Schritte `meta` und `tests`, je auch einzeln startbar.
- `tests/test_run_amt.py`: 11 Offline-Tests. Ein lokales Git-Repo mit getaggtem ersten Commit, untaggtem Zwischencommit und einem Tip ersetzt die Engine.
- `CHANGELOG.md`, `CITATION.cff`, `requirements.txt` (nur Kommentar und `pytest`), README-Abschnitt „Development“, korrigiertes Layout, `.gitignore` um `build/`, `.pytest_cache/` und `PATCH-README.md`.

**Abnahme:** `python main.py --strict` endet mit Exit-Code 0, zweimal hintereinander, `git status` beim zweiten Mal sauber; `pytest` meldet 11 grüne Tests; `run_amt.py` unterscheidet sich vom Stand `bab9ea8` nur um die Versionskonstante; ein End-to-End-Lauf `python run_amt.py animals.ttl` liefert weiterhin 106 abgeleitete Kanten.

### Erledigt 2026-10-26

- Gegenprobe der Tests per Mutation: Entfernt man das Nachladen der Historie, schlägt `test_commit_sha_outside_shallow_history_is_resolved` an; entfernt man den Fehlerzweig für unbekannte Refs, schlägt `test_unknown_ref_exits_with_a_message` an; ersetzt man `origin/<ref>` durch den lokalen Branch, schlägt `test_update_follows_the_remote_tip` an. Ein erster Entwurf des SHA-Tests nahm einen getaggten Commit und hätte die erste Mutation nicht bemerkt; deshalb gibt es den untaggten Zwischencommit.
- `meta` und `tests` laufen in unter drei Sekunden.
- Windows bestätigt am 2026-10-26 (Commit `021dc1d`, Python 3.10): `python main.py --strict` endet grün, 11 Tests in 23 s.

---

## S3 – Autoren und Rechteinhaber klären

**Ziel:** `CITATION.cff` und `LICENSE` stimmen mit `amt-engine` überein.

**Uploads:** `PRIMER.md`; Entscheidungen aus dem Formular im Engine-Chat (Details im Primer von `amt-engine`, S3).

**Abnahme:** `python main.py --strict` grün, zweimal hintereinander, `git status` sauber; `LICENSE` nennt denselben Rechteinhaber wie die Engine.

### Erledigt 2026-10-26

- Zusammen mit dem Engine-Patch ausgeliefert; die Entscheidungen stehen in A4.

## S4 – CI mit GitHub Actions

**Ziel:** Jeder Push auf `main` und jeder Pull Request läuft durch `python main.py --strict`, auf Linux und Windows.

**Uploads:** `PRIMER.md`, `README.md`, `CHANGELOG.md`; Entscheidungen aus dem Formular im Engine-Chat (siehe dort, S4).

**Abnahme:** Nach dem Push zeigt der Reiter „Actions“ den Lauf `CI` mit vier grünen Jobs.

### Erledigt 2026-10-26

- Workflow mit `actionlint` geprüft; ein echter Lauf war hier nicht möglich.
- Der Netz-Schritt `smoke` (D1) bleibt ein eigener Schritt; er gehört nicht in den Standardlauf und damit nicht in diese CI.

## S5 – Tags, Release 0.2.1 und Zenodo-DOI

**Ziel:** Wie in `amt-engine`: Tags für die bisherigen Versionen, ein erstes GitHub-Release `v0.2.1` und eine Zenodo-DOI in `CITATION.cff` und README.

**Uploads:** Zwei Patches (5a, 5c) und manuelle Befehle für die Tags (5b); Entscheidungen aus dem Formular im Engine-Chat.

**Teil 5a (Patch):** Version 0.2.1 in `run_amt.py`, `CITATION.cff`, `py/amt_runner_dev_utils.py` und `CHANGELOG.md`.

**Teil 5b (manuell):** annotierte Tags `v0.1.0` auf `fc8d18d`, `v0.2.0` auf `445904c` und `v0.2.1` auf dem Commit von 5a; `git push origin --tags`; Release aus `v0.2.1` anlegen.

**Teil 5c (Patch):** Zenodo-DOI eintragen.

**Abnahme:** `python main.py --strict` grün; `git tag` zeigt drei Tags; „Releases“ zeigt `v0.2.1`; auf zenodo.org steht die Version; nach 5c nennt `CITATION.cff` die DOI.

### Erledigt 2026-10-26

- 5a: Commit `310ae81` (Version 0.2.1); Windows-Lauf grün (11 Tests in 18 s).
- 5b: Tags `v0.1.0`, `v0.2.0`, `v0.2.1` gesetzt und gepusht, GitHub-Release `v0.2.1` angelegt.
- Zenodo: Version `10.5281/zenodo.23669558`, Concept-DOI `10.5281/zenodo.23669557`; Autoren mit ORCID aus `CITATION.cff`.
- 5c: DOI in `CITATION.cff`, Abschnitt „Citation“ im README, CHANGELOG unter `[Unreleased]`.

## S2 – Netz-Schritte smoke und drift

**Ziel:** Zwei Prüfungen, die das Netz brauchen, laufen auf Abruf und wöchentlich, ohne den Standardlauf abhängig vom Netz zu machen.

**Uploads:** `PRIMER.md`; Antworten aus einem Formular im Engine-Chat (Netz-CI: wöchentlich und auf Abruf).

**Inhalt:** `py/step_smoke.py`, `py/step_drift.py`, in `main.py` als eigene Verben; `tests/test_dev_steps.py` (9 Offline-Tests der Entscheidungen); `.github/workflows/network.yml`; README und CHANGELOG. `tests/conftest.py` nimmt `py/` in den Suchpfad auf, weil `py` sonst von pytests gleichnamigem Modul verdeckt würde.

**Abnahme:** `python main.py --strict` grün (20 Tests), zweimal hintereinander; `python main.py --only drift --strict` und `--only smoke --strict` enden mit 0; ein verändertes `animals.ttl` lässt `drift` mit `--strict` scheitern; `--from tests` und der Standardlauf rufen die Netz-Schritte nicht auf; nach dem Push zeigt „Actions“ den Workflow „Network checks“ (Start von Hand).

### Erledigt 2026-10-26

- Beide Schritte liefen gegen GitHub: `drift` meldete sieben gleiche Dateien und die eine gewollte Abweichung (`subsumption-demo.md`), `chain-test.ttl` und `skos-mapping-example.ttl` nur in der Engine; `smoke` schrieb alle sechs Dateien, 106 abgeleitete Kanten. `--ref v0.3.1` ergab denselben Wert (Engine `359b29f`).
- Gegenprobe: eine angehängte Zeile in `animals.ttl` ließ `drift --strict` mit Exit-Code 1 enden.
- Der Workflow ist mit `actionlint` geprüft; ein Lauf auf GitHub steht aus. Ein zweiter Lauf von `main.py --only …` überschreibt `build/pipeline_report.txt`; das Artefakt enthält darum nur den Bericht des letzten Schritts (`smoke`).
- Beschlüsse in A4.

---

## Teil D – Offene Punkte

- **D1** erledigt in S2: `smoke` (Engine klonen, `animals.ttl` durchlaufen lassen).
- **D2** erledigt in S2: `drift` (Vergleich der kopierten Beispiele mit `amt-engine/examples/`).
- **D3** erledigt 2026-10-26: Namen bleiben, die README trennt die beiden Bedeutungen (A4).
- **D4** erledigt 2026-10-26: `Related` in der README ist aktualisiert. Die GitHub-Pages-Seite der Engine (`https://n4o-rse.github.io/amt-engine/`, „AMT Explorer“) und `https://leiza-scit.github.io/CAA2026-amt/` (Potter Attribution) sind erreichbar; ob CAA2026-amt dasselbe Turtle-Format einliest, ließ sich aus der Seite nicht erkennen und steht deshalb nicht mehr in der README.
- **D5** erledigt 2026-10-26 (Engine-S6): `pytest` darf mitkommen. Ausgangslage: Engine-Primer, Beschluss vom 2026-10-26 („eine `requirements.txt` pro Repo“); `amt-engine` hatte zusätzlich `requirements-dev.txt`. Fasst man beide zusammen, installiert dieser Runner beim Start auch `pytest`, weil er die Datei der Engine verwendet. Entscheidung dort (Schritt S6).
- **D6** Der Engine-Aufruf aus `run_amt.py` liefert bei Konsistenzverletzungen Exit-Code 0 (siehe Engine-Primer, D6); der Wrapper reicht ihn unverändert durch.
