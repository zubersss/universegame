using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-185: what every PlayMode suite starts from. The first hour's hint cards are off (a fresh GameState on Earth would put DIG DOWN up in
    /// every test and capture); HintPlayTests and CaptureU185Hints switch them on for themselves.
    /// U-193 (D-182): the suites written before the shovel dig with the Beam they were written for (SkillStats.ToolOverride); ShovelPlayTests
    /// and CaptureU193Shovel clear it to start from a new surveyor's shovel. LeadQA (its own assembly) never sees this: it starts on the shovel.
    /// 11-10: NO TEST WRITES THE PLAYER'S SAVE. The game saves after every transition; a suite that flew one without pointing
    /// SaveSystem.RootOverride elsewhere (22 files did not), or that cleared its override, wrote the real slot under persistentDataPath,
    /// which the built player shares. SaveSystem.FallbackRoot sends every such save to a folder of the run's own, removed after it.
    /// </summary>
    [SetUpFixture]
    public class PlayModeDefaults
    {
        string saves;

        [OneTimeSetUp]
        public void Before()
        {
            Meridian.UI.HintCards.Suppressed = true;
            Meridian.Progress.SkillStats.ToolOverride = Meridian.Rig.DigTool.Beam;
            saves = System.IO.Path.Combine(UnityEngine.Application.temporaryCachePath, "meridian_saves_testrun_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            Meridian.Save.SaveSystem.FallbackRoot = saves;
        }

        [OneTimeTearDown]
        public void After()
        {
            Meridian.UI.HintCards.Suppressed = false;
            Meridian.Progress.SkillStats.ToolOverride = null;
            Meridian.Save.SaveSystem.FallbackRoot = null;
            try { if (saves != null && System.IO.Directory.Exists(saves)) System.IO.Directory.Delete(saves, true); } catch (System.IO.IOException) { }
        }
    }
}
