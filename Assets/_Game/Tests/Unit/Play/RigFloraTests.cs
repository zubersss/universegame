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
    /// their phases differ; a plant reacts (turns to look, swaps its react part) within 3 m of the surveyor; the manager's
    /// loop stays under 1.0 ms for 300 plants. U-108 (contract v3.1, B-126 snoozle, D-101): a `replaces_part` slot swaps
    /// its bone's own renderer (no extra renderer), the idle swap cycle steps on the beat, and the react shows head_open
    /// plus leaves_up, then returns to the cycle and the resting leaves.
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
            // v3.1 (U-108): the react swap on its replaced slot's own renderer and every react.also part (the snoozle: head_open, leaves_up).
            foreach (var name in target.SlotNames)
                if (!string.IsNullOrEmpty(target.Def.react.swap) && System.Array.IndexOf(target.Def.swaps[name], target.Def.react.swap) >= 0)
                    Assert.AreEqual(target.Def.react.swap, target.SlotSpriteName(name), $"the react swap on the '{name}' bone's own renderer");
            foreach (var kv in target.Def.react.also) Assert.AreEqual(kv.Value, target.SlotSpriteName(kv.Key), $"react.also: '{kv.Key}' shows '{kv.Value}'");
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

        /// <summary>
        /// U-108 (v3.1, B-126): one snoozle from the live set, no scene. Its cycle slot replaces the head bone's part: the
        /// bone's own renderer carries a cycle state, with no extra renderer and no face renderers (D-101). Advancing
        /// FloraRigs.CycleClockOffset steps the head head_open → head_half → head_closed → head_half → head_open exactly on
        /// the beat boundaries (8, 1, 3, 1 beats at 110 bpm) and never between them. Within 3 m the head shows react.swap
        /// (head_open) and the leaves lift (react.also: leaves_up); away again, the head returns to the cycle's entry and
        /// the leaves to their resting part.
        /// </summary>
        [UnityTest]
        public IEnumerator AReplacedPartStepsItsCycleOnTheBeatAndReactsOnItsOwnRenderer()
        {
            var go = new GameObject("RigFloraCycleTest");
            var who = new GameObject("RigFloraCycleTestSurveyor").transform;
            try
            {
                who.position = new Vector3(100f, 0f, 0f); // far from the plant at the origin
                var rigs = go.AddComponent<FloraRigs>();
                rigs.player = who;
                rigs.Load("flora/earth/rigset");
                float timeout = Time.realtimeSinceStartup + 15f;
                while (!rigs.Ready && Time.realtimeSinceStartup < timeout) yield return null;
                Assert.IsTrue(rigs.Ready, $"flora/earth/rigset loaded: json {rigs.Set != null} (parse error: {rigs.ParseError ?? "none"}), parts {rigs.SpriteCount}, controller {rigs.Controller != null}; nothing found at: {rigs.Missing}");
                RigSet.Plant def = null;
                foreach (var candidate in rigs.Set.plants) if (candidate.Cycle != null) { def = candidate; break; }
                if (def == null) Assert.Ignore("the live rig set has no idle.swap_cycle plant (B-126 not imported): nothing to step");
                var cycle = def.Cycle;
                var slot = def.FindSlot(cycle.slot);
                Assert.NotNull(slot, $"the cycle slot '{cycle.slot}' is a slot of the plant");
                Assert.IsTrue(slot.replaces_part, "a v3.1 replaced part");
                int bone = def.BoneIndex(slot.bone);
                Assert.GreaterOrEqual(bone, 0, "on a bone of the plant");

                var plant = rigs.Spawn(def, Vector2.zero, 4242);
                Assert.NotNull(plant);
                // Substituted, not drawn twice: the slot drives the bone's own renderer; the bone has one renderer and no child named like the slot.
                Assert.AreSame(plant.Parts[bone], plant.SlotRenderer(cycle.slot), "the slot drives the bone's own SpriteRenderer");
                Assert.AreEqual(1, plant.Bones[bone].GetComponents<SpriteRenderer>().Length, "one renderer on the bone");
                Assert.IsNull(plant.Bones[bone].Find(cycle.slot), "no extra renderer object for the slot");
                if (!def.swaps.ContainsKey("eyes")) Assert.IsNull(plant.Eyes, "no face renderers (D-101)");
                if (!def.swaps.ContainsKey("mouth")) Assert.IsNull(plant.Mouth, "no face renderers (D-101)");
                Assert.AreEqual(cycle.sequence[0], def.bones[bone].part, "the bone's authored part is the cycle's first entry (head_open)");
                Assert.GreaterOrEqual(plant.CycleIndex, 0, "the cycle runs from the first frame");
                Assert.AreEqual(cycle.sequence[plant.CycleIndex], plant.SlotSpriteName(cycle.slot), "a cycle state from the first frame");

                // Step the cycle clock: to just past entry 0's start, then to just past every boundary, then the wrap. Half a
                // beat before each boundary nothing has changed: the cycle steps on the beat, not per frame.
                float beatSeconds = 60f / def.idle.beat_bpm;
                int total = cycle.TotalBeats;
                var starts = new float[cycle.sequence.Length];
                for (int k = 1; k < starts.Length; k++) starts[k] = starts[k - 1] + cycle.beats[k - 1];
                rigs.CycleClockOffset += (total - rigs.CycleBeats(plant) + 0.05f) * beatSeconds;
                yield return null;
                Assert.AreEqual(0, plant.CycleIndex, "entry 0 after the wrap");
                Assert.AreEqual(cycle.sequence[0], plant.SlotSpriteName(cycle.slot), "head_open");
                for (int k = 1; k <= cycle.sequence.Length; k++)
                {
                    int entry = k % cycle.sequence.Length;
                    float boundary = k < cycle.sequence.Length ? starts[k] : total;
                    rigs.CycleClockOffset += (boundary - 0.6f - rigs.CycleBeats(plant)) * beatSeconds;
                    yield return null;
                    Assert.AreEqual(cycle.sequence[k - 1], plant.SlotSpriteName(cycle.slot), $"still entry {k - 1} just before beat {boundary}");
                    rigs.CycleClockOffset += (boundary - rigs.CycleBeats(plant) + 0.05f) * beatSeconds;
                    yield return null;
                    Assert.AreEqual(entry, plant.CycleIndex, $"entry {entry} at beat {boundary}");
                    Assert.AreEqual(cycle.sequence[entry], plant.SlotSpriteName(cycle.slot), $"entry {entry} at beat {boundary}");
                }

                // React within 3 m (the surveyor on its right): react.swap on the head, every react.also part (leaves_up).
                // Park the cycle in an entry other than the react swap, held for two beats or more, so the swap is a visible change.
                int parked = -1;
                for (int k = 0; k < cycle.sequence.Length; k++) if (cycle.sequence[k] != def.react.swap && cycle.beats[k] >= 2) { parked = k; break; }
                Assert.GreaterOrEqual(parked, 0, "an entry other than react.swap held for at least two beats (head_closed)");
                rigs.CycleClockOffset += (Mathf.Repeat(starts[parked] - rigs.CycleBeats(plant), total) + 0.05f) * beatSeconds;
                yield return null;
                Assert.AreEqual(cycle.sequence[parked], plant.SlotSpriteName(cycle.slot), "parked (head_closed)");
                who.position = plant.Root.position + new Vector3(1.5f, 0.5f, 0f);
                yield return null;
                Assert.IsTrue(plant.Reacting, "within 3 m: reacting");
                Assert.AreEqual(1, plant.Facing, "turned to look (the surveyor is on its right)");
                Assert.AreEqual(def.react.swap, plant.SlotSpriteName(cycle.slot), "react.swap on the cycle slot's own renderer");
                Assert.Greater(def.react.also.Count, 0, "the v3.1 react also lifts something (leaves_up)");
                foreach (var kv in def.react.also) Assert.AreEqual(kv.Value, plant.SlotSpriteName(kv.Key), $"react.also: '{kv.Key}' shows '{kv.Value}'");
                // Away: the react holds ReactSeconds, then the head returns to the cycle's current entry and the leaves to their resting part.
                who.position = new Vector3(100f, 0f, 0f);
                yield return new WaitForSeconds(FloraRigs.ReactSeconds + 0.15f);
                Assert.IsFalse(plant.Reacting, "out of the radius: the react ended");
                Assert.AreEqual(cycle.sequence[plant.CycleIndex], plant.SlotSpriteName(cycle.slot), "back to the cycle's current entry");
                foreach (var kv in def.react.also)
                {
                    var alsoSlot = def.FindSlot(kv.Key);
                    Assert.NotNull(alsoSlot, kv.Key);
                    Assert.AreEqual(def.bones[def.BoneIndex(alsoSlot.bone)].part, plant.SlotSpriteName(kv.Key), $"'{kv.Key}' back to its bone's resting part");
                }
                TestContext.Out.WriteLine($"[MERIDIAN] {def.name}: cycle '{cycle.slot}' {string.Join(" -> ", cycle.sequence)} over {total} beats at {def.idle.beat_bpm} bpm on the bone's own renderer; react {def.react.swap} + {def.react.also.Count} also slot(s); Eyes/Mouth extra renderers: {plant.Eyes != null}/{plant.Mouth != null}");
                LogAssert.NoUnexpectedReceived();
            }
            finally { Object.Destroy(go); Object.Destroy(who.gameObject); }
        }
    }
}
