using System.Text;
using Meridian.Core;
using Meridian.Player;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Events;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-102 (P-39): the settings panel, one panel opened from the title screen and the pause menu. Film effects (moved
    /// here from the pause menu), master / music / SFX volume in tenths, the keys as a read-only list, the language as a
    /// placeholder row; everything saves through GameSettings the moment it changes. The placeholder frame (the theme's
    /// panel fill) stands until B-151's `ui/panels/settings` 9-slice lands (U-124). Built once by MenuController on its canvas.
    /// </summary>
    public sealed class SettingsPanel
    {
        public GameObject Root { get; private set; }
        public bool IsOpen => Root != null && Root.activeSelf;
        public Button FilmButton { get; private set; }
        public Button MasterDown { get; private set; }
        public Button MasterUp { get; private set; }
        public Button MusicDown { get; private set; }
        public Button MusicUp { get; private set; }
        public Button SfxDown { get; private set; }
        public Button SfxUp { get; private set; }
        public Button LanguageButton { get; private set; }
        public Button BackButton { get; private set; }
        public Text KeysText { get; private set; }
        public Text MasterLabel { get; private set; }
        public Text MusicLabel { get; private set; }
        public Text SfxLabel { get; private set; }
        /// <summary>U-124: true once the settings paper drew, false when its key is absent (null while the probe runs).</summary>
        public bool? Paper { get; private set; }
        /// <summary>U-124: B-151's Film switch left of the FILM EFFECTS row (hidden until `ui/hud/film_switch` loads).</summary>
        public Image FilmSwitch { get; private set; }
        Sprite switchOff, switchOn;

        /// <summary>The panel's size at 1080p (the 9-slice frame stretches to it when it arrives).</summary>
        public static readonly Vector2 Size = new Vector2(1180f, 860f);

        public static string FilmLabel() => GameSettings.FilmEffects ? "FILM EFFECTS: ON" : "FILM EFFECTS: OFF";

        public static SettingsPanel Build(Transform canvas, InputActionAsset actions, UnityAction back)
        {
            var p = new SettingsPanel();
            var theme = UiTheme.Active;
            var panel = UiKit.ModalPanel(canvas, "Settings", Size, out var root);
            p.Root = root;
            var t = panel.transform;
            var title = UiKit.Text(t, "Title", new Vector2(0.5f, 0.5f), new Vector2(0f, 360f), new Vector2(900f, 80f), 48, true, TextAnchor.MiddleCenter);
            title.text = "SETTINGS";
            title.font = theme.TitleFace; title.fontStyle = FontStyle.Normal; // U-104 (D-090): titles in Limelight

            p.FilmButton = UiKit.Button(t, FilmLabel(), new Vector2(0f, 270f), () => { GameSettings.FilmEffects = !GameSettings.FilmEffects; p.Refresh(); });
            p.MasterLabel = VolumeRow(t, "Master", 190f, out var md, out var mu, () => GameSettings.MasterVolume = GameSettings.Stepped(GameSettings.MasterVolume, -1), () => GameSettings.MasterVolume = GameSettings.Stepped(GameSettings.MasterVolume, 1), p);
            p.MasterDown = md; p.MasterUp = mu;
            p.MusicLabel = VolumeRow(t, "Music", 120f, out var nd, out var nu, () => GameSettings.MusicVolume = GameSettings.Stepped(GameSettings.MusicVolume, -1), () => GameSettings.MusicVolume = GameSettings.Stepped(GameSettings.MusicVolume, 1), p);
            p.MusicDown = nd; p.MusicUp = nu;
            p.SfxLabel = VolumeRow(t, "Sfx", 50f, out var sd, out var su, () => GameSettings.SfxVolume = GameSettings.Stepped(GameSettings.SfxVolume, -1), () => GameSettings.SfxVolume = GameSettings.Stepped(GameSettings.SfxVolume, 1), p);
            p.SfxDown = sd; p.SfxUp = su;
            p.LanguageButton = UiKit.Button(t, "LANGUAGE: " + GameSettings.Language.ToUpperInvariant(), new Vector2(0f, -25f), () => { });
            p.LanguageButton.interactable = false; // one language until localisation exists (P-39's placeholder)

            var head = UiKit.Text(t, "KeysHeader", new Vector2(0.5f, 0.5f), new Vector2(0f, -95f), new Vector2(1000f, 36f), 20, true, TextAnchor.MiddleCenter, theme.label);
            head.text = "KEYS (rebinding comes later)";
            p.KeysText = UiKit.Text(t, "Keys", new Vector2(0.5f, 0.5f), new Vector2(0f, -205f), new Vector2(1080f, 170f), 15, false, TextAnchor.UpperCenter, theme.text);
            p.KeysText.horizontalOverflow = HorizontalWrapMode.Wrap; // OnFoot alone is a long line
            p.KeysText.text = KeyList(actions);

            // U-124 (B-151): the settings paper (its teal header band in the top slice: the title moves into it) and the Film switch's
            // brass lever left of its row, `off` / `on` with the setting. Both probe their keys: absent, the flat panel stays.
            UiPaper.ApplyModal(panel, Meridian.Art.ArtKeys.Ui.PanelSettings, ok =>
            {
                p.Paper = ok;
                var frame = panel.transform.parent != null ? panel.transform.parent.GetComponent<Image>() : null;
                if (!ok || frame == null || frame.sprite == null) return;
                float top = frame.sprite.border.w;
                title.rectTransform.anchoredPosition = new Vector2(0f, Size.y * 0.5f + top * UiPaper.BorderReach - top * 0.5f);
            });
            p.FilmSwitch = UiKit.Panel(p.FilmButton.transform, "FilmSwitch", new Vector2(0f, 0.5f), new Vector2(-48f, 0f), new Vector2(48f, 72f), Color.white);
            p.FilmSwitch.preserveAspect = true;
            p.FilmSwitch.enabled = false;
            UiPaper.LoadParts(p.FilmSwitch, Meridian.Art.ArtKeys.Ui.FilmSwitch, parts =>
            {
                parts.TryGetValue("off", out p.switchOff);
                parts.TryGetValue("on", out p.switchOn);
                p.Refresh();
            });

            p.BackButton = UiKit.Button(t, "BACK", new Vector2(0f, -360f), back);
            Chain(p.FilmButton, p.MasterDown, p.MasterUp, p.MusicDown, p.MusicUp, p.SfxDown, p.SfxUp, p.BackButton);
            root.SetActive(false);
            return p;
        }

        static Text VolumeRow(Transform t, string name, float y, out Button down, out Button up, UnityAction lower, UnityAction raise, SettingsPanel p)
        {
            var label = UiKit.Text(t, name + "Label", new Vector2(0.5f, 0.5f), new Vector2(-110f, y), new Vector2(520f, 56f), 26, true, TextAnchor.MiddleLeft);
            down = UiKit.Button(t, name + " -", new Vector2(250f, y), () => { lower(); p.Refresh(); });
            up = UiKit.Button(t, name + " +", new Vector2(340f, y), () => { raise(); p.Refresh(); });
            foreach (var b in new[] { down, up })
            {
                ((RectTransform)b.transform).sizeDelta = new Vector2(72f, 56f);
                var bt = b.GetComponentInChildren<Text>();
                ((RectTransform)bt.transform).sizeDelta = new Vector2(72f, 56f);
                bt.text = b == down ? "-" : "+";
            }
            return label;
        }

        /// <summary>Keyboard order: up / down walks the rows, left / right moves between a row's − and +.</summary>
        static void Chain(Button film, Button md, Button mu, Button nd, Button nu, Button sd, Button su, Button back)
        {
            void Set(Selectable s, Selectable upTo, Selectable downTo, Selectable left, Selectable right)
            {
                var n = new Navigation { mode = Navigation.Mode.Explicit, selectOnUp = upTo, selectOnDown = downTo, selectOnLeft = left, selectOnRight = right };
                s.navigation = n;
            }
            Set(film, back, md, null, null);
            Set(md, film, nd, null, mu); Set(mu, film, nu, md, null);
            Set(nd, md, sd, null, nu); Set(nu, mu, su, nd, null);
            Set(sd, nd, back, null, su); Set(su, nu, back, sd, null);
            Set(back, sd, film, null, null);
        }

        /// <summary>Opens the panel with the film row selected (the keyboard starts there).</summary>
        public void Open()
        {
            Refresh();
            Root.SetActive(true);
            Root.transform.SetAsLastSibling();
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(FilmButton.gameObject);
        }

        public void Close() { if (Root != null) Root.SetActive(false); }

        public void Refresh()
        {
            var ft = FilmButton.GetComponentInChildren<Text>();
            if (ft != null) ft.text = FilmLabel();
            var lever = GameSettings.FilmEffects ? switchOn : switchOff; // U-124: the lever follows the setting
            if (FilmSwitch != null) { FilmSwitch.sprite = lever; FilmSwitch.enabled = lever != null; }
            MasterLabel.text = "MASTER VOLUME   " + GameSettings.Percent(GameSettings.MasterVolume);
            MusicLabel.text = "MUSIC VOLUME   " + GameSettings.Percent(GameSettings.MusicVolume);
            SfxLabel.text = "SFX VOLUME   " + GameSettings.Percent(GameSettings.SfxVolume);
            MasterDown.interactable = GameSettings.MasterVolume > 0f; MasterUp.interactable = GameSettings.MasterVolume < 1f;
            MusicDown.interactable = GameSettings.MusicVolume > 0f; MusicUp.interactable = GameSettings.MusicVolume < 1f;
            SfxDown.interactable = GameSettings.SfxVolume > 0f; SfxUp.interactable = GameSettings.SfxVolume < 1f;
        }

        /// <summary>The keyboard and mouse bindings of every map, one line per map (the pointer's position is not a key).</summary>
        public static string KeyList(InputActionAsset actions)
        {
            if (actions == null) return "";
            var sb = new StringBuilder();
            foreach (var map in actions.actionMaps)
            {
                var line = new StringBuilder();
                foreach (var a in map.actions)
                {
                    var keys = new StringBuilder();
                    for (int i = 0; i < a.bindings.Count; i++)
                    {
                        var b = a.bindings[i];
                        if (b.isPartOfComposite) continue;
                        bool desk = b.isComposite ? CompositeIsDesk(a, i) : IsDesk(b.effectivePath);
                        if (!desk) continue;
                        if (keys.Length > 0) keys.Append(" / ");
                        keys.Append(a.GetBindingDisplayString(i));
                    }
                    if (keys.Length == 0) continue;
                    if (line.Length > 0) line.Append("    ");
                    line.Append(a.name).Append(": ").Append(keys);
                }
                if (line.Length == 0) continue;
                if (sb.Length > 0) sb.Append('\n');
                sb.Append(MapTitle(map.name)).Append("   ").Append(line);
            }
            return sb.ToString();
        }

        static bool IsDesk(string path) => !string.IsNullOrEmpty(path) && (path.StartsWith("<Keyboard>") || (path.StartsWith("<Mouse>") && !path.EndsWith("/position") && !path.EndsWith("/delta")));

        static bool CompositeIsDesk(InputAction a, int composite)
        {
            for (int i = composite + 1; i < a.bindings.Count && a.bindings[i].isPartOfComposite; i++)
                if (IsDesk(a.bindings[i].effectivePath)) return true;
            return false;
        }

        static string MapTitle(string map) => map switch
        {
            MeridianInput.OnFoot => "ON FOOT",
            MeridianInput.ShipSide => "SHIP (SIDE)",
            MeridianInput.ShipTop => "SHIP (SPACE)",
            MeridianInput.Always => "ANY TIME",
            _ => map.ToUpperInvariant(),
        };
    }
}
