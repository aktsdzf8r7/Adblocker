using HarmonyLib;
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using ZekiVerdornt;

namespace ZekiDornenlabyrinth;

/// <summary>
/// Our ship log cards must not cover the game's (or another mod's) in rumor mode. After New Horizons has given every
/// card its position (its own postfix on ShipLogManager.Awake), our group moves below the others if it overlaps them
/// (ShipLogLayout, shared with Verdornt).
/// </summary>
[HarmonyPatch(typeof(ShipLogManager), "Awake")]
public static class ShipLogPlacement
{
    public const string Prefix = "ZEKIDL_";
    private const float Margin = 450f;

    private static readonly AccessTools.FieldRef<ShipLogManager, Dictionary<string, EntryData>> EntryData =
        AccessTools.FieldRefAccess<ShipLogManager, Dictionary<string, EntryData>>("_entryDataDict");

    [HarmonyPostfix]
    [HarmonyPriority(Priority.Last)]
    public static void Postfix(ShipLogManager __instance)
    {
        try
        {
            var dict = EntryData(__instance);
            if (dict == null) return;
            var cards = dict.Select(kv => (kv.Key, kv.Value.cardPosition.x, kv.Value.cardPosition.y)).ToList();
            var (dx, dy) = ShipLogLayout.MoveBelow(cards, Prefix, Margin);
            if (dx == 0f && dy == 0f) return;
            foreach (var id in dict.Keys.Where(k => k.StartsWith(Prefix)).ToList())
            {
                var data = dict[id];
                data.cardPosition += new Vector2(dx, dy);
                dict[id] = data;
            }
            ZekiDornenlabyrinth.Instance?.Log($"Logbuch: unsere Karten um ({dx:0}, {dy:0}) verschoben, weg von den anderen.");
        }
        catch (Exception e)
        {
            ZekiDornenlabyrinth.Instance?.Log("Logbuch-Platzierung: " + e.Message, true);
        }
    }
}
