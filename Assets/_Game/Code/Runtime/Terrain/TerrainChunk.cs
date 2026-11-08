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
        public const float WaterAlpha = 0.45f;

        public Tilemap solid;
        public Tilemap liquid;
        public int cx, cy;
        CompositeCollider2D composite;
        TilemapCollider2D tileCollider;

        // ---------- U-073 block mesh (Bible 2.0 §10.4): the Tilemap stays as collision and data, renderer off ----------

        /// <summary>What the mesher needs from the world beyond this chunk (implemented by TerrainStreamer).</summary>
        public interface IBlockWorld
        {
            /// <summary>Tile at world (x, y), edits included; x unwrapped; Air outside the world's height.</summary>
            byte TileAt(int x, int y);
            /// <summary>Highest world y that gets back wall in column x (the original surface); int.MinValue = none.</summary>
            int WallTop(int x);
        }

        /// <summary>When true the block mesh renders and the tilemap renderer is off (the 3D view).</summary>
        public static bool BlocksEnabled = true;

        readonly byte[] ids = new byte[TerrainConstants.ChunkSize * TerrainConstants.ChunkSize];
        IBlockWorld world;
        MeshRenderer blockRenderer;
        Mesh blockMesh;
        System.Func<int, int, byte> outsideFn;
        System.Func<int, int> wallFn;
        static BlockMesher.Buffers buffers; // main thread only
        /// <summary>Quads in the current block mesh (tests, budget rows).</summary>
        public int BlockQuads { get; private set; }
        /// <summary>The last block rebuild's main-thread cost (ms).</summary>
        public static double LastBuildMs { get; private set; }

        public byte LocalTile(int lx, int ly) => ids[ly * TerrainConstants.ChunkSize + lx];

        /// <summary>Hooks the chunk to its world and the planet's block material (streamer, on Begin). U-156: on a smooth planet (D-161 / D-162)
        /// the ground is the traced outline instead: edge colliders and the ground mesh (SmoothGround); the tile collider, the composite, the
        /// block mesh and the tilemap renderer all stay off; the tiles stay as data.</summary>
        public void UseBlocks(IBlockWorld w, Material material, bool smoothGround = false)
        {
            world = w;
            smooth = smoothGround;
            if (blockRenderer != null) blockRenderer.sharedMaterial = material;
            var sr = GetComponent<TilemapRenderer>();
            bool on = BlocksEnabled && material != null && !smooth;
            if (sr != null) sr.enabled = !on && !smooth;
            if (blockRenderer != null) blockRenderer.enabled = on;
            if (tileCollider != null) tileCollider.enabled = !smooth;
            if (composite != null) composite.enabled = !smooth;
            if (!smooth) for (int i = 0; i < edges.Count; i++) edges[i].enabled = false;
        }

        // ---------- U-156: the smooth ground (D-161 / D-162, Bible 5.0) ----------

        /// <summary>True on a smooth planet: FinishCollision traces the outline (GroundField / GroundContour) into edge colliders.</summary>
        public bool smooth;
        readonly GroundContour contour = new GroundContour();
        /// <summary>The chunk's traced outline and fill (chunk-local metres), for the ground mesh and tests.</summary>
        public GroundContour Contour => contour;
        /// <summary>U-156: the natural surface's standing height at this chunk's 33 node columns (tile centres from one left of it): the dug-hole
        /// back wall is drawn under it. NaN where the column has no surface.</summary>
        public readonly float[] SurfaceCurve = new float[TerrainConstants.ChunkSize + 1];
        readonly System.Collections.Generic.List<EdgeCollider2D> edges = new System.Collections.Generic.List<EdgeCollider2D>(4);
        /// <summary>The edge colliders in use (one per outline).</summary>
        public int OutlineColliders { get; private set; }
        static float[] nodes;
        static int[] tops;
        static float[] curve;
        static readonly System.Collections.Generic.List<Vector2> chain = new System.Collections.Generic.List<Vector2>(256);
        /// <summary>Raised on the main thread after a chunk's outline is rebuilt (SmoothGround rebuilds its mesh from it).</summary>
        public static event System.Action<TerrainChunk> OutlineBuilt;

        /// <summary>
        /// U-156: the chunk's field nodes are the tile centres from one tile left of / under it to its last tile (33 × 33): a natural tile (its
        /// solidity as the original surface left it, OriginalTop) follows its column's curve; a dug or built one is its own solidity. Traced
        /// at ¼ m, each outline becomes one EdgeCollider2D on the chunk's static body; the mesh follows through OutlineBuilt.
        /// </summary>
        void BuildOutline()
        {
            const int C = TerrainConstants.ChunkSize;
            if (!filled || world == null)
            {
                for (int i = 0; i < edges.Count; i++) edges[i].enabled = false;
                OutlineColliders = 0;
                contour.Build(System.Array.Empty<float>(), 0, Vector2.zero);
                OutlineBuilt?.Invoke(this);
                return;
            }
            int r = GroundField.CurveKernel.Length / 2;
            nodes ??= new float[(C + 1) * (C + 1)];
            tops ??= new int[C + 1 + 2 * r];
            curve ??= new float[C + 1];
            int x0 = cx * C, y0 = cy * C, t0 = x0 - 1 - r;
            for (int k = 0; k < tops.Length; k++) tops[k] = world.WallTop(t0 + k);
            for (int i = 0; i <= C; i++) curve[i] = GroundField.Curve(x0 - 1 + i, x => tops[x - t0]);
            for (int i = 0; i <= C; i++) SurfaceCurve[i] = tops[i + r] == int.MinValue ? float.NaN : curve[i];
            for (int j = 0; j <= C; j++)
            {
                int ty = y0 - 1 + j;
                for (int i = 0; i <= C; i++)
                {
                    int tx = x0 - 1 + i;
                    byte id = tx >= x0 && ty >= y0 ? ids[(ty - y0) * C + (tx - x0)] : world.TileAt(tx, ty);
                    bool solid = TileId.IsSolid(id);
                    int top = tops[tx - t0];
                    bool natural = top != int.MinValue && solid == (ty <= top);
                    nodes[j * (C + 1) + i] = GroundField.Density(solid, natural, curve[i], ty);
                }
            }
            contour.Build(nodes, C, new Vector2(-0.5f, -0.5f));
            int lines = contour.Lines;
            while (edges.Count < lines) edges.Add(gameObject.AddComponent<EdgeCollider2D>());
            int used = 0;
            for (int i = 0; i < edges.Count; i++)
            {
                var e = edges[i];
                if (i >= lines || contour.lineCount[i] < 2) { if (e.enabled) e.enabled = false; continue; }
                chain.Clear();
                int s = contour.lineStart[i], n = contour.lineCount[i];
                for (int k = 0; k < n; k++) chain.Add(contour.points[s + k]);
                if (contour.lineClosed[i]) chain.Add(contour.points[s]);
                e.SetPoints(chain);
                if (!e.enabled) e.enabled = true;
                used++;
            }
            OutlineColliders = used;
            OutlineBuilt?.Invoke(this);
        }

        bool filled;

        void BuildBlocks()
        {
            if (blockRenderer == null || !blockRenderer.enabled) return;
            if (!filled) { blockMesh.Clear(); BlockQuads = 0; return; } // pooled/cleared: nothing to show
            const int C = TerrainConstants.ChunkSize;
            buffers ??= new BlockMesher.Buffers();
            outsideFn ??= (lx, ly) => world != null ? world.TileAt(cx * C + lx, cy * C + ly) : TileId.Air;
            wallFn ??= lx =>
            {
                if (world == null) return -1;
                int top = world.WallTop(cx * C + lx);
                return top == int.MinValue ? -1 : top - cy * C;
            };
            var watch = System.Diagnostics.Stopwatch.StartNew();
            BlockMesher.Build(ids, outsideFn, wallFn, cx * C, cy * C, buffers);
            blockMesh.Clear();
            blockMesh.SetVertices(buffers.vertices);
            blockMesh.SetNormals(buffers.normals);
            blockMesh.SetUVs(0, buffers.uv);
            blockMesh.SetTriangles(buffers.triangles, 0, false);
            blockMesh.bounds = new Bounds(new Vector3(C * 0.5f, C * 0.5f, 0.25f), new Vector3(C, C, BlockMesher.BackWallZ - BlockMesher.FrontZ + 0.5f));
            BlockQuads = buffers.Quads;
            LastBuildMs = watch.Elapsed.TotalMilliseconds;
        }

        // Allocating the full 32×32 up front keeps SetTilesBlock from growing bounds mid-stream.
        static void FixBounds(Tilemap map)
        {
            map.origin = Vector3Int.zero;
            map.size = new Vector3Int(TerrainConstants.ChunkSize, TerrainConstants.ChunkSize, 1);
            map.ResizeBounds();
        }

        /// <summary>Rebuilds merged collision after the last band; the only collider work per chunk.</summary>
        public void FinishCollision()
        {
            if (smooth) { BuildOutline(); return; } // U-156: the outline is the collision and the ground mesh's source
            // The tilemap collider applies tile changes lazily; flush them first or the merged
            // collider is built from stale shapes and bodies can fall through fresh ground.
            tileCollider.ProcessTilemapChanges();
            composite.GenerateGeometry();
            BuildBlocks(); // U-073: the block mesh follows every finished stream and every edit, in the same frame
        }

        public static TerrainChunk Create(Transform parent)
        {
            var go = new GameObject("Chunk");
            go.transform.SetParent(parent, false);
            var chunk = go.AddComponent<TerrainChunk>();

            chunk.solid = go.AddComponent<Tilemap>();
            var sr = go.AddComponent<TilemapRenderer>();
            sr.mode = TilemapRenderer.Mode.Chunk;
            // U-064: a renderer added at runtime gets Unity's unlit default sprite material, so the terrain ignored
            // every 2D light (full brightness at night, no lamp pool). Use the art's lit material (normal maps on).
            var lit = Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.lit : null;
            if (lit != null) sr.sharedMaterial = lit;
            var body = go.AddComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Static;
            var tc = go.AddComponent<TilemapCollider2D>();
            tc.compositeOperation = Collider2D.CompositeOperation.Merge;
            chunk.tileCollider = tc;
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
            if (lit != null) lr.sharedMaterial = lit;
            // See-through water (U-037): the backdrop behind it darkens with depth and the seabed stays visible.
            chunk.liquid.color = new Color(1f, 1f, 1f, WaterAlpha);
            FixBounds(chunk.liquid);

            // U-073: the block mesh renderer (material and world come from the streamer via UseBlocks).
            var blocksGo = new GameObject("Blocks");
            blocksGo.transform.SetParent(go.transform, false);
            chunk.blockMesh = new Mesh { name = "ChunkBlocks" };
            chunk.blockMesh.MarkDynamic();
            blocksGo.AddComponent<MeshFilter>().sharedMesh = chunk.blockMesh;
            chunk.blockRenderer = blocksGo.AddComponent<MeshRenderer>();
            chunk.blockRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            chunk.blockRenderer.receiveShadows = true;
            chunk.blockRenderer.enabled = false;
            return chunk;
        }

        /// <summary>Rows written per apply step, so one chunk spreads over frames within the 2 ms budget.</summary>
        public const int RowsPerStep = 4;

        public void Begin(ChunkBuffer data)
        {
            cx = data.cx; cy = data.cy;
            transform.localPosition = new Vector3(cx * TerrainConstants.ChunkSize, cy * TerrainConstants.ChunkSize, 0f);
            filled = true;
        }

        /// <summary>Writes rows [row, row + RowsPerStep) into the tilemaps. Scratch arrays (RowsPerStep × 32) are the caller's.</summary>
        public void ApplyRows(ChunkBuffer data, TerrainTileSet set, int row, TileBase[] solidScratch, TileBase[] liquidScratch, int worldWidth)
        {
            const int C = TerrainConstants.ChunkSize;
            int start = row * C;
            for (int i = 0; i < RowsPerStep * C; i++)
            {
                byte id = data.ids[start + i];
                ids[start + i] = id; // U-073: the mesher's copy (same row-major layout)
                int wx = ((data.cx * C + i % C) % worldWidth + worldWidth) % worldWidth;
                var tile = id == TileId.Air ? null : set.Get(id, data.blob[start + i], wx, data.cy * C + row + i / C);
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
            ids[ly * TerrainConstants.ChunkSize + lx] = id; // U-073
            solid.SetTile(p, isLiquid ? null : tile);
            liquid.SetTile(p, isLiquid ? tile : null);
        }

        public void Clear()
        {
            solid.ClearAllTiles();
            liquid.ClearAllTiles();
            System.Array.Clear(ids, 0, ids.Length); // U-073: empty mesh until the next stream
            filled = false;
            FixBounds(solid);
            FixBounds(liquid);
            FinishCollision();
            // Stays active: re-enabling colliders and renderers costs more than the 2 ms apply budget allows.
        }
    }
}
