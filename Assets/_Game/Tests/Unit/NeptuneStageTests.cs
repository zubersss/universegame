using System.IO;
using Meridian.Flora;
using Meridian.Planet.Weather;
using Meridian.Planets;
using Meridian.Terrain.CloudColumn;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-133 slice 1 (Bible §7.9, D-148): Neptune runs the decked-giant machinery: B-161's deck1–3 / deep by band; the Dark Storm ("storm", its rim
    /// layer breathing by its json pulse block) and the Great Dark Spot ("spot", sharing the storm's layers 1–2) as 400 m zones over decks 1–3;
    /// the plants lean with the wind through one input on the rig driver; the floes draw the methane ice and the Deep's superionic strip.
    /// </summary>
    public class NeptuneStageTests
    {
        const int W = 4096;

        [Test]
        public void NeptuneRidesTheDeckMachinery()
        {
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Neptune), "U-133: Neptune, the last, on the cartoon path");
            Assert.IsTrue(CartoonStage.Decked(PlanetId.Neptune));
            Assert.IsFalse(CartoonStage.HasZoneOverlay(PlanetId.Neptune), "its storms are whole sets, not a veil overlay");
            Assert.AreEqual(CartoonStage.JupiterDeck1, CartoonStage.FallbackFor(PlanetId.Neptune));
        }

        /// <summary>The lean test (D-148): 0° at calm to 25° at 35 m/s, linear between, capped; mirrored for −x wind; a stepped shiver in a gust.</summary>
        [Test]
        public void ThePlantsLeanWithTheWind()
        {
            Assert.AreEqual(0f, NeptuneWind.Lean(0f, false, 0), 1e-5f, "calm: upright");
            Assert.AreEqual(-25f, NeptuneWind.Lean(35f, false, 0), 1e-4f, "35 m/s +x: 25° downwind (the top toward +x)");
            Assert.AreEqual(-12.5f, NeptuneWind.Lean(17.5f, false, 0), 1e-4f, "half the gale: half the lean");
            Assert.AreEqual(-25f, NeptuneWind.Lean(60f, false, 0), 1e-4f, "never past 25°");
            foreach (var w in new[] { 4f, 8f, 14f, 20f, 35f })
                Assert.AreEqual(-NeptuneWind.Lean(w, false, 0), NeptuneWind.Lean(-w, false, 0), 1e-5f, $"{w} m/s: −x mirrors the lean");
            double t0 = 0.01, t1 = t0 + 1.0 / NeptuneWind.ShiverHz;
            float a = NeptuneWind.Lean(30f, true, t0), b = NeptuneWind.Lean(30f, true, t1);
            Assert.AreEqual(2f * NeptuneWind.ShiverDegrees, Mathf.Abs(a - b), 1e-4f, "a gust shivers in steps at 12 Hz");
            Assert.AreEqual(NeptuneWind.Lean(30f, false, t0), (a + b) * 0.5f, 1e-4f, "about the steady lean");
            Assert.AreEqual(a, NeptuneWind.Lean(30f, true, t0 + 0.02), 1e-5f, "a step holds between flips");
        }

        [Test]
        public void TheWindSwellsAndGusts()
        {
            for (double t = 0; t < 200; t += 0.37)
            {
                float s = NeptuneWind.Speed(t);
                if (NeptuneWind.Gusting(t)) { Assert.LessOrEqual(s, NeptuneWind.GustPeak + 1e-3f, $"t {t}"); Assert.GreaterOrEqual(s, NeptuneWind.CalmMin - 1e-3f); }
                else { Assert.GreaterOrEqual(s, NeptuneWind.CalmMin - 1e-3f, $"t {t}"); Assert.LessOrEqual(s, NeptuneWind.CalmMax + 1e-3f, $"t {t}"); }
            }
            Assert.AreEqual(NeptuneWind.GustPeak, NeptuneWind.Speed(NeptuneWind.GustSeconds * 0.5), 0.01f, "mid-gust: 35 m/s");
            Assert.AreEqual(1, NeptuneWind.Direction(500), "+x, the drawing's direction");
            Assert.Greater(NeptuneWind.At(500, 10), 0f);
        }

        [Test]
        public void TheStormsAreFourHundredMetreZones()
        {
            Assert.AreEqual(400, 2 * NeptuneStorms.HalfWidth, "Bible §7.9: 400 m zones");
            Assert.IsTrue(NeptuneStorms.InDarkSpot(NeptuneStorms.DarkSpotCentre, W));
            Assert.IsFalse(NeptuneStorms.InDarkSpot(NeptuneStorms.DarkSpotCentre + NeptuneStorms.HalfWidth + 1, W));
            Assert.AreEqual(NeptuneStorms.StormStart, NeptuneStorms.StormCentre(0, W));
            Assert.AreEqual(NeptuneStorms.StormStart + 50, NeptuneStorms.StormCentre(100 * Meridian.Core.TimeSystem.GameSecondsPerRealSecond, W), "the storm drifts 0.5 m/s");
            Assert.IsTrue(NeptuneStorms.InStorm(NeptuneStorms.StormStart - W, 0, W), "the column wraps");
        }

        [Test]
        public void TheSceneIsTheBandOrTheStormOverIt()
        {
            Assert.AreEqual("spot@deck2~", CartoonStage.NeptuneSceneFor(750f, NeptuneStorms.DarkSpotCentre, W, 0, null), "the Spot lies in the −x half: mirrored");
            Assert.AreEqual("storm@deck2", CartoonStage.NeptuneSceneFor(750f, NeptuneStorms.StormStart, W, 0, null));
            Assert.AreEqual("storm@deck1", CartoonStage.NeptuneSceneFor(1000f, NeptuneStorms.StormStart, W, 0, null));
            Assert.AreEqual("deck2", CartoonStage.NeptuneSceneFor(750f, 2000, W, 0, null), "between the zones: the deck");
            Assert.AreEqual("deep~", CartoonStage.NeptuneSceneFor(200f, NeptuneStorms.DarkSpotCentre, W, 0, null), "the Deep keeps its set (mirrored in the −x half)");
            int edge = NeptuneStorms.DarkSpotCentre + NeptuneStorms.HalfWidth;
            Assert.AreEqual("spot@deck2~", CartoonStage.NeptuneSceneFor(750f, edge + 10, W, 0, "spot@deck2~"), "10 m past the Spot's edge: it holds");
            Assert.AreEqual("deck2~", CartoonStage.NeptuneSceneFor(750f, edge + 30, W, 0, "spot@deck2~"), "past the hold: the deck");
            Assert.AreEqual("deck2", CartoonStage.DeckOf("storm@deck2"));
            Assert.AreEqual("storm", CartoonStage.SetOf("storm@deck2"));
            Assert.AreEqual(CloudLayout.Deck2Bottom, CartoonStage.DeckFloor("storm@deck2"), "a zone set hangs off its band's floor");
            Assert.AreEqual("storm", CartoonStage.UpperOf("spot@deck3"), "the spot shares the storm's layers 1–2");
            Assert.IsNull(CartoonStage.UpperOf("storm@deck3"));
            Assert.IsNull(CartoonStage.UpperOf("deck3"));
        }

        [Test]
        public void TheStormRimBreathesByItsPulseBlock()
        {
            var layout = SceneLayout.Parse("{\"layers\":[{\"n\":0,\"parallax\":0.1},{\"n\":1,\"parallax\":0.35,\"pulse\":{\"scale\":[0.97,1.03],\"alpha\":[0.85,1.0],\"beats\":8,\"bpm\":110,\"pivot_uv\":[0.5,0.5]}},{\"n\":2,\"parallax\":0.6}]}");
            Assert.IsFalse(ParallaxMath.Pulsed(layout.layers[0].pulse), "a layer without a block holds still");
            var p = layout.layers[1].pulse;
            Assert.IsTrue(ParallaxMath.Pulsed(p));
            double cycle = 8 * 60.0 / 110.0;
            ParallaxMath.PulseAt(p, 0, out float s0, out float a0);
            Assert.AreEqual(0.97f, s0, 1e-4f); Assert.AreEqual(0.85f, a0, 1e-4f);
            ParallaxMath.PulseAt(p, cycle * 0.5, out float s1, out float a1);
            Assert.AreEqual(1.03f, s1, 1e-4f, "half the 8-beat breath: full"); Assert.AreEqual(1f, a1, 1e-4f);
            ParallaxMath.PulseAt(p, cycle, out float s2, out _);
            Assert.AreEqual(0.97f, s2, 1e-4f, "8 beats at 110 bpm (~4.4 s): back");
            Assert.AreEqual(new Vector2(0f, 8f), ParallaxMath.PulseOffset(new Vector2(0.5f, 0f), new Vector2(0.5f, 0.5f), new Vector2(96f, 16f)), "a bottom pivot scales about the centre");
            string json = "Assets/_Game/Art/backgrounds/neptune/storm/storm.json";
            if (File.Exists(json))
                Assert.IsTrue(ParallaxMath.Pulsed(SceneLayout.Parse(File.ReadAllText(json)).layers[1].pulse), "B-169's storm set carries its rim's pulse block");
        }

        /// <summary>U-144: the column's second half blows −x: its sets show mirrored ("~", through the crossfade, held 20 m past the border), its
        /// floes run backwards with each end taking the other's cap, and the lean mirrors.</summary>
        [Test]
        public void TheWestwardHalfIsMirrored()
        {
            Assert.AreEqual(1, NeptuneWind.Direction(500));
            Assert.AreEqual(-1, NeptuneWind.Direction(3000), "the second half blows −x");
            Assert.AreEqual(-1, NeptuneWind.Direction(-500), "the column wraps");
            Assert.Greater(NeptuneWind.Lean(NeptuneWind.At(3000, 10), false, 10), 0f, "−x wind: the tops lean toward −x");
            Assert.AreEqual(1, NeptuneWind.DirectionFor(W / 2 + 10, 1), "10 m into the −x half: the +x set holds");
            Assert.AreEqual(-1, NeptuneWind.DirectionFor(W / 2 + 30, 1), "past the hold: mirrored");
            Assert.AreEqual("deck2~", CartoonStage.NeptuneSceneFor(750f, 2600, W, 0, null));
            Assert.AreEqual("deck2", CartoonStage.NeptuneSceneFor(750f, 1500, W, 0, null));
            Assert.IsTrue(CartoonStage.MirrorOf("storm@deck2~")); Assert.IsFalse(CartoonStage.MirrorOf("storm@deck2"));
            Assert.AreEqual("storm", CartoonStage.SetOf("storm@deck2~"));
            Assert.AreEqual("deck2", CartoonStage.DeckOf("storm@deck2~"));
            Assert.AreEqual(CloudLayout.Deck2Bottom, CartoonStage.DeckFloor("deck2~"), "a mirrored set hangs where its deck does");
            Assert.AreEqual("storm", CartoonStage.UpperOf("spot@deck3~"));
            Assert.AreEqual(GroundStrip.TileFrame(5), GroundStrip.StripFrame(5, false));
            Assert.AreEqual(GroundStrip.TileFrame(-6), GroundStrip.StripFrame(5, true), "mirrored: the tiles run backwards");
            Assert.AreEqual((GroundStrip.StripFrame(6, true) + 1) % GroundStrip.TileFrames, GroundStrip.StripFrame(5, true), "so the next column left continues the run");
            Assert.AreEqual(GroundStrip.CapRight, GroundStrip.LeftCapFrame(true)); Assert.AreEqual(GroundStrip.CapLeft, GroundStrip.RightCapFrame(true));
            Assert.AreEqual(GroundStrip.CapLeft, GroundStrip.LeftCapFrame(false));
        }

        /// <summary>U-144: the surveyor drifts 0.12 × the wind (on foot the ground's grip applies), nothing in the lee of a solid within 3 m upwind
        /// or while holding an anchor (within 1.5 m).</summary>
        [Test]
        public void TheWindDriftsTheSurveyorUnlessShelteredOrAnchored()
        {
            Assert.AreEqual(1.2f, NeptuneWind.Drift(10f, false, false), 1e-5f, "10 m/s: 1.2 m/s");
            Assert.AreEqual(4.2f, NeptuneWind.Drift(35f, false, false), 1e-5f, "a 35 m/s gust: 4.2 m/s");
            Assert.AreEqual(-2.4f, NeptuneWind.Drift(-20f, false, false), 1e-5f, "−x wind drifts −x");
            Assert.AreEqual(0f, NeptuneWind.Drift(35f, false, true), "anchored: stands fast");
            Assert.AreEqual(0f, NeptuneWind.Drift(35f, true, false), "sheltered: no drift");
            System.Func<int, int, bool> wall = (x, y) => x == 8 && y >= 0 && y <= 5;
            Assert.IsTrue(NeptuneWind.Sheltered(wall, new Vector2(10.5f, 2f), 1), "a wall 2 m upwind shelters");
            Assert.IsFalse(NeptuneWind.Sheltered(wall, new Vector2(10.5f, 2f), -1), "the same wall downwind does not");
            Assert.IsFalse(NeptuneWind.Sheltered(wall, new Vector2(12.5f, 2f), 1), "4 m upwind is too far");
            Assert.IsFalse(NeptuneWind.Sheltered(wall, new Vector2(10.5f, 7f), 1), "over the wall's top: in the wind");
            Assert.IsTrue(WindAnchor.WithinReach(new Vector2(3f, 1f), new Vector2(4.2f, 1f)));
            Assert.IsFalse(WindAnchor.WithinReach(new Vector2(3f, 1f), new Vector2(4.6f, 1f)));
            Assert.Greater(WindAnchor.LetGo, WindAnchor.Reach, "the hold lets go a little past where it takes");
        }

        /// <summary>D-157 (c): the drawn surveyor leans into the wind: 40 % of the flora's steady lean in the swell, 60 % in a gust, none anchored.</summary>
        [Test]
        public void TheSurveyorLeansIntoTheWind()
        {
            Assert.AreEqual(10f, NeptuneWind.SurveyorLean(35f, false, false), 1e-4f, "+x wind: the head back toward −x, 40 % of 25°");
            Assert.AreEqual(15f, NeptuneWind.SurveyorLean(35f, true, false), 1e-4f, "in a gust: 60 %");
            Assert.AreEqual(-10f, NeptuneWind.SurveyorLean(-35f, false, false), 1e-4f, "−x wind: mirrored");
            Assert.AreEqual(0f, NeptuneWind.SurveyorLean(35f, true, true), "anchored: upright");
            Assert.AreEqual(0f, NeptuneWind.SurveyorLean(0f, false, false), "calm: upright");
            Assert.AreEqual(-0.4f * NeptuneWind.Lean(14f, false, 0), NeptuneWind.SurveyorLean(14f, false, false), 1e-5f);
        }

        /// <summary>D-157 (b): the wind anchor is a Builder piece made at the fabricator (placed like a camp prop); every Neptune landing floe
        /// carries one by the pad.</summary>
        [Test]
        public void TheWindAnchorIsABuilderPiece()
        {
            var spec = Meridian.Building.PieceSpec.ForItem("wind_anchor");
            Assert.NotNull(spec, "a base piece");
            Assert.AreEqual(Meridian.Building.PieceKind.WindAnchor, spec.kind);
            Assert.AreEqual(WindAnchor.ArtKey, spec.artKey);
            Assert.IsFalse(spec.solid, "walk-through: the surveyor stands at it");
            Assert.NotNull(Meridian.Items.ItemRegistry.Get("wind_anchor"));
            var recipe = Meridian.Crafting.CraftingDefaults.Recipes().Find(r => r.output.item == "wind_anchor");
            Assert.NotNull(recipe, "the fabricator makes it");
            Assert.AreEqual(Meridian.Crafting.Station.Fabricator, recipe.station);
            Assert.Greater(Meridian.Core.PlanetSideRoot.PadAnchorOffset, 0);
        }

        /// <summary>U-144: the HUD's gust warning: GUST IN 2, GUST IN 1, then GUST while it blows; nothing between.</summary>
        [Test]
        public void TheHudWarnsOfAGust()
        {
            Assert.AreEqual(0f, NeptuneWind.SecondsToGust(1.0), 1e-5f, "a gust blows from t 0 to 4");
            Assert.AreEqual(13f, NeptuneWind.SecondsToGust(10.0), 1e-4f);
            Assert.AreEqual(0, Meridian.UI.SideHud.GustCode(1.0));
            Assert.AreEqual(-1, Meridian.UI.SideHud.GustCode(10.0), "between gusts: nothing");
            Assert.AreEqual(2, Meridian.UI.SideHud.GustCode(NeptuneWind.GustEvery - 1.5), "1.5 s out: GUST IN 2");
            Assert.AreEqual(1, Meridian.UI.SideHud.GustCode(NeptuneWind.GustEvery - 0.5));
        }

        [Test]
        public void TheFloesAreMethaneIceAndTheDeepsSuperionic()
        {
            CollectionAssert.AreEqual(new[] { "terrain/neptune/floe_strip_ice", "terrain/neptune/floe_strip_superionic" }, GroundStrip.KeysFor(PlanetId.Neptune));
            Assert.AreEqual(GroundStrip.NeptuneIce, GroundStrip.NeptuneStripFor(750f));
            Assert.AreEqual(GroundStrip.NeptuneSuperionic, GroundStrip.NeptuneStripFor(200f), "the Deep's black hot ice");
            Assert.IsTrue(GroundStrip.HasCaps(10), "B-161's floe strips are 10 frames: U-126 caps them");
        }

        [Test]
        public void ThePlantsTakeTheRigSetsVocabulary()
        {
            Assert.AreEqual("deck1", FloraRigs.NeptuneBiomeFor(1000f, false));
            Assert.AreEqual("deck2", FloraRigs.NeptuneBiomeFor(750f, false));
            Assert.AreEqual("deck3", FloraRigs.NeptuneBiomeFor(400f, false));
            Assert.AreEqual("storm", FloraRigs.NeptuneBiomeFor(750f, true), "in a storm: stormlantern, gripweed");
            Assert.AreEqual("deep", FloraRigs.NeptuneBiomeFor(200f, true), "the Deep: rimecomb");
            Assert.IsNull(FloraRigs.NeptuneBiomeFor(CloudLayout.CrushLine - 10f, false));
        }
    }
}
