using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using Meridian.EditorTools;
using Meridian.UI;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-104 (EditMode, B-121 / D-090 / D-103): the gauge sheet's needle map parses; a needle steps only on 12 Hz ticks, is
    /// exact at the tick and wobbles on a change; no HUD, panel or menu string mentions fuel; the theme carries the two faces.
    /// </summary>
    public class HudGaugeTests
    {
        const string JsonPath = "Assets/_Game/Art/ui/hud/gauges.json";

        [Test]
        public void TheGaugeSheetParsesItsThreeNeedles()
        {
            Assert.IsTrue(File.Exists(JsonPath), "B-121 gauges json in the project");
            var specs = GaugeSheet.Parse(File.ReadAllText(JsonPath));
            Assert.AreEqual(3, specs.Count, "suit_power, oxygen, gravity");
            foreach (var name in new[] { "suit_power", "oxygen", "gravity" })
            {
                Assert.IsTrue(specs.TryGetValue(name, out var s), name);
                Assert.AreEqual("dial_" + name, s.dial);
                Assert.AreEqual("needle_" + name, s.needle);
                Assert.AreEqual(125f, s.minDeg, 1e-4f);
                Assert.AreEqual(-125f, s.maxDeg, 1e-4f);
                Assert.AreEqual(0.5f, s.hub.x, 1e-4f); Assert.AreEqual(0.5f, s.hub.y, 1e-4f);
                Assert.AreEqual(0.25f, s.dangerBelow, 1e-4f);
                Assert.AreEqual(125f, s.Angle(0f), 1e-4f, "empty: 125°");
                Assert.AreEqual(0f, s.Angle(0.5f), 1e-4f, "half: straight up");
                Assert.AreEqual(-125f, s.Angle(1f), 1e-4f, "full: −125°");
                Assert.AreEqual(-125f, s.Angle(1.5f), 1e-4f, "clamped");
                Assert.AreEqual(-1f, s.SweepSign, "B-121's dials sweep clockwise");
                Assert.IsTrue(s.InDanger(0.2f)); Assert.IsFalse(s.InDanger(0.25f));
            }
            Assert.AreEqual(0, GaugeSheet.Parse("{}").Count);
            Assert.AreEqual(0, GaugeSheet.Parse(null).Count);
            var one = GaugeSheet.Parse("{\"needles\":{\"x\":{\"dial\":\"d\",\"needle\":\"n\",\"hub\":[0.4,0.6],\"min_deg\":90,\"max_deg\":-90}}}")["x"];
            Assert.AreEqual(0.4f, one.hub.x, 1e-5f); Assert.AreEqual(0.6f, one.hub.y, 1e-5f);
            Assert.AreEqual(0f, one.dangerBelow, "no danger line when the json has none");
            Assert.IsFalse(one.InDanger(0f));
        }

        [Test]
        public void TheNeedleStepsOnTwelveHertzTicksAndWobblesOnAChange()
        {
            var n = new GaugeNeedle();
            Assert.IsFalse(n.HasShown);
            Assert.IsTrue(n.Step(0.5f, 0f), "the first tick");
            Assert.AreEqual(0.5f, n.Shown, 1e-6f);
            Assert.AreEqual(0f, n.Wobble, 1e-6f, "no wobble on the first reading");
            Assert.IsFalse(n.Step(0.9f, 0.03f), "inside the same 1/12 s: held");
            Assert.AreEqual(0.5f, n.Shown, 1e-6f, "the old value shows until the tick");
            Assert.IsTrue(n.Step(0.9f, 1f / 12f + 1e-4f), "the next tick");
            Assert.AreEqual(0.9f, n.Shown, 1e-6f, "exact at the tick: within 1 % of the meter");
            Assert.Greater(n.Wobble, 0f, "a rise overshoots toward higher values");
            Assert.LessOrEqual(Mathf.Abs(n.Wobble), GaugeNeedle.WobbleDeg);
            float t = 2f / 12f;
            bool settled = false;
            for (int i = 0; i < 12 && !settled; i++, t += 1f / 12f) { n.Step(0.9f, t + 1e-4f); settled = n.Wobble == 0f; }
            Assert.IsTrue(settled, "the wobble dies within a second");
            Assert.LessOrEqual(t, 0.6f, "and well before 0.6 s");
            Assert.AreEqual(0.9f, n.Shown, 1e-6f, "the value never drifted");
            Assert.IsFalse(n.Step(0.9f, t + 0.01f) && n.Wobble != 0f, "steady: no wobble");
            n.Step(0.3f, t + 1f);
            Assert.AreEqual(0.3f, n.Shown, 1e-6f);
            Assert.Less(n.Wobble, 0f, "a fall overshoots toward lower values");
            n.Step(0.3f, t + 3f);
            Assert.AreEqual(0f, n.Wobble, 1e-6f, "settled again");
            var c = new GaugeNeedle();
            c.Step(1.7f, 0f);
            Assert.AreEqual(1f, c.Shown, 1e-6f, "clamped to the dial");
            c.Reset();
            Assert.IsFalse(c.HasShown);
        }

        [Test]
        public void NoHudPanelOrMenuStringMentionsFuel()
        {
            // D-103 / D-105: no fuel of any kind. String literals in the HUD, panel and menu code, and text in the scenes and prefabs.
            var files = new List<string>(Directory.GetFiles("Assets/_Game/Code/Runtime/UI", "*.cs", SearchOption.AllDirectories))
            {
                "Assets/_Game/Code/Runtime/Ship/ShipHud.cs",
                "Assets/_Game/Code/Runtime/Space/SpaceHud.cs",
                "Assets/_Game/Code/Runtime/Ship/EscapeLineBand.cs",
            };
            var literal = new Regex("\"[^\"\\r\\n]*fuel[^\"\\r\\n]*\"", RegexOptions.IgnoreCase);
            foreach (var f in files)
            {
                var m = literal.Match(File.ReadAllText(f));
                Assert.IsFalse(m.Success, $"{f} carries a fuel string: {m.Value}");
            }
            var assets = new List<string>(Directory.GetFiles("Assets/_Game/Scenes", "*.unity", SearchOption.AllDirectories));
            assets.AddRange(Directory.GetFiles("Assets/_Game", "*.prefab", SearchOption.AllDirectories));
            foreach (var a in assets)
                foreach (var line in File.ReadLines(a))
                    if ((line.Contains("m_Text:") || line.Contains("m_Name:")) && line.IndexOf("fuel", System.StringComparison.OrdinalIgnoreCase) >= 0)
                        Assert.Fail($"{a}: {line.Trim()}");
        }

        [Test]
        public void TheThemeCarriesTheTwoCartoonFaces()
        {
            var theme = AssetDatabase.LoadAssetAtPath<UiTheme>(SceneAuthoring.UiThemePath);
            Assert.NotNull(theme, SceneAuthoring.UiThemePath);
            Assert.NotNull(theme.hudTtf, "Patrick Hand set by FontAuthoring (CheckSetup / SceneAuthoring)");
            StringAssert.Contains("PatrickHand", theme.hudTtf.name);
            Assert.NotNull(theme.titleTtf, "Limelight set by FontAuthoring");
            StringAssert.Contains("Limelight", theme.titleTtf.name);
            Assert.AreSame(theme.hudTtf, theme.HudFace, "every HUD and menu string draws in the HUD face");
            Assert.AreSame(theme.titleTtf, theme.TitleFace, "titles in Limelight");
            Assert.NotNull(theme.hudFont, "the TextMeshPro asset that letters the Escape Line sign");
        }
    }
}
