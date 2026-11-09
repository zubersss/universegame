using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Meridian.Core;
using Meridian.Ship;
using Meridian.Space;
using Meridian.Transitions;
using Meridian.UI;
using UnityEngine;

namespace Meridian.Perf
{
    /// <summary>
    /// U-041 (D-036): memory in a real (development) player. Started only by the command line
    /// `-meridianMemoryProbe &lt;file&gt;` (tools/unity_profile.ps1 -Build): skips the main menu, flies the nine-leg route
    /// with real launches and entries (U-091, D-089 / D-110 / D-114: Earth → Space → Earth (warm) → Space → Mars → Space →
    /// Mercury → Space → Venus → Space → Earth again), writes one JSON line per leg with the player's memory counters, the residency of the planet
    /// left behind, the planet-load and transition times, the loaded bundles and the mip-streaming figures, then quits.
    /// Normal play never creates it. Everything here is report-only and allocates in the probe only.
    /// </summary>
    public sealed class MemoryProbe : MonoBehaviour
    {
        public const string Arg = "-meridianMemoryProbe";
        /// <summary>Frames recorded per leg before reading the counters.</summary>
        public const int SettleFrames = 120;

        string path;
        readonly StringBuilder lines = new StringBuilder();
        SceneDirector director;
        TransitionDirector transitions;
        Camera spaceCam;
        SpaceShip spaceShip;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Boot()
        {
            string target = ArgValue(Arg);
            if (target == null) return;
            MenuController.ShowOnBootOverride = false; // straight into the world, like a batch test run
            var go = new GameObject("MemoryProbe");
            DontDestroyOnLoad(go);
            go.AddComponent<MemoryProbe>().path = target;
        }

        static string ArgValue(string name)
        {
            var args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++)
                if (args[i] == name) return args[i + 1];
            return null;
        }

        IEnumerator Start()
        {
            float deadline = Time.realtimeSinceStartup + 240f;
            while (director == null && Time.realtimeSinceStartup < deadline) { director = FindAnyObjectByType<SceneDirector>(); yield return null; }
            while (director != null && (!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < deadline) yield return null;
            if (director == null || !director.IsReady) { Finish("boot timed out"); yield break; }
            transitions = FindAnyObjectByType<TransitionDirector>();
            spaceCam = director.Space.GetComponentInChildren<Camera>(true);
            spaceShip = director.Space.GetComponentInChildren<SpaceShip>(true);
            if (transitions == null || spaceCam == null || spaceShip == null) { Finish("no transitions or space ship"); yield break; }

            // ---- Earth (boot) ----
            yield return Leg("Earth", director.PlanetSide.sideCamera, null, "planet_earth", -1f);

            // ---- D-114: the warm Earth baseline. One launch and re-entry so the Space scene (belt, discs, waystations, starfield)
            // is resident as it will be for the rest of the run; "Earth again" is judged against this leg, "Space again" against
            // the first Space leg, and the boot → warm delta is its own row (≤ 150 MB).
            yield return LaunchFrom();
            if (GameState.Instance.view != ViewMode.Space) { Finish("the first launch did not reach space"); yield break; }
            yield return Leg("Space", spaceCam, "planet_earth", null, transitions.LastLaunchSeconds);
            yield return EnterBody("earth");
            if (director.PlanetSide == null) { Finish("re-entry into Earth did not load a planet"); yield break; }
            yield return Leg("Earth (warm)", director.PlanetSide.sideCamera, null, "planet_earth", transitions.LastEntrySeconds);

            // ---- the loop: Mars, Mercury, Venus, back to Earth; a Space leg after every launch ----
            var hops = new[]
            {
                ("Space after Earth", "planet_earth", "mars", "Mars", "planet_mars"),
                ("Space after Mars", "planet_mars", "mercury", "Mercury", "planet_mercury"),
                ("Space after Mercury", "planet_mercury", "venus", "Venus", "planet_venus"),
                ("Space after Venus", "planet_venus", "earth", "Earth again", "planet_earth"),
                // U-112 (D-139): a second loop over Mars and Earth separates a one-time first-visit cost (shader programs, driver pools) from a per-visit creep:
                // the Creep row keeps D-116's four visits to Earth again; the second-loop row is (Earth again 2 − Earth again) / 2.
                ("Space after Earth again", "planet_earth", "mars", "Mars again", "planet_mars"),
                ("Space after Mars again", "planet_mars", "earth", "Earth again 2", "planet_earth"),
            };
            foreach (var (spaceLeg, prevGroup, body, planetLeg, ownGroup) in hops)
            {
                yield return LaunchFrom();
                if (GameState.Instance.view != ViewMode.Space) { Finish($"launch before {spaceLeg} did not reach space"); yield break; }
                yield return Leg(spaceLeg, spaceCam, prevGroup, null, transitions.LastLaunchSeconds);
                yield return EnterBody(body);
                if (director.PlanetSide == null) { Finish($"entry into {body} did not load a planet"); yield break; }
                yield return Leg(planetLeg, director.PlanetSide.sideCamera, prevGroup, ownGroup, transitions.LastEntrySeconds);
            }
            // U-148 (D-158): after the thirteen legs (so their memory figures stay comparable), a real climb on Earth timed frame by frame.
            yield return ClimbLeg("Climb Earth");
            Finish(null);
        }

        /// <summary>
        /// U-148 (D-158): the climb's frame times on Earth (at Earth again 2): boarded on the pad, 1.5 s for the ship frame to settle, then full
        /// thrust to the Escape Line; every frame's unscaled time until the launch iris starts, the iris's frames apart (its longest reported).
        /// One JSON line, judged by tools/unity_profile.ps1: p99 ≤ 20 ms and no frame over 50 ms outside the iris.
        /// </summary>
        IEnumerator ClimbLeg(string where)
        {
            var side = director.PlanetSide;
            if (side == null || side.ship == null) { lines.AppendLine($"{{\"leg\":\"{where}\",\"climbError\":\"no ship\"}}"); yield break; }
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            ship.intent = default;
            float until = Time.realtimeSinceStartup + 1.5f;
            while (Time.realtimeSinceStartup < until) yield return null;
            var climb = new List<float>(4096);
            float irisWorst = 0f, top = 0f, t0 = Time.realtimeSinceStartup;
            int irisFrames = 0;
            bool iris = false;
            ship.intent.thrust = 1f;
            float deadline = t0 + 150f;
            while (Time.realtimeSinceStartup < deadline)
            {
                yield return null;
                float ms = Time.unscaledDeltaTime * 1000f;
                if (transitions.Busy) { iris = true; irisFrames++; irisWorst = Mathf.Max(irisWorst, ms); continue; }
                if (iris) break; // the iris is over: in Space
                climb.Add(ms);
                if (ship != null && ship.Body != null) top = Mathf.Max(top, ship.Body.linearVelocity.magnitude);
            }
            var sorted = climb.ToArray();
            Array.Sort(sorted);
            float p99 = sorted.Length > 0 ? sorted[Mathf.Min(sorted.Length - 1, sorted.Length * 99 / 100)] : 0f;
            float worst = sorted.Length > 0 ? sorted[sorted.Length - 1] : 0f;
            int over50 = 0;
            foreach (var ms in sorted) if (ms > 50f) over50++;
            float seconds = 0f;
            foreach (var ms in climb) seconds += ms / 1000f;
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            lines.AppendLine($"{{\"leg\":\"{where}\",\"climbFrames\":{climb.Count},\"climbSeconds\":{seconds.ToString("F1", ci)},\"topSpeed\":{top.ToString("F1", ci)}," +
                             $"\"climbP99Ms\":{p99.ToString("F1", ci)},\"climbWorstMs\":{worst.ToString("F1", ci)},\"climbOver50\":{over50}," +
                             $"\"irisFrames\":{irisFrames},\"irisWorstMs\":{irisWorst.ToString("F1", ci)},\"reachedSpace\":{(GameState.Instance.view == ViewMode.Space ? "true" : "false")}}}");
        }

        /// <summary>Boards the Pilgrim, climbs through the Escape Line (a real launch), then parks the space ship outside the planet's well.</summary>
        IEnumerator LaunchFrom()
        {
            var side = director.PlanetSide;
            var planet = GameState.Instance.currentPlanet.ToString().ToLowerInvariant();
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p; ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            yield return BusyCycle(transitions, 15f);
            spaceShip.externalInput = true;
            spaceShip.intent = default;
            var body = spaceShip.world.Find(planet);
            if (body.HasValue)
            {
                spaceShip.Position = body.Value.position + new Vector2(0f, body.Value.WellRadius + 50f);
                spaceShip.Velocity = Vector2.zero;
            }
        }

        /// <summary>A real entry into `name` (BeginEntry from just outside its ring), then waits for the planet-load clock to stop.</summary>
        IEnumerator EnterBody(string name)
        {
            while (spaceShip.Invulnerable) yield return null;
            var body = spaceShip.world.Find(name);
            if (!body.HasValue) { Finish($"no body {name}"); yield break; }
            spaceShip.Position = body.Value.position + new Vector2(0f, body.Value.RingRadius + 60f);
            spaceShip.Velocity = Vector2.zero;
            transitions.BeginEntry(body.Value);
            yield return BusyCycle(transitions, 30f);
            float until = Time.realtimeSinceStartup + 10f;
            while (director.LastPlanetLoadSeconds < 0f && Time.realtimeSinceStartup < until) yield return null;
            var side = director.PlanetSide;
            until = Time.realtimeSinceStartup + 20f;
            while (side != null && !side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
        }

        static IEnumerator BusyCycle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

        /// <summary>
        /// One JSON line: the release wait for the previous planet (≤ 5 s), then GC + UnloadUnusedAssets, 120 frames, the
        /// counters, the D-089 figures (private commit, free RAM, planet load, transition, worst iris-in frame, own handles,
        /// atlases, packed sprites, mip streaming, loaded bundles by group).
        /// </summary>
        IEnumerator Leg(string where, Camera cam, string prevGroup, string ownGroup, float transitionSec)
        {
            var monitor = BudgetMonitor.Instance;
            if (monitor == null) { lines.AppendLine($"{{\"leg\":\"{where}\",\"error\":\"no BudgetMonitor\"}}"); yield break; }
            // U-086 (Bible §11.1 Residency): the previous planet's handles should be gone within 5 s of the switch.
            int prevHandles = -1;
            float prevWait = 0f;
            if (prevGroup != null)
            {
                float t0 = Time.realtimeSinceStartup;
                prevHandles = Residency.CountPlanet(prevGroup);
                while (prevHandles > 0 && Time.realtimeSinceStartup - t0 < 5f) { yield return null; prevHandles = Residency.CountPlanet(prevGroup); }
                prevWait = Time.realtimeSinceStartup - t0;
            }
            GC.Collect();
            yield return Resources.UnloadUnusedAssets();
            monitor.ResetWindow();
            for (int i = 0; i < SettleFrames; i++) yield return null;
            var s = monitor.Snapshot(cam);
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            float loadSec = ownGroup != null ? director.LastPlanetLoadSeconds : -1f;
            int ownHandles = ownGroup != null ? Residency.CountPlanet(ownGroup) : -1;
            int atlases = ownGroup != null ? BudgetMonitor.LoadedAtlases(ownGroup) : 0;
            string holders = prevGroup != null ? Residency.Holders(prevGroup).Replace("\"", "'") : "";
            string breakdown = ((director.LastLoadBreakdown ?? "") + (string.IsNullOrEmpty(director.LastLoadPending) ? "" : "; " + director.LastLoadPending)).Replace("\"", "'"); // U-120: what was still loading at the settle
            // U-112 (D-116): where a per-visit creep can live: the Mono heap, the native allocator, and the counts that grow per visit.
            long monoUsedMB = UnityEngine.Profiling.Profiler.GetMonoUsedSizeLong() >> 20, monoHeapMB = UnityEngine.Profiling.Profiler.GetMonoHeapSizeLong() >> 20;
            long allocMB = UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong() >> 20, reservedMB = UnityEngine.Profiling.Profiler.GetTotalReservedMemoryLong() >> 20;
            long unusedMB = UnityEngine.Profiling.Profiler.GetTotalUnusedReservedMemoryLong() >> 20;
            int handlesHeld = Residency.Total;
            // U-112 (D-139): what the allocators do not count — the graphics driver's memory — and the loaded textures / meshes / shaders / materials by count and size, and the sets held.
            long gfxMB = UnityEngine.Profiling.Profiler.GetAllocatedMemoryForGraphicsDriver() >> 20;
            CountAndSize<Texture>(out int texCount, out long texSizeMB);
            CountAndSize<Mesh>(out int meshCount, out long meshSizeMB);
            int shaders = Resources.FindObjectsOfTypeAll<Shader>().Length, materials = Resources.FindObjectsOfTypeAll<Material>().Length, animClips = Resources.FindObjectsOfTypeAll<AnimationClip>().Length;
            string held = Residency.HeldKeys().Replace("\"", "'");
            int gameObjects = Resources.FindObjectsOfTypeAll<GameObject>().Length;
            int tmpObjects = Resources.FindObjectsOfTypeAll<TMPro.TMP_Text>().Length;
            int audioSources = Resources.FindObjectsOfTypeAll<AudioSource>().Length;
            lines.AppendLine($"{{\"leg\":\"{where}\",\"systemMB\":{s.systemMemoryMB},\"textureMB\":{s.textureMemoryMB},\"audioMB\":{s.audioMemoryMB}," +
                             $"\"avgFrameMs\":{s.avgFrameMs.ToString("F2", ci)}," +
                             $"\"workingSetMB\":{s.workingSetMB},\"privateMB\":{s.privateMB},\"freeMB\":{ProcessMemory.FreeSystemMB()},\"meshMB\":{s.meshMemoryMB}," +
                             $"\"resident\":\"{Residency.ResidentGroups()}\",\"prevGroup\":\"{prevGroup}\",\"prevHandles\":{prevHandles},\"holders\":\"{holders}\",\"prevWait\":{prevWait.ToString("F1", ci)}," +
                             $"\"ownGroup\":\"{ownGroup}\",\"ownHandles\":{ownHandles},\"loadSec\":{loadSec.ToString("F2", ci)},\"transitionSec\":{transitionSec.ToString("F2", ci)}," +
                             $"\"irisInWorstMs\":{transitions.LastIrisInWorstMs.ToString("F1", ci)},\"breakdown\":\"{breakdown}\"," +
                             $"\"atlases\":{atlases},\"packedSprites\":{BudgetMonitor.PackedSprites()},\"mipActive\":{(s.mipStreaming ? 1 : 0)},\"mipBudgetMB\":{s.mipBudgetMB}," +
                             $"\"nonStreamingMB\":{(long)(Texture.nonStreamingTextureMemory / 1048576UL)},\"desiredMB\":{(long)(Texture.desiredTextureMemory / 1048576UL)},\"targetMB\":{(long)(Texture.targetTextureMemory / 1048576UL)}," +
                             $"\"monoUsedMB\":{monoUsedMB},\"monoHeapMB\":{monoHeapMB},\"allocMB\":{allocMB},\"reservedMB\":{reservedMB},\"unusedReservedMB\":{unusedMB}," +
                             $"\"handlesHeld\":{handlesHeld},\"gameObjects\":{gameObjects},\"tmpObjects\":{tmpObjects},\"audioSources\":{audioSources}," +
                             $"\"gfxMB\":{gfxMB},\"texCount\":{texCount},\"texSizeMB\":{texSizeMB},\"meshCount\":{meshCount},\"meshSizeMB\":{meshSizeMB},\"shaders\":{shaders},\"materials\":{materials},\"animClips\":{animClips},\"held\":\"{held}\"," +
                             $"\"bundles\":\"{Bundles()}\"}}");
            TopTextures(where, 15);
            if (where == "Earth") yield return FilmGpu(where); // U-095: the film pass's GPU cost at 1080p
        }

        /// <summary>U-112: the loaded objects of a type and their runtime memory in MB (Profiler.GetRuntimeMemorySizeLong; reports only: allocates).</summary>
        static void CountAndSize<T>(out int count, out long sizeMB) where T : UnityEngine.Object
        {
            var all = Resources.FindObjectsOfTypeAll<T>();
            long bytes = 0;
            foreach (var o in all) bytes += UnityEngine.Profiling.Profiler.GetRuntimeMemorySizeLong(o);
            count = all.Length;
            sizeMB = bytes >> 20;
        }

        /// <summary>
        /// U-091: the Addressables groups of the loaded bundles (m_InternalBundleIdMode 1 hashes bundle names, so the group
        /// is recovered from the first art asset inside each bundle; a bundle with no parseable entry reports its own name).
        /// </summary>
        static string Bundles()
        {
            var groups = new List<string>();
            foreach (var b in AssetBundle.GetAllLoadedAssetBundles())
            {
                string g = null;
                foreach (var n in b.GetAllAssetNames()) { g = GroupFromAssetName(n); if (g != null) break; }
                if (g == null) foreach (var n in b.GetAllScenePaths()) { g = GroupFromAssetName(n); if (g != null) break; }
                g ??= b.name;
                if (!groups.Contains(g)) groups.Add(g);
            }
            groups.Sort(string.CompareOrdinal);
            return string.Join(", ", groups);
        }

        static readonly string[] ArtRoots = { "/_game/art/", "/_game/placeholders/" };
        static readonly string[] MapSuffixes = { "_color", "_normal", "_emission", "_mask" };

        static string GroupFromAssetName(string assetName)
        {
            var n = assetName.ToLowerInvariant();
            foreach (var root in ArtRoots)
            {
                int i = n.IndexOf(root, StringComparison.Ordinal);
                if (i < 0) continue;
                var rel = n.Substring(i + root.Length);
                int dot = rel.LastIndexOf('.');
                if (dot > 0) rel = rel.Substring(0, dot);
                foreach (var suffix in MapSuffixes)
                    if (rel.EndsWith(suffix, StringComparison.Ordinal)) { rel = rel.Substring(0, rel.Length - suffix.Length); break; }
                return Meridian.Art.ArtKeys.GroupOf(rel);
            }
            return null;
        }

        /// <summary>
        /// U-095, D-180: the film pass's GPU cost at 1080p (Bible §9.4: ≤ 0.6 ms) from FrameTimingManager (Frame Timing Stats on), measured
        /// interleaved: blocks of FilmBlockFrames frames with the pass on, then off (30 warm-up frames after each switch), FilmPairsMin pairs,
        /// more (up to FilmPairsMax) while the paired differences spread over FilmSpreadMs; the pass is the median of the paired differences
        /// (on − off), so drift between the halves (the GPU shares system RAM) cancels instead of landing in one difference. One JSON line
        /// with every block.
        /// </summary>
        IEnumerator FilmGpu(string where)
        {
            bool before = Meridian.Core.GameSettings.FilmEffects;
            var ons = new List<float>(FilmPairsMax);
            var offs = new List<float>(FilmPairsMax);
            var diffs = new List<float>(FilmPairsMax);
            while (diffs.Count < FilmPairsMin || (Spread(diffs) > FilmSpreadMs && diffs.Count < FilmPairsMax))
            {
                float on = 0f, off = 0f;
                yield return FilmGpuAverage(true, v => on = v);
                yield return FilmGpuAverage(false, v => off = v);
                ons.Add(on); offs.Add(off); diffs.Add(on - off);
            }
            Meridian.Core.GameSettings.FilmEffects = before;
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            string Arr(List<float> l) { var sb = new StringBuilder("["); for (int i = 0; i < l.Count; i++) { if (i > 0) sb.Append(','); sb.Append(l[i].ToString("F3", ci)); } return sb.Append(']').ToString(); }
            lines.AppendLine($"{{\"leg\":\"{where}\",\"filmGpuOnMs\":{Mean(ons).ToString("F3", ci)},\"filmGpuOffMs\":{Mean(offs).ToString("F3", ci)},\"filmPassMs\":{Median(diffs).ToString("F3", ci)},\"filmSpreadMs\":{Spread(diffs).ToString("F3", ci)},\"filmOn\":{Arr(ons)},\"filmOff\":{Arr(offs)},\"filmDiffs\":{Arr(diffs)},\"filmBlockFrames\":{FilmBlockFrames},\"width\":{Screen.width},\"height\":{Screen.height}}}");
        }

        /// <summary>D-180: frames per block, the pairs taken (at least, at most), and the spread of the pairs' differences that asks for more.</summary>
        public const int FilmBlockFrames = 300, FilmPairsMin = 4, FilmPairsMax = 8;
        public const float FilmSpreadMs = 0.3f;

        /// <summary>The median (the mean of the middle two for an even count). Pure.</summary>
        public static float Median(IList<float> values)
        {
            int n = values.Count;
            if (n == 0) return 0f;
            var s = new List<float>(values);
            s.Sort();
            return n % 2 == 1 ? s[n / 2] : 0.5f * (s[n / 2 - 1] + s[n / 2]);
        }

        /// <summary>Largest minus smallest (0 for none). Pure.</summary>
        public static float Spread(IList<float> values)
        {
            if (values.Count == 0) return 0f;
            float lo = values[0], hi = values[0];
            for (int i = 1; i < values.Count; i++) { lo = Mathf.Min(lo, values[i]); hi = Mathf.Max(hi, values[i]); }
            return hi - lo;
        }

        static float Mean(List<float> values) { float t = 0f; foreach (var v in values) t += v; return values.Count > 0 ? t / values.Count : 0f; }

        IEnumerator FilmGpuAverage(bool film, Action<float> result)
        {
            Meridian.Core.GameSettings.FilmEffects = film;
            for (int i = 0; i < 30; i++) yield return null;
            var timings = new FrameTiming[1];
            double sum = 0; int n = 0;
            for (int i = 0; i < FilmBlockFrames; i++)
            {
                yield return null;
                FrameTimingManager.CaptureFrameTimings();
                if (FrameTimingManager.GetLatestTimings(1, timings) == 1 && timings[0].gpuFrameTime > 0) { sum += timings[0].gpuFrameTime; n++; }
            }
            result(n > 0 ? (float)(sum / n) : 0f);
        }

        /// <summary>U-060 diagnosis: the largest loaded textures at this leg (name, size, format, MB), one JSON line.</summary>
        void TopTextures(string where, int count)
        {
            var all = Resources.FindObjectsOfTypeAll<Texture>();
            var sizes = new long[all.Length];
            for (int i = 0; i < all.Length; i++) sizes[i] = UnityEngine.Profiling.Profiler.GetRuntimeMemorySizeLong(all[i]);
            var order = new int[all.Length];
            for (int i = 0; i < order.Length; i++) order[i] = i;
            Array.Sort(order, (a, b) => sizes[b].CompareTo(sizes[a]));
            var sb = new StringBuilder();
            sb.Append($"{{\"leg\":\"{where}\",\"textures\":{all.Length},\"top\":[");
            for (int k = 0; k < Math.Min(count, order.Length); k++)
            {
                var t = all[order[k]];
                string fmt = t is Texture2D t2 ? t2.format.ToString() : t.GetType().Name;
                string name = (t.name ?? "").Replace("\"", "'");
                if (k > 0) sb.Append(',');
                sb.Append($"\"{name} {t.width}x{t.height} {fmt} {sizes[order[k]] / (1024 * 1024)}MB\"");
            }
            sb.Append("]}");
            lines.AppendLine(sb.ToString());
        }

        void Finish(string error)
        {
            if (error != null) lines.AppendLine($"{{\"error\":\"{error}\"}}");
            try { File.WriteAllText(path, lines.ToString()); }
            catch (Exception e) { Debug.LogError($"[MemoryProbe] could not write {path}: {e.Message}"); }
            Application.Quit(error == null ? 0 : 1);
        }
    }
}
