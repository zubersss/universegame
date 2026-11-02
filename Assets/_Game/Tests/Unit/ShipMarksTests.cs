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
    /// <summary>U-065 (EditMode): Thruster/Tank marks (Bible §4.3): thrust, launch permission, capacity, install, save.</summary>
    public class ShipMarksTests
    {
        [Test]
        public void LaunchPermissionTableForEveryPlanetAndMark()
        {
            // §4.3 "Can launch from": Mk1 Mercury, Venus, Earth, Mars, Uranus · Mk2 + Saturn, Neptune · Mk3 + Jupiter.
            var expected = new (PlanetId p, bool mk1, bool mk2, bool mk3)[]
            {
                (PlanetId.Mercury, true, true, true), (PlanetId.Venus, true, true, true),
                (PlanetId.Earth, true, true, true), (PlanetId.Mars, true, true, true),
                (PlanetId.Jupiter, false, false, true), (PlanetId.Saturn, false, true, true),
                (PlanetId.Uranus, true, true, true), (PlanetId.Neptune, false, true, true),
            };
            Assert.AreEqual(8, expected.Length);
            foreach (var e in expected)
            {
                Assert.AreEqual(e.mk1, ShipMarks.CanLaunch(1, e.p), $"Mk1 {e.p}");
                Assert.AreEqual(e.mk2, ShipMarks.CanLaunch(2, e.p), $"Mk2 {e.p}");
                Assert.AreEqual(e.mk3, ShipMarks.CanLaunch(3, e.p), $"Mk3 {e.p}");
            }
        }

        [Test]
        public void ThrustAndTankFollowTheMark()
        {
            Assert.AreEqual(12f, ShipMarks.Thrust(1)); Assert.AreEqual(20f, ShipMarks.Thrust(2)); Assert.AreEqual(35f, ShipMarks.Thrust(3));
            Assert.AreEqual(100f, ShipMarks.TankCapacity(1)); Assert.AreEqual(200f, ShipMarks.TankCapacity(2)); Assert.AreEqual(400f, ShipMarks.TankCapacity(3));
            Assert.AreEqual("THRUSTER MK1 CAN'T LIFT OFF HERE", ShipMarks.CantLiftOff[1]);
        }

        [Test]
        public void InstallRaisesTheMarkOnlyUpward()
        {
            var go = new GameObject("GS");
            var state = go.AddComponent<GameState>();
            try
            {
                state.thrusterMark = 1; state.tankMark = 1; state.tankCapacity = 100f; state.fuel = 80f;
                Assert.IsTrue(ShipMarks.Install(state, "tank_mk2"));
                Assert.AreEqual(2, state.tankMark); Assert.AreEqual(200f, state.tankCapacity); Assert.AreEqual(80f, state.fuel, "fuel stays");
                Assert.IsTrue(ShipMarks.Install(state, "tank_mk3"));
                Assert.AreEqual(400f, state.tankCapacity);
                Assert.IsFalse(ShipMarks.Install(state, "tank_mk2"), "no downgrade");
                Assert.AreEqual(400f, state.tankCapacity);
                Assert.IsTrue(ShipMarks.Install(state, "thruster_mk3"));
                Assert.AreEqual(3, state.thrusterMark);
                Assert.IsFalse(ShipMarks.Install(state, "thruster_mk2"));
                Assert.IsFalse(ShipMarks.Install(state, "iron"), "not an upgrade");
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void UpgradesAreCraftable()
        {
            var recipes = CraftingDefaults.Recipes();
            var blueprints = CraftingDefaults.Blueprints();
            foreach (var key in new[] { "thruster_mk2", "thruster_mk3", "tank_mk2", "tank_mk3" })
            {
                Assert.NotNull(ItemRegistry.Get(key), key);
                var r = recipes.Find(x => x.output.item == key);
                Assert.NotNull(r, key + " recipe");
                Assert.NotNull(blueprints.Find(b => b.id == r.blueprint), key + " blueprint");
                Assert.AreNotEqual(ShipMarks.Part.None, ShipMarks.UpgradeOf(key).part, key);
            }
        }

        [Test]
        public void MarksSurviveSaveAndOlderFilesReadMk1()
        {
            var data = new SaveData();
            data.ship.thrusterMark = 2; data.ship.tankMark = 3; data.ship.tankCapacity = 400f;
            var back = JsonUtility.FromJson<SaveData>(JsonUtility.ToJson(data));
            Assert.AreEqual(2, back.ship.thrusterMark);
            Assert.AreEqual(3, back.ship.tankMark);
            Assert.AreEqual(400f, back.ship.tankCapacity);
            var old = JsonUtility.FromJson<SaveData>("{\"version\":2,\"ship\":{\"hull\":90,\"fuel\":50,\"tankCapacity\":100}}");
            Assert.AreEqual(1, old.ship.thrusterMark, "pre-U-065 files have Mk1");
            Assert.AreEqual(1, old.ship.tankMark);
        }
    }
}
