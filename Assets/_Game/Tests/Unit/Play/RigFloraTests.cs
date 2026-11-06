using System.Collections;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Flora;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-097 (PlayMode, Earth): 300 rigged plants share one texture and one controller; at most 40 animate at full rate;
    /// their phases differ; a plant reacts (turns to look, swaps its face) within 3 m of the surveyor; the manager's loop
    /// stays under 1.0 ms for 300 plants.
    /// </summary>
    public class RigFloraTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const int Count = 300;

        [UnityTest]
        public IEnumerator ThreeHundredPlantsShareOneSheetAndOneControllerUnderTheCaps()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            var player = side.player;
            player.externalInput = true; player.intent = default;

            var go = new GameObject("RigFloraTest");
            var rigs = go.AddComponent<FloraRigs>();
            rigs.view = side.sideCamera; rigs.player = player.transform; rigs.terrain = side.terrain;
            rigs.Load("flora/earth/rigset");
            timeout = Time.realtimeSinceStartup + 15f;
            while (!rigs.Ready && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(rigs.Ready, $"flora/earth/rigset loaded: json {rigs.Set != null} (parse error: {rigs.ParseError ?? "none"}), parts {rigs.SpriteCount}, controller {rigs.Controller != null}; nothing found at: {rigs.Missing}");
            rigs.Populate(Count, 0.6f, player.Body.position.x, 12345); // ±90 m: inside the resident chunks
            Assert.AreEqual(Count, rigs.Plants.Count, "300 plants");

            // One texture, one controller.
            var textures = new HashSet<Texture>();
            var controllers = new HashSet<RuntimeAnimatorController>();
            int renderers = 0;
            foreach (var p in rigs.Plants)
            {
                controllers.Add(p.Animator.runtimeAnimatorController);
                foreach (var sr in p.Parts) if (sr != null) { textures.Add(sr.sprite.texture); renderers++; }
                if (p.Mouth != null) textures.Add(p.Mouth.sprite.texture);
                if (p.Eyes != null) textures.Add(p.Eyes.sprite.texture);
            }
            Assert.AreEqual(1, textures.Count, "every part sprite comes from the one rigset sheet");
            Assert.AreEqual(1, controllers.Count, "one AnimatorController for the set");
            Assert.Greater(renderers, Count, "parts drawn");

            // The cap: after a ranking pass, ≤ 40 at full rate, the rest cheap or still.
            yield return new WaitForSeconds(FloraRigs.RankEvery + 0.1f);
            int full = 0;
            foreach (var p in rigs.Plants) if (p.Animator.enabled) full++;
            Assert.LessOrEqual(full, FloraRigs.FullRateCap, "≤ 40 Animators at full rate");
            Assert.AreEqual(full, rigs.FullRateCount);
            Assert.Greater(rigs.CheapCount, 0, "a band of cheap idles behind them");

            // Phases differ among the full-rate plants.
            var phases = new HashSet<int>();
            foreach (var p in rigs.Plants)
                if (p.Animator.enabled) phases.Add(Mathf.FloorToInt((p.Animator.GetCurrentAnimatorStateInfo(0).normalizedTime % 1f) * 20f));
            Assert.GreaterOrEqual(phases.Count, 8, $"staggered starts (distinct twentieths among {full} full-rate plants)");

            // React within 3 m: walk the surveyor next to a plant.
            var target = rigs.Plants[Count / 2];
            var feet = new Vector2(target.Root.position.x + 1.5f, side.terrain.TopSolidY(Mathf.FloorToInt(target.Root.position.x + 1.5f)) + 1.05f);
            player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero;
            yield return null; yield return null;
            Assert.IsTrue(target.Reacting, "within 3 m: reacting");
            Assert.AreEqual(1, target.Facing, "turned to look (the surveyor is on its right)");
            if (target.Mouth != null && target.Def.swaps.ContainsKey("mouth")) Assert.AreEqual(target.Def.react.swap, target.Mouth.sprite.name, "the react face");
            var far = rigs.Plants[0];
            Assert.IsFalse(far.Reacting, "a plant 90 m away does not");

            // CPU: the manager's loop for 300 plants, p99 over 120 frames.
            var samples = new List<float>(120);
            for (int i = 0; i < 30; i++) yield return null;
            for (int i = 0; i < 120; i++) { yield return null; samples.Add(rigs.LastMs); }
            samples.Sort();
            float median = samples[samples.Count / 2], p99 = samples[Mathf.FloorToInt(samples.Count * 0.99f)];
            TestContext.Out.WriteLine($"[MERIDIAN] FloraRigs loop with {Count} plants: median {median:F3} ms, p99 {p99:F3} ms (full rate {rigs.FullRateCount}, cheap {rigs.CheapCount})");
            Assert.LessOrEqual(p99, 1.0f, "≤ 1.0 ms for 300 plants (the manager's loop; Animator evaluation of ≤ 40 plants is Unity's)");
            Object.Destroy(go);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
