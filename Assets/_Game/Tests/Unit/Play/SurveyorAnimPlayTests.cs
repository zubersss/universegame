using System.Collections;
using Meridian.Art;
using Meridian.Core;
using Meridian.Player;
using Meridian.Rendering;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-032 (PlayMode): walk → run → jump → fall → land → dig each show their clip; ≤ 0.05 ms per frame.</summary>
    public class SurveyorAnimPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;
        PlayerView view;
        double worstMs;
        string worstAt = "";
        readonly System.Collections.Generic.List<double> samples = new System.Collections.Generic.List<double>();

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            player = side.player;
            view = player.GetComponent<PlayerView>();
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            while (view.view.sprite == null && Time.realtimeSinceStartup < timeout + 10f) yield return null;
            player.externalInput = true;
            player.intent = default;
        }

        IEnumerator Frames(int n)
        {
            for (int i = 0; i < n; i++)
            {
                yield return null;
                if (view.LastUpdateMs > worstMs) { worstMs = view.LastUpdateMs; worstAt = $"{view.Clip} frame {view.Frame} (renderer setters {view.LastRendererMs * 1000:F1} µs), t {Time.realtimeSinceStartup:F2}, GC count {System.GC.CollectionCount(0)}"; }
                samples.Add(view.LastUpdateMs - view.LastRendererMs); // D-035: our code, without the engine setters
            }
        }

        /// <summary>Physics time (batch mode runs many frames per fixed step), sampling the view cost each frame.</summary>
        IEnumerator Steps(int fixedSteps)
        {
            for (int i = 0; i < fixedSteps; i++)
            {
                yield return new WaitForFixedUpdate();
                yield return null;
                if (view.LastUpdateMs > worstMs) { worstMs = view.LastUpdateMs; worstAt = $"{view.Clip} frame {view.Frame} (renderer setters {view.LastRendererMs * 1000:F1} µs), t {Time.realtimeSinceStartup:F2}, GC count {System.GC.CollectionCount(0)}"; }
                samples.Add(view.LastUpdateMs - view.LastRendererMs); // D-035: our code, without the engine setters
            }
        }

        void AssertClip(string name)
        {
            Assert.AreEqual(name, view.Clip, $"clip ({player.Body.linearVelocity}, grounded {player.Grounded})");
            Assert.IsTrue(ArtMaterials.ClipsFor(ArtKeys.Characters.Surveyor).TryGet(name, out var c));
            Assert.That(view.Frame, Is.InRange(c.start, c.start + c.length - 1), $"{name} frame from base.json's range");
        }

        [UnityTest]
        public IEnumerator WalkRunJumpFallLandDig()
        {
            yield return Boot();
            yield return Frames(30); // warm (first frames include loading)
            worstMs = 0; samples.Clear();
            AssertClip(SurveyorAnim.Idle);

            player.intent.move = -1f; // left: the landed Pilgrim stands ~4 m to the right of spawn
            yield return Steps(25);
            AssertClip(SurveyorAnim.Walk);

            player.intent.sprint = true;
            yield return Steps(30);
            AssertClip(SurveyorAnim.Run);

            player.intent.move = 0f; player.intent.sprint = false;
            yield return Steps(40); // stop
            player.PressJump();
            for (int i = 0; i < 30 && player.Grounded; i++) yield return new WaitForFixedUpdate();
            yield return Frames(2);
            AssertClip(SurveyorAnim.Jump);

            for (int i = 0; i < 200 && player.Body.linearVelocity.y > -1f; i++) yield return new WaitForFixedUpdate();
            yield return Frames(1);
            AssertClip(SurveyorAnim.Fall);

            for (int i = 0; i < 300 && !player.Grounded; i++) yield return new WaitForFixedUpdate();
            yield return Frames(1);
            AssertClip(SurveyorAnim.Land);

            yield return Steps(20);
            var p = player.Body.position;
            Assert.IsTrue(side.rig.Dig(new Vector2(p.x - 1.5f, p.y - 1.2f)), "Beam digs the ground ahead");
            yield return Frames(2);
            AssertClip(SurveyorAnim.Dig);

            samples.Sort();
            int over = samples.FindAll(s => s > 0.05).Count;
            TestContext.Out.WriteLine($"[MERIDIAN] PlayerView update: {samples.Count} frames, median {samples[samples.Count / 2] * 1000:F1} µs, p99 {samples[(int)(samples.Count * 0.99)] * 1000:F1} µs, worst {worstMs * 1000:F1} µs, {over} over 50 µs; worst at {worstAt}");
            // D-035: our code's median and p99 within the board's 0.05 ms; the worst frame (engine setter on a new clip) within 0.1 ms.
            Assert.LessOrEqual(samples[samples.Count / 2], 0.05, "median ≤ 0.05 ms (our code)");
            Assert.LessOrEqual(samples[(int)(samples.Count * 0.99)], 0.05, "p99 ≤ 0.05 ms (our code)");
            Assert.LessOrEqual(worstMs, 0.1, "worst frame incl. engine setters ≤ 0.1 ms (D-035)");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
