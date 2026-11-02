using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>Where the surveyor is, as far as the hazards care (U-049).</summary>
    public struct HazardContext
    {
        public PlanetId planet;
        /// <summary>0 midnight … 0.5 noon (DayNightMath).</summary>
        public float localTime;
        /// <summary>Weather's Cryo bonus (Mars dust storm +1).</summary>
        public int stormCryo;
        /// <summary>Earth: in the tundra biome.</summary>
        public bool tundra;
        /// <summary>Mars: inside a lava tube (Radiation 0, Bible §7.2).</summary>
        public bool lavaTube;
        /// <summary>Rock overhead (no open sky): shelters from a flare.</summary>
        public bool underground;
        /// <summary>Inside a flare shelter.</summary>
        public bool sheltered;
        /// <summary>Mercury: day side, twilight band or night side.</summary>
        public MercuryZone mercury;
        /// <summary>Mercury: a solar flare is under way.</summary>
        public bool flare;
        /// <summary>World height (Venus: the hazards rise below the cloud deck).</summary>
        public float y;
    }

    /// <summary>
    /// U-049 hazard tables (Bible §7, D-032, D-048): each hazard's raw level (0–3, a flare 4) for a place.
    /// Pure, no allocation (the caller passes the array). The giants read GiantBands (U-068).
    /// </summary>
    public static class HazardTable
    {
        /// <summary>Venus (Bible §7.4): the habitable deck sits at y 770 ± 60; below 650 Thermal and Pressure rise to 3 by the surface (Datum 320); the acid rain line is y 600.</summary>
        public const float VenusHazardTop = 650f, VenusSurface = 320f, VenusAcidRain = 600f;

        public static void Levels(in HazardContext c, int[] levels)
        {
            for (int i = 0; i < levels.Length; i++) levels[i] = 0;
            switch (c.planet)
            {
                case PlanetId.Earth:
                    levels[(int)HazardKind.Cryo] = Cryo.Level(c.planet, c.localTime, c.stormCryo, c.tundra);
                    break;

                case PlanetId.Mars:
                    levels[(int)HazardKind.Cryo] = Cryo.Level(c.planet, c.localTime, c.stormCryo);
                    levels[(int)HazardKind.Pressure] = 1;                       // thin air: suit required
                    levels[(int)HazardKind.Radiation] = c.lavaTube ? 0 : 1;     // lava tubes are natural shelters
                    break;

                case PlanetId.Mercury:
                    switch (c.mercury)
                    {
                        case MercuryZone.Day: levels[(int)HazardKind.Thermal] = 3; break;
                        case MercuryZone.Night: levels[(int)HazardKind.Cryo] = 3; break;
                        default: levels[(int)HazardKind.Thermal] = 1; levels[(int)HazardKind.Cryo] = 1; break; // the band still bites
                    }
                    bool shielded = c.sheltered || c.underground;
                    levels[(int)HazardKind.Radiation] = 2;                          // always (§7.3): no field, no air
                    // D-048: a flare is Radiation 4 in the open; shadow (night side), rock or a shelter stop it.
                    if (c.flare && !shielded && c.mercury != MercuryZone.Night) levels[(int)HazardKind.Radiation] = HazardRules.FlareLevel;
                    break;

                case PlanetId.Venus:
                    // Deck: acid haze everywhere (Toxic 1); below 650 the furnace rises toward the surface.
                    float down = Mathf.InverseLerp(VenusHazardTop, VenusSurface, c.y);
                    int furnace = c.y >= VenusHazardTop ? 0 : Mathf.Clamp(Mathf.CeilToInt(down * 3f), 1, 3);
                    levels[(int)HazardKind.Thermal] = furnace;
                    levels[(int)HazardKind.Pressure] = furnace;
                    levels[(int)HazardKind.Toxic] = c.y < VenusAcidRain ? 2 : 1;
                    break;

                case PlanetId.Jupiter:
                case PlanetId.Saturn:
                case PlanetId.Uranus:
                case PlanetId.Neptune:
                    GiantBands.For(c.planet, c.y, levels);                         // U-068: cloud-column bands
                    break;
            }
        }

        /// <summary>The worst hazard after protection: its kind and effective level (level 0 = none).</summary>
        public static int Worst(int[] levels, int[] protection, out HazardKind kind)
        {
            int worst = 0;
            kind = HazardKind.Cryo;
            for (int i = 0; i < levels.Length; i++)
            {
                int e = HazardRules.Effective(levels[i], protection[i]);
                if (e > worst) { worst = e; kind = (HazardKind)i; }
            }
            return worst;
        }
    }
}
