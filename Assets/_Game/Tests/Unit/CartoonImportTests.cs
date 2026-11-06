using System.IO;
using System.Linq;
using Meridian.EditorTools;
using Meridian.View2D;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-094 (EditMode): ArtImporter v13 rules for v3 cartoon assets (contract v3.0 §11.8): a sheet over 2048, a clip over
    /// its cap and fps ≠ 12 are rejected, overlays must be 512²; the 12 fps sheet clock; parallax offsets follow the
    /// scene json factors; the surveyor placeholder sheet's generated Animator clips sample at 12 fps.
    /// </summary>
    public class CartoonImportTests
    {
        static readonly string[] Walk = { "walk" };

        [Test]
        public void ASheetOver2048IsRejected()
        {
            Assert.IsNull(ArtRules.ValidateV3Sheet(2048, 2048, 12, 10, new[] { "idle" }, new[] { 0 }, new[] { 10 }));
            StringAssert.Contains("over 2048", ArtRules.ValidateV3Sheet(2049, 1024, 12, 10, new[] { "idle" }, new[] { 0 }, new[] { 10 }));
            StringAssert.Contains("over 2048", ArtRules.ValidateV3Sheet(1024, 4096, 12, 10, new[] { "idle" }, new[] { 0 }, new[] { 10 }));
        }

        [Test]
        public void AClipOverItsCapIsRejected()
        {
            Assert.IsNull(ArtRules.ValidateV3Sheet(1024, 1024, 12, 16, Walk, new[] { 0 }, new[] { 16 }), "walk 16 is the cap");
            StringAssert.Contains("over its cap of 16", ArtRules.ValidateV3Sheet(1024, 1024, 12, 17, Walk, new[] { 0 }, new[] { 17 }));
            StringAssert.Contains("over its cap of 12", ArtRules.ValidateV3Sheet(1024, 1024, 12, 13, new[] { "idle" }, new[] { 0 }, new[] { 13 }));
            StringAssert.Contains("over its cap of 10", ArtRules.ValidateV3Sheet(1024, 1024, 12, 11, new[] { "jump" }, new[] { 0 }, new[] { 11 }));
            StringAssert.Contains("over its cap of 16", ArtRules.ValidateV3Sheet(1024, 1024, 12, 17, new[] { "look_camera" }, new[] { 0 }, new[] { 17 }), "one-off specials ≤ 16");
            StringAssert.Contains("outside the sheet", ArtRules.ValidateV3Sheet(1024, 1024, 12, 8, Walk, new[] { 0 }, new[] { 12 }));
        }

        [Test]
        public void AnFpsOtherThan12IsRejected()
        {
            StringAssert.Contains("fps 24", ArtRules.ValidateV3Sheet(1024, 1024, 24, 12, Walk, new[] { 0 }, new[] { 12 }));
            StringAssert.Contains("fps 8", ArtRules.ValidateV3Sheet(1024, 1024, 8, 12, Walk, new[] { 0 }, new[] { 12 }));
        }

        [Test]
        public void FilmOverlaysAre512SquareAndLayersHaveFourSegmentKeys()
        {
            Assert.IsNull(ArtRules.ValidateOverlay(512, 512));
            Assert.IsNotNull(ArtRules.ValidateOverlay(1024, 1024));
            Assert.IsNotNull(ArtRules.ValidateOverlay(512, 256));
            Assert.IsTrue(ArtRules.IsOverlayKey("fx/film/grain"));
            Assert.IsTrue(ArtRules.TryParse("backgrounds/earth/plains/layer0_color.png", out var key, out _), "4-segment layer key (contract §11.4)");
            Assert.AreEqual("backgrounds/earth/plains/layer0", key);
            Assert.AreEqual("backgrounds/earth/plains", ArtRules.SceneKeyOf(key));
            Assert.IsTrue(ArtRules.TryParse("ui/palettes/earth/strip_color.png", out _, out _), "palette strip");
            Assert.IsFalse(ArtRules.TryParse("props/earth/a/b_color.png", out _, out _), "other 4-segment keys stay rejected (contract §1)");
            Assert.AreEqual("backgrounds/earth/plains", ArtImporter.V3SceneKey("backgrounds/earth/plains/plains.json"));
            Assert.IsNull(ArtImporter.V3SceneKey("backgrounds/earth/plains/other.json"));
            Assert.IsNotNull(ArtRules.ValidateBackgroundLayer(2048, 1200), "layers ≤ 1024 high");
        }

        [Test]
        public void TheSheetClockStepsOnTwosAt12Fps()
        {
            Assert.AreEqual(0, SheetClock.Frame(0f, 12, true));
            Assert.AreEqual(0, SheetClock.Frame(1f / 12f - 0.001f, 12, true), "a drawing holds for 1/12 s");
            Assert.AreEqual(1, SheetClock.Frame(1f / 12f, 12, true));
            Assert.AreEqual(0, SheetClock.Frame(1f, 12, true), "a 12-frame loop is one second");
            Assert.AreEqual(7, SheetClock.Frame(5f, 8, false), "a one-off holds its last drawing");
            Assert.AreEqual(3, SheetClock.Frame(9f / 12f, 8, true, 2), "loop_from 2: steps 8,9 → drawings 2,3");
            Assert.AreEqual(16.875f, SheetClock.FrameHeight, 1e-4f, "1080 px at 64 px/m");
        }

        [Test]
        public void ParallaxOffsetsMatchTheJsonFactors()
        {
            var layout = SceneLayout.Parse("{\"layers\": [{\"n\": 0, \"parallax\": 0.1, \"y_m\": 4.0}, {\"n\": 1, \"parallax\": 0.4, \"y_m\": 2.0}, {\"n\": 2, \"parallax\": 0.8, \"y_m\": 0.0}]}");
            Assert.AreEqual(3, layout.layers.Length);
            foreach (var l in layout.layers)
            {
                // The camera moves 10 m: the layer moves (1 − parallax) × 10 with it, so it scrolls parallax × 10 on screen.
                float a = ParallaxMath.LayerX(100f, l.parallax), b = ParallaxMath.LayerX(110f, l.parallax);
                Assert.AreEqual(10f * (1f - l.parallax), b - a, 1e-4f, $"layer {l.n} world shift");
                Assert.AreEqual(10f * l.parallax, (110f - b) - (100f - a), 1e-4f, $"layer {l.n} screen scroll = its factor");
                Assert.AreEqual(320f + l.y_m, ParallaxMath.LayerY(320f, 320f, l.y_m, l.parallax), 1e-4f, "on the datum + y_m when the camera looks at the datum");
            }
            Assert.AreEqual(3, SceneLayout.Parse("not json").layers.Length, "bad json → the default 3 layers");
        }

        [Test]
        public void TheSurveyorPlaceholderWalksAt12Fps()
        {
            const string key = "characters/surveyor/side";
            var color = ArtImporter.PlaceholderColorPath(key);
            Assert.IsTrue(File.Exists(color), "v3 placeholder sheet at the contract key");
            var sheet = ArtImporter.SheetFor(color, key);
            Assert.NotNull(sheet);
            Assert.IsTrue(sheet.IsV3 && sheet.IsSheet);
            Assert.IsNull(ArtImporter.V3Reason(key, sheet, 1956, 1564), "the placeholder passes v13");
            var ti = (TextureImporter)AssetImporter.GetAtPath(color);
            Assert.AreEqual(64f, ti.spritePixelsPerUnit, "PPU from the json");
            Assert.IsFalse(ti.mipmapEnabled, "no mips");
            var controller = SheetAnimatorBuilder.BuildIfV3(color, key);
            Assert.NotNull(controller, "controller built");
            var walk = controller.animationClips.FirstOrDefault(c => c.name == "walk");
            Assert.NotNull(walk, "walk clip");
            Assert.AreEqual(12f, walk.frameRate, "Animator sample rate 12 fps");
            Assert.AreEqual(1f, walk.length, 1e-3f, "12 drawings at 12 fps = 1 s");
            var binding = AnimationUtility.GetObjectReferenceCurveBindings(walk).Single();
            var keys = AnimationUtility.GetObjectReferenceCurve(walk, binding);
            Assert.AreEqual(12, keys.Length, "one key per drawing");
            for (int i = 1; i < keys.Length; i++) Assert.AreEqual(1f / 12f, keys[i].time - keys[i - 1].time, 1e-4f, "on twos");
            Assert.IsTrue(keys.All(k => k.value is Sprite), "every key is a sheet sprite");
            Assert.IsTrue(AnimationUtility.GetAnimationClipSettings(walk).loopTime, "walk loops");
            Assert.AreEqual("idle", controller.layers[0].stateMachine.defaultState.name);
        }
    }
}
