using System.Collections.Generic;
using Meridian.Planets;
using UnityEngine;

namespace Meridian.Terrain
{
    /// <summary>
    /// U-073: the per-planet Texture2DArray the block mesh samples (BlockMesher layers: top/side per tile material,
    /// back wall last). Until BLENDER's B-080 block textures exist every layer is a flat placeholder colour with a
    /// little noise (so faces and edges read in captures). Built once per planet and kept; tiny (8×8 per layer).
    /// </summary>
    public static class TerrainBlockPalette
    {
        const int Size = 8;
        static readonly Dictionary<PlanetId, Texture2DArray> cache = new Dictionary<PlanetId, Texture2DArray>();

        /// <summary>Top and side colours of a tile material (placeholder; palettes per Bible §9).</summary>
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
                float k = 0.92f + (h & 0xFF) / 255f * 0.16f; // ±8% grain
                px[i] = new Color(c.r * k, c.g * k, c.b * k, 1f);
            }
        }
    }
}
