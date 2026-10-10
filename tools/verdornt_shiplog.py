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
        fact('ZEKIVD_ABSTURZ_SCHLUND',
             'Im Samen liegt eine kleine, dunkle Dimension. In ihrer Mitte dreht sich ein Strudel aus Dornen, der alles in sich hineinzieht.'),
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
        fact('ZEKIVD_TURM_WACH_FACT',
             'Ich habe den Warp-Turm von Erstling geweckt. Er führt zum Ausguck hoch über dem System.'),
    ], [
        entry('ZEKIVD_AUSGUCK', 'Der Ausguck', [
            fact('ZEKIVD_AUSGUCK_FOUND',
                 'Hoch über der Bahnebene schwebt eine Nomai-Plattform mit einem großen Projektionsbecken.'),
            fact('ZEKIVD_SYSTEM_BLICK',
                 'Vom Ausguck aus sieht man das ganze System: vier verdornte Planeten um einen Stern, der in einem Käfig aus Dornen gefangen ist.'),
        ]),
        entry('ZEKIVD_NETZ', 'Das Dornen-Netz', [
            fact('ZEKIVD_EISPFORTE_FOUND',
                 'Der große Knoten von Erstling führt in eine eisblaue Dimension mit zwei weiteren Knoten.'),
            fact('ZEKIVD_SPLITTER_FOUND',
                 'Eine Dimension voller Eisdornen. Die Nomai haben hier Wegmarken hinterlassen.'),
            fact('ZEKIVD_KAELTE_FOUND',
                 'Eine dunkle, kalte Dimension. Etwas Großes lebt hier.'),
        ]),
    ], curiosity=True),
    entry('ZEKIVD_KERNE', 'Die Planetenkerne', [
        fact('ZEKIVD_KERN_ERSTLING_GENOMMEN',
             'In der Höhle hinter dem Lagertor lag der Planetenkern von Erstling: das Herz des Samens, aus dem dieser Planet gewachsen ist.'),
        rumor('ZEKIVD_KERN_SCHREIN_RUMOR', 'Ein Schrein für vier Kerne',
              'Hyssop schreibt, dass alle vier Planetenkerne zum Kernschrein vor dem Herzdorn gehören. Dann öffnet sich der Weg nach innen.'),
    ], curiosity=True),
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


def write(filename, astro_id, comment, entries):
    lines = ['<?xml version="1.0" encoding="utf-8"?>', f"<!-- {comment} -->", f"<AstroObjectEntry {SCHEMA}>", f"  <ID>{astro_id}</ID>"]
    for e in entries:
        lines += xml(e, "  ")
    lines.append("</AstroObjectEntry>")
    path = os.path.join(MOD, "planets", "shiplogs", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    write("Absturz.xml", "ZEKIVD_TH", "Logbuch: der Absturzsamen auf Timber Hearth", ABSTURZ)
    write("Verdornt.xml", "ZEKIVD_ERSTLING", "Logbuch: Dornenkranz, Etappe 1", VERDORNT)
    print("ship logs written (Verdornt)")


if __name__ == "__main__":
    main()
