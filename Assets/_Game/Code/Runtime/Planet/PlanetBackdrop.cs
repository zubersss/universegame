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
    /// layers behind the terrain (layer0 far and slowest, layer2 near), hazed toward the planet's sky.
    /// One quad, one opaque pass that composites sky + 3 layers (U-025 perf: three blended quads were too
    /// costly at 1080p on integrated graphics). Planets without layer art show only the sky color.
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

        static readonly int[] LayerTex = { Shader.PropertyToID("_Layer0"), Shader.PropertyToID("_Layer1"), Shader.PropertyToID("_Layer2") };
        static readonly int[] LayerP = { Shader.PropertyToID("_P0"), Shader.PropertyToID("_P1"), Shader.PropertyToID("_P2") };
        static readonly int[] LayerQ = { Shader.PropertyToID("_Q0"), Shader.PropertyToID("_Q1"), Shader.PropertyToID("_Q2") };
        static readonly int SkyColorId = Shader.PropertyToID("_SkyColor");
        static readonly int SeaLevelId = Shader.PropertyToID("_SeaLevel");
        static readonly int AlphaId = Shader.PropertyToID("_Alpha");
        static readonly int TintId = Shader.PropertyToID("_Tint");

        MeshRenderer quad;
        readonly Texture2D[] textures = new Texture2D[3];
        readonly AsyncOperationHandle<Texture2D>[] handles = new AsyncOperationHandle<Texture2D>[3];
        MaterialPropertyBlock block;
        public PlanetId? Planet { get; private set; }
        public int LayersLoaded { get; private set; }

        /// <summary>Layer i's loaded texture (null until loaded or when the planet has no art for it).</summary>
        public Texture2D LayerTexture(int i) => textures[i];

        void Awake()
        {
            block = new MaterialPropertyBlock();
            var go = new GameObject("Backdrop");
            go.transform.SetParent(view.transform, false);
            go.transform.localPosition = new Vector3(0f, 0f, 20f);
            go.AddComponent<MeshFilter>().sharedMesh = SpaceWorld.Quad();
            quad = go.AddComponent<MeshRenderer>();
            quad.sharedMaterial = layerMaterial;
            quad.sortingOrder = -200; // behind terrain (0) and everything else
            quad.enabled = false;
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
            view.backgroundColor = Tinted(sky, Tint);
            block.Clear();
            block.SetColor(SkyColorId, sky);
            // Earth's sea fills up to the Datum (water tiles at y ≤ datum): below it the backdrop is water.
            block.SetFloat(SeaLevelId, planet.id == PlanetId.Earth ? planet.datumY + 1f : -100000f);
            block.SetColor(TintId, Tint);
            block.SetFloat(AlphaId, Alpha);
            for (int i = 0; i < 3; i++)
            {
                textures[i] = null;
                block.SetTexture(LayerTex[i], Texture2D.blackTexture);
                block.SetVector(LayerP[i], new Vector4(TileHeights[i] * 2f, TileHeights[i], Factors[i], BaseOffset(i))); // 2048×1024 sheets
                block.SetVector(LayerQ[i], new Vector4(Haze[i], i == 0 ? 1f : i == 2 ? 2f : 0f, 0f, 0f)); // far: clamp, near: mirror, middle: end
            }
            quad.SetPropertyBlock(block);
            quad.enabled = true;
            string name = planet.id.ToString().ToLowerInvariant();
            for (int i = 0; i < 3; i++) LoadLayer(i, ArtKeys.Backgrounds.Layer(name, i));
        }

        /// <summary>Day/night multiplier (U-025) on the sky color and every layer; 1 = full day.</summary>
        public Color Tint { get; private set; } = Color.white;

        public void SetTint(Color tint)
        {
            if (Mathf.Abs(tint.r - Tint.r) + Mathf.Abs(tint.g - Tint.g) + Mathf.Abs(tint.b - Tint.b) < 0.002f) return;
            Tint = tint;
            if (Planet.HasValue && view != null) view.backgroundColor = Tinted(SkyColor(Planet.Value), tint);
            if (quad == null) return;
            quad.GetPropertyBlock(block);
            block.SetColor(TintId, tint);
            quad.SetPropertyBlock(block);
        }

        public static Color Tinted(Color sky, Color tint) => new Color(sky.r * tint.r, sky.g * tint.g, sky.b * tint.b, 1f);

        void LoadLayer(int i, string key)
        {
            var locations = Addressables.LoadResourceLocationsAsync(key);
            locations.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                Addressables.Release(loc);
                if (!exists || quad == null) return;
                handles[i] = Addressables.LoadAssetAsync<Texture2D>(key);
                handles[i].Completed += op =>
                {
                    if (quad == null || op.Status != AsyncOperationStatus.Succeeded) return;
                    textures[i] = op.Result;
                    quad.GetPropertyBlock(block);
                    block.SetTexture(LayerTex[i], op.Result);
                    block.SetVector(LayerQ[i], new Vector4(Haze[i], i == 0 ? 1f : i == 2 ? 2f : 0f, 1f, 0f));
                    quad.SetPropertyBlock(block);
                    LayersLoaded++;
                };
            };
        }

        void LateUpdate()
        {
            if (view == null || quad == null) return;
            // Generous width: the quad must cover the view at any aspect (captures switch to 16:9 targets).
            float h = view.orthographicSize * 2f, w = h * Mathf.Max(view.aspect, 2.5f);
            quad.transform.localScale = new Vector3(w, h, 1f);

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
                quad.GetPropertyBlock(block);
                block.SetFloat(AlphaId, alpha);
                quad.SetPropertyBlock(block);
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
