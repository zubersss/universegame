using Meridian.Planets;
using UnityEngine;

namespace Meridian.Planet.Lighting
{
    /// <summary>
    /// Day/night lighting values (U-025, Bible §3 day lengths, §9 sunlight). Pure math: no allocation.
    /// Local time t in 0..1: 0 midnight, 0.25 dawn, 0.5 noon, 0.75 dusk. The Sun crosses the side view
    /// from the left horizon (dawn) through straight up (noon) to the right horizon (dusk).
    /// </summary>
    public static class DayNightMath
    {
        /// <summary>The game clock starts at 0; a new game begins at 08:00 local, not at midnight.</summary>
        public const float StartOffset = 1f / 3f;

        /// <summary>Global (ambient) light at noon and at midnight, as a share of the planet's sunlight.</summary>
        public const float DayAmbient = 0.35f;
        /// <summary>Night ambient level (absolute): dark but readable until the player lamp exists (M3).</summary>
        public const float NightAmbient = 0.16f;

        /// <summary>Bible §9: sunlight intensity (clamped) per planet.</summary>
        public static float Sunlight(PlanetId p) => p switch
        {
            PlanetId.Mercury => 1.6f,
            PlanetId.Venus => 1.2f,
            PlanetId.Earth => 1.0f,
            PlanetId.Mars => 0.75f,
            PlanetId.Jupiter => 0.45f,
            PlanetId.Saturn => 0.35f,
            PlanetId.Uranus => 0.25f,
            PlanetId.Neptune => 0.2f,
            _ => 1f,
        };

        public static float LocalTime(float dayFraction) => Mathf.Repeat(dayFraction + StartOffset, 1f);

        /// <summary>Sun elevation as sin of its angle above the horizon: −1 midnight, 0 dawn/dusk, +1 noon.</summary>
        public static float Elevation(float t) => Mathf.Sin(2f * Mathf.PI * (t - 0.25f));

        /// <summary>Unit direction from the view toward the Sun (x: −1 dawn side, +1 dusk side).</summary>
        public static Vector2 SunDirection(float t)
        {
            float a = 2f * Mathf.PI * (t - 0.25f);
            return new Vector2(-Mathf.Cos(a), Mathf.Sin(a));
        }

        /// <summary>0 at night, 1 in full day; the change happens around the horizon (civil twilight).</summary>
        public static float Daylight(float t) => Smooth(-0.12f, 0.2f, Elevation(t));

        /// <summary>1 near the horizon in daylight, 0 high in the sky: drives sunrise/sunset color.</summary>
        public static float Twilight(float t) => (1f - Smooth(0.05f, 0.4f, Elevation(t))) * Smooth(-0.12f, 0.02f, Elevation(t));

        /// <summary>Far (Sun) light intensity: the §9 value at noon, 0 below the horizon.</summary>
        public static float SunIntensity(PlanetId p, float t) => Sunlight(p) * Smooth(-0.05f, 0.15f, Elevation(t));

        /// <summary>Global light intensity: DayAmbient × sunlight by day, NightAmbient at night.</summary>
        public static float AmbientIntensity(PlanetId p, float t) => Mathf.Lerp(NightAmbient, DayAmbient * Sunlight(p), Daylight(t));

        public static Color SunColor(PlanetId p, float t) => Color.Lerp(NoonSun(p), TwilightSun(p), Twilight(t));

        public static Color AmbientColor(PlanetId p, float t)
        {
            var day = Color.Lerp(DayFill(p), TwilightSun(p), 0.5f * Twilight(t));
            return Color.Lerp(NightFill, day, Daylight(t));
        }

        /// <summary>Multiplier on the sky color and the backdrop layers.</summary>
        public static Color SkyTint(PlanetId p, float t)
        {
            var day = Color.Lerp(Color.white, TwilightSun(p), 0.45f * Twilight(t));
            return Color.Lerp(NightSky, day, Daylight(t));
        }

        static readonly Color NightFill = new Color(0.55f, 0.65f, 1f);
        static readonly Color NightSky = new Color(0.1f, 0.12f, 0.2f);

        static Color NoonSun(PlanetId p) => p switch
        {
            PlanetId.Mars => new Color(1f, 0.93f, 0.84f),
            PlanetId.Venus => new Color(1f, 0.9f, 0.7f),
            PlanetId.Jupiter or PlanetId.Saturn => new Color(1f, 0.96f, 0.86f),
            _ => new Color(1f, 0.98f, 0.95f),
        };

        /// <summary>Low-sun color. Mars sunsets are blue (fine dust scatters blue forward), Earth's are orange.</summary>
        static Color TwilightSun(PlanetId p) => p switch
        {
            PlanetId.Mars => new Color(0.6f, 0.75f, 1f),
            PlanetId.Uranus or PlanetId.Neptune => new Color(0.7f, 0.85f, 1f),
            _ => new Color(1f, 0.58f, 0.32f),
        };

        static Color DayFill(PlanetId p) => p switch
        {
            PlanetId.Mars => new Color(1f, 0.86f, 0.72f),
            PlanetId.Venus => new Color(1f, 0.88f, 0.66f),
            _ => new Color(0.85f, 0.9f, 1f),
        };

        static float Smooth(float a, float b, float x)
        {
            float k = Mathf.Clamp01((x - a) / (b - a));
            return k * k * (3f - 2f * k);
        }
    }
}
