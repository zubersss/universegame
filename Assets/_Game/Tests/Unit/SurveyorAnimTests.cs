using System.IO;
using Meridian.Art;
using Meridian.Player;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-032: clip choice by priority (the sheet-registry check moved to U-075, D-069).</summary>
    public class SurveyorAnimTests
    {
        static AnimInputs Still() => new AnimInputs { grounded = true, sinceHurt = 99f, sinceLand = 99f, sinceDig = 99f, sinceHitReact = 99f, sinceJump = 99f, sinceParryHit = 99f };

        [Test]
        public void PicksByPriority()
        {
            var a = Still();
            Assert.AreEqual(SurveyorAnim.Idle, SurveyorAnim.Pick(a));
            a.vx = 4f; Assert.AreEqual(SurveyorAnim.Walk, SurveyorAnim.Pick(a), "walk 4 m/s");
            a.vx = -6.5f; Assert.AreEqual(SurveyorAnim.Run, SurveyorAnim.Pick(a), "sprint 6.5 m/s (either way)");
            a.vx = 0f; a.usingRig = true; Assert.AreEqual(SurveyorAnim.Aim, SurveyorAnim.Pick(a), "standing with the rig in use");
            a.sinceLand = 0.1f; Assert.AreEqual(SurveyorAnim.Land, SurveyorAnim.Pick(a), "landing beats aim");
            a.grounded = false; a.vy = 3f; Assert.AreEqual(SurveyorAnim.Jump, SurveyorAnim.Pick(a), "rising");
            a.vy = -3f; Assert.AreEqual(SurveyorAnim.Fall, SurveyorAnim.Pick(a), "falling");
            a.sinceDig = 0.1f; Assert.AreEqual(SurveyorAnim.Dig, SurveyorAnim.Pick(a), "digging, even airborne");
            a.sinceHurt = 0.1f; Assert.AreEqual(SurveyorAnim.Hurt, SurveyorAnim.Pick(a), "hurt beats dig");
            a.dead = true; Assert.AreEqual(SurveyorAnim.Death, SurveyorAnim.Pick(a), "death beats everything");
        }

        // D-069 (P-30): RegistryHoldsTheSurveyorClipsFromBaseJson retired. base.json became the surveyor model's json (B-078);
        // its intent (clip names, count and lengths from the json) moves into U-075's Animator check.
    }
}
