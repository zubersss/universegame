using System.IO;
using Meridian.EditorTools;
using Meridian.UI;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-104 (EditMode, D-090): the two OFL faces are in the project with their licences beside them, credited, and the
    /// UiTheme carries both as TextMeshPro assets built from them (titles: Limelight; HUD and body: Patrick Hand).
    /// </summary>
    public class HudFontsTests
    {
        [Test]
        public void TheTwoFacesAreInTheProjectWithTheirLicencesAndCredits()
        {
            foreach (var (ttf, licence, author) in new[]
            {
                (FontAuthoring.TitleTtf, "Assets/_Game/Fonts/Limelight/OFL.txt", "Sorkin"),
                (FontAuthoring.HudTtf, "Assets/_Game/Fonts/PatrickHand/OFL.txt", "Wagesreiter"),
            })
            {
                Assert.IsTrue(File.Exists(ttf), ttf);
                Assert.IsTrue(File.Exists(licence), licence + " beside the font (D-090)");
                StringAssert.Contains("SIL Open Font License", File.ReadAllText(licence));
                StringAssert.Contains(author, File.ReadAllText(licence), "the licence names its author");
                Assert.NotNull(AssetDatabase.LoadAssetAtPath<Font>(ttf), ttf + " imports as a Font");
            }
            var credits = File.ReadAllText("docs/credits/unity.md");
            StringAssert.Contains("Fonts/Limelight/Limelight-Regular.ttf", credits, "Limelight credited");
            StringAssert.Contains("Fonts/PatrickHand/PatrickHand-Regular.ttf", credits, "Patrick Hand credited");
        }

        [Test]
        public void TheThemeCarriesBothAsTextMeshProAssets()
        {
            var theme = AssetDatabase.LoadAssetAtPath<UiTheme>(SceneAuthoring.UiThemePath);
            Assert.NotNull(theme, "UiTheme asset (SceneAuthoring)");
            Assert.NotNull(theme.titleFont, "titleFont (Limelight SDF): run CheckSetup / Author Scenes");
            Assert.NotNull(theme.hudFont, "hudFont (Patrick Hand SDF)");
            Assert.AreEqual("Limelight-Regular", theme.titleFont.sourceFontFile != null ? theme.titleFont.sourceFontFile.name : theme.titleFont.name.Replace(" SDF", ""));
            Assert.AreEqual("PatrickHand-Regular", theme.hudFont.sourceFontFile != null ? theme.hudFont.sourceFontFile.name : theme.hudFont.name.Replace(" SDF", ""));
            Assert.NotNull(theme.titleFont.material, "font material saved with the asset");
            Assert.NotNull(theme.hudFont.material);
            Assert.AreEqual(TMPro.AtlasPopulationMode.Dynamic, theme.hudFont.atlasPopulationMode, "dynamic atlas: glyphs rasterise on demand");
            Assert.NotNull(theme.titleTtf); Assert.NotNull(theme.hudTtf);
        }
    }
}
