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
            if (theme.hudTtf != null)
            {
                fontSize = Mathf.RoundToInt(fontSize * HudFaceScale); // the handwritten face sits a third smaller than the monospace at the same size
                var ink = t.gameObject.AddComponent<Outline>();     // an ink rim: the light strings read over Earth's bright sky too (the 1080p capture)
                ink.effectColor = new Color(0.03f, 0.04f, 0.07f, 1f);   // full-strength: a 0.7 rim at 1 px still washed out on Earth's sky (05:02 frame)
                ink.effectDistance = new Vector2(1.5f, -1.5f);
                ink.useGraphicAlpha = false;                         // the rim keeps its own alpha: the theme's 0.6-alpha labels still read on a light sky
            }
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
            var b = rt.gameObject.AddComponent<Button>();
            b.colors = CardColors();
            b.onClick.AddListener(onClick);
            var t = Text(rt, "Label", new Vector2(0.5f, 0.5f), Vector2.zero, rt.sizeDelta, 26, true, TextAnchor.MiddleCenter, theme.text);
            t.text = label;
            PaperCard(img); // D-149 (U-136): a cream paper card, ink lettering, a 1 px ink edge
            return b;
        }

        // ---------- D-149 (U-135 / U-136): paper cards and ink boxes ----------

        /// <summary>The ink of the drawn UI (UiPaper's), its faded form on a locked card, the card cream, the locked grey, the gold band.</summary>
        public static readonly Color Ink = new Color(0.13f, 0.09f, 0.06f, 1f), InkFaded = new Color(0.13f, 0.09f, 0.06f, 0.45f);
        public static readonly Color Cream = new Color(0.95f, 0.91f, 0.80f, 1f), Greyed = new Color(0.70f, 0.68f, 0.64f, 1f), Gold = new Color(0.86f, 0.64f, 0.18f, 1f);
        /// <summary>U-135: an inventory slot's fill, a faint darkening of the paper.</summary>
        public static readonly Color SlotFill = new Color(0.30f, 0.20f, 0.08f, 0.10f);
        public const float CardEdge = 1f, SlotEdge = 2f, BandHeight = 5f;
        public const string BandName = "GoldBand", EdgeName = "InkEdge";
        /// <summary>A card's state: plain cream; cream with the gold band (selected, known); greyed with faded ink (locked, can't act).</summary>
        public enum Card { Plain, Gold, Locked }

        /// <summary>The tint a card button takes per state: a warm darkening on hover / keyboard focus, a deeper one pressed (an opaque cream fill
        /// shows no alpha boost, the old menu buttons' highlight).</summary>
        public static ColorBlock CardColors()
        {
            var c = ColorBlock.defaultColorBlock;
            c.normalColor = Color.white;
            c.highlightedColor = new Color(1f, 0.9f, 0.68f, 1f);
            c.selectedColor = new Color(1f, 0.86f, 0.55f, 1f);
            c.pressedColor = new Color(0.84f, 0.76f, 0.6f, 1f);
            c.disabledColor = Color.white; // the state shows through SetCard (the greyed card), not a tint
            return c;
        }

        /// <summary>Four ink edges `width` px wide just inside `box` (stretch-anchored children, no raycasts).</summary>
        public static void InkEdges(RectTransform box, float width, Color ink)
        {
            for (int side = 0; side < 4; side++)
            {
                var e = new GameObject(EdgeName, typeof(RectTransform), typeof(Image)).GetComponent<RectTransform>();
                e.SetParent(box, false);
                bool horizontal = side < 2;
                float a = side == 0 || side == 3 ? 1f : 0f; // top, bottom, left, right
                e.anchorMin = horizontal ? new Vector2(0f, a) : new Vector2(a, 0f);
                e.anchorMax = horizontal ? new Vector2(1f, a) : new Vector2(a, 1f);
                e.pivot = horizontal ? new Vector2(0.5f, a) : new Vector2(a, 0.5f);
                e.anchoredPosition = Vector2.zero;
                e.sizeDelta = horizontal ? new Vector2(0f, width) : new Vector2(width, 0f);
                var img = e.GetComponent<Image>();
                img.color = ink;
                img.raycastTarget = false;
            }
        }

        /// <summary>The gold band along a card's or slot's bottom edge, hidden until the state asks for it.</summary>
        public static Image GoldBand(RectTransform box)
        {
            var band = new GameObject(BandName, typeof(RectTransform), typeof(Image)).GetComponent<RectTransform>();
            band.SetParent(box, false);
            band.anchorMin = new Vector2(0f, 0f); band.anchorMax = new Vector2(1f, 0f); band.pivot = new Vector2(0.5f, 0f);
            band.anchoredPosition = new Vector2(0f, CardEdge); band.sizeDelta = new Vector2(-2f * CardEdge, BandHeight);
            var img = band.GetComponent<Image>();
            img.color = Gold;
            img.raycastTarget = false;
            img.enabled = false;
            return img;
        }

        /// <summary>D-149: a panel text a refresh recolours — on the paper ink (faded when locked / unknown), on the flat fallback panel the theme's light text. Pure.</summary>
        public static Color Letter(bool? paper, bool on) => paper == true ? (on ? Ink : InkFaded) : on ? UiTheme.Active.text : new Color(1f, 1f, 1f, 0.3f);

        /// <summary>D-149: dresses a control's fill as a paper card: cream, a 1 px ink edge, its own lettering in ink (the light rim off), the gold band
        /// ready. Built once per control.</summary>
        public static void PaperCard(Image fill)
        {
            fill.color = Cream;
            InkEdges(fill.rectTransform, CardEdge, Ink);
            GoldBand(fill.rectTransform);
            foreach (var t in fill.GetComponentsInChildren<Text>(true))
            {
                t.color = Ink;
                var rim = t.GetComponent<Outline>();
                if (rim != null) rim.enabled = false;
            }
        }

        /// <summary>D-149: a card's state — Plain cream, Gold (the band: selected / known), Locked (greyed, faded ink). No allocation (the band by name, the
        /// first label only), so panels may call it on every refresh.</summary>
        public static void SetCard(Image fill, Card state)
        {
            if (fill == null) return;
            var want = state == Card.Locked ? Greyed : Cream;
            if (fill.color != want) fill.color = want;
            var band = fill.transform.Find(BandName);
            if (band != null) { var bi = band.GetComponent<Image>(); bool on = state == Card.Gold; if (bi.enabled != on) bi.enabled = on; }
            var label = fill.GetComponentInChildren<Text>(true);
            if (label != null) { var ink = state == Card.Locked ? InkFaded : Ink; if (label.color != ink) label.color = ink; }
        }

        // ---------- U-058 shared panel style ----------

        /// <summary>Opaque panel fill (no world bleeding through).</summary>
        public static readonly Color PanelFill = new Color(0.035f, 0.045f, 0.065f, 1f);
        /// <summary>The full-screen dim behind a panel.</summary>
        public static readonly Color ScrimColor = new Color(0f, 0f, 0f, 0.78f); // LEAD, U-059 review: deeper, the world recedes behind every panel

        /// <summary>U-124 (keyboard reach): selects `preferred` when it can act, else the first interactable control under `root`, so
        /// the arrows walk a panel the moment it opens and Enter presses. Runs on open only (the search allocates).</summary>
        public static Selectable SelectFirst(Transform root, Selectable preferred = null)
        {
            var es = UnityEngine.EventSystems.EventSystem.current;
            if (es == null || root == null) return null;
            if (preferred != null && preferred.isActiveAndEnabled && preferred.IsInteractable()) { es.SetSelectedGameObject(preferred.gameObject); return preferred; }
            foreach (var s in root.GetComponentsInChildren<Selectable>(false))
                if (s.IsInteractable()) { es.SetSelectedGameObject(s.gameObject); return s; }
            return null;
        }

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
            var b = rt.gameObject.AddComponent<Button>();
            b.colors = CardColors(); // the state shows through SetAction's card, not a tint
            b.onClick.AddListener(onClick);
            var t = Text(rt, "Label", new Vector2(0.5f, 0.5f), Vector2.zero, size, 18, true, TextAnchor.MiddleCenter, Ink);
            t.text = label;
            PaperCard(img); // D-149 (U-136): CRAFT, BUY, SELL and the tabs are paper cards; the navy and blue fills are gone
            return b;
        }

        /// <summary>Shows an action button as available (a plain cream card) or not (greyed, faded ink), with interactable to match.</summary>
        public static void SetAction(Button b, bool on)
        {
            if (b.interactable != on) b.interactable = on;
            SetCard(b.targetGraphic as Image, on ? Card.Plain : Card.Locked);
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
