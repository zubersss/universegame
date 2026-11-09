using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rendering;
using Meridian.Mining;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.View2D
{
    /// <summary>
    /// U-174 (D-174, Bible 5.2 §8.1; B-203 / B-206 art): the Surface Line in the cutaway: terrain/&lt;planet&gt;/surface_line (one 4 m tile,
    /// its pivot on the line's row, u locked to world x every 4 m) laid along the line 2 m under the drawn surface, each tile on the line at
    /// its left end and turned to the line's chord over its 4 m; drawn only while the camera is below the surface (the pennants point
    /// topside). A pool of tiles across the view, placed in LateUpdate; no allocation per frame.
    /// </summary>
    public sealed class SurfaceLineView : MonoBehaviour
    {
        /// <summary>Over the ground's fill and band, under the nodes, props and the surveyor.</summary>
        public const int Order = SmoothGround.Order + 1;
        public const float TileWidth = 4f;
        const int Pool = 20;

        TerrainStreamer terrain;
        Camera view;
        string key;
        Sprite tile;
        AsyncOperationHandle<IList<Sprite>> handle;
        readonly List<SpriteRenderer> tiles = new List<SpriteRenderer>(Pool);
        Material material;

        /// <summary>True while the line draws (the camera below the surface; tests and captures read it).</summary>
        public bool Showing { get; private set; }
        /// <summary>Tiles placed on the last frame.</summary>
        public int Placed { get; private set; }

        public void Configure(Meridian.Planets.PlanetId planet, TerrainStreamer t, Camera cam)
        {
            terrain = t; view = cam;
            string want = $"terrain/{planet.ToString().ToLowerInvariant()}/surface_line";
            if (want == key) return;
            Release();
            key = want;
            var loc = UnityEngine.AddressableAssets.Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (!exists || this == null || key != want) return;
                handle = ArtLoad.Asset<IList<Sprite>>(want);
                handle.Completed += op => { if (this != null && key == want && op.Status == AsyncOperationStatus.Succeeded && op.Result != null && op.Result.Count > 0) { tile = op.Result[0]; material = ArtMaterials.MaterialFor(want); } };
            };
        }

        void Release()
        {
            if (handle.IsValid()) ArtLoad.Release(handle);
            handle = default;
            tile = null;
            foreach (var r in tiles) if (r != null) { r.sprite = null; r.enabled = false; }
        }

        void OnDestroy() => Release();

        void LateUpdate()
        {
            Placed = 0;
            bool show = tile != null && terrain != null && view != null && terrain.SmoothGround && terrain.Config != null
                        && view.transform.position.y < terrain.SurfaceAt(view.transform.position.x);
            Showing = show;
            if (!show) { for (int i = 0; i < tiles.Count; i++) if (tiles[i].enabled) tiles[i].enabled = false; return; }
            float half = Meridian.CameraRig.SideView.HalfHeight(view) * Mathf.Max(1f, view.aspect);
            float cx = view.transform.position.x;
            float x0 = Mathf.Floor((cx - half - TileWidth) / TileWidth) * TileWidth;
            for (float x = x0; x < cx + half + TileWidth && Placed < Pool; x += TileWidth)
            {
                var r = Get(Placed++);
                float y0 = DigRun.LineAt(terrain, x), y1 = DigRun.LineAt(terrain, x + TileWidth);
                r.transform.SetPositionAndRotation(new Vector3(x, y0, 0f), Quaternion.Euler(0f, 0f, Mathf.Atan2(y1 - y0, TileWidth) * Mathf.Rad2Deg));
                if (r.sprite != tile) { r.sprite = tile; if (material != null) r.sharedMaterial = material; }
                if (!r.enabled) r.enabled = true;
            }
            for (int i = Placed; i < tiles.Count; i++) if (tiles[i].enabled) tiles[i].enabled = false;
        }

        SpriteRenderer Get(int i)
        {
            while (tiles.Count <= i)
            {
                var go = new GameObject("SurfaceLine" + tiles.Count);
                go.transform.SetParent(transform, false);
                var r = go.AddComponent<SpriteRenderer>();
                r.sortingOrder = Order;
                r.enabled = false;
                tiles.Add(r);
            }
            return tiles[i];
        }
    }
}
