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
    /// U-175 (D-174, Bible 5.2 §8.1; B-204's ui/skilltree art and mock-up): the Skill Tree (K). Left, B-204's round chart with the hub, the six
    /// branch emblems and the 66 nodes at their ring radius on their branch's axis plus their angle (BLENDER's crossing-free layout, carried in
    /// SkillTree.json); links under the frames (bought: both ends bought; open: one; locked: neither), outward links straight, sideways links
    /// as arcs along their ring (never a chord across the chart); node frames by state (ring 5 the caps) with the node's icon at 40 px (0.4
    /// alpha while locked); the select ring on the chosen node. Right, the header ("Skill Tree", the Scrip held, the Surveyor Rank) and the
    /// chosen node's card on the kit's inventory paper: its frame and icon, name, branch and ring, effect, "needs:" its links, the cost on the
    /// cost tag (owned / needed), BUY greyed with the reason when it can't be bought. Buying is topside only. No per-frame work while closed.
    /// U-178 (D-175, D1_TABLES §7, B-206 / B-214): the header shows the Rank's insignia (96 px) and the expedition's badge with its numeral;
    /// at Rank 10, topside, NEW EXPEDITION opens a plain confirmation on B-206's certificate (what is wiped, what is kept, the new
    /// multiplier; no system dialog); CONFIRM presses B-214's seal, begins the next expedition (Expedition.Begin) and returns to Earth's camp.
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
        public Text Header { get; private set; }
        public Text Title { get; private set; }
        public Text Effect { get; private set; }
        public Text Needs { get; private set; }
        public Text CostText { get; private set; }
        public Text Status { get; private set; }
        public Button Buy => buy;
        /// <summary>U-178: NEW EXPEDITION (shown at Rank 10, topside), the confirmation and its text, and the seal pressing.</summary>
        public Button NewExpedition => newExpedition;
        public bool Confirming => confirmRoot != null && confirmRoot.activeSelf;
        public Text CertificateText => certBody;
        public Text CertificateTitle => certTitle;
        public Button ConfirmButton => confirm;
        public bool Sealing { get; private set; }
        public Image Insignia => insignia;
        public Image Badge => badge;
        public Text BadgeNumeral => badgeNumeral;

        // chart.json (B-204): ring radii and branch axes at the chart's 960 px; drawn here at ChartPx.
        static readonly Dictionary<int, float> RingPx = new Dictionary<int, float> { { 1, 140f }, { 2, 210f }, { 3, 285f }, { 4, 355f }, { 5, 420f } };
        static readonly Dictionary<string, float> AxisDeg = new Dictionary<string, float>
        { { "dig", -90f }, { "haul", -30f }, { "ascent", 30f }, { "survey", 90f }, { "endurance", 150f }, { "voyage", 210f } };
        const float ChartPx = 900f, EmblemPx = 408f, NodePx = 64f, CapPx = 72f, IconPx = 40f, SelectPx = 96f, ArcStepDeg = 2.5f;
        public const float K = ChartPx / 960f;
        public static readonly Vector2 ChartCentre = new Vector2(-330f, 0f);
        static readonly Color Brown = new Color(0.42f, 0.27f, 0.16f, 1f);
        const float ColX = 485f, ColW = 630f; // the right column's centre and width

        GameObject root;
        InputAction toggle;
        Button buy;
        Button newExpedition, confirm, cancel;
        GameObject confirmRoot;
        Image insignia, badge, certificate, certBadge, seal;
        Text badgeNumeral, certTitle, certBody, certBadgeNumeral;
        Sprite[] sealFrames;
        AsyncOperationHandle<IList<Sprite>> sealHandle;
        Image chart, hub, select, card, cardFrame, cardIcon, costTag;
        Text sub;
        readonly Dictionary<string, Image> icons = new Dictionary<string, Image>();
        readonly List<(List<Image> parts, string a, string b)> links = new List<(List<Image>, string, string)>();
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
            if (sealHandle.IsValid()) ArtLoad.Release(sealHandle);
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
            if (!open && !Sealing && confirmRoot != null) confirmRoot.SetActive(false);
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

        // ---------- geometry (static: SkillTreeTests checks it has no crossings) ----------

        static Vector2 Polar(float radiusPx, float screenDeg)
        {
            float a = screenDeg * Mathf.Deg2Rad;
            return ChartCentre + new Vector2(Mathf.Cos(a), -Mathf.Sin(a)) * radiusPx * K; // screen degrees, y down → UI y up
        }

        static float Degrees(SkillTree.Node n) => (AxisDeg.TryGetValue(n.branch, out var ax) ? ax : 0f) + n.angle;
        static float Radius(SkillTree.Node n) => RingPx.TryGetValue(n.ring, out var r) ? r : 140f;

        /// <summary>A node's centre on the panel (canvas units from the panel's centre).</summary>
        public static Vector2 NodePosition(SkillTree.Node n) => Polar(Radius(n), Degrees(n));

        /// <summary>A link's path on the panel: ring 1 to the hub and the outward links straight; a sideways link an arc along its ring
        /// (radius and angle eased from one end to the other the short way round), so it never cuts across the chart.</summary>
        public static List<Vector2> LinkPath(SkillTree.Node a, SkillTree.Node b)
        {
            var path = new List<Vector2>();
            if (b == null) { path.Add(NodePosition(a)); path.Add(ChartCentre); return path; }
            bool sideways = a.sideways == b.id || b.sideways == a.id;
            if (!sideways) { path.Add(NodePosition(a)); path.Add(NodePosition(b)); return path; }
            float da = Degrees(a), d = Mathf.DeltaAngle(da, Degrees(b)), ra = Radius(a), rb = Radius(b);
            int steps = Mathf.Max(2, Mathf.CeilToInt(Mathf.Abs(d) / ArcStepDeg));
            for (int i = 0; i <= steps; i++)
            {
                float t = i / (float)steps;
                path.Add(Polar(Mathf.Lerp(ra, rb, t), da + d * t));
            }
            return path;
        }

        /// <summary>Every link once: (node, linked node or null for the hub).</summary>
        public static List<(SkillTree.Node a, SkillTree.Node b)> AllLinks()
        {
            var tree = SkillTree.Current;
            var list = new List<(SkillTree.Node, SkillTree.Node)>();
            var seen = new HashSet<string>();
            foreach (var n in tree.nodes)
            {
                if (n.requires.Length == 0) list.Add((n, null));
                foreach (var r in n.requires)
                {
                    var o = tree.Get(r);
                    if (o == null) continue;
                    string pair = string.CompareOrdinal(n.id, r) < 0 ? n.id + "|" + r : r + "|" + n.id;
                    if (seen.Add(pair)) list.Add((n, o));
                }
            }
            return list;
        }

        // ---------- build ----------

        void Build()
        {
            var canvas = UiKit.Canvas(transform, "SkillTreeCanvas", 115);
            var back = UiKit.ModalPanel(canvas.transform, "SkillTree", new Vector2(1640f, 980f), out root);
            UiPaper.ApplyModal(back, "ui/skilltree/panel", _ => { if (IsOpen) Redraw(); }); // B-204's chart paper (LEAD 22:1x); the paper inks every text: the browns again
            var tree = SkillTree.Current;
            var bt = back.transform;

            chart = Img(bt, "Chart", ChartCentre, new Vector2(ChartPx, ChartPx), Color.white);
            foreach (var (a, b) in AllLinks()) AddLink(bt, a, b);
            hub = Img(bt, "Hub", ChartCentre, new Vector2(112f, 112f) * K, Color.white);
            foreach (var b in SkillTree.Branches)
                emblems.Add((Img(bt, "Emblem_" + b, Polar(EmblemPx, AxisDeg[b]), new Vector2(96f, 96f) * K, Color.white), "ui/skilltree/emblem_" + b));
            foreach (var n in tree.nodes)
            {
                var id = n.id;
                float px = n.ring == 5 ? CapPx : NodePx;
                var frame = Img(bt, "Node_" + id, NodePosition(n), new Vector2(px, px) * K, Color.white);
                var button = frame.gameObject.AddComponent<Button>();
                button.onClick.AddListener(() => Select(id));
                var icon = Img(frame.transform, "Icon", Vector2.zero, new Vector2(IconPx, IconPx) * K, Color.white);
                icon.raycastTarget = false;
                Frames[id] = frame; icons[id] = icon;
            }
            select = Img(bt, "Select", ChartCentre, new Vector2(SelectPx, SelectPx) * K, Color.clear);
            select.raycastTarget = false;

            // The header (B-204's mock-up): the title in Limelight, the purse and the Rank.
            var c = new Vector2(0.5f, 0.5f);
            var title = UiKit.Text(bt, "Header_Title", c, new Vector2(ColX, 410f), new Vector2(ColW, 90f), 64, false, TextAnchor.MiddleLeft, UiKit.Ink);
            title.font = UiTheme.Active.TitleFace;
            title.text = "Skill Tree";
            Header = UiKit.Text(bt, "Header_Purse", c, new Vector2(ColX, 340f), new Vector2(ColW, 40f), 28, false, TextAnchor.MiddleLeft, UiKit.Ink);
            // U-188 (BLENDER's 0.6.0 smoke read: "×1.00" ran into the panel's border): one line, shrinking to fit the column
            Header.horizontalOverflow = HorizontalWrapMode.Wrap; Header.verticalOverflow = VerticalWrapMode.Truncate;
            Header.resizeTextForBestFit = true; Header.resizeTextMinSize = 18; Header.resizeTextMaxSize = 28;

            // The node card on the kit's inventory paper (texts are its children: the paper keeps their colours).
            card = Img(bt, "Card", new Vector2(ColX, 95f), new Vector2(ColW, 400f), UiKit.Cream);
            UiPaper.Apply(card, ArtKeys.Ui.PanelInventory, _ => { if (IsOpen) Redraw(); });
            var ct = card.transform;
            cardFrame = Img(ct, "CardFrame", new Vector2(-220f, 110f), new Vector2(84f, 84f), Color.white);
            cardFrame.raycastTarget = false;
            cardIcon = Img(cardFrame.transform, "CardIcon", Vector2.zero, new Vector2(52f, 52f), Color.white);
            cardIcon.raycastTarget = false;
            Title = UiKit.Text(ct, "Name", c, new Vector2(60f, 128f), new Vector2(460f, 46f), 34, true, TextAnchor.MiddleLeft, UiKit.Ink);
            sub = UiKit.Text(ct, "Branch", c, new Vector2(60f, 88f), new Vector2(460f, 30f), 21, false, TextAnchor.MiddleLeft, Brown);
            Effect = UiKit.Text(ct, "Effect", c, new Vector2(0f, 22f), new Vector2(534f, 64f), 25, false, TextAnchor.UpperLeft, UiKit.Ink);
            Needs = UiKit.Text(ct, "Needs", c, new Vector2(0f, -42f), new Vector2(534f, 56f), 21, false, TextAnchor.UpperLeft, Brown);
            // U-204 F19: both wrap inside the card's width and step their size down before they would leave their boxes (LayoutCardText
            // sets the boxes for the selected node); the sizes are the handwritten face's, as UiKit.Text scaled them.
            Effect.horizontalOverflow = HorizontalWrapMode.Wrap; Effect.verticalOverflow = VerticalWrapMode.Truncate;
            Effect.resizeTextForBestFit = true; Effect.resizeTextMaxSize = Effect.fontSize; Effect.resizeTextMinSize = Mathf.RoundToInt(Effect.fontSize * 0.6f);
            Needs.horizontalOverflow = HorizontalWrapMode.Wrap; Needs.verticalOverflow = VerticalWrapMode.Truncate;
            Needs.resizeTextForBestFit = true; Needs.resizeTextMaxSize = Needs.fontSize; Needs.resizeTextMinSize = Mathf.RoundToInt(Needs.fontSize * 0.6f);
            costTag = Img(ct, "CostTag", new Vector2(0f, -122f), new Vector2(534f, 60f), UiKit.Cream);
            costTag.raycastTarget = false;
            UiPaper.Apply(costTag, "ui/skilltree/cost_tag", _ => { if (IsOpen) Redraw(); });
            CostText = UiKit.Text(costTag.transform, "Cost", c, new Vector2(24f, 0f), new Vector2(446f, 46f), 22, false, TextAnchor.MiddleLeft, UiKit.Ink);
            CostText.resizeTextForBestFit = true; CostText.resizeTextMinSize = 14; CostText.resizeTextMaxSize = 22;

            buy = UiKit.ActionButton(bt, "BUY", c, new Vector2(ColX - ColW * 0.5f + 120f, -170f), new Vector2(240f, 56f), () => BuySelected());
            Status = UiKit.Text(bt, "Status", c, new Vector2(ColX + 135f, -170f), new Vector2(360f, 56f), 22, false, TextAnchor.MiddleLeft, Brown);

            // U-178 (B-206): the Rank's insignia and the expedition's badge at the header's right; NEW EXPEDITION under BUY at Rank 10, topside.
            insignia = Img(bt, "RankInsignia", new Vector2(ColX + ColW * 0.5f - 56f, 396f), new Vector2(96f, 96f), Color.clear);
            insignia.raycastTarget = false;
            badge = Img(bt, "ExpeditionBadge", new Vector2(ColX + ColW * 0.5f - 158f, 396f), new Vector2(84f, 96f), Color.clear);
            badge.raycastTarget = false;
            badgeNumeral = Numeral(badge.transform, 0.75f);
            newExpedition = UiKit.ActionButton(bt, "NEW EXPEDITION", c, new Vector2(ColX - ColW * 0.5f + 170f, -250f), new Vector2(340f, 56f), () => ShowConfirm(true));
            newExpedition.gameObject.SetActive(false);

            // The confirmation: B-206's certificate (B-208's paper) over the right column, in plain words; CONFIRM / CANCEL; B-214's seal.
            certificate = Img(bt, "Certificate", new Vector2(ColX, 0f), CertSize, UiKit.Cream); // covers the header and the card
            UiPaper.Apply(certificate, "ui/rank/certificate", _ => { if (IsOpen) Redraw(); });
            confirmRoot = certificate.gameObject;
            var cc = certificate.transform;
            float hw = CertSize.x * 0.5f, hh = CertSize.y * 0.5f;
            certTitle = UiKit.Text(cc, "CertTitle", c, new Vector2(0f, hh - 100f), new Vector2(CertSize.x - 100f, 64f), 44, false, TextAnchor.MiddleCenter, UiKit.Ink);
            certTitle.font = UiTheme.Active.TitleFace;
            certBadge = Img(cc, "CertBadge", new Vector2(0f, hh - 210f), new Vector2(112f, 128f), Color.clear);
            certBadge.raycastTarget = false;
            certBadgeNumeral = Numeral(certBadge.transform, 1f);
            certBody = UiKit.Text(cc, "CertBody", c, new Vector2(0f, -40f), new Vector2(CertSize.x - 110f, 420f), 23, false, TextAnchor.UpperLeft, UiKit.Ink);
            certBody.horizontalOverflow = HorizontalWrapMode.Wrap;
            certBody.verticalOverflow = VerticalWrapMode.Truncate;
            confirm = UiKit.ActionButton(cc, "CONFIRM", c, new Vector2(-170f, -hh + 110f), new Vector2(220f, 56f), () => Confirm());
            cancel = UiKit.ActionButton(cc, "CANCEL", c, new Vector2(40f, -hh + 110f), new Vector2(180f, 56f), () => ShowConfirm(false));
            seal = Img(cc, "Seal", Vector2.zero, new Vector2(160f, 192f), Color.white);
            seal.rectTransform.pivot = new Vector2(0.5f, SealPivotY);
            seal.rectTransform.anchoredPosition = new Vector2(hw - SealFromEdge, -hh + SealFromEdge); // B-214: 58 px in from the right and bottom
            seal.raycastTarget = false;
            seal.enabled = false;
            confirmRoot.SetActive(false);
            Selected = tree.nodes.Length > 0 ? tree.nodes[0].id : null;
            root.SetActive(false);
            enabled = false;
        }

        /// <summary>B-214's seal: its pivot (on the seal) and its distance in from the certificate's right and bottom edges.</summary>
        public const float SealPivotY = 0.3542f, SealFromEdge = 58f;
        /// <summary>The certificate over the right column (it covers the header and the card while it is up).</summary>
        static readonly Vector2 CertSize = new Vector2(640f, 920f);

        /// <summary>The badge's numeral in Limelight ink, centred in B-206's numeral_rect [28, 30, 56, 40] (top-left px of the 112 × 128 badge).</summary>
        static Text Numeral(Transform badgeTransform, float scale)
        {
            var t = UiKit.Text(badgeTransform, "Numeral", new Vector2(0.5f, 0.5f), new Vector2(0f, (64f - 50f) * scale), new Vector2(56f, 40f) * scale,
                Mathf.RoundToInt(30f * scale), false, TextAnchor.MiddleCenter, UiKit.Ink);
            t.font = UiTheme.Active.TitleFace;
            t.raycastTarget = false;
            var o = t.GetComponent<Outline>(); if (o != null) o.enabled = false;
            return t;
        }

        /// <summary>U-178: opens (or closes) the New Expedition confirmation, its words filled from the state.</summary>
        public void ShowConfirm(bool on)
        {
            if (confirmRoot == null || Sealing) return;
            var s = GameState.Instance;
            if (on && !Expedition.CanBegin(s, Topside)) on = false;
            confirmRoot.SetActive(on);
            if (!on) { Redraw(); return; }
            int n = Mathf.Max(1, s.expedition), next = n + 1;
            certTitle.text = "A New Expedition";
            certBody.text = ConfirmationText(n);
            certBadge.sprite = Art(Expedition.BadgeKey(next)); certBadge.color = certBadge.sprite != null ? Color.white : Color.clear;
            certBadgeNumeral.text = Expedition.Roman(next);
            certTitle.color = certBody.color = certBadgeNumeral.color = UiKit.Ink;
            UiKit.SelectFirst(confirmRoot.transform, cancel);
        }

        /// <summary>The confirmation's words for leaving expedition n: what is wiped, what is kept, the new multiplier (pure; tests read it).</summary>
        public static string ConfirmationText(int n)
        {
            int next = n + 1;
            var sb = new System.Text.StringBuilder();
            sb.Append("Expedition ").Append(Expedition.Roman(n)).Append(" ends. Expedition ").Append(Expedition.Roman(next)).Append(" begins at Earth's camp.\n\n");
            sb.Append("Wiped: ").Append(string.Join(", ", Expedition.Wiped)).Append(".\n\n");
            sb.Append("Kept: ").Append(string.Join(", ", Expedition.Kept)).Append(".\n\n");
            sb.Append("Every Skill Tree stat ×").Append(Expedition.Multiplier(next).ToString("0.00", System.Globalization.CultureInfo.InvariantCulture))
              .Append(" (now ×").Append(Expedition.Multiplier(n).ToString("0.00", System.Globalization.CultureInfo.InvariantCulture)).Append(").");
            return sb.ToString();
        }

        /// <summary>U-178: CONFIRM: B-214's seal presses (10 frames, 12 fps), then the next expedition begins and the surveyor goes to Earth's camp.</summary>
        public void Confirm()
        {
            if (Sealing || !Confirming) return;
            if (!Expedition.CanBegin(GameState.Instance, Topside)) { ShowConfirm(false); return; }
            StartCoroutine(SealAndBegin());
        }

        System.Collections.IEnumerator SealAndBegin()
        {
            Sealing = true;
            confirm.interactable = cancel.interactable = false;
            if (sealFrames != null && sealFrames.Length > 0)
            {
                seal.enabled = true;
                foreach (var f in sealFrames) { seal.sprite = f; yield return new WaitForSecondsRealtime(1f / UiFrames.Fps); }
                seal.enabled = false; // the certificate's baked seal matches the last frames (B-214)
            }
            bool began = Expedition.Begin(GameState.Instance, Topside);
            Sealing = false;
            confirm.interactable = cancel.interactable = true;
            confirmRoot.SetActive(false);
            SetOpen(false);
            if (began)
            {
                var director = FindAnyObjectByType<SceneDirector>();
                if (director != null) director.StartCoroutine(director.ReturnToEarthCamp());
            }
        }

        Image Img(Transform parent, string name, Vector2 pos, Vector2 size, Color color)
        {
            var img = UiKit.Panel(parent, name, new Vector2(0.5f, 0.5f), pos, size, color);
            img.rectTransform.pivot = new Vector2(0.5f, 0.5f);
            img.rectTransform.anchoredPosition = pos;
            return img;
        }

        void AddLink(Transform parent, SkillTree.Node a, SkillTree.Node b)
        {
            var path = LinkPath(a, b);
            var parts = new List<Image>(path.Count - 1);
            for (int i = 0; i + 1 < path.Count; i++)
            {
                var p = path[i]; var q = path[i + 1]; var d = q - p;
                // a hair longer than the step, so the arc's pieces meet without a gap
                var line = Img(parent, $"Link_{a.id}_{(b != null ? b.id : "hub")}_{i}", (p + q) * 0.5f, new Vector2(d.magnitude + (path.Count > 2 ? 2f : 0f), 16f * K), Color.white);
                line.rectTransform.localRotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
                line.raycastTarget = false;
                line.type = Image.Type.Tiled;
                parts.Add(line);
            }
            links.Add((parts, a.id, b?.id));
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
            for (int r = 1; r <= Expedition.MaxRank; r++) Want(Expedition.InsigniaKey(r));
            Want(Expedition.BadgeKey(1)); Want(Expedition.BadgeKey(11));
            if (!sealHandle.IsValid()) sealHandle = UiFrames.Load("fx/ui/expedition_seal", f => { if (this != null) sealFrames = f; });
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

        static string Num(int n) => n.ToString("#,0", System.Globalization.CultureInfo.InvariantCulture).Replace(',', ' ');

        /// <summary>The reason BUY is greyed (empty when it can be bought).</summary>
        public static string Reason(SkillTree.BuyResult r) => r switch
        {
            SkillTree.BuyResult.Ok => "",
            SkillTree.BuyResult.AlreadyBought => "Bought.",
            SkillTree.BuyResult.Locked => "Locked: buy a linked node first.",
            SkillTree.BuyResult.NotTopside => "Topside only: climb above the Surface Line.",
            SkillTree.BuyResult.Scrip => "Not enough Scrip.",
            SkillTree.BuyResult.Materials => "The pack lacks the materials.",
            SkillTree.BuyResult.Datacores => "Not enough Datacores.",
            _ => "",
        };

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
            }
            foreach (var (parts, a, b) in links)
            {
                bool ba = s.skillNodes.Contains(a), bb = b == null || s.skillNodes.Contains(b);
                string st = ba && bb ? "bought" : ba || bb ? "open" : "locked";
                var sprite = Art("ui/skilltree/link_" + st);
                var col = sprite != null ? Color.white : st == "bought" ? UiKit.Gold : st == "open" ? UiKit.Ink : UiKit.InkFaded;
                foreach (var line in parts) { line.sprite = sprite; line.color = col; }
            }

            // U-178: the Rank (and the Scrip earned the next one needs), the expedition and its multiplier
            int rank = Expedition.Rank(s), nextAt = Expedition.NextRankScrip(s), expN = Mathf.Max(1, s.expedition);
            Header.text = nextAt > 0
                ? $"Scrip {Num(s.scrip)}  ·  Rank {rank} (next at {Num(nextAt)} earned)  ·  ×{Expedition.Multiplier(expN):0.00}"
                : $"Scrip {Num(s.scrip)}  ·  Rank {rank}  ·  ×{Expedition.Multiplier(expN):0.00}";
            Header.color = UiKit.Ink;
            insignia.sprite = Art(Expedition.InsigniaKey(rank)); insignia.color = insignia.sprite != null ? Color.white : Color.clear;
            badge.sprite = Art(Expedition.BadgeKey(expN)); badge.color = badge.sprite != null ? Color.white : Color.clear;
            badgeNumeral.text = Expedition.Roman(expN); badgeNumeral.color = UiKit.Ink;
            bool offer = Expedition.CanBegin(s, Topside);
            if (newExpedition.gameObject.activeSelf != offer) newExpedition.gameObject.SetActive(offer);
            var sel = tree.Get(Selected);
            select.sprite = Art("ui/skilltree/select");
            select.color = sel != null && select.sprite != null ? Color.white : Color.clear;
            if (sel == null) return;
            select.rectTransform.anchoredPosition = NodePosition(sel);

            string selState = StateOf(sel.id);
            cardFrame.sprite = Art($"ui/skilltree/node_{(sel.ring == 5 ? "cap_" : "")}{selState}");
            cardFrame.color = cardFrame.sprite != null ? Color.white : UiKit.Cream;
            cardIcon.sprite = Art("icons/nodes/" + sel.id);
            cardIcon.enabled = cardIcon.sprite != null;
            cardIcon.color = new Color(1f, 1f, 1f, selState == "locked" ? 0.4f : 1f);
            Title.text = string.IsNullOrEmpty(sel.name) ? sel.id : sel.name;
            sub.text = $"{char.ToUpperInvariant(sel.branch[0])}{sel.branch.Substring(1)}  ·  ring {sel.ring}";
            Effect.text = sel.effect;
            sub.color = Brown; Needs.color = Brown; // the paper's InkTexts set every card text to ink

            var needs = new System.Text.StringBuilder("needs: ");
            if (sel.requires.Length == 0) needs.Append("the centre");
            for (int i = 0; i < sel.requires.Length; i++)
            {
                var o = tree.Get(sel.requires[i]);
                if (i > 0) needs.Append(" or ");
                needs.Append(o != null && !string.IsNullOrEmpty(o.name) ? o.name : sel.requires[i]);
                if (s.skillNodes.Contains(sel.requires[i])) needs.Append(" (bought)");
            }
            Needs.text = needs.ToString();
            LayoutCardText();

            // The cost, owned / needed: Scrip, then each material from the pack, then Datacores.
            var cost = new System.Text.StringBuilder();
            cost.Append("Scrip ").Append(Num(s.scrip)).Append(" / ").Append(Num(sel.scrip));
            foreach (var c in sel.items)
            {
                var def = ItemRegistry.Get(c.item);
                cost.Append("   ·   ").Append(def != null ? def.name : c.item).Append(' ').Append(def != null ? s.inventory.Count(def.id) : 0).Append(" / ").Append(c.count);
            }
            if (sel.datacores > 0) cost.Append("   ·   Datacores ").Append(s.datacores).Append(" / ").Append(sel.datacores);
            CostText.text = cost.ToString();

            var r = tree.CanBuy(s, sel.id, Topside);
            Status.text = r == SkillTree.BuyResult.Ok ? "Ready to buy." : Reason(r);
            Status.color = Brown;
            if (buy != null) buy.interactable = r == SkillTree.BuyResult.Ok;
        }

        /// <summary>The card's text column, from the card's centre: the description's top, the cost tag's top, the room a description
        /// may take (two lines of its type), the gap under a one-line description (as built) and the least room the needs line keeps.</summary>
        public const float EffectTop = 54f, CostTagTop = -92f, EffectMaxH = 92f, NeedsGap = 22f, NeedsMinH = 44f, CardTextW = 534f;

        /// <summary>U-204 F19 (B-228's read of smoke_60: The Beam's description ran past the card's right border and off the screen): the
        /// description wraps inside the card, up to two lines at its full size (a longer one steps its size down, never cut off); the
        /// needs line sits under its last line (where it was for a one-line description) and above the cost tag.</summary>
        void LayoutCardText()
        {
            float effectH = Mathf.Clamp(Effect.preferredHeight, 1f, EffectMaxH); // its box's width wraps it
            Effect.rectTransform.sizeDelta = new Vector2(CardTextW, EffectMaxH);
            Effect.rectTransform.anchoredPosition = new Vector2(0f, EffectTop - EffectMaxH * 0.5f);
            float needsTop = Mathf.Max(EffectTop - effectH - NeedsGap, CostTagTop + 2f + NeedsMinH);
            float needsH = needsTop - (CostTagTop + 2f);
            Needs.rectTransform.sizeDelta = new Vector2(CardTextW, needsH);
            Needs.rectTransform.anchoredPosition = new Vector2(0f, needsTop - needsH * 0.5f);
        }
    }
}
