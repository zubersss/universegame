using System.Collections.Generic;
using UnityEngine;

namespace Meridian.Terrain
{
    /// <summary>
    /// U-156 (D-161 / D-162, Bible 5.0): the smooth cartoon ground, pure. The tile grid stays as hidden data; what draws and collides is one
    /// outline traced over a density field at the grid's vertices: where the four tiles round a vertex are as the original surface left them
    /// (the generator plus the POI stamps, no digs) the density follows the smoothed surface curve, clamp(H − y + 0.5); anywhere the player dug
    /// or built it is the tiles' occupancy (¼ per solid tile). Both cross 0.5 on the same lines (a flat surface at its integer top, a tile edge
    /// at the edge), so the surface and every hole share one path. GroundContour traces it.
    /// </summary>
    public static class GroundField
    {
        /// <summary>The contour level (a hair under ½ so a vertex at exactly ½, the tile-edge case, counts as solid without a zero-length segment).</summary>
        public const float Iso = 0.5f - 1e-3f;
        /// <summary>The steepest walkable slope (tan 35°, Bible 5.0); the generator keeps Earth's hills under SurfaceSlope.</summary>
        public const float MaxWalkSlope = 0.7f, SurfaceSlope = 0.6f;
        /// <summary>The generator's rolling-hill smoothing: a moving average over ±SmoothRadius columns before the slope clamp.</summary>
        public const int SmoothRadius = 4;
        /// <summary>The surface curve: the original column tops (stamps included) through this kernel, so plateaus stay flat and their edges ease.</summary>
        public static readonly float[] CurveKernel = { 1f, 2f, 3f, 4f, 5f, 4f, 3f, 2f, 1f }; // 9 taps: integer ramps up to 0.65 stay under 0.68 per m
        public const float CurveKernelSum = 25f;

        /// <summary>The planets whose ground is the smooth outline (Earth first, D-161 (6)); the others keep the blocks until U-159.</summary>
        public static bool Smooth(Meridian.Planets.PlanetId p) => !ForceBlocks && p == Meridian.Planets.PlanetId.Earth;
        /// <summary>Captures only: the 0.4.8 look (blocks, no hill smoothing) for the before / after frames. Read when a planet loads.</summary>
        public static bool ForceBlocks;

        /// <summary>Rolling hills: a wrapped moving average over ±radius columns, then the slope limited to maxSlope per column by the lower
        /// Lipschitz envelope (each column at most its neighbour + maxSlope: peaks cut to cones, valleys untouched), two passes each way round
        /// the ring so the seam holds too. Only ever lowers, so it always converges. Pure.</summary>
        public static float[] SmoothSurface(float[] raw, int radius, float maxSlope)
        {
            int n = raw.Length;
            var a = new float[n];
            if (n == 0) return a;
            for (int x = 0; x < n; x++)
            {
                float s = 0f;
                for (int k = -radius; k <= radius; k++) s += raw[((x + k) % n + n) % n];
                a[x] = s / (2 * radius + 1);
            }
            for (int i = 1; i <= 2 * n; i++) { int x = i % n, p = (i - 1) % n; if (a[x] > a[p] + maxSlope) a[x] = a[p] + maxSlope; }
            for (int i = 2 * n - 1; i >= 0; i--) { int x = i % n, p = (i + 1) % n; if (a[x] > a[p] + maxSlope) a[x] = a[p] + maxSlope; }
            return a;
        }

        /// <summary>The surface curve's standing height for column x from the original tops (stamps in, digs out): the tops + 1 through
        /// CurveKernel. Pure; `top` takes unwrapped columns.</summary>
        public static float Curve(int x, System.Func<int, int> top)
        {
            float s = 0f;
            int r = CurveKernel.Length / 2;
            for (int k = -r; k <= r; k++) s += CurveKernel[k + r] * (top(x + k) + 1f);
            return s / CurveKernelSum;
        }

        /// <summary>The curve's density ramp: ±FieldBand / 2 m round the surface stays unclamped, so any walkable slope traces exactly.</summary>
        public const float FieldBand = 4f;

        /// <summary>The density at a tile's centre (the field's node): a natural tile (as the original surface left it) follows its column's
        /// curve, (H − (y + ½)) / FieldBand + ½, crossing ½ exactly at H; a dug or built tile is its own solidity, 1 or 0, so a lone dug tile is
        /// a rounded ~1 m scoop and a flat dug floor still crosses ½ on the tile edge. Pure.</summary>
        public static float Density(bool solid, bool natural, float curve, int tileY)
            => natural ? Mathf.Clamp01((curve - (tileY + 0.5f)) / FieldBand + 0.5f) : (solid ? 1f : 0f);
    }

    /// <summary>
    /// U-156: marching squares over a chunk's node densities (the tile centres, 1 m apart) at Sub × Sub cells per metre (bilinear between the
    /// nodes, so a dug edge rounds), chained into polylines with the solid on the right (a surface runs +x, its air side to the left), plus the
    /// solid region's fill triangles (whole cells merged into row runs). `origin` places node (0, 0); a chunk's nodes are the tile centres from
    /// one tile left of / under it, origin (−½, −½), so neighbouring chunks' cells tile without overlap. Buffers are reused; no allocation once warm.
    /// Consecutive points closer than MinGap are merged (Box2D chains reject near-duplicate vertices).
    /// </summary>
    public sealed class GroundContour
    {
        public const int Sub = 4;
        public readonly List<Vector2> points = new List<Vector2>(512);
        /// <summary>Polyline i is points[lineStart[i] .. lineStart[i] + lineCount[i]); lineClosed[i] when it loops.</summary>
        public readonly List<int> lineStart = new List<int>(16), lineCount = new List<int>(16);
        public readonly List<bool> lineClosed = new List<bool>(16);
        public readonly List<Vector3> fillVerts = new List<Vector3>(1024);
        public readonly List<int> fillTris = new List<int>(2048);
        public int Lines => lineStart.Count;

        // segments: start / end edge keys and points
        readonly List<int> segA = new List<int>(512), segB = new List<int>(512);
        readonly List<Vector2> segPA = new List<Vector2>(512), segPB = new List<Vector2>(512);
        readonly Dictionary<int, int> startAt = new Dictionary<int, int>(512), endAt = new Dictionary<int, int>(512);
        readonly List<bool> used = new List<bool>(512);
        float[] d; int n; int m; float iso; Vector2 origin;
        public const float MinGap = 0.01f;

        /// <summary>Traces `density` ((size + 1)² node values, row-major, 1 m apart, node (0, 0) at `nodeOrigin`) at `level`.</summary>
        public void Build(float[] density, int size, Vector2 nodeOrigin, float level = GroundField.Iso)
        {
            d = density; n = size; m = size * Sub; iso = level; origin = nodeOrigin;
            points.Clear(); lineStart.Clear(); lineCount.Clear(); lineClosed.Clear();
            fillVerts.Clear(); fillTris.Clear();
            segA.Clear(); segB.Clear(); segPA.Clear(); segPB.Clear(); startAt.Clear(); endAt.Clear(); used.Clear();
            for (int cy = 0; cy < n; cy++)
            {
                int runStart = -1;
                for (int cx = 0; cx <= n; cx++)
                {
                    bool full = false, empty = false;
                    if (cx < n)
                    {
                        float a = V(cx, cy), b = V(cx + 1, cy), c = V(cx + 1, cy + 1), e = V(cx, cy + 1);
                        full = a >= iso && b >= iso && c >= iso && e >= iso;
                        empty = a < iso && b < iso && c < iso && e < iso;
                    }
                    if (full) { if (runStart < 0) runStart = cx; continue; }
                    if (runStart >= 0) { Quad(runStart, cy, cx, cy + 1); runStart = -1; }
                    if (cx < n && !empty) for (int sy = 0; sy < Sub; sy++) for (int sx = 0; sx < Sub; sx++) SubCell(cx * Sub + sx, cy * Sub + sy);
                }
            }
            Chain();
            if (origin != Vector2.zero)
            {
                for (int i = 0; i < points.Count; i++) points[i] += origin;
                var o3 = (Vector3)origin;
                for (int i = 0; i < fillVerts.Count; i++) fillVerts[i] += o3;
            }
        }

        float V(int vx, int vy) => d[vy * (n + 1) + vx];

        /// <summary>The density at sub-vertex (i, j): bilinear between the 1 m vertices.</summary>
        float S(int i, int j)
        {
            int vx = i / Sub, vy = j / Sub;
            float fx = (i - vx * Sub) / (float)Sub, fy = (j - vy * Sub) / (float)Sub;
            if (vx >= n) { vx = n - 1; fx = 1f; }
            if (vy >= n) { vy = n - 1; fy = 1f; }
            float a = V(vx, vy), b = V(vx + 1, vy), c = V(vx + 1, vy + 1), e = V(vx, vy + 1);
            return Mathf.Lerp(Mathf.Lerp(a, b, fx), Mathf.Lerp(e, c, fx), fy);
        }

        void Quad(float x0, float y0, float x1, float y1)
        {
            int v = fillVerts.Count;
            fillVerts.Add(new Vector3(x0, y0, 0f)); fillVerts.Add(new Vector3(x1, y0, 0f)); fillVerts.Add(new Vector3(x1, y1, 0f)); fillVerts.Add(new Vector3(x0, y1, 0f));
            fillTris.Add(v); fillTris.Add(v + 2); fillTris.Add(v + 1); fillTris.Add(v); fillTris.Add(v + 3); fillTris.Add(v + 2);
        }

        // Sub-cell scratch: the solid polygon walked corner → edge → corner (CCW: bl, B, br, R, tr, T, tl, L).
        readonly Vector2[] poly = new Vector2[8];

        void SubCell(int i, int j)
        {
            float bl = S(i, j), br = S(i + 1, j), tr = S(i + 1, j + 1), tl = S(i, j + 1);
            bool sbl = bl >= iso, sbr = br >= iso, str = tr >= iso, stl = tl >= iso;
            float h = 1f / Sub, x0 = i * h, y0 = j * h, x1 = x0 + h, y1 = y0 + h;
            if (sbl && sbr && str && stl) { Quad(x0, y0, x1, y1); return; }
            if (!sbl && !sbr && !str && !stl) return;
            // Edge crossings (B: bl-br, R: br-tr, T: tl-tr, L: bl-tl).
            Vector2 pB = new Vector2(Mathf.Lerp(x0, x1, T(bl, br)), y0), pR = new Vector2(x1, Mathf.Lerp(y0, y1, T(br, tr)));
            Vector2 pT = new Vector2(Mathf.Lerp(x0, x1, T(tl, tr)), y1), pL = new Vector2(x0, Mathf.Lerp(y0, y1, T(bl, tl)));
            int kB = Key(i, j, 0), kR = Key(i + 1, j, 1), kT = Key(i, j + 1, 0), kL = Key(i, j, 1);
            bool xB = sbl != sbr, xR = sbr != str, xT = stl != str, xL = sbl != stl;
            bool saddle = xB && xR && xT && xL;
            var cbl = new Vector2(x0, y0); var cbr = new Vector2(x1, y0); var ctr = new Vector2(x1, y1); var ctl = new Vector2(x0, y1);
            if (saddle)
            {
                bool centre = (bl + br + tr + tl) * 0.25f >= iso;
                if (centre == sbl)
                {
                    // bl / tr solid joined through the centre (or air through it): cut off br and tl.
                    Seg(kB, pB, kR, pR, cbr, sbr); Seg(kT, pT, kL, pL, ctl, stl);
                }
                else { Seg(kL, pL, kB, pB, cbl, sbl); Seg(kR, pR, kT, pT, ctr, str); } // cut off bl and tr
                if (centre) Hexagon(sbl, cbl, pB, cbr, sbr, pR, ctr, str, pT, ctl, stl, pL);
                else { if (sbl) Tri(cbl, pB, pL); if (sbr) Tri(cbr, pR, pB); if (str) Tri(ctr, pT, pR); if (stl) Tri(ctl, pL, pT); }
                return;
            }
            // One segment: the two crossed edges.
            int ka = 0, kb = 0; Vector2 pa = default, pb = default; bool first = true;
            if (xB) Take(ref first, ref ka, ref pa, ref kb, ref pb, kB, pB);
            if (xR) Take(ref first, ref ka, ref pa, ref kb, ref pb, kR, pR);
            if (xT) Take(ref first, ref ka, ref pa, ref kb, ref pb, kT, pT);
            if (xL) Take(ref first, ref ka, ref pa, ref kb, ref pb, kL, pL);
            Vector2 probe = sbl ? cbl : sbr ? cbr : str ? ctr : ctl; // a solid corner
            Seg(ka, pa, kb, pb, probe, true);
            // The solid polygon, walked CCW.
            int count = 0;
            if (sbl) poly[count++] = cbl; if (xB) poly[count++] = pB;
            if (sbr) poly[count++] = cbr; if (xR) poly[count++] = pR;
            if (str) poly[count++] = ctr; if (xT) poly[count++] = pT;
            if (stl) poly[count++] = ctl; if (xL) poly[count++] = pL;
            int v0 = fillVerts.Count;
            for (int k = 0; k < count; k++) fillVerts.Add(poly[k]);
            for (int k = 1; k + 1 < count; k++) { fillTris.Add(v0); fillTris.Add(v0 + k + 1); fillTris.Add(v0 + k); }
        }

        void Hexagon(bool sbl, Vector2 cbl, Vector2 pB, Vector2 cbr, bool sbr, Vector2 pR, Vector2 ctr, bool str, Vector2 pT, Vector2 ctl, bool stl, Vector2 pL)
        {
            int count = 0;
            if (sbl) poly[count++] = cbl; poly[count++] = pB;
            if (sbr) poly[count++] = cbr; poly[count++] = pR;
            if (str) poly[count++] = ctr; poly[count++] = pT;
            if (stl) poly[count++] = ctl; poly[count++] = pL;
            int v0 = fillVerts.Count;
            for (int k = 0; k < count; k++) fillVerts.Add(poly[k]);
            for (int k = 1; k + 1 < count; k++) { fillTris.Add(v0); fillTris.Add(v0 + k + 1); fillTris.Add(v0 + k); }
        }

        void Tri(Vector2 a, Vector2 b, Vector2 c)
        {
            int v0 = fillVerts.Count;
            fillVerts.Add(a); fillVerts.Add(b); fillVerts.Add(c);
            fillTris.Add(v0); fillTris.Add(v0 + 2); fillTris.Add(v0 + 1);
        }

        static void Take(ref bool first, ref int ka, ref Vector2 pa, ref int kb, ref Vector2 pb, int k, Vector2 p)
        {
            if (first) { ka = k; pa = p; first = false; } else { kb = k; pb = p; }
        }

        float T(float a, float b) { float t = (iso - a) / (b - a); return t < 0f ? 0f : t > 1f ? 1f : t; }

        /// <summary>A unique key per sub-cell edge: horizontal edges (dir 0) start at sub-vertex (i, j), vertical ones (dir 1).</summary>
        int Key(int i, int j, int dir) => ((j * (m + 1)) + i) * 2 + dir;

        /// <summary>Adds a segment oriented so `probe` (a corner off the segment) is on its right when `probeSolid`, on its left otherwise.</summary>
        void Seg(int k1, Vector2 p1, int k2, Vector2 p2, Vector2 probe, bool probeSolid)
        {
            var dir = p2 - p1; var to = probe - p1;
            float cross = dir.x * to.y - dir.y * to.x; // < 0: probe on the right
            if ((probeSolid && cross > 0f) || (!probeSolid && cross < 0f)) { var tk = k1; k1 = k2; k2 = tk; var tp = p1; p1 = p2; p2 = tp; }
            int s = segA.Count;
            segA.Add(k1); segB.Add(k2); segPA.Add(p1); segPB.Add(p2); used.Add(false);
            startAt[k1] = s; endAt[k2] = s;
        }

        void Chain()
        {
            // Open chains first (a start nobody ends at: the chunk's border), then the loops.
            for (int s = 0; s < segA.Count; s++) if (!used[s] && !endAt.ContainsKey(segA[s])) Walk(s, false);
            for (int s = 0; s < segA.Count; s++) if (!used[s]) Walk(s, true);
        }

        void Walk(int s, bool loop)
        {
            int start = points.Count;
            points.Add(segPA[s]);
            int cur = s;
            while (cur >= 0 && !used[cur])
            {
                used[cur] = true;
                var p = segPB[cur];
                if ((p - points[points.Count - 1]).sqrMagnitude >= MinGap * MinGap) points.Add(p);
                else if (points.Count - start > 1) points[points.Count - 1] = p; // keep the newest: a chain's border end stays exact
                cur = startAt.TryGetValue(segB[cur], out int next) ? next : -1;
            }
            if (loop && points.Count - start > 1 && (points[points.Count - 1] - points[start]).sqrMagnitude < MinGap * MinGap) points.RemoveAt(points.Count - 1); // the loop's last point is its first
            lineStart.Add(start); lineCount.Add(points.Count - start); lineClosed.Add(loop);
        }
    }
}
