using System.IO;
using System.Linq;
using Meridian.Art;
using Meridian.Player;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-032: clip choice by priority (the sheet-registry check moved to U-075, D-069).</summary>
    public class SurveyorAnimTests
    {
        static AnimInputs Still() => new AnimInputs { grounded = true, sinceHurt = 99f, sinceLand = 99f, sinceDig = 99f, sinceBump = 99f, sinceJump = 99f, sinceBuild = 99f, sinceSurprise = 99f };

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
            a.dead = true; Assert.AreEqual(SurveyorAnim.ConkOut, SurveyorAnim.Pick(a), "conk out (Suit power 0) beats everything");
            Assert.AreEqual(SurveyorAnim.Death, SurveyorAnim.StandIn(SurveyorAnim.ConkOut), "conk_out stands in as the old death clip");
            a.dead = false; a.sinceBump = 0.1f; Assert.AreEqual(SurveyorAnim.Bump, SurveyorAnim.Pick(a), "a bump (U-093)");
            Assert.AreEqual(SurveyorAnim.Hurt, SurveyorAnim.StandIn(SurveyorAnim.Bump));
        }

        [Test]
        public void C1ClipsPickByPriority()
        {
            // U-105: the C1 triggers slot into the order: climb-in and surprise above dash; build with dig; jetpack while airborne.
            var a = Still();
            a.grounded = false; a.vy = -2f; a.jetpacking = true;
            Assert.AreEqual(SurveyorAnim.Jetpack, SurveyorAnim.Pick(a), "jetpack while airborne");
            a.jetpacking = false; a.grounded = true; a.vy = 0f;
            a.sinceBuild = 0.1f; Assert.AreEqual(SurveyorAnim.Build, SurveyorAnim.Pick(a), "the Builder placed a tile");
            a.sinceDig = 0.1f; Assert.AreEqual(SurveyorAnim.Build, SurveyorAnim.Pick(a), "build and dig together: build (the later action)");
            a.dashing = true; Assert.AreEqual(SurveyorAnim.Dash, SurveyorAnim.Pick(a), "a dash beats the tool clips");
            a.sinceSurprise = 0.1f; Assert.AreEqual(SurveyorAnim.Surprise, SurveyorAnim.Pick(a), "the eye-pop beats the dash");
            a.climbingIn = true; Assert.AreEqual(SurveyorAnim.ClimbIn, SurveyorAnim.Pick(a), "boarding beats surprise");
            a.sinceHurt = 0.1f; Assert.AreEqual(SurveyorAnim.Hurt, SurveyorAnim.Pick(a), "hurt still beats everything but conk out");
        }

        [Test]
        public void EveryClipResolvesOnTheLiveSurveyorSheet()
        {
            // U-105 Accept: each controller state resolves to a real clip or a named stand-in; the table below is the report.
            var path = "Assets/_Game/Art/characters/surveyor/side.json";
            Assert.IsTrue(File.Exists(path), "the live surveyor sheet sidecar");
            var sheet = JsonUtility.FromJson<Meridian.EditorTools.ArtImporter.SheetManifest>(File.ReadAllText(path));
            var real = new System.Collections.Generic.HashSet<string>();
            foreach (var c in sheet.animations) real.Add(c.name);
            Assert.IsTrue(real.Contains(SurveyorAnim.Idle) && real.Contains(SurveyorAnim.Walk) && real.Contains(SurveyorAnim.Jump), "the sheet's core clips");
            int standIns = 0;
            foreach (var clip in SurveyorAnim.AllClips)
            {
                var resolved = SurveyorAnim.ResolveOn(clip, real.Contains);
                Assert.IsTrue(real.Contains(resolved), $"{clip} -> {resolved} must be a drawing the sheet has");
                bool standIn = resolved != clip;
                if (standIn) standIns++;
                TestContext.Out.WriteLine($"[MERIDIAN] U-105 {clip} -> {resolved} ({(standIn ? "stand-in" : "real")})");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] U-105: {SurveyorAnim.AllClips.Length - standIns} real clips, {standIns} named stand-ins on {sheet.key} ({real.Count} drawings)");
            Assert.AreEqual(SurveyorAnim.LookCamera, SurveyorAnim.ResolveOn(SurveyorAnim.Surprise, real.Contains), "surprise stands in as look_camera until B-116's C1 clip");
            Assert.AreEqual(SurveyorAnim.Jump, SurveyorAnim.ResolveOn(SurveyorAnim.Jetpack, real.Contains));
        }

        [Test]
        public void TheSecondSheetCarriesTheFiveC1ClipsIntoTheOneController()
        {
            // U-115 (D-121): side.json + side_b.json (B-134's art, else the stand-in under Placeholders) cover dig, build, surprise,
            // jetpack and climb_in with no stand-in; the five share side's frame size, pivot and PPU; the side controller's states for
            // them bind side_b's drawings (the renderer swaps texture with the clip).
            var side = JsonUtility.FromJson<Meridian.EditorTools.ArtImporter.SheetManifest>(File.ReadAllText("Assets/_Game/Art/characters/surveyor/side.json"));
            string bArt = "Assets/_Game/Art/characters/surveyor/side_b.json", bPlaceholder = "Assets/_Game/Placeholders/characters/surveyor/side_b.json";
            string bPath = File.Exists(bArt) ? bArt : bPlaceholder;
            Assert.IsTrue(File.Exists(bPath), "a side_b sheet (B-134 or the stand-in)");
            var sideB = JsonUtility.FromJson<Meridian.EditorTools.ArtImporter.SheetManifest>(File.ReadAllText(bPath));
            Assert.IsTrue(sideB.IsV3 && sideB.IsSheet, "side_b is a v3 frame sheet");
            Assert.AreEqual(side.frame_width, sideB.frame_width); Assert.AreEqual(side.frame_height, sideB.frame_height);
            Assert.AreEqual(side.ppu, sideB.ppu, 1e-4f); CollectionAssert.AreEqual(side.pivot, sideB.pivot, "the same pivot");
            var names = new System.Collections.Generic.HashSet<string>(side.animations.Select(a => a.name));
            foreach (var c in sideB.animations) Assert.IsTrue(names.Add(c.name), $"'{c.name}' is drawn on one sheet only (D-121)");
            var five = new[] { SurveyorAnim.Dig, SurveyorAnim.Build, SurveyorAnim.Surprise, SurveyorAnim.Jetpack, SurveyorAnim.ClimbIn };
            foreach (var clip in five) Assert.AreEqual(clip, SurveyorAnim.ResolveOn(clip, names.Contains), $"{clip} is a real clip with side_b");
            int standIns = SurveyorAnim.AllClips.Count(clip => SurveyorAnim.ResolveOn(clip, names.Contains) != clip);
            TestContext.Out.WriteLine($"[MERIDIAN] U-115: {standIns} named stand-ins across side + side_b ({bPath})");
            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(Meridian.EditorTools.SheetAnimatorBuilder.ControllerPath(ArtKeys.Characters.SurveyorSide));
            Assert.NotNull(controller, "the side controller (SheetAnimatorBuilder)");
            var states = controller.layers[0].stateMachine.states;
            var binding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
            foreach (var clip in five)
            {
                var st = System.Array.Find(states, s => s.state.name == clip);
                Assert.NotNull(st.state, $"state '{clip}' on the side controller");
                var curve = AnimationUtility.GetObjectReferenceCurve((AnimationClip)st.state.motion, binding);
                Assert.IsTrue(curve != null && curve.Length > 0, $"{clip} has drawings");
                foreach (var k in curve)
                {
                    var sprite = k.value as Sprite;
                    Assert.NotNull(sprite, $"{clip}: every key holds a drawing");
                    StringAssert.StartsWith("side_b_", sprite.name, $"{clip} plays its own frames from side_b");
                }
            }
        }

        [Test]
        public void EventsFireOnTheRightFrames()
        {
            // U-105: the builder stamps the eye-pop on surprise's first drawing and the smear on dash's first and last.
            var dash = Meridian.EditorTools.SheetAnimatorBuilder.EventsFor("dash", 8);
            Assert.AreEqual(2, dash.Length);
            Assert.AreEqual(("OnSmear", 0), dash[0]);
            Assert.AreEqual(("OnSmearEnd", 7), dash[1]);
            var surprise = Meridian.EditorTools.SheetAnimatorBuilder.EventsFor("surprise", 6);
            Assert.AreEqual(1, surprise.Length);
            Assert.AreEqual(("OnEyePop", 0), surprise[0]);
            Assert.IsEmpty(Meridian.EditorTools.SheetAnimatorBuilder.EventsFor("walk", 12));
            Assert.IsEmpty(Meridian.EditorTools.SheetAnimatorBuilder.EventsFor("dash", 0));
            // The generated dash clip (the live sheet has dash) carries them at 12 Hz.
            var clip = UnityEditor.AssetDatabase.LoadAssetAtPath<AnimationClip>(Meridian.EditorTools.SheetAnimatorBuilder.ClipPath("characters/surveyor/side", "dash"));
            if (clip == null) Assert.Inconclusive("no generated dash clip yet: run SheetAnimatorBuilder.RebuildAll");
            var events = UnityEditor.AnimationUtility.GetAnimationEvents(clip);
            Assert.AreEqual(2, events.Length, "two events on the generated dash clip");
            Assert.AreEqual("OnSmear", events[0].functionName); Assert.AreEqual(0f, events[0].time, 1e-4f);
            Assert.AreEqual("OnSmearEnd", events[1].functionName);
            Assert.That(events[1].time, Is.EqualTo(((int)(clip.length * 12f + 0.5f) - 1) / 12f).Within(1e-3f), "the last drawing at 12 Hz");
        }

        // D-069 (P-30): RegistryHoldsTheSurveyorClipsFromBaseJson retired. base.json became the surveyor model's json (B-078);
        // its intent (clip names, count and lengths from the json) moves into U-075's Animator check.
    }
}
