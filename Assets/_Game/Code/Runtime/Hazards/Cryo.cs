using Meridian.Planet.Lighting;
using Meridian.Planets;
using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>
    /// Cryo level (Bible §7, 0–3 scale) by planet, biome and time: Earth 0, 1 in tundra at night (§7.1);
    /// Mars 1 by day, 2 at night (§7.2); weather adds (Mars dust storm +1, U-026). Clamped 0..3.
    /// Other planets join with their designs (M3/M4).
    /// </summary>
    public static class Cryo
    {
        public const int Max = 3;

        public static bool IsNight(float localTime) => DayNightMath.Daylight(localTime) < 0.5f;

        /// <param name="localTime">0 midnight … 0.5 noon (DayNightMath).</param>
        /// <param name="tundra">Earth: standing in tundra (snow ground until biomes exist).</param>
        public static int Level(PlanetId planet, float localTime, int weatherBonus, bool tundra = false)
        {
            bool night = IsNight(localTime);
            int level = planet switch
            {
                PlanetId.Mars => night ? 2 : 1,
                PlanetId.Earth => tundra && night ? 1 : 0,
                _ => 0,
            };
            return Mathf.Clamp(level + weatherBonus, 0, Max);
        }
    }
}
