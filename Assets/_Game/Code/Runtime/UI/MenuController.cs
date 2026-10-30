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
        public bool Blocking => MainMenuOpen || PauseOpen;
        /// <summary>HUDs hide while the main menu or pause menu is open (U-031: nothing draws through the menu).</summary>
        public static bool HudHidden => Instance != null && Instance.Blocking;
        public Button NewButton { get; private set; }
        public Button ContinueButton { get; private set; }
        public Button QuitButton { get; private set; }
        public Button ResumeButton { get; private set; }
        public Button SaveButton { get; private set; }
        public Button MainMenuButton { get; private set; }

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

            if (pause != null && pause.WasPressedThisFrame() && !MainMenuOpen)
            {
                if (PauseOpen) Resume(); else OpenPause();
            }
        }

        // ---------- actions ----------

        public void OpenMain()
        {
            Block();
            pausePanel.SetActive(false);
            mainPanel.SetActive(true);
            ContinueButton.interactable = save != null && save.HasSave;
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
            pausePanel.SetActive(true);
            freshBoot = false;
        }

        public void Resume() => Close();

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

        void Build()
        {
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "MenuCanvas", 500);

            mainPanel = UiKit.Panel(canvas.transform, "MainMenu", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(4000f, 4000f), theme.panel).gameObject;
            var title = UiKit.Text(mainPanel.transform, "Title", new Vector2(0.5f, 0.5f), new Vector2(0f, 220f), new Vector2(900f, 120f), 96, true, TextAnchor.MiddleCenter);
            title.text = "MERIDIAN";
            var sub = UiKit.Text(mainPanel.transform, "Subtitle", new Vector2(0.5f, 0.5f), new Vector2(0f, 140f), new Vector2(900f, 40f), 20, false, TextAnchor.MiddleCenter, theme.label);
            sub.text = "a survey of the real solar system";
            NewButton = UiKit.Button(mainPanel.transform, "NEW", new Vector2(0f, 20f), NewGame);
            ContinueButton = UiKit.Button(mainPanel.transform, "CONTINUE", new Vector2(0f, -60f), Continue);
            QuitButton = UiKit.Button(mainPanel.transform, "QUIT", new Vector2(0f, -140f), Quit);
            mainPanel.SetActive(false);

            pausePanel = UiKit.Panel(canvas.transform, "Pause", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(4000f, 4000f), theme.panel).gameObject;
            var paused = UiKit.Text(pausePanel.transform, "Title", new Vector2(0.5f, 0.5f), new Vector2(0f, 160f), new Vector2(900f, 90f), 56, true, TextAnchor.MiddleCenter);
            paused.text = "PAUSED";
            ResumeButton = UiKit.Button(pausePanel.transform, "RESUME", new Vector2(0f, 40f), Resume);
            SaveButton = UiKit.Button(pausePanel.transform, "SAVE", new Vector2(0f, -40f), SaveNow);
            MainMenuButton = UiKit.Button(pausePanel.transform, "MAIN MENU", new Vector2(0f, -120f), ToMainMenu);
            pausePanel.SetActive(false);
        }
    }
}
