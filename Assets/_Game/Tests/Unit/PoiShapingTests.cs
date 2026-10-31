using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>
    /// U-057 (EditMode): a stamped POI blends into the surface: shoulders step at most 2 m, the pad sits on
    /// solid ground (no air gap under it for the backdrop to show through), and nothing overhangs it.
    /// </summary>
    public class PoiShapingTests
    {
        static PlanetConfig Config(PlanetId id) =>
            AssetDatabase.LoadAssetAtPath<PlanetConfig>($"Assets/_Game/Settings/Planets/{id}.asset");

        static int Top(EditedWorld w, int x, int height)
        {
            for (int y = height - 1; y >= 0; y--) if (TileId.IsSolid(w.TileAt(x, y))) return y;
            return -1;
        }

        [Test]
        public void PadsBlendIntoTheSurface([Values(1969, 7, 424242)] int seed)
        {
            foreach (var poi in PoiCatalog.All)
            {
                if (poi.Floating) continue;
                var c = Config(poi.planet);
                var gen = new SolidWorldGenerator(c, seed);
                var edits = new TerrainEdits();
                int gy = PoiStamp.Apply(poi, gen, edits, c.datumY);
                var world = new EditedWorld(gen, edits);
                int W = c.worldWidth;

                // Shoulders: neighbouring columns differ by at most MaxStep, outside the pad on both sides.
                for (int col = -PoiStamp.MaxShoulder; col < poi.Width + PoiStamp.MaxShoulder - 1; col++)
                {
                    if (col >= -1 && col < poi.Width) continue; // the pad itself is a stamp (its props stand there)
                    int a = PoiStamp.Wrap(poi.x + col, W), b = PoiStamp.Wrap(poi.x + col + 1, W);
                    bool shaped = PoiStamp.ShapedGround(poi, gen, c.datumY, a, out _) || PoiStamp.ShapedGround(poi, gen, c.datumY, b, out _);
                    if (!shaped) continue;
                    int step = System.Math.Abs(Top(world, a, c.worldHeight) - Top(world, b, c.worldHeight));
                    Assert.LessOrEqual(step, PoiStamp.MaxStep, $"{poi.id} seed {seed}: shoulder step at column {col}");
                }

                // Under the pad: solid (or Earth's sea) all the way down to the natural surface.
                for (int col = 0; col < poi.Width; col++)
                {
                    int x = PoiStamp.Wrap(poi.x + col, W);
                    int natural = gen.SurfaceHeight(x);
                    for (int y = System.Math.Min(gy, natural); y >= natural - 2 && y >= 0; y--)
                    {
                        int row = poi.groundRow - (y - gy);
                        if (row >= 0 && row < poi.stamp.Length && poi.stamp[row][col] == '.') continue; // a designed room (the Archive's chambers)
                        byte t = world.TileAt(x, y);
                        Assert.IsTrue(TileId.IsSolid(t) || t == TileId.Water, $"{poi.id} seed {seed}: gap under the pad at col {col}, y {y}");
                    }
                    // Nothing overhangs the pad: open air (or water) above its stamp, up to the natural surface.
                    int padTop = PoiStamp.RowY(poi, 0, gy);
                    for (int y = padTop + 1; y <= natural; y++)
                        Assert.IsFalse(TileId.IsSolid(world.TileAt(x, y)), $"{poi.id} seed {seed}: overhang at col {col}, y {y}");
                }
            }
        }
    }
}
