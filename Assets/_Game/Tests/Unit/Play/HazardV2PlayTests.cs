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
    /// <summary>
    /// U-049 (PlayMode): a solar flare kills an unprotected surveyor in the open within 30 s and not inside a
    /// shelter; the Envirosuit tier swaps the surveyor sheet; the HUD shows the worst hazard. Mercury's world
    /// arrives with U-048, so the hazards are configured for Mercury on the Earth scene (they only need its id
    /// and width).
    /// </summary>
    public class HazardV2PlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        bool wasCartoon = true;
        // D-132: the Envirosuit tier sheets (characters/surveyor/base, mk2) are the 3D path's surveyor; the cartoon surveyor has no tier sheets yet; the game runs Earth on the cartoon path, so this class switches it off for its run and restores it.
        [SetUp] public void ThreeDPath() { wasCartoon = Meridian.View2D.CartoonStage.Enabled; Meridian.View2D.CartoonStage.Enabled = false; }
        [TearDown] public void RestoreCartoon() { Meridian.View2D.CartoonStage.Enabled = wasCartoon; }
        PlanetSideRoot side;
        HazardSystem hazards;
        PlayerVitals vitals;

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            hazards = side.hazards;
            vitals = side.player.GetComponent<PlayerVitals>();
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            hazards.enabled = false; // the test steps it by hand
            // Walk away from the ship's warmth.
            var p = side.player.Body.position + new Vector2(-30f, 0f);
            int x = Mathf.FloorToInt(p.x);
            side.player.Body.position = new Vector2(x + 0.5f, side.terrain.TopSolidY(x) + 1.05f);
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
        }

        /// <summary>Mercury's hazards here, with the surveyor in Mercury's twilight band (flares reach it).</summary>
        void OnMercury(MercuryZone zone)
        {
            var mercury = GameState.Instance.catalog.Get(PlanetId.Mercury);
            hazards.ConfigureFor(mercury);
            float x = side.player.Body.position.x;
            // Shift Mercury's clock so x sits in the wanted zone: twilight at the dawn line, day a quarter world behind it, night a quarter ahead.
            float q = mercury.worldWidth * 0.25f;
            float dawn = zone == MercuryZone.Twilight ? x : zone == MercuryZone.Day ? x + q : x - q;
            var clock = Object.FindAnyObjectByType<TimeSystem>();
            hazards.mercuryClockOffset = Mathf.Repeat(dawn, mercury.worldWidth) * MercuryTerminator.CreepSecondsPerMetre - MercuryTerminator.Now(clock.GameSeconds);
            hazards.Step(0f);
            Assert.AreEqual(zone, hazards.Context.mercury, "placed in the " + zone);
        }

        float SurviveSeconds(float limit)
        {
            const float dt = 0.1f;
            for (float t = 0f; t < limit; t += dt)
            {
                hazards.Step(dt);
                if (vitals.Dead) return t + dt;
            }
            return float.PositiveInfinity;
        }

        [UnityTest]
        public IEnumerator FlareKillsInTheOpenWithin30sButNotInAShelter()
        {
            yield return Boot();
            OnMercury(MercuryZone.Twilight);
            hazards.flares.Force(0f);
            Assert.AreEqual(SolarFlares.Phase.Active, hazards.flares.Current);
            hazards.Step(0f);
            Assert.AreEqual(HazardRules.FlareLevel, hazards.EffectiveLevel, "Radiation 4 in the open (D-048)");
            Assert.AreEqual(HazardKind.Radiation, hazards.WorstKind);
            float died = SurviveSeconds(30f);
            TestContext.Out.WriteLine($"[MERIDIAN] flare in the open: dead after {died:F1} s");
            Assert.LessOrEqual(died, 30f, "an unprotected surveyor in the open dies within 30 s");

            // Again, inside a flare shelter.
            vitals.health = vitals.maxHealth;
            hazards.RestoreSuit();
            var shelter = new GameObject("TestShelter").AddComponent<FlareShelter>();
            shelter.transform.position = side.player.Body.position;
            hazards.Step(0f);
            Assert.Less(hazards.EffectiveLevel, HazardRules.FlareLevel, "the shelter stops the flare");
            Assert.IsTrue(float.IsPositiveInfinity(SurviveSeconds(SolarFlares.ActiveSeconds)), "survives the whole flare inside a shelter");
            Object.Destroy(shelter.gameObject);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator EnvirosuitTierSwapsTheSheetAndLowersLevels()
        {
            yield return Boot();
            var view = side.player.GetComponent<PlayerView>();
            Assert.AreEqual("characters/surveyor/base", view.SheetKey);
            OnMercury(MercuryZone.Day);
            Assert.AreEqual(3, hazards.EffectiveLevel, "Thermal 3 on the day side");
            hazards.Equip(2);
            Assert.AreEqual(1, hazards.EffectiveLevel, "Mk2: Thermal 3 → 1 (§7.3)");
            Assert.AreEqual(2, GameState.Instance.suitTier);
            Assert.AreEqual("characters/surveyor/mk2", view.SheetKey, "sheet swaps at equip");
            float until = Time.realtimeSinceStartup + 10f;
            while (Time.realtimeSinceStartup < until && (view.view.sprite == null || !view.view.sprite.name.StartsWith("mk2"))) yield return null;
            Assert.That(view.view.sprite.name, Does.StartWith("mk2"), "the Mk2 sheet is drawn");
            hazards.Equip(3);
            Assert.AreEqual(0, hazards.EffectiveLevel, "Mk3 → 0");
            hazards.Equip(0);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator HudShowsTheWorstHazard()
        {
            yield return Boot();
            var hud = Object.FindAnyObjectByType<Meridian.UI.SideHud>();
            OnMercury(MercuryZone.Day);
            hud.enabled = true;
            yield return null;
            Assert.AreEqual("THERMAL", hud.HazardLabel.text);
            Assert.AreEqual("3", hud.CryoText.text);
            OnMercury(MercuryZone.Night);
            yield return null;
            Assert.AreEqual("CRYO", hud.HazardLabel.text);
            OnMercury(MercuryZone.Twilight); // (re)configuring restarts the flare schedule: force after
            hazards.flares.Force(0f);
            hazards.Step(0f);
            yield return null;
            Assert.AreEqual("RADIATION", hud.HazardLabel.text);
            Assert.AreEqual("4", hud.CryoText.text, "a flare reads 4");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
