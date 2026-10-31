using System;
using System.Collections;
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
    /// `-meridianMemoryProbe &lt;file&gt;` (tools/unity_profile.ps1 -Build): skips the main menu, runs the
    /// BudgetGate route (Earth, launch, Space, entry, Mars), writes one JSON line per leg with the
    /// player's system, texture and audio memory (the same ProfilerRecorder counters BudgetMonitor
    /// reads in the Editor), then quits. Normal play never creates it.
    /// </summary>
    public sealed class MemoryProbe : MonoBehaviour
    {
        public const string Arg = "-meridianMemoryProbe";
        /// <summary>Frames recorded per leg before reading the counters.</summary>
        public const int SettleFrames = 120;

        string path;
        readonly StringBuilder lines = new StringBuilder();

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
            SceneDirector director = null;
            while (director == null && Time.realtimeSinceStartup < deadline) { director = FindAnyObjectByType<SceneDirector>(); yield return null; }
            while (director != null && (!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < deadline) yield return null;
            if (director == null || !director.IsReady) { Finish("boot timed out"); yield break; }

            // ---- Earth ----
            var side = director.PlanetSide;
            yield return Leg("Earth", side.sideCamera);

            // ---- Launch → Space ----
            var transitions = FindAnyObjectByType<TransitionDirector>();
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p; ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            yield return BusyCycle(transitions, 15f);
            var spaceCam = director.Space.GetComponentInChildren<Camera>();
            var spaceShip = director.Space.GetComponentInChildren<SpaceShip>();
            spaceShip.externalInput = true;
            spaceShip.intent = default;
            var earth = spaceShip.world.Find("earth").Value;
            spaceShip.Position = earth.position + new Vector2(0f, earth.WellRadius + 50f);
            spaceShip.Velocity = Vector2.zero;
            yield return Leg("Space", spaceCam);

            // ---- Entry → Mars ----
            while (spaceShip.Invulnerable) yield return null;
            var mars = spaceShip.world.Find("mars").Value;
            spaceShip.Position = mars.position + new Vector2(0f, mars.RingRadius + 0.5f);
            spaceShip.Velocity = new Vector2(0f, -40f);
            yield return BusyCycle(transitions, 20f);
            var marsSide = director.PlanetSide;
            float until = Time.realtimeSinceStartup + 20f;
            while (!marsSide.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            yield return Leg("Mars", marsSide.sideCamera);
            Finish(null);
        }

        static IEnumerator BusyCycle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

        IEnumerator Leg(string where, Camera cam)
        {
            var monitor = BudgetMonitor.Instance;
            if (monitor == null) { lines.AppendLine($"{{\"leg\":\"{where}\",\"error\":\"no BudgetMonitor\"}}"); yield break; }
            monitor.ResetWindow();
            for (int i = 0; i < SettleFrames; i++) yield return null;
            var s = monitor.Snapshot(cam);
            lines.AppendLine($"{{\"leg\":\"{where}\",\"systemMB\":{s.systemMemoryMB},\"textureMB\":{s.textureMemoryMB},\"audioMB\":{s.audioMemoryMB}," +
                             $"\"avgFrameMs\":{s.avgFrameMs.ToString("F2", System.Globalization.CultureInfo.InvariantCulture)}," +
                             $"\"workingSetMB\":{System.Diagnostics.Process.GetCurrentProcess().WorkingSet64 / (1024 * 1024)}}}");
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
