using UnityEngine;

namespace Meridian.View2D.Living
{
    /// <summary>
    /// U-216: the living stage's STAND-IN art, painted by code when the flag is first on (nothing under Art/: the card's "a
    /// generated placeholder only"). One 1024 x 512 colour page and a normal page on the same layout, in the piece format's
    /// terms (contract §12): each piece a picture with its root as pivot, its size in metres at Ppu, how it moves, its
    /// bend numbers and its give. They exist to move, to be counted and to be priced on the built player; BLENDER's
    /// painted pieces replace them (U-217). Deterministic: the same seed paints the same page.
    /// </summary>
    public static class LivingPlaceholders
    {
        public const int Width = 1024, Height = 512;
        public const float Ppu = 96f;

        public enum Kind { Fern, Shrub, Grass, Tuft, Reed, Rock, Vine, BigLeaf, Snag, Mote, Leaf, Shaft, Cloud }
        public const int Kinds = 13;

        static readonly RectInt[] Rects =
        {
            new RectInt(4, 4, 216, 144),     // Fern     2.25 x 1.50 m
            new RectInt(228, 4, 160, 128),   // Shrub    1.67 x 1.33
            new RectInt(396, 4, 96, 56),     // Grass    1.00 x 0.58
            new RectInt(396, 68, 96, 28),    // Tuft     1.00 x 0.29 (play_front: under 0.30 m)
            new RectInt(4, 156, 72, 220),    // Reed     0.75 x 2.29
            new RectInt(84, 156, 144, 96),   // Rock     1.50 x 1.00
            new RectInt(236, 156, 40, 300),  // Vine     0.42 x 3.13 (hangs)
            new RectInt(284, 156, 200, 240), // BigLeaf  2.08 x 2.50 (the foreground's, drawn larger)
            new RectInt(520, 4, 120, 360),   // Snag     1.25 x 3.75 (a dead trunk with a branch stub: the vine's hold)
            new RectInt(4, 384, 16, 16),     // Mote
            new RectInt(24, 384, 24, 16),    // Leaf (in the air)
            new RectInt(56, 384, 48, 120),   // Shaft of light
            new RectInt(112, 400, 112, 64),  // Cloud shadow
        };

        public static RectInt RectOf(Kind k) => Rects[(int)k];
        public static Rect UvOf(Kind k) { var r = Rects[(int)k]; return new Rect((float)r.x / Width, (float)r.y / Height, (float)r.width / Width, (float)r.height / Height); }
        public static Vector2 SizeOf(Kind k) { var r = Rects[(int)k]; return new Vector2(r.width / Ppu, r.height / Ppu); }
        /// <summary>The snag's branch tip in its picture (0..1): where the vine hangs.</summary>
        public static readonly Vector2 SnagHold = new Vector2(0.86f, 0.80f);

        /// <summary>The piece as the format describes one: picture, size, root, motion, bend, give.</summary>
        public static LivingPiece Piece(Kind k)
        {
            var p = new LivingPiece { name = k.ToString(), uv = UvOf(k), sizeM = SizeOf(k), pivot = new Vector2(0.5f, 0.03f), motion = LivingMotion.Sways, bendPower = 1.5f };
            switch (k)
            {
                case Kind.Fern: p.bendFromM = 0.15f; p.bendToM = 1.3f; p.giveM = 0.22f; break;
                case Kind.Shrub: p.bendFromM = 0.3f; p.bendToM = 1.1f; p.giveM = 0.10f; break;
                case Kind.Grass: p.pivot = new Vector2(0.5f, 0.04f); p.bendFromM = 0.05f; p.bendToM = 0.6f; p.bendPower = 1.3f; p.giveM = 0.16f; break;
                case Kind.Tuft: p.pivot = new Vector2(0.5f, 0.05f); p.bendFromM = 0.03f; p.bendToM = 0.3f; p.bendPower = 1.2f; p.giveM = 0.07f; break;
                case Kind.Reed: p.pivot = new Vector2(0.5f, 0.01f); p.bendFromM = 0.2f; p.bendToM = 2.2f; p.bendPower = 2f; p.giveM = 0.30f; break;
                case Kind.BigLeaf: p.pivot = new Vector2(0.5f, 0f); p.bendFromM = 0.3f; p.bendToM = 2.4f; p.giveM = 0.12f; break;
                case Kind.Rock: p.motion = LivingMotion.Stands; p.pivot = new Vector2(0.5f, 0.1f); break;
                case Kind.Snag: p.motion = LivingMotion.Stands; p.pivot = new Vector2(0.35f, 0.02f); break;
                case Kind.Vine: p.motion = LivingMotion.Hangs; p.pivot = new Vector2(0.5f, 1f); break;
                default: p.motion = LivingMotion.Stands; p.pivot = new Vector2(0.5f, 0.5f); break; // the air's pictures
            }
            return p;
        }

        // ---------- the painter ----------

        struct Rng
        {
            uint s;
            public Rng(int seed) { s = (uint)seed * 2654435761u + 0x9E3779B9u; if (s == 0u) s = 1u; }
            public float Next() { s ^= s << 13; s ^= s >> 17; s ^= s << 5; return (s & 0xFFFFFFu) / 16777216f; }
            public float Range(float a, float b) => a + (b - a) * Next();
        }

        static void Blend(ref Color32 dst, Color32 src, float a)
        {
            float da = dst.a / 255f, oa = a + da * (1f - a);
            if (oa <= 0f) return;
            dst.r = (byte)Mathf.Clamp((src.r * a + dst.r * da * (1f - a)) / oa + 0.5f, 0f, 255f);
            dst.g = (byte)Mathf.Clamp((src.g * a + dst.g * da * (1f - a)) / oa + 0.5f, 0f, 255f);
            dst.b = (byte)Mathf.Clamp((src.b * a + dst.b * da * (1f - a)) / oa + 0.5f, 0f, 255f);
            dst.a = (byte)Mathf.Clamp(oa * 255f + 0.5f, 0f, 255f);
        }

        /// <summary>A soft round dab at (cx, cy) px, kept inside `clip` less a 2 px margin.</summary>
        static void Dab(Color32[] px, RectInt clip, float cx, float cy, float r, Color32 c, float alpha)
        {
            int x0 = Mathf.Max(clip.xMin + 2, Mathf.FloorToInt(cx - r - 1f)), x1 = Mathf.Min(clip.xMax - 3, Mathf.CeilToInt(cx + r + 1f));
            int y0 = Mathf.Max(clip.yMin + 2, Mathf.FloorToInt(cy - r - 1f)), y1 = Mathf.Min(clip.yMax - 3, Mathf.CeilToInt(cy + r + 1f));
            float soft = Mathf.Max(0.75f, r * 0.35f);
            for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                {
                    float dx = x + 0.5f - cx, dy = y + 0.5f - cy;
                    float a = alpha * Mathf.Clamp01((r - Mathf.Sqrt(dx * dx + dy * dy)) / soft);
                    if (a > 0f) Blend(ref px[y * Width + x], c, a);
                }
        }

        /// <summary>A stroke of dabs from a to b, its radius and colour running from the first to the second.</summary>
        static void Stroke(Color32[] px, RectInt clip, Vector2 a, Vector2 b, float r0, float r1, Color32 c0, Color32 c1, float alpha = 1f)
        {
            float len = (b - a).magnitude;
            int n = Mathf.Max(1, Mathf.CeilToInt(len / Mathf.Max(0.6f, Mathf.Min(r0, r1) * 0.6f)));
            for (int i = 0; i <= n; i++)
            {
                float k = (float)i / n;
                var p = Vector2.Lerp(a, b, k);
                Dab(px, clip, p.x, p.y, Mathf.Lerp(r0, r1, k), Color32.Lerp(c0, c1, k), alpha);
            }
        }

        static Color32 Tone(Color32 c, float k) => new Color32((byte)Mathf.Clamp(c.r * k, 0f, 255f), (byte)Mathf.Clamp(c.g * k, 0f, 255f), (byte)Mathf.Clamp(c.b * k, 0f, 255f), 255);

        static readonly Color32 Stem = new Color32(46, 74, 40, 255), LeafDark = new Color32(44, 92, 46, 255), LeafLight = new Color32(112, 160, 72, 255),
            Straw = new Color32(150, 146, 84, 255), Bark = new Color32(92, 78, 62, 255), BarkLight = new Color32(140, 124, 98, 255), Stone = new Color32(124, 120, 112, 255);

        /// <summary>A blade or frond from `root` at `angle` (radians from straight up, positive to the right), curling over as it goes; leaflets
        /// either side when `leaflet` is above 0. The light is the frame's: from the upper right.</summary>
        static void Frond(Color32[] px, RectInt clip, ref Rng rng, Vector2 root, float angle, float length, float r0, float curl, float leaflet, Color32 dark, Color32 light)
        {
            const int Steps = 14;
            var p = root;
            float a = angle, step = length / Steps;
            for (int i = 0; i < Steps; i++)
            {
                float k = (float)i / Steps;
                a += curl * (0.4f + k) / Steps;
                var dir = new Vector2(Mathf.Sin(a), Mathf.Cos(a));
                var q = p + dir * step;
                float lit = Mathf.Clamp01(0.45f + 0.4f * dir.x + 0.25f * k); // lighter where it leans toward the light and at the tips
                var c = Color32.Lerp(dark, light, lit);
                Stroke(px, clip, p, q, Mathf.Lerp(r0, r0 * 0.3f, k), Mathf.Lerp(r0, r0 * 0.3f, k + 1f / Steps), c, c);
                if (leaflet > 0f && i > 1)
                {
                    var side = new Vector2(dir.y, -dir.x);
                    float ll = leaflet * (1f - k * 0.8f) * rng.Range(0.8f, 1.15f);
                    var lc = Color32.Lerp(dark, light, Mathf.Clamp01(lit + rng.Range(-0.12f, 0.12f)));
                    Stroke(px, clip, q, q + (side + dir * 0.6f).normalized * ll, r0 * 0.9f, 0.6f, lc, lc);
                    Stroke(px, clip, q, q + (-side + dir * 0.6f).normalized * ll, r0 * 0.9f, 0.6f, Tone(lc, 0.86f), Tone(lc, 0.86f));
                }
                p = q;
            }
        }

        static void PaintFern(Color32[] px, RectInt r, ref Rng rng)
        {
            var root = new Vector2(r.x + r.width * 0.5f, r.y + r.height * 0.03f + 2f);
            for (int i = 0; i < 9; i++)
            {
                float a = Mathf.Lerp(-1.25f, 1.25f, i / 8f) + rng.Range(-0.08f, 0.08f);
                float len = Mathf.Min(r.height * 0.92f, r.width * 0.5f) * (1.05f - 0.25f * Mathf.Abs(a)) * rng.Range(0.85f, 1f);
                Frond(px, r, ref rng, root, a, len, 2.2f, a * 0.9f, 9f, LeafDark, LeafLight);
            }
        }

        static void PaintShrub(Color32[] px, RectInt r, ref Rng rng)
        {
            var root = new Vector2(r.x + r.width * 0.5f, r.y + r.height * 0.03f + 2f);
            var mid = new Vector2(r.x + r.width * 0.5f, r.y + r.height * 0.56f);
            for (int i = 0; i < 4; i++) Stroke(px, r, root, mid + new Vector2(rng.Range(-0.3f, 0.3f) * r.width, rng.Range(-0.1f, 0.2f) * r.height), 3f, 1.4f, Bark, Stem);
            for (int i = 0; i < 70; i++)
            {
                float ang = rng.Range(0f, Mathf.PI * 2f), rad = Mathf.Sqrt(rng.Next());
                var c = mid + new Vector2(Mathf.Cos(ang) * rad * r.width * 0.40f, Mathf.Sin(ang) * rad * r.height * 0.36f);
                float lit = Mathf.Clamp01(0.35f + 0.5f * (c.x - mid.x) / (r.width * 0.4f) * 0.5f + 0.5f * (c.y - mid.y) / (r.height * 0.36f) * 0.6f + i / 140f);
                var col = Color32.Lerp(LeafDark, LeafLight, lit);
                var tip = c + new Vector2(rng.Range(-1f, 1f), rng.Range(-0.2f, 1f)).normalized * rng.Range(7f, 12f);
                Stroke(px, r, c, tip, 4.2f, 1.2f, col, Tone(col, 1.08f));
            }
        }

        static void PaintGrass(Color32[] px, RectInt r, ref Rng rng, int blades, float reach)
        {
            for (int i = 0; i < blades; i++)
            {
                var root = new Vector2(r.x + r.width * (0.5f + rng.Range(-0.2f, 0.2f)), r.y + 3f);
                float a = rng.Range(-0.9f, 0.9f);
                Frond(px, r, ref rng, root, a, r.height * reach * rng.Range(0.7f, 1f), 1.9f, a * 1.2f, 0f, Tone(LeafDark, 1.05f), Color32.Lerp(LeafLight, Straw, 0.35f));
            }
        }

        static void PaintReed(Color32[] px, RectInt r, ref Rng rng)
        {
            for (int i = 0; i < 5; i++)
            {
                var root = new Vector2(r.x + r.width * (0.5f + rng.Range(-0.12f, 0.12f)), r.y + 3f);
                float a = rng.Range(-0.12f, 0.12f), len = r.height * rng.Range(0.72f, 0.9f);
                var top = root + new Vector2(Mathf.Sin(a), Mathf.Cos(a)) * len;
                Stroke(px, r, root, top, 1.9f, 1.1f, Tone(Straw, 0.8f), Straw);
                Stroke(px, r, top, top + new Vector2(Mathf.Sin(a) * 1.5f, 1f).normalized * 20f, 3.4f, 1.2f, Bark, BarkLight); // the seed head
                var leafAt = Vector2.Lerp(root, top, rng.Range(0.25f, 0.55f));
                Stroke(px, r, leafAt, leafAt + new Vector2(rng.Range(-1f, 1f) > 0f ? 18f : -18f, 22f), 1.8f, 0.6f, LeafDark, LeafLight);
            }
        }

        /// <summary>A rounded stone lit from the upper right; its dome is written to the normal page too (the lit piece).</summary>
        static void PaintRock(Color32[] px, Color32[] normals, RectInt r, ref Rng rng)
        {
            float cx = r.x + r.width * 0.5f, cy = r.y + r.height * 0.42f, rx = r.width * 0.44f, ry = r.height * 0.40f;
            var lightDir = new Vector3(0.5f, 0.6f, 0.62f).normalized;
            for (int y = r.yMin + 2; y < r.yMax - 2; y++)
                for (int x = r.xMin + 2; x < r.xMax - 2; x++)
                {
                    float u = (x + 0.5f - cx) / rx, v = (y + 0.5f - cy) / ry;
                    float d = Mathf.Pow(Mathf.Pow(Mathf.Abs(u), 2.6f) + Mathf.Pow(Mathf.Abs(v), 2.6f), 1f / 2.6f); // a rounded box
                    if (d >= 1f) continue;
                    float z = Mathf.Sqrt(Mathf.Max(0f, 1f - d * d));
                    var n = new Vector3(u * 0.9f, v * 0.9f, z + 0.25f).normalized;
                    float speck = Meridian.Mining.DigRun.Hash01(x / 3, y / 3, 9911) * 0.14f - 0.07f;
                    float lit = Mathf.Clamp01(0.42f + 0.62f * Vector3.Dot(n, lightDir) + speck);
                    float a = Mathf.Clamp01((1f - d) * 14f);
                    Blend(ref px[y * Width + x], Tone(Stone, 0.55f + 0.75f * lit), a);
                    // the normal as the shader unpacks an uncompressed map: x in R (alpha 1), y in G
                    normals[y * Width + x] = new Color32((byte)(n.x * 127.5f + 127.5f), (byte)(n.y * 127.5f + 127.5f), (byte)(n.z * 127.5f + 127.5f), 255);
                }
        }

        static void PaintVine(Color32[] px, RectInt r, ref Rng rng)
        {
            float cx = r.x + r.width * 0.5f;
            Vector2 last = new Vector2(cx, r.yMax - 3f);
            for (float y = r.yMax - 3f; y > r.yMin + 4f; y -= 4f)
            {
                var p = new Vector2(cx + 5f * Mathf.Sin(y * 0.07f), y);
                Stroke(px, r, last, p, 2.3f, 2.3f, Tone(Stem, 0.9f), Stem);
                last = p;
            }
            int n = 0;
            for (float y = r.yMax - 16f; y > r.yMin + 14f; y -= 21f, n++)
            {
                var p = new Vector2(cx + 5f * Mathf.Sin(y * 0.07f), y);
                float side = (n & 1) == 0 ? 1f : -1f;
                var c = Color32.Lerp(LeafDark, LeafLight, side > 0f ? 0.7f : 0.3f);
                Stroke(px, r, p, p + new Vector2(side * 11f, -7f), 4f, 1.2f, c, Tone(c, 1.1f));
            }
        }

        static void PaintBigLeaf(Color32[] px, RectInt r, ref Rng rng)
        {
            var dark = new Color32(22, 50, 40, 255); var light = new Color32(46, 88, 60, 255);
            var root = new Vector2(r.x + r.width * 0.5f, r.y + 3f);
            var tip = new Vector2(r.x + r.width * 0.62f, r.yMax - 8f);
            Stroke(px, r, root, Vector2.Lerp(root, tip, 0.25f), 4f, 3f, dark, dark); // the stalk
            for (int i = 0; i <= 60; i++)
            {
                float k = i / 60f;
                var mid = Vector2.Lerp(Vector2.Lerp(root, tip, 0.22f), tip, k) + new Vector2(Mathf.Sin(k * 2.2f) * 10f, 0f);
                float half = r.width * 0.36f * Mathf.Sin(Mathf.PI * Mathf.Pow(k, 0.8f));
                var c = Color32.Lerp(dark, light, 0.25f + 0.5f * k + ((i & 3) == 0 ? -0.18f : 0f)); // the stripes
                Stroke(px, r, mid - new Vector2(half, half * 0.25f), mid + new Vector2(half, half * 0.25f), 4.5f, 4.5f, Tone(c, 0.9f), c);
            }
            Stroke(px, r, Vector2.Lerp(root, tip, 0.22f), tip, 2.2f, 1f, Tone(light, 1.15f), Tone(light, 1.15f)); // the midrib
        }

        static void PaintSnag(Color32[] px, RectInt r, ref Rng rng)
        {
            float bx = r.x + r.width * 0.35f;
            for (float y = r.y + 3f; y < r.yMax - 10f; y += 3f)
            {
                float k = (y - r.y) / r.height, half = Mathf.Lerp(17f, 9f, k);
                float x = bx + 3f * Mathf.Sin(y * 0.03f);
                Stroke(px, r, new Vector2(x - half, y), new Vector2(x + half, y), 3.2f, 3.2f, Tone(Bark, 0.8f), BarkLight); // lit on its right
            }
            var from = new Vector2(bx + 6f, r.y + r.height * 0.72f);
            var hold = new Vector2(r.x + r.width * SnagHold.x, r.y + r.height * SnagHold.y);
            Stroke(px, r, from, hold, 6f, 3f, Bark, BarkLight); // the branch stub the vine hangs from
            for (int i = 0; i < 14; i++) // moss
                Dab(px, r, bx + rng.Range(-12f, 12f), r.y + rng.Range(0.05f, 0.9f) * r.height, rng.Range(2f, 4f), Color32.Lerp(LeafDark, LeafLight, rng.Next()), 0.8f);
        }

        static void PaintAir(Color32[] px)
        {
            var white = new Color32(255, 255, 255, 255);
            var m = RectOf(Kind.Mote);
            Dab(px, m, m.x + m.width * 0.5f, m.y + m.height * 0.5f, 4.5f, white, 1f);
            var l = RectOf(Kind.Leaf);
            Stroke(px, l, new Vector2(l.x + 5f, l.y + 8f), new Vector2(l.xMax - 6f, l.y + 8f), 1.2f, 3.4f, new Color32(150, 150, 70, 255), new Color32(190, 170, 80, 255));
            Stroke(px, l, new Vector2(l.x + 12f, l.y + 8f), new Vector2(l.xMax - 5f, l.y + 8f), 3.4f, 0.8f, new Color32(190, 170, 80, 255), new Color32(170, 140, 60, 255));
            var s = RectOf(Kind.Shaft); // a band of light: soft at its sides, fading toward the ground
            for (int y = s.yMin + 2; y < s.yMax - 2; y++)
                for (int x = s.xMin + 2; x < s.xMax - 2; x++)
                {
                    float u = (x + 0.5f - s.x) / s.width, v = (y + 0.5f - s.y) / s.height;
                    float a = Mathf.Pow(Mathf.Sin(Mathf.PI * u), 1.6f) * Mathf.SmoothStep(0f, 1f, v) * Mathf.SmoothStep(0f, 0.12f, 1f - v);
                    px[y * Width + x] = new Color32(255, 255, 255, (byte)(a * 255f));
                }
            var c = RectOf(Kind.Cloud); // a soft oval
            for (int y = c.yMin + 2; y < c.yMax - 2; y++)
                for (int x = c.xMin + 2; x < c.xMax - 2; x++)
                {
                    float u = (x + 0.5f - c.x) / c.width * 2f - 1f, v = (y + 0.5f - c.y) / c.height * 2f - 1f;
                    float a = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(1f - (u * u + v * v)));
                    px[y * Width + x] = new Color32(255, 255, 255, (byte)(a * 255f));
                }
        }

        /// <summary>Colour bled outward under alpha 0 (contract §2), so a bent mesh and a small mip pull no dark fringe.</summary>
        static void Bleed(Color32[] px, int rounds)
        {
            var from = new Color32[px.Length];
            for (int n = 0; n < rounds; n++)
            {
                System.Array.Copy(px, from, px.Length);
                for (int y = 1; y < Height - 1; y++)
                    for (int x = 1; x < Width - 1; x++)
                    {
                        int i = y * Width + x;
                        if (from[i].a != 0 || (from[i].r | from[i].g | from[i].b) != 0) continue;
                        Color32 pick = default; bool found = false;
                        if (Painted(from[i - 1])) { pick = from[i - 1]; found = true; }
                        else if (Painted(from[i + 1])) { pick = from[i + 1]; found = true; }
                        else if (Painted(from[i - Width])) { pick = from[i - Width]; found = true; }
                        else if (Painted(from[i + Width])) { pick = from[i + Width]; found = true; }
                        if (found) px[i] = new Color32(pick.r, pick.g, pick.b, 0);
                    }
            }
        }

        static bool Painted(Color32 c) => c.a != 0 || (c.r | c.g | c.b) != 0;

        /// <summary>Paints the two pages. `colour` and `normal` are new textures (the caller owns and destroys them); `readable` keeps
        /// their pixels on the CPU side (a capture that writes the page out).</summary>
        public static void Paint(int seed, out Texture2D colour, out Texture2D normal, bool readable = false)
        {
            var px = new Color32[Width * Height];
            var nm = new Color32[Width * Height];
            var flat = new Color32(128, 128, 255, 255);
            for (int i = 0; i < nm.Length; i++) nm[i] = flat;
            var rng = new Rng(seed);
            PaintFern(px, RectOf(Kind.Fern), ref rng);
            PaintShrub(px, RectOf(Kind.Shrub), ref rng);
            PaintGrass(px, RectOf(Kind.Grass), ref rng, 16, 0.95f);
            PaintGrass(px, RectOf(Kind.Tuft), ref rng, 12, 0.9f);
            PaintReed(px, RectOf(Kind.Reed), ref rng);
            PaintRock(px, nm, RectOf(Kind.Rock), ref rng);
            PaintVine(px, RectOf(Kind.Vine), ref rng);
            PaintBigLeaf(px, RectOf(Kind.BigLeaf), ref rng);
            PaintSnag(px, RectOf(Kind.Snag), ref rng);
            PaintAir(px);
            Bleed(px, 4);
            colour = new Texture2D(Width, Height, TextureFormat.RGBA32, true, false) { name = "LivingStagePlaceholder", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            colour.SetPixels32(px);
            colour.Apply(true, !readable);
            normal = new Texture2D(Width, Height, TextureFormat.RGBA32, true, true) { name = "LivingStagePlaceholderNormal", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            normal.SetPixels32(nm);
            normal.Apply(true, !readable);
        }
    }
}
