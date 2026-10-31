using System.Collections.Generic;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>U-037: Earth biome bands (Bible §7.1), ocean and trench (D-010), smooth borders.</summary>
    public class BiomeTests
    {
        static PlanetConfig Earth() => AssetDatabase.LoadAssetAtPath<PlanetConfig>("Assets/_Game/Settings/Planets/Earth.asset");

        [Test]
        public void EveryBiomeAppearsExactlyOnceAndSpawnIsForest()
        {
            var runs = new Dictionary<Biome, int>();
            var prev = EarthBiomes.At(EarthBiomes.Width - 1);
            for (int x = 0; x < EarthBiomes.Width; x++)
            {
                var b = EarthBiomes.At(x);
                if (b != prev) { runs.TryGetValue(b, out int n); runs[b] = n + 1; }
                prev = b;
            }
            foreach (Biome b in System.Enum.GetValues(typeof(Biome)))
                Assert.AreEqual(1, runs.TryGetValue(b, out int n) ? n : 0, $"{b} is one band");
            Assert.AreEqual(Biome.Forest, EarthBiomes.At(64), "spawn in temperate forest");
            Assert.AreEqual(Biome.Forest, EarthBiomes.At(194), "the Survey Archive too");
            Assert.AreEqual(Biome.Ocean, EarthBiomes.At(2048 + 32 + 10), "the launch complex sits at the coast");
        }

        [Test]
        public void OceanFillsToSeaLevelAndHasADeepTrench()
        {
            var c = Earth();
            var g = new SolidWorldGenerator(c, 1969);
            EarthBiomes.Range(Biome.Ocean, out int start, out int len);
            int deepest = int.MaxValue;
            for (int i = 0; i < len; i++)
            {
                int x = (start + i) % c.worldWidth;
                int s = g.SurfaceHeight(x);
                deepest = System.Math.Min(deepest, s);
                if (i > EarthBiomes.Blend && i < len - EarthBiomes.Blend) // past the beaches the borders blend
                {
                    Assert.Less(s, c.datumY, $"ocean floor below sea level at x={x}");
                    Assert.AreEqual(TileId.Water, g.TileAt(x, c.datumY), $"water up to sea level at x={x}");
                    Assert.AreEqual(TileId.Water, g.TileAt(x, s + 1), $"water down to the floor at x={x}");
                }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] deepest ocean floor {c.datumY - deepest} m below sea level");
            Assert.GreaterOrEqual(c.datumY - deepest, 120, "a trench at least 120 m deep");
            Assert.LessOrEqual(c.datumY - deepest, 250, "within D-010's 250");
        }

        [Test]
        public void SurfaceMaterialFollowsTheBiome()
        {
            var c = Earth();
            var g = new SolidWorldGenerator(c, 1969);
            void Check(Biome b, byte top)
            {
                EarthBiomes.Range(b, out int start, out int len);
                int x = (start + len / 2) % c.worldWidth;
                Assert.AreEqual(top, g.TileAt(x, g.SurfaceHeight(x)), $"{b} top tile at its center (x={x})");
            }
            Check(Biome.Desert, TileId.Sand);
            Check(Biome.Tundra, TileId.Snow);
            Check(Biome.Plains, TileId.Grass);
            Check(Biome.Taiga, TileId.Grass);
            Check(Biome.Ocean, TileId.Sand);
        }

        [Test]
        public void HeightsAreDeterministicPerSeedAndBordersAreSmooth()
        {
            var c = Earth();
            var a = new SolidWorldGenerator(c, 1969);
            var a2 = new SolidWorldGenerator(c, 1969);
            var b = new SolidWorldGenerator(c, 7);
            int differ = 0;
            for (int x = 0; x < c.worldWidth; x++)
            {
                Assert.AreEqual(a.SurfaceHeight(x), a2.SurfaceHeight(x), "same seed, same world");
                if (a.SurfaceHeight(x) != b.SurfaceHeight(x)) differ++;
                int step = System.Math.Abs(a.SurfaceHeight((x + 1) % c.worldWidth) - a.SurfaceHeight(x));
                Assert.LessOrEqual(step, 3, $"no step over 3 tiles at x={x} ({EarthBiomes.At(x)} → {EarthBiomes.At(x + 1)})");
            }
            Assert.Greater(differ, c.worldWidth / 2, "another seed, another world");
        }
    }
}
