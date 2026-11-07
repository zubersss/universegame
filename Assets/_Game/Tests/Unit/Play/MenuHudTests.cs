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

        /// <summary>U-102: SETTINGS opens the panel from the title screen and the pause menu, BACK returns to the opener; the
        /// film toggle round-trips; the volume steps reach the listener and the ambient bed and persist like a restart.</summary>
        [UnityTest]
        public IEnumerator SettingsOpenFromBothMenusAndRoundTripTheFilmAndVolumes()
        {
            bool film = GameSettings.FilmEffects;
            float master = GameSettings.MasterVolume, music = GameSettings.MusicVolume, sfx = GameSettings.SfxVolume;
            MenuController.ShowOnBootOverride = true;
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var menu = MenuController.Instance;
            try
            {
                GameSettings.MasterVolume = 1f; GameSettings.MusicVolume = 1f; GameSettings.SfxVolume = 1f;
                Assert.IsTrue(menu.MainMenuOpen, "main menu on boot");
                menu.SettingsButton.onClick.Invoke();
                var panel = menu.Settings;
                Assert.IsTrue(menu.SettingsOpen, "SETTINGS on the title screen opens the panel");
                Assert.IsFalse(menu.MainMenuOpen, "the title menu hides behind it");
                Assert.IsTrue(menu.Blocking, "still blocking: time stays stopped");
                Assert.AreEqual(0f, Time.timeScale);
                var es = UnityEngine.EventSystems.EventSystem.current;
                Assert.NotNull(es, "an EventSystem for the keyboard");
                Assert.AreEqual(panel.FilmButton.gameObject, es.currentSelectedGameObject, "the keyboard starts on the film row");
                Assert.AreEqual(panel.MasterDown, panel.FilmButton.navigation.selectOnDown, "down walks to the volume rows");

                bool before = GameSettings.FilmEffects;
                panel.FilmButton.onClick.Invoke();
                Assert.AreEqual(!before, GameSettings.FilmEffects, "the film toggle flips the setting");
                StringAssert.Contains(GameSettings.FilmEffects ? "ON" : "OFF", panel.FilmButton.GetComponentInChildren<UnityEngine.UI.Text>().text, "and its label");
                panel.FilmButton.onClick.Invoke();
                Assert.AreEqual(before, GameSettings.FilmEffects, "the film toggle round-trips");

                for (int i = 0; i < 3; i++) panel.MasterDown.onClick.Invoke();
                Assert.AreEqual(0.7f, GameSettings.MasterVolume, 1e-5f, "three presses: 70 %");
                Assert.AreEqual(0.7f, AudioListener.volume, 1e-5f, "master drives the listener");
                StringAssert.Contains("70%", panel.MasterLabel.text);
                for (int i = 0; i < 5; i++) panel.MusicDown.onClick.Invoke();
                Assert.AreEqual(0.5f, GameSettings.MusicVolume, 1e-5f);
                var audio = Meridian.Audio.AudioDirector.Instance;
                Assert.NotNull(audio, "the AudioDirector in Core");
                Assert.AreEqual(audio.ambientVolume * 0.5f, audio.AmbientLevel, 1e-5f, "music scales the ambient bed");
                Assert.IsFalse(panel.SfxUp.interactable, "SFX at 100 %: + is off");
                panel.SfxDown.onClick.Invoke();
                Assert.AreEqual(audio.sfxVolume * 0.9f, audio.SfxLevel, 1e-5f, "SFX scales the one-shots");
                Assert.IsTrue(panel.SfxUp.interactable, "and + comes back");

                panel.BackButton.onClick.Invoke();
                Assert.IsFalse(menu.SettingsOpen, "BACK closes the panel");
                Assert.IsTrue(menu.MainMenuOpen, "BACK returns to the title menu");

                menu.NewButton.onClick.Invoke();
                Assert.AreEqual(1f, Time.timeScale);
                menu.OpenPause();
                menu.PauseSettingsButton.onClick.Invoke();
                Assert.IsTrue(menu.SettingsOpen, "SETTINGS on the pause menu opens the panel");
                Assert.IsFalse(menu.PauseOpen, "the pause menu hides behind it");
                Assert.AreEqual(menu.FilmButton, panel.FilmButton, "the Film effects toggle lives on the settings panel now");
                menu.CloseSettings(); // the Esc path
                Assert.IsTrue(menu.PauseOpen, "Esc / BACK returns to the pause menu");
                Assert.AreEqual(0f, Time.timeScale, "still paused");
                menu.ResumeButton.onClick.Invoke();
                Assert.AreEqual(1f, Time.timeScale, "resumed");
                Assert.IsTrue(director.PlanetSide.player.actions.FindActionMap(MeridianInput.OnFoot).enabled, "gameplay input back after the settings round trip (Block() kept its paused maps)");

                GameSettings.Reload(); // a restart reads PlayerPrefs again
                Assert.AreEqual(0.7f, GameSettings.MasterVolume, 1e-5f, "master persists");
                Assert.AreEqual(0.5f, GameSettings.MusicVolume, 1e-5f, "music persists");
                Assert.AreEqual(0.9f, GameSettings.SfxVolume, 1e-5f, "SFX persists");
                yield return null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                GameSettings.FilmEffects = film;
                GameSettings.MasterVolume = master; GameSettings.MusicVolume = music; GameSettings.SfxVolume = sfx;
            }
        }

        static IEnumerator Tap(UnityEngine.InputSystem.Keyboard keys, UnityEngine.InputSystem.Key key)
        {
            UnityEngine.InputSystem.InputSystem.QueueStateEvent(keys, new UnityEngine.InputSystem.LowLevel.KeyboardState(key));
            yield return null;
            UnityEngine.InputSystem.InputSystem.QueueStateEvent(keys, new UnityEngine.InputSystem.LowLevel.KeyboardState());
            yield return null;
        }

        /// <summary>U-124: Esc / Tab / N / B open and close the pause menu, the inventory, the catalogue and the crafting panel from a
        /// keyboard; each menu starts the keys on its first control; the paper draws 9-sliced exactly when B-151's file is on disk
        /// (until then the flat fill stays and nothing is logged); a title card asked for a planet shows only when its art exists and
        /// leaves after its 2.4 s.</summary>
        [UnityTest]
        public IEnumerator PaperPanelsOpenAndCloseFromTheKeyboard()
        {
            MenuController.ShowOnBootOverride = true;
            // The batch-mode Editor has no focused Game view: route the virtual keyboard to the game regardless of focus (FlightPlayTests' SetUp;
            // without it the 15:16 run's Esc never reached the menus). The keyboard goes in before the scene, so every map resolves with it.
            var settings = UnityEngine.InputSystem.InputSystem.settings;
            var savedEditor = settings.editorInputBehaviorInPlayMode;
            var savedBackground = settings.backgroundBehavior;
            settings.editorInputBehaviorInPlayMode = UnityEngine.InputSystem.InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
            settings.backgroundBehavior = UnityEngine.InputSystem.InputSettings.BackgroundBehavior.IgnoreFocus;
            var keys = UnityEngine.InputSystem.InputSystem.AddDevice<UnityEngine.InputSystem.Keyboard>("U124Keys");
            try
            {
                SceneDirector director = null;
                yield return Boot(d => director = d);
                var menu = MenuController.Instance;
                yield return null;
                var es = UnityEngine.EventSystems.EventSystem.current;
                Assert.NotNull(es, "an EventSystem for the keyboard");
                Assert.AreEqual(menu.NewButton.gameObject, es.currentSelectedGameObject, "the title menu starts the keys on NEW");
                menu.NewButton.onClick.Invoke();
                yield return null;

                yield return Tap(keys, UnityEngine.InputSystem.Key.Escape);
                Assert.IsTrue(menu.PauseOpen, "Esc pauses");
                Assert.AreEqual(menu.ResumeButton.gameObject, es.currentSelectedGameObject, "the pause menu starts on RESUME");
                Assert.AreEqual(menu.PauseCard.transform, menu.ResumeButton.transform.parent, "the pause buttons sit on the paper card");
                yield return Tap(keys, UnityEngine.InputSystem.Key.Escape);
                Assert.IsFalse(menu.PauseOpen, "Esc again resumes");
                Assert.AreEqual(1f, Time.timeScale);

                var inventory = Object.FindAnyObjectByType<InventoryPanel>();
                var catalogue = Object.FindAnyObjectByType<CataloguePanel>();
                var crafting = Object.FindAnyObjectByType<CraftingPanel>();
                Assert.NotNull(inventory, "the inventory panel in the game");
                Assert.NotNull(catalogue, "the catalogue panel in the game");
                Assert.NotNull(crafting, "the crafting panel in the game");
                var foot = director.PlanetSide.player.actions.FindActionMap(MeridianInput.OnFoot, true);
                Assert.IsTrue(foot.FindAction("Move").enabled, "on foot: Move is live");
                yield return Tap(keys, UnityEngine.InputSystem.Key.Tab);
                Assert.IsTrue(inventory.IsOpen, "Tab opens the inventory");
                // U-134: an open panel holds the surveyor still; its own keys stay live.
                Assert.IsFalse(foot.FindAction("Move").enabled, "U-134: Move held while a panel is open");
                Assert.IsFalse(foot.FindAction("Jump").enabled, "U-134: Jump held");
                Assert.IsTrue(foot.FindAction("Inventory").enabled && foot.FindAction("Catalogue").enabled && foot.FindAction("BuildMenu").enabled, "the panel keys stay live");
                var walker = director.PlanetSide.player.transform;
                float x0 = walker.position.x;
                UnityEngine.InputSystem.InputSystem.QueueStateEvent(keys, new UnityEngine.InputSystem.LowLevel.KeyboardState(UnityEngine.InputSystem.Key.D));
                for (int i = 0; i < 20; i++) yield return null;
                UnityEngine.InputSystem.InputSystem.QueueStateEvent(keys, new UnityEngine.InputSystem.LowLevel.KeyboardState());
                yield return null;
                Assert.AreEqual(x0, walker.position.x, 0.05f, "U-134: D does not walk the surveyor behind the open inventory");
                yield return Tap(keys, UnityEngine.InputSystem.Key.Tab);
                Assert.IsFalse(inventory.IsOpen, "Tab closes it");
                Assert.IsTrue(foot.FindAction("Move").enabled && foot.FindAction("Jump").enabled, "U-134: the last panel to close gives the keys back");
                yield return Tap(keys, UnityEngine.InputSystem.Key.N);
                Assert.IsTrue(catalogue.IsOpen, "N opens the catalogue");
                var picked = es.currentSelectedGameObject;
                Assert.NotNull(picked, "the catalogue starts the keys on a planet");
                Assert.NotNull(picked.GetComponent<UnityEngine.UI.Selectable>());
                yield return Tap(keys, UnityEngine.InputSystem.Key.N);
                Assert.IsFalse(catalogue.IsOpen, "N closes it");
                yield return Tap(keys, UnityEngine.InputSystem.Key.B);
                Assert.IsTrue(crafting.IsOpen, "B opens the crafting panel");
                Assert.IsFalse(foot.FindAction("Move").enabled, "U-134: held under the crafting panel too");
                yield return Tap(keys, UnityEngine.InputSystem.Key.B);
                Assert.IsFalse(crafting.IsOpen, "B closes it");
                Assert.IsTrue(foot.FindAction("Move").enabled, "and given back");
                Assert.IsFalse(PanelInput.Holding, "no panel holds the surveyor");

                // The paper: every probe answers, and it draws exactly when the art is on disk.
                float until = Time.realtimeSinceStartup + 10f;
                while ((!menu.PausePaper.HasValue || !menu.Settings.Paper.HasValue || !inventory.Paper.HasValue || !catalogue.Paper.HasValue || !crafting.Paper.HasValue)
                       && Time.realtimeSinceStartup < until) yield return null;
                void Paper(string what, bool? drew, string key)
                {
                    bool onDisk = File.Exists($"Assets/_Game/Art/{key}_color.png");
                    Assert.IsTrue(drew.HasValue, $"{what}: the probe for {key} answered");
                    Assert.AreEqual(onDisk, drew.Value, $"{what}: the paper draws exactly when {key} is on disk");
                }
                Paper("pause", menu.PausePaper, Meridian.Art.ArtKeys.Ui.PanelPause);
                Paper("settings", menu.Settings.Paper, Meridian.Art.ArtKeys.Ui.PanelSettings);
                Paper("inventory", inventory.Paper, Meridian.Art.ArtKeys.Ui.PanelInventory);
                Paper("catalogue", catalogue.Paper, Meridian.Art.ArtKeys.Ui.PanelScroll);
                Paper("crafting", crafting.Paper, Meridian.Art.ArtKeys.Ui.PanelSign);
                if (menu.PausePaper == true)
                {
                    Assert.AreEqual(UnityEngine.UI.Image.Type.Sliced, menu.PauseCard.type, "the pause card 9-slices");
                    Assert.AreNotEqual(Vector4.zero, menu.PauseCard.sprite.border, "with the json's border");
                }
                else Assert.AreEqual(Color.clear, menu.PauseCard.color, "no art: the pause card stays clear over the flat fill");

                // A title card: shown only when its art exists, gone after its 2.4 s.
                var cards = menu.TitleCards;
                Assert.NotNull(cards, "the title cards ride with the menus");
                cards.Show(Meridian.Planets.PlanetId.Mercury);
                string cardKey = Meridian.Art.ArtKeys.Ui.TitleCard(Meridian.Planets.PlanetId.Mercury);
                bool cardOnDisk = File.Exists($"Assets/_Game/Art/{cardKey}_color.png");
                until = Time.realtimeSinceStartup + 5f;
                while (cardOnDisk && cards.Showing == null && Time.realtimeSinceStartup < until) yield return null;
                Assert.AreEqual(cardKey, cards.LastAsked);
                if (cardOnDisk)
                {
                    Assert.AreEqual(cardKey, cards.Showing, "the Mercury card slides in");
                    until = Time.realtimeSinceStartup + TitleCard.TotalSeconds + 2f;
                    while (cards.Showing != null && Time.realtimeSinceStartup < until) yield return null;
                    Assert.IsNull(cards.Showing, "and leaves after its slide");
                    Assert.IsFalse(cards.Card.enabled);
                }
                else
                {
                    yield return null; yield return null;
                    Assert.IsNull(cards.Showing, "no card art: nothing shows");
                }
                yield return null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                if (keys != null) UnityEngine.InputSystem.InputSystem.RemoveDevice(keys);
                settings.editorInputBehaviorInPlayMode = savedEditor;
                settings.backgroundBehavior = savedBackground;
            }
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
