using Meridian.UI;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.Ship
{
    /// <summary>
    /// Ship block of the side HUD while aboard (Bible §5.1): vertical speed, thrust-to-weight and the
    /// stranded warning (thrust &lt; g). Altitude, fuel and the Escape Line bar are on SideHud (U-015).
    /// </summary>
    public sealed class ShipHud : MonoBehaviour
    {
        public SideShip ship;
        public ShipBoarding boarding;

        public Text VerticalSpeed { get; private set; }
        public Text ThrustToWeight { get; private set; }
        public Text Warning { get; private set; }

        GameObject root;
        static UiKit.NumberStrings signed, tenths;
        int lastVs = int.MinValue, lastTwr = -1;

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
            Warning = UiKit.Text(canvas.transform, "Warning", tl, new Vector2(24f, -236f), new Vector2(520f, 24f), 16, true, TextAnchor.MiddleLeft, theme.warning);
            Warning.text = "THRUST < GRAVITY: CANNOT LAUNCH";
            root.SetActive(false);
        }

        void LateUpdate()
        {
            bool show = ship != null && (boarding == null || boarding.Aboard);
            if (root.activeSelf != show) root.SetActive(show);
            if (!show) return;
            int v = Mathf.RoundToInt(ship.Body.linearVelocity.y);
            if (v != lastVs) { lastVs = v; VerticalSpeed.text = signed[v]; }
            int t = Mathf.RoundToInt(ship.Thrust / Mathf.Max(0.01f, ship.Gravity) * 10f);
            if (t != lastTwr) { lastTwr = t; ThrustToWeight.text = tenths[t]; }
            Warning.enabled = ship.ThrustBelowGravity;
        }

    }
}
