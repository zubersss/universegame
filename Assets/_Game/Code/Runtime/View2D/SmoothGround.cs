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

        /// <summary>B-178's ground sets: 0 grass (B-175's ground_band), 1 sand, 2 stone, 3 snow. U-159: the four slots per planet (VariantKeys);
        /// slot 1 (Sand) is the one with a fill of its own (AltFillKey), slot 0 the planet's B-175 band.</summary>
        public const int Grass = 0, Sand = 1, Stone = 2, Snow = 3, Variants = 4;

        /// <summary>U-159 (B-178, B-181): each planet's band keys by slot (null: no such set). Pure.</summary>
        public static string[] VariantKeys(Meridian.Planets.PlanetId id) => id switch
        {
            Meridian.Planets.PlanetId.Earth => new[] { "ground_band", "ground_band_sand", "ground_band_stone", "ground_band_snow" },
            Meridian.Planets.PlanetId.Mars => new[] { "ground_band", "ground_band_basalt", "ground_band_frost", "ground_band_talus" },
            Meridian.Planets.PlanetId.Mercury => new[] { "ground_band", "ground_band_ice", null, null },
            Meridian.Planets.PlanetId.Venus => new[] { "ground_band", "ground_band_tessera", "ground_band_vent", null },
            _ => new[] { "ground_band", null, null, null },
        };

        /// <summary>U-159: slot 1's own fill (its band json's "fill"), or null when slot 1 shares the planet's ground_fill. Pure.</summary>
        public static string AltFillKey(Meridian.Planets.PlanetId id) => id switch
        {
            Meridian.Planets.PlanetId.Earth => "ground_fill_sand",
            Meridian.Planets.PlanetId.Mars => "ground_fill_basalt",
            _ => null,
        };

        /// <summary>U-159: the slot of column x on a planet by its region (Earth by biome, the Ocean by height; Mars by landform: the polar cap's
        /// frost, Olympus's basalt, the canyon's talus; Mercury's cold traps' ice; Venus's tesserae and vent fields); 0 elsewhere. `top` is the
        /// column's original top (Earth's beach test), `width` the world's (Mercury's traps wrap). Pure.</summary>
        public static int VariantFor(Meridian.Planets.PlanetId id, int x, int top, int datumY, int width)
        {
            switch (id)
            {
                case Meridian.Planets.PlanetId.Earth:
                    switch (EarthBiomes.At(x))
                    {
                        case Biome.Desert: return Sand;
                        case Biome.Taiga: case Biome.Tundra: return Snow;
                        case Biome.Ocean: return top != int.MinValue && top + 1 <= datumY + BeachRise ? Sand : Stone;
                        default: return Grass;
                    }
                case Meridian.Planets.PlanetId.Mars:
                    switch (MarsLandforms.At(x))
                    {
                        case MarsFeature.Olympus: return 1;
                        case MarsFeature.PolarCap: return 2;
                        case MarsFeature.Canyon: return 3;
                        default: return 0;
                    }
                case Meridian.Planets.PlanetId.Mercury: return width > 0 && MercuryLandforms.InColdTrap(x, width) ? 1 : 0;
                case Meridian.Planets.PlanetId.Venus:
                    switch (VenusLandforms.At(x))
                    {
                        case VenusFeature.Tessera: return 1;
                        case VenusFeature.VentField: return 2;
                        default: return 0;
                    }
                default: return 0;
            }
        }
        string[] variantKey = VariantKeys(Meridian.Planets.PlanetId.Earth);
        Meridian.Planets.PlanetId planetId;
        /// <summary>U-128's crossfade width at a biome border (m).</summary>
        public const float BiomeFade = 3f;
        /// <summary>An Ocean column whose ground stands at most this far over the water line is beach (sand); higher, rocky shore (stone).</summary>
        public const int BeachRise = 3;

        // Submeshes, back to front (a later one draws over an earlier one).
        const int SubBack = 0, SubBackSand = 1, SubBody = 2, SubBodySand = 3, SubDecor = 4, DecorSubs = 3, SubBand = SubDecor + DecorSubs,
            SubRim = SubBand + Variants, SubCount = SubRim + 1;

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

        // ---------- U-182: the fill by depth tier ----------

        /// <summary>B-203's transition between tiers (each tier json's transition_m), centred on the tier's depth.</summary>
        public const float TierTransition = 1f;
        /// <summary>Tiers 2..5's fills (B-203's ground_fill_t2..t5; null until loaded or where a planet has none).</summary>
        readonly Sprite[] tierFills = new Sprite[4];
        readonly Dictionary<Texture, Material> tierMaterials = new Dictionary<Texture, Material>(4);
        Texture2D lineTex;
        static readonly int Tier2Id = Shader.PropertyToID("_Tier2Tex"), Tier3Id = Shader.PropertyToID("_Tier3Tex"), Tier4Id = Shader.PropertyToID("_Tier4Tex"),
            Tier5Id = Shader.PropertyToID("_Tier5Tex"), LineTexId = Shader.PropertyToID("_LineTex"), LineParamsId = Shader.PropertyToID("_LineParams"),
            TierFromId = Shader.PropertyToID("_TierFrom"), TierBlendId = Shader.PropertyToID("_TierBlend");
        static readonly int[] TierIds = { Tier2Id, Tier3Id, Tier4Id, Tier5Id };

        // ---------- U-182 (folds in U-167): the fill_decor scatter by tier ----------

        /// <summary>One piece at most per DecorCell-metre world cell (cells line up across the planet's seam: every width divides by 4),
        /// with DecorChance; never within DecorBorderGap of a tier border, wholly under the natural surface, and only where every tile
        /// under it is solid (a dug piece goes with its tile).</summary>
        public const float DecorCell = 4f, DecorChance = 0.22f, DecorBorderGap = 1.4f, DecorUnderSurface = 0.4f; // the gap clears the wobble (0.6) and half the fade
        /// <summary>The decor sets: 0 tier 1 (fill_decor_n), 1 the region fill's (fill_decor_sand_n / _basalt_n), 2..5 tiers 2..5 (fill_decor_tk_n).</summary>
        public const int DecorSets = 6, DecorPerSet = 4;
        readonly Sprite[][] decor = new Sprite[DecorSets][];
        readonly Texture[] decorTex = new Texture[DecorSubs];
        int decorPending;
        bool decorDirty;
        public int LastDecorQuads { get; private set; }
        public bool DecorArt(int set) { if (decor[set] == null) return false; foreach (var d in decor[set]) if (d != null) return true; return false; }

        void ProbeDecor()
        {
            for (int i = 0; i < DecorSets; i++) { if (decor[i] == null) decor[i] = new Sprite[DecorPerSet]; System.Array.Clear(decor[i], 0, DecorPerSet); }
            string alt = AltFillKey(planetId);
            alt = alt != null && alt.StartsWith("ground_fill_") ? alt.Substring("ground_fill_".Length) : null;
            decorPending = 0;
            for (int set = 0; set < DecorSets; set++)
            {
                if (set == 1 && alt == null) continue;
                for (int n = 1; n <= DecorPerSet; n++)
                {
                    string key = set == 0 ? $"terrain/{planet}/fill_decor_{n}" : set == 1 ? $"terrain/{planet}/fill_decor_{alt}_{n}" : $"terrain/{planet}/fill_decor_t{set}_{n}";
                    int si = set, ni = n - 1;
                    decorPending++;
                    var loc = Addressables.LoadResourceLocationsAsync(key);
                    loc.Completed += l =>
                    {
                        bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                        ArtLoad.Release(l);
                        if (this == null || !Active) return;
                        if (!exists) { DecorArrived(); return; }
                        var h = ArtLoad.Asset<IList<Sprite>>(key);
                        handles.Add(h);
                        h.Completed += op =>
                        {
                            if (this == null || !Active) return;
                            if (op.Status == AsyncOperationStatus.Succeeded && op.Result != null && op.Result.Count > 0) decor[si][ni] = op.Result[0];
                            DecorArrived();
                        };
                    };
                }
            }
        }

        /// <summary>The decor rebuilds the chunks once, when the last of its probes is in (not once per sprite).</summary>
        void DecorArrived()
        {
            if (--decorPending <= 0) decorDirty = true;
        }

        /// <summary>The cell's world-wrapped column index (so a piece is the same on both sides of the seam).</summary>
        int DecorCellX(int gx)
        {
            int cells = terrain != null && terrain.Config != null ? Mathf.Max(1, Mathf.RoundToInt(terrain.Config.worldWidth / DecorCell)) : 1;
            return ((gx % cells) + cells) % cells;
        }

        void Decor(float wx0, float wy0)
        {
            for (int i = 0; i < DecorSubs; i++) decorTex[i] = null;
            int quads = 0;
            const int C = TerrainConstants.ChunkSize;
            var t = Meridian.Mining.D1Tables.Current;
            bool any = false;
            for (int i = 0; i < DecorSets && !any; i++) any = DecorArt(i);
            if (!any || terrain == null || terrain.Config == null) { LastDecorQuads = 0; return; }
            int gx0 = Mathf.FloorToInt((wx0 - 0.5f) / DecorCell), gx1 = Mathf.FloorToInt((wx0 + C - 0.5f) / DecorCell);
            int gy0 = Mathf.FloorToInt((wy0 - 0.5f) / DecorCell), gy1 = Mathf.FloorToInt((wy0 + C - 0.5f) / DecorCell);
            var white = Color.white;
            for (int gx = gx0; gx <= gx1; gx++)
            {
                int hx = DecorCellX(gx);
                for (int gy = gy0; gy <= gy1; gy++)
                {
                    if (Meridian.Mining.DigRun.Hash01(hx, gy, 7171) > DecorChance) continue;
                    float wx = gx * DecorCell + Meridian.Mining.DigRun.Hash01(hx, gy, 7172) * DecorCell;
                    float wy = gy * DecorCell + Meridian.Mining.DigRun.Hash01(hx, gy, 7173) * DecorCell;
                    if (wx < wx0 - 0.5f || wx >= wx0 + C - 0.5f || wy < wy0 - 0.5f || wy >= wy0 + C - 0.5f) continue; // the chunk holding its centre draws it
                    float depth = Meridian.Mining.DigRun.LineAt(terrain, wx) - wy;
                    bool border = false;
                    for (int k = 1; k < t.tiers.Length; k++) if (Mathf.Abs(depth - t.tiers[k].fromM) < DecorBorderGap) border = true;
                    if (border) continue;
                    int tier = TierShown(depth, t, wx);
                    int set = tier > 0 ? tier + 1 : (DecorArt(1) && SandWeight(wx) > 0.5f ? 1 : 0);
                    var pick = DecorPick(set, Meridian.Mining.DigRun.Hash01(hx, gy, 7174));
                    if (pick == null) continue;
                    var size = pick.rect.size / pick.pixelsPerUnit;
                    if (terrain.SurfaceAt(wx) - (wy + size.y * 0.5f) < DecorUnderSurface) continue; // wholly inside the natural ground
                    bool solid = true;
                    int tx0 = Mathf.RoundToInt(wx - size.x * 0.5f), tx1 = Mathf.RoundToInt(wx + size.x * 0.5f);
                    int ty0 = Mathf.RoundToInt(wy - size.y * 0.5f), ty1 = Mathf.RoundToInt(wy + size.y * 0.5f);
                    for (int tx = tx0; tx <= tx1 && solid; tx++)
                        for (int ty = ty0; ty <= ty1 && solid; ty++)
                            solid = TileId.IsSolid(terrain.GetTile(tx, ty));
                    if (!solid) continue;
                    int slot = -1;
                    for (int i = 0; i < DecorSubs; i++) if (decorTex[i] == pick.texture || decorTex[i] == null) { slot = i; break; }
                    if (slot < 0) continue; // more atlas pages than decor submeshes: this one waits
                    decorTex[slot] = pick.texture;
                    var o = UnityEngine.Sprites.DataUtility.GetOuterUV(pick);
                    float lx = wx - wx0, ly = wy - wy0, hw = size.x * 0.5f, hh = size.y * 0.5f;
                    int b = v.Count;
                    Add(new Vector3(lx - hw, ly - hh, 0f), new Vector2(o.x, o.y), white);
                    Add(new Vector3(lx + hw, ly - hh, 0f), new Vector2(o.z, o.y), white);
                    Add(new Vector3(lx + hw, ly + hh, 0f), new Vector2(o.z, o.w), white);
                    Add(new Vector3(lx - hw, ly + hh, 0f), new Vector2(o.x, o.w), white);
                    var into = tris[SubDecor + slot];
                    into.Add(b); into.Add(b + 2); into.Add(b + 1); into.Add(b); into.Add(b + 3); into.Add(b + 2);
                    quads++;
                }
            }
            LastDecorQuads = quads;
        }

        Sprite DecorPick(int set, float roll)
        {
            var arr = decor[set];
            if (arr == null) return null;
            int n = 0;
            foreach (var d in arr) if (d != null) n++;
            if (n == 0) return null;
            int want = Mathf.Min(n - 1, Mathf.FloorToInt(roll * n));
            foreach (var d in arr) { if (d == null) continue; if (want-- == 0) return d; }
            return null;
        }

        /// <summary>U-182: the fill through the tier shader (false: the plain lit fill, as before U-182; the perf probe's A/B).</summary>
        public static bool TierShader = true;
        /// <summary>Chunks waiting for their rebuild when the decor arrives, spread DecorRebuildsPerFrame a frame (no one-frame spike).</summary>
        readonly Queue<TerrainChunk> rebuildQueue = new Queue<TerrainChunk>(64);
        public const int DecorRebuildsPerFrame = 3;

        /// <summary>Every chunk again now (tests, the perf probe).</summary>
        public void RebuildNow() => RebuildAll();

        void QueueAll()
        {
            if (!Active || terrain == null) return;
            foreach (Transform child in terrain.transform)
            {
                var c = child.GetComponent<TerrainChunk>();
                if (c != null && c.smooth) rebuildQueue.Enqueue(c);
            }
        }

        /// <summary>The Surface Line by column (world y at x = column + 0.5; one RFloat texel each, Repeat), built once per planet.</summary>
        public Texture2D LineTexture => lineTex;
        /// <summary>True once the tier shader draws this planet's fill (the registry's material and the line texture are in).</summary>
        public bool TierFill => lineTex != null && Meridian.Rendering.ArtMaterials.Active != null && Meridian.Rendering.ArtMaterials.Active.groundTiers != null;
        public bool TierArt(int tier) => tier >= 2 && tier <= 5 && tierFills[tier - 2] != null;

        /// <summary>LEAD 21:5x: how far a tier border wobbles along x (m), so it reads as a rock boundary.</summary>
        public const float TierWobbleMax = 0.6f;

        /// <summary>The shader's border wobble (GroundTiers.hlsl) for tier k+2 at world x: three sines, 2-7 m wavelengths, phased per tier,
        /// at most TierWobbleMax. Pure.</summary>
        public static float TierWobble(int k, float x)
        {
            float p = 1.7f * k;
            return TierWobbleMax * (0.5f * Mathf.Sin(x * 1.71f + p) + 0.32f * Mathf.Sin(x * 0.93f + p * 1.3f + 2.1f) + 0.18f * Mathf.Sin(x * 3.1f + p * 0.7f + 4.0f));
        }

        /// <summary>The shader's tier weights (GroundTiers.hlsl) for a depth under the Surface Line at world x: tiers 2..5 each fade in
        /// across TierTransition centred on its depth (wobbled), smoothstepped. Pure.</summary>
        public static Vector4 TierWeights(float depth, Meridian.Mining.D1Tables t, float x = 0f)
        {
            var w = Vector4.zero;
            for (int k = 0; k < 4; k++)
            {
                float from = t.tiers.Length > k + 1 ? t.tiers[k + 1].fromM : 1e6f;
                float u = Mathf.Clamp01((depth + TierWobble(k, x) - (from - 0.5f * TierTransition)) / TierTransition);
                w[k] = u * u * (3f - 2f * u);
            }
            return w;
        }

        /// <summary>The tier the fill shows at a depth and x (0 = T1 ... 4 = T5): the deepest tier whose weight has reached a half. Pure.</summary>
        public static int TierShown(float depth, Meridian.Mining.D1Tables t, float x = 0f)
        {
            var w = TierWeights(depth, t, x);
            for (int k = 3; k >= 0; k--) if (w[k] >= 0.5f) return k + 1;
            return 0;
        }

        /// <summary>The line texture's range: texel = (line - lineBase) / lineSpan (R16 UNorm: full-rate bilinear on the iGPU, ~1 cm steps
        /// over the planet's span; the float format filtered at a fraction of the rate: the U-182 perf probe).</summary>
        float lineBase, lineSpan = 1f;

        void BuildLine()
        {
            if (terrain == null || terrain.Config == null) return;
            int w = terrain.Config.worldWidth;
            if (w <= 0) return;
            var heights = new float[w];
            float lo = float.MaxValue, hi = float.MinValue;
            for (int x = 0; x < w; x++) { float h = Meridian.Mining.DigRun.LineAt(terrain, x + 0.5f); heights[x] = h; if (h < lo) lo = h; if (h > hi) hi = h; }
            lineBase = lo; lineSpan = Mathf.Max(1f, hi - lo);
            bool r16 = SystemInfo.SupportsTextureFormat(TextureFormat.R16);
            var fmt = r16 ? TextureFormat.R16 : TextureFormat.RFloat;
            if (lineTex == null || lineTex.width != w || lineTex.format != fmt)
            {
                if (lineTex != null) Destroy(lineTex);
                lineTex = new Texture2D(w, 1, fmt, false, true) { wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear, name = "SurfaceLine_" + planet };
            }
            if (r16)
            {
                var px = new ushort[w];
                for (int x = 0; x < w; x++) px[x] = (ushort)Mathf.RoundToInt(Mathf.Clamp01((heights[x] - lineBase) / lineSpan) * 65535f);
                lineTex.SetPixelData(px, 0);
            }
            else
            {
                lineBase = 0f; lineSpan = 1f;
                lineTex.SetPixelData(heights, 0);
            }
            lineTex.Apply(false, false);
            foreach (var m in tierMaterials.Values) if (m != null) DressTiers(m);
        }

        /// <summary>The line's world height the shader reads at column texel x (the texture's value, decoded). Tests.</summary>
        public float LineTexel(int x) => lineTex == null ? float.NaN : lineBase + lineTex.GetPixel(x, 0).r * lineSpan;

        /// <summary>The tier material for a base fill (the planet's ground_fill, or the desert's sand): MERIDIAN/GroundTiers with the tiers,
        /// the line texture and D1_TABLES section 1's depths. Null where the registry has no tier material (the lit material draws instead).</summary>
        Material TierMaterialFor(Texture tex)
        {
            var proto = Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.groundTiers : null;
            if (proto == null || lineTex == null || tex == null) return null;
            if (tierMaterials.TryGetValue(tex, out var m) && m != null) return m;
            m = new Material(proto) { name = "GroundTiers_" + tex.name };
            m.mainTexture = tex;
            DressTiers(m);
            tierMaterials[tex] = m;
            return m;
        }

        void DressTiers(Material m)
        {
            var t = Meridian.Mining.D1Tables.Current;
            var from = Vector4.zero;
            for (int k = 0; k < 4; k++)
            {
                var s = tierFills[k];
                m.SetTexture(TierIds[k], s != null ? s.texture : Texture2D.whiteTexture);
                from[k] = s != null && t.tiers.Length > k + 1 ? t.tiers[k + 1].fromM : 1e6f; // a tier without its art never fades in
            }
            m.SetVector(TierFromId, from);
            m.SetVector(TierBlendId, new Vector4(TierTransition, TierTransition, TierTransition, TierTransition));
            if (lineTex != null) { m.SetTexture(LineTexId, lineTex); m.SetVector(LineParamsId, new Vector4(1f / lineTex.width, 8f, lineBase, lineSpan)); }
        }
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
            planetId = id;
            variantKey = VariantKeys(id);
            biomes = false;
            for (int i = 1; i < Variants; i++) biomes |= variantKey[i] != null; // U-159: the planet has region sets
            Active = true;
            TerrainChunk.OutlineBuilt -= OnOutline;
            TerrainChunk.OutlineBuilt += OnOutline;
            for (int i = 0; i < Variants; i++)
            {
                if (variantKey[i] == null) continue;
                int variant = i;
                Probe($"terrain/{planet}/{variantKey[i]}", s => { bands[variant] = s; RebuildAll(); });
            }
            Probe($"terrain/{planet}/ground_fill", s => { fill = s; Repeat(s); RebuildAll(); });
            string altFill = AltFillKey(id); // U-159: slot 1's own fill (Earth's sand, Mars's basalt)
            if (altFill != null) Probe($"terrain/{planet}/{altFill}", s => { fillSand = s; Repeat(s); RebuildAll(); });
            Probe($"terrain/{planet}/dig_rim", s => { rim = s; RebuildAll(); });
            // U-182: the tiers' fills, and the Surface Line by column for the shader.
            for (int k = 0; k < 4; k++)
            {
                int tier = k;
                Probe($"terrain/{planet}/ground_fill_t{k + 2}", s => { tierFills[tier] = s; Repeat(s); foreach (var m in tierMaterials.Values) if (m != null) DressTiers(m); });
            }
            BuildLine();
            ProbeDecor();
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

        void OnDestroy() { TerrainChunk.OutlineBuilt -= OnOutline; Release(); if (lineTex != null) Destroy(lineTex); }

        void Release()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
            for (int i = 0; i < Variants; i++) bands[i] = null;
            fill = fillSand = rim = null;
            for (int k = 0; k < tierFills.Length; k++) tierFills[k] = null;
            rebuildQueue.Clear();
            foreach (var m in tierMaterials.Values) if (m != null) Destroy(m);
            tierMaterials.Clear();
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
            if (decorDirty) { decorDirty = false; QueueAll(); } // U-182: the decor goes in over the next frames
            for (int n = 0; n < DecorRebuildsPerFrame && rebuildQueue.Count > 0; n++)
            {
                var c = rebuildQueue.Dequeue();
                if (c != null && c.smooth && c.transform.parent == terrain.transform) Build(c);
            }
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
            if (!biomes || terrain == null || terrain.Config == null) return Grass;
            int top = planetId == Meridian.Planets.PlanetId.Earth ? terrain.OriginalTop(x) : int.MinValue;
            int v = VariantFor(planetId, x, top, terrain.Config.datumY, terrain.Config.worldWidth);
            return v < Variants && variantKey[v] != null ? v : Grass;
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
            Decor(wx0, wy0); // U-182: the tier's buried pieces, over the fill

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
                    // U-157: the band only on the natural surface; a dug floor or a mound's top is earth, ink-rimmed.
                    if (segN.y > SurfaceFacing && variantCount[Grass] > 0 && OnSurface(c, (p + q) * 0.5f, wy0)) quads += BandByBiome(p, q, np, nq, wx0);
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
            // U-182: the fills draw by depth tier where the tier shader is in (worldFill: the uv is world / 8, which the shader reads back).
            mats[SubBack] = (worldFill && TierShader ? TierMaterialFor(fillSprite.texture) : null) ?? MaterialFor(fillSprite != null ? fillSprite.texture : null);
            mats[SubBody] = mats[SubBack];
            mats[SubBackSand] = (fillSand != null && TierShader ? TierMaterialFor(fillSand.texture) : null) ?? MaterialFor(fillSand != null ? fillSand.texture : null);
            mats[SubBodySand] = mats[SubBackSand];
            for (int i = 0; i < DecorSubs; i++) mats[SubDecor + i] = MaterialFor(decorTex[i]);
            for (int i = 0; i < Variants; i++) mats[SubBand + i] = MaterialFor(variantCount[i] > 0 ? variantSprites[i][0].texture : null);
            mats[SubRim] = MaterialFor(rim != null ? rim.texture : null);
            f.GetComponent<MeshRenderer>().sharedMaterials = mats;
            ChunksBuilt++;
        }

        /// <summary>U-157: a chunk-local point lies on the natural surface (within NaturalBand of the column's surface curve), not on a dug floor
        /// or a mound.</summary>
        static bool OnSurface(TerrainChunk c, Vector2 local, float wy0)
        {
            float fi = local.x + 0.5f;
            int i = Mathf.Clamp(Mathf.FloorToInt(fi), 0, TerrainConstants.ChunkSize - 1);
            float a = c.SurfaceCurve[i], b = c.SurfaceCurve[i + 1];
            if (float.IsNaN(a) || float.IsNaN(b)) return false;
            return Mathf.Abs(wy0 + local.y - Mathf.Lerp(a, b, Mathf.Clamp01(fi - i))) < NaturalBand;
        }

        /// <summary>U-157: how far off the natural surface curve a stretch still carries the band (m).</summary>
        public const float NaturalBand = 0.35f;

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
