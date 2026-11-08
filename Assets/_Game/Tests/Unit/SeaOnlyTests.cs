using Meridian.EditorTools;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-166 (D-171): on the smooth Earth only the sea holds water. On 3 seeds no liquid tile lies outside the Ocean band (an inland basin under
    /// the datum is dry ground: smoke_42's valley at 4506 held a lake drawn as faint tiles), and none lies under the drawn outline (its centre
    /// under the column's curve, where the ground mesh would cover it); the sea itself still fills to the water line. The count the old
    /// rule (every column under the datum) would have flooded inland is logged.
    /// </summary>
    public class SeaOnlyTests
    {
        [Test]
        public void OnlyTheSeaHoldsWaterOnTheSmoothEarth()
        {
            var cfg = AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/Earth.asset");
            Assert.NotNull(cfg, "Earth's config");
            int w = cfg.worldWidth, datum = cfg.datumY;
            foreach (int seed in new[] { 1969, 7717, 31337 })
            {
                var gen = new SolidWorldGenerator(cfg, seed);
                Assert.IsTrue(gen.SmoothGround);
                var tops = new int[w];
                for (int x = 0; x < w; x++) tops[x] = PoiStamp.JointGround(gen, datum, PlanetId.Earth, x, out int g) ? g : gen.SurfaceHeight(x);
                System.Func<int, int> top = x => tops[((x % w) + w) % w];
                System.Func<int, int> pad = x => PoiStamp.PadAt(gen, datum, PlanetId.Earth, x);
                int inland = 0, under = 0, oldInland = 0, sea = 0; string firstInland = null, firstUnder = null;
                for (int x = 0; x < w; x++)
                {
                    bool ocean = EarthBiomes.At(x) == Biome.Ocean;
                    if (!ocean && gen.SurfaceHeight(x) < datum) oldInland += datum - gen.SurfaceHeight(x);
                    float curve = GroundField.Curve(x, top, pad);
                    for (int y = gen.SurfaceHeight(x) + 1; y <= datum; y++)
                    {
                        if (gen.TileAt(x, y) != TileId.Water) continue;
                        sea++;
                        if (!ocean) { inland++; firstInland ??= $"({x}, {y})"; }
                        else if (y + 0.5f < curve) { under++; firstUnder ??= $"({x}, {y}) under the curve {curve:F2}"; }
                    }
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u166 seed {seed}: {sea} water tiles; inland {inland} (the old rule flooded {oldInland}); under the outline {under}");
                Assert.AreEqual(0, inland, $"seed {seed}: no water outside the Ocean band (first {firstInland})");
                Assert.AreEqual(0, under, $"seed {seed}: no water under the outline (first {firstUnder})");
                Assert.Greater(sea, 10000, $"seed {seed}: the sea still fills to the water line");
                Assert.AreEqual(TileId.Water, gen.TileAt(EarthBiomes.TrenchCenter, datum), $"seed {seed}: the open sea at the water line");
            }
        }
    }
}
