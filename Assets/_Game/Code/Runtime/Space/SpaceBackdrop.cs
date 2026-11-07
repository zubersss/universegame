using System.Collections.Generic;
using Meridian.Art;
using Meridian.View2D;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Space
{
    /// <summary>
    /// The painted sky behind the top-down map. U-103 (D-108, B-120): the scene `backgrounds/space/starfield` from its
    /// SceneLayout json: layer0 is a 2048×1024 tile repeating in x and y as a camera-filling quad scrolling at its parallax
    /// (one draw call), layer1..3 are nebula cards drifting at theirs, wrapped so they never leave the camera's
    /// neighbourhood. Until that scene exists the U-022 star layers (backgrounds/space/layer0..2) draw as before.
    /// </summary>
    public sealed class SpaceBackdrop : MonoBehaviour
    {
        public Camera view;
        public Material layerMaterial;
        /// <summary>U-103: the painted scene (SceneLayout json + layer{n} sprites).</summary>
        public string sceneKey = "backgrounds/space/starfield";
        /// <summary>Fallback (U-022): fraction of camera motion each star layer follows in screen terms (0 = fixed to the screen).</summary>
        public float[] parallax = { 0.002f, 0.006f, 0.015f };
        /// <summary>Fallback: screen heights per texture tile, per layer: near layers show larger stars.</summary>
        public float[] tilesPerScreenHeight = { 1.0f, 0.8f, 0.6f };
        /// <summary>Nebula cards: height as a fraction of the view, and where each sits (in view heights from the camera).</summary>
        public const float CardHeight = 0.9f;
        public static readonly Vector2[] CardSpread = { new Vector2(-0.55f, 0.25f), new Vector2(0.5f, -0.3f), new Vector2(0.05f, 0.55f) };
        public const int BackOrder = -200;

        static readonly int UVScale = Shader.PropertyToID("_UVScale");
        static readonly int UVOffset = Shader.PropertyToID("_UVOffset");
        static readonly int MainTex = Shader.PropertyToID("_MainTex");

        /// <summary>The scene layout in use (null while the fallback layers draw).</summary>
        public SceneLayout Layout { get; private set; }
        public bool SceneReady => Layout != null && tiles.Count + cards.Count > 0;
        public IReadOnlyList<MeshRenderer> Tiles => tiles;
        public IReadOnlyList<SpriteRenderer> Cards => cards;

        readonly List<MeshRenderer> tiles = new List<MeshRenderer>();
        readonly List<float> tileParallax = new List<float>();
        readonly List<float> tileHeights = new List<float>();
        readonly List<SpriteRenderer> cards = new List<SpriteRenderer>();
        readonly List<float> cardParallax = new List<float>();
        readonly List<float> cardHeights = new List<float>();
        MeshRenderer[] fallback;
        MaterialPropertyBlock block;
        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>();
        AsyncOperationHandle<TextAsset> sceneHandle;

        void Awake()
        {
            block = new MaterialPropertyBlock();
            var probe = Addressables.LoadResourceLocationsAsync(sceneKey, typeof(TextAsset));
            probe.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(loc);
                if (this == null) return;
                if (exists) LoadScene(); else BuildFallback();
            };
        }

        void LoadScene()
        {
            sceneHandle = ArtLoad.Asset<TextAsset>(sceneKey);
            sceneHandle.Completed += op =>
            {
                if (this == null) return;
                if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null) { BuildFallback(); return; }
                Layout = SceneLayout.Parse(op.Result.text);
                foreach (var l in Layout.layers)
                {
                    string key = $"{sceneKey}/layer{l.n}";
                    if (l.tile) AddTile(key, l); else AddCard(key, l);
                }
            };
        }

        MeshRenderer Quad(string name, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(view.transform, false);
            go.transform.localPosition = new Vector3(0f, 0f, 40f); // in front of the camera, behind everything that matters
            go.AddComponent<MeshFilter>().sharedMesh = SpaceWorld.Quad();
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = layerMaterial;
            mr.sortingOrder = order;
            return mr;
        }

        void AddTile(string key, SceneLayout.Layer l)
        {
            var mr = Quad("Starfield" + l.n, BackOrder + l.n);
            tiles.Add(mr); tileParallax.Add(l.parallax); tileHeights.Add(l.height_px > 0 ? l.height_px / Mathf.Max(1f, Layout.ppu) : 16f);
            var h = ArtLoad.Asset<IList<Sprite>>(key);
            handles.Add(h);
            h.Completed += op =>
            {
                if (mr == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                mr.GetPropertyBlock(block);
                block.SetTexture(MainTex, op.Result[0].texture);
                mr.SetPropertyBlock(block);
            };
        }

        void AddCard(string key, SceneLayout.Layer l)
        {
            var go = new GameObject("Nebula" + l.n);
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = BackOrder + l.n;
            var mat = Meridian.Rendering.ArtMaterials.MaterialFor(key);
            if (mat != null) sr.sharedMaterial = mat;
            cards.Add(sr); cardParallax.Add(l.parallax); cardHeights.Add(l.height_px > 0 ? l.height_px / Mathf.Max(1f, Layout.ppu) : 16f);
            var h = ArtLoad.Asset<IList<Sprite>>(key);
            handles.Add(h);
            h.Completed += op =>
            {
                if (sr == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                sr.sprite = op.Result[0];
            };
        }

        void BuildFallback()
        {
            int n = parallax.Length;
            fallback = new MeshRenderer[n];
            for (int i = 0; i < n; i++)
            {
                var mr = Quad("StarLayer" + i, -100 + i);
                mr.transform.localPosition = new Vector3(0f, 0f, 40f - i);
                fallback[i] = mr;
                var h = ArtLoad.Asset<Texture2D>(ArtKeys.Backgrounds.Layer("space", i));
                handles.Add(h);
                h.Completed += op =>
                {
                    if (mr == null || op.Status != AsyncOperationStatus.Succeeded) return;
                    mr.GetPropertyBlock(block);
                    block.SetTexture(MainTex, op.Result);
                    mr.SetPropertyBlock(block);
                };
            }
        }

        /// <summary>
        /// U-117 (LEAD, space_1_saturn): the painted tile's world period: its native height at the flight zoom, and never less than half
        /// the frame when the camera zooms out, so the sky never reads as a repeating column pattern. Pure.
        /// </summary>
        public static float TilePeriod(float nativeHeight, float frameHeight) => Mathf.Max(nativeHeight, frameHeight * 0.5f);

        void LateUpdate()
        {
            if (view == null) return;
            // Generous width: the quads must cover the view at any aspect (16:9 captures from a batch-size screen).
            float aspect = Mathf.Max(view.aspect, 2.5f);
            float h = view.orthographicSize * 2f, w = h * aspect;
            var cam = (Vector2)view.transform.position;
            for (int i = 0; i < tiles.Count; i++)
            {
                // The tile keeps its painted size (height_px / ppu units) and scrolls at its parallax: UV offset = camera motion × parallax / tile size.
                var t = tiles[i].transform;
                t.localScale = new Vector3(w, h, 1f);
                float tileH = TilePeriod(tileHeights[i], h), tileW = tileH * 2f; // 2048 × 1024; U-117: the period grows with the zoom
                var scale = new Vector4(w / tileW, h / tileH, 0f, 0f);
                var offset = new Vector4(cam.x * tileParallax[i] / tileW, cam.y * tileParallax[i] / tileH, 0f, 0f);
                tiles[i].GetPropertyBlock(block);
                block.SetVector(UVScale, scale);
                block.SetVector(UVOffset, offset);
                tiles[i].SetPropertyBlock(block);
            }
            for (int i = 0; i < cards.Count; i++)
            {
                // A card drifts against the camera at its parallax, wrapped over twice the view so it never leaves the neighbourhood.
                float period = 2f * h;
                var drift = new Vector2(Mathf.Repeat(cam.x * cardParallax[i] + period * 0.5f, period) - period * 0.5f,
                                        Mathf.Repeat(cam.y * cardParallax[i] + period * 0.5f, period) - period * 0.5f);
                var spread = CardSpread[Mathf.Min(i, CardSpread.Length - 1)] * h;
                cards[i].transform.position = new Vector3(cam.x + spread.x - drift.x, cam.y + spread.y - drift.y, 40f);
                float s = CardHeight * h / Mathf.Max(1f, cardHeights[i]);
                cards[i].transform.localScale = new Vector3(s, s, 1f);
            }
            if (fallback == null) return;
            for (int i = 0; i < fallback.Length; i++)
            {
                var t = fallback[i].transform;
                t.localScale = new Vector3(w, h, 1f);
                float tile = 1f / tilesPerScreenHeight[i];
                float aspectTex = 0.5f; // layers are 2048 × 1024: one tile is twice as wide as tall
                var scale = new Vector4(aspect * aspectTex * tile, tile, 0f, 0f);
                var offset = new Vector4(cam.x * parallax[i] * aspectTex / 60f, cam.y * parallax[i] / 60f, 0f, 0f);
                fallback[i].GetPropertyBlock(block);
                block.SetVector(UVScale, scale);
                block.SetVector(UVOffset, offset);
                fallback[i].SetPropertyBlock(block);
            }
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            if (sceneHandle.IsValid()) global::Meridian.Art.ArtLoad.Release(sceneHandle);
        }
    }
}
