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

            if (b.parent != null) return; // moons: flat grey until their art exists (B-017 luna)
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
        }

        static Mesh Quad()
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
        }
    }
}
