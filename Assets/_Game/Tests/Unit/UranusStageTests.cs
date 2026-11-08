using System.IO;
using Meridian.Flora;
using Meridian.Planet;
using Meridian.Planets;
using Meridian.Terrain.CloudColumn;
using Meridian.View2D;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-130 slice 1 (Bible §7.8 the sideways winter, D-142): Uranus runs the decked-giant machinery; each deck's set is picked by the season's light
    /// (deck_sun_left / _sun_right / _night, plus the survey layer0), every light one geometry, so the U-128 crossfade turns the light and nothing
    /// slides; the floes draw the methane ice in the lit half and the dark half's slate; the plants take the rig set's vocabulary.
    /// </summary>
    public class UranusStageTests
    {
        const int W = 4096;
        const float Day = 14.3f; // Uranus.asset's dayLengthRealMinutes
        static double Season => UranusSeason.SeasonSeconds(Day);
        static readonly string[] Decks = { CartoonStage.JupiterDeck1, CartoonStage.JupiterDeck2, CartoonStage.JupiterDeck3, CartoonStage.JupiterDeep };

        [Test]
        public void UranusRidesTheDeckMachineryWithoutAZoneOverlay()
        {
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Uranus), "U-130: Uranus is on the cartoon path");
            Assert.IsTrue(CartoonStage.Decked(PlanetId.Uranus));
            Assert.IsFalse(CartoonStage.HasZoneOverlay(PlanetId.Uranus), "no Red Spot or Hexagon: the veil slot stays off");
            Assert.IsTrue(CartoonStage.HasZoneOverlay(PlanetId.Jupiter) && CartoonStage.HasZoneOverlay(PlanetId.Saturn));
            Assert.AreEqual("deck1_sun_left", CartoonStage.FallbackFor(PlanetId.Uranus), "a set not exported yet: deck1 in the morning light");
        }

        [Test]
        public void TheLitHalfSwapsEverySixDaysAndTheSunCrossesIt()
        {
            Assert.AreEqual(6 * (double)Day * 60 * 72, Season, 1e-6, "six of Uranus's own days at the TimeSystem's rate");
            double morning = Season * 0.25, evening = Season * 0.75, nextMorning = Season * 1.25;
            Assert.AreEqual(UranusSeason.SunLeft, UranusSeason.LightAt(500, W, morning, Season), "the first half lit in an even season: its morning");
            Assert.AreEqual(UranusSeason.SunRight, UranusSeason.LightAt(500, W, evening, Season), "its evening: lined from the right");
            Assert.AreEqual(UranusSeason.Night, UranusSeason.LightAt(3000, W, morning, Season), "the other half is the night");
            Assert.AreEqual(UranusSeason.Night, UranusSeason.LightAt(500, W, nextMorning, Season), "the season turns: the halves swap");
            Assert.AreEqual(UranusSeason.SunLeft, UranusSeason.LightAt(3000, W, nextMorning, Season));
            Assert.AreEqual(UranusSeason.LightAt(500, W, morning, Season), UranusSeason.LightAt(500 + W, W, morning, Season), "the column wraps");
        }

        [Test]
        public void TheLightHoldsAtAHemispheresBorderButStillTurns()
        {
            double morning = Season * 0.25;
            int border = W / 2;
            Assert.AreEqual(UranusSeason.Night, UranusSeason.LightAt(border + 5, W, morning, Season));
            Assert.AreEqual(UranusSeason.SunLeft, UranusSeason.LightFor(border + 5, W, morning, Season, UranusSeason.SunLeft), "5 columns into the night: the morning holds");
            Assert.AreEqual(UranusSeason.Night, UranusSeason.LightFor(border + UranusSeason.BorderHold + 5, W, morning, Season, UranusSeason.SunLeft), "past the hold: the night");
            Assert.AreEqual(UranusSeason.SunRight, UranusSeason.LightFor(border - 5, W, Season * 0.75, Season, UranusSeason.SunLeft), "the evening comes at the border too");
            Assert.AreEqual(UranusSeason.SunLeft, UranusSeason.LightFor(border + 5, W, Season * 1.25, Season, UranusSeason.SunRight), "a season's swap turns the light at the border");
        }

        [Test]
        public void TheSceneIsTheBandsDeckInTheSeasonsLight()
        {
            double morning = Season * 0.25;
            Assert.AreEqual("deck2_sun_left", CartoonStage.UranusSceneFor(750f, 500, W, morning, Season, null, false));
            Assert.AreEqual("deep_night", CartoonStage.UranusSceneFor(200f, 3000, W, morning, Season, null, false));
            Assert.AreEqual("deck1_sun_right+survey", CartoonStage.UranusSceneFor(1000f, 500, W, Season * 0.75, Season, "deck1_sun_left", true));
            Assert.AreEqual("deck1_night", CartoonStage.UranusSceneFor(890f, 3000, W, morning, Season, "deck1_sun_left", false), "deck1 holds 10 m under its floor while the light turns");
            Assert.AreEqual("deck2", CartoonStage.DeckOf("deck2_sun_right+survey"));
            Assert.AreEqual("sun_right", CartoonStage.LightOf("deck2_sun_right+survey"));
            Assert.AreEqual("deck2_sun_right", CartoonStage.SetOf("deck2_sun_right+survey"));
            Assert.AreEqual("deck2_survey", CartoonStage.Layer0Of("deck2_sun_right+survey"), "the survey's banded layer0 under the light's layers");
            Assert.IsNull(CartoonStage.Layer0Of("deck2_sun_right"));
            Assert.AreEqual("deck1", CartoonStage.DeckOf("deck1"), "a Jupiter set is its own deck");
            Assert.IsNull(CartoonStage.LightOf("deck1"));
        }

        /// <summary>The crossfade test: the four lights of a deck share one geometry (one floor, one anchor; once B-166 lands, the same layer
        /// stack in each json), so turning the light only fades — nothing slides.</summary>
        [Test]
        public void TheFourLightsShareAGeometry()
        {
            foreach (var deck in Decks)
            {
                float floor = CartoonStage.JupiterFloor(deck);
                Assert.GreaterOrEqual(floor, 0f, deck);
                SceneLayout first = null; string firstName = null;
                foreach (var light in UranusSeason.Lights)
                {
                    string scene = deck + "_" + light;
                    Assert.AreEqual(floor, CartoonStage.DeckFloor(scene), scene + " hangs off its deck's floor");
                    Assert.AreEqual(floor, CartoonStage.DeckFloor(scene + CartoonStage.SurveySuffix), scene + " with the survey layer0: the same floor");
                    Assert.AreEqual(ParallaxMath.AnchorY(floor), ParallaxMath.AnchorY(CartoonStage.DeckFloor(scene)), scene + ": the same anchor");
                    string json = $"Assets/_Game/Art/backgrounds/uranus/{scene}/{scene}.json";
                    if (!File.Exists(json)) continue; // the art checks bite once B-166 exports
                    var layout = SceneLayout.Parse(File.ReadAllText(json));
                    if (first == null) { first = layout; firstName = scene; continue; }
                    Assert.AreEqual(first.ppu, layout.ppu, scene); Assert.AreEqual(first.anchor, layout.anchor, scene);
                    Assert.AreEqual(first.layers.Length, layout.layers.Length, $"{scene} has {firstName}'s layers");
                    for (int i = 0; i < first.layers.Length; i++)
                    {
                        Assert.AreEqual(first.layers[i].n, layout.layers[i].n, scene);
                        Assert.AreEqual(first.layers[i].parallax, layout.layers[i].parallax, 1e-6f, $"{scene} layer{i}: {firstName}'s parallax");
                        Assert.AreEqual(first.layers[i].y_m, layout.layers[i].y_m, 1e-6f, $"{scene} layer{i}: {firstName}'s height");
                        Assert.AreEqual(first.layers[i].height_px, layout.layers[i].height_px, $"{scene} layer{i}: {firstName}'s size");
                    }
                }
            }
        }

        /// <summary>D-154: the Survey view is on while the Survey module is the active one, off for every other module.</summary>
        [Test]
        public void TheSurveyViewFollowsTheActiveModule()
        {
            Assert.IsTrue(CartoonStage.SurveyViewFor(Meridian.Rig.RigModule.Survey));
            foreach (var m in new[] { Meridian.Rig.RigModule.Beam, Meridian.Rig.RigModule.Grapple, Meridian.Rig.RigModule.Builder })
                Assert.IsFalse(CartoonStage.SurveyViewFor(m), m + " selected: the plain fog");
        }

        /// <summary>U-146: a Survey scan pulses the survey bands for 4 beats at 110 bpm (~2.2 s): up over the first beat and down over the last
        /// through the U-128 smoothstep, held between, nothing before the scan or after the fourth beat.</summary>
        [Test]
        public void TheScanPulseLastsFourBeatsAndFades()
        {
            float beat = 60f / 110f, total = 4f * beat;
            Assert.AreEqual(total, CartoonStage.SurveyPulseSeconds, 1e-5f, "4 beats at 110 bpm");
            Assert.AreEqual(0f, CartoonStage.SurveyPulseAlpha(-0.01f));
            Assert.AreEqual(0f, CartoonStage.SurveyPulseAlpha(0f), 1e-5f, "it rises from nothing");
            Assert.AreEqual(0.5f, CartoonStage.SurveyPulseAlpha(beat * 0.5f), 1e-4f, "half the first beat: half up (the crossfade's smoothstep)");
            Assert.AreEqual(1f, CartoonStage.SurveyPulseAlpha(beat), 1e-4f);
            Assert.AreEqual(1f, CartoonStage.SurveyPulseAlpha(total * 0.5f), 1e-5f, "held through beats 2-3");
            Assert.AreEqual(0.5f, CartoonStage.SurveyPulseAlpha(total - beat * 0.5f), 1e-4f, "half the last beat: half down");
            Assert.AreEqual(0f, CartoonStage.SurveyPulseAlpha(total), 1e-5f, "gone after the fourth beat");
            Assert.AreEqual(CartoonStage.SurveyPulseAlpha(beat * 0.3f), CartoonStage.SurveyPulseAlpha(total - beat * 0.3f), 1e-5f, "the fade out mirrors the fade in");
            Assert.Less(CartoonStage.SurveyPulsePeak, 1f, "over the view, never covering it");
        }

        [Test]
        public void TheFloesAreMethaneIceAndTheDarkHalfsSlate()
        {
            CollectionAssert.AreEqual(new[] { "terrain/uranus/floe_strip_ice", "terrain/uranus/floe_strip_dark" }, GroundStrip.KeysFor(PlanetId.Uranus));
            Assert.AreEqual(GroundStrip.UranusIce, GroundStrip.UranusStripFor(false));
            Assert.AreEqual(GroundStrip.UranusDark, GroundStrip.UranusStripFor(true));
            Assert.IsTrue(GroundStrip.HasCaps(10), "B-158's floe strips are 10 frames: U-126 caps them");
        }

        [Test]
        public void ThePlantsTakeTheRigSetsVocabulary()
        {
            Assert.AreEqual("deck1", FloraRigs.UranusBiomeFor(1000f, false));
            Assert.AreEqual("deck2", FloraRigs.UranusBiomeFor(750f, false));
            Assert.AreEqual("deck3", FloraRigs.UranusBiomeFor(400f, false));
            Assert.AreEqual("dark_half", FloraRigs.UranusBiomeFor(750f, true), "the dark half: embermoss");
            Assert.AreEqual("deep", FloraRigs.UranusBiomeFor(200f, true), "the diamond rain under Deck 3: prismfern, lit or not");
            Assert.IsNull(FloraRigs.UranusBiomeFor(CloudLayout.CrushLine - 10f, false), "under the Crush Line: none");
        }
    }
}
