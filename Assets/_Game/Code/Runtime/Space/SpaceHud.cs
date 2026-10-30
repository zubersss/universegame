using Meridian.Core;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.Space
{
    /// <summary>
    /// Minimal top-down HUD (speed, fuel, well indicator); the designed HUD comes with U-015.
    /// All readouts come from precomputed strings, so updating allocates nothing.
    /// </summary>
    public sealed class SpaceHud : MonoBehaviour
    {
        public SpaceShip ship;
        Text speed, fuel, well;
        static string[] numbers;      // "0".."400"
        static string[] tenths;       // "0.0".."99.9"
        int lastSpeed = -1, lastFuel = -1, lastPull = -1;
        string lastWellName;

        void Awake()
        {
            if (numbers == null)
            {
                numbers = new string[401];
                for (int i = 0; i < numbers.Length; i++) numbers[i] = i.ToString();
                tenths = new string[1000];
                for (int i = 0; i < tenths.Length; i++) tenths[i] = (i / 10f).ToString("0.0");
            }
            var canvasGo = new GameObject("HudCanvas");
            canvasGo.transform.SetParent(transform, false);
            var canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvasGo.AddComponent<CanvasScaler>().uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            Label(canvasGo.transform, "SPEED u/s", 0, font);
            speed = Value(canvasGo.transform, 0, font);
            Label(canvasGo.transform, "FUEL", 1, font);
            fuel = Value(canvasGo.transform, 1, font);
            Label(canvasGo.transform, "WELL u/s²", 2, font);
            well = Value(canvasGo.transform, 2, font);
        }

        static Text Make(Transform parent, int column, Font font, float y, int size)
        {
            var go = new GameObject("Text");
            go.transform.SetParent(parent, false);
            var t = go.AddComponent<Text>();
            t.font = font;
            t.fontSize = size;
            t.color = new Color(0.85f, 0.92f, 1f, 0.9f);
            var rt = t.rectTransform;
            rt.anchorMin = rt.anchorMax = new Vector2(0f, 1f);
            rt.pivot = new Vector2(0f, 1f);
            rt.anchoredPosition = new Vector2(24f + column * 220f, y);
            rt.sizeDelta = new Vector2(210f, 40f);
            return t;
        }

        static void Label(Transform p, string text, int column, Font font) => Make(p, column, font, -16f, 14).text = text;
        static Text Value(Transform p, int column, Font font) => Make(p, column, font, -34f, 26);

        void LateUpdate()
        {
            if (ship == null) return;
            int s = Mathf.Clamp(Mathf.RoundToInt(ship.Velocity.magnitude), 0, 400);
            if (s != lastSpeed) { lastSpeed = s; speed.text = numbers[s]; }

            var state = GameState.Instance;
            int f = state != null ? Mathf.Clamp(Mathf.CeilToInt(state.fuel), 0, 400) : 0;
            if (f != lastFuel) { lastFuel = f; fuel.text = numbers[f]; }

            int p = Mathf.Clamp(Mathf.RoundToInt(ship.LastPull.magnitude * 10f), 0, 999);
            string name = ship.InWellOf;
            if (p != lastPull || !ReferenceEquals(name, lastWellName))
            {
                lastPull = p; lastWellName = name;
                well.text = p == 0 ? "—" : tenths[p];
                well.color = p == 0 ? new Color(0.85f, 0.92f, 1f, 0.5f) : new Color(1f, 0.8f, 0.45f, 1f);
            }
        }
    }
}
