using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Meridian.Core;
using Meridian.Perf;
using Meridian.Player;
using Meridian.Ship;
using Meridian.Space;
using Meridian.Transitions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// BudgetGate v1 (Bible §11.1, U-014): one flight through the real game: Earth (idle +
    /// streaming), launch, Space, entry, Mars. With a graphics device each measured frame is
    /// rendered at 1920×1080 so draw calls and frame time include rendering; headless runs skip
    /// only the draw-call row. tools/unity_profile.ps1 runs it with graphics and sets
    /// MERIDIAN_PROFILE_REPORT, where this test writes perf_&lt;date&gt;.md.
    /// </summary>
    public class BudgetGateTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const int Frames = BudgetMonitor.Window;
        string saveRoot;
        RenderTexture rt;
        bool graphics;
        readonly List<string[]> rows = new List<string[]>();   // budget, limit, measured, result
        readonly List<string> notes = new List<string>();
        readonly List<string> failures = new List<string>();
        float firstFrameMs = -1f;

        [SetUp]
        public void SetUp()
        {
            saveRoot = Path.Combine(Application.temporaryCachePath, "meridian_saves_bg_" + Guid.NewGuid().ToString("N").Substring(0, 6));
            Meridian.Save.SaveSystem.RootOverride = saveRoot;
            graphics = SystemInfo.graphicsDeviceType != UnityEngine.Rendering.GraphicsDeviceType.Null;
            if (graphics) rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            // The game warms up at the size it renders (the screen); this test renders 1920×1080 (U-028).
            RenderWarmup.TargetSize = new Vector2Int(1920, 1080);
        }

        [TearDown]
        public void TearDown()
        {
            Meridian.Save.SaveSystem.RootOverride = null;
            RenderWarmup.TargetSize = default;
            if (Directory.Exists(saveRoot)) Directory.Delete(saveRoot, true);
            if (rt != null) { rt.Release(); UnityEngine.Object.Destroy(rt); }
        }

        void Row(string budget, string limit, string measured, bool ok)
        {
            rows.Add(new[] { budget, limit, measured, ok ? "green" : "RED" });
            if (!ok) failures.Add($"{budget}: {measured} (limit {limit})");
        }

        void Info(string budget, string limit, string measured, string result) => rows.Add(new[] { budget, limit, measured, result });

        /// <summary>Measures three windows of `Frames` frames: the first without rendering (the frames straight after the scene is ready:
        /// its bytes are the transition's own tail, printed, not judged), then the rendered window (the frame-time rows: where it
        /// always stood, `Frames` frames in), then the GC window without rendering, on a scene that has stood 2 × `Frames` frames.
        /// U-211: the GC row was the FIRST window until 0.6.3, so on Mars and in Space it read whatever the transition was still
        /// loading: two readings 17 minutes apart differed two to three times (79-132 KB, 209-620 KB), while the settled scenes read
        /// the Editor's floor (AllocByTypeTests). A steady row is the one Bible 11.1 means and the one that repeats.</summary>
        IEnumerator Measure(string where, Camera view, int drawCallLimit, Action<BudgetSnapshot, BudgetSnapshot> done)
        {
            var m = BudgetMonitor.Instance;
            // U-211's diagnostic (MERIDIAN_ALLOC_DIAG set; Editor): the Profiler records the arrival window and its allocation is
            // printed by sample path. Off in a gate reading that counts: the Profiler's own recording costs frame time.
            bool diag = !string.IsNullOrEmpty(Environment.GetEnvironmentVariable("MERIDIAN_ALLOC_DIAG"));
#if UNITY_EDITOR
            if (diag) AllocByMarkerTests.BeginCapture();
#endif
            m.ResetWindow();
            for (int i = 0; i < Frames; i++)
            {
                yield return null;
#if UNITY_EDITOR
                if (diag && i == 279) AllocByMarkerTests.EndCapture($"the gate's arrival window · {where} (its first 280 frames)", 12, 4);
#endif
            }
            var tail = m.Snapshot(view);
            tailBytes[where] = (tail.gcProfilerBytes, tail.frames);

            m.ResetWindow();
            for (int i = 0; i < Frames; i++)
            {
                if (graphics)
                {
                    var w = System.Diagnostics.Stopwatch.StartNew();
                    view.targetTexture = rt; view.Render(); view.targetTexture = null;
                    if (i == 0) firstFrameMs = (float)w.Elapsed.TotalMilliseconds; // first visible frame after the load
                }
                yield return null;
            }
            var renderWindow = m.Snapshot(view);
            // The settled window needs a scene that stands. After an entry the ship is still coming down: the camera crosses chunks
            // and the streamer goes on loading for seconds (the Profiler's capture: 1.2 MB over 9 s on Mars), which is the
            // arrival's cost, not the standing scene's: the body is held and the terrain let settle for this one window.
            bool held = holdForSettled != null && holdForSettled.simulated;
            if (held) holdForSettled.simulated = false;
            if (settledTerrain != null)
            {
                float until = Time.realtimeSinceStartup + 20f;
                for (int still = 0; still < 60 && Time.realtimeSinceStartup < until;) { yield return null; still = settledTerrain.IsSettled ? still + 1 : 0; }
            }
            for (int i = 0; i < 3; i++) yield return null; // the snapshot's own searches allocate: they are not the scene's
            m.ResetWindow();
            for (int i = 0; i < Frames; i++) yield return null;
            var gcWindow = m.Snapshot(view);
            if (held) holdForSettled.simulated = true;
            done(gcWindow, renderWindow);
        }

        /// <summary>The first window's bytes by scene (the transition's tail): an info row beside the steady GC row.</summary>
        readonly Dictionary<string, (long bytes, int frames)> tailBytes = new Dictionary<string, (long, int)>();
        /// <summary>A body held still, and the terrain waited for, while the settled GC window is read (the ship after an entry).</summary>
        Rigidbody2D holdForSettled;
        Meridian.Terrain.TerrainStreamer settledTerrain;

        void Judge(string where, BudgetSnapshot gc, BudgetSnapshot r, int drawCallLimit)
        {
            string tag = graphics ? "rendered 1920×1080" : "headless, CPU only";
            if (graphics)
                Row($"First visible frame · {where}", "≤ 50 ms (U-028)", $"{firstFrameMs:F1} ms (warm-up {(where == "Space" ? "at boot" : $"{UnityEngine.Object.FindAnyObjectByType<SceneDirector>().LastPlanetWarmupMs:F0} ms at load")})", firstFrameMs <= 50f);
            else
                Info($"First visible frame · {where}", "≤ 50 ms (U-028)", "n/a (no graphics device)", "skipped");
            Row($"Frame time · {where}", "avg ≤ 12 ms (target), p99 ≤ 16.6 ms",
                $"avg {r.avgFrameMs:F2} ms, p99 {r.p99FrameMs:F2} ms, max {r.maxFrameMs:F1} ms ({tag})",
                r.avgFrameMs <= BudgetMonitor.FrameTargetMs && r.p99FrameMs <= BudgetMonitor.FrameBudgetMs);
            if (r.drawCalls >= 0)
                Row($"Draw calls · {where}", $"≤ {drawCallLimit}", r.drawCalls.ToString(), r.drawCalls <= drawCallLimit);
            else
                Info($"Draw calls · {where}", $"≤ {drawCallLimit}", "n/a (no graphics device)", "skipped");
            // U-077 (Bible §11.1, 3D): geometry per frame.
            if (r.triangles >= 0)
                Row($"Geometry · {where}", "≤ 500 k triangles, ≤ 150 shadow casters (v3)",
                    $"{r.triangles / 1000f:F1} k triangles, {r.shadowCasters} shadow casters",
                    r.triangles <= BudgetMonitor.TrianglesCap && r.shadowCasters <= BudgetMonitor.ShadowCastersCap);
            else
                Info($"Geometry · {where}", "≤ 500 k triangles, ≤ 150 shadow casters (v3)", "n/a (no graphics device)", "skipped");
            Row($"2D lights visible · {where}", "≤ 8 (hard cap 12)", r.lightsVisible.ToString(), r.lightsVisible <= BudgetMonitor.LightsTarget);
            Row($"Particles alive · {where}", "≤ 1500 (v3)", r.particlesAlive.ToString(), r.particlesAlive <= BudgetMonitor.ParticlesCap);
            // The GC rows wait for the Editor's own floor, read once at the end of the run (FloorThenGcRows): their places are kept here.
            // Two rows (LEAD 11:3x): the settled scene, judged; the first frames after the scene is ready, a row of its own so the
            // arrival's bytes stay in sight (reported until LEAD sets its limit: a burst at arrival is where a hitch is felt).
            gcRows.Add((rows.Count, where, gc.gcProfilerBytes, gc.frames));
            rows.Add(new[] { $"GC per 300 frames, settled · {where}", GcLimit, "pending the floor", "pending" });
            rows.Add(new[] { $"GC in the first 300 frames after the scene is ready · {where}", TailLimit, "pending the floor", "pending" });
            // D-036/D-058: memory is judged in the development build (unity_profile -Build); the Editor row is info only.
            bool memOk = Within(r.workingSetMB, BudgetMonitor.WorkingSetMB) && Within(r.textureMemoryMB, BudgetMonitor.TexturesMB) && Within(r.audioMemoryMB, BudgetMonitor.AudioMB);
            Info($"Memory · {where} (Editor)", "< 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089)",
                $"working set {Mb(r.workingSetMB)}, system {Mb(r.systemMemoryMB)}, textures {Mb(r.textureMemoryMB)}, meshes {Mb(r.meshMemoryMB)}, audio {Mb(r.audioMemoryMB)} (Editor process: upper bound)",
                memOk ? "info (within)" : "info (over; the dev-build row decides, D-058)");
        }

        // ---- the GC rows (08:3x) ----
        // Until 0.6.2 the row judged BudgetMonitor's main-thread figure (P-16), System.GC.GetAllocatedBytesForCurrentThread, which reads
        // 0 B for any allocation in Unity's runtime: the row was green on nothing in every gate, with the live counter printed beside
        // it unjudged (410 KB to 9.6 MB per 300 frames). The row now judges Unity's own "GC Allocated In Frame" over the window, less
        // the Editor's and the test runner's own bytes, read at the end of this run with every root object of the scene inactive.
        const string GcLimit = "≤ 1 KB of the game's own (Unity's 'GC Allocated In Frame' over a steady window, 600 frames after the scene is ready, less the Editor's floor read in this run)";
        const string TailLimit = "reported (U-211; LEAD sets the limit): the game's own bytes in the first window after the scene is ready, before the settled one";
        readonly List<(int row, string where, long live, int frames)> gcRows = new List<(int, string, long, int)>();

        /// <summary>Reads the Editor's floor (after a control: the counter must show a known 64 KB array) and fills the GC rows in.</summary>
        IEnumerator FloorThenGcRows()
        {
            long floor = 0, seenKnown = 0;
            bool live;
            var off = new List<GameObject>();
            using (var rec = Unity.Profiling.ProfilerRecorder.StartNew(Unity.Profiling.ProfilerCategory.Memory, "GC Allocated In Frame"))
            {
                for (int i = 0; i < 3; i++) yield return null;
                var known = new byte[65536];
                for (int i = 0; i < 3; i++) { yield return null; seenKnown = Math.Max(seenKnown, rec.LastValue); }
                GC.KeepAlive(known);
                live = rec.Valid && seenKnown >= 65536;
                foreach (var root in SceneManager.GetActiveScene().GetRootGameObjects())
                    if (root.activeSelf) { root.SetActive(false); off.Add(root); }
                for (int i = 0; i < 10; i++) yield return null;
                long sum = 0, least = long.MaxValue;
                for (int i = 0; i < Frames; i++) { yield return null; long v = rec.LastValue; sum += v; least = Math.Min(least, v); }
                // The floor is the LEAST frame, times the window: the Editor's own loop adds 52 B or a kilobyte to a frame now and
                // then, in the floor's window as in a scene's, so the sum wandered by about 1 KB a run (87 000, 87 418, 88 247 B on
                // 11-10), as much as the limit; taken off, settled scenes read -1 143 to +598 B. With the least frame the game's
                // figure is an upper bound (the Editor's odd extra frames stay in it) and it repeats.
                floor = least * Frames;
                foreach (var root in off) if (root != null) root.SetActive(true);
                for (int i = 0; i < 10; i++) yield return null;
                notes.Add($"GC rows: Unity's 'GC Allocated In Frame'; the control (a 65536 B array) read {seenKnown} B{(live ? "" : ": THE COUNTER IS NOT LIVE, the rows are not judged green")}; the Editor's and the test runner's own floor: the least frame {least} B, so {floor} B per {Frames} frames (the window's sum was {sum} B), read with every root object inactive");
            }
            foreach (var g in gcRows)
            {
                long share = g.frames > 0 ? floor * g.frames / Frames : floor;
                long game = g.live - share;
                bool ok = live && game <= BudgetMonitor.GcBytesPer300;
                // D-201 (LEAD 08:3x): Earth's rows gate the build (the owner's playtest is Earth's dig); a scene over on Mars or in
                // Space is U-211's (first after 0.6.3): shown RED with its number, named, not a gate failure
                bool gates = g.where.StartsWith("Earth", StringComparison.Ordinal);
                string measured = $"{game} B of the game's own ({g.live} B in the window of {g.frames} frames, the floor {share} B)";
                rows[g.row] = new[] { $"GC per 300 frames, settled · {g.where}", GcLimit, measured, ok ? "green" : gates ? "RED" : "RED: U-211 (D-201: Earth's rows gate)" };
                if (!ok && gates) failures.Add($"GC per 300 frames, settled · {g.where}: {measured} (limit {GcLimit})");
                if (tailBytes.TryGetValue(g.where, out var tail))
                {
                    long tailShare = tail.frames > 0 ? floor * tail.frames / Frames : floor;
                    rows[g.row + 1] = new[] { $"GC in the first 300 frames after the scene is ready · {g.where}", TailLimit, $"{tail.bytes - tailShare} B of the game's own ({tail.bytes} B in the window of {tail.frames} frames, the floor {tailShare} B)", "info (U-211: no limit yet)" };
                }
            }
        }

        static string Mb(long v) => v < 0 ? "n/a" : $"{v} MB";
        static bool Within(long v, long limit) => v < 0 || v <= limit;

        static IEnumerator WaitBusyCycle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

        [UnityTest]
        public IEnumerator EarthSpaceMarsStayWithinBudgets()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            Assert.NotNull(BudgetMonitor.Instance, "BudgetMonitor in Core");
            // D-083: the wrapper measures free RAM before the Editor launches (MERIDIAN_FREE_RAM_MB); inside the Editor the number is already spent.
            var freeAtStart = Environment.GetEnvironmentVariable("MERIDIAN_FREE_RAM_MB");
            notes.Add($"Load during measurement (D-019/D-083): {OtherHeavyJobs()}; free RAM at start {(string.IsNullOrEmpty(freeAtStart) ? "n/a (no wrapper)" : freeAtStart + " MB")} (in-Editor now {ProcessMemory.FreeSystemMB()} MB); Unity Editor processes {UnityEditorProcesses()}");

            // ---- Earth, idle ----
            var side = director.PlanetSide;
            // D-177 (2): the first 2 s after boot stay measured: every frame rendered at 1080p, max ≤ 50 ms gates; the p99 (≤ 25 ms) is recorded in
            // 0.5.1 and gates from U-179 on (it traces those loads behind the title card).
            {
                var bootFrames = new List<float>(256);
                yield return null; // the frame that ran the notes' process queries above (D-083) is the gate's own, not the game's
                float bootUntil = Time.realtimeSinceStartup + 2f;
                while (Time.realtimeSinceStartup < bootUntil)
                {
                    if (graphics) { side.sideCamera.targetTexture = rt; side.sideCamera.Render(); side.sideCamera.targetTexture = null; }
                    yield return null;
                    bootFrames.Add(Time.unscaledDeltaTime * 1000f);
                }
                bootFrames.Sort();
                float bootMax = bootFrames.Count > 0 ? bootFrames[bootFrames.Count - 1] : 0f;
                float bootP99 = bootFrames.Count > 0 ? bootFrames[Mathf.Clamp(Mathf.CeilToInt(bootFrames.Count * 0.99f) - 1, 0, bootFrames.Count - 1)] : 0f;
                Row("Boot settle · Earth", "the first 2 s after boot: max frame ≤ 50 ms (gates); p99 ≤ 25 ms (recorded in 0.5.1, gates from U-179) (D-177)",
                    $"{bootFrames.Count} frames: max {bootMax:F1} ms, p99 {bootP99:F1} ms{(bootP99 > 25f ? " (p99 over 25: U-179)" : "")} ({(graphics ? "rendered 1920×1080" : "headless, CPU only")})", bootMax <= 50f);
            }
            // D-177 (1): the idle row measures the camp settled, as C0's row does: the flora Ready, then 120 frames.
            {
                float ft0 = Time.realtimeSinceStartup;
                while (side.cartoon != null && side.cartoon.Flora != null && !side.cartoon.Flora.Ready && Time.realtimeSinceStartup - ft0 < 15f) yield return null;
                for (int i = 0; i < 120; i++) yield return null;
            }
            BudgetSnapshot gc = default, r = default;
            yield return Measure("Earth", side.sideCamera, BudgetMonitor.DrawCallsSide, (a, b) => { gc = a; r = b; });
            Judge("Earth", gc, r, BudgetMonitor.DrawCallsSide);

            // ---- Earth, streaming (D-019) ----
            var t = side.terrain;
            var cam = side.sideCamera;
            var follow = cam.GetComponent<CameraFollow>();
            follow.enabled = false;
            // U-165: streaming follows the camera, so the camp's chunks unload under the surveyor while the camera is 200 m away: hold it
            // still meanwhile (it fell through its unloaded ground and the solid rescue lifted it 0.76 m when the camera came back).
            var surveyor = side.player != null ? side.player.Body : null;
            bool surveyorSim = surveyor != null && surveyor.simulated;
            if (surveyor != null) surveyor.simulated = false;
            var applyMs = new double[400];
            float worst = 0f;
            for (int i = 0; i < applyMs.Length; i++)
            {
                cam.transform.position += new Vector3(0.5f, 0f, 0f);
                if (graphics) { cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; }
                yield return null;
                applyMs[i] = t.LastApplyMs;
                worst = Mathf.Max(worst, Time.unscaledDeltaTime * 1000f);
            }
            var sorted = (double[])applyMs.Clone();
            Array.Sort(sorted);
            int over = applyMs.Count(a => a > 2.0);
            double p99 = sorted[sorted.Length * 99 / 100];
            Row("Chunk generation · Earth streaming 200 m", "≤ 2 ms main thread in ≥ 99% of frames; no hitch > 33 ms (D-019)",
                $"p99 {p99:F2} ms, {over}/400 over 2 ms, worst frame {worst:F1} ms",
                p99 <= 2.0 && over <= 4 && worst < 33f);
            cam.transform.position -= new Vector3(200f, 0f, 0f);
            follow.enabled = true;
            while (!t.IsSettled) yield return null;
            yield return new WaitForFixedUpdate(); // the camp's colliders back in the physics world
            if (surveyor != null) surveyor.simulated = surveyorSim;

            // ---- Launch → Space ----
            var transitions = UnityEngine.Object.FindAnyObjectByType<TransitionDirector>();
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p; ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            yield return WaitBusyCycle(transitions, 10f);
            Row("Transition · launch (side → top-down)", "≤ 1.5 s", $"{transitions.LastLaunchSeconds:F2} s", transitions.LastLaunchSeconds <= 1.5f);

            var spaceCam = director.Space.GetComponentInChildren<Camera>();
            var spaceShip = director.Space.GetComponentInChildren<SpaceShip>();
            spaceShip.externalInput = true;
            spaceShip.intent = default;
            // Park outside Earth's well: an idle ship on the ring falls back in and (correctly) re-enters.
            var earth = spaceShip.world.Find("earth").Value;
            spaceShip.Position = earth.position + new Vector2(0f, earth.WellRadius + 50f);
            spaceShip.Velocity = Vector2.zero;
            yield return Measure("Space", spaceCam, BudgetMonitor.DrawCallsTop, (a, b) => { gc = a; r = b; });
            Assert.AreEqual(ViewMode.Space, GameState.Instance.view, "still in space after the measurement");
            Judge("Space", gc, r, BudgetMonitor.DrawCallsTop);

            // ---- Entry → Mars ----
            // Headless frames are fast: the 1 s post-launch invulnerability (which ignores ring crossings) may still run.
            while (spaceShip.Invulnerable) yield return null;
            var mars = spaceShip.world.Find("mars").Value;
            spaceShip.Position = mars.position + new Vector2(0f, mars.RingRadius + 0.5f);
            spaceShip.Velocity = new Vector2(0f, -40f);
            yield return WaitBusyCycle(transitions, 15f);
            Row("Planet load · Mars entry", "≤ 5 s (v3)", $"{transitions.LastEntrySeconds:F2} s ({director.LastLoadBreakdown})", transitions.LastEntrySeconds <= 5f);
            Info("Transition · entry (top-down → side)", "≤ 1.5 s in the dev-build transition rows (D-136 (2): the Editor transition row is info, like the Editor memory rows)", $"{transitions.LastEntrySeconds:F2} s (Editor)", "info");

            side = director.PlanetSide;
            Assert.NotNull(side, "entered a planet");
            Assert.AreEqual(Meridian.Planets.PlanetId.Mars, side.Config.id);
            while (!side.terrain.IsSettled) yield return null;
            // U-086 (Bible §11.1 v3 Residency): the previous planet's groups release within 5 s of the transition; only the
            // current planet's groups (+ common, ui, icons, space; "session" = the film overlays, U-091) stay resident.
            float resT0 = Time.realtimeSinceStartup;
            int earthHandles = Residency.CountPlanet("planet_earth");
            while (earthHandles > 0 && Time.realtimeSinceStartup - resT0 < 5f) { yield return null; earthHandles = Residency.CountPlanet("planet_earth"); }
            float resWait = Time.realtimeSinceStartup - resT0;
            // D-083: the row reads "pending U-091" until U-091 closes; its measurement is U-091's evidence, not a gate failure.
            bool resOk = earthHandles == 0 && Residency.OnlyPlanet("planet_mars");
            Info("Residency · after Mars entry", "previous planet released within 5 s; only the current planet + common/ui/icons/space resident (v3)",
                $"planet_earth handles {earthHandles} after {resWait:F1} s (holders: {Residency.Holders("planet_earth")}); resident: {Residency.ResidentGroups()}",
                resOk ? "green (pending U-091)" : "pending U-091 (D-083): would be red");
            holdForSettled = side.ship != null ? side.ship.Body : null; // Mars' three scenes: the ship is still coming down from the entry
            settledTerrain = side.terrain;
            yield return Measure("Mars", side.sideCamera, BudgetMonitor.DrawCallsSide, (a, b) => { gc = a; r = b; });
            Judge("Mars", gc, r, BudgetMonitor.DrawCallsSide);

            // ---- Mars in a full dust storm (U-026): the fog pass and the puffs ----
            var storm = side.dustStorm;
            var clock = UnityEngine.Object.FindAnyObjectByType<TimeSystem>();
            storm.Force(0.1f, 300f);
            clock.Advance(0.1f + Meridian.Planet.Weather.DustStorm.RampRealSeconds + 1f);
            yield return null;
            Assert.AreEqual(1f, storm.Intensity, 1e-3f, "full storm for the measurement");
            yield return Measure("Mars dust storm", side.sideCamera, BudgetMonitor.DrawCallsSide, (a, b) => { gc = a; r = b; });
            Judge("Mars dust storm", gc, r, BudgetMonitor.DrawCallsSide);

            // ---- U-033 effects at their peak: the one-shot pool kept full every frame, in the storm ----
            var stress = new GameObject("FxStress").AddComponent<FxStress>();
            stress.pool = side.GetComponentInChildren<Meridian.FX.FxPool>();
            stress.around = side.sideCamera.transform;
            Assert.NotNull(stress.pool, "FxPool on PlanetSide");
            for (int i = 0; i < 30; i++) yield return null;
            Assert.AreEqual(Meridian.FX.FxPool.Size, stress.pool.Alive, "pool full");
            yield return Measure("Mars FX peak", side.sideCamera, BudgetMonitor.DrawCallsSide, (a, b) => { gc = a; r = b; });
            Judge("Mars FX peak", gc, r, BudgetMonitor.DrawCallsSide);
            UnityEngine.Object.Destroy(stress.gameObject);
            holdForSettled = null; settledTerrain = null;

            // ---- Earth on the v4 cartoon path (U-101: the rows U-098 asks for; Bible §9.6, D-089) ----
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            try
            {
                yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Earth));
                side = director.PlanetSide;
                Assert.IsTrue(side.cartoon != null && side.cartoon.Active, "the cartoon path is on for Earth");
                while (!side.terrain.IsSettled) yield return null;
                float c0t0 = Time.realtimeSinceStartup;
                while (side.cartoon.Flora != null && !side.cartoon.Flora.Ready && Time.realtimeSinceStartup - c0t0 < 15f) yield return null;
                for (int i = 0; i < 60; i++) yield return null; // plants placed, sheets in
                yield return Measure("Earth C0 (cartoon)", side.sideCamera, BudgetMonitor.DrawCallsSide, (a, b) => { gc = a; r = b; });
                Judge("Earth C0 (cartoon)", gc, r, BudgetMonitor.DrawCallsSide);
                long ws = r.workingSetMB > 0 ? r.workingSetMB : r.systemMemoryMB;
                Info("Working set · Earth C0 (v4, D-089)", "< 2.0 GB (warn 1.7); the dev-build probe rows decide (D-114 / D-116, P-28 / D-120)", $"{ws} MB (Editor process: an upper bound of the build){(ws >= 1741 && ws < 2048 ? ", above the 1.7 GB warning line" : "")}", ws < 2048 ? "info (within)" : "info (over; the dev-build row decides)");
                int animated = 0;
                foreach (var a in UnityEngine.Object.FindObjectsByType<Animator>(FindObjectsInactive.Exclude)) if (a.isActiveAndEnabled && a.runtimeAnimatorController != null) animated++;
                var flora = side.cartoon.Flora;
                Row("Animated objects · Earth C0", "≤ 40 on screen (Bible §9.6)", $"{animated} Animators running (flora full rate {(flora != null ? flora.FullRateCount : 0)}, cheap idle {(flora != null ? flora.CheapCount : 0)}, plants {(flora != null ? flora.Plants.Count : 0)})", animated <= 40);
                int atlases = AtlasFilesFor("earth");
                Row("Sprite atlases · Earth", "≤ 8 per planet (contract §11.8)", $"{atlases} planet_earth* atlases on disk", atlases <= 8);
            }
            finally { Meridian.View2D.CartoonStage.Enabled = wasCartoon; }

            yield return FloorThenGcRows();
            StaticRows();
            WriteReport();
            Assert.IsEmpty(failures, "budgets over: " + string.Join("; ", failures));
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>Import-time rows (textures, audio, size caps) read from the importers.</summary>
        /// <summary>A v3 cartoon asset (contract §11): its sidecar says "style": "v3", or it is a 4-segment background layer / palette strip.</summary>
        static bool IsV3Asset(string root, string colorPath)
        {
            var json = colorPath.Substring(0, colorPath.Length - "_color.png".Length) + ".json";
            if (System.IO.File.Exists(json) && System.Text.RegularExpressions.Regex.IsMatch(System.IO.File.ReadAllText(json), "\"style\"\\s*:\\s*\"v3\"")) return true;
            var rel = colorPath.Substring(root.Length + 1);
            return rel.Split('/').Length == 4 && (rel.StartsWith("backgrounds/", StringComparison.Ordinal) || rel.StartsWith("ui/palettes/", StringComparison.Ordinal));
        }

        /// <summary>U-101: the planet's sprite atlases on disk (Settings/Atlases/planet_&lt;planet&gt;*.spriteatlasv2); -1 outside the Editor.</summary>
        static int AtlasFilesFor(string planet)
        {
#if UNITY_EDITOR
            const string dir = "Assets/_Game/Settings/Atlases";
            if (!System.IO.Directory.Exists(dir)) return 0;
            int n = 0;
            foreach (var f in System.IO.Directory.GetFiles(dir, "*.spriteatlasv2"))
                if (System.IO.Path.GetFileNameWithoutExtension(f).StartsWith("planet_" + planet, StringComparison.Ordinal)) n++;
            return n;
#else
            return -1;
#endif
        }

        void StaticRows()
        {
#if UNITY_EDITOR
            int wrongColor = 0, wrongNormal = 0, missingMips = 0, npotNoMips = 0, v3NoMips = 0, total = 0;
            var wrong = new List<string>();
            foreach (var root in new[] { "Assets/_Game/Art", "Assets/_Game/Placeholders" })
            foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:Texture2D", new[] { root }))
            {
                var path = UnityEditor.AssetDatabase.GUIDToAssetPath(guid);
                if (!(UnityEditor.AssetImporter.GetAtPath(path) is UnityEditor.TextureImporter ti)) continue;
                total++;
                var fmt = ti.GetPlatformTextureSettings("Standalone").format;
                if (path.EndsWith("_normal.png")) { if (fmt != UnityEditor.TextureImporterFormat.BC5) { wrongNormal++; wrong.Add(path); } }
                // D-192 amended (LEAD 11-09 22:2x): the dug cells' back walls are the one colour map that is uncompressed RGBA32, not BC7
                else if (path.EndsWith("_color.png") && fmt != (Meridian.Art.ArtKeys.IsBackWall(path) ? UnityEditor.TextureImporterFormat.RGBA32 : UnityEditor.TextureImporterFormat.BC7)) { wrongColor++; wrong.Add(path); }
                bool world = !path.Contains("/fx/") && !path.Contains("/icons/") && !path.Contains("/ui/");
                // D-061: non-power-of-two sheets import without mips (NPOT + mips would be stored uncompressed).
                ti.GetSourceTextureWidthAndHeight(out int tw, out int th);
                bool pot = Mathf.IsPowerOfTwo(tw) && Mathf.IsPowerOfTwo(th);
                // Contract v3.0 §11.8 (D-086): v3 cartoon assets import WITHOUT mips by rule; the mips rule here is the v2 one.
                bool v3 = path.EndsWith("_color.png") && IsV3Asset(root, path);
                if (path.EndsWith("_color.png") && world && !ti.mipmapEnabled) { if (v3) v3NoMips++; else if (pot) missingMips++; else npotNoMips++; }
            }
            Row("Textures", "BC7 color (the back walls RGBA32, D-192), BC5 normals, mips on POT world sprites (NPOT: none, D-061)",
                $"{total} textures: {wrongColor} color not BC7 (a back wall: not RGBA32), {wrongNormal} normals not BC5, {missingMips} POT world sprites without mips ({npotNoMips} NPOT without, D-061; {v3NoMips} v3 without by rule, contract §11.8){(wrong.Count > 0 ? "; off-rule: " + string.Join(", ", wrong.Take(5)) : "")}",
                wrongColor == 0 && wrongNormal == 0 && missingMips == 0);

            int bigAtlas = 0, atlases = 0;
            foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:SpriteAtlas", new[] { "Assets/_Game/Settings/Atlases" }))
            {
                atlases++;
                var atlas = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.U2D.SpriteAtlas>(UnityEditor.AssetDatabase.GUIDToAssetPath(guid));
                var s = UnityEditor.U2D.SpriteAtlasExtensions.GetPlatformSettings(atlas, "Standalone");
                if (s.maxTextureSize > 2048) bigAtlas++;
            }
            Row("Atlases", "≤ 2048²", $"{atlases} atlases, {bigAtlas} allow more than 2048", bigAtlas == 0);

            int wrongAudio = 0, clips = 0;
            foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:AudioClip", new[] { "Assets/_Game/Audio" }))
            {
                clips++;
                var ai = (UnityEditor.AudioImporter)UnityEditor.AssetImporter.GetAtPath(UnityEditor.AssetDatabase.GUIDToAssetPath(guid));
                var s = ai.defaultSampleSettings;
                bool music = UnityEditor.AssetDatabase.GUIDToAssetPath(guid).Contains("/ambient/");
                bool ok = s.compressionFormat == AudioCompressionFormat.Vorbis &&
                          s.loadType == (music ? AudioClipLoadType.Streaming : AudioClipLoadType.CompressedInMemory);
                if (!ok) wrongAudio++;
            }
            Row("Audio", "Vorbis; loops streamed, SFX compressed in memory", $"{clips} clips, {wrongAudio} off-rule", wrongAudio == 0);
            Info("Asset size caps", "contract §2/§4; importer rejects oversize", "enforced by ArtImporter (EditMode tests RejectsOversize…, FileSizeLimit…)", "green (tests)");
#endif
        }

        /// <summary>Where texture memory goes at the end of the route (Mars): the 15 largest loaded textures.</summary>
        static void AppendTopTextures(StringBuilder sb)
        {
            var all = Resources.FindObjectsOfTypeAll<Texture>()
                .Select(t => (t, bytes: UnityEngine.Profiling.Profiler.GetRuntimeMemorySizeLong(t)))
                .OrderByDescending(x => x.bytes).ToList();
            long total = all.Sum(x => x.bytes);
            sb.AppendLine();
            sb.AppendLine($"Largest loaded textures at the end of the route ({all.Count} textures, {total / 1048576} MB in all, Editor's own included):");
            sb.AppendLine();
            sb.AppendLine("| Texture | Size | Format | MB |");
            sb.AppendLine("|---|---|---|---|");
            foreach (var (t, bytes) in all.Take(15))
            {
                string fmt = t is Texture2D t2 ? t2.format.ToString() : t is RenderTexture rt ? "RT " + rt.format : t.GetType().Name;
                sb.AppendLine($"| {t.name} | {t.width}×{t.height} | {fmt} | {bytes / 1048576f:F1} |");
            }
        }

        void WriteReport()
        {
            var path = Environment.GetEnvironmentVariable("MERIDIAN_PROFILE_REPORT");
            var sb = new StringBuilder();
            sb.AppendLine($"# UNITY performance report {DateTime.Now:yyyy-MM-dd HH:mm}");
            sb.AppendLine();
            sb.AppendLine($"BudgetGate v3 (U-014; U-086 with the D-077 limits): `BudgetGateTests.EarthSpaceMarsStayWithinBudgets`. Graphics: {(graphics ? SystemInfo.graphicsDeviceName : "none (headless)")}. " +
                          "Memory rows read the Editor process, an upper bound for the built game.");
            foreach (var n in notes) sb.AppendLine($"- {n}");
            sb.AppendLine();
            sb.AppendLine("| Budget (Bible §11.1) | Limit | Measured | Result |");
            sb.AppendLine("|---|---|---|---|");
            foreach (var r in rows) sb.AppendLine($"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |");
            AppendTopTextures(sb);
            TestContext.Out.WriteLine(sb.ToString());
            if (string.IsNullOrEmpty(path)) return;
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, sb.ToString());
        }

        /// <summary>D-083: Unity Editor processes alive at the start (this one included); 2+ means a contention run.</summary>
        static int UnityEditorProcesses()
        {
            int n = 0;
            foreach (var p in System.Diagnostics.Process.GetProcessesByName("Unity"))
            {
                // D-015: the Hub's always-on unity.exe is not an Editor; count only Hub\Editor installs, and never a process we cannot read.
                try { if (p.MainModule != null && p.MainModule.FileName.IndexOf(@"\Hub\Editor\", StringComparison.OrdinalIgnoreCase) >= 0) n++; } catch (Exception) { }
                p.Dispose();
            }
            return n;
        }

        static string OtherHeavyJobs()
        {
            var found = new List<string>();
            if (Directory.Exists("coordination/locks"))
                foreach (var f in Directory.GetFiles("coordination/locks", "heavy_*.lock"))
                    if (!f.EndsWith("heavy_unity.lock")) found.Add(Path.GetFileName(f));
            if (System.Diagnostics.Process.GetProcessesByName("blender").Length > 0) found.Add("blender.exe running");
            return found.Count == 0 ? "none" : string.Join(", ", found);
        }
    }

    /// <summary>Keeps an FxPool full (U-033 peak): a new dig-spark or dust burst wherever a slot frees up.</summary>
    public sealed class FxStress : MonoBehaviour
    {
        public Meridian.FX.FxPool pool;
        public Transform around;
        int n;

        void Update()
        {
            if (pool == null) return;
            while (pool.Alive < Meridian.FX.FxPool.Size)
            {
                n++;
                var key = (n & 1) == 0 ? Meridian.Art.ArtKeys.Fx.Dust : Meridian.Art.ArtKeys.Fx.DigSparks;
                var p = (Vector2)around.position + new Vector2((n * 37 % 30) - 15f, (n * 11 % 12) - 6f);
                if (!pool.Play(key, p, 1.5f)) break;
            }
        }
    }
}
