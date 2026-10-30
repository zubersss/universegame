using System.Linq;
using Meridian.EditorTools;
using Meridian.Planets;
using Meridian.Space;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-011 (EditMode): well formula (Bible §4.4) and the top-down layout (Bible §3).</summary>
    public class SpaceTests
    {
        static PlanetCatalog Catalog() =>
            AssetDatabase.LoadAssetAtPath<PlanetCatalog>(PlanetConfigAuthoring.CatalogPath);

        [Test]
        public void EarthWellEdgePullsOneUnitPerSecondSquared()
        {
            Assert.That(WellMath.Acceleration(9.81f, 25f, 100f), Is.EqualTo(1.00f).Within(1).Percent);
        }

        [Test]
        public void RingPullsMatchBible()
        {
            Assert.AreEqual(11.1f, WellMath.Acceleration(9.81f, 25f, 30f), 0.05f, "Earth at its Atmosphere Ring");
            Assert.AreEqual(28.1f, WellMath.Acceleration(24.79f, 106f, 127.2f), 0.05f, "Jupiter at its Atmosphere Ring");
            Assert.AreEqual(0f, WellMath.Acceleration(9.81f, 25f, 100.01f), "nothing outside 4R");
        }

        // Bible §3 table: orbit radius, R, Atmosphere Ring, Gravity Well.
        [TestCase("mercury", 1150f, 14f, 17f, 56f)] [TestCase("venus", 1650f, 24f, 29f, 96f)]
        [TestCase("earth", 2000f, 25f, 30f, 100f)] [TestCase("mars", 2550f, 17f, 20f, 68f)]
        [TestCase("jupiter", 5400f, 106f, 127f, 424f)] [TestCase("saturn", 7700f, 96f, 115f, 384f)]
        [TestCase("uranus", 11800f, 57f, 68f, 228f)] [TestCase("neptune", 15400f, 56f, 67f, 224f)]
        public void PlanetPositionsAndRadiiMatchSection3(string name, float orbit, float r, float ring, float well)
        {
            var b = SpaceLayout.Build(Catalog()).Single(x => x.name == name);
            Assert.AreEqual(orbit, b.position.magnitude, 0.01f, "orbit radius");
            Assert.AreEqual(r, b.radius, "R");
            Assert.AreEqual(ring, b.RingRadius, 0.5f, "ring 1.2R (table rounds)");
            Assert.AreEqual(well, b.WellRadius, 0.01f, "well 4R");
            Assert.IsTrue(b.landable);
        }

        [Test]
        public void SunAndMoonsFollowSection3()
        {
            var bodies = SpaceLayout.Build(Catalog());
            var sun = bodies.Single(b => b.isSun);
            Assert.AreEqual(Vector2.zero, sun.position);
            Assert.AreEqual(300f, sun.radius);
            Assert.AreEqual(1200f, sun.WellRadius);
            Assert.AreEqual(360f, WellMath.SunKillFactor * sun.radius);
            Assert.IsFalse(sun.landable);
            foreach (var m in bodies.Where(b => b.parent != null))
            {
                Assert.That(m.radius, Is.InRange(3f, 8f), m.name);
                Assert.AreEqual(3f * m.radius, m.WellRadius, 1e-4f, m.name);
                Assert.IsFalse(m.landable, m.name);
            }
            Assert.AreEqual(7, bodies.Count(b => b.parent != null), "Luna, Phobos, Deimos, Io, Europa, Titan, Triton");
        }

        [Test]
        public void EarthToMarsIsAboutSevenSecondsAtCruise()
        {
            var bodies = SpaceLayout.Build(Catalog());
            float d = Vector2.Distance(bodies.Single(b => b.name == "earth").position, bodies.Single(b => b.name == "mars").position);
            Assert.AreEqual(7f, d / SpaceLayout.CruiseSpeed, 0.5f);
        }

        [Test]
        public void NoTwoWellsOverlapOutsideTheSun()
        {
            var bodies = SpaceLayout.Build(Catalog()).Where(b => !b.isSun).ToList();
            for (int i = 0; i < bodies.Count; i++)
            for (int j = i + 1; j < bodies.Count; j++)
            {
                float d = Vector2.Distance(bodies[i].position, bodies[j].position);
                Assert.Greater(d, bodies[i].WellRadius + bodies[j].WellRadius, $"{bodies[i].name} / {bodies[j].name}");
            }
            foreach (var b in bodies)
            {
                float r = b.position.magnitude;
                Assert.IsTrue(r + b.WellRadius < SpaceLayout.BeltInner || r - b.WellRadius > SpaceLayout.BeltOuter, $"{b.name} well clear of the belt");
            }
        }
    }
}
