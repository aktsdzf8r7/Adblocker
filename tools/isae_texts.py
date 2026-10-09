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
    "Pye hat ihn verboten. Ich baue ihn trotzdem – dort, wo die Sonne am hellsten ist, zwischen ihr und Timber Hearth.",
), [("ZEKISAE_SEDUM_PLAN", [1, 2, 3]), ("ZEKISAE_RUMOR", [1, 2, 3, 4])])

# ------------------------------------------------------------------ control module (Kontrollmodul)
text("ISAE_Status.xml", "Vessel-Computer im Kontrollmodul der Aussendungseinheit", chain(
    "INTERSTELLARE SONDEN AUSSENDUNGSEINHEIT. Zustand: erwacht.",
    "Weckbedingung erfüllt: Das Aschezwilling-Projekt hat zum ersten Mal Erinnerungen in die Vergangenheit geschickt. Schlafdauer: 281 042 Jahre.",
    "Auslöser des Schusses: Tod des Sterns. Sobald er zusammenbricht, wird ihm alle verbleibende Energie entzogen.",
    "Fokuskanonen Alpha, Beta und Gamma: ausgerichtet. Phasenkoppler: verbunden. Sonde im Startmodul: bereit. Ziel im Navigationsmodul: berechnet.",
    "Erwartete Folgen für dieses System: keine. Der Stern stirbt ohnehin. – Sedum",
), [("ZEKISAE_ZWECK", [1, 3]), ("ZEKISAE_ERWACHT", [2]), ("ZEKISAE_FOKUS_RUMOR", [4]), ("ZEKISAE_START_RUMOR", [4]),
    ("ZEKISAE_NAVI_RUMOR", [4])])

text("ISAE_Linum.xml", "Linums Aufzeichnung (Vessel-Recorder) im Kontrollmodul", chain(
    "Hier spricht Linum. Ich habe Sedums Rechnungen geprüft. Sie stimmen. Aber er hat etwas übersehen.",
    "Auf dem Aschezwilling bauen die anderen ein Projekt, das die Energie der sterbenden Sonne einfängt, um Erinnerungen in die Vergangenheit zu schicken.",
    "Nimmt die Aussendungseinheit diese Energie zuerst, gibt es keine Supernova mehr. Keine Supernova, kein Projekt. Keine Schleife.",
    "Wer in der Schleife gefangen ist, kehrt dann nicht zurück. Das Universum endet – aber er endet vor ihm.",
    "Ich habe heimlich eine Abschaltung eingebaut: Trenne die Phasenkoppler auf allen drei Fokuskanonen. Dann erwacht der Hauptschalter hier im Kontrollmodul.",
), [("ZEKISAE_GEFAHR", [1, 2, 3, 4]), ("ZEKISAE_ANLEITUNG", [5])])

text("Sedum_Abschied.xml", "Wandschrift im Kontrollmodul: Sedums letzte Worte (neben seinen Überresten)", chain(
    "Sedum: Die Geisterwolke hat die Sonnenstation erreicht. Pye ruft alle zurück. Ich bleibe hier.",
    "Sedum: Linum, ich habe deine Koppler gefunden. Du hast eine Abschaltung in meine Einheit gebaut.",
    "Sedum: Ich habe sie nicht entfernt. Wenn du recht hast, soll jemand anderes entscheiden können.",
    "Sedum: Ich lasse die Einheit schlafen, bis die Sonne stirbt. Dann trägt sie unsere Warnung zu den Clans.",
    "Sedum: Wer immer dies liest: Die Entscheidung gehört jetzt dir.",
), [("ZEKISAE_SEDUM_ENDE", [1, 2, 3, 4, 5]), ("ZEKISAE_LINUM_SCHALTER", [2, 3])])

text("ISAE_Hauptschalter.xml", "Wegmarke am Hauptschalter (erscheint, wenn alle Koppler getrennt sind)", [
    (1, None, "Linum: Die Koppler sind getrennt. Nur dieses Interface hält die Einheit noch wach. Schalte sie ab."),
])

# ------------------------------------------------------------------ launch module (Startmodul)
text("Start_Bau.xml", "Wandschrift im Startmodul: wie die Einheit gebaut wurde", chain(
    "Erica: Die letzte Ladung vom Konstruktionshof ist da. Niemand hat gefragt, wofür die Ringe sind.",
    "Sedum: Gut. Die Hülle folgt den Plänen des Vessels. Es ist das Stärkste, was wir je gebaut haben.",
    "Erica: Und der Kern? Ein gewöhnlicher Warpkern hält die Energie eines Sterns nicht aus.",
    "Sedum: Ich habe den Entwurf des fortgeschrittenen Warpkerns aus den Rettungskapseln abgeschrieben. Er wird sie halten.",
    "Erica: Pye wird wütend sein. Sedum: Pye wird es verstehen, wenn die Clans uns antworten.",
), [("ZEKISAE_START_BAU", [1, 2]), ("ZEKISAE_START_KERN", [3, 4, 5])])

text("Start_Sonde.xml", "Vessel-Computer im Startmodul: die Nutzlast", chain(
    "STARTMODUL. Nutzlast: eine Ersatzsonde der Orbitalen Sondenkanone, umgebaut für interstellare Entfernungen.",
    "Botschaft an Bord: »An alle Clans: Wir sind dem Signal des Auges gefolgt. Unser Vessel ist in den Dornen zerschellt.«",
    "»Folgt dem Signal nicht durch die Dornen. Sucht einen anderen Weg. Wartet nicht auf uns.«",
    "Startfenster: Tod des Sterns. Flugdauer bis zum Heimatstern: unbekannt. Die Sonde verlässt die Kanone durch den Lauf.",
), [("ZEKISAE_START_SONDE", [1, 4]), ("ZEKISAE_BOTSCHAFT", [2, 3])])

# ------------------------------------------------------------------ navigation module (Navigationsmodul)
text("Navi_Ziel.xml", "Vessel-Computer im Navigationsmodul: das Ziel", chain(
    "NAVIGATIONSMODUL. Ziel: der Heimatstern der Nomai.",
    "Position nach den Sternkarten des Vessels berechnet. Der Stern ist von hier aus nicht zu sehen; er liegt hinter dem Nebel, aus dem das Signal des Auges kam.",
    "Nötige Geschwindigkeit: ein Vielfaches dessen, was ein lebender Stern liefern kann.",
    "Lösung: die gesamte Energie eines sterbenden Sterns in einem einzigen Augenblick. Darum warten wir. – Sedum",
), [("ZEKISAE_NAVI_ZIEL", [1, 2]), ("ZEKISAE_NAVI_ENERGIE", [3, 4])])

text("Navi_Pye.xml", "Pyes Aufzeichnung (Vessel-Recorder) im Navigationsmodul", chain(
    "Hier spricht Pye. Sedum, ich habe deine Pläne gesehen. Die Antwort ist nein.",
    "Wir haben die Sonnenstation gebaut, um die Sonne zu zwingen. Sie hat versagt, und ich bin heute froh darüber.",
    "Das Aschezwilling-Projekt braucht den Tod der Sonne, wenn er kommt. Du würdest ihn stehlen.",
    "Unsere Clans werden uns finden oder nicht. Wir haben kein Recht, dafür alles andere zu opfern.",
    "Schalte die Einheit ab. Das ist keine Bitte.",
), [("ZEKISAE_PYE_VERBOT", [1, 2, 3, 4, 5])])

text("Navi_Wand.xml", "Wandschrift im Navigationsmodul: Linum und Sedum über das Ziel", chain(
    "Linum: Du hast den Heimatstern gefunden? Nach all den Jahren auf dem Vessel?",
    "Sedum: Die Sternkarten des Vessels sind genau. Er liegt hinter dem Nebel des Auges, weiter als wir je gedacht haben.",
    "Linum: Dann wird die Sonde Jahrtausende brauchen. Vielleicht gibt es dort niemanden mehr, der sie liest.",
    "Sedum: Vielleicht. Aber wenn doch, verirrt sich wenigstens kein zweites Vessel in den Dornen.",
), [("ZEKISAE_NAVI_ZWEIFEL", [1, 2, 3, 4])])

# ------------------------------------------------------------------ the three focus cannons
text("Fokus_Alpha.xml", "Vessel-Computer auf Fokuskanone Alpha", chain(
    "FOKUSKANONE ALPHA. Aufgabe: den Energiestrom des Sterns bündeln und in die Hauptkanone lenken.",
    "Phasenkoppler: verbunden. Der Kristall am Koppler leuchtet, solange der Strom fließen kann.",
    "Erica: Wir haben die Schwerkraftkanonen von Ember Twin nachgebaut. Sie werfen sonst Fähren; hier werfen sie Licht.",
    "Linum: Trenne den Koppler. Wenn der Kristall erlischt, ist Alpha frei.",
), [("ZEKISAE_FOKUS_ZWECK", [1, 2]), ("ZEKISAE_FOKUS_BAU", [3])])

text("Fokus_Beta.xml", "Vessel-Computer auf Fokuskanone Beta", chain(
    "FOKUSKANONE BETA. Ausrichtung: parallel zur Hauptkanone, auf den Heimatstern.",
    "Sedum: Die drei Kanonen bilden ein Dreieck. Nur gemeinsam halten sie den Strom eines ganzen Sterns.",
    "Linum: Dann reicht es, ihnen das Dreieck zu nehmen.",
), [("ZEKISAE_FOKUS_DREIECK", [1, 2, 3])])

text("Fokus_Gamma.xml", "Vessel-Computer auf Fokuskanone Gamma", chain(
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
