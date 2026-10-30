using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.Tilemaps;

namespace Meridian.Terrain
{
    /// <summary>
    /// Loads each material's 47-tile sheet by asset key (Addressables) and builds one Tile per
    /// sheet cell. Sprites carry their normal map as a secondary texture, so tiles are lit.
    /// </summary>
    public sealed class TerrainTileSet : IDisposable
    {
        readonly Tile[][] tiles = new Tile[TileId.Count][];
        readonly Tile[][] interior = new Tile[TileId.Count][];
        readonly List<AsyncOperationHandle<IList<Sprite>>> handles = new List<AsyncOperationHandle<IList<Sprite>>>();
        int pending;

        public bool IsReady => pending == 0;

        public void Load(IEnumerable<byte> ids)
        {
            foreach (var id in ids)
            {
                var key = TileId.ArtKey(id);
                if (key == null || tiles[id] != null) continue;
                pending++;
                byte captured = id;
                var h = Addressables.LoadAssetAsync<IList<Sprite>>(key);
                handles.Add(h);
                h.Completed += op =>
                {
                    pending--;
                    if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null)
                    {
                        Debug.LogError($"[Terrain] Could not load tile sheet '{key}'.");
                        return;
                    }
                    LoadFromSprites(captured, op.Result);
                };
            }
        }

        /// <summary>Builds a material's tiles from its sliced sprites (named         /// <summary>Sheet cells 47–62 hold variants of the fully surrounded tile 46 (D-020).</summary>lt;material        /// <summary>Sheet cells 47–62 hold variants of the fully surrounded tile 46 (D-020).</summary>gt;_        /// <summary>Sheet cells 47–62 hold variants of the fully surrounded tile 46 (D-020).</summary>lt;cell        /// <summary>Sheet cells 47–62 hold variants of the fully surrounded tile 46 (D-020).</summary>gt;). Tests call it directly.</summary>
        public void LoadFromSprites(byte id, IList<Sprite> sprites) => tiles[id] = BuildTiles(sprites, id);

        /// <summary>Sheet cells 47–62 hold variants of the fully surrounded tile 46 (D-020).</summary>
        public const int FirstInteriorVariant = BlobAutotile.VariantCount, MaxInteriorVariants = 16;

        Tile[] BuildTiles(IList<Sprite> sprites, byte id)
        {
            var result = new Tile[BlobAutotile.VariantCount];
            var variants = new List<Tile>();
            var sorted = new List<(int index, Sprite sprite)>();
            foreach (var s in sprites)
            {
                int us = s.name.LastIndexOf('_');
                if (us < 0 || !int.TryParse(s.name.Substring(us + 1), out int index)) continue;
                if (index >= 0 && index < FirstInteriorVariant + MaxInteriorVariants) sorted.Add((index, s));
            }
            sorted.Sort((a, b) => a.index.CompareTo(b.index));
            foreach (var (index, s) in sorted)
            {
                var t = ScriptableObject.CreateInstance<Tile>();
                t.sprite = s;
                FitToCell(t, s);
                t.colliderType = TileId.IsSolid(id) ? Tile.ColliderType.Grid : Tile.ColliderType.None;
                if (index < FirstInteriorVariant) result[index] = t;
                else variants.Add(t);
            }
            interior[id] = variants.ToArray();
            // A sheet with a single sprite (unsliced) still renders: reuse it for every variant.
            if (result[0] == null && sprites.Count > 0)
            {
                var t = ScriptableObject.CreateInstance<Tile>();
                t.sprite = sprites[0];
                t.colliderType = TileId.IsSolid(id) ? Tile.ColliderType.Grid : Tile.ColliderType.None;
                for (int i = 0; i < result.Length; i++) result[i] ??= t;
            }
            for (int i = 0; i < result.Length; i++) result[i] ??= result[0];
            return result;
        }

        /// <summary>
        /// The importer cuts terrain cells 1 texel inside the 128 px grid so bilinear and mip
        /// sampling never read the neighboring cell (those reads drew thin lines between rows).
        /// The tile scales the 126 px sprite back to exactly one 1 m cell.
        /// </summary>
        static void FitToCell(Tile t, Sprite s)
        {
            float size = s.rect.width / s.pixelsPerUnit;
            if (size <= 0f || Mathf.Approximately(size, 1f)) return;
            t.transform = Matrix4x4.Scale(new Vector3(1f / size, 1f / size, 1f));
            t.flags = TileFlags.LockTransform;
        }

        public TileBase Get(byte id, byte variant)
        {
            var set = id < tiles.Length ? tiles[id] : null;
            return set == null ? null : set[variant];
        }

        /// <summary>Number of interior variants loaded for a material (0 = the sheet has none).</summary>
        public int InteriorVariants(byte id) => id < interior.Length && interior[id] != null ? interior[id].Length : 0;

        /// <summary>
        /// The tile to draw at world (wrappedX, y). Interior tiles (blob 46) pick tile 46 or one of its
        /// variants by a stable hash of the position, so the same world always looks the same (D-020).
        /// </summary>
        public TileBase Get(byte id, byte blob, int wrappedX, int y)
        {
            int n = blob == BlobAutotile.VariantCount - 1 ? InteriorVariants(id) : 0;
            if (n == 0) return Get(id, blob);
            int pick = VariantPick(wrappedX, y, n + 1);
            return pick == 0 ? Get(id, blob) : interior[id][pick - 1];
        }

        /// <summary>Stable choice in [0, options) from a tile position (integer hash; no allocation, no seed).</summary>
        public static int VariantPick(int wrappedX, int y, int options)
        {
            unchecked
            {
                uint h = (uint)wrappedX * 0x8DA6B343u ^ (uint)y * 0xD8163841u;
                h ^= h >> 15; h *= 0x2C1B3C6Du; h ^= h >> 12; h *= 0x297A2D39u; h ^= h >> 15;
                return (int)(h % (uint)options);
            }
        }

        public void Dispose()
        {
            foreach (var set in interior)
                if (set != null)
                    foreach (var t in set)
                        if (t != null) UnityEngine.Object.Destroy(t);
            foreach (var set in tiles)
                if (set != null)
                    foreach (var t in set)
                        if (t != null) UnityEngine.Object.Destroy(t);
            foreach (var h in handles) if (h.IsValid()) Addressables.Release(h);
            handles.Clear();
        }
    }
}
