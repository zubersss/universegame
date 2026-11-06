using System.Collections;
using Meridian.Core;
using Meridian.Perf;
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
    /// U-091 (PlayMode, Bible §11.1 v3 Residency): Earth → Space → Mars → Space → Earth. After each hop the planet
    /// left behind holds no live Addressables handle within 5 s, the system memory comes back to within 10 % of the
    /// first visit, every planet load is ≤ 5 s and every transition ≤ 1.5 s, and streaming at run speed with the
    /// resident radius of 3 never hitches above 33 ms.
    /// </summary>
    public class ResidencyTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string saveRoot;

        [SetUp]
        public void SetUp()
        {
            saveRoot = System.IO.Path.Combine(Application.temporaryCachePath, "meridian_saves_res_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            Meridian.Save.SaveSystem.RootOverride = saveRoot;
        }

        [TearDown]
        public void TearDown()
        {
            Meridian.Save.SaveSystem.RootOverride = null;
            if (System.IO.Directory.Exists(saveRoot)) System.IO.Directory.Delete(saveRoot, true);
        }

        static IEnumerator BusyCycle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

        static IEnumerator Launch(SceneDirector director, TransitionDirector transitions)
        {
            var side = director.PlanetSide;
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p; ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            yield return BusyCycle(transitions, 10f);
            Assert.AreEqual(ViewMode.Space, GameState.Instance.view, "in space");
            Assert.LessOrEqual(transitions.LastLaunchSeconds, 1.5f, "launch ≤ 1.5 s");
        }

        static IEnumerator Enter(SceneDirector director, TransitionDirector transitions, string body)
        {
            var spaceShip = director.Space.GetComponentInChildren<SpaceShip>();
            spaceShip.externalInput = true;
            spaceShip.intent = default;
            while (spaceShip.Invulnerable) yield return null;
            var target = spaceShip.world.Find(body).Value;
            spaceShip.Position = target.position + new Vector2(0f, target.RingRadius + 0.5f);
            spaceShip.Velocity = new Vector2(0f, -40f);
            yield return BusyCycle(transitions, 15f);
            Assert.LessOrEqual(transitions.LastEntrySeconds, 5f, "planet load ≤ 5 s (v3)");
            var side = director.PlanetSide;
            Assert.NotNull(side, "entered " + body);
            while (!side.terrain.IsSettled) yield return null;
        }

        static IEnumerator ReleasedWithin5s(string planetGroup)
        {
            float t0 = Time.realtimeSinceStartup;
            int n = Residency.CountPlanet(planetGroup);
            while (n > 0 && Time.realtimeSinceStartup - t0 < 5f) { yield return null; n = Residency.CountPlanet(planetGroup); }
            Debug.Log($"[MERIDIAN] residency: {planetGroup} handles {n} after {Time.realtimeSinceStartup - t0:F1} s (holders: {Residency.Holders(planetGroup)}); resident: {Residency.ResidentGroups()}");
            Assert.AreEqual(0, n, $"{planetGroup} released within 5 s; holders: {Residency.Holders(planetGroup)}");
        }

        [UnityTest]
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
            for (int i = 0; i < 60; i++) yield return null;
            long earthFirst = monitor.Snapshot(director.PlanetSide.sideCamera).systemMemoryMB;
            Debug.Log($"[MERIDIAN] residency: Earth first visit system {earthFirst} MB; resident: {Residency.ResidentGroups()}");

            // Streaming at run speed with the resident radius of 3: no hitch above 33 ms.
            var side = director.PlanetSide;
            var cam = side.sideCamera;
            var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
            follow.enabled = false;
            float worst = 0f;
            for (int i = 0; i < 300; i++)
            {
                cam.transform.position += new Vector3(6.5f * Time.deltaTime, 0f, 0f);
                yield return null;
                if (i > 5) worst = Mathf.Max(worst, Time.unscaledDeltaTime * 1000f);
            }
            Debug.Log($"[MERIDIAN] residency: streaming at 6.5 m/s, worst frame {worst:F1} ms, resident radius {Meridian.Terrain.TerrainConstants.ResidentRadius}");
            Assert.AreEqual(3, Meridian.Terrain.TerrainConstants.ResidentRadius, "resident radius 3 (v3)");
            Assert.Less(worst, 33f, "no hitch > 33 ms while streaming");
            follow.enabled = true;

            yield return Launch(director, transitions);
            yield return ReleasedWithin5s("planet_earth");
            yield return Enter(director, transitions, "mars");
            yield return ReleasedWithin5s("planet_earth");
            yield return Launch(director, transitions);
            yield return ReleasedWithin5s("planet_mars");
            yield return Enter(director, transitions, "earth");
            yield return ReleasedWithin5s("planet_mars");
            for (int i = 0; i < 60; i++) yield return null;
            var back = Resources.UnloadUnusedAssets();
            while (!back.isDone) yield return null;
            long earthAgain = monitor.Snapshot(director.PlanetSide.sideCamera).systemMemoryMB;
            Debug.Log($"[MERIDIAN] residency: Earth second visit system {earthAgain} MB (first {earthFirst} MB)");
            if (earthFirst > 0 && earthAgain > 0)
                Assert.LessOrEqual(earthAgain, earthFirst * 1.10f, "system memory back within 10 % of the first visit");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
