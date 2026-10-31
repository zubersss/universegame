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
        /// <summary>Vertical world-follow per layer (U-039 fix): layers hang off the Datum, so canyons and Olympus keep a sane horizon.</summary>
        public static readonly float[] Follow = { 0.1f, 0.15f, 0.2f };
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
        static readonly int DatumId = Shader.PropertyToID("_Datum");
        static readonly int HorizonId = Shader.PropertyToID("_HorizonOffset");
        static readonly int GroundId = Shader.PropertyToID("_GroundColor");
        static readonly int AlphaId = Shader.PropertyToID("_Alpha");
        static readonly int TintId = Shader.PropertyToID("_Tint");

        MeshRenderer quad;
        readonly Texture2D[] textures = new Texture2D[3];
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

        /// <summary>Hazy distant ground under the far horizon (canyon floors, below the layers).</summary>
        public static Color GroundColor(PlanetId id) => id switch
        {
            PlanetId.Mars => new Color(0.46f, 0.29f, 0.2f),
            PlanetId.Earth => new Color(0.24f, 0.28f, 0.2f),
            _ => SkyColor(id) * 0.45f,
        };

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
            ResetWalls();
            Planet = planet.id;
            LayersLoaded = 0;
            var sky = SkyColor(planet.id);
            view.backgroundColor = Tinted(sky, Tint);
            block.Clear();
            block.SetColor(SkyColorId, sky);
            // Earth's sea fills up to the Datum (water tiles at y ≤ datum): below it the backdrop is water.
            block.SetFloat(SeaLevelId, planet.id == PlanetId.Earth ? planet.datumY + 1f : -100000f);
            seaLevel = planet.id == PlanetId.Earth ? planet.datumY + 1f : float.NegativeInfinity;
            if (underwaterMaterial != null) underwaterMaterial.SetFloat(SeaLevelId, planet.datumY + 1f);
            block.SetFloat(DatumId, planet.datumY);
            block.SetFloat(HorizonId, BaseOffset(0) + ContentBase[0] * TileHeights[0]); // the far ridge's foot
            block.SetColor(GroundId, GroundColor(planet.id));
            block.SetColor(TintId, Tint);
            block.SetFloat(AlphaId, Alpha);
            for (int i = 0; i < 3; i++)
            {
                textures[i] = null;
                block.SetTexture(LayerTex[i], Texture2D.blackTexture);
                block.SetVector(LayerP[i], new Vector4(TileHeights[i] * 2f, TileHeights[i], Factors[i], BaseOffset(i))); // 2048×1024 sheets
                block.SetVector(LayerQ[i], new Vector4(Haze[i], ContentBase[i], 0f, Follow[i])); // y: cut below the layer's own ground line
            }
            quad.SetPropertyBlock(block);
            quad.enabled = true;
            baseSet = planet.id.ToString().ToLowerInvariant();
            mainSet = null;
            ShowMain(baseSet);
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

        // ---------- art sets and the biome cross-fade (U-038) ----------

        /// <summary>One backdrop art set (`backgrounds/&lt;name&gt;/layer0..2`), loaded on demand.</summary>
        sealed class ArtSet
        {
            public readonly Texture2D[] tex = new Texture2D[3];
            public readonly AsyncOperationHandle<Texture2D>[] handles = new AsyncOperationHandle<Texture2D>[3];
            public int pending, loaded;
            public bool missing; // no layer0 art: the base set stands in
        }

        /// <summary>Width of the cross-fade window centred on a biome border (m).</summary>
        public const float FadeWidth = 20f;
        /// <summary>Sets within this distance of the camera load ahead; others are released.</summary>
        public const float PreloadDistance = 60f, KeepDistance = 120f;

        readonly System.Collections.Generic.Dictionary<string, ArtSet> sets = new System.Collections.Generic.Dictionary<string, ArtSet>();
        readonly System.Collections.Generic.List<string> dropScratch = new System.Collections.Generic.List<string>();
        string baseSet, mainSet, overlaySet;
        MeshRenderer overlay;
        MaterialPropertyBlock overlayBlock;
        static readonly int FadeId = Shader.PropertyToID("_Fade");

        /// <summary>The art set shown by the main backdrop / the cross-fade overlay (null when none).</summary>
        public string MainSet => mainSet;
        public string OverlaySet => overlay != null && overlay.enabled ? overlaySet : null;
        /// <summary>Opacity of the overlay set over the main one (0 when not fading).</summary>
        public float FadeWeight { get; private set; }

        /// <summary>Earth's backdrop set per biome (B-026); other planets have one set.</summary>
        public static string SetFor(PlanetId p, int x)
        {
            if (p != PlanetId.Earth) return p.ToString().ToLowerInvariant();
            switch (Meridian.Terrain.EarthBiomes.At(x))
            {
                case Meridian.Terrain.Biome.Desert: return "earth_desert";
                case Meridian.Terrain.Biome.Ocean: return "earth_coast";
                case Meridian.Terrain.Biome.Taiga:
                case Meridian.Terrain.Biome.Tundra: return "earth_taiga";
                default: return "earth";
            }
        }

        /// <summary>The set to draw for `name`: itself once known to exist, else the planet's base set.</summary>
        string Resolve(string name) => sets.TryGetValue(name, out var s) && s.missing ? baseSet : name;

        ArtSet Request(string name)
        {
            if (sets.TryGetValue(name, out var set)) return set;
            set = new ArtSet();
            sets[name] = set;
            for (int i = 0; i < 3; i++) LoadLayer(name, set, i);
            return set;
        }

        void LoadLayer(string name, ArtSet set, int i)
        {
            string key = ArtKeys.Backgrounds.Layer(name, i);
            set.pending++;
            var locations = Addressables.LoadResourceLocationsAsync(key);
            locations.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                Addressables.Release(loc);
                if (!exists || quad == null || !sets.TryGetValue(name, out var live) || live != set)
                {
                    set.pending--;
                    if (!exists && i == 0 && name != baseSet) set.missing = true;
                    return;
                }
                set.handles[i] = Addressables.LoadAssetAsync<Texture2D>(key);
                set.handles[i].Completed += op =>
                {
                    set.pending--;
                    if (quad == null || op.Status != AsyncOperationStatus.Succeeded || !sets.TryGetValue(name, out var now) || now != set)
                    {
                        // Dropped while loading (planet change or released): don't keep the sheet.
                        if (set.handles[i].IsValid()) { Addressables.Release(set.handles[i]); set.handles[i] = default; }
                        return;
                    }
                    set.tex[i] = op.Result;
                    set.loaded++;
                    if (name == mainSet) ApplyLayer(quad, block, i, op.Result, true);
                };
            };
        }

        void ApplyLayer(MeshRenderer r, MaterialPropertyBlock b, int i, Texture2D t, bool main)
        {
            r.GetPropertyBlock(b);
            b.SetTexture(LayerTex[i], t != null ? t : Texture2D.blackTexture);
            b.SetVector(LayerQ[i], new Vector4(Haze[i], ContentBase[i], t != null ? 1f : 0f, Follow[i]));
            r.SetPropertyBlock(b);
            if (main) { textures[i] = t; LayersLoaded = 0; foreach (var x in textures) if (x != null) LayersLoaded++; }
        }

        /// <summary>Switches the main backdrop to a set (its loaded layers at once, the rest as they arrive).</summary>
        void ShowMain(string name)
        {
            if (name == mainSet) return;
            mainSet = name;
            var set = Request(name);
            for (int i = 0; i < 3; i++) ApplyLayer(quad, block, i, set.tex[i], true);
        }

        void UpdateBiomeFade()
        {
            if (!Planet.HasValue || baseSet == null) return;
            var p = Planet.Value;
            int x = Mathf.FloorToInt(view.transform.position.x);
            string left = Resolve(SetFor(p, x - (int)(FadeWidth * 0.5f)));
            string right = Resolve(SetFor(p, x + (int)(FadeWidth * 0.5f)));
            // Load the neighbours early (their sheets arrive asynchronously, never at the border).
            Request(Resolve(SetFor(p, x - (int)PreloadDistance)));
            Request(Resolve(SetFor(p, x + (int)PreloadDistance)));

            ShowMain(left);
            float t = 0f;
            if (right != left)
            {
                // Share of the 20 m window already in the right-hand biome (21 samples, 1 m apart).
                int n = 0, half = (int)(FadeWidth * 0.5f);
                for (int k = -half; k <= half; k++) if (Resolve(SetFor(p, x + k)) == right) n++;
                t = Mathf.Clamp01(n / FadeWidth);
                var rs = Request(right);
                if (rs.loaded == 0) t = 0f; // not here yet: keep showing the left set alone
            }
            FadeWeight = t;
            SetOverlay(t > 0f ? right : null, t);
            if ((Time.frameCount & 63) == 0) ReleaseFarSets(p, x);
        }

        void SetOverlay(string name, float t)
        {
            if (overlay == null)
            {
                if (name == null) return;
                var go = new GameObject("BackdropFade");
                go.transform.SetParent(view.transform, false);
                go.transform.localPosition = new Vector3(0f, 0f, 19.9f);
                go.AddComponent<MeshFilter>().sharedMesh = SpaceWorld.Quad();
                overlay = go.AddComponent<MeshRenderer>();
                var m = new Material(layerMaterial) { name = "SideParallaxFade" };
                m.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
                m.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                overlay.sharedMaterial = m;
                overlay.sortingOrder = -199; // just over the main backdrop
                overlayBlock = new MaterialPropertyBlock();
            }
            bool on = name != null;
            if (overlay.enabled != on) overlay.enabled = on;
            if (!on) return;
            overlaySet = name;
            overlay.transform.localScale = quad.transform.localScale;
            // Everything (sky, walls, sea, tint) as the main backdrop, only the layers and the opacity differ.
            quad.GetPropertyBlock(overlayBlock);
            var set = sets[name];
            for (int i = 0; i < 3; i++)
            {
                overlayBlock.SetTexture(LayerTex[i], set.tex[i] != null ? set.tex[i] : Texture2D.blackTexture);
                overlayBlock.SetVector(LayerQ[i], new Vector4(Haze[i], ContentBase[i], set.tex[i] != null ? 1f : 0f, Follow[i]));
            }
            overlayBlock.SetFloat(FadeId, t);
            overlay.SetPropertyBlock(overlayBlock);
        }

        void ReleaseFarSets(PlanetId p, int x)
        {
            dropScratch.Clear();
            foreach (var kv in sets)
            {
                string n = kv.Key;
                if (n == baseSet || n == mainSet || n == overlaySet) continue;
                bool near = false;
                for (int d = -(int)KeepDistance; d <= (int)KeepDistance && !near; d += 10) near = SetFor(p, x + d) == n;
                if (!near && kv.Value.pending == 0) dropScratch.Add(n);
            }
            foreach (var n in dropScratch) { ReleaseSet(sets[n]); sets.Remove(n); }
        }

        static void ReleaseSet(ArtSet set)
        {
            for (int i = 0; i < 3; i++)
                if (set.handles[i].IsValid()) { Addressables.Release(set.handles[i]); set.handles[i] = default; }
        }

        void LateUpdate()
        {
            if (view == null || quad == null) return;
            // Generous width: the quad must cover the view at any aspect (captures switch to 16:9 targets).
            float h = view.orthographicSize * 2f, w = h * Mathf.Max(view.aspect, 2.5f);
            quad.transform.localScale = new Vector3(w, h, 1f);
            UpdateBiomeFade();

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
            UpdateWalls();
            UpdateUnderwater();
        }

        // ---------- background walls (U-040) ----------

        /// <summary>Columns covered by the wall map around the camera (±128 m: any zoom).</summary>
        public const int WallColumns = 256;
        /// <summary>The near-surface wall material reaches this deep; deeper walls use the deep material.</summary>
        public const float WallNearDepth = 4f;
        public const float WallDark = 0.32f;

        /// <summary>POI stamps change the original ground line where they sit (their walls follow the stamp).</summary>
        public Meridian.Planet.POI.PoiPlacer pois;

        Texture2D wallMap;
        Color[] wallPixels;
        int wallOrigin = int.MinValue;
        bool wallTexturesSet;
        public bool WallsReady => wallTexturesSet;

        static readonly int WallMapId = Shader.PropertyToID("_WallMap");
        static readonly int WallOriginId = Shader.PropertyToID("_WallOrigin");
        static readonly int[] WallTexIds = { Shader.PropertyToID("_WallTex0"), Shader.PropertyToID("_WallTex1"), Shader.PropertyToID("_WallTex2") };
        static readonly int[] WallRectIds = { Shader.PropertyToID("_WallRect0"), Shader.PropertyToID("_WallRect1"), Shader.PropertyToID("_WallRect2") };

        /// <summary>Wall materials per planet: slot 0 near-surface, 1 deep rock, 2 the special near layer (sand / ice).</summary>
        static byte[] WallMaterials(PlanetId p) => p == PlanetId.Mars
            ? new[] { Meridian.Terrain.TileId.Regolith, Meridian.Terrain.TileId.Basalt, Meridian.Terrain.TileId.Ice }
            : new[] { Meridian.Terrain.TileId.Soil, Meridian.Terrain.TileId.Stone, Meridian.Terrain.TileId.Sand };

        /// <summary>The original ground line of column x (top solid tile before any digging; stamps included).</summary>
        public int WallTop(int x)
        {
            if (pois != null && pois.StampGroundAt(x, out int stamped)) return stamped;
            return terrain.Generator.SurfaceHeight(terrain.WrapX(x));
        }

        /// <summary>Near and deep wall slots of column x (biome / landform).</summary>
        void WallSlots(int x, out int near, out int deep)
        {
            deep = 1;
            near = 0;
            if (Planet == PlanetId.Earth)
            {
                var b = Meridian.Terrain.EarthBiomes.At(x);
                if (b == Meridian.Terrain.Biome.Desert || b == Meridian.Terrain.Biome.Ocean) near = 2;
            }
            else if (Planet == PlanetId.Mars && Meridian.Terrain.MarsLandforms.At(x) == Meridian.Terrain.MarsFeature.PolarCap) near = 2;
        }

        void UpdateWalls()
        {
            if (terrain == null || terrain.Generator == null || !Planet.HasValue) return;
            if (!wallTexturesSet)
            {
                if (!terrain.TileSet.IsReady) return;
                var mats = WallMaterials(Planet.Value);
                quad.GetPropertyBlock(block);
                for (int i = 0; i < 3; i++)
                {
                    var tile = terrain.TileSet.Get(mats[i], 46) as UnityEngine.Tilemaps.Tile;
                    if (tile == null || tile.sprite == null) return;
                    var tex = tile.sprite.texture;
                    var r = tile.sprite.textureRect;
                    block.SetTexture(WallTexIds[i], tex);
                    block.SetVector(WallRectIds[i], new Vector4(r.x / tex.width, r.y / tex.height, r.width / tex.width, r.height / tex.height));
                }
                if (wallMap == null)
                {
                    wallMap = new Texture2D(WallColumns, 1, TextureFormat.RGBAFloat, false, true) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, name = "WallMap" };
                    wallPixels = new Color[WallColumns];
                }
                block.SetTexture(WallMapId, wallMap);
                quad.SetPropertyBlock(block);
                wallTexturesSet = true;
                wallOrigin = int.MinValue;
            }
            int origin = Mathf.FloorToInt(view.transform.position.x) - WallColumns / 2;
            if (Mathf.Abs(origin - wallOrigin) < 16) return; // refresh every 16 m of travel (the map spans ±128 m)
            wallOrigin = origin;
            for (int i = 0; i < WallColumns; i++)
            {
                int x = origin + i;
                WallSlots(x, out int near, out int deep);
                wallPixels[i] = new Color(WallTop(x), near, deep, 1f);
            }
            wallMap.SetPixels(wallPixels);
            wallMap.Apply(false, false);
            quad.GetPropertyBlock(block);
            block.SetFloat(WallOriginId, origin);
            quad.SetPropertyBlock(block);
        }

        // ---------- underwater tint (U-040, LEAD: seabed by water depth) ----------

        /// <summary>Multiply overlay below sea level (Earth): one quad over the world, only while the sea is in view.</summary>
        public Material underwaterMaterial;
        MeshRenderer tintQuad;
        float seaLevel = float.NegativeInfinity;
        public bool UnderwaterVisible => tintQuad != null && tintQuad.enabled;

        void UpdateUnderwater()
        {
            if (underwaterMaterial == null || view == null) return;
            if (tintQuad == null)
            {
                var go = new GameObject("UnderwaterTint");
                go.transform.SetParent(view.transform, false);
                go.transform.localPosition = new Vector3(0f, 0f, 2f);
                go.AddComponent<MeshFilter>().sharedMesh = SpaceWorld.Quad();
                tintQuad = go.AddComponent<MeshRenderer>();
                tintQuad.sharedMaterial = underwaterMaterial;
                tintQuad.sortingOrder = 30; // over terrain, water and the surveyor; under fx and the HUD
            }
            float bottom = view.transform.position.y - view.orthographicSize;
            bool on = !float.IsNegativeInfinity(seaLevel) && bottom < seaLevel;
            if (tintQuad.enabled != on) tintQuad.enabled = on;
            if (!on) return;
            float h = view.orthographicSize * 2f, w = h * Mathf.Max(view.aspect, 2.5f);
            tintQuad.transform.localScale = new Vector3(w, h, 1f);
        }

        void OnEnable() => Meridian.Core.RenderWarmup.Warming += OnWarming;
        void OnDisable() => Meridian.Core.RenderWarmup.Warming -= OnWarming;

        /// <summary>The underwater overlay joins the load warm-up render so the first sea view doesn't stall.</summary>
        void OnWarming(Camera cam, bool on)
        {
            if (cam != view) return;
            UpdateUnderwater();
            if (tintQuad == null) return;
            if (on) tintQuad.enabled = true;
            else UpdateUnderwater();
        }

        /// <summary>Forget the wall textures (planet change).</summary>
        void ResetWalls() { wallTexturesSet = false; wallOrigin = int.MinValue; }

        /// <summary>How far layer i's image shifts on screen per metre of camera motion (its factor).</summary>
        public static float ScreenShiftPerMetre(int i) => Factors[i];

        void Release()
        {
            foreach (var s in sets.Values) ReleaseSet(s);
            sets.Clear();
            mainSet = overlaySet = null;
            FadeWeight = 0f;
            if (overlay != null) overlay.enabled = false;
            for (int i = 0; i < 3; i++) textures[i] = null;
        }

        void OnDestroy() => Release();
    }
}
