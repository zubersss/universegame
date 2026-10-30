using System.Linq;
using Meridian.EditorTools;
using Meridian.Planets;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>U-002: PlanetConfig assets match Bible §3, §4.1, §5.1 (values typed here independently).</summary>
    public class PlanetConfigTests
    {
        // id, g, ×Earth, v_esc, fuel, width, height, datum, escAlt, escY, crush
        static readonly object[] Bible =
        {
            new object[] { PlanetId.Mercury, 3.70f,  0.38f, 4.3f,  6,  2048, 500,  320,  120, 440,  -1 },
            new object[] { PlanetId.Venus,   8.87f,  0.90f, 10.4f, 16, 4096, 1000, 320,  600, 920,  -1 },
            new object[] { PlanetId.Earth,   9.81f,  1.00f, 11.2f, 17, 4096, 800,  320,  400, 720,  -1 },
            new object[] { PlanetId.Mars,    3.72f,  0.38f, 5.0f,  8,  3072, 640,  320,  250, 570,  -1 },
            new object[] { PlanetId.Jupiter, 24.79f, 2.53f, 59.5f, 89, 4096, 2000, 1100, 800, 1900, 100 },
            new object[] { PlanetId.Saturn,  10.44f, 1.06f, 35.5f, 53, 4096, 2000, 1100, 700, 1800, 100 },
            new object[] { PlanetId.Uranus,  8.69f,  0.89f, 21.3f, 32, 4096, 2000, 1100, 600, 1700, 100 },
            new object[] { PlanetId.Neptune, 11.15f, 1.14f, 23.5f, 35, 4096, 2000, 1100, 650, 1750, 100 },
        };

        static PlanetConfig Load(PlanetId id) =>
            AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/{id}.asset");

        [Test]
        public void AllEightConfigsPresentAndInCatalog()
        {
            var catalog = AssetDatabase.LoadAssetAtPath<PlanetCatalog>(PlanetConfigAuthoring.CatalogPath);
            Assert.NotNull(catalog, "PlanetCatalog asset missing");
            foreach (PlanetId id in System.Enum.GetValues(typeof(PlanetId)))
            {
                var c = Load(id);
                Assert.NotNull(c, $"{id}.asset missing");
                Assert.AreEqual(id, c.id);
                Assert.AreSame(c, catalog.Get(id), $"catalog entry for {id}");
            }
            Assert.AreEqual(8, catalog.planets.Count(p => p != null));
        }

        [TestCaseSource(nameof(Bible))]
        public void GravityMatchesBible(PlanetId id, float g, float xEarth, float vEsc, int fuel,
            int w, int h, int datum, int escAlt, int escY, int crush)
        {
            var c = Load(id);
            Assert.That(c.gravity, Is.EqualTo(g).Within(0.5).Percent, "g");
            // Ratio to Earth ±0.5% of the exact ratio; the ×Earth column is that ratio to 2 decimals.
            var earth = Load(PlanetId.Earth);
            Assert.That(c.gravity / earth.gravity, Is.EqualTo(g / 9.81f).Within(0.5).Percent, "ratio");
            Assert.That(c.GravityRatio, Is.EqualTo(xEarth).Within(0.005f + 1e-4f), "×Earth column");
            Assert.AreEqual(-g, c.GravityVector.y, 1e-4f);
        }

        [TestCaseSource(nameof(Bible))]
        public void LaunchFuelIsRoundedOnePointFiveTimesEscapeVelocity(PlanetId id, float g, float xEarth,
            float vEsc, int fuel, int w, int h, int datum, int escAlt, int escY, int crush)
        {
            var c = Load(id);
            Assert.AreEqual(vEsc, c.escapeVelocityKms, 1e-4f, "v_esc");
            Assert.AreEqual(fuel, c.LaunchFuelCost, "launch fuel");
        }

        [TestCaseSource(nameof(Bible))]
        public void WorldDimensionsMatchSection5_1(PlanetId id, float g, float xEarth, float vEsc, int fuel,
            int w, int h, int datum, int escAlt, int escY, int crush)
        {
            var c = Load(id);
            Assert.AreEqual(w, c.worldWidth, "width");
            Assert.AreEqual(h, c.worldHeight, "height");
            Assert.AreEqual(datum, c.datumY, "datum");
            Assert.AreEqual(escAlt, c.escapeAltitude, "escape altitude");
            Assert.AreEqual(escY, c.EscapeLineY, "escape line y");
            Assert.AreEqual(crush, c.crushLineY, "crush line y");
            Assert.AreEqual(crush >= 0, c.HasCrushLine);
            Assert.Less(c.EscapeLineY, c.worldHeight, "escape line inside world");
        }

        [Test]
        public void LaunchFuelFormulaRoundsHalfUp()
        {
            Assert.AreEqual(8, PlanetConfig.LaunchFuelFor(5.0f));   // 7.5 → 8
            Assert.AreEqual(17, PlanetConfig.LaunchFuelFor(11.2f)); // 16.8 → 17
        }
    }
}
