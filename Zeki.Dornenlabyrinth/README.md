# Das Dornenlabyrinth

*Eine New-Horizons-Mod für Outer Wilds. Version 0.1.0.*

Zwischen Giant's Deep und Dark Bramble treibt ein einzelner Dornensamen um die Sonne: der **Treibsamen**. Er ruft auf der Frequenz *Dornenrufe*. Wer hineinfliegt, landet in einem **unendlichen Labyrinth** aus Bramble-Dimensionen.

Das Labyrinth ist **fest**. Es hat in jeder Schleife und bei jedem Spielstand dieselbe Form. Wer sich einen Weg merkt, findet ihn wieder, und wer einen Weg weitergibt, gibt ihn allen weiter.

Vor dir war schon jemand hier: **Gneis**, ein Hearthianer, der mit seinem Schiff in den Samen geflogen ist. Seine Notizen treiben auf kleinen Flößen mit Laternen durch das Labyrinth.

## Installation

1. [New Horizons](https://outerwildsmods.com/mods/newhorizons/) im Mod Manager installieren.
2. Den Ordner `Zeki.Dornenlabyrinth` in den OWML-Mod-Ordner kopieren (`…/OWML/Mods/Zeki.Dornenlabyrinth`).
3. Spiel starten.

Das DLC ist nicht nötig. Die Mod läuft neben *Verdornt*, *Die Aussendungseinheit* und dem *Schleiersystem*.

## Die Farben

Um besondere Knoten liegt ein leuchtender **Farbkranz**. Normale Knoten haben einen schwachen, graugrünen.

| Farbe | Wohin der Knoten führt |
|---|---|
| normal | in einen Raum eines zufälligen Typs, tiefer hinein |
| **Rot** | in ein **Anglerfisch-Nest** |
| **Grün** | zurück in den **Vorhof**. Von dort geht es durch die Wand hinaus. |
| **Gelb** | in eine **echte Dimension von Dark Bramble**, zum Beispiel Hub, Rettungskapsel, Pionier oder Vessel. Zurück geht es nur durch Dark Bramble. |
| **Lila** | einen Schritt näher an das **Bramble-Herz**. Neun lila Knoten führen vom Vorhof bis zum Herz. |

**Durch die Wand zurück:** Wer aus einem Raum durch die Nebelwand fliegt, kommt aus dem Knoten heraus, durch den er hereinkam. Das klappt bis zu 64 Räume weit. Aus dem Vorhof geht es durch die Wand hinaus zum Treibsamen.

## Die Räume

Es gibt erwachsene Knoten und Baby-Samen. Beide führen weiter. Beim Betreten zeigt eine Meldung den Raum und seine Tiefe.

| Raum | Was dort ist |
|---|---|
| Vorhof | Start und Ausgang. Gneis' erste Notiz erklärt die Farben. |
| Dornengang | der gewöhnliche Raum |
| Dornenwald | sehr dichte Ranken, enge Lücken |
| **Hitzekammer** | Sechs Samen führen alle in eine weitere Hitzekammer. Mit jeder Runde steigt die **Hitzestufe**, der Schaden beträgt 4 × Stufe pro Sekunde. Der eine große Knoten ist der kühle Ausweg. |
| **Frostkammer** | feste Wasserkristalle, ein eingefrorener Anglerfisch, ein Anglerfisch-Skelett im Eisblock und ein Nomai-Skelett. Die Kälte bremst und lässt das Visier beschlagen. |
| Anglerfisch-Nest | roter Nebel und zwei lebende Anglerfische |
| Samenkammer | acht Baby-Samen, jeder führt woandershin |
| Nebelkammer | so dichter Nebel, dass man die Knoten nur am Licht erkennt |
| Leere | riesig, fast dunkel, mit einem einzigen fernen Knoten |
| Strömungskammer | Eine Strömung treibt dich quer durch den Raum. |
| Echokammer | vier Signale „Echo“ auf *Dornenrufe*. Nur eines sitzt an einem Knoten. |
| Wrackkammer | Gneis' zerbissenes Schiff, ein Nomai-Skelett und eine Notiz |
| Spiegelkammer | Fast jeder Ausgang führt in eine weitere Spiegelkammer, und dort verliert man den Weg zum Herz. Nur einer führt hinaus. |
| Herzpfad | lila Nebel und Gneis' letzte Notiz |
| Herzkammer | das Bramble-Herz in einem Nest aus Wurzeln. Der einzige Ausgang ist grün. |

## Das Bramble-Herz

Im Herz des Labyrinths schwebt ein pulsierender lila Samenkern. Man kann ihn nehmen.

- **Das Labyrinth blutet.** Für den Rest der Schleife ist jeder Knoten rot, außer den grünen. Grün bleibt der Weg nach Hause.
- **Das Herz singt.** Sobald du mit dem Herz draußen bist, jagt kein Anglerfisch im ganzen System mehr, bis die Schleife endet. Das gilt auch in Dark Bramble.
- Beim nächsten Schleifenbeginn liegt das Herz wieder an seinem Platz. Was im Logbuch steht, bleibt.

## Kurzer Weg

1. Signalskop auf *Dornenrufe* stellen und dem Signal „Treibsamen“ folgen. Es liegt außerhalb der Bahn von Giant's Deep.
2. Im Vorhof die Notiz auf dem Floß lesen.
3. Immer dem **lila** Kranz folgen. Spiegelkammern und Hitzekammern meiden.
4. Nach neun lila Knoten liegt die Herzkammer vor dir. Das Herz nehmen und durch den **grünen** Knoten zurück in den Vorhof fliegen, dann durch die Wand hinaus.

## Zum Ausprobieren

Wichtig ist, was das OWML-Log schreibt. Die Mod schreibt viel mit, beim Laden und bei jedem Durchflug.

- [ ] Das Signal „Treibsamen“ ist auf *Dornenrufe* zu hören, und der Samen ist auf der Karte zu sehen.
- [ ] Der Treibsamen führt in den Vorhof, und aus dem Vorhof führt die Wand wieder hinaus.
- [ ] Im Log steht `Labyrinth: 15 von 15 Räumen, 74 Knoten, 7 von 7 Dark-Bramble-Dimensionen.`
- [ ] Jeder Knoten hat einen Farbkranz, und die Farben passen zur Tabelle.
- [ ] Durch die Wand zurück: Man kommt aus dem Knoten heraus, durch den man kam.
- [ ] Die Hitzestufe steigt in der Hitzekammer (Meldung „HITZE STUFE n“) und fällt beim Verlassen.
- [ ] Gelbe Knoten führen in Dark Bramble.
- [ ] Mit dem Herz in der Hand: Meldung „DAS LABYRINTH BLUTET“, und alle Kränze außer Grün sind rot.
- [ ] Draußen mit dem Herz: Meldung „DAS HERZ SINGT“, und Anglerfische in Dark Bramble jagen nicht mehr.
- [ ] Die Logbuch-Karten liegen nicht über denen des Spiels.

Falls etwas nicht greift, bleiben die Knoten bei dem Ziel, das New Horizons ihnen gibt, nämlich dem Vorhof. Steckenbleiben kann man also nicht.
