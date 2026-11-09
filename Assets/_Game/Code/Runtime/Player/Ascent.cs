using System.Collections.Generic;
using Meridian.Mining;
using Meridian.Progress;
using UnityEngine;

namespace Meridian.Player
{
    /// <summary>U-176: what the surveyor climbs: a Builder ladder (climb_ladder) or the winch's line (reel_up).</summary>
    public enum ClimbKind { None, Ladder, Winch }

    /// <summary>U-176: a column the surveyor can climb: its centre x, the feet's lowest and highest heights on it, its speed (m/s,
    /// before the pack's load) and how far the body stands beside it (B-210's side_b sockets: the ladder in front, the hands on the line).</summary>
    public struct ClimbSpot
    {
        public ClimbKind kind;
        public float x, bottom, top, speed, beside;
    }

    /// <summary>U-176: a source of climb columns (the ladders, the winch).</summary>
    public interface IClimbSource
    {
        /// <summary>The column the body at `feet` can hold now (within reach of it), if any.</summary>
        bool Find(Vector2 feet, out ClimbSpot spot);
    }

    /// <summary>
    /// U-176 (Bible 5.2 §8.1, D1_TABLES §4 "Climbing"): the ways back up. The climb columns' registry (PlayerController asks it while W / S
    /// is held) and the tables' numbers as pure maths: each way's speed and its time over a climb, the pack's load factor on every one.
    /// </summary>
    public static class Ascent
    {
        static readonly List<IClimbSource> sources = new List<IClimbSource>();

        public static void Register(IClimbSource s) { if (s != null && !sources.Contains(s)) sources.Add(s); }
        public static void Unregister(IClimbSource s) => sources.Remove(s);

        public static bool Find(Vector2 feet, out ClimbSpot spot)
        {
            for (int i = 0; i < sources.Count; i++)
                if (sources[i] != null && sources[i].Find(feet, out spot)) return true;
            spot = default;
            return false;
        }

        static D1Tables.AscentTable T => D1Tables.Current.ascent;

        /// <summary>The ladder's climb (m/s) with the Climb stat (asc_climb_1 ×1.3), before the load.</summary>
        public static float LadderSpeed => T.ladderClimb * SkillStats.ClimbSpeed;
        /// <summary>The Grapple's reel (m/s) with the reel stat (asc_grapple_2 ×1.5, _3 ×2), before the load.</summary>
        public static float ReelSpeed => T.grappleReel * SkillStats.ReelSpeed;
        /// <summary>The winch's ride (m/s), before the load.</summary>
        public static float WinchSpeed => T.winchSpeed;
        public static float HookSpeed => T.hookSpeed;
        public static float RecallSeconds => T.recallSeconds;

        /// <summary>The reel stops this far short of the hook (m): the hands hang under it.</summary>
        public const float ReelStop = 0.9f;
        /// <summary>The line's end in the hands, above the feet (m; B-210's reel socket is 1.0 to 1.86 m up over reel_up).</summary>
        public const float HandsUp = 1.4f;

        /// <summary>Seconds up `metres` of ladder (or the winch's line) at `speed` m/s under the load factor.</summary>
        public static float ColumnSeconds(float metres, float speed, float load) => metres / Mathf.Max(0.01f, speed * load);

        /// <summary>Seconds up `metres` by the Grapple: hops of (line − the reel's stop), each the hook's flight out plus the reel.</summary>
        public static float GrappleSeconds(float metres, float lineM, float reel, float hook, float load)
        {
            float hop = Mathf.Max(0.5f, lineM - ReelStop);
            int hops = Mathf.CeilToInt(metres / hop);
            return metres / Mathf.Max(0.01f, reel * load) + hops * lineM / Mathf.Max(0.01f, hook);
        }
    }
}
