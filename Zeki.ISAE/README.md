# Die Aussendungseinheit

*Eine New-Horizons-Mod für das normale Sonnensystem von Outer Wilds.*

Seit Beginn der Schleife meldet dein Schiff eine fremde Nomai-Energiesignatur. Zwischen der Sonne und Timber Hearth, weit über der Bahnebene der Planeten, kreist eine zweite Orbitale Sondenkanone: die **Interstellare Sonden Aussendungseinheit**. Drei schwebende Fokuskanonen umkreisen sie im Dreieck, und alle vier zielen in dieselbe Richtung.

Wenn du nichts tust, endet diese Schleife nicht mit einer Supernova. In einem Finale saugt die Einheit der sterbenden Sonne über leuchtende Energieströme ihr Licht ab. Die Sonne schrumpft, färbt sich rot und dann violett-weiß und verlischt mit einem Blitz. Die Hauptkanone feuert eine Sonde zu einem fremden Stern, die Kamera folgt ihr, das Universum wird dunkel, und dann heißt es:

> **Das Universum endet, aber du endest vor ihm...**

## Installation

1. [New Horizons](https://outerwildsmods.com/mods/newhorizons/) im Outer Wilds Mod Manager installieren.
2. Den Ordner `Zeki.ISAE` in den OWML-Mod-Ordner kopieren (`…/OWML/Mods/Zeki.ISAE`). Die `ZekiISAE.dll` liegt schon darin.
3. Spiel starten. Die Mod kann zusammen mit dem *Schleiersystem* laufen, braucht es aber nicht.

Das DLC *Echoes of the Eye* ist nicht nötig.

## Einstellungen (Mod Manager → Einstellungen)

| Einstellung | Standard | Bedeutung |
|---|---|---|
| Erst nach der Entdeckung scharf | aus | Wenn an: Die Sonne wird erst entzogen, nachdem du die Aussendungseinheit einmal besucht hast. Gut, wenn du erst das normale Spiel spielen willst. |
| Dauer des Energieentzugs | 60 s | Wie lange die Sonne am Ende der Schleife schrumpft (20–180 s). |
| Filmische Kamera im Finale | an | Die Kamera dreht sich zur sterbenden Sonne und folgt dann dem Schuss. Aus: Du behältst die Steuerung, alles andere passiert trotzdem. |
| Spiel-Materialien für die neuen Modelle | an | Die Blender-Modelle bekommen das Nomai-Metall der Sondenkanone. Aus: einfache Farben (falls die Modelle seltsam aussehen). |
| Hauptkanone automatisch ausrichten | an | Misst im Spiel, wohin der Lauf der echten Sondenkanone zeigt, und richtet die Kopie parallel zu den Fokuskanonen aus. |

## Die Geschichte (Spoiler)

Der Nomai **Sedum** half beim Bau der Orbitalen Sondenkanone. Ihm war klar, dass das Auge vielleicht gar nicht in diesem kleinen System liegt. Er entwarf deshalb eine Kanone, die Sonden zu *anderen Sternen* schießen kann. Sie braucht mehr Energie, als ein lebender Stern hergibt, also soll sie warten, bis die Sonne stirbt, und ihr dann alles nehmen. Pye verbot den Entwurf. Sedum baute ihn trotzdem.

Seine Helferin **Linum** prüfte die Rechnungen und fand den Fehler: Ohne Supernova gibt es keine Energie für das Projekt auf dem Aschezwilling. Ohne Projekt gibt es keine Schleife, und wer in ihr gefangen ist, kehrt nie zurück. Linum hinterließ eine Anleitung zum Abschalten.

## Komplettlösung (Spoiler)

1. **Signal finden:** Im Signalskop gibt es die neue Frequenz *Energiesignaturen*. Die Quelle ist die Aussendungseinheit. Im Logbuch steht sie ab dem Start als Gerücht.
2. *(Optional)* **Hinweis in der echten Sondenkanone:** Im Kontrollmodul der Orbitalen Sondenkanone über Giant's Deep steht ein neuer Computer mit Sedums Notiz.
3. **Kontrollmodul der Aussendungseinheit:** Ein Computer zeigt den Zustand der Einheit, ein Recorder enthält Linums Warnung und die Anleitung.
4. **Die drei Fokuskanonen** Alpha, Beta und Gamma kreisen 340 m um die Hauptkanone. Es sind schwebende Nomai-Plattformen mit künstlicher Schwerkraft auf dem Deck, auf dem du landen und laufen kannst. Auf jedem Deck steht ein leuchtender Kristall auf einem Sockel, der **Phasenkoppler**. Interaktion: *Phasenkoppler trennen*. Der Kristall zerspringt und sein Licht erlischt.
5. Sind alle drei Koppler getrennt, erscheint im Kontrollmodul der **Hauptschalter** mit einer Wegmarke. Interaktion: *Aussendungseinheit abschalten*. Der Energiekern erlischt.

Das Abschalten ist dauerhaft (im Spielstand gespeichert). Danach endet jede Schleife wieder ganz normal mit der Supernova. Getrennte Koppler bleiben ebenfalls über Schleifen hinweg getrennt.

Gegen Ende der Schleife (5 Minuten vorher) warnt das Schiff noch einmal.

## Wie die Kanone entstanden ist (ehrlich)

**Eine heile, frei bearbeitbare Orbitale Sondenkanone gibt es nicht öffentlich.** Ich habe GitHub und die Outer-Wilds-Mod-Datenbank durchsucht (über 500 Pfade aus veröffentlichten New-Horizons-Mods ausgewertet). Mods wie *EyeWitness* fügen der Vanilla-Kanone nur Texte hinzu, andere löschen sie. Ein eigenständiges Modell im modernen Vessel-Stil existiert nirgends. Dafür bräuchte man ein selbst gebautes Unity-Asset-Bundle.

Die Aussendungseinheit kopiert deshalb beim Laden **die komplette Kanone aus dem Spiel selbst** (`OrbitalProbeCannon_Body/Sector_OrbitalProbeCannon`: Nabe, Lauf, Kontroll- und Startmodul). Entfernt werden die Vanilla-Texte und das Orb-Interface; an ihre Stelle kommen die neuen Texte. Weil es eine Kopie des Originals ist, trägt das Startmodul dieselben Schäden wie im Spiel. Drei sich drehende Energieringe aus Blender legen sich im Vessel-Stil um den Lauf.

## Die Blender-Modelle

Die neuen Teile sind in Blender gebaut. Die Datei `Zeki.ISAE.Source/blender/ISAE_Props.blend` kannst du selbst öffnen und bearbeiten. Das Skript `tools/isae_models.py` erzeugt sie und exportiert sie als OBJ.

| Modell | Wo |
|---|---|
| **Fokuskanone** | Die drei kleinen Kanonen: schwebendes Deck mit Nomai-Rumpf darunter, drei geschwungene Arme, drei Fokusringe übereinander, Emitter in der Mitte, Sockel für den Phasenkoppler. Keine Asteroiden mehr. |
| **Fokusring** | Drei segmentierte, leuchtende Ringe, die sich um den Lauf der Hauptkanone drehen (im Finale achtmal schneller). |
| **Hauptschalter** | Konsole mit Hebel im Kontrollmodul, erscheint mit den getrennten Kopplern. |
| **Sonde** | Die interstellare Sonde, die im Finale abgefeuert wird. |

Outer Wilds lädt normalerweise nur Unity-Asset-Bundles, und die kann man nur mit dem Unity-Editor bauen. Deshalb lädt die DLL die OBJ-Dateien zur Laufzeit selbst: Sie baut daraus Meshes mit Kollision und gibt ihnen die Materialien der Sondenkanone. Wo die Modelle stehen, steht in `assets/models/placements.json`. Wenn dir ein Material nicht gefällt, kannst du dort einen exakten Materialnamen aus dem Spiel eintragen (zum Beispiel mit Unity Explorer nachsehen).

Damit die Kopie der echten Nomai-Sonde nicht in die Quere kommt, schaltet die DLL jede Startsteuerung der Sondenkanone ab, die nicht zur Original-Kanone gehört.

## Was die DLL macht

New Horizons kann vieles, aber nicht „Sonne schrumpft statt Supernova“. Dafür gibt es den C#-Teil (`Zeki.ISAE.Source`):

- **Supernova ersetzen:** Ein Harmony-Patch auf `SunController.OnTriggerSupernova` (und auf die ferne Ansicht der Sonne) startet das Finale statt der Supernova, solange die Einheit nicht abgeschaltet ist.
- **Das Finale** (`Finale.cs`) läuft in mehreren Schritten:
  1. Kinobalken und Untertitel blenden ein, die Musik des Endes läuft.
  2. Energieströme fließen von der Sonne in alle vier Kanonen, und Lichtsäulen steigen aus ihnen auf.
  3. Die Sonne schrumpft und färbt sich rot, dann violett-weiß. Dafür nutzt die DLL die Kollaps-Materialien und Kollaps-Partikel des Spiels.
  4. In den letzten 10 Sekunden dreht sich die Kamera zur Sonne. Sie verlischt mit einem Blitz.
  5. Die Hauptkanone feuert eine Sonde mit Leuchtspur ab, und die Kamera folgt ihr.
  6. Es wird dunkel, die Augen schließen sich, und New Horizons zeigt „Das Universum endet, aber du endest vor ihm...“. Danach läuft der Abspann mit der Musik des Spielendes, aber ohne den Urknall-Epilog.
- **Modelle laden:** Die DLL lädt die Blender-Modelle (`Models.cs`) und richtet die kopierte Kanone aus.
- **Echte Sonde schützen:** Die DLL verhindert, dass die Kopie die echte Nomai-Sonde abfeuert.
- **Der Rest** (Bedingungen, Logbuch, Schalter) läuft über normale New-Horizons-Konfigurationen.

## Ausrichtung der Kanonen

Die Fokuskanonen zielen entlang der Y-Achse ihres Körpers, und ihr Dreieck kreist in der Ebene senkrecht dazu. Alle Körper dieser Mod haben weder Achsneigung noch Eigendrehung, deshalb zeigen die vier Kanonen immer in dieselbe Richtung.

In welche Richtung der Lauf der Vanilla-Sondenkanone zeigt, ist nirgends dokumentiert. Die DLL misst es deshalb im Spiel: Die Start-Effekte der echten Kanone sitzen an ihrer Mündung. Danach dreht sie die Kopie so, dass ihr Lauf parallel zu den Fokuskanonen steht. Das Ergebnis steht im OWML-Log („Lauf der Sondenkanone (lokal): …“). Schaltest du „Hauptkanone automatisch ausrichten“ aus, gilt die Drehung `AIM_OPC` aus `tools/isae_build.py`.

## Für Entwickler

```bash
pip install numpy pillow jsonschema lxml
blender -b -P tools/isae_models.py -- Zeki.ISAE   # Blender 4.2: Modelle, anchors.json, .blend, Logbuchfoto
python tools/isae_texts.py Zeki.ISAE        # Nomai-Texte
python tools/isae_build.py Zeki.ISAE        # Körper, System, placements.json, Bilder, Manifeste
python tools/nh_validate.py Zeki.ISAE       # Schemas, Logbuch, Bedingungen, Platzierung
cd Zeki.ISAE.Source && dotnet build -c Release   # baut ZekiISAE.dll und kopiert sie nach Zeki.ISAE
```

Das Logbuch (`planets/shiplogs/ISAE.xml`) ist handgeschrieben. Der Validator erkennt auch Bedingungen, die von Interaktionsvolumen oder vom C#-Code gesetzt werden. `isae_models.py` schreibt in `anchors.json` die Punkte auf den Modellen (Koppler-Sockel, Konsole, Emitter, Lampen), an denen `isae_build.py` die Spielobjekte platziert. Wer ein Modell in Blender ändert, muss deshalb danach `isae_build.py` erneut ausführen.

## Wichtiger Testhinweis

Alle Dateien sind gegen die offiziellen New-Horizons-Schemas geprüft, die DLL baut ohne Warnungen gegen die echten Spielbibliotheken, und die Mechaniken habe ich am New-Horizons-Quellcode nachvollzogen. **Ich konnte die Mod nicht selbst in Outer Wilds starten.** Unsicher sind vor allem:

- ob die automatische Ausrichtung die Mündung richtig erkennt (das Log zeigt den Messwert),
- ob alle Teile der kopierten Kanone sauber mitgeladen werden,
- wie die Spiel-Materialien auf den Blender-Modellen aussehen (notfalls die Einstellung ausschalten oder Namen in `placements.json` eintragen),
- das Timing und die Kameraführung im Finale.

Am einfachsten passt du das mit dem Debug-Modus von New Horizons (Taste P zeigt die Position unter dem Fadenkreuz) und Unity Explorer an.
