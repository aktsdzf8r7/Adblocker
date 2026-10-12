using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;

namespace ZekiVerdornt.Tests;

public class VocabularyTests
{
    private static readonly Word Wir = new() { id = "wir", de = "wir", laut = "krrh", grund = true };
    private static readonly Word Licht = new() { id = "licht", de = "Licht", laut = "vael", grund = true };
    private static readonly Dictionary<string, Word> Words = new() { ["wir"] = Wir, ["licht"] = Licht };

    [Fact]
    public void ParseSplitsWordsAndText()
    {
        var tokens = Vocabulary.Parse("{wir} tragen {licht}.");
        Assert.Equal(new[] { "wir", null, "licht", null }, tokens.Select(t => t.WordId).ToArray());
        Assert.Equal(" tragen ", tokens[1].Text);
        Assert.Equal(".", tokens[3].Text);
    }

    [Fact]
    public void ParseRejectsUnclosedBrace() => Assert.Throws<FormatException>(() => Vocabulary.Parse("{wir tragen"));

    [Fact]
    public void ParseRejectsEmptyBraces() => Assert.Throws<FormatException>(() => Vocabulary.Parse("a {} b"));

    [Fact]
    public void BaseWordsNeedTheTranslator()
    {
        Assert.False(Vocabulary.Learnable(Licht, _ => false, _ => false));
        Assert.True(Vocabulary.Learnable(Licht, c => c == Vocabulary.LanguageCondition, _ => false));
    }

    [Fact]
    public void FactSourceTeaches()
    {
        var herz = new Word { id = "herz", de = "Herz", laut = "marh", quellen = new List<string> { "fact:ZEKIVD_SPRACHE_1" } };
        Assert.False(Vocabulary.Learnable(herz, _ => true, _ => false));
        Assert.True(Vocabulary.Learnable(herz, _ => false, f => f == "ZEKIVD_SPRACHE_1"));
    }

    [Fact]
    public void KernSourceTeaches()
    {
        var waechter = new Word { id = "waechter", de = "Wächter", laut = "ghorrm", quellen = new List<string> { "kern:NEBEL_1" } };
        Assert.True(Vocabulary.Learnable(waechter, c => c == "ZEKIVD_WORTKERN_NEBEL_1", _ => false));
        Assert.False(Vocabulary.Learnable(waechter, c => c == Vocabulary.LanguageCondition, _ => true));
    }

    [Fact]
    public void RenderShowsSoundsForUnknownWords()
    {
        var pieces = Vocabulary.Render("{wir} tragen {licht}.", Words, id => id == "licht", true);
        Assert.Equal(4, pieces.Count);
        Assert.Equal(("krrh", false, true), (pieces[0].Text, pieces[0].Known, pieces[0].IsWord));
        Assert.Equal((" tragen ", true, false), (pieces[1].Text, pieces[1].Known, pieces[1].IsWord));
        Assert.Equal(("Licht", true, true), (pieces[2].Text, pieces[2].Known, pieces[2].IsWord));
        Assert.Equal((".", true, false), (pieces[3].Text, pieces[3].Known, pieces[3].IsWord));
    }

    [Fact]
    public void RenderWithoutTranslatorShowsOnlySounds()
    {
        var pieces = Vocabulary.Render("{wir} tragen {licht}.", Words, _ => true, false);
        Assert.Equal("krrh", pieces[0].Text);
        Assert.Equal("vael", pieces[2].Text);
        Assert.False(pieces[2].Known);
    }

    [Fact]
    public void ValidateRejectsUnknownWord()
    {
        var lang = new Language { woerter = new List<Word> { Wir }, texte = new List<ScriptText> { new() { id = "t", zeilen = new List<string> { "{wir} im {nebel}" } } } };
        var e = Assert.Throws<FormatException>(() => Vocabulary.Validate(lang));
        Assert.Contains("nebel", e.Message);
    }

    [Fact]
    public void ValidateRejectsDuplicateIds()
    {
        var lang = new Language { woerter = new List<Word> { Licht, new() { id = "licht", de = "Licht", laut = "x", grund = true } } };
        Assert.Throws<FormatException>(() => Vocabulary.Validate(lang));
    }

    [Fact]
    public void ValidateRejectsSourceWithoutPrefix()
    {
        var lang = new Language { woerter = new List<Word> { new() { id = "herz", de = "Herz", laut = "marh", quellen = new List<string> { "ZEKIVD_SPRACHE_1" } } } };
        Assert.Throws<FormatException>(() => Vocabulary.Validate(lang));
    }

    [Fact]
    public void WordConditionIsUpperCase() => Assert.Equal("ZEKIVD_WORT_LICHT", Vocabulary.WordCondition("licht"));
}
