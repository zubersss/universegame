using System.Collections;
using Meridian.Player;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-091 test helper (D-089 "no hitch > 33 ms streaming at radius 3"): moves the side camera at run speed in REAL time
    /// (PlayerTuning.SprintSpeed, 6.5 m/s, whatever the frame rate) with CameraFollow off, so the terrain really streams at
    /// the speed a running surveyor forces. One helper serves ResidencyTests (headless) and BudgetGate (rendered).
    /// </summary>
    public static class RunSpeedStreaming
    {
        public struct StreamResult
        {
            public float worstMs, metres, seconds, metresPerSecond;
            public int frames, chunksCrossed;
            public override string ToString() => $"{metres:F0} m in {seconds:F1} s ({metresPerSecond:F1} m/s), {frames} frames, {chunksCrossed} chunks crossed, worst {worstMs:F1} ms";
        }

        public const float MinMetres = 96f, GuardSeconds = 60f, ChunkMetres = 32f;
        public const int MinFrames = 300, SkipFrames = 6;

        /// <summary>Runs right until at least MinMetres and MinFrames are covered (60 s guard); `renderFrame` (may be null) runs each frame before the yield.</summary>
        public static IEnumerator Run(Camera cam, TerrainStreamer t, System.Action renderFrame, System.Action<StreamResult> done)
        {
            var follow = cam.GetComponent<CameraFollow>();
            bool wasEnabled = follow != null && follow.enabled;
            if (follow != null) follow.enabled = false;
            var r = new StreamResult();
            float x0 = cam.transform.position.x, t0 = Time.realtimeSinceStartup;
            int lastChunk = Mathf.FloorToInt(x0 / ChunkMetres), frames = 0;
            while ((cam.transform.position.x - x0 < MinMetres || r.frames < MinFrames) && Time.realtimeSinceStartup - t0 < GuardSeconds)
            {
                float dt = Mathf.Min(Time.unscaledDeltaTime, 1f / 30f); // a long frame never teleports the camera past a chunk
                cam.transform.position += new Vector3(PlayerTuning.SprintSpeed * dt, 0f, 0f);
                renderFrame?.Invoke();
                yield return null;
                frames++;
                if (frames > SkipFrames) { r.frames++; r.worstMs = Mathf.Max(r.worstMs, Time.unscaledDeltaTime * 1000f); }
                int chunk = Mathf.FloorToInt(cam.transform.position.x / ChunkMetres);
                if (chunk != lastChunk) { r.chunksCrossed++; lastChunk = chunk; }
            }
            r.metres = cam.transform.position.x - x0;
            r.seconds = Time.realtimeSinceStartup - t0;
            r.metresPerSecond = r.seconds > 0f ? r.metres / r.seconds : 0f;
            if (follow != null) follow.enabled = wasEnabled;
            done(r);
        }

        /// <summary>Puts the camera 3 m over the original ground at its column and waits (≤ 5 s) for the terrain to settle there.</summary>
        public static IEnumerator ToSurface(Camera cam, TerrainStreamer t)
        {
            int x = Mathf.FloorToInt(cam.transform.position.x);
            cam.transform.position = new Vector3(x + 0.5f, t.OriginalTop(x) + 3f, cam.transform.position.z);
            float until = Time.realtimeSinceStartup + 5f;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
        }
    }
}
