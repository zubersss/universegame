using System.Collections.Generic;
using Unity.Profiling;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Meridian.Perf
{
    /// <summary>One reading of the Bible §11.1 budgets.</summary>
    public struct BudgetSnapshot
    {
        public float avgFrameMs, p99FrameMs, maxFrameMs;
        public int frames;
        public long drawCalls;            // last rendered frame; -1 when no graphics device
        public long triangles, shadowCasters; // U-077 (Bible §11.1 geometry row): last rendered frame; -1 when unavailable
        public long gcBytesLast300;       // managed bytes allocated on the main thread (gameplay code) over the window
        public long gcProfilerBytes;      // Unity "GC Allocated In Frame" counter over the window (in the Editor it includes Editor work)
        public int lightsVisible;         // 2D lights touching the camera view (global lights included)
        public int particlesAlive;
        public long systemMemoryMB, textureMemoryMB, audioMemoryMB; // -1 when the counter is unavailable
        public long meshMemoryMB;         // U-086 (v3): "Mesh Memory" counter
        public long workingSetMB;         // U-086 (v3): the OS working set of the process (ProcessMemory); -1 off Windows
        public long privateMB;            // U-091 (D-089): private commit (ProcessMemory.PrivateMB); page trimming cannot hide a leak in it
        public bool mipStreaming;         // U-091: QualitySettings.streamingMipmapsActive
        public long mipBudgetMB;          // U-091: QualitySettings.streamingMipmapsMemoryBudget
    }

    /// <summary>
    /// Runtime budget meter (Bible §11.1, U-014). Records frame times and GC per frame into fixed
    /// 300-frame rings (no per-frame allocation); counts lights and particles only when asked.
    /// Lives in Core. BudgetGateTests and tools/unity_profile.ps1 read it.
    /// </summary>
    public sealed class BudgetMonitor : MonoBehaviour
    {
        public const int Window = 300;
        public const float FrameBudgetMs = 16.6f, FrameTargetMs = 12f;
        public const int DrawCallsSide = 250, DrawCallsTop = 80; // v3 (D-077): 250 side view, 80 top-down
        public const int LightsTarget = 8, LightsHardCap = 12;
        public const int ParticlesCap = 1500; // v3 (D-077)
        /// <summary>U-077 (Bible §11.1, 3D): geometry per frame.</summary>
        public const long TrianglesCap = 500_000, ShadowCastersCap = 150; // v3 (D-077): 500 k
        public const long GcBytesPer300 = 1024;
        // U-091 (Bible §11.1 v4, D-089): the built game, Editor closed: working set < 2.0 GB (warning line 1.7), textures ≤ 512 MB,
        // audio ≤ 150 MB, ≤ 8 sprite atlases per planet, mip streaming budget 512 MB, planet load ≤ 5 s, transition ≤ 1.5 s,
        // no streaming hitch > 33 ms. Meshes are reported, not judged.
        public const long WorkingSetMB = 2048, WorkingSetWarnMB = 1741, TexturesMB = 512, AudioMB = 150;
        public const int AtlasesPerPlanet = 8, MipBudgetMB = 512;
        public const float PlanetLoadSeconds = 5f, TransitionSeconds = 1.5f, HitchMs = 33f;

        public static BudgetMonitor Instance { get; private set; }

        readonly float[] frameMs = new float[Window];
        readonly long[] gcBytes = new long[Window];
        readonly long[] gcProfiler = new long[Window];
        long lastThreadBytes = -1;
        readonly float[] sortScratch = new float[Window];
        int head, count;

        ProfilerRecorder draws, tris, casters, gcFrame, systemMem, textureMem, audioMem, meshMem;
        readonly List<Light2D> lights = new List<Light2D>();
        readonly List<ParticleSystem> particles = new List<ParticleSystem>();

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        void OnEnable()
        {
            draws = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count");
            tris = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Triangles Count");
            casters = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Shadow Casters Count");
            gcFrame = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame");
            systemMem = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "System Used Memory");
            textureMem = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "Texture Memory");
            audioMem = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "Audio Used Memory");
            meshMem = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "Mesh Memory");
        }

        void OnDisable()
        {
            draws.Dispose(); tris.Dispose(); casters.Dispose(); gcFrame.Dispose(); systemMem.Dispose(); textureMem.Dispose(); audioMem.Dispose(); meshMem.Dispose();
        }

        void OnDestroy() { if (Instance == this) Instance = null; }

        void Update()
        {
            frameMs[head] = Time.unscaledDeltaTime * 1000f;
            long now = System.GC.GetAllocatedBytesForCurrentThread();
            gcBytes[head] = lastThreadBytes < 0 ? 0 : now - lastThreadBytes;
            lastThreadBytes = now;
            gcProfiler[head] = gcFrame.Valid ? gcFrame.LastValue : 0;
            head = (head + 1) % Window;
            if (count < Window) count++;
        }

        /// <summary>Forget earlier frames (e.g. after a load) so the next reading covers only what follows.</summary>
        public void ResetWindow() { head = 0; count = 0; lastThreadBytes = System.GC.GetAllocatedBytesForCurrentThread(); }

        public int FramesRecorded => count;

        /// <summary>Takes a reading. Light and particle counts search the scene (call it from tests/tools, not per frame).</summary>
        /// <summary>U-091 (D-089 atlas row): loaded sprite atlases whose name starts with `planetGroup` (reports only: allocates).</summary>
        public static int LoadedAtlases(string planetGroup)
        {
            int n = 0;
            foreach (var a in Resources.FindObjectsOfTypeAll<UnityEngine.U2D.SpriteAtlas>())
                if (a != null && a.name.StartsWith(planetGroup, System.StringComparison.Ordinal)) n++;
            return n;
        }

        /// <summary>U-091: loaded sprites that are packed in an atlas; 0 while sprite packing is off (reports only: allocates).</summary>
        public static int PackedSprites()
        {
            int n = 0;
            foreach (var s in Resources.FindObjectsOfTypeAll<Sprite>()) if (s != null && s.packed) n++;
            return n;
        }

        public BudgetSnapshot Snapshot(Camera view)
        {
            var s = new BudgetSnapshot { frames = count };
            float sum = 0f, max = 0f;
            long gc = 0, gcp = 0;
            for (int i = 0; i < count; i++)
            {
                sum += frameMs[i];
                if (frameMs[i] > max) max = frameMs[i];
                gc += gcBytes[i];
                gcp += gcProfiler[i];
                sortScratch[i] = frameMs[i];
            }
            s.avgFrameMs = count > 0 ? sum / count : 0f;
            s.maxFrameMs = max;
            System.Array.Sort(sortScratch, 0, count);
            s.p99FrameMs = count > 0 ? sortScratch[Mathf.Min(count - 1, count * 99 / 100)] : 0f;
            s.gcBytesLast300 = gc;
            s.gcProfilerBytes = gcp;
            s.drawCalls = SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null ? -1 : (draws.Valid ? draws.LastValue : -1);
            s.triangles = s.drawCalls < 0 ? -1 : (tris.Valid ? tris.LastValue : -1);
            s.shadowCasters = s.drawCalls < 0 ? -1 : (casters.Valid ? casters.LastValue : -1);
            s.lightsVisible = CountVisibleLights(view);
            s.particlesAlive = CountParticles();
            s.systemMemoryMB = systemMem.Valid ? systemMem.LastValue / (1024 * 1024) : -1;
            s.textureMemoryMB = textureMem.Valid ? textureMem.LastValue / (1024 * 1024) : -1;
            s.audioMemoryMB = audioMem.Valid ? audioMem.LastValue / (1024 * 1024) : -1;
            s.meshMemoryMB = meshMem.Valid ? meshMem.LastValue / (1024 * 1024) : -1;
            s.workingSetMB = ProcessMemory.WorkingSetMB();
            s.privateMB = ProcessMemory.PrivateMB();
            s.mipStreaming = QualitySettings.streamingMipmapsActive;
            s.mipBudgetMB = (long)QualitySettings.streamingMipmapsMemoryBudget;
            return s;
        }

        int CountVisibleLights(Camera view)
        {
            lights.Clear();
            lights.AddRange(FindObjectsByType<Light2D>());
            if (view == null) return lights.Count;
            float h = Meridian.CameraRig.SideView.HalfHeight(view), w = h * view.aspect;
            var c = (Vector2)view.transform.position;
            var rect = new Rect(c.x - w, c.y - h, 2f * w, 2f * h);
            int n = 0;
            foreach (var l in lights)
            {
                if (!l.isActiveAndEnabled || l.intensity <= 0f) continue;
                if (l.lightType == Light2D.LightType.Global) { n++; continue; }
                float r = l.lightType == Light2D.LightType.Point ? l.pointLightOuterRadius : 2f;
                var p = (Vector2)l.transform.position;
                var bounds = new Rect(p.x - r, p.y - r, 2f * r, 2f * r);
                if (bounds.Overlaps(rect)) n++;
            }
            return n;
        }

        int CountParticles()
        {
            particles.Clear();
            particles.AddRange(FindObjectsByType<ParticleSystem>());
            int n = 0;
            foreach (var p in particles) n += p.particleCount;
            // U-033 sprite effects count as particles: pooled one-shots plus active loops.
            return n + Meridian.FX.FxPool.TotalAlive + Meridian.FX.FxLoop.ActiveCount;
        }
    }
}
