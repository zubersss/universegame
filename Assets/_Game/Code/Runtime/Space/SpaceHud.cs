using Meridian.Core;
using Meridian.UI;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.Space
{
    /// <summary>
    /// Top-down HUD (U-011, styled in U-015): speed, fuel, and the Gravity Well indicator (which
    /// body pulls hardest, and how hard). Precomputed strings: updates allocate nothing.
    /// </summary>
    public sealed class SpaceHud : MonoBehaviour
    {
        public SpaceShip ship;

        public Text Speed { get; private set; }
        public Text Fuel { get; private set; }
        public Text Well { get; private set; }
        public Text WellName { get; private set; }

        static UiKit.NumberStrings numbers, tenths;
        int lastSpeed = -1, lastFuel = -1, lastPull = -1;
        string lastWellName = "";

        void Awake()
        {
            numbers ??= new UiKit.NumberStrings(0, 400);
            tenths ??= new UiKit.NumberStrings(0, 999, "0.0", 10f);
            var theme = UiTheme.Active;
            var canvas = UiKit.Canvas(transform, "SpaceHudCanvas", 100);
            var root = canvas.transform;
            var tl = new Vector2(0f, 1f);
            UiKit.Panel(root, "Accent", tl, new Vector2(24f, -20f), new Vector2(560f, 2f), UiTheme.Accent(null));
            Label(root, "SPEED u/s", 0);
            Speed = Value(root, 0);
            Label(root, "FUEL", 1);
            Fuel = Value(root, 1);
            Label(root, "WELL u/s²", 2);
            Well = Value(root, 2);
            WellName = UiKit.Text(root, "WellName", tl, new Vector2(24f + 2 * 200f, -98f), new Vector2(180f, 20f), 14, false, TextAnchor.MiddleLeft, theme.label);
        }

        static void Label(Transform root, string text, int column) =>
            UiKit.Text(root, text, new Vector2(0f, 1f), new Vector2(24f + column * 200f, -36f), new Vector2(180f, 18f), 13,
                false, TextAnchor.MiddleLeft, UiTheme.Active.label).text = text;

        static Text Value(Transform root, int column) =>
            UiKit.Text(root, "Value", new Vector2(0f, 1f), new Vector2(24f + column * 200f, -66f), new Vector2(180f, 34f), 28);

        void LateUpdate()
        {
            if (ship == null) return;
            int s = Mathf.RoundToInt(ship.Velocity.magnitude);
            if (s != lastSpeed) { lastSpeed = s; Speed.text = numbers[s]; }

            var state = GameState.Instance;
            int f = state != null ? Mathf.CeilToInt(state.fuel) : 0;
            if (f != lastFuel) { lastFuel = f; Fuel.text = numbers[f]; }

            int p = Mathf.RoundToInt(ship.LastPull.magnitude * 10f);
            string name = ship.InWellOf ?? "";
            if (p != lastPull || !ReferenceEquals(name, lastWellName))
            {
                lastPull = p; lastWellName = name;
                bool inWell = p > 0;
                Well.text = inWell ? tenths[p] : "—";
                Well.color = inWell ? UiTheme.Active.warning : UiTheme.Active.label;
                WellName.text = name; // body names are interned constants: no allocation
            }
        }
    }
}
