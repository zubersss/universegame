using System.Collections.Generic;
using Meridian.Art;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.View2D
{
    /// <summary>
    /// U-156 (D-161 / D-162, Bible 5.0; contract v3.2 §11.9, D-163): draws a smooth planet's ground from each chunk's traced outline: one mesh
    /// per chunk, back to front: the back wall (the natural ground under its surface curve, shaded, so a dug hole shows the cross-section behind
    /// it, never the sky), the body (the outline's fill), the band (B-175's ground_band along every upward-facing stretch of the outline, bent
    /// by its normal: 24 px out, 40 px in, u by world x so chunks join) and the rim (B-175's dig_rim along walls and ceilings). On Earth the
    /// band and the desert's fill go by the column's biome (B-178: sand on the desert and the beaches, stone on the rocky shore, snow on the
    /// taiga and tundra, B-175's grass set elsewhere), crossfaded over BiomeFade at each border (U-128's smoothstep). Until the art lands the
    /// band is the grass strip's frames (a missing variant takes the grass set), the body the strip's fill colour and the rim a 0.09 m ink line.
    /// Built when a chunk's outline is (TerrainChunk.OutlineBuilt) and again when the art arrives; never per frame.
    /// </summary>
    public sealed class SmoothGround : MonoBehaviour
    {
        /// <summary>A stretch of outline carries the band where its outward normal is within 60° of up (a 35° slope's is 0.82).</summary>
        public const float SurfaceFacing = 0.5f;
        public const float RimWidth = 0.09f, BackShade = 0.55f, Z = GroundStrip.Z;
        public const int Order = GroundStrip.Order;
        static readonly Color Ink = new Color(0.12f, 0.10f, 0.09f, 1f);

        /// <summary>B-178's ground sets: 0 grass (B-175's ground_band), 1 sand, 2 stone, 3 snow.</summary>
        public const int Grass = 0, Sand = 1, Stone = 2, Snow = 3, Variants = 4;
        static readonly string[] VariantKey = { "ground_band", "ground_band_sand", "ground_band_stone", "ground_band_snow" };
        /// <summary>U-128's crossfade width at a biome border (m).</summary>
        public const float BiomeFade = 3f;
        /// <summary>An Ocean column whose ground stands at most this far over the water line is beach (sand); higher, rocky shore (stone).</summary>
        public const int BeachRise = 3;

        // Submeshes, back to front (a later one draws over an earlier one).
        const int SubBack = 0, SubBackSand = 1, SubBody = 2, SubBodySand = 3, SubBand = 4, SubRim = SubBand + Variants, SubCount = SubRim + 1;

        public TerrainStreamer terrain;
        public GroundStrip strips;
        public bool Active { get; private set; }
        /// <summary>Chunks built and the band quads laid on the last build (tests, captures).</summary>
        public int ChunksBuilt { get; private set; }
        public int LastBandQuads { get; private set; }
        /// <summary>True once B-175's band / fill / rim are in (else the placeholders draw).</summary>
        public bool BandArt => bands[Grass] != null;
        public bool FillArt => fill != null;
        /// <summary>True once B-178's set for the variant is in.</summary>
        public bool VariantArt(int variant) => bands[variant] != null;
        /// <summary>Band quads per variant on the last build (tests, captures).</summary>
        public readonly int[] LastVariantQuads = new int[Variants];

        string planet;
        bool biomes;
        readonly Sprite[] bands = new Sprite[Variants];
        Sprite fill, fillSand, rim;
        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>(8);
        readonly Dictionary<TerrainChunk, MeshFilter> meshes = new Dictionary<TerrainChunk, MeshFilter>(64);
        readonly Dictionary<Texture, Material> materials = new Dictionary<Texture, Material>(8);
        int stripsSeen = -1;

        // Mesh scratch (main thread).
        readonly List<Vector3> v = new List<Vector3>(4096);
        readonly List<Vector2> uv = new List<Vector2>(4096);
        readonly List<Color> col = new List<Color>(4096);
        readonly List<int>[] tris = new List<int>[SubCount];
        readonly List<Vector2> nrm = new List<Vector2>(256);
        readonly Material[] mats = new Material[SubCount];
        readonly Sprite[][] variantSprites = new Sprite[Variants][];
        readonly int[] variantCount = new int[Variants];
        readonly float[] variantWidth = new float[Variants];
        readonly float[] wp = new float[Variants], wq = new float[Variants];
        readonly List<Vector2> clipA = new List<Vector2>(8), clipB = new List<Vector2>(8);

        void Awake() { EnsureScratch(); }

        void EnsureScratch()
        {
            for (int i = 0; i < SubCount; i++) if (tris[i] == null) tris[i] = new List<int>(i == SubBody ? 4096 : 1024);
            for (int i = 0; i < Variants; i++) if (variantSprites[i] == null) variantSprites[i] = new Sprite[GroundStrip.TileFrames];
        }

        public void Configure(Meridian.Planets.PlanetId id, TerrainStreamer t, GroundStrip g)
        {
            Release();
            EnsureScratch();
            terrain = t; strips = g; planet = id.ToString().ToLowerInvariant();
            biomes = id == Meridian.Planets.PlanetId.Earth;
            Active = true;
            TerrainChunk.OutlineBuilt -= OnOutline;
            TerrainChunk.OutlineBuilt += OnOutline;
            for (int i = 0; i < Variants; i++)
            {
                if (i != Grass && !biomes) continue;
                int variant = i;
                Probe($"terrain/{planet}/{VariantKey[i]}", s => { bands[variant] = s; RebuildAll(); });
            }
            Probe($"terrain/{planet}/ground_fill", s => { fill = s; Repeat(s); RebuildAll(); });
            if (biomes) Probe($"terrain/{planet}/ground_fill_sand", s => { fillSand = s; Repeat(s); RebuildAll(); });
            Probe($"terrain/{planet}/dig_rim", s => { rim = s; RebuildAll(); });
            RebuildAll();
        }

        static void Repeat(Sprite s) { if (s != null && s.texture != null) s.texture.wrapMode = TextureWrapMode.Repeat; }

        public void Deactivate()
        {
            Active = false;
            TerrainChunk.OutlineBuilt -= OnOutline;
            foreach (var kv in meshes) if (kv.Value != null) kv.Value.gameObject.SetActive(false);
            Release();
        }

        void OnDestroy() { TerrainChunk.OutlineBuilt -= OnOutline; Release(); }

        void Release()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
            for (int i = 0; i < Variants; i++) bands[i] = null;
            fill = fillSand = rim = null;
        }

        /// <summary>A key not exported yet is probed quietly (D-143) and its placeholder stays.</summary>
        void Probe(string key, System.Action<Sprite> got)
        {
            var loc = Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (!exists || this == null || !Active) return;
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                handles.Add(h);
                h.Completed += op => { if (this != null && Active && op.Status == AsyncOperationStatus.Succeeded && op.Result != null && op.Result.Count > 0) got(op.Result[0]); };
            };
        }

        void LateUpdate()
        {
            // The placeholder band comes from the ground strip's frames: rebuild once they are in.
            if (!Active || strips == null) return;
            int seen = strips.MaterialsLoaded;
            if (seen != stripsSeen) { stripsSeen = seen; RebuildAll(); }
        }

        void RebuildAll()
        {
            if (!Active || terrain == null) return;
            foreach (Transform child in terrain.transform)
            {
                var c = child.GetComponent<TerrainChunk>();
                if (c != null && c.smooth) Build(c);
            }
        }

        void OnOutline(TerrainChunk c)
        {
            if (!Active || terrain == null || c == null || c.transform.parent != terrain.transform) return;
            Build(c);
        }

        Material MaterialFor(Texture tex)
        {
            if (tex == null) tex = Texture2D.whiteTexture;
            if (materials.TryGetValue(tex, out var m) && m != null) return m;
            var lit = Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.lit : null;
            m = lit != null ? new Material(lit) : new Material(Shader.Find("Sprites/Default"));
            m.name = "SmoothGround_" + tex.name;
            m.mainTexture = tex;
            materials[tex] = m;
            return m;
        }

        // ---------- B-178: the ground set by biome ----------

        /// <summary>The ground set of column x: Earth's biome (the Ocean split by height into beach and rocky shore); grass elsewhere.</summary>
        public int VariantAt(int x)
        {
            if (!biomes) return Grass;
            switch (EarthBiomes.At(x))
            {
                case Biome.Desert: return Sand;
                case Biome.Taiga: case Biome.Tundra: return Snow;
                case Biome.Ocean:
                    int top = terrain != null ? terrain.OriginalTop(x) : int.MinValue;
                    return terrain != null && terrain.Config != null && top + 1 <= terrain.Config.datumY + BeachRise ? Sand : Stone;
                default: return Grass;
            }
        }

        /// <summary>Each set's weight at world x: its share of the BiomeFade window round x, smoothstepped (U-128); they sum to 1.</summary>
        public void Weights(float x, float[] w)
        {
            for (int i = 0; i < Variants; i++) w[i] = 0f;
            if (!biomes) { w[Grass] = 1f; return; }
            float a = x - BiomeFade * 0.5f, b = x + BiomeFade * 0.5f;
            for (int c = Mathf.FloorToInt(a); c <= Mathf.FloorToInt(b); c++)
            {
                float o = Mathf.Min(b, c + 1f) - Mathf.Max(a, c);
                if (o > 0f) w[VariantAt(c)] += o / BiomeFade;
            }
            float sum = 0f;
            for (int i = 0; i < Variants; i++) { w[i] = Mathf.SmoothStep(0f, 1f, w[i]); sum += w[i]; }
            if (sum > 0f) for (int i = 0; i < Variants; i++) w[i] /= sum;
        }

        float SandWeight(float x) { Weights(x, wp); return wp[Sand]; }

        /// <summary>The band's sprites for a set, left to right, and each one's width in metres: B-178 / B-175's one 8 m sheet (a set not in yet
        /// takes the grass set's), or the grass strip's eight 1 m frames.</summary>
        int BandSprites(int variant, out float width)
        {
            width = 0f;
            var buf = variantSprites[variant];
            var sheet = bands[variant] != null ? bands[variant] : bands[Grass];
            if (sheet != null) { buf[0] = sheet; width = sheet.bounds.size.x; return 1; }
            var frames = strips != null ? strips.FramesOf(0) : null;
            if (frames == null || frames.Length == 0) return 0;
            int n = Mathf.Min(GroundStrip.TileFrames, frames.Length, buf.Length);
            for (int i = 0; i < n; i++) buf[i] = frames[i];
            width = frames[0].bounds.size.x;
            return n;
        }

        MeshFilter FilterFor(TerrainChunk c)
        {
            if (meshes.TryGetValue(c, out var f) && f != null) { if (!f.gameObject.activeSelf) f.gameObject.SetActive(true); return f; }
            var go = new GameObject("SmoothGround");
            go.transform.SetParent(c.transform, false);
            go.transform.localPosition = new Vector3(0f, 0f, Z);
            f = go.AddComponent<MeshFilter>();
            f.sharedMesh = new Mesh { name = "SmoothGround" };
            f.sharedMesh.MarkDynamic();
            var r = go.AddComponent<MeshRenderer>();
            r.sortingOrder = Order;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
            meshes[c] = f;
            return f;
        }

        void Build(TerrainChunk c)
        {
            EnsureScratch();
            var f = FilterFor(c);
            var mesh = f.sharedMesh;
            var k = c.Contour;
            const int C = TerrainConstants.ChunkSize;
            float wx0 = c.cx * C, wy0 = c.cy * C;
            v.Clear(); uv.Clear(); col.Clear();
            for (int i = 0; i < SubCount; i++) tris[i].Clear();

            // The body's sampling: B-175's fill in world space, or the strip's fill tile's colour.
            Sprite fillSprite = fill != null ? fill : strips != null ? strips.FillOf(0) : null;
            Vector2 fillUv = fillSprite != null ? Centre(fillSprite) : new Vector2(0.5f, 0.5f);
            Color fillTint = fillSprite != null ? Color.white : new Color(0.45f, 0.36f, 0.27f, 1f);
            bool worldFill = fill != null && fill.texture != null && fill.rect.width >= fill.texture.width - 0.5f;
            Vector2 FillUv(float lx, float ly) => worldFill ? new Vector2((wx0 + lx) / 8f, (wy0 + ly) / 8f) : fillUv;
            Vector2 WorldUv(float lx, float ly) => new Vector2((wx0 + lx) / 8f, (wy0 + ly) / 8f);
            var back = new Color(fillTint.r * BackShade, fillTint.g * BackShade, fillTint.b * BackShade, 1f);

            // Does any of this chunk take the desert's sand fill? (Most chunks: no, and they skip the overlay.)
            bool sandFill = false;
            if (biomes && fillSand != null && fillSand.texture != null)
                for (int i = -2; i <= C + 2 && !sandFill; i++) sandFill = SandWeight(wx0 + i) > 0f;

            // 1. The back wall: under the natural surface curve, from the chunk's foot, shaded (and the desert's sand over it, faded in).
            if (k.Lines > 0 || k.fillVerts.Count > 0)
            {
                float yb = -0.5f, yt = C - 0.5f;
                for (int i = 0; i < C; i++)
                {
                    float h0 = c.SurfaceCurve[i] - wy0, h1 = c.SurfaceCurve[i + 1] - wy0;
                    if (float.IsNaN(h0) || float.IsNaN(h1)) continue;
                    h0 = Mathf.Min(h0, yt); h1 = Mathf.Min(h1, yt);
                    if (h0 <= yb && h1 <= yb) continue;
                    float x0 = i - 0.5f, x1 = i + 0.5f;
                    BackQuad(tris[SubBack], x0, x1, yb, h0, h1, back, back, FillUv);
                    if (sandFill)
                    {
                        float s0 = SandWeight(wx0 + x0), s1 = SandWeight(wx0 + x1);
                        if (s0 > 0f || s1 > 0f)
                            BackQuad(tris[SubBackSand], x0, x1, yb, h0, h1, new Color(BackShade, BackShade, BackShade, s0), new Color(BackShade, BackShade, BackShade, s1), WorldUv);
                    }
                }
            }

            // 2. The body (and the desert's sand over it, faded in across the border).
            int fb = v.Count;
            for (int i = 0; i < k.fillVerts.Count; i++) { var p = k.fillVerts[i]; Add(p, FillUv(p.x, p.y), fillTint); }
            for (int i = 0; i < k.fillTris.Count; i++) tris[SubBody].Add(fb + k.fillTris[i]);
            if (sandFill) SandBody(k, wx0, WorldUv);

            // 3 / 4. The band along upward-facing stretches (by biome, crossfaded), the rim along the rest.
            for (int i = 0; i < Variants; i++) { variantCount[i] = BandSprites(i, out variantWidth[i]); LastVariantQuads[i] = 0; }
            int quads = 0;
            for (int line = 0; line < k.Lines; line++)
            {
                int s = k.lineStart[line], n = k.lineCount[line];
                bool closed = k.lineClosed[line];
                if (n < 2) continue;
                Normals(k.points, s, n, closed);
                float arc = 0f;
                int segs = closed ? n : n - 1;
                for (int a = 0; a < segs; a++)
                {
                    int ia = s + a, ib = s + (a + 1) % n;
                    Vector2 p = k.points[ia], q = k.points[ib];
                    Vector2 np = nrm[a], nq = nrm[(a + 1) % n];
                    var segN = Normal(q - p);
                    float len = (q - p).magnitude;
                    if (segN.y > SurfaceFacing && variantCount[Grass] > 0) quads += BandByBiome(p, q, np, nq, wx0);
                    else Rim(p, q, np, nq, arc);
                    arc += len;
                }
            }
            LastBandQuads = quads;

            mesh.Clear();
            mesh.SetVertices(v);
            mesh.SetUVs(0, uv);
            mesh.SetColors(col);
            mesh.subMeshCount = SubCount;
            for (int i = 0; i < SubCount; i++) mesh.SetTriangles(tris[i], i, false);
            mesh.bounds = new Bounds(new Vector3(C * 0.5f - 0.5f, C * 0.5f - 0.5f, 0f), new Vector3(C + 2f, C + 2f, 1f));
            mats[SubBack] = MaterialFor(fillSprite != null ? fillSprite.texture : null);
            mats[SubBody] = mats[SubBack];
            mats[SubBackSand] = MaterialFor(fillSand != null ? fillSand.texture : null);
            mats[SubBodySand] = mats[SubBackSand];
            for (int i = 0; i < Variants; i++) mats[SubBand + i] = MaterialFor(variantCount[i] > 0 ? variantSprites[i][0].texture : null);
            mats[SubRim] = MaterialFor(rim != null ? rim.texture : null);
            f.GetComponent<MeshRenderer>().sharedMaterials = mats;
            ChunksBuilt++;
        }

        void BackQuad(List<int> into, float x0, float x1, float yb, float h0, float h1, Color c0, Color c1, System.Func<float, float, Vector2> uvOf)
        {
            int b = v.Count;
            Add(new Vector3(x0, yb, 0.01f), uvOf(x0, yb), c0); Add(new Vector3(x1, yb, 0.01f), uvOf(x1, yb), c1);
            Add(new Vector3(x1, Mathf.Max(h1, yb), 0.01f), uvOf(x1, h1), c1); Add(new Vector3(x0, Mathf.Max(h0, yb), 0.01f), uvOf(x0, h0), c0);
            into.Add(b); into.Add(b + 2); into.Add(b + 1); into.Add(b); into.Add(b + 3); into.Add(b + 2);
        }

        /// <summary>The body's triangles again in the sand fill, alpha = the sand's weight: whole where the weight holds at 0 or 1 across a
        /// triangle, else clipped into 1 m slabs (column centre to column centre) so the vertex alpha follows the fade.</summary>
        void SandBody(GroundContour k, float wx0, System.Func<float, float, Vector2> uvOf)
        {
            var into = tris[SubBodySand];
            for (int t = 0; t + 2 < k.fillTris.Count; t += 3)
            {
                Vector2 a = k.fillVerts[k.fillTris[t]], b = k.fillVerts[k.fillTris[t + 1]], d = k.fillVerts[k.fillTris[t + 2]];
                float xmin = Mathf.Min(a.x, Mathf.Min(b.x, d.x)), xmax = Mathf.Max(a.x, Mathf.Max(b.x, d.x));
                // The weight across the triangle's span, at each slab edge inside it and its ends.
                float lo = 1f, hi = 0f;
                for (float x = xmin; ; x = Mathf.Min(xmax, Mathf.Floor(x + 0.5f) + 0.5f))
                {
                    float w = SandWeight(wx0 + x);
                    lo = Mathf.Min(lo, w); hi = Mathf.Max(hi, w);
                    if (x >= xmax - 1e-5f) break;
                }
                if (hi <= 0f) continue;
                if (lo >= 1f)
                {
                    int i0 = v.Count;
                    var white = Color.white;
                    Add(a, uvOf(a.x, a.y), white); Add(b, uvOf(b.x, b.y), white); Add(d, uvOf(d.x, d.y), white);
                    into.Add(i0); into.Add(i0 + 1); into.Add(i0 + 2);
                    continue;
                }
                for (float s0 = Mathf.Floor(xmin + 0.5f) - 0.5f; s0 < xmax; s0 += 1f)
                {
                    clipA.Clear(); clipA.Add(a); clipA.Add(b); clipA.Add(d);
                    ClipX(clipA, clipB, s0, true); ClipX(clipB, clipA, s0 + 1f, false);
                    if (clipA.Count < 3) continue;
                    int i0 = v.Count;
                    for (int j = 0; j < clipA.Count; j++)
                    {
                        var p = clipA[j];
                        Add(p, uvOf(p.x, p.y), new Color(1f, 1f, 1f, SandWeight(wx0 + p.x)));
                    }
                    for (int j = 1; j + 1 < clipA.Count; j++) { into.Add(i0); into.Add(i0 + j); into.Add(i0 + j + 1); }
                }
            }
        }

        /// <summary>Sutherland–Hodgman against one vertical line: keeps x ≥ edge (keepRight) or x ≤ edge.</summary>
        static void ClipX(List<Vector2> src, List<Vector2> dst, float edge, bool keepRight)
        {
            dst.Clear();
            for (int i = 0; i < src.Count; i++)
            {
                Vector2 p = src[i], q = src[(i + 1) % src.Count];
                bool pin = keepRight ? p.x >= edge : p.x <= edge, qin = keepRight ? q.x >= edge : q.x <= edge;
                if (pin) dst.Add(p);
                if (pin != qin && Mathf.Abs(q.x - p.x) > 1e-7f) dst.Add(Vector2.Lerp(p, q, (edge - p.x) / (q.x - p.x)));
            }
        }

        /// <summary>One stretch of band in the set(s) of its columns: one set at full alpha, or across a border two crossfaded (the lower set full
        /// until halfway, the upper fading in over it, so the ground never shows through mid-fade). Returns quads.</summary>
        int BandByBiome(Vector2 p, Vector2 q, Vector2 np, Vector2 nq, float wx0)
        {
            Weights(wx0 + p.x, wp); Weights(wx0 + q.x, wq);
            int first = -1, second = -1; float best = 0f, next = 0f;
            for (int i = 0; i < Variants; i++)
            {
                float m = Mathf.Max(wp[i], wq[i]);
                if (m > best) { second = first; next = best; first = i; best = m; }
                else if (m > next) { second = i; next = m; }
            }
            if (first < 0) first = Grass;
            if (second < 0 || next < 1e-3f)
            {
                int n = Band(p, q, np, nq, wx0, first, 1f, 1f);
                LastVariantQuads[first] += n;
                return n;
            }
            int lower = Mathf.Min(first, second), upper = Mathf.Max(first, second);
            float up = wp[upper] / Mathf.Max(1e-5f, wp[upper] + wp[lower]), uq = wq[upper] / Mathf.Max(1e-5f, wq[upper] + wq[lower]);
            int quads = Band(p, q, np, nq, wx0, lower, Mathf.Clamp01(2f * (1f - up)), Mathf.Clamp01(2f * (1f - uq)));
            quads += Band(p, q, np, nq, wx0, upper, Mathf.Clamp01(2f * up), Mathf.Clamp01(2f * uq));
            LastVariantQuads[lower]++; LastVariantQuads[upper]++;
            return quads;
        }

        void Add(Vector3 p, Vector2 t, Color c) { v.Add(p); uv.Add(t); col.Add(c); }

        static Vector2 Normal(Vector2 d) { var n = new Vector2(-d.y, d.x); float m = n.magnitude; return m > 1e-6f ? n / m : Vector2.up; } // the air side: left of the walk

        /// <summary>Per point: the mean of its two segments' outward normals (a chain's ends take their one segment's).</summary>
        void Normals(List<Vector2> pts, int s, int n, bool closed)
        {
            nrm.Clear();
            for (int i = 0; i < n; i++)
            {
                bool hasPrev = closed || i > 0, hasNext = closed || i < n - 1;
                Vector2 sum = Vector2.zero;
                if (hasPrev) sum += Normal(pts[s + i] - pts[s + (i - 1 + n) % n]);
                if (hasNext) sum += Normal(pts[s + (i + 1) % n] - pts[s + i]);
                float m = sum.magnitude;
                nrm.Add(m > 1e-6f ? sum / m : Vector2.up);
            }
        }

        static Vector2 Centre(Sprite sp)
        {
            var r = sp.textureRect; var t = sp.texture;
            return t != null ? new Vector2(r.center.x / t.width, r.center.y / t.height) : new Vector2(0.5f, 0.5f);
        }

        /// <summary>One stretch of a set's band from p to q (chunk-local), split where its sprites change (every `w` metres of world x): each
        /// piece a quad from its outline points out along the normal by the sprite's rows above its pivot and in by those below, its alpha
        /// running from alphaP to alphaQ. Returns quads.</summary>
        int Band(Vector2 p, Vector2 q, Vector2 np, Vector2 nq, float wx0, int variant, float alphaP, float alphaQ)
        {
            if (alphaP <= 0f && alphaQ <= 0f) return 0;
            int count = variantCount[variant];
            float w = variantWidth[variant];
            if (count <= 0 || w <= 0f) return 0;
            var sprites = variantSprites[variant];
            var into = tris[SubBand + variant];
            int quads = 0;
            float xa = wx0 + p.x, xb = wx0 + q.x;
            bool forward = xb >= xa;
            float t0 = 0f;
            while (t0 < 1f - 1e-5f)
            {
                float x = Mathf.Lerp(xa, xb, t0);
                // The next sprite boundary along x in the walk's direction.
                float cell = Mathf.Floor(x / w + (forward ? 1e-4f : -1e-4f));
                float boundary = forward ? (cell + 1f) * w : cell * w;
                float t1 = Mathf.Abs(xb - xa) < 1e-6f ? 1f : Mathf.Clamp01((boundary - xa) / (xb - xa));
                if (t1 <= t0 + 1e-6f) t1 = 1f;
                int idx = (((int)cell) % count + count) % count;
                var sp = sprites[idx];
                var r = sp.textureRect; var tex = sp.texture;
                float above = (r.height - sp.pivot.y) / sp.pixelsPerUnit, below = sp.pivot.y / sp.pixelsPerUnit;
                Vector2 a = Vector2.Lerp(p, q, t0), b = Vector2.Lerp(p, q, t1);
                Vector2 na = Vector2.Lerp(np, nq, t0).normalized, nb = Vector2.Lerp(np, nq, t1).normalized;
                float ua = (Mathf.Lerp(xa, xb, t0) / w - cell), ub = (Mathf.Lerp(xa, xb, t1) / w - cell);
                float u0 = (r.xMin + Mathf.Clamp01(ua) * r.width) / tex.width, u1 = (r.xMin + Mathf.Clamp01(ub) * r.width) / tex.width;
                float vTop = r.yMax / tex.height, vBot = r.yMin / tex.height;
                var ca = new Color(1f, 1f, 1f, Mathf.Lerp(alphaP, alphaQ, t0));
                var cb = new Color(1f, 1f, 1f, Mathf.Lerp(alphaP, alphaQ, t1));
                int i0 = v.Count;
                Add(a + na * above, new Vector2(u0, vTop), ca);
                Add(b + nb * above, new Vector2(u1, vTop), cb);
                Add(b - nb * below, new Vector2(u1, vBot), cb);
                Add(a - na * below, new Vector2(u0, vBot), ca);
                into.Add(i0); into.Add(i0 + 1); into.Add(i0 + 2); into.Add(i0); into.Add(i0 + 2); into.Add(i0 + 3);
                quads++;
                t0 = t1;
            }
            return quads;
        }

        /// <summary>One stretch of rim: B-175's dig_rim (its pivot on the ink row) along the arc, or a 0.09 m ink line centred on the outline.</summary>
        void Rim(Vector2 p, Vector2 q, Vector2 np, Vector2 nq, float arc)
        {
            float above = RimWidth * 0.5f, below = RimWidth * 0.5f;
            Vector2 uvA = new Vector2(0.5f, 0.5f), uvB = uvA, uvC = uvA, uvD = uvA;
            Color tint = Ink;
            if (rim != null && rim.texture != null)
            {
                var r = rim.textureRect; var tex = rim.texture;
                above = (r.height - rim.pivot.y) / rim.pixelsPerUnit; below = rim.pivot.y / rim.pixelsPerUnit;
                float w = rim.bounds.size.x, len = (q - p).magnitude;
                float ua = Mathf.Repeat(arc / w, 1f), ub = ua + len / w;
                if (ub > 1f) ub = 1f; // a stretch longer than the sheet's remainder clamps (stretches are ≤ ¼ m)
                float u0 = (r.xMin + ua * r.width) / tex.width, u1 = (r.xMin + ub * r.width) / tex.width;
                float vt = r.yMax / tex.height, vb = r.yMin / tex.height;
                uvA = new Vector2(u0, vt); uvB = new Vector2(u1, vt); uvC = new Vector2(u1, vb); uvD = new Vector2(u0, vb);
                tint = Color.white;
            }
            int i0 = v.Count;
            Add(p + np * above, uvA, tint); Add(q + nq * above, uvB, tint); Add(q - nq * below, uvC, tint); Add(p - np * below, uvD, tint);
            var into = tris[SubRim];
            into.Add(i0); into.Add(i0 + 1); into.Add(i0 + 2); into.Add(i0); into.Add(i0 + 2); into.Add(i0 + 3);
        }
    }
}
