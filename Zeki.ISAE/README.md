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
| Hauptkanone automatisch ausrichten | an | Misst im Spiel, wohin der Lauf der echten Sondenkanone zeigt, und richtet die Kopie parallel zu den Fokuskanonen aus. |

## Die Geschichte (Spoiler)

Der Nomai **Sedum** half beim Bau der Orbitalen Sondenkanone. Ihm war klar, dass das Auge vielleicht gar nicht in diesem kleinen System liegt. Er entwarf deshalb eine Kanone, die Sonden zu *anderen Sternen* schießen kann. Sie braucht mehr Energie, als ein lebender Stern hergibt, also soll sie warten, bis die Sonne stirbt, und ihr dann alles nehmen. Pye verbot den Entwurf. Sedum baute ihn trotzdem.

Seine Helferin **Linum** prüfte die Rechnungen und fand den Fehler: Ohne Supernova gibt es keine Energie für das Projekt auf dem Aschezwilling. Ohne Projekt gibt es keine Schleife, und wer in ihr gefangen ist, kehrt nie zurück. Linum hinterließ eine Anleitung zum Abschalten.

## Komplettlösung (Spoiler)

1. **Signal finden:** Im Signalskop gibt es die neue Frequenz *Energiesignaturen*. Die Quelle ist die Aussendungseinheit. Im Logbuch steht sie ab dem Start als Gerücht.
2. *(Optional)* **Hinweis in der echten Sondenkanone:** Im Kontrollmodul der Orbitalen Sondenkanone über Giant's Deep steht ein neuer Computer mit Sedums Notiz.
3. **Kontrollmodul der Aussendungseinheit:** Ein Vessel-Computer zeigt den Zustand der Einheit, ein Vessel-Recorder enthält Linums Warnung und die Anleitung.
4. **Die drei Fokuskanonen** Alpha, Beta und Gamma kreisen 340 m um die Hauptkanone. Es sind schwebende Schwerkraftkanonen ohne Felsen, mit künstlicher Schwerkraft über ihrer Startplattform, auf der du landen und laufen kannst. Auf jeder Plattform leuchtet ein Kristall, der **Phasenkoppler**. Interaktion: *Phasenkoppler trennen*. Der Kristall zerspringt und sein Licht erlischt.
5. Sind alle drei Koppler getrennt, erscheint im Kontrollmodul der **Hauptschalter**: das Koordinaten-Interface des Vessels mit einem schwebenden Warpkern darüber, daneben eine Wegmarke. Interaktion: *Aussendungseinheit abschalten*. Der Energiekern erlischt.

Das Abschalten ist dauerhaft (im Spielstand gespeichert). Danach endet jede Schleife wieder ganz normal mit der Supernova. Getrennte Koppler bleiben ebenfalls über Schleifen hinweg getrennt.

Gegen Ende der Schleife (5 Minuten vorher) warnt das Schiff noch einmal.

## Wie die Kanone entstanden ist (ehrlich)

**Eine heile, frei bearbeitbare Orbitale Sondenkanone gibt es nicht öffentlich.** Ich habe GitHub und die Outer-Wilds-Mod-Datenbank durchsucht (über 500 Pfade aus veröffentlichten New-Horizons-Mods ausgewertet). Mods wie *EyeWitness* fügen der Vanilla-Kanone nur Texte hinzu, andere löschen sie. Ein eigenständiges Modell im modernen Vessel-Stil existiert nirgends. Dafür bräuchte man ein selbst gebautes Unity-Asset-Bundle.

Die Aussendungseinheit kopiert deshalb beim Laden **die komplette Kanone aus dem Spiel selbst** (`OrbitalProbeCannon_Body/Sector_OrbitalProbeCannon`: Nabe, Lauf, Kontroll- und Startmodul). Entfernt werden die Vanilla-Texte und das Orb-Interface; an ihre Stelle kommen die neuen Texte. Weil es eine Kopie des Originals ist, trägt das Startmodul dieselben Schäden wie im Spiel.

## Alles aus dem Spiel

Jedes Bauteil, das es in Outer Wilds schon gibt, wird aus dem Spiel kopiert, im Vessel-Stil, wo es eine Vessel-Variante gibt. Alle Pfade stammen aus veröffentlichten New-Horizons-Mods, in denen sie schon funktionieren.

| Bauteil | Original im Spiel |
|---|---|
| Hauptkanone | die Orbitale Sondenkanone |
| Ringe um den Lauf | die Bauringe des Konstruktionshofs auf Giant's Deep, mit denen die Nomai die echte Kanone gebaut haben. Sie drehen sich langsam, im Finale achtmal schneller. |
| Fokuskanonen | die Schwerkraftkanone von Ember Twin mit ihrer Startplattform |
| Hauptschalter | das Koordinaten-Interface von der Brücke des Vessels und der fortgeschrittene Warpkern des Vessels |
| Computer und Recorder | Vessel-Computer und Vessel-Recorder, wie in den Rettungskapseln |
| Interstellare Sonde im Finale | eine Kopie der echten Nomai-Sonde |
| Lichter, Kristalle, Energiekern | Nomai-Lampen, Schwerkraftkristalle, Warp-Partikel des Vessel-Warpkerns, Lichtsäule einer Rettungskapsel |

Einige Dinge lassen sich nur im laufenden Spiel ausmessen. Das erledigt die DLL (`GameProps.cs`), sobald New Horizons alles gebaut hat:

- Sie richtet die Kanone aus.
- Sie schiebt die Bauringe auf die Mitte des Laufs.
- Sie verschiebt jede Schwerkraftkanone so, dass ihre Startplattform genau dort liegt, wo Kristall, Computer, Lampen und Schwerkraftfeld stehen.
- Sie versteckt die Sonde bis zum Schuss.

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
- **Bauteile ausrichten:** Die DLL misst die kopierten Spiel-Bauteile aus und richtet sie aus (`GameProps.cs`).
- **Echte Sonde schützen:** Die DLL verhindert, dass die Kopie die echte Nomai-Sonde abfeuert.
- **Der Rest** (Bedingungen, Logbuch, Schalter) läuft über normale New-Horizons-Konfigurationen.

## Ausrichtung der Kanonen

Die Fokuskanonen zielen entlang der Y-Achse ihres Körpers, und ihr Dreieck kreist in der Ebene senkrecht dazu. Alle Körper dieser Mod haben weder Achsneigung noch Eigendrehung, deshalb zeigen die vier Kanonen immer in dieselbe Richtung.

In welche Richtung der Lauf der Vanilla-Sondenkanone zeigt, ist nirgends dokumentiert. Die DLL misst es deshalb im Spiel: Die Start-Effekte der echten Kanone sitzen an ihrer Mündung. Danach dreht sie die Kopie so, dass ihr Lauf parallel zu den Fokuskanonen steht. Das Ergebnis steht im OWML-Log („Lauf der Sondenkanone (lokal): …“). Schaltest du „Hauptkanone automatisch ausrichten“ aus, gilt die Drehung `AIM_OPC` aus `tools/isae_build.py`.

## Für Entwickler

```bash
pip install numpy pillow jsonschema lxml
python tools/isae_texts.py Zeki.ISAE        # Nomai-Texte
python tools/isae_build.py Zeki.ISAE        # Körper, System, Bilder, Manifeste
python tools/nh_validate.py Zeki.ISAE       # Schemas, Logbuch, Bedingungen, Platzierung
cd Zeki.ISAE.Source && dotnet build -c Release   # baut ZekiISAE.dll und kopiert sie nach Zeki.ISAE
```

Das Logbuch (`planets/shiplogs/ISAE.xml`) ist handgeschrieben. Der Validator erkennt auch Bedingungen, die von Interaktionsvolumen oder vom C#-Code gesetzt werden.

## Wichtiger Testhinweis

Alle Dateien sind gegen die offiziellen New-Horizons-Schemas geprüft, die DLL baut ohne Warnungen gegen die echten Spielbibliotheken, und die Mechaniken habe ich am New-Horizons-Quellcode nachvollzogen. **Ich konnte die Mod nicht selbst in Outer Wilds starten.** Unsicher sind vor allem:

- ob die automatische Ausrichtung die Mündung richtig erkennt (das Log zeigt den Messwert),
- ob alle Teile der kopierten Kanone sauber mitgeladen werden,
- ob Startplattform und Bauringe richtig vermessen werden (das Log zeigt die Werte),
- wie die schwebenden Schwerkraftkanonen von unten aussehen (im Spiel stehen sie auf Fels),
- das Timing und die Kameraführung im Finale.

Am einfachsten passt du das mit dem Debug-Modus von New Horizons (Taste P zeigt die Position unter dem Fadenkreuz) und Unity Explorer an.
