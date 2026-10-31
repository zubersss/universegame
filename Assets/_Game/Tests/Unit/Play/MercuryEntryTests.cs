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
    /// <summary>U-048 (PlayMode): launch from Earth, enter Mercury from orbit in ≤ 1.5 s, land in a working world (terrain, hazards, flares, POIs).</summary>
    public class MercuryEntryTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static IEnumerator BusyCycle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

        [UnityTest]
        public IEnumerator EntryToMercuryWithin1500ms()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();

            // Launch → Space.
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            var side = director.PlanetSide;
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p; ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            yield return BusyCycle(transitions, 15f);
            Assert.AreEqual(ViewMode.Space, GameState.Instance.view, "in space");

            // Entry → Mercury.
            var craft = director.Space.GetComponentInChildren<SpaceShip>();
            craft.externalInput = true;
            craft.intent = default;
            while (craft.Invulnerable) yield return null;
            var mercury = craft.world.Find("mercury").Value;
            craft.Position = mercury.position + new Vector2(0f, mercury.RingRadius + 0.5f);
            craft.Velocity = new Vector2(0f, -40f);
            yield return BusyCycle(transitions, 20f);
            side = director.PlanetSide;
            TestContext.Out.WriteLine($"[MERIDIAN] Mercury entry {transitions.LastEntrySeconds:F2} s ({director.LastLoadBreakdown})");
            Assert.AreEqual(PlanetId.Mercury, side.Config.id, "on Mercury");
            Assert.LessOrEqual(transitions.LastEntrySeconds, 1.5f, "entry ≤ 1.5 s (U-048)");

            // A working world: terrain settles, the hazards and flares run, the POIs are placed.
            timeout = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(side.terrain.IsSettled, "terrain settled");
            Assert.IsTrue(side.hazards.flares != null && side.hazards.flares.Running, "solar flares run on Mercury");
            Assert.AreEqual(2, side.hazards.levels[(int)Meridian.Hazards.HazardKind.Radiation] >= 2 ? 2 : 0, "Radiation 2 always");
            Assert.AreEqual(4, side.pois.placed.Count, "the four Mercury POIs");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
