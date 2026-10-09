# -*- coding: utf-8 -*-
"""
Source of all Nomai texts of the Schleiersystem story. Writes planets/text/*.xml.

Layout rules (checked by schleier_validate.py):
  * whiteboards: at most 3 blocks - NH lays arcs out in a 5.4 x 3.6 m field, a whiteboard is far smaller
  * "Bodenschrift" (wall text lying on a plaza floor): at most 6 blocks
  * recorders/computers: linear chains; pre-crash computers have only 5 rings

Usage:  python tools/schleier_texts.py [path/to/Zeki.Schleiersystem]
"""
import os
import sys
from xml.sax.saxutils import escape

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Schleiersystem"))
SCHEMA = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="https://raw.githubusercontent.com/Outer-Wilds-New-Horizons/new-horizons/main/NewHorizons/Schemas/text_schema.xsd"'

TEXTS = {}


def text(name, comment, blocks, reveals=()):
    TEXTS[name] = (comment, blocks, list(reveals))


def chain(*texts):
    """Linear chain for recorders and computers: every block follows the previous one."""
    return [(i + 1, i if i else None, t) for i, t in enumerate(texts)]


# =============================================================== Hearthian system: the probe
text("Sonde_Aufzeichnung.xml", "Recorder an der abgestürzten Sonde (Schleiersignal, Sonnensystem)", chain(
    "[SIGNAL SCHWACH] … wiederhole … Hier spricht Ilex vom Clan des Zweiten Echos. Diese Sonde trägt unsere letzte Nachricht.",
    "An unsere Geschwister auf dem großen Schiff: Wir sind nicht dem Auge gefolgt, sondern seinem Echo. Es hat uns in ein System geführt, das von außen niemand sehen kann. Wir nennen es den Schleier.",
    "Der Schleier lässt alles herein, aber nichts hinaus. Unser Schiff, die Laterne, verlor beim Eintritt seinen Warpkern und wurde von einem Dornenplaneten verschlungen. Nur unsere Kapseln entkamen. [DATENFEHLER]",
    "Drei Welten umkreisen den blassen Stern, dazu der Dorn. Auf der inneren bündelt Tansy das Sternenlicht. Auf der Welt der stillen Wasser bewahrt Sorrel unser Archiv. Die äußere zerbricht – in ihrem Herzen liegt der Grund für all das.",
    "Uns bleibt nicht viel Zeit. [SIGNALVERLUST] … das System vergisst, wo es ist, wenn niemand von außen hinsieht. Es braucht ein Auge, das nicht zu uns gehört.",
    "Die Koordinaten des Schleiers sind in dieser Sonde gespeichert. Ein Warpantrieb kann ihnen folgen. Wer auch immer du bist: Bitte komm. Sieh uns an. [AUFZEICHNUNG ENDE]",
), [("ZEKSCHLEIER_RECORDING_1", [1, 2]), ("ZEKSCHLEIER_RECORDING_2", [1, 2, 3, 4]), ("ZEKSCHLEIER_WARP_UNLOCKED", [1, 2, 3, 4, 5, 6])])

text("Sonde_Protokoll.xml", "Whiteboard neben der Sonde: Boragos Startprotokoll", [
    (1, None, "Borago: Sonde Nummer elf. Die zehn vor ihr sind in den Stern zurückgefallen. Ich habe sie so klein gebaut, dass der Schleier sie vielleicht übersieht."),
    (2, 1, "Ilex: Richte sie auf das Signal des Auges. Wenn unsere Geschwister irgendwo sind, dann dort."),
    (3, 2, "Borago: Und wenn sie niemand findet? – Ilex: Dann fliegt sie eben weiter. Eine Nachricht, die niemand liest, ist immer noch mehr als Schweigen."),
], [("ZEKSCHLEIER_SONDE_ELF", [1, 2])])

# =============================================================== Schleierkern
text("Kern_Beobachtung.xml", "Bodenschrift im Observatorium: der flackernde Stern", [
    (1, None, "Tansy: Die Messungen sind eindeutig. Der Stern flackert – aber nur in den Aufzeichnungen, die niemand sofort liest."),
    (2, 1, "Sorrel: Du meinst, er verändert sich, wenn wir nicht hinsehen?"),
    (3, 2, "Tansy: Nicht nur der Stern. Der äußere Planet stand gestern ein winziges Stück neben seiner berechneten Bahn. Kein Messfehler."),
    (4, 3, "Ilex: Dann ist der Schleier weder Nebel noch Staub. Er ist eine Quantenhülle um das ganze System. Was niemand sieht, ist nicht festgelegt."),
    (5, 2, "Yarrow: Dann gucke ich ab jetzt ganz fest hin!"),
], [("ZEKSCHLEIER_KERN_DRIFT", [1, 2, 3]), ("ZEKSCHLEIER_SCHLEIER_NATUR", [1, 2, 3, 4])])

text("Kern_Lichtbuendler.xml", "Computer am Lichtbündler: Tansys Versuchsprotokoll", chain(
    "LICHTBÜNDLER – PROTOKOLL. Spiegelring ausgerichtet. Ziel: das Herz des äußeren Planeten.",
    "Versuch 1: Sternenlicht gebündelt und auf das Herz gerichtet. Die Splitter des Bruchs wandern weiter.",
    "Versuch 7: Intensität verdreifacht. Keine Wirkung. Die Splitter bewegen sich, sobald keiner von uns in ihrer Nähe ist.",
    "Versuch 12: Abgebrochen. Ergebnis: Licht ist kein Beobachter. Ein Auge ohne Geist ist nur ein Fenster.",
    "Notiz: Ilex will selbst ins Herz hinabsteigen. Ich habe den Warp am Ufer des Archivs dafür ausgerichtet. Ich wünschte, ich hätte es nicht getan.",
), [("ZEKSCHLEIER_KERN_LICHTBUENDLER", [1, 2]), ("ZEKSCHLEIER_KERN_FEHLSCHLAG", [1, 2, 3, 4]), ("ZEKSCHLEIER_HERZ_RUMOR", [1, 2, 3, 4, 5])])

text("Kern_Tansy.xml", "Recorder neben Tansys Überresten", chain(
    "Hier ist Tansy. Die anderen sind zum Archiv zurückgekehrt. Ich bleibe beim Lichtbündler.",
    "Ilex ist jetzt seit drei Umläufen im Herz. Die Splitter halten still. Es funktioniert – solange Ilex wach bleibt.",
    "Ich richte den Spiegelring jede Nacht neu aus, damit Ilex dort unten wenigstens ein wenig Licht hat. Mehr kann ich nicht tun.",
    "Wer auch immer dies findet: Entzünde den Lichtbündler wieder, wenn der Schleier fällt. Ilex soll nicht im Dunkeln sein.",
), [("ZEKSCHLEIER_KERN_TANSY", [1, 2, 3, 4])])

text("Kern_Werkstatt.xml", "Whiteboard in Tansys Werkstatt: die Sonnenwacht", [
    (1, None, "Tansy: Von hier aus sehe ich das Flackern nur verschwommen. Ich brauche Messungen ganz nah am Stern."),
    (2, 1, "Borago: Dann verankern wir eine Wache an dem kleinen Felsen, der dicht um den Stern kreist."),
    (3, 2, "Tansy: Der Warp im Resonanzfeld führt hinauf. Haltet euch von der Glut fern, wenn ihr hinüberwechselt."),
], [("ZEKSCHLEIER_WACHT_RUMOR", [1, 2, 3])])

text("Kern_Wegweiser.xml", "Steinmännchen am Grat", [
    (1, None, "Tansy: Zum Observatorium immer dem Grat folgen und nicht in die Spalten fallen. Damit bist du gemeint, Borago."),
])

text("Kern_Resonator.xml", "Wegmarke im Resonanzfeld (Kinderschrift)", [
    (1, None, "Yarrow: Tansy sagt, die Kristalle hier singen, wenn das Sternenlicht sie trifft. Ich höre nichts. Aber ich habe trotzdem ganz lange zugehört."),
], [("ZEKSCHLEIER_KERN_RESONATOR", [1])])

# =============================================================== Schleiersee
text("See_Ankunft.xml", "Bodenschrift auf dem Platz der Siedlung: die Ankunft", [
    (1, None, "Ilex: Wir haben es geschafft. Die Kapsel hat die Wasserwelt erreicht. Aber die Laterne ist verloren – der Dornenplanet hat sie verschlungen."),
    (2, 1, "Sorrel: Hier gibt es Wasser und Bäume. Wir können atmen. Wir können bleiben, bis wir verstehen, was geschehen ist."),
    (3, 2, "Borago (über Funk vom Dorn): Bleiben? Das Echo, dem wir gefolgt sind, war falsch. Das Auge ist nicht hier. Es war nie hier."),
    (4, 3, "Ilex: Vielleicht nicht. Aber irgendetwas hat uns hierher gerufen. Und ich will wissen, was."),
    (5, 2, "Yarrow: Darf ich zu der kleinen Insel schwimmen? Myrte war schon da!"),
], [("ZEKSCHLEIER_LATERNE", [1]), ("ZEKSCHLEIER_ECHO_FALSCH", [1, 2, 3]), ("ZEKSCHLEIER_KINDER_RUMOR", [1, 2, 5])])

text("See_Kapsel.xml", "Whiteboard an Kapsel 2: die drei Kapseln", [
    (1, None, "Sorrel: Als die Laterne in den Dorn gezogen wurde, lösten sich drei Kapseln. Wir in Kapsel 2 erreichten diese Welt."),
    (2, 1, "Sorrel: Kapsel 1 mit Borago, Hysop und Kerria stürzte auf den Dorn selbst. Sie leben – wir hören ihren Notruf."),
    (3, 2, "Sorrel: Von Kapsel 3 und Melisse fehlt jede Spur. Ihr Signal kommt aus dem Inneren des Dorns."),
], [("ZEKSCHLEIER_KAPSEL2_LOG", [1]), ("ZEKSCHLEIER_DORN_RUMOR", [1, 2]), ("ZEKSCHLEIER_KAPSEL3_RUMOR", [1, 2, 3])])

text("See_Geschwister.xml", "Whiteboard im Archiv: die Trennung vom großen Clan", [
    (1, None, "Sorrel: Für das Archiv. Wir verließen die Heimat gemeinsam mit dem großen Clan. Sie folgten mit ihrem Schiff dem stärksten Signal des Auges."),
    (2, 1, "Sorrel: Wir aber hörten ein zweites, schwächeres Signal. Ilex hielt es für ein Echo, das uns auf einem anderen Weg zum Auge führen würde."),
    (3, 2, "Ilex: Ich bereue es nicht. Aber ich hoffe jeden Tag, dass unsere Geschwister das Auge gefunden haben – und nicht in dieselbe Falle gesprungen sind wie wir."),
], [("ZEKSCHLEIER_SEE_SCHWESTERN", [1, 2])])

text("See_Archiv.xml", "Computer im Archiv: Sorrels Chronik", chain(
    "ARCHIV DES ZWEITEN ECHOS. Eintrag 1: Die Splitter des äußeren Planeten wandern. Wer sie beobachtet, hält sie fest.",
    "Eintrag 2: Ohne einen Beobachter von außen verliert das ganze System seinen Ort. Der äußere Planet zerbricht zuerst, denn sein Herz ist ein einziger gewaltiger Splitter.",
    "Eintrag 3: Tansys Lichtbündler auf der inneren Welt ist gescheitert. Borago baut auf dem äußeren Planeten Sonden, die den Schleier verlassen sollen.",
    "Eintrag 4: Ilex ist über den Warp am unteren Ufer ins Herz gegangen. Seitdem ist das Herz still. Der Bruch hält. Wir warten.",
    "Eintrag 5: Wir haben aufgehört, die Umläufe zu zählen. Wer dies liest: Nimm den Warp am Ufer. Ilex wartet dort unten auf dich – auf irgendjemanden.",
), [("ZEKSCHLEIER_SEE_ARCHIV", [1, 2]), ("ZEKSCHLEIER_KERN_RUMOR", [1, 2, 3]), ("ZEKSCHLEIER_BRUCH_RUMOR", [1, 2, 3]),
    ("ZEKSCHLEIER_HERZ_WEG", [1, 2, 3, 4, 5])])

text("See_Augenlid.xml", "Bodenschrift am unteren Ufer", [
    (1, None, "Ilex: Ich schreibe dies dorthin, wo es nur findet, wer wirklich sucht."),
    (2, 1, "Ilex: Der Schleier ist nicht unser Feind. Er ist wie ein Augenlid, das sich über diesem System geschlossen hat."),
    (3, 2, "Ilex: Wir können es nicht von innen öffnen. Das kann nur jemand, der von außen kommt."),
], [("ZEKSCHLEIER_SEE_AUGENLID", [1, 2, 3])])

text("See_Kinder.xml", "Bodenschrift auf Yarrows Insel (Kinderschrift)", [
    (1, None, "Yarrow: Myrte sagt, die Sterne draußen gibt es gar nicht mehr, weil wir sie nicht sehen können."),
    (2, 1, "Myrte: Das hab ich nicht gesagt! Ich hab gesagt, VIELLEICHT gibt es sie nicht mehr."),
    (3, 2, "Yarrow: Ilex sagt, sie sind noch da. Sie können uns nur nicht sehen. Das ist etwas anderes."),
    (4, 3, "Myrte: Und wenn uns niemand sieht – sind wir dann auch nicht mehr da?"),
    (5, 4, "Yarrow: Doch. Wir sehen uns ja gegenseitig. Das zählt auch."),
], [("ZEKSCHLEIER_SEE_KINDER", [1, 2, 3, 4, 5])])

text("See_Steinturm.xml", "Steinmännchen auf Yarrows Insel", [
    (1, None, "Yarrow: Das ist mein Steinturm. Bitte nicht umwerfen. Und wenn doch, bau ihn wieder auf!"),
])

text("See_Epilog.xml", "Epilog: erscheint erst, wenn sich der Schleier gehoben hat", [
    (1, None, "Sorrel: Diese Worte waren immer hier. Sie waren nur nicht beobachtet. Jetzt, da sich der Schleier gehoben hat, kannst du sie lesen."),
    (2, 1, "Sorrel: Der Lichtbündler brennt wieder, so wie Tansy es sich gewünscht hat. Ilex ist nicht mehr im Dunkeln."),
    (3, 2, "Sorrel: Unser Echo hat uns nicht zum Auge geführt. Aber es hat dich zu uns geführt. Vielleicht ist das dasselbe."),
    (4, 2, "Yarrow: Siehst du? Ich hab doch gesagt, dass es zählt!"),
], [("ZEKSCHLEIER_EPILOG", [1, 2, 3])])

# =============================================================== Schleierbruch
text("Bruch_Signalturm.xml", "Bodenschrift am Signalturm: die Sonden", [
    (1, None, "Borago: Der Signalturm steht. Von hier aus schicken wir die Sonden durch den Schleier – oder versuchen es zumindest."),
    (2, 1, "Borago: Sonde vier: zurückgefallen. Sonde sieben: zurückgefallen. Sonde zehn: in den Stern gestürzt."),
    (3, 2, "Ilex: Dann bauen wir eine elfte. Kleiner. Leiser. Etwas, das der Schleier übersieht."),
    (4, 3, "Borago: Die elfte ist gestartet. Ich höre ihr Signal nicht mehr. Ich weiß nicht, ob das ein gutes Zeichen ist."),
    (5, 1, "Tansy: Richte den Turm auf das Signal des Auges aus. Wenn irgendwer zuhört, dann dort."),
], [("ZEKSCHLEIER_BRUCH_SONDEN", [1, 2, 3]), ("ZEKSCHLEIER_BRUCH_ELF", [1, 2, 3, 4])])

text("Bruch_Abschied.xml", "Bodenschrift am Signalturm: Ilex' Entscheidung", [
    (1, None, "Borago: Du willst allein ins Herz? Für wie lange? Bis du stirbst?"),
    (2, 1, "Ilex: So lange, bis jemand von außen kommt. Solange ich hinsehe, zerbricht der Bruch nicht weiter."),
    (3, 2, "Borago: Und wenn niemand kommt?"),
    (4, 3, "Ilex: Dann habe ich euch Zeit geschenkt. Das ist genug."),
    (5, 3, "Tansy: Ich halte das Licht für dich an, Ilex. Jede Nacht."),
], [("ZEKSCHLEIER_BRUCH_ABSCHIED", [1, 2, 3, 4])])

text("Bruch_Splitter.xml", "Wegmarke im Splitterfeld", [
    (1, None, "Borago: Nicht wegsehen! Die Splitter wandern, sobald niemand hinsieht. Wer hier steht und schaut, hält sie fest."),
], [("ZEKSCHLEIER_SPLITTER", [1])])

text("Bruch_Warnung.xml", "Steinmännchen am Rand des Schlunds", [
    (1, None, "Borago: Der Boden hier ist dünn wie Eierschale. Der Schlund führt hinab zum Herz – aber nur Ilex ist je hinuntergestiegen."),
])

text("Herz_Ilex.xml", "Ilex' letzte Aufzeichnung im Herz des Bruchs (Finale)", chain(
    "Hier spricht Ilex, aus dem Herz des Bruchs. Wenn du diese Aufzeichnung abspielst, bist du hier unten bei mir – oder bei dem, was von mir übrig ist.",
    "Ich bin hinabgestiegen, um das Herz zu beobachten. Solange ich hinsah, hielten die Splitter still. Der Bruch hörte auf zu zerbrechen.",
    "Aber kein Nomai lebt ewig. Irgendwann werden sich meine Augen schließen, und der Schleier wird uns wieder vergessen.",
    "Wir haben einen Fehler gemacht, als wir ein Auge suchten. Das Auge ist kein Ort. Das Auge ist der, der hinsieht.",
    "Du bist von außen gekommen. Du hast den Schleier durchschaut, als es niemand sonst konnte. Durch dich sind wir wieder irgendwo.",
    "Also sieh uns an. Erinnere dich an Tansy, Sorrel, Borago, Hysop, Kerria, Melisse, Yarrow und Myrte. Und erzähl von uns – damit uns noch jemand sieht, wenn du längst weitergezogen bist.",
), [("ZEKSCHLEIER_HERZ_ILEX", [1, 2, 3]), ("ZEKSCHLEIER_FINALE", [1, 2, 3, 4, 5, 6])])

# =============================================================== Schleierdorn (bramble planet)
text("Dorn_Kapsel1.xml", "Computer in Kapsel 1 (Absturzstelle auf dem Dorn)", chain(
    "KAPSEL 1 – NOTFALLPROTOKOLL. Trennung von der Laterne erfolgreich. Insassen: Borago, Hysop, Kerria.",
    "Steuerung ausgefallen. Die Kapsel wird von der Oberfläche des Dornenplaneten angezogen. Aufprall unvermeidlich.",
    "Aufprall überstanden. Hülle beschädigt. Alle drei Insassen leben.",
    "Notruf aktiv. Antwort von Kapsel 2 empfangen: Sie haben die Wasserwelt erreicht. Kein Signal von Kapsel 3.",
    "Letzte Peilung der Laterne: im Inneren des Dorns, hinter dem großen Schlund. Sie sendet nicht mehr.",
), [("ZEKSCHLEIER_KAPSEL1_LOG", [1, 2, 3]), ("ZEKSCHLEIER_LATERNE_RUMOR", [1, 2, 3, 4, 5])])

text("Dorn_Lager.xml", "Whiteboard im Lager bei Kapsel 1", [
    (1, None, "Hysop: Der Warp zum Archiv steht. Borago und ich gehen hinüber. Kerria, komm mit uns."),
    (2, 1, "Kerria: Nein. Melisse ist irgendwo dort drin, und die Laterne auch. Ich bleibe und finde einen Weg durch die Ranken."),
    (3, 2, "Hysop: Dann markiere deinen Weg. Wenn du nicht zurückkommst, folgen wir deinen Zeichen."),
], [("ZEKSCHLEIER_DORN_LAGER", [1, 2, 3])])

text("Dorn_Forschung.xml", "Bodenschrift in Kerrias Forschungsruine am Schlund", [
    (1, None, "Kerria: Der Dorn ist kein gewöhnlicher Planet. Er ist ein Samen, so groß wie eine Welt, und in ihm ist mehr Raum, als außen Platz hätte."),
    (2, 1, "Kerria: Hinter dem Schlund verzweigen sich die Ranken. Jeder Knoten führt in eine andere Kammer. Viele führen nirgendwohin."),
    (3, 2, "Kerria: Ich habe die Knoten nach ihrem Licht benannt. GOLD führt tiefer, zur Laterne. BLAU führt zu meinem Lager."),
    (4, 3, "Kerria: ROT – niemals. Dort lebt etwas Blindes, Großes. Es hört jedes Geräusch."),
    (5, 2, "Hysop: Melisses Notruf ist auf dem Signalskop zu hören, wenn man nah genug an einem Knoten ist. Folgt ihm."),
], [("ZEKSCHLEIER_LAB_RUMOR", [1, 2]), ("ZEKSCHLEIER_LAB_WEG", [1, 2, 3, 4])])

text("Dorn_Abschied.xml", "Steinmännchen am Schlund", [
    (1, None, "Kerria: Ich bin hineingegangen. Wartet nicht auf mich – aber folgt dem goldenen Licht, wenn ihr mich sucht."),
])

# =============================================================== Labyrinth
text("Lab_Halle.xml", "Wegmarke in der Dornenhalle", [
    (1, None, "Kerria: Gold für die Laterne. Blau für mein Lager. Rot – niemals."),
], [("ZEKSCHLEIER_LAB_FARBEN", [1])])

text("Lab_Rankengarten.xml", "Recorder in Kerrias Lager (Rankengarten)", chain(
    "Kerrias Lager, Tag zwölf. Ich habe die Halle, den Rankengarten und eine rote Kammer gefunden. Die rote Kammer betrete ich nie wieder.",
    "Die Ranken bewegen sich nicht, aber der Weg ändert sich trotzdem, wenn ich zu lange wegsehe. Der Schleier reicht bis hier herein.",
    "Melisses Signal kommt aus der goldenen Kammer. Ich gehe morgen hinein.",
    "Falls dies jemand hört: Ich habe meine Zeichen hinterlassen. Folge dem Gold.",
), [("ZEKSCHLEIER_LAB_KERRIA", [1, 2, 3, 4])])

text("Lab_Melisse.xml", "Aufzeichnung in Kapsel 3 (Kapselgrund)", chain(
    "Hier ist Melisse, Kapsel 3. Die Kapsel ist zwischen den Ranken festgefahren. Es ist dunkel und still.",
    "Ich sehe die Laterne nicht mehr, aber ich höre ihr Summen. Es kommt aus dem goldenen Licht hinter mir.",
    "Ich habe noch Luft für einige Stunden. Ich sende weiter, damit mich jemand findet.",
    "Wenn du kommst und ich bin nicht mehr hier: Die Laterne lebt noch. Bring sie nach Hause.",
), [("ZEKSCHLEIER_KAPSEL3_MELISSE", [1, 2, 3, 4])])

text("Lab_Echokammer.xml", "Recorder in der Echokammer", chain(
    "Melisse … nein, hier ist Kerria. Ich bin dem falschen Licht gefolgt.",
    "Etwas bewegt sich im Nebel. Es ist blind, aber es hört alles. Nicht den Antrieb benutzen. Langsam treiben.",
    "Ich kehre um. Wer dies hört: Verlasse diese Kammer, so leise du kannst.",
), [("ZEKSCHLEIER_ECHOKAMMER", [1, 2, 3])])

text("Lab_Laterne.xml", "Computer an der Laterne (Logbuch des Schiffes)", chain(
    "LOGBUCH DER LATERNE. Warpsprung zum Echo abgeschlossen. Ziel erreicht. Kein Auge gefunden.",
    "Warnung: Leistung des Warpkerns fällt. Ursache unbekannt. Ein Schleier umgibt das System.",
    "Warnung: starke Anziehung durch einen Dornenplaneten. Kurs nicht zu halten. Kapseln werden vorbereitet.",
    "Kapseln 1, 2 und 3 gestartet. Die Laterne treibt in die Ranken.",
    "Notiz von Kerria, viel später: Ich habe sie gefunden. Ihr Kern glimmt noch – genug für einen Sprung, wenn man die richtigen Koordinaten kennt.",
), [("ZEKSCHLEIER_LATERNE_LOG", [1, 2, 3, 4, 5])])

text("Lab_Kerria.xml", "Kerrias letzte Aufzeichnung neben der Laterne", chain(
    "Hier ist Kerria. Ich habe die Laterne erreicht. Melisse habe ich nicht mehr lebend gefunden.",
    "Ich habe Melisses Koordinaten des Schleiers in das Schiff eingegeben. Wer sie kennt, findet hierher zurück.",
    "Ich bleibe bei der Laterne. Sie war unser Zuhause. Jemand sollte bei ihr sein.",
), [("ZEKSCHLEIER_LATERNE_KERRIA", [1, 2, 3])])

# =============================================================== Kanonenwrack
text("Wrack_Protokoll.xml", "Computer im Wrack der Sondenkanone", chain(
    "SONDENKANONE – BAUPROTOKOLL. Gebaut von Borago und Hysop aus den Resten von Kapsel 1 und den Ranken des Dorns.",
    "Ziel: eine Sonde mit voller Kraft durch den Schleier schießen, hinaus zum Signal des Auges.",
    "Schuss ausgelöst. Die Sonde hat den Schleier erreicht …",
    "… und ist zurückgekommen. Mit derselben Kraft. Sie hat die Kanone zerrissen.",
    "Borago: Gewalt bringt uns nicht hinaus. Ich baue kleinere Sonden. Viele kleine. Vielleicht übersieht der Schleier eine.",
), [("ZEKSCHLEIER_WRACK_LOG", [1, 2, 3, 4]), ("ZEKSCHLEIER_WRACK_BORAGO", [1, 2, 3, 4, 5])])

text("Wrack_Tafel.xml", "Whiteboard auf dem Felsen beim Wrack", [
    (1, None, "Hysop: Die Sonde steckt noch im Fels. Sie ist exakt dorthin zurückgeflogen, wo wir sie abgeschossen haben."),
    (2, 1, "Borago: Wie ein Spiegel. Der Schleier gibt alles zurück, was wir ihm entgegenwerfen."),
    (3, 2, "Hysop: Dann müssen wir etwas finden, das er nicht zurückwirft."),
], [("ZEKSCHLEIER_WRACK_SPIEGEL", [1, 2, 3])])

# =============================================================== Sonnenwacht
text("Wacht_Messung.xml", "Computer der Sonnenwacht: Tansys Sternmessungen", chain(
    "SONNENWACHT – MESSREIHE. Beobachter anwesend: Tansy. Helligkeit des Sterns: stabil.",
    "Beobachter abwesend, Messung automatisch: Helligkeit schwankt um bis zu ein Zehntel.",
    "Beobachter wieder anwesend: Helligkeit sofort stabil. Die Schwankung verschwindet, sobald jemand hinsieht.",
    "Ergebnis: Der Stern ist nur so fest, wie wir ihn ansehen. Und wir sind nur wenige.",
    "Tansy: Wenn ich das Licht des Sterns bündeln könnte, würde es vielleicht für uns hinsehen. Ich baue einen Lichtbündler auf der inneren Welt.",
), [("ZEKSCHLEIER_WACHT_STERN", [1, 2, 3, 4]), ("ZEKSCHLEIER_WACHT_PLAN", [1, 2, 3, 4, 5])])

text("Wacht_Ilex.xml", "Recorder in der Sonnenwacht", chain(
    "Hier ist Ilex, auf der Sonnenwacht. Von hier aus kann man den Schleier sehen: ein feiner Schimmer, der das ganze System umschließt.",
    "Der Stern ist darin gefangen wie wir. Er strahlt und strahlt, und niemand außerhalb sieht sein Licht.",
    "Ich frage mich, ob irgendwo jemand gerade in unsere Richtung schaut – und nur Dunkelheit sieht.",
), [("ZEKSCHLEIER_WACHT_ILEX", [1, 2, 3])])


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
