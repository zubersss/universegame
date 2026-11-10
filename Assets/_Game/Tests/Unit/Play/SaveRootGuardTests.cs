using System.IO;
using Meridian.Save;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// D-203 (11-10): no test run reaches the player's own save folder. The game autosaves after every transition into SaveSystem.Root;
    /// the Editor and the built player share persistentDataPath, so a test that flew a transition with no RootOverride (22 files did)
    /// overwrote the slot the owner plays. PlayModeDefaults now sets SaveSystem.FallbackRoot for the whole run: this row fails the run
    /// if that guard is ever taken out, or if the root a test would save to with no override lies under persistentDataPath. And the
    /// player's own switch for a script that drives it (the smoke, the memory probe): "-meridianSaveRoot &lt;folder&gt;".
    /// </summary>
    public class SaveRootGuardTests
    {
        [Test]
        public void NoTestCanReachThePlayersOwnSaveFolder()
        {
            Assert.IsFalse(string.IsNullOrEmpty(SaveSystem.FallbackRoot), "the run's own save root is set (PlayModeDefaults): without it a test with no RootOverride saves into the player's real slot");
            string real = Path.GetFullPath(Application.persistentDataPath).TrimEnd('\\', '/');
            string was = SaveSystem.RootOverride;
            SaveSystem.RootOverride = null; // what a test that sets nothing, or clears its own, would save to
            try
            {
                string root = Path.GetFullPath(SaveSystem.Root);
                Assert.IsFalse(root.StartsWith(real, System.StringComparison.OrdinalIgnoreCase), $"with no override a test's saves go to '{root}': never under the player's '{real}'");
                TestContext.Out.WriteLine($"[MERIDIAN] save root guard (PlayMode): with no override a test saves to '{root}'; the player's own folder is '{real}'");
            }
            finally { SaveSystem.RootOverride = was; }
        }

        [Test]
        public void ThePlayersSwitchNamesTheSaveRootOfARun()
        {
            Assert.AreEqual("-meridianSaveRoot", SaveSystem.RootSwitch);
            Assert.AreEqual(@"C:\logs\smoke_saves", SaveSystem.RootFromArgs(new[] { "MERIDIAN.exe", "-meridianSmoke", @"C:\logs\smoke", "-meridianSaveRoot", @"C:\logs\smoke_saves", "-screen-width", "1920" }));
            Assert.AreEqual(@"C:\logs\probe saves", SaveSystem.RootFromArgs(new[] { "MERIDIAN.exe", "-meridianSaveRoot", "\"C:\\logs\\probe saves\"" }), "quotes off");
            Assert.IsNull(SaveSystem.RootFromArgs(new[] { "MERIDIAN.exe", "-screen-width", "1920" }), "no switch: the player's own folder, as always");
            Assert.IsNull(SaveSystem.RootFromArgs(new[] { "MERIDIAN.exe", "-meridianSaveRoot" }), "the switch with nothing after it is no root");
            Assert.IsNull(SaveSystem.RootFromArgs(null));
        }
    }
}
