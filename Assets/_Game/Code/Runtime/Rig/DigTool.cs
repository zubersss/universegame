namespace Meridian.Rig
{
    /// <summary>
    /// U-193 (D-182, the owner 11-09): what the surveyor digs with. A new surveyor digs with the shovel (D1_TABLES §1: a slower stroke, a
    /// short reach); The Beam (dig_power_1, its "beam" flag) swaps it for the Beam for good; a New Expedition starts with the shovel again.
    /// Read it from Progress.SkillStats.DigTool (or RigTools.Tool). The dig slot stays RigModule.Beam whichever tool it holds.
    /// </summary>
    public enum DigTool { Shovel, Beam }
}
