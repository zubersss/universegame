using System.Diagnostics;
using Meridian.Rendering;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Meridian.Core
{
    /// <summary>
    /// Shader/pipeline warm-up (U-028, P-17). Renders a camera once into an off-screen target with a
    /// temporary rig in view: one of each sprite material (lit, lit-emissive) and a tilemap holding a
    /// tile of every loaded terrain material. Everything the view will draw gets its shaders and
    /// pipeline state built here, behind a cover, instead of on the first visible frame.
    /// </summary>
    public static class RenderWarmup
    {
        public static float LastMs { get; private set; }

        /// <summary>
        /// Size of the off-screen warm-up target. URP 2D allocates its light textures per target size,
        /// so warming at a different size than the game renders leaves that allocation for the first
        /// visible frame. Default (0,0) = the current screen size; tools that render at a fixed size set it.
        /// </summary>
        public static Vector2Int TargetSize;

        static Sprite white;

        public static float WarmUp(Camera cam, TerrainTileSet tiles = null)
        {
            if (cam == null || SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null) return 0f;
            var watch = Stopwatch.StartNew();
            var rig = BuildRig(cam, tiles);
            int w = Mathf.Max(64, TargetSize.x > 0 ? TargetSize.x : Screen.width);
            int h = Mathf.Max(64, TargetSize.y > 0 ? TargetSize.y : Screen.height);
            var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32);
            var previous = cam.targetTexture;
            cam.targetTexture = rt;
            cam.Render();
            cam.targetTexture = previous;
            RenderTexture.ReleaseTemporary(rt);
            Object.DestroyImmediate(rig);
            LastMs = (float)watch.Elapsed.TotalMilliseconds;
            return LastMs;
        }

        static GameObject BuildRig(Camera cam, TerrainTileSet tiles)
        {
            var rig = new GameObject("WarmupRig");
            var c = cam.transform.position;
            rig.transform.position = new Vector3(c.x, c.y, 0f);
            if (white == null) white = Sprite.Create(Texture2D.whiteTexture, new Rect(0, 0, 4, 4), new Vector2(0.5f, 0.5f), 4f);

            var reg = ArtMaterials.Active;
            AddSprite(rig.transform, "Lit", reg != null ? reg.lit : null, new Vector3(-1f, 0f, 0f));
            AddSprite(rig.transform, "LitEmissive", reg != null ? reg.litEmissive : null, new Vector3(1f, 0f, 0f));

            if (tiles != null)
            {
                var grid = new GameObject("Grid", typeof(Grid));
                grid.transform.SetParent(rig.transform, false);
                var tm = new GameObject("Tiles").AddComponent<Tilemap>();
                tm.transform.SetParent(grid.transform, false);
                var tr = tm.gameObject.AddComponent<TilemapRenderer>();
                tr.mode = TilemapRenderer.Mode.Chunk;
                int x = -6;
                for (byte id = 1; id < TileId.Count; id++)
                {
                    var t = tiles.Get(id, BlobAutotile.VariantCount - 1);
                    if (t != null) tm.SetTile(new Vector3Int(x++, -2, 0), t);
                }
            }
            return rig;
        }

        static void AddSprite(Transform parent, string name, Material mat, Vector3 at)
        {
            var sr = new GameObject(name).AddComponent<SpriteRenderer>();
            sr.transform.SetParent(parent, false);
            sr.transform.localPosition = at;
            sr.sprite = white;
            if (mat != null) sr.sharedMaterial = mat;
        }
    }
}
