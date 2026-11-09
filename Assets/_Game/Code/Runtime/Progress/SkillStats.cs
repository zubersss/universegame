using System.Collections.Generic;
using Meridian.Core;
using Meridian.Mining;
using UnityEngine;

namespace Meridian.Progress
{
    /// <summary>
    /// U-175 (D1_TABLES §5, LEAD's stacking rule 19:0x): the Skill Tree's stats from the bought nodes. "+" amounts add up on the base; a "×"
    /// never compounds with another "×" on the same stat: the best bought one applies (the largest over 1, the smallest under 1), onto the
    /// additive total; set values take the best bought (the largest; "min" stats the smallest); flags are on once bought. Then the expedition
    /// multiplier (1 + step × (n − 1), D-175) on every stat it covers. Recomputed when the bought set changes, read cheaply every frame.
    /// </summary>
    public static class SkillStats
    {
        static readonly Dictionary<string, float> adds = new Dictionary<string, float>(), muls = new Dictionary<string, float>(),
            sets = new Dictionary<string, float>(), mins = new Dictionary<string, float>();
        static readonly HashSet<string> flags = new HashSet<string>();
        static float expedition = 1f;

        /// <summary>The expedition factor (D-175): 1 for the first expedition, +0.25 each New Expedition.</summary>
        public static float ExpeditionFactor => expedition;

        /// <summary>Rebuilds the stats from the state's bought nodes and expedition.</summary>
        /// <summary>U-183: bumped on every recompute, so views re-read the chain levels only when the tree changed.</summary>
        public static int Version { get; private set; }

        public static void Recompute(GameState s)
        {
            Version++;
            adds.Clear(); muls.Clear(); sets.Clear(); mins.Clear(); flags.Clear();
            var tree = SkillTree.Current;
            expedition = s != null ? 1f + tree.expeditionStep * Mathf.Max(0, s.expedition - 1) : 1f;
            if (s == null) return;
            foreach (var id in s.skillNodes)
            {
                var n = tree.Get(id);
                if (n == null) continue;
                foreach (var m in n.mods)
                {
                    switch (m.op)
                    {
                        case "add": adds[m.stat] = (adds.TryGetValue(m.stat, out var a) ? a : 0f) + m.value; break;
                        case "mul":
                            // The best bought ×: the one farthest from 1 in its own direction.
                            if (!muls.TryGetValue(m.stat, out var b) || (m.value >= 1f ? m.value > b : m.value < b)) muls[m.stat] = m.value;
                            break;
                        case "set": if (!sets.TryGetValue(m.stat, out var c) || m.value > c) sets[m.stat] = m.value; break;
                        case "min": if (!mins.TryGetValue(m.stat, out var d) || m.value < d) mins[m.stat] = m.value; break;
                        case "flag": flags.Add(m.stat); break;
                    }
                }
            }
        }

        /// <summary>Recomputes and pushes the stats into the systems that hold them (the pack, the dirt store, the thruster, the suit).</summary>
        public static void Apply(GameState s)
        {
            Recompute(s);
            if (s == null) return;
            s.ApplyD1();
            int mark = Mathf.RoundToInt(Value("thruster_mark", 1f));
            if (s.thrusterMark < mark) s.thrusterMark = mark;
            int suit = Mathf.RoundToInt(Value("suit_tier", 0f));
            if (s.suitTier < suit) s.suitTier = suit;
        }

        /// <summary>A stat's value from its base: (base + adds) × the best ×; a set / min value replaces the base; × the expedition factor
        /// where the tree says the stat is multiplied.</summary>
        public static float Value(string stat, float baseValue)
        {
            float v = baseValue;
            if (sets.TryGetValue(stat, out var set)) v = Mathf.Max(v, set);
            if (mins.TryGetValue(stat, out var min)) v = Mathf.Min(v, min);
            if (adds.TryGetValue(stat, out var add)) v += add;
            if (muls.TryGetValue(stat, out var mul)) v *= mul;
            return SkillTree.Current.Multiplied(stat) ? v * expedition : v;
        }

        public static bool Has(string flag) => flags.Contains(flag);

        // The stats the game reads (bases from the D1 tables or the systems they replace).
        public static float BeamPower => Value("beam_power", D1Tables.Current.beamPowerStart);
        public static float BrushRadius => Value("brush_radius", 0.9f);
        public static float PackKg => Value("pack_kg", D1Tables.Current.packLimitKg);
        public static int DirtStore => Mathf.RoundToInt(Value("dirt_store", D1Tables.Current.dirtStoreStart));
        public static float LoadK => Value("load_k", D1Tables.Current.loadK);
        public static float JetThrust => Value("jet_thrust", 1f);
        public static float JetPowerUse => Value("jet_power_use", 1f);
        public static float ClimbSpeed => Value("climb_speed", 1f);
        /// <summary>The Survey pulse's radius (m): the scanner's 8 m plus the tree's, all under the expedition factor (D-175).</summary>
        public static float ScanRadius => Value("scan_radius", 8f);
        public static float ScanDepthAdd => Value("scan_depth", 0f);
        public static float Oxygen => (1f + (adds.TryGetValue("oxygen", out var o) ? o : 0f)) * (muls.TryGetValue("oxygen_mul", out var om) ? om : 1f) * expedition;
        public static float FallDamageFactor => Mathf.Max(0f, 1f - Value("fall_damage_cut", 0f));
        public static float SafeFallM => Value("safe_fall_m", 0f);
        public static float WaystationBonus => Value("waystation_bonus", D1Tables.Current.waystationBonus);
        public static float GrappleM => Value("grapple_m", 0f);
        public static float ReelSpeed => Value("reel_speed", 1f);
        /// <summary>U-176: the metres one ladder placement fills (0: no ladders before asc_ladder_1) and the dirt each costs.</summary>
        public static float LadderM => Value("ladder_m", 0f);
        public static float LadderDirtPerM => Value("ladder_dirt_per_m", D1Tables.Current.ascent.ladderDirtPerM);
        /// <summary>U-176: hooks the Grapple can hold at once (asc_grapple_3: two, a second hook takes over without a drop).</summary>
        public static int GrappleAnchors => Mathf.Max(1, Mathf.RoundToInt(Value("grapple_anchors", 1f)));
        /// <summary>U-176: the steepest ground the surveyor stands on without sliding (degrees; asc_climb_1: 40).</summary>
        public static float NoSlideDeg => Value("no_slide_deg", D1Tables.Current.ascent.walkRampDeg);
        /// <summary>U-176: the winch line from the Surface Line (asc_winch) and the recall beacons a run (asc_recall).</summary>
        public static bool Winch => Has("winch");
        public static int RecallBeacons => Mathf.RoundToInt(Value("recall_beacons", 0f));
        public static float HoldKg => Value("hold_kg", 0f);
        public static float OreWeight => Value("ore_weight", 1f);
        public static int TierShift => Mathf.RoundToInt(Value("tier_shift", 0f));
    }
}
