using UnityEngine;
using UnityEngine.UI;

namespace Meridian.Ship
{
    /// <summary>
    /// Ship HUD in side view (Bible §5.1): altitude, vertical speed, fuel, thrust-to-weight, and an
    /// altitude bar with the Escape Line marker. Placeholder look; U-015 designs it. Precomputed
    /// strings keep updates allocation-free.
    /// </summary>
    public sealed class ShipHud : MonoBehaviour
    {
        public SideShip ship;
        public ShipBoarding boarding;
        public int datumY;
        public int escapeLineY;
        public int worldHeight = 800;

        Text alt, vs, fuel, twr, warn;
        RectTransform shipMarker, escapeMarker;
        GameObject root;
        static string[] signed;  // -2000..4000
        static string[] tenths;  // 0.0..9.9 for TWR
        int lastAlt = int.MinValue, lastVs = int.MinValue, lastFuel = -1, lastTwr = -1;
        const int SignedMin = -2000;
        const float BarHeight = 300f;

        void Awake()
        {
            if (signed == null)
            {
                signed = new string[6001];
                for (int i = 0; i < signed.Length; i++) signed[i] = (i + SignedMin).ToString();
                tenths = new string[100];
                for (int i = 0; i < tenths.Length; i++) tenths[i] = (i / 10f).ToString("0.0");
            }
            root = new GameObject("ShipHudCanvas");
            root.transform.SetParent(transform, false);
            var canvas = root.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            root.AddComponent<CanvasScaler>().uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            alt = Row(font, "ALT m", 0); vs = Row(font, "V/S m/s", 1); fuel = Row(font, "FUEL", 2); twr = Row(font, "T/W", 3);
            warn = Make(root.transform, font, new Vector2(24f, -260f), 18, new Color(1f, 0.45f, 0.3f));
            warn.text = "THRUST < GRAVITY: CANNOT LAUNCH";

            var bar = Box(root.transform, new Vector2(-40f, 0f), new Vector2(6f, BarHeight), new Color(1f, 1f, 1f, 0.25f), new Vector2(1f, 0.5f));
            escapeMarker = Box(bar, Vector2.zero, new Vector2(26f, 3f), new Color(0.55f, 0.85f, 1f, 0.9f), new Vector2(0.5f, 0f));
            shipMarker = Box(bar, Vector2.zero, new Vector2(16f, 8f), new Color(1f, 0.8f, 0.4f, 1f), new Vector2(0.5f, 0f));
            root.SetActive(false);
        }

        Text Row(Font font, string label, int row)
        {
            Make(root.transform, font, new Vector2(24f, -80f - row * 44f), 13, new Color(0.85f, 0.92f, 1f, 0.7f)).text = label;
            return Make(root.transform, font, new Vector2(110f, -74f - row * 44f), 24, new Color(0.85f, 0.92f, 1f, 0.95f));
        }

        static Text Make(Transform parent, Font font, Vector2 pos, int size, Color color)
        {
            var go = new GameObject("Text");
            go.transform.SetParent(parent, false);
            var t = go.AddComponent<Text>();
            t.font = font; t.fontSize = size; t.color = color;
            var rt = t.rectTransform;
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0f, 1f);
            rt.anchoredPosition = pos;
            rt.sizeDelta = new Vector2(420f, 36f);
            return t;
        }

        static RectTransform Box(Transform parent, Vector2 pos, Vector2 size, Color color, Vector2 anchor)
        {
            var go = new GameObject("Box");
            go.transform.SetParent(parent, false);
            go.AddComponent<Image>().color = color;
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            return rt;
        }

        void LateUpdate()
        {
            bool show = ship != null && (boarding == null || boarding.Aboard);
            if (root.activeSelf != show) root.SetActive(show);
            if (!show) return;

            int a = Mathf.Clamp(Mathf.RoundToInt(ship.Body.position.y - SideShip.SkidDrop - datumY), SignedMin, 4000);
            if (a != lastAlt) { lastAlt = a; alt.text = signed[a - SignedMin]; }
            int v = Mathf.Clamp(Mathf.RoundToInt(ship.Body.linearVelocity.y), SignedMin, 4000);
            if (v != lastVs) { lastVs = v; vs.text = signed[v - SignedMin]; }
            int f = Mathf.Clamp(Mathf.CeilToInt(ship.Fuel), 0, 4000);
            if (f != lastFuel) { lastFuel = f; fuel.text = signed[f - SignedMin]; }
            int t = Mathf.Clamp(Mathf.RoundToInt(ship.Thrust / Mathf.Max(0.01f, ship.Gravity) * 10f), 0, 99);
            if (t != lastTwr) { lastTwr = t; twr.text = tenths[t]; }
            warn.enabled = ship.ThrustBelowGravity;

            float span = Mathf.Max(1f, worldHeight);
            escapeMarker.anchoredPosition = new Vector2(0f, escapeLineY / span * BarHeight);
            shipMarker.anchoredPosition = new Vector2(0f, Mathf.Clamp01(ship.Body.position.y / span) * BarHeight);
        }

        public void ConfigureFor(Meridian.Planets.PlanetConfig p)
        {
            datumY = p.datumY; escapeLineY = p.EscapeLineY; worldHeight = p.worldHeight;
        }
    }
}
