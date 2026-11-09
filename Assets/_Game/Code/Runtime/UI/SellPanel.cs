using System.Collections.Generic;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Player;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-174 (D-174, Bible 5.2 §8.1): the Sell panel (G), topside only: the pack's sellable materials, each line its count and Scrip at the
    /// D1 tables' prices, the total, and SELL ALL. Below the Surface Line it opens to say so and sells nothing (DigRun.SellPack refuses).
    /// On the U-058 panel style (UiKit, the paper modal). No per-frame work while closed.
    /// </summary>
    public sealed class SellPanel : MonoBehaviour
    {
        public PlayerController player;
        public static bool AnyOpen { get; private set; }
        public bool IsOpen => root != null && root.activeSelf;
        /// <summary>The last SELL ALL's Scrip (-1 refused below the line; tests and captures read it).</summary>
        public int LastPaid { get; private set; }
        /// <summary>The line labels and the total (tests and captures read them).</summary>
        public readonly List<Text> Lines = new List<Text>();
        public Text Total { get; private set; }
        public Text Note { get; private set; }

        const int MaxLines = 10;
        GameObject root;
        InputAction toggle;
        Button sell;

        void Start()
        {
            Build();
            if (player != null && player.actions != null)
            {
                toggle = player.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("Sell");
                if (toggle != null) toggle.performed += OnToggle;
            }
        }

        void OnDestroy()
        {
            PanelInput.Close(this);
            ItemIcons.Loaded -= OnIcons;
            if (toggle != null) toggle.performed -= OnToggle;
            if (IsOpen) AnyOpen = false;
        }

        void OnToggle(InputAction.CallbackContext _) => SetOpen(!IsOpen);

        public void SetOpen(bool open)
        {
            if (root == null || root.activeSelf == open) return;
            root.SetActive(open);
            if (open) PanelInput.Open(this, toggle != null ? toggle.actionMap : null); else PanelInput.Close(this);
            AnyOpen = open;
            enabled = open;
            if (open) { Redraw(); UiKit.SelectFirst(root.transform, sell); }
        }

        void Update() { if (toggle != null) PanelInput.Hold(toggle.actionMap); }

        /// <summary>The surveyor's feet are at or above the Surface Line.</summary>
        public bool Topside
        {
            get
            {
                var side = FindAnyObjectByType<PlanetSideRoot>();
                if (side == null || side.terrain == null || player == null || !side.terrain.SmoothGround) return true;
                return DigRun.Topside(side.terrain, player.Body.position);
            }
        }

        /// <summary>SELL ALL: the pack's sellable materials for Scrip, topside only.</summary>
        public int SellAll()
        {
            LastPaid = DigRun.SellPack(GameState.Instance, Topside, false);
            Redraw();
            return LastPaid;
        }

        // U-174 (LEAD 18:5x): ink at the HUD's size in aligned columns (icon, name, count, Scrip, kg), the total on its own rule.
        const float ColIcon = 34f, ColName = 74f, ColCount = 330f, ColScrip = 420f, ColKg = 540f, RowH = 34f, Top = -96f;
        readonly List<Image> icons = new List<Image>();
        readonly List<Text> names = new List<Text>(), counts = new List<Text>(), scrips = new List<Text>(), kgs = new List<Text>();

        void Build()
        {
            var canvas = UiKit.Canvas(transform, "SellCanvas", 114);
            var back = UiKit.ModalPanel(canvas.transform, "Sell", new Vector2(720f, 640f), out root);
            UiPaper.ApplyModal(back, Meridian.Art.ArtKeys.Ui.PanelScroll, _ => { });
            var tl = new Vector2(0f, 1f);
            var ink = UiKit.Ink;
            UiKit.Text(back.transform, "Header", tl, new Vector2(34f, -30f), new Vector2(640f, 30f), 22, true, TextAnchor.MiddleLeft, ink).text = "SELL THE PACK";
            Text Head(string n, float x, float w, TextAnchor a, string t) { var h = UiKit.Text(back.transform, n, tl, new Vector2(x, -62f), new Vector2(w, 22f), 14, true, a, UiKit.InkFaded); h.text = t; return h; }
            Head("HName", ColName, 240f, TextAnchor.MiddleLeft, "MATERIAL");
            Head("HCount", ColCount - 60f, 80f, TextAnchor.MiddleRight, "COUNT");
            Head("HScrip", ColScrip - 20f, 100f, TextAnchor.MiddleRight, "SCRIP");
            Head("HKg", ColKg - 20f, 100f, TextAnchor.MiddleRight, "KG");
            UiKit.Panel(back.transform, "HeadRule", tl, new Vector2(34f, -84f), new Vector2(620f, 1.5f), ink);
            for (int i = 0; i < MaxLines; i++)
            {
                float y = Top - i * RowH;
                var icon = UiKit.Panel(back.transform, "Icon" + i, tl, new Vector2(ColIcon, y + 2f), new Vector2(28f, 28f), Color.white);
                icon.preserveAspect = true;
                icons.Add(icon);
                names.Add(UiKit.Text(back.transform, "Name" + i, tl, new Vector2(ColName, y), new Vector2(240f, 28f), 17, false, TextAnchor.MiddleLeft, ink));
                counts.Add(UiKit.Text(back.transform, "Count" + i, tl, new Vector2(ColCount - 60f, y), new Vector2(80f, 28f), 17, false, TextAnchor.MiddleRight, ink));
                scrips.Add(UiKit.Text(back.transform, "Scrip" + i, tl, new Vector2(ColScrip - 20f, y), new Vector2(100f, 28f), 17, false, TextAnchor.MiddleRight, ink));
                kgs.Add(UiKit.Text(back.transform, "Kg" + i, tl, new Vector2(ColKg - 20f, y), new Vector2(100f, 28f), 17, false, TextAnchor.MiddleRight, ink));
                Lines.Add(names[i]);
            }
            UiKit.Panel(back.transform, "TotalRule", tl, new Vector2(34f, Top - MaxLines * RowH + 4f), new Vector2(620f, 2f), ink);
            Total = UiKit.Text(back.transform, "Total", tl, new Vector2(34f, Top - MaxLines * RowH - 8f), new Vector2(620f, 30f), 19, true, TextAnchor.MiddleLeft, ink);
            Note = UiKit.Text(back.transform, "Note", tl, new Vector2(34f, Top - MaxLines * RowH - 42f), new Vector2(620f, 24f), 15, false, TextAnchor.MiddleLeft, UiKit.InkFaded);
            sell = UiKit.ActionButton(back.transform, "SELL ALL", tl, new Vector2(34f, -572f), new Vector2(260f, 48f), () => SellAll());
            ItemIcons.Loaded += OnIcons;
            root.SetActive(false);
            enabled = false;
        }

        void OnIcons() { if (IsOpen) Redraw(); }

        void Redraw()
        {
            var state = GameState.Instance;
            var tables = D1Tables.Current;
            int line = 0;
            if (state != null)
            {
                var inv = state.inventory;
                for (int s = 0; s < Inventory.SlotCount && line < MaxLines; s++)
                {
                    var st = inv[s];
                    if (st.IsEmpty || !tables.Sellable(st.itemId)) continue;
                    var def = ItemRegistry.Get(st.itemId);
                    var sp = ItemIcons.Get(st.itemId);
                    icons[line].sprite = sp;
                    icons[line].enabled = sp != null;
                    names[line].text = def != null ? def.name : "?";
                    counts[line].text = st.count.ToString();
                    scrips[line].text = Mathf.RoundToInt(st.count * tables.Scrip(st.itemId)).ToString();
                    kgs[line].text = (st.count * tables.Kg(st.itemId)).ToString("0.#");
                    line++;
                }
            }
            for (int i = line; i < MaxLines; i++) { icons[i].enabled = false; names[i].text = counts[i].text = scrips[i].text = kgs[i].text = ""; }
            bool topside = Topside;
            int value = state != null ? DigRun.PackValue(state.inventory, false) : 0;
            Total.text = state != null ? $"TOTAL {value} Scrip      pack {state.inventory.Weight:0.#} / {state.inventory.LimitKg:0.#} kg      purse {state.scrip}" : "";
            Note.text = !topside ? "Topside only: climb above the Surface Line to sell." : line == 0 ? "Nothing to sell: dig deeper for materials." : LastPaid > 0 ? $"Sold for {LastPaid} Scrip." : "";
            if (sell != null) sell.interactable = topside && line > 0;
        }
    }
}
