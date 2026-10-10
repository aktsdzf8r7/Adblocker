# -*- coding: utf-8 -*-
"""
Nomai texts of "Verdornt" (Zeki.Verdornt). Writes planets/text/*.xml.

Four Nomai write here: Hyssop, Rue, Tansy - and Yarrow, who does not exist (spec 3.1). Yarrow's lines are made
with yarrow(); the reveal comes in stage 3, so in stage 1 his lines must read like an ordinary fourth crew member.

Usage:  python tools/verdornt_texts.py [path/to/Zeki.Verdornt]
"""
import os
import sys
from xml.sax.saxutils import escape

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Verdornt"))
SCHEMA = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="https://raw.githubusercontent.com/Outer-Wilds-New-Horizons/new-horizons/main/NewHorizons/Schemas/text_schema.xsd"'
TEXTS = {}
YARROW_LINES = []   # every line Yarrow "wrote", for the reveal in stage 3


def text(name, comment, blocks, reveals=()):
    TEXTS[name] = (comment, blocks, list(reveals))


def chain(*texts):
    return [(i + 1, i if i else None, t) for i, t in enumerate(texts)]


def yarrow(line):
    """A line signed by Yarrow, the fourth Nomai who was never there."""
    YARROW_LINES.append(line)
    return "Yarrow: " + line


# ------------------------------------------------------------------ the camp's reactive core computer (four states)
text("Lagerkern_Start.xml", "Lagerkern im Lager auf Erstling: Grundzustand", chain(
    "LAGERKERN. Lager auf Erstling. Bewohner: Hyssop, Rue, Tansy, Yarrow.",
    "Letzter Eintrag vor 281 044 Jahren. Seitdem: Stille.",
    "Rücksamen: bereit. Warp-Turm: schläft. Kernhöhle: verschlossen.",
))
text("Lagerkern_Ankunft.xml", "Lagerkern: nach der Ankunft des Spielers", chain(
    "LAGERKERN. Unbekannte Lebensform durch den Ankunftssamen eingetroffen.",
    "Herkunft: das System, zu dem Tansys Samen geflogen ist. Der Samen ist angekommen.",
    "Empfehlung: den Warp-Turm wecken. Die Murmel liegt in ihrer Röhre am Fuß des Turms.",
    "Der Rücksamen in seiner Kupferwiege führt dorthin zurück, woher du kamst.",
), [("ZEKIVD_LAGER_RUMOR_TURM", [3]), ("ZEKIVD_RUECKSAMEN", [4])])
text("Lagerkern_Turm.xml", "Lagerkern: nachdem der Warp-Turm geweckt wurde", chain(
    "LAGERKERN. Warp-Turm Erstling: wach. Ziel: der Ausguck über dem Kranz.",
    "Vom Ausguck aus zeigt das große Becken das ganze System.",
    "Kernhöhle: verschlossen. Die Murmel des Tores liegt am Rand der Plattform.",
), [("ZEKIVD_TURM_WACH_FACT", [1])])
text("Lagerkern_Kern.xml", "Lagerkern: nachdem der Planetenkern von Erstling genommen wurde", chain(
    "LAGERKERN. Planetenkern Erstling: aus der Höhle entnommen.",
    "Hyssop: Jeder Planet hier trägt einen solchen Kern. Alle stammen vom selben Herzen.",
    "Hyssop: Bringt man alle vier zum Kernschrein vor dem Herzdorn, öffnet sich der Weg nach innen.",
), [("ZEKIVD_KERN_SCHREIN_RUMOR", [3])])


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
    print(f"{len(TEXTS)} Nomai texts written (Verdornt)")


if __name__ == "__main__":
    write_all()
