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
using UnityEngine.UI;

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
                // U-140: the recipes page inside the paper; PageDown / PageUp turn the page, the row count says where.
                StringAssert.Contains(" of ", crafting.RowCount.text, "the faded-ink row count");
                if (crafting.Pages > 1)
                {
                    Assert.AreEqual(0, crafting.Page);
                    yield return Tap(keys, UnityEngine.InputSystem.Key.PageDown);
                    Assert.AreEqual(1, crafting.Page, "PageDown turns the recipes page");
                    yield return Tap(keys, UnityEngine.InputSystem.Key.PageUp);
                    Assert.AreEqual(0, crafting.Page, "PageUp turns it back");
                    Assert.IsFalse(crafting.PrevButton.interactable, "the first page: PREV greyed");
                }
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
                Paper("crafting", crafting.Paper, CraftingPanel.PaperKey); // D-149: the inventory paper
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

        /// <summary>U-181 (B-208): every flat paper in the game (the pause card, the inventory, the Skill Tree's node card and cost tag, the
        /// panels' frames) carries the tiled grain: a "Grain" child in the paper's own shape masking a Tiled grain at 1 texel = 1 canvas px
        /// (1 screen px at 1080p).</summary>
        [UnityTest]
        public IEnumerator EveryFlatPaperCarriesTheTiledGrain()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var hud = director.PlanetSide.sideHud;
            hud.Inventory.SetOpen(true); hud.Inventory.SetOpen(false);
            hud.Skills.SetOpen(true);
            float until = Time.realtimeSinceStartup + 6f;
            while (Time.realtimeSinceStartup < until) yield return null; // the papers and the grain load
            var flat = new System.Collections.Generic.HashSet<string>();
            foreach (var k in UiPaper.Grained) flat.Add(k.Substring(k.LastIndexOf('/') + 1) + "_color");
            int papers = 0;
            var seen = new System.Text.StringBuilder();
            foreach (var img in Object.FindObjectsByType<Image>(FindObjectsInactive.Include))
            {
                if (img.sprite == null || img.name == "Grain" || !flat.Contains(img.sprite.texture.name)) continue;
                papers++;
                seen.Append(' ').Append(img.name).Append('(').Append(img.sprite.texture.name).Append(')');
                var tile = UiPaper.GrainOf(img);
                Assert.NotNull(tile, $"{img.name} ({img.sprite.texture.name}): its grain");
                Assert.AreEqual(Image.Type.Tiled, tile.type, img.name);
                Assert.NotNull(tile.sprite, img.name + ": the grain loaded");
                StringAssert.StartsWith("grain", tile.sprite.texture.name);
                Assert.IsNotNull(tile.transform.parent.GetComponent<Mask>(), img.name + ": masked by the paper's shape");
                Assert.IsFalse(tile.transform.parent.GetComponent<Mask>().showMaskGraphic, "the mask draws nothing");
                Assert.AreSame(img.sprite, tile.transform.parent.GetComponent<Image>().sprite, "the mask is the paper's own shape");
                Assert.AreEqual(0, tile.transform.parent.GetSiblingIndex(), "over the paper, under what is on it");
                float refPpu = tile.canvas != null ? tile.canvas.referencePixelsPerUnit : 100f;
                float tilePx = tile.sprite.rect.width / tile.sprite.pixelsPerUnit * refPpu / tile.pixelsPerUnitMultiplier;
                Assert.AreEqual(tile.sprite.rect.width, tilePx, 0.01f, img.name + ": 1 texel = 1 canvas px (a 128-texel tile spans 128 px at 1080p)");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u181 {papers} flat papers carry the grain:{seen}");
            Assert.GreaterOrEqual(papers, 3, "the pause card, the inventory, the Skill Tree's card at least");
            hud.Skills.SetOpen(false);
            LogAssert.NoUnexpectedReceived();
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

        /// <summary>
        /// U-201 (LEAD's read of smoke_42 and of the Editor capture u193/1: an empty outlined bar with a small box between the Rank medallion
        /// and PACK, topside): the depth tag, its chip and their eight ink edges are on exactly while a depth is shown. Awake used to switch
        /// off the two fills only, so the edges drew from every boot until the first dig below the Surface Line and back. A fresh boot
        /// topside, a board and an exit, the inventory opened and closed: all off; below the line: all on with the depth; back up: all off.
        /// </summary>
        [UnityTest]
        public IEnumerator TheDepthTagDrawsOnlyWithADepth()
        {
            var settings = UnityEngine.InputSystem.InputSystem.settings;
            var savedEditor = settings.editorInputBehaviorInPlayMode;
            var savedBackground = settings.backgroundBehavior;
            settings.editorInputBehaviorInPlayMode = UnityEngine.InputSystem.InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
            settings.backgroundBehavior = UnityEngine.InputSystem.InputSettings.BackgroundBehavior.IgnoreFocus;
            var keys = UnityEngine.InputSystem.InputSystem.AddDevice<UnityEngine.InputSystem.Keyboard>("U201Keys");
            try
            {
                SceneDirector director = null;
                yield return Boot(d => director = d);
                var side = director.PlanetSide;
                var hud = side.sideHud;
                side.hazards.enabled = false;
                side.creatures.autoSpawn = false; side.creatures.DespawnAll();
                for (int i = 0; i < 5; i++) yield return null;
                Assert.AreEqual(10, hud.DepthParts.Count, "the tag and the chip, each with its four ink edges");
                void AllOff(string when)
                {
                    Assert.AreEqual("", hud.DepthText.text, $"{when}: no depth string topside");
                    foreach (var img in hud.DepthParts) Assert.IsFalse(img.enabled, $"{when}: {img.transform.parent.name}/{img.name} draws with no depth shown");
                }
                Assert.IsTrue(Meridian.Mining.DigRun.Topside(side.terrain, side.player.Body.position), "the surveyor starts topside");
                AllOff("a fresh boot topside");

                var boarding = side.ship.GetComponent<ShipBoarding>();
                boarding.ForceAboard();
                yield return null; yield return null;
                Assert.IsTrue(boarding.TryExit(), "the surveyor steps out again");
                for (int i = 0; i < 30 && !side.player.Grounded; i++) yield return new WaitForFixedUpdate();
                yield return null; yield return null;
                if (Meridian.Mining.DigRun.Topside(side.terrain, side.player.Body.position)) AllOff("after a board and an exit");

                var inventory = Object.FindAnyObjectByType<InventoryPanel>();
                Assert.NotNull(inventory, "the inventory panel in the game");
                yield return Tap(keys, UnityEngine.InputSystem.Key.Tab);
                Assert.IsTrue(inventory.IsOpen, "Tab opens the inventory");
                yield return null;
                yield return Tap(keys, UnityEngine.InputSystem.Key.Tab);
                Assert.IsFalse(inventory.IsOpen, "Tab closes it");
                yield return null; yield return null;
                if (Meridian.Mining.DigRun.Topside(side.terrain, side.player.Body.position)) AllOff("after the inventory opened and closed");

                // Below the Surface Line (the body held there, its transform with it): the tag, the chip and every edge with the depth.
                var body = side.player.Body;
                var up = body.position;
                var below = new Vector2(up.x, Meridian.Mining.DigRun.LineAt(side.terrain, up.x) - 4.5f);
                body.simulated = false;
                body.position = below; side.player.transform.position = below;
                yield return null; yield return null;
                StringAssert.StartsWith("DEPTH 4 m", hud.DepthText.text, "4.5 m under the Surface Line");
                foreach (var img in hud.DepthParts) Assert.IsTrue(img.enabled, $"below the line: {img.transform.parent.name}/{img.name} is off");

                body.position = up; side.player.transform.position = up;
                body.simulated = true;
                yield return null; yield return null;
                AllOff("back topside");
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

        /// <summary>
        /// U-147 (D-149): the HUD's lettering sits on small paper tags in ink, at 1080p and at 720p (the canvas laid out at each screen size as its
        /// scaler would: 1920×1080 units scaled to the screen): every tag on screen, no two tags overlapping, each tag's lettering drawn inside it
        /// (the longest strings set: RADIATION, -99.9/s, -2000, the longest POI name at 3999 m), ink with the light rim off; with the gauge art in,
        /// no light-blue lettering left on the HUD.
        /// </summary>
        [UnityTest]
        public IEnumerator TheHudLetteringSitsOnPaperTags()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var hud = director.PlanetSide.sideHud;
            float until = Time.realtimeSinceStartup + 10f;
            while (!hud.GaugesReady && Time.realtimeSinceStartup < until) yield return null;
            yield return null;
            Assert.GreaterOrEqual(hud.Tags.Count, 4 + hud.MarkerTags.Count, "hazard, suit, escape, altitude and a tag per POI row");
            var canvas = hud.HazardLabel.canvas.rootCanvas;
            var crt = (RectTransform)canvas.transform;
            var mode = canvas.renderMode;
            var theme = UiTheme.Active;
            try
            {
                canvas.renderMode = RenderMode.WorldSpace;
                foreach (var screen in new[] { new Vector2(1920f, 1080f), new Vector2(1280f, 720f) })
                {
                    crt.sizeDelta = new Vector2(1920f, 1080f);
                    crt.localScale = Vector3.one * (screen.y / 1080f);
                    crt.position = Vector3.zero;
                    hud.HazardLabel.text = "RADIATION"; hud.CryoText.text = "4"; hud.SuitRateText.text = "-99.9/s"; hud.AltText.text = "-2000";
                    for (int i = 0; i < hud.MarkerTags.Count; i++)
                    {
                        hud.MarkerTags[i].gameObject.SetActive(true);
                        hud.MarkerNames[i].text = "m  MERIDIAN STATION"; hud.MarkerDistances[i].text = "3999";
                    }
                    Canvas.ForceUpdateCanvases();
                    var bounds = WorldRect(crt);
                    var shown = new System.Collections.Generic.List<Rect>();
                    for (int i = 0; i < hud.Tags.Count; i++)
                    {
                        var tag = hud.Tags[i];
                        if (!tag.gameObject.activeInHierarchy) continue;
                        var r = WorldRect(tag.rectTransform);
                        string at = $"{screen.y}p {tag.name}";
                        Assert.IsTrue(Inside(r, bounds, 0.5f), $"{at} {r} on screen ({bounds})");
                        foreach (var other in shown) Assert.IsFalse(r.Overlaps(Shrink(other, 0.5f)), $"{at} {r} clear of {other}");
                        shown.Add(r);
                        foreach (var t in hud.TagLetters[i])
                        {
                            if (t == null || !t.enabled || string.IsNullOrEmpty(t.text)) continue;
                            Assert.AreEqual(UiKit.Ink, t.color, $"{at}: {t.name} in ink");
                            var rim = t.GetComponent<UnityEngine.UI.Outline>();
                            Assert.IsTrue(rim == null || !rim.enabled, $"{at}: {t.name} without the light rim");
                            var drawn = Drawn(t);
                            Assert.IsTrue(drawn.xMin >= r.xMin - 1f && drawn.xMax <= r.xMax + 1f, $"{at}: {t.name} '{t.text}' {drawn} across its tag {r}");
                            Assert.IsTrue(drawn.center.y > r.yMin && drawn.center.y < r.yMax, $"{at}: {t.name} centred on its tag");
                            Assert.LessOrEqual(t.fontSize * t.rectTransform.lossyScale.y, r.height + 2f, $"{at}: {t.name} fits its tag's height");
                        }
                    }
                }
                if (hud.GaugesReady)
                {
                    foreach (var t in canvas.GetComponentsInChildren<UnityEngine.UI.Text>(false))
                    {
                        if (!t.enabled || string.IsNullOrEmpty(t.text) || t == hud.StormText) continue;
                        bool light = Mathf.Abs(t.color.r - theme.text.r) < 0.02f && Mathf.Abs(t.color.g - theme.text.g) < 0.02f && Mathf.Abs(t.color.b - theme.text.b) < 0.02f;
                        Assert.IsFalse(light, $"{t.name} '{t.text}' still in the light-blue HUD colour");
                    }
                }
                else TestContext.Out.WriteLine("[MERIDIAN] U-147: the gauge art is not in; the light-blue check waits for it");
            }
            finally
            {
                canvas.renderMode = mode;
            }
        }

        static Rect WorldRect(RectTransform rt)
        {
            var c = new Vector3[4];
            rt.GetWorldCorners(c);
            return Rect.MinMaxRect(c[0].x, c[0].y, c[2].x, c[2].y);
        }

        static bool Inside(Rect r, Rect outer, float tol) => r.xMin >= outer.xMin - tol && r.yMin >= outer.yMin - tol && r.xMax <= outer.xMax + tol && r.yMax <= outer.yMax + tol;

        static Rect Shrink(Rect r, float by) => Rect.MinMaxRect(r.xMin + by, r.yMin + by, r.xMax - by, r.yMax - by);

        /// <summary>The span a one-line Text draws (its preferred size placed by its alignment in its box), in world units.</summary>
        static Rect Drawn(UnityEngine.UI.Text t)
        {
            var box = WorldRect(t.rectTransform);
            float w = t.preferredWidth * t.rectTransform.lossyScale.x, h = t.preferredHeight * t.rectTransform.lossyScale.y;
            int col = (int)t.alignment % 3; // 0 left, 1 centre, 2 right
            float x0 = col == 0 ? box.xMin : col == 2 ? box.xMax - w : box.center.x - w * 0.5f;
            return new Rect(x0, box.center.y - h * 0.5f, w, h);
        }
    }
}
