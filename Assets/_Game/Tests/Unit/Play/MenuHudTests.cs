using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Player;
using Meridian.Save;
using Meridian.Ship;
using Meridian.Space;
using Meridian.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-015 (PlayMode): main menu, pause, side HUD, ship block, top HUD in the real Core flow.</summary>
    public class MenuHudTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string saveRoot;

        [SetUp]
        public void SetUp()
        {
            saveRoot = Path.Combine(Application.temporaryCachePath, "meridian_saves_ui_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = saveRoot;
        }

        [TearDown]
        public void TearDown()
        {
            MenuController.ShowOnBootOverride = null;
            SaveSystem.RootOverride = null;
            Time.timeScale = 1f;
            if (Directory.Exists(saveRoot)) Directory.Delete(saveRoot, true);
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
            yield return null;
            done(director);
        }

        [UnityTest]
        public IEnumerator MainMenuThenPauseThenSaveThenContinueEnabled()
        {
            MenuController.ShowOnBootOverride = true;
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var menu = MenuController.Instance;
            Assert.NotNull(menu, "MenuController in Core");
            Assert.IsTrue(menu.MainMenuOpen, "main menu on boot");
            Assert.AreEqual(0f, Time.timeScale, "time stopped behind the menu");
            var actions = director.PlanetSide.player.actions;
            Assert.IsFalse(actions.FindActionMap(MeridianInput.OnFoot).enabled, "gameplay input off");
            Assert.IsFalse(menu.ContinueButton.interactable, "no save yet: Continue disabled");
            // U-031: nothing of the HUD draws through the menu.
            var hudCanvas = director.PlanetSide.sideHud.GetComponentInChildren<Canvas>(true);
            yield return null;
            Assert.IsFalse(hudCanvas.enabled, "side HUD hidden behind the main menu");

            menu.NewButton.onClick.Invoke();
            Assert.IsFalse(menu.MainMenuOpen);
            Assert.AreEqual(1f, Time.timeScale);
            Assert.IsTrue(actions.FindActionMap(MeridianInput.OnFoot).enabled, "gameplay input back");
            yield return null;
            Assert.IsTrue(hudCanvas.enabled, "side HUD back in play");

            menu.OpenPause();
            Assert.IsTrue(menu.PauseOpen);
            Assert.AreEqual(0f, Time.timeScale, "paused");
            yield return null;
            Assert.IsFalse(hudCanvas.enabled, "side HUD hidden behind the pause menu");
            menu.SaveButton.onClick.Invoke();
            Assert.IsTrue(SaveSystem.Instance.HasSave, "Save from the pause menu writes the slot");
            menu.ResumeButton.onClick.Invoke();
            Assert.IsFalse(menu.PauseOpen);
            Assert.AreEqual(1f, Time.timeScale);

            menu.OpenMain();
            Assert.IsTrue(menu.ContinueButton.interactable, "a save exists: Continue enabled");
            menu.ContinueButton.onClick.Invoke();
            Assert.IsFalse(menu.MainMenuOpen);
            yield return null;
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator BatchRunsSkipTheBootMenu()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            Assert.IsFalse(MenuController.Instance.Blocking, "tests and tools are not blocked by the menu");
            Assert.AreEqual(1f, Time.timeScale);
        }

        [UnityTest]
        public IEnumerator SideHudShowsHealthAndEscapeLine()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var side = director.PlanetSide;
            var hud = side.sideHud;
            Assert.NotNull(hud, "SideHud on PlanetSide");
            // U-093: the top gauge is Suit power = (suit integrity + reserve) / 200: full suit + reserve 64 = 82 %.
            side.hazards.enabled = false;
            side.hazards.RestoreSuit();
            side.player.GetComponent<PlayerVitals>().health = 64f;
            yield return null; yield return null;
            Assert.AreEqual("82", hud.HealthText.text);
            Assert.AreEqual(0.82f, hud.HealthFill.fillAmount, 1e-3f);
            Assert.AreEqual(1f, hud.OxygenFill.fillAmount, "oxygen placeholder full");
            Assert.AreEqual(720f / 800f * SideHud.BarHeight, hud.EscapeMarker.anchoredPosition.y, 0.01f, "Escape Line marker at y 720 of 800");
            float playerY = side.player.Body.position.y;
            Assert.AreEqual(playerY / 800f * SideHud.BarHeight, hud.YouMarker.anchoredPosition.y, 0.5f, "player marker");
            Assert.AreEqual(Mathf.RoundToInt(playerY - 320f).ToString(), hud.AltText.text, "altitude above the Datum");

            // Aboard: the ship block appears; Earth T/W 12 / 9.81 = 1.22 ≥ 1.2, so white and no warning (D-106).
            side.ship.GetComponent<ShipBoarding>().ForceAboard();
            yield return null; yield return null;
            var shipHud = side.shipHud;
            Assert.IsTrue(shipHud.VerticalSpeed.gameObject.activeInHierarchy, "ship block visible aboard");
            Assert.AreEqual("1.2", shipHud.ThrustToWeight.text, "T/W 12 / 9.81");
            Assert.IsFalse(shipHud.Warning.enabled);
            Assert.AreEqual(ShipHud.TwrState.Ok, shipHud.State);
            // D-106: 1.08 (Mk1 on Neptune) reads amber with the slow-climb line; 1.22 back to white.
            shipHud.Apply(ShipHud.StateFor(12f / 11.15f));
            Assert.AreEqual(ShipHud.TwrState.Amber, shipHud.State, "T/W 1.08 is amber");
            Assert.AreEqual(ShipHud.Amber, shipHud.ThrustToWeight.color);
            Assert.IsTrue(shipHud.Warning.enabled);
            shipHud.Apply(ShipHud.StateFor(12f / 9.81f));
            Assert.AreEqual(ShipHud.TwrState.Ok, shipHud.State, "T/W 1.22 is not amber");
            Assert.AreNotEqual(ShipHud.Amber, shipHud.ThrustToWeight.color);
            Assert.IsFalse(shipHud.Warning.enabled);

            // U-104 (B-121, D-090, D-103): the dials track their meters at the 12 Hz step, the painted Escape Line carries its
            // lettered sign on the line, the ship block shows the four rows, every HUD string draws in the HUD face.
            float until = Time.realtimeSinceStartup + 15f;
            while (!hud.GaugesReady && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsTrue(hud.GaugesReady, "ui/hud/gauges armed the three dials");
            float tickUntil = Time.time + 0.3f;
            while (Time.time < tickUntil) yield return null; // past a 12 Hz tick
            Assert.AreEqual(0.82f, hud.SuitGauge.Motion.Shown, 0.01f, "suit power dial within 1 % of its meter");
            Assert.AreEqual(1f, hud.OxygenGauge.Motion.Shown, 0.01f, "oxygen dial full (placeholder meter)");
            Assert.AreEqual(1f / SideHud.GravityFullScale, hud.GravityGauge.Motion.Shown, 0.01f, "Earth: 1 g on the 3 g dial");
            float z = hud.SuitGauge.Needle.rectTransform.localEulerAngles.z; if (z > 180f) z -= 360f;
            Assert.AreEqual(hud.SuitGauge.Spec.Angle(0.82f), z, GaugeNeedle.WobbleDeg + 0.5f, "the needle on its sweep (a wobble allowed)");
            Assert.IsFalse(hud.HealthFill.transform.parent.gameObject.activeSelf, "the bar stepped aside for the dial");
            Assert.NotNull(UiTheme.Active.hudTtf, "Patrick Hand in the theme (D-090)");
            StringAssert.Contains("PatrickHand", hud.HealthText.font.name, "HUD numerals in the HUD face");
            var band = side.escapeBand;
            until = Time.realtimeSinceStartup + 15f;
            while (!(band.UsesArt && band.Sign != null && band.Sign.sprite != null) && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsTrue(band.UsesArt, "ui/hud/escape_line drawn");
            yield return null;
            Assert.AreEqual((float)side.Config.EscapeLineY, band.SignY, 0.01f, "the sign stands on the Escape Line");
            Assert.AreEqual(EscapeLineBand.Lettering, band.SignLettering, "lettered ESCAPE LINE at runtime");
            Assert.IsFalse(band.band.enabled, "the old band is off");
            Assert.AreEqual("0", shipHud.Tilt.text, "level on the pad");
            Assert.IsTrue(int.TryParse(shipHud.Altitude.text, out int agl) && agl >= 0 && agl <= 3, $"skids on the pad: AGL {shipHud.Altitude.text}");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator TopHudShowsSpeedAndWell()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            director.SetView(ViewMode.Space);
            yield return null;
            var ship = director.Space.GetComponentInChildren<SpaceShip>();
            ship.externalInput = true;
            ship.intent = default;
            var earth = ship.world.Find("earth").Value;
            ship.Position = earth.position + new Vector2(0f, 50f); // inside Earth's well (2R)
            ship.Velocity = new Vector2(30f, 0f);
            for (int i = 0; i < 3; i++) yield return new WaitForFixedUpdate();
            yield return null;
            var hud = director.Space.GetComponentInChildren<SpaceHud>();
            Assert.AreEqual(Mathf.RoundToInt(ship.Velocity.magnitude).ToString(), hud.Speed.text);
            Assert.AreEqual("earth", hud.WellName.text, "well indicator names the body");
            Assert.AreEqual((Mathf.Round(ship.LastPull.magnitude * 10f) / 10f).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture), hud.Well.text);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
