using Meridian.UI;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.Ship
{
    /// <summary>
    /// Ship block of the side HUD while aboard (Bible §5.1, §4.3 v4.1): vertical speed and thrust-to-weight. U-107 (D-106):
    /// thrust-to-weight is the only climb limit, so the T/W readout turns amber below AmberLine (a slow climb) and the
    /// stranded warning shows below 1.0 (the ship cannot climb here). Altitude and the Escape Line bar are on SideHud.
    /// </summary>
    public sealed class ShipHud : MonoBehaviour
    {
        /// <summary>D-106: thrust-to-weight below this reads amber.</summary>
        public const float AmberLine = 1.2f;
        public static readonly Color Amber = new Color(1f, 0.72f, 0.2f, 1f);

        public enum TwrState { Ok, Amber, CannotClimb }

        /// <summary>The HUD state for a thrust-to-weight ratio (pure; tested at 1.08 and 1.22).</summary>
        public static TwrState StateFor(float thrustToWeight) =>
            thrustToWeight <= 1f ? TwrState.CannotClimb : thrustToWeight < AmberLine ? TwrState.Amber : TwrState.Ok;

        public SideShip ship;
        public ShipBoarding boarding;

        public Text VerticalSpeed { get; private set; }
        public Text ThrustToWeight { get; private set; }
        public Text Warning { get; private set; }
        public TwrState State { get; private set; }

        GameObject root;
        Color twrColor;
        static UiKit.NumberStrings signed, tenths;
        int lastVs = int.MinValue, lastTwr = -1;
        TwrState lastState = (TwrState)(-1);
        const string CannotClimbLine = "THRUST < GRAVITY: CANNOT CLIMB HERE";
        const string SlowClimbLine = "LOW THRUST: SLOW CLIMB";

        void Awake()
        {
            signed ??= new UiKit.NumberStrings(-2000, 4000);
            tenths ??= new UiKit.NumberStrings(0, 99, "0.0", 10f);
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "ShipHudCanvas", 101);
            root = canvas.gameObject;
            var tl = new Vector2(0f, 1f);
            UiKit.Text(canvas.transform, "VsLabel", tl, new Vector2(24f, -176f), new Vector2(120f, 18f), 13, false, TextAnchor.MiddleLeft, theme.label).text = "V/S m/s";
            VerticalSpeed = UiKit.Text(canvas.transform, "Vs", tl, new Vector2(24f, -200f), new Vector2(160f, 30f), 26);
            UiKit.Text(canvas.transform, "TwLabel", tl, new Vector2(170f, -176f), new Vector2(120f, 18f), 13, false, TextAnchor.MiddleLeft, theme.label).text = "T/W";
            ThrustToWeight = UiKit.Text(canvas.transform, "Tw", tl, new Vector2(170f, -200f), new Vector2(120f, 30f), 26);
            twrColor = ThrustToWeight.color;
            Warning = UiKit.Text(canvas.transform, "Warning", tl, new Vector2(24f, -236f), new Vector2(520f, 24f), 16, true, TextAnchor.MiddleLeft, theme.warning);
            Warning.enabled = false;
            root.SetActive(false);
        }

        void LateUpdate()
        {
            bool show = ship != null && (boarding == null || boarding.Aboard) && !MenuController.HudHidden;
            if (root.activeSelf != show) root.SetActive(show);
            if (!show) return;
            int v = Mathf.RoundToInt(ship.Body.linearVelocity.y);
            if (v != lastVs) { lastVs = v; VerticalSpeed.text = signed[v]; }
            float twr = ship.ThrustToWeight;
            int t = Mathf.RoundToInt(twr * 10f);
            if (t != lastTwr) { lastTwr = t; ThrustToWeight.text = tenths[t]; }
            Apply(StateFor(twr));
        }

        /// <summary>Shows a state (tests drive it directly too).</summary>
        public void Apply(TwrState s)
        {
            State = s;
            if (s == lastState) return;
            lastState = s;
            ThrustToWeight.color = s == TwrState.Ok ? twrColor : s == TwrState.Amber ? Amber : Warning.color;
            Warning.enabled = s != TwrState.Ok;
            Warning.text = s == TwrState.CannotClimb ? CannotClimbLine : SlowClimbLine;
        }
    }
}
