using System.Collections.Generic;
using Meridian.Art;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Ship;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// Side-view HUD (Bible §5.1, §9; U-015): health, oxygen (placeholder until the Envirosuit
    /// system), the altitude bar (U-107: no ship fuel, D-103) with the Escape Line marker. Thin, planet-tinted,
    /// monospace numerals; updates allocate nothing.
    /// </summary>
    public sealed class SideHud : MonoBehaviour
    {
        public const float BarHeight = 320f;

        public PlayerController player;
        public SideShip ship;
        public ShipBoarding boarding;
        public Meridian.Planet.Weather.DustStorm storm;
        public Meridian.Hazards.HazardSystem hazards;
        public Meridian.Planet.POI.PoiPlacer pois;

        public Image HealthFill { get; private set; }
        public Image OxygenFill { get; private set; }
        /// <summary>U-104 (B-121): the three dials (Suit power, oxygen, the gravity readout); the bars stay the fallback, and keep their fill amounts, until the sheet is in.</summary>
        public HudGauge SuitGauge { get; private set; }
        public HudGauge OxygenGauge { get; private set; }
        public HudGauge GravityGauge { get; private set; }
        public bool GaugesReady => SuitGauge != null && SuitGauge.Ready && OxygenGauge.Ready && GravityGauge.Ready;
        /// <summary>B-121 draws the dials 320 px at 1x; the HUD shows them at this scale, three across the top-left at 1080p.</summary>
        public const float DialScale = 0.5f;
        /// <summary>The gravity dial's full scale in g (Jupiter's 2.5 g sits inside it; Earth reads a third).</summary>
        public const float GravityFullScale = 3f;
        public Text OxygenText { get; private set; }
        Text suitPowerLabel, o2Label;
        IList<Sprite> gaugeSprites;
        TextAsset gaugeJson;
        readonly List<AsyncOperationHandle> gaugeHandles = new List<AsyncOperationHandle>(2);
        public RectTransform EscapeMarker { get; private set; }
        public RectTransform YouMarker { get; private set; }
        public Text HealthText { get; private set; }
        public Text AltText { get; private set; }
        /// <summary>U-026: "DUST STORM IN 45 s" during the warning, "DUST STORM" while it blows; empty otherwise.</summary>
        public Text StormText { get; private set; }
        /// <summary>U-029: Cryo level 0–3, suit integrity bar, and the suit's rate ("-1.5/s", "+5/s").</summary>
        public Text CryoText { get; private set; }
        public Image SuitFill { get; private set; }
        public Text SuitRateText { get; private set; }
        /// <summary>U-030 map markers, one per POI on this planet: "&lt; 120 m  SURVEY ARCHIVE".</summary>
        public readonly System.Collections.Generic.List<Text> MarkerNames = new System.Collections.Generic.List<Text>();
        public readonly System.Collections.Generic.List<Text> MarkerDistances = new System.Collections.Generic.List<Text>();
        readonly System.Collections.Generic.List<Text> markerArrows = new System.Collections.Generic.List<Text>();
        readonly System.Collections.Generic.List<int> markerLast = new System.Collections.Generic.List<int>();
        Transform hudRoot;

        PlanetConfig planet;
        PlayerVitals vitals;
        Image accentLine;
        static UiKit.NumberStrings numbers;
        int lastHealth = -1, lastAlt = int.MinValue;
        int lastStorm = -2;
        int lastCryo = -1, lastSuit = -1, lastRate = int.MinValue;
        static readonly string[] CryoLevels = { "0", "1", "2", "3", "4" };
        static readonly string[] KindNames = { "THERMAL", "CRYO", "RADIATION", "TOXIC", "PRESSURE" };
        int lastKind = -1;
        /// <summary>U-147 (D-149): the paper tags under the HUD's lettering (hazard, suit, escape, altitude, the gauges' captions, the POI rows).</summary>
        public readonly System.Collections.Generic.List<Image> Tags = new System.Collections.Generic.List<Image>();
        /// <summary>U-147: each POI row's tag (shown with its row).</summary>
        public readonly System.Collections.Generic.List<Image> MarkerTags = new System.Collections.Generic.List<Image>();
        /// <summary>U-147: the lettering each tag carries, in the order of Tags (tests check it sits on its tag in ink).</summary>
        public readonly System.Collections.Generic.List<Text[]> TagLetters = new System.Collections.Generic.List<Text[]>();
        Image Tag(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, Vector2 pivot, params Text[] letters)
        {
            var tag = UiKit.PaperTag(parent, name, anchor, pos, size, pivot, letters.Length > 0 && letters[0] != null ? letters[0].transform : null);
            foreach (var t in letters) UiKit.InkOn(t);
            Tags.Add(tag); TagLetters.Add(letters);
            return tag;
        }
        /// <summary>U-049: the name of the hazard shown beside the level (the worst one).</summary>
        public Text HazardLabel { get; private set; }
        static string[] stormWarnings;
        const string StormNow = "DUST STORM";

        void Awake()
        {
            numbers ??= new UiKit.NumberStrings(-2000, 4000);
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "SideHudCanvas", 100);
            hudCanvas = canvas;
            var root = canvas.transform;
            hudRoot = root;
            var tl = new Vector2(0f, 1f);

            accentLine = UiKit.Panel(root, "Accent", tl, new Vector2(24f, -20f), new Vector2(220f, 2f), UiTheme.Accent(null));
            suitPowerLabel = Label(root, "SUIT POWER", -36f); // U-093 (D-087): no health; the suit's integrity + reserve as one gauge
            HealthFill = UiKit.Bar(root, "Health", tl, new Vector2(24f, -58f), new Vector2(220f, 6f), theme.health);
            HealthText = UiKit.Text(root, "HealthValue", tl, new Vector2(252f, -48f), new Vector2(80f, 24f), 18);
            o2Label = Label(root, "O2", -76f);
            OxygenFill = UiKit.Bar(root, "Oxygen", tl, new Vector2(24f, -98f), new Vector2(220f, 6f), theme.oxygen);
            OxygenText = UiKit.Text(root, "OxygenValue", tl, new Vector2(252f, -88f), new Vector2(80f, 24f), 18, false, TextAnchor.MiddleLeft, theme.label);
            OxygenText.text = "100"; // placeholder until the Envirosuit oxygen system (M3)
            // U-104: the suit rows sit under the dials and their numbers (y −246 … −288); the ship block (ShipHud) follows under them.
            HazardLabel = UiKit.Text(root, "HazardKind", new Vector2(0f, 1f), new Vector2(24f, -246f), new Vector2(200f, 18f), 13, false, TextAnchor.MiddleLeft, UiTheme.Active.label);
            HazardLabel.text = KindNames[(int)Meridian.Hazards.HazardKind.Cryo];
            CryoText = UiKit.Text(root, "CryoLevel", tl, new Vector2(130f, -246f), new Vector2(30f, 18f), 13, true, TextAnchor.MiddleLeft, new Color(0.6f, 0.85f, 1f, 1f));
            var suitWord = Label(root, "SUIT", -266f);
            SuitFill = UiKit.Bar(root, "Suit", tl, new Vector2(24f, -288f), new Vector2(220f, 6f), new Color(0.6f, 0.85f, 1f, 1f));
            SuitRateText = UiKit.Text(root, "SuitRate", tl, new Vector2(252f, -278f), new Vector2(120f, 24f), 16);
            SuitRateText.text = "";
            // U-147 (D-149): the hazard row and the suit row on paper tags in ink; the suit bar an ink-ruled strip with a gold fill.
            Tag(root, "HazardTag", tl, new Vector2(18f, -243f), new Vector2(128f, 23f), tl, HazardLabel, CryoText);
            Tag(root, "SuitTag", tl, new Vector2(18f, -267f), new Vector2(312f, 32f), tl, suitWord, SuitRateText);
            var suitBack = SuitFill.transform.parent.GetComponent<Image>();
            suitBack.color = UiKit.Cream;
            UiKit.InkEdges(suitBack.rectTransform, UiKit.CardEdge, UiKit.Ink);
            SuitFill.color = UiKit.Gold;
            BuildGauges(root);

            // Altitude bar on the right edge: world bottom → world top, Escape Line marked.
            var right = new Vector2(1f, 0.5f);
            UiKit.Panel(root, "AltBar", right, new Vector2(-40f, 0f), new Vector2(3f, BarHeight), theme.barBack);
            var bar = UiKit.Rect(root, "AltSpace", right, new Vector2(-40f, -BarHeight * 0.5f), new Vector2(3f, BarHeight), new Vector2(0.5f, 0f));
            EscapeMarker = UiKit.Panel(bar, "Escape", new Vector2(0.5f, 0f), Vector2.zero, new Vector2(30f, 2f), UiKit.Gold).rectTransform; // U-147: a gold rule (it reads on every sky)
            var escapeLabel = UiKit.Text(EscapeMarker, "EscapeLabel", new Vector2(0f, 0.5f), new Vector2(-8f, 0f), new Vector2(120f, 20f), 13, false, TextAnchor.MiddleRight, new Color(0.6f, 0.88f, 1f, 0.95f));
            escapeLabel.rectTransform.pivot = new Vector2(1f, 0.5f);
            escapeLabel.text = "ESCAPE";
            Tag(EscapeMarker, "EscapeTag", new Vector2(0f, 0.5f), new Vector2(-4f, 0f), new Vector2(70f, 22f), new Vector2(1f, 0.5f), escapeLabel); // U-147
            YouMarker = UiKit.Panel(bar, "You", new Vector2(0.5f, 0f), Vector2.zero, new Vector2(14f, 6f), theme.text).rectTransform;
            AltText = UiKit.Text(root, "AltValue", right, new Vector2(-64f, -BarHeight * 0.5f - 22f), new Vector2(160f, 24f), 18, false, TextAnchor.MiddleRight);
            AltText.rectTransform.pivot = new Vector2(1f, 0.5f);
            Tag(root, "AltTag", right, new Vector2(-60f, -BarHeight * 0.5f - 22f), new Vector2(76f, 26f), new Vector2(1f, 0.5f), AltText); // U-147

            if (stormWarnings == null)
            {
                stormWarnings = new string[61];
                for (int i = 0; i <= 60; i++) stormWarnings[i] = "DUST STORM IN " + i + " s";
            }
            StormText = UiKit.Text(root, "Storm", new Vector2(0.5f, 1f), new Vector2(0f, -40f), new Vector2(600f, 28f), 20, true, TextAnchor.MiddleCenter, new Color(1f, 0.72f, 0.45f, 1f));
            StormText.text = "";

            // U-045: the Tab inventory panel lives beside the HUD (built in code, no scene change).
            Inventory = gameObject.AddComponent<InventoryPanel>();
            Inventory.player = player;
            // U-051: the crafting panel (B).
            Crafting = gameObject.AddComponent<CraftingPanel>();
            Crafting.player = player;
            // U-054: the Survey Catalogue (N).
            Catalogue = gameObject.AddComponent<CataloguePanel>();
            Catalogue.player = player;
        }

        public InventoryPanel Inventory { get; private set; }
        public CraftingPanel Crafting { get; private set; }
        public CataloguePanel Catalogue { get; private set; }

        const int MaxMarkers = 4;

        void BuildMarkers()
        {
            for (int i = 0; i < MaxMarkers; i++)
            {
                float y = -40f - i * 22f;
                // Boxes are pinned by their top-right corner (UiKit): arrow -440..-420, distance -420..-340 (right-aligned), name -320..-100.
                var right = new Vector2(1f, 1f);
                var arrow = UiKit.Text(hudRoot, "MarkerArrow" + i, right, new Vector2(-420f, y), new Vector2(20f, 20f), 14, true, TextAnchor.MiddleCenter, new Color(1f, 0.85f, 0.5f, 1f));
                var dist = UiKit.Text(hudRoot, "MarkerDistance" + i, right, new Vector2(-340f, y), new Vector2(80f, 20f), 14, false, TextAnchor.MiddleRight);
                var name = UiKit.Text(hudRoot, "MarkerName" + i, right, new Vector2(-100f, y), new Vector2(220f, 20f), 13, false, TextAnchor.MiddleLeft, UiTheme.Active.label);
                arrow.text = dist.text = name.text = "";
                // U-147 (D-149): each row on its own paper tag in ink, shown with its row.
                var tag = Tag(hudRoot, "MarkerTag" + i, right, new Vector2(-96f, y + 1f), new Vector2(348f, 21f), right, arrow, dist, name);
                tag.gameObject.SetActive(false);
                MarkerTags.Add(tag);
                markerArrows.Add(arrow); MarkerDistances.Add(dist); MarkerNames.Add(name);
                markerLast.Add(int.MinValue);
            }
        }

        void UpdateMarkers()
        {
            if (pois == null) return;
            if (markerArrows.Count == 0) BuildMarkers();
            var body = player != null && player.isActiveAndEnabled ? (Transform)player.transform : ship != null ? ship.transform : null;
            if (body == null) return;
            float px = body.position.x;
            int next = 0; // walks the placed POIs that show a marker (the spawn camp doesn't)
            for (int i = 0; i < MaxMarkers; i++)
            {
                while (next < pois.placed.Count && !pois.placed[next].def.marker) next++;
                bool on = next < pois.placed.Count;
                if (!on) { if (MarkerNames[i].text.Length > 0) { MarkerNames[i].text = markerArrows[i].text = MarkerDistances[i].text = ""; markerLast[i] = int.MinValue; } if (MarkerTags[i].gameObject.activeSelf) MarkerTags[i].gameObject.SetActive(false); continue; }
                if (!MarkerTags[i].gameObject.activeSelf) MarkerTags[i].gameObject.SetActive(true);
                var p = pois.placed[next++];
                if (!ReferenceEquals(MarkerNames[i].text, p.def.MarkerText)) MarkerNames[i].text = p.def.MarkerText;
                float dx = p.nearestX - px;
                int d = Mathf.Min(Mathf.RoundToInt(Mathf.Abs(dx)), 3999);
                int code = dx < 0f ? -d - 1 : d; // sign carries the arrow
                if (code == markerLast[i]) continue;
                markerLast[i] = code;
                markerArrows[i].text = d < 3 ? "*" : dx < 0f ? "<" : ">";
                MarkerDistances[i].text = numbers[d];
            }
        }

        void UpdateHazards()
        {
            if (hazards == null) return;
            // U-049: the worst hazard after the suit (its name and effective level); Cryo while nothing bites.
            int c = hazards.EffectiveLevel;
            int k = c > 0 ? (int)hazards.WorstKind : (int)Meridian.Hazards.HazardKind.Cryo;
            if (c != lastCryo) { lastCryo = c; CryoText.text = CryoLevels[Mathf.Clamp(c, 0, 4)]; }
            if (k != lastKind) { lastKind = k; HazardLabel.text = KindNames[k]; }
            int s = Mathf.CeilToInt(hazards.SuitIntegrity);
            if (s != lastSuit) { lastSuit = s; SuitFill.fillAmount = hazards.SuitIntegrity / Meridian.Hazards.HazardRules.SuitMax; }
            int r = Mathf.RoundToInt(hazards.SuitRate * 10f); // tenths per second
            if (r != lastRate) { lastRate = r; SuitRateText.text = RateString(r); }
        }

        static string[] rateStrings;

        /// <summary>"-1.5/s" style strings for -99.9..+9.9 per second, built once.</summary>
        static string RateString(int tenths)
        {
            if (tenths == 0) return "";
            if (rateStrings == null)
            {
                rateStrings = new string[1100];
                for (int i = 0; i < rateStrings.Length; i++)
                {
                    int t = i - 999;
                    rateStrings[i] = t == 0 ? "" : (t > 0 ? "+" : "-") + (Mathf.Abs(t) / 10) + "." + (Mathf.Abs(t) % 10) + "/s";
                }
            }
            return rateStrings[Mathf.Clamp(tenths, -999, 100) + 999];
        }

        void UpdateStorm()
        {
            int code = -1; // -1 none, 0..60 warning seconds, 61 storm
            if (storm != null && storm.OnMars)
            {
                if (storm.Phase == Meridian.Planet.Weather.StormPhase.Storm) code = 61;
                else if (storm.Phase == Meridian.Planet.Weather.StormPhase.Warning && storm.time != null)
                    code = Mathf.Clamp(Mathf.CeilToInt((float)((storm.Current.start - storm.time.GameSeconds) / TimeSystem.GameSecondsPerRealSecond)), 0, 60);
            }
            if (code == lastStorm) return;
            lastStorm = code;
            StormText.text = code < 0 ? "" : code == 61 ? StormNow : stormWarnings[code];
        }

        Text Label(Transform root, string text, float y)
        {
            var t = UiKit.Text(root, text, new Vector2(0f, 1f), new Vector2(24f, y), new Vector2(200f, 18f), 13, false, TextAnchor.MiddleLeft, UiTheme.Active.label);
            t.text = text;
            return t;
        }

        /// <summary>
        /// U-104 (B-121): the three dials across the top-left, built hidden; `ui/hud/gauges` (six parts) and its json arm them
        /// when the sheet is in the catalog, and the bars step aside. The needles step on the 12 Hz ticks in LateUpdate.
        /// </summary>
        void BuildGauges(Transform root)
        {
            float d = 320f * DialScale, x = 24f, y = -24f, gap = 16f;
            SuitGauge = new HudGauge(root, "suit_power", new Vector2(x, y), d, "SUIT POWER");
            OxygenGauge = new HudGauge(root, "oxygen", new Vector2(x + d + gap, y), d, "OXYGEN");
            GravityGauge = new HudGauge(root, "gravity", new Vector2(x + 2f * (d + gap), y), d, "GRAVITY") { DangerTint = false };
            var probe = Addressables.LoadResourceLocationsAsync(ArtKeys.Ui.HudGauges + "/json", typeof(TextAsset));
            probe.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                ArtLoad.Release(loc);
                if (this == null || !exists) return;
                var sprites = ArtLoad.Asset<IList<Sprite>>(ArtKeys.Ui.HudGauges);
                gaugeHandles.Add(sprites);
                sprites.Completed += op => { if (this == null) return; if (op.Status == AsyncOperationStatus.Succeeded && op.Result != null && op.Result.Count > 0) gaugeSprites = op.Result; OnGaugeArt(); };
                var json = ArtLoad.Asset<TextAsset>(ArtKeys.Ui.HudGauges + "/json");
                gaugeHandles.Add(json);
                json.Completed += op => { if (this == null) return; if (op.Status == AsyncOperationStatus.Succeeded && op.Result != null) gaugeJson = op.Result; OnGaugeArt(); };
            };
        }

        void OnGaugeArt()
        {
            if (gaugeSprites == null || gaugeJson == null || GaugesReady) return;
            var specs = GaugeSheet.Parse(gaugeJson.text);
            var byName = new Dictionary<string, Sprite>(gaugeSprites.Count);
            foreach (var s in gaugeSprites) if (s != null) byName[s.name] = s;
            foreach (var g in new[] { SuitGauge, OxygenGauge, GravityGauge })
                if (specs.TryGetValue(g.Name, out var spec)) g.Arm(spec, byName, DialScale);
            if (!GaugesReady) { Debug.LogWarning($"[MERIDIAN] SideHud: {ArtKeys.Ui.HudGauges} lacks a dial or a needle part; the bars stay."); return; }
            // The bars step aside (their fill amounts keep updating: tests read them); the numbers move under their dials.
            HealthFill.transform.parent.gameObject.SetActive(false);
            OxygenFill.transform.parent.gameObject.SetActive(false);
            suitPowerLabel.enabled = false;
            o2Label.enabled = false;
            Under(HealthText, SuitGauge);
            Under(OxygenText, OxygenGauge);
            // U-147 (D-149): each dial's caption (and its number) on a paper tag in ink under the dial.
            GaugeTag(SuitGauge, HealthText); GaugeTag(OxygenGauge, OxygenText); GaugeTag(GravityGauge, null);
        }

        void GaugeTag(HudGauge g, Text number)
        {
            float w = g.Dial.rectTransform.sizeDelta.x;
            var pos = g.Dial.rectTransform.anchoredPosition + new Vector2(w * 0.1f, -g.Size - 1f);
            var tag = Tag(g.Caption.transform.parent, "GaugeTag_" + g.Name, new Vector2(0f, 1f), pos, new Vector2(w * 0.8f, number != null ? 47f : 23f), new Vector2(0f, 1f), g.Caption, number);
            if (number != null && number.transform.GetSiblingIndex() < tag.transform.GetSiblingIndex()) tag.transform.SetSiblingIndex(number.transform.GetSiblingIndex());
        }

        static void Under(Text t, HudGauge g)
        {
            var rt = t.rectTransform;
            rt.pivot = new Vector2(0.5f, 1f);
            rt.anchoredPosition = g.Dial.rectTransform.anchoredPosition + new Vector2(g.Dial.rectTransform.sizeDelta.x * 0.5f, -g.Size - 22f);
            rt.sizeDelta = new Vector2(g.Dial.rectTransform.sizeDelta.x, 24f);
            t.alignment = TextAnchor.MiddleCenter;
        }

        void OnDestroy()
        {
            foreach (var h in gaugeHandles) if (h.IsValid()) ArtLoad.Release(h);
        }

        public void ConfigureFor(PlanetConfig p)
        {
            planet = p;
            var accent = UiTheme.Accent(p.id);
            accentLine.color = accent;
            EscapeMarker.anchoredPosition = new Vector2(0f, (float)p.EscapeLineY / p.worldHeight * BarHeight);
        }

        Canvas hudCanvas;

        void LateUpdate()
        {
            bool hidden = MenuController.HudHidden || InventoryPanel.AnyOpen || CraftingPanel.AnyOpen || CataloguePanel.AnyOpen; // U-058: nothing draws through a full-screen panel
            if (hudCanvas != null && hudCanvas.enabled == hidden) hudCanvas.enabled = !hidden;
            if (vitals == null && player != null) vitals = player.GetComponent<PlayerVitals>();
            if (vitals != null)
            {
                // U-093: Suit power % = (suit integrity + reserve) / (SuitMax + reserve max); without a HazardSystem, the reserve alone.
                float suit = hazards != null ? hazards.SuitIntegrity : 0f, suitMax = hazards != null ? Meridian.Hazards.HazardRules.SuitMax : 0f;
                float power = (suit + vitals.health) / Mathf.Max(1f, suitMax + vitals.maxHealth);
                int h = Mathf.CeilToInt(power * 100f - 1e-3f);
                if (h != lastHealth) { lastHealth = h; HealthText.text = numbers[h]; HealthFill.fillAmount = power; }
                if (SuitGauge != null) SuitGauge.Target = power;
            }
            if (SuitGauge != null)
            {
                // U-104: the dials follow their meters on the 12 Hz ticks (a wobble on change); gravity reads the planet's g.
                OxygenGauge.Target = OxygenFill.fillAmount;
                GravityGauge.Target = planet != null ? planet.GravityRatio / GravityFullScale : 0f;
                float now = Time.time;
                var danger = UiTheme.Active.warning;
                SuitGauge.Step(now, danger); OxygenGauge.Step(now, danger); GravityGauge.Step(now, danger);
            }
            UpdateStorm();
            UpdateHazards();
            UpdateMarkers();
            if (planet == null) return;
            bool aboard = boarding != null && boarding.Aboard;
            var body = aboard && ship != null ? ship.Body : player != null && player.isActiveAndEnabled ? player.Body : null;
            if (body == null) return;
            float y = body.position.y;
            YouMarker.anchoredPosition = new Vector2(0f, Mathf.Clamp01(y / planet.worldHeight) * BarHeight);
            int alt = Mathf.RoundToInt(y - planet.datumY);
            if (alt != lastAlt) { lastAlt = alt; AltText.text = numbers[alt]; }
        }
    }
}
