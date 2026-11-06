using System.Collections.Generic;
using Meridian.Planets;
using UnityEngine;

namespace Meridian.Terrain
{
    /// <summary>
    /// U-073: the per-planet Texture2DArray the block mesh samples (BlockMesher layers: top/side per tile material,
    /// back wall last). Until BLENDER's B-080 block textures exist every layer is a flat placeholder colour with a
    /// little noise (so faces and edges read in captures). Built once per planet and kept; tiny (8Ã—8 per layer).
    /// </summary>
    public static class TerrainBlockPalette
    {
        /// <summary>Logs the array build per planet (a U-073 diagnostic; off so test runs with LogAssert stay clean).</summary>
        public static bool Verbose;
        const int Size = 8;
        static readonly Dictionary<PlanetId, Texture2DArray> cache = new Dictionary<PlanetId, Texture2DArray>();

        /// <summary>Top and side colours of a tile material (placeholder; palettes per Bible Â§9).</summary>
        public static (Color top, Color side) ColorsOf(byte id) => id switch
        {
            TileId.Soil => (new Color(0.42f, 0.30f, 0.20f), new Color(0.40f, 0.28f, 0.18f)),
            TileId.Grass => (new Color(0.30f, 0.52f, 0.20f), new Color(0.40f, 0.29f, 0.18f)),
            TileId.Stone => (new Color(0.50f, 0.50f, 0.50f), new Color(0.46f, 0.46f, 0.47f)),
            TileId.Sand => (new Color(0.84f, 0.76f, 0.52f), new Color(0.78f, 0.69f, 0.47f)),
            TileId.Snow => (new Color(0.93f, 0.95f, 0.98f), new Color(0.85f, 0.88f, 0.93f)),
            TileId.Water => (new Color(0.15f, 0.35f, 0.60f), new Color(0.15f, 0.35f, 0.60f)),
            TileId.Regolith => (new Color(0.72f, 0.38f, 0.22f), new Color(0.64f, 0.33f, 0.20f)),
            TileId.Basalt => (new Color(0.24f, 0.22f, 0.22f), new Color(0.21f, 0.19f, 0.19f)),
            TileId.Hematite => (new Color(0.48f, 0.20f, 0.17f), new Color(0.42f, 0.17f, 0.15f)),
            TileId.Ice => (new Color(0.82f, 0.90f, 0.95f), new Color(0.70f, 0.82f, 0.90f)),
            TileId.MercuryRegolith => (new Color(0.58f, 0.57f, 0.58f), new Color(0.50f, 0.49f, 0.51f)),
            TileId.MercuryBasalt => (new Color(0.22f, 0.21f, 0.24f), new Color(0.19f, 0.18f, 0.21f)),
            TileId.Sulfide => (new Color(0.62f, 0.55f, 0.30f), new Color(0.55f, 0.48f, 0.26f)),
            TileId.MercuryIce => (new Color(0.78f, 0.82f, 0.90f), new Color(0.68f, 0.72f, 0.82f)),
            TileId.VenusBasalt => (new Color(0.20f, 0.16f, 0.13f), new Color(0.17f, 0.13f, 0.11f)),
            TileId.Sulfur => (new Color(0.88f, 0.78f, 0.25f), new Color(0.80f, 0.70f, 0.22f)),
            TileId.Tessera => (new Color(0.52f, 0.40f, 0.30f), new Color(0.46f, 0.35f, 0.27f)),
            TileId.VentGlass => (new Color(0.30f, 0.45f, 0.40f), new Color(0.26f, 0.40f, 0.36f)),
            TileId.FloeIce => (new Color(0.90f, 0.86f, 0.76f), new Color(0.84f, 0.79f, 0.68f)),
            TileId.FloeCore => (new Color(0.70f, 0.62f, 0.50f), new Color(0.64f, 0.56f, 0.45f)),
            _ => (new Color(1f, 0f, 1f), new Color(1f, 0f, 1f)), // missing: magenta, so it shows
        };

        /// <summary>The back wall's rock per planet (the deep material, darkened in the shader).</summary>
        public static Color WallOf(PlanetId p) => p switch
        {
            PlanetId.Earth => ColorsOf(TileId.Stone).side,
            PlanetId.Mars => ColorsOf(TileId.Basalt).side,
            PlanetId.Mercury => ColorsOf(TileId.MercuryBasalt).side,
            PlanetId.Venus => ColorsOf(TileId.VenusBasalt).side,
            _ => new Color(0.3f, 0.3f, 0.32f),
        };

        /// <summary>The arrays the TerrainBlocks shader samples. normal/mask are null on placeholder planets.</summary>
        public struct Arrays
        {
            public Texture2DArray color, normal, mask;
            public bool Real => normal != null;
        }

        static PlanetId? realPlanet;
        static Arrays realArrays;

        /// <summary>
        /// B-080: the planet's block material textures (ArtMaterials.blockTextures) copied on the GPU into three arrays
        /// (colour BC7 sRGB, normal BC5, mask BC7 linear; 512Â² with mips). Layers the planet doesn't use repeat the
        /// back wall. Falls back to the flat placeholder palette when the planet has none or the maps don't match.
        /// Only the current planet's real arrays are kept.
        /// </summary>
        public static Arrays ArraysFor(PlanetId planet)
        {
            if (realPlanet == planet && realArrays.color != null) return realArrays;
            Release();
            var real = BuildReal(planet);
            if (real.color != null) { realPlanet = planet; realArrays = real; return real; }
            return new Arrays { color = For(planet) };
        }

        static void Release()
        {
            if (realArrays.color != null) Object.Destroy(realArrays.color);
            if (realArrays.normal != null) Object.Destroy(realArrays.normal);
            if (realArrays.mask != null) Object.Destroy(realArrays.mask);
            realArrays = default;
            realPlanet = null;
        }

        static Arrays BuildReal(PlanetId planet)
        {
            var reg = Meridian.Rendering.ArtMaterials.Active;
            if (reg == null || reg.blockTextures == null || reg.blockTextures.Count == 0) return default;
            string p = planet.ToString().ToLowerInvariant();
            var wall = reg.FindBlock(p, "backwall", "wall");
            if (wall == null || wall.color == null || wall.normal == null || wall.mask == null) return default;
            if (SystemInfo.copyTextureSupport == UnityEngine.Rendering.CopyTextureSupport.None) return default;

            var layers = new Meridian.Rendering.ArtMaterials.BlockTexture[BlockMesher.LayerCount];
            int found = 0;
            for (int id = 1; id < TileId.Count; id++)
            {
                var key = TileId.ArtKey((byte)id);
                if (key == null) continue;
                var parts = key.Split('/');
                if (parts.Length != 3 || parts[1] != p) continue;
                var top = reg.FindBlock(p, parts[2], "top");
                var side = reg.FindBlock(p, parts[2], "side");
                if (top != null) { layers[BlockMesher.TopLayer((byte)id)] = top; found++; }
                if (side != null) { layers[BlockMesher.SideLayer((byte)id)] = side; found++; }
            }
            if (found == 0) return default;
            layers[BlockMesher.BackWallLayer] = wall;
            for (int i = 0; i < layers.Length; i++)
            {
                var l = layers[i];
                if (l == null || l.color == null || l.normal == null || l.mask == null || !Same(l, wall)) layers[i] = wall; // unused or incomplete: the wall
            }

            var a = new Arrays
            {
                color = NewArray(wall.color, layers.Length, "BlockColor_" + planet),
                normal = NewArray(wall.normal, layers.Length, "BlockNormal_" + planet),
                mask = NewArray(wall.mask, layers.Length, "BlockMask_" + planet),
            };
            for (int i = 0; i < layers.Length; i++)
            {
                Graphics.CopyTexture(layers[i].color, 0, a.color, i);
                Graphics.CopyTexture(layers[i].normal, 0, a.normal, i);
                Graphics.CopyTexture(layers[i].mask, 0, a.mask, i);
            }
            if (Verbose) Debug.Log($"[MERIDIAN] block textures for {planet}: {found} faces from the registry, {layers.Length} layers ({wall.color.width}Â² {wall.color.graphicsFormat})");
            return a;
        }

        static bool Same(Meridian.Rendering.ArtMaterials.BlockTexture l, Meridian.Rendering.ArtMaterials.BlockTexture w) =>
            l.color.width == w.color.width && l.color.height == w.color.height && l.color.graphicsFormat == w.color.graphicsFormat && l.color.mipmapCount == w.color.mipmapCount
            && l.normal.graphicsFormat == w.normal.graphicsFormat && l.normal.width == w.normal.width && l.normal.mipmapCount == w.normal.mipmapCount
            && l.mask.graphicsFormat == w.mask.graphicsFormat && l.mask.width == w.mask.width && l.mask.mipmapCount == w.mask.mipmapCount;

        static Texture2DArray NewArray(Texture2D like, int depth, string name)
        {
            var flags = UnityEngine.Experimental.Rendering.TextureCreationFlags.DontInitializePixels;
            if (like.mipmapCount > 1) flags |= UnityEngine.Experimental.Rendering.TextureCreationFlags.MipChain;
            var arr = new Texture2DArray(like.width, like.height, depth, like.graphicsFormat, flags, like.mipmapCount)
            {
                name = name,
                wrapMode = TextureWrapMode.Repeat,
                filterMode = FilterMode.Trilinear,
                anisoLevel = 4,
            };
            return arr;
        }

        public static Texture2DArray For(PlanetId planet)
        {
            if (cache.TryGetValue(planet, out var arr) && arr != null) return arr;
            arr = new Texture2DArray(Size, Size, BlockMesher.LayerCount, TextureFormat.RGBA32, false)
            {
                name = $"BlockPalette_{planet}",
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Repeat,
            };
            var px = new Color32[Size * Size];
            for (int id = 0; id < TileId.Count; id++)
            {
                var (top, side) = ColorsOf((byte)id);
                Fill(px, top, id * 31 + 1); arr.SetPixels32(px, BlockMesher.TopLayer((byte)id));
                Fill(px, side, id * 31 + 2); arr.SetPixels32(px, BlockMesher.SideLayer((byte)id));
            }
            Fill(px, WallOf(planet), 977); arr.SetPixels32(px, BlockMesher.BackWallLayer);
            arr.Apply(false, true); // no CPU copy kept
            cache[planet] = arr;
            return arr;
        }

        static void Fill(Color32[] px, Color c, int seed)
        {
            uint h = (uint)seed * 2654435761u;
            for (int i = 0; i < px.Length; i++)
            {
                h ^= h << 13; h ^= h >> 17; h ^= h << 5;
                float k = 0.92f + (h & 0xFF) / 255f * 0.16f; // Â±8% grain
                px[i] = new Color(c.r * k, c.g * k, c.b * k, 1f);
            }
        }
    }
}
