using System.IO;
using Meridian.Save;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// D-203 (11-10): the EditMode run's own save root, as PlayModeDefaults sets one for the PlayMode run: a test that makes a
    /// SaveSystem and sets no RootOverride (or clears its own) can never write the player's real slot under persistentDataPath.
    /// </summary>
    [SetUpFixture]
    public class EditModeDefaults
    {
        string saves;

        [OneTimeSetUp]
        public void Before()
        {
            saves = Path.Combine(Application.temporaryCachePath, "meridian_saves_editrun_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.FallbackRoot = saves;
        }

        [OneTimeTearDown]
        public void After()
        {
            SaveSystem.FallbackRoot = null;
            try { if (saves != null && Directory.Exists(saves)) Directory.Delete(saves, true); } catch (IOException) { }
        }
    }

    /// <summary>The EditMode run's guard row (see SaveRootGuardTests in the PlayMode assembly).</summary>
    public class SaveRootGuardEditTests
    {
        [Test]
        public void NoEditModeTestCanReachThePlayersOwnSaveFolder()
        {
            Assert.IsFalse(string.IsNullOrEmpty(SaveSystem.FallbackRoot), "the run's own save root is set (EditModeDefaults)");
            string real = Path.GetFullPath(Application.persistentDataPath).TrimEnd('\\', '/');
            string was = SaveSystem.RootOverride;
            SaveSystem.RootOverride = null;
            try
            {
                string root = Path.GetFullPath(SaveSystem.Root);
                Assert.IsFalse(root.StartsWith(real, System.StringComparison.OrdinalIgnoreCase), $"with no override a test's saves go to '{root}': never under the player's '{real}'");
            }
            finally { SaveSystem.RootOverride = was; }
        }
    }
}
