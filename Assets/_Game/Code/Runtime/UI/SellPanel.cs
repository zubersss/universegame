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

        void Build()
        {
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "SellCanvas", 114);
            var back = UiKit.ModalPanel(canvas.transform, "Sell", new Vector2(720f, 640f), out root);
            UiPaper.ApplyModal(back, Meridian.Art.ArtKeys.Ui.PanelScroll, _ => { });
            var tl = new Vector2(0f, 1f);
            UiKit.Text(back.transform, "Header", tl, new Vector2(28f, -32f), new Vector2(660f, 30f), 22, true, TextAnchor.MiddleLeft, theme.text).text = "SELL THE PACK";
            for (int i = 0; i < MaxLines; i++)
                Lines.Add(UiKit.Text(back.transform, "Line" + i, tl, new Vector2(28f, -86f - i * 38f), new Vector2(660f, 30f), 17, false, TextAnchor.MiddleLeft, theme.text));
            Total = UiKit.Text(back.transform, "Total", tl, new Vector2(28f, -480f), new Vector2(660f, 30f), 19, true, TextAnchor.MiddleLeft, theme.text);
            Note = UiKit.Text(back.transform, "Note", tl, new Vector2(28f, -516f), new Vector2(660f, 30f), 15, false, TextAnchor.MiddleLeft, theme.label);
            sell = UiKit.ActionButton(back.transform, "SELL ALL", tl, new Vector2(28f, -570f), new Vector2(260f, 48f), () => SellAll());
            root.SetActive(false);
            enabled = false;
        }

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
                    Lines[line++].text = $"{(def != null ? def.name : "?")} × {st.count}   {Mathf.RoundToInt(st.count * tables.Scrip(st.itemId))} Scrip   {st.count * tables.Kg(st.itemId):0.#} kg";
                }
            }
            for (int i = line; i < MaxLines; i++) Lines[i].text = "";
            bool topside = Topside;
            int value = state != null ? DigRun.PackValue(state.inventory, false) : 0;
            Total.text = state != null ? $"TOTAL {value} Scrip    pack {state.inventory.Weight:0.#} / {state.inventory.LimitKg:0.#} kg    purse {state.scrip} Scrip" : "";
            Note.text = !topside ? "Topside only: climb above the Surface Line to sell." : line == 0 ? "Nothing to sell: dig deeper for materials." : LastPaid > 0 ? $"Sold for {LastPaid} Scrip." : "";
            if (sell != null) sell.interactable = topside && line > 0;
        }
    }
}
