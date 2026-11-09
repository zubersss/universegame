using System.Collections.Generic;
using Meridian.Core;

namespace Meridian.Rig
{
    /// <summary>
    /// U-183 (B-205; Bible 5.3 §8.1): the tools look like their upgrades. Each look's Mk from the Skill Tree's chain: the Beam by Dig power
    /// (dig_power_1 Mk2, _2 Mk3, _3 and _4 Mk4, _5 Mk5), the Grapple by its line (asc_grapple_1 Mk1, _2 Mk2, _3 Mk3), the jetpack by its
    /// upgrades (asc_jet_2 Mk2, asc_jet_3 Mk3; Mk1 the pack as drawn). Pure over the bought nodes.
    /// </summary>
    public static class RigLooks
    {
        /// <summary>U-193 (D-182): the dig slot's look: 0 the shovel until The Beam; then the Beam by Dig power, one node later than U-183's
        /// chain: dig_power_1 (The Beam) Mk1, _2 Mk2, _3 Mk3, _4 Mk4, _5 Mk5.</summary>
        public static int BeamMk(ICollection<string> bought)
        {
            if (bought == null) return 0;
            if (bought.Contains("dig_power_5")) return 5;
            if (bought.Contains("dig_power_4")) return 4;
            if (bought.Contains("dig_power_3")) return 3;
            if (bought.Contains("dig_power_2")) return 2;
            if (bought.Contains("dig_power_1")) return 1;
            return 0;
        }

        /// <summary>U-193: the shovel's sprite (B-226; the Beam Mk1 stands in until it is exported).</summary>
        public const string ShovelKey = "props/rig/shovel";

        public static int GrappleMk(ICollection<string> bought)
        {
            if (bought == null) return 1;
            if (bought.Contains("asc_grapple_3")) return 3;
            if (bought.Contains("asc_grapple_2")) return 2;
            return 1;
        }

        public static int JetpackMk(ICollection<string> bought)
        {
            if (bought == null) return 1;
            if (bought.Contains("asc_jet_3")) return 3;
            if (bought.Contains("asc_jet_2")) return 2;
            return 1;
        }

        public static int MkOf(RigModule m, ICollection<string> bought) =>
            m == RigModule.Beam ? BeamMk(bought) : m == RigModule.Grapple ? GrappleMk(bought) : 1;

        /// <summary>The tool's sprite key at a Mk: Mk1 the module's own (props/rig/beam = beam_mk1), else props/rig/beam_mk&lt;n&gt; /
        /// grapple_mk&lt;n&gt;. The archived v2 Lance is never a look (D-087).</summary>
        public static string ToolKey(RigModule m, int mk) =>
            m == RigModule.Beam && mk <= 0 ? ShovelKey
            : mk <= 1 || (m != RigModule.Beam && m != RigModule.Grapple) ? RigModules.ArtKey(m) : $"{RigModules.ArtKey(m)}_mk{mk}";

        /// <summary>The Beam's ray at a Mk (fx/beam_ray/mk&lt;n&gt;; the v2 base sheet is not used).</summary>
        public static string RayKey(int mk) => $"fx/beam_ray/mk{System.Math.Clamp(mk, 1, 5)}";

        /// <summary>The jetpack overlay at a Mk (null for Mk1: the pack as drawn).</summary>
        public static string JetpackKey(int mk) => mk >= 2 ? $"props/rig/jetpack_mk{System.Math.Min(mk, 3)}" : null;

        static readonly HashSet<string> none = new HashSet<string>();
        public static ICollection<string> Bought => GameState.Instance != null ? GameState.Instance.skillNodes : (ICollection<string>)none;
    }
}
