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
                    tiles[captured] = BuildTiles(op.Result, captured);
                };
            }
        }

        static Tile[] BuildTiles(IList<Sprite> sprites, byte id)
        {
            var result = new Tile[BlobAutotile.VariantCount];
            foreach (var s in sprites)
            {
                int us = s.name.LastIndexOf('_');
                if (us < 0 || !int.TryParse(s.name.Substring(us + 1), out int index)) continue;
                if (index < 0 || index >= result.Length) continue;
                var t = ScriptableObject.CreateInstance<Tile>();
                t.sprite = s;
                FitToCell(t, s);
                t.colliderType = TileId.IsSolid(id) ? Tile.ColliderType.Grid : Tile.ColliderType.None;
                result[index] = t;
            }
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

        public void Dispose()
        {
            foreach (var set in tiles)
                if (set != null)
                    foreach (var t in set)
                        if (t != null) UnityEngine.Object.Destroy(t);
            foreach (var h in handles) if (h.IsValid()) Addressables.Release(h);
            handles.Clear();
        }
    }
}
