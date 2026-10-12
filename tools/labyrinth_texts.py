# -*- coding: utf-8 -*-
"""
Gneis's notes in "Das Dornenlabyrinth" (Zeki.Dornenlabyrinth): New Horizons dialogue trees on the floating rafts in
the Vorhof, the Wrackkammer and on the Herzpfad. Every note reveals the ship log facts it tells about.

Usage:  python tools/labyrinth_texts.py [path/to/Zeki.Dornenlabyrinth]
"""
import os
import sys
from xml.sax.saxutils import escape

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Dornenlabyrinth"))
SCHEMA = ('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
          'xsi:noNamespaceSchemaLocation="https://raw.githubusercontent.com/Outer-Wilds-New-Horizons/new-horizons/main/NewHorizons/Schemas/dialogue_schema.xsd"')

# name -> (title, pages, facts revealed by reading it)
NOTES = {
    "Gneis_Farben": ("Notiz auf einem Floß", [
        "WER DAS LIEST: MERK DIR DIE FARBEN.",
        "Ich bin Gneis. Ich bin mit meinem Schiff in diesen Samen geflogen, weil er so schön grün geleuchtet hat. Das war ein Fehler.",
        "Die Knoten hier drin führen jedes Mal woanders hin. Aber manche tragen einen leuchtenden Kranz, und dessen Farbe lügt nie.",
        "GRÜN bringt dich hierher zurück, in den Vorhof. Von hier aus kommst du durch die Wand nach draußen.",
        "ROT heißt: Da wohnt ein Anglerfisch. Licht aus, langsam fliegen. Besser gar nicht erst hinein.",
        "GELB führt ganz woanders hin, nämlich in die echten Dimensionen von Dark Bramble. Von dort geht es nur durch Dark Bramble selbst wieder hinaus.",
        "LILA zieht nach innen. Wer dem Lila folgt, dem wird es immer wärmer und stiller. Ich glaube, da drin schlägt etwas.",
        "Wer sich verirrt, fliegt einfach durch die Wand zurück. Das Labyrinth merkt sich, woher man kam. Meistens.",
        "– Gneis",
    ], ["ZEKIDL_FARBE_GRUEN", "ZEKIDL_FARBE_ROT", "ZEKIDL_FARBE_GELB", "ZEKIDL_FARBE_LILA", "ZEKIDL_GNEIS_RUMOR", "ZEKIDL_HERZ_RUMOR"]),
    "Gneis_Wrack": ("Notiz am Wrack", [
        "Das ist mein Schiff. Beziehungsweise: Das war es.",
        "Ich bin durch einen roten Knoten geflogen, bevor ich die Farben kannte. Der Anglerfisch hat das Heck erwischt, und ich bin mit den Resten hierher getrieben.",
        "Das Skelett war schon da, als ich kam. Ein Nomai. Die Nomai waren also auch hier, und sie haben es auch nicht hinausgeschafft.",
        "Seitdem fliege ich mit dem Anzug weiter. Der Anzug hält, die Vorräte nicht mehr lange.",
        "– Gneis",
    ], ["ZEKIDL_GNEIS_WRACK"]),
    "Gneis_Herzpfad": ("Notiz im lila Nebel", [
        "Lila Nebel. Ich bin nah dran.",
        "Ich habe die lila Knoten gezählt: neun Stück vom Vorhof bis zum Herz, wenn man keinen Fehler macht. In einer Spiegelkammer verliert man den Faden, dann geht das Zählen wieder von vorne los.",
        "Hinter dem letzten lila Knoten schlägt das Herz des Labyrinths. Es singt. Die Anglerfische hören es und werden still.",
        "Wer es nimmt, bringt das Labyrinth zum Bluten, sagt das Singen. Dann ist jeder Weg rot, nur der grüne nach Hause nicht.",
        "Ich nehme es mit. Ich bringe es hinaus. Ich will die Sonne noch einmal sehen.",
        "– Gneis (seine letzte Notiz)",
    ], ["ZEKIDL_GNEIS_HERZPFAD", "ZEKIDL_HERZ_RUMOR_SINGT"]),
}


def write_all():
    for name, (title, pages, facts) in NOTES.items():
        xml = ['<?xml version="1.0" encoding="utf-8"?>', f"<DialogueTree {SCHEMA}>", f"  <NameField>{escape(title)}</NameField>",
               "  <DialogueNode>", "    <Name>START</Name>", "    <EntryCondition>DEFAULT</EntryCondition>", "    <Dialogue>"]
        xml += [f"      <Page>{escape(p)}</Page>" for p in pages]
        xml += ["    </Dialogue>", "    <RevealFacts>"]
        xml += [f"      <FactID>{f}</FactID>" for f in facts]
        xml += ["    </RevealFacts>", "  </DialogueNode>", "</DialogueTree>"]
        path = os.path.join(MOD, "planets", "dialogue", name + ".xml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(xml) + "\n")


if __name__ == "__main__":
    write_all()
