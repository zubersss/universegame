using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>Bible §7 hazards, each on a 0–3 scale. Cryo is live in M2; the others plug in with M3/M4.</summary>
    public enum HazardKind { Thermal, Cryo, Radiation, Toxic, Pressure }

    /// <summary>
    /// U-029: what a hazard level does to an unprotected surveyor. The suit's integrity (0–100) drains
    /// first; at 0 the same rate comes off health. Level 3 is lethal in 30 s from a full suit and full
    /// health (Bible §7: "3 lethal within 30 s unprotected"). Warmth (ship, lit shelter) cancels the
    /// hazard and recharges the suit. A protection module of tier k lowers the level by k (M3).
    /// </summary>
    public static class HazardRules
    {
        public const int Kinds = 5;
        public const float SuitMax = 100f;
        /// <summary>Bible §7: level 3 kills within this long, unprotected.</summary>
        public const float LethalSeconds = 30f;
        /// <summary>Designed time to death at level 3 from full suit and health: inside the 30 s with a margin for frame steps.</summary>
        public const float Level3Seconds = 29.5f;
        public const float WarmRecharge = 5f;

        /// <summary>Points per second off the suit (then off health) at an effective level.</summary>
        public static float DrainPerSecond(int level) => level switch
        {
            <= 0 => 0f,
            1 => 0.4f,                                    // a cold night: the suit lasts ~4 min
            2 => 1.5f,                                    // Mars night: ~1 min of suit
            _ => (SuitMax + 100f) / Level3Seconds,        // 6.78/s: suit + 100 health gone in 29.5 s
        };

        public static int Effective(int level, int protectionTier) => Mathf.Clamp(level - protectionTier, 0, 3);
    }
}
