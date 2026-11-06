using System.Collections.Generic;
using Meridian.Art;
using Meridian.Perf;
using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Planet.Backdrop
{
    /// <summary>
    /// U-090 (Bible §10.10, contract §10, D-079): the painted-stage stack per region. DepthBands keeps the play-plane
    /// side (ground strip, near flora, ridge_mid, the planet skyline); this component adds the rest and the streaming:
    ///  0 foreground pieces (props/&lt;planet&gt;_foreground/*, one per 12 m at z −3…−1.5, never within 6 m of the spawn, a POI or a pad, no shadows),
    ///  3 rocks_near (backgrounds/&lt;planet&gt;/rocks_near, period 128 m, z 8…14),
    ///  5 hills_far (backgrounds/&lt;planet&gt;_&lt;region&gt;/hills_far, period 512 m, z 80…140),
    ///  6 the region's skyline_far (period 1024 m, z 150…400; the planet's skyline through DepthBands otherwise) and the stage.json set-pieces,
    ///  7 the cloud strip (backgrounds/&lt;planet&gt;/clouds at z 500, period 2048 m, scrolling 0.5 m/s); the dome stays on PlanetBackdrop.
    /// Each region's set is one Addressable label `stage_&lt;planet&gt;_&lt;region&gt;`: the neighbour's set preloads within 200 m
    /// of the border and is released 5 s after the camera is out of reach. Missing keys draw as flat tinted placeholder
    /// quads, so all 8 planets run before BLENDER's sets land. No layer has collision; digging and building are untouched.
    /// </summary>
    public sealed class StageLayers : MonoBehaviour
    {
        public Camera view;
        public TerrainStreamer terrain;
        public Meridian.Planet.POI.PoiPlacer pois;
        public DepthBands bands;
        public PlanetBackdrop backdrop;

        public enum Slot { Foreground = 0, PlayPlane = 1, NearFlora = 2, NearRocks = 3, MidRidge = 4, FarHills = 5, FarMountains = 6, Sky = 7 }

        public struct LayerInfo
        {
            public Slot slot;
            public string key;
            public float z;
            public bool ready, placeholder;
            public bool Drawn => ready || placeholder;
        }

        // Depths and periods (Bible §10.10).
        public const float ForegroundNearZ = -3f, ForegroundFarZ = -1.5f, ForegroundKeepOut = 6f;
        public const float RocksZ = 11f, RocksPeriod = 128f;
        public const float HillsZ = 110f, HillsPeriod = 512f;
        public const float SkylineZ = 250f, SkylinePeriod = 1024f;
        public const float CloudZ = 500f, CloudPeriod = 2048f, CloudHeight = 512f, CloudScroll = 0.5f;
        public const float PreloadDistance = 200f, ReleaseDelay = 5f;
        public const int ForegroundHalfWidth = 96;
        /// <summary>Haze mix toward the region's haze_rgb by depth (contract §10: 20 % at z 20, 45 % at 60, 70 % at 150+).</summary>
        public static float HazeAt(float z) => z <= 20f ? 0.2f : z <= 60f ? Mathf.Lerp(0.2f, 0.45f, (z - 20f) / 40f) : z <= 150f ? Mathf.Lerp(0.45f, 0.7f, (z - 60f) / 90f) : 0.7f;

        sealed class StageSet
        {
            public string region, label;
            public AsyncOperationHandle<IList<UnityEngine.Object>> handle;
            public AsyncOperationHandle<TextAsset> manifestHandle;
            public StageManifest manifest;
            public bool nothingToLoad, manifestChecked;
            public float releaseAt = -1f;
            public bool Resident => nothingToLoad || (handle.IsValid() && handle.IsDone);
        }

        readonly Dictionary<string, StageSet> sets = new Dictionary<string, StageSet>();
        readonly List<string> dropSets = new List<string>();
        readonly Dictionary<int, GameObject> foreground = new Dictionary<int, GameObject>();
        readonly List<int> dropFg = new List<int>();
        readonly List<LayerInfo> layers = new List<LayerInfo>(12);
        readonly List<GameObject> setPieces = new List<GameObject>();
        ModelBand rocks, hills, skyline;
        GameObject cloudGo;
        MeshRenderer cloudRenderer;
        AsyncOperationHandle<Texture2D> cloudHandle;
        bool cloudMissing;
        MaterialPropertyBlock cloudBlock;
        static readonly int BaseMapId = Shader.PropertyToID("_BaseMap"), BaseColorId = Shader.PropertyToID("_BaseColor");
        PlanetId planet;
        string planetName;
        bool configured;
        int fgCentre = int.MinValue;
        string setPiecesRegion;

        public string Region { get; private set; }
        public StageManifest Manifest { get; private set; }
        /// <summary>The stack as last described: one entry per slot (set-pieces appear as extra FarMountains entries).</summary>
        public IReadOnlyList<LayerInfo> Layers { get { Describe(); return layers; } }
        public bool IsSetResident(string region) => sets.TryGetValue(region, out var s) && s.Resident;
        public bool IsSetHeld(string region) => sets.ContainsKey(region);
        public static string LabelFor(string region) => "stage_" + region;

        public void ConfigureFor(PlanetConfig config)
        {
            Clear();
            planet = config.id;
            planetName = planet.ToString().ToLowerInvariant();
            configured = true;
        }

        /// <summary>Distinct slots drawn (ready or placeholder) for the current region.</summary>
        public int DrawnSlots()
        {
            Describe();
            int mask = 0, n = 0;
            foreach (var l in layers) { int bit = 1 << (int)l.slot; if (l.Drawn && (mask & bit) == 0) { mask |= bit; n++; } }
            return n;
        }

        void LateUpdate()
        {
            if (!configured || view == null || terrain == null || terrain.Config == null) return;
            float camX = view.transform.position.x;
            int col = terrain.WrapX(Mathf.FloorToInt(camX));
            int width = terrain.Config.worldWidth;

            string region = StageRegions.At(planet, col);
            if (region != Region) EnterRegion(region);
            StreamSets(col, width);

            float baseY = bands != null ? bands.BaseY : view.transform.position.y - 4f;
            bool shown = backdrop == null || backdrop.Alpha > 0.01f;
            rocks?.Place(camX, baseY, shown);
            hills?.Place(camX, baseY, shown);
            skyline?.Place(camX, baseY, shown);
            PlaceSetPieces(baseY, width);
            PlaceClouds(camX, baseY);

            if (fgCentre == int.MinValue || Mathf.Abs(Mathf.FloorToInt(camX) - fgCentre) >= 16) { fgCentre = Mathf.FloorToInt(camX); UpdateForeground(fgCentre); }
        }

        void EnterRegion(string region)
        {
            Region = region;
            var set = Request(region);
            Manifest = set.manifest ?? StageManifest.Default(region);
            hills?.Destroy(); skyline?.Destroy();
            var haze = Manifest.Haze;
            hills = new ModelBand(transform, $"backgrounds/{region}/hills_far", HillsPeriod, HillsZ, HillsPeriod, 60f, new Color(0.45f, 0.5f, 0.55f));
            hills.SetHaze(Color.Lerp(Color.white, haze, HazeAt(HillsZ)));
            skyline = new ModelBand(transform, $"backgrounds/{region}/skyline_far", SkylinePeriod, SkylineZ, SkylinePeriod, 150f, new Color(0.55f, 0.58f, 0.65f));
            skyline.SetHaze(Color.Lerp(Color.white, haze, HazeAt(SkylineZ)));
            if (rocks == null)
            {
                rocks = new ModelBand(transform, $"backgrounds/{planetName}/rocks_near", RocksPeriod, RocksZ, RocksPeriod, 6f, new Color(0.4f, 0.38f, 0.35f));
            }
            rocks.SetHaze(Color.Lerp(Color.white, haze, HazeAt(RocksZ)));
            BuildSetPieces(region);
        }

        // ---------- set streaming (one label per region) ----------

        StageSet Request(string region)
        {
            if (sets.TryGetValue(region, out var s)) { s.releaseAt = -1f; return s; }
            s = new StageSet { region = region, label = LabelFor(region) };
            sets[region] = s;
            var probe = Addressables.LoadResourceLocationsAsync(s.label);
            probe.Completed += l =>
            {
                bool any = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(l);
                if (this == null || !sets.TryGetValue(region, out var live) || live != s) return;
                if (!any) { s.nothingToLoad = true; return; }
                s.handle = ArtLoad.Assets<UnityEngine.Object>(s.label, "planet_" + planetName);
            };
            var manifestKey = $"backgrounds/{region}/stage";
            var mprobe = Addressables.LoadResourceLocationsAsync(manifestKey, typeof(TextAsset));
            mprobe.Completed += l =>
            {
                bool any = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(l);
                if (this == null) return;
                if (!any) { s.manifestChecked = true; return; }
                s.manifestHandle = ArtLoad.Asset<TextAsset>(manifestKey);
                s.manifestHandle.Completed += op =>
                {
                    s.manifestChecked = true;
                    if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                    s.manifest = StageManifest.Parse(region, op.Result.text);
                    if (region == Region) { Manifest = s.manifest; ApplyManifest(); }
                };
            };
            return s;
        }

        void ApplyManifest()
        {
            var haze = Manifest.Haze;
            hills?.SetHaze(Color.Lerp(Color.white, haze, HazeAt(HillsZ)));
            skyline?.SetHaze(Color.Lerp(Color.white, haze, HazeAt(SkylineZ)));
            rocks?.SetHaze(Color.Lerp(Color.white, haze, HazeAt(RocksZ)));
            BuildSetPieces(Region);
            fgCentre = int.MinValue; // the foreground piece list may have changed
        }

        void StreamSets(int col, int width)
        {
            // The neighbour's set preloads within 200 m of the border.
            if (StageRegions.DistanceToBorder(planet, width, col) <= PreloadDistance)
            {
                var next = StageRegions.Neighbour(planet, width, col);
                if (next != null) Request(next);
            }
            // Sets out of reach (not current, not within 200 m of their bounds) release 5 s later.
            dropSets.Clear();
            foreach (var kv in sets)
            {
                var s = kv.Value;
                if (s.region == Region) { s.releaseAt = -1f; continue; }
                bool near = WithinReach(s.region, col, width);
                if (near) { s.releaseAt = -1f; continue; }
                if (s.releaseAt < 0f) s.releaseAt = Time.time + ReleaseDelay;
                else if (Time.time >= s.releaseAt) dropSets.Add(kv.Key);
            }
            foreach (var r in dropSets) ReleaseSet(r);
        }

        bool WithinReach(string region, int col, int width)
        {
            // Walk the region's bounds from a column inside it: the neighbour of the current region, or any region 200 m away.
            if (StageRegions.Neighbour(planet, width, col) == region && StageRegions.DistanceToBorder(planet, width, col) <= PreloadDistance) return true;
            return false;
        }

        void ReleaseSet(string region)
        {
            if (!sets.TryGetValue(region, out var s)) return;
            sets.Remove(region);
            if (s.handle.IsValid()) global::Meridian.Art.ArtLoad.Release(s.handle);
            if (s.manifestHandle.IsValid()) global::Meridian.Art.ArtLoad.Release(s.manifestHandle);
        }

        // ---------- set-pieces (layer 6, per stage.json) ----------

        void BuildSetPieces(string region)
        {
            foreach (var go in setPieces) if (go != null) Destroy(go);
            setPieces.Clear();
            setPiecesRegion = region;
            if (Manifest == null) return;
            foreach (var p in Manifest.setpieces)
            {
                if (p == null || string.IsNullOrEmpty(p.key)) continue;
                var go = new GameObject("SetPiece " + p.key);
                go.transform.SetParent(transform, false);
                go.transform.localScale = new Vector3(p.mirror ? -p.scale : p.scale, p.scale, p.scale);
                go.AddComponent<ModelView>().Load($"backgrounds/{region}/{p.key}");
                setPieces.Add(go);
            }
        }

        void PlaceSetPieces(float baseY, int width)
        {
            if (Manifest == null || setPieces.Count == 0 || terrain == null) return;
            StageRegions.Bounds(planet, width, terrain.WrapX(Mathf.FloorToInt(view.transform.position.x)), out int start, out int length);
            float camX = view.transform.position.x;
            int n = Mathf.Min(setPieces.Count, Manifest.setpieces.Length);
            for (int i = 0; i < n; i++)
            {
                var p = Manifest.setpieces[i];
                var go = setPieces[i];
                if (go == null) continue;
                // `at` is a fraction of the region width from its western edge, applied on the wrapped world nearest the camera.
                float x = start + p.at * length;
                x += Mathf.Round((camX - x) / width) * width;
                go.transform.localPosition = new Vector3(x, baseY, p.z);
                var mv = go.GetComponent<ModelView>();
                if (mv != null && mv.Ready) { mv.SetTint(Color.Lerp(Color.white, Manifest.Haze, HazeAt(p.z))); mv.SetShadows(false); }
            }
        }

        // ---------- foreground pieces (layer 0) ----------

        static uint Hash(int i, uint salt) { uint h = (uint)i * 0x9E3779B1u ^ salt; h ^= h >> 16; h *= 0x7FEB352Du; h ^= h >> 15; h *= 0x846CA68Bu; h ^= h >> 16; return h; }
        static float Unit(int i, uint salt) => (Hash(i, salt) & 0xFFFFFF) / (float)0x1000000;

        /// <summary>The foreground piece at slot `i` (one per spacing): its wrapped column, key, depth and yaw; false when the slot is kept clear.</summary>
        public bool ForegroundAt(int i, out int x, out string key, out float z, out float yaw)
        {
            float spacing = Manifest != null ? Manifest.Spacing : 12f;
            x = Mathf.FloorToInt(i * spacing + Unit(i, 0x51) * (spacing - 3f) + 1.5f);
            var pieces = Manifest != null ? Manifest.Pieces : StageManifest.DefaultPieces;
            key = $"props/{planetName}_foreground/{pieces[(int)(Hash(i, 0x9) % (uint)pieces.Length)]}";
            z = Mathf.Lerp(ForegroundNearZ, ForegroundFarZ, Unit(i, 0x33));
            yaw = Unit(i, 0x77) * 360f;
            return !KeptClear(x);
        }

        /// <summary>Within 6 m of the spawn camp, a POI stamp or a landing pad (pads are POI props): no foreground piece.</summary>
        public bool KeptClear(int x)
        {
            if (terrain == null) return false;
            float spawn = Meridian.Planet.POI.PoiCatalog.SpawnCamp.CenterX;
            int w = terrain.Config != null ? terrain.Config.worldWidth : 1;
            float dx = Mathf.Abs(Mathf.DeltaAngle(x * 360f / w, spawn * 360f / w)) * w / 360f;
            if (dx <= ForegroundKeepOut + 2f) return true;
            if (pois == null) return false;
            for (int d = -(int)ForegroundKeepOut; d <= (int)ForegroundKeepOut; d++)
                if (pois.StampGroundAt(terrain.WrapX(x + d), out _)) return true;
            return false;
        }

        void UpdateForeground(int centre)
        {
            float spacing = Manifest != null ? Manifest.Spacing : 12f;
            int i0 = Mathf.FloorToInt((centre - ForegroundHalfWidth) / spacing), i1 = Mathf.CeilToInt((centre + ForegroundHalfWidth) / spacing);
            dropFg.Clear();
            foreach (var kv in foreground) if (kv.Key < i0 || kv.Key > i1) dropFg.Add(kv.Key);
            foreach (int i in dropFg) { if (foreground[i] != null) Destroy(foreground[i]); foreground.Remove(i); }
            for (int i = i0; i <= i1; i++)
            {
                if (foreground.ContainsKey(i)) continue;
                GameObject go = null;
                if (ForegroundAt(i, out int x, out string key, out float z, out float yaw))
                {
                    int top = terrain.OriginalTop(x);
                    go = new GameObject("Foreground " + key.Substring(key.LastIndexOf('/') + 1));
                    go.transform.SetParent(transform, false);
                    go.transform.localPosition = new Vector3(x + 0.5f, top + 1f, z);
                    go.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
                    var piece = go.AddComponent<ForegroundPiece>();
                    piece.Begin(key, Manifest != null ? Manifest.Haze : Color.white);
                }
                foreground[i] = go;
            }
        }

        // ---------- the cloud strip (layer 7) ----------

        void PlaceClouds(float camX, float baseY)
        {
            if (cloudMissing) return;
            if (cloudGo == null)
            {
                cloudGo = StagePlaceholder.Quad(transform, "Clouds", CloudPeriod, CloudHeight, new Color(1f, 1f, 1f, 1f));
                cloudRenderer = cloudGo.GetComponent<MeshRenderer>();
                cloudGo.SetActive(false);
                cloudBlock = new MaterialPropertyBlock();
                var key = $"backgrounds/{planetName}/clouds";
                var probe = Addressables.LoadResourceLocationsAsync(key, typeof(Texture2D));
                probe.Completed += l =>
                {
                    bool any = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                    global::Meridian.Art.ArtLoad.Release(l);
                    if (this == null) return;
                    if (!any) { cloudMissing = true; return; } // the dome alone: no strip to draw
                    cloudHandle = ArtLoad.Asset<Texture2D>(key);
                    cloudHandle.Completed += op =>
                    {
                        if (this == null || cloudGo == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) { cloudMissing = true; return; }
                        cloudRenderer.GetPropertyBlock(cloudBlock);
                        cloudBlock.SetTexture(BaseMapId, op.Result);
                        cloudBlock.SetColor(BaseColorId, Color.white);
                        cloudRenderer.SetPropertyBlock(cloudBlock);
                        cloudGo.SetActive(true);
                    };
                };
                return;
            }
            if (!cloudGo.activeSelf) return;
            // One period wide, re-centred on the camera; the texture scrolls 0.5 m/s through the UV offset.
            cloudGo.transform.localPosition = new Vector3(camX, baseY + 120f, CloudZ);
            cloudRenderer.GetPropertyBlock(cloudBlock);
            cloudBlock.SetVector(Shader.PropertyToID("_BaseMap_ST"), new Vector4(1f, 1f, (camX + Time.time * CloudScroll) / CloudPeriod, 0f));
            cloudRenderer.SetPropertyBlock(cloudBlock);
        }

        // ---------- description (tests, captures) ----------

        void Describe()
        {
            layers.Clear();
            if (!configured) return;
            float fgZ = 0f; string fgKey = null; bool fgReady = false, fgPlaceholder = false;
            foreach (var kv in foreground)
            {
                if (kv.Value == null) continue;
                var piece = kv.Value.GetComponent<ForegroundPiece>();
                if (piece == null) continue;
                fgKey = piece.Key; fgZ = kv.Value.transform.localPosition.z; fgReady |= piece.Ready; fgPlaceholder |= piece.Placeholder;
                if (fgReady) break;
            }
            layers.Add(new LayerInfo { slot = Slot.Foreground, key = fgKey ?? $"props/{planetName}_foreground/*", z = fgZ, ready = fgReady, placeholder = fgPlaceholder });
            layers.Add(new LayerInfo { slot = Slot.PlayPlane, key = "terrain", z = 0f, ready = terrain != null && terrain.IsSettled });
            layers.Add(new LayerInfo { slot = Slot.NearFlora, key = bands != null && bands.FloraCount > 0 ? "props/flora" : "props/flora (none here)", z = DepthBands.FloraNearZ, ready = bands != null && bands.FloraCount > 0, placeholder = bands != null && bands.Ground != null });
            if (rocks != null) layers.Add(new LayerInfo { slot = Slot.NearRocks, key = rocks.key, z = RocksZ, ready = rocks.Ready, placeholder = rocks.Placeholder });
            layers.Add(new LayerInfo { slot = Slot.MidRidge, key = bands != null ? bands.RidgeKey : null, z = bands != null && bands.RidgeReady ? bands.RidgeDepth.x : 40f, ready = bands != null && bands.RidgeReady, placeholder = bands != null && bands.RidgePlaceholder });
            if (hills != null) layers.Add(new LayerInfo { slot = Slot.FarHills, key = hills.key, z = HillsZ, ready = hills.Ready, placeholder = hills.Placeholder });
            if (skyline != null) layers.Add(new LayerInfo { slot = Slot.FarMountains, key = skyline.key, z = SkylineZ, ready = skyline.Ready || (bands != null && bands.SkylineReady), placeholder = skyline.Placeholder });
            foreach (var go in setPieces)
            {
                if (go == null) continue;
                var mv = go.GetComponent<ModelView>();
                layers.Add(new LayerInfo { slot = Slot.FarMountains, key = mv != null ? mv.Key : go.name, z = go.transform.localPosition.z, ready = mv != null && mv.Ready });
            }
            layers.Add(new LayerInfo { slot = Slot.Sky, key = cloudMissing ? "skydome (PlanetBackdrop)" : $"backgrounds/{planetName}/clouds", z = CloudZ, ready = cloudGo != null && cloudGo.activeSelf, placeholder = cloudMissing || (backdrop != null) });
        }

        void Clear()
        {
            rocks?.Destroy(); hills?.Destroy(); skyline?.Destroy();
            rocks = hills = skyline = null;
            foreach (var go in setPieces) if (go != null) Destroy(go);
            setPieces.Clear();
            foreach (var go in foreground.Values) if (go != null) Destroy(go);
            foreground.Clear();
            fgCentre = int.MinValue;
            foreach (var r in new List<string>(sets.Keys)) ReleaseSet(r);
            if (cloudGo != null) Destroy(cloudGo);
            cloudGo = null; cloudRenderer = null; cloudMissing = false;
            if (cloudHandle.IsValid()) { global::Meridian.Art.ArtLoad.Release(cloudHandle); cloudHandle = default; }
            Region = null; Manifest = null;
        }

        void OnDestroy() => Clear();
    }

    /// <summary>U-090: one foreground piece: a ModelView at negative z with shadows off, or a small translucent placeholder card.</summary>
    public sealed class ForegroundPiece : MonoBehaviour
    {
        public string Key { get; private set; }
        public bool Ready => model != null && model.Ready;
        public bool Placeholder { get; private set; }
        ModelView model;
        float born;
        Color tint;

        public void Begin(string key, Color haze)
        {
            Key = key;
            tint = Color.Lerp(new Color(0.25f, 0.3f, 0.22f, 0.8f), haze, 0.15f);
            born = Time.time;
            model = gameObject.AddComponent<ModelView>();
            model.Loaded += () => model.SetShadows(false);
            model.Load(key);
        }

        void LateUpdate()
        {
            if (Ready || Placeholder || model == null || model.Loading || Time.time - born < 1.5f) return;
            Placeholder = true;
            StagePlaceholder.Quad(transform, "Placeholder", 1.2f, 2f, tint);
        }
    }
}
