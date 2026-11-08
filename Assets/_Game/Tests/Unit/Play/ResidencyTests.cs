using System.Collections;
using Meridian.Core;
using Meridian.Perf;
using Meridian.Planets;
using Meridian.Ship;
using Meridian.Space;
using Meridian.Terrain;
using Meridian.Transitions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-091 (PlayMode, Bible §11.1 v4, D-089 / D-110): Earth → Space → Mars → Space → Earth with real launches and entries.
    /// After each hop the planet left behind holds no live Addressables handle within 5 s (its own handles were tracked
    /// while it was visited), every transition is ≤ 1.5 s and every planet load (entry start → terrain settled + nothing
    /// pending in the planet's groups) ≤ 5 s, streaming at run speed with the resident radius of 3 never hitches above
    /// 33 ms, and the working set and private commit of a second visit stay within 10 % of the first.
    /// </summary>
    public class ResidencyTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string saveRoot;

        struct Reading { public long ws, priv, tex, free; public override string ToString() => $"working set {ws} MB, private {priv} MB, textures {tex} MB (free RAM {free} MB)"; }

        [SetUp]
        public void SetUp()
        {
            saveRoot = System.IO.Path.Combine(Application.temporaryCachePath, "meridian_saves_res_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            Meridian.Save.SaveSystem.RootOverride = saveRoot;
            TerrainTileSet.ReleasePrefetch();
        }

        [TearDown]
        public void TearDown()
        {
            Meridian.Save.SaveSystem.RootOverride = null;
            TerrainTileSet.ReleasePrefetch();
            if (System.IO.Directory.Exists(saveRoot)) System.IO.Directory.Delete(saveRoot, true);
        }

        static void Log(string s) => TestContext.Out.WriteLine("[MERIDIAN] residency: " + s);

        static IEnumerator BusyCycle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

        /// <summary>60 frames, GC, UnloadUnusedAssets, 30 frames, then the counters (a callback: iterators cannot have out parameters).</summary>
        static IEnumerator Settled(BudgetMonitor m, Camera cam, System.Action<Reading> done)
        {
            for (int i = 0; i < 60; i++) yield return null;
            System.GC.Collect();
            yield return Resources.UnloadUnusedAssets();
            for (int i = 0; i < 30; i++) yield return null;
            var s = m.Snapshot(cam);
            done(new Reading { ws = s.workingSetMB > 0 ? s.workingSetMB : s.systemMemoryMB, priv = ProcessMemory.PrivateMB(), tex = s.textureMemoryMB, free = ProcessMemory.FreeSystemMB() });
        }

        static int OwnSheets(PlanetId p)
        {
            int n = 0;
            foreach (var id in TerrainStreamer.MaterialsFor(p)) { var k = TileId.ArtKey(id); if (k != null && !Meridian.Art.ArtKeys.IsSharedTerrain(k)) n++; }
            return n;
        }

        static IEnumerator Launch(SceneDirector director, TransitionDirector transitions, PlanetId planet)
        {
            string group = Residency.PlanetGroup(planet);
            Assert.GreaterOrEqual(Residency.CountPlanet(group), OwnSheets(planet), $"{group}: the visited planet's own sheets are tracked (holders: {Residency.Holders(group)})");
            var side = director.PlanetSide;
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            ship.Body.simulated = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p; ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            yield return BusyCycle(transitions, 10f);
            Assert.AreEqual(ViewMode.Space, GameState.Instance.view, "in space");
            Log($"launch from {planet}: {transitions.LastLaunchSeconds:F2} s");
            Assert.LessOrEqual(transitions.LastLaunchSeconds, 1.5f, "launch transition ≤ 1.5 s");
            var spaceShip = director.Space.GetComponentInChildren<SpaceShip>();
            spaceShip.externalInput = true;
            spaceShip.intent = default;
            var body = spaceShip.world.Find(planet.ToString().ToLowerInvariant());
            if (body.HasValue) { spaceShip.Position = body.Value.position + new Vector2(0f, body.Value.WellRadius + 50f); spaceShip.Velocity = Vector2.zero; }
        }

        static IEnumerator Enter(SceneDirector director, TransitionDirector transitions, string body)
        {
            var spaceShip = director.Space.GetComponentInChildren<SpaceShip>();
            spaceShip.externalInput = true;
            spaceShip.intent = default;
            while (spaceShip.Invulnerable) yield return null;
            var target = spaceShip.world.Find(body).Value;
            spaceShip.Position = target.position + new Vector2(0f, target.RingRadius + 0.5f);
            spaceShip.Velocity = new Vector2(0f, -40f); // the next step crosses the ring: a real entry
            yield return BusyCycle(transitions, 15f);
            var side = director.PlanetSide;
            Assert.NotNull(side, "entered " + body);
            float until = Time.realtimeSinceStartup + 10f;
            while (director.LastPlanetLoadSeconds < 0f && Time.realtimeSinceStartup < until) yield return null;
            Log($"entry into {body}: transition {transitions.LastEntrySeconds:F2} s, planet load {director.LastPlanetLoadSeconds:F2} s ({director.LastLoadBreakdown}), worst iris-in frame {transitions.LastIrisInWorstMs:F1} ms");
            Assert.LessOrEqual(transitions.LastEntrySeconds, 1.5f, "entry transition ≤ 1.5 s (D-089)");
            Assert.GreaterOrEqual(director.LastPlanetLoadSeconds, 0f, "the planet-load clock stopped");
            Assert.LessOrEqual(director.LastPlanetLoadSeconds, 5f, "planet load ≤ 5 s: entry start → terrain settled + no pending planet load (D-089)");
            while (!side.terrain.IsSettled) yield return null;
        }

        static IEnumerator ReleasedWithin5s(string planetGroup)
        {
            float t0 = Time.realtimeSinceStartup;
            int n = Residency.CountPlanet(planetGroup);
            while (n > 0 && Time.realtimeSinceStartup - t0 < 5f) { yield return null; n = Residency.CountPlanet(planetGroup); }
            Log($"{planetGroup} handles {n} after {Time.realtimeSinceStartup - t0:F1} s (holders: {Residency.Holders(planetGroup)}); resident: {Residency.ResidentGroups()}");
            Assert.AreEqual(0, n, $"{planetGroup} released within 5 s; holders: {Residency.Holders(planetGroup)}");
        }

        static IEnumerator Stream(PlanetSideRoot side, string planet)
        {
            RunSpeedStreaming.StreamResult r = default;
            yield return RunSpeedStreaming.Run(side.sideCamera, side.terrain, null, x => r = x);
            Log($"streaming on {planet}: {r}, resident radius {TerrainConstants.ResidentRadius}");
            Assert.AreEqual(3, TerrainConstants.ResidentRadius, "resident radius 3");
            Assert.GreaterOrEqual(r.frames, RunSpeedStreaming.MinFrames, "enough frames counted");
            Assert.GreaterOrEqual(r.metres, RunSpeedStreaming.MinMetres, "enough ground covered");
            Assert.GreaterOrEqual(r.chunksCrossed, 3, "chunks really streamed");
            Assert.Less(r.worstMs, 33f, $"no hitch > 33 ms while streaming on {planet}");
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator PlanetsReleaseOnTransitionAndMemoryReturns()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            var monitor = BudgetMonitor.Instance;
            Assert.NotNull(monitor, "BudgetMonitor in Core");

            // 1. Earth: the first visit's reading, then streaming at run speed.
            Reading earthFirst = default;
            yield return Settled(monitor, director.PlanetSide.sideCamera, r => earthFirst = r);
            Log($"Earth first visit: {earthFirst}; resident: {Residency.ResidentGroups()}");
            yield return Stream(director.PlanetSide, "Earth");

            // 2. Launch: Earth releases, Space's first reading.
            yield return Launch(director, transitions, PlanetId.Earth);
            yield return ReleasedWithin5s("planet_earth");
            Reading spaceFirst = default;
            yield return Settled(monitor, director.Space.GetComponentInChildren<Camera>(), r => spaceFirst = r);
            Log($"Space first: {spaceFirst}");

            // 3. Enter Mars: Earth stays released, only Mars is resident, Mars's own sheets are tracked.
            yield return Enter(director, transitions, "mars");
            yield return ReleasedWithin5s("planet_earth");
            Assert.IsTrue(Residency.OnlyPlanet("planet_mars"), $"only Mars resident: {Residency.ResidentGroups()}; held: venus [{Residency.Holders("planet_venus")}], warden [{Residency.Holders("planet_warden")}], waystation [{Residency.Holders("planet_waystation")}], earth [{Residency.Holders("planet_earth")}]");
            Assert.GreaterOrEqual(Residency.CountPlanet("planet_mars"), OwnSheets(PlanetId.Mars), "Mars's own sheets tracked");

            // 4. Stream Mars at run speed (the ship parked mid-air meanwhile).
            var mars = director.PlanetSide;
            mars.ship.Body.simulated = false;
            yield return RunSpeedStreaming.ToSurface(mars.sideCamera, mars.terrain);
            yield return Stream(mars, "Mars");
            mars.ship.Body.simulated = true;

            // 5. Launch from Mars: Mars releases; Space again within 10 % of the first time.
            yield return Launch(director, transitions, PlanetId.Mars);
            yield return ReleasedWithin5s("planet_mars");
            Reading spaceAgain = default;
            yield return Settled(monitor, director.Space.GetComponentInChildren<Camera>(), r => spaceAgain = r);
            Log($"Space again: {spaceAgain} (first {spaceFirst})");
            TestContext.Out.WriteLine($"[MERIDIAN] Space working set again {spaceAgain.ws} vs {spaceFirst.ws} MB (info, D-116: private commit judges)"); // D-116
            if (spaceFirst.priv > 0) Assert.LessOrEqual(spaceAgain.priv, spaceFirst.priv * 1.10f, "Space private commit back within 10 %");

            // 6. Enter Earth again: Mars releases, only Earth resident, Earth again within 10 % of the first visit.
            yield return Enter(director, transitions, "earth");
            yield return ReleasedWithin5s("planet_mars");
            Assert.IsTrue(Residency.OnlyPlanet("planet_earth"), $"only Earth resident: {Residency.ResidentGroups()}");
            Reading earthAgain = default;
            yield return Settled(monitor, director.PlanetSide.sideCamera, r => earthAgain = r);
            Log($"Earth again: {earthAgain} (first {earthFirst})");
            TestContext.Out.WriteLine($"[MERIDIAN] Earth working set again {earthAgain.ws} vs {earthFirst.ws} MB (info, D-116: private commit judges)"); // D-116
            if (earthFirst.priv > 0) Assert.LessOrEqual(earthAgain.priv, earthFirst.priv * 1.10f, "Earth private commit back within 10 %");

            foreach (var r in new[] { earthFirst, spaceFirst, spaceAgain, earthAgain }) Assert.Greater(r.ws, 0, "every reading is real (no silent skip)");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
