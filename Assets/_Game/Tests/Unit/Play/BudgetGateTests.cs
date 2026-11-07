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

        /// <summary>Measures `Frames` frames: first a GC window without rendering, then a rendered window.</summary>
        IEnumerator Measure(string where, Camera view, int drawCallLimit, Action<BudgetSnapshot, BudgetSnapshot> done)
        {
            var m = BudgetMonitor.Instance;
            m.ResetWindow();
            for (int i = 0; i < Frames; i++) yield return null;
            var gcWindow = m.Snapshot(view);

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
            done(gcWindow, renderWindow);
        }

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
            Row($"GC per 300 frames · {where}", "≤ 1 KB (main-thread managed allocations; P-16)",
                $"{gc.gcBytesLast300} B (Unity GC counter incl. Editor: {gc.gcProfilerBytes / 1024} KB)", gc.gcBytesLast300 <= BudgetMonitor.GcBytesPer300);
            // D-036/D-058: memory is judged in the development build (unity_profile -Build); the Editor row is info only.
            bool memOk = Within(r.workingSetMB, BudgetMonitor.WorkingSetMB) && Within(r.textureMemoryMB, BudgetMonitor.TexturesMB) && Within(r.audioMemoryMB, BudgetMonitor.AudioMB);
            Info($"Memory · {where} (Editor)", "< 2.0 GB working set (warn 1.7), ≤ 512 MB textures, ≤ 150 MB audio; meshes reported (v4, D-089)",
                $"working set {Mb(r.workingSetMB)}, system {Mb(r.systemMemoryMB)}, textures {Mb(r.textureMemoryMB)}, meshes {Mb(r.meshMemoryMB)}, audio {Mb(r.audioMemoryMB)} (Editor process: upper bound)",
                memOk ? "info (within)" : "info (over; the dev-build row decides, D-058)");
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
            BudgetSnapshot gc = default, r = default;
            yield return Measure("Earth", side.sideCamera, BudgetMonitor.DrawCallsSide, (a, b) => { gc = a; r = b; });
            Judge("Earth", gc, r, BudgetMonitor.DrawCallsSide);

            // ---- Earth, streaming (D-019) ----
            var t = side.terrain;
            var cam = side.sideCamera;
            var follow = cam.GetComponent<CameraFollow>();
            follow.enabled = false;
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
            Row("Transition · entry (top-down → side)", "≤ 1.5 s", $"{transitions.LastEntrySeconds:F2} s", transitions.LastEntrySeconds <= 1.5f);

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

            // ---- Earth on the v4 cartoon path (U-101: the rows U-098 asks for; Bible §9.6, D-089) ----
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
                Row("Working set · Earth C0 (v4, D-089)", "< 2.0 GB (warn 1.7)", $"{ws} MB (Editor process: an upper bound of the build){(ws >= 1741 && ws < 2048 ? ", above the 1.7 GB warning line" : "")}", ws < 2048);
                int animated = 0;
                foreach (var a in UnityEngine.Object.FindObjectsByType<Animator>(FindObjectsInactive.Exclude)) if (a.isActiveAndEnabled && a.runtimeAnimatorController != null) animated++;
                var flora = side.cartoon.Flora;
                Row("Animated objects · Earth C0", "≤ 40 on screen (Bible §9.6)", $"{animated} Animators running (flora full rate {(flora != null ? flora.FullRateCount : 0)}, cheap idle {(flora != null ? flora.CheapCount : 0)}, plants {(flora != null ? flora.Plants.Count : 0)})", animated <= 40);
                int atlases = AtlasFilesFor("earth");
                Row("Sprite atlases · Earth", "≤ 8 per planet (contract §11.8)", $"{atlases} planet_earth* atlases on disk", atlases <= 8);
            }
            finally { Meridian.View2D.CartoonStage.Enabled = false; }

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
                else if (path.EndsWith("_color.png") && fmt != UnityEditor.TextureImporterFormat.BC7) { wrongColor++; wrong.Add(path); }
                bool world = !path.Contains("/fx/") && !path.Contains("/icons/") && !path.Contains("/ui/");
                // D-061: non-power-of-two sheets import without mips (NPOT + mips would be stored uncompressed).
                ti.GetSourceTextureWidthAndHeight(out int tw, out int th);
                bool pot = Mathf.IsPowerOfTwo(tw) && Mathf.IsPowerOfTwo(th);
                // Contract v3.0 §11.8 (D-086): v3 cartoon assets import WITHOUT mips by rule; the mips rule here is the v2 one.
                bool v3 = path.EndsWith("_color.png") && IsV3Asset(root, path);
                if (path.EndsWith("_color.png") && world && !ti.mipmapEnabled) { if (v3) v3NoMips++; else if (pot) missingMips++; else npotNoMips++; }
            }
            Row("Textures", "BC7 color, BC5 normals, mips on POT world sprites (NPOT: none, D-061)",
                $"{total} textures: {wrongColor} color not BC7, {wrongNormal} normals not BC5, {missingMips} POT world sprites without mips ({npotNoMips} NPOT without, D-061; {v3NoMips} v3 without by rule, contract §11.8){(wrong.Count > 0 ? "; off-rule: " + string.Join(", ", wrong.Take(5)) : "")}",
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
