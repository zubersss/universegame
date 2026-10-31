using Meridian.Core;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Ship;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// Side-view HUD (Bible §5.1, §9; U-015): health, oxygen (placeholder until the Envirosuit
    /// system), ship fuel, and the altitude bar with the Escape Line marker. Thin, planet-tinted,
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

        public Image HealthFill { get; private set; }
        public Image OxygenFill { get; private set; }
        public Image FuelFill { get; private set; }
        public RectTransform EscapeMarker { get; private set; }
        public RectTransform YouMarker { get; private set; }
        public Text HealthText { get; private set; }
        public Text FuelText { get; private set; }
        public Text AltText { get; private set; }
        /// <summary>U-026: "DUST STORM IN 45 s" during the warning, "DUST STORM" while it blows; empty otherwise.</summary>
        public Text StormText { get; private set; }
        /// <summary>U-029: Cryo level 0–3, suit integrity bar, and the suit's rate ("-1.5/s", "+5/s").</summary>
        public Text CryoText { get; private set; }
        public Image SuitFill { get; private set; }
        public Text SuitRateText { get; private set; }

        PlanetConfig planet;
        PlayerVitals vitals;
        Image accentLine;
        static UiKit.NumberStrings numbers;
        int lastHealth = -1, lastFuel = -1, lastAlt = int.MinValue;
        int lastStorm = -2;
        int lastCryo = -1, lastSuit = -1, lastRate = int.MinValue;
        static readonly string[] CryoLevels = { "0", "1", "2", "3" };
        static string[] stormWarnings;
        const string StormNow = "DUST STORM";

        void Awake()
        {
            numbers ??= new UiKit.NumberStrings(-2000, 4000);
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "SideHudCanvas", 100);
            hudCanvas = canvas;
            var root = canvas.transform;
            var tl = new Vector2(0f, 1f);

            accentLine = UiKit.Panel(root, "Accent", tl, new Vector2(24f, -20f), new Vector2(220f, 2f), UiTheme.Accent(null));
            Label(root, "HEALTH", -36f);
            HealthFill = UiKit.Bar(root, "Health", tl, new Vector2(24f, -58f), new Vector2(220f, 6f), theme.health);
            HealthText = UiKit.Text(root, "HealthValue", tl, new Vector2(252f, -48f), new Vector2(80f, 24f), 18);
            Label(root, "O2", -76f);
            OxygenFill = UiKit.Bar(root, "Oxygen", tl, new Vector2(24f, -98f), new Vector2(220f, 6f), theme.oxygen);
            var o2 = UiKit.Text(root, "OxygenValue", tl, new Vector2(252f, -88f), new Vector2(80f, 24f), 18, false, TextAnchor.MiddleLeft, theme.label);
            o2.text = "100"; // placeholder until the Envirosuit oxygen system (M3)
            Label(root, "SHIP FUEL", -116f);
            FuelFill = UiKit.Bar(root, "Fuel", tl, new Vector2(24f, -138f), new Vector2(220f, 6f), UiTheme.Accent(null));
            FuelText = UiKit.Text(root, "FuelValue", tl, new Vector2(252f, -128f), new Vector2(80f, 24f), 18);
            Label(root, "CRYO", -156f);
            CryoText = UiKit.Text(root, "CryoLevel", tl, new Vector2(70f, -156f), new Vector2(30f, 18f), 13, true, TextAnchor.MiddleLeft, new Color(0.6f, 0.85f, 1f, 1f));
            Label(root, "SUIT", -176f);
            SuitFill = UiKit.Bar(root, "Suit", tl, new Vector2(24f, -198f), new Vector2(220f, 6f), new Color(0.6f, 0.85f, 1f, 1f));
            SuitRateText = UiKit.Text(root, "SuitRate", tl, new Vector2(252f, -188f), new Vector2(120f, 24f), 16);
            SuitRateText.text = "";

            // Altitude bar on the right edge: world bottom → world top, Escape Line marked.
            var right = new Vector2(1f, 0.5f);
            UiKit.Panel(root, "AltBar", right, new Vector2(-40f, 0f), new Vector2(3f, BarHeight), theme.barBack);
            var bar = UiKit.Rect(root, "AltSpace", right, new Vector2(-40f, -BarHeight * 0.5f), new Vector2(3f, BarHeight), new Vector2(0.5f, 0f));
            EscapeMarker = UiKit.Panel(bar, "Escape", new Vector2(0.5f, 0f), Vector2.zero, new Vector2(30f, 2f), new Color(0.6f, 0.88f, 1f, 0.95f)).rectTransform;
            var escapeLabel = UiKit.Text(EscapeMarker, "EscapeLabel", new Vector2(0f, 0.5f), new Vector2(-8f, 0f), new Vector2(120f, 20f), 13, false, TextAnchor.MiddleRight, new Color(0.6f, 0.88f, 1f, 0.95f));
            escapeLabel.rectTransform.pivot = new Vector2(1f, 0.5f);
            escapeLabel.text = "ESCAPE";
            YouMarker = UiKit.Panel(bar, "You", new Vector2(0.5f, 0f), Vector2.zero, new Vector2(14f, 6f), theme.text).rectTransform;
            AltText = UiKit.Text(root, "AltValue", right, new Vector2(-64f, -BarHeight * 0.5f - 22f), new Vector2(160f, 24f), 18, false, TextAnchor.MiddleRight);
            AltText.rectTransform.pivot = new Vector2(1f, 0.5f);

            if (stormWarnings == null)
            {
                stormWarnings = new string[61];
                for (int i = 0; i <= 60; i++) stormWarnings[i] = "DUST STORM IN " + i + " s";
            }
            StormText = UiKit.Text(root, "Storm", new Vector2(0.5f, 1f), new Vector2(0f, -40f), new Vector2(600f, 28f), 20, true, TextAnchor.MiddleCenter, new Color(1f, 0.72f, 0.45f, 1f));
            StormText.text = "";
        }

        void UpdateHazards()
        {
            if (hazards == null) return;
            int c = hazards.CryoLevel;
            if (c != lastCryo) { lastCryo = c; CryoText.text = CryoLevels[Mathf.Clamp(c, 0, 3)]; }
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

        void Label(Transform root, string text, float y) =>
            UiKit.Text(root, text, new Vector2(0f, 1f), new Vector2(24f, y), new Vector2(200f, 18f), 13, false, TextAnchor.MiddleLeft, UiTheme.Active.label).text = text;

        public void ConfigureFor(PlanetConfig p)
        {
            planet = p;
            var accent = UiTheme.Accent(p.id);
            accentLine.color = accent;
            FuelFill.color = accent;
            EscapeMarker.anchoredPosition = new Vector2(0f, (float)p.EscapeLineY / p.worldHeight * BarHeight);
        }

        Canvas hudCanvas;

        void LateUpdate()
        {
            bool hidden = MenuController.HudHidden;
            if (hudCanvas != null && hudCanvas.enabled == hidden) hudCanvas.enabled = !hidden;
            var state = GameState.Instance;
            if (vitals == null && player != null) vitals = player.GetComponent<PlayerVitals>();
            if (vitals != null)
            {
                int h = Mathf.CeilToInt(vitals.health);
                if (h != lastHealth) { lastHealth = h; HealthText.text = numbers[h]; HealthFill.fillAmount = vitals.health / vitals.maxHealth; }
            }
            if (state != null)
            {
                int f = Mathf.CeilToInt(state.fuel);
                if (f != lastFuel) { lastFuel = f; FuelText.text = numbers[f]; FuelFill.fillAmount = state.fuel / Mathf.Max(1f, state.tankCapacity); }
            }
            UpdateStorm();
            UpdateHazards();
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
