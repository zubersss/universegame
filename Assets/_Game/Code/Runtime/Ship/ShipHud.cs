using Meridian.UI;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.Ship
{
    /// <summary>
    /// Ship block of the side HUD while aboard (Bible §5.1, §4.3 v4.1; U-104, D-103: no fuel anywhere): vertical speed,
    /// thrust-to-weight, altitude above the ground and the tilt, in the HUD face. U-107 (D-106): thrust-to-weight is the only
    /// climb limit, so the T/W readout turns amber below AmberLine (a slow climb) and the stranded warning shows below 1.0
    /// (the ship cannot climb here). The altitude above the Datum and the Escape Line bar stay on SideHud.
    /// </summary>
    public sealed class ShipHud : MonoBehaviour
    {
        /// <summary>D-106: thrust-to-weight below this reads amber.</summary>
        public const float AmberLine = 1.2f;
        public static readonly Color Amber = new Color(1f, 0.72f, 0.2f, 1f);
        /// <summary>U-104: the block sits under the gauges and the suit rows of SideHud.</summary>
        public const float RowLabelY = -316f, RowValueY = -340f, WarningY = -380f;

        public enum TwrState { Ok, Amber, CannotClimb }

        /// <summary>The HUD state for a thrust-to-weight ratio (pure; tested at 1.08 and 1.22).</summary>
        public static TwrState StateFor(float thrustToWeight) =>
            thrustToWeight <= 1f ? TwrState.CannotClimb : thrustToWeight < AmberLine ? TwrState.Amber : TwrState.Ok;

        public SideShip ship;
        public ShipBoarding boarding;

        public Text VerticalSpeed { get; private set; }
        public Text ThrustToWeight { get; private set; }
        /// <summary>U-104: height of the skids above the ground under them, whole metres.</summary>
        public Text Altitude { get; private set; }
        /// <summary>U-104: the hull's tilt in whole degrees, signed (+ = leaning left, RocketFlight).</summary>
        public Text Tilt { get; private set; }
        public Text Warning { get; private set; }
        public TwrState State { get; private set; }

        GameObject root;
        Color twrColor;
        static UiKit.NumberStrings signed, tenths;
        int lastVs = int.MinValue, lastTwr = -1, lastAlt = int.MinValue, lastTilt = int.MinValue;
        TwrState lastState = (TwrState)(-1);
        const string CannotClimbLine = "THRUST < GRAVITY: CANNOT CLIMB HERE";
        const string SlowClimbLine = "LOW THRUST: SLOW CLIMB";
        const string NoGround = "---";

        void Awake()
        {
            signed ??= new UiKit.NumberStrings(-2000, 4000);
            tenths ??= new UiKit.NumberStrings(0, 99, "0.0", 10f);
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "ShipHudCanvas", 101);
            root = canvas.gameObject;
            var tl = new Vector2(0f, 1f);
            Row(canvas.transform, "VsLabel", "V/S m/s", 24f, out var vs); VerticalSpeed = vs;
            Row(canvas.transform, "TwLabel", "T/W", 170f, out var tw); ThrustToWeight = tw;
            Row(canvas.transform, "AltLabel", "AGL m", 300f, out var alt); Altitude = alt;
            Row(canvas.transform, "TiltLabel", "TILT °", 450f, out var tilt); Tilt = tilt;
            twrColor = ThrustToWeight.color;
            Warning = UiKit.Text(canvas.transform, "Warning", tl, new Vector2(24f, WarningY), new Vector2(560f, 24f), 16, true, TextAnchor.MiddleLeft, theme.warning);
            Warning.enabled = false;
            root.SetActive(false);
        }

        static void Row(Transform parent, string name, string label, float x, out Text value)
        {
            var tl = new Vector2(0f, 1f);
            UiKit.Text(parent, name, tl, new Vector2(x, RowLabelY), new Vector2(130f, 18f), 14, false, TextAnchor.MiddleLeft, UiTheme.Active.label).text = label;
            value = UiKit.Text(parent, name.Replace("Label", ""), tl, new Vector2(x, RowValueY), new Vector2(140f, 30f), 26);
        }

        void LateUpdate()
        {
            bool show = ship != null && (boarding == null || boarding.Aboard) && !MenuController.HudHidden;
            if (root.activeSelf != show) root.SetActive(show);
            if (!show) return;
            int v = Mathf.Clamp(Mathf.RoundToInt(ship.Body.linearVelocity.y), -2000, 4000);
            if (v != lastVs) { lastVs = v; VerticalSpeed.text = signed[v]; }
            float twr = ship.ThrustToWeight;
            int t = Mathf.Clamp(Mathf.RoundToInt(twr * 10f), 0, 99);
            if (t != lastTwr) { lastTwr = t; ThrustToWeight.text = tenths[t]; }
            float agl = ship.AltitudeAboveGround;
            int a = float.IsFinite(agl) ? Mathf.Clamp(Mathf.RoundToInt(agl), 0, 4000) : int.MaxValue; // no ground under the probe: a dash (MinValue is the unset mark)
            if (a != lastAlt) { lastAlt = a; Altitude.text = a == int.MaxValue ? NoGround : signed[a]; }
            int tilt = Mathf.Clamp(Mathf.RoundToInt(ship.Tilt), -2000, 4000);
            if (tilt != lastTilt) { lastTilt = tilt; Tilt.text = signed[tilt]; }
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
