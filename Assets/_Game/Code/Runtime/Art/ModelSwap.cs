using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Art
{
    /// <summary>
    /// U-076 (Bible 2.0 §10.6): puts a key's 3D model where its 2D sprite stands and, once every tile has loaded,
    /// stops drawing the sprite (forceRenderingOff: the sprite keeps its bounds, colliders and materials, so the
    /// gameplay code and its tests that read them are untouched). Keys without a model never swap: the sprite stays.
    /// The model's origin is its base (contract §9), placed at `localBase` under `parent`. Optional: `tiles` copies
    /// `tileStep` metres apart, centred (the 2 m landing-pad module, D-068), and a fit to a footprint like the sprite's.
    /// </summary>
    public sealed class ModelSwap : MonoBehaviour
    {
        public enum Fit { None, Height, Stretch }

        public SpriteRenderer Sprite { get; private set; }
        public string Key { get; private set; }
        public bool Ready { get; private set; }
        public readonly List<ModelView> Views = new List<ModelView>();
        /// <summary>Fires once, when the model (or the sheet, U-113) takes over the sprite.</summary>
        public event System.Action<ModelSwap> Swapped;
        /// <summary>U-113 (D-117): the sheet that draws this key when it has no model (props/common/* after B-131); null on the model path.</summary>
        public SheetProp Sheet { get; private set; }
        public bool UsesSheet => Sheet != null;
        int tiles = 1;
        float tileStep;

        Fit fit;
        Vector2 footprint;

        public static ModelSwap Attach(SpriteRenderer sprite, string key, Transform parent, Vector3 localBase,
                                       int tiles = 1, float tileStep = 0f, Fit fit = Fit.None, Vector2 footprint = default)
        {
            var go = new GameObject("Model");
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localBase;
            var s = go.AddComponent<ModelSwap>();
            s.Sprite = sprite;
            s.Key = key;
            s.fit = fit;
            s.footprint = footprint;
            tiles = Mathf.Max(1, tiles);
            s.tiles = tiles; s.tileStep = tileStep;
            for (int i = 0; i < tiles; i++)
            {
                var t = new GameObject(tiles == 1 ? "View" : "Tile" + i);
                t.transform.SetParent(go.transform, false);
                t.transform.localPosition = new Vector3((i - (tiles - 1) * 0.5f) * tileStep, 0f, 0f);
                var v = t.AddComponent<ModelView>();
                v.Loaded += s.OnLoaded;
                s.Views.Add(v);
                v.Load(key);
            }
            return s;
        }

        void Start()
        {
            // U-113: no model under the key but a v3 sheet (its json is addressed at <key>/json): the sprite stays and the sheet dresses it.
            var model = Addressables.LoadResourceLocationsAsync(Key, typeof(GameObject));
            model.Completed += l =>
            {
                bool hasModel = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (this == null || Ready || hasModel || Sprite == null) return;
                var json = Addressables.LoadResourceLocationsAsync(Key + "/json", typeof(TextAsset));
                json.Completed += j =>
                {
                    bool hasSheet = j.Status == AsyncOperationStatus.Succeeded && j.Result != null && j.Result.Count > 0;
                    ArtLoad.Release(j);
                    if (this == null || Ready || !hasSheet || Sprite == null) return;
                    var fp = footprint.x > 0f ? footprint : new Vector2(tiles * tileStep, 0f); // a tiled POI prop: its tiles' span, no height rule
                    Sheet = SheetProp.Attach(Sprite, Key, fp, fit == Fit.Stretch, fit == Fit.Height);
                    Sheet.Loaded += p => { if (this == null || Ready) return; Ready = true; Swapped?.Invoke(this); };
                };
            };
        }

        void OnLoaded()
        {
            foreach (var v in Views) if (!v.Ready) return;
            if (Ready) return;
            Ready = true;
            if (fit != Fit.None) ApplyFit();
            if (Sprite != null) Sprite.forceRenderingOff = true;
            Swapped?.Invoke(this);
        }

        /// <summary>Scales the model like the sprite was: Height = uniform to the footprint's height, Stretch = to its width and height.</summary>
        void ApplyFit()
        {
            var size = ModelSize(Views[0].Instance);
            if (size.x <= 0f || size.y <= 0f || footprint.y <= 0f) return;
            transform.localScale = fit == Fit.Stretch
                ? new Vector3(footprint.x / size.x, footprint.y / size.y, 1f)
                : Vector3.one * (footprint.y / size.y);
        }

        static readonly Dictionary<string, Vector3> sizes = new Dictionary<string, Vector3>();

        /// <summary>The model's true extent in its own space (the vertices: a skinned renderer's bounds are padded).</summary>
        public static Bounds ModelBounds(GameObject instance)
        {
            var root = instance.transform;
            bool any = false;
            var b = new Bounds();
            void Add(Vector3 p) { if (!any) { b = new Bounds(p, Vector3.zero); any = true; } else b.Encapsulate(p); }
            foreach (var mf in instance.GetComponentsInChildren<MeshFilter>())
            {
                if (mf.sharedMesh == null || mf.name.EndsWith("_LOD1")) continue;
                var mb = mf.sharedMesh.bounds;
                var m = root.worldToLocalMatrix * mf.transform.localToWorldMatrix;
                for (int i = 0; i < 8; i++)
                    Add(m.MultiplyPoint3x4(mb.center + Vector3.Scale(mb.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1))));
            }
            foreach (var smr in instance.GetComponentsInChildren<SkinnedMeshRenderer>())
            {
                var baked = new Mesh();
                smr.BakeMesh(baked, true);
                var m = root.worldToLocalMatrix * smr.transform.localToWorldMatrix;
                foreach (var v in baked.vertices) Add(m.MultiplyPoint3x4(v));
                Destroy(baked);
            }
            return b;
        }

        Vector3 ModelSize(GameObject instance)
        {
            if (sizes.TryGetValue(Key, out var s)) return s;
            s = ModelBounds(instance).size;
            sizes[Key] = s;
            return s;
        }

        /// <summary>A named node of the first tile's model (sockets: "socket_light", "socket_cockpit"), or null.</summary>
        public Transform Find(string node)
        {
            if (Views.Count == 0 || Views[0].Instance == null) return null;
            foreach (var t in Views[0].Instance.GetComponentsInChildren<Transform>(true))
                if (t.name == node) return t;
            return null;
        }
    }
}
