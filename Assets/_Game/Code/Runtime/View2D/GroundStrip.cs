using System.Collections.Generic;
using Meridian.Art;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.View2D
{
    /// <summary>
    /// U-100: the cartoon ground placeholder. While the v4 path is on, every visible terrain column gets a 1 m slice of the
    /// `terrain/earth/ground_strip` sheet (8 frames of 64×128 px: ink top line, one-tone grass lip, flat dirt) hung from
    /// its top solid tile, a flat dirt fill (a tile cut from the same sheet) down to the frame bottom, and an ink edge
    /// where neighbouring columns differ in height (dug walls). Drawn just in front of the 3D block faces, which keep
    /// collision and digging; columns follow digs through TerrainStreamer.TileChanged. Pooled renderers, no allocation per frame.
    /// </summary>
    public sealed class GroundStrip : MonoBehaviour
    {
        public const string Key = "terrain/earth/ground_strip";
        public const float Z = -0.01f, StripHeight = 2f, FillDepth = 20f, EdgeWidth = 0.09f;
        public const int Order = 1;
        static readonly Color Ink = new Color(0.33f, 0.39f, 0.5f); // × the dirt tone ≈ #1E1A17
        static readonly Color Back = new Color(0.62f, 0.62f, 0.66f); // a dug hole's back wall: the dirt tone, shaded

        public TerrainStreamer terrain;
        public Camera view;

        public bool Ready => frames != null;
        public int Columns => count;

        Sprite[] frames;
        Sprite dirt;
        AsyncOperationHandle<IList<Sprite>> handle;
        readonly List<SpriteRenderer> tops = new List<SpriteRenderer>(64), fills = new List<SpriteRenderer>(64), edges = new List<SpriteRenderer>(64), backs = new List<SpriteRenderer>(64);
        int firstColumn = int.MinValue, lastColumn = int.MinValue, count;
        bool dirty = true;

        void OnEnable() { if (terrain != null) terrain.TileChanged += OnTile; }
        void OnDisable() { if (terrain != null) terrain.TileChanged -= OnTile; }

        public void Load()
        {
            if (terrain != null) { terrain.TileChanged -= OnTile; terrain.TileChanged += OnTile; }
            handle = ArtLoad.Asset<IList<Sprite>>(Key);
            handle.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                frames = new Sprite[op.Result.Count];
                op.Result.CopyTo(frames, 0);
                // A flat dirt tile: the bottom 8 px of the first slice (1 m × 1/8 m), tiled for the fills and the edges.
                var r = frames[0].rect;
                dirt = Sprite.Create(frames[0].texture, new Rect(r.x, r.y, r.width, 8f), new Vector2(0.5f, 1f), frames[0].pixelsPerUnit, 0, SpriteMeshType.FullRect);
                dirty = true;
            };
        }

        void OnTile(int x, int y, byte old, byte now) { if (x >= firstColumn - 1 && x <= lastColumn + 1) dirty = true; }

        void LateUpdate()
        {
            if (view == null || terrain == null || frames == null) return;
            float half = view.orthographicSize * view.aspect + 2f;
            int first = Mathf.FloorToInt(view.transform.position.x - half), last = Mathf.CeilToInt(view.transform.position.x + half);
            if (!dirty && first == firstColumn && last == lastColumn) return;
            firstColumn = first; lastColumn = last; dirty = false;
            count = last - first + 1;
            while (tops.Count < count) { tops.Add(Make("Strip", Order, null)); fills.Add(Make("Fill", Order - 1, dirt)); edges.Add(Make("Edge", Order + 1, dirt)); backs.Add(Make("Back", Order - 2, dirt)); }
            float prevTop = terrain.TopSolidY(first - 1) + 1f;
            for (int i = 0; i < tops.Count; i++)
            {
                bool on = i < count;
                tops[i].enabled = on; fills[i].enabled = on;
                if (!on) { edges[i].enabled = false; backs[i].enabled = false; continue; }
                int x = first + i;
                float top = terrain.TopSolidY(x) + 1f; // the ground line
                var t = tops[i];
                t.sprite = frames[((x % frames.Length) + frames.Length) % frames.Length];
                t.transform.position = new Vector3(x + 0.5f, top, Z);
                var f = fills[i];
                f.transform.position = new Vector3(x + 0.5f, top - StripHeight, Z);
                f.size = new Vector2(1f, FillDepth);
                // A step between this column and the one before: an ink edge down the wall.
                float step = Mathf.Abs(top - prevTop);
                var e = edges[i];
                e.enabled = step > 0.01f;
                if (e.enabled) { e.transform.position = new Vector3(x, Mathf.Max(top, prevTop), Z - 0.001f); e.size = new Vector2(EdgeWidth, step); }
                // A dug column (lower than both neighbours' lowest): a shaded back wall up to that line, so no block face shows in the hole.
                float rim = Mathf.Min(prevTop, terrain.TopSolidY(x + 1) + 1f);
                var bk = backs[i];
                bk.enabled = rim > top + 0.01f;
                if (bk.enabled) { bk.transform.position = new Vector3(x + 0.5f, rim, Z + 0.001f); bk.size = new Vector2(1f, rim - top); }
                prevTop = top;
            }
        }

        SpriteRenderer Make(string name, int order, Sprite tile)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = order;
            if (tile != null) { sr.sprite = tile; sr.drawMode = SpriteDrawMode.Tiled; sr.tileMode = SpriteTileMode.Continuous; }
            if (name == "Edge") sr.color = Ink;
            else if (name == "Back") sr.color = Back;
            return sr;
        }

        void OnDestroy()
        {
            if (terrain != null) terrain.TileChanged -= OnTile;
            if (handle.IsValid()) ArtLoad.Release(handle);
        }
    }
}
