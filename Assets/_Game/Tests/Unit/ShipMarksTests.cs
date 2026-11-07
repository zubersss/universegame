using Meridian.Core;
using Meridian.Crafting;
using Meridian.Items;
using Meridian.Planets;
using Meridian.Save;
using Meridian.Ship;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-065, U-107 (EditMode): Thruster marks (Bible §4.3 v4.1): thrust, the physics-only climb rule (D-106), install,
    /// save. No tanks since U-107 (D-103).
    /// </summary>
    public class ShipMarksTests
    {
        [Test]
        public void ClimbTableForEveryPlanetAndMark()
        {
            // D-106: a mark climbs wherever its thrust exceeds g. Mk1 everywhere but Jupiter; Mk2 the same; Mk3 everywhere.
            var expected = new (PlanetId p, float g, bool mk1, bool mk2, bool mk3)[]
            {
                (PlanetId.Mercury, 3.70f, true, true, true), (PlanetId.Venus, 8.87f, true, true, true),
                (PlanetId.Earth, 9.81f, true, true, true), (PlanetId.Mars, 3.72f, true, true, true),
                (PlanetId.Jupiter, 24.79f, false, false, true), (PlanetId.Saturn, 10.44f, true, true, true),
                (PlanetId.Uranus, 8.69f, true, true, true), (PlanetId.Neptune, 11.15f, true, true, true),
            };
            Assert.AreEqual(8, expected.Length);
            foreach (var e in expected)
            {
                Assert.AreEqual(e.mk1, ShipMarks.CanClimb(1, e.g), $"Mk1 {e.p}");
                Assert.AreEqual(e.mk2, ShipMarks.CanClimb(2, e.g), $"Mk2 {e.p}");
                Assert.AreEqual(e.mk3, ShipMarks.CanClimb(3, e.g), $"Mk3 {e.p}");
            }
        }

        [Test]
        public void ThrustFollowsTheMark()
        {
            Assert.AreEqual(12f, ShipMarks.Thrust(1)); Assert.AreEqual(20f, ShipMarks.Thrust(2)); Assert.AreEqual(35f, ShipMarks.Thrust(3));
            Assert.AreEqual(12f, ShipMarks.Thrust(0), "below Mk1 reads Mk1");
            Assert.AreEqual(35f, ShipMarks.Thrust(9), "above Mk3 reads Mk3");
            Assert.AreEqual("THRUSTER MK1 CAN'T CLIMB HERE", ShipMarks.CantClimb[1]);
        }

        [Test]
        public void InstallRaisesTheMarkOnlyUpward()
        {
            var go = new GameObject("GS");
            var state = go.AddComponent<GameState>();
            try
            {
                state.thrusterMark = 1;
                Assert.IsTrue(ShipMarks.Install(state, "thruster_mk2"));
                Assert.AreEqual(2, state.thrusterMark);
                Assert.IsTrue(ShipMarks.Install(state, "thruster_mk3"));
                Assert.AreEqual(3, state.thrusterMark);
                Assert.IsFalse(ShipMarks.Install(state, "thruster_mk2"), "no downgrade");
                Assert.IsFalse(ShipMarks.Install(state, "iron"), "not an upgrade");
                Assert.IsFalse(ShipMarks.Install(state, "tank_mk2"), "no tanks (U-107)");
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void UpgradesAreCraftable()
        {
            var recipes = CraftingDefaults.Recipes();
            var blueprints = CraftingDefaults.Blueprints();
            foreach (var key in new[] { "thruster_mk2", "thruster_mk3" })
            {
                Assert.NotNull(ItemRegistry.Get(key), key);
                var r = recipes.Find(x => x.output.item == key);
                Assert.NotNull(r, key + " recipe");
                Assert.NotNull(blueprints.Find(b => b.id == r.blueprint), key + " blueprint");
                Assert.AreNotEqual(ShipMarks.Part.None, ShipMarks.UpgradeOf(key).part, key);
            }
            foreach (var key in new[] { "tank_mk2", "tank_mk3" })
            {
                Assert.IsNull(ItemRegistry.Get(key), key + " is retired (U-107)");
                Assert.IsNull(recipes.Find(x => x.output.item == key), key + " has no recipe");
                Assert.IsNull(blueprints.Find(b => b.id == key), key + " has no blueprint");
            }
        }

        [Test]
        public void MarksSurviveSaveAndOlderFilesReadMk1()
        {
            var data = new SaveData();
            data.ship.thrusterMark = 2;
            var back = JsonUtility.FromJson<SaveData>(JsonUtility.ToJson(data));
            Assert.AreEqual(2, back.ship.thrusterMark);
            // A pre-U-107 file still carries fuel and tank fields; they are ignored and the hull reads.
            var old = JsonUtility.FromJson<SaveData>("{\"version\":2,\"ship\":{\"hull\":90,\"fuel\":50,\"tankCapacity\":100,\"tankMark\":2}}");
            Assert.AreEqual(1, old.ship.thrusterMark, "pre-U-065 files have Mk1");
            Assert.AreEqual(90f, old.ship.hull, 1e-4f);
            Assert.IsFalse(JsonUtility.ToJson(back).Contains("fuel"), "a new save writes no fuel");
        }
    }
}
