using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-156 (EditMode, D-161 / D-162): the smooth ground's pure core. The generator's hills keep every column-to-column slope under the
    /// walkable limit; the curve keeps a plateau flat and eases its edge; the contour traces flat ground exactly on its integer line (the
    /// jump heights cannot move), a slope as a straight line, and a dug hole as one closed, rounded loop with the solid on its right; the fill
    /// covers exactly the solid area.
    /// </summary>
    public class GroundFieldTests
    {
        const int C = 32;
        static readonly Vector2 Half = new Vector2(0.5f, 0.5f); // node (i, j) is tile (i, j)'s centre

        static float[] Field(System.Func<int, int, float> f)
        {
            var d = new float[(C + 1) * (C + 1)];
            for (int y = 0; y <= C; y++) for (int x = 0; x <= C; x++) d[y * (C + 1) + x] = f(x, y);
            return d;
        }

        static float FillArea(GroundContour c)
        {
            float a = 0f;
            for (int t = 0; t < c.fillTris.Count; t += 3)
            {
                Vector3 p = c.fillVerts[c.fillTris[t]], q = c.fillVerts[c.fillTris[t + 1]], r = c.fillVerts[c.fillTris[t + 2]];
                a += Mathf.Abs((q.x - p.x) * (r.y - p.y) - (r.x - p.x) * (q.y - p.y)) * 0.5f;
            }
            return a;
        }

        [Test]
        public void TheHillsStayWalkable()
        {
            var raw = new float[512];
            var rng = new System.Random(156);
            for (int i = 0; i < raw.Length; i++) raw[i] = 300f + (float)rng.NextDouble() * 6f + 20f * Mathf.Sin(i * 0.11f) + (i % 97 == 0 ? 15f : 0f); // noise, hills, spikes
            var s = GroundField.SmoothSurface(raw, GroundField.SmoothRadius, GroundField.SurfaceSlope);
            for (int i = 0; i < s.Length; i++)
                Assert.LessOrEqual(Mathf.Abs(s[(i + 1) % s.Length] - s[i]), GroundField.SurfaceSlope + 1e-4f, $"column {i}: the slope stays under {GroundField.SurfaceSlope}");
            var flat = GroundField.SmoothSurface(new float[] { 5f, 5f, 5f, 5f, 5f, 5f, 5f, 5f, 5f, 5f }, 4, 0.6f);
            foreach (var v in flat) Assert.AreEqual(5f, v, 1e-5f, "flat stays flat");
        }

        [Test]
        public void TheCurveKeepsAPlateauFlatAndEasesItsEdge()
        {
            System.Func<int, int> top = x => x < 20 ? 10 : 14; // a 4 m step: a plateau's edge
            Assert.AreEqual(11f, GroundField.Curve(5, top), 1e-5f, "flat left of the edge, standing on top + 1");
            Assert.AreEqual(15f, GroundField.Curve(40, top), 1e-5f, "flat on the plateau");
            for (int x = 10; x < 30; x++)
                Assert.LessOrEqual(GroundField.Curve(x + 1, top) - GroundField.Curve(x, top), 4f * 4f / GroundField.CurveKernelSum + 1e-4f, "the edge eased over the kernel");
        }

        [Test]
        public void FlatGroundTracesExactlyOnItsLine()
        {
            var c = new GroundContour();
            c.Build(Field((x, y) => GroundField.Density(false, true, 10f, y)), C, Half);
            Assert.AreEqual(1, c.Lines, "one outline");
            Assert.IsFalse(c.lineClosed[0], "open: it runs off both chunk edges");
            int s = c.lineStart[0], n = c.lineCount[0];
            Assert.AreEqual(0.5f, c.points[s].x, 1e-4f, "it starts at the chunk's left edge (the surface runs +x, solid on its right)");
            Assert.AreEqual(C + 0.5f, c.points[s + n - 1].x, 1e-4f, "and ends at the right edge");
            for (int i = 0; i < n; i++) Assert.AreEqual(10f, c.points[s + i].y, 0.01f, "exactly on the integer line: flat-ground jumps cannot change");
            Assert.AreEqual(C * (10f - 0.5f), FillArea(c), 0.5f, "the fill is the solid area");
        }

        [Test]
        public void ASlopeIsAStraightLine()
        {
            var c = new GroundContour();
            c.Build(Field((x, y) => GroundField.Density(false, true, 8f + 0.5f * (x + 0.5f), y)), C, Half);
            Assert.AreEqual(1, c.Lines);
            int s = c.lineStart[0], n = c.lineCount[0];
            for (int i = 0; i < n; i++) { var p = c.points[s + i]; Assert.AreEqual(8f + 0.5f * p.x, p.y, 0.02f, $"point {p} on the slope"); }
        }

        [Test]
        public void ADugHoleIsOneRoundedLoop()
        {
            // Solid everywhere except a 2 × 2 tile hole (tiles 14..15, 14..15): the nodes are the tiles' own solidity.
            System.Func<int, int, bool> solid = (tx, ty) => !(tx >= 14 && tx <= 15 && ty >= 14 && ty <= 15);
            var c = new GroundContour();
            c.Build(Field((x, y) => GroundField.Density(solid(x, y), false, 0f, y)), C, Half);
            Assert.AreEqual(1, c.Lines, "one outline");
            Assert.IsTrue(c.lineClosed[0], "a hole is a closed loop");
            int s = c.lineStart[0], n = c.lineCount[0];
            float area = 0f; bool corner = false;
            for (int i = 0; i < n; i++)
            {
                Vector2 p = c.points[s + i], q = c.points[s + (i + 1) % n];
                area += p.x * q.y - q.x * p.y;
                if ((p - new Vector2(14f, 14f)).sqrMagnitude < 1e-4f || (p - new Vector2(16f, 16f)).sqrMagnitude < 1e-4f) corner = true;
            }
            area *= 0.5f;
            Assert.IsFalse(corner, "no square corner: the hole's corners are rounded off");
            Assert.Greater(area, 0f, "solid on the right: a hole winds counter-clockwise (its air on the left)");
            Assert.That(Mathf.Abs(area), Is.InRange(2.5f, 4.01f), "about the 2 × 2 hole, less its rounded corners");
            Assert.AreEqual(C * C - Mathf.Abs(area), FillArea(c), 0.05f, "the fill is everything but the hole");
        }
    }
}
