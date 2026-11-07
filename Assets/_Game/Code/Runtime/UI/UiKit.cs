using System;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>Builds the HUD/menu pieces in code with the theme (no prefabs to keep in sync).</summary>
    public static class UiKit
    {
        /// <summary>U-104: Patrick Hand's x-height is small; HUD and menu strings draw this much larger than their JetBrains Mono sizes (the 1080p capture).</summary>
        public const float HudFaceScale = 1.35f;
        public static Canvas Canvas(Transform parent, string name, int sortingOrder)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var c = go.AddComponent<Canvas>();
            c.renderMode = RenderMode.ScreenSpaceOverlay;
            c.sortingOrder = sortingOrder;
            var scaler = go.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.matchWidthOrHeight = 0.5f;
            go.AddComponent<GraphicRaycaster>();
            return c;
        }

        public static RectTransform Rect(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, Vector2? pivot = null)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = pivot ?? anchor;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            return rt;
        }

        public static Image Panel(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, Color color)
        {
            var img = Rect(parent, name, anchor, pos, size).gameObject.AddComponent<Image>();
            img.color = color;
            img.raycastTarget = false;
            return img;
        }

        public static Text Text(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, int fontSize,
            bool bold = false, TextAnchor align = TextAnchor.MiddleLeft, Color? color = null)
        {
            var t = Rect(parent, name, anchor, pos, size).gameObject.AddComponent<Text>();
            var theme = UiTheme.Active;
            // U-104 (D-090): Patrick Hand carries every HUD, panel and menu string (bold is synthetic on the one face); JetBrains Mono until the theme has it.
            t.font = theme.hudTtf != null ? theme.HudFace : bold ? theme.Bold : theme.Regular;
            t.fontStyle = bold && theme.hudTtf != null ? FontStyle.Bold : FontStyle.Normal;
            if (theme.hudTtf != null) fontSize = Mathf.RoundToInt(fontSize * HudFaceScale); // the handwritten face sits a third smaller than the monospace at the same size
            t.fontSize = fontSize;
            t.alignment = align;
            t.color = color ?? theme.text;
            t.raycastTarget = false;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            // JetBrains Mono's line height exceeds tight boxes; truncation silently drops the whole line.
            t.verticalOverflow = VerticalWrapMode.Overflow;
            return t;
        }

        public static Button Button(Transform parent, string label, Vector2 pos, UnityAction onClick)
        {
            var theme = UiTheme.Active;
            var rt = Rect(parent, label, new Vector2(0.5f, 0.5f), pos, new Vector2(360f, 64f));
            var img = rt.gameObject.AddComponent<Image>();
            img.color = new Color(1f, 1f, 1f, 0.08f);
            var b = rt.gameObject.AddComponent<Button>();
            var colors = b.colors;
            colors.highlightedColor = new Color(1f, 1f, 1f, 2.5f);
            colors.pressedColor = new Color(1f, 1f, 1f, 3.5f);
            colors.disabledColor = new Color(1f, 1f, 1f, 0.35f);
            b.colors = colors;
            b.onClick.AddListener(onClick);
            var t = Text(rt, "Label", new Vector2(0.5f, 0.5f), Vector2.zero, rt.sizeDelta, 26, true, TextAnchor.MiddleCenter, theme.text);
            t.text = label;
            return b;
        }

        // ---------- U-058 shared panel style ----------

        /// <summary>Opaque panel fill (no world bleeding through).</summary>
        public static readonly Color PanelFill = new Color(0.035f, 0.045f, 0.065f, 1f);
        /// <summary>The full-screen dim behind a panel.</summary>
        public static readonly Color ScrimColor = new Color(0f, 0f, 0f, 0.78f); // LEAD, U-059 review: deeper, the world recedes behind every panel
        public static readonly Color ActionOn = new Color(0.25f, 0.55f, 0.85f, 1f), ActionOff = new Color(0.14f, 0.15f, 0.17f, 1f);
        public static readonly Color ActionTextOn = Color.white, ActionTextOff = new Color(1f, 1f, 1f, 0.28f);

        /// <summary>A full-screen scrim (blocks clicks to the world) with an opaque, framed panel centred on it. Returns the panel.</summary>
        public static Image ModalPanel(Transform canvas, string name, Vector2 size, out GameObject root)
        {
            var scrim = Rect(canvas, name + "Scrim", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(4000f, 4000f)).gameObject.AddComponent<Image>();
            scrim.color = ScrimColor;
            scrim.raycastTarget = true;
            root = scrim.gameObject;
            var frame = Panel(scrim.transform, name + "Frame", new Vector2(0.5f, 0.5f), Vector2.zero, size + new Vector2(4f, 4f), UiTheme.Accent(null) * new Color(1f, 1f, 1f, 0.6f));
            var panel = Panel(frame.transform, name, new Vector2(0.5f, 0.5f), Vector2.zero, size, PanelFill);
            panel.raycastTarget = true;
            return panel;
        }

        /// <summary>An action button (CRAFT, SELL, BUY): accent fill when it can act, dark and dim when not.</summary>
        public static Button ActionButton(Transform parent, string label, Vector2 anchor, Vector2 pos, Vector2 size, UnityAction onClick)
        {
            var rt = Rect(parent, label, anchor, pos, size, anchor);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = ActionOn;
            var b = rt.gameObject.AddComponent<Button>();
            var colors = b.colors;
            colors.normalColor = Color.white; colors.highlightedColor = new Color(1.15f, 1.15f, 1.15f, 1f); colors.pressedColor = new Color(0.8f, 0.8f, 0.8f, 1f);
            colors.disabledColor = Color.white; // the state shows through SetAction, not a tint
            b.colors = colors;
            b.onClick.AddListener(onClick);
            var t = Text(rt, "Label", new Vector2(0.5f, 0.5f), Vector2.zero, size, 18, true, TextAnchor.MiddleCenter, ActionTextOn);
            t.text = label;
            return b;
        }

        /// <summary>Shows an action button as available or not (fill, label and interactable together).</summary>
        public static void SetAction(Button b, bool on)
        {
            if (b.interactable == on && b.targetGraphic != null && ((Image)b.targetGraphic).color == (on ? ActionOn : ActionOff)) return;
            b.interactable = on;
            if (b.targetGraphic is Image img) img.color = on ? ActionOn : ActionOff;
            var t = b.GetComponentInChildren<Text>();
            if (t != null) t.color = on ? ActionTextOn : ActionTextOff;
        }

        /// <summary>A thin horizontal bar: returns the fill image (set fillAmount 0..1).</summary>
        public static Image Bar(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, Color fill)
        {
            var back = Panel(parent, name, anchor, pos, size, UiTheme.Active.barBack);
            var f = Panel(back.transform, "Fill", new Vector2(0f, 0.5f), Vector2.zero, size, fill);
            f.rectTransform.pivot = new Vector2(0f, 0.5f);
            f.type = Image.Type.Filled;
            f.fillMethod = Image.FillMethod.Horizontal;
            f.sprite = WhiteSprite();
            return f;
        }

        static Sprite white;
        static Sprite WhiteSprite()
        {
            if (white != null) return white;
            white = Sprite.Create(Texture2D.whiteTexture, new Rect(0, 0, 4, 4), new Vector2(0.5f, 0.5f));
            return white;
        }

        /// <summary>"0".."max" (and negatives down to -min) built once, so HUD updates never allocate.</summary>
        public sealed class NumberStrings
        {
            readonly string[] values;
            readonly int min;
            public NumberStrings(int min, int max, string format = "0", float divisor = 1f)
            {
                this.min = min;
                values = new string[max - min + 1];
                for (int i = 0; i < values.Length; i++) values[i] = ((i + min) / divisor).ToString(format, System.Globalization.CultureInfo.InvariantCulture);
            }
            public string this[int v] => values[Math.Clamp(v, min, min + values.Length - 1) - min];
        }
    }
}
