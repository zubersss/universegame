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
            /// <summary>U-156: the pad height where column x lies across a stamped POI on a smooth planet; int.MinValue elsewhere.</summary>
            int PadTop(int x);
            /// <summary>U-157 (P-54): a brushed tile's fill level (0-255), if it has one.</summary>
            bool TryLevel(int x, int y, out byte level);
            /// <summary>U-157: any density blocks in chunk (cx, cy).</summary>
            bool HasLevels(int cx, int cy);
            /// <summary>U-157 (D-168): a brushed tile's quarter-metre density block (read only), if it has one.</summary>
            bool TryBlock(int x, int y, out byte[] block);
            /// <summary>U-157 (D-168): the drawn ground's density at a world point (the sub-nodes, bilinear).</summary>
            float FieldAt(Vector2 p);
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
        // U-156: the water tile (ApplyRows and SetTileLocal remember it) and the cells this chunk filled with it under a submerged column.
        static TileBase waterTile;
        readonly System.Collections.Generic.List<int> shoreWater = new System.Collections.Generic.List<int>(32);

        /// <summary>U-156: on a smooth planet the drawn ground can sit below a submerged column's top tile, so water fills that tile's cell too (the
        /// ground mesh covers it under the outline): blocky water never leaves a step of open backdrop over a rounded crest. View only; swimming
        /// reads the tile ids.</summary>
        void ShoreWater(int x0, int y0)
        {
            const int C = TerrainConstants.ChunkSize;
            for (int k = 0; k < shoreWater.Count; k++) { int i = shoreWater[k]; if (!TileId.IsLiquid(ids[i])) liquid.SetTile(new Vector3Int(i % C, i / C, 0), null); }
            shoreWater.Clear();
            if (waterTile == null) return;
            for (int ly = 0; ly < C; ly++)
                for (int lx = 0; lx < C; lx++)
                {
                    int i = ly * C + lx;
                    if (!TileId.IsSolid(ids[i])) continue;
                    byte above = ly + 1 < C ? ids[i + C] : world.TileAt(x0 + lx, y0 + ly + 1);
                    if (!TileId.IsLiquid(above)) continue;
                    liquid.SetTile(new Vector3Int(lx, ly, 0), waterTile);
                    shoreWater.Add(i);
                }
        }

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
            ShoreWater(x0, y0);
            for (int k = 0; k < tops.Length; k++) tops[k] = world.WallTop(t0 + k);
            for (int i = 0; i <= C; i++) curve[i] = GroundField.Curve(x0 - 1 + i, x => tops[x - t0], world.PadTop);
            for (int i = 0; i <= C; i++) SurfaceCurve[i] = tops[i + r] == int.MinValue ? float.NaN : curve[i];
            bool levelled = world.HasLevels(cx, cy) || world.HasLevels(cx - 1, cy) || world.HasLevels(cx, cy - 1) || world.HasLevels(cx - 1, cy - 1);
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
                    float density = GroundField.Density(solid, natural, curve[i], ty);
                    if (levelled && world.TryLevel(tx, ty, out byte level)) density = level / 255f; // U-157 (P-54): a brushed tile's node density
                    nodes[j * (C + 1) + i] = density;
                }
            }
            outlineLevelled = levelled;
            if (levelled) { FillSubNodes(x0, y0); contour.Build(nodes, C, new Vector2(-0.5f, -0.5f), GroundField.Iso, subNodes, subCells); }
            else contour.Build(nodes, C, new Vector2(-0.5f, -0.5f));
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
                // U-156 (LEAD, the stag's attempt 3): an open chain leaves through the chunk's edge and goes on in the neighbour's outline; Box2D's
                // ghost vertices get that outline's next node, so a box sliding across the seam meets one surface, not a corner.
                bool open = !contour.lineClosed[i];
                e.useAdjacentStartPoint = open; e.useAdjacentEndPoint = open;
                if (open)
                {
                    e.adjacentStartPoint = Beyond(chain[0], chain[1], x0, y0);
                    e.adjacentEndPoint = Beyond(chain[n - 1], chain[n - 2], x0, y0);
                }
                if (!e.enabled) e.enabled = true;
                used++;
            }
            OutlineColliders = used;
            OutlineBuilt?.Invoke(this);
        }

        // U-157 (D-168): the quarter-metre sub-node values of this chunk's brushed tiles, shared by every chunk (the outline is built on the main
        // thread, one chunk at a time), and the 1 m cells they touch.
        static float[] subNodes;
        static bool[] subCells;
        bool outlineLevelled;

        /// <summary>U-157 (D-168): copies every brushed tile's block over the chunk's sub-node grid (node (i, j) is tile (x0 − 1 + i, y0 − 1 + j);
        /// its block's sub-node (a, b) is sub-node (i·Sub + a, j·Sub + b)) and flags the cells round it, so they are traced sub-cell by sub-cell.</summary>
        void FillSubNodes(int x0, int y0)
        {
            const int C = TerrainConstants.ChunkSize, Sub = GroundContour.Sub, M = C * Sub;
            if (subNodes == null) { subNodes = new float[(M + 1) * (M + 1)]; subCells = new bool[C * C]; }
            for (int k = 0; k < subNodes.Length; k++) subNodes[k] = float.NaN;
            System.Array.Clear(subCells, 0, subCells.Length);
            for (int j = 0; j <= C; j++)
                for (int i = 0; i <= C; i++)
                {
                    if (!world.TryBlock(x0 - 1 + i, y0 - 1 + j, out var blk)) continue;
                    for (int b = 0; b < Sub; b++)
                    {
                        int sj = j * Sub + b;
                        if (sj > M) break;
                        for (int a = 0; a < Sub; a++)
                        {
                            int si = i * Sub + a;
                            if (si > M) break;
                            subNodes[sj * (M + 1) + si] = blk[b * Sub + a] / 255f;
                        }
                    }
                    for (int dj = -1; dj <= 0; dj++)
                        for (int di = -1; di <= 0; di++)
                        {
                            int ci = i + di, cj = j + dj;
                            if (ci >= 0 && ci < C && cj >= 0 && cj < C) subCells[cj * C + ci] = true;
                        }
                }
        }

        /// <summary>U-156: the neighbour outline's node next to a chain's end on this chunk's side (the iso crossing in the neighbour's first ¼ m
        /// sub-cell, from the same field), or the chain carried on straight where that is ambiguous (a top or bottom edge, a sub-cell corner).</summary>
        Vector2 Beyond(Vector2 end, Vector2 inner, int x0, int y0)
        {
            const int C = TerrainConstants.ChunkSize;
            const float Sub = 1f / GroundContour.Sub;
            Vector2 straight = end + (end - inner);
            bool right = end.x > C - 1f, left = end.x < 0f;
            if (!right && !left) return straight;
            float fy = (end.y + 0.5f) / Sub;
            if (Mathf.Abs(fy - Mathf.Round(fy)) < 1e-3f) return straight;
            float xa = right ? end.x : end.x - Sub, xb = xa + Sub, far = right ? xb : xa;
            float ya = -0.5f + Mathf.Floor(fy) * Sub, yb = ya + Sub;
            float iso = GroundField.Iso;
            float fa = Field(far, ya, x0, y0) - iso, fb = Field(far, yb, x0, y0) - iso;
            if (fa * fb < 0f) return new Vector2(far, ya + fa / (fa - fb) * Sub);
            float ta = Field(xa, yb, x0, y0) - iso, tb = Field(xb, yb, x0, y0) - iso;
            if (ta * tb < 0f) return new Vector2(xa + ta / (ta - tb) * Sub, yb);
            float ba = Field(xa, ya, x0, y0) - iso, bb = Field(xb, ya, x0, y0) - iso;
            if (ba * bb < 0f) return new Vector2(xa + ba / (ba - bb) * Sub, ya);
            return straight;
        }

        /// <summary>The field at a chunk-local point: the four tile-centre nodes round it, bilinear (past this chunk's nodes, from the world).</summary>
        float Field(float lx, float ly, int x0, int y0)
        {
            if (outlineLevelled) return world.FieldAt(new Vector2(x0 + lx, y0 + ly)); // U-157 (D-168): the brushed blocks, as traced
            float fi = lx + 0.5f, fj = ly + 0.5f;
            int i = Mathf.FloorToInt(fi), j = Mathf.FloorToInt(fj);
            float u = fi - i, v = fj - j;
            float b = Mathf.Lerp(NodeAt(i, j, x0, y0), NodeAt(i + 1, j, x0, y0), u);
            float t = Mathf.Lerp(NodeAt(i, j + 1, x0, y0), NodeAt(i + 1, j + 1, x0, y0), u);
            return Mathf.Lerp(b, t, v);
        }

        float NodeAt(int i, int j, int x0, int y0)
        {
            const int C = TerrainConstants.ChunkSize;
            if (i >= 0 && i <= C && j >= 0 && j <= C) return nodes[j * (C + 1) + i];
            int tx = x0 - 1 + i, ty = y0 - 1 + j;
            bool solid = TileId.IsSolid(world.TileAt(tx, ty));
            int top = world.WallTop(tx);
            if (world.TryLevel(tx, ty, out byte level)) return level / 255f;
            float curveAt = GroundField.Curve(tx, world.WallTop, world.PadTop);
            return GroundField.Density(solid, top != int.MinValue && solid == (ty <= top), curveAt, ty);
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
                if (isLiquid && tile != null) waterTile = tile; // U-156
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
            if (isLiquid && tile != null) waterTile = tile; // U-156
        }

        public void Clear()
        {
            solid.ClearAllTiles();
            shoreWater.Clear(); // U-156
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
