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
        /// <summary>U-135 (D-149): the crafting panel's paper — the inventory's (the 192×128 sign stretched over 1840×900 drew its plank lines as two bars).</summary>
        public const string PaperKey = Meridian.Art.ArtKeys.Ui.PanelInventory;

        /// <summary>Tree nodes by blueprint id (tests and captures read them).</summary>
        public readonly Dictionary<string, Image> Nodes = new Dictionary<string, Image>();
        public readonly Dictionary<string, Button> CraftButtons = new Dictionary<string, Button>();
        /// <summary>U-140 (D-151): the recipes column pages inside the paper (nothing draws past its bottom edge): this many rows a page, PREV / NEXT
        /// cards, PageUp / PageDown and the wheel, a faded-ink row count.</summary>
        public const int RecipesPerPage = 17;
        public int Page { get; private set; }
        public int Pages => Mathf.Max(1, (rows.Count + RecipesPerPage - 1) / RecipesPerPage);
        public Button PrevButton { get; private set; }
        public Button NextButton { get; private set; }
        public Text RowCount { get; private set; }

        /// <summary>U-140: shows page p of the recipes (clamped): its rows moved up into the first page's slots, the rest hidden.</summary>
        public void ShowPage(int p)
        {
            Page = Mathf.Clamp(p, 0, Pages - 1);
            float lift = Page * RecipesPerPage * RowH;
            for (int i = 0; i < rows.Count; i++)
            {
                bool on = i / RecipesPerPage == Page;
                var row = rows[i];
                for (int k = 0; k < row.parts.Count; k++)
                {
                    var part = row.parts[k];
                    if (part.gameObject.activeSelf != on) part.gameObject.SetActive(on);
                    if (on) part.anchoredPosition = new Vector2(part.anchoredPosition.x, row.baseY[k] + lift);
                }
            }
            if (RowCount != null)
            {
                int first = Page * RecipesPerPage, last = Mathf.Min(rows.Count, first + RecipesPerPage);
                RowCount.text = rows.Count == 0 ? "" : $"recipes {first + 1}–{last} of {rows.Count}"; // on a page change only
                RowCount.color = UiKit.Letter(Paper, false);
            }
            if (PrevButton != null) UiKit.SetAction(PrevButton, Page > 0);
            if (NextButton != null) UiKit.SetAction(NextButton, Page < Pages - 1);
        }

        /// <summary>U-194: the page a recipe's row is on (-1 if the panel lists no such recipe), for the smoke's shot of a given row.</summary>
        public int PageOf(string recipeId)
        {
            for (int i = 0; i < rows.Count; i++) if (rows[i].recipe != null && rows[i].recipe.id == recipeId) return i / RecipesPerPage;
            return -1;
        }
        public string LastMessage { get; private set; } = "";

        const float RowH = 42f, Icon = 30f;

        sealed class Row
        {
            public Recipe recipe;
            public Text name, station;
            public readonly List<(Image icon, int itemId)> icons = new List<(Image, int)>();
            /// <summary>U-140: every piece the row drew on the panel and its y on the first page.</summary>
            public readonly List<RectTransform> parts = new List<RectTransform>(12);
            public readonly List<float> baseY = new List<float>(12);
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
            PanelInput.Close(this); // U-134
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
            if (open) PanelInput.Open(this, toggle != null ? toggle.actionMap : null); else PanelInput.Close(this); // U-134: the surveyor stands still while a panel is open
            AnyOpen = open;
            enabled = open;
            if (open) { FillIcons(); Refresh(); UiKit.SelectFirst(root.transform); } // U-124: keyboard reach, the first craftable button takes the keys
        }

        void Update()
        {
            if (toggle != null) PanelInput.Hold(toggle.actionMap); // U-134: re-held each frame (a resume re-enables whole maps)
            if (iconsDirty) { iconsDirty = false; FillIcons(); }
            // Stations come and go as the surveyor walks: refresh twice a second while open.
            // U-140: PageUp / PageDown and the wheel page the recipes (read only while the panel is open: Update runs only then).
            var kb = Keyboard.current;
            if (kb != null) { if (kb.pageDownKey.wasPressedThisFrame) ShowPage(Page + 1); else if (kb.pageUpKey.wasPressedThisFrame) ShowPage(Page - 1); }
            var mouse = Mouse.current;
            if (mouse != null) { float wheel = mouse.scroll.ReadValue().y; if (wheel < -0.01f) ShowPage(Page + 1); else if (wheel > 0.01f) ShowPage(Page - 1); }
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
            UiPaper.ApplyModal(back, PaperKey, ok => Paper = ok); // U-135 (D-149): on the inventory paper (the sign stays for short in-world labels); flat until the art is on disk
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
                UiKit.PaperCard(node); // D-149 (U-136): a blueprint tile is a paper card; known = the gold band, locked = greyed
            }

            // Recipes: icon rows.
            for (int i = 0; i < book.recipes.Count; i++)
            {
                var r = book.recipes[i];
                float y = -72f - i * RowH;
                var row = new Row { recipe = r };
                int partsFrom = back.transform.childCount; // U-140: what this row draws is paged as one
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
                for (int c = partsFrom; c < back.transform.childCount; c++)
                {
                    var part = (RectTransform)back.transform.GetChild(c);
                    row.parts.Add(part);
                    row.baseY.Add(part.anchoredPosition.y);
                }
                rows.Add(row);
            }
            // U-140: the page cards and the row count along the paper's bottom, clear of the message line.
            PrevButton = UiKit.ActionButton(back.transform, "PREV", tl, new Vector2(1490f, -832f), new Vector2(150f, 34f), () => ShowPage(Page - 1));
            NextButton = UiKit.ActionButton(back.transform, "NEXT", tl, new Vector2(1660f, -832f), new Vector2(150f, 34f), () => ShowPage(Page + 1));
            RowCount = UiKit.Text(back.transform, "RowCount", tl, new Vector2(860f, -836f), new Vector2(560f, 26f), 14, false, TextAnchor.MiddleLeft, theme.label);
            ShowPage(0);
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
                if (Nodes.TryGetValue(b.id, out var img)) UiKit.SetCard(img, CraftingSystem.IsUnlocked(b, flags) ? UiKit.Card.Gold : UiKit.Card.Locked);
            foreach (var row in rows)
            {
                var check = CraftingSystem.Check(book, row.recipe, inventory, flags, Here);
                bool unlocked = check != CraftingSystem.Result.Locked;
                row.name.color = UiKit.Letter(Paper, unlocked); // D-149: ink on the paper (the 0.4.5 smoke: near-white names on cream)
                bool stationHere = check != CraftingSystem.Result.NoStation && check != CraftingSystem.Result.Locked;
                row.station.color = Paper == true ? (stationHere ? UiKit.Ink : UiKit.InkFaded) : stationHere ? UiTheme.Accent(null) : UiTheme.Active.label;
                UiKit.SetAction(CraftButtons[row.recipe.id], check == CraftingSystem.Result.Crafted);
            }
        }
    }
}
