using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-185: what every PlayMode suite starts from. The first hour's hint cards are off (a fresh GameState on Earth would put DIG DOWN up in
    /// every test and capture); HintPlayTests and CaptureU185Hints switch them on for themselves.
    /// U-193 (D-182): the suites written before the shovel dig with the Beam they were written for (SkillStats.ToolOverride); ShovelPlayTests
    /// and CaptureU193Shovel clear it to start from a new surveyor's shovel. LeadQA (its own assembly) never sees this: it starts on the shovel.
    /// </summary>
    [SetUpFixture]
    public class PlayModeDefaults
    {
        [OneTimeSetUp]
        public void Before()
        {
            Meridian.UI.HintCards.Suppressed = true;
            Meridian.Progress.SkillStats.ToolOverride = Meridian.Rig.DigTool.Beam;
        }

        [OneTimeTearDown]
        public void After()
        {
            Meridian.UI.HintCards.Suppressed = false;
            Meridian.Progress.SkillStats.ToolOverride = null;
        }
    }
}
