using System.Collections.Generic;
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
    /// U-156 (EditMode, D-161 / D-162): Earth's drawn ground stays walkable. On ten seeds, with every stamped POI's shaping in (the pad raised
    /// or cut, its shoulders eased at 0.65, joint where two POIs' shoulders meet), the surface curve the outline follows never steps more than tan 35° between neighbouring columns,
    /// the hidden grid never more than one tile, and each pad stays flat to its ends (the Pilgrim's pad, the camp, the crates at its edge).
    /// </summary>
    public class SmoothGroundTests
    {
        [TestCase(PlanetId.Earth)]
        [TestCase(PlanetId.Mars)] // U-159
        public void TheCurveStaysWalkableOnTenSeeds(PlanetId planet)
        {
            var cfg = AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/{planet}.asset");
            Assert.NotNull(cfg, planet + "'s config");
            Assert.IsTrue(GroundField.Smooth(planet), $"{planet} is a smooth planet (D-161 (6), U-159)");
            var pois = new List<PoiDef>();
            foreach (var p in PoiCatalog.For(planet)) if (!p.Floating && p.stamp != null) pois.Add(p);
            int w = cfg.worldWidth;
            for (int seed = 1; seed <= 10; seed++)
            {
                var gen = new SolidWorldGenerator(cfg, seed * 7717);
                Assert.IsTrue(gen.SmoothGround, $"seed {seed}: the generator smooths Earth");
                var pads = new int[pois.Count];
                for (int i = 0; i < pois.Count; i++) pads[i] = PoiStamp.GroundY(pois[i], gen, cfg.datumY);
                var tops = new int[w];
                for (int x = 0; x < w; x++)
                {
                    tops[x] = PoiStamp.JointGround(gen, cfg.datumY, planet, x, out int g) ? g : gen.SurfaceHeight(x); // TerrainStreamer.WallTop on a smooth planet
                }
                System.Func<int, int> top = x => tops[((x % w) + w) % w];
                System.Func<int, int> pad = x => PoiStamp.PadAt(gen, cfg.datumY, planet, x); // TerrainStreamer.PadTop
                float worst = 0f; int at = 0, worstStep = 0;
                for (int x = 0; x < w; x++)
                {
                    float s = Mathf.Abs(GroundField.Curve(x + 1, top, pad) - GroundField.Curve(x, top, pad));
                    if (s > worst) { worst = s; at = x; }
                    worstStep = Mathf.Max(worstStep, Mathf.Abs(top(x + 1) - top(x)));
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u156 {planet} seed {seed}: steepest curve step {worst:F3} m per m at column {at}, largest grid step {worstStep}");
                Assert.LessOrEqual(worst, GroundField.MaxWalkSlope, $"seed {seed}: the curve at column {at} steps {worst:F3} (≤ tan 35°)");
                Assert.LessOrEqual(worstStep, 1, $"seed {seed}: the hidden grid never steps more than one tile");
                for (int i = 0; i < pois.Count; i++)
                {
                    var poi = pois[i];
                    for (int x = poi.x; x < poi.x + poi.Width; x++) // the whole stamp: its props never stand over the easing
                        Assert.AreEqual(pads[i] + 1f, GroundField.Curve(x, top, pad), 1e-4f, $"seed {seed}: the pad at x {poi.x} stays flat to its ends: column {x}");
                }
            }
        }
    }
}
