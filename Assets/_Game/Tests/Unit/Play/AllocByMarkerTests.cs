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
    /// U-211 (D-201; the card: "a Profiler capture"): WHAT allocates, by the Profiler's own samples. The Editor's profiler records a
    /// window of frames; each frame's hierarchy is read back and every leaf that holds managed allocation is summed by its path
    /// (a script's callback shows as "Type.Update() [Invoke]" over its "GC.Alloc"). The gate's route: Space parked outside Earth's
    /// well; Mars from the frame its terrain settles (the gate's own window) and again later; a reading for the perf report, not
    /// a bar. Editor only; runs only when MERIDIAN_ALLOC_DIAG is set.
    /// </summary>
    public class AllocByMarkerTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string saveRoot;

        // D-203: this class flies a launch and an entry and each one autosaves: into a folder of its own (as BudgetGateTests does).
        [SetUp]
        public void SetUp()
        {
            saveRoot = System.IO.Path.Combine(Application.temporaryCachePath, "meridian_saves_allocmarker_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            Meridian.Save.SaveSystem.RootOverride = saveRoot;
        }

        [TearDown]
        public void TearDown()
        {
            Meridian.Save.SaveSystem.RootOverride = null;
            if (System.IO.Directory.Exists(saveRoot)) System.IO.Directory.Delete(saveRoot, true);
        }

        static IEnumerator WaitBusyCycle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

#if UNITY_EDITOR
        internal static void BeginCapture()
        {
            UnityEditorInternal.ProfilerDriver.ClearAllFrames();
            UnityEditorInternal.ProfilerDriver.profileEditor = false;
            UnityEngine.Profiling.Profiler.enabled = true;
            UnityEditorInternal.ProfilerDriver.enabled = true;
        }

        /// <summary>Stops the capture and writes its managed allocation by sample path (the last `tail` names of each path), the
        /// `top` largest; with `times`, the frame of the window whose `timeUnder` sample ran longest, by its children's time.</summary>
        internal static void EndCapture(string label, int top = 14, int tail = 3, string timeUnder = null)
        {
            UnityEditorInternal.ProfilerDriver.enabled = false;
            UnityEngine.Profiling.Profiler.enabled = false;
            int first = UnityEditorInternal.ProfilerDriver.firstFrameIndex, last = UnityEditorInternal.ProfilerDriver.lastFrameIndex;
            var bytesOf = new Dictionary<string, long>(); var framesOf = new Dictionary<string, int>(); var mostOf = new Dictionary<string, long>();
            var children = new List<int>(); var stack = new Stack<int>();
            int read = 0; long all = 0, worstFrameBytes = 0; int worstFrame = -1;
            double slowest = 0; int slowestFrame = -1;
            for (int f = first; f <= last && f >= 0; f++)
            for (int thread = 0; thread < 96; thread++) // every thread: Unity's counter counts them all (a worker's managed allocation too)
            {
                using (var view = UnityEditorInternal.ProfilerDriver.GetHierarchyFrameDataView(f, thread, UnityEditor.Profiling.HierarchyFrameDataView.ViewModes.MergeSamplesWithTheSameName, UnityEditor.Profiling.HierarchyFrameDataView.columnGcMemory, false))
                {
                    if (view == null || !view.valid) break;
                    string threadName = thread == 0 ? null : view.threadName;
                    if (thread == 0) read++;
                    int root = view.GetRootItemID();
                    long frameBytes = 0;
                    stack.Clear(); stack.Push(root);
                    while (stack.Count > 0)
                    {
                        int id = stack.Pop();
                        view.GetItemChildren(id, children);
                        bool deeper = false;
                        for (int c = 0; c < children.Count; c++)
                        {
                            if (timeUnder != null && thread == 0 && view.GetItemName(children[c]) == timeUnder)
                            {
                                double ms = view.GetItemColumnDataAsFloat(children[c], UnityEditor.Profiling.HierarchyFrameDataView.columnTotalTime);
                                if (ms > slowest) { slowest = ms; slowestFrame = f; }
                            }
                            if (view.GetItemColumnDataAsFloat(children[c], UnityEditor.Profiling.HierarchyFrameDataView.columnGcMemory) > 0f) { deeper = true; stack.Push(children[c]); }
                            else if (timeUnder != null) stack.Push(children[c]); // the time search walks everything
                        }
                        if (deeper || id == root) continue;
                        long b = (long)view.GetItemColumnDataAsFloat(id, UnityEditor.Profiling.HierarchyFrameDataView.columnGcMemory);
                        if (b <= 0) continue;
                        string path = view.GetItemPath(id);
                        var parts = path.Split('/');
                        string key = parts.Length <= tail ? path : string.Join(" / ", parts, parts.Length - tail, tail);
                        if (threadName != null) key = $"[thread {threadName}] {key}";
                        bytesOf.TryGetValue(key, out long sum); bytesOf[key] = sum + b;
                        framesOf.TryGetValue(key, out int n); framesOf[key] = n + 1;
                        mostOf.TryGetValue(key, out long most); if (b > most) mostOf[key] = b;
                        frameBytes += b; all += b;
                    }
                    if (frameBytes > worstFrameBytes) { worstFrameBytes = frameBytes; worstFrame = f - first; }
                }
            }
            var keys = new List<string>(bytesOf.Keys);
            keys.Sort((a, b) => bytesOf[b].CompareTo(bytesOf[a]));
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < keys.Count && i < top; i++)
                sb.Append($"\n    {bytesOf[keys[i]],9} B in {framesOf[keys[i]],3} frame(s) (the most in one {mostOf[keys[i]]}): {keys[i]}");
            if (keys.Count > top) sb.Append($"\n    … and {keys.Count - top} smaller paths");
            TestContext.Out.WriteLine($"[MERIDIAN] alloc by marker · {label}: {read} frames read ({first}-{last}); {all} B in all, every thread ({(read > 0 ? all / read : 0)} B a frame); the worst frame on one thread {worstFrameBytes} B (frame {worstFrame} of the window); by path:{(keys.Count == 0 ? " nothing allocated" : sb.ToString())}");
            if (timeUnder == null || slowestFrame < 0) return;
            // the slowest frame of `timeUnder`: its children by time
            using (var view = UnityEditorInternal.ProfilerDriver.GetHierarchyFrameDataView(slowestFrame, 0, UnityEditor.Profiling.HierarchyFrameDataView.ViewModes.MergeSamplesWithTheSameName, UnityEditor.Profiling.HierarchyFrameDataView.columnTotalTime, false))
            {
                var lines = new System.Text.StringBuilder();
                stack.Clear(); stack.Push(view.GetRootItemID());
                while (stack.Count > 0)
                {
                    int id = stack.Pop();
                    view.GetItemChildren(id, children);
                    for (int c = 0; c < children.Count; c++)
                    {
                        if (view.GetItemName(children[c]) != timeUnder) { stack.Push(children[c]); continue; }
                        var under = new List<int>();
                        Describe(view, children[c], 0, lines, under);
                    }
                }
                TestContext.Out.WriteLine($"[MERIDIAN] time by marker · {label}: the frame where '{timeUnder}' ran longest ({slowest:F3} ms, frame {slowestFrame - first} of the window):{lines}");
            }
        }

        static void Describe(UnityEditor.Profiling.HierarchyFrameDataView view, int id, int depth, System.Text.StringBuilder lines, List<int> scratch)
        {
            if (depth > 5) return;
            float total = view.GetItemColumnDataAsFloat(id, UnityEditor.Profiling.HierarchyFrameDataView.columnTotalTime);
            float self = view.GetItemColumnDataAsFloat(id, UnityEditor.Profiling.HierarchyFrameDataView.columnSelfTime);
            float calls = view.GetItemColumnDataAsFloat(id, UnityEditor.Profiling.HierarchyFrameDataView.columnCalls);
            if (depth > 0 && total < 0.02f) return;
            lines.Append($"\n    {new string(' ', depth * 2)}{view.GetItemName(id)}: {total:F3} ms (self {self:F3}, {calls:F0} call(s))");
            var kids = new List<int>();
            view.GetItemChildren(id, kids);
            kids.Sort((a, b) => view.GetItemColumnDataAsFloat(b, UnityEditor.Profiling.HierarchyFrameDataView.columnTotalTime).CompareTo(view.GetItemColumnDataAsFloat(a, UnityEditor.Profiling.HierarchyFrameDataView.columnTotalTime)));
            for (int i = 0; i < kids.Count && i < 8; i++) Describe(view, kids[i], depth + 1, lines, scratch);
        }
#endif

        [UnityTest, Timeout(600000)]
        public IEnumerator WhatAllocatesInSpaceAndOnMars()
        {
            if (string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("MERIDIAN_ALLOC_DIAG"))) Assert.Ignore("Set MERIDIAN_ALLOC_DIAG to run the allocation-by-marker diagnostic.");
#if !UNITY_EDITOR
            Assert.Ignore("Editor only: the Profiler's frames are read back through the Editor.");
            yield break;
#else
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            var side = director.PlanetSide;
            const int Window = 280; // under the profiler's 300-frame history
            try
            {
                // ---- Launch → Space (the gate's steps): the window from the frame the gate's own begins ----
                var transitions = Object.FindAnyObjectByType<TransitionDirector>();
                var ship = side.ship;
                ship.GetComponent<ShipBoarding>().ForceAboard();
                ship.externalInput = true;
                var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
                ship.Body.position = p; ship.transform.position = p;
                ship.Body.linearVelocity = new Vector2(0f, 12f);
                // the transition's own end (the Profiler keeps its last 300 frames): the gate's first window begins with the frame the
                // transition ended in (its monitor reads a frame late), so what that frame makes (the autosave) is in the gate's row
                BeginCapture();
                yield return WaitBusyCycle(transitions, 10f);
                yield return null;
                EndCapture("the LAUNCH's last 300 frames, to one frame past its end (the frame the gate's Space window opens with)", 12, 4);
                var spaceShip = director.Space.GetComponentInChildren<SpaceShip>();
                spaceShip.externalInput = true;
                spaceShip.intent = default;
                var earth = spaceShip.world.Find("earth").Value;
                spaceShip.Position = earth.position + new Vector2(0f, earth.WellRadius + 50f);
                spaceShip.Velocity = Vector2.zero;
                BeginCapture();
                for (int i = 0; i < Window; i++) yield return null;
                EndCapture("Space, the gate's window (straight after the launch, parked outside Earth's well)");
                for (int i = 0; i < 300; i++) yield return null;
                BeginCapture();
                for (int i = 0; i < Window; i++) yield return null;
                EndCapture("Space, 300 frames later (steady)");
                Assert.AreEqual(ViewMode.Space, GameState.Instance.view, "still in Space");

                // ---- Entry → Mars: the gate's window, then steady ----
                while (spaceShip.Invulnerable) yield return null;
                var mars = spaceShip.world.Find("mars").Value;
                spaceShip.Position = mars.position + new Vector2(0f, mars.RingRadius + 0.5f);
                spaceShip.Velocity = new Vector2(0f, -40f);
                BeginCapture();
                yield return WaitBusyCycle(transitions, 15f);
                yield return null;
                EndCapture("the ENTRY's last 300 frames, to one frame past its end", 12, 4);
                side = director.PlanetSide;
                Assert.NotNull(side, "entered a planet");
                Assert.AreEqual(Meridian.Planets.PlanetId.Mars, side.Config.id);
                while (!side.terrain.IsSettled) yield return null;
                BeginCapture();
                for (int i = 0; i < Window; i++) yield return null;
                EndCapture("Mars, the gate's window (from the frame the terrain settles after the entry)");
                for (int i = 0; i < 300; i++) yield return null;
                BeginCapture();
                for (int i = 0; i < Window; i++) yield return null;
                EndCapture("Mars, 300 frames later (steady)");

                // A batch frame is about a millisecond: 280 frames are a third of a second of the game, and what runs once a second
                // (a spawn tick, a readout) falls in a window by luck. So: the game stepped 1/60 s a frame, three windows on end:
                // 14 s of Mars as the game runs.
                Time.captureDeltaTime = 1f / 60f;
                for (int w = 0; w < 3; w++)
                {
                    BeginCapture();
                    for (int i = 0; i < Window; i++) yield return null;
                    EndCapture($"Mars as the game runs, 4.7 s of game time at a 60 fps step, window {w + 1} of 3");
                }

                // ---- the gate's FX peak: the forced storm, the one-shot pool kept full every frame ----
                var storm = side.dustStorm;
                var clock = Object.FindAnyObjectByType<TimeSystem>();
                storm.Force(0.1f, 300f);
                clock.Advance(0.1f + Meridian.Planet.Weather.DustStorm.RampRealSeconds + 1f);
                var stress = new GameObject("FxStress").AddComponent<FxStress>();
                stress.pool = side.GetComponentInChildren<Meridian.FX.FxPool>();
                stress.around = side.sideCamera.transform;
                for (int i = 0; i < 30; i++) yield return null;
                for (int w = 0; w < 2; w++)
                {
                    BeginCapture();
                    for (int i = 0; i < Window; i++) yield return null;
                    EndCapture($"Mars FX peak (the storm forced, the one-shot pool kept full), 4.7 s of game time, window {w + 1} of 2; pool alive {stress.pool.Alive}");
                }
                Object.Destroy(stress.gameObject);
            }
            finally
            {
                Time.captureDeltaTime = 0f;
                UnityEditorInternal.ProfilerDriver.enabled = false;
                UnityEngine.Profiling.Profiler.enabled = false;
            }
#endif
        }
    }
}
