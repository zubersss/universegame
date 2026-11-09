using System.Collections.Generic;
using Meridian.Art;
using Meridian.Core;
using Meridian.Mining;
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
    /// <summary>
    /// U-176 (D1_TABLES §4 "Climbing", asc_winch, B-210's winch_post): the winch. With asc_winch, the Builder's right click at a shaft's mouth
    /// (the aim between the Surface Line and a metre over the drawn surface) stands the post there (one a planet: placing again moves it),
    /// its base at the drawn surface over the shaft, leaning onto the side with ground. Its line hangs from the post's line_socket straight
    /// down to the first ground, any depth; holding W beside it rides it up at the tables' 6 m/s × the pack's load to just under the post
    /// (topside: the Surface Line is 2 m under the surface).
    /// </summary>
    public sealed class Winch : MonoBehaviour, IClimbSource
    {
        public const string Kind = "winch";
        public const string PostKey = "props/dig/winch_post";
        /// <summary>The line's top on the post (B-210's line_socket, metres from the post's pivot at its base).</summary>
        public static readonly Vector2 LineSocket = new Vector2(0.27f, 0.62f);
        /// <summary>The body stands this far from the line while it rides (the hands on it: B-210's reel socket, ~0.45 m in front).</summary>
        public const float Beside = 0.45f;

        public static Winch Instance { get; private set; }
        public TerrainStreamer terrain;
        public Transform player;

        SpriteRenderer post;
        LineRenderer line;
        AsyncOperationHandle<IList<Sprite>> handle;
        PlanetId planet;

        public bool Standing { get; private set; }
        /// <summary>The post's base (the drawn surface over the shaft), the side it leans to (+1 / −1), the line's x, top and foot.</summary>
        public Vector2 Base { get; private set; }
        public int Dir { get; private set; } = 1;
        public float LineX => Base.x + Dir * LineSocket.x;
        public float LineTop => Base.y + LineSocket.y;
        public float LineFoot { get; private set; }
        /// <summary>The feet's highest point on the ride (the hands at the line's top).</summary>
        public float RideTop => LineTop - Ascent.HandsUp;

        string PlanetKey => planet.ToString();
        static GameState State => GameState.Instance;

        void OnEnable() { Instance = this; Ascent.Register(this); }
        void OnDisable() { if (Instance == this) Instance = null; Ascent.Unregister(this); }

        void Awake()
        {
            var go = new GameObject("WinchPost");
            go.transform.SetParent(transform, false);
            post = go.AddComponent<SpriteRenderer>();
            post.sortingOrder = Ladders.SortingOrder;
            post.enabled = false;
            var lgo = new GameObject("WinchLine");
            lgo.transform.SetParent(transform, false);
            line = lgo.AddComponent<LineRenderer>();
            line.useWorldSpace = true;
            line.positionCount = 2;
            line.startWidth = line.endWidth = 0.05f;
            line.numCapVertices = 0;
            line.startColor = line.endColor = new Color(0.13f, 0.10f, 0.08f, 1f); // the cable's ink
            var unlit = ArtMaterials.Active != null ? ArtMaterials.Active.unlit : null;
            if (unlit != null) line.sharedMaterial = unlit;
            line.sortingOrder = Ladders.SortingOrder;
            line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            line.receiveShadows = false;
            line.enabled = false;
            handle = ArtLoad.Asset<IList<Sprite>>(PostKey);
            handle.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                post.sprite = op.Result[0];
                var mat = ArtMaterials.MaterialFor(PostKey);
                if (mat != null) post.sharedMaterial = mat;
                Draw();
            };
        }

        void OnDestroy() { if (handle.IsValid()) ArtLoad.Release(handle); }

        public void ConfigureFor(PlanetId id)
        {
            planet = id;
            Standing = false;
            var s = State;
            if (s != null)
                foreach (var a in s.ascentPieces)
                    if (a.kind == Kind && a.planet == PlanetKey) { Stand(new Vector2(a.x / 100f, a.y / 100f), a.dir); break; }
            Draw();
        }

        /// <summary>
        /// The Builder's right click with asc_winch: aimed at a shaft's mouth (open ground over open ground, between the Surface Line and a
        /// metre over the drawn surface), stands the post there. Returns false elsewhere (the click then places a ladder).
        /// </summary>
        public bool Place(Vector2 aimWorld)
        {
            if (!SkillStats.Winch || terrain == null) return false;
            if (player != null && (aimWorld - (Vector2)player.position).sqrMagnitude > RigTools.Reach * RigTools.Reach) return false;
            float surface = terrain.SurfaceAt(aimWorld.x);
            float lineY = DigRun.LineAt(terrain, aimWorld.x);
            if (aimWorld.y < lineY || aimWorld.y > surface + 1f) return false;
            var c = RigTools.TileOf(aimWorld);
            if (TileId.IsSolid(terrain.GetTile(c.x, c.y)) || TileId.IsSolid(terrain.GetTile(c.x, Mathf.FloorToInt(lineY) - 1))) return false;
            // lean onto the side with ground at the surface (the post's foot rests on the rim)
            int sy = Mathf.FloorToInt(surface - 0.5f);
            int dir = TileId.IsSolid(terrain.GetTile(c.x - 1, sy)) || TileId.IsSolid(terrain.GetTile(c.x - 2, sy)) ? 1 : -1;
            var at = new Vector2(c.x + 0.5f - dir * LineSocket.x, surface);
            Stand(at, dir);
            var s = State;
            if (s != null)
            {
                s.ascentPieces.RemoveAll(a => a.kind == Kind && a.planet == PlanetKey);
                s.ascentPieces.Add(new AscentSave { planet = PlanetKey, kind = Kind, x = Mathf.RoundToInt(at.x * 100f), y = Mathf.RoundToInt(at.y * 100f), dir = dir });
            }
            Draw();
            return true;
        }

        void Stand(Vector2 at, int dir)
        {
            Standing = true;
            Base = at;
            Dir = dir >= 0 ? 1 : -1;
            LineFoot = FootOfLine();
        }

        /// <summary>The first ground under the line's top (the line hangs to it), scanned cell by cell; 400 m at most.</summary>
        float FootOfLine()
        {
            if (terrain == null) return LineTop - 1f;
            int x = Mathf.FloorToInt(LineX);
            int y = Mathf.FloorToInt(LineTop);
            for (int k = 0; k < 400; k++, y--)
                if (TileId.IsSolid(terrain.GetTile(x, y - 1))) return y;
            return y;
        }

        public void Remove()
        {
            Standing = false;
            State?.ascentPieces.RemoveAll(a => a.kind == Kind && a.planet == PlanetKey);
            Draw();
        }

        void Draw()
        {
            if (post == null) return;
            post.enabled = Standing && post.sprite != null;
            line.enabled = Standing;
            if (!Standing) return;
            post.transform.position = new Vector3(Base.x, Base.y, 0f);
            post.flipX = Dir < 0;
            line.SetPosition(0, new Vector3(LineX, LineTop, 0f));
            line.SetPosition(1, new Vector3(LineX, LineFoot, 0f));
        }

        float lastFootCheck;

        void Update()
        {
            // the shaft deepens under a standing line: it follows the ground down (twice a second)
            if (!Standing || Time.time < lastFootCheck + 0.5f) return;
            lastFootCheck = Time.time;
            float foot = FootOfLine();
            if (!Mathf.Approximately(foot, LineFoot)) { LineFoot = foot; Draw(); }
        }

        /// <summary>The line, for a body within 0.9 m of it between its foot and the ride's top.</summary>
        public bool Find(Vector2 feet, out ClimbSpot spot)
        {
            spot = default;
            if (!Standing || Mathf.Abs(feet.x - LineX) > 0.9f) return false;
            if (feet.y < LineFoot - 0.3f || feet.y > RideTop + 0.1f) return false;
            spot = new ClimbSpot { kind = ClimbKind.Winch, x = LineX, bottom = LineFoot, top = RideTop, speed = Ascent.WinchSpeed, beside = Beside };
            return true;
        }
    }
}
