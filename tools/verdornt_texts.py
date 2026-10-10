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

# ------------------------------------------------------------------ Timber Hearth: the crashed seed
text("Absturz_Rinde.xml", "Nomai-Schrift auf einem Computer am Absturzsamen (Timber Hearth)", chain(
    "Tansy: Wer dies liest, hat den Samen gefunden. Er ist nicht gewachsen – er wurde geworfen.",
    "Tansy: Wir haben ihn auf den Stern gezielt, den das Vessel verlassen hat. Der Flug dauert länger als jedes Leben.",
    "Tansy: Im Samen wartet ein Strudel. Er führt zu uns. Hab keine Angst vor den Dornen. Sie gehören hierher – wir nicht.",
), [("ZEKIVD_ABSTURZ_NOMAI", [1, 2])])

# ------------------------------------------------------------------ the arrival chamber
text("Ankunft_Tansy.xml", "Computer in der Ankunftskammer", chain(
    "Tansy: Ankunftskammer. Wer hier erwacht, ist durch meinen Samen gekommen.",
    "Tansy: Der kleine Samen dort führt hinaus nach Erstling. Unser Lager ist nicht weit.",
), [("ZEKIVD_TANSY_WURF", [1])])

# ------------------------------------------------------------------ the camp: three recorders
text("Lager_Hyssop.xml", "Hyssops Aufzeichnung im Lager", chain(
    "Hier spricht Hyssop. Das Vessel ist in den Dornen zerschellt. Wir drei wollten zu den Rettungskapseln.",
    "Ein alter, dunkler Samen tief in den Dornen hat uns hindurchgezogen. Wir kamen hier heraus, aus einem kleinen Samen – Lichtjahre entfernt.",
    "Dieses System ist überwuchert. Vier Planeten, und dort, wo die Sonne sein sollte, ein Käfig aus Dornen um einen gefangenen Stern.",
    "Ich glaube, hier hat die Dornenwelt angefangen. Was wir zu Hause „die Dornen“ nannten, ist nur ein einzelner Samen von hier.",
), [("ZEKIVD_FALSCH_ABGEBOGEN", [1, 2]), ("ZEKIVD_URSPRUNG", [3, 4])])
text("Lager_Rue.xml", "Rues Aufzeichnung im Lager", chain(
    "Rue: Ich habe die Knoten von Erstling kartiert. Sie führen in Dimensionen, und die Dimensionen zu anderen Planeten.",
    "Rue: Die Dornen sind ein Netz. Wer den richtigen Weg kennt, braucht kein Schiff.",
    "Rue: Ich habe Wegmarken geritzt. Folgt ihnen. Und flieht vor dem Licht in der Kälte – es ist kein Stern.",
    yarrow("Ich habe die Wegmarken nachgezählt. Es sind mehr, als Rue geritzt hat."),
    "Rue: Yarrow, du zählst immer falsch.",
), [("ZEKIVD_NETZ_RUE", [1, 2]), ("ZEKIVD_KAELTE_HINWEIS", [3])])
text("Lager_Tansy.xml", "Tansys Aufzeichnung im Lager", chain(
    "Tansy: Ich habe die Warp-Türme nach den Plänen von Ember Twin gebaut. Einer steht auf jedem Planeten.",
    "Tansy: Die Röhren sind meine Erfindung: Eine Murmel rollt in eine Mulde, und der Turm erwacht. Einfach genug für jeden.",
    "Tansy: Der Turm von Erstling führt zum Ausguck. Von dort sieht man, was wir hier gefunden haben.",
), [("ZEKIVD_LAGER_RUMOR_TURM", [2]), ("ZEKIVD_TUERME", [1])])

# ------------------------------------------------------------------ the tower, the cave, the Ausguck
text("Turm_Erstling.xml", "Computer am Warp-Turm von Erstling", chain(
    "WARP-TURM ERSTLING. Gegenstück: Ausguck.",
    "Zustand: schläft, bis die Murmel in der oberen Mulde liegt.",
    "Weitere Türme: Glutdorn, Nebelranke, Hohlsamen. Jeder mit eigener Röhre.",
), [("ZEKIVD_TUERME", [3])])
text("Hoehle_Kern.xml", "Computer in der Kernhöhle hinter dem Lagertor", chain(
    "Hyssop: Unter dem Eis von Erstling lag dieser Kern – der Samenkern, aus dem der ganze Planet gewachsen ist.",
    "Hyssop: Jeder Planet hier trägt einen. Und alle gleichen einem Kern, den wir nur aus der Ferne messen konnten: dem Mutterkern im Herzdorn.",
    "Hyssop: Der Mutterkern hat jeden Samen dieses Systems geworfen. Vielleicht auch den Samen, der zu unseren Dornen wurde.",
    "Hyssop: Vor dem Herzdorn steht ein Schrein mit vier Fassungen. Ich bin sicher, dass er die vier Kerne will.",
), [("ZEKIVD_KERN_PLAN", [1, 2]), ("ZEKIVD_MUTTERKERN_RUMOR", [2, 3]), ("ZEKIVD_KERN_SCHREIN_RUMOR", [4])])
text("Ausguck_System.xml", "Computer auf dem Ausguck", chain(
    "AUSGUCK. Blick auf das System, das wir Dornenkranz nennen.",
    "Innen: Herzdorn, der gefangene Stern. Dann Erstling, Glutdorn, Nebelranke, Hohlsamen.",
    "Der Stern lebt noch. Sein Licht fällt durch die Lücken im Geflecht. Die Dornen trinken es.",
    "Hyssop: Ich zähle die Samen, die der Herzdorn hinauswirft. Ich nenne es die Bramblesation. Sie wächst.",
    yarrow("Schlechtes Wortspiel."),
), [("ZEKIVD_SYSTEM_NAMEN", [1, 2]), ("ZEKIVD_HERZDORN_RUMOR", [3]), ("ZEKIVD_BRAMBLESATION", [4])])

# ------------------------------------------------------------------ trail markers in the thorn network
text("Splitter_Rue.xml", "Rues Computer im Splittergang", chain(
    "Rue: Splittergang. Nur Eis. Kein Weg weiter – noch nicht.",
    "Rue: Die anderen Planeten erreicht man über den Kreuzweg. Sein Knoten wächst noch zu.",
), [("ZEKIVD_NETZ_RUE", [2])])
text("Kaelte_Hinweis.xml", "Computer im Kältenest", chain(
    "Rue: Kältenest. Das Licht hier gehört einem Fisch. Leise sein.",
    "Tansy: Der Ausguck liegt hoch über der Bahn der Planeten. Ohne Schiff: nur über den Turm von Erstling.",
), [("ZEKIVD_KAELTE_HINWEIS", [1])])


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
