using System.Collections;
using System.Collections.Generic;
using Meridian.Core;
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
    /// U-211 (D-201): WHICH SCRIPT allocates in the scenes BudgetGate reads red on the live counter (Space, Mars, Mars' dust storm).
    /// A reading for the perf report, not a bar. The gate's own route (launch from Earth, park outside Earth's well; entry to Mars;
    /// the forced storm); in each scene a base reading, then every script TYPE in turn switched off for a short window and back on
    /// (leave one out): a type's share is how far the frame's bytes fall without it. Unity's "GC Allocated In Frame" after a
    /// control; the Editor's and the runner's own floor is about 290 B a frame. Runs only when MERIDIAN_ALLOC_DIAG is set (it
    /// switches scripts off and on in a live scene: not a sweep's row).
    /// </summary>
    public class AllocByTypeTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        /// <summary>Not switched off: the scene's own directors and state (their OnDisable / OnEnable would change the scene measured).</summary>
        static readonly HashSet<string> Keep = new HashSet<string>
        {
            "SceneDirector", "TransitionDirector", "GameState", "SaveSystem", "BudgetMonitor", "PlanetSideRoot", "SpaceRoot", "TimeSystem",
            "UniversalAdditionalCameraData", "PlaymodeTestsController",
        };

        static IEnumerator WaitBusyCycle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

        string saveRoot;

        // D-203: this class flies a launch and an entry and each one autosaves: into a folder of its own (as BudgetGateTests does).
        [SetUp]
        public void SetUp()
        {
            saveRoot = System.IO.Path.Combine(Application.temporaryCachePath, "meridian_saves_alloctype_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            Meridian.Save.SaveSystem.RootOverride = saveRoot;
        }

        [TearDown]
        public void TearDown()
        {
            Meridian.Save.SaveSystem.RootOverride = null;
            if (System.IO.Directory.Exists(saveRoot)) System.IO.Directory.Delete(saveRoot, true);
        }

        [UnityTest, Timeout(600000)]
        public IEnumerator WhichScriptAllocatesInSpaceAndOnMars()
        {
            if (string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("MERIDIAN_ALLOC_DIAG"))) Assert.Ignore("Set MERIDIAN_ALLOC_DIAG to run the allocation-by-type diagnostic.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            var side = director.PlanetSide;
            bool ignoreWas = LogAssert.ignoreFailingMessages;
            LogAssert.ignoreFailingMessages = true; // a script switched off can make another complain: the reading goes on
            try
            {
                using (var gc = Unity.Profiling.ProfilerRecorder.StartNew(Unity.Profiling.ProfilerCategory.Memory, "GC Allocated In Frame"))
                {
                    Assert.IsTrue(gc.Valid, "Unity's 'GC Allocated In Frame' counter is there");
                    for (int i = 0; i < 3; i++) yield return null;
                    var known = new byte[65536];
                    long seenKnown = 0;
                    for (int i = 0; i < 3; i++) { yield return null; seenKnown = System.Math.Max(seenKnown, gc.LastValue); }
                    System.GC.KeepAlive(known);
                    Assert.GreaterOrEqual(seenKnown, 65536L, "the control: the counter sees a 64 KB array in the frame it is made");

                    long avg = 0, least = 0, most = 0, median = 0; int busy = 0;
                    var window = new long[600];
                    IEnumerator Read(int frames)
                    {
                        for (int i = 0; i < 4; i++) yield return null; // the counter reads a frame late; let the change land
                        long sum = 0; least = long.MaxValue; most = 0; busy = 0;
                        for (int i = 0; i < frames; i++) { yield return null; long v = gc.LastValue; window[i] = v; sum += v; least = System.Math.Min(least, v); most = System.Math.Max(most, v); }
                        avg = sum / frames;
                        System.Array.Sort(window, 0, frames);
                        median = window[frames / 2];
                        for (int i = 0; i < frames; i++) if (window[i] > least + 64) busy++;
                    }

                    IEnumerator LeaveOneOut(string scene)
                    {
                        yield return Read(300);
                        long baseAvg = avg, baseLeast = least, baseMost = most, baseMedian = median; int baseBusy = busy;
                        var groups = new SortedDictionary<string, List<MonoBehaviour>>(System.StringComparer.Ordinal);
                        foreach (var m in Object.FindObjectsByType<MonoBehaviour>())
                        {
                            if (m == null || !m.isActiveAndEnabled) continue;
                            var type = m.GetType();
                            string ns = type.Namespace ?? "";
                            if (Keep.Contains(type.Name) || ns.Contains("TestTools") || ns.Contains("TestRunner") || ns.StartsWith("Meridian.Tests")) continue;
                            string key = (ns.StartsWith("Meridian") ? "" : "~") + type.FullName; // the game's own first, the engine's after
                            if (!groups.TryGetValue(key, out var list)) groups[key] = list = new List<MonoBehaviour>();
                            list.Add(m);
                        }
                        var found = new List<(long saved, string line)>();
                        int types = 0;
                        foreach (var g in groups)
                        {
                            types++;
                            foreach (var m in g.Value) if (m != null) m.enabled = false;
                            yield return Read(40);
                            foreach (var m in g.Value) if (m != null) m.enabled = true;
                            long saved = baseAvg - avg;
                            if (System.Math.Abs(saved) >= 24) found.Add((saved, $"{g.Key.TrimStart('~')} x{g.Value.Count}: {(saved > 0 ? "-" : "+")}{System.Math.Abs(saved)} B a frame without it (avg {avg}, least {least}, most {most})"));
                            for (int i = 0; i < 2; i++) yield return null;
                        }
                        yield return Read(300);
                        found.Sort((a, b) => b.saved.CompareTo(a.saved));
                        var sb = new System.Text.StringBuilder();
                        foreach (var f in found) sb.Append("\n    ").Append(f.line);
                        TestContext.Out.WriteLine($"[MERIDIAN] alloc by type · {scene}: base avg {baseAvg} B a frame (least {baseLeast}, median {baseMedian}, most {baseMost}; {baseBusy} of 300 frames over the least + 64 B); after the pass avg {avg} (least {least}, median {median}, most {most}; {busy} busy frames); {types} script types switched off in turn, 40 frames each; the ones that move the frame by 24 B or more:{(found.Count == 0 ? " none" : sb.ToString())}");
                    }

                    // ---- Launch → Space, parked outside Earth's well (the gate's own steps) ----
                    var transitions = Object.FindAnyObjectByType<TransitionDirector>();
                    var ship = side.ship;
                    ship.GetComponent<ShipBoarding>().ForceAboard();
                    ship.externalInput = true;
                    var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
                    ship.Body.position = p; ship.transform.position = p;
                    ship.Body.linearVelocity = new Vector2(0f, 12f);
                    yield return WaitBusyCycle(transitions, 10f);
                    var spaceShip = director.Space.GetComponentInChildren<SpaceShip>();
                    spaceShip.externalInput = true;
                    spaceShip.intent = default;
                    var earth = spaceShip.world.Find("earth").Value;
                    spaceShip.Position = earth.position + new Vector2(0f, earth.WellRadius + 50f);
                    spaceShip.Velocity = Vector2.zero;
                    Assert.AreEqual(ViewMode.Space, GameState.Instance.view, "in Space");
                    for (int i = 0; i < 60; i++) yield return null;
                    yield return LeaveOneOut("Space (parked outside Earth's well)");
                    Assert.AreEqual(ViewMode.Space, GameState.Instance.view, "still in Space after the pass");

                    // ---- Entry → Mars ----
                    while (spaceShip.Invulnerable) yield return null;
                    spaceShip.externalInput = true; spaceShip.intent = default;
                    var mars = spaceShip.world.Find("mars").Value;
                    spaceShip.Position = mars.position + new Vector2(0f, mars.RingRadius + 0.5f);
                    spaceShip.Velocity = new Vector2(0f, -40f);
                    yield return WaitBusyCycle(transitions, 15f);
                    side = director.PlanetSide;
                    Assert.NotNull(side, "entered a planet");
                    Assert.AreEqual(Meridian.Planets.PlanetId.Mars, side.Config.id);
                    while (!side.terrain.IsSettled) yield return null;
                    for (int i = 0; i < 120; i++) yield return null;
                    yield return LeaveOneOut("Mars (after the entry, settled)");

                    // ---- Mars in a full dust storm ----
                    var storm = side.dustStorm;
                    var clock = Object.FindAnyObjectByType<TimeSystem>();
                    storm.Force(0.1f, 300f);
                    clock.Advance(0.1f + Meridian.Planet.Weather.DustStorm.RampRealSeconds + 1f);
                    for (int i = 0; i < 30; i++) yield return null;
                    yield return LeaveOneOut($"Mars dust storm (intensity {storm.Intensity:0.00})");
                }
            }
            finally { LogAssert.ignoreFailingMessages = ignoreWas; }
        }
    }
}
