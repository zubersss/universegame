using System.IO;
using Meridian.Art;
using Meridian.Player;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-032: clip choice by priority, and the clip ranges come from base.json via the registry.</summary>
    public class SurveyorAnimTests
    {
        static AnimInputs Still() => new AnimInputs { grounded = true, sinceHurt = 99f, sinceLand = 99f, sinceDig = 99f };

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

        [Test]
        public void RegistryHoldsTheSurveyorClipsFromBaseJson()
        {
            var json = File.ReadAllText("Assets/_Game/Art/characters/surveyor/base.json");
            var sheet = JsonUtility.FromJson<Meridian.EditorTools.ArtImporter.SheetManifest>(json);
            var set = ArtMaterials.ClipsFor(ArtKeys.Characters.Surveyor);
            Assert.NotNull(set, "registry has the surveyor clips");
            Assert.AreEqual(sheet.fps, set.fps);
            Assert.AreEqual(sheet.animations.Length, set.clips.Count);
            foreach (var c in sheet.animations)
            {
                Assert.IsTrue(set.TryGet(c.name, out var r), c.name);
                Assert.AreEqual(c.start, r.start, c.name);
                Assert.AreEqual(c.length, r.length, c.name);
                Assert.AreEqual(c.loop, r.loop, c.name);
            }
            foreach (var name in new[] { SurveyorAnim.Idle, SurveyorAnim.Walk, SurveyorAnim.Run, SurveyorAnim.Jump, SurveyorAnim.Fall,
                                         SurveyorAnim.Land, SurveyorAnim.Dig, SurveyorAnim.Aim, SurveyorAnim.Hurt, SurveyorAnim.Death })
                Assert.IsTrue(set.TryGet(name, out _), $"base.json has '{name}'");
        }
    }
}
