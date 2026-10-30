using UnityEngine;
using UnityEngine.Tilemaps;

namespace Meridian.Terrain
{
    /// <summary>
    /// A pooled 32×32 chunk: a solid Tilemap with merged collision and a liquid Tilemap without.
    /// Only this chunk's collider rebuilds when it changes (Bible §10.4).
    /// </summary>
    public sealed class TerrainChunk : MonoBehaviour
    {

        public Tilemap solid;
        public Tilemap liquid;
        public int cx, cy;
        CompositeCollider2D composite;

        // Allocating the full 32×32 up front keeps SetTilesBlock from growing bounds mid-stream.
        static void FixBounds(Tilemap map)
        {
            map.origin = Vector3Int.zero;
            map.size = new Vector3Int(TerrainConstants.ChunkSize, TerrainConstants.ChunkSize, 1);
            map.ResizeBounds();
        }

        /// <summary>Rebuilds merged collision after the last band; the only collider work per chunk.</summary>
        public void FinishCollision() => composite.GenerateGeometry();

        public static TerrainChunk Create(Transform parent)
        {
            var go = new GameObject("Chunk");
            go.transform.SetParent(parent, false);
            var chunk = go.AddComponent<TerrainChunk>();

            chunk.solid = go.AddComponent<Tilemap>();
            var sr = go.AddComponent<TilemapRenderer>();
            sr.mode = TilemapRenderer.Mode.Chunk;
            var body = go.AddComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Static;
            var tc = go.AddComponent<TilemapCollider2D>();
            tc.compositeOperation = Collider2D.CompositeOperation.Merge;
            var composite = go.AddComponent<CompositeCollider2D>();
            composite.geometryType = CompositeCollider2D.GeometryType.Polygons;
            composite.generationType = CompositeCollider2D.GenerationType.Manual; // built once per chunk (FinishCollision)
            chunk.composite = composite;
            FixBounds(chunk.solid);

            var liquidGo = new GameObject("Liquid");
            liquidGo.transform.SetParent(go.transform, false);
            chunk.liquid = liquidGo.AddComponent<Tilemap>();
            var lr = liquidGo.AddComponent<TilemapRenderer>();
            lr.mode = TilemapRenderer.Mode.Chunk;
            lr.sortingOrder = 1;
            FixBounds(chunk.liquid);
            return chunk;
        }

        /// <summary>Rows written per apply step, so one chunk spreads over frames within the 2 ms budget.</summary>
        public const int RowsPerStep = 4;

        public void Begin(ChunkBuffer data)
        {
            cx = data.cx; cy = data.cy;
            transform.localPosition = new Vector3(cx * TerrainConstants.ChunkSize, cy * TerrainConstants.ChunkSize, 0f);
        }

        /// <summary>Writes rows [row, row + RowsPerStep) into the tilemaps. Scratch arrays (RowsPerStep × 32) are the caller's.</summary>
        public void ApplyRows(ChunkBuffer data, TerrainTileSet set, int row, TileBase[] solidScratch, TileBase[] liquidScratch)
        {
            const int C = TerrainConstants.ChunkSize;
            int start = row * C;
            for (int i = 0; i < RowsPerStep * C; i++)
            {
                byte id = data.ids[start + i];
                var tile = id == TileId.Air ? null : set.Get(id, data.blob[start + i]);
                bool isLiquid = TileId.IsLiquid(id);
                solidScratch[i] = isLiquid ? null : tile;
                liquidScratch[i] = isLiquid ? tile : null;
            }
            var band = new BoundsInt(0, row, 0, C, RowsPerStep, 1);
            solid.SetTilesBlock(band, solidScratch);
            liquid.SetTilesBlock(band, liquidScratch);
        }

        /// <summary>Sets one tile in chunk-local coordinates (edits). Caller rebuilds collision.</summary>
        public void SetTileLocal(int lx, int ly, byte id, TileBase tile)
        {
            var p = new Vector3Int(lx, ly, 0);
            bool isLiquid = TileId.IsLiquid(id);
            solid.SetTile(p, isLiquid ? null : tile);
            liquid.SetTile(p, isLiquid ? tile : null);
        }

        public void Clear()
        {
            solid.ClearAllTiles();
            liquid.ClearAllTiles();
            FixBounds(solid);
            FixBounds(liquid);
            composite.GenerateGeometry();
            // Stays active: re-enabling colliders and renderers costs more than the 2 ms apply budget allows.
        }
    }
}
