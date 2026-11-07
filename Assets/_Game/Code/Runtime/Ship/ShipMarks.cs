namespace Meridian.Ship
{
    /// <summary>
    /// U-065 ship marks (Bible §4.3 v4.1) as data: Thruster Mk1/Mk2/Mk3 give 12 / 20 / 35 m/s² along the rocket's up
    /// axis. U-107 (D-103): no fuel and no tanks; a thruster climbs wherever its acceleration exceeds the planet's g
    /// (times ClimbMargin), and that is the only limit. Pure. Crafted upgrade items (thruster_mk2, thruster_mk3)
    /// install through Install.
    /// </summary>
    public static class ShipMarks
    {
        public const int MinMark = 1, MaxMark = 3;
        /// <summary>
        /// Thrust-to-weight a thruster needs to count as climbing (1 = any thrust above g). D-103 makes thrust-to-weight
        /// the only limit; whether the §4.1 column (Saturn and Neptune on Mk2) needs a margin above 1 is with LEAD.
        /// </summary>
        public const float ClimbMargin = 1f;

        public static float Thrust(int mark) => Clamp(mark) switch { 3 => 35f, 2 => 20f, _ => 12f };

        /// <summary>True where this mark's thrust lifts the ship against `gravity` (m/s²).</summary>
        public static bool CanClimb(int thrusterMark, float gravity) => Thrust(thrusterMark) > gravity * ClimbMargin;

        /// <summary>The lowest thruster mark that climbs against `gravity`; MaxMark + 1 when none does.</summary>
        public static int MinThrusterToClimb(float gravity)
        {
            for (int m = MinMark; m <= MaxMark; m++) if (CanClimb(m, gravity)) return m;
            return MaxMark + 1;
        }

        /// <summary>HUD lines, built once (no per-frame strings): the §4.3 stranded warning.</summary>
        public static readonly string[] CantClimb =
        {
            "", "THRUSTER MK1 CAN'T CLIMB HERE", "THRUSTER MK2 CAN'T CLIMB HERE", "THRUSTER MK3 CAN'T CLIMB HERE",
        };

        public enum Part { None, Thruster }

        /// <summary>Which part and mark an upgrade item installs (thruster_mk2, thruster_mk3).</summary>
        public static (Part part, int mark) UpgradeOf(string itemKey) => itemKey switch
        {
            "thruster_mk2" => (Part.Thruster, 2),
            "thruster_mk3" => (Part.Thruster, 3),
            _ => (Part.None, 0),
        };

        /// <summary>Installs an upgrade if it is better than what's fitted. Returns false for a non-upgrade or no improvement.</summary>
        public static bool Install(Meridian.Core.GameState state, string itemKey)
        {
            if (state == null) return false;
            var (part, mark) = UpgradeOf(itemKey);
            if (part != Part.Thruster || mark <= state.thrusterMark) return false;
            state.thrusterMark = mark;
            return true;
        }

        static int Clamp(int m) => m < MinMark ? MinMark : m > MaxMark ? MaxMark : m;
    }
}
