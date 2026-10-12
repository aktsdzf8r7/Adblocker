# Das Dornenlabyrinth – Design-Spezifikation

Eine neue New-Horizons-Mod (`Zeki.Dornenlabyrinth`) für das normale Sonnensystem von Outer Wilds.

## 1. Ziel

Ein weiterer Dornensamen, der **Treibsamen**, taucht im Sonnensystem auf. Er führt in ein **unendliches Labyrinth** aus Bramble-Dimensionen.

- Das Labyrinth ist **fest**: Es hat in jeder Schleife und bei jedem Spielstand dieselbe Form. Wer sich einen Weg merkt, findet ihn wieder.
- Besondere Knoten tragen eine Farbe (Abschnitt 4).
- Es gibt **erwachsene Knoten** und **Baby-Samen** (NH `isSeed`).
- Es gibt viele Raumtypen mit eigenen Regeln (Abschnitt 5).
- Im Inneren liegt das **Bramble-Herz** (Abschnitt 6).

**Erfolg heißt:**
- Man kann beliebig tief ins Labyrinth fliegen und findet über grüne Knoten immer wieder hinaus.
- Die Farben halten, was sie versprechen.
- Ein Raumtyp ist am Aussehen und an seiner Regel erkennbar.
- Das Herz ist über lila Knoten erreichbar und verändert die Schleife spürbar.

Die Person kann das Spiel nicht für mich starten. Was die DLL zur Laufzeit tut, muss robust sein und viel ins OWML-Log schreiben.

## 2. Ort: der Treibsamen

- Ein kleiner NH-Körper `Treibsamen` auf einer Kreisbahn um die Sonne, mit Radius 18 000. Er liegt zwischen Giant's Deep und Dark Bramble.
- Er besteht nur aus einem großen Dornenknoten (Skala 1) mit grünlichem Licht.
- Ein Signal auf der Frequenz *Dornenrufe* („Treibsamen“) führt hin.
- Der Knoten führt in den **Vorhof**, und der Vorhof führt wieder hinaus.

## 3. Prinzip: Raumtypen und das Umleiten zur Laufzeit

- Jeder Raumtyp ist **genau eine** NH-Dimension, `Labyrinth_<Typ>`, mit festem Inhalt: Nebel, Ranken, Requisiten, Volumes.
- Jeder Raum hat einen **Vorrat an Knoten** (Abschnitt 5). NH baut sie mit Platzhalter-Zielen.
- Das Labyrinth selbst ist ein **unendlicher Graph** aus Raum-Instanzen. Eine Instanz hat eine 64-Bit-Nummer. Aus ihr folgen deterministisch (`MazeGraph`):
  - der Raumtyp,
  - wie viele Knoten und Samen aus dem Vorrat sichtbar sind,
  - pro sichtbarem Ausgang die Farbe und die Nummer der Ziel-Instanz,
  - der **Herz-Abstand** `h`.
- **Vor jedem Durchflug** durch einen Knoten unseres Labyrinths stellt die DLL den Zielraum auf die neue Instanz ein:
  1. Sie rechnet die Ziel-Instanz aus.
  2. Sie setzt `InnerFogWarpVolume._linkedOuterWarpVolume` des Knotens auf die Dimension des Zieltyps.
  3. Sie richtet die Knoten des Zielraums ein: sichtbar oder versteckt, Farbe, Ziel.
  4. Sie setzt den Rückweg: `OuterFogWarpVolume._linkedInnerWarpVolume` des Zielraums zeigt auf den Knoten, durch den man kam.
- Ein **Rückweg-Stapel** (bis 64 Einträge) merkt sich, woher man kam. Wer durch die Wand fliegt, landet wieder in der vorigen Instanz.
- Der Vorhof ist Instanz 0. Er hat `h` = 9 und immer einen Ausgang nach draußen, den Treibsamen.

## 4. Farben

| Farbe | Bedeutung |
|---|---|
| normal (graugrün, wie Dark Bramble) | eine Instanz eines zufälligen gewöhnlichen Typs |
| **Rot** | Die Ziel-Instanz ist ein **Anglerfisch-Nest**. |
| **Grün** | Das Ziel ist der **Vorhof** (Instanz 0). Von dort geht es hinaus. |
| **Gelb** | Das Ziel ist eine **echte Dimension von Dark Bramble**: Hub, Rettungskapsel, Pionier, Anglerfisch-Nest, Cluster, Kleines Nest oder Vessel. Man findet sie über ihre Körpernamen (`DB_*Dimension_Body`, `DB_SmallNest_Body`). Von dort führt der Weg nur durch Dark Bramble zurück. |
| **Lila** | Die Ziel-Instanz hat `h - 1`. Bei `h = 1` ist das Ziel die **Herzkammer**. |

**Regeln von `MazeGraph`:**
- Jede Instanz außer der Herzkammer hat höchstens einen lila Ausgang. Instanzen mit `h ≤ 9` auf dem Herzpfad haben genau einen.
- Ein gewöhnlicher Ausgang führt zu einer Instanz mit `h` zwischen 6 und 12.
- Der Vorhof hat immer einen lila Ausgang und keinen roten.
- Etwa jede vierte Instanz hat einen grünen Ausgang, jede siebte einen gelben.
- Rote Ausgänge gibt es nur in tieferen Räumen, also ab einem Abstand von 2 Räumen zum Vorhof.

**Darstellung:**
- Die DLL färbt das Punktlicht und die Lichtschäfte des Knotens ein.
- Dazu legt sie einen leuchtenden **Farbkranz** aus Blender um jeden sichtbaren Knoten, in der jeweiligen Farbe. So ist die Farbe immer deutlich, auch wenn das Einfärben der NH-Interna nicht greift.

## 5. Raumtypen

Jeder Raum hat einen Radius, eine Nebelfarbe, einen Knoten-Vorrat und eine Regel. Erwachsene Knoten haben Skala 0.5, Baby-Samen Skala 1 (10 m).

| Typ | Radius | Vorrat (Knoten / Samen) | Inhalt und Regel |
|---|---|---|---|
| **Vorhof** | 300 | 3 / 2 + Ausgang | Start und Ausgang. Ein Wegweiser-Text von Gneis erklärt die Farben. |
| **Dornengang** | 350 | 4 / 3 | der gewöhnliche Raum |
| **Dornenwald** | 300 | 4 / 3 | sehr dichte Ranken, enge Lücken |
| **Hitzekammer** | 250 | 1 / 6 | Alle 6 Samen führen **in die Hitzekammer selbst**. Jede Wiederholung erhöht die Stufe; das Hitze-Volume richtet `4 × Stufe` Schaden pro Sekunde an. Die Stufe wird angezeigt. Der eine erwachsene Knoten ist der kühle Ausweg; die Stufe fällt beim Verlassen auf 0. |
| **Frostkammer** | 320 | 3 / 2 | feste Wasserkristalle (Blender), 1–2 eingefrorene Anglerfische (Kopien ohne KI in einem Eisblock), ein Nomai-Skelett. Ein Schleppvolume bremst. |
| **Anglerfisch-Nest** | 400 | 3 / 1 | 2 lebende Anglerfische, dunkler roter Nebel |
| **Samenkammer** | 280 | 1 / 8 | viele Baby-Samen, jeder führt in eine andere Instanz |
| **Nebelkammer** | 350 | 3 / 2 | sehr dichter Nebel. Die Knoten erkennt man nur an ihrem Licht. |
| **Leere** | 700 | 1 / 0 | riesig und fast dunkel, mit einem fernen Knoten |
| **Strömungskammer** | 350 | 3 / 2 | Ein Richtungsvolume treibt alles durch den Raum. |
| **Echokammer** | 300 | 3 / 2 | 4 falsche Signale „Echo“ auf *Dornenrufe*. Nur eins sitzt an einem Knoten. |
| **Wrackkammer** | 320 | 3 / 1 | Trümmer eines Hearthianer-Schiffs (Blender), ein Skelett und eine Notiz von Gneis |
| **Spiegelkammer** | 300 | 4 / 0 | Alle Ausgänge führen in eine weitere Spiegelkammer, nur einer nicht. Die anderen verlieren `h`-Fortschritt. |
| **Herzpfad** | 320 | 3 / 2 | lila Nebel und Wegmarken von Gneis. Lila Ausgänge kommen hier gehäuft vor. |
| **Herzkammer** | 260 | 1 / 0 | das Bramble-Herz. Der einzige Ausgang ist grün. |

**Typ-Verteilung gewöhnlicher Ziele:**
- Dornengang 22 %, Dornenwald 12 %, Samenkammer 10 %, Nebelkammer 10 %, Frostkammer 9 %, Strömungskammer 9 %, Echokammer 8 %, Leere 6 %, Hitzekammer 6 %, Wrackkammer 4 %, Spiegelkammer 4 %.
- Ziele mit `h ≤ 3` sind zu 50 % ein Herzpfad.

**Gneis:**
- Gneis ist ein Hearthianer, der vor langer Zeit in den Samen geflogen ist.
- Seine Notizen (NH-Dialoge an Papier-Modellen) im Vorhof, in der Wrackkammer und auf dem Herzpfad erzählen, wie er die Farben gelernt hat. Er ist nie wieder hinausgekommen.

## 6. Das Bramble-Herz

- In der Herzkammer schwebt das **Bramble-Herz**: ein pulsierender lila Samenkern, ein NH-Item.
- Nimmt man es (`pickupFact` `ZEKIDL_HERZ_GENOMMEN`):
  1. **Das Labyrinth blutet.** Für den Rest der Schleife ist jeder Ausgang rot, außer den grünen. Die Ziele werden Nester, Grün bleibt der Weg hinaus.
  2. **Das Herz singt.** Sobald man mit dem Herz außerhalb des Labyrinths ist, ignorieren alle Anglerfische des Systems den Spieler bis zum Ende der Schleife. Ein Harmony-Prefix auf `AnglerfishController.ChangeState` verhindert *Investigating* und *Chasing*.
  3. Eine Meldung, ein Logbuch-Eintrag und ein Ton begleiten beides.
- Beim nächsten Schleifenbeginn liegt das Herz wieder an seinem Platz. Das Wissen aus dem Logbuch bleibt.

## 7. Technik

| Teil | Aufgabe |
|---|---|
| `tools/labyrinth_build.py` | NH-Configs: Treibsamen, 15 Raum-Dimensionen mit Knoten-Vorrat, Volumes, Requisiten, Signale, Dialoge, Logbuch, `assets/labyrinth.json` (Knotennamen pro Raum für die DLL) |
| `tools/labyrinth_models.py` | Blender: Farbkranz, Wasserkristalle, Eisblock, Schiffswrack, Notiz, Bramble-Herz |
| `Zeki.Dornenlabyrinth.Source/Logic/MazeGraph.cs` | rein und getestet: Instanz → Typ, Ausgänge, Farben, `h`. Zufall: SplitMix64. |
| `Logic/MazeWalk.cs` | rein und getestet: Rückweg-Stapel, Hitzestufe |
| `Labyrinth.cs` | Laufzeit: findet Räume und Knoten, fängt Durchflüge ab (Harmony auf `FogWarpVolume.WarpDetector`), leitet um, färbt ein, blendet ein und aus |
| `BrambleHeart.cs` | Herz: Bluten, Anglerfisch-Ruhe, Meldungen |
| `Zeki.Dornenlabyrinth.Tests` | xunit |

Der Validator `tools/nh_validate.py` prüft die Configs wie bei den anderen Mods.

## 8. Fehlerverhalten

- Findet die DLL einen Raum oder Knoten nicht, loggt sie das. Der Knoten behält dann sein NH-Ziel, den Vorhof. Man bleibt also nie stecken.
- Fehlt eine gelbe Vanilla-Dimension, wird der Ausgang normal.
- Jeder Laufzeit-Schritt steckt in try/catch und schreibt ins Log.

## 9. Nicht im Umfang

- Mehrspieler.
- Eine Zufallsquelle pro Spielstand: Die Form ist für alle gleich, damit Wege teilbar sind.
- Das Schiff im Labyrinth: Es kann wie in Dark Bramble mitfliegen, bekommt aber keine Sonderregeln.
