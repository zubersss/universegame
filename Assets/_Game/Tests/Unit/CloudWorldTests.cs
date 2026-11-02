using Meridian.Planets;
using Meridian.Terrain;
using Meridian.Terrain.CloudColumn;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-061 (EditMode): the cloud-column generator behind IWorldGenerator (Bible §7.5).</summary>
    public class CloudWorldTests
    {
        static PlanetConfig Jupiter()
        {
            var c = ScriptableObject.CreateInstance<PlanetConfig>();
            c.id = PlanetId.Jupiter; c.worldType = WorldType.CloudColumn;
            c.worldWidth = 4096; c.worldHeight = 2000; c.datumY = 1100; c.escapeAltitude = 800;
            return c;
        }

        [Test]
        public void TilesMatchTheLayoutAndNothingIsSolidOutsideFloes()
        {
            var cfg = Jupiter();
            try
            {
                var gen = new CloudWorldGenerator(cfg, 1969);
                Assert.AreEqual(4096, gen.Width); Assert.AreEqual(2000, gen.Height);
                int solid = 0;
                for (int x = 0; x < 4096; x += 7)
                    for (int y = 0; y < 2000; y += 5)
                    {
                        byte t = gen.TileAt(x, y);
                        Assert.AreEqual(CloudLayout.TileAt(x, y, 1969), t);
                        if (t != TileId.Air) { solid++; Assert.IsTrue(t == TileId.FloeIce || t == TileId.FloeCore); }
                        if (y < CloudLayout.CrushLine || y >= CloudLayout.Datum) Assert.AreEqual(TileId.Air, t, $"no floe at y {y}");
                    }
                Assert.Greater(solid, 0, "the column holds floes");
            }
            finally { Object.DestroyImmediate(cfg); }
        }

        [Test]
        public void SurfaceIsTheTopOfTheHighestFloeOrTheDatum()
        {
            var cfg = Jupiter();
            try
            {
                var gen = new CloudWorldGenerator(cfg, 7);
                int onFloe = 0;
                for (int x = 0; x < 4096; x += 13)
                {
                    int s = gen.SurfaceHeight(x);
                    if (s == CloudLayout.Datum) continue;
                    onFloe++;
                    Assert.AreNotEqual(TileId.Air, gen.TileAt(x, s), $"x {x}: surface {s} is solid");
                    for (int y = s + 1; y < CloudLayout.Datum; y++)
                        Assert.AreEqual(TileId.Air, gen.TileAt(x, y), $"x {x}: nothing solid above the surface {s} (y {y})");
                }
                Assert.Greater(onFloe, 50, "most columns have a floe to stand on");
            }
            finally { Object.DestroyImmediate(cfg); }
        }

        [Test]
        public void GiantsLoadFloeTilesOnly()
        {
            foreach (var p in new[] { PlanetId.Jupiter, PlanetId.Saturn, PlanetId.Uranus, PlanetId.Neptune })
                CollectionAssert.AreEquivalent(new[] { TileId.FloeIce, TileId.FloeCore }, TerrainStreamer.MaterialsFor(p), p.ToString());
        }
    }
}
