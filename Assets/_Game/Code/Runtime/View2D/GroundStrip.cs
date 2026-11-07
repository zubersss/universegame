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
    /// its top solid tile, plus a flat dirt fill below, just in front of the 3D block faces (which keep collision and
    /// digging). Columns follow digs through TerrainStreamer.TileChanged. One pooled renderer pair per column.
    /// </summary>
    public sealed class GroundStrip : MonoBehaviour
    {
        public const string Key = "terrain/earth/ground_strip";
        public const float Z = -0.01f, StripHeight = 2f, FillDepth = 14f;
        public const int Order = 1;
        static readonly Color Dirt = new Color(0.36f, 0.26f, 0.18f);

        public TerrainStreamer terrain;
        public Camera view;

        public bool Ready => frames != null;
        public int Columns => tops.Count;

        Sprite[] frames;
        Sprite white;
        AsyncOperationHandle<IList<Sprite>> handle;
        readonly List<SpriteRenderer> tops = new List<SpriteRenderer>(64), fills = new List<SpriteRenderer>(64);
        int firstColumn = int.MinValue, lastColumn = int.MinValue;
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
            int n = last - first + 1;
            while (tops.Count < n) { tops.Add(Make("Strip", Order)); fills.Add(Make("Fill", Order - 1)); }
            for (int i = 0; i < tops.Count; i++)
            {
                bool on = i < n;
                tops[i].enabled = on; fills[i].enabled = on;
                if (!on) continue;
                int x = first + i;
                float top = terrain.TopSolidY(x) + 1f; // the ground line
                var t = tops[i];
                t.sprite = frames[((x % frames.Length) + frames.Length) % frames.Length];
                t.transform.position = new Vector3(x + 0.5f, top, Z);
                var f = fills[i];
                f.transform.position = new Vector3(x + 0.5f, top - StripHeight, Z);
                f.size = new Vector2(1f, FillDepth);
            }
        }

        SpriteRenderer Make(string name, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = order;
            if (name == "Fill")
            {
                if (white == null) { var tex = Texture2D.whiteTexture; white = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 1f), tex.width, 0, SpriteMeshType.FullRect); }
                sr.sprite = white; sr.drawMode = SpriteDrawMode.Tiled; sr.color = Dirt;
            }
            return sr;
        }

        void OnDestroy()
        {
            if (terrain != null) terrain.TileChanged -= OnTile;
            if (handle.IsValid()) ArtLoad.Release(handle);
        }
    }
}
