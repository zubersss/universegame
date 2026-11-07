using Meridian.Art;
using Meridian.EditorTools;
using Meridian.Planets;
using Meridian.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.Tests
{
    /// <summary>U-124 (contract §11.6, B-151): the importer's 9-slice rule, the paper frame around a modal panel, the panel text in
    /// ink, the title card's slide and its keys.</summary>
    public class PaperUiTests
    {
        [Test]
        public void TheSliceJsonBecomesUnitysSpriteBorder()
        {
            // The json reads [left, top, right, bottom]; Unity's Sprite.border is (left, bottom, right, top).
            Assert.AreEqual(new Vector4(10f, 40f, 30f, 20f), ArtImporter.BorderFromSlice(new[] { 10, 20, 30, 40 }));
            Assert.AreEqual(new Vector4(48f, 48f, 48f, 80f), ArtImporter.BorderFromSlice(new[] { 48, 80, 48, 48 }), "the settings paper: its 80 px header band on top");
            Assert.AreEqual(Vector4.zero, ArtImporter.BorderFromSlice(null), "no slice: no border");
            Assert.AreEqual(Vector4.zero, ArtImporter.BorderFromSlice(new[] { 4, 4 }), "a malformed slice: no border");
            var sheet = JsonUtility.FromJson<ArtImporter.SheetManifest>("{\"key\":\"ui/panels/scroll\",\"style\":\"v3\",\"ppu\":64,\"pivot\":[0.5,0.5],\"slice\":[64,28,64,28]}");
            Assert.IsTrue(sheet.HasSlice, "B-151's panel json carries its slice");
            Assert.IsFalse(sheet.IsSheet, "a panel is one image (Single), not a frame sheet");
            Assert.AreEqual(new Vector4(64f, 28f, 64f, 28f), ArtImporter.BorderFromSlice(sheet.slice));
            Assert.IsFalse(JsonUtility.FromJson<ArtImporter.SheetManifest>("{\"key\":\"ui/titlecards/mars\",\"style\":\"v3\"}").HasSlice, "a title card has none");
        }

        [Test]
        public void ThePaperFrameReachesPastTheContentByEachBorder()
        {
            var b = new Vector4(48f, 48f, 48f, 80f) * UiPaper.BorderReach; // the settings paper: (left, bottom, right, top)
            Assert.AreEqual(new Vector2(1180f + 72f, 860f + 96f), UiPaper.FrameSize(new Vector2(1180f, 860f), b), "the frame grows by 3/4 of each border");
            Assert.AreEqual(new Vector2(0f, 12f), UiPaper.FrameOffset(b), "the taller header band shifts the frame up by half the difference");
            var scroll = new Vector4(64f, 28f, 64f, 28f) * UiPaper.BorderReach;
            Assert.AreEqual(Vector2.zero, UiPaper.FrameOffset(scroll), "a symmetric scroll stays centred");
            Assert.LessOrEqual(UiPaper.FrameSize(new Vector2(1840f, 900f), new Vector4(40f, 40f, 40f, 40f) * UiPaper.BorderReach).x, 1920f, "the crafting sign still fits a 1080p screen");
        }

        [Test]
        public void ThePanelsOwnTextTurnsToInkButtonsAndCellsKeepTheirs()
        {
            var panel = new GameObject("Panel", typeof(RectTransform), typeof(Image));
            try
            {
                var title = new GameObject("Title", typeof(RectTransform), typeof(Text), typeof(Outline));
                title.transform.SetParent(panel.transform, false);
                title.GetComponent<Text>().color = Color.white;
                var group = new GameObject("Group", typeof(RectTransform)); // a plain container: its text is still the panel's
                group.transform.SetParent(panel.transform, false);
                var label = new GameObject("Label", typeof(RectTransform), typeof(Text));
                label.transform.SetParent(group.transform, false);
                var button = new GameObject("Button", typeof(RectTransform), typeof(Image), typeof(Button));
                button.transform.SetParent(panel.transform, false);
                var caption = new GameObject("Caption", typeof(RectTransform), typeof(Text));
                caption.transform.SetParent(button.transform, false);
                caption.GetComponent<Text>().color = Color.white;

                Assert.AreEqual(2, UiPaper.InkTexts(panel.transform), "the title and the grouped label");
                Assert.AreEqual(UiPaper.Ink, title.GetComponent<Text>().color);
                Assert.IsFalse(title.GetComponent<Outline>().enabled, "the light rim for the dark fill goes");
                Assert.AreEqual(UiPaper.Ink, label.GetComponent<Text>().color);
                Assert.AreEqual(Color.white, caption.GetComponent<Text>().color, "a button's label keeps its colour on its own fill");
            }
            finally { Object.DestroyImmediate(panel); }
        }

        [Test]
        public void TheTitleCardSlidesInHoldsAndSlidesOut()
        {
            Assert.AreEqual(-1920f, TitleCard.SlideX(0f), 1e-3f, "starts off the left edge");
            Assert.AreEqual(0f, TitleCard.SlideX(TitleCard.SlideSeconds), 1e-3f, "centred after the slide-in");
            Assert.AreEqual(0f, TitleCard.SlideX(TitleCard.SlideSeconds + TitleCard.HoldSeconds * 0.5f), 1e-3f, "held");
            Assert.AreEqual(1920f, TitleCard.SlideX(TitleCard.TotalSeconds), 1e-3f, "ends off the right edge");
            float prev = float.NegativeInfinity;
            for (float t = 0f; t <= TitleCard.TotalSeconds; t += 0.05f)
            {
                float x = TitleCard.SlideX(t);
                Assert.GreaterOrEqual(x, prev - 1e-3f, $"never moves back (t {t:F2})");
                prev = x;
            }
            Assert.AreEqual(2.4f, TitleCard.TotalSeconds, 1e-5f, "0.4 in, 1.6 held, 0.4 out");
            Assert.Less(TitleCard.SortingOrder, 500, "under the menus");
        }

        [Test]
        public void TheUiKeysFollowTheContract()
        {
            Assert.AreEqual("ui/titlecards/mercury", ArtKeys.Ui.TitleCard(PlanetId.Mercury));
            Assert.AreEqual("ui/titlecards/earth", ArtKeys.Ui.TitleCard(PlanetId.Earth));
            Assert.AreEqual("ui/panels/pause", ArtKeys.Ui.PanelPause);
            Assert.AreEqual("ui/panels/settings", ArtKeys.Ui.PanelSettings);
            Assert.AreEqual("ui/panels/inventory", ArtKeys.Ui.PanelInventory);
            Assert.AreEqual("ui/panels/sign", ArtKeys.Ui.PanelSign);
            Assert.AreEqual("ui/panels/scroll", ArtKeys.Ui.PanelScroll);
            Assert.AreEqual("ui/hud/film_switch", ArtKeys.Ui.FilmSwitch);
        }
    }
}
