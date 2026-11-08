using System.Collections.Generic;
using Meridian.Art;
using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Mining
{
    /// <summary>U-158: a harvested node's state, saved per planet (GameState.nodeStates) so leaving and coming back does not regrow it.</summary>
    [System.Serializable]
    public sealed class NodeSave
    {
        public string planet;
        public int x;
        public int charges;
        public double spentAt;
    }

    /// <summary>
    /// U-158 (D-161 (3), D-162 (5), D-167 (1)-(2), Bible 5.0 (c)): a smooth planet's resources. Surface nodes (B-176's props/&lt;planet&gt;/node_&lt;item&gt;:
    /// full, harvested, an 8-frame glint) stand on the natural ground: the Beam takes one item per stroke for NodeCharges strokes, then the
    /// node shows harvested until it regrows a game day later (saved in GameState.nodeStates). Mercury's Solarite node is cut only in the
    /// twilight window after a flare, as the crystals are. Buried finds lie 2-10 m under the original surface, hidden until a Survey pulse
    /// reaches them: then the find shows in the cutaway and the planet's scan_x pulses on the ground above it. A pocket (pocket_&lt;item&gt;)
    /// gives PocketYield of its item when the brush opens its tile; a relic (Earth's data cache, Mars's lander beacon, Mercury's sunshade
    /// probe, Venus's pressure capsule) gives one Datacore and a story flag; Earth's Warden vault door plays its open clip when dug to.
    /// A dug find stays spent: its tile stays dug in the save. Everything is placed from the world seed, so it is the same every visit.
    /// Until a key's art loads, a drawn placeholder (a tinted rock, a ring, an X) stands in. No per-frame allocation.
    /// </summary>
    public sealed class ResourceFinds : MonoBehaviour
    {
        public const int NodeCharges = 3, PocketYield = 3;
        public const double RegrowGameSeconds = 86400.0;
        /// <summary>Node spacing along the ground (m, hashed between) and the buried finds' spacing; every CacheSpacing a relic, every VaultSpacing (Earth) a vault.</summary>
        public const int NodeSpacingMin = 50, NodeSpacingMax = 90, PocketSpacing = 40, CacheSpacing = 400, VaultSpacing = 1200;
        public const int PocketDepthMin = 2, PocketDepthMax = 10;
        /// <summary>The Beam reaches a node within this of its foot (m, horizontal) and this high.</summary>
        public const float NodeHalfWidth = 1f, NodeHeight = 1.5f;
        /// <summary>B-176's sheets: 12 fps; a node glints for its 8 frames once every GlintPeriod ticks.</summary>
        public const float Fps = 12f;
        public const int GlintStart = 2, GlintFrames = 8, GlintPeriod = 48, VaultOpenFrames = 6;

        /// <summary>B-176's node / pocket items per planet (the trade list), in key order.</summary>
        public static string[] ItemsOf(PlanetId p) => p switch
        {
            PlanetId.Earth => new[] { "iron", "copper", "carbon", "silica", "water_ice" },
            PlanetId.Mars => new[] { "hematite", "perchlorate", "water_ice" },
            PlanetId.Mercury => new[] { "solarite", "nickel" },
            PlanetId.Venus => new[] { "vitriol_glass", "sulfur" },
            _ => new string[0],
        };

        /// <summary>D-167 (1): each inner planet's relic key (B-176).</summary>
        public static string RelicOf(PlanetId p) => p switch
        {
            PlanetId.Earth => "props/earth/data_cache",
            PlanetId.Mars => "props/mars/lander_beacon",
            PlanetId.Mercury => "props/mercury/sunshade_probe",
            PlanetId.Venus => "props/venus/pressure_capsule",
            _ => null,
        };

        public const string VaultKey = "props/earth/vault_door";

        /// <summary>The module gate's only planet rule: Mercury's Solarite is cut only in the twilight window after a flare (U-059); every other node always.</summary>
        public static bool Workable(PlanetId p, string item, float sinceLastFlare) =>
            !(p == PlanetId.Mercury && item == "solarite") || Meridian.Items.OnlyHere.SolariteHarvestable(sinceLastFlare);

        public enum Kind { Pocket, Relic, Vault }

        public sealed class Node
        {
            public int x; public float y; public string item; public int charges = NodeCharges; public double spentAt = double.NegativeInfinity;
            public SpriteRenderer view; public int phase;
            /// <summary>Its sheet's key (props/&lt;planet&gt;/node_&lt;item&gt;), built once.</summary>
            public string key;
        }

        public sealed class Pocket
        {
            public int x, y; public string item; public Kind kind; public bool revealed, spent;
            /// <summary>The vault door's open clip frame (−1 closed).</summary>
            public int openFrame = -1;
            public SpriteRenderer view, mark;
            public string Key(string planetKey) => kind == Kind.Vault ? VaultKey : kind == Kind.Relic ? relicKey : $"props/{planetKey}/pocket_{item}";
            internal string relicKey;
        }

        public TerrainStreamer terrain;
        public Meridian.Rig.RigTools rig;
        /// <summary>Mercury's flare clock (the Solarite node's window); set by PlanetSideRoot.</summary>
        public Meridian.Hazards.SolarFlares flares;
        public bool Active { get; private set; }
        public readonly List<Node> nodes = new List<Node>();
        public readonly List<Pocket> pockets = new List<Pocket>();
        /// <summary>Items (and Datacores) paid out (tests).</summary>
        public int Paid { get; private set; }

        PlanetId planet;
        string planetKey, scanKey;
        readonly Dictionary<string, Sprite[]> art = new Dictionary<string, Sprite[]>();
        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>();
        Meridian.Core.TimeSystem clock;
        System.Func<Vector2, int> hook;
        Transform root;

        public void Configure(PlanetConfig config, TerrainStreamer t, Meridian.Rig.RigTools tools, int seed)
        {
            Deactivate();
            terrain = t; rig = tools; planet = config.id; planetKey = planet.ToString().ToLowerInvariant(); scanKey = $"props/{planetKey}/scan_x";
            if (t == null || !t.SmoothGround || ItemsOf(planet).Length == 0) return;
            Active = true;
            clock = FindAnyObjectByType<Meridian.Core.TimeSystem>();
            root = new GameObject("ResourceFinds").transform;
            root.SetParent(transform, false);
            Place(config, seed);
            Restore();
            foreach (var item in ItemsOf(planet)) { Probe($"props/{planetKey}/node_{item}"); Probe($"props/{planetKey}/pocket_{item}"); }
            Probe(scanKey);
            if (RelicOf(planet) != null) Probe(RelicOf(planet));
            if (planet == PlanetId.Earth) Probe(VaultKey);
            hook = Harvest;
            if (rig != null && !rig.harvesters.Contains(hook)) rig.harvesters.Add(hook);
            t.TileChanged += OnTile;
            Refresh();
        }

        public void Deactivate()
        {
            if (rig != null && hook != null) rig.harvesters.Remove(hook);
            if (terrain != null) terrain.TileChanged -= OnTile;
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear(); art.Clear();
            nodes.Clear(); pockets.Clear();
            if (root != null) Destroy(root.gameObject);
            root = null;
            Active = false;
        }

        void OnDestroy() => Deactivate();

        static uint Hash(int a, int b, int seed)
        {
            unchecked
            {
                uint h = (uint)seed * 0x9E3779B1u ^ (uint)a * 0x85EBCA77u ^ (uint)b * 0xC2B2AE3Du;
                h ^= h >> 15; h *= 0x2C1B3C6Du; h ^= h >> 12; h *= 0x297A2D39u; h ^= h >> 15;
                return h;
            }
        }

        static float Hash01(int a, int b, int seed) => (Hash(a, b, seed) & 0xFFFFFF) / (float)0x1000000;

        /// <summary>Natural, dry ground off every POI stamp: a node or a find may go here.</summary>
        bool Open(int x)
        {
            if (terrain.PadTop(x) != int.MinValue) return false;
            int top = terrain.OriginalTop(x);
            if (top == int.MinValue) return false;
            return terrain.BaseGenerator.TileAt(terrain.WrapX(x), top + 1) != TileId.Water;
        }

        void Place(PlanetConfig config, int seed)
        {
            var items = ItemsOf(planet);
            int w = config.worldWidth, s = seed ^ (int)planet * 7919;
            for (int x = 8, i = 0; x < w - 8; i++)
            {
                if (Open(x) && Open(x - 1) && Open(x + 1))
                {
                    string item = items[(int)(Hash01(i, 1, s) * items.Length) % items.Length];
                    nodes.Add(new Node { x = x, y = terrain.SurfaceAt(x + 0.5f), item = item, key = $"props/{planetKey}/node_{item}", phase = (int)(Hash01(i, 6, s) * GlintPeriod) });
                }
                x += NodeSpacingMin + (int)(Hash01(i, 2, s) * (NodeSpacingMax - NodeSpacingMin));
            }
            string relic = RelicOf(planet);
            for (int x = 20, i = 0; x < w - 20; x += PocketSpacing, i++)
            {
                int px = x + (int)(Hash01(i, 3, s) * 16f) - 8;
                if (!Open(px)) continue;
                var kind = planet == PlanetId.Earth && x % VaultSpacing < PocketSpacing && x >= VaultSpacing ? Kind.Vault
                    : relic != null && x % CacheSpacing < PocketSpacing ? Kind.Relic : Kind.Pocket;
                int depth = kind == Kind.Vault ? PocketDepthMax - 2 : PocketDepthMin + (int)(Hash01(i, 4, s) * (PocketDepthMax - PocketDepthMin + 1));
                int py = terrain.OriginalTop(px) - depth;
                if (!TileId.IsSolid(terrain.BaseGenerator.TileAt(terrain.WrapX(px), py))) continue;
                pockets.Add(new Pocket { x = px, y = py, kind = kind, relicKey = relic, item = kind == Kind.Pocket ? items[(int)(Hash01(i, 5, s) * items.Length) % items.Length] : null });
            }
            foreach (var n in nodes) n.view = Sprite(root, $"Node_{n.item}_{n.x}", new Vector2(n.x + 0.5f, n.y), SmoothGroundOrder + 2);
            foreach (var p in pockets)
            {
                p.view = Sprite(root, $"{p.kind}_{p.x}", new Vector2(p.x + 0.5f, p.y + 0.5f), SmoothGroundOrder + 1);
                p.mark = Sprite(root, $"ScanX_{p.x}", new Vector2(p.x + 0.5f, terrain.SurfaceAt(p.x + 0.5f)), SmoothGroundOrder + 2);
                p.view.enabled = p.mark.enabled = false;
            }
        }

        /// <summary>The save's state: harvested nodes (GameState.nodeStates), dug finds (their tiles in the terrain edits), opened vaults and found relics (flags).</summary>
        void Restore()
        {
            var state = Meridian.Core.GameState.Instance;
            if (state != null)
                foreach (var s in state.nodeStates)
                {
                    if (s.planet != planetKey) continue;
                    foreach (var n in nodes) if (n.x == s.x) { n.charges = Mathf.Clamp(s.charges, 0, NodeCharges); n.spentAt = s.spentAt; }
                }
            foreach (var p in pockets)
            {
                bool dug = false;
                foreach (var c in Footprint(p)) if (!TileId.IsSolid(terrain.GetTile(c.x, c.y)) && TileId.IsSolid(terrain.BaseGenerator.TileAt(terrain.WrapX(c.x), c.y))) dug = true;
                if (p.kind == Kind.Vault)
                {
                    bool open = dug || state != null && state.HasFlag(VaultFlag(p));
                    p.openFrame = open ? VaultOpenFrames - 1 : -1;
                    p.revealed |= open;
                }
                else p.spent = dug;
            }
        }

        void Save(Node n)
        {
            var state = Meridian.Core.GameState.Instance;
            if (state == null) return;
            foreach (var s in state.nodeStates)
                if (s.planet == planetKey && s.x == n.x) { s.charges = n.charges; s.spentAt = n.spentAt; return; }
            state.nodeStates.Add(new NodeSave { planet = planetKey, x = n.x, charges = n.charges, spentAt = n.spentAt });
        }

        string VaultFlag(Pocket p) => $"vault_door:{planetKey}:{p.x}";
        string RelicFlag(Pocket p) => $"relic:{planetKey}:{p.x}";

        /// <summary>The tiles that open a find: its own; a vault door's 2 m face, its tile and the ring round it.</summary>
        static IEnumerable<Vector2Int> Footprint(Pocket p)
        {
            int r = p.kind == Kind.Vault ? 1 : 0;
            for (int y = p.y - r; y <= p.y + r; y++)
                for (int x = p.x - r; x <= p.x + r; x++)
                    yield return new Vector2Int(x, y);
        }

        const int SmoothGroundOrder = Meridian.View2D.SmoothGround.Order;

        static SpriteRenderer Sprite(Transform parent, string name, Vector2 at, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = new Vector3(at.x, at.y, Meridian.View2D.SmoothGround.Z - 0.05f);
            var r = go.AddComponent<SpriteRenderer>();
            r.sortingOrder = order;
            return r;
        }

        void Probe(string key)
        {
            if (art.ContainsKey(key)) return;
            var loc = Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (!exists || this == null || !Active) return;
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                handles.Add(h);
                h.Completed += op =>
                {
                    if (this == null || !Active || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    art[key] = InOrder(op.Result);
                    Refresh();
                };
            };
        }

        /// <summary>The sliced frames by their _&lt;n&gt; suffix (the importer's names); a gap takes frame 0.</summary>
        static Sprite[] InOrder(IList<Sprite> sprites)
        {
            var list = new Sprite[sprites.Count];
            foreach (var sp in sprites)
            {
                if (sp == null) continue;
                int u = sp.name.LastIndexOf('_');
                if (u >= 0 && int.TryParse(sp.name.Substring(u + 1), out int n) && n >= 0 && n < list.Length) list[n] = sp;
            }
            for (int i = 0; i < list.Length; i++) if (list[i] == null) list[i] = list[0] != null ? list[0] : sprites[0];
            return list;
        }

        bool Has(string key) => art.ContainsKey(key);

        /// <summary>The frame for a key, or the drawn placeholder.</summary>
        Sprite Frame(string key, int index, Placeholder fallback)
        {
            if (art.TryGetValue(key, out var f) && f.Length > 0) return f[Mathf.Clamp(index, 0, f.Length - 1)];
            return PlaceholderSprite(fallback);
        }

        void Refresh()
        {
            if (!Active) return;
            double now = Now;
            foreach (var n in nodes)
            {
                if (n.charges <= 0 && now - n.spentAt >= RegrowGameSeconds) { n.charges = NodeCharges; Save(n); } // regrown
                n.view.sprite = Frame(n.key, n.charges > 0 ? 0 : 1, Placeholder.Rock);
                n.view.color = Has(n.key) ? Color.white : TintOf(n.item, n.charges > 0 ? 1f : 0.55f);
            }
            string scan = scanKey;
            foreach (var p in pockets)
            {
                string key = p.Key(planetKey);
                p.view.sprite = Frame(key, p.kind == Kind.Vault ? Mathf.Max(0, p.openFrame + 1) : 0, Placeholder.Ring);
                p.view.color = Has(key) ? Color.white : p.kind == Kind.Pocket ? TintOf(p.item, 1f) : new Color(0.85f, 0.7f, 0.3f, 1f);
                p.mark.sprite = Frame(scan, 0, Placeholder.Cross);
                p.mark.color = Has(scan) ? Color.white : new Color(0.85f, 0.2f, 0.15f, 1f);
                p.view.enabled = p.kind == Kind.Vault ? p.revealed : p.revealed && !p.spent;
                p.mark.enabled = p.revealed && !p.spent && p.openFrame < 0;
            }
        }

        double Now => clock != null ? clock.GameSeconds : Time.time * Meridian.Core.TimeSystem.GameSecondsPerRealSecond;

        int tick;
        float tickAt, regrowAt;
        void Update()
        {
            if (!Active) return;
            if (Time.time >= regrowAt)
            {
                regrowAt = Time.time + 2f; // regrowth is slow: a check every 2 s
                double now = Now;
                bool any = false;
                foreach (var n in nodes) if (n.charges <= 0 && now - n.spentAt >= RegrowGameSeconds) any = true;
                if (any) Refresh();
            }
            if (Time.time < tickAt) return;
            tickAt = Time.time + 1f / Fps;
            tick++;
            // B-176's clips: a full node's glint; the scan X's pulse; a vault door's one-shot open.
            foreach (var n in nodes)
            {
                if (n.charges <= 0 || !n.view.isVisible) continue;
                if (!art.TryGetValue(n.key, out var f) || f.Length < GlintStart + GlintFrames) continue;
                int k = (tick + n.phase) % GlintPeriod;
                n.view.sprite = f[k < GlintFrames ? GlintStart + k : 0];
            }
            art.TryGetValue(scanKey, out var marks);
            foreach (var p in pockets)
            {
                if (marks != null && marks.Length > 1 && p.mark.enabled && p.mark.isVisible) p.mark.sprite = marks[tick % marks.Length];
                if (p.kind == Kind.Vault && p.openFrame >= 0 && p.openFrame < VaultOpenFrames - 1)
                {
                    p.openFrame++;
                    p.view.sprite = Frame(VaultKey, p.openFrame + 1, Placeholder.Ring);
                }
            }
        }

        /// <summary>The Beam at a node: 1 item per stroke while it has charges and its window is open (1), glancing off a harvested or crusted node (0); -1 when no node is there.</summary>
        public int Harvest(Vector2 world)
        {
            if (!Active) return -1;
            foreach (var n in nodes)
            {
                if (Mathf.Abs(world.x - (n.x + 0.5f)) > NodeHalfWidth || world.y < n.y - 0.3f || world.y > n.y + NodeHeight) continue;
                if (n.charges <= 0) return 0;
                if (!Workable(planet, n.item, flares != null ? flares.SinceLastFlare : float.PositiveInfinity)) return 0;
                n.charges--;
                if (n.charges == 0) n.spentAt = Now;
                Save(n);
                Pay(n.item, 1, new Vector2(n.x + 0.5f, n.y + 0.6f));
                Refresh();
                return 1;
            }
            return -1;
        }

        void Pay(string itemKey, int count, Vector2 at)
        {
            var def = Meridian.Items.ItemRegistry.Get(itemKey);
            if (def == null) return;
            for (int i = 0; i < count; i++)
            {
                if (rig != null && rig.drops != null) rig.drops.Spawn(def.id, at + new Vector2((i - (count - 1) * 0.5f) * 0.4f, 0f), null);
                else if (rig != null && rig.inventory != null) rig.inventory.Add(def.id, 1);
                Paid++;
            }
        }

        /// <summary>A Survey pulse: reveals the finds within `radius`; returns the item keys of pockets newly revealed (the scanner catalogues them).</summary>
        public List<string> Reveal(Vector2 centre, float radius)
        {
            var found = new List<string>();
            if (!Active) return found;
            foreach (var p in pockets)
            {
                if (p.revealed || p.spent) continue;
                if ((new Vector2(p.x + 0.5f, p.y + 0.5f) - centre).sqrMagnitude > radius * radius) continue;
                p.revealed = true;
                if (p.kind == Kind.Pocket) found.Add(p.item);
            }
            Refresh();
            return found;
        }

        /// <summary>The brush opened a tile: a find there pays out once (a vault door opens).</summary>
        void OnTile(int x, int y, byte was, byte now)
        {
            if (!Active || TileId.IsSolid(now) || !TileId.IsSolid(was)) return;
            int wx = terrain.WrapX(x);
            foreach (var p in pockets)
            {
                if (p.spent || p.openFrame >= 0) continue;
                int r = p.kind == Kind.Vault ? 1 : 0;
                if (Mathf.Abs(y - p.y) > r || Mathf.Abs(Wrapped(wx - terrain.WrapX(p.x))) > r) continue;
                var state = Meridian.Core.GameState.Instance;
                switch (p.kind)
                {
                    case Kind.Pocket: p.spent = true; Pay(p.item, PocketYield, new Vector2(p.x + 0.5f, p.y + 0.5f)); break;
                    case Kind.Relic:
                        p.spent = true;
                        if (state != null) { state.datacores++; state.SetFlag(RelicFlag(p)); }
                        Paid++;
                        break;
                    case Kind.Vault:
                        p.openFrame = 0; p.revealed = true;
                        if (state != null) state.SetFlag(VaultFlag(p));
                        break;
                }
                Refresh();
                return;
            }
        }

        int Wrapped(int dx)
        {
            int w = terrain.Config != null ? terrain.Config.worldWidth : int.MaxValue;
            if (dx > w / 2) dx -= w; else if (dx < -w / 2) dx += w;
            return dx;
        }

        // ---------- placeholders until a key's art loads ----------

        enum Placeholder { Rock, Ring, Cross }
        static readonly Dictionary<Placeholder, Sprite> placeholders = new Dictionary<Placeholder, Sprite>();

        static Color TintOf(string item, float light)
        {
            Color c = item switch
            {
                "iron" => new Color(0.62f, 0.36f, 0.28f), "copper" => new Color(0.30f, 0.62f, 0.55f), "carbon" => new Color(0.22f, 0.22f, 0.24f),
                "silica" => new Color(0.88f, 0.86f, 0.80f), "water_ice" => new Color(0.70f, 0.86f, 0.95f), "hematite" => new Color(0.55f, 0.25f, 0.22f),
                "perchlorate" => new Color(0.93f, 0.90f, 0.75f), "solarite" => new Color(0.98f, 0.80f, 0.30f), "nickel" => new Color(0.70f, 0.72f, 0.68f),
                "vitriol_glass" => new Color(0.55f, 0.80f, 0.45f), "sulfur" => new Color(0.95f, 0.88f, 0.25f), _ => Color.grey,
            };
            return new Color(c.r * light, c.g * light, c.b * light, 1f);
        }

        static Sprite PlaceholderSprite(Placeholder kind)
        {
            if (placeholders.TryGetValue(kind, out var s) && s != null) return s;
            const int N = 64;
            var tex = new Texture2D(N, N, TextureFormat.RGBA32, false) { name = "Find" + kind, wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[N * N];
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float u = (x + 0.5f) / N - 0.5f, v = (y + 0.5f) / N - 0.5f, a = 0f;
                    switch (kind)
                    {
                        case Placeholder.Rock: // a rounded outcrop on its base, an ink edge
                        {
                            float d = Mathf.Sqrt(u * u * 1.2f + (v + 0.5f) * (v + 0.5f)) - 0.62f;
                            a = Mathf.Clamp01(-d * 40f);
                            if (d > -0.05f && d < 0f) { px[y * N + x] = new Color32(40, 32, 28, 255); continue; }
                            break;
                        }
                        case Placeholder.Ring: { float d = Mathf.Abs(Mathf.Sqrt(u * u + v * v) - 0.36f); a = Mathf.Clamp01(1f - d * 14f) + (Mathf.Sqrt(u * u + v * v) < 0.36f ? 0.55f : 0f); break; }
                        case Placeholder.Cross: { float d = Mathf.Min(Mathf.Abs(u - v), Mathf.Abs(u + v)); a = Mathf.Abs(u) < 0.4f && Mathf.Abs(v) < 0.4f ? Mathf.Clamp01(1f - d * 12f) : 0f; break; }
                    }
                    byte al = (byte)(Mathf.Clamp01(a) * 255f);
                    px[y * N + x] = new Color32(255, 255, 255, al);
                }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            var pivot = kind == Placeholder.Rock ? new Vector2(0.5f, 0f) : new Vector2(0.5f, 0.5f);
            s = UnityEngine.Sprite.Create(tex, new Rect(0, 0, N, N), pivot, kind == Placeholder.Rock ? 40f : 64f);
            placeholders[kind] = s;
            return s;
        }
    }
}
