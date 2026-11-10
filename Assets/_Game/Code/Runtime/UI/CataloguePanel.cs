using Meridian.Art;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Survey;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-054 Survey Catalogue (N), on the U-058 panel style: the planets with their completion on the left, the
    /// chosen planet's entries on the right (creatures, minerals, sites): scanned ones with icon, name and the
    /// Datacores they paid, unscanned ones as "?". The current planet opens first. No per-frame work while closed.
    /// </summary>
    public sealed class CataloguePanel : MonoBehaviour
    {
        public PlayerController player;
        public static bool AnyOpen { get; private set; }
        public bool IsOpen => root != null && root.activeSelf;
        /// <summary>U-124: true once the panel's paper drew, false when its key is absent (null while the probe runs).</summary>
        public bool? Paper { get; private set; }
        public PlanetId Shown { get; private set; } = PlanetId.Earth;

        /// <summary>Planet completion labels and the entry name labels (tests and captures read them).</summary>
        public readonly Dictionary<PlanetId, Text> Completion = new Dictionary<PlanetId, Text>();
        public readonly List<Text> EntryNames = new List<Text>();

        const int MaxEntries = 24, Cols = 3;
        GameObject root;
        Text header;
        InputAction toggle;
        readonly List<(Image icon, Text name, Text info)> cells = new List<(Image, Text, Text)>();
        readonly Dictionary<string, Sprite> creatureIcons = new Dictionary<string, Sprite>();
        readonly HashSet<string> creatureRequested = new HashSet<string>();
        readonly Dictionary<PlanetId, Button> planetButtons = new Dictionary<PlanetId, Button>();
        /// <summary>Unscanned entries: their icon as a dark silhouette (LEAD, U-054 review).</summary>
        static readonly Color Silhouette = new Color(0f, 0f, 0f, 0.7f);
        readonly List<AsyncOperationHandle<IList<Sprite>>> handles = new List<AsyncOperationHandle<IList<Sprite>>>();
        bool dirty;

        void Start()
        {
            Build();
            ItemIcons.Loaded += MarkDirty;
            if (player != null && player.actions != null)
            {
                toggle = player.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("Catalogue");
                if (toggle != null) toggle.performed += OnToggle;
            }
        }

        void OnDestroy()
        {
            PanelInput.Close(this); // U-134
            ItemIcons.Loaded -= MarkDirty;
            if (toggle != null) toggle.performed -= OnToggle;
            foreach (var h in handles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            if (IsOpen) AnyOpen = false;
        }

        void OnToggle(InputAction.CallbackContext _) => SetOpen(!IsOpen);
        void MarkDirty() => dirty = true;

        public void SetOpen(bool open)
        {
            if (root == null || root.activeSelf == open) return;
            root.SetActive(open);
            if (open) PanelInput.Open(this, toggle != null ? toggle.actionMap : null); else PanelInput.Close(this); // U-134: the surveyor stands still while a panel is open
            AnyOpen = open;
            enabled = open;
            if (open)
            {
                var here = FindAnyObjectByType<PlanetSideRoot>();
                if (here != null && here.Config != null) Shown = here.Config.id;
                Redraw();
                UiKit.SelectFirst(root.transform, planetButtons.TryGetValue(Shown, out var shownButton) ? shownButton : null); // U-124: keyboard reach, the arrows walk the planets
            }
            else ReleaseCreatureIcons();
        }

        /// <summary>
        /// U-060: a creature icon is the first frame of the species' whole sheet (color, normal, emission). Keeping
        /// every sheet ever shown held other planets' creatures in memory; closed, the panel lets them go.
        /// </summary>
        void ReleaseCreatureIcons()
        {
            foreach (var c in cells) if (c.icon != null) c.icon.sprite = null;
            foreach (var h in handles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            handles.Clear();
            creatureIcons.Clear();
            creatureRequested.Clear();
        }

        public void Show(PlanetId p) { Shown = p; Redraw(); }

        void Update() { if (toggle != null) PanelInput.Hold(toggle.actionMap); if (dirty) Redraw(); } // U-134: re-held each frame (a resume re-enables whole maps)

        void Build()
        {
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "CatalogueCanvas", 113);
            var back = UiKit.ModalPanel(canvas.transform, "Catalogue", new Vector2(1500f, 860f), out root);
            UiPaper.ApplyModal(back, Meridian.Art.ArtKeys.Ui.PanelScroll, ok => Paper = ok); // U-124 (B-151): the survey record on the parchment scroll (P-50); flat until the art is on disk
            var tl = new Vector2(0f, 1f);
            header = UiKit.Text(back.transform, "Header", tl, new Vector2(28f, -32f), new Vector2(1200f, 28f), 20, true, TextAnchor.MiddleLeft, theme.text);

            int row = 0;
            foreach (PlanetId p in System.Enum.GetValues(typeof(PlanetId)))
            {
                float y = -80f - row * 56f;
                var planet = p;
                planetButtons[p] = UiKit.ActionButton(back.transform, p.ToString().ToUpperInvariant(), tl, new Vector2(28f, y), new Vector2(200f, 44f), () => Show(planet));
                Completion[p] = UiKit.Text(back.transform, "Pct_" + p, tl, new Vector2(240f, y - 8f), new Vector2(80f, 28f), 16, true, TextAnchor.MiddleLeft, theme.label);
                row++;
            }

            for (int i = 0; i < MaxEntries; i++)
            {
                float x = 360f + (i % Cols) * 370f, y = -80f - (i / Cols) * 92f;
                var cell = UiKit.Rect(back.transform, "Entry" + i, tl, new Vector2(x, y), new Vector2(356f, 80f), tl).gameObject.AddComponent<Image>();
                cell.color = new Color(1f, 1f, 1f, 0.05f);
                var icon = UiKit.Panel(cell.transform, "Icon", tl, new Vector2(8f, -8f), new Vector2(64f, 64f), Color.white);
                icon.rectTransform.pivot = tl; icon.preserveAspect = true; icon.enabled = false;
                var name = UiKit.Text(cell.transform, "Name", tl, new Vector2(84f, -20f), new Vector2(260f, 24f), 16, true, TextAnchor.MiddleLeft, theme.text);
                var info = UiKit.Text(cell.transform, "Info", tl, new Vector2(84f, -50f), new Vector2(260f, 20f), 13, false, TextAnchor.MiddleLeft, theme.label);
                cells.Add((icon, name, info));
                EntryNames.Add(name);
            }
            root.SetActive(false);
            enabled = false;
        }

        /// <summary>An entry's icon: a mineral's item icon, a creature's first frame, a site's icons/catalogue/&lt;label&gt; (U-192, D-187:
        /// B-223's camp and B-233's ten). Null while it loads, and for a site whose icon is not exported (the slot stays empty).</summary>
        Sprite IconOf(CatalogueEntry e)
        {
            if (e.kind == EntryKind.Mineral) return ItemIcons.Get(e.itemId, FindAnyObjectByType<Meridian.Terrain.TerrainStreamer>());
            if (string.IsNullOrEmpty(e.artKey)) return null;
            if (creatureIcons.TryGetValue(e.artKey, out var sp)) return sp;
            if (creatureRequested.Add(e.artKey))
            {
                var key = e.artKey;
                if (e.kind == EntryKind.Site)
                {
                    // a key not exported yet is probed quietly (D-143): no error, the slot stays empty
                    var loc = Addressables.LoadResourceLocationsAsync(key);
                    loc.Completed += l =>
                    {
                        bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                        ArtLoad.Release(l);
                        if (exists && this != null) LoadIcon(key);
                    };
                }
                else LoadIcon(key);
            }
            return null;
        }

        void LoadIcon(string key)
        {
            var h = ArtLoad.Asset<IList<Sprite>>(key);
            handles.Add(h);
            h.Completed += op =>
            {
                if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                Sprite first = op.Result[0];
                foreach (var s in op.Result) if (s.name.EndsWith("_0")) first = s;
                creatureIcons[key] = first;
                dirty = true;
            };
        }

        /// <summary>The icon the cell of entry `id` shows now (null: none, or the entry is not on the shown planet); tests and captures.</summary>
        public Sprite IconShownFor(string id)
        {
            var list = Catalogue.For(Shown);
            for (int i = 0; i < list.Count && i < cells.Count; i++)
                if (list[i].id == id) return cells[i].icon.enabled ? cells[i].icon.sprite : null;
            return null;
        }

        void Redraw()
        {
            dirty = false;
            var state = GameState.Instance;
            if (root == null || state == null) return;
            header.text = $"SURVEY CATALOGUE  ·  {Shown.ToString().ToUpperInvariant()}        {state.datacores} DATACORES";
            foreach (var kv in Completion)
            {
                var list = Catalogue.For(kv.Key);
                kv.Value.text = list.Count == 0 ? "—" : $"{Mathf.RoundToInt(Catalogue.Completion(kv.Key, state.catalogue) * 100f)}%";
            }
            // Only the planet shown reads as selected; the rest stay clickable in a quiet fill (LEAD, U-054 review).
            foreach (var kv in planetButtons)
            {
                bool on = kv.Key == Shown;
                UiKit.SetCard(kv.Value.targetGraphic as Image, on ? UiKit.Card.Gold : UiKit.Card.Plain); // D-149 (U-136): the planet shown wears the gold band
            }
            var entries = Catalogue.For(Shown);
            for (int i = 0; i < cells.Count; i++)
            {
                var (icon, name, info) = cells[i];
                bool on = i < entries.Count;
                icon.transform.parent.gameObject.SetActive(on);
                if (!on) continue;
                var e = entries[i];
                bool known = state.catalogue.Contains(e.id);
                name.text = known ? e.name : "?";
                info.text = known ? $"{e.kind.ToString().ToUpperInvariant()}  ·  {e.Datacores} DC" : e.kind.ToString().ToUpperInvariant() + "  ·  not yet surveyed";
                name.color = UiKit.Letter(Paper, known); // D-149: ink on the paper
                // Scanned: the icon. Unscanned: the same icon as a dark silhouette — a shape to look for.
                var sp = IconOf(e);
                icon.sprite = sp;
                icon.enabled = sp != null;
                icon.color = known ? Color.white : Silhouette;
            }
        }
    }
}
