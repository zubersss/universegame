using System;
using System.Collections.Generic;
using UnityEngine;

namespace Meridian.Terrain
{
    /// <summary>
    /// U-073 (Bible 2.0 §10.4): builds one chunk's block mesh from its tile ids: 1 m cubes spanning z −0.5 … +0.5
    /// on the play plane, only faces exposed to air (or liquid) are emitted, and they are greedy-merged:
    /// front faces as rectangles per material, top/bottom/left/right faces as runs along their edge. The back of a
    /// block is never seen and never emitted. A back wall (one quad per vertical run) sits BackWallZ behind the
    /// plane in the open cells that lie at or below the column's original surface (caves, dug holes), so digging
    /// shows rock behind. UVs are world metres / TileMetres (tileable at 2 m); uv.z (third component, in uv0 as a
    /// Vector3) carries the Texture2DArray layer: TopLayer(id) or SideLayer(id), BackWallLayer for the wall.
    /// Pure and allocation-free after warm-up (the caller owns the lists); main thread or worker.
    /// </summary>
    public static class BlockMesher
    {
        public const int C = TerrainConstants.ChunkSize;
        public const float FrontZ = -0.5f, BackZ = 0.5f, BackWallZ = 1.0f, TileMetres = 2f;

        /// <summary>Layer of a material's top face / side face in the per-planet array; the wall layer comes last.</summary>
        public static int TopLayer(byte id) => id * 2;
        public static int SideLayer(byte id) => id * 2 + 1;
        public static int BackWallLayer => TileId.Count * 2;
        public static int LayerCount => TileId.Count * 2 + 1;

        public sealed class Buffers
        {
            public readonly List<Vector3> vertices = new List<Vector3>(4096);
            public readonly List<Vector3> normals = new List<Vector3>(4096);
            public readonly List<Vector3> uv = new List<Vector3>(4096);
            public readonly List<int> triangles = new List<int>(6144);
            internal readonly bool[] used = new bool[C * C];
            public void Clear() { vertices.Clear(); normals.Clear(); uv.Clear(); triangles.Clear(); }
            public int Quads => triangles.Count / 6;
        }

        /// <summary>
        /// Builds the mesh data for a chunk. ids: C×C, row-major (index = y·C + x). outside(lx, ly): the tile just
        /// outside the chunk (lx or ly in −1 or C). wallTop(lx): the highest local y that gets back wall in column
        /// lx (−1 = none; ≥ C−1 = the whole column). ox/oy: the chunk's world origin in tiles (for world UVs).
        /// </summary>
        public static void Build(byte[] ids, Func<int, int, byte> outside, Func<int, int> wallTop, int ox, int oy, Buffers b)
        {
            b.Clear();
            FrontFaces(ids, ox, oy, b);
            for (int y = 0; y < C; y++) EdgeRuns(ids, outside, ox, oy, b, y, horizontal: true, up: true);
            for (int y = 0; y < C; y++) EdgeRuns(ids, outside, ox, oy, b, y, horizontal: true, up: false);
            for (int x = 0; x < C; x++) EdgeRuns(ids, outside, ox, oy, b, x, horizontal: false, up: true);
            for (int x = 0; x < C; x++) EdgeRuns(ids, outside, ox, oy, b, x, horizontal: false, up: false);
            if (wallTop != null) BackWall(ids, wallTop, ox, oy, b);
        }

        static bool Solid(byte id) => TileId.IsSolid(id);

        // Greedy rectangles of front faces, per material.
        static void FrontFaces(byte[] ids, int ox, int oy, Buffers b)
        {
            var used = b.used;
            Array.Clear(used, 0, used.Length);
            for (int y = 0; y < C; y++)
            for (int x = 0; x < C; x++)
            {
                int i = y * C + x;
                byte id = ids[i];
                if (used[i] || !Solid(id)) continue;
                int w = 1;
                while (x + w < C && !used[i + w] && ids[i + w] == id) w++;
                int h = 1;
                while (y + h < C)
                {
                    int r = (y + h) * C + x;
                    bool row = true;
                    for (int k = 0; k < w; k++) if (used[r + k] || ids[r + k] != id) { row = false; break; }
                    if (!row) break;
                    h++;
                }
                for (int yy = 0; yy < h; yy++) for (int k = 0; k < w; k++) used[(y + yy) * C + x + k] = true;
                float layer = SideLayer(id);
                Quad(b, new Vector3(x, y, FrontZ), new Vector3(x + w, y, FrontZ), new Vector3(x + w, y + h, FrontZ), new Vector3(x, y + h, FrontZ),
                     Vector3.back, ox, oy, layer, front: true);
            }
        }

        // One line of cells: emit merged faces on the side that touches air (top/bottom for rows, right/left for columns).
        static void EdgeRuns(byte[] ids, Func<int, int, byte> outside, int ox, int oy, Buffers b, int line, bool horizontal, bool up)
        {
            int start = -1; byte runId = 0;
            for (int k = 0; k <= C; k++)
            {
                bool face = false; byte id = 0;
                if (k < C)
                {
                    int x = horizontal ? k : line, y = horizontal ? line : k;
                    id = ids[y * C + x];
                    if (Solid(id))
                    {
                        int nx = x + (horizontal ? 0 : (up ? 1 : -1)), ny = y + (horizontal ? (up ? 1 : -1) : 0);
                        byte n = nx >= 0 && nx < C && ny >= 0 && ny < C ? ids[ny * C + nx] : (outside != null ? outside(nx, ny) : TileId.Air);
                        face = !Solid(n);
                    }
                }
                if (start >= 0 && (!face || id != runId))
                {
                    EmitEdge(b, line, start, k, horizontal, up, runId, ox, oy);
                    start = -1;
                }
                if (face && start < 0) { start = k; runId = id; }
            }
        }

        static void EmitEdge(Buffers b, int line, int from, int to, bool horizontal, bool up, byte id, int ox, int oy)
        {
            if (horizontal)
            {
                float y = up ? line + 1 : line;
                var n = up ? Vector3.up : Vector3.down;
                var a = new Vector3(from, y, FrontZ); var bb = new Vector3(to, y, FrontZ);
                var c = new Vector3(to, y, BackZ); var d = new Vector3(from, y, BackZ);
                // Top faces wear the material's top layer (grass on soil); bottoms the side layer.
                if (up) Quad(b, a, bb, c, d, n, ox, oy, TopLayer(id), front: false);
                else Quad(b, a, d, c, bb, n, ox, oy, SideLayer(id), front: false);
            }
            else
            {
                float x = up ? line + 1 : line;
                var n = up ? Vector3.right : Vector3.left;
                var a = new Vector3(x, from, FrontZ); var bb = new Vector3(x, to, FrontZ);
                var c = new Vector3(x, to, BackZ); var d = new Vector3(x, from, BackZ);
                if (up) Quad(b, a, d, c, bb, n, ox, oy, SideLayer(id), front: false);
                else Quad(b, a, bb, c, d, n, ox, oy, SideLayer(id), front: false);
            }
        }

        // Back wall: vertical runs of open cells at or below the column's wall top.
        static void BackWall(byte[] ids, Func<int, int> wallTop, int ox, int oy, Buffers b)
        {
            for (int x = 0; x < C; x++)
            {
                int top = Math.Min(C - 1, wallTop(x));
                int start = -1;
                for (int y = 0; y <= top + 1; y++)
                {
                    bool open = y <= top && !Solid(ids[y * C + x]);
                    if (open && start < 0) start = y;
                    if (!open && start >= 0)
                    {
                        Quad(b, new Vector3(x, start, BackWallZ), new Vector3(x + 1, start, BackWallZ), new Vector3(x + 1, y, BackWallZ), new Vector3(x, y, BackWallZ),
                             Vector3.back, ox, oy, BackWallLayer, front: true);
                        start = -1;
                    }
                }
            }
        }

        // Triangles a-c-b and a-d-c: callers order a,b,c,d so that Cross(c − a, b − a) points along n (Unity treats
        // clockwise-from-outside as front-facing); BlockMesherTests checks every triangle against its normal.
        static void Quad(Buffers b, Vector3 a, Vector3 bv, Vector3 c, Vector3 d, Vector3 n, int ox, int oy, float layer, bool front)
        {
            int i = b.vertices.Count;
            b.vertices.Add(a); b.vertices.Add(bv); b.vertices.Add(c); b.vertices.Add(d);
            b.normals.Add(n); b.normals.Add(n); b.normals.Add(n); b.normals.Add(n);
            b.uv.Add(Uv(a, n, ox, oy, layer)); b.uv.Add(Uv(bv, n, ox, oy, layer)); b.uv.Add(Uv(c, n, ox, oy, layer)); b.uv.Add(Uv(d, n, ox, oy, layer));
            b.triangles.Add(i); b.triangles.Add(i + 2); b.triangles.Add(i + 1);
            b.triangles.Add(i); b.triangles.Add(i + 3); b.triangles.Add(i + 2);
        }

        // World-space planar UVs: fronts and walls use x/y, tops/bottoms x/z, sides z/y.
        static Vector3 Uv(Vector3 p, Vector3 n, int ox, int oy, float layer)
        {
            float wx = ox + p.x, wy = oy + p.y, wz = p.z - FrontZ;
            if (n.y != 0f) return new Vector3(wx / TileMetres, wz / TileMetres, layer);
            if (n.x != 0f) return new Vector3(wz / TileMetres, wy / TileMetres, layer);
            return new Vector3(wx / TileMetres, wy / TileMetres, layer);
        }
    }
}
