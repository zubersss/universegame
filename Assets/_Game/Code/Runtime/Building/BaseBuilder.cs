using Meridian.Art;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Items;
using Meridian.Planets;
using Meridian.Terrain;
using Meridian.UI;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.UI;

namespace Meridian.Building
{
    /// <summary>
    /// U-056 Bases v1 on the planet side. The Builder places base pieces (shelter walls, doors, lamps, crates;
    /// on Venus aerostat decks and float cells) on the tile grid; the Beam takes them down again (the item comes
    /// back). A space sealed by walls, doors, crates or decks together with the ground counts as shelter: warmth
    /// and protection from every hazard (WarmthSource.Shelter). Decks placed in open air on Venus start an
    /// aerostat; pieces built onto it ride it; it holds its height while its float cells lift its load and sinks
    /// when overloaded (Buoyancy), stopping on the ground. Everything is kept in GameState (saved) and rebuilt
    /// when the planet loads.
    /// </summary>
    public sealed class BaseBuilder : MonoBehaviour
    {
        public const int MaxShelterCells = 300, ShelterReach = 16;
        public const float HudRange = 15f;
        /// <summary>A lamp's warm light reaches this far (m; LEAD, U-064).</summary>
        public const float LampRadius = 5f;
        /// <summary>U-074: the 3D lamp light (URP point lights fade to zero at their range, so the range exceeds the pool radius).</summary>
        public const float Lamp3DRangeFactor = 1.6f, Lamp3DIntensity = 4f, Lamp3DFront = 1.6f;

        public TerrainStreamer terrain;
        public Meridian.Rig.RigTools rig;
        public Transform player;

        public sealed class Piece
        {
            public PieceSpec spec;
            public BasePieceSave save;
            public GameObject go;
            public Aerostat aerostat;
            /// <summary>U-076: the piece's 3D model (replaces the sprite once loaded).</summary>
            public Meridian.Art.ModelSwap model;
        }

        public sealed class Aerostat
        {
            public AerostatSave save;
            public Rigidbody2D body;
            public readonly Dictionary<Vector2Int, Piece> cells = new Dictionary<Vector2Int, Piece>();
            public readonly List<Piece> pieces = new List<Piece>();
            public bool Grounded { get; internal set; }
            public float Lift { get { float l = 0f; foreach (var p in pieces) l += p.spec.lift; return l; } }
            public float Load { get { float m = 0f; foreach (var p in pieces) m += p.spec.mass; return m; } }
            public float Margin => Buoyancy.Margin(Lift, Load);
            /// <summary>World cell of local cell (0, 0) now (sinking moves it down).</summary>
            public Vector2Int Origin => new Vector2Int(save.x, Mathf.FloorToInt(save.y - save.sunk));
            public Vector2 Position => body.position;
        }

        public readonly List<Piece> pieces = new List<Piece>();
        public readonly List<Aerostat> aerostats = new List<Aerostat>();
        readonly Dictionary<Vector2Int, Piece> ground = new Dictionary<Vector2Int, Piece>();
        readonly Dictionary<string, Sprite> art = new Dictionary<string, Sprite>();
        readonly HashSet<string> requested = new HashSet<string>();
        readonly List<AsyncOperationHandle<IList<Sprite>>> handles = new List<AsyncOperationHandle<IList<Sprite>>>();
        readonly Queue<Vector2Int> frontier = new Queue<Vector2Int>(MaxShelterCells);
        readonly HashSet<Vector2Int> seen = new HashSet<Vector2Int>();
        PlanetId planet;
        int version, shelterVersion = -1;
        Vector2Int shelterCell;
        bool shelterResult;
        Text hud;

        GameState State => GameState.Instance;
        string PlanetKey => planet.ToString();

        void Awake()
        {
            var canvas = UiKit.Canvas(transform, "BaseHudCanvas", 105);
            hud = UiKit.Text(canvas.transform, "AerostatMargin", new Vector2(0.5f, 1f), new Vector2(0f, -40f), new Vector2(700f, 28f), 18, true, TextAnchor.MiddleCenter, UiTheme.Active.text);
            hud.gameObject.SetActive(false);
        }

        void OnEnable() => Meridian.Hazards.WarmthSource.Shelter = Sheltered;
        void OnDisable() { if (Meridian.Hazards.WarmthSource.Shelter == (System.Func<Vector2, bool>)Sheltered) Meridian.Hazards.WarmthSource.Shelter = null; }

        void OnDestroy()
        {
            if (terrain != null) terrain.TileChanged -= OnTile;
            foreach (var h in handles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
        }

        /// <summary>Rebuilds this planet's base from the saved records; hooks the Builder and the Beam.</summary>
        public void ConfigureFor(PlanetId id)
        {
            planet = id;
            Clear();
            if (terrain != null) { terrain.TileChanged -= OnTile; terrain.TileChanged += OnTile; }
            if (rig != null) { rig.placePiece = PlaceItem; rig.dismantle = Dismantle; }
            var state = State;
            if (state == null) return;
            foreach (var a in state.aerostats) if (a.planet == PlanetKey) MakeAerostat(a);
            foreach (var s in state.basePieces)
            {
                if (s.planet != PlanetKey || !System.Enum.TryParse<PieceKind>(s.kind, out var kind)) continue;
                var a = s.aerostat != 0 ? aerostats.Find(k => k.save.id == s.aerostat) : null;
                Spawn(PieceSpec.Get(kind), s, a);
            }
            version++;
        }

        void Clear()
        {
            foreach (var p in pieces) if (p.go != null) Destroy(p.go);
            foreach (var a in aerostats) if (a.body != null) Destroy(a.body.gameObject);
            pieces.Clear(); aerostats.Clear(); ground.Clear();
            version++;
        }

        void OnTile(int x, int y, byte old, byte now) => version++;

        // ---------- lookups ----------

        bool TerrainSolid(Vector2Int c) => terrain != null && TileId.IsSolid(terrain.GetTile(c.x, c.y));

        public Piece PieceAt(Vector2Int c)
        {
            if (ground.TryGetValue(c, out var p)) return p;
            foreach (var a in aerostats)
                if (a.cells.TryGetValue(c - a.Origin, out p)) return p;
            return null;
        }

        Aerostat AerostatNear(Vector2Int c, Vector2Int size)
        {
            for (int dx = -1; dx <= size.x; dx++)
                for (int dy = -1; dy <= size.y; dy++)
                {
                    bool corner = (dx == -1 || dx == size.x) && (dy == -1 || dy == size.y);
                    if (corner) continue;
                    var p = PieceAt(c + new Vector2Int(dx, dy));
                    if (p != null && p.aerostat != null) return p.aerostat;
                }
            return null;
        }

        bool Supported(Vector2Int c, Vector2Int size)
        {
            for (int dx = -1; dx <= size.x; dx++)
                for (int dy = -1; dy <= size.y; dy++)
                {
                    bool corner = (dx == -1 || dx == size.x) && (dy == -1 || dy == size.y);
                    bool inside = dx >= 0 && dx < size.x && dy >= 0 && dy < size.y;
                    if (corner || inside) continue;
                    var n = c + new Vector2Int(dx, dy);
                    if (TerrainSolid(n) || ground.ContainsKey(n)) return true;
                }
            return false;
        }

        // ---------- building ----------

        /// <summary>The Builder with a base-piece item selected: true if it placed one (the caller uses one up).</summary>
        public bool PlaceItem(Vector2 world, int itemId)
        {
            var def = ItemRegistry.Get(itemId);
            var spec = def != null ? PieceSpec.ForItem(def.key) : null;
            return spec != null && Place(world, spec.kind) != null;
        }

        /// <summary>Places a piece with its bottom-left cell at `world` (tests use this). Null if it can't go there.</summary>
        public Piece Place(Vector2 world, PieceKind kind)
        {
            var spec = PieceSpec.Get(kind);
            var c = new Vector2Int(Mathf.FloorToInt(world.x), Mathf.FloorToInt(world.y));
            for (int dx = 0; dx < spec.size.x; dx++)
                for (int dy = 0; dy < spec.size.y; dy++)
                {
                    var cell = c + new Vector2Int(dx, dy);
                    if (TerrainSolid(cell) || PieceAt(cell) != null) return null;
                }
            var aerostat = AerostatNear(c, spec.size);
            if (aerostat == null && kind == PieceKind.FloatCell) return null; // float cells only lift an aerostat
            if (aerostat == null && !Supported(c, spec.size))
            {
                // Open air: only a deck on Venus, which starts a new aerostat.
                if (kind != PieceKind.Deck || planet != PlanetId.Venus) return null;
                var a = new AerostatSave { id = NextAerostatId(), planet = PlanetKey, x = c.x, y = c.y };
                State.aerostats.Add(a);
                aerostat = MakeAerostat(a);
            }
            var save = new BasePieceSave { planet = PlanetKey, kind = kind.ToString(), aerostat = aerostat != null ? aerostat.save.id : 0 };
            var local = aerostat != null ? c - aerostat.Origin : c;
            save.x = local.x; save.y = local.y;
            State.basePieces.Add(save);
            var piece = Spawn(spec, save, aerostat);
            version++;
            return piece;
        }

        int NextAerostatId()
        {
            int id = 1;
            foreach (var a in State.aerostats) id = Mathf.Max(id, a.id + 1);
            return id;
        }

        Aerostat MakeAerostat(AerostatSave save)
        {
            var go = new GameObject("Aerostat" + save.id);
            go.transform.SetParent(transform, false);
            var body = go.AddComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            var a = new Aerostat { save = save, body = body };
            body.position = new Vector2(save.x, save.y - save.sunk);
            go.transform.position = body.position;
            aerostats.Add(a);
            return a;
        }

        Piece Spawn(PieceSpec spec, BasePieceSave save, Aerostat aerostat)
        {
            var go = new GameObject($"{spec.kind}_{save.x}_{save.y}");
            var piece = new Piece { spec = spec, save = save, go = go, aerostat = aerostat };
            if (aerostat != null)
            {
                go.transform.SetParent(aerostat.body.transform, false);
                go.transform.localPosition = new Vector3(save.x, save.y, 0f);
                for (int dx = 0; dx < spec.size.x; dx++)
                    for (int dy = 0; dy < spec.size.y; dy++) aerostat.cells[new Vector2Int(save.x + dx, save.y + dy)] = piece;
                aerostat.pieces.Add(piece);
            }
            else
            {
                go.transform.SetParent(transform, false);
                go.transform.position = new Vector3(save.x, save.y, 0f);
                for (int dx = 0; dx < spec.size.x; dx++)
                    for (int dy = 0; dy < spec.size.y; dy++) ground[new Vector2Int(save.x + dx, save.y + dy)] = piece;
            }
            if (spec.solid)
            {
                var box = go.AddComponent<BoxCollider2D>();
                box.size = spec.size;
                box.offset = new Vector2(spec.size.x * 0.5f, spec.size.y * 0.5f);
            }
            if (spec.kind == PieceKind.Lamp)
            {
                // U-064: a lamp lights its shelter: a small warm point light at its head.
                var lightGo = new GameObject("Light");
                lightGo.transform.SetParent(go.transform, false);
                lightGo.transform.localPosition = new Vector3(spec.size.x * 0.5f, spec.size.y - 0.2f, 0f);
                var light = lightGo.AddComponent<UnityEngine.Rendering.Universal.Light2D>();
                light.lightType = UnityEngine.Rendering.Universal.Light2D.LightType.Point;
                light.pointLightOuterRadius = LampRadius;
                light.pointLightInnerRadius = 0.4f;
                light.intensity = 1.1f;
                light.color = new Color(1f, 0.8f, 0.55f);
                // U-074 (Bible 2.0 §10.5): the 3D renderer's lamp: a warm point light a little in front of the play plane,
                // so it pools on block fronts and the back wall; no shadows (budget: ≤ 150 casters, Sun only).
                var lamp3D = lightGo.AddComponent<Light>();
                lamp3D.type = LightType.Point;
                lamp3D.color = light.color;
                lamp3D.range = LampRadius * Lamp3DRangeFactor;
                lamp3D.intensity = Lamp3DIntensity;
                lamp3D.shadows = LightShadows.None;
                lightGo.transform.localPosition += new Vector3(0f, 0f, -Lamp3DFront); // in front of the block faces (z −0.5), not grazing them
            }
            var viewGo = new GameObject("View");
            viewGo.transform.SetParent(go.transform, false);
            viewGo.transform.localPosition = new Vector3(spec.size.x * 0.5f, 0f, 0f);
            var view = viewGo.AddComponent<SpriteRenderer>();
            view.sortingOrder = 3;
            Dress(view, spec);
            // U-076: the piece's model on the footprint's bottom centre, scaled like the sprite (stretch pieces fill
            // their cells; the others keep their proportions at the footprint's height).
            piece.model = Meridian.Art.ModelSwap.Attach(view, spec.artKey, go.transform, viewGo.transform.localPosition,
                fit: spec.stretch ? Meridian.Art.ModelSwap.Fit.Stretch : Meridian.Art.ModelSwap.Fit.Height, footprint: spec.size);
            if (spec.kind == PieceKind.Lamp)
            {
                var lightT = go.transform.Find("Light");
                piece.model.Swapped += s =>
                {
                    // LEAD cycle 179: the lamp lights from its bulb (socket_light); the 3D light keeps its U-074 offset
                    // in front of the block faces.
                    var socket = s.Find("socket_light");
                    if (socket == null || lightT == null) return;
                    var p = socket.position;
                    lightT.position = new Vector3(p.x, p.y, p.z - Lamp3DFront);
                };
            }
            if (spec.kind == PieceKind.Door) doors.Add(piece);
            pieces.Add(piece);
            return piece;
        }

        /// <summary>The Beam on a piece: takes it down and gives its item back. False if no piece is there.</summary>
        public bool Dismantle(Vector2 world)
        {
            var c = new Vector2Int(Mathf.FloorToInt(world.x), Mathf.FloorToInt(world.y));
            var p = PieceAt(c);
            if (p == null) return false;
            Remove(p);
            var def = ItemRegistry.Get(p.spec.itemKey);
            if (def != null)
            {
                if (rig != null && rig.drops != null) rig.drops.Spawn(def.id, world, null);
                else State?.inventory.Add(def.id, 1);
            }
            return true;
        }

        void Remove(Piece p)
        {
            State?.basePieces.Remove(p.save);
            pieces.Remove(p);
            if (p.aerostat != null)
            {
                var a = p.aerostat;
                a.pieces.Remove(p);
                var dead = new List<Vector2Int>();
                foreach (var kv in a.cells) if (kv.Value == p) dead.Add(kv.Key);
                foreach (var k in dead) a.cells.Remove(k);
                if (a.pieces.Count == 0)
                {
                    State?.aerostats.Remove(a.save);
                    aerostats.Remove(a);
                    Destroy(a.body.gameObject);
                }
            }
            else
            {
                var dead = new List<Vector2Int>();
                foreach (var kv in ground) if (kv.Value == p) dead.Add(kv.Key);
                foreach (var k in dead) ground.Remove(k);
            }
            if (p.go != null) Destroy(p.go);
            version++;
        }

        // ---------- art ----------

        void Dress(SpriteRenderer view, PieceSpec spec)
        {
            if (art.TryGetValue(spec.artKey, out var sp)) { Fit(view, spec, sp); return; }
            if (!requested.Add(spec.artKey)) { StartCoroutine(WaitFor(view, spec)); return; }
            var h = ArtLoad.Asset<IList<Sprite>>(spec.artKey);
            handles.Add(h);
            h.Completed += op =>
            {
                if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                art[spec.artKey] = op.Result[0];
            };
            StartCoroutine(WaitFor(view, spec));
        }

        System.Collections.IEnumerator WaitFor(SpriteRenderer view, PieceSpec spec)
        {
            float until = Time.realtimeSinceStartup + 10f;
            Sprite sp = null;
            while (view != null && !art.TryGetValue(spec.artKey, out sp) && Time.realtimeSinceStartup < until) yield return null;
            if (view != null && sp != null) Fit(view, spec, sp);
        }

        static void Fit(SpriteRenderer view, PieceSpec spec, Sprite sp)
        {
            view.sprite = sp;
            var mat = Meridian.Rendering.ArtMaterials.MaterialFor(spec.artKey);
            if (mat != null) view.sharedMaterial = mat;
            var b = sp.bounds.size;
            if (b.x <= 0f || b.y <= 0f) return;
            // The art's pivot is bottom-centre: it stands on the footprint's bottom edge.
            // Walls overlap: the art has soft side margins (wider than top and bottom); neighbours meet without a seam.
            float overX = spec.kind == PieceKind.Wall ? 1.25f : 1f, overY = spec.kind == PieceKind.Wall ? 1.1f : 1f;
            view.transform.localScale = spec.stretch
                ? new Vector3(overX * spec.size.x / b.x, overY * spec.size.y / b.y, 1f)
                : Vector3.one * (spec.size.y / b.y);
        }

        // ---------- shelter ----------

        bool Blocks(Vector2Int c, ref bool byPiece)
        {
            if (TerrainSolid(c)) return true;
            var p = PieceAt(c);
            if (p != null && p.spec.seals) { byPiece = true; return true; }
            return false;
        }

        /// <summary>Whether `p` lies in a space sealed by base pieces and the ground (cached until something changes).</summary>
        public bool Sheltered(Vector2 p)
        {
            if (pieces.Count == 0) return false;
            var start = new Vector2Int(Mathf.FloorToInt(p.x), Mathf.FloorToInt(p.y + 0.5f));
            if (start == shelterCell && version == shelterVersion) return shelterResult;
            shelterCell = start; shelterVersion = version;
            shelterResult = Flood(start);
            return shelterResult;
        }

        /// <summary>Why the last shelter check ended (tests and diagnostics).</summary>
        public string LastFlood { get; private set; } = "";

        bool Flood(Vector2Int start)
        {
            bool byPiece = false;
            if (Blocks(start, ref byPiece)) { LastFlood = $"start {start} is blocked"; return false; }
            frontier.Clear(); seen.Clear();
            frontier.Enqueue(start); seen.Add(start);
            while (frontier.Count > 0)
            {
                var c = frontier.Dequeue();
                if (seen.Count > MaxShelterCells || Mathf.Abs(c.x - start.x) > ShelterReach || Mathf.Abs(c.y - start.y) > ShelterReach) { LastFlood = $"open: from {start} reached {c} ({seen.Count} cells)"; return false; }
                for (int i = 0; i < 4; i++)
                {
                    var n = c + (i == 0 ? Vector2Int.left : i == 1 ? Vector2Int.right : i == 2 ? Vector2Int.up : Vector2Int.down);
                    if (seen.Contains(n) || Blocks(n, ref byPiece)) continue;
                    seen.Add(n);
                    frontier.Enqueue(n);
                }
            }
            LastFlood = $"sealed: {seen.Count} cells from {start}, by pieces {byPiece}";
            return byPiece; // a sealed pocket of plain rock is a cave, not a shelter
        }

        // ---------- aerostats ----------

        readonly List<Piece> doors = new List<Piece>();
        /// <summary>U-076: a door's model opens (its `open` clip) while the surveyor is this close, and closes after.</summary>
        public const float DoorOpenRange = 1.8f;
        public const string DoorClip = "open";

        void UpdateDoors()
        {
            for (int i = doors.Count - 1; i >= 0; i--)
            {
                var d = doors[i];
                if (d.go == null) { doors.RemoveAt(i); continue; }
                if (d.model == null || !d.model.Ready) continue;
                bool near = player != null && Mathf.Abs(player.position.x - (d.go.transform.position.x + d.spec.size.x * 0.5f)) < DoorOpenRange
                            && player.position.y > d.go.transform.position.y - 0.5f && player.position.y < d.go.transform.position.y + d.spec.size.y;
                int want = near ? 1 : -1;
                // U-113 (D-117): the door drawn from its sheet plays `open` once forward on approach and backward on leaving.
                if (d.model.UsesSheet) { if (d.model.Sheet.Towards != want) d.model.Sheet.PlayToward(DoorClip, near); continue; }
                var m = d.model.Views.Count > 0 ? d.model.Views[0] : null;
                if (m == null) continue;
                if (m.Towards != want) m.PlayToward(DoorClip, near);
            }
        }

        void Update()
        {
            UpdateDoors();
            float dt = Time.deltaTime;
            Aerostat nearest = null;
            float best = HudRange * HudRange;
            foreach (var a in aerostats)
            {
                float sink = Buoyancy.SinkSpeed(a.Lift, a.Load);
                a.Grounded = false;
                if (sink > 0f)
                {
                    // Sink, but stop on the ground: no piece's bottom may pass into a solid tile.
                    float step = sink * dt, limit = step;
                    float baseY = a.save.y - a.save.sunk;
                    foreach (var kv in a.cells)
                    {
                        float bottom = baseY + kv.Key.y;
                        int x = a.save.x + kv.Key.x;
                        int under = Mathf.FloorToInt(bottom - step); // the tile the bottom would enter
                        if (TerrainSolid(new Vector2Int(x, under))) limit = Mathf.Min(limit, Mathf.Max(0f, bottom - (under + 1)));
                    }
                    a.Grounded = limit < step;
                    if (limit > 0f)
                    {
                        int before = a.Origin.y;
                        a.save.sunk += limit;
                        a.body.MovePosition(new Vector2(a.save.x, a.save.y - a.save.sunk));
                        if (a.Origin.y != before) version++;
                    }
                }
                if (player != null)
                {
                    float d = ((Vector2)player.position - a.Position).sqrMagnitude;
                    if (d < best) { best = d; nearest = a; }
                }
            }
            bool show = nearest != null;
            if (hud.gameObject.activeSelf != show) hud.gameObject.SetActive(show);
            if (show)
            {
                float m = nearest.Margin;
                hud.text = $"AEROSTAT   LIFT {nearest.Lift:F0}  ·  LOAD {nearest.Load:F0}  ·  MARGIN {(m >= 0f ? "+" : "")}{m:F0}{(m < 0f ? "  SINKING" : "")}";
                hud.color = m < 0f ? new Color(1f, 0.45f, 0.35f) : UiTheme.Active.text;
            }
        }
    }
}
