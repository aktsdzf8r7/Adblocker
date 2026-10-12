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


def yarrow_sign(line):
    """A computer entry Yarrow "signed" (computers speak like computers, so his name is a field, not a voice)."""
    YARROW_LINES.append(line)
    return line


def yarrow(line):
    """A line signed by Yarrow, the fourth Nomai who was never there."""
    YARROW_LINES.append(line)
    return "Yarrow: " + line


# ------------------------------------------------------------------ the camp's reactive core computer (four states)
text("Lagerkern_Start.xml", "Lagerkern im Lager auf Erstling: Grundzustand", chain(
    "LAGERKERN. Lager auf Erstling. Bewohner: Hyssop, Rue, Tansy, Yarrow.",
    "Letzter Eintrag vor 281 044 Jahren. Seitdem: Stille.",
    "Rücksamen: bereit. Warp-Turm: schläft. Kernhöhle: verschlossen.",
), [("ZEKIVD_VIER_RUMOR", [1])])
text("Lagerkern_Ankunft.xml", "Lagerkern: nach der Ankunft des Spielers", chain(
    "LAGERKERN. Unbekannte Lebensform durch den Ankunftssamen eingetroffen.",
    "Herkunft: das System, zu dem Tansys Samen geflogen ist. Der Samen ist angekommen.",
    "Empfehlung: den Warp-Turm wecken. Die Murmel liegt in ihrer Röhre am Fuß des Turms.",
    "Rückweg: der Rücksamen in seiner Kupferwiege. Ziel: das Herkunftssystem der Lebensform.",
    "Bewohner des Lagers: Hyssop, Rue, Tansy, Yarrow. Anwesend: keiner.",
), [("ZEKIVD_LAGER_RUMOR_TURM", [3]), ("ZEKIVD_RUECKSAMEN", [4]), ("ZEKIVD_VIER_RUMOR", [5])])
text("Lagerkern_Turm.xml", "Lagerkern: nachdem der Warp-Turm geweckt wurde", chain(
    "LAGERKERN. Warp-Turm Erstling: wach. Ziel: der Ausguck über dem Kranz.",
    "Vom Ausguck aus zeigt das große Becken das ganze System.",
    "Kernhöhle: verschlossen. Die Murmel des Tores liegt am Rand der Plattform.",
    "Bewohner des Lagers: Hyssop, Rue, Tansy, Yarrow. Anwesend: keiner.",
), [("ZEKIVD_TURM_WACH_FACT", [1]), ("ZEKIVD_VIER_RUMOR", [4])])
text("Lagerkern_Kern.xml", "Lagerkern: nachdem der Planetenkern von Erstling genommen wurde", chain(
    "LAGERKERN. Planetenkern Erstling: aus der Höhle entnommen.",
    "Archiv (Hyssop): Jeder Planet trägt einen solchen Kern. Alle stammen vom selben Herzen.",
    "Kernschrein vor dem Herzdorn: 4 Fassungen. Bei 4 eingesetzten Kernen öffnet sich der Weg nach innen.",
    "Bewohner des Lagers: Hyssop, Rue, Tansy, Yarrow. Anwesend: keiner.",
), [("ZEKIVD_KERN_SCHREIN_RUMOR", [3]), ("ZEKIVD_VIER_RUMOR", [4])])

# ------------------------------------------------------------------ Timber Hearth: the crashed seed
text("Absturz_Rinde.xml", "Computer am Absturzsamen (Timber Hearth): das Flugprotokoll des Samens", chain(
    "SAMEN 1 – FLUGPROTOKOLL. Start: Dornenkranz. Ziel: der Stern, den das Vessel verließ.",
    "Antrieb: keiner. Der Samen wurde geworfen, nicht gepflanzt. Werferin: Tansy. Flugzeit: länger als ein Leben.",
    "Ladung: ein Strudel. Er führt zum Lager auf Erstling. Hinweis für Ankömmlinge: Die Dornen gehören dorthin. Wir nicht.",
), [("ZEKIVD_ABSTURZ_NOMAI", [1, 2]), ("ZEKIVD_SCHLUND_RUMOR", [3])])

# ------------------------------------------------------------------ the arrival chamber
text("Ankunft_Tansy.xml", "Computer in der Ankunftskammer", chain(
    "ANKUNFTSKAMMER. Ankunft registriert: eine Lebensform. Weg: Samen 1, geworfen von Tansy in Richtung des Vessel-Systems.",
    "Ausgang: der kleine Samen. Ziel: Erstling. Entfernung zum Lager: gering.",
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
), [("ZEKIVD_LAGER_RUMOR_TURM", [2]), ("ZEKIVD_TUERME", [1]), ("ZEKIVD_AUSGUCK_RUMOR", [3])])

# ------------------------------------------------------------------ the tower, the cave, the Ausguck
text("Turm_Erstling.xml", "Computer am Warp-Turm von Erstling", chain(
    "WARP-TURM ERSTLING. Gegenstück: Ausguck.",
    "Zustand: schläft, bis die Murmel in der oberen Mulde liegt.",
    "Weitere Türme: Glutdorn, Nebelranke, Hohlsamen. Jeder mit eigener Röhre.",
), [("ZEKIVD_TUERME", [3])])
text("Hoehle_Kern.xml", "Computer in der Kernhöhle hinter dem Lagertor", chain(
    "KERNHÖHLE – MESSUNG. Objekt: Samenkern von Erstling. Befund: Aus ihm ist der ganze Planet gewachsen.",
    "Vergleich: Jeder Planet des Systems trägt einen solchen Kern. Alle gleichen einem Kern im Herzdorn: dem Mutterkern.",
    "Mutterkern: Ursprung aller Samen dieses Systems. Wahrscheinlichkeit, dass er auch die Dornen des Vessel-Systems warf: hoch.",
    "Kernschrein vor dem Herzdorn: 4 Fassungen, leer. Erwartete Füllung: 4 Planetenkerne. Auswertung: Hyssop.",
), [("ZEKIVD_KERN_PLAN", [1, 2]), ("ZEKIVD_MUTTERKERN_RUMOR", [2, 3]), ("ZEKIVD_KERN_SCHREIN_RUMOR", [4])])
text("Ausguck_System.xml", "Computer auf dem Ausguck", chain(
    "AUSGUCK. Blick auf das System Dornenkranz.",
    "Körper, von innen: Herzdorn (gefangener Stern), Erstling, Glutdorn, Nebelranke, Hohlsamen.",
    "Herzdorn: Stern aktiv. Licht dringt durch die Lücken im Geflecht. Die Dornen trinken es.",
    "Samenzählung (Hyssop): steigend. Bezeichnung der Zählung: Bramblesation.",
    yarrow_sign("Kommentar zur Bezeichnung: „Schlechtes Wortspiel.“ Eingetragen von: Yarrow."),
), [("ZEKIVD_SYSTEM_NAMEN", [1, 2]), ("ZEKIVD_HERZDORN_RUMOR", [3]), ("ZEKIVD_BRAMBLESATION", [4])])

# ------------------------------------------------------------------ trail markers in the thorn network
text("Splitter_Rue.xml", "Computer im Splittergang", chain(
    "SPLITTERGANG – WEGMARKE. Weiterer Weg: keiner. Noch nicht.",
    "Andere Planeten: über den Kreuzweg. Knoten zum Kreuzweg: wächst noch zu. Kartiert von: Rue.",
), [("ZEKIVD_NETZ_RUE", [2])])
text("Kaelte_Hinweis.xml", "Computer im Kältenest", chain(
    "KÄLTENEST – WARNUNG. Lichtquelle dieser Dimension: ein Anglerfisch. Lautstärke senken.",
    "Ausguck: hoch über der Bahnebene. Erreichbar mit dem Schiff oder über den Warp-Turm von Erstling.",
), [("ZEKIVD_KAELTE_HINWEIS", [1])])


# ------------------------------------------------------------------ 0.2.0: the stations on every planet
# The root lab on Erstling (Hyssop): the overgrown translator.
text("Labor_Hyssop_1.xml", "Wurzellabor auf Erstling: Messreihe 1", chain(
    "WURZELLABOR – MESSREIHE 1. Schwingung der großen Wurzel: gleichmäßig. Muster: wie Stimmen, nicht wie Wind.",
    "Versuchsaufbau: ein Übersetzer an der großen Wurzel. Ziel: hören, was sie sagt. Leitung: Hyssop.",
))
text("Labor_Hyssop_2.xml", "Wurzellabor: Messreihe 2, der verbrambelte Übersetzer", chain(
    "WURZELLABOR – MESSREIHE 2. Zustand des Übersetzers: über Nacht von der Wurzel umwachsen. Er leuchtet grün.",
    "Ausgabe des Übersetzers: Laute, deren Bedeutung niemand kennt. Antwort der Wurzeln: ja.",
    yarrow_sign("Offene Frage, eingetragen von Yarrow: Lassen sie uns nach Hause?"),
), [("ZEKIVD_SPRACHE_RUMOR", [1, 2])])
text("Labor_Hyssop_3.xml", "Wurzellabor: Hinweis zum Übersetzer", chain(
    "WURZELLABOR – HINWEIS. Wer den Übersetzer berührt, dessen Übersetzer hört die einfachsten Wörter.",
    "Weitere Wörter: im Wortarchiv des Kristallobservatoriums auf Hohlsamen. Verwaltet von: Tansy.",
), [("ZEKIVD_OBSERVATORIUM_RUMOR", [2])])

# The Glutwerk on Glutdorn (Hyssop, Rue): heat from the core, the bridge to the node slab.
text("Glutwerk_Hyssop.xml", "Glutwerk auf Glutdorn: Wärmemessung", chain(
    "GLUTWERK – WÄRMEMESSUNG. Temperatur der Schollen: hoch. Quelle: der Kern, nicht die Sonne.",
    "Weg der Wärme: durch die Dornen nach oben. Die Dornen halten die Schollen – und wärmen sie.",
))
text("Glutwerk_Rue.xml", "Glutwerk: die Brücke", chain(
    "GLUTWERK – BRÜCKE. Ziel: die Knotenscholle. Antrieb: die Murmel am Brückenkopf. Erbaut von: Rue.",
    "Knoten auf der Knotenscholle: führt in eine glühende Pforte. Erkundet: bis zur Pforte.",
    "Personal: Hyssop, Wurzellabor in der breitesten Schlucht von Erstling. Angabe: Er hört die Wurzeln.",
), [("ZEKIVD_LABOR_RUMOR", [3])])
text("Glutwerk_Aufzeichnung.xml", "Aufzeichnung im Glutwerk", chain(
    "Rue: Wer das hört: Lass die Murmel nicht in der Mitte liegen. Die Brücke mag nur ganz oder gar nicht.",
    yarrow("Wir haben die Brücke zweimal getestet. Sie hält."),
))

# The drifting station on Nebelranke (Rue): the guardians, and a fish that talks.
text("Treib_Rue_1.xml", "Treibstation auf Nebelranke: Beobachtung der Wächter", chain(
    "TREIBSTATION – BEOBACHTUNG. Die Wächter im Nebel gehorchen den Ranken. Singen die Ranken, schwimmen die Wächter fort.",
    "Zählung der Wächterlichter: steigend.",
))
text("Treib_Rue_2.xml", "Treibstation: Karte", chain(
    "TREIBSTATION – KARTE. Knoten an einer Insel: führt in eine Pforte voller Nebel. Bewachung: keine. Noch nicht.",
    "Außenposten: ein Wärmewerk auf der größten Scholle von Glutdorn. Erbaut von: Hyssop.",
), [("ZEKIVD_GLUTWERK_RUMOR", [2])])
text("Treib_Aufzeichnung.xml", "Aufzeichnung in der Treibstation", chain(
    "Rue: Etwas im Nebel hat mit mir gesprochen. Ein Fisch. Er hat sich vorgestellt, höflich, wie ein Gelehrter.",
    "Rue: Hyssop glaubt mir nicht.",
    yarrow("Ich glaube dir, Rue."),
), [("ZEKIVD_ERNESTO_RUMOR", [1])])

# The crystal observatory on Hohlsamen (Tansy): every note teaches words of the bramble language.
text("Obs_Tansy_1.xml", "Kristallobservatorium: Wortarchiv, Eintrag 1", chain(
    "WORTARCHIV DER DORNENSPRACHE – EINTRAG 1. Form: Laute, keine Zeichen. Wiedergabe: der überwachsene Übersetzer.",
    "Gesichert: „marh“ = Herz. „vrass“ = tragen. „gaar“ = Welten.",
), [("ZEKIVD_SPRACHE_1", [2])])
text("Obs_Tansy_2.xml", "Kristallobservatorium: Wortarchiv, Eintrag 2", chain(
    "WORTARCHIV – EINTRAG 2. „essh“ = hinaus. „zhiv“ = Fremde. Bezug: wir.",
    "„luum“ = schlafen. Beobachtung: Die Dornen schlafen nie ganz.",
), [("ZEKIVD_SPRACHE_2", [1, 2])])
text("Obs_Tansy_3.xml", "Kristallobservatorium: Wortarchiv, Eintrag 3", chain(
    "WORTARCHIV – EINTRAG 3. „shii“ = hören. „dhuum“ = Kern, aus dem ein Planet wächst.",
    "Befund: Die Dornen hören uns seit unserer Ankunft.",
    "Personal: Rue, Treibstation auf der größten Insel im Nebel von Nebelranke.",
), [("ZEKIVD_SPRACHE_3", [1]), ("ZEKIVD_TREIBSTATION_RUMOR", [3])])
text("Obs_Tansy_4.xml", "Kristallobservatorium: Wortarchiv, Eintrag 4", chain(
    "WORTARCHIV – EINTRAG 4. „maa-dhuum“ = Mutter-Kern, Ort: Herzdorn. „oro-oro“ = Kreis, Zyklus.",
    "„nekh-ohn“ = niemand. Aussage der Dornen: Einer von euch spricht mit niemand. Zuordnung: ungeklärt.",
    yarrow_sign("Vorschlag zur Zuordnung: Hyssop. Er redet mit Wurzeln. Eingetragen von: Yarrow."),
), [("ZEKIVD_SPRACHE_4", [1, 2])])

# The gates behind the planets' nodes.
text("Glutpforte_Rue.xml", "Computer in der Glutpforte", chain(
    "GLUTPFORTE – WEGMARKE. Die Karte endet hier. Innere Knoten: heiß wie Glut. Weiter: ein anderes Mal. Kartiert von: Rue.",
))
text("Nebelpforte_Rue.xml", "Computer in der Nebelpforte", chain(
    "NEBELPFORTE – WEGMARKE. Verbindungen: der Kreuzweg und die Nester der Wächter. Warnung: Vorsicht. Kartiert von: Rue.",
))
text("Hohlpforte_Tansy.xml", "Computer in der Hohlpforte", chain(
    "HOHLPFORTE – WEGMARKE. Dahinter: Tansys Werkstatt. Weg: lang und dunkel.",
))


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
