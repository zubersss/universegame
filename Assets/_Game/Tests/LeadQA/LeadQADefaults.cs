using NUnit.Framework;

namespace Meridian.Tests.LeadQA
{
    /// <summary>
    /// D-203: no LeadQA run may write the player's real save folder. Each LeadQA class points SaveSystem.RootOverride at a folder of
    /// its own and clears it in TearDown; this fixture is the net under them for the whole run: a save made with no override
    /// (a transition's autosave after a TearDown, or a class added later without the SetUp) goes to a temp folder, removed after.
    /// The Play assembly has its own (PlayModeDefaults); a fixture only covers its own assembly.
    /// </summary>
    [SetUpFixture]
    public class LeadQADefaults
    {
        string saves;
        string before;

        [OneTimeSetUp]
        public void Before()
        {
            before = Meridian.Save.SaveSystem.FallbackRoot;
            saves = System.IO.Path.Combine(UnityEngine.Application.temporaryCachePath, "meridian_saves_leadqa_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            Meridian.Save.SaveSystem.FallbackRoot = saves;
            TestContext.Out.WriteLine($"[LEADQA] saves with no override go to {saves}");
        }

        [OneTimeTearDown]
        public void After()
        {
            Meridian.Save.SaveSystem.FallbackRoot = before;
            try { if (saves != null && System.IO.Directory.Exists(saves)) System.IO.Directory.Delete(saves, true); } catch (System.IO.IOException) { }
        }
    }
}
