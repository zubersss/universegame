using System.Collections.Generic;
using Meridian.Items;
using Meridian.Player;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// Tab inventory panel (U-045): the 40 slots as a 10 × 4 grid with each item's icon and count; a
    /// click selects the Builder's slot. Built in code with the theme like the rest of the HUD. Closed,
    /// it does no per-frame work (only the Tab action's callback); open, it redraws on Inventory.Changed.
    /// </summary>
    public sealed class InventoryPanel : MonoBehaviour
    {
        public const int Columns = 10;
        public const float Cell = 84f, Gap = 8f;
        /// <summary>U-181 (LEAD): the count chip (canvas px) and the count's size before UiKit's Patrick Hand scale (×1.35: 26 px, digits ~18 px).</summary>
        public const float ChipW = 46f, ChipH = 26f;
        public const int CountSize = 19;
        Image[] chips;
        /// <summary>The count chips (tests, captures).</summary>
        public Image ChipOf(int slot) => chips != null ? chips[slot] : null;

        public PlayerController player;
        public Meridian.Terrain.TerrainStreamer terrain;
        public Inventory inventory;

        public bool IsOpen => root != null && root.activeSelf;
        /// <summary>U-124: true once the panel's paper drew, false when its key is absent (null while the probe runs).</summary>
        public bool? Paper { get; private set; }

        /// <summary>True while any inventory panel is open: rig clicks pass to the panel, not the world.</summary>
        public static bool AnyOpen { get; private set; }
        public Image[] Icons { get; private set; }
        public Text[] Counts { get; private set; }
        public Text SelectedName { get; private set; }

        GameObject root;
        Image[] frames;
        /// <summary>U-135: each slot's gold band (on for the selected slot); tests read them.</summary>
        public Image[] Bands => bands;
        Image[] bands;
        InputAction toggle;
        bool dirty = true;
        static UiKit.NumberStrings numbers;

        void Start()
        {
            numbers ??= new UiKit.NumberStrings(0, Inventory.StackMax);
            if (terrain == null) terrain = FindAnyObjectByType<Meridian.Terrain.TerrainStreamer>();
            if (inventory == null && Meridian.Core.GameState.Instance != null) inventory = Meridian.Core.GameState.Instance.inventory;
            Build();
            if (inventory != null) inventory.Changed += MarkDirty;
            ItemIcons.Loaded += MarkDirty;
            if (player != null && player.actions != null)
            {
                toggle = player.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("Inventory");
                if (toggle != null) toggle.performed += OnToggle;
            }
        }

        void OnDestroy()
        {
            PanelInput.Close(this); // U-134
            if (inventory != null) inventory.Changed -= MarkDirty;
            ItemIcons.Loaded -= MarkDirty;
            if (IsOpen) AnyOpen = false;
            if (toggle != null) toggle.performed -= OnToggle;
        }

        void OnToggle(InputAction.CallbackContext _) => SetOpen(!IsOpen);

        void MarkDirty() => dirty = true;

        public void SetOpen(bool open)
        {
            if (root == null || root.activeSelf == open) return;
            root.SetActive(open);
            if (open) PanelInput.Open(this, toggle != null ? toggle.actionMap : null); else PanelInput.Close(this); // U-134: the surveyor stands still while a panel is open
            AnyOpen = open;
            enabled = open; // closed: no Update at all
            if (open) { dirty = true; Redraw(); }
        }

        void Build()
        {
            var canvas = UiKit.Canvas(transform, "InventoryCanvas", 110);
            var theme = UiTheme.Active;
            int rows = Inventory.SlotCount / Columns;
            var size = new Vector2(Columns * Cell + (Columns + 1) * Gap, rows * Cell + (rows + 1) * Gap + 56f);
            var center = new Vector2(0.5f, 0.5f);
            var back = UiKit.ModalPanel(canvas.transform, "Inventory", size, out root); // U-058: opaque, over a scrim
            UiPaper.ApplyModal(back, Meridian.Art.ArtKeys.Ui.PanelInventory, ok => Paper = ok); // U-124 (B-151): inventory paper; flat until the art is on disk
            var title = UiKit.Text(back.transform, "Title", new Vector2(0f, 1f), new Vector2(Gap + 4f, -28f), new Vector2(300f, 28f), 20, true, TextAnchor.MiddleLeft, theme.label);
            title.text = "INVENTORY";
            SelectedName = UiKit.Text(back.transform, "Selected", new Vector2(1f, 1f), new Vector2(-Gap - 4f, -28f), new Vector2(420f, 28f), 18, false, TextAnchor.MiddleRight, theme.text);
            SelectedName.rectTransform.pivot = new Vector2(1f, 0.5f);

            Icons = new Image[Inventory.SlotCount];
            Counts = new Text[Inventory.SlotCount];
            frames = new Image[Inventory.SlotCount];
            bands = new Image[Inventory.SlotCount];
            chips = new Image[Inventory.SlotCount];
            var tl = new Vector2(0f, 1f);
            for (int i = 0; i < Inventory.SlotCount; i++)
            {
                int col = i % Columns, row = i / Columns;
                var pos = new Vector2(Gap + col * (Cell + Gap), -56f - row * (Cell + Gap));
                var cell = UiKit.Rect(back.transform, "Slot" + i, tl, pos, new Vector2(Cell, Cell), tl);
                var frame = cell.gameObject.AddComponent<Image>();
                frame.color = UiKit.SlotFill; // U-135 (D-149): an ink-line box on a faint darkening of the paper, so an empty inventory shows its grid
                frames[i] = frame;
                UiKit.InkEdges(cell, UiKit.SlotEdge, UiKit.Ink);
                bands[i] = UiKit.GoldBand(cell); // the selected slot's gold band
                int slot = i;
                cell.gameObject.AddComponent<Button>().onClick.AddListener(() => { if (inventory != null) inventory.Select(slot); });
                var icon = UiKit.Panel(cell, "Icon", center, new Vector2(-3f, 3f), new Vector2(Cell - 24f, Cell - 24f), Color.white); // U-181 (LEAD): nudged up-left of the count chip
                icon.preserveAspect = true;
                icon.enabled = false;
                Icons[i] = icon;
                // U-181 (LEAD, u181 review): the stack count on a small paper chip in the slot's bottom-right corner, in ink at ≥ 18 px, crisp
                // (no rim), never over the icon's middle: selling by the pack makes the counts matter
                var chip = UiKit.PaperTag(cell, "CountChip", new Vector2(1f, 0f), new Vector2(-3f, 3f), new Vector2(ChipW, ChipH), new Vector2(1f, 0f));
                chip.raycastTarget = false;
                var count = UiKit.Text(chip.transform, "Count", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(ChipW - 4f, ChipH), CountSize, true, TextAnchor.MiddleCenter, UiKit.Ink);
                UiKit.InkOn(count);
                count.horizontalOverflow = HorizontalWrapMode.Overflow; // a fixed 26 px: "999" fits the chip's 42 px
                chip.gameObject.SetActive(false);
                Counts[i] = count;
                chips[i] = chip;
            }
            root.SetActive(false);
            enabled = false;
        }

        void Update()
        {
            if (toggle != null) PanelInput.Hold(toggle.actionMap); // U-134: re-held each frame (a resume re-enables whole maps)
            if (dirty) Redraw();
        }

        void Redraw()
        {
            dirty = false;
            if (inventory == null) return;
            for (int i = 0; i < Inventory.SlotCount; i++)
            {
                var s = inventory[i];
                bool selected = i == inventory.Selected;
                if (bands[i].enabled != selected) bands[i].enabled = selected; // U-135: the gold band, not an accent fill
                if (s.IsEmpty) { Icons[i].enabled = false; Counts[i].text = ""; if (chips[i].gameObject.activeSelf) chips[i].gameObject.SetActive(false); continue; }
                if (!chips[i].gameObject.activeSelf) chips[i].gameObject.SetActive(true);
                var sprite = IconOf(s.itemId);
                Icons[i].sprite = sprite;
                Icons[i].enabled = sprite != null;
                Counts[i].text = numbers[s.count];
            }
            var sel = inventory[inventory.Selected];
            var def = sel.IsEmpty ? null : ItemRegistry.Get(sel.itemId);
            SelectedName.text = def == null ? "" : def.placeTile != 0 ? def.name + "  ·  BUILDER" : def.name;
        }

        /// <summary>The item's icon from the shared cache (U-058); a late icon marks the panel dirty.</summary>
        Sprite IconOf(int itemId) => ItemIcons.Get(itemId, terrain);
    }
}
