using System.IO;
using Meridian.Creatures;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-114 (B-135, cycle 259): the Earth swimmers. Pike, shark and squid live in the Water habitat: they spawn only on a water
    /// column deep enough for their height plus their floor clearance (0.38 / 0.87 / 0.70 m, pivot centre), and their v3 sheets
    /// carry idle, swim, react, bump, flee in that order, so the shared move slot (index 1) plays `swim`.
    /// </summary>
    public class SwimmerTests
    {
        static SpawnSite Column(byte above, int depth, byte floor = TileId.Sand) =>
            new SpawnSite { surfaceTile = floor, aboveTile = above, waterDepth = depth, surfaceY = 300, datumY = 320, planet = PlanetId.Earth };

        [Test]
        public void TheSwimmersSpawnOnlyInWaterDeepEnoughForThem()
        {
            var pike = SpeciesSpec.Get(Species.Pike); var shark = SpeciesSpec.Get(Species.Shark); var squid = SpeciesSpec.Get(Species.Squid);
            foreach (var s in new[] { pike, shark, squid })
            {
                Assert.AreEqual(Habitat.Water, s.habitat, s.artKey);
                Assert.IsTrue(s.Swims && s.Flies, s.artKey + " has no gravity and holds an altitude like a flier");
                Assert.AreEqual(PlanetId.Earth, s.planet);
                Assert.IsTrue(s.Allows(Column(TileId.Water, 6)), s.artKey + " in a 6 m pool");
                Assert.IsFalse(s.Allows(Column(TileId.Air, 0, TileId.Grass)), s.artKey + " never on a meadow");
                Assert.IsFalse(s.Allows(Column(TileId.Water, 1)), s.artKey + " not in a puddle");
            }
            Assert.AreEqual(0.38f, pike.floorClearance, 1e-6f); Assert.AreEqual(0.87f, shark.floorClearance, 1e-6f); Assert.AreEqual(0.70f, squid.floorClearance, 1e-6f);
            Assert.IsTrue(pike.Allows(Column(TileId.Water, 2)), "a pike (1.25 + 0.38 m) fits two metres of water");
            Assert.IsFalse(shark.Allows(Column(TileId.Water, 2)), "a shark (2.0 + 0.87 m) does not");
            Assert.IsFalse(squid.Allows(Column(TileId.Water, 2)), "nor a squid (2.25 + 0.70 m)");
            Assert.AreEqual(new Vector2(2.0f, 1.25f), pike.size); Assert.AreEqual(new Vector2(3.5f, 2.0f), shark.size); Assert.AreEqual(new Vector2(5.0f, 2.25f), squid.size);
            Assert.AreEqual(Temper.Flees, pike.temper); Assert.AreEqual(Temper.Territorial, shark.temper); Assert.AreEqual(Temper.Flees, squid.temper);
            Assert.IsFalse(SpeciesSpec.Get(Species.Stag).Allows(Column(TileId.Water, 6)), "a stag never spawns under water");
        }

        [Test]
        public void TheThreeSwimmerSheetsCarryTheClipOrderAndTheFrameSizes()
        {
            var expect = new (string key, int w, int h)[] { ("pike", 128, 80), ("shark", 224, 128), ("squid", 320, 144) };
            foreach (var e in expect)
            {
                string path = $"Assets/_Game/Art/creatures/earth/{e.key}.json";
                Assert.IsTrue(File.Exists(path), path);
                var sheet = JsonUtility.FromJson<Sheet>(File.ReadAllText(path));
                Assert.AreEqual(e.w, sheet.frame_width, e.key + " frame width"); Assert.AreEqual(e.h, sheet.frame_height, e.key + " frame height");
                Assert.AreEqual(64f, sheet.ppu, 1e-4f, e.key + " at PPU 64");
                Assert.AreEqual(new[] { 0.5f, 0.5f }, sheet.pivot, e.key + " pivot centre");
                Assert.AreEqual(5, sheet.animations.Length, e.key + " clips");
                Assert.AreEqual("idle", sheet.animations[0].name); Assert.AreEqual("swim", sheet.animations[1].name, "the move slot is swim");
                Assert.AreEqual("react", sheet.animations[2].name); Assert.AreEqual("bump", sheet.animations[3].name); Assert.AreEqual("flee", sheet.animations[4].name);
                Assert.IsTrue(File.Exists($"Assets/_Game/Art/creatures/earth/{e.key}_color.png"), e.key + " colour map");
            }
        }

        [System.Serializable] class Clip { public string name; public int start, length; }
        [System.Serializable] class Sheet { public int frame_width, frame_height; public float ppu; public float[] pivot; public Clip[] animations; }
    }
}
