using System.Collections;
using Meridian.Core;
using Meridian.Hazards;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-050 (PlayMode): stand on the floating station; a surface dive is lethal without Mk2 and survivable with it; the wind pushes on the deck, not below.</summary>
    public class VenusPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;
        PlayerVitals vitals;

        IEnumerator BootVenus()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Venus));
            side = director.PlanetSide;
            Assert.AreEqual(PlanetId.Venus, side.Config.id);
            side.hazards.enabled = false; // stepped by hand where it matters
            player = side.player;
            vitals = player.GetComponent<PlayerVitals>();
            vitals.maxHealth = 100f; vitals.health = 100f;
        }

        IEnumerator PutAt(float x, float y)
        {
            player.Body.position = new Vector2(x, y);
            player.transform.position = player.Body.position;
            player.Body.linearVelocity = Vector2.zero;
            float until = Time.realtimeSinceStartup + 15f;
            yield return null;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 90 && !player.Grounded; i++) yield return new WaitForFixedUpdate();
        }

        float Deck => Meridian.Planet.POI.PoiCatalog.MeridianStation.floatY + (336f - 62f) / 128f;

        [UnityTest]
        public IEnumerator StandOnTheFloatingStationInToxicHaze()
        {
            yield return BootVenus();
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            float until = Time.realtimeSinceStartup + 5f;
            while (side.pois.Solids.Count < 5 && Time.realtimeSinceStartup < until) yield return null;
            yield return PutAt(station.x + 10f, Deck + 1.5f);
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Grounded, "standing on the deck");
            Assert.AreEqual(Deck, player.Body.position.y, 0.15f, "on the deck surface, ~450 m above the ground");
            side.hazards.Step(0f);
            Assert.AreEqual(1, side.hazards.levels[(int)HazardKind.Toxic], "acid haze");
            Assert.AreEqual(0, side.hazards.levels[(int)HazardKind.Thermal]);
            Assert.AreEqual(1, side.hazards.EffectiveLevel, "the deck is the habitable layer");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator SurfaceDiveIsLethalWithoutMk2()
        {
            yield return BootVenus();
            var vent = VenusLandforms.Vents[0];
            int x = vent.x0 + 4;
            yield return PutAt(x + 0.5f, side.terrain.TopSolidY(x) + 1.1f);
            side.hazards.Equip(0);
            side.hazards.RestoreSuit();
            side.hazards.Step(0f);
            Assert.AreEqual(3, side.hazards.EffectiveLevel, "Thermal 3, Pressure 3 by the vent");
            float t = 0f;
            for (; t < 60f && !vitals.Dead; t += 0.1f) side.hazards.Step(0.1f);
            TestContext.Out.WriteLine($"[MERIDIAN] unprotected dive: dead after {t:F1} s");
            Assert.IsTrue(vitals.Dead, "an unprotected dive kills");
            Assert.LessOrEqual(t, 30f, "within 30 s");

            vitals.health = vitals.maxHealth;
            side.hazards.Equip(2); // Mk2 Thermal + Pressure (§7.4 gate)
            side.hazards.RestoreSuit();
            side.hazards.Step(0f);
            Assert.AreEqual(1, side.hazards.EffectiveLevel, "Mk2: 3 → 1");
            for (t = 0f; t < 180f && !vitals.Dead; t += 0.1f) side.hazards.Step(0.1f);
            Assert.IsFalse(vitals.Dead, "a 3-minute dive in Mk2");
            Assert.Greater(side.hazards.SuitIntegrity, 0f, "the suit still holds");
            side.hazards.Equip(0);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator WindPushesOnTheDeckNotBelow()
        {
            yield return BootVenus();
            Assert.IsTrue(side.wind != null && side.wind.enabled, "super-rotation on Venus");
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            float until = Time.realtimeSinceStartup + 5f;
            while (side.pois.Solids.Count < 5 && Time.realtimeSinceStartup < until) yield return null;
            yield return PutAt(station.x + 4f, Deck + 1.5f);
            float x0 = player.Body.position.x;
            for (int i = 0; i < 100; i++) yield return new WaitForFixedUpdate(); // 2 s idle
            float drift = player.Body.position.x - x0;
            TestContext.Out.WriteLine($"[MERIDIAN] deck drift {drift:F2} m in 2 s (wind {side.wind.Current:F2} m/s)");
            Assert.Greater(side.wind.Current, 2f, "a stiff wind on the deck");
            Assert.Greater(drift, 0.8f, "an idle surveyor drifts with it");

            int sx = 1900;
            yield return PutAt(sx + 0.5f, side.terrain.TopSolidY(sx) + 1.1f);
            x0 = player.Body.position.x;
            for (int i = 0; i < 100; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(0f, side.wind.Current, 1e-3f, "calm at the surface");
            Assert.AreEqual(x0, player.Body.position.x, 0.05f, "no drift below");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
