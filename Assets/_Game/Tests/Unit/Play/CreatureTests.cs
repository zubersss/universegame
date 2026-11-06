using System.Collections;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Player;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-027 (PlayMode): stag flees within 8 m, wolf packs only at night, no creature falls through streamed chunks, AI ≤ 0.5 ms with 20.</summary>
    public class CreatureTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        CreatureDirector creatures;
        PlayerController player;

        IEnumerator BootEarth()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            creatures = side.creatures;
            Assert.NotNull(creatures, "CreatureDirector on PlanetSide");
            Assert.IsFalse(creatures.autoSpawn, "batch runs don't spawn on their own");
            player = side.player;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate(); // player settles
            var vitals = player.GetComponent<PlayerVitals>();
            vitals.maxHealth = vitals.health = 1e6f; // a hazard must not end the test (bumps never drain)
        }

        Vector2 OnSurface(float x, Species s)
        {
            int tx = Mathf.FloorToInt(x);
            int surface = side.terrain.TopSolidY(tx);
            return new Vector2(tx + 0.5f, surface + 1f + SpeciesSpec.Get(s).size.y * 0.5f + 0.05f);
        }

        [UnityTest]
        public IEnumerator StagFleesWithin8Metres()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.5f;
            float px = player.transform.position.x;
            var near = creatures.Spawn(Species.Stag, OnSurface(px + 7f, Species.Stag)); // tile-snapped: 6.5–7.5 m away
            var far = creatures.Spawn(Species.Stag, OnSurface(px - 10f, Species.Stag));
            // A chunk still being rebuilt holds its creatures (no thinking): start the clock once both are free.
            for (int i = 0; i < 300 && (near.Held || far.Held); i++) yield return new WaitForFixedUpdate();
            for (int i = 0; i < 40; i++) yield return new WaitForFixedUpdate();
            string where = $"near held {near.Held} at {Mathf.Abs(near.Body.position.x - player.Body.position.x):F1} m, far held {far.Held} at {Mathf.Abs(far.Body.position.x - player.Body.position.x):F1} m";
            Assert.AreEqual(CreatureState.Flee, near.State, "inside 8 m: flees (" + where + ")");
            Assert.AreNotEqual(CreatureState.Flee, far.State, "10 m: doesn't");
            float d0 = Mathf.Abs(near.Body.position.x - player.Body.position.x);
            Assert.Greater(near.Body.linearVelocity.x, 1f, "runs away (player is to its left)");
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            float d1 = Mathf.Abs(near.Body.position.x - player.Body.position.x);
            TestContext.Out.WriteLine($"[MERIDIAN] stag: {d0:F1} m → {d1:F1} m in 1.2 s");
            Assert.Greater(d1, d0 + 3f, "distance opens");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator WolfPacksSpawnOnlyAtNight()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.5f; // noon
            yield return null;
            for (int i = 0; i < 300; i++) creatures.SpawnTick();
            Assert.AreEqual(0, creatures.CountOf(Species.GreyWolf), "no wolves by day");
            Assert.Greater(creatures.CountOf(Species.Stag), 0, "stags by day (the spawner works)");
            creatures.DespawnAll();

            side.dayNight.Override = 0.0f; // midnight
            yield return null;
            for (int i = 0; i < 300 && creatures.CountOf(Species.GreyWolf) < 2; i++) creatures.SpawnTick();
            int wolves = creatures.CountOf(Species.GreyWolf);
            TestContext.Out.WriteLine($"[MERIDIAN] wolves at midnight: {wolves}");
            Assert.GreaterOrEqual(wolves, 2, "a pack at night");

            side.dayNight.Override = 0.5f; // dawn comes: off-screen wolves leave
            for (int i = 0; i < 10; i++) yield return null;
            foreach (var c in creatures.All)
                if (c.Alive && c.Spec.id == Species.GreyWolf)
                    Assert.Less(Mathf.Abs(c.Body.position.x - player.Body.position.x), 22f, "only on-screen wolves stay after dawn");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator CreaturesNeverFallThroughStreamedChunks()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.5f;
            float px = player.transform.position.x;
            var spawned = new List<Creature>();
            for (int i = 0; i < CreatureDirector.MaxCreatures; i++)
            {
                float x = px - 50f + i * 5f + (i % 2) * 0.3f;
                if (Mathf.Abs(x - px) < 10f) x += 20f; // keep them calm (outside flee range)
                var c = creatures.Spawn(Species.Stag, OnSurface(x, Species.Stag));
                Assert.NotNull(c);
                spawned.Add(c);
            }
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();

            // Send the streaming focus 300 m away: the creatures' chunks unload; then come back.
            var cam = side.sideCamera;
            cam.GetComponent<CameraFollow>().enabled = false;
            var home = cam.transform.position;
            cam.transform.position = home + new Vector3(300f, 0f, 0f);
            float until = Time.realtimeSinceStartup + 10f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            int held = 0;
            foreach (var c in spawned) if (c.Alive && c.Held) held++;
            Assert.Greater(held, 0, "creatures without loaded ground are held");

            cam.transform.position = home;
            yield return null;
            until = Time.realtimeSinceStartup + 10f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 120; i++) yield return new WaitForFixedUpdate();

            int checkedCount = 0;
            foreach (var c in spawned)
            {
                if (!c.Alive) continue;
                checkedCount++;
                Assert.IsFalse(c.Held, $"{c.name} released when its ground is back");
                var p = c.Body.position;
                int surface = side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(Mathf.FloorToInt(p.x)));
                float feet = p.y - c.Spec.size.y * 0.5f;
                Assert.GreaterOrEqual(feet, surface + 1f - 0.25f, $"{c.name} at x {p.x:F1} stands on the ground (feet {feet:F2}, surface top {surface + 1})");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] {checkedCount} creatures checked after the round trip, {held} were held while away");
            Assert.Greater(checkedCount, 10);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AiTakesAtMostHalfAMillisecondWith20Creatures()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.0f; // night: wolves hunt, stags flee
            float px = player.transform.position.x;
            for (int i = 0; i < CreatureDirector.MaxCreatures; i++)
            {
                var s = i % 2 == 0 ? Species.Stag : Species.GreyWolf;
                Assert.NotNull(creatures.Spawn(s, OnSurface(px - 18f + i * 1.9f, s)));
            }
            Assert.AreEqual(CreatureDirector.MaxCreatures, creatures.AliveCount);
            Assert.IsNull(creatures.Spawn(Species.Stag, OnSurface(px, Species.Stag)), "20 is the cap");
            for (int i = 0; i < 30; i++) yield return null; // warm
            var samples = new List<double>(300);
            for (int i = 0; i < 300; i++) { yield return null; samples.Add(creatures.LastAiMs); }
            samples.Sort();
            double avg = 0; foreach (var s in samples) avg += s; avg /= samples.Count;
            double p99 = samples[(int)(samples.Count * 0.99) - 1], max = samples[samples.Count - 1];
            double median = samples[samples.Count / 2];
            TestContext.Out.WriteLine($"[MERIDIAN] AI with 20 creatures: avg {avg:F3} ms, median {median:F3} ms, p99 {p99:F3} ms, max {max:F3} ms");
            // D-047 (extends D-035): the 0.5 ms budget (board U-027) holds for median and p99; one worst frame
            // up to 2× is logged, not failed (batch-load spikes outside our code).
            Assert.LessOrEqual(median, 0.5, "median ≤ 0.5 ms AI (U-027, D-047)");
            Assert.LessOrEqual(p99, 0.5, "p99 ≤ 0.5 ms AI (U-027, D-047)");
            Assert.LessOrEqual(max, 1.0, "worst frame ≤ 2 × 0.5 ms (D-047)");
            if (max > 0.5) TestContext.Out.WriteLine($"[MERIDIAN] AI worst frame {max:F3} ms over 0.5 ms: logged per D-047");
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>
        /// U-042: every species' lowest opaque point (the tight sprite mesh) sits within 2 px of the ground
        /// contact in its idle, walk and death frames; and a settled Earth creature's contact is the ground line.
        /// </summary>
        [UnityTest]
        public IEnumerator PawsOnTheGround()
        {
            yield return BootEarth();
            var report = new System.Text.StringBuilder();
            var fails = new List<string>();
            // Walkers only: fliers (U-055) use a centred pivot and never stand. The Cinderhulk's night sheet too.
            var keys = new List<string>();
            foreach (Species s in System.Enum.GetValues(typeof(Species)))
            {
                var sp0 = SpeciesSpec.Get(s);
                if (sp0.Flies) continue;
                keys.Add(sp0.artKey);
                if (sp0.nightArtKey != null) keys.Add(sp0.nightArtKey);
            }
            foreach (string key in keys)
            {
#if UNITY_EDITOR
                // D-070 (P-31): a model species (B-082) is checked on its model: the json's clips registered, feet on y 0.
                string glb = $"Assets/_Game/Art/{key}.glb";
                if (System.IO.File.Exists(glb))
                {
                    var mclips = Meridian.Rendering.ArtMaterials.ModelClipsFor(key);
                    Assert.NotNull(mclips, key + " model clips registered");
                    var mjson = JsonUtility.FromJson<ModelJson>(System.IO.File.ReadAllText($"Assets/_Game/Art/{key}.json"));
                    Assert.AreEqual(mjson.clips.Length, mclips.clips.Count, key + " clip count = json");
                    foreach (var mc in mjson.clips) Assert.IsTrue(mclips.TryGet(mc.name, out _), $"{key} clip '{mc.name}'");
                    var prefab = UnityEditor.AssetDatabase.LoadMainAssetAtPath(glb) as GameObject;
                    Assert.NotNull(prefab, glb);
                    var inst = Object.Instantiate(prefab);
                    inst.transform.position = Vector3.zero;
                    // The geometry's lowest point (SkinnedMeshRenderer.bounds is the importer's padded estimate, not the vertices).
                    float bottom = float.PositiveInfinity, padded = float.PositiveInfinity;
                    foreach (var smr in inst.GetComponentsInChildren<SkinnedMeshRenderer>())
                    {
                        padded = Mathf.Min(padded, smr.bounds.min.y);
                        var baked = new Mesh();
                        smr.BakeMesh(baked, true);
                        foreach (var v in baked.vertices) bottom = Mathf.Min(bottom, smr.transform.TransformPoint(v).y);
                        Object.Destroy(baked);
                    }
                    foreach (var mf in inst.GetComponentsInChildren<MeshFilter>())
                        if (mf.sharedMesh != null) foreach (var v in mf.sharedMesh.vertices) bottom = Mathf.Min(bottom, mf.transform.TransformPoint(v).y);
                    report.AppendLine($"{key} model: lowest vertex {bottom:F3} m (renderer bounds {padded:F3})");
                    if (Mathf.Abs(bottom) > 0.02f) fails.Add($"{key} model: feet at y {bottom:F3} (± 0.02)");
                    Object.Destroy(inst);
                    continue;
                }
#endif
                var h = UnityEngine.AddressableAssets.Addressables.LoadAssetAsync<IList<Sprite>>(key);
                yield return h;
                Assert.AreEqual(UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationStatus.Succeeded, h.Status, key);
                var byIndex = new Dictionary<int, Sprite>();
                foreach (var sp in h.Result)
                {
                    int us = sp.name.LastIndexOf('_');
                    if (us >= 0 && int.TryParse(sp.name.Substring(us + 1), out int idx)) byIndex[idx] = sp;
                }
                var clips = Meridian.Rendering.ArtMaterials.ClipsFor(key);
                Assert.NotNull(clips, key + " clips registered");
#if UNITY_EDITOR
                // The shipped sheet itself (the imported textures aren't CPU-readable and may be atlased).
                string png = $"Assets/_Game/Art/{key}_color.png";
                var spec = JsonUtility.FromJson<SheetSpec>(System.IO.File.ReadAllText($"Assets/_Game/Art/{key}.json"));
                var cpu = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
                Assert.IsTrue(cpu.LoadImage(System.IO.File.ReadAllBytes(png)), png);
                var pixels = cpu.GetPixels32();
                float pivotPx = spec.pivot[1] * spec.frame_height;
                foreach (var clip in clips.clips)
                {
                    if (clip.name != "idle" && clip.name != "walk" && clip.name != "death") continue;
                    for (int f = clip.start; f < clip.start + clip.length; f++)
                    {
                        Assert.IsTrue(byIndex.TryGetValue(f, out var sp), $"{key} frame {f}");
                        // The import keeps the sheet's pivot: the ground contact is pivotPx above the frame's bottom.
                        if (Mathf.Abs(sp.pivot.y - pivotPx) > 0.5f) fails.Add($"{key} frame {f}: imported pivot {sp.pivot.y:F1} px, sheet {pivotPx:F1} px");
                        int x0 = (f % spec.columns) * (spec.frame_width + spec.gutter);
                        int top = (f / spec.columns) * (spec.frame_height + spec.gutter);
                        int y0 = cpu.height - (top + spec.frame_height); // texture rows run bottom-up
                        int lowest = -1;
                        for (int y = 0; y < spec.frame_height && lowest < 0; y++)
                            for (int x = 0; x < spec.frame_width; x++)
                                if (pixels[(y0 + y) * cpu.width + x0 + x].a > 127) { lowest = y; break; }
                        float px = lowest - pivotPx; // lowest opaque row's bottom edge vs the ground contact
                        report.AppendLine($"{key} {clip.name} {f}: lowest opaque {px:F1} px from contact");
                        if (lowest < 0 || Mathf.Abs(px) > 2f) fails.Add($"{key} {clip.name} frame {f}: {px:F1} px");
                    }
                }
                Object.Destroy(cpu);
#endif
            }

            // Physics: an Earth creature at rest stands with its contact (the box bottom, the sprite pivot) on the ground line.
            side.dayNight.Override = 0.5f;
            float px0 = player.transform.position.x;
            foreach (var s in new[] { Species.Stag, Species.GreyWolf })
            {
                var c = creatures.Spawn(s, OnSurface(px0 + (s == Species.Stag ? -34f : -44f), s)); // west of the camp: no props underfoot
                for (int i = 0; i < 300 && c.Held; i++) yield return new WaitForFixedUpdate();
                for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
                // The box from the body itself (Collider2D.bounds can lag a frame behind a resized, re-pooled box).
                Vector2 b = c.Body.position + c.Box.offset;
                float boxBottom = b.y - c.Box.size.y * 0.5f, half = c.Box.size.x * 0.5f;
                float ground = Mathf.Max(side.terrain.TopSolidY(Mathf.FloorToInt(b.x - half + 0.01f)), side.terrain.TopSolidY(Mathf.FloorToInt(b.x + half - 0.01f))) + 1f;
                // D-070: a model species stands on its model's feet origin; wait for the model to load.
                for (int i = 0; i < 600 && c.Model != null && !c.Model.Ready; i++) yield return null;
                bool model = c.Model != null && c.Model.Ready;
                float contact = model ? c.Model.transform.position.y : c.View.transform.position.y;
                float twoPx = model ? 0.02f : 2f / c.View.sprite.pixelsPerUnit;
                report.AppendLine($"{s}: sprite contact {contact:F3}, box bottom {boxBottom:F3}, ground {ground:F3}; v {c.Body.linearVelocity}, state {c.State}");
                if (Mathf.Abs(boxBottom - contact) > twoPx) fails.Add($"{s}: sprite contact {contact:F3} vs box bottom {boxBottom:F3}");
                // Box2D keeps a contact skin of a few cm between resting colliders; anything near 0.5 m is the old sink.
                if (Mathf.Abs(ground - boxBottom) > 0.06f) fails.Add($"{s}: box bottom {boxBottom:F3} vs ground {ground:F3}");
            }
            TestContext.Out.WriteLine("[MERIDIAN] U-042\n" + report);
            Assert.IsEmpty(fails, "lowest opaque point within 2 px of the ground contact");
            LogAssert.NoUnexpectedReceived();
        }

        [System.Serializable]
        public sealed class SheetSpec { public int frame_width, frame_height, columns, gutter; public float[] pivot; }

        [System.Serializable] public sealed class ModelJson { public int fps; public ModelJsonClip[] clips; }
        [System.Serializable] public sealed class ModelJsonClip { public string name; public int frames; public bool loop; }
    }
}
