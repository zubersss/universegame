using System.Collections.Generic;
using Meridian.Core;
using Meridian.Player;
using Meridian.Save;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.UI;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// Main menu (New, Continue, Quit) and pause menu (Esc: Resume, Save, Main Menu), U-015.
    /// While either is open, time stops and the gameplay input maps are off. The main menu opens
    /// on boot for human play; batch test runs skip it unless a test asks (ShowOnBootOverride).
    /// </summary>
    public sealed class MenuController : MonoBehaviour
    {
        public static MenuController Instance { get; private set; }
        /// <summary>Tests set this to true/false; null = show on boot unless running in batch mode.</summary>
        public static bool? ShowOnBootOverride;

        public InputActionAsset actions;
        public SaveSystem save;

        public bool MainMenuOpen => mainPanel != null && mainPanel.activeSelf;
        public bool PauseOpen => pausePanel != null && pausePanel.activeSelf;
        /// <summary>U-102: the settings panel, opened from the title screen or the pause menu (BACK or Esc returns there).</summary>
        public bool SettingsOpen => Settings != null && Settings.IsOpen;
        public bool Blocking => MainMenuOpen || PauseOpen || SettingsOpen;
        public SettingsPanel Settings { get; private set; }
        /// <summary>SETTINGS on the title screen and on the pause menu.</summary>
        public Button SettingsButton { get; private set; }
        public Button PauseSettingsButton { get; private set; }
        /// <summary>HUDs hide while the main menu or pause menu is open (U-031: nothing draws through the menu).</summary>
        public static bool HudHidden => Instance != null && Instance.Blocking;
        public Button NewButton { get; private set; }
        public Button ContinueButton { get; private set; }
        public Button QuitButton { get; private set; }
        public Button ResumeButton { get; private set; }
        public Button SaveButton { get; private set; }
        public Button MainMenuButton { get; private set; }
        /// <summary>U-124: the paper card behind the pause menu's title and buttons (clear until B-151's ui/panels/pause is on disk).</summary>
        public Image PauseCard { get; private set; }
        public static readonly Vector2 PauseCardSize = new Vector2(640f, 520f);
        /// <summary>U-124: true once the pause paper drew, false when its key is absent (null while the probe runs).</summary>
        public bool? PausePaper { get; private set; }
        /// <summary>U-124: the planet title cards (the intertitle slide-in after each entry).</summary>
        public TitleCard TitleCards { get; private set; }

        GameObject mainPanel, pausePanel;
        InputAction pause;
        readonly List<InputActionMap> pausedMaps = new List<InputActionMap>();

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            if (actions == null) actions = MeridianInput.Build();
            EnsureEventSystem();
            Build();
            TitleCards = GetComponent<TitleCard>();
            if (TitleCards == null) TitleCards = gameObject.AddComponent<TitleCard>(); // U-124: it finds the TransitionDirector in Start
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
            if (Blocking) Time.timeScale = 1f;
        }

        void Start()
        {
            if (save == null) save = SaveSystem.Instance;
            var always = actions.FindActionMap(MeridianInput.Always, true);
            pause = always.FindAction("Pause");
            always.Enable();
            bool show = ShowOnBootOverride ?? !Application.isBatchMode;
            if (show) OpenMain();
        }

        void Update()
        {
            // Scenes that load behind an open menu (PlanetSide at boot) enable their maps late: keep them off.
            if (Blocking)
                foreach (var map in actions.actionMaps)
                    if (map.enabled && map.name != MeridianInput.Always) { map.Disable(); if (!pausedMaps.Contains(map)) pausedMaps.Add(map); }

            if (pause != null && pause.WasPressedThisFrame())
            {
                if (SettingsOpen) CloseSettings(); // Esc backs out of the settings to the menu that opened them
                else if (!MainMenuOpen) { if (PauseOpen) Resume(); else if (!Meridian.Space.SpaceMap.CloseOnEscape()) OpenPause(); } // U-184: Esc closes the system map first
            }
        }

        // ---------- actions ----------

        public void OpenMain()
        {
            Block();
            pausePanel.SetActive(false);
            Settings.Close();
            mainPanel.SetActive(true);
            ContinueButton.interactable = save != null && save.HasSave;
            Select(NewButton);
        }

        public void NewGame()
        {
            // A fresh boot is already a new game; after play has started, restart Core from scratch.
            if (freshBoot) { Close(); freshBoot = false; return; }
            Restart();
        }

        public void Continue()
        {
            if (save == null || !save.HasSave) return;
            Close();
            freshBoot = false;
            StartCoroutine(save.Load());
        }

        public void Quit()
        {
#if UNITY_EDITOR
            if (!Application.isBatchMode) UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        public void OpenPause()
        {
            Block();
            mainPanel.SetActive(false);
            Settings.Close();
            pausePanel.SetActive(true);
            freshBoot = false;
            Select(ResumeButton);
        }

        public void Resume() => Close();

        GameObject settingsOpener;

        /// <summary>U-102: the settings over the menu that opened them; that menu hides until BACK.</summary>
        public void OpenSettings()
        {
            Block();
            settingsOpener = MainMenuOpen ? mainPanel : PauseOpen ? pausePanel : null;
            mainPanel.SetActive(false);
            pausePanel.SetActive(false);
            Settings.Open();
        }

        public void CloseSettings()
        {
            var opener = settingsOpener;
            settingsOpener = null;
            // The opener comes back before the panel goes, so Blocking never drops in between: Block() would otherwise run
            // again and forget the gameplay maps it paused (Resume would leave the controls off).
            if (opener != null) opener.SetActive(true);
            if (opener == mainPanel) OpenMain();
            else if (opener == pausePanel) OpenPause();
            else Close();
        }

        /// <summary>The keyboard starts on a menu's first button (arrows walk the rest, Enter presses).</summary>
        static void Select(Selectable s)
        {
            if (s != null && EventSystem.current != null) EventSystem.current.SetSelectedGameObject(s.gameObject);
        }

        public void SaveNow()
        {
            if (save != null) save.Save();
        }

        public void ToMainMenu()
        {
            Close();
            Restart();
        }

        bool freshBoot = true;

        void Restart()
        {
            Time.timeScale = 1f;
            ShowOnBootOverride = true;
            SceneManager.LoadScene(SceneManager.GetSceneByBuildIndex(0).name, LoadSceneMode.Single);
        }

        void Block()
        {
            if (Blocking) return;
            Time.timeScale = 0f;
            pausedMaps.Clear();
            foreach (var map in actions.actionMaps)
                if (map.enabled && map.name != MeridianInput.Always) { pausedMaps.Add(map); map.Disable(); }
        }

        void Close()
        {
            mainPanel.SetActive(false);
            pausePanel.SetActive(false);
            Settings.Close();
            Time.timeScale = 1f;
            foreach (var map in pausedMaps) map.Enable();
            pausedMaps.Clear();
        }

        // ---------- building ----------

        static void EnsureEventSystem()
        {
            if (EventSystem.current != null || FindAnyObjectByType<EventSystem>() != null) return;
            var go = new GameObject("EventSystem");
            go.AddComponent<EventSystem>();
            go.AddComponent<InputSystemUIInputModule>();
        }

        /// <summary>U-047: the title art keeps its left third clear for the menu (the Pilgrim sits right of it).</summary>
        public const float MenuX = -640f;

        void Build()
        {
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "MenuCanvas", 500);

            mainPanel = UiKit.Panel(canvas.transform, "MainMenu", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(4000f, 4000f), theme.panel).gameObject;
            // U-044 title art (BLENDER ui/title/*): full-screen background and the logo; the text title stays until the logo arrives.
            var background = UiKit.Panel(mainPanel.transform, "TitleBackground", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1920f, 1080f), Color.white);
            background.enabled = false;
            var title = UiKit.Text(mainPanel.transform, "Title", new Vector2(0.5f, 0.5f), new Vector2(MenuX, 220f), new Vector2(900f, 120f), 96, true, TextAnchor.MiddleCenter);
            title.text = "MERIDIAN";
            title.font = UiTheme.Active.TitleFace; title.fontStyle = FontStyle.Normal; // U-104 (D-090): titles in Limelight
            var logo = UiKit.Panel(mainPanel.transform, "TitleLogo", new Vector2(0.5f, 0.5f), new Vector2(MenuX, 230f), new Vector2(560f, 140f), Color.white);
            logo.preserveAspect = true;
            logo.enabled = false;
            LoadTitleArt("ui/title/background", background, null);
            LoadTitleArt("ui/title/logo", logo, title);
            var sub = UiKit.Text(mainPanel.transform, "Subtitle", new Vector2(0.5f, 0.5f), new Vector2(MenuX, 140f), new Vector2(560f, 40f), 20, false, TextAnchor.MiddleCenter, theme.label);
            sub.text = "a survey of the real solar system";
            NewButton = UiKit.Button(mainPanel.transform, "NEW", new Vector2(MenuX, 20f), NewGame);
            ContinueButton = UiKit.Button(mainPanel.transform, "CONTINUE", new Vector2(MenuX, -60f), Continue);
            SettingsButton = UiKit.Button(mainPanel.transform, "SETTINGS", new Vector2(MenuX, -140f), OpenSettings); // U-102
            QuitButton = UiKit.Button(mainPanel.transform, "QUIT", new Vector2(MenuX, -220f), Quit);
            mainPanel.SetActive(false);

            pausePanel = UiKit.Panel(canvas.transform, "Pause", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(4000f, 4000f), theme.panel).gameObject;
            // U-124: the pause menu sits on a paper card (B-151's ui/panels/pause, 9-slice) once the art is on disk; clear until then.
            PauseCard = UiKit.Panel(pausePanel.transform, "PauseCard", new Vector2(0.5f, 0.5f), new Vector2(0f, -20f), PauseCardSize, Color.clear);
            var card = PauseCard.transform;
            var paused = UiKit.Text(card, "Title", new Vector2(0.5f, 0.5f), new Vector2(0f, 180f), new Vector2(560f, 90f), 56, true, TextAnchor.MiddleCenter);
            paused.text = "PAUSED";
            paused.font = theme.TitleFace; paused.fontStyle = FontStyle.Normal; // U-124: titles in Limelight (D-090)
            ResumeButton = UiKit.Button(card, "RESUME", new Vector2(0f, 60f), Resume);
            SaveButton = UiKit.Button(card, "SAVE", new Vector2(0f, -20f), SaveNow);
            PauseSettingsButton = UiKit.Button(card, "SETTINGS", new Vector2(0f, -100f), OpenSettings); // U-102: the Film effects toggle moved in there
            MainMenuButton = UiKit.Button(card, "MAIN MENU", new Vector2(0f, -180f), ToMainMenu);
            pausePanel.SetActive(false);
            UiPaper.Apply(PauseCard, Meridian.Art.ArtKeys.Ui.PanelPause, ok => PausePaper = ok);

            Settings = SettingsPanel.Build(canvas.transform, actions, CloseSettings);
        }

        /// <summary>U-095's Film effects toggle, now on the settings panel (U-102).</summary>
        public Button FilmButton => Settings != null ? Settings.FilmButton : null;

        /// <summary>Title art is optional: if the key isn't there, the themed text title stays.</summary>
        void LoadTitleArt(string key, Image target, Text replaces)
        {
            var loc = UnityEngine.AddressableAssets.Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(l);
                if (!exists || target == null) return;
                var h = Meridian.Art.ArtLoad.Asset<System.Collections.Generic.IList<Sprite>>(key);
                h.Completed += op =>
                {
                    if (target == null || op.Status != UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    target.sprite = op.Result[0];
                    target.enabled = true;
                    if (replaces != null) replaces.enabled = false;
                };
            };
        }
    }
}
