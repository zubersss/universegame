using Meridian.Core;
using Meridian.Mining;
using Meridian.Player;
using Meridian.Progress;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-176 (Bible 5.2 §8.1, D1_TABLES §4 "Climbing", LEAD 23:5x): the ways back up as data. The tables' times for 30 m by each way, empty and
    /// with a full pack (load factor 0.5); each Ascent node changes its stat by the table's amount; the grip's slope test; the clips.
    /// (AscentPlayTests climbs a real shaft by each way against these.)
    /// </summary>
    public class AscentTests
    {
        GameObject go;
        GameState s;

        [SetUp]
        public void SetUp()
        {
            go = new GameObject("GameStateU176");
            s = go.AddComponent<GameState>();
            SkillStats.Recompute(s);
        }

        [TearDown]
        public void TearDown()
        {
            SkillStats.Recompute(null);
            Object.DestroyImmediate(go);
        }

        void Buy(params string[] ids)
        {
            foreach (var id in ids) s.skillNodes.Add(id);
            SkillStats.Recompute(s);
        }

        [Test]
        public void TheTablesTimeEachWayUpThirtyMetres()
        {
            var t = D1Tables.Current.ascent;
            Assert.AreEqual(2.5f, t.ladderClimb); Assert.AreEqual(2f, t.ladderDirtPerM); Assert.AreEqual(4f, t.grappleReel);
            Assert.AreEqual(6f, t.winchSpeed, "LEAD 23:5x: the ring-5 winch beats the grapple"); Assert.AreEqual(5f, t.recallSeconds); Assert.AreEqual(35f, t.walkRampDeg);
            Assert.AreEqual(12f, Ascent.ColumnSeconds(30f, Ascent.LadderSpeed, 1f), 1e-3f, "ladder, empty");
            Assert.AreEqual(24f, Ascent.ColumnSeconds(30f, Ascent.LadderSpeed, 0.5f), 1e-3f, "ladder, a full pack (k 0.5)");
            Assert.AreEqual(5f, Ascent.ColumnSeconds(30f, Ascent.WinchSpeed, 1f), 1e-3f, "winch, empty");
            Assert.AreEqual(10f, Ascent.ColumnSeconds(30f, Ascent.WinchSpeed, 0.5f), 1e-3f, "winch, full");
            Assert.AreEqual(33.3f, Ascent.ColumnSeconds(200f, Ascent.WinchSpeed, 1f), 0.1f, "200 m by the winch");
            Buy("asc_grapple_1");
            float g = Ascent.GrappleSeconds(30f, SkillStats.GrappleM, Ascent.ReelSpeed, Ascent.HookSpeed, 1f);
            Assert.AreEqual(8.5f, g, 0.3f, "grapple (12 m line): ~3 hops, ~8.5 s empty");
            Assert.AreEqual(16f, Ascent.GrappleSeconds(30f, SkillStats.GrappleM, Ascent.ReelSpeed, Ascent.HookSpeed, 0.5f), 0.3f, "~16 s full");
        }

        [Test]
        public void EachAscentNodeChangesItsStatByItsAmount()
        {
            Assert.AreEqual(0f, SkillStats.LadderM, "no ladders before asc_ladder_1");
            Assert.AreEqual(0f, SkillStats.GrappleM, "no Grapple before asc_grapple_1");
            Assert.IsFalse(SkillStats.Winch); Assert.AreEqual(0, SkillStats.RecallBeacons); Assert.AreEqual(1, SkillStats.GrappleAnchors);
            Assert.AreEqual(35f, SkillStats.NoSlideDeg);
            float ladder = Ascent.LadderSpeed, reel = Ascent.ReelSpeed, thrust = SkillStats.JetThrust, power = SkillStats.JetPowerUse;

            Buy("asc_ladder_1");
            Assert.AreEqual(1f, SkillStats.LadderM); Assert.AreEqual(2f, SkillStats.LadderDirtPerM, "1 m a placement at 2 dirt a metre");
            Buy("asc_climb_1");
            Assert.AreEqual(ladder * 1.3f, Ascent.LadderSpeed, 1e-4f, "climbing ×1.3");
            Assert.AreEqual(40f, SkillStats.NoSlideDeg, "no slide on ≤ 40°");
            Assert.AreEqual(9.23f, Ascent.ColumnSeconds(30f, Ascent.LadderSpeed, 1f), 0.01f, "30 m of ladder with asc_climb_1");
            Buy("asc_ladder_2");
            Assert.AreEqual(3f, SkillStats.LadderM); Assert.AreEqual(1f, SkillStats.LadderDirtPerM, "3 m a placement at 1 dirt a metre");

            Buy("asc_grapple_1");
            Assert.AreEqual(12f, SkillStats.GrappleM); Assert.AreEqual(reel, Ascent.ReelSpeed, 1e-4f);
            Buy("asc_jet_1");
            Assert.AreEqual(thrust * 1.3f, SkillStats.JetThrust, 1e-4f);
            Buy("asc_grapple_2");
            Assert.AreEqual(24f, SkillStats.GrappleM); Assert.AreEqual(reel * 1.5f, Ascent.ReelSpeed, 1e-4f);
            Buy("asc_jet_2");
            Assert.AreEqual(power * 0.7f, SkillStats.JetPowerUse, 1e-4f);
            Buy("asc_jet_3");
            Assert.AreEqual(thrust * 1.6f, SkillStats.JetThrust, 1e-4f); Assert.AreEqual(power * 0.5f, SkillStats.JetPowerUse, 1e-4f);
            Buy("asc_grapple_3");
            Assert.AreEqual(40f, SkillStats.GrappleM); Assert.AreEqual(reel * 2f, Ascent.ReelSpeed, 1e-4f); Assert.AreEqual(2, SkillStats.GrappleAnchors);
            Assert.Less(Ascent.GrappleSeconds(30f, 40f, Ascent.ReelSpeed, Ascent.HookSpeed, 1f), Ascent.ColumnSeconds(30f, Ascent.LadderSpeed, 1f));
            Buy("asc_winch");
            Assert.IsTrue(SkillStats.Winch);
            Buy("asc_recall");
            Assert.AreEqual(1, SkillStats.RecallBeacons);
        }

        [Test]
        public void TheLoadSlowsTheJetpackAboveGravityNeverStrands()
        {
            // U-190 (D1_TABLES §4, 01:5x): effective lift = g + (thrust − g) × load factor when thrust > g
            Assert.AreEqual(14f, PlayerController.JetLift(14f, 14f, 9.81f, 1f), 1e-4f, "empty: the whole thrust");
            Assert.AreEqual(9.81f + 4.19f * 0.5f, PlayerController.JetLift(14f, 14f, 9.81f, 0.5f), 1e-4f, "a full Mk1 pack on Earth climbs at half the net rate");
            Assert.Greater(PlayerController.JetLift(14f, 14f, 9.81f, 0.5f), 9.81f, "it still rises");
            Assert.AreEqual(3.71f + 10.29f * 0.5f, PlayerController.JetLift(14f, 14f, 3.71f, 0.5f), 1e-4f, "Mars");
            Assert.AreEqual((9.81f + 4.19f * 0.5f) * 0.5f, PlayerController.JetLift(7f, 14f, 9.81f, 0.5f), 1e-4f, "the step the charge runs out in: its share");
            Assert.AreEqual(4f, PlayerController.JetLift(8f, 8f, 9.81f, 0.5f), 1e-4f, "a thrust under g scales whole");
            Assert.AreEqual(0f, PlayerController.JetLift(0f, 14f, 9.81f, 0.5f), "not firing");
        }

        [Test]
        public void TheGripHoldsRampsUpToItsAngle()
        {
            Vector2 Normal(float deg) => new Vector2(-Mathf.Sin(deg * Mathf.Deg2Rad), Mathf.Cos(deg * Mathf.Deg2Rad));
            Assert.IsFalse(PlayerController.TooSteep(Normal(30f), 35f));
            Assert.IsFalse(PlayerController.TooSteep(Normal(35f), 35f), "35° walks (D1_TABLES §4)");
            Assert.IsTrue(PlayerController.TooSteep(Normal(37.5f), 35f), "steeper slides");
            Assert.IsFalse(PlayerController.TooSteep(Normal(37.5f), 40f), "asc_climb_1: no slide on ≤ 40°");
            Assert.IsTrue(PlayerController.TooSteep(Normal(42f), 40f));
            Assert.IsFalse(PlayerController.TooSteep(Vector2.up, 35f));
        }

        [Test]
        public void TheClimbsHaveTheirClips()
        {
            Assert.AreEqual(SurveyorAnim.ClimbLadder, SurveyorAnim.Pick(new AnimInputs { ladder = true, grounded = true, sinceHurt = 99, sinceLand = 99, sinceDig = 99, sinceBump = 99, sinceJump = 99, sinceBuild = 99, sinceSurprise = 99 }));
            Assert.AreEqual(SurveyorAnim.ReelUp, SurveyorAnim.Pick(new AnimInputs { reeling = true, sinceHurt = 99, sinceLand = 99, sinceDig = 99, sinceBump = 99, sinceJump = 99, sinceBuild = 99, sinceSurprise = 99 }));
            CollectionAssert.Contains(SurveyorAnim.AllClips, SurveyorAnim.ClimbLadder);
            CollectionAssert.Contains(SurveyorAnim.AllClips, SurveyorAnim.ReelUp);
        }
    }
}
