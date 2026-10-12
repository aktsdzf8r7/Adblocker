# -*- coding: utf-8 -*-
"""
The bramble language of "Verdornt" (spec 2026-10-11, section 4): its words, its texts, where the texts grow and
where the word cores lie. Writes assets/sprache.json for the DLL (BrambleScript.cs, Logic/Vocabulary.cs).

The brambles speak in roots of words: the translator gives every verb as it hears it (infinitive), which is why a
translated text reads a little broken. Unknown words stay as the sounds the translator picks up.

Usage:  python tools/verdornt_sprache.py [path/to/Zeki.Verdornt]
"""
import json
import os
import re
import sys

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Verdornt"))

FACTS = ("ZEKIVD_SPRACHE_1", "ZEKIVD_SPRACHE_2", "ZEKIVD_SPRACHE_3", "ZEKIVD_SPRACHE_4")   # Tansy's notes (verdornt_texts.py)

# id, German, sound, sources ("grund" = known with the translator)
WORDS = [
    ("wir", "wir", "krrh", "grund"), ("licht", "Licht", "vael", "grund"), ("wachsen", "wachsen", "thorrn", "grund"),
    ("samen", "Samen", "ssk", "grund"), ("stern", "Stern", "ahl-vael", "grund"), ("weit", "weit", "oroom", "grund"),
    ("rufen", "rufen", "hhuun", "grund"), ("klein", "Kleinen", "tik", "grund"), ("hier", "hier", "dah", "grund"),
    ("nicht", "nicht", "nekh", "grund"),
    ("herz", "Herz", "marh", "fact:ZEKIVD_SPRACHE_1"), ("tragen", "tragen", "vrass", "fact:ZEKIVD_SPRACHE_1"),
    ("welten", "Welten", "gaar", "fact:ZEKIVD_SPRACHE_1"),
    ("hinaus", "hinaus", "essh", "fact:ZEKIVD_SPRACHE_2"), ("fremde", "Fremde", "zhiv", "fact:ZEKIVD_SPRACHE_2"),
    ("schlafen", "schlafen", "luum", "fact:ZEKIVD_SPRACHE_2"),
    ("hoeren", "hören", "shii", "fact:ZEKIVD_SPRACHE_3"), ("kern", "Kern", "dhuum", "fact:ZEKIVD_SPRACHE_3"),
    ("mutter", "Mutter", "maa-dhuum", "fact:ZEKIVD_SPRACHE_4"), ("kreis", "Kreis", "oro-oro", "fact:ZEKIVD_SPRACHE_4"),
    ("niemand", "niemand", "nekh-ohn", "fact:ZEKIVD_SPRACHE_4"),
    ("eis", "Eis", "kiirr", "kern:ERSTLING_1"), ("halten", "halten", "gripp", "kern:ERSTLING_1"),
    ("antworten", "antworten", "ha-ruun", "kern:ERSTLING_2"), ("warten", "warten", "ehhm", "kern:ERSTLING_2"),
    ("glut", "Glut", "rhaash", "kern:GLUT_1"), ("zerbrechen", "zerbrechen", "krak", "kern:GLUT_1"),
    ("waerme", "Wärme", "rhaa", "kern:GLUT_2"), ("brennen", "brennen", "rhaash-ka", "kern:GLUTPFORTE"),
    ("waechter", "Wächter", "ghorrm", "kern:NEBEL_1"), ("leben", "Leben", "vii", "kern:NEBEL_1"),
    ("wege", "Wege", "tharr", "kern:NEBEL_2"), ("geschwister", "Geschwister", "ssk-ssk", "kern:NEBEL_2"),
    ("hueten", "hüten", "gorrh", "kern:NEBELPFORTE"), ("singen", "singen", "lhaa", "kern:NEBELPFORTE"),
    ("masken", "Masken", "vesk", "kern:HOHL_1"), ("fallen", "fallen", "vuuh", "kern:HOHL_1"),
    ("einer", "Einer", "ohn", "kern:HOHL_2"),
    ("dunkel", "Dunkel", "umbr", "kern:HOHLPFORTE"), ("vergessen", "vergessen", "lethh", "kern:HOHLPFORTE"),
]

# id, title, lines
TEXTS = [
    ("Labor_Ruf", "Der Ruf des Herzens", [
        "{wir} {rufen}. {wir} {rufen} {weit}.",
        "{samen}, {wachsen}! {tragen} das {licht} {hinaus}.",
        "Das {herz} {rufen}, und die {samen} {antworten}.",
    ]),
    ("Erstling_Kluft", "Was der Riss sagt", [
        "{hier} {schlafen} {eis}. {wir} {halten} es.",
        "{nicht} {zerbrechen}. {wir} {halten}, bis das {herz} {rufen}.",
    ]),
    ("Glut_Ruf", "Gespräch mit der Glut", [
        "{glut}, {wir} {hoeren} dich.",
        "Deine {waerme} ist unsere {waerme}. Das {licht} des {stern} ist in dir.",
        "{wir} {zerbrechen} die {welten} {nicht}. {wir} {halten} sie.",
    ]),
    ("Glut_Schollen", "An die Schollen", [
        "Ihr Stücke, {nicht} {fallen}. {wir} {halten} euch.",
        "{wir} {tragen} euch, wie das {herz} uns {tragen}.",
    ]),
    ("Glut_Waerme", "Glutlied", [
        "{brennen}, {brennen}, {wachsen}.",
        "Wo {glut} ist, ist {leben}. Wo {leben} ist, {wachsen} {wir}.",
    ]),
    ("Nebel_Waechter", "An die Wächter", [
        "{waechter}, {hueten} die {wege}.",
        "Die {klein} {nicht} hinein. {nicht} zum {herz}.",
        "Wer {singen} kann, ist {nicht} {fremde}.",
    ]),
    ("Nebel_Lied", "Lied im Nebel", [
        "{geschwister}, {hoeren}! Im Nebel {singen} {wir}.",
        "Die {waechter} {singen} {nicht}. Sie {warten}.",
        "{einer} {singen} doch. Er spricht mit den {klein}.",
    ]),
    ("Hohl_Masken", "Über die Kleinen mit den Masken", [
        "Die {klein} mit den {masken} kamen. Drei. Sie {hoeren} uns.",
        "{einer} spricht mit {niemand}.",
        "{wir} zählten wieder: drei {masken}. Immer drei.",
    ]),
    ("Hohl_Vergessen", "Was der Samen vergaß", [
        "{wir} {vergessen} {nicht}. {wir} {schlafen} nur.",
        "Ein {samen} {fallen} ins {dunkel}. Er {schlafen} im {eis}, {weit}.",
        "Er {antworten} {nicht}. Aber er {wachsen}.",
    ]),
    ("Glutpforte_Text", "Pforte der Glut", [
        "{hier} {brennen} der Weg. {fremde}, {nicht} weiter. Noch {nicht}.",
    ]),
    ("Nebelpforte_Text", "Pforte im Nebel", [
        "{wege} im Nebel. Die {waechter} {warten}. {wir} {hoeren} dich, {fremde}.",
    ]),
    ("Hohlpforte_Text", "Pforte des Dunkels", [
        "Im {dunkel} {wachsen} der {kreis}. Die {mutter} im {kern} {rufen}.",
        "Der {kreis} {wachsen}, und doch {wachsen} er {weit}.",
    ]),
]

# where each text grows: body, anchor group, anchor name ("dim:<x,y,z>" for a fixed point in a dimension), standing or flat
TEXT_SPOTS = {
    "Labor_Ruf": ("Erstling", "wurzellabor", "schrift", False),
    "Erstling_Kluft": ("Erstling", "erstling", "schrift1", True),
    "Glut_Ruf": ("Glutdorn", "glutwerk", "schrift", False),
    "Glut_Schollen": ("Glutdorn", "glutdorn", "schrift1", False),
    "Glut_Waerme": ("Glutdorn", "glutdorn", "schrift2", True),
    "Nebel_Waechter": ("Nebelranke", "nebelranke", "schrift1", False),
    "Nebel_Lied": ("Nebelranke", "nebelranke", "schrift2", True),
    "Hohl_Masken": ("Hohlsamen", "hohlsamen", "schrift1", False),
    "Hohl_Vergessen": ("Hohlsamen", "hohlsamen", "schrift2", True),
    "Glutpforte_Text": ("Glutpforte", None, (40, -30, 60), False),
    "Nebelpforte_Text": ("Nebelpforte", None, (-50, 20, 40), False),
    "Hohlpforte_Text": ("Hohlpforte", None, (30, 40, -50), False),
}

# word cores: id -> body, anchor group, anchor name (or a fixed point in a dimension)
KERN_SPOTS = {
    "ERSTLING_1": ("Erstling", "erstling", "wortkern1"), "ERSTLING_2": ("Erstling", "erstling", "wortkern2"),
    "GLUT_1": ("Glutdorn", "glutdorn", "wortkern1"), "GLUT_2": ("Glutdorn", "glutdorn", "wortkern2"),
    "NEBEL_1": ("Nebelranke", "nebelranke", "wortkern1"), "NEBEL_2": ("Nebelranke", "nebelranke", "wortkern2"),
    "HOHL_1": ("Hohlsamen", "hohlsamen", "wortkern1"), "HOHL_2": ("Hohlsamen", "hohlsamen", "wortkern2"),
    "GLUTPFORTE": ("Glutpforte", None, (-60, 10, -40)), "NEBELPFORTE": ("Nebelpforte", None, (50, -40, -30)),
    "HOHLPFORTE": ("Hohlpforte", None, (-40, -20, 60)),
}


def language():
    return {
        "woerter": [{"id": i, "de": de, "laut": laut, "grund": q == "grund", "quellen": [] if q == "grund" else [q]}
                    for i, de, laut, q in WORDS],
        "texte": [{"id": i, "titel": t, "zeilen": z} for i, t, z in TEXTS],
    }


def check():
    """The same rules as Vocabulary.Validate in the DLL, at build time (Review Focus 4)."""
    ids = [w[0] for w in WORDS]
    assert len(ids) == len(set(ids)), "word ids twice"
    for i, _, z in TEXTS:
        for line in z:
            assert line.count("{") == line.count("}"), f"{i}: unbalanced braces"
            for w in re.findall(r"\{([^}]*)\}", line):
                assert w in ids, f"text {i} uses unknown word {w}"
    assert set(TEXT_SPOTS) == {t[0] for t in TEXTS}, "every text needs exactly one spot"
    kerns = {q[5:] for _, _, _, q in WORDS if q.startswith("kern:")}
    assert kerns <= set(KERN_SPOTS), f"word cores without a spot: {kerns - set(KERN_SPOTS)}"


def write_all(mod=MOD):
    check()
    path = os.path.join(mod, "assets", "sprache.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(language(), f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"bramble language: {len(WORDS)} words, {len(TEXTS)} texts")


if __name__ == "__main__":
    write_all()
