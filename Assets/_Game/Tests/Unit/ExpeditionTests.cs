using System.IO;
using System.Linq;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Progress;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-178 (D-175, Bible 5.3 §8.1, D1_TABLES §7): the Surveyor Rank and the New Expedition as data. The Rank at each threshold; the offer
    /// only at Rank 10 and topside; the wipe and the keep lists exactly; the multiplier on each stat at expeditions 1, 2 and 4 (never the load
    /// factor, the stroke cap or prices); the confirmation's words; B-206's numerals and badges; B-214's insignia track; no other way to unbuy
    /// a node. (ExpeditionPlayTests: the panel, the return to Earth's camp, the save mid-expedition 3, the HUD's rank-up.)
    /// </summary>
    public class ExpeditionTests
    {
        GameObject go;
        GameState s;
        System.Func<int, float> kg0;

        [SetUp]
        public void SetUp()
        {
            go = new GameObject("GameStateU178");
            s = go.AddComponent<GameState>();
            kg0 = Inventory.KgOf;
            SkillStats.Recompute(s);
        }

        [TearDown]
        public void TearDown()
        {
            SkillStats.Recompute(null);
            Inventory.KgOf = kg0;
            Object.DestroyImmediate(go);
        }

        static int Id(string key) => ItemRegistry.Get(key).id;

        [Test]
        public void TheRankAtEachThreshold()
        {
            var t = D1Tables.Current.rankScrip;
            CollectionAssert.AreEqual(new[] { 0, 300, 800, 1800, 3500, 7000, 14000, 28000, 50000, 80000 }, t, "D1_TABLES §7");
            for (int r = 1; r <= 10; r++)
            {
                s.scripEarned = t[r - 1];
                Assert.AreEqual(r, Expedition.Rank(s), $"Rank {r} at {t[r - 1]} earned");
                if (r > 1) { s.scripEarned = t[r - 1] - 1; Assert.AreEqual(r - 1, Expedition.Rank(s), $"one short of Rank {r}"); }
            }
            s.scripEarned = 10000000;
            Assert.AreEqual(10, Expedition.Rank(s), "10 is the top");
            Assert.AreEqual(-1, Expedition.NextRankScrip(s));
            s.scripEarned = 1000;
            Assert.AreEqual(1800, Expedition.NextRankScrip(s));
            s.scrip = 999999; s.scripEarned = 0;
            Assert.AreEqual(1, Expedition.Rank(s), "Scrip held is not Scrip earned (sales only)");
        }

        [Test]
        public void TheOfferIsOnlyAtRankTenTopside()
        {
            s.scripEarned = 79999;
            Assert.IsFalse(Expedition.CanBegin(s, true), "Rank 9");
            s.scripEarned = 80000;
            Assert.IsFalse(Expedition.CanBegin(s, false), "below the Surface Line");
            Assert.IsTrue(Expedition.CanBegin(s, true));
            s.skillNodes.Add("dig_power_1");
            Assert.IsFalse(Expedition.Begin(s, false), "not topside: nothing happens");
            Assert.AreEqual(1, s.expedition); Assert.IsTrue(s.skillNodes.Contains("dig_power_1"));
            s.scripEarned = 100;
            Assert.IsFalse(Expedition.Begin(s, true), "not Rank 10: nothing happens");
            Assert.AreEqual(1, s.expedition);
        }

        [Test]
        public void TheWipeAndTheKeepListsExactly()
        {
            SkillStats.Apply(s);
            s.scripEarned = 90000; s.scrip = 12345;
            foreach (var n in new[] { "dig_power_1", "haul_pack_1", "voy_thrust_2", "end_suit_mk3" }) s.skillNodes.Add(n);
            s.thrusterMark = 3; s.suitTier = 3;
            s.inventory.Add(Id("clay"), 5);
            s.cargo.Add(new CargoStack { itemId = Id("iron"), count = 7 });
            s.datacores = 9;
            s.catalogue.Add("earth_fern");
            s.SetFlag("story_ch1");
            s.basePieces.Add(new Meridian.Building.BasePieceSave { planet = "Earth", kind = "Wall", x = 3, y = 4 });
            s.ascentPieces.Add(new Meridian.Building.AscentSave { planet = "Earth", kind = "ladder", x = 1, y = 2 });
            s.dirt.count = 12;
            s.contracts.Add(new Meridian.Trade.Contract());
            s.currentPlanet = Meridian.Planets.PlanetId.Mars;
            int began = 0; void On(int n) => began = n;
            Expedition.Began += On;
            try { Assert.IsTrue(Expedition.Begin(s, true)); } finally { Expedition.Began -= On; }
            // wiped
            Assert.AreEqual(2, s.expedition); Assert.AreEqual(2, began);
            Assert.AreEqual(0, s.skillNodes.Count, "the bought nodes");
            Assert.AreEqual(Meridian.Trade.Market.StartingScrip, s.scrip, "Scrip: a new surveyor's purse");
            Assert.AreEqual(0, s.scripEarned); Assert.AreEqual(1, Expedition.Rank(s), "the Rank");
            Assert.AreEqual(0f, s.inventory.Weight); Assert.AreEqual(0, s.inventory.Count(Id("clay")), "the pack");
            Assert.AreEqual(0, s.cargo.Count, "the rocket's hold");
            Assert.AreEqual(1, s.thrusterMark, "the tree's thruster mark back to the start (a load would map it back to nodes)");
            Assert.AreEqual(0, s.suitTier, "the tree's suit tier too");
            // kept
            Assert.AreEqual(9, s.datacores, "Datacores");
            Assert.IsTrue(s.catalogue.Contains("earth_fern"), "the Catalogue");
            Assert.IsTrue(s.HasFlag("story_ch1"), "the story");
            Assert.AreEqual(1, s.basePieces.Count, "buildings"); Assert.AreEqual(1, s.ascentPieces.Count, "ladders are buildings");
            Assert.AreEqual(12, s.dirt.count, "the dirt store is not the pack");
            Assert.AreEqual(1, s.contracts.Count);
            Assert.AreEqual(Meridian.Planets.PlanetId.Mars, s.currentPlanet, "the return to Earth's camp is SceneDirector's (ExpeditionPlayTests)");
            Assert.AreEqual(5, Expedition.Wiped.Length); Assert.AreEqual(5, Expedition.Kept.Length);
        }

        [Test]
        public void TheMultiplierOnEachStatAtExpeditionsOneTwoAndFour()
        {
            Assert.AreEqual(1f, Expedition.Multiplier(1)); Assert.AreEqual(1.25f, Expedition.Multiplier(2)); Assert.AreEqual(1.75f, Expedition.Multiplier(4));
            var tree = SkillTree.Current;
            foreach (var n in tree.nodes) s.skillNodes.Add(n.id); // every node: every stat has a value
            var stats = tree.nodes.SelectMany(n => n.mods).Where(m => m.op != "flag").Select(m => m.stat).Distinct().ToArray();
            s.expedition = 1; SkillStats.Recompute(s);
            var one = stats.ToDictionary(k => k, k => SkillStats.Value(k, 1f));
            float oxygen1 = SkillStats.Oxygen, cap = D1Tables.Current.strokeCapSeconds, loadK1 = SkillStats.LoadK;
            float price = D1Tables.Current.Scrip(Id("iron"));
            foreach (int e in new[] { 2, 4 })
            {
                s.expedition = e; SkillStats.Recompute(s);
                float m = Expedition.Multiplier(e);
                foreach (var k in stats)
                    Assert.AreEqual(one[k] * (tree.Multiplied(k) ? m : 1f), SkillStats.Value(k, 1f), 1e-3f, $"{k} at expedition {e}");
                Assert.AreEqual(oxygen1 * m, SkillStats.Oxygen, 1e-3f, "oxygen");
                Assert.AreEqual(loadK1, SkillStats.LoadK, 1e-6f, "the load factor's k is never multiplied");
                Assert.AreEqual(cap, D1Tables.Current.strokeCapSeconds, "nor the stroke cap");
                Assert.AreEqual(price, D1Tables.Current.Scrip(Id("iron")), "nor prices");
            }
            foreach (var k in new[] { "beam_power", "brush_radius", "pack_kg", "dirt_store", "climb_speed", "jet_thrust", "reel_speed", "scan_radius", "scan_depth", "depth_hazard_cut" })
                Assert.IsTrue(tree.Multiplied(k), k + " is multiplied (D1_TABLES §7)");
            foreach (var k in new[] { "load_k", "jet_power_use", "ore_weight", "waystation_bonus", "scan_cooldown" })
                Assert.IsFalse(tree.Multiplied(k), k + ": a cost, a price or a k is not");
        }

        [Test]
        public void TheConfirmationSaysWhatGoesAndWhatStays()
        {
            var text = Meridian.UI.SkillTreePanel.ConfirmationText(1);
            foreach (var w in Expedition.Wiped) StringAssert.Contains(w, text);
            foreach (var k in Expedition.Kept) StringAssert.Contains(k, text);
            StringAssert.Contains("×1.25", text); StringAssert.Contains("(now ×1.00)", text);
            StringAssert.Contains("Expedition II begins at Earth's camp", text);
            StringAssert.Contains("×2.00 (now ×1.75)", Meridian.UI.SkillTreePanel.ConfirmationText(4));
        }

        [Test]
        public void TheBadgesNumeralsAndTheRankUpTrack()
        {
            Assert.AreEqual("I", Expedition.Roman(1)); Assert.AreEqual("IV", Expedition.Roman(4)); Assert.AreEqual("IX", Expedition.Roman(9));
            Assert.AreEqual("X", Expedition.Roman(10)); Assert.AreEqual("XI", Expedition.Roman(11)); Assert.AreEqual("XIV", Expedition.Roman(14));
            Assert.AreEqual("ui/rank/expedition_badge", Expedition.BadgeKey(10));
            Assert.AreEqual("ui/rank/expedition_badge_laurel", Expedition.BadgeKey(11), "B-206: the laurel from XI");
            Assert.AreEqual("ui/rank/insignia_10", Expedition.InsigniaKey(10));
            for (int r = 1; r <= 10; r++) Assert.IsTrue(File.Exists($"Assets/_Game/Art/ui/rank/insignia_{r}.json"), "B-206's insignia " + r);
            // B-214's insignia_track, copied into the HUD (the fx jsons are not addressable): the same numbers
            var json = File.ReadAllText("Assets/_Game/Art/fx/ui/rank_up.json");
            var m = System.Text.RegularExpressions.Regex.Matches(json, "\"dy_px\"\\s*:\\s*(-?[0-9.]+)\\s*,\\s*\"scale\"\\s*:\\s*([0-9.]+)");
            Assert.AreEqual(Meridian.UI.SideHud.RankUpTrack.Length, m.Count);
            for (int i = 0; i < m.Count; i++)
            {
                Assert.AreEqual(float.Parse(m[i].Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture), Meridian.UI.SideHud.RankUpTrack[i].x, 1e-4f);
                Assert.AreEqual(float.Parse(m[i].Groups[2].Value, System.Globalization.CultureInfo.InvariantCulture), Meridian.UI.SideHud.RankUpTrack[i].y, 1e-4f);
            }
            StringAssert.Contains("0.4583", json, "the rank_up pivot");
            StringAssert.Contains("[\n    58,\n    58\n  ]".Replace("\n", "").Replace(" ", ""), File.ReadAllText("Assets/_Game/Art/fx/ui/expedition_seal.json").Replace("\n", "").Replace("\r", "").Replace(" ", ""), "the seal 58 px in");
        }

        [Test]
        public void NoOtherWayToUnbuyANode()
        {
            // The bought set shrinks in exactly two places: a New Expedition's wipe and a load replacing the state with the file's set.
            var hits = Directory.GetFiles("Assets/_Game/Code", "*.cs", SearchOption.AllDirectories)
                .SelectMany(f => File.ReadAllLines(f).Select((line, i) => (f: f.Replace('\\', '/'), line, i)))
                .Where(x => System.Text.RegularExpressions.Regex.IsMatch(x.line, @"skillNodes\s*\.\s*(Remove|Clear|ExceptWith|RemoveWhere|IntersectWith|SymmetricExceptWith)\b"))
                .Select(x => $"{x.f.Substring(x.f.IndexOf("Code/"))}:{x.i + 1}").ToArray();
            CollectionAssert.AreEquivalent(new[] { "Code/Runtime/Progress/Expedition.cs", "Code/Runtime/Save/SaveSystem.cs" }, hits.Select(h => h.Substring(0, h.LastIndexOf(':'))).ToArray(),
                "found: " + string.Join(", ", hits));
            var api = typeof(SkillTree).GetMethods().Select(mi => mi.Name).Concat(typeof(SkillStats).GetMethods().Select(mi => mi.Name));
            foreach (var name in api)
                Assert.IsFalse(System.Text.RegularExpressions.Regex.IsMatch(name, "Unbuy|Refund|Respec|Sell|Reset", System.Text.RegularExpressions.RegexOptions.IgnoreCase), name);
        }
    }
}
