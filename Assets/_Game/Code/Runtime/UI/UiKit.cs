using System;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>Builds the HUD/menu pieces in code with the theme (no prefabs to keep in sync).</summary>
    public static class UiKit
    {
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
            t.font = bold ? theme.Bold : theme.Regular;
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
