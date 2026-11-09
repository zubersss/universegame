using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-185: what every PlayMode suite starts from. The first hour's hint cards are off (a fresh GameState on Earth would put DIG DOWN up in
    /// every test and capture); HintPlayTests and CaptureU185Hints switch them on for themselves.
    /// </summary>
    [SetUpFixture]
    public class PlayModeDefaults
    {
        [OneTimeSetUp] public void Before() => Meridian.UI.HintCards.Suppressed = true;
        [OneTimeTearDown] public void After() => Meridian.UI.HintCards.Suppressed = false;
    }
}
