using System.Collections.Generic;
using Meridian.Core;
using Meridian.Crafting;
using Meridian.Items;
using Meridian.Player;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-051 crafting panel (B), U-058 readability: a modal opaque panel over a scrim (the HUD hides behind it).
    /// The Blueprint Tree on the left (tier columns; unlocked nodes lit, locked ones dim with what unlocks them);
    /// recipes on the right as icon rows (output, inputs with counts, station) with a CRAFT button that is plainly
    /// off unless the blueprint, the station and the inputs are all there. Closed, it does no per-frame work.
    /// </summary>
    public sealed class CraftingPanel : MonoBehaviour
    {
        public PlayerController player;
        public static bool AnyOpen { get; private set; }
        public bool IsOpen => root != null && root.activeSelf;
        /// <summary>U-124: true once the panel's paper drew, false when its key is absent (null while the probe runs).</summary>
        public bool? Paper { get; private set; }

        /// <summary>Tree nodes by blueprint id (tests and captures read them).</summary>
        public readonly Dictionary<string, Image> Nodes = new Dictionary<string, Image>();
        public readonly Dictionary<string, Button> CraftButtons = new Dictionary<string, Button>();
        public string LastMessage { get; private set; } = "";

        static readonly Color Lit = new Color(0.25f, 0.55f, 0.85f, 1f), Dim = new Color(0.12f, 0.13f, 0.16f, 1f);
        const float RowH = 42f, Icon = 30f;

        sealed class Row
        {
            public Recipe recipe;
            public Text name, station;
            public readonly List<(Image icon, int itemId)> icons = new List<(Image, int)>();
        }

        GameObject root;
        Text message;
        InputAction toggle;
        RecipeBook book;
        Inventory inventory;
        Meridian.Terrain.TerrainStreamer terrain;
        readonly List<Row> rows = new List<Row>();
        readonly List<(Image img, string name)> nodeIcons = new List<(Image, string)>();
        float nextRefresh;
        bool iconsDirty;

        void Start()
        {
            book = RecipeBook.Active;
            if (GameState.Instance != null) inventory = GameState.Instance.inventory;
            terrain = FindAnyObjectByType<Meridian.Terrain.TerrainStreamer>();
            Build();
            if (inventory != null) inventory.Changed += Refresh;
            ItemIcons.Loaded += MarkIcons;
            if (player != null && player.actions != null)
            {
                toggle = player.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("BuildMenu");
                if (toggle != null) toggle.performed += OnToggle;
            }
        }

        void OnDestroy()
        {
            if (inventory != null) inventory.Changed -= Refresh;
            ItemIcons.Loaded -= MarkIcons;
            if (toggle != null) toggle.performed -= OnToggle;
            if (IsOpen) AnyOpen = false;
        }

        void OnToggle(InputAction.CallbackContext _) => SetOpen(!IsOpen);
        void MarkIcons() => iconsDirty = true;

        public void SetOpen(bool open)
        {
            if (root == null || root.activeSelf == open) return;
            root.SetActive(open);
            AnyOpen = open;
            enabled = open;
            if (open) { FillIcons(); Refresh(); UiKit.SelectFirst(root.transform); } // U-124: keyboard reach, the first craftable button takes the keys
        }

        void Update()
        {
            if (iconsDirty) { iconsDirty = false; FillIcons(); }
            // Stations come and go as the surveyor walks: refresh twice a second while open.
            if (Time.unscaledTime < nextRefresh) return;
            nextRefresh = Time.unscaledTime + 0.5f;
            Refresh();
        }

        Vector2 Here => player != null ? (Vector2)player.transform.position : Vector2.zero;
        ICollection<string> Flags => GameState.Instance != null ? GameState.Instance.storyFlags : null;

        void Build()
        {
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "CraftingCanvas", 111);
            var back = UiKit.ModalPanel(canvas.transform, "Crafting", new Vector2(1840f, 900f), out root);
            UiPaper.ApplyModal(back, Meridian.Art.ArtKeys.Ui.PanelSign, ok => Paper = ok); // U-124 (B-151): the workbench on the painted wooden sign (P-50); flat until the art is on disk
            var tl = new Vector2(0f, 1f);
            UiKit.Text(back.transform, "TreeTitle", tl, new Vector2(28f, -32f), new Vector2(400f, 28f), 20, true, TextAnchor.MiddleLeft, theme.label).text = "BLUEPRINT TREE";
            UiKit.Text(back.transform, "RecipeTitle", tl, new Vector2(860f, -32f), new Vector2(400f, 28f), 20, true, TextAnchor.MiddleLeft, theme.label).text = "RECIPES";
            message = UiKit.Text(back.transform, "Message", new Vector2(0f, 0f), new Vector2(28f, 26f), new Vector2(1790f, 24f), 16, false, TextAnchor.MiddleLeft, theme.text);

            if (book == null) { message.text = "No recipe book (MERIDIAN/Authoring)"; root.SetActive(false); enabled = false; return; }

            // Tree: one column per tier, nodes stacked.
            var perTier = new Dictionary<int, int>();
            foreach (var b in book.blueprints)
            {
                perTier.TryGetValue(b.tier, out int n);
                perTier[b.tier] = n + 1;
                var pos = new Vector2(28f + b.tier * 158f, -72f - n * 96f);
                var node = UiKit.Rect(back.transform, "Node_" + b.id, tl, pos, new Vector2(148f, 84f), tl).gameObject.AddComponent<Image>();
                node.color = Dim;
                Nodes[b.id] = node;
                var nodeIcon = UiKit.Panel(node.transform, "Icon", new Vector2(1f, 0f), new Vector2(-6f, 6f), new Vector2(30f, 30f), Color.white);
                nodeIcon.rectTransform.pivot = new Vector2(1f, 0f);
                nodeIcon.preserveAspect = true;
                nodeIcon.enabled = false;
                nodeIcons.Add((nodeIcon, b.icon));
                var t = UiKit.Text(node.transform, "Name", tl, new Vector2(10f, -16f), new Vector2(132f, 22f), 14, true, TextAnchor.MiddleLeft, theme.text);
                t.horizontalOverflow = HorizontalWrapMode.Wrap;
                t.text = b.name;
                string needs = string.IsNullOrEmpty(b.unlockFlag) ? (b.requires != null && b.requires.Length > 0 ? "after " + b.requires[0] : "known") : b.unlockFlag.Replace("beacon:", "beacon · ");
                UiKit.Text(node.transform, "Needs", tl, new Vector2(10f, -62f), new Vector2(132f, 18f), 12, false, TextAnchor.MiddleLeft, theme.label).text = needs;
            }

            // Recipes: icon rows.
            for (int i = 0; i < book.recipes.Count; i++)
            {
                var r = book.recipes[i];
                float y = -72f - i * RowH;
                var row = new Row { recipe = r };
                float x = 860f;
                row.icons.Add((IconAt(back.transform, x, y), ItemRegistry.Get(r.output.item)?.id ?? 0));
                row.name = UiKit.Text(back.transform, "Out_" + r.id, tl, new Vector2(x + Icon + 8f, y - 4f), new Vector2(250f, Icon), 16, true, TextAnchor.MiddleLeft, theme.text);
                row.name.text = (r.output.count > 1 ? r.output.count + " × " : "") + Name(r.output.item);
                x += 300f;
                UiKit.Text(back.transform, "Arrow_" + r.id, tl, new Vector2(x, y - 4f), new Vector2(30f, Icon), 18, true, TextAnchor.MiddleCenter, theme.label).text = "←";
                x += 40f;
                foreach (var a in r.inputs)
                {
                    row.icons.Add((IconAt(back.transform, x, y), ItemRegistry.Get(a.item)?.id ?? 0));
                    UiKit.Text(back.transform, "In_" + r.id + a.item, tl, new Vector2(x + Icon + 4f, y - 4f), new Vector2(40f, Icon), 16, true, TextAnchor.MiddleLeft, theme.text).text = "× " + a.count;
                    x += Icon + 56f;
                }
                row.station = UiKit.Text(back.transform, "Station_" + r.id, tl, new Vector2(1500f, y - 4f), new Vector2(150f, Icon), 13, false, TextAnchor.MiddleLeft, theme.label);
                row.station.text = r.station.ToString().ToUpperInvariant();
                var recipe = r;
                CraftButtons[r.id] = UiKit.ActionButton(back.transform, "CRAFT", tl, new Vector2(1680f, y), new Vector2(130f, 34f), () => Craft(recipe));
                rows.Add(row);
            }
            root.SetActive(false);
            enabled = false;
        }

        static Image IconAt(Transform parent, float x, float y)
        {
            var img = UiKit.Panel(parent, "Icon", new Vector2(0f, 1f), new Vector2(x, y), new Vector2(Icon, Icon), Color.white);
            img.rectTransform.pivot = new Vector2(0f, 1f);
            img.preserveAspect = true;
            img.enabled = false;
            return img;
        }

        void FillIcons()
        {
            foreach (var (img, name) in nodeIcons)
            {
                // A blueprint icon is an art name (B-051), or an item's key.
                var sp = ItemIcons.GetNamed(name);
                img.sprite = sp;
                img.enabled = sp != null;
            }
            foreach (var row in rows)
                foreach (var (icon, id) in row.icons)
                {
                    var sp = ItemIcons.Get(id, terrain);
                    icon.sprite = sp;
                    icon.enabled = sp != null;
                }
        }

        static string Name(string key) => ItemRegistry.Get(key)?.name ?? key;

        /// <summary>Crafts a recipe (buttons and tests). Returns the outcome; the panel shows it.</summary>
        public CraftingSystem.Result Craft(Recipe r)
        {
            var result = CraftingSystem.Craft(book, r, inventory, Flags, Here);
            LastMessage = result == CraftingSystem.Result.Crafted ? $"Crafted {r.output.count} × {Name(r.output.item)}" : $"{Name(r.output.item)}: {result}";
            // U-065: a ship upgrade fits itself to the Pilgrim when crafted (the item is used up).
            if (result == CraftingSystem.Result.Crafted && Meridian.Ship.ShipMarks.Install(GameState.Instance, r.output.item))
            {
                inventory.Remove(ItemRegistry.Get(r.output.item).id, 1);
                LastMessage = $"Installed {Name(r.output.item)}";
            }
            if (message != null) message.text = LastMessage;
            Refresh();
            return result;
        }

        void Refresh()
        {
            if (!IsOpen || book == null || inventory == null) return;
            var flags = Flags;
            foreach (var b in book.blueprints)
                if (Nodes.TryGetValue(b.id, out var img)) img.color = CraftingSystem.IsUnlocked(b, flags) ? Lit : Dim;
            foreach (var row in rows)
            {
                var check = CraftingSystem.Check(book, row.recipe, inventory, flags, Here);
                bool unlocked = check != CraftingSystem.Result.Locked;
                row.name.color = unlocked ? UiTheme.Active.text : new Color(1f, 1f, 1f, 0.3f);
                bool stationHere = check != CraftingSystem.Result.NoStation && check != CraftingSystem.Result.Locked;
                row.station.color = stationHere ? UiTheme.Accent(null) : UiTheme.Active.label;
                UiKit.SetAction(CraftButtons[row.recipe.id], check == CraftingSystem.Result.Crafted);
            }
        }
    }
}
