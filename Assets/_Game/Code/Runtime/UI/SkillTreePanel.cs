using System.Collections.Generic;
using Meridian.Art;
using Meridian.Core;
using Meridian.Items;
using Meridian.Player;
using Meridian.Progress;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-175 (D-174, Bible 5.2 §8.1; B-204's ui/skilltree art): the Skill Tree (K). B-204's round chart with the hub, the six branch emblems
    /// and the 66 nodes at their ring radius on their branch's axis plus their slot (the chart.json geometry); links drawn under the frames
    /// (bought: both ends bought; open: one; locked: neither); node frames by state (ring 5 the caps) with the node's icon at 40 px (0.4
    /// alpha while locked); the chosen node's card: its effect, its cost, BUY. Buying is topside only. No per-frame work while closed.
    /// </summary>
    public sealed class SkillTreePanel : MonoBehaviour
    {
        public PlayerController player;
        public static bool AnyOpen { get; private set; }
        public bool IsOpen => root != null && root.activeSelf;
        public string Selected { get; private set; }
        public SkillTree.BuyResult LastBuy { get; private set; }
        /// <summary>Each node's frame (tests and captures read them).</summary>
        public readonly Dictionary<string, Image> Frames = new Dictionary<string, Image>();
        public Text Title { get; private set; }
        public Text Effect { get; private set; }
        public Text CostText { get; private set; }
        public Text Status { get; private set; }

        // chart.json (B-204): ring radii, branch axes and slot angles at the chart's 960 px; drawn here at ChartPx.
        static readonly Dictionary<int, float> RingPx = new Dictionary<int, float> { { 1, 140f }, { 2, 210f }, { 3, 285f }, { 4, 355f }, { 5, 420f } };
        static readonly Dictionary<string, float> AxisDeg = new Dictionary<string, float>
        { { "dig", -90f }, { "haul", -30f }, { "ascent", 30f }, { "survey", 90f }, { "endurance", 150f }, { "voyage", 210f } };
        static readonly float[] Slots2 = { -15f, 15f }, Slots3 = { -20f, 0f, 20f };
        const float ChartPx = 900f, EmblemPx = 408f, NodePx = 64f, IconPx = 40f;
        static readonly Vector2 ChartCentre = new Vector2(-280f, 0f);
        float K => ChartPx / 960f;

        GameObject root;
        InputAction toggle;
        Button buy;
        Image chart, hub;
        readonly Dictionary<string, Image> icons = new Dictionary<string, Image>();
        readonly List<(Image line, string a, string b)> links = new List<(Image, string, string)>();
        readonly List<(Image img, string key)> emblems = new List<(Image, string)>();
        readonly Dictionary<string, Sprite> art = new Dictionary<string, Sprite>();
        readonly HashSet<string> requested = new HashSet<string>();
        readonly List<AsyncOperationHandle<IList<Sprite>>> handles = new List<AsyncOperationHandle<IList<Sprite>>>();

        void Start()
        {
            Build();
            if (player != null && player.actions != null)
            {
                toggle = player.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("Skills");
                if (toggle != null) toggle.performed += OnToggle;
            }
        }

        void OnDestroy()
        {
            PanelInput.Close(this);
            if (toggle != null) toggle.performed -= OnToggle;
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
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
            if (open) { LoadArt(); Redraw(); UiKit.SelectFirst(root.transform, buy); }
        }

        void Update() { if (toggle != null) PanelInput.Hold(toggle.actionMap); }

        /// <summary>The surveyor is topside (the Surface Line, U-174).</summary>
        public bool Topside
        {
            get
            {
                var side = FindAnyObjectByType<PlanetSideRoot>();
                if (side == null || side.terrain == null || player == null || !side.terrain.SmoothGround) return true;
                return Meridian.Mining.DigRun.Topside(side.terrain, player.Body.position);
            }
        }

        public void Select(string id) { Selected = id; Redraw(); }

        /// <summary>BUY: the chosen node, topside only.</summary>
        public SkillTree.BuyResult BuySelected()
        {
            LastBuy = SkillTree.Current.Buy(GameState.Instance, Selected, Topside);
            Redraw();
            return LastBuy;
        }

        static Vector2 Polar(float radiusPx, float screenDeg, float k)
        {
            float a = screenDeg * Mathf.Deg2Rad;
            return ChartCentre + new Vector2(Mathf.Cos(a), -Mathf.Sin(a)) * radiusPx * k; // screen degrees, y down → UI y up
        }

        public static Vector2 NodePosition(SkillTree.Node n, float k)
        {
            var tree = SkillTree.Current;
            int inRing = 0;
            foreach (var o in tree.nodes) if (o.branch == n.branch && o.ring == n.ring) inRing++;
            var slots = inRing >= 3 ? Slots3 : Slots2;
            float deg = AxisDeg.TryGetValue(n.branch, out var ax) ? ax : 0f;
            return Polar(RingPx.TryGetValue(n.ring, out var r) ? r : 140f, deg + slots[Mathf.Clamp(n.slot, 0, slots.Length - 1)], k);
        }

        void Build()
        {
            var canvas = UiKit.Canvas(transform, "SkillTreeCanvas", 115);
            var back = UiKit.ModalPanel(canvas.transform, "SkillTree", new Vector2(1640f, 980f), out root);
            UiPaper.ApplyModal(back, ArtKeys.Ui.PanelScroll, _ => { });
            var c = new Vector2(0.5f, 0.5f);
            var tree = SkillTree.Current;
            float k = K;

            chart = Img(back.transform, "Chart", ChartCentre, new Vector2(ChartPx, ChartPx), Color.white);
            // Links under the frames: ring 1 to the hub, the rest to each linked node (each pair once).
            var drawn = new HashSet<string>();
            foreach (var n in tree.nodes)
            {
                var a = NodePosition(n, k);
                if (n.requires.Length == 0) AddLink(back.transform, a, ChartCentre, n.id, null);
                foreach (var r in n.requires)
                {
                    var o = tree.Get(r);
                    if (o == null) continue;
                    string pair = string.CompareOrdinal(n.id, r) < 0 ? n.id + "|" + r : r + "|" + n.id;
                    if (!drawn.Add(pair)) continue;
                    AddLink(back.transform, a, NodePosition(o, k), n.id, r);
                }
            }
            hub = Img(back.transform, "Hub", ChartCentre, new Vector2(112f, 112f) * k, Color.white);
            foreach (var b in SkillTree.Branches)
                emblems.Add((Img(back.transform, "Emblem_" + b, Polar(EmblemPx, AxisDeg[b], k), new Vector2(96f, 96f) * k, Color.white), "ui/skilltree/emblem_" + b));
            foreach (var n in tree.nodes)
            {
                var id = n.id;
                var frame = Img(back.transform, "Node_" + id, NodePosition(n, k), new Vector2(NodePx, NodePx) * k, Color.white);
                var button = frame.gameObject.AddComponent<Button>();
                button.onClick.AddListener(() => Select(id));
                var icon = Img(frame.transform, "Icon", Vector2.zero, new Vector2(IconPx, IconPx) * k, Color.white);
                icon.raycastTarget = false;
                Frames[id] = frame; icons[id] = icon;
            }

            // The chosen node's card, right of the chart.
            var tl = new Vector2(0.5f, 0.5f);
            float x = 480f; // the card centred right of the chart (UiKit.Text and ActionButton pivot on their centre)
            Title = UiKit.Text(back.transform, "Title", tl, new Vector2(x, 380f), new Vector2(520f, 34f), 22, true, TextAnchor.MiddleLeft, UiKit.Ink);
            Effect = UiKit.Text(back.transform, "Effect", tl, new Vector2(x, 300f), new Vector2(520f, 110f), 18, false, TextAnchor.UpperLeft, UiKit.Ink);
            CostText = UiKit.Text(back.transform, "Cost", tl, new Vector2(x, 170f), new Vector2(520f, 110f), 18, false, TextAnchor.UpperLeft, UiKit.Ink);
            Status = UiKit.Text(back.transform, "Status", tl, new Vector2(x, 60f), new Vector2(520f, 60f), 16, false, TextAnchor.UpperLeft, UiKit.InkFaded);
            buy = UiKit.ActionButton(back.transform, "BUY", tl, new Vector2(x, -20f), new Vector2(220f, 48f), () => BuySelected());
            Selected = tree.nodes.Length > 0 ? tree.nodes[0].id : null;
            root.SetActive(false);
            enabled = false;
        }

        Image Img(Transform parent, string name, Vector2 pos, Vector2 size, Color color)
        {
            var img = UiKit.Panel(parent, name, new Vector2(0.5f, 0.5f), pos, size, color);
            img.rectTransform.pivot = new Vector2(0.5f, 0.5f);
            img.rectTransform.anchoredPosition = pos;
            return img;
        }

        void AddLink(Transform parent, Vector2 a, Vector2 b, string idA, string idB)
        {
            var d = b - a;
            var line = Img(parent, "Link_" + idA + "_" + (idB ?? "hub"), (a + b) * 0.5f, new Vector2(d.magnitude, 16f * K), Color.white);
            line.rectTransform.localRotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
            line.raycastTarget = false;
            line.type = Image.Type.Tiled;
            links.Add((line, idA, idB));
        }

        void LoadArt()
        {
            void Want(string key)
            {
                if (!requested.Add(key)) return;
                var loc = UnityEngine.AddressableAssets.Addressables.LoadResourceLocationsAsync(key);
                loc.Completed += l =>
                {
                    bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                    ArtLoad.Release(l);
                    if (!exists || this == null) return;
                    var h = ArtLoad.Asset<IList<Sprite>>(key);
                    handles.Add(h);
                    h.Completed += op => { if (this != null && op.Status == AsyncOperationStatus.Succeeded && op.Result != null && op.Result.Count > 0) { art[key] = op.Result[0]; if (IsOpen) Redraw(); } };
                };
            }
            foreach (var s in new[] { "chart", "hub", "node_bought", "node_available", "node_locked", "node_cap_bought", "node_cap_available", "node_cap_locked", "link_bought", "link_open", "link_locked", "select" })
                Want("ui/skilltree/" + s);
            foreach (var e in emblems) Want(e.key);
            foreach (var n in SkillTree.Current.nodes) Want("icons/nodes/" + n.id);
        }

        Sprite Art(string key) => art.TryGetValue(key, out var s) ? s : null;

        /// <summary>A node's state: bought, available (linked), locked.</summary>
        public string StateOf(string id)
        {
            var s = GameState.Instance;
            var tree = SkillTree.Current;
            var n = tree.Get(id);
            if (s == null || n == null) return "locked";
            if (s.skillNodes.Contains(id)) return "bought";
            return tree.Linked(n, s.skillNodes) ? "available" : "locked";
        }

        void Redraw()
        {
            var s = GameState.Instance;
            var tree = SkillTree.Current;
            if (s == null) return;
            chart.sprite = Art("ui/skilltree/chart"); chart.color = chart.sprite != null ? Color.white : new Color(0.9f, 0.85f, 0.72f, 1f);
            hub.sprite = Art("ui/skilltree/hub");
            foreach (var e in emblems) { e.img.sprite = Art(e.key); e.img.enabled = e.img.sprite != null; }
            foreach (var n in tree.nodes)
            {
                string state = StateOf(n.id);
                var f = Frames[n.id];
                f.sprite = Art($"ui/skilltree/node_{(n.ring == 5 ? "cap_" : "")}{state}");
                f.color = f.sprite != null ? Color.white : state == "bought" ? UiKit.Gold : state == "available" ? UiKit.Cream : UiKit.Greyed;
                var ic = icons[n.id];
                ic.sprite = Art("icons/nodes/" + n.id);
                ic.enabled = ic.sprite != null;
                ic.color = new Color(1f, 1f, 1f, state == "locked" ? 0.4f : 1f);
                f.transform.localScale = n.id == Selected ? Vector3.one * 1.15f : Vector3.one;
            }
            foreach (var (line, a, b) in links)
            {
                bool ba = s.skillNodes.Contains(a), bb = b == null || s.skillNodes.Contains(b);
                string st = ba && bb ? "bought" : ba || bb ? "open" : "locked";
                line.sprite = Art("ui/skilltree/link_" + st);
                line.color = line.sprite != null ? Color.white : st == "bought" ? UiKit.Gold : st == "open" ? UiKit.Ink : UiKit.InkFaded;
            }
            var sel = tree.Get(Selected);
            if (sel == null) return;
            Title.text = sel.id.ToUpperInvariant().Replace('_', ' ');
            Effect.text = $"{sel.branch.ToUpperInvariant()} · RING {sel.ring}\n{sel.effect}";
            var cost = new System.Text.StringBuilder();
            cost.Append(sel.scrip).Append(" Scrip (purse ").Append(s.scrip).Append(')');
            foreach (var c in sel.items)
            {
                var def = ItemRegistry.Get(c.item);
                cost.Append("\n").Append(def != null ? def.name : c.item).Append(" × ").Append(c.count).Append(" (pack ").Append(def != null ? s.inventory.Count(def.id) : 0).Append(')');
            }
            if (sel.datacores > 0) cost.Append("\nDatacores × ").Append(sel.datacores).Append(" (held ").Append(s.datacores).Append(')');
            CostText.text = cost.ToString();
            var r = tree.CanBuy(s, sel.id, Topside);
            Status.text = r switch
            {
                SkillTree.BuyResult.Ok => "Ready to buy.",
                SkillTree.BuyResult.AlreadyBought => "Bought.",
                SkillTree.BuyResult.Locked => "Locked: buy a linked node first.",
                SkillTree.BuyResult.NotTopside => "Topside only: climb above the Surface Line.",
                SkillTree.BuyResult.Scrip => "Not enough Scrip.",
                SkillTree.BuyResult.Materials => "The pack lacks the materials.",
                SkillTree.BuyResult.Datacores => "Not enough Datacores.",
                _ => "",
            };
            if (buy != null) buy.interactable = r == SkillTree.BuyResult.Ok;
        }
    }
}
