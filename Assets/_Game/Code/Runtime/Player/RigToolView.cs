using System.Collections.Generic;
using Meridian.Art;
using Meridian.FX;
using Meridian.Rendering;
using Meridian.Rig;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Player
{
    /// <summary>
    /// U-046: the selected Rig module in the surveyor's hand (props/rig/*, pivot [0.375, 0.5] at the grip),
    /// rotated to the aim; the Beam's ray (fx/beam_ray, pivot [0, 0.5], tiled in x from the muzzle to the
    /// hit); the Builder's ghost (fx/builder_ghost, 8-frame pulse) on the target cell, red when blocked.
    /// </summary>
    public sealed class RigToolView : MonoBehaviour
    {
        /// <summary>The grip, relative to the surveyor's feet (facing right; mirrored when facing left).</summary>
        public static readonly Vector2 Hand = new Vector2(0.12f, 0.95f);
        public const float BeamHeight = 0.25f;
        public static readonly Color Blocked = new Color(1f, 0.3f, 0.25f, 0.9f);

        public PlayerRigInput input;
        public RigTools rig;

        public SpriteRenderer Tool { get; private set; }
        public SpriteRenderer Beam { get; private set; }
        public SpriteRenderer Ghost { get; private set; }
        public Vector2 HandWorld { get; private set; }
        public Vector2 MuzzleWorld { get; private set; }
        public float AimDegrees { get; private set; }
        public float BeamLength { get; private set; }
        public bool GhostBlocked { get; private set; }

        readonly Sprite[] tools = new Sprite[RigModules.Count + 1];
        readonly AsyncOperationHandle<IList<Sprite>>[] toolHandles = new AsyncOperationHandle<IList<Sprite>>[RigModules.Count + 1];
        FxSheet beamSheet, ghostSheet;
        // U-183: each tool's look by its chain level (RigLooks), re-read when the Skill Tree changes; the Beam's cable to the pack.
        readonly int[] mk = new int[RigModules.Count + 1];
        int lookVersion = -1;
        public int MkOf(RigModule m) => mk[(int)m];
        public LineRenderer Cable { get; private set; }
        /// <summary>U-183: the grip sits on the drawn frame's hand socket (false: the fixed Hand).</summary>
        public bool HandOnSocket { get; private set; }
        /// <summary>The drawn frame the grip was placed for, and the grip in the surveyor's squash-root space (mirrored with the drawing).</summary>
        public int HandFrame { get; private set; } = -1;
        public Vector2 HandLocal { get; private set; }

        /// <summary>The drawn surveyor's front glove for its current frame (props/rig/hand_socket: hand_socket on the side sheet,
        /// hand_socket_b on side_b), mirrored with the drawing; `held` where the sheet draws a tool in that hand.</summary>
        Vector2? DrawnHand(out bool onSocket, out bool held)
        {
            onSocket = held = false;
            if (body == null) body = GetComponentInParent<Transform>().GetComponentInChildren<Meridian.View2D.SpriteCharacterView>();
            if (body == null || body.Renderer == null || !body.Renderer.enabled) return null;
            bool b = JetpackOverlay.SheetB(body.Renderer.sprite); // U-176: the drawn frame's sheet (side_b's clips play under the side key)
            var table = ArtMaterials.SocketFor("props/rig/hand_socket", b ? "hand_socket_b" : "hand_socket");
            int i = JetpackOverlay.FrameOf(body.Renderer.sprite);
            if (b)
            {
                var heldTable = ArtMaterials.SocketFor("props/rig/hand_socket", "held_b");
                held = heldTable != null && heldTable.Has(i);
            }
            if (table == null || !table.Has(i)) return null;
            bool flip = body.Renderer.flipX;
            onSocket = true;
            HandFrame = i;
            HandLocal = new Vector2(flip ? -table[i, 0] : table[i, 0], table[i, 1]);
            return body.SquashRoot.TransformPoint(HandLocal);
        }
        public Vector2 CableFrom { get; private set; }
        public Vector2 CableTo { get; private set; }
        const int CablePoints = 7;
        const float CableSag = 0.14f, CableWidth = 0.035f;
        static readonly Color CableInk = new Color(0.13f, 0.10f, 0.08f, 1f);
        Meridian.View2D.SpriteCharacterView body;
        /// <summary>U-176: the drawn surveyor the tool sits on (null before it is found).</summary>
        public Meridian.View2D.SpriteCharacterView Body => body;
        float beamAge, ghostAge;
        readonly RaycastHit2D[] hits = new RaycastHit2D[8];
        static readonly ContactFilter2D AnyCollider = ContactFilter2D.noFilter;

        void Awake()
        {
            Tool = Child("RigTool", 6);
            Beam = Child("BeamRay", 6);
            Beam.drawMode = SpriteDrawMode.Tiled;
            Beam.tileMode = SpriteTileMode.Continuous;
            Ghost = Child("BuilderGhost", 6);
            Beam.enabled = Ghost.enabled = false;
            var cg = new GameObject("BeamCable");
            cg.transform.SetParent(transform, false);
            Cable = cg.AddComponent<LineRenderer>();
            Cable.positionCount = CablePoints;
            Cable.useWorldSpace = true;
            Cable.startWidth = Cable.endWidth = CableWidth;
            Cable.startColor = Cable.endColor = CableInk;
            Cable.numCapVertices = 2;
            Cable.sortingOrder = 6;
            var unlit = ArtMaterials.Active != null ? ArtMaterials.Active.unlit : null;
            if (unlit != null) Cable.sharedMaterial = unlit;
            Cable.enabled = false;
        }

        SpriteRenderer Child(string name, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = order;
            return sr;
        }

        void Start()
        {
            ReadLooks();
            ghostSheet = FxSheet.Get(ArtKeys.Fx.BuilderGhost);
        }

        void OnDestroy()
        {
            foreach (var h in toolHandles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
        }

        /// <summary>U-183: each module's Mk from the bought nodes; a changed look loads its sprite (the old one released) and the Beam's ray.</summary>
        void ReadLooks()
        {
            lookVersion = Meridian.Progress.SkillStats.Version;
            var bought = RigLooks.Bought;
            for (int m = 1; m <= RigModules.Count; m++)
            {
                int want = RigLooks.MkOf((RigModule)m, bought);
                if (want == mk[m] && toolHandles[m].IsValid()) continue;
                mk[m] = want;
                LoadTool((RigModule)m, want);
            }
            beamSheet = FxSheet.Get(RigLooks.RayKey(mk[(int)RigModule.Beam]));
        }

        void LoadTool(RigModule m, int level)
        {
            string key = RigLooks.ToolKey(m, level);
            if (toolHandles[(int)m].IsValid()) global::Meridian.Art.ArtLoad.Release(toolHandles[(int)m]);
            var h = ArtLoad.Asset<IList<Sprite>>(key);
            toolHandles[(int)m] = h;
            h.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                if (mk[(int)m] != level) return; // a later look superseded it
                tools[(int)m] = op.Result[0];
                if (Tool != null && input != null && input.module == m) Show(m);
            };
        }

        RigModule shown;

        void Show(RigModule m)
        {
            shown = m;
            Tool.sprite = tools[(int)m];
            var mat = ArtMaterials.MaterialFor(RigLooks.ToolKey(m, mk[(int)m]));
            if (mat != null) Tool.sharedMaterial = mat;
        }

        /// <summary>Where the tool points: the aim while the rig is aimed, else straight ahead.</summary>
        void LateUpdate()
        {
            if (input == null) return;
            if (lookVersion != Meridian.Progress.SkillStats.Version) { ReadLooks(); Show(input.module); }
            if (shown != input.module || Tool.sprite != tools[(int)input.module]) Show(input.module);

            bool left = input.AimWorld.x < transform.position.x;
            var feet = (Vector2)transform.position;
            // U-183 (B-218's hand_socket): the grip on the drawn frame's front glove where BLENDER's pose maths has one, else the fixed hand;
            // hidden where the sheet draws its own tool in that hand (held_b: the dig / build / climb clips).
            bool held;
            HandWorld = DrawnHand(out bool onSocket, out held) is Vector2 h && onSocket ? h : feet + new Vector2(left ? -Hand.x : Hand.x, Hand.y);
            HandOnSocket = onSocket;
            if (Tool.enabled == held) Tool.enabled = !held;
            Vector2 dir = input.AimWorld - HandWorld;
            if (dir.sqrMagnitude < 1e-4f) dir = left ? Vector2.left : Vector2.right;
            AimDegrees = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
            Tool.transform.position = HandWorld;
            Tool.transform.rotation = Quaternion.Euler(0f, 0f, AimDegrees);
            Tool.flipY = left; // keep the tool upright when pointing left
            var muzzle = RigModules.Muzzle(input.module, mk[(int)input.module]);
            if (left) muzzle.y = -muzzle.y;
            MuzzleWorld = HandWorld + (Vector2)(Tool.transform.rotation * muzzle);

            UpdateBeam(dir.normalized);
            UpdateGhost();
            UpdateCable(left);
        }

        /// <summary>U-183: the Beam's cable (B-205: arm-mounted, cable-fed): from the tool's cable_socket to the pack on the surveyor's back
        /// (the jetpack's back socket for the drawn frame; the pack's usual place when there is none), sagging a little.</summary>
        void UpdateCable(bool left)
        {
            bool on = input.module == RigModule.Beam && Tool.sprite != null && Tool.enabled;
            var key = RigLooks.ToolKey(RigModule.Beam, mk[(int)RigModule.Beam]);
            var socket = ArtMaterials.SocketFor(key, "cable_socket");
            on &= socket != null && socket.Has(0);
            if (Cable.enabled != on) Cable.enabled = on;
            if (!on) return;
            var local = new Vector2(socket[0, 0], left ? -socket[0, 1] : socket[0, 1]);
            CableFrom = HandWorld + (Vector2)(Tool.transform.rotation * local);
            CableTo = JetpackOverlay.PackWorld(body, transform, left);
            var mid = (CableFrom + CableTo) * 0.5f + Vector2.down * CableSag;
            for (int i = 0; i < CablePoints; i++)
            {
                float t = i / (CablePoints - 1f), u = 1f - t;
                var p = u * u * CableFrom + 2f * u * t * mid + t * t * CableTo;
                Cable.SetPosition(i, new Vector3(p.x, p.y, 0.01f));
            }
        }

        void UpdateBeam(Vector2 dir)
        {
            bool on = input.module == RigModule.Beam && input.Using && beamSheet != null && beamSheet.Ready;
            if (Beam.enabled != on) Beam.enabled = on;
            if (!on) { beamAge = 0f; BeamLength = 0f; return; }
            // To the first terrain hit, at most the Rig's reach, never past the aim point.
            float max = Mathf.Min(RigTools.Reach, Vector2.Distance(MuzzleWorld, input.AimWorld) + 0.5f);
            float len = max;
            int n = Physics2D.Raycast(MuzzleWorld, dir, AnyCollider, hits, max);
            for (int i = 0; i < n; i++)
                if (hits[i].collider.GetComponentInParent<TerrainChunk>() != null) { len = hits[i].distance; break; }
            BeamLength = len;
            beamAge += Time.deltaTime;
            int f = beamSheet.FrameAt(beamAge);
            if (f >= 0 && Beam.sprite != beamSheet.frames[f])
            {
                Beam.sprite = beamSheet.frames[f];
                if (beamSheet.material != null) Beam.sharedMaterial = beamSheet.material;
            }
            Beam.transform.position = MuzzleWorld;
            Beam.transform.rotation = Quaternion.Euler(0f, 0f, AimDegrees);
            Beam.size = new Vector2(Mathf.Max(0.01f, len), BeamHeight);
        }

        static Sprite ring;
        /// <summary>U-157: a 1 m anti-aliased ring (the brush ghost), made once.</summary>
        static Sprite Ring
        {
            get
            {
                if (ring != null) return ring;
                const int N = 128;
                var tex = new Texture2D(N, N, TextureFormat.RGBA32, false) { name = "BrushRing", wrapMode = TextureWrapMode.Clamp };
                var px = new Color32[N * N];
                for (int y = 0; y < N; y++)
                    for (int x = 0; x < N; x++)
                    {
                        float d = Mathf.Sqrt((x + 0.5f - N * 0.5f) * (x + 0.5f - N * 0.5f) + (y + 0.5f - N * 0.5f) * (y + 0.5f - N * 0.5f));
                        float a = Mathf.Clamp01(1f - Mathf.Abs(d - (N * 0.5f - 5f)) / 3f) + 0.18f * Mathf.Clamp01((N * 0.5f - 5f - d) / 2f);
                        px[y * N + x] = new Color32(255, 255, 255, (byte)(Mathf.Clamp01(a) * 255f));
                    }
                tex.SetPixels32(px);
                tex.Apply(false, true);
                ring = Sprite.Create(tex, new Rect(0, 0, N, N), new Vector2(0.5f, 0.5f), N);
                ring.name = "BrushRing";
                return ring;
            }
        }

        void UpdateGhost()
        {
            bool brush = rig != null && rig.Brush; // U-157: a round ghost the brush's size on a smooth planet
            bool on = input.module == RigModule.Builder && rig != null && (brush || ghostSheet != null && ghostSheet.Ready)
                      && (input.AimWorld - (Vector2)transform.position).sqrMagnitude <= (RigTools.Reach + 1f) * (RigTools.Reach + 1f);
            if (Ghost.enabled != on) Ghost.enabled = on;
            if (!on) { ghostAge = 0f; return; }
            ghostAge += Time.deltaTime;
            if (brush)
            {
                Ghost.transform.position = new Vector3(input.AimWorld.x, input.AimWorld.y, 0f);
                if (Ghost.sprite != Ring) Ghost.sprite = Ring;
                float pulse = 1f + 0.04f * Mathf.Sin(ghostAge * 6f);
                Ghost.transform.localScale = Vector3.one * (2f * RigTools.BrushRadius * pulse);
            }
            var cell = RigTools.TileOf(input.AimWorld);
            if (!brush) Ghost.transform.position = new Vector3(cell.x + 0.5f, cell.y + 0.5f, 0f);
            int f = brush ? -1 : ghostSheet.FrameAt(ghostAge);
            if (f >= 0 && Ghost.sprite != ghostSheet.frames[f])
            {
                Ghost.sprite = ghostSheet.frames[f];
                if (ghostSheet.material != null) Ghost.sharedMaterial = ghostSheet.material;
                float w = Ghost.sprite.bounds.size.x;
                Ghost.transform.localScale = w > 0f ? Vector3.one / w : Vector3.one; // one tile
            }
            byte tile = rig.SelectedTile;
            GhostBlocked = tile == TileId.Air || !rig.CanPlace(input.AimWorld, tile);
            var c = GhostBlocked ? Blocked : Color.white;
            if (Ghost.color != c) Ghost.color = c;
        }
    }
}
