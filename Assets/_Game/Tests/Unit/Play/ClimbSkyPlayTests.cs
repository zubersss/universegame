using System.Collections;
using Meridian.Core;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-109 (PlayMode): the climb sky on the cartoon stage. Place() rides the climb without flying it: on the pad the frame is
    /// the painted sky to its top row, half-way up it darkens toward the top, on the Escape Line the frame top is space black
    /// with the B-120 starfield loaded, covering the frame at its full (low) alpha; +20 m (entry) is black too; nothing
    /// allocates per frame.
    /// </summary>
    public class ClimbSkyPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static void AssertColour(Color expect, Color got, string what)
        {
            Assert.AreEqual(expect.r, got.r, 2e-3f, what + " (r)");
            Assert.AreEqual(expect.g, got.g, 2e-3f, what + " (g)");
            Assert.AreEqual(expect.b, got.b, 2e-3f, what + " (b)");
        }

        [UnityTest, Timeout(180000)]
        public IEnumerator TheClimbSkyStaysPaintedOnThePadAndIsBlackWithStarsAtTheEscapeLine()
        {
            bool was = CartoonStage.Enabled;
            CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                Assert.IsTrue(director.IsReady, "Core booted");
                var side = director.PlanetSide;
                Assert.IsTrue(side.cartoon != null && side.cartoon.Active, "the cartoon stage is on for Earth");
                var sky = side.cartoon.Sky;
                Assert.NotNull(sky, "CartoonStage builds the ClimbSky");
                Assert.NotNull(sky.Gradient, "the gradient strip exists");
                Assert.NotNull(sky.Stars, "the star renderer exists");
                Assert.AreEqual(ParallaxLayers.BackOrder - 3, sky.Gradient.sortingOrder, "the flat gradient draws behind everything");
                Assert.NotNull(sky.Overlay, "the overlay strip exists");
                Assert.AreEqual(ParallaxLayers.BackOrder - 1, sky.Stars.sortingOrder, "the stars sit between the gradient and the painting");
                Assert.AreEqual(side.sideCamera.transform, sky.Gradient.transform.parent, "the gradient rides the side camera");
                Assert.AreEqual(side.Config.EscapeLineY, sky.escapeY, 1e-4f, "the Escape Line from PlanetConfig");
                Assert.AreEqual(sky.layers.anchorY, sky.anchorY, 1e-4f, "the same resting anchor as the layers");
                // Let the painted layer0 land (its top edge sets the geometry; a placeholder strip would end under the frame top).
                float until = Time.realtimeSinceStartup + 15f;
                while (sky.layers.placeholders.Count > 0 && sky.layers.placeholders[0] && Time.realtimeSinceStartup < until) yield return null;
                Assert.IsTrue(sky.layers.placeholders.Count > 0 && !sky.layers.placeholders[0], "backgrounds/earth/plains/layer0 loaded");
                yield return null;
                Assert.IsTrue(sky.Textured, "the overlay fades layer0's own painting into the sky (no flat join)");
                Assert.IsTrue(sky.Overlay.enabled, "the overlay is on once the art is in");
                Assert.AreEqual(ParallaxLayers.BackOrder + sky.layers.Layout.layers.Length, sky.Overlay.sortingOrder, "the overlay draws in front of every painted layer");
                Assert.Less(sky.Overlay.sortingOrder, 0, "and behind the terrain");
                Assert.IsTrue(sky.TopMeasured, "the edge colour is measured from layer0's top band");

                // On the pad: the camera at rest sees painted sky up to the frame top; every visible row of the gradient is the top colour.
                sky.Place(sky.anchorY);
                Assert.Greater(sky.Span, 1f, "a positive span");
                Assert.GreaterOrEqual(sky.EdgeY, sky.anchorY + side.sideCamera.orthographicSize - 0.01f, "layer0's top edge reaches the frame top at rest");
                AssertColour(sky.TopColour, sky.FrameTop, "frame top on the pad is the painted top row");
                AssertColour(sky.TopColour, sky.FrameBottom, "frame bottom on the pad");
                Assert.AreEqual(0f, sky.StarAlpha, 1e-5f, "no stars on the pad");
                Assert.IsFalse(sky.Stars.enabled, "stars hidden on the pad");
                Assert.IsTrue(sky.Gradient.enabled, "the gradient is on");

                // Half-way: darker at the frame top than at the bottom, still no stars (the first two thirds).
                float half = (sky.datumY + sky.escapeY) * 0.5f;
                sky.Place(half);
                Assert.Less(ClimbSkyMath.Luma(sky.FrameTop), ClimbSkyMath.Luma(sky.FrameBottom), "darker toward the top half-way up");
                Assert.Greater(ClimbSkyMath.Luma(sky.FrameTop), ClimbSkyMath.Luma(ClimbSkyMath.SpaceBlack), "not black yet half-way");
                Assert.AreEqual(0f, sky.StarAlpha, 1e-5f, "no stars half-way");
                Assert.IsTrue(sky.StarsRequested, "the starfield was requested at half the climb");

                // The Escape Line: black at the frame top, stars at their full alpha once the sheet is in.
                sky.Place(sky.escapeY);
                AssertColour(ClimbSkyMath.SpaceBlack, sky.FrameTop, "space black at the frame top on the Escape Line");
                Assert.AreEqual(ClimbSkyMath.MaxStarAlpha, sky.StarAlpha, 1e-5f, "stars at full alpha on the line");
                until = Time.realtimeSinceStartup + 20f;
                while (!sky.StarsReady && Time.realtimeSinceStartup < until) { sky.Place(sky.escapeY); yield return null; }
                Assert.IsTrue(sky.StarsReady, $"{ClimbSky.StarsKey} loaded for the climb");
                sky.Place(sky.escapeY);
                Assert.IsTrue(sky.Stars.enabled, "stars shown at the line");
                Assert.AreEqual(ClimbSkyMath.MaxStarAlpha, sky.Stars.color.a, 1e-5f, "sprite alpha = star alpha");
                Assert.AreEqual(SpriteDrawMode.Tiled, sky.Stars.drawMode);
                var b = sky.Stars.bounds;
                var c = side.sideCamera.transform.position;
                float halfH = side.sideCamera.orthographicSize, halfW = halfH * side.sideCamera.aspect;
                Assert.IsTrue(b.min.x <= c.x - halfW && b.max.x >= c.x + halfW, $"the star block covers the frame's width ({b.min.x:F1}–{b.max.x:F1} around {c.x:F1} ± {halfW:F1})");
                Assert.IsTrue(b.min.y <= sky.escapeY - halfH && b.max.y >= sky.escapeY + halfH, $"the star block covers the frame's height ({b.min.y:F1}–{b.max.y:F1} around {sky.escapeY:F1} ± {halfH:F1})");

                // Entry rides the same curves: above the line it is black and starry too.
                sky.Place(sky.escapeY + 20f);
                AssertColour(ClimbSkyMath.SpaceBlack, sky.FrameTop, "black above the line (entry)");
                Assert.AreEqual(ClimbSkyMath.MaxStarAlpha, sky.StarAlpha, 1e-5f);

                // Back on the pad the stars go away and the painting is back.
                sky.Place(sky.anchorY);
                Assert.IsFalse(sky.Stars.enabled, "stars hidden again on the ground");
                AssertColour(sky.TopColour, sky.FrameTop, "painted again on the ground");

                // No per-frame allocation (the row colours reuse their array; the tile block moves in place).
                sky.Place(half);
                long before = System.GC.GetAllocatedBytesForCurrentThread();
                for (int i = 0; i < 120; i++) sky.Place(half + i * 2f);
                long bytes = System.GC.GetAllocatedBytesForCurrentThread() - before;
                Assert.AreEqual(0, bytes, "Place allocates nothing");
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                CartoonStage.Enabled = was;
            }
        }
    }
}
