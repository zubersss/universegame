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
        // id, g, ×Earth, v_esc, climb (lowest thruster mark, D-106), width, height, datum, escAlt, escY, crush
        static readonly object[] Bible =
        {
            new object[] { PlanetId.Mercury, 3.70f,  0.38f, 4.3f,  1,  2048, 500,  320,  120, 440,  -1 },
            new object[] { PlanetId.Venus,   8.87f,  0.90f, 10.4f, 1,  4096, 1000, 320,  600, 920,  -1 },
            new object[] { PlanetId.Earth,   9.81f,  1.00f, 11.2f, 1,  4096, 800,  320,  400, 720,  -1 },
            new object[] { PlanetId.Mars,    3.72f,  0.38f, 5.0f,  1,  3072, 640,  320,  250, 570,  -1 },
            new object[] { PlanetId.Jupiter, 24.79f, 2.53f, 59.5f, 3,  4096, 2000, 1100, 800, 1900, 100 },
            new object[] { PlanetId.Saturn,  10.44f, 1.06f, 35.5f, 1,  4096, 2000, 1100, 700, 1800, 100 },
            new object[] { PlanetId.Uranus,  8.69f,  0.89f, 21.3f, 1,  4096, 2000, 1100, 600, 1700, 100 },
            new object[] { PlanetId.Neptune, 11.15f, 1.14f, 23.5f, 1,  4096, 2000, 1100, 650, 1750, 100 },
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
        public void GravityMatchesBible(PlanetId id, float g, float xEarth, float vEsc, int climb,
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
        public void ThrusterClassMatchesBible(PlanetId id, float g, float xEarth,
            float vEsc, int climb, int w, int h, int datum, int escAlt, int escY, int crush)
        {
            var c = Load(id);
            Assert.AreEqual(vEsc, c.escapeVelocityKms, 1e-4f, "v_esc");
            // U-107 (D-103, D-106): thrust-to-weight is the only climb limit (the launch-fuel column is gone).
            Assert.AreEqual(climb, c.MinThrusterToClimb, "lowest thruster mark that climbs");
        }

        [TestCaseSource(nameof(Bible))]
        public void WorldDimensionsMatchSection5_1(PlanetId id, float g, float xEarth, float vEsc, int climb,
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

        /// <summary>D-106: Mk1 lifts off every planet but Jupiter (Saturn net 1.56, Neptune 0.85 m/s²); Mk2 can't lift off Jupiter (20 &lt; 24.79); Mk3 can.</summary>
        [Test]
        public void ThrusterClassIsPhysicsAlone()
        {
            foreach (PlanetId id in System.Enum.GetValues(typeof(PlanetId)))
            {
                var c = Load(id);
                Assert.AreEqual(id != PlanetId.Jupiter, Meridian.Ship.ShipMarks.CanClimb(1, c.gravity), $"Mk1 on {id}");
                Assert.AreEqual(id != PlanetId.Jupiter, Meridian.Ship.ShipMarks.CanClimb(2, c.gravity), $"Mk2 on {id}");
                Assert.IsTrue(Meridian.Ship.ShipMarks.CanClimb(3, c.gravity), $"Mk3 on {id}");
            }
            Assert.AreEqual(1.56f, Meridian.Ship.ShipMarks.Thrust(1) - Load(PlanetId.Saturn).gravity, 0.01f, "Saturn net on Mk1");
            Assert.AreEqual(0.85f, Meridian.Ship.ShipMarks.Thrust(1) - Load(PlanetId.Neptune).gravity, 0.01f, "Neptune net on Mk1");
            Assert.AreEqual(4, Meridian.Ship.ShipMarks.MinThrusterToClimb(40f), "nothing climbs against 40 m/s²");
        }
    }
}
