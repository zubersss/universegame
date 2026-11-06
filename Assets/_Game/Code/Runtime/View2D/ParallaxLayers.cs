using System.Collections.Generic;
using Meridian.Art;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.View2D
{
    /// <summary>U-094 (contract §11.4): a painted scene's &lt;scene&gt;.json.</summary>
    [System.Serializable]
    public sealed class SceneLayout
    {
        [System.Serializable] public sealed class Layer { public int n; public float parallax; public float y_m; }
        public Layer[] layers;

        /// <summary>Three layers (far, mid, near) when a scene has no json yet.</summary>
        public static SceneLayout Default() => new SceneLayout
        {
            layers = new[] { new Layer { n = 0, parallax = 0.1f, y_m = 4f }, new Layer { n = 1, parallax = 0.3f, y_m = 2f }, new Layer { n = 2, parallax = 0.6f, y_m = 0f } },
        };

        public static SceneLayout Parse(string json)
        {
            if (string.IsNullOrEmpty(json)) return Default();
            try
            {
                var s = JsonUtility.FromJson<SceneLayout>(json);
                return s != null && s.layers != null && s.layers.Length > 0 ? s : Default();
            }
            catch (System.Exception) { return Default(); }
        }
    }

    /// <summary>
    /// U-094: where a parallax layer sits, pure C#. `parallax` is the layer's scroll factor against the ground: 1 scrolls with
    /// the ground, 0.1 drifts at a tenth of it (far), 0 stays fixed to the screen. The layer's bottom rests y_m above the
    /// planet's surface datum when the camera looks at the datum and moves vertically by the same factor.
    /// </summary>
    public static class ParallaxMath
    {
        public static float LayerX(float cameraX, float parallax) => cameraX * (1f - parallax);
        public static float LayerY(float cameraY, float datumY, float yM, float parallax) => datumY + yM + (cameraY - datumY) * (1f - parallax);
    }

    /// <summary>
    /// U-094 (Bible §9.4 v4, contract §11.4): 3–5 painted layers behind the side view from backgrounds/&lt;planet&gt;/&lt;scene&gt;/:
    /// each layer is one tiled SpriteRenderer (3 widths wide, so it always covers the frame) placed every LateUpdate by
    /// ParallaxMath. A layer whose PNG is missing draws a flat tinted placeholder strip, so the scene runs before the art
    /// lands. Draw order: layer 0 (farthest) at the back. No allocation per frame.
    /// </summary>
    public sealed class ParallaxLayers : MonoBehaviour
    {
        public Camera view;
        /// <summary>World height of the planet's surface datum (the layers' y_m are above it).</summary>
        public float datumY;
        public const int BackOrder = -200;
        /// <summary>Placeholder strip size (m) and tints far → near (muted Earth plains: sky haze, hills, meadow).</summary>
        public const float PlaceholderWidth = 32f, PlaceholderHeight = 8f;
        static readonly Color[] PlaceholderTints = { new Color(0.78f, 0.80f, 0.70f), new Color(0.62f, 0.68f, 0.50f), new Color(0.48f, 0.58f, 0.36f), new Color(0.40f, 0.50f, 0.30f), new Color(0.34f, 0.42f, 0.26f) };

        public string SceneKey { get; private set; }
        public SceneLayout Layout { get; private set; } = SceneLayout.Default();
        public readonly List<SpriteRenderer> renderers = new List<SpriteRenderer>(5);
        public readonly List<bool> placeholders = new List<bool>(5);

        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>(6);
        static Sprite white;

        /// <summary>Builds the layers of backgrounds/&lt;planet&gt;/&lt;scene&gt; (placeholders at once, art as it loads).</summary>
        public void ConfigureFor(string planet, string scene, float surfaceDatum)
        {
            Clear();
            datumY = surfaceDatum;
            SceneKey = $"backgrounds/{planet}/{scene}";
            Build(SceneLayout.Default());
            Probe<TextAsset>(SceneKey, h => h.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                Build(SceneLayout.Parse(op.Result.text));
            });
        }

        void Build(SceneLayout layout)
        {
            foreach (var r in renderers) if (r != null) Destroy(r.gameObject);
            renderers.Clear(); placeholders.Clear();
            Layout = layout;
            for (int i = 0; i < layout.layers.Length; i++)
            {
                var l = layout.layers[i];
                var go = new GameObject("Layer" + l.n);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = BackOrder + l.n;
                SetPlaceholder(sr, l.n);
                renderers.Add(sr);
                placeholders.Add(true);
                int index = i;
                Probe<Sprite>(SceneKey + "/layer" + l.n, h => h.Completed += op =>
                {
                    if (this == null || index >= renderers.Count || renderers[index] != sr || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                    sr.color = Color.white;
                    sr.drawMode = SpriteDrawMode.Tiled;
                    sr.sprite = op.Result;
                    sr.size = new Vector2(op.Result.bounds.size.x * 3f, op.Result.bounds.size.y);
                    placeholders[index] = false;
                });
            }
            LateUpdate();
        }

        static void SetPlaceholder(SpriteRenderer sr, int n)
        {
            if (white == null)
            {
                var tex = Texture2D.whiteTexture;
                white = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0f), tex.width);
                white.name = "ParallaxPlaceholder";
            }
            sr.sprite = white;
            sr.drawMode = SpriteDrawMode.Sliced;
            sr.size = new Vector2(PlaceholderWidth * 3f, PlaceholderHeight - n);
            sr.color = PlaceholderTints[Mathf.Clamp(n, 0, PlaceholderTints.Length - 1)];
        }

        void Probe<T>(string address, System.Action<AsyncOperationHandle<T>> load)
        {
            var probe = Addressables.LoadResourceLocationsAsync(address, typeof(T));
            probe.Completed += l =>
            {
                IResourceLocation loc = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0 ? l.Result[0] : null;
                ArtLoad.Release(l);
                if (loc == null || this == null) return;
                var h = ArtLoad.Asset<T>(loc, SceneKey);
                handles.Add(h);
                load(h);
            };
        }

        void LateUpdate()
        {
            if (view == null) return;
            var c = view.transform.position;
            for (int i = 0; i < renderers.Count && i < Layout.layers.Length; i++)
            {
                var l = Layout.layers[i];
                var sr = renderers[i];
                if (sr == null) continue;
                float w = sr.size.x / 3f;
                float x = ParallaxMath.LayerX(c.x, l.parallax);
                // Keep the 3-wide strip centred on the camera: shift by whole tile widths (tileable art, no seam).
                if (w > 0f) x += Mathf.Round((c.x - x) / w) * w;
                sr.transform.position = new Vector3(x, ParallaxMath.LayerY(c.y, datumY, l.y_m, l.parallax), 0f);
            }
        }

        void Clear()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
        }

        void OnDestroy() => Clear();
    }
}
