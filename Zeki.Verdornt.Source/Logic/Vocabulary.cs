using System;
using System.Collections.Generic;
using System.Text;

namespace ZekiVerdornt;

/// <summary>A word of the bramble language (assets/sprache.json, written by tools/verdornt_sprache.py).</summary>
public class Word
{
    public string id, de, laut;
    /// <summary>A base word: known as soon as the overgrown translator was found.</summary>
    public bool grund;
    /// <summary>Where else it is learnt: "fact:&lt;ship log fact&gt;" or "kern:&lt;word core id&gt;".</summary>
    public List<string> quellen = new();
}

/// <summary>A text in bramble script: lines of German with {word} slots.</summary>
public class ScriptText
{
    public string id, titel;
    public List<string> zeilen = new();
}

public class Language
{
    public List<Word> woerter = new();
    public List<ScriptText> texte = new();
}

/// <summary>Fixed text (WordId null) or a word slot of a line.</summary>
public readonly struct Token
{
    public readonly string Text;
    public readonly string WordId;

    public Token(string text, string wordId)
    {
        Text = text;
        WordId = wordId;
    }
}

/// <summary>A piece of a rendered line: fixed text, a translated word, or the sounds of an unknown word.</summary>
public readonly struct Piece
{
    public readonly string Text;
    public readonly bool Known;
    public readonly bool IsWord;

    public Piece(string text, bool known, bool isWord)
    {
        Text = text;
        Known = known;
        IsWord = isWord;
    }
}

/// <summary>
/// The bramble language (spec 2026-10-11, section 4): which words can be learnt, and how a line reads with the
/// words the player knows. Unknown words stay as the brambles' sounds.
/// </summary>
public static class Vocabulary
{
    /// <summary>Set when the overgrown translator in the root lab was touched: the base words, and reading at all.</summary>
    public const string LanguageCondition = "ZEKIVD_DORNSPRACHE";

    /// <summary>The persistent condition that remembers a learnt word.</summary>
    public static string WordCondition(string id) => "ZEKIVD_WORT_" + id.ToUpperInvariant();

    /// <summary>The persistent condition a word core sets when touched.</summary>
    public static string KernCondition(string id) => "ZEKIVD_WORTKERN_" + id.ToUpperInvariant();

    public static List<Token> Parse(string line)
    {
        var tokens = new List<Token>();
        var text = new StringBuilder();
        for (var i = 0; i < line.Length; i++)
        {
            if (line[i] != '{')
            {
                text.Append(line[i]);
                continue;
            }
            var end = line.IndexOf('}', i + 1);
            if (end < 0) throw new FormatException($"Unclosed {{ in \"{line}\"");
            var id = line.Substring(i + 1, end - i - 1).Trim();
            if (id.Length == 0) throw new FormatException($"Empty {{}} in \"{line}\"");
            if (text.Length > 0) tokens.Add(new Token(text.ToString(), null));
            text.Clear();
            tokens.Add(new Token(id, id));
            i = end;
        }
        if (text.Length > 0) tokens.Add(new Token(text.ToString(), null));
        return tokens;
    }

    /// <summary>Whether the player has what teaches this word: the translator for a base word, or one of its sources.</summary>
    public static bool Learnable(Word w, Func<string, bool> condition, Func<string, bool> fact)
    {
        if (w.grund && condition(LanguageCondition)) return true;
        foreach (var q in w.quellen ?? new List<string>())
        {
            if (q.StartsWith("fact:") && fact(q.Substring(5))) return true;
            if (q.StartsWith("kern:") && condition(KernCondition(q.Substring(5)))) return true;
        }
        return false;
    }

    /// <summary>A line as it reads: known words in German (only once the player can translate at all), others as sounds.</summary>
    public static List<Piece> Render(string line, IReadOnlyDictionary<string, Word> words, Func<string, bool> known, bool canTranslate)
    {
        var pieces = new List<Piece>();
        foreach (var t in Parse(line))
        {
            if (t.WordId == null)
            {
                pieces.Add(new Piece(t.Text, true, false));
                continue;
            }
            var w = words[t.WordId];
            var k = canTranslate && known(w.id);
            pieces.Add(new Piece(k ? w.de : w.laut, k, true));
        }
        return pieces;
    }

    /// <summary>Throws on duplicate word ids, sources without "fact:"/"kern:", and texts using words that do not exist.</summary>
    public static void Validate(Language lang)
    {
        var ids = new HashSet<string>();
        foreach (var w in lang.woerter)
        {
            if (string.IsNullOrEmpty(w.id) || !ids.Add(w.id)) throw new FormatException($"Word id \"{w.id}\" is empty or twice.");
            foreach (var q in w.quellen ?? new List<string>())
                if (!q.StartsWith("fact:") && !q.StartsWith("kern:")) throw new FormatException($"Word {w.id}: source \"{q}\" needs fact: or kern:.");
        }
        foreach (var t in lang.texte)
            foreach (var line in t.zeilen)
                foreach (var token in Parse(line))
                    if (token.WordId != null && !ids.Contains(token.WordId))
                        throw new FormatException($"Text {t.id} uses unknown word {token.WordId}.");
    }
}
