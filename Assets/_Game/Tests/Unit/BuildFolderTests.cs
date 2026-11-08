using Meridian.EditorTools;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-143: the owner's release player in Build/MERIDIAN_&lt;v&gt;/ (no Development Build watermark), the probed development player beside
    /// it in Build/MERIDIAN_&lt;v&gt;_dev/ (the memory probe needs its counters). tools/unity_build_selftest.ps1 checks the wrappers agree.</summary>
    public class BuildFolderTests
    {
        [Test]
        public void TheReleaseAndTheDevBuildSitSideBySide()
        {
            Assert.AreEqual($"Build/{GameInfo.Product}_{GameInfo.Version}", BuildTools.OutputFolderFor(true), "the release: the plain folder");
            Assert.AreEqual($"Build/{GameInfo.Product}_{GameInfo.Version}_dev", BuildTools.OutputFolderFor(false), "the development build: _dev");
            Assert.AreEqual(BuildTools.OutputFolder, BuildTools.OutputFolderFor(true));
            Assert.AreEqual("MERIDIAN", GameInfo.Product, "the wrappers look for Build/MERIDIAN_<v>");
        }
    }
}
