using System.Collections.Generic;
using Meridian.Art;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.View2D
{
    /// <summary>
    /// U-156 (D-161 / D-162, Bible 5.0; contract v3.2 §11.9, D-163): draws a smooth planet's ground from each chunk's traced outline: one mesh
    /// per chunk with four submeshes, back to front: the back wall (the natural ground under its surface curve, shaded, so a dug hole shows the
    /// cross-section behind it, never the sky), the body (the outline's fill), the band (B-175's ground_band along every upward-facing stretch
    /// of the outline, bent by its normal: 24 px out, 40 px in, u by world x so chunks join) and the rim (B-175's dig_rim along walls and
    /// ceilings). Until B-175 lands the band is the grass strip's frames, the body the strip's fill colour and the rim a 0.09 m ink line.
    /// Built when a chunk's outline is (TerrainChunk.OutlineBuilt) and again when the art arrives; never per frame.
    /// </summary>
    public sealed class SmoothGround : MonoBehaviour
    {
        /// <summary>A stretch of outline carries the band where its outward normal is within 60° of up (a 35° slope's is 0.82).</summary>
        public const float SurfaceFacing = 0.5f;
        public const float RimWidth = 0.09f, BackShade = 0.55f, Z = GroundStrip.Z;
        public const int Order = GroundStrip.Order;
        static readonly Color Ink = new Color(0.12f, 0.10f, 0.09f, 1f);

        public TerrainStreamer terrain;
        public GroundStrip strips;
        public bool Active { get; private set; }
        /// <summary>Chunks built and the band quads laid on the last build (tests, captures).</summary>
        public int ChunksBuilt { get; private set; }
        public int LastBandQuads { get; private set; }
        /// <summary>True once B-175's band / fill / rim are in (else the placeholders draw).</summary>
        public bool BandArt => band != null;
        public bool FillArt => fill != null;

        string planet;
        Sprite band, fill, rim;
        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>(3);
        readonly Dictionary<TerrainChunk, MeshFilter> meshes = new Dictionary<TerrainChunk, MeshFilter>(64);
        readonly Dictionary<Texture, Material> materials = new Dictionary<Texture, Material>(4);
        int stripsSeen = -1;

        // Mesh scratch (main thread).
        readonly List<Vector3> v = new List<Vector3>(4096);
        readonly List<Vector2> uv = new List<Vector2>(4096);
        readonly List<Color> col = new List<Color>(4096);
        readonly List<int> tBack = new List<int>(1024), tFill = new List<int>(4096), tBand = new List<int>(2048), tRim = new List<int>(2048);
        readonly List<Vector2> nrm = new List<Vector2>(256);
        readonly Material[] mats = new Material[4];

        public void Configure(Meridian.Planets.PlanetId id, TerrainStreamer t, GroundStrip g)
        {
            Release();
            terrain = t; strips = g; planet = id.ToString().ToLowerInvariant();
            Active = true;
            TerrainChunk.OutlineBuilt -= OnOutline;
            TerrainChunk.OutlineBuilt += OnOutline;
            Probe($"terrain/{planet}/ground_band", s => { band = s; RebuildAll(); });
            Probe($"terrain/{planet}/ground_fill", s => { fill = s; if (fill.texture != null) fill.texture.wrapMode = TextureWrapMode.Repeat; RebuildAll(); });
            Probe($"terrain/{planet}/dig_rim", s => { rim = s; RebuildAll(); });
            RebuildAll();
        }

        public void Deactivate()
        {
            Active = false;
            TerrainChunk.OutlineBuilt -= OnOutline;
            foreach (var kv in meshes) if (kv.Value != null) kv.Value.gameObject.SetActive(false);
            Release();
        }

        void OnDestroy() { TerrainChunk.OutlineBuilt -= OnOutline; Release(); }

        void Release()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
            band = fill = rim = null;
        }

        /// <summary>A key not exported yet is probed quietly (D-143) and its placeholder stays.</summary>
        void Probe(string key, System.Action<Sprite> got)
        {
            var loc = Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (!exists || this == null || !Active) return;
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                handles.Add(h);
                h.Completed += op => { if (this != null && Active && op.Status == AsyncOperationStatus.Succeeded && op.Result != null && op.Result.Count > 0) got(op.Result[0]); };
            };
        }

        void LateUpdate()
        {
            // The placeholder band comes from the ground strip's frames: rebuild once they are in.
            if (!Active || strips == null) return;
            int seen = strips.MaterialsLoaded;
            if (seen != stripsSeen) { stripsSeen = seen; RebuildAll(); }
        }

        void RebuildAll()
        {
            if (!Active || terrain == null) return;
            foreach (Transform child in terrain.transform)
            {
                var c = child.GetComponent<TerrainChunk>();
                if (c != null && c.smooth) Build(c);
            }
        }

        void OnOutline(TerrainChunk c)
        {
            if (!Active || terrain == null || c == null || c.transform.parent != terrain.transform) return;
            Build(c);
        }

        Material MaterialFor(Texture tex)
        {
            if (tex == null) tex = Texture2D.whiteTexture;
            if (materials.TryGetValue(tex, out var m) && m != null) return m;
            var lit = Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.lit : null;
            m = lit != null ? new Material(lit) : new Material(Shader.Find("Sprites/Default"));
            m.name = "SmoothGround_" + tex.name;
            m.mainTexture = tex;
            materials[tex] = m;
            return m;
        }

        /// <summary>The band's sprites, left to right, and each one's width in metres: B-175's one 8 m sheet, or the grass strip's eight 1 m frames.</summary>
        Sprite[] bandSprites = new Sprite[1];
        int BandSprites(out float width)
        {
            width = 0f;
            if (band != null) { bandSprites[0] = band; width = band.bounds.size.x; return 1; }
            var frames = strips != null ? strips.FramesOf(0) : null;
            if (frames == null || frames.Length == 0) return 0;
            int n = Mathf.Min(GroundStrip.TileFrames, frames.Length);
            if (bandSprites.Length < n) bandSprites = new Sprite[n];
            for (int i = 0; i < n; i++) bandSprites[i] = frames[i];
            width = frames[0].bounds.size.x;
            return n;
        }

        MeshFilter FilterFor(TerrainChunk c)
        {
            if (meshes.TryGetValue(c, out var f) && f != null) { if (!f.gameObject.activeSelf) f.gameObject.SetActive(true); return f; }
            var go = new GameObject("SmoothGround");
            go.transform.SetParent(c.transform, false);
            go.transform.localPosition = new Vector3(0f, 0f, Z);
            f = go.AddComponent<MeshFilter>();
            f.sharedMesh = new Mesh { name = "SmoothGround" };
            f.sharedMesh.MarkDynamic();
            var r = go.AddComponent<MeshRenderer>();
            r.sortingOrder = Order;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
            meshes[c] = f;
            return f;
        }

        void Build(TerrainChunk c)
        {
            var f = FilterFor(c);
            var mesh = f.sharedMesh;
            var k = c.Contour;
            const int C = TerrainConstants.ChunkSize;
            float wx0 = c.cx * C, wy0 = c.cy * C;
            v.Clear(); uv.Clear(); col.Clear(); tBack.Clear(); tFill.Clear(); tBand.Clear(); tRim.Clear();

            // The body's sampling: B-175's fill in world space, or the strip's fill tile's colour.
            Sprite fillSprite = fill != null ? fill : strips != null ? strips.FillOf(0) : null;
            Vector2 fillUv = fillSprite != null ? Centre(fillSprite) : new Vector2(0.5f, 0.5f);
            Color fillTint = fillSprite != null ? Color.white : new Color(0.45f, 0.36f, 0.27f, 1f);
            bool worldFill = fill != null && fill.texture != null && fill.rect.width >= fill.texture.width - 0.5f;
            Vector2 FillUv(float lx, float ly) => worldFill ? new Vector2((wx0 + lx) / 8f, (wy0 + ly) / 8f) : fillUv;

            // 1. The back wall: under the natural surface curve, from the chunk's foot, shaded.
            if (k.Lines > 0 || k.fillVerts.Count > 0)
            {
                float yb = -0.5f, yt = C - 0.5f;
                var back = new Color(fillTint.r * BackShade, fillTint.g * BackShade, fillTint.b * BackShade, 1f);
                for (int i = 0; i < C; i++)
                {
                    float h0 = c.SurfaceCurve[i] - wy0, h1 = c.SurfaceCurve[i + 1] - wy0;
                    if (float.IsNaN(h0) || float.IsNaN(h1)) continue;
                    h0 = Mathf.Min(h0, yt); h1 = Mathf.Min(h1, yt);
                    if (h0 <= yb && h1 <= yb) continue;
                    float x0 = i - 0.5f, x1 = i + 0.5f;
                    int b = v.Count;
                    Add(new Vector3(x0, yb, 0.01f), FillUv(x0, yb), back); Add(new Vector3(x1, yb, 0.01f), FillUv(x1, yb), back);
                    Add(new Vector3(x1, Mathf.Max(h1, yb), 0.01f), FillUv(x1, h1), back); Add(new Vector3(x0, Mathf.Max(h0, yb), 0.01f), FillUv(x0, h0), back);
                    tBack.Add(b); tBack.Add(b + 2); tBack.Add(b + 1); tBack.Add(b); tBack.Add(b + 3); tBack.Add(b + 2);
                }
            }

            // 2. The body.
            int fb = v.Count;
            for (int i = 0; i < k.fillVerts.Count; i++) { var p = k.fillVerts[i]; Add(p, FillUv(p.x, p.y), fillTint); }
            for (int i = 0; i < k.fillTris.Count; i++) tFill.Add(fb + k.fillTris[i]);

            // 3 / 4. The band along upward-facing stretches, the rim along the rest.
            int bandCount = BandSprites(out float bandW);
            int quads = 0;
            for (int line = 0; line < k.Lines; line++)
            {
                int s = k.lineStart[line], n = k.lineCount[line];
                bool closed = k.lineClosed[line];
                if (n < 2) continue;
                Normals(k.points, s, n, closed);
                float arc = 0f;
                int segs = closed ? n : n - 1;
                for (int a = 0; a < segs; a++)
                {
                    int ia = s + a, ib = s + (a + 1) % n;
                    Vector2 p = k.points[ia], q = k.points[ib];
                    Vector2 np = nrm[a], nq = nrm[(a + 1) % n];
                    var segN = Normal(q - p);
                    float len = (q - p).magnitude;
                    if (segN.y > SurfaceFacing && bandCount > 0) quads += Band(p, q, np, nq, wx0, bandCount, bandW);
                    else Rim(p, q, np, nq, arc);
                    arc += len;
                }
            }
            LastBandQuads = quads;

            mesh.Clear();
            mesh.SetVertices(v);
            mesh.SetUVs(0, uv);
            mesh.SetColors(col);
            mesh.subMeshCount = 4;
            mesh.SetTriangles(tBack, 0, false);
            mesh.SetTriangles(tFill, 1, false);
            mesh.SetTriangles(tBand, 2, false);
            mesh.SetTriangles(tRim, 3, false);
            mesh.bounds = new Bounds(new Vector3(C * 0.5f - 0.5f, C * 0.5f - 0.5f, 0f), new Vector3(C + 2f, C + 2f, 1f));
            mats[0] = MaterialFor(fillSprite != null ? fillSprite.texture : null);
            mats[1] = mats[0];
            mats[2] = MaterialFor(bandCount > 0 ? bandSprites[0].texture : null);
            mats[3] = MaterialFor(rim != null ? rim.texture : null);
            f.GetComponent<MeshRenderer>().sharedMaterials = mats;
            ChunksBuilt++;
        }

        void Add(Vector3 p, Vector2 t, Color c) { v.Add(p); uv.Add(t); col.Add(c); }

        static Vector2 Normal(Vector2 d) { var n = new Vector2(-d.y, d.x); float m = n.magnitude; return m > 1e-6f ? n / m : Vector2.up; } // the air side: left of the walk

        /// <summary>Per point: the mean of its two segments' outward normals (a chain's ends take their one segment's).</summary>
        void Normals(List<Vector2> pts, int s, int n, bool closed)
        {
            nrm.Clear();
            for (int i = 0; i < n; i++)
            {
                bool hasPrev = closed || i > 0, hasNext = closed || i < n - 1;
                Vector2 sum = Vector2.zero;
                if (hasPrev) sum += Normal(pts[s + i] - pts[s + (i - 1 + n) % n]);
                if (hasNext) sum += Normal(pts[s + (i + 1) % n] - pts[s + i]);
                float m = sum.magnitude;
                nrm.Add(m > 1e-6f ? sum / m : Vector2.up);
            }
        }

        static Vector2 Centre(Sprite sp)
        {
            var r = sp.textureRect; var t = sp.texture;
            return t != null ? new Vector2(r.center.x / t.width, r.center.y / t.height) : new Vector2(0.5f, 0.5f);
        }

        /// <summary>One stretch of band from p to q (chunk-local), split where the band's sprites change (every `w` metres of world x): each
        /// piece a quad from its outline points out along the normal by the sprite's rows above its pivot and in by those below. Returns quads.</summary>
        int Band(Vector2 p, Vector2 q, Vector2 np, Vector2 nq, float wx0, int count, float w)
        {
            int quads = 0;
            float xa = wx0 + p.x, xb = wx0 + q.x;
            bool forward = xb >= xa;
            float t0 = 0f;
            while (t0 < 1f - 1e-5f)
            {
                float x = Mathf.Lerp(xa, xb, t0);
                // The next sprite boundary along x in the walk's direction.
                float cell = Mathf.Floor(x / w + (forward ? 1e-4f : -1e-4f));
                float boundary = forward ? (cell + 1f) * w : cell * w;
                float t1 = Mathf.Abs(xb - xa) < 1e-6f ? 1f : Mathf.Clamp01((boundary - xa) / (xb - xa));
                if (t1 <= t0 + 1e-6f) t1 = 1f;
                int idx = (((int)cell) % count + count) % count;
                var sp = bandSprites[idx];
                var r = sp.textureRect; var tex = sp.texture;
                float above = (r.height - sp.pivot.y) / sp.pixelsPerUnit, below = sp.pivot.y / sp.pixelsPerUnit;
                Vector2 a = Vector2.Lerp(p, q, t0), b = Vector2.Lerp(p, q, t1);
                Vector2 na = Vector2.Lerp(np, nq, t0).normalized, nb = Vector2.Lerp(np, nq, t1).normalized;
                float ua = (Mathf.Lerp(xa, xb, t0) / w - cell), ub = (Mathf.Lerp(xa, xb, t1) / w - cell);
                float u0 = (r.xMin + Mathf.Clamp01(ua) * r.width) / tex.width, u1 = (r.xMin + Mathf.Clamp01(ub) * r.width) / tex.width;
                float vTop = r.yMax / tex.height, vBot = r.yMin / tex.height;
                int i0 = v.Count;
                Add(a + na * above, new Vector2(u0, vTop), Color.white);
                Add(b + nb * above, new Vector2(u1, vTop), Color.white);
                Add(b - nb * below, new Vector2(u1, vBot), Color.white);
                Add(a - na * below, new Vector2(u0, vBot), Color.white);
                tBand.Add(i0); tBand.Add(i0 + 1); tBand.Add(i0 + 2); tBand.Add(i0); tBand.Add(i0 + 2); tBand.Add(i0 + 3);
                quads++;
                t0 = t1;
            }
            return quads;
        }

        /// <summary>One stretch of rim: B-175's dig_rim (its pivot on the ink row) along the arc, or a 0.09 m ink line centred on the outline.</summary>
        void Rim(Vector2 p, Vector2 q, Vector2 np, Vector2 nq, float arc)
        {
            float above = RimWidth * 0.5f, below = RimWidth * 0.5f;
            Vector2 uvA = new Vector2(0.5f, 0.5f), uvB = uvA, uvC = uvA, uvD = uvA;
            Color tint = Ink;
            if (rim != null && rim.texture != null)
            {
                var r = rim.textureRect; var tex = rim.texture;
                above = (r.height - rim.pivot.y) / rim.pixelsPerUnit; below = rim.pivot.y / rim.pixelsPerUnit;
                float w = rim.bounds.size.x, len = (q - p).magnitude;
                float ua = Mathf.Repeat(arc / w, 1f), ub = ua + len / w;
                if (ub > 1f) ub = 1f; // a stretch longer than the sheet's remainder clamps (stretches are ≤ ¼ m)
                float u0 = (r.xMin + ua * r.width) / tex.width, u1 = (r.xMin + ub * r.width) / tex.width;
                float vt = r.yMax / tex.height, vb = r.yMin / tex.height;
                uvA = new Vector2(u0, vt); uvB = new Vector2(u1, vt); uvC = new Vector2(u1, vb); uvD = new Vector2(u0, vb);
                tint = Color.white;
            }
            int i0 = v.Count;
            Add(p + np * above, uvA, tint); Add(q + nq * above, uvB, tint); Add(q - nq * below, uvC, tint); Add(p - np * below, uvD, tint);
            tRim.Add(i0); tRim.Add(i0 + 1); tRim.Add(i0 + 2); tRim.Add(i0); tRim.Add(i0 + 2); tRim.Add(i0 + 3);
        }
    }
}
