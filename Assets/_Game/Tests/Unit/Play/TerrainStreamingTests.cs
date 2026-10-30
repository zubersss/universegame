using System.Collections;
using Meridian.Core;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-007: Earth streams from Core with only chunks within 2 resident and the apply budget kept.</summary>
    public class TerrainStreamingTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static IEnumerator BootEarth(System.Action<PlanetSideRoot> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            yield return SceneManager.LoadSceneAsync("Core", LoadSceneMode.Single);
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 10f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady, "SceneDirector ready");
            done(director.PlanetSide);
        }

        /// <summary>Other roles' heavy locks and Blender processes present now ("none" = a clean measurement).</summary>
        static string OtherHeavyJobs()
        {
            var found = new System.Collections.Generic.List<string>();
            if (System.IO.Directory.Exists("coordination/locks"))
                foreach (var f in System.IO.Directory.GetFiles("coordination/locks", "heavy_*.lock"))
                    if (!f.EndsWith("heavy_unity.lock")) found.Add(System.IO.Path.GetFileName(f));
            if (System.Diagnostics.Process.GetProcessesByName("blender").Length > 0) found.Add("blender.exe running");
            return found.Count == 0 ? "none" : string.Join(", ", found);
        }

        static IEnumerator WaitSettled(TerrainStreamer t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(t.IsSettled, "terrain settled in time");
        }

        [UnityTest]
        public IEnumerator EarthStreamsWithinRadiusBudgetAndFrameTime()
        {
            PlanetSideRoot side = null;
            yield return BootEarth(s => side = s);
            var t = side.terrain;
            Assert.NotNull(t, "TerrainStreamer on PlanetSide");
            yield return WaitSettled(t, 20f);

            Assert.AreEqual(25, t.ResidentCount, "5×5 chunks around the camera");
            Assert.IsTrue(t.AllResidentWithinRadius(out int worst), $"worst distance {worst}");

            // Fly right at 30 m/s-equivalent steps (0.5 m per frame) for 400 frames, crossing ~6 chunks.
            var cam = side.sideCamera.transform;
            t.ResetStats();
            float total = 0f, worstFrame = 0f;
            const int frames = 400;
            var applyMs = new double[frames];
            for (int i = 0; i < frames; i++)
            {
                cam.position += new Vector3(0.5f, 0f, 0f);
                yield return null;
                total += Time.unscaledDeltaTime;
                worstFrame = Mathf.Max(worstFrame, Time.unscaledDeltaTime);
                applyMs[i] = t.LastApplyMs;
                Assert.IsTrue(t.AllResidentWithinRadius(out worst), $"frame {i}: resident chunk {worst} away");
            }
            float avgMs = total / frames * 1000f;
            TestContext.Out.WriteLine($"[MERIDIAN] Load during measurement (D-019): {OtherHeavyJobs()}");
            var sorted = (double[])applyMs.Clone();
            System.Array.Sort(sorted);
            int over = 0;
            foreach (var a in applyMs) if (a > 2.0) over++;
            TestContext.Out.WriteLine($"[MERIDIAN] Terrain apply per frame: p50 {sorted[frames / 2]:F2} ms, p95 {sorted[frames * 95 / 100]:F2}, p99 {sorted[frames * 99 / 100]:F2}, frames over 2 ms: {over}/{frames}");
            TestContext.Out.WriteLine($"[MERIDIAN] Terrain streaming: avg {avgMs:F2} ms, worst frame {worstFrame * 1000f:F2} ms, max apply {t.MaxApplyMs:F2} ms, max band {t.MaxBandMs:F2} ms");
            Assert.LessOrEqual(avgMs, 12f, "average frame ≤ 12 ms while streaming");
            // Bible §11.1: chunk apply ≤ 2 ms per frame, no hitch > 33 ms during streaming. Asserted as p99 + hitch
            // because single OS stalls on the shared 8 GB laptop (one 20 ms band seen) are outside the code's control (P-06).
            Assert.LessOrEqual(sorted[frames * 99 / 100], 2.0, "chunk apply ≤ 2 ms in 99% of streaming frames");
            Assert.LessOrEqual(over, frames / 100, "at most 1% of frames over the 2 ms apply budget");
            Assert.Less(worstFrame * 1000f, 33f, "no hitch > 33 ms during streaming");

            yield return WaitSettled(t, 10f);
            Assert.AreEqual(25, t.ResidentCount);
            Assert.IsTrue(t.AllResidentWithinRadius(out worst));
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator SettledTerrainAllocatesNothingPerFrame()
        {
            PlanetSideRoot side = null;
            yield return BootEarth(s => side = s);
            yield return WaitSettled(side.terrain, 20f);
            for (int i = 0; i < 10; i++) yield return null;

            long before = System.GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 300; i++) yield return null;
            long allocated = System.GC.GetAllocatedBytesForCurrentThread() - before;
            TestContext.Out.WriteLine($"[MERIDIAN] GC over 300 settled frames: {allocated} bytes");
            Assert.LessOrEqual(allocated, 1024, "≤ 1 KB per 300 frames (Bible §11.1)");
        }
    }
}
