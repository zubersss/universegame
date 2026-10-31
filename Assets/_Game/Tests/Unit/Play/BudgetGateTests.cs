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
            Row($"2D lights visible · {where}", "≤ 8 (hard cap 12)", r.lightsVisible.ToString(), r.lightsVisible <= BudgetMonitor.LightsTarget);
            Row($"Particles alive · {where}", "≤ 600", r.particlesAlive.ToString(), r.particlesAlive <= BudgetMonitor.ParticlesCap);
            Row($"GC per 300 frames · {where}", "≤ 1 KB (main-thread managed allocations; P-16)",
                $"{gc.gcBytesLast300} B (Unity GC counter incl. Editor: {gc.gcProfilerBytes / 1024} KB)", gc.gcBytesLast300 <= BudgetMonitor.GcBytesPer300);
            Row($"Memory · {where}", "≤ 2.5 GB system, ≤ 600 MB textures, ≤ 60 MB audio",
                $"system {Mb(r.systemMemoryMB)}, textures {Mb(r.textureMemoryMB)}, audio {Mb(r.audioMemoryMB)} (Editor process: upper bound)",
                Within(r.systemMemoryMB, BudgetMonitor.RamMB) && Within(r.textureMemoryMB, BudgetMonitor.TexturesMB) && Within(r.audioMemoryMB, BudgetMonitor.AudioMB));
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
            notes.Add($"Load during measurement (D-019): {OtherHeavyJobs()}");

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
            Row("Planet load · Mars entry", "≤ 4 s", $"{transitions.LastEntrySeconds:F2} s ({director.LastLoadBreakdown})", transitions.LastEntrySeconds <= 4f);
            Row("Transition · entry (top-down → side)", "≤ 1.5 s", $"{transitions.LastEntrySeconds:F2} s", transitions.LastEntrySeconds <= 1.5f);

            side = director.PlanetSide;
            Assert.NotNull(side, "entered a planet");
            Assert.AreEqual(Meridian.Planets.PlanetId.Mars, side.Config.id);
            while (!side.terrain.IsSettled) yield return null;
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

            StaticRows();
            WriteReport();
            Assert.IsEmpty(failures, "budgets over: " + string.Join("; ", failures));
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>Import-time rows (textures, audio, size caps) read from the importers.</summary>
        void StaticRows()
        {
#if UNITY_EDITOR
            int wrongColor = 0, wrongNormal = 0, missingMips = 0, total = 0;
            foreach (var root in new[] { "Assets/_Game/Art", "Assets/_Game/Placeholders" })
            foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:Texture2D", new[] { root }))
            {
                var path = UnityEditor.AssetDatabase.GUIDToAssetPath(guid);
                if (!(UnityEditor.AssetImporter.GetAtPath(path) is UnityEditor.TextureImporter ti)) continue;
                total++;
                var fmt = ti.GetPlatformTextureSettings("Standalone").format;
                if (path.EndsWith("_normal.png")) { if (fmt != UnityEditor.TextureImporterFormat.BC5) wrongNormal++; }
                else if (path.EndsWith("_color.png") && fmt != UnityEditor.TextureImporterFormat.BC7) wrongColor++;
                bool world = !path.Contains("/fx/") && !path.Contains("/icons/") && !path.Contains("/ui/");
                if (path.EndsWith("_color.png") && world && !ti.mipmapEnabled) missingMips++;
            }
            Row("Textures", "BC7 color, BC5 normals, mips on world sprites",
                $"{total} textures: {wrongColor} color not BC7, {wrongNormal} normals not BC5, {missingMips} world sprites without mips",
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
            sb.AppendLine($"BudgetGate v1 (U-014): `BudgetGateTests.EarthSpaceMarsStayWithinBudgets`. Graphics: {(graphics ? SystemInfo.graphicsDeviceName : "none (headless)")}. " +
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
