# Verdornt 0.2.0 – Planeten neu und die Dornensprache

Ergänzung zu `2026-10-10-verdornt-design.md`. Wo sich beide widersprechen, gilt dieses Dokument.

## 1. Ziel und Anlass

Rückmeldung nach 0.1.1:
- Alle Planeten sind „nur Bälle aus Bramble“.
- Außer Erstling haben sie keine Bramble-Knoten und zu wenig Lore und Gebäude.
- Die Dimensionen will die Person erst anschauen, wenn die Planeten stimmen.

Gewünscht:
1. **Planetenform:** In der Mitte jedes Planeten sitzt ein großer Bramble. Seine Wurzeln halten die Reste des Planeten zusammen.
2. **Inhalt:** Jeder Planet bekommt Bramble-Knoten, Lore und Gebäude.
3. **Neue Sprache, die Dornensprache.** Man lernt sie lesen, wenn man in einem Nomai-Labor einen verbrambelten Übersetzer findet. Die Texte sind die Kommunikation der Brambles untereinander und mit anderen Lebewesen.

Entschieden:
- Jeder Planet ist **unterschiedlich stark zerstört**.
- Die Sprache lernt man **Stück für Stück**: Jedes gelernte Wort wird ab dann in allen Texten übersetzt.

**Erfolg heißt:**
- Jeder der vier Planeten sieht von weitem und aus der Nähe klar nach „Bramble-Kern hält Planetenreste“ aus, und keiner gleicht dem anderen.
- Auf jedem gibt es eine Station, Texte, einen Knoten und etwas zu tun.
- Die Dornensprache ist anfangs unlesbar und wird beim Erkunden spürbar verständlicher.

## 2. Planetenform (Blender, `tools/verdornt_models.py`)

### 2.1 Gemeinsame Bauteile (neue Helfer)

| Helfer | Was es baut |
|---|---|
| `bramble_core(name, R, rnd)` | Ein Knäuel aus 20–30 dicken Ranken (wie der Herzdorn-Käfig, nur dichter) um eine leuchtende Samenlicht-Kugel, Radius etwa 0,3–0,45 × Planetenradius. Durch die Lücken sieht man das Licht. |
| `roots(name, R_core, targets, rnd)` | Verzweigte, sich verjüngende Wurzeln (`tube(..., taper=True)`) vom Kern zu jedem Zielpunkt. An jedem Ziel endet ein Wurzelgriff mit 3–5 Fingern, der das Krustenstück umklammert. |
| `crust_shard(name, R, centre_dir, size, thickness, mat, rnd)` | Ein Krustenstück: ein dickes, gezacktes Kugelschalen-Segment mit verschobener Oberfläche. Oben begehbar, unten mit Bruchkanten. |

Flache Plätze für Stationen und Lager bleiben in der Kruste ausgespart (wie bisher mit `flats`).

### 2.2 Die vier Planeten

| Planet (R) | Kern | Reste |
|---|---|---|
| **Erstling** (260) | Kern R≈100, Eislicht bläulich | Die Eiskruste ist zu etwa 80 % heil. 5–6 Schluchten (20–60 m breit, bis zum Kern tief) zerreißen sie. Wurzeln klammern sich über die Schluchtränder. Lager und Ankunft bleiben an ihren Stellen. |
| **Glutdorn** (220) | Kern R≈90 um eine glühende Lava-Kugel | Etwa 14 Schollen (40–90 m) hängen an Wurzeln. Zwischen ihnen sind 15–40 m Luft mit Blick auf die Lava, dazu begehbare Wurzelbrücken. Die Glutrisse liegen auf den Schollen. |
| **Nebelranke** (640, Nebel) | Kern R≈220 tief im Nebel | Ein schräger Trümmerring aus etwa 12 Inseln (60–120 m) im Radius 420–560. Die Riesenranken treiben zwischen den Inseln. NH-Boden (`groundSize`) entfällt; man landet auf den Inseln. |
| **Hohlsamen** (300) | Kristallkern R≈110, violett | Von der Samenhülle bleiben nur etwa 10 Splitter (Rippen und Schalenstücke) im dichten Wurzelnetz. Kristalldornen wachsen aus dem Kern nach außen. |

Die Schwerkraft wirkt wie bisher in NH zur Mitte. `surfaceSize` folgt dem äußersten begehbaren Radius.

**Prüfpunkt 1:** Bevor Inhalt gebaut wird, gehen Blender-Renderings der vier Planeten an die Person.

## 3. Inhalt pro Planet

### 3.1 Stationen (Blender, je eigenes Modell)

| Planet | Station | Was dort ist |
|---|---|---|
| **Erstling** | **Wurzellabor** (Hyssop), unten in der größten Schlucht, halb in den Kern gewachsen | Der verbrambelte Übersetzer, eingewachsen in eine Wurzel; 3 Nomai-Texte (Hyssops Forschung an den Ranken); 1 Dornenschrift |
| **Glutdorn** | **Glutwerk**: eine Nomai-Wärmestation auf der größten Scholle | Eine Murmel-Röhre fährt eine Brücke über die Lavaspalte zur Knoten-Scholle aus (Bedingung `ZEKIVD_GLUTBRUECKE_AUS`); 4 Nomai-Texte; 2 Dornenschriften |
| **Nebelranke** | **Treibstation** auf der größten Trümmerinsel, mit Laternen | 4 Nomai-Texte (Rue); 2 Dornenschriften (Gespräch mit den Wächtern = Anglerfischen); ein Hinweis auf Ernesto |
| **Hohlsamen** | **Kristallobservatorium** zwischen zwei Hüllensplittern | Projektionsbecken, das Herzdorn von nahem zeigt; 4 Nomai-Texte (Tansy erforscht die Sprache, jede Notiz lehrt Wörter); 2 Dornenschriften |

Jeder Planet bekommt außerdem 2 **Wortkerne** (siehe 4.3) und einen Logbuch-Eintrag für die Station.

### 3.2 Knoten und Pforten

| Planet | Knoten (NH-Name) | → Dimension |
|---|---|---|
| Erstling | `ZEKIVD_Erstling_Knoten` (besteht) | Eispforte (besteht) |
| Glutdorn | `ZEKIVD_Glutdorn_Knoten` auf der Knoten-Scholle | **Glutpforte** |
| Nebelranke | `ZEKIVD_Nebelranke_Knoten` an einer Insel | **Nebelpforte** |
| Hohlsamen | `ZEKIVD_Hohlsamen_Knoten` am Kristallkern | **Hohlpforte** |

Glutpforte, Nebelpforte und Hohlpforte werden jetzt als **einfache Dimensionen** gebaut: Nebel in Planetenfarbe, echte Dark-Bramble-Ranken, Ausgangsknoten zum Planeten, eine Dornenschrift und ein Wortkern. Die tieferen Dimensionen (6–9, 11–15, 17–20, 21–23) kommen in einer späteren Lieferung; ihre Knoten fehlen bis dahin.

## 4. Die Dornensprache

### 4.1 Schrift

- **Dornenschrift** ist ein Blender-Modell (`dornenschrift.obj`): eine flache Rindenplatte, auf der leuchtende Dornenranken in Spiralen und Knoten wachsen. Eine Variante steht frei, eine liegt flach auf dem Boden.
- Jede Instanz hat eine Text-ID. Platzierung über `placements.json` → `"schriften": [{name, body, parentPath, position, rotation, text}]`.

### 4.2 Lesen (DLL, `BrambleScript.cs`)

- Der Spieler zieht seinen Übersetzer (`ToolMode.Translator`) und zielt aus höchstens 6 m auf eine Dornenschrift. Dann erscheint ein **eigenes grünes Übersetzerfenster** in der Bildschirmmitte unten. Wegsehen oder Wegstecken schließt es.
- **Vor dem Fund** des verbrambelten Übersetzers (Bedingung `ZEKIVD_DORNSPRACHE` fehlt):
  - Überschrift „UNBEKANNTE SPRACHE“,
  - der ganze Text nur als Laute.
- **Danach:**
  - Überschrift „DORNENSPRACHE“,
  - bekannte Wörter auf Deutsch,
  - unbekannte Wörter als ihre Laute in einer anderen Farbe, zum Beispiel *krrhsh*.
- Laute statt Fantasiezeichen, weil die Spielschrift exotische Zeichen nicht sicher darstellt.
- Ein Text wird wortweise aufgebaut. Satzzeichen und Satzbau sind schon deutsch, nur die Wörter fehlen. So wird ein Text mit jedem gelernten Wort lesbarer.

### 4.3 Lernen

- **Der verbrambelte Übersetzer** liegt im Wurzellabor. Eine NH-Interaktion „Verbrambelten Übersetzer berühren“ setzt die persistente Bedingung `ZEKIVD_DORNSPRACHE`. Damit sind die etwa 10 **Grundwörter** bekannt.
- **Weitere Wörter** (etwa 40 insgesamt) haben je eine oder mehrere Quellen:
  - `fact:<ID>`: ein Logbuch-Fakt. Tansys Nomai-Notizen im Kristallobservatorium enthüllen beim Lesen Fakten (`ShipLogConditions` im Text-XML).
  - `kern:<ID>`: ein **Wortkern**. Das ist ein kleiner leuchtender Samen; eine NH-Interaktion „Wortkern berühren“ setzt die persistente Bedingung `ZEKIVD_WORTKERN_<ID>`.
- Die DLL prüft die Quellen alle 0,5 s. Ein neu gelerntes Wort wird als persistente Bedingung `ZEKIVD_WORT_<WORT>` gemerkt und meldet „NEUES WORT: <deutsch>“.
- Fortschritt bleibt über Schleifen erhalten.

### 4.4 Daten (`tools/verdornt_sprache.py` → `assets/sprache.json`)

```json
{
  "woerter": [{"id": "licht", "de": "Licht", "laut": "vael", "grund": true, "quellen": []},
              {"id": "waechter", "de": "Wächter", "laut": "ghorrm", "quellen": ["kern:NEBEL_1"]}],
  "texte": [{"id": "Glut_Ruf", "titel": "Ruf an die Samen",
             "zeilen": ["{wir} {tragen} das {licht} {hinaus}.", "..."]}]
}
```

`{wort}` steht für ein Wort der Sprache, alles andere ist fester Text.

### 4.5 Inhalt der Texte (etwa 12 Dornentexte)

- **Herzdorn an seine Samen:** Fliegt hinaus, tragt das Licht weiter.
- **Samen antworten** aus der Ferne, darunter einer, der „im Eis schläft“ (Dark Bramble).
- **Brambles an die Wächter (Anglerfische):** Hütet die Wege, die Kleinen sollen nicht hinein.
- **Brambles über die Nomai:** „Die Kleinen mit den Masken. Sie hören zu. Einer spricht mit niemandem.“ Das ist ein Wink zu Yarrow.

Die Brambles sind nicht böse. Sie verstehen sich als Träger des Sternenlichts und wollen weiterwachsen. Das bereitet Ende B „Der Zyklus“ vor.

### 4.6 Logik und Tests

`Logic/Vocabulary.cs` ist rein und ohne Unity. Es enthält:
- `Parse(zeile)` → Tokens,
- `Render(text, known)` → Zeilen mit Markierung bekannt/unbekannt,
- `Known(wort, conditions, facts)` → bekannt ja/nein.

Getestet wird mit xunit:
- Grundwörter nur mit `ZEKIVD_DORNSPRACHE`,
- Quellen `fact:` und `kern:`,
- unbekannte Wörter als Laute,
- Satzzeichen bleiben erhalten,
- unbekannte `{wort}`-IDs werfen beim Laden einen Fehler.

## 5. Technik

| Datei | Änderung |
|---|---|
| `tools/verdornt_models.py` | neue Helfer (2.1), vier Planeten neu, Modelle Wurzellabor, Glutwerk (+ Brücke), Treibstation, Kristallobservatorium, Dornenschrift, verbrambelter Übersetzer, Wortkern; Anker für alles |
| `tools/verdornt_build.py` | Knoten, drei Pforten, Stationen, Texte, Interaktionen, Wortkerne, Schriften, Röhre am Glutwerk, Version 0.2.0 |
| `tools/verdornt_texts.py` | etwa 15 neue Nomai-Texte |
| `tools/verdornt_sprache.py` (neu) | Wörter und Dornentexte → `assets/sprache.json` |
| `tools/verdornt_shiplog.py` | Einträge für die Stationen und die Sprache |
| `tools/nh_validate.py` | prüft `sprache.json`: Wörter existieren, jede Quelle existiert als Fakt oder Wortkern, jede Schrift hat einen Text |
| `Zeki.Verdornt.Source/BrambleScript.cs` (neu) | Schriften platzieren, Fenster, Lernen |
| `Zeki.Verdornt.Source/Logic/Vocabulary.cs` (neu) | reine Logik |

## 6. Lieferungen

1. **Vorschau:** Blender-Renderings der vier neuen Planeten. Die Person segnet sie ab.
2. **Planeten im Spiel:** neue Körper, Stationen, Nomai-Texte, Knoten, Pforten, Glutwerk-Brücke.
3. **Dornensprache:** Labor mit Übersetzer, Schriften, Wortkerne, Fenster, Lernen. Danach Version 0.2.0 als ZIP.

## 7. Nicht im Umfang (später)

- die tieferen Dimensionen 6–9, 11–15, 17–23,
- das Schiff mit der Notiz,
- Ernesto selbst (jetzt nur der Hinweis),
- Herzdorn-Inhalt, der Kernschrein und die Enden.
