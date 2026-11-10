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
    /// <summary>
    /// U-027 (PlayMode): stag flees within 8 m, wolf packs only at night, no creature falls through streamed chunks, AI ≤ 0.5 ms with 20.
    /// U-108 (B-127): the gull plays its `fly` clip while airborne and leaves it on the ground.
    /// </summary>
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
            // Open ground 40 m west of the camp: the camp's props, pad and ship (U-035/U-076) block a running stag on both flanks.
            int ptx = Mathf.FloorToInt(player.Body.position.x) - 40;
            var open = new Vector2(ptx + 0.5f, side.terrain.TopSolidY(ptx) + 1.05f);
            player.Body.position = open; player.transform.position = open; player.Body.linearVelocity = Vector2.zero;
            yield return null;
            float settle = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < settle) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
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
            int ntx = Mathf.FloorToInt(near.Body.position.x), nty = Mathf.FloorToInt(near.Body.position.y - near.Spec.size.y * 0.5f - 0.1f);
            Assert.Greater(near.Body.linearVelocity.x, 1f, $"runs away (player is to its left; held {near.Held}, simulated {near.Body.simulated}, state {near.State}, at {near.Body.position}, ready {side.terrain.IsCollisionReady(ntx, nty)}/{side.terrain.IsCollisionReady(ntx, nty - 2)}, settled {side.terrain.IsSettled})");
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            float d1 = Mathf.Abs(near.Body.position.x - player.Body.position.x);
            TestContext.Out.WriteLine($"[MERIDIAN] stag: {d0:F1} m → {d1:F1} m in 1.2 s");
            Assert.Greater(d1, d0 + 3f, "distance opens");
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>U-205 (BLENDER's 0.6.2 read, G11: two bears on one spot in smoke_33): the spawner leaves a body and a half (3 m at
        /// least) between a new creature and the living ones of its kind, and a pack's members stand 1.3 bodies apart in whole tiles.</summary>
        [UnityTest]
        public IEnumerator TheSpawnerKeepsItsKindApart()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.5f;
            yield return null;
            var bear = SpeciesSpec.Get(Species.BrownBear);
            Assert.AreEqual(3.15f, CreatureDirector.SpawnGap(bear), 1e-4f, "a bear (2.1 m): a body and a half");
            Assert.AreEqual(3, CreatureDirector.PackStepTiles(bear), "a bear's pack-mate: 3 tiles on (1.3 bodies, whole tiles)");
            Assert.AreEqual(3f, CreatureDirector.SpawnGap(SpeciesSpec.Get(Species.Gull)), 1e-4f, "a small body: 3 m");
            Assert.AreEqual(2, CreatureDirector.PackStepTiles(SpeciesSpec.Get(Species.Gull)), "2 tiles at least");

            // a bear stands where the spawner would put another: none is placed within the gap, to either side of it
            creatures.DespawnAll();
            float px = player.transform.position.x;
            var first = creatures.Spawn(Species.BrownBear, OnSurface(px - 30f, Species.BrownBear));
            Assert.NotNull(first);
            float bx = first.Body.position.x;
            foreach (float dx in new[] { 0f, 1f, -2f, 3f })
                Assert.AreEqual(0, creatures.SpawnPack(bear, bx + dx, player.Body.position.y, 1), $"no bear {dx:0} m from a bear");
            Assert.AreEqual(1, creatures.CountOf(Species.BrownBear));
            creatures.DespawnAll();

            // the natural spawner by day: no two of a kind stand closer than a pack's step or the gap
            for (int i = 0; i < 300; i++) creatures.SpawnTick();
            int alive = 0, pairs = 0;
            float closest = float.MaxValue; string who = "";
            foreach (var a in creatures.All)
            {
                if (!a.Alive) continue;
                alive++;
                foreach (var b in creatures.All)
                {
                    if (!b.Alive || ReferenceEquals(a, b) || a.Spec.id != b.Spec.id) continue;
                    pairs++;
                    float d = Mathf.Abs(a.Body.position.x - b.Body.position.x);
                    float least = Mathf.Min(CreatureDirector.PackStepTiles(a.Spec), CreatureDirector.SpawnGap(a.Spec));
                    if (d - least < closest) { closest = d - least; who = $"{a.Spec.id} {d:0.0} m apart (least {least:0.0})"; }
                    Assert.GreaterOrEqual(d, least - 1e-3f, $"two {a.Spec.id} {d:0.00} m apart");
                }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u205 spawn spacing: {alive} alive after 300 ticks, {pairs / 2} pairs of a kind, the tightest: {who}");
            Assert.Greater(alive, 0, "the spawner works");
            creatures.DespawnAll();
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
                    Assert.LessOrEqual(Mathf.Abs(c.Body.position.x - player.Body.position.x), 22f, "only on-screen wolves stay after dawn (the director leaves beyond 22 m)");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator CreaturesNeverFallThroughStreamedChunks()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.5f;
            creatures.autoSpawn = false; creatures.DespawnAll(); // D-132: the cartoon path's own spawns (gulls) must not take the pool's slots
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
            // U-169 (as BudgetGate / StageLayer): the camera travels alone and streams the camp out under the surveyor; hold it meanwhile.
            bool playerSim = player.Body.simulated;
            player.Body.simulated = false;
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
            yield return new WaitForFixedUpdate();
            player.Body.simulated = playerSim; // the camp is back under it
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
            creatures.autoSpawn = false; creatures.DespawnAll(); // D-132: an empty pool for the 20-creature count
            float px = player.transform.position.x;
            for (int i = 0; i < CreatureDirector.MaxCreatures; i++)
            {
                var s = i % 2 == 0 ? Species.Stag : Species.GreyWolf;
                Assert.NotNull(creatures.Spawn(s, OnSurface(px - 18f + i * 1.9f, s)));
            }
            Assert.AreEqual(CreatureDirector.MaxCreatures, creatures.AliveCount);
            Assert.IsNull(creatures.Spawn(Species.Stag, OnSurface(px, Species.Stag)), "20 is the cap");
            yield return MeasureAi(creatures, "20 creatures");
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>D-193 (LEAD 20:1x, on the diagnostic below: the one frame over 1 ms was the 56th after a 30-frame warm-up, in the first
        /// run of a process only, with no allocation and no collection in it): the AI's budget read over steady frames. A warm-up of
        /// AiWarmFrames after the spawn, whose own worst frame is logged and held to 2.0 ms (a real first-time hitch cannot hide there);
        /// then AiMeasuredFrames with D-047's limits unchanged (median and p99 ≤ 0.5 ms, worst ≤ 1.0 ms), the average ≤ 0.5 ms, and two
        /// new asserts: the AI allocates 0 B in every frame and no collection runs inside an AI frame. CreatureTests and
        /// InnerCreatureTests both measure through here.</summary>
        public const int AiWarmFrames = 150, AiMeasuredFrames = 300;
        public static IEnumerator MeasureAi(CreatureDirector director, string label)
        {
            double warmWorst = 0; int warmWorstAt = -1;
            for (int i = 0; i < AiWarmFrames; i++)
            {
                yield return null;
                if (director.LastAiMs > warmWorst) { warmWorst = director.LastAiMs; warmWorstAt = i; }
            }
            var samples = new List<double>(AiMeasuredFrames);
            double avg = 0; long bytes = 0; int allocFrames = 0, collections = 0;
            for (int i = 0; i < AiMeasuredFrames; i++)
            {
                yield return null;
                samples.Add(director.LastAiMs); avg += director.LastAiMs;
                if (director.LastAiAllocBytes > 0) { allocFrames++; bytes += director.LastAiAllocBytes; }
                collections += director.LastAiCollections;
            }
            avg /= AiMeasuredFrames;
            samples.Sort();
            double median = samples[samples.Count / 2], p99 = samples[(int)(samples.Count * 0.99) - 1], max = samples[samples.Count - 1];
            TestContext.Out.WriteLine($"[MERIDIAN] AI with {label}: steady avg {avg:F3} ms, median {median:F3}, p99 {p99:F3}, worst {max:F3} over {AiMeasuredFrames} frames; the warm-up's worst {warmWorst:F3} ms at frame {warmWorstAt} of {AiWarmFrames}; the AI allocated {bytes} B in {allocFrames} frame(s), {collections} collection(s) inside AI frames; spike note: {(string.IsNullOrEmpty(director.LastSpikeNote) ? "none" : director.LastSpikeNote)}");
            Assert.LessOrEqual(warmWorst, 2.0, $"the warm-up's worst frame ≤ 2.0 ms (D-193): frame {warmWorstAt}");
            Assert.LessOrEqual(avg, 0.5, "average ≤ 0.5 ms AI (D-193)");
            Assert.LessOrEqual(median, 0.5, "median ≤ 0.5 ms AI (U-027, D-047)");
            Assert.LessOrEqual(p99, 0.5, "p99 ≤ 0.5 ms AI (U-027, D-047)");
            Assert.LessOrEqual(max, 1.0, "worst steady frame ≤ 2 × 0.5 ms (D-047, D-193)");
            Assert.AreEqual(0, allocFrames, $"the AI allocates 0 B a frame (D-193): {bytes} B over {allocFrames} frame(s)");
            Assert.AreEqual(0, collections, "no collection inside an AI frame (D-193)");
        }

        /// <summary>
        /// LEAD 19:5x: the diagnostic for the AI worst-frame row (D-047's 1 ms bound read 1.68, 1.31, 1.000, 1.131 and a solo 1.014 over two
        /// days). Six runs of the same 300 frames in one process: every frame's AI time, what the AI allocated and whether a gen-0
        /// collection ran inside it; for each run the worst frame's index, the three worst frames with their collections and bytes,
        /// and avg / p99 / worst. Its reading at 20:09 (the one frame over 1 ms: frame 56 of the first run only, 0 B, no collection)
        /// became D-193; the on / off switch it had for U-204 F17's two lines measured them free and is gone (LEAD: a diagnostic's
        /// tool does not ship). Asserts nothing about time; runs only when MERIDIAN_AI_DIAG is set.
        /// </summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator AiWorstFrameDiagnostic()
        {
            if (string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("MERIDIAN_AI_DIAG"))) Assert.Ignore("Set MERIDIAN_AI_DIAG to run the AI worst-frame diagnostic.");
            yield return BootEarth();
            side.dayNight.Override = 0.0f;
            creatures.autoSpawn = false; creatures.DespawnAll();
            float px = player.transform.position.x;
            for (int i = 0; i < CreatureDirector.MaxCreatures; i++)
            {
                var s = i % 2 == 0 ? Species.Stag : Species.GreyWolf;
                Assert.NotNull(creatures.Spawn(s, OnSurface(px - 18f + i * 1.9f, s)));
            }
            for (int i = 0; i < 30; i++) yield return null; // warm, as the gate's test
            const int Frames = 300;
            var ms = new double[Frames]; var bytes = new long[Frames]; var gcs = new int[Frames]; var order = new int[Frames];
            {
                for (int run = 0; run < 6; run++)
                {
                    for (int i = 0; i < Frames; i++)
                    {
                        yield return null;
                        ms[i] = creatures.LastAiMs; bytes[i] = creatures.LastAiAllocBytes; gcs[i] = creatures.LastAiCollections; order[i] = i;
                    }
                    System.Array.Sort(order, (a, b) => ms[b].CompareTo(ms[a])); // worst first
                    double avg = 0; long allocated = 0; int collections = 0, frameAllocs = 0;
                    for (int i = 0; i < Frames; i++) { avg += ms[i]; allocated += bytes[i]; collections += gcs[i]; if (bytes[i] > 0) frameAllocs++; }
                    avg /= Frames;
                    double p99 = ms[order[Frames / 100]];
                    string worst3 = "";
                    for (int k = 0; k < 3; k++) worst3 += $"{(k > 0 ? "; " : "")}frame {order[k]}: {ms[order[k]]:F3} ms, {bytes[order[k]]} B, {gcs[order[k]]} gen-0 collection(s)";
                    TestContext.Out.WriteLine($"[MERIDIAN] AI diag run {run + 1}: avg {avg:F3} ms, p99 {p99:F3}, worst {ms[order[0]]:F3} at frame {order[0]} of {Frames}; the three worst: {worst3}; over the run {allocated} B allocated by the AI in {frameAllocs} frame(s), {collections} gen-0 collection(s) inside AI frames");
                }
            }
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
                // D-120 (P-31): a model species (B-082's glb) is listed as skipped until its C2 sheet lands (stag and wolf with B-132,
                // D-119); the sheet species below are the judged ones.
                string glb = $"Assets/_Game/Art/{key}.glb";
                if (System.IO.File.Exists(glb))
                {
                    report.AppendLine($"{key}: model species, skipped until its C2 sheet replaces the glb (D-119 / D-120)");
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
                // D-070: a model species stands on its model's feet origin; wait for the model to load, then read the box and the contact on
                // the same frame (a wandering stag walks on while the model loads: read apart, they parted by its climb).
                for (int i = 0; i < 600 && c.Model != null && !c.Model.Ready; i++) yield return null;
                yield return new WaitForFixedUpdate();
                // The box from the body itself (Collider2D.bounds can lag a frame behind a resized, re-pooled box).
                Vector2 b = c.Body.position + c.Box.offset;
                float boxBottom = b.y - c.Box.size.y * 0.5f - c.Box.edgeRadius, half = c.Box.size.x * 0.5f + c.Box.edgeRadius; // U-156: rounded corners
                // The ground line: the drawn surface's highest point under the box (D-161, as FootingTests: on the smooth ground the tile grid
                // stands up to 0.75 m over a slope's outline; an upright box rests on the high side of the slope).
                float ground = Mathf.Max(side.terrain.SurfaceAt(b.x - half), Mathf.Max(side.terrain.SurfaceAt(b.x), side.terrain.SurfaceAt(b.x + half)));
                bool model = c.Model != null && c.Model.Ready;
                // The body's own pose, not the interpolated transform's (the box above is the body's).
                float contact = (model ? c.Model.transform.position.y : c.View.transform.position.y) + (c.Body.position.y - c.transform.position.y);
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

        /// <summary>
        /// U-108 (B-127): the gull's v3 sheet carries a `fly` clip (frames 40–51, loop); a gull off the ground plays it once the
        /// FlyAfter hysteresis passes, and a gull whose feet touch the ground leaves it within a few frames (LandAfter) for idle/walk.
        /// The hysteresis itself is proved two ways a raw `Airborne = !grounded` would fail: lift-off reads at least FlyAfter of game
        /// time after the spawn (the director ticks in Update with Time.deltaTime, so the ticks' dt sum to Time.time's advance), and
        /// once the clip has switched it never switches back within its phase (no frame off fly aloft, none back on fly once landed).
        /// The gull is held on the ground by position each frame: the director steers a flier back into its hover band at 12 m/s².
        /// </summary>
        [UnityTest]
        public IEnumerator GullFliesWhileAirborne()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.5f; // noon: the gull is a Day species (never despawned by the dawn rule)
            // Frames and clips are captured at spawn (CreatureDirector.Spawn): without the sheet the gull keeps the placeholder and never animates.
            float timeout = Time.realtimeSinceStartup + 20f;
            while (!creatures.ArtReady(Species.Gull) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(creatures.ArtReady(Species.Gull), "the gull sheet (creatures/earth/gull, B-127) loads");
            // West of the camp (no props underfoot, as PawsOnTheGround) and outside the 6 m flee range.
            var feet = OnSurface(player.transform.position.x - 34f, Species.Gull);
            var aloft = feet + new Vector2(0f, 3.5f); // inside the 2–5 m hover band: the director keeps it there
            yield return null; // spawn in the frame phase, after this frame's director tick: the gull's first tick is next frame's, and t0 is its frame time
            var gull = creatures.Spawn(Species.Gull, aloft);
            Assert.NotNull(gull, "a gull");
            float t0 = Time.time;
            Assert.IsFalse(gull.Airborne, "a spawn starts grounded (Setup resets the hysteresis); Airborne flips only after FlyAfter of ticks");

            // Lift-off: the first physics frame that shows fly, the game time it took, and whether the clip ever left fly again.
            int flewAfter = -1, flicker = 0;
            float flewAt = float.NaN;
            for (int i = 0; i < 60; i++)
            {
                yield return new WaitForFixedUpdate();
                if (gull.CurrentClip == Creature.FlyClip) { if (flewAfter < 0) { flewAfter = i + 1; flewAt = Time.time; } }
                else if (flewAfter > 0) flicker++;
            }
            int frameAir = FrameIndex(gull.View.sprite);
            TestContext.Out.WriteLine($"[MERIDIAN] gull aloft: fly after {flewAfter} physics frames ({flewAt - t0:F3} s of game time), {flicker} frames off fly since; now clip {gull.CurrentClip}, pick {gull.LastPick}, sprite {gull.View.sprite.name}, airborne {gull.Airborne}, at {gull.Body.position} (feet {feet}), v {gull.Body.linearVelocity}, state {gull.State}");
            Assert.Greater(flewAfter, 0, "an airborne gull takes the fly clip within 60 physics frames");
            // Hysteresis: Airborne needs FlyAfter of ticks without contact. The ticks' dt sum to Time.time's advance since the spawn
            // frame, and a fixed step's Time.time trails the frame it belongs to by at most two steps (the catch-up loop), so the first
            // fly frame reads at least FlyAfter − 2·fixedDeltaTime after t0 at any frame rate. A raw `Airborne = !grounded` flips at
            // the first tick and shows fly within one frame plus two steps (~0.06 s at 60 fps): under this bound whenever a frame
            // is shorter than FlyAfter (a frame longer than FlyAfter lifts off in one tick by design).
            Assert.GreaterOrEqual(flewAt - t0, Creature.FlyAfter - 2f * Time.fixedDeltaTime, $"lift-off waits FlyAfter ({Creature.FlyAfter} s) of ticks without ground contact (hysteresis), not the first tick");
            Assert.AreEqual(0, flicker, "once airborne the fly clip holds (hysteresis: no flicker aloft)");
            Assert.IsTrue(gull.Airborne, "off the ground after FlyAfter");
            Assert.AreEqual(Creature.FlyClip, gull.CurrentClip, "an airborne gull plays fly");
            Assert.IsTrue(frameAir >= 40 && frameAir <= 51, $"a fly frame (gull_40..gull_51), drew {gull.View.sprite.name}");

            // Land it: feet on the ground, pinned there each frame. Once it has left fly it must stay off it (no flicker on the ground).
            int landedAfter = -1;
            flicker = 0;
            for (int i = 0; i < 20; i++)
            {
                gull.Body.position = feet; gull.transform.position = feet; gull.Body.linearVelocity = Vector2.zero;
                yield return new WaitForFixedUpdate();
                if (gull.CurrentClip != Creature.FlyClip) { if (landedAfter < 0) landedAfter = i + 1; }
                else if (landedAfter > 0) flicker++;
            }
            int frameGround = FrameIndex(gull.View.sprite);
            TestContext.Out.WriteLine($"[MERIDIAN] gull landed: left fly after {landedAfter} physics frames, {flicker} frames back on fly since; now clip {gull.CurrentClip}, pick {gull.LastPick}, sprite {gull.View.sprite.name}, airborne {gull.Airborne}, at {gull.Body.position}, v {gull.Body.linearVelocity}");
            Assert.Greater(landedAfter, 0, "a landed gull leaves the fly clip within 20 physics frames");
            Assert.AreEqual(0, flicker, "once landed the fly clip never returns (hysteresis: no flicker on the ground)");
            Assert.IsFalse(gull.Airborne, "on the ground after LandAfter");
            Assert.AreNotEqual(Creature.FlyClip, gull.CurrentClip, "a landed gull does not play fly");
            Assert.IsTrue(frameGround >= 0 && frameGround < 40, $"an idle/walk frame (gull_0..gull_21) on the ground, drew {gull.View.sprite.name}");
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>The frame a sheet sprite shows, from its `_N` suffix (as CreatureDirector.LoadArt indexes them); −1 when unnamed.</summary>
        static int FrameIndex(Sprite sp)
        {
            if (sp == null) return -1;
            int u = sp.name.LastIndexOf('_');
            return u >= 0 && int.TryParse(sp.name.Substring(u + 1), out int n) ? n : -1;
        }

        [System.Serializable]
        public sealed class SheetSpec { public int frame_width, frame_height, columns, gutter; public float[] pivot; }

        [System.Serializable] public sealed class ModelJson { public int fps; public ModelJsonClip[] clips; }
        [System.Serializable] public sealed class ModelJsonClip { public string name; public int frames; public bool loop; }
    }
}
