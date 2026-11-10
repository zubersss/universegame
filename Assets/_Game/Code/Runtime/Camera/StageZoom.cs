using UnityEngine;

namespace Meridian.CameraRig
{
    /// <summary>
    /// U-213 (3) (D-202 (3)): the close camera, behind a flag (off: the shipped frame, 64 px a metre everywhere). On, the
    /// surveyor on foot at the surface is framed at SurfacePxPerMetre (96; 128 for the closer trial) and the frame eases back
    /// to the shipped 64 px a metre underground: 3 m or more under the ground's own surface, or under a roof of ground (a dug
    /// room, a tunnel). Never a cut: StageCamera eases the frame's share over about a second. The HUD, the hint cards and the
    /// reticle's marks keep their size on the screen. The numbers and the rule are here, pure; CameraFollow reads the world.
    /// </summary>
    public static class StageZoom
    {
        /// <summary>The switch a built player takes: "-meridianCloseCamera" (96 px a metre) or "-meridianCloseCamera 128".</summary>
        public const string Switch = "-meridianCloseCamera";

        /// <summary>The flag. Off unless the player was started with the switch (tests and captures set it and put it back).</summary>
        public static bool Enabled;

        /// <summary>The shipped frame's scale (SheetClock.PixelsPerUnit: 1080 px = 16.875 m), kept underground.</summary>
        public const float UndergroundPxPerMetre = 64f;
        public const float DefaultSurfacePxPerMetre = 96f, MinSurfacePxPerMetre = 64f, MaxSurfacePxPerMetre = 160f;
        /// <summary>Px a metre on foot at the surface while the flag is on.</summary>
        public static float SurfacePxPerMetre = DefaultSurfacePxPerMetre;

        /// <summary>Underground from this depth under the surface (m); back at the surface above LeaveDepthM (no flutter on the edge).</summary>
        public const float UndergroundDepthM = 3f, LeaveDepthM = 2.5f;
        /// <summary>A roof of ground this near over the head (m) is a room or a tunnel: underground at any depth.</summary>
        public const float RoofScanM = 6f;
        /// <summary>The frame's share eases with this SmoothDamp time: within 2 % of the way after about 1 s.</summary>
        public const float EaseTime = 0.34f;
        /// <summary>The world is asked (the depth, the roof) once in this many frames; the ease runs every frame.</summary>
        public const int CheckEveryFrames = 6;

        /// <summary>The frame's share of the shipped frame at `pxPerMetre`: 64 / 96 = 2/3 (16.875 m becomes 11.25 m), 64 / 128 = 1/2. Pure.</summary>
        public static float Share(float pxPerMetre) =>
            UndergroundPxPerMetre / Mathf.Clamp(pxPerMetre, MinSurfacePxPerMetre, MaxSurfacePxPerMetre);

        /// <summary>The share on foot at the surface now (1 with the flag off).</summary>
        public static float SurfaceShare => Enabled ? Share(SurfacePxPerMetre) : 1f;

        /// <summary>Whether the surveyor counts as underground: under a roof of ground at any depth, else by depth with a half metre of
        /// hysteresis (in at UndergroundDepthM, out above LeaveDepthM). Pure.</summary>
        public static bool Underground(bool was, float depthM, bool roofed) =>
            roofed || depthM >= (was ? LeaveDepthM : UndergroundDepthM);

        /// <summary>The share a frame is to ease toward: 1 underground, the surface share above. Pure.</summary>
        public static float GoalShare(bool underground) => underground ? 1f : SurfaceShare;

        /// <summary>Reads the switch from a command line (the player's own at boot; a test's). Returns whether it was there; `pxPerMetre`
        /// is the number after it when one follows (else the default). Pure.</summary>
        public static bool ReadSwitch(string[] args, out float pxPerMetre)
        {
            pxPerMetre = DefaultSurfacePxPerMetre;
            if (args == null) return false;
            int i = System.Array.IndexOf(args, Switch);
            if (i < 0) return false;
            if (i + 1 < args.Length && float.TryParse(args[i + 1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float asked)
                && asked >= MinSurfacePxPerMetre && asked <= MaxSurfacePxPerMetre) pxPerMetre = asked;
            return true;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Boot()
        {
            // a fresh process (and the Editor's play mode with domain reload off): the flag is what the command line says
            Enabled = ReadSwitch(System.Environment.GetCommandLineArgs(), out float asked);
            SurfacePxPerMetre = asked;
        }
    }
}
