using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.UI;

namespace ZekiVerdornt;

/// <summary>placements.json "schriften": where a text in bramble script grows.</summary>
public class ScriptPlacement
{
    public string name, body, parentPath, text;
    public Vector3Data position = new(), rotation = new();
    /// <summary>Grown flat on the ground instead of on a standing slab.</summary>
    public bool boden;
}

/// <summary>placements.json "wortkerne": a word core (the NH interaction volume beside it sets ZEKIVD_WORTKERN_&lt;ID&gt;).</summary>
public class KernPlacement
{
    public string id, body;
    public Vector3Data position = new(), rotation = new();
}

/// <summary>Marks a placed bramble script and the text it shows.</summary>
public class ScriptMarker : MonoBehaviour
{
    public string TextId;
    public bool Flat;

    public Vector3 Centre => transform.position + transform.up * (Flat ? 0.2f : 1.15f);
}

/// <summary>
/// The bramble language (spec 2026-10-11, section 4):
///   * places the scripts and word cores of this system (assets/sprache.json + placements.json),
///   * while the translator is drawn and aimed at a script within 6 m, shows a green translator window: known words in
///     German, unknown ones as the brambles' sounds; before the overgrown translator was touched, only sounds,
///   * every half second learns the words whose source the player has (Vocabulary.Learnable) and remembers them in
///     persistent conditions, announcing each word once.
/// </summary>
public class BrambleScript : MonoBehaviour
{
    private const float Reach = 6f, Cone = 12f;
    private static readonly Color Panel = new(0.05f, 0.12f, 0.07f, 0.82f);

    private ZekiVerdornt _mod;
    private Dictionary<string, Word> _words;
    private Dictionary<string, ScriptText> _texts;
    private readonly List<ScriptMarker> _scripts = new();
    private readonly List<(string id, GameObject go)> _kerne = new();
    private readonly HashSet<string> _known = new();
    private GameObject _window;
    private Text _title, _body;
    private ScriptMarker _shown;
    private int _version, _shownVersion = -1;
    private bool _canTranslate;
    private float _nextLearn;

    public static void Setup(ZekiVerdornt mod)
    {
        var file = Path.Combine(mod.ModHelper.Manifest.ModFolderPath, "assets/sprache.json");
        if (!File.Exists(file))
        {
            mod.Log("sprache.json fehlt – keine Dornensprache.", true);
            return;
        }
        Language lang;
        try
        {
            lang = JsonConvert.DeserializeObject<Language>(File.ReadAllText(file));
            Vocabulary.Validate(lang);
        }
        catch (Exception e)
        {
            mod.Log("sprache.json ist fehlerhaft: " + e.Message, true);
            return;
        }
        new GameObject("VD_Dornensprache").AddComponent<BrambleScript>().Init(mod, lang);
    }

    private void Init(ZekiVerdornt mod, Language lang)
    {
        _mod = mod;
        _words = lang.woerter.ToDictionary(w => w.id);
        _texts = lang.texte.ToDictionary(t => t.id);
        foreach (var s in ModelPlacer.Data.schriften ?? new List<ScriptPlacement>())
        {
            var parent = ModelPlacer.Parent(mod, s.body, s.parentPath);
            if (parent == null) continue;
            var go = ModelPlacer.Build(mod, new PropPlacement
            {
                model = s.boden ? "dornenschrift_boden" : "dornenschrift", name = s.name, body = s.body,
                position = s.position, rotation = s.rotation, collider = true
            }, parent);
            if (go == null) continue;
            var marker = go.AddComponent<ScriptMarker>();
            marker.TextId = s.text;
            marker.Flat = s.boden;
            _scripts.Add(marker);
        }
        foreach (var k in ModelPlacer.Data.wortkerne ?? new List<KernPlacement>())
        {
            var parent = ModelPlacer.Parent(mod, k.body, null);
            if (parent == null) continue;
            var go = ModelPlacer.Build(mod, new PropPlacement
            {
                model = "wortkern", name = "VD_Wortkern_Modell_" + k.id, body = k.body, position = k.position, rotation = k.rotation
            }, parent);
            if (go == null) continue;
            go.SetActive(!Condition(Vocabulary.KernCondition(k.id)));
            _kerne.Add((k.id, go));
        }
        foreach (var w in _words.Values)
            if (Condition(Vocabulary.WordCondition(w.id))) _known.Add(w.id);
        _canTranslate = Condition(Vocabulary.LanguageCondition);
        BuildWindow();
        mod.Log($"Dornensprache: {_words.Count} Wörter ({_known.Count} bekannt), {_scripts.Count} Schriften, {_kerne.Count} Wortkerne, " +
                $"Übersetzer {(_canTranslate ? "gefunden" : "nicht gefunden")}.");
    }

    private static bool Condition(string name) => PlayerData.GetPersistentCondition(name);

    public void Update()
    {
        if (Time.time >= _nextLearn)
        {
            _nextLearn = Time.time + 0.5f;
            Learn();
        }
        var target = Aimed();
        if (target != _shown || _shownVersion != _version)
        {
            _shown = target;
            _shownVersion = _version;
            if (target != null) Fill(target);
        }
        if (_window.activeSelf != (target != null)) _window.SetActive(target != null);
    }

    // ------------------------------------------------------------------------------------------ learning
    private void Learn()
    {
        var log = Locator.GetShipLogManager();
        var learnt = new List<string>();
        foreach (var w in _words.Values)
        {
            if (_known.Contains(w.id) || !Vocabulary.Learnable(w, Condition, f => log != null && log.IsFactRevealed(f))) continue;
            _known.Add(w.id);
            PlayerData.SetPersistentCondition(Vocabulary.WordCondition(w.id), true);
            learnt.Add(w.de);
        }
        var found = !_canTranslate && Condition(Vocabulary.LanguageCondition);
        if (found)
        {
            _canTranslate = true;
            log?.RevealFact(Vocabulary.LanguageFact, true, true);
            Crossing.PlayOneShot(AudioType.NomaiPowerOn);
            ZekiVerdornt.Notify($"DEIN ÜBERSETZER HÖRT JETZT DIE DORNEN. {_known.Count} WÖRTER DER DORNENSPRACHE BEKANNT.", 8f);
        }
        else if (learnt.Count > 0 && _canTranslate)
        {
            Crossing.PlayOneShot(AudioType.ToolTranslatorEquip);
            ZekiVerdornt.Notify((learnt.Count == 1 ? "NEUES WORT: " : "NEUE WÖRTER: ") + string.Join(", ", learnt).ToUpperInvariant(), 6f);
        }
        if (found || learnt.Count > 0)
        {
            _version++;
            _mod.Log($"Dornensprache: {_known.Count} von {_words.Count} Wörtern bekannt.");
        }
        foreach (var (id, go) in _kerne)
            if (go != null && go.activeSelf && Condition(Vocabulary.KernCondition(id))) go.SetActive(false);
    }

    // ------------------------------------------------------------------------------------------ reading
    /// <summary>The script the player aims the drawn translator at (nearest to the view centre), or null.</summary>
    private ScriptMarker Aimed()
    {
        var cam = Locator.GetPlayerCamera();
        var tools = Locator.GetToolModeSwapper();
        var dm = Locator.GetDeathManager();
        if (cam == null || tools == null || !tools.IsInToolMode(ToolMode.Translator)) return null;
        if (dm != null && (dm.IsPlayerDying() || dm.IsPlayerDead())) return null;
        ScriptMarker best = null;
        var bestAngle = Cone;
        foreach (var m in _scripts)
        {
            if (m == null || !m.gameObject.activeInHierarchy) continue;
            var to = m.Centre - cam.transform.position;
            if (to.magnitude > Reach) continue;
            var angle = Vector3.Angle(cam.transform.forward, to);
            if (angle < bestAngle)
            {
                bestAngle = angle;
                best = m;
            }
        }
        return best;
    }

    private void Fill(ScriptMarker m)
    {
        if (!_texts.TryGetValue(m.TextId, out var text)) return;
        _title.text = _canTranslate ? "DORNENSPRACHE – " + text.titel.ToUpperInvariant() : "UNBEKANNTE SPRACHE";
        var sb = new StringBuilder();
        foreach (var line in text.zeilen)
        {
            foreach (var p in Vocabulary.Render(line, _words, _known.Contains, _canTranslate))
            {
                if (!p.IsWord) sb.Append(_canTranslate ? p.Text : Punctuation(p.Text));
                else if (p.Known) sb.Append("<color=#E8FFE8>").Append(p.Text).Append("</color>");
                else sb.Append("<i><color=#7FD88A>").Append(p.Text).Append("</color></i>");
            }
            sb.Append('\n');
        }
        _body.text = sb.ToString().TrimEnd();
    }

    /// <summary>Without the overgrown translator the glue between the words is not German either: only its pauses stay.</summary>
    private static string Punctuation(string s) => new(s.Where(c => c is ' ' or '.' or ',' or '!' or '?' or ':' or '–').ToArray());

    private void BuildWindow()
    {
        _window = new GameObject("VD_Dornenfenster");
        _window.transform.SetParent(transform, false);
        var canvas = _window.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 500;
        var scaler = _window.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        var panel = new GameObject("Tafel", typeof(RectTransform));
        panel.transform.SetParent(_window.transform, false);
        var rt = (RectTransform)panel.transform;
        rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0f);
        rt.pivot = new Vector2(0.5f, 0f);
        rt.anchoredPosition = new Vector2(0, 120);
        rt.sizeDelta = new Vector2(1100, 300);
        var image = panel.AddComponent<Image>();
        image.color = Panel;
        image.raycastTarget = false;
        var font = Resources.FindObjectsOfTypeAll<Font>().FirstOrDefault(f => f.name.Contains("SpaceMono"))
                   ?? Resources.GetBuiltinResource<Font>("Arial.ttf");
        _title = Label(panel.transform, font, 26, FontStyle.Bold, new Color(0.55f, 1f, 0.6f), new Vector2(0, -18), 40);
        _body = Label(panel.transform, font, 24, FontStyle.Normal, Color.white, new Vector2(0, -66), 220);
        _window.SetActive(false);
    }

    private static Text Label(Transform parent, Font font, int size, FontStyle style, Color color, Vector2 top, float height)
    {
        var go = new GameObject("Text", typeof(RectTransform));
        go.transform.SetParent(parent, false);
        var rt = (RectTransform)go.transform;
        rt.anchorMin = new Vector2(0f, 1f);
        rt.anchorMax = new Vector2(1f, 1f);
        rt.pivot = new Vector2(0.5f, 1f);
        rt.anchoredPosition = top;
        rt.sizeDelta = new Vector2(-60, height);
        var t = go.AddComponent<Text>();
        t.font = font;
        t.fontSize = size;
        t.fontStyle = style;
        t.color = color;
        t.supportRichText = true;
        t.alignment = TextAnchor.UpperCenter;
        t.horizontalOverflow = HorizontalWrapMode.Wrap;
        t.verticalOverflow = VerticalWrapMode.Overflow;
        t.raycastTarget = false;
        return t;
    }
}
