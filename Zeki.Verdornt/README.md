# Verdornt

*Eine New-Horizons-Mod für Outer Wilds. Version 0.1.0, Etappe 1 von 3: „Ankunft“.*

Zu Beginn der Schleife ist ein riesiger Dornensamen auf Timber Hearth eingeschlagen, gleich neben dem alten Krater. Er raucht noch, und er ist offen. Wer hineinfliegt, landet in **Dornenkranz**: einem fremden System, in dem die Dornen alles überwuchert haben. Vier Planeten, und dort, wo die Sonne sein sollte, ein Käfig aus Dornen um einen gefangenen Stern.

Drei Nomai vom Vessel sind in Dark Bramble falsch abgebogen und hier gestrandet: **Hyssop**, **Rue** und **Tansy**. Und dann ist da noch **Yarrow**.

## Installation

1. [New Horizons](https://outerwildsmods.com/mods/newhorizons/) im Mod Manager installieren.
2. Den Ordner `Zeki.Verdornt` in den OWML-Mod-Ordner kopieren (`…/OWML/Mods/Zeki.Verdornt`).
3. Spiel starten.

Das DLC ist nicht nötig. Die Mod läuft neben *Die Aussendungseinheit* und dem *Schleiersystem*.

## Was es in Etappe 1 gibt

- **Der Absturzsamen** auf Timber Hearth, mit Krater, Rauch, einer Absperrung samt Notiz von Hornfels und einer Nomai-Schrift von Tansy.
- **Der Samenschlund:** eine Dimension im Samen mit einem Dornenstrudel. Er zieht dich ins fremde System.
- **Dornenkranz** mit allen Körpern, jeder „wie Dark Bramble, nur anders“:

| Körper | Aussehen |
|---|---|
| Herzdorn | ein gefangener Stern, dessen Licht durch einen Käfig aus Dornen fällt |
| Erstling | Eis-Kristalle auf Rinde |
| Glutdorn | Glutrisse und glühende Dornspitzen |
| Nebelranke | grüner Nebel mit riesigen treibenden Ranken |
| Hohlsamen | ein aufgebrochener Riesensamen mit Kristallen innen |

- **Das Lager auf Erstling:**
  - drei Kuppeln und ein Kernrechner, der auf deinen Fortschritt reagiert
  - drei Aufzeichnungen
  - eine Kernhöhle hinter einem Tor
  - ein Warp-Turm und der Rücksamen nach Hause
- **Murmel-Röhren:** Schau die Murmel an und halte *Interagieren*. Sie folgt deinem Blick durch die Röhre. Lass los, und sie rollt in die nächste Mulde.
  - Am Lagertor: Das Tor öffnet sich.
  - Am Warp-Turm: Der Turm erwacht.
  - Am Lift des Ausgucks: Der Lift fährt hoch oder runter.
- **Der Ausguck** hoch über dem System. Sein Projektionsbecken zeigt das **ganze System**. Der Stein dafür liegt im Lager. Ein zweites Becken im Lager zeigt zurück.
- **Das Dornen-Netz, erster Teil:** Eispforte, Splittergang und Kältenest. Die Wurzeln dort sind echte Dark-Bramble-Ranken aus dem Spiel. Im Kältenest lebt ein Anglerfisch.
- **14 Nomai-Texte** und ein Logbuch mit vier Neugier-Zweigen.

## Komplettlösung Etappe 1 (Spoiler)

1. **Der Samen:** Auf Timber Hearth zum frischen Krater neben dem alten Einschlagkrater fliegen. Durch den Samen hinein.
2. **Der Strudel:** In die Mitte des Strudels fliegen. Du wachst neben einem kleinen Samen auf Erstling auf.
3. **Das Lager:** Es liegt nicht weit vom Ankunftssamen. Lies den Kernrechner in der Mitte.
4. **Der Warp-Turm:**
   1. Rolle die Murmel in der Röhre am Fuß des Turms ganz nach oben. Der Turm erwacht.
   2. Stell dich auf sein Warppad, und du kommst zum Ausguck.
5. **Der Ausguck:** Fahr mit dem Lift aufs Deck, die Röhre ist auf dem Lift. Leg den Stein „System“ ins Becken und sieh dir das ganze System an.
6. **Die Kernhöhle:**
   1. Rolle die Murmel am Rand der Lagerplattform ans Ende ihrer Röhre. Das Tor hebt sich.
   2. Drinnen liegt der **Planetenkern von Erstling**.
7. **Nach Hause:** Interagiere mit dem kleinen Samen in der Kupferwiege im Lager. Oder warte das Ende der Schleife ab: Dann explodiert der gefangene Stern, und du wachst auf Timber Hearth auf.

## Einstellungen

| Einstellung | Standard | Bedeutung |
|---|---|---|
| Filmische Übergänge | an | grüner Nebel beim Durchqueren des Samens |

## Testliste (bitte im Spiel prüfen)

Ich kann Outer Wilds nicht selbst starten. Alles ist gegen die Schemas von New Horizons geprüft, die DLL baut ohne Warnungen, und die Logik hat 17 Unit-Tests. Bitte prüf im Spiel:

- [ ] Der Samen auf Timber Hearth liegt neben dem alten Krater auf dem Boden. Das OWML-Log nennt den Abstand.
- [ ] Hineinfliegen bringt dich in den Samenschlund. Der Strudel wechselt das System.
- [ ] Du wachst im grünen Nebel neben dem Ankunftssamen auf, nicht in ihm.
- [ ] Der Rücksamen im Lager bringt dich zurück nach Timber Hearth.
- [ ] Die Murmeln lassen sich ziehen und rasten ein.
- [ ] Das Tor hebt sich, und der Turm erwacht: Sein Warppad bringt dich zum Ausguck.
- [ ] Der Lift trägt dich mit: Wer auf ihm steht, fährt mit, ohne durchzufallen.
- [ ] Der Kernrechner wechselt seinen Text: nach der Ankunft, nach dem Wecken des Turms, nach dem Nehmen des Kerns.
- [ ] Das Becken auf dem Ausguck zeigt das ganze System.
- [ ] Das Licht von Herzdorn fällt durch den Käfig.
- [ ] Am Ende der Schleife explodiert Herzdorn, und du wachst auf Timber Hearth auf.
- [ ] Die Materialien: Rinde von den echten Dark-Bramble-Ranken, Nomai-Hülle von echten Nomai-Bauten. Das OWML-Log zeigt die Zuordnung.

## Als Nächstes

- **Etappe 2:**
  - Glutdorn, Nebelranke und Hohlsamen zum Erkunden, das ganze Dornen-Netz und alle Warp-Türme
  - dein Schiff im System, samt einer Notiz
  - Ernesto
- **Etappe 3:** Herzdorn, der Mutterkern und die zwei Enden.

## Für Entwickler

```bash
blender -b -P tools/verdornt_models.py -- Zeki.Verdornt   # Blender 4.2: Körper, Lager, Turm, Röhren, Anker
python tools/verdornt_build.py Zeki.Verdornt              # Configs, Texte, Logbuch, placements.json, Bilder
python tools/nh_validate.py Zeki.Verdornt                 # Schemas, Logbuch, Bedingungen, Bramble-Netz
python tools/obj_check.py Zeki.Verdornt/assets/models     # Ausrichtung der Meshes
cd Zeki.Verdornt.Source && dotnet build -c Release        # ZekiVerdornt.dll
dotnet test Zeki.Verdornt.Tests                           # Logik: Übergang, Computer, Röhren
```

Design und Plan stehen in `docs/superpowers/specs/2026-10-10-verdornt-design.md` und `docs/superpowers/plans/2026-10-10-verdornt-etappe1.md`.
