using System.Collections;
using Meridian.Core;
using Meridian.Hazards;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-068 (PlayMode): the suit meter shows a giant's band level when the surveyor stands at that height. The
    /// cloud column arrives with U-061, so (like HazardV2PlayTests for Mercury) the hazards are configured for a
    /// giant on the Earth scene and read a stub body placed at each band's height.
    /// </summary>
    public class GiantBandsPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator SuitMeterShowsTheBandLevel()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            var hazards = side.hazards;
            hazards.enabled = false; // stepped by hand
            var hud = Object.FindAnyObjectByType<Meridian.UI.SideHud>();
            hud.enabled = true;

            var stub = new GameObject("GiantBandStub").transform;
            float x = side.player.Body.position.x - 30f; // away from the ship's warmth
            hazards.body = stub;
            hazards.Equip(0);

            var cases = new (PlanetId planet, float y, string kind, string level)[]
            {
                (PlanetId.Jupiter, 1000f, "RADIATION", "3"), // Deck 1: belts
                (PlanetId.Jupiter, 750f, "RADIATION", "1"),  // Deck 2: shielded to 1
                (PlanetId.Jupiter, 280f, "THERMAL", "2"),    // Deep
                (PlanetId.Saturn, 1000f, "CRYO", "2"),       // Deck 1
                (PlanetId.Uranus, 750f, "CRYO", "3"),        // Deck 2
                (PlanetId.Neptune, 120f, "PRESSURE", "3"),   // low Deep
            };
            foreach (var c in cases)
            {
                hazards.ConfigureFor(GameState.Instance.catalog.Get(c.planet));
                stub.position = new Vector3(x, c.y, 0f);
                hazards.Step(0f);
                yield return null;
                Assert.AreEqual(c.kind, hud.HazardLabel.text, $"{c.planet} y {c.y}");
                Assert.AreEqual(c.level, hud.CryoText.text, $"{c.planet} y {c.y}");
            }
            Object.Destroy(stub.gameObject);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
