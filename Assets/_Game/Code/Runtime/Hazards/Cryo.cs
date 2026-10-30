using Meridian.Planet.Lighting;
using Meridian.Planets;
using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>
    /// Cryo level (Bible §7, 0–3 scale). Started by U-026 for the dust storm's +1; U-029 adds biomes
    /// (Earth tundra night 1), suit drain, shelter warmth and the HUD meter on top of this table.
    /// </summary>
    public static class Cryo
    {
        public const int Max = 3;

        /// <summary>Base level by planet and local time (0 midnight … 0.5 noon), plus weather (dust storm +1), clamped 0..3.</summary>
        public static int Level(PlanetId planet, float localTime, int weatherBonus)
        {
            bool night = DayNightMath.Daylight(localTime) < 0.5f;
            int level = planet switch
            {
                PlanetId.Mars => night ? 2 : 1,
                _ => 0,
            };
            return Mathf.Clamp(level + weatherBonus, 0, Max);
        }
    }
}
