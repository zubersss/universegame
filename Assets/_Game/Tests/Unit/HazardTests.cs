using Meridian.Hazards;
using Meridian.Planets;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-029: Cryo level table (Bible §7.1/§7.2) and hazard drain rules (§7: level 3 lethal in 30 s).</summary>
    public class HazardTests
    {
        const float Noon = 0.5f, Midnight = 0f;

        [Test]
        public void CryoLevelTable()
        {
            Assert.AreEqual(0, Cryo.Level(PlanetId.Earth, Noon, 0), "Earth surface: none");
            Assert.AreEqual(0, Cryo.Level(PlanetId.Earth, Midnight, 0), "Earth temperate night: none");
            Assert.AreEqual(1, Cryo.Level(PlanetId.Earth, Midnight, 0, tundra: true), "tundra night: 1");
            Assert.AreEqual(0, Cryo.Level(PlanetId.Earth, Noon, 0, tundra: true), "tundra day: 0");
            Assert.AreEqual(1, Cryo.Level(PlanetId.Mars, Noon, 0), "Mars day: 1");
            Assert.AreEqual(2, Cryo.Level(PlanetId.Mars, Midnight, 0), "Mars night: 2");
            Assert.AreEqual(2, Cryo.Level(PlanetId.Mars, Noon, 1), "Mars day + dust storm: 2");
            Assert.AreEqual(3, Cryo.Level(PlanetId.Mars, Midnight, 1), "Mars night + dust storm: 3");
            Assert.AreEqual(3, Cryo.Level(PlanetId.Mars, Midnight, 9), "clamped at 3");
        }

        [Test]
        public void ProtectionTiersLowerTheLevel()
        {
            Assert.AreEqual(2, HazardRules.Effective(3, 1));
            Assert.AreEqual(0, HazardRules.Effective(2, 3));
            Assert.AreEqual(3, HazardRules.Effective(3, 0));
        }

        [Test]
        public void Level3IsLethalIn30SecondsAndLowerLevelsAreNot()
        {
            Assert.AreEqual(0f, HazardRules.DrainPerSecond(0));
            Assert.That(HazardRules.DrainPerSecond(1), Is.LessThan(HazardRules.DrainPerSecond(2)));
            Assert.That(HazardRules.DrainPerSecond(2), Is.LessThan(HazardRules.DrainPerSecond(3)));
            float t3 = SecondsToDeath(3);
            Assert.LessOrEqual(t3, HazardRules.LethalSeconds, "level 3: lethal within 30 s");
            Assert.Greater(t3, 29f, "but not much sooner (suit first, then health)");
            Assert.Greater(SecondsToDeath(2), 30f, "level 2 is not lethal within 30 s");
            Assert.Greater(SecondsToDeath(1), 300f, "level 1 takes minutes");
        }

        static float SecondsToDeath(int level)
        {
            float suit = HazardRules.SuitMax, health = 100f, t = 0f, dt = 0.02f;
            while (health > 0f && t < 3600f)
            {
                float d = HazardRules.DrainPerSecond(level) * dt;
                float s = System.Math.Min(suit, d);
                suit -= s;
                health -= d - s;
                t += dt;
            }
            return t;
        }
    }
}
