using Meridian.Core;
using Meridian.Mining;
using Meridian.Planets;
using Meridian.Progress;
using Meridian.Rig;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-193 (D-182, the owner 11-09): a new surveyor digs with the shovel (D1_TABLES §1: stroke base 0.5 s, cap 12 s, reach 2 m); The Beam
    /// (dig_power_1, 250 Scrip) swaps it for the Beam for good (0.25 s base, its reach, 8 s cap, power 1.5); a save keeps the swap; a New
    /// Expedition starts with the shovel again.
    /// </summary>
    public class ShovelTests
    {
        GameObject go;
        GameState s;

        [SetUp]
        public void SetUp()
        {
            go = new GameObject("GameStateU193");
            s = go.AddComponent<GameState>();
            SkillStats.Recompute(s);
        }

        [TearDown]
        public void TearDown()
        {
            SkillStats.Recompute(null);
            Object.DestroyImmediate(go);
        }

        [Test]
        public void TheShovelsStrokesOnTheTables()
        {
            var t = D1Tables.Current;
            Assert.AreEqual(DigTool.Shovel, SkillStats.DigTool, "a new surveyor's shovel");
            Assert.AreEqual(1f, SkillStats.DigPower, 1e-5f);
            Assert.AreEqual(2f, SkillStats.DigReach, 1e-5f, "the shovel reaches 2 m");
            Assert.AreEqual(0.5f, t.StrokeSeconds(PlanetId.Earth, 5f, SkillStats.DigPower, SkillStats.DigTool), 1e-4f, "T1 on Earth");
            Assert.AreEqual(2f, t.StrokeSeconds(PlanetId.Earth, 55f, SkillStats.DigPower, SkillStats.DigTool), 1e-4f, "T3 on Earth");
            Assert.AreEqual(12f, t.StrokeSeconds(PlanetId.Earth, 230f, 0.05f, DigTool.Shovel), 1e-4f, "the shovel's 12 s cap");
            Assert.AreEqual(8f, t.StrokeSeconds(PlanetId.Earth, 230f, 0.05f, DigTool.Beam), 1e-4f, "the Beam's 8 s cap");
            Assert.AreEqual(t.StrokeSeconds(PlanetId.Earth, 55f, 1f), t.StrokeSeconds(PlanetId.Earth, 55f, 1f, DigTool.Beam), 1e-6f, "the 3-argument form is the Beam's");
        }

        [Test]
        public void TheBeamSwapsTheShovelForGoodAndASaveKeepsIt()
        {
            var tree = SkillTree.Current;
            var beam = tree.Get("dig_power_1");
            Assert.AreEqual("The Beam", beam.name);
            Assert.AreEqual(250, beam.scrip, "The Beam costs 250 Scrip");
            Assert.IsEmpty(beam.requires, "it needs only the centre");
            s.scrip = 1000;
            Assert.AreEqual(SkillTree.BuyResult.Ok, tree.Buy(s, "dig_power_1", true));
            Assert.AreEqual(DigTool.Beam, SkillStats.DigTool, "bought: the Beam");
            Assert.AreEqual(1.5f, SkillStats.DigPower, 1e-5f);
            Assert.AreEqual(RigTools.Reach, SkillStats.DigReach, 1e-5f, "the Beam's reach");
            Assert.AreEqual(0.25f / 1.5f, D1Tables.Current.StrokeSeconds(PlanetId.Earth, 5f, SkillStats.DigPower, SkillStats.DigTool), 1e-4f, "T1: 0.167 s");

            // a save and a load keep it (the tool follows the bought node)
            var data = new Meridian.Save.SaveData();
            data.skillNodes.AddRange(s.skillNodes);
            var back = JsonUtility.FromJson<Meridian.Save.SaveData>(JsonUtility.ToJson(data));
            s.skillNodes.Clear();
            SkillStats.Apply(s);
            Assert.AreEqual(DigTool.Shovel, SkillStats.DigTool, "nothing bought: the shovel");
            foreach (var n in back.skillNodes) s.skillNodes.Add(n);
            SkillStats.Apply(s);
            Assert.AreEqual(DigTool.Beam, SkillStats.DigTool, "loaded: the Beam again");
        }

        [Test]
        public void ANewExpeditionStartsWithTheShovel()
        {
            s.scrip = 1000;
            Assert.AreEqual(SkillTree.BuyResult.Ok, SkillTree.Current.Buy(s, "dig_power_1", true));
            Assert.AreEqual(DigTool.Beam, SkillStats.DigTool);
            s.scripEarned = 1000000; // Rank 10
            Assert.IsTrue(Expedition.Begin(s, true), "a New Expedition at Rank 10, topside");
            Assert.AreEqual(DigTool.Shovel, SkillStats.DigTool, "the shovel again");
            Assert.AreEqual(0, RigLooks.BeamMk(s.skillNodes), "and its look");
        }
    }
}
