using Meridian.Core;
using Meridian.Items;
using Meridian.Progress;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-175 (D-174, Bible 5.2 §8.1, D1_TABLES §5): the Skill Tree as data. 66 nodes, six branches; buying needs a bought link (ring 1: none)
    /// and the cost (Scrip, the pack's materials, Datacores), topside only; effects change their stats by the table's amounts under LEAD's
    /// stacking rule (+ adds; the best × applies, never compounded; set values the best; then the expedition factor, D-175); a sideways link
    /// opens its neighbour; the save keeps the nodes and the expedition; an old save's tool / suit / ship unlocks map to nodes.
    /// </summary>
    public class SkillTreeTests
    {
        GameObject go;
        GameState s;
        System.Func<int, float> kg0;

        [SetUp]
        public void SetUp()
        {
            go = new GameObject("GameStateU175");
            s = go.AddComponent<GameState>();
            kg0 = Inventory.KgOf;
            s.scrip = 100000;
            s.datacores = 10;
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
        public void TheTreeIsSixtySixNodesInSixBranches()
        {
            var t = SkillTree.Current;
            Assert.AreEqual(66, t.nodes.Length);
            foreach (var b in SkillTree.Branches)
            {
                int n = 0;
                foreach (var node in t.nodes) if (node.branch == b) n++;
                Assert.AreEqual(11, n, $"{b}: 11 nodes");
            }
            foreach (var node in t.nodes)
            {
                Assert.AreEqual(node.ring == 1, node.requires.Length == 0, $"{node.id}: ring 1 links to the centre only");
                foreach (var r in node.requires) Assert.NotNull(t.Get(r), $"{node.id}: its link {r} exists");
                foreach (var c in node.items) Assert.NotNull(ItemRegistry.Get(c.item), $"{node.id}: {c.item} is an item");
                Assert.Greater(node.mods.Length, 0, $"{node.id}: an effect");
            }
            Assert.AreEqual(80, t.Get("dig_power_1").scrip);
            Assert.AreEqual(1, t.Get("dig_core_bit").datacores);
            Assert.AreEqual("deep_diamond", t.Get("dig_core_bit").items[0].item);
        }

        [Test]
        public void BuyingNeedsTheLinkTheCostAndTopside()
        {
            var t = SkillTree.Current;
            Assert.AreEqual(SkillTree.BuyResult.Locked, t.CanBuy(s, "dig_power_2", true), "ring 2 needs its link");
            Assert.AreEqual(SkillTree.BuyResult.NotTopside, t.CanBuy(s, "dig_power_1", false), "topside only");
            s.scrip = 50;
            Assert.AreEqual(SkillTree.BuyResult.Scrip, t.CanBuy(s, "dig_power_1", true), "80 Scrip");
            s.scrip = 100000;
            int before = s.scrip;
            Assert.AreEqual(SkillTree.BuyResult.Ok, t.Buy(s, "dig_power_1", true));
            Assert.AreEqual(before - 80, s.scrip, "the Scrip spent");
            Assert.AreEqual(SkillTree.BuyResult.AlreadyBought, t.CanBuy(s, "dig_power_1", true));
            Assert.AreEqual(SkillTree.BuyResult.Ok, t.Buy(s, "dig_power_2", true), "the link opens ring 2");
            Assert.AreEqual(SkillTree.BuyResult.Materials, t.CanBuy(s, "dig_power_3", true), "ring 3 needs hematite × 6 from the pack");
            s.inventory.Add(Id("hematite"), 6);
            Assert.AreEqual(SkillTree.BuyResult.Ok, t.Buy(s, "dig_power_3", true));
            Assert.AreEqual(0, s.inventory.Count(Id("hematite")), "the materials spent");
        }

        [Test]
        public void EffectsChangeTheirStatsByTheTablesAmounts()
        {
            var t = SkillTree.Current;
            Assert.AreEqual(1f, SkillStats.BeamPower, 1e-4f, "Beam power 1 at the start");
            Assert.AreEqual(0.9f, SkillStats.BrushRadius, 1e-4f);
            Assert.AreEqual(30f, SkillStats.PackKg, 1e-4f);
            Assert.AreEqual(60, SkillStats.DirtStore);
            Assert.AreEqual(0.5f, SkillStats.LoadK, 1e-4f);
            foreach (var id in new[] { "dig_power_1", "dig_power_2", "dig_brush_1", "haul_pack_1", "haul_dirt_1", "haul_pack_2", "haul_light_1", "asc_grapple_1", "asc_ladder_1", "asc_jet_1", "sur_scan_1", "voy_price_1", "end_fall_1" })
            {
                Assert.AreEqual(SkillTree.BuyResult.Ok, t.Buy(s, id, true), id);
            }
            Assert.AreEqual(1f + 0.5f + 1f, SkillStats.BeamPower, 1e-4f, "+0.5 +1");
            Assert.AreEqual(1.0f, SkillStats.BrushRadius, 1e-4f, "+0.1 m");
            Assert.AreEqual(30f + 15f + 25f, SkillStats.PackKg, 1e-4f, "+15 +25 kg");
            Assert.AreEqual(70f, s.inventory.LimitKg, 1e-4f, "the pack's limit applied");
            Assert.AreEqual(100, SkillStats.DirtStore, "+40");
            Assert.AreEqual(100, s.dirt.capacity, "the store's size applied");
            Assert.AreEqual(0.35f, SkillStats.LoadK, 1e-4f, "k → 0.35");
            Assert.AreEqual(12f, SkillStats.GrappleM, 1e-4f, "a 12 m line");
            Assert.AreEqual(1.3f, SkillStats.JetThrust, 1e-4f);
            Assert.AreEqual(18f, SkillStats.ScanRadius, 1e-4f, "8 m + 10");
            Assert.AreEqual(0.35f, SkillStats.WaystationBonus, 1e-4f, "0.25 + 0.10");
            Assert.AreEqual(0.7f, SkillStats.FallDamageFactor, 1e-4f, "fall damage −30 %");

            // LEAD's rule: the best × applies, never compounded (jet ×1.3 then ×1.6 is ×1.6; power use ×0.7 then ×0.5 is ×0.5); sets the best.
            s.inventory.Add(Id("perchlorate"), 5); s.inventory.Add(Id("solarite"), 3); s.inventory.Add(Id("hematite"), 5); s.inventory.Add(Id("vitriol_glass"), 3);
            foreach (var id in new[] { "asc_jet_2", "asc_jet_3", "asc_grapple_2" }) Assert.AreEqual(SkillTree.BuyResult.Ok, t.Buy(s, id, true), id);
            Assert.AreEqual(1.6f, SkillStats.JetThrust, 1e-4f, "the best ×, not 1.3 × 1.6");
            Assert.AreEqual(0.5f, SkillStats.JetPowerUse, 1e-4f, "power use ×0.5, not 0.7 × 0.5");
            Assert.AreEqual(24f, SkillStats.GrappleM, 1e-4f, "the best line");
            Assert.AreEqual(1.5f, SkillStats.ReelSpeed, 1e-4f);
        }

        [Test]
        public void ASidewaysLinkOpensItsNeighbourAndTheExpeditionMultiplies()
        {
            var t = SkillTree.Current;
            // haul_magnet_1 links to haul_light_1 or, sideways, to dig_brush_2.
            Assert.AreEqual(SkillTree.BuyResult.Locked, t.CanBuy(s, "haul_magnet_1", true));
            s.skillNodes.Add("dig_brush_2");
            Assert.IsTrue(t.Linked(t.Get("haul_magnet_1"), s.skillNodes), "the sideways link opens the neighbouring branch's node");
            Assert.AreEqual("dig_brush_2", t.Get("haul_magnet_1").sideways);

            // D-175: expedition 3 multiplies the tree's stats by 1 + 0.25 × 2 = 1.5; k and the prices are not multiplied.
            s.skillNodes.Clear();
            s.expedition = 3;
            SkillStats.Apply(s);
            Assert.AreEqual(1.5f, SkillStats.ExpeditionFactor, 1e-4f);
            Assert.AreEqual(1.5f, SkillStats.BeamPower, 1e-4f, "Beam power 1 × 1.5");
            Assert.AreEqual(45f, SkillStats.PackKg, 1e-4f, "the pack 30 × 1.5");
            Assert.AreEqual(0.5f, SkillStats.LoadK, 1e-4f, "k is not multiplied");
            Assert.AreEqual(0.25f, SkillStats.WaystationBonus, 1e-4f, "prices are not multiplied");
        }

        [Test]
        public void TheSaveKeepsTheTreeAndAnOldSaveMapsItsUnlocks()
        {
            var data = new Meridian.Save.SaveData();
            data.skillNodes.Add("dig_power_1");
            data.expedition = 2;
            var back = JsonUtility.FromJson<Meridian.Save.SaveData>(JsonUtility.ToJson(data));
            CollectionAssert.AreEqual(new[] { "dig_power_1" }, back.skillNodes);
            Assert.AreEqual(2, back.expedition);
            var old = JsonUtility.FromJson<Meridian.Save.SaveData>("{\"version\":3}");
            Assert.AreEqual(1, old.expedition, "an older file: the first expedition");
            var migrated = Meridian.Save.SaveMigrations.Migrate(old);
            Assert.Less(migrated.loadedVersion, SkillTree.SaveVersion, "a v3 file is pre-tree: its unlocks map on load");
            Assert.AreEqual(Meridian.Save.SaveData.CurrentVersion, migrated.version);
            Assert.AreEqual(SkillTree.SaveVersion, Meridian.Save.SaveData.CurrentVersion, "the tree's save version is this build's");

            foreach (var (_, node) in SkillTree.OldBlueprints) Assert.NotNull(SkillTree.Current.Get(node), $"{node} is a node");
            // A trade blueprint open from the start (Jetpack Mk2) says nothing: no node for it.
            Assert.AreEqual(0, SkillTree.MapOldUnlocks(s), "a fresh old save: nothing earned, nothing mapped");
            // The fitted Mk3 thruster, the Mk3 suit, the Saturn beacon (Skip Drive Mk2), the Uranus beacon (Jetpack Mk3, the deep-diamond tip).
            s.thrusterMark = 3; s.suitTier = 3; s.storyFlags.Add("beacon:saturn"); s.storyFlags.Add("beacon:uranus");
            Assert.AreEqual(6, SkillTree.MapOldUnlocks(s));
            foreach (var id in new[] { "voy_thrust_2", "voy_thrust_3", "end_suit_mk3", "voy_skip_1", "asc_jet_2", "dig_power_2" }) Assert.IsTrue(s.skillNodes.Contains(id), id);
            Assert.IsFalse(s.skillNodes.Contains("asc_jet_1"), "Jetpack Mk2 (a trade) was never earned");
        }
    }
}
