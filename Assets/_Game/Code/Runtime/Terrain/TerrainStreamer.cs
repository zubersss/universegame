using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using Meridian.Planets;
using UnityEngine;
using UnityEngine.Tilemaps;
using Debug = UnityEngine.Debug;

namespace Meridian.Terrain
{
    /// <summary>
    /// Streams chunks around the camera (Bible §10.4): generation on a worker thread, apply on
    /// the main thread within 2 ms per frame, chunks within ResidentRadius (3) of the camera resident, others
    /// pooled. The world wraps in x.
    /// </summary>
    public sealed class TerrainStreamer : MonoBehaviour, TerrainChunk.IBlockWorld
    {
        const int C = TerrainConstants.ChunkSize, R = TerrainConstants.ResidentRadius;

        public Transform follow;

        public IWorldGenerator Generator { get; private set; }
        public IWorldGenerator BaseGenerator { get; private set; }
        public TerrainEdits Edits { get; private set; }
        public TerrainTileSet TileSet => tileSet;
        /// <summary>(x, y, old id, new id) after a tile changes through SetTile.</summary>
        public event System.Action<int, int, byte, byte> TileChanged;
        public PlanetConfig Config { get; private set; }
        public int ResidentCount => resident.Count;
        public int PendingCount => pending.Count;
        public double LastApplyMs { get; private set; }
        public double MaxApplyMs { get; private set; }
        public double MaxBandMs { get; private set; }
        /// <summary>
        /// Settled: the sheets are in, the first streaming pass has queued the chunks around the target, and none is pending or
        /// mid-apply. U-091: with prefetched sheets the tile set is ready the instant Begin returns, so without `firstPass` the
        /// frame before the first Update read as settled and released the surveyor into empty space (the C0 smoke "fall").
        /// </summary>
        public bool IsSettled => started && firstPass && tileSet.IsReady && pending.Count == 0 && ready.IsEmpty && inProgress == null;
        /// <summary>U-156 (D-161 / D-162): true on a smooth planet: the chunks trace the outline (edge colliders, the ground mesh) instead of tiles and blocks.</summary>
        public bool SmoothGround { get; private set; }

        /// <summary>U-120: the per-frame apply budget while the first window fills after Begin (behind the boot cover or the entry fade), in ms.
        /// The cold first boot spent ~5 s of its 6–8 s settling the terrain at TerrainConstants.ApplyPlanMs (1 ms) with nothing on screen.</summary>
        public const double FirstFillPlanMs = 12.0;
        /// <summary>True once the streamer has settled since Begin; the apply budget is FirstFillPlanMs before, ApplyPlanMs after.</summary>
        public bool FirstFillDone { get; private set; }
        /// <summary>The apply budget for a frame: the first fill's wide window until the first settle, the streaming budget after. Pure.</summary>
        public static double PlanMs(bool firstFillDone) => firstFillDone ? TerrainConstants.ApplyPlanMs : FirstFillPlanMs;
        bool firstPass;

        readonly Dictionary<long, TerrainChunk> resident = new Dictionary<long, TerrainChunk>(32);
        readonly HashSet<long> pending = new HashSet<long>();
        readonly HashSet<long> stale = new HashSet<long>();
        readonly List<TerrainChunk> touched = new List<TerrainChunk>(4);
        readonly Stack<TerrainChunk> pool = new Stack<TerrainChunk>(32);
        readonly List<long> scratchKeys = new List<long>(32);
        readonly TileBase[] solidScratch = new TileBase[TerrainChunk.RowsPerStep * C];
        readonly TileBase[] liquidScratch = new TileBase[TerrainChunk.RowsPerStep * C];
        ChunkBuffer inProgress;
        TerrainChunk inProgressChunk;
        int nextRow;
        double bandEstimateMs;
        readonly Stopwatch watch = new Stopwatch();

        readonly ConcurrentQueue<ChunkBuffer> ready = new ConcurrentQueue<ChunkBuffer>();
        BlockingCollection<ChunkBuffer> inbox;
        Thread worker;
        TerrainTileSet tileSet = new TerrainTileSet();
        int chunksY, lastCx = int.MinValue, lastCy = int.MinValue;
        bool started;

        public void Begin(PlanetConfig config, int seed, Transform target, TerrainEdits edits = null)
        {
            Stop();
            Config = config;
            follow = target;
            // U-061: the giants are cloud columns (floes, no ground) behind the same generator interface.
            BaseGenerator = config.worldType == WorldType.CloudColumn
                ? new Meridian.Terrain.CloudColumn.CloudWorldGenerator(config, seed)
                : new SolidWorldGenerator(config, seed);
            Edits = edits ?? new TerrainEdits();
            Generator = new EditedWorld(BaseGenerator, Edits);
            stale.Clear();
            chunksY = config.worldHeight / C;
            tileSet = new TerrainTileSet();
            tileSet.Load(MaterialsFor(config.id));

            inbox = new BlockingCollection<ChunkBuffer>(new ConcurrentQueue<ChunkBuffer>());
            var gen = Generator;
            var queue = inbox;
            worker = new Thread(() => Work(gen, queue)) { IsBackground = true, Name = "MERIDIAN terrain" };
            worker.Start();
            lastCx = lastCy = int.MinValue;
            // Pre-warm the pool at load so streaming never pays for GameObject creation.
            int needed = (2 * R + 1) * (2 * R + 1) + 2 * R + 1;
            while (pool.Count + resident.Count < needed) pool.Push(TerrainChunk.Create(transform));
            // U-073: block meshes with the planet's palette (one shared material instance per streamer).
            wallTops = null; // per-planet back-wall tops, recomputed lazily
            var reg = Meridian.Rendering.ArtMaterials.Active;
            if (blockMaterial == null && reg != null && reg.terrainBlocks != null) blockMaterial = new Material(reg.terrainBlocks) { name = "Terrain_Blocks (planet)" };
            if (blockMaterial != null)
            {
                // B-080: real block textures (colour/normal/mask arrays) when the planet has them; else the flat palette.
                var arrays = TerrainBlockPalette.ArraysFor(config.id);
                blockMaterial.SetTexture(BlockArrayId, arrays.color);
                if (arrays.Real)
                {
                    blockMaterial.SetTexture(BlockNormalsId, arrays.normal);
                    blockMaterial.SetTexture(BlockMasksId, arrays.mask);
                    blockMaterial.EnableKeyword("_BLOCK_MAPS");
                }
                else blockMaterial.DisableKeyword("_BLOCK_MAPS");
                // D-067: the grass top colour blends down the top ~8 cm of grass side faces.
                blockMaterial.SetFloat(FringeLayerId, BlockMesher.SideLayer(TileId.Grass));
            }
            SmoothGround = config.worldType == WorldType.Solid && GroundField.Smooth(config.id); // U-156 (D-161 / D-162): the traced outline on a smooth planet
            foreach (var c in pool) c.UseBlocks(this, blockMaterial, SmoothGround);
            foreach (var c in resident.Values) c.UseBlocks(this, blockMaterial, SmoothGround);
            started = true;
            firstPass = false;
            FirstFillDone = false; // U-120: a fresh window fills under the wide budget
        }

        // ---------- U-073: the world as the block mesher sees it ----------
        static readonly int BlockArrayId = Shader.PropertyToID("_BlockArray");
        static readonly int BlockNormalsId = Shader.PropertyToID("_BlockNormals");
        static readonly int BlockMasksId = Shader.PropertyToID("_BlockMasks");
        static readonly int FringeLayerId = Shader.PropertyToID("_FringeLayer");
        Material blockMaterial;

        /// <summary>The planet's block material (tests, captures).</summary>
        public Material BlockMaterial => blockMaterial;

        byte TerrainChunk.IBlockWorld.TileAt(int x, int y) => GetTile(x, y);

        // Back-wall top per column: the original surface, lowered where a POI stamp shaped the ground (the spawn camp
        // levels a hill: without this the wall filled the levelled cells). Player digs don't count, so digging shows
        // the wall. Computed once per column per planet.
        int[] wallTops;
        Meridian.Planet.POI.PoiDef[] wallPois;
        int[] wallPoiPad;
        const int WallUnknown = int.MinValue + 1;

        /// <summary>U-076: the column's original surface row (POI-shaped ground included, player digs not): the ground behind the play plane.</summary>
        public int OriginalTop(int x) => ((TerrainChunk.IBlockWorld)this).WallTop(x);

        /// <summary>U-156: the pad height across a stamped POI on a smooth planet (the drawn curve holds it flat to the stamp's ends); int.MinValue
        /// elsewhere and on every other planet.</summary>
        public int PadTop(int x) => SmoothGround && Config != null ? Meridian.Planet.POI.PoiStamp.PadAt(BaseGenerator, Config.datumY, Config.id, x) : int.MinValue;

        /// <summary>U-156: the drawn surface's height over column x's centre on a smooth planet (the outline's line where nothing is dug or built).</summary>
        public float CurveAt(int x) => GroundField.Curve(x, OriginalTop, PadTop);

        /// <summary>U-157 (P-54): a brushed tile's node density (0-255: its block's [0]), if it has a block.</summary>
        public bool TryLevel(int x, int y, out byte level) { level = 0; return Edits != null && Edits.TryGetLevel(WrapX(x), y, out level); }

        /// <summary>U-157 (D-168): a brushed tile's quarter-metre density block (TerrainEdits.Block bytes; read only), if it has one.</summary>
        public bool TryBlock(int x, int y, out byte[] block) { block = null; return Edits != null && Edits.TryGetBlock(WrapX(x), y, out block); }

        /// <summary>U-157: any density blocks in chunk (cx, cy) (cx may be unwrapped).</summary>
        public bool HasLevels(int cx, int cy) => Edits != null && Config != null && Edits.HasLevels(WorldNoise.FloorDiv(WrapX(cx * C), C), cy);

        /// <summary>U-157 (D-168): any density block that can shape the field round tile (x, y) (its chunk or the chunk past either far edge).</summary>
        public bool HasLevelsNear(int x, int y)
        {
            int cx = WorldNoise.FloorDiv(x, C), cy = WorldNoise.FloorDiv(y, C), cx1 = WorldNoise.FloorDiv(x + 1, C), cy1 = WorldNoise.FloorDiv(y + 1, C);
            return HasLevels(cx, cy) || HasLevels(cx1, cy) || HasLevels(cx, cy1) || HasLevels(cx1, cy1);
        }

        /// <summary>U-157 (D-168): stores a tile's density block (the array is kept) and retraces the outlines round it (batched within
        /// BeginBatch / EndBatch). An array already stored for the tile may be passed again after an in-place change.</summary>
        public void SetBlock(int x, int y, byte[] block)
        {
            if (!started || Edits == null || y < 0 || y >= Config.worldHeight) return;
            Edits.SetBlock(WrapX(x), y, block);
            RefreshAround(x, y);
        }

        /// <summary>U-157 (D-168): quarter-metre sub-nodes per metre (GroundContour.Sub, TerrainEdits.BlockSide).</summary>
        public const int Sub = TerrainEdits.BlockSide;

        /// <summary>U-157 (D-168): the drawn ground's density at the global sub-node (i, j), which sits at (i / Sub + 1/2, j / Sub + 1/2): a brushed
        /// tile's block value, else bilinear between the four tile-centre nodes round it (what the tracer does between nodes).</summary>
        public float SubDensity(int i, int j)
        {
            int tx = WorldNoise.FloorDiv(i, Sub), ty = WorldNoise.FloorDiv(j, Sub), a = i - tx * Sub, b = j - ty * Sub;
            if (TryBlock(tx, ty, out var blk)) return blk[b * Sub + a] / 255f;
            float n00 = NodeDensity(tx, ty);
            if (a == 0 && b == 0) return n00;
            float fx = a / (float)Sub, fy = b / (float)Sub;
            float n10 = a == 0 ? n00 : NodeDensity(tx + 1, ty), n01 = b == 0 ? n00 : NodeDensity(tx, ty + 1);
            float n11 = a == 0 ? n01 : b == 0 ? n10 : NodeDensity(tx + 1, ty + 1);
            return Mathf.Lerp(Mathf.Lerp(n00, n10, fx), Mathf.Lerp(n01, n11, fx), fy);
        }

        /// <summary>U-157 (D-168): the drawn ground's density at world p, bilinear between the sub-nodes round it; the traced outline is its iso.</summary>
        public float FieldAt(Vector2 p)
        {
            float u = (p.x - 0.5f) * Sub, v = (p.y - 0.5f) * Sub;
            int i = Mathf.FloorToInt(u), j = Mathf.FloorToInt(v);
            float fx = u - i, fy = v - j;
            float a = SubDensity(i, j), b = SubDensity(i + 1, j), c = SubDensity(i, j + 1), d = SubDensity(i + 1, j + 1);
            return Mathf.Lerp(Mathf.Lerp(a, b, fx), Mathf.Lerp(c, d, fx), fy);
        }

        /// <summary>U-157: the drawn ground's density at tile (x, y)'s centre: its fill level if brushed, else the natural surface's ramp for a
        /// natural tile, else 1 / 0 for a dug or built one (GroundField.Density).</summary>
        public float NodeDensity(int x, int y)
        {
            if (TryLevel(x, y, out byte l)) return l / 255f;
            bool solid = TileId.IsSolid(GetTile(x, y));
            int top = OriginalTop(x);
            return GroundField.Density(solid, top != int.MinValue && solid == (y <= top), CurveAt(x), y);
        }

        /// <summary>U-156: the drawn outline's height at world x where nothing is dug or built (the curve between column centres, linear, as
        /// the marching squares trace it).</summary>
        public float SurfaceAt(float x)
        {
            float fx = x - 0.5f;
            int i = Mathf.FloorToInt(fx);
            return Mathf.Lerp(CurveAt(i), CurveAt(i + 1), fx - i);
        }

        int TerrainChunk.IBlockWorld.WallTop(int x)
        {
            if (Config == null || Config.worldType != WorldType.Solid) return int.MinValue;
            int wx = WrapX(x);
            if (wallTops == null || wallTops.Length != Config.worldWidth)
            {
                wallTops = new int[Config.worldWidth];
                for (int i = 0; i < wallTops.Length; i++) wallTops[i] = WallUnknown;
                var list = new List<Meridian.Planet.POI.PoiDef>();
                foreach (var p in Meridian.Planet.POI.PoiCatalog.For(Config.id)) if (!p.Floating && p.stamp != null) list.Add(p);
                wallPois = list.ToArray();
                wallPoiPad = new int[wallPois.Length];
                for (int i = 0; i < wallPois.Length; i++) wallPoiPad[i] = Meridian.Planet.POI.PoiStamp.GroundY(wallPois[i], BaseGenerator, Config.datumY);
            }
            int top = wallTops[wx];
            if (top != WallUnknown) return top;
            top = BaseGenerator.SurfaceHeight(wx);
            // U-156: on a smooth planet a stamp's shaped ground IS the column's surface, raised or cut (the curve eases a raised pad too);
            // elsewhere the back wall keeps the lower of the two, as before.
            if (SmoothGround) { if (Meridian.Planet.POI.PoiStamp.JointGround(BaseGenerator, Config.datumY, Config.id, wx, out int joint)) top = joint; }
            else
                for (int i = 0; i < wallPois.Length; i++)
                    if (Meridian.Planet.POI.PoiStamp.ShapedGround(wallPois[i], BaseGenerator, Config.datumY, wx, out int g, wallPoiPad[i]) && g < top) top = g;
            wallTops[wx] = top;
            return top;
        }

        public static IEnumerable<byte> MaterialsFor(PlanetId id) => id switch
        {
            PlanetId.Earth => new[] { TileId.Soil, TileId.Grass, TileId.Stone, TileId.Sand, TileId.Snow, TileId.Water },
            PlanetId.Mercury => new[] { TileId.MercuryRegolith, TileId.MercuryBasalt, TileId.Sulfide, TileId.MercuryIce },
            PlanetId.Venus => new[] { TileId.VenusBasalt, TileId.Sulfur, TileId.Tessera, TileId.VentGlass },
            // U-061: the giants' cloud columns hold only floes (ice skin over a denser core; Jupiter's art for now, B-048).
            PlanetId.Jupiter or PlanetId.Saturn or PlanetId.Uranus or PlanetId.Neptune => new[] { TileId.FloeIce, TileId.FloeCore },
            // Mars: the polar cap wears CO₂ frost (Snow) over its ice (U-039); without it the frost had no art and no collision (U-064).
            _ => new[] { TileId.Regolith, TileId.Basalt, TileId.Hematite, TileId.Ice, TileId.Snow },
        };

        void Work(IWorldGenerator gen, BlockingCollection<ChunkBuffer> queue)
        {
            try
            {
                foreach (var b in queue.GetConsumingEnumerable())
                {
                    b.Generate(gen);
                    ready.Enqueue(b);
                }
            }
            catch (System.Exception e) { Debug.LogException(e); }
        }

        // U-156 / D-165 (a): on a smooth planet a buried body is lifted onto the outline (an edge outline cannot push it out).
        void FixedUpdate()
        {
            if (started && SmoothGround && Config != null) SolidRescue.Tick(this);
        }

        void Update()
        {
            if (!started || follow == null) return;
            var p = follow.position;
            int ccx = WorldNoise.FloorDiv(Mathf.FloorToInt(p.x), C);
            int ccy = Mathf.Clamp(WorldNoise.FloorDiv(Mathf.FloorToInt(p.y), C), 0, chunksY - 1);
            if (ccx != lastCx || ccy != lastCy)
            {
                lastCx = ccx; lastCy = ccy;
                Retarget(ccx, ccy);
            }
            ApplyReady();
            firstPass = true;
            if (!FirstFillDone && IsSettled) FirstFillDone = true; // U-120: from here the streaming budget rules
        }

        bool Wanted(int cx, int cy) =>
            Mathf.Abs(cx - lastCx) <= R && Mathf.Abs(cy - lastCy) <= R && cy >= 0 && cy < chunksY;

        void Retarget(int ccx, int ccy)
        {
            scratchKeys.Clear();
            foreach (var kv in resident)
                if (!Wanted(kv.Value.cx, kv.Value.cy)) scratchKeys.Add(kv.Key);
            foreach (var key in scratchKeys)
            {
                var chunk = resident[key];
                resident.Remove(key);
                chunk.Clear();
                pool.Push(chunk);
            }

            // Nearest first: rings outward from the camera chunk.
            for (int ring = 0; ring <= R; ring++)
            for (int dy = -ring; dy <= ring; dy++)
            for (int dx = -ring; dx <= ring; dx++)
            {
                if (Mathf.Max(Mathf.Abs(dx), Mathf.Abs(dy)) != ring) continue;
                int cx = ccx + dx, cy = ccy + dy;
                if (cy < 0 || cy >= chunksY) continue;
                long key = ChunkBuffer.Key(cx, cy);
                if (resident.ContainsKey(key) || pending.Contains(key)) continue;
                pending.Add(key);
                inbox.Add(ChunkBuffer.Rent(cx, cy));
            }
        }

        void ApplyReady()
        {
            if (!tileSet.IsReady) return;
            watch.Restart();
            double step = bandEstimateMs;
            // Start another band only if the slowest recent band still fits in the budget;
            // always do at least one so streaming can't stall.
            bool first = true;
            double plan = PlanMs(FirstFillDone); // U-120: the first fill behind the cover takes a wide window
            while (first || watch.Elapsed.TotalMilliseconds + step < plan)
            {
                first = false;
                if (inProgress == null && !StartNext()) break;
                if (!resident.ContainsKey(ChunkBuffer.Key(inProgress.cx, inProgress.cy)))
                {
                    // Released by Retarget while half-written.
                    ChunkBuffer.Return(inProgress);
                    inProgress = null;
                    continue;
                }
                double before = watch.Elapsed.TotalMilliseconds;
                if (nextRow < C) inProgressChunk.ApplyRows(inProgress, tileSet, nextRow, solidScratch, liquidScratch, Config.worldWidth);
                else inProgressChunk.FinishCollision(); // one extra step after the last band
                double cost = watch.Elapsed.TotalMilliseconds - before;
                step = System.Math.Max(step, cost);
                if (cost > MaxBandMs) MaxBandMs = cost;
                bandEstimateMs = System.Math.Max(cost, bandEstimateMs * 0.98); // remember slow bands, decay slowly
                nextRow += TerrainChunk.RowsPerStep;
                if (nextRow > C)
                {
                    ChunkBuffer.Return(inProgress);
                    inProgress = null;
                }
            }
            LastApplyMs = watch.Elapsed.TotalMilliseconds;
            if (LastApplyMs > MaxApplyMs) MaxApplyMs = LastApplyMs;
        }

        bool StartNext()
        {
            while (ready.TryDequeue(out var b))
            {
                long key = ChunkBuffer.Key(b.cx, b.cy);
                if (stale.Remove(key) && Wanted(b.cx, b.cy))
                {
                    // Edited after the worker read it: generate again with the new diff.
                    inbox.Add(b);
                    continue;
                }
                pending.Remove(key);
                if (!Wanted(b.cx, b.cy) || resident.ContainsKey(key)) { ChunkBuffer.Return(b); continue; }
                if (pool.Count > 0) inProgressChunk = pool.Pop();
                else { inProgressChunk = TerrainChunk.Create(transform); inProgressChunk.UseBlocks(this, blockMaterial, SmoothGround); }
                inProgressChunk.Begin(b);
                resident[key] = inProgressChunk;
                inProgress = b;
                nextRow = 0;
                return true;
            }
            return false;
        }

        /// <summary>
        /// True when the chunk holding world tile (x, y) is resident with its collision built (U-027:
        /// bodies there may move; elsewhere they are held so they can't fall through missing ground).
        /// x is unwrapped, as positions are.
        /// </summary>
        public bool IsCollisionReady(int x, int y)
        {
            if (!started) return false;
            long key = ChunkBuffer.Key(WorldNoise.FloorDiv(x, C), WorldNoise.FloorDiv(y, C));
            if (!resident.ContainsKey(key)) return false;
            return inProgress == null || ChunkBuffer.Key(inProgress.cx, inProgress.cy) != key;
        }

        /// <summary>
        /// The highest solid tile in column x, edits and POI stamps included (U-035: spawn and landing
        /// stand on a stamped camp, not on the generated surface underneath). Scans down from 40 m above
        /// the generated surface.
        /// </summary>
        public int TopSolidY(int x)
        {
            int start = Mathf.Min(Config.worldHeight - 1, Generator.SurfaceHeight(WrapX(x)) + 40);
            for (int y = start; y > 0; y--)
                if (TileId.IsSolid(GetTile(x, y))) return y;
            return 0;
        }

        // ---------- edits (U-008) ----------

        public int WrapX(int x)
        {
            int w = Config.worldWidth;
            return ((x % w) + w) % w;
        }

        /// <summary>Current tile at world tile (x, y), edits included. x may be unwrapped.</summary>
        public byte GetTile(int x, int y) =>
            y < 0 || y >= Config.worldHeight ? TileId.Air : Generator.TileAt(WrapX(x), y);

        /// <summary>
        /// Changes one tile, records the diff, and refreshes the tile and its 8 neighbors in the
        /// resident chunks; only the touched chunks rebuild collision. Main thread only.
        /// </summary>
        public bool SetTile(int x, int y, byte id)
        {
            if (!started || y < 0 || y >= Config.worldHeight) return false;
            int wx = WrapX(x);
            byte old = Generator.TileAt(wx, y);
            if (old == id) return false;
            Edits.Set(wx, y, id, BaseGenerator.TileAt(wx, y));
            RefreshAround(x, y);
            TileChanged?.Invoke(x, y, old, id);
            return true;
        }

        void RefreshAround(int x, int y)
        {
            touched.Clear();
            for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++)
            {
                int tx = x + dx, ty = y + dy;
                if (ty < 0 || ty >= Config.worldHeight) continue;
                int cx = WorldNoise.FloorDiv(tx, C), cy = WorldNoise.FloorDiv(ty, C);
                long key = ChunkBuffer.Key(cx, cy);
                if (pending.Contains(key)) stale.Add(key);
                if (!resident.TryGetValue(key, out var chunk)) continue;
                if (chunk == inProgressChunk && inProgress != null)
                {
                    // Half-written from an old buffer: drop it and generate again.
                    resident.Remove(key);
                    chunk.Clear();
                    pool.Push(chunk);
                    ChunkBuffer.Return(inProgress);
                    inProgress = null;
                    pending.Add(key);
                    inbox.Add(ChunkBuffer.Rent(cx, cy));
                    continue;
                }
                byte t = GetTile(tx, ty);
                var tile = t == TileId.Air ? null : tileSet.Get(t, BlobAutotile.Index(MaskAt(tx, ty, t)), WrapX(tx), ty);
                chunk.SetTileLocal(tx - cx * C, ty - cy * C, t, tile);
                if (!touched.Contains(chunk)) touched.Add(chunk);
            }
            if (batching > 0) { foreach (var c in touched) batchTouched.Add(c); return; }
            foreach (var c in touched) c.FinishCollision();
        }

        // U-157: a brush stroke sets several tiles; each touched chunk rebuilds its collision and outline once, at EndBatch.
        int batching;
        readonly HashSet<TerrainChunk> batchTouched = new HashSet<TerrainChunk>();

        /// <summary>U-157: defers the collision / outline rebuilds of the SetTile calls that follow until EndBatch (nestable).</summary>
        public void BeginBatch() => batching++;

        public void EndBatch()
        {
            if (batching <= 0 || --batching > 0) return;
            foreach (var c in batchTouched) if (c != null) c.FinishCollision();
            batchTouched.Clear();
        }

        int MaskAt(int x, int y, byte id)
        {
            bool liquid = TileId.IsLiquid(id);
            int m = 0;
            if (ChunkBuffer.Connects(GetTile(x, y + 1), liquid)) m |= BlobAutotile.N;
            if (ChunkBuffer.Connects(GetTile(x + 1, y + 1), liquid)) m |= BlobAutotile.NE;
            if (ChunkBuffer.Connects(GetTile(x + 1, y), liquid)) m |= BlobAutotile.E;
            if (ChunkBuffer.Connects(GetTile(x + 1, y - 1), liquid)) m |= BlobAutotile.SE;
            if (ChunkBuffer.Connects(GetTile(x, y - 1), liquid)) m |= BlobAutotile.S;
            if (ChunkBuffer.Connects(GetTile(x - 1, y - 1), liquid)) m |= BlobAutotile.SW;
            if (ChunkBuffer.Connects(GetTile(x - 1, y), liquid)) m |= BlobAutotile.W;
            if (ChunkBuffer.Connects(GetTile(x - 1, y + 1), liquid)) m |= BlobAutotile.NW;
            return m;
        }

        /// <summary>The tile currently drawn in the resident chunk at (x, y), for tests; null if not resident.</summary>
        public TileBase RenderedTile(int x, int y)
        {
            int cx = WorldNoise.FloorDiv(x, C), cy = WorldNoise.FloorDiv(y, C);
            if (!resident.TryGetValue(ChunkBuffer.Key(cx, cy), out var chunk)) return null;
            var p = new Vector3Int(x - cx * C, y - cy * C, 0);
            return chunk.solid.GetTile(p) ?? chunk.liquid.GetTile(p);
        }

        /// <summary>True when every resident chunk is within the resident radius of the camera chunk.</summary>
        public bool AllResidentWithinRadius(out int worst)
        {
            worst = 0;
            foreach (var c in resident.Values)
                worst = Mathf.Max(worst, Mathf.Max(Mathf.Abs(c.cx - lastCx), Mathf.Abs(c.cy - lastCy)));
            return worst <= R;
        }

        public void ResetStats() { MaxApplyMs = 0; MaxBandMs = 0; }

        void Stop()
        {
            started = false;
            firstPass = false;
            inbox?.CompleteAdding();
            worker?.Join(1000);
            worker = null;
            inbox?.Dispose();
            inbox = null;
            while (ready.TryDequeue(out var b)) ChunkBuffer.Return(b);
            if (inProgress != null) { ChunkBuffer.Return(inProgress); inProgress = null; }
            pending.Clear();
            foreach (var c in resident.Values) { c.Clear(); pool.Push(c); }
            resident.Clear();
            tileSet?.Dispose();
        }

        void OnDestroy() => Stop();
    }
}
