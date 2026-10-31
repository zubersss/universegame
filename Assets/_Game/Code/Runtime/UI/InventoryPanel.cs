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

        public PlayerController player;
        public Meridian.Terrain.TerrainStreamer terrain;
        public Inventory inventory;

        public bool IsOpen => root != null && root.activeSelf;
        /// <summary>True while any inventory panel is open: rig clicks pass to the panel, not the world.</summary>
        public static bool AnyOpen { get; private set; }
        public Image[] Icons { get; private set; }
        public Text[] Counts { get; private set; }
        public Text SelectedName { get; private set; }

        GameObject root;
        Image[] frames;
        InputAction toggle;
        bool dirty = true;
        static UiKit.NumberStrings numbers;
        readonly Dictionary<int, Sprite> icons = new Dictionary<int, Sprite>();
        readonly HashSet<int> requested = new HashSet<int>();
        readonly List<AsyncOperationHandle<IList<Sprite>>> handles = new List<AsyncOperationHandle<IList<Sprite>>>();

        void Start()
        {
            numbers ??= new UiKit.NumberStrings(0, Inventory.StackMax);
            if (terrain == null) terrain = FindAnyObjectByType<Meridian.Terrain.TerrainStreamer>();
            if (inventory == null && Meridian.Core.GameState.Instance != null) inventory = Meridian.Core.GameState.Instance.inventory;
            Build();
            if (inventory != null) inventory.Changed += MarkDirty;
            if (player != null && player.actions != null)
            {
                toggle = player.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("Inventory");
                if (toggle != null) toggle.performed += OnToggle;
            }
        }

        void OnDestroy()
        {
            if (inventory != null) inventory.Changed -= MarkDirty;
            if (IsOpen) AnyOpen = false;
            if (toggle != null) toggle.performed -= OnToggle;
            foreach (var h in handles) if (h.IsValid()) Addressables.Release(h);
            handles.Clear();
        }

        void OnToggle(InputAction.CallbackContext _) => SetOpen(!IsOpen);

        void MarkDirty() => dirty = true;

        public void SetOpen(bool open)
        {
            if (root == null || root.activeSelf == open) return;
            root.SetActive(open);
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
            var back = UiKit.Panel(canvas.transform, "Inventory", center, Vector2.zero, size, new Color(0.04f, 0.05f, 0.07f, 0.86f));
            root = back.gameObject;
            var title = UiKit.Text(back.transform, "Title", new Vector2(0f, 1f), new Vector2(Gap + 4f, -28f), new Vector2(300f, 28f), 20, true, TextAnchor.MiddleLeft, theme.label);
            title.text = "INVENTORY";
            SelectedName = UiKit.Text(back.transform, "Selected", new Vector2(1f, 1f), new Vector2(-Gap - 4f, -28f), new Vector2(420f, 28f), 18, false, TextAnchor.MiddleRight, theme.text);
            SelectedName.rectTransform.pivot = new Vector2(1f, 0.5f);

            Icons = new Image[Inventory.SlotCount];
            Counts = new Text[Inventory.SlotCount];
            frames = new Image[Inventory.SlotCount];
            var tl = new Vector2(0f, 1f);
            for (int i = 0; i < Inventory.SlotCount; i++)
            {
                int col = i % Columns, row = i / Columns;
                var pos = new Vector2(Gap + col * (Cell + Gap), -56f - row * (Cell + Gap));
                var cell = UiKit.Rect(back.transform, "Slot" + i, tl, pos, new Vector2(Cell, Cell), tl);
                var frame = cell.gameObject.AddComponent<Image>();
                frame.color = new Color(1f, 1f, 1f, 0.06f);
                frames[i] = frame;
                int slot = i;
                cell.gameObject.AddComponent<Button>().onClick.AddListener(() => { if (inventory != null) inventory.Select(slot); });
                var icon = UiKit.Panel(cell, "Icon", center, Vector2.zero, new Vector2(Cell - 20f, Cell - 20f), Color.white);
                icon.preserveAspect = true;
                icon.enabled = false;
                Icons[i] = icon;
                var count = UiKit.Text(cell, "Count", new Vector2(1f, 0f), new Vector2(-6f, 14f), new Vector2(Cell - 8f, 22f), 16, true, TextAnchor.MiddleRight, theme.text);
                count.rectTransform.pivot = new Vector2(1f, 0.5f);
                Counts[i] = count;
            }
            root.SetActive(false);
            enabled = false;
        }

        void Update()
        {
            if (dirty) Redraw();
        }

        void Redraw()
        {
            dirty = false;
            if (inventory == null) return;
            var accent = UiTheme.Accent(null);
            for (int i = 0; i < Inventory.SlotCount; i++)
            {
                var s = inventory[i];
                bool selected = i == inventory.Selected;
                frames[i].color = selected ? new Color(accent.r, accent.g, accent.b, 0.35f) : new Color(1f, 1f, 1f, 0.06f);
                if (s.IsEmpty) { Icons[i].enabled = false; Counts[i].text = ""; continue; }
                var sprite = IconOf(s.itemId);
                Icons[i].sprite = sprite;
                Icons[i].enabled = sprite != null;
                Counts[i].text = numbers[s.count];
            }
            var sel = inventory[inventory.Selected];
            var def = sel.IsEmpty ? null : ItemRegistry.Get(sel.itemId);
            SelectedName.text = def == null ? "" : def.placeTile != 0 ? def.name + "  ·  BUILDER" : def.name;
        }

        /// <summary>The item's icon (B-013), or for tile items without one the tile's own sprite; loads once.</summary>
        Sprite IconOf(int itemId)
        {
            if (icons.TryGetValue(itemId, out var sp)) return sp;
            var def = ItemRegistry.Get(itemId);
            if (def == null) return null;
            if (def.icon == null)
            {
                var tile = terrain != null ? terrain.TileSet.Get(def.placeTile, Meridian.Terrain.BlobAutotile.VariantCount - 1) as UnityEngine.Tilemaps.Tile : null;
                if (tile != null && tile.sprite != null) icons[itemId] = tile.sprite;
                return tile != null ? tile.sprite : null;
            }
            if (requested.Add(itemId))
            {
                var h = Addressables.LoadAssetAsync<IList<Sprite>>(def.icon);
                handles.Add(h);
                h.Completed += op =>
                {
                    if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    icons[itemId] = op.Result[0];
                    dirty = true;
                };
            }
            return null;
        }
    }
}
