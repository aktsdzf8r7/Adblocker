# -*- coding: utf-8 -*-
"""
Ship log of "Die Aussendungseinheit" (Zeki.ISAE). Writes planets/shiplogs/ISAE.xml.

Usage:  python tools/isae_shiplog.py [path/to/Zeki.ISAE]
"""
import os
import sys
from xml.sax.saxutils import escape

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.ISAE"))
SCHEMA = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="https://raw.githubusercontent.com/Outer-Wilds-New-Horizons/new-horizons/main/NewHorizons/Schemas/shiplog_schema.xsd"'


def entry(eid, name, facts, children=(), curiosity=False):
    return eid, name, facts, list(children), curiosity


def rumor(fid, name, text, source=None):
    return "R", fid, name, text, source


def fact(fid, text):
    return "E", fid, text


LOG = (
    entry('ZEKISAE_ISAE', 'Interstellare Sonden Aussendungseinheit', [
        rumor('ZEKISAE_SIGNATUR', 'Eine fremde Energiesignatur',
              'Seit dem Start meldet mein Schiff eine unbekannte Nomai-Energiesignatur zwischen der Sonne und Timber Hearth, weit über der Bahnebene der Planeten. Mein Signalskop empfängt sie auf der Frequenz „Energiesignaturen“.'),
        rumor('ZEKISAE_RUMOR', 'Sedums verbotener Entwurf',
              'Ein Nomai namens Sedum wollte gegen Pyes Verbot eine zweite, stärkere Kanone bauen. Sie soll Sonden zu anderen Sternen schicken und braucht dafür mehr Energie, als ein lebender Stern hergibt.'),
        fact('ZEKISAE_FOUND',
             'Eine riesige Kanone im Stil des Vessels kreist um die Sonne, über einen Kilometer lang, mit gepanzertem Kern, gezahnten Schienen und Klauen an der Mündung. Sie zielt auf die Sonne, und drei Fokuskanonen umkreisen ihren Lauf.'),
        fact('ZEKISAE_ZWECK',
             'Die Aussendungseinheit wartet auf den Tod der Sonne. Sobald der Stern zusammenbricht, trinken ihre Linse und die Fokuskanonen seine ganze Energie für einen einzigen Schuss zu einem fremden Stern.'),
        fact('ZEKISAE_ERWACHT',
             'Die Einheit hat 281 042 Jahre geschlafen. Sie ist erwacht, als das Aschezwilling-Projekt zum ersten Mal Erinnerungen in die Vergangenheit geschickt hat – also, als meine Zeitschleife begann.'),
        fact('ZEKISAE_GEFAHR',
             'Linum hat erkannt: Nimmt die Einheit der Sonne ihre Energie, gibt es keine Supernova. Ohne Supernova schickt das Aschezwilling-Projekt keine Erinnerungen zurück. Die Schleife endet – und ich mit ihr.'),
        fact('ZEKISAE_ANLEITUNG',
             'Um die Einheit abzuschalten, muss ich die Phasenkoppler auf allen drei Fokuskanonen trennen. Danach erwacht im Kontrollmodul der Hauptschalter.'),
        fact('ZEKISAE_ABGESCHALTET',
             'Ich habe die Aussendungseinheit abgeschaltet. Ihre Linse ist erloschen. Die Sonne darf wieder so sterben, wie sie es immer tut.'),
    ], [
        entry('ZEKISAE_KONTROLLE', 'Das Kontrollmodul', [
            fact('ZEKISAE_KONTROLLE_FOUND',
                 'Das Kontrollmodul ist eine Kopie der Module der Orbitalen Sondenkanone. Neben dem Computer und Linums Aufzeichnung ist ein Platz leer – dort erscheint später der Hauptschalter.'),
        ]),
        entry('ZEKISAE_KERN', 'Die Kernkammer', [
            rumor('ZEKISAE_KERN_RUMOR', 'Eine Luke im Panzer',
                  'Linum sagt, Sedum habe sich in die Kernkammer zurückgezogen. Die Luke liegt in der Panzerung unter der ersten Schiene.', source='ZEKISAE_KONTROLLE'),
            fact('ZEKISAE_KERN_FOUND',
                 'Im Inneren der Panzerung glüht das Herz der Einheit über einem Sockel. Davor liegen die Überreste eines Nomai.'),
            fact('ZEKISAE_SEDUM_ENDE',
                 'Sedum blieb beim Herz seiner Einheit, als die Geisterwolke kam. Er ließ sie schlafen, damit sie beim Tod der Sonne eine Warnung zu den anderen Nomai-Clans trägt.'),
            fact('ZEKISAE_LINUM_SCHALTER',
                 'Sedum hat Linums heimliche Abschaltung gefunden – und sie absichtlich eingebaut gelassen. Er wollte, dass jemand nach ihm entscheiden kann.'),
            fact('ZEKISAE_NAVI_ZWEIFEL',
                 'Linum zweifelte, ob am Ziel überhaupt noch jemand lebt. Sedum wollte wenigstens verhindern, dass sich ein zweites Vessel in den Dornen verirrt.'),
        ]),
        entry('ZEKISAE_START', 'Das Startmodul', [
            rumor('ZEKISAE_START_RUMOR', 'Eine Sonde wartet',
                  'Laut dem Computer im Kontrollmodul wartet im Startmodul eine Sonde auf den Schuss.', source='ZEKISAE_KONTROLLE'),
            fact('ZEKISAE_START_FOUND',
                 'Im Startmodul schwebt eine Nomai-Sonde, bereit für den Schuss.'),
            fact('ZEKISAE_START_BAU',
                 "Sedum und eine Pilotin namens Erica haben die Einheit heimlich gebaut. Die Teile kamen vom Konstruktionshof auf Giant's Deep, die Hülle folgt den Plänen des Vessels."),
            fact('ZEKISAE_START_KERN',
                 'Für die Energie eines ganzen Sterns braucht die Einheit einen fortgeschrittenen Warpkern wie im Vessel. Sedum hat seinen Entwurf aus den Rettungskapseln abgeschrieben.'),
            fact('ZEKISAE_START_SONDE',
                 'Die Sonde ist eine umgebaute Ersatzsonde der Orbitalen Sondenkanone. Sie soll durch den Lauf der Hauptkanone zum Heimatstern der Nomai fliegen.'),
            fact('ZEKISAE_BOTSCHAFT',
                 'Die Sonde trägt eine Warnung an die anderen Clans: Folgt dem Signal des Auges nicht durch die Dornen. Unser Vessel ist dort zerschellt.'),
        ]),
        entry('ZEKISAE_NAVI', 'Das Navigationsmodul', [
            rumor('ZEKISAE_NAVI_RUMOR', 'Ein berechnetes Ziel',
                  'Der Computer im Kontrollmodul meldet, das Ziel der Einheit sei im Navigationsmodul berechnet.', source='ZEKISAE_KONTROLLE'),
            fact('ZEKISAE_NAVI_FOUND',
                 'Im Navigationsmodul dreht sich eine leuchtende Sternkarte.'),
            fact('ZEKISAE_NAVI_ZIEL',
                 'Das Ziel ist der Heimatstern der Nomai. Er liegt hinter dem Nebel, aus dem das Signal des Auges kam.'),
            fact('ZEKISAE_NAVI_ENERGIE',
                 'So weit kommt eine Sonde nur mit der gesamten Energie eines sterbenden Sterns in einem einzigen Augenblick. Darum wartet die Einheit auf den Tod der Sonne.'),
            fact('ZEKISAE_PYE_VERBOT',
                 'Pye hat die Einheit verboten: Das Aschezwilling-Projekt braucht den Tod der Sonne, und niemand hat das Recht, ihn für eine Botschaft zu opfern.'),
        ]),
        entry('ZEKISAE_FOKUS', 'Die Fokuskanonen', [
            rumor('ZEKISAE_FOKUS_RUMOR', 'Drei Fokuskanonen',
                  'Drei kleinere Kanonen namens Alpha, Beta und Gamma umkreisen den Lauf der Aussendungseinheit. Ihre Phasenkoppler sind noch verbunden.', source='ZEKISAE_KONTROLLE'),
            fact('ZEKISAE_FOKUS_FOUND',
                 'Jede Fokuskanone ist eine Nomai-Schwerkraftkanone in einem Gerüst aus drei Dornen. Oben sitzt ein Emitter, der auf die Sonne zielt, unten ein Kiel. Eine rote Leitung verbindet ihn mit der Hauptkanone.'),
            fact('ZEKISAE_FOKUS_ZWECK',
                 'Die Fokuskanonen bündeln den Energiestrom des Sterns und lenken ihn in die Hauptkanone.'),
            fact('ZEKISAE_FOKUS_LEITUNG',
                 'Wird ein Phasenkoppler getrennt, erlischt die rote Leitung dieser Fokuskanone.'),
            fact('ZEKISAE_FOKUS_BAU',
                 'Erica hat die Fokuskanonen nach der Schwerkraftkanone von Ember Twin gebaut. Statt Fähren werfen sie Licht.'),
            fact('ZEKISAE_FOKUS_DREIECK',
                 'Nur alle drei gemeinsam halten den Strom eines ganzen Sterns. Fehlt einer, bricht das Dreieck.'),
            fact('ZEKISAE_FOKUS_SONNE',
                 'Die Einheit zielt immer auf die Sonne und folgt ihr, solange niemand an Bord ist. Nach dem Tod der Sonne wendet sie sich ab und schießt zu den Sternen.'),
            fact('ZEKISAE_FOKUS_OBEN',
                 'Auf Fokuskanone Beta liegt der Phasenkoppler oben unter dem Emitter.'),
            fact('ZEKISAE_FOKUS_UNTEN',
                 'Auf Fokuskanone Gamma hängt der Phasenkoppler unter dem Kiel, in der Leere.'),
            fact('ZEKISAE_FOKUS_VERSTECK',
                 'Linum hat die Koppler versteckt, damit nur jemand sie findet, der wirklich sucht.'),
            fact('ZEKISAE_KOPPLER_A_FACT',
                 'Der Phasenkoppler von Fokuskanone Alpha ist getrennt.'),
            fact('ZEKISAE_KOPPLER_B_FACT',
                 'Der Phasenkoppler von Fokuskanone Beta ist getrennt.'),
            fact('ZEKISAE_KOPPLER_C_FACT',
                 'Der Phasenkoppler von Fokuskanone Gamma ist getrennt.'),
        ]),
        entry('ZEKISAE_SEDUM', 'Sedum, Linum, Pye und Erica', [
            fact('ZEKISAE_SEDUM_PLAN',
                 'Sedum baute die Aussendungseinheit, weil das Auge vielleicht nicht in diesem System liegt. Eine Sonde zu den Sternen schien ihm wichtiger als alles andere.'),
            fact('ZEKISAE_LINUM_REUE',
                 'Linum half Sedum, prüfte seine Rechnungen und entschied sich am Ende gegen ihn: Niemand darf das Ende eines anderen wählen.'),
        ]),
        entry('ZEKISAE_SPUREN', 'Spuren im Sonnensystem', [
            fact('ZEKISAE_SPUR_ET',
                 'Auf Ember Twin hat Erica die Schwerkraftkanone vermessen, für drei Kanonen, deren Zweck Sedum ihr nicht verriet.'),
            fact('ZEKISAE_SPUR_ATTLE',
                 'Auf dem Attlerock hat Linum die Sonne gemessen: Sie altert und wird in einigen hunderttausend Jahren sterben.'),
            fact('ZEKISAE_SPUR_GD',
                 "Im Kern von Giant's Deep las Linum beim Sondenverfolgungsmodul, dass die ersten Schüsse das Auge nicht fanden – für Sedum ein Beweis, für Linum ein Grund weiterzusuchen."),
            fact('ZEKISAE_SPUR_BH',
                 'Auf Brittle Hollow lehnte Pyes Versammlung Sedums Antrag ab. Pye fürchtete, dass er trotzdem baut.'),
        ]),
    ], curiosity=True)
)


def xml(e, ind):
    eid, name, facts, children, curiosity = e
    out = [f"{ind}<Entry>", f"{ind}  <ID>{eid}</ID>", f"{ind}  <Name>{escape(name)}</Name>"]
    if curiosity:
        out.append(f"{ind}  <IsCuriosity/>")
    for f in facts:
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
        out += xml(c, ind + "  ")
    out.append(f"{ind}</Entry>")
    return out


def main():
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<!-- Logbuch: die Interstellare Sonden Aussendungseinheit im Sonnensystem -->",
             f"<AstroObjectEntry {SCHEMA}>", "  <ID>ISAE</ID>"] + xml(LOG, "  ") + ["</AstroObjectEntry>"]
    path = os.path.join(MOD, "planets", "shiplogs", "ISAE.xml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("ship log written")


if __name__ == "__main__":
    main()
