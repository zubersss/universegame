using Meridian.Terrain;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-120 (D-129 / D-136): the cold first boot spent ~5 s of its 6–8 s settling the terrain under the 1 ms streaming budget with
    /// nothing on screen (perf_2026-11-07.md: "terrain settled at 5.69 s; still loading: none"). The first fill after Begin runs under
    /// a wide per-frame window behind the boot cover or the entry fade; the streaming budget rules once the streamer has settled.
    /// </summary>
    public class FirstFillTests
    {
        [Test]
        public void TheFirstFillTakesAWideWindowAndStreamingKeepsItsBudget()
        {
            Assert.AreEqual(TerrainStreamer.FirstFillPlanMs, TerrainStreamer.PlanMs(false), 1e-9, "before the first settle: the wide window");
            Assert.AreEqual(TerrainConstants.ApplyPlanMs, TerrainStreamer.PlanMs(true), 1e-9, "after it: the streaming budget (D-019: ≤ 2 ms in 99 % of frames)");
            Assert.Greater(TerrainStreamer.FirstFillPlanMs, 4 * TerrainConstants.ApplyPlanMs, "a real head start");
            Assert.LessOrEqual(TerrainStreamer.FirstFillPlanMs, 16.6, "never more than a 60 Hz frame: the cover's fade and the HUD keep moving");
        }
    }
}
