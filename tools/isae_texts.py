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

# ------------------------------------------------------------------ control module (Kontrollmodul, a copy of the real OPC module)
text("ISAE_Status.xml", "Computer im Kontrollmodul der Aussendungseinheit", chain(
    "INTERSTELLARE SONDEN AUSSENDUNGSEINHEIT. Zustand: erwacht. Ausrichtung: auf den Stern.",
    "Weckbedingung erfüllt: Das Aschezwilling-Projekt hat zum ersten Mal Erinnerungen in die Vergangenheit geschickt. Schlafdauer: 281 042 Jahre.",
    "Auslöser des Schusses: Tod des Sterns. Sobald er zusammenbricht, trinken Linse und Fokuskanonen alle verbleibende Energie.",
    "Fokuskanonen Alpha, Beta und Gamma: ausgerichtet. Phasenkoppler: verbunden. Sonde im Startmodul: bereit. Ziel im Navigationsmodul: berechnet.",
    "Erwartete Folgen für dieses System: keine. Der Stern stirbt ohnehin. – Sedum",
), [("ZEKISAE_ZWECK", [1, 3]), ("ZEKISAE_ERWACHT", [2]), ("ZEKISAE_FOKUS_RUMOR", [4]), ("ZEKISAE_START_RUMOR", [4]),
    ("ZEKISAE_NAVI_RUMOR", [4])])

text("ISAE_Linum.xml", "Linums Aufzeichnung im Kontrollmodul", chain(
    "Hier spricht Linum. Ich habe Sedums Rechnungen geprüft. Sie stimmen. Aber er hat etwas übersehen.",
    "Auf dem Aschezwilling bauen die anderen ein Projekt, das die Energie der sterbenden Sonne einfängt, um Erinnerungen in die Vergangenheit zu schicken.",
    "Nimmt die Aussendungseinheit diese Energie zuerst, gibt es keine Supernova mehr. Keine Supernova, kein Projekt. Keine Schleife.",
    "Wer in der Schleife gefangen ist, kehrt dann nicht zurück. Das Universum endet – aber er endet vor ihm.",
    "Ich habe heimlich eine Abschaltung eingebaut: Trenne die Phasenkoppler auf allen drei Fokuskanonen. Dann erwacht der Hauptschalter hier im Kontrollmodul.",
    "Sedum hat sich in die Kernkammer zurückgezogen. Die Luke liegt in der Panzerung unter der ersten Schiene.",
), [("ZEKISAE_GEFAHR", [1, 2, 3, 4]), ("ZEKISAE_ANLEITUNG", [5]), ("ZEKISAE_KERN_RUMOR", [6])])

text("ISAE_Hauptschalter.xml", "Wegmarke am Hauptschalter (erscheint, wenn alle Koppler getrennt sind)", [
    (1, None, "Linum: Die Koppler sind getrennt. Nur dieses Interface hält die Einheit noch wach. Schalte sie ab."),
])

# ------------------------------------------------------------------ the core chamber (Kernkammer, Blender)
text("Sedum_Abschied.xml", "Computer in der Kernkammer: Sedums letzte Worte (neben seinen Überresten)", chain(
    "Sedum: Die Geisterwolke hat die Sonnenstation erreicht. Pye ruft alle zurück. Ich bleibe hier, beim Herz der Einheit.",
    "Sedum: Linum, ich habe deine Koppler gefunden. Du hast eine Abschaltung in meine Einheit gebaut.",
    "Sedum: Ich habe sie nicht entfernt. Wenn du recht hast, soll jemand anderes entscheiden können.",
    "Sedum: Ich lasse die Einheit schlafen, bis die Sonne stirbt. Dann trägt sie unsere Warnung zu den Clans.",
    "Sedum: Wer immer dies liest: Die Entscheidung gehört jetzt dir.",
), [("ZEKISAE_SEDUM_ENDE", [1, 2, 3, 4, 5]), ("ZEKISAE_LINUM_SCHALTER", [2, 3])])

text("Kammer_Zweifel.xml", "Aufzeichnung in der Kernkammer: Linum und Sedum über das Ziel", chain(
    "Linum: Du hast den Heimatstern gefunden? Nach all den Jahren auf dem Vessel?",
    "Sedum: Die Sternkarten des Vessels sind genau. Er liegt hinter dem Nebel des Auges, weiter als wir je gedacht haben.",
    "Linum: Dann wird die Sonde Jahrtausende brauchen. Vielleicht gibt es dort niemanden mehr, der sie liest.",
    "Sedum: Vielleicht. Aber wenn doch, verirrt sich wenigstens kein zweites Vessel in den Dornen.",
), [("ZEKISAE_NAVI_ZWEIFEL", [1, 2, 3, 4])])

# ------------------------------------------------------------------ launch module (Startmodul)
text("Start_Bau.xml", "Aufzeichnung im Startmodul: wie die Einheit gebaut wurde", chain(
    "Erica: Die letzte Ladung vom Konstruktionshof ist da. Niemand hat gefragt, wofür die Schienen sind.",
    "Sedum: Gut. Die Hülle folgt den Plänen des Vessels. Es ist das Stärkste, was wir je gebaut haben.",
    "Erica: Und der Kern? Ein gewöhnlicher Warpkern hält die Energie eines Sterns nicht aus.",
    "Sedum: Ich habe den Entwurf des fortgeschrittenen Warpkerns aus den Rettungskapseln abgeschrieben. Er wird sie halten.",
    "Erica: Pye wird wütend sein. Sedum: Pye wird es verstehen, wenn die Clans uns antworten.",
), [("ZEKISAE_START_BAU", [1, 2]), ("ZEKISAE_START_KERN", [3, 4, 5])])

text("Start_Sonde.xml", "Computer im Startmodul: die Nutzlast", chain(
    "STARTMODUL. Nutzlast: eine Ersatzsonde der Orbitalen Sondenkanone, umgebaut für interstellare Entfernungen.",
    "Botschaft an Bord: »An alle Clans: Wir sind dem Signal des Auges gefolgt. Unser Vessel ist in den Dornen zerschellt.«",
    "»Folgt dem Signal nicht durch die Dornen. Sucht einen anderen Weg. Wartet nicht auf uns.«",
    "Startfenster: Tod des Sterns. Flugdauer bis zum Heimatstern: unbekannt. Die Sonde verlässt die Kanone durch den Lauf.",
), [("ZEKISAE_START_SONDE", [1, 4]), ("ZEKISAE_BOTSCHAFT", [2, 3])])

# ------------------------------------------------------------------ navigation module (Navigationsmodul)
text("Navi_Ziel.xml", "Computer im Navigationsmodul: das Ziel", chain(
    "NAVIGATIONSMODUL. Ziel: der Heimatstern der Nomai.",
    "Position nach den Sternkarten des Vessels berechnet. Der Stern ist von hier aus nicht zu sehen; er liegt hinter dem Nebel, aus dem das Signal des Auges kam.",
    "Nötige Geschwindigkeit: ein Vielfaches dessen, was ein lebender Stern liefern kann.",
    "Lösung: die gesamte Energie eines sterbenden Sterns in einem einzigen Augenblick. Darum warten wir. – Sedum",
), [("ZEKISAE_NAVI_ZIEL", [1, 2]), ("ZEKISAE_NAVI_ENERGIE", [3, 4])])

text("Navi_Pye.xml", "Pyes Aufzeichnung im Navigationsmodul", chain(
    "Hier spricht Pye. Sedum, ich habe deine Pläne gesehen. Die Antwort ist nein.",
    "Wir haben die Sonnenstation gebaut, um die Sonne zu zwingen. Sie hat versagt, und ich bin heute froh darüber.",
    "Das Aschezwilling-Projekt braucht den Tod der Sonne, wenn er kommt. Du würdest ihn stehlen.",
    "Unsere Clans werden uns finden oder nicht. Wir haben kein Recht, dafür alles andere zu opfern.",
    "Schalte die Einheit ab. Das ist keine Bitte.",
), [("ZEKISAE_PYE_VERBOT", [1, 2, 3, 4, 5])])

# ------------------------------------------------------------------ the three focus cannons (computer + recorder each)
text("Fokus_Alpha.xml", "Computer auf Fokuskanone Alpha", chain(
    "FOKUSKANONE ALPHA. Aufgabe: den Energiestrom des Sterns bündeln und in die Hauptkanone lenken.",
    "Ausrichtung: auf den Stern. Phasenkoppler: verbunden, auf dem Deck.",
    "Linum: Den ersten Koppler habe ich offen gelassen. Trenne ihn, dann erlischt die rote Leitung zur Hauptkanone.",
), [("ZEKISAE_FOKUS_ZWECK", [1, 2]), ("ZEKISAE_FOKUS_LEITUNG", [3])])

text("Fokus_Alpha_Erica.xml", "Ericas Aufzeichnung auf Fokuskanone Alpha", chain(
    "Hier spricht Erica. Ich habe die Schwerkraftkanone von Ember Twin dreimal vermessen.",
    "Dort wirft sie Fähren ins All. Hier soll sie Licht werfen – den Strom eines ganzen Sterns.",
    "Sedum will um jede Kanone ein Gerüst mit drei Dornen. Er sagt, der Stern soll sehen, wer ihn nimmt.",
), [("ZEKISAE_FOKUS_BAU", [1, 2, 3])])

text("Fokus_Beta.xml", "Computer auf Fokuskanone Beta", chain(
    "FOKUSKANONE BETA. Ausrichtung: auf den Stern, parallel zur Hauptkanone.",
    "Sedum: Die drei Kanonen bilden ein Dreieck. Nur gemeinsam halten sie den Strom eines ganzen Sterns.",
    "Linum: Den zweiten Koppler habe ich nach oben gebracht, unter den Emitter. Sedum klettert dort nie hinauf.",
), [("ZEKISAE_FOKUS_DREIECK", [1, 2]), ("ZEKISAE_FOKUS_OBEN", [3])])

text("Fokus_Beta_Sedum.xml", "Sedums Aufzeichnung auf Fokuskanone Beta", chain(
    "Hier spricht Sedum. Die Einheit muss immer auf die Sonne zielen. Sie folgt ihr, solange niemand an Bord ist.",
    "Wenn der Stern stirbt, trinken Linse und Emitter sein Licht. Danach wendet sich die Kanone ab, zu den Sternen, und schießt.",
    "Ein Stern für eine Botschaft. Ich halte das für einen gerechten Tausch.",
), [("ZEKISAE_FOKUS_SONNE", [1, 2, 3])])

text("Fokus_Gamma.xml", "Computer auf Fokuskanone Gamma", chain(
    "FOKUSKANONE GAMMA. Bereit.",
    "Phasenkoppler: verbunden. Ort: nicht auf dem Deck.",
    "Linum: Der dritte Koppler hängt unter dem Kiel, in der Leere. Dort sucht niemand.",
), [("ZEKISAE_FOKUS_UNTEN", [2, 3])])

text("Fokus_Gamma_Linum.xml", "Linums Aufzeichnung auf Fokuskanone Gamma", chain(
    "Linum: Sedum, wenn du dies je liest: Es tut mir leid.",
    "Ich habe deine Koppler versteckt, damit nur jemand sie findet, der wirklich sucht.",
    "Ein Weg zu den Sternen ist nichts wert, wenn dafür alle enden, die ihn gehen könnten. Niemand darf das Ende eines anderen wählen.",
), [("ZEKISAE_LINUM_REUE", [1, 3]), ("ZEKISAE_FOKUS_VERSTECK", [2])])

# ------------------------------------------------------------------ traces on the other planets
text("ET_Erica.xml", "Aufzeichnung auf Ember Twin: Erica vermisst die Schwerkraftkanone", chain(
    "Erica: Das ist sie, die Schwerkraftkanone. Sie wirft unsere Fähren bis hinauf zur Sonnenstation.",
    "Sedum braucht drei davon, aber nicht für Fähren. Er sagt mir nicht, wofür.",
    "Ich habe jedes Maß abgeschrieben. Morgen fliege ich zum Konstruktionshof auf Giant's Deep.",
), [("ZEKISAE_SPUR_ET", [1, 2, 3])])

text("Attlerock_Linum.xml", "Aufzeichnung auf dem Attlerock: Linum misst die Sonne", chain(
    "Linum: Vom Mond aus sieht man die Sonne ohne Wolken.",
    "Ich habe sie hundert Tage lang gemessen. Sie altert. In ein paar hunderttausend Jahren wird sie sterben.",
    "Sedum sagt, seine Einheit kann so lange warten. Ich frage mich, wer dann noch da ist, um sie aufzuhalten.",
), [("ZEKISAE_SPUR_ATTLE", [1, 2, 3])])

text("GD_Linum.xml", "Aufzeichnung im Kern von Giant's Deep: Linum beim Sondenverfolgungsmodul", chain(
    "Linum: Hier unten im Kern liegt das Modul, das die Sonden der Kanone verfolgt.",
    "Die ersten Schüsse haben das Auge nicht gefunden. Sedum nimmt das als Beweis, dass es nicht in diesem System liegt.",
    "Ich nehme es als Grund, weiterzusuchen – nicht als Grund, die Sonne zu opfern.",
), [("ZEKISAE_SPUR_GD", [1, 2, 3])])

text("BH_Pye.xml", "Aufzeichnung auf Brittle Hollow: Pyes Versammlung", chain(
    "Pye: Versammlung der Ältesten. Sedums Antrag: eine Einheit, die einem sterbenden Stern seine Energie nimmt, um eine Sonde zur Heimat zu schicken.",
    "Beschluss: abgelehnt. Die Sonnenstation war unser letzter Versuch, eine Sonne zu zwingen.",
    "Sedum hat den Saal ohne ein Wort verlassen. Ich fürchte, er baut trotzdem.",
), [("ZEKISAE_SPUR_BH", [1, 2, 3]), ("ZEKISAE_RUMOR", [1, 3])])


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
