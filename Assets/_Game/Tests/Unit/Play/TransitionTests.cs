using System.Collections;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Ship;
using Meridian.Space;
using Meridian.Transitions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-012 (PlayMode): launch Earth → ring and entry ring → Mars, through the real Core flow.</summary>
    public class TransitionTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string saveRoot;

        // Transitions autosave (U-013): keep those writes out of the real save folder.
        [SetUp]
        public void SetUp()
        {
            saveRoot = System.IO.Path.Combine(Application.temporaryCachePath, "meridian_saves_tr_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            Meridian.Save.SaveSystem.RootOverride = saveRoot;
        }

        [TearDown]
        public void TearDown()
        {
            Meridian.Save.SaveSystem.RootOverride = null;
            if (System.IO.Directory.Exists(saveRoot)) System.IO.Directory.Delete(saveRoot, true);
        }

        static IEnumerator Boot(System.Action<SceneDirector> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            done(director);
        }

        static IEnumerator WaitIdle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null; // wait for it to start
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

        /// <summary>Boards the ship and puts it just under the Escape Line climbing; the next steps launch it.</summary>
        static IEnumerator LaunchFromEarth(SceneDirector director, TransitionDirector transitions)
        {
            var side = director.PlanetSide;
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p;
            ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            yield return WaitIdle(transitions, 10f);
        }

        [UnityTest]
        public IEnumerator LaunchPutsShipOnEarthsRingAtItsLongitudeWithStateCarried()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            var state = GameState.Instance;
            state.hull = 87f; state.thrusterMark = 2;
            state.cargo.Add(new CargoStack { itemId = 3, count = 12 });
            var side = director.PlanetSide;
            float x = side.ship.Body.position.x;
            int width = side.Config.worldWidth;
            var time = Object.FindAnyObjectByType<TimeSystem>();

            yield return LaunchFromEarth(director, transitions);

            Assert.AreEqual(ViewMode.Space, state.view, "now in space");
            Assert.IsNull(director.PlanetSide, "PlanetSide unloaded");
            TestContext.Out.WriteLine($"[MERIDIAN] launch took {transitions.LastLaunchSeconds:F2} s");
            Assert.LessOrEqual(transitions.LastLaunchSeconds, 1.5f, "launch ≤ 1.5 s total");

            var earth = transitions.LaunchBody.Value;
            Assert.AreEqual(PlanetId.Earth, earth.planet);
            var offset = transitions.LaunchPlacement - earth.position;
            Assert.AreEqual(earth.RingRadius, offset.magnitude, 0.01f, "on the Atmosphere Ring");
            float placedAngle = Mathf.Repeat(Mathf.Atan2(offset.y, offset.x) * Mathf.Rad2Deg, 360f);
            Assert.AreEqual(transitions.LastLaunchAngle, placedAngle, 0.05f);
            float lonOnly = TransitionDirector.Longitude(x, width);
            float rotationNow = time.DayFraction(state.catalog.Get(PlanetId.Earth)) * 360f;
            Assert.AreEqual(0f, Mathf.DeltaAngle(lonOnly + rotationNow, placedAngle), 0.5f,
                "angle = longitude + planet rotation (rotation drifts < 0.5° during the test)");
            var radial = Vector2.Dot(transitions.LaunchVelocity, offset.normalized);
            Assert.AreEqual(20f, radial, 0.01f, "20 u/s outward");
            Assert.AreEqual(20f, transitions.LaunchVelocity.magnitude, 0.01f, "purely radial");

            Assert.AreEqual(87f, state.hull, 1e-4f, "hull carried");
            Assert.AreEqual(2, state.thrusterMark, "thruster mark carried");
            Assert.AreEqual(1, state.cargo.Count);
            Assert.AreEqual(12, state.cargo[0].count, "cargo carried");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator EntryIntoMarsArrivesAtEscapeLinePlus20Descending15()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            yield return LaunchFromEarth(director, transitions);
            var state = GameState.Instance;
            float hull = state.hull;

            var ship = director.Space.GetComponentInChildren<SpaceShip>();
            ship.externalInput = true;
            ship.intent = default;
            var mars = ship.world.Find("mars").Value;
            // Just outside Mars' ring, moving inward: the next step crosses it.
            ship.Position = mars.position + new Vector2(0f, mars.RingRadius + 0.5f);
            ship.Velocity = new Vector2(0f, -40f);
            yield return new WaitForSeconds(1.1f); // past the launch invulnerability
            ship.Position = mars.position + new Vector2(0f, mars.RingRadius + 0.5f);
            ship.Velocity = new Vector2(0f, -40f);
            yield return WaitIdle(transitions, 15f);

            TestContext.Out.WriteLine($"[MERIDIAN] entry took {transitions.LastEntrySeconds:F2} s");
            Assert.AreEqual(ViewMode.PlanetSide, state.view);
            Assert.AreEqual(PlanetId.Mars, state.currentPlanet);
            var side = director.PlanetSide;
            Assert.NotNull(side, "PlanetSide loaded");
            Assert.AreEqual(PlanetId.Mars, side.Config.id);
            Assert.IsTrue(side.LastArrival.HasValue);
            var arrival = side.LastArrival.Value;
            Assert.AreEqual(570f + 20f, arrival.shipPosition.y, 1e-3f, "Escape Line + 20 m");
            Assert.AreEqual(-15f, arrival.shipVelocity.y, 1e-3f, "descending 15 m/s");
            Assert.AreEqual(-3.72f, Physics2D.gravity.y, 1e-4f, "Mars gravity on");
            Assert.AreEqual(hull, state.hull, 1e-4f, "hull unchanged");
            Assert.IsTrue(side.ship.GetComponent<ShipBoarding>().Aboard, "surveyor aboard");
            Assert.IsTrue(side.ship.piloted, "side controls live (U-107: no lock)");
            Assert.AreEqual(0f, side.ship.Tilt, 1e-3f, "upright (D-102)");
            Assert.LessOrEqual(transitions.LastEntrySeconds, 4f, "planet load ≤ 4 s (Bible §11.1)");

            // The ship then flies down under Mars gravity (sanity: it is descending, not frozen).
            float y0 = side.ship.Body.position.y;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
            Assert.Less(side.ship.Body.position.y, y0, "descending");
            LogAssert.NoUnexpectedReceived();
        }

        // ---------- U-206: no creature of another planet on arrival ----------

        /// <summary>One creature put beside the surveyor (the director's despawn range is measured from it, aboard or not), so the planet is left with creatures alive.</summary>
        static void SpawnBesideTheSurveyor(PlanetSideRoot side, Meridian.Creatures.Species species)
        {
            var at = (Vector2)side.player.transform.position + new Vector2(4f, 1f);
            Assert.NotNull(side.creatures.Spawn(species, at), $"a {species} spawned on {side.Config.id}");
            Assert.Greater(side.creatures.AliveCount, 0, $"creatures alive on {side.Config.id} before the planet change");
        }

        /// <summary>The real route out: aboard, just under the Escape Line climbing; checks creatures are still alive as the launch begins.</summary>
        static IEnumerator LaunchWithCreaturesAlive(SceneDirector director, TransitionDirector transitions, Meridian.Creatures.Species species)
        {
            var side = director.PlanetSide;
            var ship = side.ship;
            SpawnBesideTheSurveyor(side, species);
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p;
            ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            float timeout = Time.realtimeSinceStartup + 10f;
            while (!transitions.Busy && Time.realtimeSinceStartup < timeout) { ship.Body.linearVelocity = new Vector2(0f, 12f); yield return null; }
            Assert.IsTrue(transitions.Busy, $"the launch from {side.Config.id} began");
            int alive = side.creatures.AliveCount;
            TestContext.Out.WriteLine($"[MERIDIAN] U-206 leaving {side.Config.id} by the Escape Line: {alive} creature(s) alive, gulls {side.creatures.CountOf(Meridian.Creatures.Species.Gull)}");
            Assert.Greater(alive, 0, $"creatures alive on {side.Config.id} as the launch begins");
            while (transitions.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.AreEqual(ViewMode.Space, GameState.Instance.view, "in space");
        }

        /// <summary>The real route in: the space ship put just outside the body's ring flying inward (twice: the first pass sits inside the launch's invulnerable second).</summary>
        static IEnumerator EnterFromSpace(SceneDirector director, TransitionDirector transitions, string bodyName)
        {
            var ship = director.Space.GetComponentInChildren<SpaceShip>();
            ship.externalInput = true;
            ship.intent = default;
            for (int pass = 0; pass < 2; pass++)
            {
                var body = ship.world.Find(bodyName).Value;
                ship.Position = body.position + new Vector2(0f, body.RingRadius + 0.5f);
                ship.Velocity = new Vector2(0f, -40f);
                if (pass == 0) yield return new WaitForSeconds(1.1f);
            }
            yield return WaitIdle(transitions, 15f);
        }

        /// <summary>
        /// On arrival: nothing alive is another planet's species, and nothing draws the director's placeholder box (natives that spawned before
        /// their sheet take it when it lands, U-108: they get a few seconds).
        /// </summary>
        static IEnumerator AssertOnlyNativesAlive(SceneDirector director, PlanetId planet, string route)
        {
            var side = director.PlanetSide;
            Assert.NotNull(side, $"{route}: PlanetSide loaded");
            Assert.AreEqual(planet, side.Config.id, route);
            var creatures = side.creatures;
            Assert.AreEqual(planet, creatures.Planet.id, $"{route}: the creature director is set for {planet}");
            int alive = 0, boxes = 0;
            foreach (var c in creatures.All)
            {
                if (!c.Alive) continue;
                alive++;
                Assert.AreEqual(planet, c.Spec.planet, $"{route}: a {c.Spec.id} is alive on {planet} at arrival (another planet's species has no sheet here and draws as its placeholder box)");
            }
            float until = Time.realtimeSinceStartup + 6f;
            do
            {
                boxes = 0;
                foreach (var c in creatures.All) if (c.Alive && c.IsPlaceholder && c.View.enabled) boxes++;
                if (boxes > 0) yield return null;
            } while (boxes > 0 && Time.realtimeSinceStartup < until);
            foreach (var c in creatures.All)
            {
                if (!c.Alive) continue;
                Assert.AreEqual(planet, c.Spec.planet, $"{route}: a {c.Spec.id} is alive on {planet} after arrival");
                Assert.IsFalse(c.IsPlaceholder && c.View.enabled, $"{route}: a {c.Spec.id} draws the placeholder box on {planet}");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] U-206 {route}: on {planet}, {alive} creature(s) alive at arrival, all {planet}'s; gulls {creatures.CountOf(Meridian.Creatures.Species.Gull)}; placeholder boxes {boxes}");
        }

        /// <summary>
        /// U-206 (U-204 F14, the pale box behind the Pilgrim on Mars in 0.6.0's, 0.6.1's and 0.6.2's smoke): with creatures alive, Earth → Mars and
        /// Mars → Earth by a direct load and by the real route (the Escape Line out, the ring in): no creature of another planet's species is alive
        /// on arrival and none draws as a placeholder. The cause was the cartoon stage's camp gull, spawned on every planet's stage; Earth keeps it.
        /// </summary>
        [UnityTest]
        public IEnumerator NoCreatureOfAnotherPlanetIsAliveOnArrival()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            var catalog = GameState.Instance.catalog;
            var gull = Meridian.Creatures.Species.Gull;
            Assert.AreEqual(PlanetId.Earth, director.PlanetSide.Config.id, "the boot lands at Earth's camp");
            TestContext.Out.WriteLine($"[MERIDIAN] U-206 boot: Earth, {director.PlanetSide.creatures.AliveCount} creature(s) alive, gulls {director.PlanetSide.creatures.CountOf(gull)}");

            // 1. a direct load, Earth → Mars
            SpawnBesideTheSurveyor(director.PlanetSide, Meridian.Creatures.Species.Stag);
            yield return director.LoadPlanetSide(catalog.Get(PlanetId.Mars));
            var side = director.PlanetSide;
            side.hazards.enabled = false;
            if (side.wardens != null) side.wardens.enabled = false;
            Assert.AreEqual(0, side.creatures.CountOf(gull), "no gull on Mars (a direct load)");
            yield return AssertOnlyNativesAlive(director, PlanetId.Mars, "direct load Earth → Mars");

            // 2. a direct load, Mars → Earth: the camp's gull is back
            SpawnBesideTheSurveyor(director.PlanetSide, Meridian.Creatures.Species.Dustskater);
            yield return director.LoadPlanetSide(catalog.Get(PlanetId.Earth));
            side = director.PlanetSide;
            if (side.cartoon != null && side.cartoon.Active)
                Assert.AreEqual(Meridian.View2D.CartoonStage.GullCount, side.creatures.CountOf(gull), "Earth's camp has its gull again (U-101)");
            yield return AssertOnlyNativesAlive(director, PlanetId.Earth, "direct load Mars → Earth");
            float settle = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < settle) yield return null;

            // 3. the real route, Earth → Mars
            yield return LaunchWithCreaturesAlive(director, transitions, Meridian.Creatures.Species.Stag);
            yield return EnterFromSpace(director, transitions, "mars");
            Assert.AreEqual(ViewMode.PlanetSide, GameState.Instance.view, "landed view");
            Assert.AreEqual(0, director.PlanetSide.creatures.CountOf(gull), "no gull on Mars (the real route)");
            yield return AssertOnlyNativesAlive(director, PlanetId.Mars, "real route Earth → Mars");

            // 4. the real route, Mars → Earth
            yield return LaunchWithCreaturesAlive(director, transitions, Meridian.Creatures.Species.Dustskater);
            yield return EnterFromSpace(director, transitions, "earth");
            Assert.AreEqual(ViewMode.PlanetSide, GameState.Instance.view, "landed view");
            yield return AssertOnlyNativesAlive(director, PlanetId.Earth, "real route Mars → Earth");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
