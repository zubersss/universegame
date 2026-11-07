using Meridian.Planets;

namespace Meridian.Ship
{
    /// <summary>
    /// U-065 ship marks (Bible §4.3) as data: Thruster Mk1/Mk2/Mk3 give 12 / 20 / 35 m/s² vertical (lateral 60%)
    /// and may launch only from the planets in the "Can launch from" row; Tank Mk1/Mk2/Mk3 hold 100 / 200 / 400
    /// units of Launch Fuel. Pure. Crafted upgrade items (thruster_mk2 … tank_mk3) install through Install.
    /// </summary>
    public static class ShipMarks
    {
        public const int MinMark = 1, MaxMark = 3;

        public static float Thrust(int mark) => Clamp(mark) switch { 3 => 35f, 2 => 20f, _ => 12f };

        public static float TankCapacity(int mark) => Clamp(mark) switch { 3 => 400f, 2 => 200f, _ => 100f };

        /// <summary>The lowest thruster mark the table lets launch from this planet (§4.3 "Can launch from").</summary>
        public static int MinThrusterToLaunch(PlanetId p) => p switch
        {
            PlanetId.Saturn => 2,
            PlanetId.Neptune => 2,
            PlanetId.Jupiter => 3,
            _ => 1, // Mercury, Venus, Earth, Mars, Uranus
        };

        public static bool CanLaunch(int thrusterMark, PlanetId p) => Clamp(thrusterMark) >= MinThrusterToLaunch(p);

        /// <summary>HUD lines, built once (no per-frame strings).</summary>
        public static readonly string[] CantLiftOff =
        {
            "", "THRUSTER MK1 CAN'T LIFT OFF HERE", "THRUSTER MK2 CAN'T LIFT OFF HERE", "THRUSTER MK3 CAN'T LIFT OFF HERE",
        };

        public enum Part { None, Thruster, Tank }

        /// <summary>Which part and mark an upgrade item installs (thruster_mk2, thruster_mk3, tank_mk2, tank_mk3).</summary>
        public static (Part part, int mark) UpgradeOf(string itemKey) => itemKey switch
        {
            "thruster_mk2" => (Part.Thruster, 2),
            "thruster_mk3" => (Part.Thruster, 3),
            "tank_mk2" => (Part.Tank, 2),
            "tank_mk3" => (Part.Tank, 3),
            _ => (Part.None, 0),
        };

        /// <summary>
        /// Installs an upgrade into the ship state if it is better than what's fitted: sets the mark (and the tank
        /// capacity; fuel stays). Returns false for a non-upgrade or a mark that isn't an improvement.
        /// </summary>
        public static bool Install(Meridian.Core.GameState state, string itemKey)
        {
            if (state == null) return false;
            var (part, mark) = UpgradeOf(itemKey);
            switch (part)
            {
                case Part.Thruster:
                    if (mark <= state.thrusterMark) return false;
                    state.thrusterMark = mark;
                    return true;
                case Part.Tank:
                    if (mark <= state.tankMark) return false;
                    state.tankMark = mark;
                    state.tankCapacity = TankCapacity(mark);
                    return true;
                default:
                    return false;
            }
        }

        static int Clamp(int m) => m < MinMark ? MinMark : m > MaxMark ? MaxMark : m;
    }
}
