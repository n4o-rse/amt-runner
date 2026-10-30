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
- `run_amt.py` braucht nur die Standardbibliothek. Die Pakete der Engine (`rdflib`, `pyshacl`, `pyvis`) kommen zur Laufzeit aus `[project].dependencies` der `pyproject.toml` des Engine-Klons (seit S6; vorher aus dessen `requirements.txt`); die feste Liste im Skript ist nur der Rückfall.
- Sieben von acht kopierten Beispieldateien sind byte-identisch mit `amt-engine/examples/`. `subsumption-demo.md` weicht gewollt ab (Befehle `python run_amt.py …` statt `python -m amt.runner …`, ein Absatz zu `out/run-…`).
- Ein End-to-End-Lauf (`python run_amt.py animals.ttl`, Linux, Python 3.13, Engine von GitHub) erzeugt wie in der README beschrieben 106 abgeleitete Kanten und sechs Ausgabedateien.
- Das Layout in der README nannte nur `animals.ttl` und `subsumption-demo.ttl`, obwohl auch die Potter- und SKOS-Beispiele im Repo liegen. Das Pin-Beispiel nannte noch `a50822c`. Beides korrigiert in S1.
- `LICENSE` nannte „NFDI4Objects | Research Software Engineering Projects“, die der Engine „Florian Thiery | LEIZA | NFDI4Objects“. Geklärt in S3 (A4).
- Das Repo `amt-runner` und der Befehl `amt-runner` der Engine heißen gleich und meinen Verschiedenes: das eine klont und installiert, das andere ist die Pipeline selbst.
- Die Fehler aus 0.2.0 (veralteter lokaler Branch im flachen Klon, Tag oder SHA nicht im flachen Verlauf) waren nicht durch Tests abgedeckt. S1 legt sie fest; die Tests schlagen an, wenn man das Nachladen der Historie oder das Auschecken von `origin/<ref>` entfernt (geprüft per Mutation).
- Umzug des Repos (2026-10-30, Stand `d34bd1f`): `amt-runner` liegt jetzt unter `https://github.com/alpaca-fair-framework/`, die Engine ebenfalls. 35 Zeilen nennen noch `n4o-rse`: in `run_amt.py` das Klonziel `AMT_REPO_URL` (Zeile 48) sowie `EXPLORER_URL` und `HOWTO_URL` (Zeilen 59 und 62), dazu `py/step_drift.py`, `CITATION.cff`, `README.md`, `CHANGELOG.md`, `PRIMER.md` und die kopierten Beispiel-TTLs. Gezählt mit `grep` ohne `.git`. Nicht geprüft: ob die Weiterleitung von GitHub auch für `git clone` und `git fetch` im flachen Klon des Runners greift.
- Hextupel (2026-10-30): Der Runner ruft `amt.runner` der Engine unverändert auf und wertet keine Kanten aus. Ein Lauf mit Typ und Methode braucht deshalb keinen neuen Wrapper-Code, nur eine Engine mit dem Hextupel (Vorschlag: 0.6.0, Engine-Primer S21), ein Beispiel (`drift` vergleicht die Kopien mit `amt-engine/examples/`), Dokumentation und den Hinweis auf `--update`. Gegenstück zu S19 bis S23 im Primer von `amt-engine`.


### A2 Zielbild

```
python run_amt.py input.ttl [--ref R] [--update] [--minimal] [engine flags]
   │
   ├─► .amt-cache/amt-engine   (git clone --depth 1, dann detached auf origin/<ref>)
   ├─► pip install <Laufzeit-Pakete aus <engine>/pyproject.toml>   (einmal, Fingerabdruck)
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
| `pytest` aus der Engine-`requirements.txt` | hinfällig seit S6 (2026-10-27): der Runner installiert nur die Laufzeit-Pakete aus `pyproject.toml` des Engine-Klons, nicht mehr `requirements.txt` (die auch `pytest`, Pillow und PyYAML enthält); keine zweite Liste im Runner, nur der Rückfall bei fehlender Datei | 2026-10-27 |
| Hinweis nach dem Lauf | `run_amt.py` nennt am Ende die Adresse des Explorers (`https://n4o-rse.github.io/amt-engine/explorer/`) und die Datei `<name>.reasoned.ttl`, die sich dort mit dem Ordner-Knopf laden lässt | 2026-10-27 |
| Version | 0.3.0 zusammen mit der Engine 0.4.0 (Beschluss 2026-10-27); die Nummern ändert S13, nicht S6; 0.4.0 zusammen mit der Engine 0.5.0 (S9, S18) | 2026-10-27 |
| Versionen der GitHub Actions | `checkout@v5`, `setup-python@v6`, `upload-artifact@v6` (alle Node 24, geprüft an `action.yml`), wie in `amt-engine` | 2026-10-26 |
| `--check-only` im Wrapper | gehört dem Wrapper (eigene Option, Hilfetext), wird an die Engine weitergereicht; schreibt nichts: kein Laufordner, kein `latest`; fehlt die Option in der gecachten Engine, endet der Wrapper mit Exit-Code 2 und dem Rat `--update` (gleiches Muster wie `--minimal`) | 2026-10-27 |
| Meldung bei gescheitertem Lauf | der Wrapper erklärt die Exit-Codes 1 bis 3 der Engine in einem Satz und nennt die How-To-Seite; andere Codes (meist ein Traceback einer zu alten Engine) bekommen den Rat `--update`; der Exit-Code wird unverändert durchgereicht | 2026-10-27 |
| CI-Matrix | Ubuntu und Windows, Python 3.10 und 3.13; Auslöser Push auf `main`, Pull Request und manuell; nur `python main.py --strict` (meta, tests; ohne Netz), kein Smoke-Lauf | 2026-10-26 |
| Autoren in `CITATION.cff` | Florian Thiery (ORCID 0000-0002-3246-3531) und Allard W. Mees (ORCID 0000-0002-7634-5342), beide LEIZA; ersetzt den Vorschlag „nur Thiery“ | 2026-10-26 |
| Rechteinhaber in `LICENSE` | „Florian Thiery \| LEIZA \| Research Squirrel Engineers Network“, wie in `amt-engine` | 2026-10-26 |
| Bedeutung von `RELEASE_DATE` | Datum des Commits, der die Version geliefert hat (0.2.0: 2026-08-29, 0.2.1: 2026-10-26) | 2026-10-26 |
| Tags und Releases | `v0.1.0` und `v0.2.0` als annotierte Tags auf `fc8d18d` und `445904c`, ohne GitHub-Release; `v0.2.1` ist das erste Release (keine Verhaltensänderung außer der Konstante `__version__`) | 2026-10-26 |
| DOI | Concept-DOI `10.5281/zenodo.23669557` steht in `CITATION.cff` und README; Version 0.2.1 trägt `10.5281/zenodo.23669558` | 2026-10-26 |
| Zenodo | GitHub-Zenodo-Anbindung ist eingeschaltet; nur das Release `v0.2.1` wird archiviert | 2026-10-26 |
| Hextupel im Runner | Vorschlag: die Beschlüsse stehen im Primer von `amt-engine` (A4, 2026-10-30: Standard „vage“, Gewichts-Properties, abgeleitete Kanten); der Runner bekommt keine eigene Typ-Logik und kein neues Flag | Vorschlag |
| Versions-Hinweis zum Hextupel | Vorschlag: keine Versionsprüfung im Wrapper (anders als bei `--minimal` und `--check-only`, die neue Optionen sind); die README nennt die Mindestversion der Engine und verweist auf `--update` | Vorschlag |
| Version | Vorschlag: Runner 0.5.0 zusammen mit Engine 0.6.0 | Vorschlag |
| Adressen nach dem Umzug | folgt dem Engine-Primer (A4, 2026-10-30): Klonziel `https://github.com/alpaca-fair-framework/amt-engine.git`, Explorer und How-To unter `https://alpaca-fair-framework.github.io/amt-engine/`; die Prosa veröffentlichter CHANGELOG-Einträge behält die Adresse ihrer Zeit | 2026-10-30 |
| Namensräume der Beispiele | die Kopien folgen der Engine (A4 dort, 2026-10-30): `http://github.com/alpaca-fair-framework/amt-explore/` und `http://github.com/alpaca-fair-framework/amt-engine/subsumption-demo/`; die Kopien sind byteweise gleich mit denen der Engine, `drift` prüft das | 2026-10-30 |

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
| S6 | Nur Laufzeit-Abhängigkeiten installieren (aus `pyproject.toml` der Engine), Hinweis auf den Explorer, README | amt-runner | S5 | Patch geliefert, nach Push erledigt |
| S7 | Release 0.3.0 (Version, CHANGELOG, `smoke` mit `--update`), Tag, GitHub-Release, Zenodo | amt-runner | S6 | Patch, Tag `v0.3.0`, Release und Zenodo erledigt; DOI-Patch (Versions-DOI `10.5281/zenodo.23688616`) geliefert |
| S8 | `--check-only` im Wrapper, Erklärung der Exit-Codes, Hinweis auf `--update` (Gegenstück zu S16 in `amt-engine`) | amt-runner | S7 | erledigt 2026-10-27 |
| S9 | Release 0.4.0 (Version, CHANGELOG, Pinning-Beispiel `v0.5.0`), Tag, GitHub-Release, Zenodo (Gegenstück zu S18 in `amt-engine`) | amt-runner | S8 | 9a und 9b erledigt (Tag `v0.4.0`, Release, Zenodo); 9c als Patch geliefert |
| S10 | Adressen auf `alpaca-fair-framework` umstellen (`AMT_REPO_URL`, `EXPLORER_URL`, `HOWTO_URL`, `CITATION.cff`, README, `drift`); Gegenstück zu S19 in `amt-engine` | amt-runner | S9 | erledigt 2026-10-30 |
| S11 | Hextupel: Beispiel samt `.md`, README-Abschnitt, Hinweis auf die Mindestversion der Engine; Release 0.5.0 samt Zenodo; Gegenstück zu S21 bis S23 in `amt-engine` | amt-runner | S10, Engine S21 | 11a und 11b erledigt (Tag `v0.5.0`, Release, Zenodo); 11c als Patch geliefert |

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

## S6 – Schlankere Abhängigkeiten und Hinweis auf den Explorer

**Ziel:** Der Runner installiert nur, was ein Lauf braucht, und sagt am Ende, wo man das Ergebnis ansehen kann.

**Inhalt:** In `run_amt.py` liest `_engine_dependencies()` die Laufzeit-Pakete aus `[project].dependencies` der `pyproject.toml` des Engine-Klons (`tomllib`, unter Python 3.10 ein kleiner Textleser); fehlt die Datei oder ist sie unlesbar, gilt `AMT_FALLBACK_DEPS`. Der Fingerabdruck ist der Hash dieser Liste, nicht mehr der von `requirements.txt`: Änderungen an den Entwicklungspaketen der Engine lösen keine Neuinstallation mehr aus; beim ersten Lauf nach dem Update meldet der Runner einmal „Engine dependencies changed“. Nach dem Lauf steht die Adresse des Explorers in der Ausgabe. Tests: Parser, Fallback, Fingerabdruck, Aufruf von `pip`, Hinweis (7 neue Tests). README, CHANGELOG `[Unreleased]`.

**Abnahme:** `python main.py --strict` grün, zweimal; `python main.py --only smoke --strict` (Netz) installiert nur `rdflib`, `pyshacl`, `pyvis` und endet mit der Explorer-Zeile.

---

## S7 – Release 0.3.0

**Ziel:** Der Runner 0.3.0 ist veröffentlicht und archiviert, zusammen mit der Engine 0.4.0 (siehe S13 im Primer von `amt-engine`).

**Inhalt:** Version 0.3.0 in `run_amt.py`, `CITATION.cff`, `py/amt_runner_dev_utils.py` (`RELEASE_DATE` 2026-10-27) und `CHANGELOG.md`; die README nennt `--ref v0.4.0` als Beispiel. Der Schritt `smoke` ruft den Wrapper mit `--update` auf: beim ersten Windows-Lauf nach S6 lief er gegen die zwischengespeicherte alte Engine (`a50822c`) und bestätigte deshalb nichts über den neuen Stand; ein Test hält das fest.

**Danach (manuell):** annotierter Tag `v0.3.0` auf dem Commit dieses Patches, Release auf GitHub, Zenodo, dann ein Patch mit der Versions-DOI in README und CHANGELOG.

**Abnahme:** `python main.py --strict` zweimal grün; `python main.py --only smoke --strict` zeigt im Lauf den aktuellen Commit der Engine; `git tag` zeigt `v0.3.0`.

---

## S8 – Prüfen ohne Ausgabe, verständliche Fehler

**Ziel:** Der Wrapper unterstützt das Prüfen einer Datei beim Bauen, ohne Ausgabeordner, und erklärt, was ein Abbruch bedeutet.

**Anlass:** Rückmeldung von Karsten (AFE → AMT), siehe S16 im Primer von `amt-engine`: sein Lauf endete mit einem Traceback aus `.amt-cache/amt-engine/amt/viz.py`, weil der Cache eine ältere Engine enthielt als `main`.

**Inhalt:** `run_amt.py`: Option `--check-only` (Hilfetext), `run_pipeline(..., check_only=True)` ohne Laufordner und ohne `latest`, Prüfung mit `engine_supports()`; `EXIT_MESSAGES` und `HOWTO_URL`; Tests in `tests/test_run_amt.py`; CHANGELOG und README.

**Abnahme:** `python main.py --strict` zweimal grün; `python run_amt.py animals.ttl --check-only --update` druckt die Diagnose und legt keinen Ordner unter `out/` an; mit der alten Engine (`--ref v0.4.0`) endet derselbe Befehl mit Exit-Code 2 und dem Rat `--update`.

### Erledigt 2026-10-27

- Sandbox: 33 Tests grün (vorher 27). Noch offen: der Netz-Lauf `python main.py --only smoke --strict` und ein Lauf unter Windows; `--check-only` gegen die echte Engine geht erst, wenn der Engine-Patch (S16) auf `main` liegt.

---

## S9 – Release 0.4.0

**Ziel:** Der Runner 0.4.0 mit `--check-only` ist veröffentlicht und archiviert, zusammen mit der Engine 0.5.0 (siehe S18 im Primer von `amt-engine`).

**Inhalt (9a, Patch):** Version 0.4.0 in `run_amt.py`, `CITATION.cff`, `py/amt_runner_dev_utils.py` und `CHANGELOG.md`; die README nennt `--ref v0.5.0` als Beispiel und verlangt für `--check-only` die Engine 0.5.0 oder neuer (die Engine 0.4.0 kennt die Option nicht); Verweis auf die How-To-Seite „Run and look at the result“.

**Versions-DOI Runner 0.4.0:** `10.5281/zenodo.23695549`.

**Danach (manuell, 9b):** annotierter Tag `v0.4.0` auf dem Commit von 9a, Release auf GitHub, Zenodo. **9c (Patch):** die Versions-DOI in README und CHANGELOG.

**Abnahme:** `python main.py --strict` zweimal grün; `python main.py --only smoke --strict` läuft gegen die Engine `main`; `git tag` zeigt `v0.4.0`.

## S10 – Adressen auf alpaca-fair-framework umstellen

**Ziel:** Klonziel und Verweise des Runners nennen die neue Organisation, ohne dass sich Argumente oder Ausgabedateien ändern.

**Uploads:** `PRIMER.md` und das Bundle des Runners; der Engine-Patch aus S19, falls schon ausgeliefert.

**Inhalt:** `AMT_REPO_URL`, `EXPLORER_URL` und `HOWTO_URL` in `run_amt.py`, `py/step_drift.py`, `CITATION.cff`, `README.md` und die kopierten Beispiel-TTLs. Die Beispiele sind Kopien der Engine-Beispiele; ändert S19 sie dort, meldet `drift` Abweichungen, bis sie hier nachgezogen sind. Die neue Pages-Adresse wird in der Engine festgelegt (Engine-Primer, D18); diesen Schritt erst danach ausliefern. Eintrag im `CHANGELOG.md` unter `[Unreleased]`, `Changed`.

**Abnahme:** `git grep -n "n4o-rse" -- .` nennt nur bewusst belassene Treffer (mit Liste im `PATCH-README.md`); `python main.py --strict` zweimal grün, `git status` danach sauber; `python main.py --only smoke --strict` klont die Engine von der neuen Adresse und läuft durch.

### Erledigt 2026-10-30

- Ersetzt in `run_amt.py` (`AMT_REPO_URL`, `EXPLORER_URL`, `HOWTO_URL`), `py/step_drift.py` (`ENGINE_URL`), `CITATION.cff`, `README.md` (Klonbefehle, Fork- und Pull-Request-Hinweise, Beispielausgabe, Links), den Namensräumen der drei kopierten Beispiele und den Verweislinks am Ende des `CHANGELOG.md`. Die Prosa der veröffentlichten Einträge (drei Stellen mit der alten Pages-Adresse) und die älteren Einträge in diesem Primer bleiben unverändert.
- Die Beispielkopien sind byteweise gleich mit denen im Engine-Patch (S19, Namensräume). Bis der Engine-Patch gepusht ist, meldet `drift` Abweichungen, weil es gegen die Engine `main` vergleicht; deshalb beide Patches zusammen einspielen und die Engine zuerst pushen.
- `python main.py --strict` zweimal grün; `python main.py --only smoke --strict` klont die Engine über die neue Adresse und läuft durch (106 abgeleitete Kanten, Explorer-Hinweis mit der neuen Adresse).

## S11 – Hextupel im Runner und Release 0.5.0

**Ziel:** Eine Datei mit Typ und Methode läuft über den Runner, und der Runner 0.5.0 ist zusammen mit der Engine 0.6.0 veröffentlicht und archiviert.

**Uploads:** `PRIMER.md`, das Bundle des Runners, `examples/hextuple-demo.ttl` und `.md` aus der Engine (S21).

**Inhalt:** das Beispiel `hextuple-demo.ttl` mit `.md` (die `.md` weicht wie bei `subsumption-demo.md` gewollt ab: Befehle `python run_amt.py …`); ein README-Abschnitt (Englisch), der Typ und Methode erklärt, die Mindestversion der Engine nennt und `--update` empfiehlt; keine neue Wrapper-Logik und deshalb kein neuer Offline-Test, `smoke` deckt das Beispiel gegen die echte Engine ab. Version 0.5.0 in `run_amt.py`, `CITATION.cff`, `py/amt_runner_dev_utils.py` und `CHANGELOG.md`; Release nach dem Muster von S9 (11a Patch, 11b manuell: Tag, Release, Zenodo; 11c Patch: Versions-DOI).

**Abnahme:** wie S9: `python main.py --strict` zweimal grün; `python main.py --only smoke --strict` läuft mit dem Hextupel-Beispiel durch und die Ausgabe nennt Typ und Methode; `git tag` zeigt `v0.5.0`; nach 11c nennt die README die Versions-DOI.

### Erledigt 2026-10-30 (11a)

- Version 0.5.0 in `run_amt.py`, `py/amt_runner_dev_utils.py` (`RELEASE`, `RELEASE_DATE` 2026-10-30), `CITATION.cff` und `CHANGELOG.md` (`[0.5.0] - 2026-10-30`, Vergleichslinks); Pinning-Beispiel `--ref v0.6.0`.
- Neu: `hextuple-demo.ttl` (byte-gleich zur Engine) und `hextuple-demo.md` (Befehl `python run_amt.py hextuple-demo.ttl`, Hinweis auf Engine 0.6.0; weicht gewollt ab, steht in `INTENDED` von `py/step_drift.py`); README-Abschnitt und Layout-Zeile.
- Geprüft: `python main.py --strict` zweimal grün, `git status` stabil; `python main.py --only drift` grün (8 Dateien gleich, 2 weichen gewollt ab); `python run_amt.py hextuple-demo.ttl --update` gegen die gepushte Engine (a451995): alle sechs Ausgabedateien, fünf `fw:hasMethod` in der Ausgabe. `smoke` wurde nicht auf `hextuple-demo.ttl` erweitert (er prüft weiter `animals.ttl`).
- Offen: 11b und 11c siehe unten.

### Erledigt 2026-10-30 (11b, 11c)

- 11b (durch den Autor): Commit `f18f360` (Release-Patch), Folgecommit `eb6adb1`, annotierter Tag `v0.5.0` auf `eb6adb1`, GitHub-Release, Zenodo. Versions-DOI Runner 0.5.0: `10.5281/zenodo.23809732`; die Concept-DOI `10.5281/zenodo.23669557` bleibt.
- Zwischenfall: im lokalen Checkout des Autors fehlten `animals.ttl`, `subsumption-demo.ttl` und `SKOSconceptExample.ttl` schon vor dem Einspielen (`git status` zeigte `D`, `smoke` meldete „Input file not found: animals.ttl“). `git add -A` hat die Löschungen in `f18f360` mit aufgenommen (12 statt der erwarteten 9 Einträge). Behoben mit `git checkout 5802352 -- <drei Dateien>` und Folgecommit `eb6adb1`; der Tag wurde erst danach gesetzt. Regel: vor `git add -A` muss `git status --short` genau die in der `PATCH-README.md` genannten Einträge zeigen, und ein roter Schritt (hier `smoke`) wird vor dem Commit geklärt.
- 11c (Patch): die Versions-DOI in README (Abschnitt „Citation“) und unter `[Unreleased]` im CHANGELOG.

## Teil D – Offene Punkte

- **D1** erledigt in S2: `smoke` (Engine klonen, `animals.ttl` durchlaufen lassen).
- **D2** erledigt in S2: `drift` (Vergleich der kopierten Beispiele mit `amt-engine/examples/`).
- **D3** erledigt 2026-10-26: Namen bleiben, die README trennt die beiden Bedeutungen (A4).
- **D4** erledigt 2026-10-26: `Related` in der README ist aktualisiert. Die GitHub-Pages-Seite der Engine (`https://n4o-rse.github.io/amt-engine/`, „AMT Explorer“) und `https://leiza-scit.github.io/CAA2026-amt/` (Potter Attribution) sind erreichbar; ob CAA2026-amt dasselbe Turtle-Format einliest, ließ sich aus der Seite nicht erkennen und steht deshalb nicht mehr in der README.
- **D5** erledigt 2026-10-26 (Engine-S6): `pytest` darf mitkommen. Ausgangslage: Engine-Primer, Beschluss vom 2026-10-26 („eine `requirements.txt` pro Repo“); `amt-engine` hatte zusätzlich `requirements-dev.txt`. Fasst man beide zusammen, installiert dieser Runner beim Start auch `pytest`, weil er die Datei der Engine verwendet. Entscheidung dort (Schritt S6).
- **D6** Der Engine-Aufruf aus `run_amt.py` liefert bei Konsistenzverletzungen Exit-Code 0 (siehe Engine-Primer, D6); der Wrapper reicht ihn unverändert durch.
- **D7** S11 wartet auf S20 im Primer von `amt-engine` (Festlegungen zum Hextupel) und auf S21 (Engine mit Typ und Methode). Erst danach Beispiel und README-Abschnitt schreiben.
- **D8** erledigt in S10 (2026-10-30): Die Pages-Adresse ist `https://alpaca-fair-framework.github.io/amt-engine/` (Engine-Primer, A4); `EXPLORER_URL` und `HOWTO_URL` sind umgestellt.
