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
    /// the hidden grid never more than one tile, and each pad's middle stays flat (the Pilgrim's pad, the camp).
    /// </summary>
    public class SmoothGroundTests
    {
        [Test]
        public void EarthsCurveStaysWalkableOnTenSeeds()
        {
            var cfg = AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/Earth.asset");
            Assert.NotNull(cfg, "Earth's config");
            Assert.IsTrue(GroundField.Smooth(PlanetId.Earth), "Earth is a smooth planet (D-161 (6))");
            var pois = new List<PoiDef>();
            foreach (var p in PoiCatalog.For(PlanetId.Earth)) if (!p.Floating && p.stamp != null) pois.Add(p);
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
                    tops[x] = PoiStamp.JointGround(gen, cfg.datumY, PlanetId.Earth, x, out int g) ? g : gen.SurfaceHeight(x); // TerrainStreamer.WallTop on a smooth planet
                }
                System.Func<int, int> top = x => tops[((x % w) + w) % w];
                float worst = 0f; int at = 0, worstStep = 0;
                for (int x = 0; x < w; x++)
                {
                    float s = Mathf.Abs(GroundField.Curve(x + 1, top) - GroundField.Curve(x, top));
                    if (s > worst) { worst = s; at = x; }
                    worstStep = Mathf.Max(worstStep, Mathf.Abs(top(x + 1) - top(x)));
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u156 seed {seed}: steepest curve step {worst:F3} m per m at column {at}, largest grid step {worstStep}");
                Assert.LessOrEqual(worst, GroundField.MaxWalkSlope, $"seed {seed}: the curve at column {at} steps {worst:F3} (≤ tan 35°)");
                Assert.LessOrEqual(worstStep, 1, $"seed {seed}: the hidden grid never steps more than one tile");
                for (int i = 0; i < pois.Count; i++)
                {
                    var poi = pois[i];
                    int r = GroundField.CurveKernel.Length / 2;
                    for (int x = poi.x + r; x < poi.x + poi.Width - r; x++)
                        Assert.AreEqual(pads[i] + 1f, GroundField.Curve(x, top), 1e-4f, $"seed {seed}: the pad at x {poi.x}: its middle stays flat at column {x}");
                }
            }
        }
    }
}
