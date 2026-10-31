using System.Collections;
using Meridian.Core;
using Meridian.Hazards;
using Meridian.Planets;
using Meridian.Player;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-029 (PlayMode): Mars night drains the suit, the ship stops it, Cryo 3 kills an unprotected surveyor within 30 s, the HUD shows it.</summary>
    public class HazardPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        HazardSystem hazards;
        PlayerController player;
        PlayerVitals vitals;

        IEnumerator BootOnMarsAtNight()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Mars));
            side = director.PlanetSide;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout + 20f) yield return null;
            hazards = side.hazards;
            Assert.NotNull(hazards, "HazardSystem on PlanetSide");
            player = side.player;
            vitals = player.GetComponent<PlayerVitals>();
            if (side.hazards.boarding.Aboard) Assert.IsTrue(side.hazards.boarding.TryExit(), "step out of the ship");
            side.dayNight.Override = 0f; // midnight
            yield return MoveAwayFromShip(15f);
            vitals.Restore();
            hazards.RestoreSuit();
        }

        IEnumerator MoveAwayFromShip(float metres)
        {
            float x = side.ship.Body.position.x - metres;
            int surface = side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(Mathf.FloorToInt(x)));
            player.Body.position = new Vector2(x, surface + 2f);
            player.Body.linearVelocity = Vector2.zero;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
        }

        [UnityTest]
        public IEnumerator MarsNightDrainsTheSuitAndTheShipStopsIt()
        {
            yield return BootOnMarsAtNight();
            yield return null;
            Assert.AreEqual(2, hazards.CryoLevel, "Mars night: Cryo 2");
            Assert.IsFalse(hazards.Warm);
            float before = hazards.SuitIntegrity;
            float t0 = Time.time;
            while (Time.time - t0 < 2f) yield return null;
            float lost = before - hazards.SuitIntegrity;
            TestContext.Out.WriteLine($"[MERIDIAN] Mars night: suit {before:F1} → {hazards.SuitIntegrity:F1} in {Time.time - t0:F2} s");
            Assert.AreEqual(1.5f * (Time.time - t0), lost, 0.3f, "drains 1.5/s at Cryo 2");
            Assert.AreEqual(100f, vitals.health, 1e-3f, "health untouched while the suit holds");
            var hud = side.sideHud;
            Assert.AreEqual("2", hud.CryoText.text, "HUD shows the level");
            Assert.AreEqual("-1.5/s", hud.SuitRateText.text, "HUD shows the drain");
            Assert.Less(hud.SuitFill.fillAmount, 1f, "suit bar going down");

            // Walk up to the ship: its warmth stops the drain and recharges the suit.
            hazards.Step(20f); // 20 s more of Mars night: well below full, so the recharge shows
            float low = hazards.SuitIntegrity;
            yield return MoveAwayFromShip(3f);
            Assert.IsTrue(hazards.Warm, "within 6 m of the ship");
            Assert.AreEqual(0, hazards.EffectiveLevel);
            Assert.GreaterOrEqual(hazards.SuitIntegrity, low, "no more drain by the ship");
            yield return null;
            StringAssert.StartsWith("+", hud.SuitRateText.text, "HUD shows the recharge");

            // Aboard is warm too, wherever the ship is.
            yield return MoveAwayFromShip(15f);
            Assert.IsFalse(hazards.Warm);
            side.hazards.boarding.ForceAboard();
            yield return null;
            Assert.IsTrue(hazards.Warm, "aboard the ship");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator Cryo3KillsAnUnprotectedSurveyorWithin30Seconds()
        {
            yield return BootOnMarsAtNight();
            var time = Object.FindAnyObjectByType<TimeSystem>();
            side.dustStorm.Force(0.1f, 300f);
            time.Advance(0.2f);
            yield return null;
            Assert.AreEqual(3, hazards.CryoLevel, "Mars night + dust storm: Cryo 3");
            Assert.IsFalse(hazards.Warm);

            hazards.enabled = false; // step 30 s of exposure by hand
            hazards.RestoreSuit();
            vitals.Restore();
            float t = 0f, dt = 0.02f;
            bool aliveAt29 = true;
            while (!vitals.Dead && t < 60f)
            {
                hazards.Step(dt);
                t += dt;
                if (t > 29f && t < 29f + dt * 1.5f) aliveAt29 = !vitals.Dead;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] Cryo 3 unprotected: dead after {t:F2} s");
            Assert.IsTrue(vitals.Dead, "lethal");
            Assert.LessOrEqual(t, 30f + dt, "within 30 s");
            Assert.IsTrue(aliveAt29, "not much sooner than 30 s (suit then health)");

            // A Cryo Mk1 module (M3) would make the same exposure level 2: survivable for 30 s.
            vitals.Restore();
            hazards.RestoreSuit();
            hazards.protection[(int)HazardKind.Cryo] = 1;
            for (float s = 0f; s < 30f; s += dt) hazards.Step(dt);
            Assert.IsFalse(vitals.Dead, "Mk1 protection: alive after 30 s");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
