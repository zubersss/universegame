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
    /// U-051: the crafting panel (B): the Blueprint Tree on the left (tier columns; unlocked nodes lit,
    /// locked ones dim with what unlocks them) and the recipes on the right (station, inputs, a Craft button
    /// that works when the blueprint, station and inputs are all there). Closed, it does no per-frame work.
    /// </summary>
    public sealed class CraftingPanel : MonoBehaviour
    {
        public PlayerController player;
        public static bool AnyOpen { get; private set; }
        public bool IsOpen => root != null && root.activeSelf;

        /// <summary>Tree nodes by blueprint id (tests and captures read them).</summary>
        public readonly Dictionary<string, Image> Nodes = new Dictionary<string, Image>();
        public readonly Dictionary<string, Button> CraftButtons = new Dictionary<string, Button>();
        public string LastMessage { get; private set; } = "";

        static readonly Color Lit = new Color(0.32f, 0.62f, 0.86f, 0.9f), Dim = new Color(1f, 1f, 1f, 0.08f);
        GameObject root;
        Text message;
        InputAction toggle;
        RecipeBook book;
        Inventory inventory;
        readonly List<(Recipe recipe, Text label)> rows = new List<(Recipe, Text)>();
        float nextRefresh;

        void Start()
        {
            book = RecipeBook.Active;
            if (GameState.Instance != null) inventory = GameState.Instance.inventory;
            Build();
            if (inventory != null) inventory.Changed += Refresh;
            if (player != null && player.actions != null)
            {
                toggle = player.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("BuildMenu");
                if (toggle != null) toggle.performed += _ => SetOpen(!IsOpen);
            }
        }

        void OnDestroy()
        {
            if (inventory != null) inventory.Changed -= Refresh;
            if (IsOpen) AnyOpen = false;
        }

        public void SetOpen(bool open)
        {
            if (root == null || root.activeSelf == open) return;
            root.SetActive(open);
            AnyOpen = open;
            enabled = open;
            if (open) Refresh();
        }

        void Update()
        {
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
            var center = new Vector2(0.5f, 0.5f);
            var back = UiKit.Panel(canvas.transform, "Crafting", center, Vector2.zero, new Vector2(1840f, 820f), new Color(0.04f, 0.05f, 0.07f, 0.92f));
            root = back.gameObject;
            var tl = new Vector2(0f, 1f);
            UiKit.Text(back.transform, "TreeTitle", tl, new Vector2(24f, -30f), new Vector2(400f, 28f), 20, true, TextAnchor.MiddleLeft, theme.label).text = "BLUEPRINT TREE";
            UiKit.Text(back.transform, "RecipeTitle", tl, new Vector2(820f, -30f), new Vector2(400f, 28f), 20, true, TextAnchor.MiddleLeft, theme.label).text = "RECIPES";
            message = UiKit.Text(back.transform, "Message", new Vector2(0f, 0f), new Vector2(24f, 22f), new Vector2(1790f, 24f), 16, false, TextAnchor.MiddleLeft, theme.text);

            if (book == null) { message.text = "No recipe book (MERIDIAN/Authoring)"; root.SetActive(false); enabled = false; return; }

            // Tree: one column per tier, nodes stacked.
            var perTier = new Dictionary<int, int>();
            foreach (var b in book.blueprints)
            {
                perTier.TryGetValue(b.tier, out int n);
                perTier[b.tier] = n + 1;
                var pos = new Vector2(24f + b.tier * 152f, -70f - n * 92f); // five tiers fit left of the recipes (x < 790)
                var node = UiKit.Rect(back.transform, "Node_" + b.id, tl, pos, new Vector2(144f, 80f), tl).gameObject.AddComponent<Image>();
                node.color = Dim;
                Nodes[b.id] = node;
                var t = UiKit.Text(node.transform, "Name", tl, new Vector2(8f, -14f), new Vector2(132f, 22f), 13, true, TextAnchor.MiddleLeft, theme.text);
                t.horizontalOverflow = HorizontalWrapMode.Wrap;
                t.text = b.name;
                string needs = string.IsNullOrEmpty(b.unlockFlag) ? (b.requires != null && b.requires.Length > 0 ? "after " + b.requires[0] : "known") : b.unlockFlag.Replace("beacon:", "beacon · ");
                UiKit.Text(node.transform, "Needs", tl, new Vector2(8f, -50f), new Vector2(132f, 20f), 11, false, TextAnchor.MiddleLeft, theme.label).text = needs;
            }

            // Recipes: a row each.
            int row = 0;
            foreach (var r in book.recipes)
            {
                var pos = new Vector2(820f, -70f - row * 44f);
                var label = UiKit.Text(back.transform, "Recipe_" + r.id, tl, pos, new Vector2(560f, 36f), 14, false, TextAnchor.MiddleLeft, theme.text);
                label.text = Describe(r);
                rows.Add((r, label));
                var recipe = r;
                var btn = UiKit.Button(back.transform, "CRAFT", Vector2.zero, () => Craft(recipe));
                var rt = (RectTransform)btn.transform;
                rt.anchorMin = rt.anchorMax = rt.pivot = tl;
                rt.anchoredPosition = new Vector2(1690f, pos.y);
                rt.sizeDelta = new Vector2(130f, 36f);
                CraftButtons[r.id] = btn;
                row++;
            }
            root.SetActive(false);
            enabled = false;
        }

        static string Name(string key) => ItemRegistry.Get(key)?.name ?? key;

        static string Describe(Recipe r)
        {
            var sb = new System.Text.StringBuilder();
            sb.Append(r.output.count).Append(" × ").Append(Name(r.output.item)).Append("   ←   ");
            for (int i = 0; i < r.inputs.Length; i++)
            {
                if (i > 0) sb.Append(" + ");
                sb.Append(r.inputs[i].count).Append(' ').Append(Name(r.inputs[i].item));
            }
            sb.Append("   [").Append(r.station).Append(']');
            return sb.ToString();
        }

        /// <summary>Crafts a recipe (buttons and tests). Returns the outcome; the panel shows it.</summary>
        public CraftingSystem.Result Craft(Recipe r)
        {
            var result = CraftingSystem.Craft(book, r, inventory, Flags, Here);
            LastMessage = result == CraftingSystem.Result.Crafted ? $"Crafted {r.output.count} × {Name(r.output.item)}" : $"{Name(r.output.item)}: {result}";
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
            foreach (var (r, label) in rows)
            {
                var check = CraftingSystem.Check(book, r, inventory, flags, Here);
                bool unlocked = check != CraftingSystem.Result.Locked;
                label.color = unlocked ? UiTheme.Active.text : new Color(1f, 1f, 1f, 0.3f);
                bool can = check == CraftingSystem.Result.Crafted;
                var btn = CraftButtons[r.id];
                btn.interactable = can;
                var caption = btn.GetComponentInChildren<Text>();
                if (caption != null) caption.color = can ? UiTheme.Active.text : new Color(1f, 1f, 1f, 0.22f); // clearly not craftable
            }
        }
    }
}
