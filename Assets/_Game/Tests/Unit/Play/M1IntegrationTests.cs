using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Save;
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
    /// U-017: the M1 loop end to end with real physics and no teleports (Bible §12 M1): Earth (dig,
    /// board, launch burn from rest) → Escape Line → top-down flight to Mars → entry → powered
    /// descent and a clean landing → exit, dig → save → fresh boot → load → same world and state.
    /// Run twice (two test cases), each with a clean console.
    /// </summary>
    public class M1IntegrationTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string saveRoot;

        [SetUp]
        public void SetUp()
        {
            saveRoot = Path.Combine(Application.temporaryCachePath, "meridian_saves_m1_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = saveRoot;
        }

        [TearDown]
        public void TearDown()
        {
            SaveSystem.RootOverride = null;
            if (Directory.Exists(saveRoot)) Directory.Delete(saveRoot, true);
        }

        [UnityTest] public IEnumerator M1LoopRun1() => M1Loop();
        [UnityTest] public IEnumerator M1LoopRun2() => M1Loop();

        static IEnumerator Boot(System.Action<SceneDirector> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady, "Core booted");
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            done(director);
        }

        static IEnumerator Until(System.Func<bool> condition, float seconds, string what)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!condition() && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
            Assert.IsTrue(condition(), $"timed out: {what}");
        }

        IEnumerator M1Loop()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var state = GameState.Instance;
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            var side = director.PlanetSide;
            Assert.AreEqual(PlanetId.Earth, side.Config.id);
            Assert.IsTrue(side.player.Grounded, "standing on Earth");

            // ---- Earth: dig with the Beam next to the player ----
            int ex = side.spawnX + 2, ey = side.terrain.TopSolidY(ex);
            Assert.IsTrue(side.rig.Dig(new Vector2(ex + 0.5f, ey + 0.5f)), "dig on Earth");

            // ---- Board and launch from rest: the §4.1 burn (17) over the first 3 s ----
            var ship = side.ship;
            Assert.IsTrue(ship.AtRest, "Pilgrim landed at rest");
            var boarding = ship.GetComponent<ShipBoarding>();
            boarding.ForceAboard();
            ship.externalInput = true;
            float fuelAtStart = state.fuel;
            ship.intent.thrust = 1f;
            yield return Until(() => state.view == ViewMode.Space && !transitions.Busy, 60f, "climb to the Escape Line and launch");
            Assert.AreEqual(fuelAtStart - 17f, state.fuel, 0.05f, "launch fuel 17 from Earth");
            Assert.LessOrEqual(transitions.LastLaunchSeconds, 1.5f);

            // ---- Top-down: fly to Mars and cross its Atmosphere Ring ----
            var spaceShip = director.Space.GetComponentInChildren<SpaceShip>();
            spaceShip.externalInput = true;
            var mars = spaceShip.world.Find("mars").Value;
            float t = 0f;
            while (state.view == ViewMode.Space && t < 40f)
            {
                var to = mars.position - spaceShip.Position;
                spaceShip.Heading = Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg;
                spaceShip.intent.thrust = 1f;
                yield return new WaitForFixedUpdate();
                t += Time.fixedDeltaTime;
            }
            spaceShip.intent = default;
            yield return Until(() => !transitions.Busy && director.PlanetSide != null, 15f, "entry into Mars");
            side = director.PlanetSide;
            Assert.AreEqual(PlanetId.Mars, side.Config.id, "entered Mars");
            Assert.AreEqual(-3.72f, Physics2D.gravity.y, 1e-4f);

            // ---- Powered descent and a clean landing (§4.3: ≤ 6 m/s is clean) ----
            ship = side.ship;
            ship.externalInput = true;
            float hullBefore = state.hull;
            float elapsed = 0f;
            while (!ship.Grounded && elapsed < 120f)
            {
                float alt = ship.AltitudeAboveGround;
                float target = -Mathf.Clamp(alt * 0.25f, 2f, 20f); // slow down as the ground comes up
                ship.intent.thrust = ship.Body.linearVelocity.y < target ? 1f : 0f;
                yield return new WaitForFixedUpdate();
                elapsed += Time.fixedDeltaTime;
            }
            ship.intent = default;
            Assert.IsTrue(ship.Grounded, "landed on Mars");
            TestContext.Out.WriteLine($"[MERIDIAN] Mars touchdown {ship.LastTouchdownSpeed:F2} m/s after {elapsed:F1} s");
            Assert.LessOrEqual(ship.LastTouchdownSpeed, SideShip.CleanTouchdown, "clean touchdown");
            Assert.AreEqual(hullBefore, state.hull, 1e-4f, "no hull damage");
            yield return Until(() => ship.AtRest, 5f, "ship at rest");

            // ---- Exit and dig on Mars ----
            boarding = ship.GetComponent<ShipBoarding>();
            Assert.IsTrue(boarding.TryExit(), "exit the landed ship");
            yield return Until(() => side.player.Grounded, 10f, "surveyor on the ground");
            var player = side.player;
            int mx = Mathf.FloorToInt(player.Body.position.x) + 1, my = side.terrain.TopSolidY(mx);
            Assert.IsTrue(side.rig.Dig(new Vector2(mx + 0.5f, my + 0.5f)), "dig on Mars");
            yield return Until(() => player.Grounded, 10f, "standing after the dig");

            // ---- Save, then a fresh boot and load ----
            var save = SaveSystem.Instance;
            save.Save();
            var expectFuel = state.fuel;
            var expectHull = state.hull;
            var expectPlayer = player.Body.position;
            int earthEdits = state.EditsFor(PlanetId.Earth).Count, marsEdits = state.EditsFor(PlanetId.Mars).Count;
            Assert.Greater(earthEdits, 0); Assert.Greater(marsEdits, 0);

            yield return Boot(d => director = d);
            state = GameState.Instance;
            Assert.AreEqual(PlanetId.Earth, state.currentPlanet, "a fresh boot starts on Earth");
            yield return SaveSystem.Instance.Load();
            side = director.PlanetSide;
            yield return Until(() => side.terrain.IsSettled, 20f, "Mars terrain after load");

            Assert.AreEqual(PlanetId.Mars, state.currentPlanet, "loaded onto Mars");
            Assert.AreEqual(PlanetId.Mars, side.Config.id);
            Assert.AreEqual(expectFuel, state.fuel, 1e-3f, "fuel");
            Assert.AreEqual(expectHull, state.hull, 1e-3f, "hull");
            Assert.AreEqual(earthEdits, state.EditsFor(PlanetId.Earth).Count, "Earth diffs");
            Assert.AreEqual(marsEdits, state.EditsFor(PlanetId.Mars).Count, "Mars diffs");
            Assert.AreEqual(TileId.Air, side.terrain.GetTile(mx, my), "the Mars dig is still dug");
            Assert.AreEqual(expectPlayer.x, side.player.Body.position.x, 0.1f, "player x");
            Assert.AreEqual(expectPlayer.y, side.player.Body.position.y, 0.1f, "player y");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
