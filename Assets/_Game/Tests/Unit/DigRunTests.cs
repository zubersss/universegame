using System.Collections.Generic;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-174 (D-174, Bible 5.2 §8.1, docs/D1_TABLES.md): the dig run's rules from the D1 tables (data, not code). Stroke times per tier with
    /// Beam power 1 and 4 and the 8 s cap (a tier-5 stroke possible with the starting Beam); a dug tile's give follows the tier's material
    /// chance and the planet's weights over 20 000 hashed tiles; the pack refuses past its limit; the load factor; selling topside pays the
    /// tables' Scrip and empties the pack, refused below the line; the save keeps the dirt store and the Scrip earned.
    /// </summary>
    public class DigRunTests
    {
        D1Tables T => D1Tables.Current;

        [Test]
        public void TheTablesLoadAsData()
        {
            Assert.AreEqual(5, T.tiers.Length, "five depth tiers");
            Assert.AreEqual(new[] { 0f, 10f, 40f, 100f, 200f }, System.Array.ConvertAll(T.tiers, t => t.fromM), "tier depths (m under the line)");
            Assert.AreEqual(new[] { 1f, 2f, 4f, 8f, 16f }, System.Array.ConvertAll(T.tiers, t => t.hardness), "tier hardness");
            foreach (var p in new[] { PlanetId.Earth, PlanetId.Mars, PlanetId.Mercury, PlanetId.Venus })
            {
                var planet = T.PlanetOf(p);
                Assert.NotNull(planet, $"{p} has tier tables");
                Assert.AreEqual(5, planet.tiers.Length, $"{p}: five tier tables");
                foreach (var tier in planet.tiers)
                    foreach (var r in tier.rows)
                    {
                        Assert.NotNull(ItemRegistry.Get(r.item), $"{p}: {r.item} is an item");
                        Assert.IsTrue(T.Sellable(ItemRegistry.Get(r.item).id), $"{p}: {r.item} has a price and a weight");
                    }
            }
            Assert.AreEqual(2f, T.surfaceLineDepth, "the Surface Line 2 m under the drawn surface");
            Assert.AreEqual(30f, T.packLimitKg);
            Assert.AreEqual(60, T.dirtStoreStart);
        }

        [Test]
        public void StrokeTimePerTierWithBeamPowerOneAndFourAndTheCap()
        {
            float[] depths = { 5f, 20f, 60f, 150f, 250f };
            float[] earth1 = { 0.25f, 0.5f, 1f, 2f, 4f };
            for (int i = 0; i < 5; i++)
            {
                Assert.AreEqual(i, T.TierIndex(depths[i]), $"{depths[i]} m is T{i + 1}");
                Assert.AreEqual(earth1[i], T.StrokeSeconds(PlanetId.Earth, depths[i], 1f), 1e-4f, $"Earth T{i + 1}, power 1");
                Assert.AreEqual(earth1[i] / 4f, T.StrokeSeconds(PlanetId.Earth, depths[i], 4f), 1e-4f, $"Earth T{i + 1}, power 4");
            }
            Assert.AreEqual(0.25f * 1.6f * 2f, T.StrokeSeconds(PlanetId.Mars, 20f, 1f), 1e-4f, "Mars T2");
            // The cap: Venus T5 at power 1 would take 0.25 × 4 × 16 = 16 s; it takes 8, so a tier-5 stroke is possible with the starting Beam.
            Assert.AreEqual(8f, T.StrokeSeconds(PlanetId.Venus, 250f, 1f), 1e-4f, "capped at 8 s");
            foreach (var p in new[] { PlanetId.Earth, PlanetId.Mars, PlanetId.Mercury, PlanetId.Venus })
                Assert.LessOrEqual(T.StrokeSeconds(p, 999f, T.beamPowerStart), T.strokeCapSeconds, $"{p}: T5 with the starting Beam");
            Assert.AreEqual(0f, T.TierIndex(0f), "0 m at the line is T1");
        }

        [Test]
        public void ADugTilesGiveFollowsTheTables()
        {
            const int N = 20000;
            foreach (var (planet, tier) in new[] { (PlanetId.Earth, 1), (PlanetId.Mars, 3), (PlanetId.Venus, 4) })
            {
                var counts = new Dictionary<int, int>();
                int materials = 0;
                for (int i = 0; i < N; i++)
                {
                    DigRun.Rolls(i % 997, i / 997, 1969, out float mr, out float pr);
                    int item = T.Roll(planet, tier, mr, pr, false);
                    if (item == 0) continue;
                    materials++;
                    counts[item] = counts.TryGetValue(item, out var c) ? c + 1 : 1;
                }
                float chance = T.tiers[tier].materialChance;
                TestContext.Out.WriteLine($"[MERIDIAN] u174 {planet} T{tier + 1}: {materials} materials of {N} ({100f * materials / N:F2} %, the table {100f * chance:F0} %)");
                Assert.AreEqual(chance, (float)materials / N, 0.01f, $"{planet} T{tier + 1}: the material chance");
                var rows = T.Rows(planet, tier);
                float total = 0f;
                foreach (var r in rows) total += r.weight;
                var byItem = new Dictionary<int, float>();
                foreach (var r in rows) { int id = ItemRegistry.Get(r.item).id; byItem[id] = (byItem.TryGetValue(id, out var w) ? w : 0f) + r.weight / total; }
                foreach (var kv in byItem)
                    Assert.AreEqual(kv.Value, (counts.TryGetValue(kv.Key, out var c) ? c : 0) / (float)materials, 0.04f, $"{planet} T{tier + 1}: {ItemRegistry.Get(kv.Key).key}'s share");
            }
            // Mercury T4: polar ice only in a cold trap (graphite elsewhere); a pocket's item is the tier's rarest (the last row).
            int ice = ItemRegistry.Get("polar_ice").id, graphite = ItemRegistry.Get("graphite").id;
            bool iceInTrap = false, iceOutside = false;
            for (int i = 0; i < N; i++)
            {
                DigRun.Rolls(i, 7, 3, out float mr, out float pr);
                if (T.Roll(PlanetId.Mercury, 3, 0f, pr, true) == ice) iceInTrap = true;
                if (T.Roll(PlanetId.Mercury, 3, 0f, pr, false) == ice) iceOutside = true;
            }
            Assert.IsTrue(iceInTrap, "Mercury T4: polar ice in a cold trap");
            Assert.IsFalse(iceOutside, "Mercury T4: no polar ice outside one");
            Assert.AreEqual(ItemRegistry.Get("deep_diamond").id, T.Rarest(PlanetId.Earth, 4), "Earth T5's pocket: deep diamond");
            Assert.AreEqual(ItemRegistry.Get("copper").id, T.Rarest(PlanetId.Earth, 1), "Earth T2's pocket: copper");
            Assert.AreEqual(0, T.Roll(PlanetId.Earth, 0, 0.5f, 0.5f, false), "a roll over the chance is dirt");
            Assert.AreNotEqual(graphite, 0);
        }

        [Test]
        public void ThePackRefusesPastItsLimitAndLoadSlowsTheClimb()
        {
            var kg0 = Inventory.KgOf;
            Inventory.KgOf = T.Kg;
            try
            {
                var inv = new Inventory { LimitKg = 30f };
                int refusedEvents = 0;
                inv.Refused += () => refusedEvents++;
                int iron = ItemRegistry.Get("iron").id;
                Assert.AreEqual(1f, DigRun.LoadFactor(inv), 1e-4f, "empty: full climb");
                int left = inv.Add(iron, 20); // 2 kg each
                Assert.AreEqual(5, left, "15 iron (30 kg) fit, 5 refused");
                Assert.AreEqual(1, refusedEvents, "the HUD's pack-full cue");
                Assert.AreEqual(30f, inv.Weight, 1e-3f);
                Assert.AreEqual(1, inv.Add(iron, 1), "full: no more");
                Assert.AreEqual(0.5f, DigRun.LoadFactor(inv), 1e-4f, "a full pack: 1 − 0.5 × 30 / 30");
                Assert.AreEqual(0, inv.Add(ItemRegistry.Get("suit_patch").id, 3), "weightless goods still fit");
                inv.Remove(iron, 5);
                Assert.AreEqual(0.5f + 0.5f * 10f / 30f, DigRun.LoadFactor(inv), 1e-4f, "lighter, faster");
                var plain = new Inventory();
                Assert.AreEqual(0, plain.Add(iron, 500), "a plain inventory has no limit");
            }
            finally { Inventory.KgOf = kg0; }
        }

        [Test]
        public void SellingPaysTheTablesTopsideOnlyAndTheSaveKeepsTheRun()
        {
            var kg0 = Inventory.KgOf;
            var go = new GameObject("GameStateU174");
            try
            {
                var state = go.AddComponent<GameState>();
                Inventory.KgOf = T.Kg;
                int iron = ItemRegistry.Get("iron").id, clay = ItemRegistry.Get("clay").id, patch = ItemRegistry.Get("suit_patch").id;
                state.inventory.Add(iron, 10);
                state.inventory.Add(clay, 5);
                state.inventory.Add(patch, 2);
                int scrip0 = state.scrip;
                Assert.AreEqual(10 * 12 + 5 * 2, DigRun.PackValue(state.inventory, false));
                Assert.AreEqual(-1, DigRun.SellPack(state, false, false), "below the Surface Line: refused");
                Assert.AreEqual(10, state.inventory.Count(iron), "nothing sold below the line");
                Assert.AreEqual(130, DigRun.SellPack(state, true, false), "10 iron × 12 + 5 clay × 2");
                Assert.AreEqual(scrip0 + 130, state.scrip);
                Assert.AreEqual(130, state.scripEarned, "earned this expedition (Rank, D-175)");
                Assert.AreEqual(0, state.inventory.Count(iron) + state.inventory.Count(clay), "the pack's materials sold");
                Assert.AreEqual(2, state.inventory.Count(patch), "crafted goods are not the pack's materials");
                state.inventory.Add(iron, 4);
                Assert.AreEqual(Mathf.RoundToInt(48 * 1.25f), DigRun.SellPack(state, true, true), "a Waystation pays +25 %");

                // The save keeps the dirt store and the Scrip earned (the pack and the purse were saved before).
                var data = new Meridian.Save.SaveData { scrip = state.scrip, scripEarned = state.scripEarned, dirt = 37 };
                var back = JsonUtility.FromJson<Meridian.Save.SaveData>(JsonUtility.ToJson(data));
                Assert.AreEqual(state.scrip, back.scrip);
                Assert.AreEqual(state.scripEarned, back.scripEarned);
                Assert.AreEqual(37, back.dirt);
                var store = new DirtStore { capacity = 60 };
                Assert.AreEqual(60, store.Add(80), "the dirt store holds 60");
                Assert.IsTrue(store.Full);
                Assert.AreEqual(10, store.Spend(10));
            }
            finally { Inventory.KgOf = kg0; Object.DestroyImmediate(go); }
        }
    }
}
