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
            SubRim = SubBand + Variants, SubTop = SubRim + 1, TopSubs = 5, SubCount = SubTop + TopSubs;

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

        /// <summary>The transition between tiers, centred on the tier's depth. U-196 (LEAD 17:3x, on u196/1 and u200/2): 0.35 m, where
        /// B-203's jsons say transition_m 1.0 (they stay until those fills are next exported): across a metre two differently patterned
        /// fills blended into a soft dark smudge that read as a stain or a shadow; at 0.35 m a border reads as a boundary between layers.</summary>
        public const float TierTransition = 0.35f;
        /// <summary>Tiers 2..5's fills (B-203's ground_fill_t2..t5; null until loaded or where a planet has none).</summary>
        readonly Sprite[] tierFills = new Sprite[4];

        // ---------- U-196 (B-230): the dug cell's back face ----------

        /// <summary>B-230's back walls (terrain/&lt;planet&gt;/back_wall_t1..t5: cut earth one step darker than its tier's fill, no ink
        /// outline, a 256 px tile at 64 px a metre; null until loaded or where a planet has none).</summary>
        readonly Sprite[] walls = new Sprite[5];
        Material wallMaterial;
        /// <summary>A wall tile's side in metres (the fills' is 8).</summary>
        public const float WallTileM = 4f;
        static readonly int TileTexelsId = Shader.PropertyToID("_TileTexels");
        /// <summary>The back wall draws B-230's tiles (false: the fill shaded, as before the art and where a planet has no walls).</summary>
        public bool WallArt => wallMaterial != null && walls[0] != null;
        /// <summary>Tier `tier`'s wall (1..5) is in.</summary>
        public bool WallTier(int tier) => tier >= 1 && tier <= 5 && walls[tier - 1] != null;
        public Material WallMaterialNow => wallMaterial;

        /// <summary>The back wall's material: MERIDIAN/GroundTiers over the walls (t1 its base, t2..t5 by depth under the Surface Line, as
        /// the fills crossfade), read at world / 4. The same shader on the submesh the back wall already had: no draw call more. Null
        /// until the first wall is in or where the registry has no tier material: the fill's own material then draws the wall, shaded.</summary>
        Material WallMaterial()
        {
            if (!TierShader || walls[0] == null || walls[0].texture == null || lineTex == null) return null;
            var proto = Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.groundTiers : null;
            if (proto == null) return null;
            if (wallMaterial == null) { wallMaterial = new Material(proto) { name = "GroundWalls_" + planet }; DressWalls(); }
            return wallMaterial;
        }

        void DressWalls()
        {
            var m = wallMaterial;
            if (m == null || walls[0] == null || walls[0].texture == null) return;
            m.mainTexture = walls[0].texture;
            var t = Meridian.Mining.D1Tables.Current;
            var from = Vector4.zero;
            for (int k = 0; k < 4; k++)
            {
                var s = walls[k + 1];
                m.SetTexture(TierIds[k], s != null ? s.texture : walls[0].texture);
                from[k] = s != null && t.tiers.Length > k + 1 ? t.tiers[k + 1].fromM : 1e6f; // a tier without its wall keeps the one over it
            }
            m.SetVector(TierFromId, from);
            m.SetVector(TierBlendId, new Vector4(TierTransition, TierTransition, TierTransition, TierTransition));
            m.SetFloat(TileTexelsId, walls[0].texture.width);
            if (lineTex != null) { m.SetTexture(LineTexId, lineTex); m.SetVector(LineParamsId, new Vector4(1f / lineTex.width, WallTileM, lineBase, lineSpan)); }
        }

        /// <summary>Tests: the materials a chunk's ground mesh draws its back wall and its body with (false where the chunk has no mesh).</summary>
        public bool ChunkMaterials(TerrainChunk c, out Material backWall, out Material body)
        {
            backWall = body = null;
            if (c == null || !meshes.TryGetValue(c, out var f) || f == null) return false;
            var m = f.GetComponent<MeshRenderer>().sharedMaterials;
            if (m == null || m.Length <= SubBody) return false;
            backWall = m[SubBack]; body = m[SubBody];
            return true;
        }

        /// <summary>The smooth ground of the planet side that is up (null between planets).</summary>
        public static SmoothGround Current { get; private set; }
        /// <summary>D-190 (1): column x draws the band's own fill (Earth's sand, Mars's basalt) more than the planet's ground_fill.</summary>
        public bool BandFillAt(float x) => Active && biomes && fillSand != null && SandWeight(x) >= 0.5f;
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
                    int tier = TierShown(depth, t, wx, WobbleKeepAt(wx));
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

        // ---------- U-186: the brink lips and the surface decor ----------

        /// <summary>A natural brink (LEAD 22:1x: natural only; a dug edge has its dig_rim): a node of the natural surface curve where a gentle
        /// stretch (|slope| at most LipGentle) turns into a fall of at least LipSteep a metre over the next LipRun metres, the sharpest node of
        /// the turn. The lip's pivot sits on the node, turned to the gentle side's tangent, mirrored for a drop to the left: its curl wraps down
        /// over the edge.</summary>
        public const float LipGentle = 0.3f, LipSteep = 0.55f, LipTurn = 0.6f;
        public const int LipRun = 2;
        /// <summary>The surface decor: one piece at most per SurfaceDecorCell metres of surface (SurfaceDecorChance), on stretches no steeper
        /// than SurfaceDecorMaxSlope, never on a POI's pad or a dug cell (only the natural surface carries the band).</summary>
        public const float SurfaceDecorCell = 3f, SurfaceDecorChance = 0.3f, SurfaceDecorMaxSlope = 0.45f;
        public const int SurfaceDecorPerSet = 6;
        readonly Sprite[] lips = new Sprite[Variants];
        readonly Sprite[][] surfaceDecor = new Sprite[Variants][];
        readonly Texture[] topTex = new Texture[TopSubs];
        int topPending;
        /// <summary>Lips / decor pieces left out because their chunk already had TopSubs atlas pages (diagnostics).</summary>
        public int TopSlotRejects { get; private set; }
        /// <summary>The distinct textures (atlas pages) of the loaded lips and surface decor (diagnostics).</summary>
        public int TopTextures { get { var set = new HashSet<Texture>(); for (int v = 0; v < Variants; v++) { if (lips[v] != null) set.Add(lips[v].texture); if (surfaceDecor[v] != null) foreach (var d in surfaceDecor[v]) if (d != null) set.Add(d.texture); } return set.Count; } }
        public int LastLips { get; private set; }
        public int LastSurfaceDecor { get; private set; }
        readonly Dictionary<TerrainChunk, Vector2Int> topCounts = new Dictionary<TerrainChunk, Vector2Int>(64);
        /// <summary>Lips and surface decor pieces over every chunk built now (captures, tests).</summary>
        public Vector2Int TopShown { get { var t = Vector2Int.zero; foreach (var kv in topCounts) if (kv.Key != null && kv.Key.gameObject.activeInHierarchy) t += kv.Value; return t; } }
        public bool LipArt(int variant) => lips[variant] != null;
        public bool SurfaceDecorArt(int variant) { var a = surfaceDecor[variant]; if (a == null) return false; foreach (var d in a) if (d != null) return true; return false; }

        /// <summary>The gentle side's slope (rise toward the drop, m a metre) and the fall's (m a metre, positive falling) at node n over
        /// LipRun metres each side: the curve's smoothing rounds a cliff's corner over a few nodes, so one node's step never shows it.</summary>
        public static void BrinkSlopes(System.Func<int, float> curve, int n, int side, out float gentle, out float fall)
        {
            gentle = side > 0 ? (curve(n) - curve(n - LipRun)) / LipRun : (curve(n) - curve(n + LipRun)) / LipRun;
            fall = side > 0 ? (curve(n) - curve(n + LipRun)) / LipRun : (curve(n) - curve(n - LipRun)) / LipRun;
        }

        static float Turn(System.Func<int, float> curve, int n, int side) { BrinkSlopes(curve, n, side, out float g, out float f); return g + f; }

        /// <summary>U-186: is node n of the natural surface curve (CurveAt(n) at x = n + 0.5) a brink? `side` +1 for a drop to the right, -1
        /// to the left; `angleDeg` the gentle side's tangent. Pure over the curve.</summary>
        public static bool NaturalBrink(System.Func<int, float> curve, int n, out int side, out float angleDeg)
        {
            side = 0; angleDeg = 0f;
            for (int sd = 1; sd >= -1; sd -= 2)
            {
                BrinkSlopes(curve, n, sd, out float gentle, out float fall);
                if (Mathf.Abs(gentle) > LipGentle || fall < LipSteep) continue;
                float turn = gentle + fall;
                if (turn < LipTurn) continue;
                // the sharpest node of the turn (one lip a brink, not one a column round a rounded crest)
                if (Turn(curve, n - sd, sd) > turn || Turn(curve, n + sd, sd) >= turn) continue;
                side = sd;
                angleDeg = Mathf.Atan(sd > 0 ? gentle : -gentle) * Mathf.Rad2Deg; // the tangent of the surface leading to the brink
                return true;
            }
            return false;
        }

        /// <summary>A band set's suffix (ground_band_sand: "sand"; the planet's base set: null). Pure.</summary>
        public static string VariantSuffix(Meridian.Planets.PlanetId id, int variant)
        {
            var k = VariantKeys(id);
            if (variant <= 0 || variant >= k.Length || k[variant] == null) return null;
            return k[variant].StartsWith("ground_band_") ? k[variant].Substring("ground_band_".Length) : null;
        }

        /// <summary>The variant's lip key (ground_lip_suffix; the base ground_lip for the base set). Pure.</summary>
        public static string LipKey(Meridian.Planets.PlanetId id, int variant)
        {
            string sfx = VariantSuffix(id, variant);
            string planetName = id.ToString().ToLowerInvariant();
            return sfx == null ? $"terrain/{planetName}/ground_lip" : $"terrain/{planetName}/ground_lip_{sfx}";
        }

        /// <summary>The variant's n-th surface decor key (ground_decor_n for the base set, ground_decor_suffix_n). Pure.</summary>
        public static string SurfaceDecorKey(Meridian.Planets.PlanetId id, int variant, int n)
        {
            string sfx = VariantSuffix(id, variant);
            string planetName = id.ToString().ToLowerInvariant();
            return sfx == null ? $"terrain/{planetName}/ground_decor_{n}" : $"terrain/{planetName}/ground_decor_{sfx}_{n}";
        }

        /// <summary>The planet's dig puff key. D-190 (3): one puff a planet, coloured by its tint; the band sets' own puffs
        /// (dig_puff_sand, _snow, ...) are retired and no key is built for them. Pure.</summary>
        public static string PuffKey(Meridian.Planets.PlanetId id) => $"terrain/{id.ToString().ToLowerInvariant()}/dig_puff";

        void ProbeTop()
        {
            topPending = 0;
            for (int v = 0; v < Variants; v++)
            {
                lips[v] = null;
                if (surfaceDecor[v] == null) surfaceDecor[v] = new Sprite[SurfaceDecorPerSet];
                System.Array.Clear(surfaceDecor[v], 0, SurfaceDecorPerSet);
                if (variantKey[v] == null) continue;
                int vi = v;
                ProbeTopKey(LipKey(planetId, v), s => lips[vi] = s);
                for (int n = 1; n <= SurfaceDecorPerSet; n++) { int ni = n - 1; ProbeTopKey(SurfaceDecorKey(planetId, v, n), s => surfaceDecor[vi][ni] = s); }
            }
        }

        /// <summary>A lip or decor key, probed quietly (a set has as many pieces as BLENDER drew); the chunks rebuild once all are in.</summary>
        void ProbeTopKey(string key, System.Action<Sprite> got)
        {
            topPending++;
            var loc = Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (this == null || !Active) return;
                if (!exists) { TopArrived(); return; }
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                handles.Add(h);
                h.Completed += op =>
                {
                    if (this == null || !Active) return;
                    if (op.Status == AsyncOperationStatus.Succeeded && op.Result != null && op.Result.Count > 0) got(op.Result[0]);
                    TopArrived();
                };
            };
        }

        void TopArrived() { if (--topPending <= 0) decorDirty = true; }

        bool OnPad(float worldX) => terrain != null && terrain.PadTop(Mathf.RoundToInt(worldX)) != int.MinValue;

        bool IsBand(TerrainChunk c, Vector2 p, Vector2 q, float wy0) => Normal(q - p).y > SurfaceFacing && OnSurface(c, (p + q) * 0.5f, wy0);

        /// <summary>The lips (on the natural brinks) and the surface decor over the chunk's band (after the band and the rim: drawn over both).</summary>
        void TopSprites(TerrainChunk c, GroundContour k, float wx0, float wy0)
        {
            for (int i = 0; i < TopSubs; i++) topTex[i] = null;
            int lipsN = 0, decorN = 0;
            const int C = TerrainConstants.ChunkSize;
            for (int line = 0; line < k.Lines; line++)
            {
                int s0 = k.lineStart[line], n = k.lineCount[line];
                bool closed = k.lineClosed[line];
                if (n < 2) continue;
                int segs = closed ? n : n - 1;
                for (int a = 0; a < segs; a++)
                {
                    Vector2 p = k.points[s0 + a], q = k.points[s0 + (a + 1) % n];
                    if (IsBand(c, p, q, wy0)) decorN += SurfaceDecorOn(p, q, wx0, wy0, C);
                }
            }
            // The natural brinks whose node lies in this chunk (x = n + 0.5 in [wx0 - 0.5, wx0 + C - 0.5)).
            int x0 = Mathf.RoundToInt(wx0);
            System.Func<int, float> curve = terrain.CurveAt;
            for (int nn = x0 - 1; nn < x0 + C - 1; nn++)
            {
                if (!NaturalBrink(curve, nn, out int side, out float angle)) continue;
                float y = terrain.CurveAt(nn);
                float ly = y - wy0;
                if (ly < -0.5f || ly >= C - 0.5f) continue;
                if (terrain.PadTop(nn) != int.MinValue || terrain.PadTop(nn + 1) != int.MinValue) continue;
                // intact: the high side's two cells under the brink still stand (dug away, the lip goes with them)
                int top = side > 0 ? nn : nn + 1, row = Mathf.FloorToInt(y - 0.5f);
                if (!TileId.IsSolid(terrain.GetTile(top, row)) || !TileId.IsSolid(terrain.GetTile(top, row - 1))) continue;
                int variant = VariantAt(top);
                var sprite = lips[variant] != null ? lips[variant] : lips[Grass];
                if (sprite != null && TopQuad(sprite, new Vector2(nn + 0.5f - wx0, ly), side < 0, angle)) lipsN++;
            }
            LastLips = lipsN; LastSurfaceDecor = decorN;
            topCounts[c] = new Vector2Int(lipsN, decorN);
        }

        int SurfaceDecorOn(Vector2 p, Vector2 q, float wx0, float wy0, int C)
        {
            float x0 = Mathf.Min(p.x, q.x), x1 = Mathf.Max(p.x, q.x);
            if (x1 - x0 < 1e-4f || Mathf.Abs(q.y - p.y) / (x1 - x0) > SurfaceDecorMaxSlope) return 0;
            int placed = 0;
            int g0 = Mathf.FloorToInt((wx0 + x0) / SurfaceDecorCell), g1 = Mathf.FloorToInt((wx0 + x1) / SurfaceDecorCell);
            for (int g = g0; g <= g1; g++)
            {
                int hx = SurfaceCellX(g);
                if (Meridian.Mining.DigRun.Hash01(hx, 31, 8181) > SurfaceDecorChance) continue;
                float wx = g * SurfaceDecorCell + Meridian.Mining.DigRun.Hash01(hx, 31, 8182) * SurfaceDecorCell;
                float lx = wx - wx0;
                if (lx < x0 || lx >= x1 || lx < -0.5f || lx >= C - 0.5f) continue; // the segment (and the chunk) holding the spot draws it
                if (OnPad(wx)) continue;
                int variant = VariantAt(Mathf.RoundToInt(wx));
                var pick = SurfacePick(variant, Meridian.Mining.DigRun.Hash01(hx, 31, 8183));
                if (pick == null) continue;
                float ly = Mathf.Lerp(p.y, q.y, (lx - p.x) / (q.x - p.x));
                if (TopQuad(pick, new Vector2(lx, ly), false)) placed++;
            }
            return placed;
        }

        int SurfaceCellX(int g)
        {
            int cells = terrain != null && terrain.Config != null ? Mathf.Max(1, Mathf.RoundToInt(terrain.Config.worldWidth / SurfaceDecorCell)) : 1;
            return ((g % cells) + cells) % cells;
        }

        Sprite SurfacePick(int variant, float roll)
        {
            var arr = surfaceDecor[variant];
            int n = 0;
            if (arr != null) foreach (var d in arr) if (d != null) n++;
            if (n == 0 && variant != Grass) { arr = surfaceDecor[Grass]; n = 0; if (arr != null) foreach (var d in arr) if (d != null) n++; }
            if (n == 0) return null;
            int want = Mathf.Min(n - 1, Mathf.FloorToInt(roll * n));
            foreach (var d in arr) { if (d == null) continue; if (want-- == 0) return d; }
            return null;
        }

        /// <summary>A sprite as a quad at its pivot (chunk-local), mirrored in x when asked and turned by `angleDeg` about the pivot; into the
        /// top submesh of its texture.</summary>
        bool TopQuad(Sprite sprite, Vector2 at, bool mirror, float angleDeg = 0f)
        {
            int slot = -1;
            for (int i = 0; i < TopSubs; i++) if (topTex[i] == sprite.texture || topTex[i] == null) { slot = i; break; }
            if (slot < 0) { TopSlotRejects++; return false; }
            topTex[slot] = sprite.texture;
            var size = sprite.rect.size / sprite.pixelsPerUnit;
            var piv = new Vector2(sprite.pivot.x / sprite.rect.width, sprite.pivot.y / sprite.rect.height);
            // corners about the pivot (mirrored: the sprite flipped in its own x), turned, then placed
            float l = mirror ? -(1f - piv.x) * size.x : -piv.x * size.x, r = l + size.x, bt = -piv.y * size.y, tp = bt + size.y;
            float rad = angleDeg * Mathf.Deg2Rad, cs = Mathf.Cos(rad), sn = Mathf.Sin(rad);
            Vector3 P(float x, float y) => new Vector3(at.x + x * cs - y * sn, at.y + x * sn + y * cs, -0.01f);
            var o = UnityEngine.Sprites.DataUtility.GetOuterUV(sprite);
            float u0 = mirror ? o.z : o.x, u1 = mirror ? o.x : o.z;
            var white = Color.white;
            int b = v.Count;
            Add(P(l, bt), new Vector2(u0, o.y), white);
            Add(P(r, bt), new Vector2(u1, o.y), white);
            Add(P(r, tp), new Vector2(u1, o.w), white);
            Add(P(l, tp), new Vector2(u0, o.w), white);
            var into = tris[SubTop + slot];
            into.Add(b); into.Add(b + 2); into.Add(b + 1); into.Add(b); into.Add(b + 3); into.Add(b + 2);
            return true;
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
        public static Vector4 TierWeights(float depth, Meridian.Mining.D1Tables t, float x = 0f, float keep = 1f)
        {
            var w = Vector4.zero;
            for (int k = 0; k < 4; k++)
            {
                float from = t.tiers.Length > k + 1 ? t.tiers[k + 1].fromM : 1e6f;
                float u = Mathf.Clamp01((depth + keep * TierWobble(k, x) - (from - 0.5f * TierTransition)) / TierTransition);
                w[k] = u * u * (3f - 2f * u);
            }
            return w;
        }

        /// <summary>The tier the fill shows at a depth and x (0 = T1 ... 4 = T5): the deepest tier whose weight has reached a half. Pure.</summary>
        public static int TierShown(float depth, Meridian.Mining.D1Tables t, float x = 0f, float keep = 1f)
        {
            var w = TierWeights(depth, t, x, keep);
            for (int k = 3; k >= 0; k--) if (w[k] >= 0.5f) return k + 1;
            return 0;
        }

        // ---- U-196 (B-228's F7): a tier border under a slope ----
        /// <summary>The Surface Line's slope (m per m) at which a border keeps half its wobble.</summary>
        public const float WobbleSlope0 = 0.12f;
        /// <summary>How much of its wobble a border keeps where the Surface Line has this slope: all of it on level ground, 15 % under a
        /// 20-degree hill. The wobble's own slope reaches 1.0 (TierWobbleSlopeMax), steeper than a 30-degree hill's 0.58: at full strength a
        /// border under a slope alternated flat treads and steep risers and, blurred by its transition, read as stair-steps (0.6.1's
        /// smoke_54..57). Pure; the line texture's second channel holds it per column for the shader.</summary>
        public static float WobbleKeep(float slope)
        {
            float k = slope / WobbleSlope0;
            return 1f / (1f + k * k);
        }
        /// <summary>The steepest the wobble itself runs (m per m): the sum of its three sines' amplitude x frequency.</summary>
        public const float TierWobbleSlopeMax = TierWobbleMax * (0.5f * 1.71f + 0.32f * 0.93f + 0.18f * 3.1f);

        float[] wobbleKeep;
        /// <summary>The wobble kept at world x (between column centres, linear: as the shader's bilinear sample); 1 before the line is built.</summary>
        public float WobbleKeepAt(float x)
        {
            if (wobbleKeep == null || wobbleKeep.Length == 0) return 1f;
            float fx = x - 0.5f;
            int i = Mathf.FloorToInt(fx), n = wobbleKeep.Length;
            int a = ((i % n) + n) % n;
            return Mathf.Lerp(wobbleKeep[a], wobbleKeep[(a + 1) % n], fx - i);
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
            // U-196 (F7): the wobble each column's borders keep, from the line's slope across the column (its neighbours' centres)
            if (wobbleKeep == null || wobbleKeep.Length != w) wobbleKeep = new float[w];
            for (int x = 0; x < w; x++) wobbleKeep[x] = WobbleKeep(Mathf.Abs(heights[(x + 1) % w] - heights[(x - 1 + w) % w]) * 0.5f);
            // two channels: r the line, g the wobble kept (R16G16 UNorm: full-rate bilinear on the iGPU as R16 was; the float pair elsewhere)
            bool rg16 = SystemInfo.SupportsTextureFormat(TextureFormat.RG32);
            var fmt = rg16 ? TextureFormat.RG32 : TextureFormat.RGFloat;
            if (lineTex == null || lineTex.width != w || lineTex.format != fmt)
            {
                if (lineTex != null) Destroy(lineTex);
                lineTex = new Texture2D(w, 1, fmt, false, true) { wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear, name = "SurfaceLine_" + planet };
            }
            if (rg16)
            {
                var px = new ushort[w * 2];
                for (int x = 0; x < w; x++)
                {
                    px[x * 2] = (ushort)Mathf.RoundToInt(Mathf.Clamp01((heights[x] - lineBase) / lineSpan) * 65535f);
                    px[x * 2 + 1] = (ushort)Mathf.RoundToInt(Mathf.Clamp01(wobbleKeep[x]) * 65535f);
                }
                lineTex.SetPixelData(px, 0);
            }
            else
            {
                lineBase = 0f; lineSpan = 1f;
                var px = new float[w * 2];
                for (int x = 0; x < w; x++) { px[x * 2] = heights[x]; px[x * 2 + 1] = wobbleKeep[x]; }
                lineTex.SetPixelData(px, 0);
            }
            lineTex.Apply(false, false);
            foreach (var m in tierMaterials.Values) if (m != null) DressTiers(m);
            DressWalls();
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
            Current = this;
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
            // U-196 (B-230): the back walls; the first one in turns the wall's material over (the chunks rebuild over the next frames)
            for (int k = 0; k < walls.Length; k++)
            {
                int tier = k;
                Probe($"terrain/{planet}/back_wall_t{k + 1}", s => { walls[tier] = s; Repeat(s); DressWalls(); if (tier == 0) QueueAll(); });
            }
            BuildLine();
            ProbeDecor();
            ProbeTop(); // U-186
            RebuildAll();
        }

        static void Repeat(Sprite s) { if (s != null && s.texture != null) s.texture.wrapMode = TextureWrapMode.Repeat; }

        public void Deactivate()
        {
            Active = false;
            if (Current == this) Current = null;
            TerrainChunk.OutlineBuilt -= OnOutline;
            foreach (var kv in meshes) if (kv.Value != null) kv.Value.gameObject.SetActive(false);
            Release();
        }

        void OnDestroy() { if (Current == this) Current = null; TerrainChunk.OutlineBuilt -= OnOutline; Release(); if (lineTex != null) Destroy(lineTex); }

        void Release()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
            for (int i = 0; i < Variants; i++) bands[i] = null;
            fill = fillSand = rim = null;
            for (int k = 0; k < tierFills.Length; k++) tierFills[k] = null;
            for (int k = 0; k < walls.Length; k++) walls[k] = null;
            if (wallMaterial != null) Destroy(wallMaterial);
            wallMaterial = null;
            rebuildQueue.Clear();
            foreach (var m in tierMaterials.Values) if (m != null) Destroy(m);
            tierMaterials.Clear();
            // U-188 (0.6.0's probe: Mono +14 MB, 56 ChunkBlocks meshes and ~10 materials per planet visit, never returned): a planet's chunks die
            // with it, but held as keys here they stayed reachable with their meshes; the materials were made per texture each visit.
            topCounts.Clear();
            deadChunks.Clear();
            foreach (var kv in meshes) if (kv.Key == null) deadChunks.Add(kv.Key);
            foreach (var c in deadChunks) meshes.Remove(c);
            deadChunks.Clear();
            foreach (var m in materials.Values) if (m != null) Destroy(m);
            materials.Clear();
        }
        readonly List<TerrainChunk> deadChunks = new List<TerrainChunk>(64);

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
            // U-196 (B-230): the back wall is the tier's wall tile where it is in (already one step darker than the fill: only the hole's
            // shading multiplies it), else the fill shaded as before the art.
            var wallMat = worldFill ? WallMaterial() : null;
            bool wallOn = wallMat != null;
            Vector2 WallUv(float lx, float ly) => new Vector2((wx0 + lx) / WallTileM, (wy0 + ly) / WallTileM);
            System.Func<float, float, Vector2> backUv = wallOn ? WallUv : FillUv;
            var back = wallOn ? Color.white : new Color(fillTint.r * BackShade, fillTint.g * BackShade, fillTint.b * BackShade, 1f);

            // Does any of this chunk take the desert's sand fill? (Most chunks: no, and they skip the overlay.)
            bool sandFill = false;
            if (biomes && fillSand != null && fillSand.texture != null)
                for (int i = -2; i <= C + 2 && !sandFill; i++) sandFill = SandWeight(wx0 + i) > 0f;

            // 1. The back wall: under the natural surface curve, shaded (and the desert's sand over it, faded in). U-187: only where it can show,
            // behind the cells dug (or a cave's air) under the natural surface and one cell round them; the body covers the rest, so the
            // solid ground's pixels draw once, not twice (U-182's A/B room).
            if (k.Lines > 0 || k.fillVerts.Count > 0)
            {
                float yt = C - 0.5f;
                BackAir(wx0, wy0);
                BackMask(C, backAir, backMask);
                bool anyBack = false;
                for (int m = 0; m < backMask.Length && !anyBack; m++) anyBack = backMask[m];
                if (anyBack) HoleShadeGrid(wx0, wy0); // U-196: only a chunk with a hole pays for its shading
                var sandBack = new Color(BackShade, BackShade, BackShade, 1f);
                for (int i = 0; i < C && anyBack; i++)
                {
                    float h0 = c.SurfaceCurve[i] - wy0, h1 = c.SurfaceCurve[i + 1] - wy0;
                    if (float.IsNaN(h0) || float.IsNaN(h1)) continue;
                    h0 = Mathf.Min(h0, yt); h1 = Mathf.Min(h1, yt);
                    float x0 = i - 0.5f, x1 = i + 0.5f;
                    for (int j = 0; j < C; j++)
                    {
                        if (!backMask[i + j * C]) continue;
                        // U-196: a quad a cell (they ran merged up the column), so its corners carry the hole's shading
                        float yb = j - 0.5f, top = j + 0.5f;
                        float t0 = Mathf.Min(h0, top), t1 = Mathf.Min(h1, top);
                        if (t0 <= yb && t1 <= yb) continue;
                        BackQuadShaded(tris[SubBack], c, wy0, x0, x1, yb, t0, t1, back, 1f, 1f, backUv);
                        if (sandFill)
                        {
                            float s0 = SandWeight(wx0 + x0), s1 = SandWeight(wx0 + x1);
                            if (s0 > 0f || s1 > 0f) BackQuadShaded(tris[SubBackSand], c, wy0, x0, x1, yb, t0, t1, sandBack, s0, s1, WorldUv);
                        }
                    }
                }
            }

            LastBackQuads = tris[SubBack].Count / 6; // U-187
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
                    else { RimShadow(c, p, q, np, nq, wy0, backUv); Rim(p, q, np, nq, arc); } // U-196: the hole's soft inner shadow under the ink rim
                    arc += len;
                }
            }
            LastBandQuads = quads;
            TopSprites(c, k, wx0, wy0); // U-186: the brink lips and the surface decor, over the band and the rim

            mesh.Clear();
            mesh.SetVertices(v);
            mesh.SetUVs(0, uv);
            mesh.SetColors(col);
            mesh.subMeshCount = SubCount;
            for (int i = 0; i < SubCount; i++) mesh.SetTriangles(tris[i], i, false);
            mesh.bounds = new Bounds(new Vector3(C * 0.5f - 0.5f, C * 0.5f - 0.5f, 0f), new Vector3(C + 2f, C + 2f, 1f));
            // U-182: the fills draw by depth tier where the tier shader is in (worldFill: the uv is world / 8, which the shader reads back).
            mats[SubBody] = (worldFill && TierShader ? TierMaterialFor(fillSprite.texture) : null) ?? MaterialFor(fillSprite != null ? fillSprite.texture : null);
            mats[SubBack] = wallOn ? wallMat : mats[SubBody]; // U-196: the walls' material on the back wall's submesh, the same shader
            mats[SubBackSand] = (fillSand != null && TierShader ? TierMaterialFor(fillSand.texture) : null) ?? MaterialFor(fillSand != null ? fillSand.texture : null);
            mats[SubBodySand] = mats[SubBackSand];
            for (int i = 0; i < DecorSubs; i++) mats[SubDecor + i] = MaterialFor(decorTex[i]);
            for (int i = 0; i < Variants; i++) mats[SubBand + i] = MaterialFor(variantCount[i] > 0 ? variantSprites[i][0].texture : null);
            mats[SubRim] = MaterialFor(rim != null ? rim.texture : null);
            for (int i = 0; i < TopSubs; i++) mats[SubTop + i] = MaterialFor(topTex[i]);
            f.GetComponent<MeshRenderer>().sharedMaterials = mats;
            ChunksBuilt++;
        }

        // ---------- U-187: the back wall only where it shows ----------

        bool[] backAir, backMask;
        /// <summary>Back-wall quads laid on the last build (tests, the perf report).</summary>
        public int LastBackQuads { get; private set; }

        /// <summary>The chunk's cells (and a one-cell ring round it) that are air under the natural surface: dug, or a cave's. Index
        /// (i + 1) + (j + 1) * (C + 2) for i, j in -1..C.</summary>
        void BackAir(float wx0, float wy0)
        {
            const int C = TerrainConstants.ChunkSize, W = C + 2;
            if (backAir == null || backAir.Length != W * W) { backAir = new bool[W * W]; backMask = new bool[C * C]; }
            for (int i = -1; i <= C; i++)
            {
                int wx = Mathf.RoundToInt(wx0) + i;
                float surface = terrain.SurfaceAt(wx);
                for (int j = -1; j <= C; j++)
                {
                    int wy = Mathf.RoundToInt(wy0) + j;
                    backAir[(i + 1) + (j + 1) * W] = wy < surface && !TileId.IsSolid(terrain.GetTile(wx, wy));
                }
            }
        }

        /// <summary>U-187: the cells whose back wall can show: any cell within one of air under the natural surface (`air`, (C+2)² with its
        /// one-cell ring) → `mask` (C², i + j * C). A dug cell always has its back wall; an undug cell with no dug neighbour has none. Pure.</summary>
        public static void BackMask(int C, bool[] air, bool[] mask)
        {
            int W = C + 2;
            for (int j = 0; j < C; j++)
                for (int i = 0; i < C; i++)
                {
                    bool need = false;
                    for (int dj = 0; dj <= 2 && !need; dj++)
                        for (int di = 0; di <= 2 && !need; di++)
                            need = air[(i + di) + (j + dj) * W];
                    mask[i + j * C] = need;
                }
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

        /// <summary>One column's back wall from yb up to the curve h0 → h1. U-171 (LEAD's smoke_43 read): where the curve crosses yb inside the
        /// column the wall stops at the crossing (a triangle); clamping the low corner up to yb instead ran its top over the curve, a 1 m wedge
        /// of wall in the air beside a steep shore at a chunk's bottom edge.</summary>
        void BackQuad(List<int> into, float x0, float x1, float yb, float h0, float h1, Color c0, Color c1, System.Func<float, float, Vector2> uvOf)
        {
            if (h0 > yb && h1 < yb) { float u = (h0 - yb) / (h0 - h1); x1 = Mathf.Lerp(x0, x1, u); c1 = Color.Lerp(c0, c1, u); h1 = yb; }
            else if (h1 > yb && h0 < yb) { float u = (yb - h0) / (h1 - h0); x0 = Mathf.Lerp(x0, x1, u); c0 = Color.Lerp(c0, c1, u); h0 = yb; }
            h0 = Mathf.Max(h0, yb); h1 = Mathf.Max(h1, yb);
            int b = v.Count;
            Add(new Vector3(x0, yb, 0.01f), uvOf(x0, yb), c0); Add(new Vector3(x1, yb, 0.01f), uvOf(x1, yb), c1);
            Add(new Vector3(x1, h1, 0.01f), uvOf(x1, h1), c1); Add(new Vector3(x0, h0, 0.01f), uvOf(x0, h0), c0);
            into.Add(b); into.Add(b + 2); into.Add(b + 1); into.Add(b); into.Add(b + 3); into.Add(b + 2);
        }

        // ---------- U-196 (D-183, the owner's 0.6.0 playtest): holes read as holes ----------

        /// <summary>The back wall darkens with depth under the natural surface (to DepthShadeFloor of its shade at DepthShadeM and below) and
        /// with the extra way its air is from the open sky beyond straight up (to AirShadeFloor over AirFalloffM: a side tunnel off a shaft,
        /// a closed room); a soft ink shadow RimShadowM wide lies inside every dug edge. All of it in the back wall's own vertex colours and
        /// triangles: no texture sample, no draw call added.</summary>
        public const float DepthShadeM = 6f, DepthShadeFloor = 0.55f, AirFalloffM = 3f, AirShadeFloor = 0.8f, RimShadowM = 0.3f, RimShadowInk = 0.5f;
        /// <summary>The shading grid's ring round the chunk (cells) and how far over the grid a column is searched for the open sky.</summary>
        public const int AirRing = 4, LitScan = 12;

        /// <summary>The depth term: 1 at the natural surface, DepthShadeFloor from DepthShadeM down. Pure.</summary>
        public static float DepthShade(float depth) => Mathf.Lerp(1f, DepthShadeFloor, Mathf.Clamp01(depth / DepthShadeM));
        /// <summary>The open-air term for the path to the sky beyond the straight-up distance (m): 1 under an open shaft, AirShadeFloor from
        /// AirFalloffM on (and in a closed pocket: +infinity). Pure.</summary>
        public static float AirShade(float extra) => Mathf.Lerp(1f, AirShadeFloor, Mathf.Clamp01(extra / AirFalloffM));

        /// <summary>For a W x W grid of cells (index i + j * W, j up): `air` (not solid), `lit` (air that sees the sky straight up, or is above
        /// the natural surface), `depth` (m under the natural surface at the cell) → `extra`: how much longer the cell's way through air to
        /// the sky is than straight up (0 where lit; +infinity in solid and in air no lit cell reaches). Four alternating sweeps: exact for
        /// the first few metres off a lit cell, which is all AirFalloffM needs. Pure.</summary>
        public static void AirExtra(int W, bool[] air, bool[] lit, float[] depth, float[] extra)
        {
            int n = W * W;
            for (int k = 0; k < n; k++) extra[k] = air[k] && lit[k] ? Mathf.Max(0f, depth[k]) : float.PositiveInfinity; // the path, first
            for (int sweep = 0; sweep < 4; sweep++)
            {
                bool forward = (sweep & 1) == 0;
                for (int a = 0; a < n; a++)
                {
                    int k = forward ? a : n - 1 - a;
                    if (!air[k] || lit[k]) continue;
                    int i = k % W, j = k / W;
                    float best = extra[k];
                    if (i > 0 && extra[k - 1] + 1f < best) best = extra[k - 1] + 1f;
                    if (i < W - 1 && extra[k + 1] + 1f < best) best = extra[k + 1] + 1f;
                    if (j > 0 && extra[k - W] + 1f < best) best = extra[k - W] + 1f;
                    if (j < W - 1 && extra[k + W] + 1f < best) best = extra[k + W] + 1f;
                    extra[k] = best;
                }
            }
            for (int k = 0; k < n; k++) if (!float.IsPositiveInfinity(extra[k])) extra[k] = Mathf.Max(0f, extra[k] - Mathf.Max(0f, depth[k]));
        }

        bool[] holeAir, holeLit;
        float[] holeDepth, holeExtra, nodeExtra;

        /// <summary>The chunk's shading: the air grid with its ring (cells as BackAir's: tile wx, wy at local i, j), which of it sees the sky,
        /// its extra path, then the extra at the chunk's cell corners (the least of the air cells round each, capped at AirFalloffM).</summary>
        void HoleShadeGrid(float wx0, float wy0)
        {
            const int C = TerrainConstants.ChunkSize, R = AirRing, W = C + 2 * R, N = C + 1;
            if (holeAir == null || holeAir.Length != W * W)
            {
                holeAir = new bool[W * W]; holeLit = new bool[W * W]; holeDepth = new float[W * W]; holeExtra = new float[W * W]; nodeExtra = new float[N * N];
            }
            int bx = Mathf.RoundToInt(wx0), by = Mathf.RoundToInt(wy0);
            for (int i = -R; i < C + R; i++)
            {
                int wx = bx + i;
                float surface = terrain.SurfaceAt(wx);
                // the sky over the grid's top row: air all the way up to the natural surface (LitScan cells at most)
                bool above = true;
                int over = by + C + R;
                for (int wy = over; wy < surface && above; wy++) above = wy - over < LitScan && !TileId.IsSolid(terrain.GetTile(wx, wy));
                for (int j = C + R - 1; j >= -R; j--)
                {
                    int wy = by + j, k = (i + R) + (j + R) * W;
                    bool air = !TileId.IsSolid(terrain.GetTile(wx, wy));
                    holeAir[k] = air;
                    holeDepth[k] = surface - wy;
                    above = air && (wy >= surface || above); // a solid cell shuts the sky off for the column under it
                    holeLit[k] = above;
                }
            }
            AirExtra(W, holeAir, holeLit, holeDepth, holeExtra);
            for (int nj = 0; nj < N; nj++)
                for (int ni = 0; ni < N; ni++)
                {
                    float least = AirFalloffM;
                    for (int dj = -1; dj <= 0; dj++)
                        for (int di = -1; di <= 0; di++)
                        {
                            int k = (ni + di + R) + (nj + dj + R) * W;
                            if (holeAir[k] && holeExtra[k] < least) least = holeExtra[k];
                        }
                    nodeExtra[ni + nj * N] = least;
                }
        }

        /// <summary>The hole's shading at a chunk-local point: the depth term under the chunk's own surface curve times the open-air term
        /// between the cell corners round it.</summary>
        float HoleShade(TerrainChunk c, float lx, float ly, float wy0)
        {
            const int C = TerrainConstants.ChunkSize, N = C + 1;
            float fi = lx + 0.5f, fj = ly + 0.5f;
            int i = Mathf.Clamp(Mathf.FloorToInt(fi), 0, C - 1), j = Mathf.Clamp(Mathf.FloorToInt(fj), 0, C - 1);
            float u = Mathf.Clamp01(fi - i), w = Mathf.Clamp01(fj - j);
            float a = c.SurfaceCurve[i], b = c.SurfaceCurve[i + 1];
            float depth = float.IsNaN(a) || float.IsNaN(b) ? 0f : Mathf.Max(0f, Mathf.Lerp(a, b, u) - (wy0 + ly));
            float low = Mathf.Lerp(nodeExtra[i + j * N], nodeExtra[i + 1 + j * N], u), high = Mathf.Lerp(nodeExtra[i + (j + 1) * N], nodeExtra[i + 1 + (j + 1) * N], u);
            return DepthShade(depth) * AirShade(Mathf.Lerp(low, high, w));
        }

        /// <summary>BackQuad for one cell with the hole's shading at each corner: `tint` times HoleShade there, alpha a0 → a1 across the cell.</summary>
        void BackQuadShaded(List<int> into, TerrainChunk c, float wy0, float x0, float x1, float yb, float h0, float h1, Color tint, float a0, float a1, System.Func<float, float, Vector2> uvOf)
        {
            float xa = x0, span = Mathf.Max(1e-5f, x1 - x0);
            if (h0 > yb && h1 < yb) { float u = (h0 - yb) / (h0 - h1); x1 = Mathf.Lerp(x0, x1, u); h1 = yb; }
            else if (h1 > yb && h0 < yb) { float u = (yb - h0) / (h1 - h0); x0 = Mathf.Lerp(x0, x1, u); h0 = yb; }
            h0 = Mathf.Max(h0, yb); h1 = Mathf.Max(h1, yb);
            int b = v.Count;
            ShadedVertex(c, wy0, x0, yb, tint, Mathf.Lerp(a0, a1, (x0 - xa) / span), uvOf);
            ShadedVertex(c, wy0, x1, yb, tint, Mathf.Lerp(a0, a1, (x1 - xa) / span), uvOf);
            ShadedVertex(c, wy0, x1, h1, tint, Mathf.Lerp(a0, a1, (x1 - xa) / span), uvOf);
            ShadedVertex(c, wy0, x0, h0, tint, Mathf.Lerp(a0, a1, (x0 - xa) / span), uvOf);
            into.Add(b); into.Add(b + 2); into.Add(b + 1); into.Add(b); into.Add(b + 3); into.Add(b + 2);
        }

        void ShadedVertex(TerrainChunk c, float wy0, float x, float y, Color tint, float alpha, System.Func<float, float, Vector2> uvOf)
        {
            float s = HoleShade(c, x, y, wy0);
            Add(new Vector3(x, y, 0.01f), uvOf(x, y), new Color(tint.r * s, tint.g * s, tint.b * s, tint.a * alpha));
        }

        /// <summary>The soft shadow inside a dug edge: from the outline (ink at RimShadowInk) RimShadowM into the hole (clear), in the back
        /// wall's triangles after its quads (over them, under the body and the ink rim). Only where the strip lies under the natural surface:
        /// a mound's side and a cliff's face stand in the open air and get none.</summary>
        void RimShadow(TerrainChunk c, Vector2 p, Vector2 q, Vector2 np, Vector2 nq, float wy0, System.Func<float, float, Vector2> uvOf)
        {
            Vector2 inside = (p + q) * 0.5f + (np + nq) * (0.25f * RimShadowM);
            const int C = TerrainConstants.ChunkSize;
            float fi = inside.x + 0.5f;
            int i = Mathf.Clamp(Mathf.FloorToInt(fi), 0, C - 1);
            float a = c.SurfaceCurve[i], b = c.SurfaceCurve[i + 1];
            if (float.IsNaN(a) || float.IsNaN(b) || wy0 + inside.y > Mathf.Lerp(a, b, Mathf.Clamp01(fi - i)) - 0.05f) return;
            Vector2 pf = p + np * RimShadowM, qf = q + nq * RimShadowM;
            var ink = new Color(0f, 0f, 0f, RimShadowInk);
            var clear = new Color(0f, 0f, 0f, 0f);
            int i0 = v.Count;
            Add(new Vector3(p.x, p.y, 0.005f), uvOf(p.x, p.y), ink); Add(new Vector3(q.x, q.y, 0.005f), uvOf(q.x, q.y), ink);
            Add(new Vector3(qf.x, qf.y, 0.005f), uvOf(qf.x, qf.y), clear); Add(new Vector3(pf.x, pf.y, 0.005f), uvOf(pf.x, pf.y), clear);
            var into = tris[SubBack];
            into.Add(i0); into.Add(i0 + 1); into.Add(i0 + 2); into.Add(i0); into.Add(i0 + 2); into.Add(i0 + 3);
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
