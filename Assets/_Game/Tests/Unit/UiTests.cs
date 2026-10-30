using System.IO;
using System.Linq;
using Meridian.EditorTools;
using Meridian.UI;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-015 (EditMode): OFL font in the theme, license shipped and credited; number strings.</summary>
    public class UiTests
    {
        [Test]
        public void ThemeUsesJetBrainsMono()
        {
            var theme = AssetDatabase.LoadAssetAtPath<UiTheme>(SceneAuthoring.UiThemePath);
            Assert.NotNull(theme, "UI/Resources/UiTheme.asset");
            Assert.NotNull(theme.regular); Assert.NotNull(theme.bold);
            StringAssert.Contains("JetBrainsMono", AssetDatabase.GetAssetPath(theme.regular));
            StringAssert.Contains("JetBrainsMono", AssetDatabase.GetAssetPath(theme.bold));
        }

        [Test]
        public void OflLicenseShippedAndCredited()
        {
            Assert.IsTrue(File.Exists("Assets/_Game/UI/Fonts/JetBrainsMono-OFL.txt"), "OFL text ships with the font");
            StringAssert.Contains("SIL Open Font License", File.ReadAllText("Assets/_Game/UI/Fonts/JetBrainsMono-OFL.txt"));
            var credits = File.ReadAllText("docs/credits/unity.md");
            foreach (var font in Directory.GetFiles("Assets/_Game/UI/Fonts", "*.ttf"))
            {
                var path = font.Replace('\\', '/');
                var line = credits.Split('\n').FirstOrDefault(l => l.Contains(path));
                Assert.NotNull(line, $"{path} credited");
                StringAssert.Contains("Open Font License", line);
            }
        }

        [Test]
        public void NumberStringsCoverRangeWithoutAllocatingLater()
        {
            var n = new UiKit.NumberStrings(-5, 400);
            Assert.AreEqual("-5", n[-5]); Assert.AreEqual("0", n[0]); Assert.AreEqual("400", n[400]);
            Assert.AreEqual("400", n[999], "clamps");
            var t = new UiKit.NumberStrings(0, 99, "0.0", 10f);
            Assert.AreEqual("1.2", t[12]); Assert.AreEqual("0.0", t[0]); Assert.AreEqual("9.9", t[99]);
            Assert.AreSame(n[42], n[42], "same instance every time");
        }
    }
}
