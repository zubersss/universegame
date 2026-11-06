using Meridian.Art;
using Meridian.Rendering;
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
        static readonly int ViewHalfId = Shader.PropertyToID("_ViewHalf");
        float viewHalf = -1f;

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
            PlanetId.Mercury => new Color(0.2f, 0.19f, 0.21f), // dark regolith: the black sky must not make the haze #000 (U-057)
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
            planetDatum = planet.datumY;
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
        /// <summary>Whether a set's three layers are loaded (tests wait on the set preloaded ahead of a border).</summary>
        public bool SetReady(string name) => sets.TryGetValue(name, out var s) && s.loaded == 3;

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
            // Mercury (U-048): the far layer without its painted Sun; the Sun is its own sprite (MercurySun).
            string key = name == "mercury" && i == 0 ? ArtKeys.Backgrounds.Layer(name, i) + "_nosun" : ArtKeys.Backgrounds.Layer(name, i);
            set.pending++;
            var locations = Addressables.LoadResourceLocationsAsync(key);
            locations.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(loc);
                if (!exists || quad == null || !sets.TryGetValue(name, out var live) || live != set)
                {
                    set.pending--;
                    if (!exists && i == 0 && name != baseSet) set.missing = true;
                    return;
                }
                set.handles[i] = ArtLoad.Asset<Texture2D>(key);
                set.handles[i].Completed += op =>
                {
                    set.pending--;
                    if (quad == null || op.Status != AsyncOperationStatus.Succeeded || !sets.TryGetValue(name, out var now) || now != set)
                    {
                        // Dropped while loading (planet change or released): don't keep the sheet.
                        if (set.handles[i].IsValid()) { global::Meridian.Art.ArtLoad.Release(set.handles[i]); set.handles[i] = default; }
                        return;
                    }
                    set.tex[i] = op.Result;
                    set.loaded++;
                    if (name == mainSet) ApplyLayer(quad, block, i, op.Result, true);
                };
            };
        }

        /// <summary>U-076: with the 3D depth bands drawn, this quad shows only layer 0 (the sky), parked behind the skyline.</summary>
        public bool DepthBandsOn { get; private set; }
        public const float DepthBandsBehindPlane = 600f; // U-090: behind the 500 m cloud strip (was 450)

        public void SetDepthBands(bool on)
        {
            if (on == DepthBandsOn) return;
            DepthBandsOn = on;
            if (mainSet != null && sets.TryGetValue(mainSet, out var set))
                for (int i = 1; i < 3; i++) ApplyLayer(quad, block, i, set.tex[i], true);
        }

        void ApplyLayer(MeshRenderer r, MaterialPropertyBlock b, int i, Texture2D t, bool main)
        {
            if (DepthBandsOn && i > 0) t = null; // ridges and skyline are meshes now
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
            quad.GetPropertyBlock(block);
            block.SetFloat(DatumId, DatumOf(name));
            if (Planet.HasValue) block.SetColor(GroundId, GroundColorOf(name, Planet.Value));
            quad.SetPropertyBlock(block);
        }

        // ---------- Mercury's Sun (U-048) ----------

        /// <summary>Mercury's Sun: ~2.5× Earth's apparent size; radius as a share of the view's half-height.</summary>
        public const float SunRadius = 0.32f;
        static readonly int SunId = Shader.PropertyToID("_Sun");
        static readonly int GlowId = Shader.PropertyToID("_Glow");
        Vector4 glowShown = new Vector4(0f, 1f, 0f, -1f);
        Meridian.Core.TimeSystem clock;
        Vector4 sunShown = new Vector4(0f, 0f, 0f, -1f);
        /// <summary>Whether Mercury's Sun is drawn now (tests/captures), and its height (0 at dawn/dusk … 1 at noon).</summary>
        public bool SunVisible => sunShown.w > 0.5f;
        public float SunElevation { get; private set; }

        /// <summary>
        /// The Sun is drawn by the backdrop shader in the sky, under the layers, so the ridges hide it near the
        /// horizon (a sprite would draw over the opaque composite). It rises on the day side (-x) at the dawn line,
        /// stands overhead a quarter world back, sets toward +x at the dusk line; never in a cold trap.
        /// </summary>
        void UpdateSun()
        {
            var v = Vector4.zero;
            if (Planet == PlanetId.Mercury)
            {
                if (clock == null) clock = FindAnyObjectByType<Meridian.Core.TimeSystem>();
                var c = view.transform.position;
                int w = terrain != null && terrain.Config != null ? terrain.Config.worldWidth : 2048;
                float t = Meridian.Terrain.MercuryTerminator.LocalTime(c.x, Meridian.Terrain.MercuryTerminator.Now(clock != null ? clock.GameSeconds : 0), w);
                bool shade = terrain != null && Meridian.Terrain.MercuryLandforms.PermanentShadow(terrain.WrapX(Mathf.FloorToInt(c.x)), w);
                if (t > 0.2f && t < 0.8f && !shade)
                {
                    float phase = Mathf.Clamp01((t - 0.25f) / 0.5f) * Mathf.PI;
                    SunElevation = Mathf.Max(0f, Mathf.Sin(phase));
                    float half = Meridian.CameraRig.SideView.HalfHeight(view), wide = half * Mathf.Max(view.aspect, 1f);
                    float horizon = planetDatum + (BaseOffset(0) + ContentBase[0] * TileHeights[0]) + (c.y - planetDatum) * (1f - Follow[0]);
                    float r = SunRadius * half;
                    // From half below the far horizon (rising/setting behind the ridges) to high in the view at noon.
                    float y = horizon - r * 0.5f + SunElevation * (c.y + half * 0.75f - horizon + r * 0.5f);
                    v = new Vector4(c.x - Mathf.Cos(phase) * wide * 0.75f, y, r, 1f);
                }
                else SunElevation = 0f;
            }
            // U-057: the twilight band glows violet low over the horizon, strongest on the terminators.
            var g = new Vector4(0f, 1f, 0f, 0f);
            if (Planet == PlanetId.Mercury && clock != null)
            {
                var c = view.transform.position;
                int w = terrain != null && terrain.Config != null ? terrain.Config.worldWidth : 2048;
                float t = Meridian.Terrain.MercuryTerminator.LocalTime(c.x, Meridian.Terrain.MercuryTerminator.Now(clock.GameSeconds), w);
                float off = Mathf.Min(Mathf.Abs(t - 0.25f), Mathf.Abs(t - 0.75f));
                float band = Meridian.Terrain.MercuryTerminator.TwilightWidth * 0.5f / w; // the band's half-width in day fractions
                g = new Vector4(0.55f * Mathf.Clamp01(1f - off / band), Meridian.CameraRig.SideView.HalfHeight(view) * 0.6f, 0f, 0f);
            }
            if (v == sunShown && g == glowShown) return;
            sunShown = v;
            glowShown = g;
            quad.GetPropertyBlock(block);
            block.SetVector(SunId, v);
            block.SetVector(GlowId, g);
            quad.SetPropertyBlock(block);
        }

        // ---------- Mars canyon set (B-049, LEAD cycle after U-047) ----------

        public const string CanyonSet = "mars_canyon";
        /// <summary>Camera depth below the Datum (m) where the canyon set starts / finishes fading in, and where it preloads.</summary>
        public const float CanyonFadeStart = 37f, CanyonFadeEnd = 57f, CanyonPreload = 17f;
        float planetDatum;

        /// <summary>The level a set's layers hang off: the canyon set hangs off the canyon floor, all others off the Datum.</summary>
        /// <summary>The haze tone under a set's layers: below Venus's cloud deck you look down into cloud, not onto ground.</summary>
        static Color GroundColorOf(string set, PlanetId p) => set == VenusDeck ? new Color(0.8f, 0.66f, 0.46f) : GroundColor(p);

        float DatumOf(string set) => set == CanyonSet ? planetDatum - Meridian.Terrain.MarsLandforms.CanyonDepth
            : set == VenusDeck ? Meridian.Terrain.VenusLandforms.DeckY - 2f : planetDatum;

        void UpdateCanyonFade()
        {
            float depth = planetDatum - view.transform.position.y;
            string canyon = Resolve(CanyonSet);
            if (depth > CanyonPreload) Request(canyon);
            float t = canyon == baseSet ? 0f : Mathf.Clamp01((depth - CanyonFadeStart) / (CanyonFadeEnd - CanyonFadeStart));
            if (t > 0f && (!sets.TryGetValue(canyon, out var cs) || cs.loaded == 0)) t = 0f; // not here yet: stay on the mars set
            if (t >= 1f) { ShowMain(canyon); FadeWeight = 0f; SetOverlay(null, 0f); return; }
            ShowMain(baseSet);
            FadeWeight = t;
            SetOverlay(t > 0f ? canyon : null, t);
        }

        // ---------- Venus: surface ↔ cloud deck (U-050) ----------

        public const string VenusDeck = "venus_deck", VenusSurface = "venus_surface";
        /// <summary>Camera height where the deck set starts / finishes replacing the surface set.</summary>
        public const float VenusFadeBottom = 640f, VenusFadeTop = 700f;

        void UpdateVenusFade()
        {
            float y = view.transform.position.y;
            // Both sets stay loaded on Venus: a dive or a climb crosses the band in seconds.
            var deck = Request(VenusDeck);
            Request(VenusSurface);
            float t = Mathf.Clamp01((y - VenusFadeBottom) / (VenusFadeTop - VenusFadeBottom));
            if (t > 0f && deck.loaded == 0) t = 0f;
            if (t >= 1f) { ShowMain(VenusDeck); FadeWeight = 0f; SetOverlay(null, 0f); return; }
            ShowMain(VenusSurface);
            FadeWeight = t;
            SetOverlay(t > 0f ? VenusDeck : null, t);
        }

        void UpdateBiomeFade()
        {
            if (!Planet.HasValue || baseSet == null) return;
            var p = Planet.Value;
            if (p == PlanetId.Mars) { UpdateCanyonFade(); return; }
            if (p == PlanetId.Venus) { UpdateVenusFade(); return; }
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
            overlayBlock.SetFloat(DatumId, DatumOf(name));
            if (Planet.HasValue) overlayBlock.SetColor(GroundId, GroundColorOf(name, Planet.Value));
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
                if (n == CanyonSet || n == VenusDeck || n == VenusSurface) continue; // chosen by height, not by column
                bool near = false;
                for (int d = -(int)KeepDistance; d <= (int)KeepDistance && !near; d += 10) near = SetFor(p, x + d) == n;
                if (!near && kv.Value.pending == 0) dropScratch.Add(n);
            }
            foreach (var n in dropScratch) { ReleaseSet(sets[n]); sets.Remove(n); }
        }

        static void ReleaseSet(ArtSet set)
        {
            for (int i = 0; i < 3; i++)
                if (set.handles[i].IsValid()) { global::Meridian.Art.ArtLoad.Release(set.handles[i]); set.handles[i] = default; }
        }

        void LateUpdate()
        {
            if (view == null || quad == null) return;
            // Generous width: the quad must cover the view at any aspect (captures switch to 16:9 targets).
            // U-072: under the perspective rail the quad sits behind the play plane and is sized for its depth;
            // the shader keeps working in play-plane metres (viewHalf), so the art scale doesn't change.
            float quadDepth = DepthBandsOn && !view.orthographic
                ? Meridian.CameraRig.SideView.PlaneDistance(view) + DepthBandsBehindPlane // behind skyline_far (z ≤ 400 m)
                : Meridian.CameraRig.SideView.BackdropDepth(view);
            float h = Meridian.CameraRig.SideView.HalfHeightAtDepth(view, quadDepth) * 2f, w = h * Mathf.Max(view.aspect, 2.5f);
            quad.transform.localPosition = new Vector3(0f, 0f, quadDepth);
            quad.transform.localScale = new Vector3(w, h, 1f);
            if (overlay != null)
            {
                overlay.transform.localPosition = new Vector3(0f, 0f, quadDepth - 0.1f);
                overlay.transform.localScale = quad.transform.localScale;
            }
            float planeHalf = Meridian.CameraRig.SideView.HalfHeight(view);
            if (!Mathf.Approximately(planeHalf, viewHalf))
            {
                viewHalf = planeHalf;
                quad.GetPropertyBlock(block);
                block.SetFloat(ViewHalfId, viewHalf);
                quad.SetPropertyBlock(block);
            }
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
            UpdateSun();
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
        static byte[] WallMaterials(PlanetId p) => p switch
        {
            PlanetId.Mars => new[] { Meridian.Terrain.TileId.Regolith, Meridian.Terrain.TileId.Basalt, Meridian.Terrain.TileId.Ice },
            PlanetId.Mercury => new[] { Meridian.Terrain.TileId.MercuryRegolith, Meridian.Terrain.TileId.MercuryBasalt, Meridian.Terrain.TileId.MercuryIce },
            PlanetId.Venus => new[] { Meridian.Terrain.TileId.VenusBasalt, Meridian.Terrain.TileId.VenusBasalt, Meridian.Terrain.TileId.Tessera },
            _ => new[] { Meridian.Terrain.TileId.Soil, Meridian.Terrain.TileId.Stone, Meridian.Terrain.TileId.Sand },
        };

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
            else if (Planet == PlanetId.Mercury && terrain != null && Meridian.Terrain.MercuryLandforms.PermanentShadow(terrain.WrapX(x), terrain.Config.worldWidth)) near = 2;
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
                // a: 1 where the column holds sea water at sea level (the underwater tint applies only there).
                bool sea = !float.IsNegativeInfinity(seaLevel) && terrain.Generator.TileAt(terrain.WrapX(x), (int)seaLevel - 1) == Meridian.Terrain.TileId.Water;
                wallPixels[i] = new Color(WallTop(x), near, deep, sea ? 1f : 0f);
            }
            wallMap.SetPixels(wallPixels);
            wallMap.Apply(false, false);
            quad.GetPropertyBlock(block);
            block.SetFloat(WallOriginId, origin);
            if (underwaterMaterial != null)
            {
                underwaterMaterial.SetTexture(WallMapId, wallMap);
                underwaterMaterial.SetFloat(WallOriginId, origin);
            }
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
            float bottom = view.transform.position.y - Meridian.CameraRig.SideView.HalfHeight(view);
            bool on = !float.IsNegativeInfinity(seaLevel) && bottom < seaLevel;
            if (tintQuad.enabled != on) tintQuad.enabled = on;
            if (!on) return;
            // U-072: just in front of the play plane, so its world y (the tint's depth below sea level) matches the plane.
            float tz = view.orthographic ? 2f : Meridian.CameraRig.SideView.PlaneDistance(view) - 0.5f;
            tintQuad.transform.localPosition = new Vector3(0f, 0f, tz);
            float h = Meridian.CameraRig.SideView.HalfHeightAtDepth(view, tz) * 2f, w = h * Mathf.Max(view.aspect, 2.5f);
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
