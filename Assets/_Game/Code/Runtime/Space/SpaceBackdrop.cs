using Meridian.Art;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Space
{
    /// <summary>
    /// Star layers behind the top-down map (U-022): backgrounds/space/layer0..2 as camera-filling
    /// quads, tiled in x and y, scrolling at parallax factors (layer0 slowest). One draw call per layer.
    /// </summary>
    public sealed class SpaceBackdrop : MonoBehaviour
    {
        public Camera view;
        public Material layerMaterial;
        /// <summary>Fraction of camera motion each layer follows in screen terms (0 = fixed to the screen).</summary>
        public float[] parallax = { 0.002f, 0.006f, 0.015f };
        /// <summary>Screen heights per texture tile, per layer: near layers show larger stars.</summary>
        public float[] tilesPerScreenHeight = { 1.0f, 0.8f, 0.6f };

        static readonly int UVScale = Shader.PropertyToID("_UVScale");
        static readonly int UVOffset = Shader.PropertyToID("_UVOffset");
        static readonly int MainTex = Shader.PropertyToID("_MainTex");

        MeshRenderer[] layers;
        MaterialPropertyBlock block;
        AsyncOperationHandle<Texture2D>[] handles;

        void Awake()
        {
            int n = parallax.Length;
            layers = new MeshRenderer[n];
            handles = new AsyncOperationHandle<Texture2D>[n];
            block = new MaterialPropertyBlock();
            for (int i = 0; i < n; i++)
            {
                var go = new GameObject("StarLayer" + i);
                go.transform.SetParent(view.transform, false);
                go.transform.localPosition = new Vector3(0f, 0f, 40f - i); // in front of the camera, behind nothing that matters
                go.AddComponent<MeshFilter>().sharedMesh = SpaceWorld.Quad();
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterial = layerMaterial;
                mr.sortingOrder = -100 + i;
                layers[i] = mr;
                int index = i;
                handles[i] = Addressables.LoadAssetAsync<Texture2D>(ArtKeys.Backgrounds.Layer("space", i));
                handles[i].Completed += op =>
                {
                    if (mr == null || op.Status != AsyncOperationStatus.Succeeded) return;
                    mr.GetPropertyBlock(block);
                    block.SetTexture(MainTex, op.Result);
                    mr.SetPropertyBlock(block);
                };
            }
        }

        void LateUpdate()
        {
            if (view == null) return;
            float h = view.orthographicSize * 2f, w = h * view.aspect;
            var cam = (Vector2)view.transform.position;
            for (int i = 0; i < layers.Length; i++)
            {
                var t = layers[i].transform;
                t.localScale = new Vector3(w, h, 1f);
                // A tile spans tilesPerScreenHeight screen heights at the reference zoom, independent of zoom.
                float tile = 1f / tilesPerScreenHeight[i];
                float aspectTex = 0.5f; // layers are 2048 × 1024: one tile is twice as wide as tall
                var scale = new Vector4(view.aspect * aspectTex * tile, tile, 0f, 0f);
                var offset = new Vector4(cam.x * parallax[i] * aspectTex / 60f, cam.y * parallax[i] / 60f, 0f, 0f);
                layers[i].GetPropertyBlock(block);
                block.SetVector(UVScale, scale);
                block.SetVector(UVOffset, offset);
                layers[i].SetPropertyBlock(block);
            }
        }

        void OnDestroy()
        {
            if (handles == null) return;
            foreach (var h in handles) if (h.IsValid()) Addressables.Release(h);
        }
    }
}
