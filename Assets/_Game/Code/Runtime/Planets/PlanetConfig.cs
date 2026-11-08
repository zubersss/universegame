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

        /// <summary>U-107 (D-103): the lowest thruster mark that climbs here (no launch fuel exists; thrust-to-weight is the only limit).</summary>
        public int MinThrusterToClimb => Meridian.Ship.ShipMarks.MinThrusterToClimb(gravity);

        /// <summary>U-149 (D-158 (3)): the air's density at the Datum relative to Earth's, the drag's ρ_surface. Placeholders tuned on the
        /// captures: Mercury 0 (no air), Mars 0.15, Earth 1, Venus 3, the four giants 1.5.</summary>
        public static float SurfaceAirDensityFor(PlanetId id) => id switch
        {
            PlanetId.Mercury => 0f,
            PlanetId.Mars => 0.15f,
            PlanetId.Earth => 1f,
            PlanetId.Venus => 3f,
            _ => 1.5f,
        };

        public float SurfaceAirDensity => SurfaceAirDensityFor(id);

        /// <summary>U-149: the air's density at world height y: ρ_surface·(1 − h/H)² with h above the Datum, 0 at and above the Escape Line.</summary>
        public float AirDensityAt(float y) => Meridian.Ship.RocketFlight.AirDensity(SurfaceAirDensity, y - datumY, escapeAltitude);

        /// <summary>U-150 (D-158 (4)): the game's speed of sound (m/s), 0 without air. Placeholders tuned on the pure climb (spool + drag) so a
        /// full-thrust upright climb crosses it before the Escape Line where ρ ≥ 0.1: Earth Mk1 at ~59 % of the way; Mars Mk1 and Venus Mk1
        /// (from the station deck) low, where their thin dense layer still is; Jupiter Mk3, Saturn Mk2, Uranus Mk1, Neptune Mk2 near half way.</summary>
        public static float SpeedOfSoundFor(PlanetId id) => id switch
        {
            PlanetId.Mercury => 0f,
            PlanetId.Venus => 12f,
            PlanetId.Earth => 30f,
            PlanetId.Mars => 16f,
            PlanetId.Jupiter => 80f,
            PlanetId.Saturn => 70f,
            PlanetId.Uranus => 40f,
            PlanetId.Neptune => 65f,
            _ => 0f,
        };

        public float SpeedOfSound => SpeedOfSoundFor(id);
    }
}
