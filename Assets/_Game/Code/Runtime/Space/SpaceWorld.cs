using System.Collections.Generic;
using Meridian.Core;
using Meridian.Planets;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Space
{
    /// <summary>
    /// Builds the top-down map from SpaceLayout: Sun and planet discs (PlanetDisc shader), moons,
    /// Atmosphere Rings, Gravity Well edges, and the belt as one mesh. Lives under SpaceRoot.
    /// </summary>
    public sealed class SpaceWorld : MonoBehaviour
    {
        public PlanetCatalog catalog;
        public Material discMaterial;
        public Material lineMaterial;
        public int beltAsteroids = 900;
        /// <summary>Asteroids in the art belt (U-034): dense enough to read as a belt at flight zoom; still 6 draw calls.</summary>
        public int beltArtAsteroids = 6000;
        public int seed = 1969;

        readonly List<BodyInfo> bodies = new List<BodyInfo>();
        readonly List<AsyncOperationHandle<Texture2D>> handles = new List<AsyncOperationHandle<Texture2D>>();
        static Mesh quad;
        public IReadOnlyList<BodyInfo> Bodies => bodies;
        public bool Built { get; private set; }

        static readonly int MainTex = Shader.PropertyToID("_MainTex");
        static readonly int Tint = Shader.PropertyToID("_Tint");
        static readonly int SunDir = Shader.PropertyToID("_SunDir");
        static readonly int AtmoColor = Shader.PropertyToID("_AtmoColor");
        static readonly int AtmoWidth = Shader.PropertyToID("_AtmoWidth");
        static readonly int Emissive = Shader.PropertyToID("_Emissive");

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

        public void Build()
        {
            if (Built) return;
            bodies.AddRange(SpaceLayout.Build(catalog));
            foreach (var b in bodies)
            {
                var go = new GameObject(b.name);
                go.transform.SetParent(transform, false);
                go.transform.localPosition = b.position;
                AddDisc(go.transform, b);
                if (b.landable) AddCircle(go.transform, "AtmosphereRing", b.RingRadius, new Color(0.55f, 0.8f, 1f, 0.55f), 0.004f);
                AddCircle(go.transform, "GravityWell", b.WellRadius,
                    b.isSun ? new Color(1f, 0.55f, 0.2f, 0.25f) : new Color(1f, 1f, 1f, 0.12f), 0.0025f);
                if (b.isSun)
                    AddCircle(go.transform, "KillZone", WellMath.SunKillFactor * b.radius, new Color(1f, 0.3f, 0.1f, 0.5f), 0.003f);
            }
            AddBelt();
            Built = true;
        }

        void AddDisc(Transform parent, BodyInfo b)
        {
            const float atmo = 0.08f;
            var go = new GameObject("Disc");
            go.transform.SetParent(parent, false);
            go.transform.localScale = Vector3.one * (2f * b.radius * (1f + atmo));
            go.AddComponent<MeshFilter>().sharedMesh = Quad();
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = discMaterial;
            mr.sortingOrder = 10;

            var block = new MaterialPropertyBlock();
            var dir = b.isSun ? Vector2.left : (-b.position).normalized;
            block.SetVector(SunDir, new Vector4(dir.x, dir.y, 0.35f, 0f));
            block.SetFloat(AtmoWidth, atmo);
            block.SetFloat(Emissive, b.isSun ? 1f : 0f);
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
            var h = Addressables.LoadAssetAsync<Texture2D>($"planets/{b.name}/surface");
            handles.Add(h);
            h.Completed += op =>
            {
                if (mr == null || op.Status != AsyncOperationStatus.Succeeded) return;
                mr.GetPropertyBlock(block);
                block.SetTexture(MainTex, op.Result);
                mr.SetPropertyBlock(block);
            };
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
                Addressables.Release(loc);
                if (!exists || parent == null) return;
                var go = new GameObject("Glow");
                go.transform.SetParent(parent, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sharedMaterial = lineMaterial; // unlit: a glow isn't lit by the scene
                sr.sortingOrder = 9;               // just behind the disc
                glows.Add(sr);
                var h = Addressables.LoadAssetAsync<IList<Sprite>>(key);
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
                Addressables.Release(loc);
                if (!exists || this == null) return;
                var h = Addressables.LoadAssetAsync<Texture2D>(key);
                handles.Add(h);
                h.Completed += op => { if (op.Status == AsyncOperationStatus.Succeeded) done(op.Result); };
            };
        }

        /// <summary>
        /// Saturn's rings (B-018 handoff): the 1024 px sheet's A-ring outer edge is r = 500 px and Saturn's
        /// radius is 220.4 px, so the sheet spans 1024 / 220.4 × R in the world (446 u at R 96).
        /// </summary>
        public const float RingSheetPx = 1024f, RingSaturnRadiusPx = 220.4f;
        public SpriteRenderer Rings { get; private set; }

        void AddRings(Transform parent, BodyInfo b)
        {
            const string key = "planets/saturn/rings";
            var locations = Addressables.LoadResourceLocationsAsync(key);
            locations.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                Addressables.Release(loc);
                if (!exists || parent == null) return;
                var go = new GameObject("Rings");
                go.transform.SetParent(parent, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sharedMaterial = lineMaterial; // unlit like the discs' day side; the shadow side is in the art
                sr.sortingOrder = 11;              // over the disc's atmosphere rim; the ring's hole leaves the globe clear
                Rings = sr;
                var h = Addressables.LoadAssetAsync<IList<Sprite>>(key);
                spriteHandles.Add(h);
                h.Completed += op =>
                {
                    if (sr == null || op.Status != AsyncOperationStatus.Succeeded || op.Result.Count == 0) return;
                    sr.sprite = op.Result[0];
                    float width = RingSheetPx / RingSaturnRadiusPx * b.radius;
                    go.transform.localScale = Vector3.one * (width / sr.sprite.bounds.size.x);
                };
            };
        }

        // ---------- asteroid belt from art (U-034) ----------

        public const int AsteroidKinds = 6;
        public const int ClusterSize = 15;
        public const float ClusterSpread = 35f;
        readonly List<Vector2> beltClusters = new List<Vector2>();
        /// <summary>Centers of the asteroid clumps (captures frame one).</summary>
        public IReadOnlyList<Vector2> BeltClusters => beltClusters;
        /// <summary>Belt meshes built from props/space/asteroid_01..06 (one per kind: ≤ 6 draw calls). Empty until the art loads.</summary>
        public readonly List<MeshRenderer> BeltArt = new List<MeshRenderer>();
        MeshRenderer beltFallback;

        void LoadBeltArt()
        {
            var sprites = new Sprite[AsteroidKinds];
            int pending = AsteroidKinds;
            for (int k = 0; k < AsteroidKinds; k++)
            {
                int kind = k;
                string key = $"props/space/asteroid_{kind + 1:00}";
                var locations = Addressables.LoadResourceLocationsAsync(key);
                locations.Completed += loc =>
                {
                    bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                    Addressables.Release(loc);
                    if (!exists) { if (--pending == 0) BuildBeltArt(sprites); return; }
                    var h = Addressables.LoadAssetAsync<IList<Sprite>>(key);
                    spriteHandles.Add(h);
                    h.Completed += op =>
                    {
                        if (op.Status == AsyncOperationStatus.Succeeded && op.Result.Count > 0) sprites[kind] = op.Result[0];
                        if (--pending == 0) BuildBeltArt(sprites);
                    };
                };
            }
        }

        /// <summary>
        /// The same belt (positions, sizes, rotations from the seed) drawn with the asteroid sprites: each
        /// kind is one mesh of its sprite's geometry instanced at varied rotation and scale.
        /// </summary>
        void BuildBeltArt(Sprite[] sprites)
        {
            if (this == null) return;
            int kinds = 0;
            foreach (var s in sprites) if (s != null) kinds++;
            if (kinds == 0) return; // keep the flat belt
            var verts = new List<Vector3>[AsteroidKinds];
            var uvs = new List<Vector2>[AsteroidKinds];
            var colors = new List<Color32>[AsteroidKinds];
            var tris = new List<int>[AsteroidKinds];
            for (int k = 0; k < AsteroidKinds; k++) { verts[k] = new List<Vector3>(); uvs[k] = new List<Vector2>(); colors[k] = new List<Color32>(); tris[k] = new List<int>(); }

            var rng = new System.Random(seed + 7);
            // Clumps: an even spread over 18 M u² shows ~8 rocks per screen; clusters read as a belt.
            int clusters = Mathf.Max(1, beltArtAsteroids / ClusterSize);
            beltClusters.Clear();
            for (int c = 0; c < clusters; c++)
            {
                float ca = (float)rng.NextDouble() * Mathf.PI * 2f;
                float cr = Mathf.Lerp(SpaceLayout.BeltInner + ClusterSpread, SpaceLayout.BeltOuter - ClusterSpread, (float)rng.NextDouble());
                beltClusters.Add(new Vector2(Mathf.Cos(ca) * cr, Mathf.Sin(ca) * cr));
            }
            for (int i = 0; i < beltArtAsteroids; i++)
            {
                var center = beltClusters[i % clusters];
                float oa = (float)rng.NextDouble() * Mathf.PI * 2f;
                float od = ClusterSpread * Mathf.Sqrt((float)rng.NextDouble());
                float a = Mathf.Atan2(center.y + Mathf.Sin(oa) * od, center.x + Mathf.Cos(oa) * od);
                float r = new Vector2(center.x + Mathf.Cos(oa) * od, center.y + Mathf.Sin(oa) * od).magnitude;
                float size = Mathf.Lerp(2f, 12f, (float)(rng.NextDouble() * rng.NextDouble())); // u across (the ship is 4)
                float rot = (float)rng.NextDouble() * 360f;
                int kind = rng.Next(AsteroidKinds);
                byte shade = (byte)(185 + rng.Next(70));
                while (sprites[kind] == null) kind = (kind + 1) % AsteroidKinds;
                var s = sprites[kind];
                float scale = size / Mathf.Max(s.bounds.size.x, s.bounds.size.y);
                var m = Matrix4x4.TRS(new Vector3(Mathf.Cos(a) * r, Mathf.Sin(a) * r, 0f), Quaternion.Euler(0f, 0f, rot), Vector3.one * scale);
                int baseIndex = verts[kind].Count;
                var sv = s.vertices;
                var su = s.uv;
                for (int v = 0; v < sv.Length; v++)
                {
                    verts[kind].Add(m.MultiplyPoint3x4(sv[v]));
                    uvs[kind].Add(su[v]);
                    colors[kind].Add(new Color32(shade, shade, shade, 255));
                }
                foreach (var t in s.triangles) tris[kind].Add(baseIndex + t);
            }

            var mat = Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.lit : lineMaterial;
            var block = new MaterialPropertyBlock();
            var secondary = new SecondarySpriteTexture[4];
            for (int k = 0; k < AsteroidKinds; k++)
            {
                if (sprites[k] == null || verts[k].Count == 0) continue;
                var mesh = new Mesh { name = "BeltArt" + (k + 1), indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
                mesh.SetVertices(verts[k]);
                mesh.SetUVs(0, uvs[k]);
                mesh.SetColors(colors[k]);
                mesh.SetTriangles(tris[k], 0);
                mesh.RecalculateBounds();
                var go = new GameObject("BeltArt" + (k + 1));
                go.transform.SetParent(transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterial = mat;
                mr.sortingOrder = 4;
                block.Clear();
                block.SetTexture(MainTex, sprites[k].texture);
                int n = sprites[k].GetSecondaryTextures(secondary);
                for (int t = 0; t < n; t++) if (secondary[t].name == "_NormalMap") block.SetTexture("_NormalMap", secondary[t].texture);
                mr.SetPropertyBlock(block);
                BeltArt.Add(mr);
            }
            // The flat belt stays as fine dust between the clumps (one more draw call).
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
            beltFallback = mr; // flat stand-in until the asteroid art loads
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
            foreach (var h in handles) if (h.IsValid()) Addressables.Release(h);
            foreach (var h in spriteHandles) if (h.IsValid()) Addressables.Release(h);
        }
    }
}
