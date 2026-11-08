using Meridian.EditorTools;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>
    /// U-169: on the smooth Earth the drawn curve never stands more than 0.25 m over the top solid tile (POI stamps applied as the game applies
    /// them), on 3 seeds. Where it did, the surveyor walked on drawn ground with a gap of air tiles under it: digs, drops and TopSolidY spawns
    /// read the ground 1.66 m too low 30 m west of the camp (HazardV2PlayTests' rescue: the camp's shoulder cone met rising ground in a
    /// V-notch the 9-tap curve bridges). Columns carved under their top (a stamp's room) draw their hole, not the curve, and are skipped.
    /// </summary>
    public class CurveOverTilesTests
    {
        public const float Allowed = GroundField.FillSlack;

        [Test]
        public void TheCurveNeverStandsOverUnfilledGround()
        {
            var cfg = AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/Earth.asset");
            Assert.NotNull(cfg, "Earth's config");
            int w = cfg.worldWidth, datum = cfg.datumY;
            foreach (int seed in new[] { 1969, 7717, 31337 })
            {
                var gen = new SolidWorldGenerator(cfg, seed);
                Assert.IsTrue(gen.SmoothGround);
                var edits = new TerrainEdits();
                foreach (var poi in PoiCatalog.For(PlanetId.Earth)) PoiStamp.Apply(poi, gen, edits, datum);
                System.Func<int, int> wrap = x => ((x % w) + w) % w;
                System.Func<int, int> top = x => PoiStamp.JointGround(gen, datum, PlanetId.Earth, wrap(x), out int g) ? g : gen.SurfaceHeight(wrap(x));
                System.Func<int, int> pad = x => PoiStamp.PadAt(gen, datum, PlanetId.Earth, wrap(x));
                int over = 0, carved = 0; float worst = 0f; string worstAt = "", first = null;
                for (int x = 0; x < w; x++)
                {
                    int t = TopSolid(gen, edits, x);
                    if (t < top(x)) { carved++; continue; } // a stamp's room or entrance: drawn as its hole (non-natural tiles), not as the curve
                    float gap = GroundField.Curve(x, top, pad) - (t + 1);
                    if (gap <= Allowed) continue;
                    over++;
                    string at = $"x {x}: curve {GroundField.Curve(x, top, pad):F2}, top solid {t}, joint/natural top {top(x)}, natural {gen.SurfaceHeight(x)}, pad {(pad(x) == int.MinValue ? "-" : pad(x).ToString())}, biome {EarthBiomes.At(x)}";
                    first ??= at;
                    if (gap > worst) { worst = gap; worstAt = at; }
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u169 seed {seed}: {over} columns with the curve over {Allowed} m above the top solid tile ({carved} carved columns skipped); worst {worst:F2} m at [{worstAt}]; first [{first}]");
                Assert.AreEqual(0, over, $"seed {seed}: the curve over unfilled ground (worst {worst:F2} m at [{worstAt}])");
            }
        }

        static int TopSolid(SolidWorldGenerator gen, TerrainEdits edits, int x)
        {
            for (int y = gen.SurfaceHeight(x) + 40; y > 0; y--)
            {
                byte id = edits.TryGet(x, y, out byte e) ? e : gen.TileAt(x, y);
                if (TileId.IsSolid(id)) return y;
            }
            return 0;
        }
    }
}
