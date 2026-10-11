# -*- coding: utf-8 -*-
"""
Ship log of "Verdornt" (Zeki.Verdornt). Writes planets/shiplogs/Absturz.xml (system SolarSystem, on Timber Hearth)
and planets/shiplogs/Verdornt.xml (system Verdornt, on Erstling). Stage 1 entries.

Usage:  python tools/verdornt_shiplog.py [path/to/Zeki.Verdornt]
"""
import os
import sys
from xml.sax.saxutils import escape

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Verdornt"))
SCHEMA = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="https://raw.githubusercontent.com/Outer-Wilds-New-Horizons/new-horizons/main/NewHorizons/Schemas/shiplog_schema.xsd"'


def entry(eid, name, facts, children=(), curiosity=False):
    return eid, name, facts, list(children), curiosity


def rumor(fid, name, text, source=None):
    return "R", fid, name, text, source


def fact(fid, text):
    return "E", fid, text


ABSTURZ = (
    entry('ZEKIVD_ABSTURZ', 'Der Absturzsamen', [
        fact('ZEKIVD_ABSTURZ_FOUND',
             'Neben dem alten Einschlagkrater auf Timber Hearth liegt ein frischer: Ein riesiger Dornensamen ist zu Beginn dieser Schleife eingeschlagen. Er ist offen – man kann hineinfliegen.'),
        fact('ZEKIVD_ABSTURZ_NOMAI',
             'Auf einem Nomai-Computer am Samen steht: Der Samen ist nicht gewachsen, er wurde geworfen – von einer Nomai namens Tansy.'),
    ], [
        entry('ZEKIVD_SCHLUND', 'Der Samenschlund', [
            rumor('ZEKIVD_SCHLUND_RUMOR', 'Ein Strudel im Samen',
                  'Das Flugprotokoll des Samens nennt seine Ladung: einen Strudel, der zum Lager auf Erstling führt.', 'ZEKIVD_ABSTURZ'),
            fact('ZEKIVD_ABSTURZ_SCHLUND',
                 'Im Samen liegt eine kleine, dunkle Dimension. In ihrer Mitte dreht sich ein Strudel aus Dornen, der alles in sich hineinzieht.'),
        ]),
    ], curiosity=True),
)

VERDORNT = (
    entry('ZEKIVD_LAGER', 'Das Lager auf Erstling', [
        fact('ZEKIVD_ANKUNFT',
             'Der Strudel hat mich in ein fremdes System gezogen. Ich bin neben einem kleinen Samen auf einem eisgepanzerten Dornenplaneten zu mir gekommen.'),
        fact('ZEKIVD_LAGER_FOUND',
             'Auf Erstling steht ein verlassenes Nomai-Lager: drei Kuppeln, ein Kernrechner, eine verschlossene Höhle und ein Warp-Turm.'),
        fact('ZEKIVD_RUECKSAMEN',
             'Ein kleiner Samen in einer Kupferwiege im Lager führt zurück nach Timber Hearth.'),
        rumor('ZEKIVD_LAGER_RUMOR_TURM', 'Ein schlafender Warp-Turm',
              'Der Lagerkern empfiehlt, den Warp-Turm zu wecken. Seine Murmel liegt in einer Röhre am Fuß des Turms.'),
        fact('ZEKIVD_TUERME',
             'Tansy hat auf jedem Planeten einen Warp-Turm gebaut. Jeder erwacht, wenn seine Murmel in die richtige Mulde rollt.'),
        fact('ZEKIVD_TURM_WACH_FACT',
             'Ich habe den Warp-Turm von Erstling geweckt. Er führt zum Ausguck hoch über dem System.'),
    ], [
        entry('ZEKIVD_AUSGUCK', 'Der Ausguck', [
            rumor('ZEKIVD_AUSGUCK_RUMOR', 'Ein Ausguck über dem System',
                  'Tansy sagt, der Warp-Turm von Erstling führt zu einem Ausguck, von dem man alles sieht, was die drei hier gefunden haben.',
                  'ZEKIVD_LAGER'),
            rumor('ZEKIVD_HERZDORN_RUMOR', 'Ein gefangener Stern',
                  'In der Mitte des Systems ist ein Stern in einem Käfig aus Dornen gefangen. Die Dornen trinken sein Licht.'),
            fact('ZEKIVD_SYSTEM_NAMEN',
                 'Die Nomai nannten das System Dornenkranz: Herzdorn in der Mitte, dann Erstling, Glutdorn, Nebelranke und Hohlsamen.'),
            fact('ZEKIVD_BRAMBLESATION',
                 'Hyssop zählte die Samen, die der Herzdorn ins All wirft, und nannte das die Bramblesation. Sie wächst immer weiter.'),
            fact('ZEKIVD_AUSGUCK_FOUND',
                 'Hoch über der Bahnebene schwebt eine Nomai-Plattform mit einem großen Projektionsbecken.'),
            fact('ZEKIVD_SYSTEM_BLICK',
                 'Vom Ausguck aus sieht man das ganze System: vier verdornte Planeten um einen Stern, der in einem Käfig aus Dornen gefangen ist.'),
        ]),
        entry('ZEKIVD_NETZ', 'Das Dornen-Netz', [
            rumor('ZEKIVD_KAELTE_HINWEIS', 'Ein Licht in der Kälte',
                  'Rue warnt vor einem Licht in einer kalten Dimension: Es ist kein Stern, sondern ein Anglerfisch.', 'ZEKIVD_LAGER'),
            fact('ZEKIVD_NETZ_RUE',
                 'Rue hat die Knoten kartiert: Die Dornen bilden ein Netz zwischen den Planeten. Der Weg zu den anderen führt über einen Kreuzweg.'),
            fact('ZEKIVD_EISPFORTE_FOUND',
                 'Der große Knoten von Erstling führt in eine eisblaue Dimension mit zwei weiteren Knoten.'),
            fact('ZEKIVD_SPLITTER_FOUND',
                 'Eine Dimension voller Eisdornen. Die Nomai haben hier Wegmarken hinterlassen.'),
            fact('ZEKIVD_KAELTE_FOUND',
                 'Eine dunkle, kalte Dimension. Etwas Großes lebt hier.'),
            fact('ZEKIVD_GLUTPFORTE_FOUND',
                 'Der Knoten von Glutdorn führt in eine glühende Dimension. Rues Karte endet hier.'),
            fact('ZEKIVD_NEBELPFORTE_FOUND',
                 'Der Knoten von Nebelranke führt in eine Dimension voller grünem Nebel. Von hier geht es zu den Nestern der Wächter.'),
            fact('ZEKIVD_HOHLPFORTE_FOUND',
                 'Der Knoten am Kristallkern von Hohlsamen führt in eine dunkle, violette Dimension. Dahinter liegt Tansys Werkstatt.'),
        ]),
    ], curiosity=True),
    entry('ZEKIVD_VIER', 'Hyssop, Rue, Tansy und Yarrow', [
        rumor('ZEKIVD_VIER_RUMOR', 'Vier Bewohner',
              'Der Lagerkern nennt vier Bewohner des Lagers: Hyssop, Rue, Tansy und Yarrow.', 'ZEKIVD_LAGER'),
        fact('ZEKIVD_FALSCH_ABGEBOGEN',
             'Drei Nomai vom Vessel – Hyssop, Rue und Tansy – suchten in den Dornen nach den Rettungskapseln. Ein alter Samen zog sie in dieses System.'),
        fact('ZEKIVD_URSPRUNG',
             'Hyssop glaubt, dass Dornenkranz der Ursprung von Dark Bramble ist: Unsere Dornen sind nur ein Samen von hier.'),
        fact('ZEKIVD_TANSY_WURF',
             'Tansy hat einen Samen in Richtung unseres Systems geworfen, als Weg für alle, die nach ihnen kommen. Er schlug auf Timber Hearth ein.'),
    ], [
        entry('ZEKIVD_LABOR', 'Das Wurzellabor', [
            rumor('ZEKIVD_LABOR_RUMOR', 'Hyssop hört die Wurzeln',
                  'Das Glutwerk führt Hyssop als Personal im Wurzellabor, unten in der breitesten Schlucht von Erstling. Er hört die Wurzeln.',
                  'ZEKIVD_GLUTWERK'),
            fact('ZEKIVD_LABOR_FOUND',
                 'Unten in der breitesten Schlucht von Erstling steht Hyssops Labor auf einem Teller aus Wurzeln, direkt am leuchtenden Kern.'),
        ]),
        entry('ZEKIVD_SPRACHE', 'Die Dornensprache', [
            rumor('ZEKIVD_SPRACHE_RUMOR', 'Ein Übersetzer, der die Dornen hört',
                  'Im Wurzellabor ist eine Wurzel um einen Übersetzer gewachsen. Er gibt Laute wieder, und die Wurzeln antworten.', 'ZEKIVD_LABOR'),
            fact('ZEKIVD_DORNSPRACHE_FAKT',
                 'Im Wurzellabor ist eine Wurzel um einen Nomai-Übersetzer gewachsen. Seit ich ihn berührt habe, übersetzt mein Übersetzer die leuchtende Dornenschrift – aber nur die Wörter, die ich kenne.'),
            fact('ZEKIVD_SPRACHE_1', 'Tansy kannte die ersten Wörter: Herz, tragen, Welten.'),
            fact('ZEKIVD_SPRACHE_2', 'Tansy lernte die Wörter für hinaus, Fremde und schlafen.'),
            fact('ZEKIVD_SPRACHE_3', 'Tansy lernte die Wörter für hören und Kern.'),
            fact('ZEKIVD_SPRACHE_4', 'Tansy lernte die Wörter für Mutter-Kern, Kreis und niemand. Die Dornen sagen, einer der Nomai spreche mit niemand.'),
        ]),
    ], curiosity=True),
    entry('ZEKIVD_KERNE', 'Die Planetenkerne', [
        rumor('ZEKIVD_MUTTERKERN_RUMOR', 'Der Mutterkern',
              'Alle Planetenkerne gleichen einem Kern im Herzdorn: dem Mutterkern, der jeden Samen dieses Systems geworfen hat.', 'ZEKIVD_LAGER'),
        fact('ZEKIVD_KERN_PLAN',
             'Ein Planetenkern ist der Samenkern, aus dem ein ganzer Planet gewachsen ist.'),
        fact('ZEKIVD_KERN_ERSTLING_GENOMMEN',
             'In der Höhle hinter dem Lagertor lag der Planetenkern von Erstling: das Herz des Samens, aus dem dieser Planet gewachsen ist.'),
        rumor('ZEKIVD_KERN_SCHREIN_RUMOR', 'Ein Schrein für vier Kerne',
              'Alle vier Planetenkerne gehören zum Kernschrein vor dem Herzdorn. Dann öffnet sich der Weg nach innen.', 'ZEKIVD_LAGER'),
    ], curiosity=True),
)


GLUTDORN = (
    entry('ZEKIVD_GLUTWERK', 'Das Glutwerk', [
        rumor('ZEKIVD_GLUTWERK_RUMOR', 'Ein Wärmewerk auf Glutdorn',
              'Die Karte der Treibstation verzeichnet ein Wärmewerk auf der größten Scholle von Glutdorn, erbaut von Hyssop.', 'ZEKIVD_TREIBSTATION'),
        fact('ZEKIVD_GLUTWERK_FOUND',
             'Auf der größten Scholle von Glutdorn steht das Glutwerk. Eine Brücke führt über die Lavaspalte zur Scholle mit dem Knoten – wenn ihre Murmel richtig liegt.'),
    ]),
)
NEBELRANKE = (
    entry('ZEKIVD_TREIBSTATION', 'Die Treibstation', [
        rumor('ZEKIVD_TREIBSTATION_RUMOR', 'Rues Station im Nebel',
              'Das Wortarchiv führt Rue in einer Treibstation auf der größten Insel im Nebel von Nebelranke.', 'ZEKIVD_OBSERVATORIUM'),
        rumor('ZEKIVD_ERNESTO_RUMOR', 'Ein Fisch, der spricht',
              'Rue behauptet, im Nebel habe ein Fisch mit ihr gesprochen – höflich, wie ein Gelehrter.'),
        fact('ZEKIVD_TREIBSTATION_FOUND',
             'Die Inseln von Nebelranke kreisen als Ring um einen Kern aus Dornen. Auf der größten steht Rues Treibstation.'),
    ]),
)
HOHLSAMEN = (
    entry('ZEKIVD_OBSERVATORIUM', 'Das Kristallobservatorium', [
        rumor('ZEKIVD_OBSERVATORIUM_RUMOR', 'Tansys Wörter',
              'Das Wurzellabor verweist auf ein Wortarchiv der Dornensprache im Kristallobservatorium auf Hohlsamen, verwaltet von Tansy.', 'ZEKIVD_LABOR'),
        fact('ZEKIVD_OBSERVATORIUM_FOUND',
             'Auf dem größten Splitter der Samenhülle von Hohlsamen steht Tansys Observatorium, offen zum Himmel.'),
        fact('ZEKIVD_HERZ_BLICK',
             'Das Becken im Observatorium zeigt den Herzdorn ganz nah: einen Stern hinter Ranken, dicker als Planeten.'),
    ]),
)


def xml(e, ind, tree=None):
    eid, name, facts, children, curiosity = e
    # every entry below a curiosity names it, otherwise New Horizons draws it without the curiosity's colour
    out = [f"{ind}<Entry>", f"{ind}  <ID>{eid}</ID>", f"{ind}  <Name>{escape(name)}</Name>"]
    if tree:
        out.append(f"{ind}  <Curiosity>{tree}</Curiosity>")
    tree = tree or eid
    if curiosity:
        out.append(f"{ind}  <IsCuriosity/>")
    # the schema wants the rumor facts before the explore facts
    for f in sorted(facts, key=lambda f: f[0] != "R"):
        if f[0] == "R":
            _, fid, rname, text, source = f
            out += [f"{ind}  <RumorFact>", f"{ind}    <ID>{fid}</ID>"]
            if source:
                out.append(f"{ind}    <SourceID>{source}</SourceID>")
            out += [f"{ind}    <RumorName>{escape(rname)}</RumorName>", f"{ind}    <Text>{escape(text)}</Text>", f"{ind}  </RumorFact>"]
        else:
            _, fid, text = f
            out += [f"{ind}  <ExploreFact>", f"{ind}    <ID>{fid}</ID>", f"{ind}    <Text>{escape(text)}</Text>", f"{ind}  </ExploreFact>"]
    for c in children:
        out += xml(c, ind + "  ", tree)
    out.append(f"{ind}</Entry>")
    return out


def write(filename, astro_id, comment, entries, tree=None):
    lines = ['<?xml version="1.0" encoding="utf-8"?>', f"<!-- {comment} -->", f"<AstroObjectEntry {SCHEMA}>", f"  <ID>{astro_id}</ID>"]
    for e in entries:
        lines += xml(e, "  ", tree)
    lines.append("</AstroObjectEntry>")
    path = os.path.join(MOD, "planets", "shiplogs", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    write("Absturz.xml", "ZEKIVD_TH", "Logbuch: der Absturzsamen auf Timber Hearth", ABSTURZ)
    write("Verdornt.xml", "ZEKIVD_ERSTLING", "Logbuch: Dornenkranz", VERDORNT)
    write("Glutdorn.xml", "ZEKIVD_GLUTDORN", "Logbuch: Glutdorn", GLUTDORN, tree="ZEKIVD_VIER")
    write("Nebelranke.xml", "ZEKIVD_NEBELRANKE", "Logbuch: Nebelranke", NEBELRANKE, tree="ZEKIVD_VIER")
    write("Hohlsamen.xml", "ZEKIVD_HOHLSAMEN", "Logbuch: Hohlsamen", HOHLSAMEN, tree="ZEKIVD_VIER")
    print("ship logs written (Verdornt)")


if __name__ == "__main__":
    main()
