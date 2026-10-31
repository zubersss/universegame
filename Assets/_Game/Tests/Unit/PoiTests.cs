using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>U-030: POI stamps land at their fixed column in every world, exactly, once.</summary>
    public class PoiTests
    {
        static PlanetConfig Config(PlanetId id) =>
            AssetDatabase.LoadAssetAtPath<PlanetConfig>($"Assets/_Game/Settings/Planets/{id}.asset");

        [Test]
        public void CatalogIsWellFormed()
        {
            foreach (var poi in PoiCatalog.All)
            {
                var c = Config(poi.planet);
                Assert.That(poi.x, Is.InRange(0, c.worldWidth - poi.Width), $"{poi.id} inside the world");
                foreach (var row in poi.stamp) Assert.AreEqual(poi.Width, row.Length, $"{poi.id} rows all {poi.Width} wide");
                Assert.That(poi.groundRow, Is.InRange(0, poi.stamp.Length - 1));
                Assert.IsNotEmpty(poi.props, poi.id);
            }
            Assert.LessOrEqual(System.Math.Abs(PoiCatalog.SurveyArchive.CenterX - 64f), 200f, "the Archive is within 200 m of spawn");
            Assert.AreEqual(2, System.Linq.Enumerable.Count(PoiCatalog.For(PlanetId.Earth)));
            Assert.AreEqual(2, System.Linq.Enumerable.Count(PoiCatalog.For(PlanetId.Mars)));
        }

        [Test]
        public void StampsLandAtTheirColumnInEveryWorld([Values(1969, 7, 424242)] int seed)
        {
            foreach (var poi in PoiCatalog.All)
            {
                var c = Config(poi.planet);
                var world = new SolidWorldGenerator(c, seed);
                var edits = new TerrainEdits();
                int gy = PoiStamp.Apply(poi, world, edits, c.datumY);
                Assert.GreaterOrEqual(gy, c.datumY + 1, $"{poi.id}: ground above sea level");
                var edited = new EditedWorld(world, edits);
                int cells = 0;
                for (int row = 0; row < poi.stamp.Length; row++)
                for (int col = 0; col < poi.Width; col++)
                {
                    var want = PoiStamp.CellTile(poi.stamp[row][col], poi.planet);
                    if (want == null) continue;
                    int x = PoiStamp.Wrap(poi.x + col, c.worldWidth), y = PoiStamp.RowY(poi, row, gy);
                    Assert.AreEqual(want.Value, edited.TileAt(x, y), $"{poi.id} seed {seed} cell ({col},{row})");
                    cells++;
                }
                Assert.Greater(cells, 100, poi.id);
                int count = edits.Count;
                PoiStamp.Apply(poi, world, edits, c.datumY);
                Assert.AreEqual(count, edits.Count, $"{poi.id}: stamping again changes nothing");
            }
        }
    }
}
