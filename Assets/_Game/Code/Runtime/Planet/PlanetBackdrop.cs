using Meridian.Art;
using Meridian.Planets;
using Meridian.Space;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Planet
{
    /// <summary>
    /// Side-view atmosphere (U-024, Bible §9): `backgrounds/&lt;planet&gt;/layer0..2` as three parallax
    /// layers behind the terrain (layer0 far and slowest, layer2 near), hazed toward the planet's sky,
    /// and the camera clearing to that sky color. Three draw calls. Planets without layer art keep
    /// only the sky color.
    /// </summary>
    public sealed class PlanetBackdrop : MonoBehaviour
    {
        public Camera view;
        public Material layerMaterial;

        /// <summary>Per layer: parallax factor (share of world motion), tile height in m, haze.</summary>
        public static readonly float[] Factors = { 0.06f, 0.22f, 0.45f };
        public static readonly float[] TileHeights = { 28f, 22f, 16f };
        public static readonly float[] Haze = { 0.35f, 0.2f, 0.08f };
        /// <summary>
        /// Where each layer's content starts in its sheet (fraction from the bottom), read off the
        /// B-010/B-011 renders: layer0 = base of the far ridgeline, layer1 = base of the treeline/hills
        /// band, layer2 = near ground from the bottom edge. That line sits just under the surface.
        /// </summary>
        public static readonly float[] ContentBase = { 0.22f, 0.28f, 0f };
        /// <summary>The content base sits this far below the camera: under the player's feet (the camera looks 1.5 m above them).</summary>
        public const float BaseBelowCamera = 4f;
        /// <summary>The backdrop fades out between these depths of the camera below the local surface (caves).</summary>
        public const float FadeStartDepth = 4f, FadeEndDepth = 10f;

        /// <summary>Shader _BaseOffset: sheet bottom relative to the camera, so row `contentBase` lands 4 m below it.</summary>
        public static float BaseOffset(int i) => -(BaseBelowCamera + ContentBase[i] * TileHeights[i]);

        public Meridian.Terrain.TerrainStreamer terrain;
        public float Alpha { get; private set; } = 1f;

        static readonly int MainTex = Shader.PropertyToID("_MainTex");
        static readonly int TileSize = Shader.PropertyToID("_TileSize");
        static readonly int Factor = Shader.PropertyToID("_Factor");
        static readonly int BaseOffsetId = Shader.PropertyToID("_BaseOffset");
        static readonly int AlphaId = Shader.PropertyToID("_Alpha");
        static readonly int HazeColor = Shader.PropertyToID("_HazeColor");
        static readonly int HazeAmount = Shader.PropertyToID("_HazeAmount");
        static readonly int ExtendBelow = Shader.PropertyToID("_ExtendBelow");

        readonly MeshRenderer[] layers = new MeshRenderer[3];
        readonly AsyncOperationHandle<Texture2D>[] handles = new AsyncOperationHandle<Texture2D>[3];
        MaterialPropertyBlock block;
        public PlanetId? Planet { get; private set; }
        public int LayersLoaded { get; private set; }

        void Awake()
        {
            block = new MaterialPropertyBlock();
            for (int i = 0; i < layers.Length; i++)
            {
                var go = new GameObject("BackdropLayer" + i);
                go.transform.SetParent(view.transform, false);
                go.transform.localPosition = new Vector3(0f, 0f, 20f - i);
                go.AddComponent<MeshFilter>().sharedMesh = SpaceWorld.Quad();
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterial = layerMaterial;
                mr.sortingOrder = -200 + i; // behind terrain (0) and everything else
                mr.enabled = false;
                layers[i] = mr;
            }
        }

        public static Color SkyColor(PlanetId id) => id switch
        {
            PlanetId.Mars => new Color(0.78f, 0.6f, 0.42f),     // butterscotch (Bible §7.2, B-011)
            PlanetId.Mercury => new Color(0.03f, 0.03f, 0.05f), // no atmosphere
            PlanetId.Venus => new Color(0.86f, 0.72f, 0.45f),
            PlanetId.Jupiter => new Color(0.82f, 0.66f, 0.5f),
            PlanetId.Saturn => new Color(0.86f, 0.78f, 0.55f),
            PlanetId.Uranus => new Color(0.55f, 0.82f, 0.85f),
            PlanetId.Neptune => new Color(0.28f, 0.36f, 0.75f),
            _ => new Color(0.45f, 0.62f, 0.85f),                  // Earth
        };

        public void ConfigureFor(PlanetConfig planet)
        {
            Release();
            Planet = planet.id;
            LayersLoaded = 0;
            var sky = SkyColor(planet.id);
            view.backgroundColor = sky;
            string name = planet.id.ToString().ToLowerInvariant();
            for (int i = 0; i < layers.Length; i++)
            {
                var mr = layers[i];
                mr.enabled = false;
                block.Clear();
                block.SetVector(TileSize, new Vector4(TileHeights[i] * 2f, TileHeights[i], 0f, 0f)); // 2048×1024 sheets
                block.SetFloat(Factor, Factors[i]);
                block.SetFloat(BaseOffsetId, BaseOffset(i));
                block.SetFloat(AlphaId, 1f);
                block.SetFloat(ExtendBelow, i == 0 ? 1f : i == 2 ? 2f : 0f); // far: clamp, near: mirror, middle: end
                block.SetColor(HazeColor, sky);
                block.SetFloat(HazeAmount, Haze[i]);
                mr.SetPropertyBlock(block);
                LoadLayer(i, ArtKeys.Backgrounds.Layer(name, i));
            }
        }

        void LoadLayer(int i, string key)
        {
            var mr = layers[i];
            var locations = Addressables.LoadResourceLocationsAsync(key);
            locations.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                Addressables.Release(loc);
                if (!exists || mr == null) return;
                handles[i] = Addressables.LoadAssetAsync<Texture2D>(key);
                handles[i].Completed += op =>
                {
                    if (mr == null || op.Status != AsyncOperationStatus.Succeeded) return;
                    mr.GetPropertyBlock(block);
                    block.SetTexture(MainTex, op.Result);
                    mr.SetPropertyBlock(block);
                    mr.enabled = true;
                    LayersLoaded++;
                };
            };
        }

        void LateUpdate()
        {
            if (view == null) return;
            // Generous width: the quad must cover the view at any aspect (captures switch to 16:9 targets).
            float h = view.orthographicSize * 2f, w = h * Mathf.Max(view.aspect, 2.5f);
            for (int i = 0; i < layers.Length; i++) layers[i].transform.localScale = new Vector3(w, h, 1f);

            // Underground the sky backdrop fades out (caves show the sky color only, M2 cave art later).
            float alpha = 1f;
            if (terrain != null && terrain.Generator != null)
            {
                var c = view.transform.position;
                float surface = terrain.Generator.SurfaceHeight(terrain.WrapX(Mathf.FloorToInt(c.x)));
                float depth = surface - c.y;
                alpha = 1f - Mathf.InverseLerp(FadeStartDepth, FadeEndDepth, depth);
            }
            if (!Mathf.Approximately(alpha, Alpha))
            {
                Alpha = alpha;
                for (int i = 0; i < layers.Length; i++)
                {
                    layers[i].GetPropertyBlock(block);
                    block.SetFloat(AlphaId, alpha);
                    layers[i].SetPropertyBlock(block);
                }
            }
        }

        /// <summary>How far layer i's image shifts on screen per metre of camera motion (its factor).</summary>
        public static float ScreenShiftPerMetre(int i) => Factors[i];

        void Release()
        {
            for (int i = 0; i < handles.Length; i++)
                if (handles[i].IsValid()) { Addressables.Release(handles[i]); handles[i] = default; }
        }

        void OnDestroy() => Release();
    }
}
