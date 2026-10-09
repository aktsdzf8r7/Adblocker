# Die Aussendungseinheit

*Eine New-Horizons-Mod für das normale Sonnensystem von Outer Wilds.*

Seit Beginn der Schleife meldet dein Schiff eine fremde Nomai-Energiesignatur. Zwischen der Sonne und Timber Hearth, weit über der Bahnebene der Planeten, kreist eine zweite Orbitale Sondenkanone: die **Interstellare Sonden Aussendungseinheit**. Drei kleine Schwerkraftkanonen umkreisen sie im Dreieck, und alle vier zielen in dieselbe Richtung.

Wenn du nichts tust, endet diese Schleife nicht mit einer Supernova. Die Einheit entzieht der sterbenden Sonne ihre ganze Energie. Die Sonne schrumpft, bis sie erlischt, und dann heißt es:

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
| Dauer des Energieentzugs | 45 s | Wie lange die Sonne am Ende der Schleife schrumpft (10–180 s). |

## Die Geschichte (Spoiler)

Der Nomai **Sedum** half beim Bau der Orbitalen Sondenkanone. Ihm war klar, dass das Auge vielleicht gar nicht in diesem kleinen System liegt. Er entwarf deshalb eine Kanone, die Sonden zu *anderen Sternen* schießen kann. Sie braucht mehr Energie, als ein lebender Stern hergibt, also soll sie warten, bis die Sonne stirbt, und ihr dann alles nehmen. Pye verbot den Entwurf. Sedum baute ihn trotzdem.

Seine Helferin **Linum** prüfte die Rechnungen und fand den Fehler: Ohne Supernova gibt es keine Energie für das Projekt auf dem Aschezwilling. Ohne Projekt gibt es keine Schleife, und wer in ihr gefangen ist, kehrt nie zurück. Linum hinterließ eine Anleitung zum Abschalten.

## Komplettlösung (Spoiler)

1. **Signal finden:** Im Signalskop gibt es die neue Frequenz *Energiesignaturen*. Die Quelle ist die Aussendungseinheit. Im Logbuch steht sie ab dem Start als Gerücht.
2. *(Optional)* **Hinweis in der echten Sondenkanone:** Im Kontrollmodul der Orbitalen Sondenkanone über Giant's Deep steht ein neuer Computer mit Sedums Notiz.
3. **Kontrollmodul der Aussendungseinheit:** Ein Computer zeigt den Zustand der Einheit, ein Recorder enthält Linums Warnung und die Anleitung.
4. **Die drei Fokuskanonen** Alpha, Beta und Gamma kreisen 340 m um die Hauptkanone. Auf jeder steht neben der Schwerkraftkanone ein leuchtender Kristall, der **Phasenkoppler**. Interaktion: *Phasenkoppler trennen*. Der Kristall zerspringt und sein Licht erlischt.
5. Sind alle drei Koppler getrennt, erscheint im Kontrollmodul der **Hauptschalter** mit einer Wegmarke. Interaktion: *Aussendungseinheit abschalten*. Der Energiekern erlischt.

Das Abschalten ist dauerhaft (im Spielstand gespeichert). Danach endet jede Schleife wieder ganz normal mit der Supernova. Getrennte Koppler bleiben ebenfalls über Schleifen hinweg getrennt.

Gegen Ende der Schleife (5 Minuten vorher) warnt das Schiff noch einmal.

## Wie die Kanone entstanden ist (ehrlich)

**Eine heile, frei bearbeitbare Orbitale Sondenkanone gibt es nicht öffentlich.** Ich habe GitHub und die Outer-Wilds-Mod-Datenbank durchsucht (über 500 Pfade aus veröffentlichten New-Horizons-Mods ausgewertet). Mods wie *EyeWitness* fügen der Vanilla-Kanone nur Texte hinzu, andere löschen sie. Ein eigenständiges Modell im modernen Vessel-Stil existiert nirgends. Dafür bräuchte man ein selbst gebautes Unity-Asset-Bundle.

Die Aussendungseinheit kopiert deshalb beim Laden **die komplette Kanone aus dem Spiel selbst** (`OrbitalProbeCannon_Body/Sector_OrbitalProbeCannon`: Nabe, Lauf, Kontroll- und Startmodul). Entfernt werden die Vanilla-Texte und das Orb-Interface; an ihre Stelle kommen die neuen Texte. Die Fokuskanonen sind Kopien der Schwerkraftkanone von Brittle Hollow. Weil es eine Kopie des Originals ist, trägt das Startmodul dieselben Schäden wie im Spiel.

Damit die Kopie der echten Nomai-Sonde nicht in die Quere kommt, schaltet die DLL jede Startsteuerung der Sondenkanone ab, die nicht zur Original-Kanone gehört.

## Was die DLL macht

New Horizons kann vieles, aber nicht „Sonne schrumpft statt Supernova“. Dafür gibt es den C#-Teil (`Zeki.ISAE.Source`):

- Ein Harmony-Patch auf `SunController.OnTriggerSupernova` ersetzt die Supernova durch einen Energieentzug, solange die Einheit nicht abgeschaltet ist. Die Sonne schrumpft, ihr Licht wird schwächer, dann erlischt sie.
- Danach setzt die DLL die Bedingung `ZEKISAE_UNIVERSUM_ENDET` und der Spieler stirbt. New Horizons zeigt dann den Game-Over-Text aus `addon-manifest.json` und den Abspann.
- Während des Entzugs leuchten Strahlen aus allen vier Kanonen (Bedingung `ZEKISAE_ENTZUG`).
- Die Bedingungen, das Logbuch und die Schalter laufen über normale New-Horizons-Konfigurationen.

## Feinabstimmung: Ausrichtung der Kanonen

Die Fokuskanonen stehen auf dem Nordpol ihrer Felsen und zielen deshalb entlang der Welt-Y-Achse. Ihr Dreieck kreist in der Ebene senkrecht dazu. Alle Körper dieser Mod haben weder Achsneigung noch Eigendrehung, deshalb zeigen die vier Kanonen immer in dieselbe Richtung.

In welche Richtung der Lauf der Vanilla-Sondenkanone in ihrem eigenen Koordinatensystem zeigt, ist nirgends dokumentiert. Falls die Hauptkanone im Spiel nicht parallel zu den Fokuskanonen steht, ändere `AIM_OPC` in `tools/isae_build.py` (Euler-Winkel in Grad) und baue neu. Alternativ kannst du direkt die `rotation` von `ISAE_Hauptkanone` in `planets/ISAE.json` anpassen. Ein Lauf entlang der lokalen Z-Achse braucht zum Beispiel `(-90, 0, 0)`. `AIM_GRAV_YAW` dreht die Fokuskanonen um ihre Schussachse.

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

- die Laufrichtung der kopierten Kanone (siehe oben),
- ob alle Teile der kopierten Kanone sauber mitgeladen werden,
- Größe und Bodenhöhe der Schwerkraftkanonen auf den Felsen,
- wie die Sonne bei sehr kleiner Größe aussieht.

Am einfachsten passt du das mit dem Debug-Modus von New Horizons (Taste P zeigt die Position unter dem Fadenkreuz) und Unity Explorer an.
