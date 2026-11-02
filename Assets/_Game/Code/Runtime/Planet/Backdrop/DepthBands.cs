using System.Collections.Generic;
using Meridian.Art;
using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Planet.Backdrop
{
    /// <summary>
    /// U-076 (Bible 2.0 §10.3, contract v2.2 depth bands): the 3D world behind the play plane, replacing the v1
    /// parallax layers 1 and 2 (layer 0, the sky, stays on PlanetBackdrop's quad, pushed behind the skyline):
    ///  · ground: a strip of the column's original surface from the blocks' back face (z 0.5) to z 12, with risers
    ///    and a skirt, in the planet's block material: the near props plane stands on it;
    ///  · flora: seeded per column on that strip, z 1.5–9 for ground cover,
    ///    per biome (B-085 Earth, B-089 Mars; trees z 6–12 and 6 % of forest columns, D-071), none inside POI stamps or on water;
    ///  · ridge_mid (z 20–60 m, 256 m period) per region and skyline_far (z 150–400 m, 512 m period): three copies
    ///    each, re-centred on the camera, standing on the mean surface around it.
    /// All of it is world-fixed, so the perspective rail gives the parallax. Bands fade with the sky underground.
    /// </summary>
    public sealed class DepthBands : MonoBehaviour
    {
        public Camera view;
        public TerrainStreamer terrain;
        public PlanetBackdrop backdrop;
        public Meridian.Planet.POI.PoiPlacer pois;

        public const float RidgePeriod = 256f, SkylinePeriod = 512f;
        public const float GroundBackZ = 12f, GroundSkirt = 40f;
        public const int GroundHalfWidth = 96, GroundStep = 16;
        /// <summary>D-071: ground flora z 1.5–9; trees z 6–12 so their crowns sit behind the surveyor and leave the ridge visible.</summary>
        public const float FloraNearZ = 1.5f, FloraFarZ = 9f, TreeNearZ = 6f, TreeFarZ = 12f;
        /// <summary>The mean surface under the bands: columns sampled every 8 m over ±64 m, eased over ~2 s.</summary>
        public const int BaseHalfWidth = 64, BaseStep = 8;
        public const float BaseEase = 2f;

        sealed class Band
        {
            public string key;
            public float period;
            public GameObject root;
            public readonly ModelView[] copies = new ModelView[3];
            public bool Ready => copies[0] != null && copies[0].Ready;
            public bool checkedDepth;
        }

        PlanetId planet;
        bool configured;
        Band ridge, skyline;
        float baseY;
        bool baseSet;
        int groundCentre = int.MinValue;
        MeshFilter groundFilter;
        MeshRenderer groundRenderer;
        Mesh groundMesh;
        readonly Dictionary<int, GameObject> flora = new Dictionary<int, GameObject>();
        readonly List<int> drop = new List<int>();

        /// <summary>Tests/captures: whether the bands are drawn, and the world z range the ridge covers.</summary>
        public bool RidgeReady => ridge != null && ridge.Ready;
        public bool SkylineReady => skyline != null && skyline.Ready;
        public string RidgeKey => ridge?.key;
        public string SkylineKey => skyline?.key;
        public int FloraCount => flora.Count;
        public Mesh Ground => groundMesh;
        /// <summary>The ridge model's depth range after placement (a check that it lies behind the play plane).</summary>
        public Vector2 RidgeDepth { get; private set; }
        public bool RidgeMirrored { get; private set; }

        public void ConfigureFor(PlanetConfig config)
        {
            Clear();
            planet = config.id;
            configured = planet == PlanetId.Earth || planet == PlanetId.Mars;
            baseSet = false;
            groundCentre = int.MinValue;
        }

        public static string RidgeFor(PlanetId p, int x)
        {
            if (p == PlanetId.Mars) return "backgrounds/mars_plains/ridge_mid";
            if (p != PlanetId.Earth) return null;
            switch (EarthBiomes.At(x))
            {
                case Biome.Plains: return "backgrounds/earth_plains/ridge_mid";
                case Biome.Desert: return "backgrounds/earth_desert/ridge_mid";
                case Biome.Ocean: return "backgrounds/earth_coast/ridge_mid";
                case Biome.Taiga: return "backgrounds/earth_taiga/ridge_mid";
                case Biome.Tundra: return "backgrounds/earth_tundra/ridge_mid";
                default: return "backgrounds/earth_forest/ridge_mid";
            }
        }

        public static string SkylineFor(PlanetId p) =>
            p == PlanetId.Earth ? "backgrounds/earth/skyline_far" : p == PlanetId.Mars ? "backgrounds/mars/skyline_far" : null;

        // ---------- flora tables (B-085 / B-089) ----------

        public readonly struct FloraPick
        {
            public readonly string key;
            public readonly float chance;
            public readonly bool tree;
            public FloraPick(string key, float chance, bool tree = false) { this.key = key; this.chance = chance; this.tree = tree; }
        }

        const string EF = "props/earth_flora/", MF = "props/mars_flora/";
        static readonly FloraPick[] Forest = { new FloraPick(EF + "tree_oak", 0.04f, true), new FloraPick(EF + "tree_birch", 0.02f, true), /* D-071: trees 6 % */ new FloraPick(EF + "bush_a", 0.08f), new FloraPick(EF + "bush_b", 0.05f), new FloraPick(EF + "rock_c", 0.04f), new FloraPick(EF + "grass", 0.22f) };
        static readonly FloraPick[] Plains = { new FloraPick(EF + "grass", 0.32f), new FloraPick(EF + "bush_a", 0.06f), new FloraPick(EF + "tree_birch", 0.03f, true), new FloraPick(EF + "tree_oak", 0.02f, true), new FloraPick(EF + "rock_a", 0.03f) };
        static readonly FloraPick[] Desert = { new FloraPick(EF + "cactus", 0.07f), new FloraPick(EF + "dead_tree", 0.02f, true), new FloraPick(EF + "rock_b", 0.05f) };
        static readonly FloraPick[] Coast = { new FloraPick(EF + "grass", 0.15f), new FloraPick(EF + "rock_a", 0.05f), new FloraPick(EF + "tree_spruce", 0.03f, true) };
        static readonly FloraPick[] Taiga = { new FloraPick(EF + "tree_spruce", 0.14f, true), new FloraPick(EF + "rock_a", 0.04f), new FloraPick(EF + "grass", 0.10f), new FloraPick(EF + "bush_a", 0.03f) };
        static readonly FloraPick[] Tundra = { new FloraPick(EF + "rock_a", 0.05f), new FloraPick(EF + "grass", 0.12f), new FloraPick(EF + "dead_tree", 0.02f, true) };
        static readonly FloraPick[] Mars = { new FloraPick(MF + "boulder_a", 0.02f), new FloraPick(MF + "boulder_b", 0.02f), new FloraPick(MF + "boulder_c", 0.02f), new FloraPick(MF + "rock_a", 0.04f), new FloraPick(MF + "rock_b", 0.03f), new FloraPick(MF + "dust_bush", 0.03f) };

        public static FloraPick[] FloraFor(PlanetId p, int x)
        {
            if (p == PlanetId.Mars) return Mars;
            if (p != PlanetId.Earth) return null;
            switch (EarthBiomes.At(x))
            {
                case Biome.Plains: return Plains;
                case Biome.Desert: return Desert;
                case Biome.Ocean: return Coast;
                case Biome.Taiga: return Taiga;
                case Biome.Tundra: return Tundra;
                default: return Forest;
            }
        }

        static uint Hash(int x, uint salt)
        {
            uint h = (uint)x * 0x9E3779B1u ^ salt;
            h ^= h >> 16; h *= 0x7FEB352Du; h ^= h >> 15; h *= 0x846CA68Bu; h ^= h >> 16;
            return h;
        }

        static float Unit(int x, uint salt) => (Hash(x, salt) & 0xFFFFFF) / (float)0x1000000;

        /// <summary>The flora at world column x (wrapped), or default when none. Pure: the same column always gets the same plant.</summary>
        public static bool FloraAt(PlanetId p, int x, out FloraPick pick, out float z, out float yaw, out float scale)
        {
            pick = default; z = yaw = 0f; scale = 1f;
            var table = FloraFor(p, x);
            if (table == null) return false;
            float r = Unit(x, 0xF10A), acc = 0f;
            foreach (var f in table)
            {
                acc += f.chance;
                if (r >= acc) continue;
                pick = f;
                float near = f.tree ? TreeNearZ : FloraNearZ, far = f.tree ? TreeFarZ : FloraFarZ;
                z = Mathf.Lerp(near, far, Unit(x, 0x2D));
                yaw = Unit(x, 0x7A) * 360f;
                scale = Mathf.Lerp(0.85f, 1.15f, Unit(x, 0x5C));
                return true;
            }
            return false;
        }

        // ---------- per frame ----------

        void LateUpdate()
        {
            if (!configured || view == null || terrain == null || terrain.Config == null) return;
            float camX = view.transform.position.x;
            int col = Mathf.FloorToInt(camX);

            // The bands' foot: the mean original surface around the camera, eased so walking over a hill doesn't bob them.
            float sum = 0f; int n = 0;
            for (int dx = -BaseHalfWidth; dx <= BaseHalfWidth; dx += BaseStep) { sum += terrain.OriginalTop(col + dx) + 1f; n++; }
            float target = sum / n;
            baseY = baseSet ? Mathf.Lerp(baseY, target, 1f - Mathf.Exp(-Time.deltaTime / BaseEase)) : target;
            baseSet = true;

            string rk = RidgeFor(planet, terrain.WrapX(col));
            if (ridge == null || ridge.key != rk) { DropBand(ridge); ridge = MakeBand(rk, RidgePeriod); }
            string sk = SkylineFor(planet);
            if (skyline == null && sk != null) skyline = MakeBand(sk, SkylinePeriod);

            bool shown = backdrop == null || backdrop.Alpha > 0.01f;
            PlaceBand(ridge, camX, shown);
            PlaceBand(skyline, camX, shown);
            if (backdrop != null) backdrop.SetDepthBands(RidgeReady || SkylineReady);

            if (groundCentre == int.MinValue || Mathf.Abs(col - groundCentre) >= GroundStep)
            {
                groundCentre = col;
                BuildGround(col);
                UpdateFlora(col);
            }
        }

        Band MakeBand(string key, float period)
        {
            if (key == null) return null;
            var b = new Band { key = key, period = period, root = new GameObject("Band " + key) };
            b.root.transform.SetParent(transform, false);
            for (int i = 0; i < 3; i++)
            {
                var go = new GameObject("Copy" + i);
                go.transform.SetParent(b.root.transform, false);
                b.copies[i] = go.AddComponent<ModelView>();
                b.copies[i].Load(key);
            }
            return b;
        }

        void DropBand(Band b)
        {
            if (b != null && b.root != null) Destroy(b.root);
        }

        void PlaceBand(Band b, float camX, bool shown)
        {
            if (b == null) return;
            if (b.root.activeSelf != shown) b.root.SetActive(shown);
            if (!b.Ready) return;
            if (!b.checkedDepth)
            {
                // The bands lie behind the play plane (+z, away from the camera). glTF's −Z depth arrives as Unity −Z
                // under glTFast's import, so a band whose geometry lies at negative z is mirrored in z (the exporter's
                // camera side then faces our camera). Measured once per band from the model itself.
                b.checkedDepth = true;
                var mb = ModelSwap.ModelBounds(b.copies[0].Instance);
                bool mirror = mb.center.z < 0f;
                if (mirror) foreach (var c in b.copies) c.transform.localScale = new Vector3(1f, 1f, -1f);
                if (b == ridge)
                {
                    RidgeMirrored = mirror;
                    RidgeDepth = mirror ? new Vector2(-mb.max.z, -mb.min.z) : new Vector2(mb.min.z, mb.max.z);
                }
            }
            float k = Mathf.Round(camX / b.period);
            for (int i = 0; i < 3; i++)
                b.copies[i].transform.localPosition = new Vector3((k + i - 1) * b.period, baseY, 0f);
        }

        // ---------- the ground behind the play plane ----------

        readonly List<Vector3> gv = new List<Vector3>(4096);
        readonly List<Vector3> gn = new List<Vector3>(4096);
        readonly List<Vector3> guv = new List<Vector3>(4096);
        readonly List<int> gt = new List<int>(6144);

        void BuildGround(int centre)
        {
            var mat = terrain.BlockMaterial;
            if (mat == null) return;
            if (groundMesh == null)
            {
                var go = new GameObject("Ground (behind the play plane)");
                go.transform.SetParent(transform, false);
                groundFilter = go.AddComponent<MeshFilter>();
                groundRenderer = go.AddComponent<MeshRenderer>();
                groundRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                groundMesh = new Mesh { name = "DepthBands ground" };
                groundMesh.MarkDynamic();
                groundFilter.sharedMesh = groundMesh;
            }
            groundRenderer.sharedMaterial = mat;
            gv.Clear(); gn.Clear(); guv.Clear(); gt.Clear();
            float z0 = BlockMesher.BackZ, z1 = GroundBackZ;
            int x0 = centre - GroundHalfWidth, x1 = centre + GroundHalfWidth;
            int prevG = int.MinValue; byte prevId = 0;
            for (int x = x0; x <= x1; x++)
            {
                int wx = terrain.WrapX(x);
                int top = terrain.OriginalTop(x);
                byte id = terrain.BaseGenerator.TileAt(wx, top);
                if (!TileId.IsSolid(id)) id = TileId.Soil;
                bool water = top + 1 < terrain.Config.worldHeight && terrain.BaseGenerator.TileAt(wx, top + 1) == TileId.Water;
                int g = water ? int.MinValue : top + 1;
                if (g != int.MinValue)
                {
                    // Top, and the skirt down the back edge (facing the camera).
                    Quad(new Vector3(x, g, z0), new Vector3(x + 1, g, z0), new Vector3(x + 1, g, z1), new Vector3(x, g, z1), Vector3.up, BlockMesher.TopLayer(id));
                    Quad(new Vector3(x, g - GroundSkirt, z1), new Vector3(x + 1, g - GroundSkirt, z1), new Vector3(x + 1, g, z1), new Vector3(x, g, z1), Vector3.back, BlockMesher.SideLayer(id));
                }
                // The riser between this column and the previous one faces the lower side.
                if (prevG != int.MinValue && g != int.MinValue && prevG != g)
                {
                    if (prevG > g) Riser(x, g, prevG, z0, z1, true, BlockMesher.SideLayer(prevId));
                    else Riser(x, prevG, g, z0, z1, false, BlockMesher.SideLayer(id));
                }
                else if (prevG != int.MinValue && g == int.MinValue) Riser(x, prevG - (int)GroundSkirt, prevG, z0, z1, true, BlockMesher.SideLayer(prevId));
                else if (prevG == int.MinValue && g != int.MinValue && x > x0) Riser(x, g - (int)GroundSkirt, g, z0, z1, false, BlockMesher.SideLayer(id));
                prevG = g; prevId = id;
            }
            groundMesh.Clear();
            groundMesh.indexFormat = gv.Count > 65000 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16;
            groundMesh.SetVertices(gv);
            groundMesh.SetNormals(gn);
            groundMesh.SetUVs(0, guv);
            groundMesh.SetTriangles(gt, 0);
            groundMesh.RecalculateBounds();
        }

        /// <summary>A riser at x from y0 to y1; facesRight = its normal is +x (the higher ground is on the left).</summary>
        void Riser(int x, float y0, float y1, float z0, float z1, bool facesRight, float layer)
        {
            if (facesRight) Quad(new Vector3(x, y0, z0), new Vector3(x, y0, z1), new Vector3(x, y1, z1), new Vector3(x, y1, z0), Vector3.right, layer);
            else Quad(new Vector3(x, y0, z0), new Vector3(x, y1, z0), new Vector3(x, y1, z1), new Vector3(x, y0, z1), Vector3.left, layer);
        }

        // Same convention as BlockMesher: a,b,c,d with Cross(c − a, b − a) along n; triangles a-c-b, a-d-c; world planar UVs.
        void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 n, float layer)
        {
            int i = gv.Count;
            gv.Add(a); gv.Add(b); gv.Add(c); gv.Add(d);
            for (int k = 0; k < 4; k++) gn.Add(n);
            guv.Add(Uv(a, n, layer)); guv.Add(Uv(b, n, layer)); guv.Add(Uv(c, n, layer)); guv.Add(Uv(d, n, layer));
            gt.Add(i); gt.Add(i + 2); gt.Add(i + 1);
            gt.Add(i); gt.Add(i + 3); gt.Add(i + 2);
        }

        static Vector3 Uv(Vector3 p, Vector3 n, float layer)
        {
            float t = BlockMesher.TileMetres, wz = p.z - BlockMesher.FrontZ;
            if (n.y != 0f) return new Vector3(p.x / t, wz / t, layer);
            if (n.x != 0f) return new Vector3(wz / t, p.y / t, layer);
            return new Vector3(p.x / t, p.y / t, layer);
        }

        // ---------- flora ----------

        void UpdateFlora(int centre)
        {
            int x0 = centre - GroundHalfWidth, x1 = centre + GroundHalfWidth;
            drop.Clear();
            foreach (var kv in flora) if (kv.Key < x0 || kv.Key > x1) drop.Add(kv.Key);
            foreach (int x in drop) { if (flora[x] != null) Destroy(flora[x]); flora.Remove(x); }
            for (int x = x0; x <= x1; x++)
            {
                if (flora.ContainsKey(x)) continue;
                int wx = terrain.WrapX(x);
                GameObject go = null;
                if (FloraAt(planet, wx, out var pick, out float z, out float yaw, out float scale) && !InPoi(x))
                {
                    int top = terrain.OriginalTop(x);
                    bool water = terrain.BaseGenerator.TileAt(wx, top + 1) == TileId.Water;
                    if (!water)
                    {
                        go = new GameObject("Flora " + pick.key.Substring(pick.key.LastIndexOf('/') + 1));
                        go.transform.SetParent(transform, false);
                        go.transform.localPosition = new Vector3(x + 0.5f, top + 1f, z);
                        go.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
                        go.transform.localScale = Vector3.one * scale;
                        go.AddComponent<ModelView>().Load(pick.key);
                    }
                }
                flora[x] = go; // null = a column checked and left bare
            }
        }

        bool InPoi(int x) => pois != null && pois.StampGroundAt(terrain.WrapX(x), out _);

        void Clear()
        {
            DropBand(ridge); DropBand(skyline);
            ridge = skyline = null;
            foreach (var go in flora.Values) if (go != null) Destroy(go);
            flora.Clear();
            if (groundMesh != null) groundMesh.Clear();
            if (backdrop != null) backdrop.SetDepthBands(false);
        }

        void OnDestroy()
        {
            if (groundMesh != null) Destroy(groundMesh);
        }
    }
}
