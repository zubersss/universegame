using UnityEngine;

namespace Meridian.Rig
{
    /// <summary>
    /// The Rig's four modules (Bible §6/§8 v4), switched with 1–4 or Q/E. D-087: slot 2 was the Lance (archived);
    /// it is the Grapple now, which does nothing until its own task lands (Bible: M4).
    /// </summary>
    public enum RigModule { Beam = 1, Grapple = 2, Survey = 3, Builder = 4 }

    /// <summary>Per-module art and geometry (B-037 hand-off, D-041).</summary>
    public static class RigModules
    {
        public const int Count = 4;

        /// <summary>Tool sprite (pivot [0.375, 0.5]: the grip sits in the surveyor's hand).</summary>
        public static string ArtKey(RigModule m) => m switch
        {
            RigModule.Beam => "props/rig/beam",
            RigModule.Grapple => "props/rig/grapple",
            RigModule.Survey => "props/rig/survey",
            _ => "props/rig/builder",
        };

        /// <summary>The key the tool view loads: each module's own (U-183: B-205's props/rig/grapple replaced the v2 Lance stand-in).</summary>
        public static string LoadKey(RigModule m) => ArtKey(m);

        /// <summary>Muzzle offset from the grip in the tool's own space (m, tool pointing +x).</summary>
        public static Vector2 Muzzle(RigModule m) => m switch
        {
            RigModule.Beam => new Vector2(0.47f, 0.03f),
            RigModule.Grapple => new Vector2(0.52f, 0.035f),
            RigModule.Survey => new Vector2(0.30f, 0.06f),
            _ => new Vector2(0.44f, 0.03f),
        };

        public static RigModule Next(RigModule m, int step)
        {
            int i = ((int)m - 1 + step) % Count;
            if (i < 0) i += Count;
            return (RigModule)(i + 1);
        }
    }
}
