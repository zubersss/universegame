using System.Collections.Generic;
using Meridian.Art;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Trade;
using Meridian.UI;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.UI;

namespace Meridian.Space
{
    /// <summary>
    /// U-184 (D-178, the owner's USER-34; B-209's ui/map art): the maps of the top-down view.
    /// (1) The minimap: B-209's brass porthole in the top-right corner, north-up, centred on the ship: the Sun and the planets (and the
    /// Moon) as their map discs with name tags, faint dotted orbits, dashed Gravity Wells, the Waystations, a landed tick, the ship's arrow
    /// turned to its heading. Its range fits the nearest planets and widens with speed; a body beyond the rim shows as a rim arrow with its
    /// distance. Hidden while a climb / entry transition runs and while a menu is up.
    /// (2) M opens the system map (M or Esc closes it; nothing pauses): one paper chart, the whole system at one linear scale on the right
    /// and the inner planets (Mercury to Mars, where the linear scale would stack them on the Sun) in an inset at their own linear scale
    /// on the left; the same marks, the planets landed on ticked, the ship where it is.
    /// Marks sit at their true positions on their chart's scale (SpaceMapTests); a Gravity Well never draws smaller than its planet's disc
    /// plus a margin, so it reads round the mark. Per frame: positions only (the marks are built once; distance labels change only when
    /// their tenth of a thousand units does).
    /// </summary>
    public sealed class SpaceMap : MonoBehaviour
    {
        public SpaceShip ship;

        // The minimap (B-209: the frame 256 px, its clear centre r < 99 px, the paper chart 208 px).
        public const float FramePx = 256f, ClearPx = 99f, ChartPx = 208f, Margin = 24f, RimPx = 89f, InsideMargin = 4f, WellMargin = 6f;
        public const float MinRange = 500f, FitRange = 3000f, MaxRange = 6000f, LookAheadSeconds = 5f, FitFactor = 1.15f, ZoomRate = 2.5f;
        static readonly float[] RimTagPx = { 74f, 52f };
        static readonly float[] TagSlides = { 0f, 14f, -14f, 28f, -28f, 42f, -42f };
        /// <summary>How many of the off-edge bodies (the nearest) carry a distance tag beside their rim arrow.</summary>
        public const int RimTags = 3;
        /// <summary>An off-edge body within this many degrees of a nearer one's arrow shares that arrow (no pile of arrows).</summary>
        public const float RimClusterDeg = 10f;
        readonly List<float> rimBearings = new List<float>(12);

        // The system map: the paper 1760 x 980; the inset (the inner planets) on the left, the whole system on the right.
        public static readonly Vector2 PanelSize = new Vector2(1760f, 980f);
        public static readonly Vector2 InsetCentre = new Vector2(-470f, -40f), FullCentre = new Vector2(400f, -40f);
        public const float InsetRadiusPx = 320f, FullRadiusPx = 350f, InnerRange = 2900f, OuterRange = 16000f;
        public static float InsetScale => InsetRadiusPx / InnerRange;
        public static float FullScale => FullRadiusPx / OuterRange;

        public RectTransform Minimap { get; private set; }
        public bool MinimapShown => Minimap != null && Minimap.gameObject.activeInHierarchy;
        /// <summary>World units from the ship to the porthole's clear edge.</summary>
        public float Range { get; private set; } = 700f;
        /// <summary>Canvas px per world unit on the minimap.</summary>
        public float Scale => ClearPx / Range;
        public RectTransform ShipArrow { get; private set; }
        public bool SystemOpen => systemRoot != null && systemRoot.activeSelf;
        public RectTransform SystemShip { get; private set; }
        public bool Built { get; private set; }
        public MapLines MiniOrbits { get; private set; }
        public MapLines MiniWells { get; private set; }

        /// <summary>A body's marks on the minimap.</summary>
        public sealed class Mark
        {
            public string name, label;
            public BodyInfo body;
            public bool moon;
            public Vector2 size;
            public RectTransform disc, tag, tick, rim, rimTag;
            public Text rimLabel;
            public int rimTenths = -1;
            public float dist2;
            public Vector2 tagOffset, rimTagSize;
        }

        /// <summary>A body's or station's mark on the system map (its chart is the inset or the whole system).</summary>
        public sealed class SystemMark
        {
            public string name;
            public Vector2 world;
            public bool inset;
            public RectTransform disc, tag, tick, leader;
            /// <summary>The tag sits off its usual place (under the disc), joined to the disc by its leader line.</summary>
            public bool moved;
        }

        public readonly List<Mark> Marks = new List<Mark>();
        public readonly List<SystemMark> SystemMarks = new List<SystemMark>();
        public readonly List<(Waystation station, RectTransform mark, RectTransform tag)> Stations = new List<(Waystation, RectTransform, RectTransform)>();

        static readonly Dictionary<string, string> Names = new Dictionary<string, string>
        {
            { "sun", "Sun" }, { "mercury", "Mercury" }, { "venus", "Venus" }, { "earth", "Earth" }, { "mars", "Mars" }, { "jupiter", "Jupiter" },
            { "saturn", "Saturn" }, { "uranus", "Uranus" }, { "neptune", "Neptune" }, { "luna", "Moon" },
        };

        static SpaceMap openMap;
        Transitions.TransitionDirector director;
        InputAction systemKey;
        GameObject systemRoot;
        RectTransform insetChart, fullChart;
        Image miniChart, frame, systemPaper, cartouche;
        Text cartoucheFallback;
        MapLines insetOrbits, insetWells, fullOrbits, fullWells;
        bool rangeSet;
        readonly List<(Graphic target, string key, bool sliced)> wanted = new List<(Graphic, string, bool)>();
        readonly Dictionary<string, Sprite> art = new Dictionary<string, Sprite>();
        readonly List<AsyncOperationHandle<IList<Sprite>>> handles = new List<AsyncOperationHandle<IList<Sprite>>>();
        readonly List<Rect> placedTags = new List<Rect>(12);
        readonly List<Mark> rimOrder = new List<Mark>(12);
        float directorSearchAt;

        // ---------- the pure maths (SpaceMapTests) ----------

        /// <summary>The minimap's target range: the second-nearest planet's distance (so the nearest two fit), clamped, plus the ground the
        /// ship covers in LookAheadSeconds at its speed; never past MaxRange.</summary>
        public static float TargetRange(IReadOnlyList<BodyInfo> bodies, Vector2 at, float speed)
        {
            float d1 = float.PositiveInfinity, d2 = float.PositiveInfinity;
            for (int i = 0; i < bodies.Count; i++)
            {
                var b = bodies[i];
                if (b.isSun || b.parent != null) continue;
                float d = Vector2.Distance(b.position, at);
                if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) d2 = d;
            }
            float fit = float.IsPositiveInfinity(d2) ? MinRange : Mathf.Clamp(d2 * FitFactor, MinRange, FitRange);
            return Mathf.Min(MaxRange, fit + Mathf.Max(0f, speed) * LookAheadSeconds);
        }

        /// <summary>A world point on the minimap (canvas px from its centre; north up).</summary>
        public static Vector2 MiniPosition(Vector2 world, Vector2 ship, float scale) => (world - ship) * scale;

        /// <summary>A world point on the system map (canvas px from the paper's centre): the inset inside InnerRange of the Sun, else the
        /// whole-system chart.</summary>
        public static Vector2 SystemPosition(Vector2 world, out bool inset)
        {
            inset = world.magnitude < InnerRange;
            return inset ? InsetCentre + world * InsetScale : FullCentre + world * FullScale;
        }

        /// <summary>Planets the player has landed on: Earth (home), the one they are on, an entry's "landed:" flag (U-184), a beacon's flag
        /// (saves from before U-184).</summary>
        public static bool Landed(GameState s, PlanetId p)
        {
            if (p == PlanetId.Earth) return true;
            if (s == null) return false;
            if (s.currentPlanet == p) return true;
            string n = p.ToString().ToLowerInvariant();
            return s.HasFlag("landed:" + n) || s.HasFlag("beacon:" + n);
        }

        public static string LandedFlag(PlanetId p) => "landed:" + p.ToString().ToLowerInvariant();

        static bool OnMaps(BodyInfo b) => b.isSun || b.parent == null || b.name == "luna";
        static string Display(string name) => Names.TryGetValue(name, out var n) ? n : name;

        static Vector2 DiscSize(BodyInfo b) => b.isSun ? new Vector2(40f, 40f) : b.name == "saturn" ? new Vector2(56f, 32f) : b.name == "luna" ? new Vector2(20f, 20f) : new Vector2(32f, 32f);
        static string DiscKey(BodyInfo b) => b.isSun ? "ui/map/sun" : "ui/map/planet_" + b.name;

        /// <summary>Esc while the system map is open closes it (MenuController asks before opening the pause menu).</summary>
        public static bool CloseOnEscape()
        {
            if (openMap == null || !openMap.SystemOpen) return false;
            openMap.SetSystemOpen(false);
            return true;
        }

        // ---------- life ----------

        void Start() => HookKey();

        /// <summary>M (the ShipTop map's SystemMap). The ship's actions can arrive after this Start: hooked once they do.</summary>
        void HookKey()
        {
            if (systemKey != null || ship == null || ship.actions == null) return;
            var top = ship.actions.FindActionMap(MeridianInput.ShipTop, false);
            systemKey = top != null ? top.FindAction("SystemMap") : null;
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            if (openMap == this) openMap = null;
        }

        void OnDisable()
        {
            if (SystemOpen) SetSystemOpen(false); // the view switched away
        }

        public void SetSystemOpen(bool open)
        {
            if (systemRoot == null || systemRoot.activeSelf == open) return;
            systemRoot.SetActive(open);
            openMap = open ? this : (openMap == this ? null : openMap);
            if (open) UpdateSystem();
        }

        bool Hidden
        {
            get
            {
                if (director == null && Time.unscaledTime >= directorSearchAt)
                {
                    director = FindAnyObjectByType<Transitions.TransitionDirector>();
                    directorSearchAt = Time.unscaledTime + 1f;
                }
                return ship == null || ship.Destroyed || MenuController.HudHidden || (director != null && director.Busy);
            }
        }

        void LateUpdate()
        {
            if (systemKey == null) HookKey();
            if (!Built) { TryBuild(); if (!Built) return; }
            bool hidden = Hidden;
            if (Minimap.gameObject.activeSelf == hidden) Minimap.gameObject.SetActive(!hidden);
            if (hidden) { if (SystemOpen) SetSystemOpen(false); return; }
            if (systemKey != null && systemKey.WasPressedThisFrame()) SetSystemOpen(!SystemOpen); // M (polled, as the menus read Esc)
            UpdateMinimap(Time.unscaledDeltaTime);
            if (SystemOpen) UpdateSystemShip();
        }

        // ---------- build ----------

        /// <summary>Builds the maps and starts their art now: SceneDirector calls it at boot behind the boot cover (the Space scene just
        /// loaded, its world built), so the first frame in space has nothing to make (BudgetGate's space rows).</summary>
        public void Prepare()
        {
            HookKey();
            if (!Built) TryBuild();
            if (Built) Canvas.ForceUpdateCanvases(); // the marks' meshes too, while the view is up for its warm-up
        }

        void TryBuild()
        {
            if (ship == null || ship.world == null || !ship.world.Built || ship.world.Bodies.Count == 0) return;
            BuildMinimap();
            BuildSystemMap();
            LoadArt();
            Built = true;
        }

        Image Img(Transform parent, string name, Vector2 pos, Vector2 size, Color color, string key = null, bool sliced = false)
        {
            var img = UiKit.Panel(parent, name, new Vector2(0.5f, 0.5f), pos, size, color);
            img.rectTransform.pivot = new Vector2(0.5f, 0.5f);
            img.rectTransform.anchoredPosition = pos;
            img.raycastTarget = false;
            if (key != null) wanted.Add((img, key, sliced));
            return img;
        }

        MapLines Lines(Transform parent, string name, Vector2 pos, string key, float dashPx, float clip, float alpha)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = new Vector2(2f * clip, 2f * clip);
            rt.anchoredPosition = pos;
            var l = go.AddComponent<MapLines>();
            l.raycastTarget = false;
            l.dashPx = dashPx; l.thickPx = 8f; l.clipRadius = clip;
            l.color = new Color(1f, 1f, 1f, alpha);
            wanted.Add((l, key, false));
            return l;
        }

        /// <summary>A name tag (B-209's name_tag, lettered in Patrick Hand); returns it sized to its text.</summary>
        RectTransform Tag(Transform parent, string name, string text, int fontSize, out Text label)
        {
            var tag = Img(parent, name, Vector2.zero, new Vector2(64f, 22f), UiKit.Cream, "ui/map/name_tag", true);
            label = UiKit.Text(tag.transform, "Label", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(240f, 22f), fontSize, false, TextAnchor.MiddleCenter, UiKit.Ink);
            label.font = UiTheme.Active.HudFace;
            var rim = label.GetComponent<Outline>();
            if (rim != null) rim.enabled = false;
            label.raycastTarget = false;
            SetTag(tag.rectTransform, label, text);
            return tag.rectTransform;
        }

        static void SetTag(RectTransform tag, Text label, string text)
        {
            label.text = text;
            float w = Mathf.Ceil(label.preferredWidth) + 14f;
            tag.sizeDelta = new Vector2(w, 22f);
            label.rectTransform.sizeDelta = new Vector2(w, 22f);
        }

        void BuildMinimap()
        {
            var canvas = UiKit.Canvas(transform, "SpaceMapCanvas", 104);
            var go = new GameObject("Minimap", typeof(RectTransform));
            Minimap = (RectTransform)go.transform;
            Minimap.SetParent(canvas.transform, false);
            Minimap.anchorMin = Minimap.anchorMax = new Vector2(1f, 1f);
            Minimap.pivot = new Vector2(0.5f, 0.5f);
            Minimap.sizeDelta = new Vector2(FramePx, FramePx);
            Minimap.anchoredPosition = new Vector2(-Margin - FramePx * 0.5f, -Margin - FramePx * 0.5f);

            miniChart = Img(Minimap, "Chart", Vector2.zero, new Vector2(ChartPx, ChartPx), new Color(0.93f, 0.88f, 0.76f, 0.92f), "ui/map/minimap_chart");
            MiniOrbits = Lines(Minimap, "Orbits", Vector2.zero, "ui/map/orbit_dot", 16f, ClearPx, 0.6f);
            MiniWells = Lines(Minimap, "Wells", Vector2.zero, "ui/map/well_dash", 32f, ClearPx, 1f);
            foreach (var b in ship.world.Bodies)
            {
                if (!OnMaps(b)) continue;
                var m = new Mark { name = b.name, label = Display(b.name), body = b, moon = b.parent != null, size = DiscSize(b) };
                m.disc = Img(Minimap, "Disc_" + b.name, Vector2.zero, m.size, UiTheme.Accent(b.landable ? b.planet : (PlanetId?)null), DiscKey(b)).rectTransform;
                m.tag = Tag(Minimap, "Tag_" + b.name, m.label, 15, out _);
                m.tagOffset = m.moon ? new Vector2(m.size.x * 0.5f + m.tag.sizeDelta.x * 0.5f + 3f, 0f) : new Vector2(0f, -(m.size.y * 0.5f + 12f));
                if (b.landable) m.tick = Img(Minimap, "Landed_" + b.name, Vector2.zero, new Vector2(20f, 20f), Color.clear, "ui/map/landed").rectTransform;
                Marks.Add(m);
            }
            ShipArrow = Img(Minimap, "Ship", Vector2.zero, new Vector2(32f, 32f), new Color(0.85f, 0.25f, 0.2f, 1f), "ui/map/ship").rectTransform;
            frame = Img(Minimap, "Frame", Vector2.zero, new Vector2(FramePx, FramePx), Color.clear, "ui/map/minimap_frame");
            foreach (var m in Marks)
            {
                if (m.moon) continue;
                m.rim = Img(Minimap, "Rim_" + m.name, Vector2.zero, new Vector2(24f, 24f), UiKit.Gold, "ui/map/rim_arrow").rectTransform;
                m.rimTag = Tag(Minimap, "RimTag_" + m.name, m.label, 13, out m.rimLabel);
                m.rim.gameObject.SetActive(false); m.rimTag.gameObject.SetActive(false);
            }
        }

        void BuildSystemMap()
        {
            var canvas = UiKit.Canvas(transform, "SystemMapCanvas", 112);
            systemRoot = new GameObject("SystemMap", typeof(RectTransform));
            var root = (RectTransform)systemRoot.transform;
            root.SetParent(canvas.transform, false);
            root.anchorMin = root.anchorMax = root.pivot = new Vector2(0.5f, 0.5f);
            root.sizeDelta = PanelSize;
            systemPaper = Img(root, "Paper", Vector2.zero, PanelSize, UiKit.Cream, "ui/map/system_panel", true);
            cartouche = Img(root, "Cartouche", new Vector2(0f, PanelSize.y * 0.5f - 75f), new Vector2(384f, 80f), Color.clear, "ui/map/title_cartouche");
            cartoucheFallback = UiKit.Text(root, "Title", new Vector2(0.5f, 0.5f), new Vector2(0f, PanelSize.y * 0.5f - 75f), new Vector2(600f, 70f), 40, false, TextAnchor.MiddleCenter, UiKit.Ink);
            cartoucheFallback.font = UiTheme.Active.TitleFace;
            cartoucheFallback.text = "THE SOLAR SYSTEM";
            Caption(root, "InsetCaption", "The inner planets", InsetCentre + new Vector2(0f, InsetRadiusPx + 24f));
            Caption(root, "FullCaption", "The whole system", FullCentre + new Vector2(0f, FullRadiusPx + 24f));

            insetChart = Chart(root, "Inset", InsetCentre);
            fullChart = Chart(root, "Full", FullCentre);
            insetOrbits = Lines(insetChart, "Orbits", Vector2.zero, "ui/map/orbit_dot", 16f, InsetRadiusPx + 4f, 0.7f);
            insetWells = Lines(insetChart, "Wells", Vector2.zero, "ui/map/well_dash", 32f, InsetRadiusPx + 4f, 1f);
            fullOrbits = Lines(fullChart, "Orbits", Vector2.zero, "ui/map/orbit_dot", 16f, FullRadiusPx + 4f, 0.7f);
            fullWells = Lines(fullChart, "Wells", Vector2.zero, "ui/map/well_dash", 32f, FullRadiusPx + 4f, 1f);

            foreach (var b in ship.world.Bodies)
            {
                if (!OnMaps(b) || b.parent != null) continue; // LEAD 20:4x: the Moon only on the minimap
                bool inner = b.position.magnitude < InnerRange;
                if (!b.isSun && b.parent == null) { insetOrbits.Add(Vector2.zero, b.position.magnitude * InsetScale); fullOrbits.Add(Vector2.zero, b.position.magnitude * FullScale); }
                // The Sun goes on both charts; the rest on the one that holds them (the inner planets and the Moon in the inset).
                if (b.isSun || inner) AddSystemMark(b, true);
                if (b.isSun || !inner) AddSystemMark(b, false);
            }
            insetOrbits.Commit(); insetWells.Commit(); fullOrbits.Commit(); fullWells.Commit();
            PlaceSystemTags();
            SystemShip = Img(fullChart, "Ship", Vector2.zero, new Vector2(32f, 32f), new Color(0.85f, 0.25f, 0.2f, 1f), "ui/map/ship").rectTransform;
            insetShip = Img(insetChart, "Ship", Vector2.zero, new Vector2(32f, 32f), new Color(0.85f, 0.25f, 0.2f, 1f), "ui/map/ship").rectTransform;
            systemRoot.SetActive(false);
        }

        RectTransform insetShip;

        static RectTransform Chart(RectTransform root, string name, Vector2 centre)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var rt = (RectTransform)go.transform;
            rt.SetParent(root, false);
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = Vector2.zero;
            rt.anchoredPosition = centre;
            return rt;
        }

        static void Caption(RectTransform root, string name, string text, Vector2 pos)
        {
            var t = UiKit.Text(root, name, new Vector2(0.5f, 0.5f), pos, new Vector2(500f, 32f), 24, false, TextAnchor.MiddleCenter, UiKit.Ink);
            t.font = UiTheme.Active.HudFace;
            t.text = text;
        }

        void AddSystemMark(BodyInfo b, bool inset)
        {
            var chart = inset ? insetChart : fullChart;
            float scale = inset ? InsetScale : FullScale;
            var size = DiscSize(b);
            var p = b.position * scale;
            var wells = inset ? insetWells : fullWells;
            if (!b.isSun) wells.Add(p, Mathf.Max(b.WellRadius * scale, Mathf.Max(size.x, size.y) * 0.5f + WellMargin)); // LEAD 20:4x: wells for planets only
            var sm = new SystemMark { name = b.name, world = b.position, inset = inset };
            sm.disc = Img(chart, "Disc_" + b.name, p, size, UiTheme.Accent(b.landable ? b.planet : (PlanetId?)null), DiscKey(b)).rectTransform;
            bool moon = b.parent != null;
            sm.leader = Img(chart, "Leader_" + b.name, p, new Vector2(1f, 1.5f), UiKit.Ink).rectTransform; // under the tag: built first
            sm.leader.gameObject.SetActive(false);
            sm.tag = Tag(chart, "Tag_" + b.name, Display(b.name), 18, out _);
            sm.tag.anchoredPosition = moon ? p + new Vector2(size.x * 0.5f + sm.tag.sizeDelta.x * 0.5f + 3f, 0f) : p + new Vector2(0f, -(size.y * 0.5f + 13f));
            if (b.landable)
            {
                sm.tick = Img(chart, "Landed_" + b.name, p + new Vector2(size.x * 0.5f + 4f, -size.y * 0.5f + 4f), new Vector2(20f, 20f), Color.clear, "ui/map/landed").rectTransform;
                sm.tick.gameObject.SetActive(false);
            }
            SystemMarks.Add(sm);
        }

        /// <summary>The system map's tags, as the minimap's: each takes the first of its places round its disc (under it first) where it covers no
        /// disc, station mark, tick or tag already placed on its chart; a tag pushed off its first place gets a short ink leader to its disc.</summary>
        void PlaceSystemTags()
        {
            PlaceSystemTags(true);
            PlaceSystemTags(false);
        }

        void PlaceSystemTags(bool inset)
        {
            placedTags.Clear();
            foreach (var sm in SystemMarks)
            {
                if (sm.inset != inset) continue;
                if (sm.disc != null) placedTags.Add(new Rect(sm.disc.anchoredPosition - sm.disc.sizeDelta * 0.5f, sm.disc.sizeDelta));
                if (sm.tick != null && sm.tick.gameObject.activeSelf) placedTags.Add(new Rect(sm.tick.anchoredPosition - sm.tick.sizeDelta * 0.5f, sm.tick.sizeDelta));
            }
            foreach (var sm in SystemMarks)
            {
                if (sm.inset != inset || sm.tag == null) continue;
                Vector2 p = sm.disc.anchoredPosition, ds = sm.disc.sizeDelta, ts = sm.tag.sizeDelta;
                float below = ds.y * 0.5f + 13f, side = ds.x * 0.5f + ts.x * 0.5f + 5f;
                Vector2 best = p + new Vector2(0f, -below);
                bool moved = false;
                for (int i = 0; i < TagSpots.Length; i++)
                {
                    var o = TagSpots[i];
                    var c = p + new Vector2(o.x * side, o.y > 0f ? (below + (o.y - 1f) * 26f) : o.y < 0f ? -(below + (-o.y - 1f) * 26f) : 0f);
                    if (o.x != 0f && o.y != 0f) c.y = p.y + Mathf.Sign(o.y) * (ds.y * 0.5f + 4f + (Mathf.Abs(o.y) - 1f) * 26f);
                    var r = new Rect(c - ts * 0.5f, ts);
                    if (!Free(r)) continue;
                    best = c; moved = i > 0;
                    break;
                }
                sm.tag.anchoredPosition = best;
                placedTags.Add(new Rect(best - ts * 0.5f, ts));
                sm.moved = moved;
                Show(sm.leader, moved);
                if (!moved) continue;
                // the leader: from the disc's edge to the tag box's nearest point
                var box = new Rect(best - ts * 0.5f, ts);
                var near = new Vector2(Mathf.Clamp(p.x, box.xMin, box.xMax), Mathf.Clamp(p.y, box.yMin, box.yMax));
                var d = near - p;
                float len = d.magnitude - Mathf.Max(ds.x, ds.y) * 0.5f;
                if (len < 3f) { Show(sm.leader, false); continue; }
                var dir = d / d.magnitude;
                var from = p + dir * (Mathf.Max(ds.x, ds.y) * 0.5f);
                sm.leader.anchoredPosition = from + dir * (len * 0.5f);
                sm.leader.sizeDelta = new Vector2(len, 1.5f);
                sm.leader.localRotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg);
            }
        }

        /// <summary>A tag's places round its disc, in order: (x: −1 left / 0 centred / 1 right; y: −n the nth row under, +n the nth row over).</summary>
        static readonly Vector2[] TagSpots =
        {
            new Vector2(0f, -1f), new Vector2(0f, 1f), new Vector2(1f, 0f), new Vector2(-1f, 0f),
            new Vector2(1f, -1f), new Vector2(-1f, -1f), new Vector2(1f, 1f), new Vector2(-1f, 1f),
            new Vector2(0f, -2f), new Vector2(0f, 2f), new Vector2(0f, -3f), new Vector2(0f, 3f),
        };

        // ---------- art ----------

        void LoadArt()
        {
            var keys = new HashSet<string> { "ui/map/station", "ui/map/name_tag" }; // stations come later (the docking bay)
            foreach (var w in wanted) keys.Add(w.key);
            foreach (var key in keys)
            {
                string k = key;
                var loc = UnityEngine.AddressableAssets.Addressables.LoadResourceLocationsAsync(k);
                loc.Completed += l =>
                {
                    bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                    ArtLoad.Release(l);
                    if (!exists || this == null) return;
                    var h = ArtLoad.Asset<IList<Sprite>>(k);
                    handles.Add(h);
                    h.Completed += op =>
                    {
                        if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                        art[k] = op.Result[0];
                        Dress(k, op.Result[0]);
                    };
                };
            }
        }

        void Dress(string key, Sprite s)
        {
            foreach (var (target, k, sliced) in wanted)
            {
                if (k != key || target == null) continue;
                if (target is MapLines lines) { lines.Sprite = s; continue; }
                if (!(target is Image img)) continue;
                img.sprite = s;
                img.color = Color.white;
                if (sliced && s.border.sqrMagnitude > 0f)
                {
                    img.type = Image.Type.Sliced;
                    float refPpu = img.canvas != null ? img.canvas.referencePixelsPerUnit : 100f;
                    img.pixelsPerUnitMultiplier = s.pixelsPerUnit > 0f ? refPpu / s.pixelsPerUnit : 1f;
                    Meridian.UI.UiPaper.Grain(img, key); // U-181: B-208's grain over the flat paper
                }
            }
            if (key == "ui/map/title_cartouche" && cartoucheFallback != null) cartoucheFallback.gameObject.SetActive(false);
        }

        public bool HasArt(string key) => art.ContainsKey(key);

        // ---------- per frame ----------

        void UpdateMinimap(float dt)
        {
            var bodies = ship.world.Bodies;
            Vector2 at = ship.Position;
            float target = TargetRange(bodies, at, ship.Velocity.magnitude);
            Range = rangeSet ? Mathf.Lerp(Range, target, 1f - Mathf.Exp(-ZoomRate * dt)) : target;
            rangeSet = true;
            float k = Scale;
            var state = GameState.Instance;

            MiniOrbits.Clear(); MiniWells.Clear();
            var sun = MiniPosition(Vector2.zero, at, k);
            rimOrder.Clear();
            placedTags.Clear();
            placedTags.Add(new Rect(-16f, -16f, 32f, 32f)); // the ship's arrow
            foreach (var m in Marks)
            {
                var p = MiniPosition(m.body.position, at, k);
                if (!m.body.isSun && !m.moon) MiniOrbits.Add(sun, m.body.position.magnitude * k);
                MiniWells.Add(p, Mathf.Max(m.body.WellRadius * k, Mathf.Max(m.size.x, m.size.y) * 0.5f + WellMargin));
                bool inside = p.magnitude <= ClearPx - InsideMargin;
                Show(m.disc, inside);
                if (inside) { m.disc.anchoredPosition = p; placedTags.Add(new Rect(p - m.size * 0.5f, m.size)); }
                // the name tag only where its whole box lies in the porthole's clear centre
                bool tagFits = inside && Fits(p + m.tagOffset, m.tag.sizeDelta);
                Show(m.tag, tagFits);
                if (tagFits) { m.tag.anchoredPosition = p + m.tagOffset; placedTags.Add(new Rect(p + m.tagOffset - m.tag.sizeDelta * 0.5f, m.tag.sizeDelta)); }
                if (m.tick != null)
                {
                    bool tick = inside && Landed(state, m.body.planet);
                    Show(m.tick, tick);
                    if (tick) m.tick.anchoredPosition = p + new Vector2(m.size.x * 0.5f + 4f, -m.size.y * 0.5f + 4f);
                }
                if (m.rim == null) continue;
                Show(m.rim, !inside);
                if (!inside) { m.dist2 = (m.body.position - at).sqrMagnitude; rimOrder.Add(m); } else Show(m.rimTag, false);
            }
            MiniOrbits.Commit(); MiniWells.Commit();

            foreach (var w in Waystation.All) if (w != null && FindStation(w) < 0) AddMiniStation(w);
            for (int i = Stations.Count - 1; i >= 0; i--)
            {
                var (w, mark, tag) = Stations[i];
                if (w == null) { if (mark != null) Destroy(mark.gameObject); if (tag != null) Destroy(tag.gameObject); Stations.RemoveAt(i); continue; }
                var p = MiniPosition(w.transform.position, at, k);
                bool inside = p.magnitude <= ClearPx - InsideMargin;
                Show(mark, inside);
                if (inside) { mark.anchoredPosition = p; placedTags.Add(new Rect(p - new Vector2(12f, 12f), new Vector2(24f, 24f))); }
                var tagAt = p + new Vector2(12f + tag.sizeDelta.x * 0.5f + 3f, 0f);
                bool tagFits = inside && Fits(tagAt, tag.sizeDelta) && Free(new Rect(tagAt - tag.sizeDelta * 0.5f, tag.sizeDelta));
                Show(tag, tagFits);
                if (tagFits) { tag.anchoredPosition = tagAt; placedTags.Add(new Rect(tagAt - tag.sizeDelta * 0.5f, tag.sizeDelta)); }
            }

            // Every body beyond the rim gets its arrow; the nearest RimTags of them also their distance tag, on the outermost of three
            // rings where it fits the porthole and covers no mark or tag (else none: the system map, M, has them all).
            for (int i = 1; i < rimOrder.Count; i++) // nearest first: an insertion sort (a dozen bodies; a Sort lambda would allocate each frame)
            {
                var x = rimOrder[i];
                int j0 = i - 1;
                while (j0 >= 0 && rimOrder[j0].dist2 > x.dist2) { rimOrder[j0 + 1] = rimOrder[j0]; j0--; }
                rimOrder[j0 + 1] = x;
            }
            rimBearings.Clear();
            int tagged = 0;
            for (int j = 0; j < rimOrder.Count; j++)
            {
                var m = rimOrder[j];
                var off = m.body.position - at;
                float dist = off.magnitude;
                var dir = dist > 1e-3f ? off / dist : Vector2.up;
                float bearing = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
                // bodies lined up behind a nearer one (the inner planets seen from the giants) share its arrow
                bool behind = false;
                foreach (float b in rimBearings) if (Mathf.Abs(Mathf.DeltaAngle(b, bearing)) < RimClusterDeg) { behind = true; break; }
                Show(m.rim, !behind);
                if (behind) { Show(m.rimTag, false); continue; }
                rimBearings.Add(bearing);
                m.rim.anchoredPosition = dir * RimPx;
                m.rim.localRotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg - 90f); // the arrow points up at 0
                bool placed = false;
                if (tagged < RimTags)
                {
                    int tenths = Mathf.RoundToInt(dist / 100f);
                    if (tenths != m.rimTenths) { m.rimTenths = tenths; SetTag(m.rimTag, m.rimLabel, $"{m.label} {tenths / 10f:0.0}k"); }
                    var size = m.rimTag.sizeDelta;
                    // the tag's outer edge just inside its arrow, then slid along the rim (either way) until it covers nothing
                    float extent = Mathf.Abs(dir.x) * size.x * 0.5f + Mathf.Abs(dir.y) * size.y * 0.5f;
                    var along = new Vector2(-dir.y, dir.x);
                    foreach (float r in RimTagPx)
                    {
                        foreach (float t in TagSlides)
                        {
                            var pos = dir * (r - extent + 12f) + along * t;
                            var box = new Rect(pos - size * 0.5f, size);
                            if (!Fits(pos, size) || !Free(box)) continue;
                            m.rimTag.anchoredPosition = pos;
                            placedTags.Add(box);
                            placed = true;
                            break;
                        }
                        if (placed) break;
                    }
                }
                if (placed) tagged++;
                Show(m.rimTag, placed);
            }
            ShipArrow.localRotation = Quaternion.Euler(0f, 0f, ship.Heading - 90f); // the arrow points up at 0; Heading 0 = +x
        }

        int FindStation(Waystation w)
        {
            for (int i = 0; i < Stations.Count; i++) if (Stations[i].station == w) return i;
            return -1;
        }

        void AddMiniStation(Waystation w)
        {
            var mark = Img(Minimap, "Station_" + w.planet, Vector2.zero, new Vector2(24f, 24f), UiKit.Ink, "ui/map/station").rectTransform;
            var tag = Tag(Minimap, "StationTag_" + w.planet, "Waystation", 14, out _);
            int under = ShipArrow.GetSiblingIndex();
            mark.SetSiblingIndex(under); tag.SetSiblingIndex(under + 1);
            if (art.TryGetValue("ui/map/station", out var s)) Dress("ui/map/station", s);
            if (art.TryGetValue("ui/map/name_tag", out var t)) Dress("ui/map/name_tag", t);
            Stations.Add((w, mark, tag));
        }

        /// <summary>A box (centre, size) lies wholly inside the porthole's clear centre.</summary>
        public static bool Fits(Vector2 centre, Vector2 size)
        {
            var h = size * 0.5f;
            float r = ClearPx - 1f;
            return (centre + h).magnitude <= r && (centre - h).magnitude <= r && (centre + new Vector2(h.x, -h.y)).magnitude <= r && (centre + new Vector2(-h.x, h.y)).magnitude <= r;
        }

        bool Free(Rect box)
        {
            foreach (var o in placedTags) if (o.Overlaps(box)) return false;
            return true;
        }

        static void Show(Component c, bool on) { if (c != null && c.gameObject.activeSelf != on) c.gameObject.SetActive(on); }

        /// <summary>The Waystations on the system map (the docking bay creates them after the world builds: added as they appear).</summary>
        void SyncSystemStations()
        {
            foreach (var w in Waystation.All)
            {
                if (w == null) continue;
                string id = "station:" + w.planet;
                bool have = false;
                foreach (var sm in SystemMarks) if (sm.name == id) { have = true; break; }
                if (have) continue;
                Vector2 p = w.transform.position;
                bool inset = p.magnitude < InnerRange;
                var chart = inset ? insetChart : fullChart;
                var mark = Img(chart, "Station_" + w.planet, p * (inset ? InsetScale : FullScale), new Vector2(24f, 24f), UiKit.Ink, "ui/map/station").rectTransform;
                SystemMarks.Add(new SystemMark { name = id, world = p, inset = inset, disc = mark });
                mark.SetAsFirstSibling(); // under the planets' marks and tags
                if (art.TryGetValue("ui/map/station", out var s)) Dress("ui/map/station", s);
            }
        }

        void UpdateSystem()
        {
            SyncSystemStations();
            var state = GameState.Instance;
            foreach (var sm in SystemMarks)
                if (sm.tick != null) Show(sm.tick, Landed(state, PlanetOf(sm.name)));
            PlaceSystemTags(); // after the ticks: a shown tick is a place a tag must not cover
            UpdateSystemShip();
        }

        static PlanetId PlanetOf(string name) => System.Enum.TryParse(name, true, out PlanetId p) ? p : PlanetId.Earth;

        void UpdateSystemShip()
        {
            Vector2 at = ship.Position;
            var rot = Quaternion.Euler(0f, 0f, ship.Heading - 90f);
            SystemShip.anchoredPosition = at * FullScale;
            SystemShip.localRotation = rot;
            bool inner = at.magnitude < InnerRange;
            Show(insetShip, inner);
            if (inner) { insetShip.anchoredPosition = at * InsetScale; insetShip.localRotation = rot; }
        }

        /// <summary>The system map's position of a mark (canvas px from the paper's centre), for SpaceMapTests.</summary>
        public static Vector2 PanelPosition(RectTransform mark) =>
            mark.anchoredPosition + (mark.parent is RectTransform chart ? chart.anchoredPosition : Vector2.zero);
    }
}
