# -*- coding: utf-8 -*-
"""
Ship log of "Das Dornenlabyrinth" (Zeki.Dornenlabyrinth): planets/shiplogs/Treibsamen.xml (system SolarSystem, on the
Treibsamen). One curiosity; every entry below it is linked to another by a rumor with a SourceID, so nothing stands
alone in rumor mode. Writes the entry pictures as well.

Usage:  python tools/labyrinth_shiplog.py [path/to/Zeki.Dornenlabyrinth]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verdornt_shiplog as vs  # noqa: E402  (the XML writer)
from verdornt_shiplog import entry, fact, rumor  # noqa: E402

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Dornenlabyrinth"))

# room type -> (fact id, text); the Herzkammer has its own entry, the Vorhof too
ROOMS = {
    "Dornengang": "Ein gewöhnlicher Raum voller Ranken, mit mehreren Knoten und Samen.",
    "Dornenwald": "Die Ranken stehen hier so dicht wie Bäume. Zwischen ihnen bleiben nur schmale Lücken.",
    "Hitzekammer": "Eine glühende Kammer voller Samen, die alle in dieselbe Kammer zurückführen. Mit jeder Runde wird es heißer. Nur der eine große Knoten führt hinaus.",
    "Frostkammer": "Eine eiskalte Kammer mit festen Wasserkristallen. Ein Anglerfisch ist im Eis eingefroren. Die Kälte bremst jede Bewegung.",
    "Nest": "Ein Anglerfisch-Nest: dunkler, roter Nebel, und es leben Anglerfische darin.",
    "Samenkammer": "Ein Raum voller Baby-Samen. Jeder führt woanders hin.",
    "Nebelkammer": "So dichter Nebel, dass man die Knoten nur an ihrem Licht erkennt.",
    "Leere": "Ein riesiger, fast dunkler Raum. Ganz weit weg leuchtet ein einziger Knoten.",
    "Stroemung": "Eine Strömung treibt alles quer durch den Raum.",
    "Echokammer": "Hier rufen mehrere Signale namens „Echo“. Nur eines davon sitzt an einem Knoten.",
    "Wrack": "Die Trümmer eines Hearthianer-Schiffs treiben durch den Raum, daneben ein Nomai-Skelett.",
    "Spiegelkammer": "Fast jeder Ausgang führt in eine weitere Spiegelkammer, und dort verliert man den Weg zum Herz. Nur einer führt hinaus.",
    "Herzpfad": "Lila Nebel und Wegmarken. Hier ist man dem Herz nahe.",
}


def fid(room):
    return f"ZEKIDL_{room.upper()}_FOUND"


LOG = (
    entry("ZEKIDL_TREIBSAMEN", "Der Treibsamen", [
        fact("ZEKIDL_TREIBSAMEN_SIGNAL",
             "Auf der Frequenz Dornenrufe ruft etwas zwischen Giant's Deep und Dark Bramble: ein einzelner Dornensamen, der um die Sonne treibt."),
        fact("ZEKIDL_TREIBSAMEN_FOUND", "Der Treibsamen ist nur ein großer Knoten mit grünlichem Licht. Man kann hineinfliegen."),
    ], [
        entry("ZEKIDL_VORHOF", "Der Vorhof", [
            fact("ZEKIDL_VORHOF_FOUND",
                 "Hinter dem Treibsamen liegt ein Vorhof aus Ranken mit fünf Knoten. Von hier geht es tiefer hinein oder durch die Wand wieder hinaus."),
        ]),
        entry("ZEKIDL_FARBEN", "Die Farben der Knoten", [
            rumor("ZEKIDL_FARBEN_RUMOR", "Eine Notiz im Vorhof", "Im Vorhof treibt ein Floß mit einer Notiz und einer Laterne.", "ZEKIDL_VORHOF"),
            fact("ZEKIDL_FARBE_GRUEN", "Ein grüner Kranz führt zurück in den Vorhof, und von dort geht es hinaus."),
            fact("ZEKIDL_FARBE_ROT", "Ein roter Kranz führt in ein Anglerfisch-Nest."),
            fact("ZEKIDL_FARBE_GELB", "Ein gelber Kranz führt in eine echte Dimension von Dark Bramble. Zurück geht es nur durch Dark Bramble."),
            fact("ZEKIDL_FARBE_LILA", "Ein lila Kranz führt einen Schritt näher an das Innere des Labyrinths."),
        ]),
        entry("ZEKIDL_RAEUME", "Die Räume des Labyrinths", [
            rumor("ZEKIDL_RAEUME_RUMOR", "Jedes Mal ein anderer Raum",
                  "Die Knoten des Vorhofs führen in Räume, die jedes Mal anders aussehen, und immer tiefer hinein.", "ZEKIDL_VORHOF"),
        ] + [fact(fid(r), t) for r, t in ROOMS.items()]),
        entry("ZEKIDL_GNEIS", "Gneis", [
            rumor("ZEKIDL_GNEIS_RUMOR", "Ein Hearthianer im Samen",
                  "Die Notiz im Vorhof ist von Gneis unterschrieben, einem Hearthianer, der mit seinem Schiff in den Samen geflogen ist.",
                  "ZEKIDL_FARBEN"),
            fact("ZEKIDL_GNEIS_WRACK",
                 "Gneis ist durch einen roten Knoten geflogen, und ein Anglerfisch hat sein Schiff zerbissen. Danach ist er mit dem Anzug weitergeflogen."),
            fact("ZEKIDL_GNEIS_HERZPFAD", "Gneis hat das Herz gefunden. Er wollte es hinausbringen und die Sonne noch einmal sehen."),
        ]),
        entry("ZEKIDL_HERZ", "Das Bramble-Herz", [
            rumor("ZEKIDL_HERZ_RUMOR", "Etwas schlägt im Inneren",
                  "Gneis glaubt, dass im Inneren des Labyrinths etwas schlägt. Die lila Knoten führen dorthin.", "ZEKIDL_FARBEN"),
            rumor("ZEKIDL_HERZ_RUMOR_SINGT", "Das Herz singt",
                  "Neun lila Knoten führen vom Vorhof zum Herz. Das Herz singt, und die Anglerfische werden still, wenn sie es hören.", "ZEKIDL_GNEIS"),
            fact("ZEKIDL_HERZ_FOUND", "In einer Kammer aus lila Licht schwebt das Bramble-Herz in einem Nest aus Wurzeln. Der einzige Ausgang ist grün."),
            fact("ZEKIDL_HERZ_GENOMMEN", "Ich habe das Bramble-Herz genommen."),
            fact("ZEKIDL_HERZ_BLUTET", "Seit ich das Herz trage, blutet das Labyrinth: Jeder Knoten ist rot, nur die grünen nicht."),
            fact("ZEKIDL_HERZ_SINGT", "Draußen singt das Herz. Die Anglerfische hören es und jagen niemanden mehr, bis die Schleife endet."),
        ]),
    ], curiosity=True),
)

# rumor mode: far below the vanilla cards (the DLL moves the group further if it still overlaps)
ENTRIES = {"ZEKIDL_TREIBSAMEN": (0, -3000), "ZEKIDL_VORHOF": (-500, -3350), "ZEKIDL_FARBEN": (0, -3550), "ZEKIDL_RAEUME": (-650, -3800),
           "ZEKIDL_GNEIS": (500, -3800), "ZEKIDL_HERZ": (150, -4150)}
TINTS = {"ZEKIDL_TREIBSAMEN": (140, 230, 130), "ZEKIDL_VORHOF": (170, 220, 160), "ZEKIDL_FARBEN": (255, 220, 120), "ZEKIDL_RAEUME": (150, 190, 140),
         "ZEKIDL_GNEIS": (220, 170, 120), "ZEKIDL_HERZ": (190, 110, 255)}


def entry_art(eid, seed):
    """A thorn ball with the entry's tint, ringed by the four colours of the labyrinth."""
    import schleier_build as sb
    from PIL import ImageDraw
    rnd = random.Random(seed)
    tint = TINTS[eid]
    img = sb.starfield(512, seed, tint=tint)
    d = ImageDraw.Draw(img)
    c = 256
    for k, col in enumerate(((220, 60, 50), (90, 230, 110), (240, 210, 70), (170, 90, 255))):
        a = math.tau * k / 4 + 0.4
        x, y = c + 175 * math.cos(a), c + 175 * math.sin(a)
        d.ellipse([x - 28, y - 28, x + 28, y + 28], outline=col + (255,), width=7)
    for _ in range(22):
        a = rnd.uniform(0, math.tau)
        r1, r2 = rnd.uniform(40, 90), rnd.uniform(140, 230)
        d.line([(c + r1 * math.cos(a), c + r1 * math.sin(a)), (c + r2 * math.cos(a + 0.3), c + r2 * math.sin(a + 0.3))],
               fill=(70, 55, 40, 255), width=rnd.randint(5, 12))
    d.ellipse([c - 70, c - 70, c + 70, c + 70], fill=tint + (255,), outline=(255, 255, 240, 255), width=5)
    return img


def main():
    vs.MOD = MOD
    vs.write("Treibsamen.xml", "ZEKIDL_TREIBSAMEN_KOERPER", "Logbuch: der Treibsamen und das Dornenlabyrinth", LOG)
    import schleier_build as sb
    sb.MOD = MOD
    for k, eid in enumerate(ENTRIES):
        sb.save(entry_art(eid, 300 + k), f"planets/assets/shiplog/entries/{eid}.png")


if __name__ == "__main__":
    main()
