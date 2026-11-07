using Meridian.Art;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Planets;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.Rendering;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.Space
{
    /// <summary>
    /// Builds the top-down map from SpaceLayout: the Sun and planets as spheroids lit from the Sun (SpaceLit,
    /// U-078: terminator from the real Sun direction, atmosphere halo shell, cloud shell where the art has one),
    /// moons, Saturn's ring mesh, Atmosphere Rings, Gravity Well edges, the dust belt as one mesh and the
    /// asteroid models instanced over it. Lives under SpaceRoot.
    /// </summary>
    public sealed class SpaceWorld : MonoBehaviour
    {
        public PlanetCatalog catalog;
        /// <summary>The v1 PlanetDisc material (SceneAuthoring still assigns it); unused since U-078.</summary>
        public Material discMaterial;
        public Material lineMaterial;
        /// <summary>MERIDIAN/SpaceLit; Resources/SpaceLit when the scene has none.</summary>
        public Material spaceLitMaterial;
        public int beltAsteroids = 900;
        /// <summary>
        /// Asteroid models instanced over the dust belt (U-078). Each is 80–570 triangles (B-090), so the count is
        /// also capped by BeltTriangleBudget; the dust belt keeps the belt dense between them.
        /// </summary>
        public int beltModelRocks = 400;
        public int seed = 1969;

        /// <summary>Triangles the belt rocks may add to the Space view (Bible §11.1 geometry row: 300 k in all).</summary>
        public const int BeltTriangleBudget = 140_000;
        /// <summary>The ring mesh (B-090) is modelled for Saturn's R = 96 u; its outer edge is 2.269 R.</summary>
        public const float RingMeshRadius = 96f, RingOuterR = 2.269f;
        public const float AtmoShellWidth = 0.08f, CloudShellWidth = 0.02f;
        /// <summary>Earth's cloud shell turns once per this many seconds.</summary>
        public const float CloudTurnSeconds = 600f;

        readonly List<BodyInfo> bodies = new List<BodyInfo>();
        readonly List<AsyncOperationHandle<Texture2D>> handles = new List<AsyncOperationHandle<Texture2D>>();
        readonly List<AsyncOperationHandle<GameObject>> prefabHandles = new List<AsyncOperationHandle<GameObject>>();
        readonly List<AsyncOperationHandle<Material>> materialHandles = new List<AsyncOperationHandle<Material>>();
        static Mesh quad;
        public IReadOnlyList<BodyInfo> Bodies => bodies;
        public bool Built { get; private set; }

        static readonly int MainTex = Shader.PropertyToID("_MainTex");
        static readonly int EmissionMap = Shader.PropertyToID("_EmissionMap");
        static readonly int Tint = Shader.PropertyToID("_Tint");
        static readonly int Rotation = Shader.PropertyToID("_Rotation");
        static readonly int AtmoColor = Shader.PropertyToID("_AtmoColor");
        static readonly int AtmoShell = Shader.PropertyToID("_AtmoShell");
        static readonly int Emissive = Shader.PropertyToID("_Emissive");
        static readonly int Ambient = Shader.PropertyToID("_Ambient");
        static readonly int AlphaFromTex = Shader.PropertyToID("_AlphaFromTex");
        static readonly int CullProp = Shader.PropertyToID("_Cull");
        static readonly int RadialProp = Shader.PropertyToID("_Radial"); // U-086: ring sheets sampled radially
        static readonly int RimStrength = Shader.PropertyToID("_RimStrength");

        void Awake()
        {
            if (catalog == null && GameState.Instance != null) catalog = GameState.Instance.catalog;
            if (catalog != null) Build();
        }

        public BodyInfo? Find(string name)
        {
            foreach (var b in bodies) if (b.name == name) return b;
            return null;
        }

        /// <summary>The shared SpaceLit material: the scene's, or Resources/SpaceLit (its asset keeps the shader in builds).</summary>
        public Material SpaceLit
        {
            get
            {
                if (spaceLitMaterial == null) spaceLitMaterial = Resources.Load<Material>("SpaceLit");
                if (spaceLitMaterial == null)
                {
                    var shader = Shader.Find("MERIDIAN/SpaceLit");
                    spaceLitMaterial = shader != null ? new Material(shader) { name = "SpaceLit (runtime)" } : lineMaterial;
                }
                return spaceLitMaterial;
            }
        }

        public void Build()
        {
            if (Built) return;
            bodies.AddRange(SpaceLayout.Build(catalog));
            foreach (var b in bodies)
            {
                var go = new GameObject(b.name);
                go.transform.SetParent(transform, false);
                go.transform.localPosition = b.position;
                AddSphere(go.transform, b);
                if (b.landable) AddCircle(go.transform, "AtmosphereRing", b.RingRadius, new Color(0.55f, 0.8f, 1f, 0.55f), 0.004f);
                AddCircle(go.transform, "GravityWell", b.WellRadius,
                    b.isSun ? new Color(1f, 0.55f, 0.2f, 0.25f) : new Color(1f, 1f, 1f, 0.12f), 0.0025f);
                if (b.isSun)
                    AddCircle(go.transform, "KillZone", WellMath.SunKillFactor * b.radius, new Color(1f, 0.3f, 0.1f, 0.5f), 0.003f);
            }
            AddBelt();
            Built = true;
        }

        // ---------- planets as spheroids (U-078) ----------

        MeshRenderer cloudShell;
        MaterialPropertyBlock cloudBlock;
        float cloudTurn;

        /// <summary>
        /// The body as a spheroid named "Disc" (its surface, lit by SpaceLit from the Sun), plus an atmosphere halo
        /// shell for bodies with an atmosphere and a cloud shell where planets/&lt;name&gt;/clouds exists.
        /// </summary>
        void AddSphere(Transform parent, BodyInfo b)
        {
            ProbeDisc(parent, b); // U-103 (D-098): where the painted disc exists it replaces the spheroid, its shells and Saturn's ring mesh
            if (b.isSun) ProbeSunRig(parent, b); // U-116 (D-123): the painted Sun rig replaces the lit spheroid where its sheet exists
            var mr = AddShell(parent, "Disc", 2f * b.radius, 10, out var block);
            block.SetFloat(Emissive, b.isSun ? 1f : 0f);
            block.SetFloat(Ambient, 0.06f);
            block.SetColor(AtmoColor, b.isSun ? new Color(1f, 0.75f, 0.35f, 1f) : AtmosphereColor(b.name));
            block.SetColor(Tint, b.parent != null ? new Color(0.62f, 0.6f, 0.58f) : Color.white);
            mr.SetPropertyBlock(block);

            if (b.parent != null)
            {
                // Moons: their surface art where it exists (B-017: luna), flat grey otherwise.
                LoadIfExists($"planets/{b.name}/surface", tex =>
                {
                    if (mr == null) return;
                    mr.GetPropertyBlock(block);
                    block.SetTexture(MainTex, tex);
                    block.SetColor(Tint, Color.white);
                    mr.SetPropertyBlock(block);
                });
                return;
            }
            AddGlow(parent, b);
            if (b.name == "saturn") AddRings(parent, b);
            var h = ArtLoad.Asset<Texture2D>($"planets/{b.name}/surface");
            handles.Add(h);
            h.Completed += op =>
            {
                if (mr == null || op.Status != AsyncOperationStatus.Succeeded) return;
                mr.GetPropertyBlock(block);
                block.SetTexture(MainTex, op.Result);
                mr.SetPropertyBlock(block);
            };
            if (b.isSun) return;

            var atmo = AtmosphereColor(b.name);
            if (atmo.a > 0.15f)
            {
                var shell = AddShell(parent, "Atmo", 2f * b.radius * (1f + AtmoShellWidth), 12, out var ab);
                ab.SetFloat(AtmoShell, 1f);
                ab.SetColor(AtmoColor, atmo);
                shell.SetPropertyBlock(ab);
                Shells.Add(shell);
            }
            LoadIfExists($"planets/{b.name}/clouds", tex =>
            {
                if (parent == null) return;
                var clouds = AddShell(parent, "Clouds", 2f * b.radius * (1f + CloudShellWidth), 11, out var cb);
                cb.SetTexture(MainTex, tex);
                cb.SetFloat(AlphaFromTex, 2f);
                cb.SetFloat(Ambient, 0.06f);
                cb.SetFloat(RimStrength, 0f);
                cb.SetColor(AtmoColor, atmo);
                clouds.SetPropertyBlock(cb);
                Shells.Add(clouds);
                if (b.name == "earth") { cloudShell = clouds; cloudBlock = cb; }
            });
        }

        // ---------- painted discs (U-103, D-098, B-119) ----------

        /// <summary>The bodies drawn as disc sprites (tests and captures).</summary>
        public readonly List<DiscSprite> Discs = new List<DiscSprite>();
        public SpriteRenderer RingsBack { get; private set; }
        public SpriteRenderer RingsFront { get; private set; }
        /// <summary>Saturn's ring wobble from planets/saturn/disc_rig.json (null until it loads).</summary>
        public RingWobble.Wobble SaturnWobble { get; private set; }
        readonly HashSet<string> discBodies = new HashSet<string>();
        DiscSprite ringDisc;
        AsyncOperationHandle<TextAsset> rigHandle;

        /// <summary>The disc sheet key of a body: planets/&lt;name&gt;/disc, or planets/&lt;parent&gt;/&lt;name&gt; for a moon (D-098).</summary>
        public static string DiscKey(BodyInfo b) => b.parent != null ? $"planets/{b.parent}/{b.name}" : $"planets/{b.name}/disc";

        /// <summary>U-116: the Sun's rig once planets/sun/disc_rig is found (null before, and where the sheet is missing).</summary>
        public SunView Sun { get; private set; }

        /// <summary>U-116 (D-123): where planets/sun/disc_rig exists the rig replaces the Sun's spheroid (the glow and the light stay).</summary>
        void ProbeSunRig(Transform parent, BodyInfo b)
        {
            var locations = Addressables.LoadResourceLocationsAsync(SunView.Key);
            locations.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(loc);
                if (!exists || parent == null || this == null) return;
                var old = parent.Find("Disc");
                if (old != null)
                {
                    var mr = old.GetComponent<MeshRenderer>();
                    if (mr != null) Shells.Remove(mr);
                    Destroy(old.gameObject);
                }
                var go = new GameObject("SunRig");
                go.transform.SetParent(parent, false);
                Sun = go.AddComponent<SunView>();
                Sun.Load(SunView.Key, b.radius, 10);
            };
        }

        /// <summary>Where planets/&lt;name&gt;/disc exists (art or placeholder), the disc sprite replaces the spheroid and its shells.</summary>
        void ProbeDisc(Transform parent, BodyInfo b)
        {
            var key = DiscKey(b); // a moon's sheet lives under its parent (planets/earth/luna, D-098); a planet's at planets/<name>/disc
            var locations = Addressables.LoadResourceLocationsAsync(key);
            locations.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(loc);
                if (!exists || parent == null) return;
                discBodies.Add(b.name);
                foreach (var n in new[] { "Disc", "Atmo", "Clouds", "Rings" })
                {
                    var old = parent.Find(n);
                    if (old == null) continue;
                    var mr = old.GetComponent<MeshRenderer>();
                    if (mr != null) Shells.Remove(mr);
                    if (n == "Rings") { Rings = null; RingsReady = false; }
                    if (n == "Clouds" && cloudShell != null && cloudShell.transform == old) cloudShell = null;
                    Destroy(old.gameObject);
                }
                var go = new GameObject("Disc");
                go.transform.SetParent(parent, false);
                var disc = go.AddComponent<DiscSprite>();
                disc.Load(key, b.radius, 10);
                Discs.Add(disc);
                if (b.name == "saturn") AddRingSprites(parent, disc);
            };
        }

        /// <summary>Saturn's painted rings: rings_back behind the disc, rings_front in front, both at the disc's scale, breathing per disc_rig.json.</summary>
        void AddRingSprites(Transform parent, DiscSprite disc)
        {
            ringDisc = disc;
            RingsBack = RingSprite(parent, "planets/saturn/rings_back", 9);
            RingsFront = RingSprite(parent, "planets/saturn/rings_front", 11);
            rigHandle = ArtLoad.Asset<TextAsset>("planets/saturn/disc_rig/json");
            rigHandle.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                SaturnWobble = RingWobble.Parse(op.Result.text)?.wobble;
            };
        }

        SpriteRenderer RingSprite(Transform parent, string key, int order)
        {
            var go = new GameObject(key.Substring(key.LastIndexOf('/') + 1));
            go.transform.SetParent(parent, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = order;
            var mat = Meridian.Rendering.ArtMaterials.MaterialFor(key);
            if (mat != null) sr.sharedMaterial = mat;
            var h = ArtLoad.Asset<IList<Sprite>>(key);
            spriteHandles.Add(h);
            h.Completed += op =>
            {
                if (sr == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                sr.sprite = op.Result[0];
                if (RingsBack != null && RingsFront != null && RingsBack.sprite != null && RingsFront.sprite != null) RingsReady = true; // U-103: both painted rings in
            };
            return sr;
        }

        void StepRings()
        {
            if (ringDisc == null || !ringDisc.Ready || RingsBack == null || RingsFront == null) return;
            var (sy, rot) = RingWobble.At(Time.time, SaturnWobble);
            float s = ringDisc.Scale;
            var scale = new Vector3(s, s * sy, 1f);
            var q = Quaternion.Euler(0f, 0f, rot);
            RingsBack.transform.localScale = scale; RingsBack.transform.localRotation = q;
            RingsFront.transform.localScale = scale; RingsFront.transform.localRotation = q;
        }

        /// <summary>Atmosphere and cloud shells, for tests and captures.</summary>
        public readonly List<MeshRenderer> Shells = new List<MeshRenderer>();

        MeshRenderer AddShell(Transform parent, string name, float diameter, int order, out MaterialPropertyBlock block)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localScale = Vector3.one * diameter;
            go.AddComponent<MeshFilter>().sharedMesh = SpaceMeshes.Spheroid();
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = SpaceLit;
            mr.shadowCastingMode = ShadowCastingMode.Off;
            mr.receiveShadows = false;
            mr.sortingOrder = order;
            block = new MaterialPropertyBlock();
            return mr;
        }

        void Update()
        {
            if (cloudShell != null)
            {
                cloudTurn = (cloudTurn + Time.deltaTime / CloudTurnSeconds) % 1f;
                cloudBlock.SetFloat(Rotation, cloudTurn);
                cloudShell.SetPropertyBlock(cloudBlock);
            }
            StepRings(); // U-103: Saturn's painted rings breathe on the beat
            if (beltReady && SystemInfo.graphicsDeviceType != GraphicsDeviceType.Null) DrawBelt(); // no device under -nographics tests
        }

        /// <summary>Glow width in R (BLENDER handoffs): planets 2.56 R, the Sun 3.2 R.</summary>
        public const float PlanetGlowWidth = 2.56f, SunGlowWidth = 3.2f;
        readonly List<SpriteRenderer> glows = new List<SpriteRenderer>();
        public IReadOnlyList<SpriteRenderer> Glows => glows;

        /// <summary>planets/&lt;name&gt;/glow behind the disc, only where that art exists.</summary>
        void AddGlow(Transform parent, BodyInfo b)
        {
            var key = $"planets/{b.name}/glow";
            var locations = Addressables.LoadResourceLocationsAsync(key);
            locations.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(loc);
                if (!exists || parent == null) return;
                var go = new GameObject("Glow");
                go.transform.SetParent(parent, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sharedMaterial = lineMaterial; // unlit: a glow isn't lit by the scene
                sr.sortingOrder = 8;               // behind the disc and, on Saturn, behind rings_back (U-103)
                glows.Add(sr);
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                h.Completed += op =>
                {
                    if (sr == null || op.Status != AsyncOperationStatus.Succeeded || op.Result.Count == 0) return;
                    sr.sprite = op.Result[0];
                    float width = (b.isSun ? SunGlowWidth : PlanetGlowWidth) * b.radius;
                    go.transform.localScale = Vector3.one * (width / sr.sprite.bounds.size.x);
                };
                spriteHandles.Add(h);
            };
        }

        readonly List<AsyncOperationHandle<IList<Sprite>>> spriteHandles = new List<AsyncOperationHandle<IList<Sprite>>>();

        void LoadIfExists(string key, System.Action<Texture2D> done)
        {
            var locations = Addressables.LoadResourceLocationsAsync(key);
            locations.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(loc);
                if (!exists || this == null) return;
                var h = ArtLoad.Asset<Texture2D>(key);
                handles.Add(h);
                h.Completed += op => { if (op.Status == AsyncOperationStatus.Succeeded) done(op.Result); };
            };
        }

        /// <summary>The key's model prefab (a .glb under Art/) when it exists; null otherwise.</summary>
        void LoadModelIfExists(string key, System.Action<GameObject> done)
        {
            var locations = Addressables.LoadResourceLocationsAsync(key, typeof(GameObject));
            locations.Completed += loc =>
            {
                IResourceLocation glb = null;
                if (loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null)
                    foreach (var l in loc.Result)
                        if (l.InternalId != null && l.InternalId.EndsWith(".glb", System.StringComparison.OrdinalIgnoreCase)) { glb = l; break; }
                global::Meridian.Art.ArtLoad.Release(loc);
                if (glb == null || this == null) { done(null); return; }
                var h = ArtLoad.Asset<GameObject>(glb, key);
                prefabHandles.Add(h);
                h.Completed += op => done(op.Status == AsyncOperationStatus.Succeeded ? op.Result : null);
            };
        }

        /// <summary>The key's generated material (Generated/Models/&lt;key&gt;.mat) for its maps; null when there is none.</summary>
        void LoadGeneratedMaterial(string key, System.Action<Material> done)
        {
            var locations = Addressables.LoadResourceLocationsAsync(key, typeof(Material));
            locations.Completed += loc =>
            {
                IResourceLocation mat = null;
                if (loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null)
                    foreach (var l in loc.Result)
                        if (l.InternalId != null && l.InternalId.EndsWith(".mat", System.StringComparison.OrdinalIgnoreCase)) { mat = l; break; }
                global::Meridian.Art.ArtLoad.Release(loc);
                if (mat == null || this == null) { done(null); return; }
                var h = ArtLoad.Asset<Material>(mat, key);
                materialHandles.Add(h);
                h.Completed += op => done(op.Status == AsyncOperationStatus.Succeeded ? op.Result : null);
            };
        }

        /// <summary>A SpaceLit material carrying a generated URP/Lit material's albedo and emission maps.</summary>
        public Material SpaceLitFrom(Material generated, string name)
        {
            var m = new Material(SpaceLit) { name = name };
            if (generated != null)
            {
                if (generated.HasProperty("_BaseMap")) m.SetTexture(MainTex, generated.GetTexture("_BaseMap"));
                if (generated.HasProperty("_EmissionMap")) m.SetTexture(EmissionMap, generated.GetTexture("_EmissionMap"));
            }
            m.SetFloat(Ambient, 0.25f);
            m.SetFloat(RimStrength, 0f);
            m.enableInstancing = true;
            return m;
        }

        /// <summary>
        /// Saturn's rings (B-090): planets/saturn/ring_mesh, a flat annulus 1.239–2.269 R modelled for R = 96 in the
        /// horizontal (XZ) plane, turned into the view plane and scaled to Saturn's R; the texture is the
        /// planets/saturn/rings sheet (colour + alpha, the shadow side in the art), drawn unlit and double-sided.
        /// </summary>
        public MeshRenderer Rings { get; private set; }
        public bool RingsReady { get; private set; }

        void AddRings(Transform parent, BodyInfo b)
        {
            LoadModelIfExists("planets/saturn/ring_mesh", prefab =>
            {
                if (prefab == null || parent == null || discBodies.Contains(b.name)) return; // U-103: the painted rings took over
                var go = Instantiate(prefab, parent, false);
                go.name = "Rings";
                go.transform.localPosition = Vector3.zero;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                go.transform.localScale = Vector3.one * (b.radius / RingMeshRadius);
                var mr = go.GetComponentInChildren<MeshRenderer>();
                if (mr == null) return;
                var mat = SpaceLitFrom(null, "Rings");
                mat.SetFloat(Emissive, 1f);
                mat.SetFloat(AlphaFromTex, 1f);
                mat.SetFloat(CullProp, 0f);
                mat.SetFloat(RadialProp, 1f);
                mr.sharedMaterial = mat;
                mr.shadowCastingMode = ShadowCastingMode.Off;
                mr.receiveShadows = false;
                mr.sortingOrder = 12;
                Rings = mr;
                var h = ArtLoad.Asset<IList<Sprite>>("planets/saturn/rings");
                spriteHandles.Add(h);
                h.Completed += op =>
                {
                    if (mr == null || op.Status != AsyncOperationStatus.Succeeded || op.Result.Count == 0) return;
                    mat.SetTexture(MainTex, op.Result[0].texture);
                    RingsReady = true;
                };
            });
        }

        // ---------- asteroid belt from the models (U-034 → U-078) ----------

        public const int AsteroidKinds = 6;
        public const int ClusterSize = 15;
        public const float ClusterSpread = 35f;
        readonly List<Vector2> beltClusters = new List<Vector2>();
        /// <summary>Centers of the asteroid clumps (captures frame one).</summary>
        public IReadOnlyList<Vector2> BeltClusters => beltClusters;

        /// <summary>One asteroid model and its instances over the belt: one instanced draw per kind.</summary>
        public sealed class BeltKind
        {
            public string key;
            public Mesh mesh;
            public Material material;
            public Matrix4x4[] matrices;
            public int count;
            public int triangles;
        }
        /// <summary>Belt kinds with their art loaded (props/space/asteroid_01..06); empty until the models arrive.</summary>
        public readonly List<BeltKind> Belt = new List<BeltKind>();
        /// <summary>Rocks placed over the belt once the models are in.</summary>
        public int BeltRocks { get; private set; }
        public bool BeltReady => beltReady;
        bool beltReady;
        MeshRenderer beltFallback;
        RenderParams beltParams;

        void LoadBeltArt()
        {
            var kinds = new BeltKind[AsteroidKinds];
            int pending = AsteroidKinds * 2;
            for (int k = 0; k < AsteroidKinds; k++)
            {
                int kind = k;
                string key = $"props/space/asteroid_{kind + 1:00}";
                kinds[kind] = new BeltKind { key = key };
                LoadModelIfExists(key, prefab =>
                {
                    var mf = prefab != null ? prefab.GetComponentInChildren<MeshFilter>() : null;
                    if (mf != null && mf.sharedMesh != null) { kinds[kind].mesh = mf.sharedMesh; kinds[kind].triangles = (int)(mf.sharedMesh.GetIndexCount(0) / 3); }
                    if (--pending == 0) BuildBeltArt(kinds);
                });
                LoadGeneratedMaterial(key, generated =>
                {
                    kinds[kind].material = SpaceLitFrom(generated, "Belt " + key);
                    if (--pending == 0) BuildBeltArt(kinds);
                });
            }
        }

        /// <summary>
        /// The same belt (positions, sizes, rotations from the seed) with the asteroid models: each kind is one
        /// instanced draw (Graphics.RenderMeshInstanced), the rock count capped by BeltTriangleBudget.
        /// </summary>
        void BuildBeltArt(BeltKind[] kinds)
        {
            if (this == null) return;
            int loaded = 0, triSum = 0;
            foreach (var k in kinds) if (k.mesh != null && k.material != null) { loaded++; triSum += k.triangles; }
            if (loaded == 0) return; // keep the flat belt
            int rocks = Mathf.Min(beltModelRocks, BeltTriangleBudget / Mathf.Max(1, triSum / loaded));
            var counts = new int[AsteroidKinds];
            var rng = new System.Random(seed + 7);
            int clusters = Mathf.Max(1, rocks / ClusterSize);
            beltClusters.Clear();
            for (int c = 0; c < clusters; c++)
            {
                float ca = (float)rng.NextDouble() * Mathf.PI * 2f;
                float cr = Mathf.Lerp(SpaceLayout.BeltInner + ClusterSpread, SpaceLayout.BeltOuter - ClusterSpread, (float)rng.NextDouble());
                beltClusters.Add(new Vector2(Mathf.Cos(ca) * cr, Mathf.Sin(ca) * cr));
            }
            var placed = new List<(int kind, Matrix4x4 m)>(rocks);
            for (int i = 0; i < rocks; i++)
            {
                var center = beltClusters[i % clusters];
                float oa = (float)rng.NextDouble() * Mathf.PI * 2f;
                float od = ClusterSpread * Mathf.Sqrt((float)rng.NextDouble());
                var p = new Vector2(center.x + Mathf.Cos(oa) * od, center.y + Mathf.Sin(oa) * od);
                float size = Mathf.Lerp(2f, 12f, (float)(rng.NextDouble() * rng.NextDouble())); // u across (the ship is 4)
                var rot = Quaternion.Euler((float)rng.NextDouble() * 360f, (float)rng.NextDouble() * 360f, (float)rng.NextDouble() * 360f);
                int kind = rng.Next(AsteroidKinds);
                while (kinds[kind].mesh == null || kinds[kind].material == null) kind = (kind + 1) % AsteroidKinds;
                var ext = kinds[kind].mesh.bounds.size;
                float scale = size / Mathf.Max(ext.x, Mathf.Max(ext.y, ext.z));
                placed.Add((kind, Matrix4x4.TRS(new Vector3(p.x, p.y, 0f), rot, Vector3.one * scale)));
                counts[kind]++;
            }
            Belt.Clear();
            for (int k = 0; k < AsteroidKinds; k++)
            {
                var kind = kinds[k];
                if (kind.mesh == null || kind.material == null || counts[k] == 0) continue;
                kind.matrices = new Matrix4x4[counts[k]];
                kind.count = 0;
                Belt.Add(kind);
            }
            foreach (var (kind, m) in placed) kinds[kind].matrices[kinds[kind].count++] = m;
            BeltRocks = rocks;
            float extent = SpaceLayout.BeltOuter + 20f;
            beltParams = new RenderParams
            {
                worldBounds = new Bounds(transform.position, new Vector3(2f * extent, 2f * extent, 40f)),
                shadowCastingMode = ShadowCastingMode.Off,
                receiveShadows = false,
                layer = gameObject.layer,
            };
            beltReady = true;
            // The flat belt stays as fine dust between the rocks (one more draw call).
        }

        /// <summary>One instanced draw per kind, every frame; no allocation (the matrices are fixed).</summary>
        void DrawBelt()
        {
            for (int i = 0; i < Belt.Count; i++)
            {
                var kind = Belt[i];
                beltParams.material = kind.material;
                Graphics.RenderMeshInstanced(beltParams, kind.mesh, 0, kind.matrices, kind.count);
            }
        }

        static Color AtmosphereColor(string name) => name switch
        {
            "earth" => new Color(0.45f, 0.65f, 1f, 0.9f),
            "mars" => new Color(0.95f, 0.65f, 0.45f, 0.5f),
            "venus" => new Color(1f, 0.9f, 0.6f, 0.9f),
            "mercury" => new Color(0.6f, 0.6f, 0.6f, 0.1f),
            "uranus" or "neptune" => new Color(0.5f, 0.85f, 1f, 0.8f),
            _ => new Color(1f, 0.92f, 0.8f, 0.6f),
        };

        void AddCircle(Transform parent, string name, float radius, Color color, float widthOfRadius)
        {
            const int segments = 128;
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var lr = go.AddComponent<LineRenderer>();
            lr.sharedMaterial = lineMaterial;
            lr.useWorldSpace = false;
            lr.loop = true;
            lr.positionCount = segments;
            lr.widthMultiplier = Mathf.Max(0.6f, radius * widthOfRadius);
            lr.startColor = lr.endColor = color;
            lr.sortingOrder = 5;
            var pts = new Vector3[segments];
            for (int i = 0; i < segments; i++)
            {
                float a = i * Mathf.PI * 2f / segments;
                pts[i] = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f) * radius;
            }
            lr.SetPositions(pts);
        }

        /// <summary>The asteroid belt as one mesh (one draw call): small irregular quads, 1–6 u.</summary>
        void AddBelt()
        {
            var rng = new System.Random(seed);
            int n = beltAsteroids;
            var verts = new Vector3[n * 4];
            var colors = new Color32[n * 4];
            var tris = new int[n * 6];
            for (int i = 0; i < n; i++)
            {
                float a = (float)rng.NextDouble() * Mathf.PI * 2f;
                float r = Mathf.Lerp(SpaceLayout.BeltInner, SpaceLayout.BeltOuter, (float)rng.NextDouble());
                float s = Mathf.Lerp(1f, 6f, (float)(rng.NextDouble() * rng.NextDouble())) * 0.5f;
                float rot = (float)rng.NextDouble() * Mathf.PI;
                var c = new Vector3(Mathf.Cos(a) * r, Mathf.Sin(a) * r, 0f);
                for (int k = 0; k < 4; k++)
                {
                    float ang = rot + k * Mathf.PI * 0.5f;
                    float jitter = 0.75f + 0.5f * (float)rng.NextDouble();
                    verts[i * 4 + k] = c + new Vector3(Mathf.Cos(ang), Mathf.Sin(ang), 0f) * s * jitter;
                    byte g = (byte)(90 + rng.Next(60));
                    colors[i * 4 + k] = new Color32(g, (byte)(g * 0.92f), (byte)(g * 0.85f), 255);
                }
                tris[i * 6] = i * 4; tris[i * 6 + 1] = i * 4 + 1; tris[i * 6 + 2] = i * 4 + 2;
                tris[i * 6 + 3] = i * 4; tris[i * 6 + 4] = i * 4 + 2; tris[i * 6 + 5] = i * 4 + 3;
            }
            var mesh = new Mesh { name = "Belt" };
            mesh.vertices = verts;
            mesh.colors32 = colors;
            mesh.triangles = tris;
            mesh.RecalculateBounds();
            var go = new GameObject("Belt");
            go.transform.SetParent(transform, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = lineMaterial;
            mr.sortingOrder = 4;
            beltFallback = mr; // fine dust under the rocks
            LoadBeltArt();
        }

        public static Mesh Quad()
        {
            if (quad != null) return quad;
            quad = new Mesh { name = "DiscQuad" };
            quad.vertices = new[] { new Vector3(-0.5f, -0.5f), new Vector3(0.5f, -0.5f), new Vector3(0.5f, 0.5f), new Vector3(-0.5f, 0.5f) };
            quad.uv = new[] { new Vector2(0, 0), new Vector2(1, 0), new Vector2(1, 1), new Vector2(0, 1) };
            quad.triangles = new[] { 0, 2, 1, 0, 3, 2 };
            quad.RecalculateBounds();
            return quad;
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            foreach (var h in spriteHandles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            foreach (var h in prefabHandles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            foreach (var h in materialHandles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            if (rigHandle.IsValid()) global::Meridian.Art.ArtLoad.Release(rigHandle);
        }
    }
}
