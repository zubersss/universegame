using System.Collections.Generic;
using System.IO;

namespace Meridian.Terrain
{
    /// <summary>
    /// Player changes to one planet's terrain, stored as (chunk, index, tileId) diffs against the
    /// seeded generator (Bible §10.4). Thread-safe: the terrain worker reads while gameplay writes.
    /// Saved as terrain_&lt;planet&gt;.bin (Bible §10.7).
    /// </summary>
    public sealed class TerrainEdits
    {
        const uint Magic = 0x3144544D; // "MTD1"
        /// <summary>2 (U-157 / P-54): a fill level per brushed tile follows the diffs; a v1 file has none (whole tiles).</summary>
        public const int Version = 2;
        const int C = TerrainConstants.ChunkSize;

        readonly Dictionary<long, Dictionary<int, byte>> chunks = new Dictionary<long, Dictionary<int, byte>>();
        // U-157 (P-54, D-167 (4)): the drawn ground's density (0-255) at a brushed tile's centre, so scoops and mounds trace round at any size.
        readonly Dictionary<long, Dictionary<int, byte>> levels = new Dictionary<long, Dictionary<int, byte>>();
        readonly object gate = new object();

        /// <summary>Number of edited tiles.</summary>
        public int Count
        {
            get
            {
                lock (gate)
                {
                    int n = 0;
                    foreach (var c in chunks.Values) n += c.Count;
                    return n;
                }
            }
        }

        public int ChunkCount { get { lock (gate) return chunks.Count; } }

        static void Locate(int x, int y, out long key, out int index)
        {
            int cx = WorldNoise.FloorDiv(x, C), cy = WorldNoise.FloorDiv(y, C);
            key = ChunkBuffer.Key(cx, cy);
            index = (y - cy * C) * C + (x - cx * C);
        }

        /// <summary>x must be wrapped into [0, width).</summary>
        public bool TryGet(int x, int y, out byte id)
        {
            Locate(x, y, out long key, out int index);
            lock (gate)
            {
                id = 0;
                return chunks.TryGetValue(key, out var c) && c.TryGetValue(index, out id);
            }
        }

        /// <summary>Records a change; a tile set back to its generated value drops its diff.</summary>
        public void Set(int x, int y, byte id, byte generated)
        {
            Locate(x, y, out long key, out int index);
            lock (gate)
            {
                if (!chunks.TryGetValue(key, out var c))
                {
                    if (id == generated) return;
                    chunks[key] = c = new Dictionary<int, byte>();
                }
                if (id == generated) { c.Remove(index); if (c.Count == 0) chunks.Remove(key); }
                else c[index] = id;
            }
        }

        public void Clear() { lock (gate) { chunks.Clear(); levels.Clear(); } }

        /// <summary>U-157 (P-54): a brushed tile's fill level (its node density × 255), x wrapped.</summary>
        public bool TryGetLevel(int x, int y, out byte level)
        {
            Locate(x, y, out long key, out int index);
            lock (gate)
            {
                level = 0;
                return levels.TryGetValue(key, out var c) && c.TryGetValue(index, out level);
            }
        }

        /// <summary>U-157 (P-54): records a brushed tile's fill level (x wrapped).</summary>
        public void SetLevel(int x, int y, byte level)
        {
            Locate(x, y, out long key, out int index);
            lock (gate)
            {
                if (!levels.TryGetValue(key, out var c)) levels[key] = c = new Dictionary<int, byte>();
                c[index] = level;
            }
        }

        /// <summary>U-157: any fill levels in the chunk (cx, cy)? (The tracer skips the lookups when none.)</summary>
        public bool HasLevels(int cx, int cy) { lock (gate) return levels.ContainsKey(ChunkBuffer.Key(cx, cy)); }

        public int LevelCount { get { lock (gate) { int n = 0; foreach (var c in levels.Values) n += c.Count; return n; } } }

        /// <summary>U-157: every edited tile (x as stored, wrapped; y; id): a snapshot, so the edits may change while it is walked.</summary>
        public List<(int x, int y, byte id)> Cells()
        {
            var list = new List<(int x, int y, byte id)>();
            lock (gate)
                foreach (var kv in chunks)
                {
                    int cx = (int)(kv.Key >> 32), cy = (int)(uint)kv.Key;
                    foreach (var e in kv.Value) list.Add((cx * C + e.Key % C, cy * C + e.Key / C, e.Value));
                }
            return list;
        }

        /// <summary>U-157: drops a tile's diff (x wrapped): the generator's value stands there again.</summary>
        public void Remove(int x, int y)
        {
            Locate(x, y, out long key, out int index);
            lock (gate)
                if (chunks.TryGetValue(key, out var c)) { c.Remove(index); if (c.Count == 0) chunks.Remove(key); }
        }

        public void Write(BinaryWriter w)
        {
            lock (gate)
            {
                w.Write(Magic);
                w.Write(Version);
                w.Write(chunks.Count);
                foreach (var kv in chunks)
                {
                    w.Write(kv.Key);
                    w.Write(kv.Value.Count);
                    foreach (var t in kv.Value) { w.Write((ushort)t.Key); w.Write(t.Value); }
                }
                // v2: the fill levels.
                w.Write(levels.Count);
                foreach (var kv in levels)
                {
                    w.Write(kv.Key);
                    w.Write(kv.Value.Count);
                    foreach (var t in kv.Value) { w.Write((ushort)t.Key); w.Write(t.Value); }
                }
            }
        }

        public void Read(BinaryReader r)
        {
            if (r.ReadUInt32() != Magic) throw new InvalidDataException("not a MERIDIAN terrain diff file");
            int version = r.ReadInt32();
            if (version > Version) throw new InvalidDataException($"terrain diff version {version} is newer than {Version}");
            lock (gate)
            {
                chunks.Clear();
                int n = r.ReadInt32();
                for (int i = 0; i < n; i++)
                {
                    long key = r.ReadInt64();
                    int count = r.ReadInt32();
                    var c = new Dictionary<int, byte>(count);
                    for (int j = 0; j < count; j++) c[r.ReadUInt16()] = r.ReadByte();
                    chunks[key] = c;
                }
                levels.Clear();
                if (version < 2) return; // a v1 file (0.4.8): whole tiles, no levels
                int m = r.ReadInt32();
                for (int i = 0; i < m; i++)
                {
                    long key = r.ReadInt64();
                    int count = r.ReadInt32();
                    var c = new Dictionary<int, byte>(count);
                    for (int j = 0; j < count; j++) c[r.ReadUInt16()] = r.ReadByte();
                    levels[key] = c;
                }
            }
        }

        public void SaveFile(string path)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var tmp = path + ".tmp";
            using (var w = new BinaryWriter(File.Create(tmp))) Write(w);
            if (File.Exists(path)) File.Delete(path);
            File.Move(tmp, path);
        }

        public void LoadFile(string path)
        {
            using (var r = new BinaryReader(File.OpenRead(path))) Read(r);
        }
    }

    /// <summary>The seeded world with the player's edits on top. Thread-safe.</summary>
    public sealed class EditedWorld : IWorldGenerator
    {
        public readonly IWorldGenerator Base;
        public readonly TerrainEdits Edits;

        public EditedWorld(IWorldGenerator baseGenerator, TerrainEdits edits)
        {
            Base = baseGenerator;
            Edits = edits;
        }

        public int Width => Base.Width;
        public int Height => Base.Height;
        public int SurfaceHeight(int x) => Base.SurfaceHeight(x);

        public byte TileAt(int x, int y) =>
            y >= 0 && y < Base.Height && Edits.TryGet(x, y, out var id) ? id : Base.TileAt(x, y);
    }
}
