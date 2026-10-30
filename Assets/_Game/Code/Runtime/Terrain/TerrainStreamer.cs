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
    /// the main thread within 2 ms per frame, only chunks within 2 of the camera resident, others
    /// pooled. The world wraps in x.
    /// </summary>
    public sealed class TerrainStreamer : MonoBehaviour
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
        public bool IsSettled => started && tileSet.IsReady && pending.Count == 0 && ready.IsEmpty && inProgress == null;

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
            BaseGenerator = new SolidWorldGenerator(config, seed);
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
            started = true;
        }

        static IEnumerable<byte> MaterialsFor(PlanetId id) => id == PlanetId.Earth
            ? new[] { TileId.Soil, TileId.Grass, TileId.Stone, TileId.Sand, TileId.Snow, TileId.Water }
            : new[] { TileId.Regolith, TileId.Basalt, TileId.Hematite, TileId.Ice };

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
            while (first || watch.Elapsed.TotalMilliseconds + step < TerrainConstants.ApplyPlanMs)
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
                inProgressChunk = pool.Count > 0 ? pool.Pop() : TerrainChunk.Create(transform);
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
            foreach (var c in touched) c.FinishCollision();
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
