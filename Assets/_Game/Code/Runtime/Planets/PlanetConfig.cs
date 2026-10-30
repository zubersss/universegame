using System;
using UnityEngine;

namespace Meridian.Planets
{
    public enum PlanetId { Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune }

    public enum WorldType { Solid, CloudColumn }

    /// <summary>
    /// Every per-planet number from Bible §3, §4.1, §4.2 and §5.1. Systems read these values;
    /// nothing else hard-codes a planet number.
    /// </summary>
    [CreateAssetMenu(menuName = "MERIDIAN/Planet Config", fileName = "PlanetConfig")]
    public sealed class PlanetConfig : ScriptableObject
    {
        public const float EarthGravity = 9.81f;

        [Header("Identity")]
        public PlanetId id;
        public WorldType worldType;
        public bool landable = true;

        [Header("Physics (Bible §4.1, §4.2)")]
        [Tooltip("Surface gravity, m/s².")] public float gravity;
        [Tooltip("Escape velocity, km/s.")] public float escapeVelocityKms;
        [Tooltip("Terminal fall speed on the play layer, m/s.")] public float terminalVelocity;

        [Header("Side-view world (Bible §5.1), tiles = meters")]
        public int worldWidth;
        public int worldHeight;
        public int datumY;
        public int escapeAltitude;
        [Tooltip("-1 when the planet has no Crush Line.")] public int crushLineY = -1;

        [Header("Time (Bible §3)")]
        [Tooltip("Real minutes per in-game day; 0 = special rule (Mercury terminator).")]
        public float dayLengthRealMinutes;

        [Header("Top-down (Bible §3)")]
        public float orbitRadius;
        public float visualRadius;

        public float GravityRatio => gravity / EarthGravity;
        public Vector2 GravityVector => new Vector2(0f, -gravity);
        public int EscapeLineY => datumY + escapeAltitude;
        public bool HasCrushLine => crushLineY >= 0;
        public float AtmosphereRingRadius => 1.2f * visualRadius;
        public float GravityWellRadius => 4f * visualRadius;

        /// <summary>Launch fuel cost in units of a 100-unit tank = round(1.5 × v_esc) (Bible §4.1).</summary>
        public int LaunchFuelCost => LaunchFuelFor(escapeVelocityKms);

        public static int LaunchFuelFor(float escapeVelocityKms) =>
            (int)Math.Round(1.5 * escapeVelocityKms, MidpointRounding.AwayFromZero);
    }
}
