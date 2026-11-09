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
                var menuButton = new GameObject("MenuButton", typeof(RectTransform), typeof(Image), typeof(Button)); // UiKit.Button: a 0.08 white fill
                menuButton.transform.SetParent(panel.transform, false);
                menuButton.GetComponent<Image>().color = new Color(1f, 1f, 1f, 0.08f);
                var menuLabel = new GameObject("MenuLabel", typeof(RectTransform), typeof(Text));
                menuLabel.transform.SetParent(menuButton.transform, false);
                menuLabel.GetComponent<Text>().color = Color.white;

                Assert.AreEqual(3, UiPaper.InkTexts(panel.transform), "the title, the grouped label and the clear-filled menu button's label");
                Assert.AreEqual(UiPaper.Ink, menuLabel.GetComponent<Text>().color, "a near-clear fill lets the paper show: its label inks (the 15:26 capture's light labels on cream)");
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

        static int Count(Transform t, string name) { int n = 0; for (int i = 0; i < t.childCount; i++) if (t.GetChild(i).name == name) n++; return n; }

        /// <summary>U-135 (D-149): an inventory slot is an ink-line box (four 2 px ink edges inside it, a faint paper-darkening fill) with a gold band for
        /// the selected slot, so an empty inventory shows its grid; the crafting panel sits on the inventory paper, not the stretched sign.</summary>
        [Test]
        public void SlotsAreInkBoxesAndCraftingSitsOnTheInventoryPaper()
        {
            var slot = new GameObject("Slot", typeof(RectTransform), typeof(Image));
            try
            {
                var rt = slot.GetComponent<RectTransform>();
                rt.sizeDelta = new Vector2(96f, 96f);
                UiKit.InkEdges(rt, UiKit.SlotEdge, UiKit.Ink);
                var band = UiKit.GoldBand(rt);
                Assert.AreEqual(4, Count(rt, UiKit.EdgeName), "four ink edges");
                foreach (Transform c in rt)
                {
                    if (c.name != UiKit.EdgeName) continue;
                    var e = (RectTransform)c;
                    Assert.AreEqual(UiKit.Ink, c.GetComponent<Image>().color);
                    Assert.AreEqual(UiKit.SlotEdge, Mathf.Max(Mathf.Abs(e.sizeDelta.x), Mathf.Abs(e.sizeDelta.y)), 1e-4f, "2 px wide (the stretched side reads 0)");
                    Assert.IsFalse(c.GetComponent<Image>().raycastTarget, "the edges never take the slot's clicks");
                }
                Assert.IsFalse(band.enabled, "the gold band waits for the selection");
                Assert.AreEqual(UiKit.Gold, band.color);
                Assert.Less(UiKit.SlotFill.a, UiPaper.OwnGroundAlpha, "the slot's fill is the paper's (its count letters in ink)");
            }
            finally { Object.DestroyImmediate(slot); }
            Assert.AreEqual(ArtKeys.Ui.PanelInventory, CraftingPanel.PaperKey, "D-149: crafting moves from the sign to the inventory paper");
        }

        /// <summary>U-136 (D-149): every button, tab and tile is a cream paper card with ink lettering and a 1 px ink edge; the state shows as the gold band
        /// (selected / known) or a greyed card with faded ink (locked / can't act); no navy or blue fill.</summary>
        [Test]
        public void ButtonsTabsAndTilesArePaperCards()
        {
            var root = new GameObject("Root", typeof(RectTransform));
            try
            {
                var menu = UiKit.Button(root.transform, "RESUME", Vector2.zero, () => { });
                var menuFill = (Image)menu.targetGraphic;
                var menuLabel = menu.GetComponentInChildren<Text>();
                Assert.AreEqual(UiKit.Cream, menuFill.color, "a menu button is a cream card");
                Assert.AreEqual(UiKit.Ink, menuLabel.color, "lettered in ink");
                Assert.AreEqual(4, Count(menu.transform, UiKit.EdgeName), "a 1 px ink edge");
                var rim = menuLabel.GetComponent<Outline>();
                Assert.IsTrue(rim == null || !rim.enabled, "no light rim on the cream");
                Assert.AreNotEqual(menu.colors.normalColor, menu.colors.selectedColor, "keyboard focus shows on the opaque card");

                var craft = UiKit.ActionButton(root.transform, "CRAFT", new Vector2(0f, 1f), Vector2.zero, new Vector2(130f, 34f), () => { });
                var craftFill = (Image)craft.targetGraphic;
                var craftLabel = craft.GetComponentInChildren<Text>();
                UiKit.SetAction(craft, false);
                Assert.IsFalse(craft.interactable);
                Assert.AreEqual(UiKit.Greyed, craftFill.color, "can't act: a greyed card");
                Assert.AreEqual(UiKit.InkFaded, craftLabel.color, "with faded ink");
                UiKit.SetAction(craft, true);
                Assert.IsTrue(craft.interactable);
                Assert.AreEqual(UiKit.Cream, craftFill.color, "can act: cream, not blue");
                Assert.AreEqual(UiKit.Ink, craftLabel.color);

                var band = craft.transform.Find(UiKit.BandName).GetComponent<Image>();
                UiKit.SetCard(craftFill, UiKit.Card.Gold);
                Assert.IsTrue(band.enabled, "selected / known: the gold band");
                Assert.AreEqual(UiKit.Cream, craftFill.color);
                UiKit.SetCard(craftFill, UiKit.Card.Plain);
                Assert.IsFalse(band.enabled);
                UiKit.SetCard(craftFill, UiKit.Card.Locked);
                Assert.IsFalse(band.enabled, "a locked card has no band");
                Assert.AreEqual(UiKit.Greyed, craftFill.color);

                // A refreshed panel text (a recipe name, a catalogue entry): ink on the paper, faded when locked; light on the flat fallback.
                Assert.AreEqual(UiKit.Ink, UiKit.Letter(true, true));
                Assert.AreEqual(UiKit.InkFaded, UiKit.Letter(true, false));
                Assert.AreEqual(UiTheme.Active.text, UiKit.Letter(false, true), "no paper: the theme's light text");
                Assert.AreEqual(UiTheme.Active.text, UiKit.Letter(null, true), "the probe still out: light");
            }
            finally { Object.DestroyImmediate(root); }
        }
    
        [Test]
        public void TheFlatPapersAreTheOnesWhoseJsonAsksForTheGrain()
        {
            // U-181 (B-208): UiPaper.Grained mirrors the jsons (the panels' jsons are not addressable at runtime)
            var fromJson = new System.Collections.Generic.HashSet<string>();
            foreach (var f in System.IO.Directory.GetFiles("Assets/_Game/Art/ui", "*.json", System.IO.SearchOption.AllDirectories))
            {
                var text = System.IO.File.ReadAllText(f);
                if (!System.Text.RegularExpressions.Regex.IsMatch(text, "\"grain\"\\s*:\\s*\"ui/panels/grain\"")) continue;
                var key = System.Text.RegularExpressions.Regex.Match(text, "\"key\"\\s*:\\s*\"([^\"]+)\"").Groups[1].Value;
                fromJson.Add(key);
            }
            CollectionAssert.AreEquivalent(fromJson, UiPaper.Grained, "the flat papers");
            Assert.IsFalse(UiPaper.Grained.Contains(UiPaper.GrainKey));
            var grain = System.IO.File.ReadAllText("Assets/_Game/Art/ui/panels/grain.json");
            StringAssert.Contains("\"tile_x\": true", grain); StringAssert.Contains("\"texel_px\": 1", grain);
        }
    }
}
