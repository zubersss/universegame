using System.Collections.Generic;
using Meridian.Art;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Progress;
using Meridian.Rendering;
using Meridian.Rig;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Building
{
    /// <summary>U-176: a ladder cell or the winch post, saved per planet (GameState.ascentPieces).</summary>
    [System.Serializable]
    public sealed class AscentSave
    {
        public string planet;
        public string kind;
        public int x, y;
        public int dir = 1;
    }

    /// <summary>
    /// U-176 (Bible 5.2 §8.1, D1_TABLES §4 "Climbing", B-210's art): the Builder's ladders. Right click with the Builder (asc_ladder_1 and up)
    /// fills open cells upward from the aim, the tree's metres a placement (1; asc_ladder_2: 3), each metre paid from the dirt store (2;
    /// asc_ladder_2: 1); aimed at a ladder it extends it from its top. One props/dig/ladder piece a metre, ladder_top over a column's highest,
    /// ladder_bottom under its lowest. A column is climbed with W / S (PlayerController, through Ascent); a cell the ground fills (a mound)
    /// loses its piece. The cells are saved with the planet.
    /// </summary>
    public sealed class Ladders : MonoBehaviour, IClimbSource
    {
        public const string Kind = "ladder";
        public const string PieceKey = "props/dig/ladder", TopKey = "props/dig/ladder_top", BottomKey = "props/dig/ladder_bottom";
        /// <summary>Drawn behind the surveyor (order 6) and in front of the ground's back wall.</summary>
        public const int SortingOrder = 5;
        /// <summary>The body stands this far from a ladder's centre while it climbs (B-210's side_b "ladder" socket: 0.38 m in front).</summary>
        public const float Beside = 0.38f;

        public static Ladders Instance { get; private set; }
        public TerrainStreamer terrain;
        public Transform player;

        /// <summary>Raised when a placement adds ladder metres (the bottom cell and the metres).</summary>
        public event System.Action<Vector2Int, int> Placed;

        readonly HashSet<Vector2Int> cells = new HashSet<Vector2Int>();
        readonly List<SpriteRenderer> drawn = new List<SpriteRenderer>();
        readonly Sprite[] sprites = new Sprite[3];
        readonly AsyncOperationHandle<IList<Sprite>>[] handles = new AsyncOperationHandle<IList<Sprite>>[3];
        PlanetId planet;
        bool dirty;

        public int Count => cells.Count;
        public bool Has(Vector2Int cell) => cells.Contains(cell);
        public IEnumerable<Vector2Int> Cells => cells;
        /// <summary>Pieces drawn now (tests).</summary>
        public int Drawn { get; private set; }

        static GameState State => GameState.Instance;
        string PlanetKey => planet.ToString();

        void OnEnable() { Instance = this; Ascent.Register(this); }
        void OnDisable() { if (Instance == this) Instance = null; Ascent.Unregister(this); }

        void Awake()
        {
            string[] keys = { PieceKey, TopKey, BottomKey };
            for (int i = 0; i < keys.Length; i++)
            {
                int k = i;
                handles[k] = ArtLoad.Asset<IList<Sprite>>(keys[k]);
                handles[k].Completed += op =>
                {
                    if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    sprites[k] = op.Result[0];
                    dirty = true;
                };
            }
        }

        void OnDestroy()
        {
            for (int i = 0; i < handles.Length; i++) if (handles[i].IsValid()) ArtLoad.Release(handles[i]);
            if (terrain != null) terrain.TileChanged -= OnTile;
        }

        /// <summary>Rebuilds this planet's ladders from the save.</summary>
        public void ConfigureFor(PlanetId id)
        {
            planet = id;
            cells.Clear();
            if (terrain != null) { terrain.TileChanged -= OnTile; terrain.TileChanged += OnTile; }
            var s = State;
            if (s != null)
                foreach (var a in s.ascentPieces)
                    if (a.kind == Kind && a.planet == PlanetKey) cells.Add(new Vector2Int(a.x, a.y));
            dirty = true;
        }

        /// <summary>
        /// The Builder's right click: ladder metres upward from the aim's cell (from a ladder's top when aimed at one) while the cells are open
        /// and the dirt store pays. Returns the metres placed (0: no ladders bought yet, out of reach, no open cell, or not enough dirt).
        /// </summary>
        public int Place(Vector2 aimWorld)
        {
            int metres = Mathf.RoundToInt(SkillStats.LadderM);
            if (metres <= 0 || terrain == null) return 0;
            if (player != null && (aimWorld - (Vector2)player.position).sqrMagnitude > RigTools.Reach * RigTools.Reach) return 0;
            var c = RigTools.TileOf(aimWorld);
            while (cells.Contains(c)) c.y++;
            int cost = Mathf.Max(0, Mathf.RoundToInt(SkillStats.LadderDirtPerM));
            var store = State != null ? State.dirt : null;
            var first = c;
            int placed = 0;
            for (int k = 0; k < metres; k++, c.y++)
            {
                if (TileId.IsSolid(terrain.GetTile(c.x, c.y)) || cells.Contains(c)) break;
                if (cost > 0)
                {
                    if (store == null || store.count < cost) break;
                    store.Spend(cost);
                }
                cells.Add(c);
                State?.ascentPieces.Add(new AscentSave { planet = PlanetKey, kind = Kind, x = c.x, y = c.y });
                placed++;
            }
            if (placed > 0) { dirty = true; Placed?.Invoke(first, placed); }
            return placed;
        }

        /// <summary>Removes a ladder cell (and its save).</summary>
        public bool Remove(Vector2Int c)
        {
            if (!cells.Remove(c)) return false;
            State?.ascentPieces.RemoveAll(a => a.kind == Kind && a.planet == PlanetKey && a.x == c.x && a.y == c.y);
            dirty = true;
            return true;
        }

        void OnTile(int x, int y, byte old, byte id)
        {
            if (TileId.IsSolid(id)) Remove(new Vector2Int(x, y)); // a mound buried it
        }

        /// <summary>The column a body at `feet` can hold: a ladder cell beside it (within 0.9 m of its centre) at the feet, the waist or
        /// just under the feet (stepping down onto a ladder's top).</summary>
        public bool Find(Vector2 feet, out ClimbSpot spot)
        {
            spot = default;
            if (cells.Count == 0) return false;
            int fx = Mathf.FloorToInt(feet.x);
            for (int dx = 0; dx <= 2; dx++)
            {
                int cx = fx + (dx == 0 ? 0 : dx == 1 ? -1 : 1);
                if (Mathf.Abs(cx + 0.5f - feet.x) > 0.9f) continue;
                for (int h = 0; h < 3; h++)
                {
                    int cy = Mathf.FloorToInt(feet.y + (h == 0 ? 0.2f : h == 1 ? 1.0f : -0.4f));
                    var c = new Vector2Int(cx, cy);
                    if (!cells.Contains(c)) continue;
                    int lo = cy, hi = cy;
                    while (cells.Contains(new Vector2Int(cx, lo - 1))) lo--;
                    while (cells.Contains(new Vector2Int(cx, hi + 1))) hi++;
                    spot = new ClimbSpot { kind = ClimbKind.Ladder, x = cx + 0.5f, bottom = lo, top = hi + 1, speed = Ascent.LadderSpeed, beside = Beside };
                    return true;
                }
            }
            return false;
        }

        void LateUpdate()
        {
            if (dirty) Redraw();
        }

        /// <summary>One piece a cell, a top over each column's highest cell and a foot under its lowest (pooled renderers).</summary>
        void Redraw()
        {
            dirty = false;
            int n = 0;
            if (sprites[0] != null)
            {
                foreach (var c in cells)
                {
                    Draw(ref n, sprites[0], PieceKey, new Vector2(c.x + 0.5f, c.y));
                    if (!cells.Contains(new Vector2Int(c.x, c.y + 1)) && sprites[1] != null) Draw(ref n, sprites[1], TopKey, new Vector2(c.x + 0.5f, c.y + 1f));
                    if (!cells.Contains(new Vector2Int(c.x, c.y - 1)) && sprites[2] != null) Draw(ref n, sprites[2], BottomKey, new Vector2(c.x + 0.5f, c.y));
                }
            }
            for (int i = n; i < drawn.Count; i++) if (drawn[i].enabled) drawn[i].enabled = false;
            Drawn = n;
        }

        void Draw(ref int n, Sprite sprite, string key, Vector2 at)
        {
            if (n == drawn.Count)
            {
                var go = new GameObject("Ladder");
                go.transform.SetParent(transform, false);
                var r = go.AddComponent<SpriteRenderer>();
                r.sortingOrder = SortingOrder;
                drawn.Add(r);
            }
            var sr = drawn[n++];
            sr.sprite = sprite;
            var mat = ArtMaterials.MaterialFor(key);
            if (mat != null && sr.sharedMaterial != mat) sr.sharedMaterial = mat;
            sr.transform.position = new Vector3(at.x, at.y, 0f);
            sr.enabled = true;
        }
    }
}
