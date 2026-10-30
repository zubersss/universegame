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

            menu.NewButton.onClick.Invoke();
            Assert.IsFalse(menu.MainMenuOpen);
            Assert.AreEqual(1f, Time.timeScale);
            Assert.IsTrue(actions.FindActionMap(MeridianInput.OnFoot).enabled, "gameplay input back");

            menu.OpenPause();
            Assert.IsTrue(menu.PauseOpen);
            Assert.AreEqual(0f, Time.timeScale, "paused");
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
        public IEnumerator SideHudShowsHealthFuelAndEscapeLine()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var side = director.PlanetSide;
            var hud = side.sideHud;
            Assert.NotNull(hud, "SideHud on PlanetSide");
            side.player.GetComponent<PlayerVitals>().health = 64f;
            GameState.Instance.fuel = 41f;
            yield return null; yield return null;
            Assert.AreEqual("64", hud.HealthText.text);
            Assert.AreEqual(0.64f, hud.HealthFill.fillAmount, 1e-3f);
            Assert.AreEqual("41", hud.FuelText.text);
            Assert.AreEqual(0.41f, hud.FuelFill.fillAmount, 1e-3f);
            Assert.AreEqual(1f, hud.OxygenFill.fillAmount, "oxygen placeholder full");
            Assert.AreEqual(720f / 800f * SideHud.BarHeight, hud.EscapeMarker.anchoredPosition.y, 0.01f, "Escape Line marker at y 720 of 800");
            float playerY = side.player.Body.position.y;
            Assert.AreEqual(playerY / 800f * SideHud.BarHeight, hud.YouMarker.anchoredPosition.y, 0.5f, "player marker");
            Assert.AreEqual(Mathf.RoundToInt(playerY - 320f).ToString(), hud.AltText.text, "altitude above the Datum");

            // Aboard: the ship block appears; Earth thrust 12 > g 9.81 so no stranded warning.
            side.ship.GetComponent<ShipBoarding>().ForceAboard();
            yield return null; yield return null;
            var shipHud = side.shipHud;
            Assert.IsTrue(shipHud.VerticalSpeed.gameObject.activeInHierarchy, "ship block visible aboard");
            Assert.AreEqual("1.2", shipHud.ThrustToWeight.text, "T/W 12 / 9.81");
            Assert.IsFalse(shipHud.Warning.enabled);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator TopHudShowsSpeedFuelAndWell()
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
            GameState.Instance.fuel = 77f;
            for (int i = 0; i < 3; i++) yield return new WaitForFixedUpdate();
            yield return null;
            var hud = director.Space.GetComponentInChildren<SpaceHud>();
            Assert.AreEqual(Mathf.RoundToInt(ship.Velocity.magnitude).ToString(), hud.Speed.text);
            Assert.AreEqual("77", hud.Fuel.text);
            Assert.AreEqual("earth", hud.WellName.text, "well indicator names the body");
            Assert.AreEqual((Mathf.Round(ship.LastPull.magnitude * 10f) / 10f).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture), hud.Well.text);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
