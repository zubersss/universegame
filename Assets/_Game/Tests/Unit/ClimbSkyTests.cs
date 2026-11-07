using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-109 (EditMode): the climb sky's curves, pure. The gradient is layer0's painting extended upward in layer0's own
    /// parallax frame: the top-row colour at the painted edge, space black `span` metres above it, where the span is the
    /// frame-top distance when the camera centre is on the Escape Line; the stars fade in over the last third of the climb.
    /// </summary>
    public class ClimbSkyTests
    {
        // Earth's plains (plains.json layer0: parallax 0.1, y_m −2, 1024 px at 64 ppu = 16 m; PlanetConfig: datum 320, Escape Line 720).
        const float Parallax = 0.1f, Datum = 320f, Escape = 720f, HalfH = 16.875f * 0.5f;
        static float Anchor => ParallaxMath.AnchorY(Datum);
        static float EdgeRest => Datum - 2f + 16f;
        static readonly Color Top = new Color(0.45f, 0.62f, 0.85f, 1f);

        static void AssertColour(Color expect, Color got, string what)
        {
            Assert.AreEqual(expect.r, got.r, 1e-5f, what + " (r)");
            Assert.AreEqual(expect.g, got.g, 1e-5f, what + " (g)");
            Assert.AreEqual(expect.b, got.b, 1e-5f, what + " (b)");
            Assert.AreEqual(1f, got.a, 1e-6f, what + " (opaque)");
        }

        [Test]
        public void TheShadeIsThePaintedRowAtTheEdgeAndSpaceBlackAtTheSpan()
        {
            AssertColour(Top, ClimbSkyMath.Shade(Top, 0f, 40f), "the top row at the edge");
            AssertColour(Top, ClimbSkyMath.Shade(Top, -30f, 40f), "and everywhere below it (behind the painting)");
            AssertColour(ClimbSkyMath.SpaceBlack, ClimbSkyMath.Shade(Top, 40f, 40f), "space black at the span");
            AssertColour(ClimbSkyMath.SpaceBlack, ClimbSkyMath.Shade(Top, 400f, 40f), "and beyond it (entry from above)");
            float last = ClimbSkyMath.Luma(Top);
            for (int i = 1; i <= 40; i++)
            {
                float l = ClimbSkyMath.Luma(ClimbSkyMath.Shade(Top, i, 40f));
                Assert.LessOrEqual(l, last + 1e-6f, $"darker with every metre ({i})");
                last = l;
            }
            var mid = ClimbSkyMath.Shade(Top, 20f, 40f);
            Assert.Less(ClimbSkyMath.Luma(mid), ClimbSkyMath.Luma(Top));
            Assert.Greater(ClimbSkyMath.Luma(mid), ClimbSkyMath.Luma(ClimbSkyMath.SpaceBlack));
            Assert.AreEqual(1f, ClimbSkyMath.Shade(new Color(1f, 1f, 1f, 0.2f), 20f, 40f).a, "opaque whatever the inputs' alpha");
            AssertColour(ClimbSkyMath.SpaceBlack, ClimbSkyMath.Shade(Top, 5f, 0f), "a zero span is all black");
        }

        [Test]
        public void TheSpanPutsTheFrameTopAtBlackOnTheEscapeLineAndKeepsThePadPainted()
        {
            float span = ClimbSkyMath.Span(Parallax, Escape, Anchor, EdgeRest, HalfH);
            float edgeAtLine = ClimbSkyMath.EdgeY(Escape, Anchor, EdgeRest, Parallax);
            Assert.AreEqual(span, Escape + HalfH - edgeAtLine, 1e-3f, "frame top − edge on the line = the span");
            Assert.AreEqual(39.33f, span, 0.05f, "Earth: about 39 m of layer0's frame");
            // On the pad the frame top is still under the painted edge: nothing of the gradient shows.
            float edgeAtRest = ClimbSkyMath.EdgeY(Anchor, Anchor, EdgeRest, Parallax);
            Assert.AreEqual(EdgeRest, edgeAtRest, 1e-5f);
            Assert.LessOrEqual(Anchor + HalfH, edgeAtRest, "the painted sky reaches the frame top at rest");
            AssertColour(Top, ClimbSkyMath.Shade(Top, Anchor + HalfH - edgeAtRest, span), "the frame top on the pad is the painted row");
            // The edge rides up with the camera at (1 − parallax): the line ParallaxLayers places layer0 on, plus its height.
            float cam = Datum + 200f;
            Assert.AreEqual(ParallaxMath.LayerY(cam, Anchor, Datum, -2f, Parallax) + 16f, ClimbSkyMath.EdgeY(cam, Anchor, EdgeRest, Parallax), 1e-4f);
            // Half-way up the frame is darker at its top than at its bottom, neither end black.
            float edgeHalf = ClimbSkyMath.EdgeY(cam, Anchor, EdgeRest, Parallax);
            float topL = ClimbSkyMath.Luma(ClimbSkyMath.Shade(Top, cam + HalfH - edgeHalf, span));
            float bottomL = ClimbSkyMath.Luma(ClimbSkyMath.Shade(Top, cam - HalfH - edgeHalf, span));
            Assert.Less(topL, bottomL);
            Assert.Greater(topL, ClimbSkyMath.Luma(ClimbSkyMath.SpaceBlack));
            Assert.AreEqual(1f, ClimbSkyMath.Span(0f, Escape, Anchor, Anchor + 100f, HalfH), "a towering far layer still gets a 1 m fade");
        }

        [Test]
        public void TheStarsFadeInOverTheLastThirdOfTheClimb()
        {
            Assert.AreEqual(0f, ClimbSkyMath.Climb(Datum, Datum, Escape));
            Assert.AreEqual(0.5f, ClimbSkyMath.Climb(Datum + 200f, Datum, Escape), 1e-6f);
            Assert.AreEqual(1f, ClimbSkyMath.Climb(Escape + 20f, Datum, Escape), "clamped above the line (entry)");
            Assert.AreEqual(0f, ClimbSkyMath.Climb(Datum - 50f, Datum, Escape), "clamped below the datum (a dug camp)");
            Assert.AreEqual(0f, ClimbSkyMath.Climb(Datum + 10f, Datum, Datum), "a degenerate line never divides by zero");
            Assert.AreEqual(0f, ClimbSkyMath.StarAlpha(0f));
            Assert.AreEqual(0f, ClimbSkyMath.StarAlpha(0.5f));
            Assert.AreEqual(0f, ClimbSkyMath.StarAlpha(ClimbSkyMath.StarsFrom), 1e-6f, "nothing through the first two thirds");
            Assert.Greater(ClimbSkyMath.StarAlpha(0.8f), 0f);
            Assert.Less(ClimbSkyMath.StarAlpha(0.8f), ClimbSkyMath.StarAlpha(0.9f), "rising");
            Assert.AreEqual(ClimbSkyMath.MaxStarAlpha, ClimbSkyMath.StarAlpha(1f), 1e-6f, "full at the line");
            Assert.AreEqual(ClimbSkyMath.MaxStarAlpha, ClimbSkyMath.StarAlpha(1.3f), 1e-6f);
            Assert.LessOrEqual(ClimbSkyMath.MaxStarAlpha, 0.7f, "low alpha: the painting stays the picture");
            Assert.Greater(ClimbSky.LoadStarsAt, 0f);
            Assert.Less(ClimbSky.LoadStarsAt, ClimbSkyMath.StarsFrom, "the sheet loads before it could ever show");
        }
    }
}
