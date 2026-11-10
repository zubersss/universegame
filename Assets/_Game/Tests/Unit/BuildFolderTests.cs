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

        /// <summary>D-194 (LEAD 11-09 23:5x): the Windows player's graphics API is pinned to Direct3D 11 alone, not left automatic (the
        /// built player took 11 and the Editor 12, and the Editor's frame figures did not hold in the player); an Editor that has a
        /// graphics device (a capture, a graphics PlayMode run) draws on that same API. A headless run has none to compare.</summary>
        [Test]
        public void ThePlayerAndTheEditorDrawOnDirect3D11()
        {
            Assert.AreEqual(UnityEngine.Rendering.GraphicsDeviceType.Direct3D11, CheckSetup.PlayerApi);
            Assert.IsTrue(CheckSetup.Direct3D11Pinned(UnityEditor.BuildTarget.StandaloneWindows64),
                "the Windows player's graphics APIs are Direct3D 11 alone (CheckSetup.PinDirect3D11 sets it; ProjectSettings carries it)");
            var here = UnityEngine.SystemInfo.graphicsDeviceType;
            if (here == UnityEngine.Rendering.GraphicsDeviceType.Null) Assert.Pass("no graphics device in this run: the Editor's API is checked by the perf captures");
            Assert.AreEqual(CheckSetup.PlayerApi, here, "the Editor draws on the player's API");
        }
    }
}
