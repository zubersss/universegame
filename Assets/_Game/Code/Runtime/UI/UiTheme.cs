using Meridian.Planets;
using UnityEngine;

namespace Meridian.UI
{
    /// <summary>
    /// Look of every HUD and menu (Bible §9: thin HUD, planet-tinted accents, monospace OFL
    /// numerals). Lives in UI/Resources so any HUD finds it without a scene reference.
    /// </summary>
    [CreateAssetMenu(menuName = "MERIDIAN/UI Theme", fileName = "UiTheme")]
    public sealed class UiTheme : ScriptableObject
    {
        public const string ResourceName = "UiTheme";

        public Font regular;   // JetBrains Mono Regular (OFL 1.1)
        public Font bold;      // JetBrains Mono Bold (OFL 1.1)
        public Color text = new Color(0.86f, 0.92f, 1f, 0.95f);
        public Color label = new Color(0.86f, 0.92f, 1f, 0.6f);
        public Color panel = new Color(0.03f, 0.05f, 0.08f, 0.82f);
        public Color barBack = new Color(1f, 1f, 1f, 0.12f);
        public Color warning = new Color(1f, 0.45f, 0.3f, 1f);
        public Color health = new Color(0.55f, 0.9f, 0.6f, 0.95f);
        public Color oxygen = new Color(0.55f, 0.8f, 1f, 0.95f);

        static UiTheme active;
        public static UiTheme Active
        {
            get
            {
                if (active == null) active = Resources.Load<UiTheme>(ResourceName);
                if (active == null) active = CreateInstance<UiTheme>(); // tests without the asset still get colors
                return active;
            }
        }

        public Font Regular => regular != null ? regular : Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        public Font Bold => bold != null ? bold : Regular;

        /// <summary>Planet-tinted accent (Bible §9 palettes).</summary>
        public static Color Accent(PlanetId? planet) => planet switch
        {
            PlanetId.Mercury => new Color(0.78f, 0.7f, 0.95f),
            PlanetId.Venus => new Color(1f, 0.82f, 0.55f),
            PlanetId.Earth => new Color(0.45f, 0.85f, 0.75f),
            PlanetId.Mars => new Color(0.95f, 0.55f, 0.35f),
            PlanetId.Jupiter => new Color(0.95f, 0.7f, 0.5f),
            PlanetId.Saturn => new Color(0.95f, 0.85f, 0.55f),
            PlanetId.Uranus => new Color(0.55f, 0.92f, 0.95f),
            PlanetId.Neptune => new Color(0.5f, 0.6f, 1f),
            _ => new Color(1f, 0.78f, 0.42f), // space: warm Sun
        };
    }
}
