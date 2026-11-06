using System.Collections;
using Meridian.Core;
using Meridian.Player;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-094 (PlayMode) smoke_c0_earth: with the v4 path on, Earth's side view is an orthographic 16.875 m frame, the painted
    /// parallax layers sit where their factors say, the v3 surveyor sheet draws and walks on the 12 fps clock (or its
    /// 12 fps Animator), and the console stays clean.
    /// </summary>
    public class CartoonSmokeTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [TearDown]
        public void Off() => CartoonStage.Enabled = false;

        [UnityTest]
        public IEnumerator smoke_c0_earth()
        {
            CartoonStage.Enabled = true;
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            Assert.NotNull(side.cartoon, "CartoonStage on PlanetSide");
            Assert.IsTrue(side.cartoon.Active, "the v4 path is on for Earth");

            var cam = side.sideCamera;
            Assert.IsTrue(cam.orthographic, "orthographic side camera");
            Assert.AreEqual(SheetClock.FrameHeight * 0.5f, cam.orthographicSize, 0.01f, "16.875 m tall (1080 px at 64 px/m)");

            // Parallax: 3+ layers placed by their json factors (whole tile widths aside).
            var layers = side.cartoon.Layers;
            Assert.NotNull(layers);
            Assert.GreaterOrEqual(layers.renderers.Count, 3, "3–5 painted layers (placeholders count)");
            for (int i = 0; i < 30; i++) yield return null;
            var c = cam.transform.position;
            for (int i = 0; i < layers.renderers.Count; i++)
            {
                var l = layers.Layout.layers[i];
                var sr = layers.renderers[i];
                float w = sr.size.x / 3f;
                float expect = ParallaxMath.LayerX(c.x, l.parallax);
                float off = sr.transform.position.x - expect;
                float rem = w > 0f ? Mathf.Abs(off - Mathf.Round(off / w) * w) : Mathf.Abs(off);
                Assert.Less(rem, 0.01f, $"layer {l.n} x follows parallax {l.parallax}");
                Assert.AreEqual(ParallaxMath.LayerY(c.y, layers.datumY, l.y_m, l.parallax), sr.transform.position.y, 0.01f, $"layer {l.n} y");
            }

            // The surveyor draws from the v3 sheet and walks at 12 fps.
            var view = side.cartoon.Surveyor;
            Assert.NotNull(view, "SpriteCharacterView on the surveyor");
            timeout = Time.realtimeSinceStartup + 10f;
            while (!view.Ready && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(view.Ready, "characters/surveyor/side loaded (placeholder until B-111)");
            Assert.NotNull(view.Renderer.sprite, "a drawing on screen");
            var player = side.player;
            player.externalInput = true;
            player.intent = new PlayerIntent { move = 1f };
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(SurveyorAnim.Walk, view.Clip, "walking");
            if (view.UsesAnimator)
            {
                var info = view.Animator.GetCurrentAnimatorClipInfo(0);
                Assert.Greater(info.Length, 0);
                Assert.AreEqual(12f, info[0].clip.frameRate, "Animator sample rate 12 fps");
            }
            else
            {
                // Fallback stepping: the drawing changes every 1/12 s.
                int f0 = view.Frame;
                float t0 = Time.time;
                while (view.Frame == f0 && Time.time - t0 < 0.5f) yield return null;
                Assert.AreNotEqual(f0, view.Frame, "the walk advances");
                Assert.LessOrEqual(Time.time - t0, 1f / 12f + 0.1f, "within a 12 fps step");
            }
            player.intent = new PlayerIntent { move = -1f };
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            yield return null;
            Assert.IsTrue(view.Renderer.flipX, "facing left is a runtime flip");
            player.intent = default;
            LogAssert.NoUnexpectedReceived();
        }
    }
}
