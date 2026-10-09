# -*- coding: utf-8 -*-
"""
Nomai texts of "Die Aussendungseinheit" (Zeki.ISAE). Writes planets/text/*.xml.
Same layout rules as the Schleiersystem texts (see schleier_texts.py).

Usage:  python tools/isae_texts.py [path/to/Zeki.ISAE]
"""
import os
import sys
from xml.sax.saxutils import escape

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.ISAE"))
SCHEMA = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="https://raw.githubusercontent.com/Outer-Wilds-New-Horizons/new-horizons/main/NewHorizons/Schemas/text_schema.xsd"'
TEXTS = {}


def text(name, comment, blocks, reveals=()):
    TEXTS[name] = (comment, blocks, list(reveals))


def chain(*texts):
    return [(i + 1, i if i else None, t) for i, t in enumerate(texts)]


# ------------------------------------------------------------------ the hint inside the vanilla cannon
text("OPC_Sedum.xml", "Computer im Kontrollmodul der Orbitalen Sondenkanone (Hinweis auf die Aussendungseinheit)", chain(
    "Notiz von Sedum: Die Kanone ist fertig. Sie wird das Signal des Auges in diesem System suchen.",
    "Aber dieses System ist klein. Wenn das Auge nicht hier ist, brauchen wir eine Sonde, die zu anderen Sternen fliegt.",
    "Mein Entwurf dafür, die Interstellare Sonden Aussendungseinheit, braucht mehr Energie, als ein lebender Stern hergibt.",
    "Pye hat ihn verboten. Ich baue ihn trotzdem – dort, wo die Sonne am hellsten ist.",
), [("ZEKISAE_SEDUM_PLAN", [1, 2, 3]), ("ZEKISAE_RUMOR", [1, 2, 3, 4])])

# ------------------------------------------------------------------ inside the ISAE control module
text("ISAE_Status.xml", "Computer im Kontrollmodul der Aussendungseinheit", chain(
    "INTERSTELLARE SONDEN AUSSENDUNGSEINHEIT. Zustand: wartend.",
    "Auslöser: Zusammenbruch des Sterns. Sobald er stirbt, wird ihm alle verbleibende Energie entzogen.",
    "Fokuskanonen Alpha, Beta und Gamma: ausgerichtet. Phasenkoppler: verbunden.",
    "Erwarteter Schuss: eine Sonde, schneller als jedes Licht dieses Systems, zu einem fremden Stern.",
    "Erwartete Folgen für dieses System: keine. Der Stern stirbt ohnehin. – Sedum",
), [("ZEKISAE_ZWECK", [1, 2]), ("ZEKISAE_FOKUS_RUMOR", [1, 2, 3])])

text("ISAE_Linum.xml", "Linums Aufzeichnung im Kontrollmodul", chain(
    "Hier spricht Linum. Ich habe Sedums Rechnungen geprüft. Sie stimmen. Aber Sedum hat etwas übersehen.",
    "Auf dem Aschezwilling bauen die anderen ein Projekt, das die Energie der sterbenden Sonne einfängt, um Erinnerungen in die Vergangenheit zu schicken.",
    "Nimmt die Aussendungseinheit diese Energie zuerst, gibt es keine Supernova mehr. Keine Supernova, kein Projekt. Keine Schleife.",
    "Wer in der Schleife gefangen ist, kehrt dann nicht zurück. Das Universum endet – aber er endet vor ihm.",
    "Um sie abzuschalten: Trenne die Phasenkoppler auf allen drei Fokuskanonen. Dann erwacht der Hauptschalter hier im Kontrollmodul.",
), [("ZEKISAE_GEFAHR", [1, 2, 3, 4]), ("ZEKISAE_ANLEITUNG", [1, 2, 3, 4, 5])])

text("ISAE_Hauptschalter.xml", "Wegmarke am Hauptschalter (erscheint, wenn alle Koppler getrennt sind)", [
    (1, None, "Linum: Die Koppler sind getrennt. Nur dieser Schalter hält die Einheit noch wach. Schalte sie ab."),
])

# ------------------------------------------------------------------ the three focus cannons
text("Fokus_Alpha.xml", "Computer auf Fokuskanone Alpha", chain(
    "FOKUSKANONE ALPHA. Aufgabe: den Energiestrom des Sterns bündeln und in die Hauptkanone lenken.",
    "Phasenkoppler: verbunden. Der Kristall am Koppler leuchtet, solange der Strom fließen kann.",
    "Linum: Trenne den Koppler. Wenn der Kristall erlischt, ist Alpha frei.",
), [("ZEKISAE_FOKUS_ZWECK", [1, 2])])

text("Fokus_Beta.xml", "Computer auf Fokuskanone Beta", chain(
    "FOKUSKANONE BETA. Ausrichtung: parallel zur Hauptkanone.",
    "Sedum: Die drei Kanonen bilden ein Dreieck. Nur gemeinsam halten sie den Strom eines ganzen Sterns.",
    "Linum: Dann reicht es, ihnen das Dreieck zu nehmen.",
), [("ZEKISAE_FOKUS_DREIECK", [1, 2, 3])])

text("Fokus_Gamma.xml", "Computer auf Fokuskanone Gamma", chain(
    "FOKUSKANONE GAMMA. Bereit.",
    "Linum: Sedum, wenn du dies je liest: Es tut mir leid.",
    "Linum: Ein Weg zu den Sternen ist nichts wert, wenn dafür alle enden, die ihn gehen könnten. Niemand darf das Ende eines anderen wählen.",
), [("ZEKISAE_LINUM_REUE", [1, 2, 3])])


def write_all():
    out_dir = os.path.join(MOD, "planets", "text")
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith(".xml") and f not in TEXTS:
            os.remove(os.path.join(out_dir, f))
    for name, (comment, blocks, reveals) in TEXTS.items():
        out = ['<?xml version="1.0" encoding="utf-8"?>', f"<!-- {comment} -->", f"<NomaiObject {SCHEMA}>"]
        for bid, parent, t in blocks:
            out.append("  <TextBlock>")
            out.append(f"    <ID>{bid}</ID>")
            if parent:
                out.append(f"    <ParentID>{parent}</ParentID>")
            out.append(f"    <Text>{escape(t)}</Text>")
            out.append("  </TextBlock>")
        if reveals:
            out.append("  <ShipLogConditions>")
            for fact, ids in reveals:
                out += ["    <RevealFact>", f"      <FactID>{fact}</FactID>", f"      <Condition>{','.join(map(str, ids))}</Condition>", "    </RevealFact>"]
            out.append("  </ShipLogConditions>")
        out.append("</NomaiObject>")
        with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + "\n")
    print(f"{len(TEXTS)} Nomai texts written")


if __name__ == "__main__":
    write_all()
