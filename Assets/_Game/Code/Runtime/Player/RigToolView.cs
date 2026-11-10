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
    /// U-046: the selected Rig module in the surveyor's hand (props/rig/*, pivot [0.375, 0.5] at the grip); the Beam's ray (fx/beam_ray,
    /// pivot [0, 0.5], tiled in x from the muzzle to the hit); the Builder's ghost (fx/builder_ghost, 8-frame pulse) on the target cell,
    /// red when blocked.
    /// U-209 (D-196): the dig slot's tool is part of the stroke. At rest it is carried (no cursor tracking with the button up). In a
    /// shovel swing it steps through the swing's five drawings on the stroke's 12 Hz clock: raised for the wind-up, the blade's tip AT
    /// the contact point on the contact drawing (DigPose: slid back through the glove for a near target, the body's lunge for a far
    /// one), a pry, the toss, the recover; the body leans in and recoils with it on its squash root. The Beam's angle is critically
    /// damped toward the aim, its ray runs from the muzzle to the target from the press' own frame with a glow at the hit. A reticle
    /// shows where a dig would land (the brush's circle, or the cell on block ground; its tint says in reach, pulled in to the reach,
    /// or nothing to dig) and a crack mark the work its target holds. The other modules keep pointing at the cursor.
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
        /// <summary>The tool's drawn angle (degrees, counter-clockwise from +x).</summary>
        public float AimDegrees { get; private set; }
        public float BeamLength { get; private set; }
        public bool GhostBlocked { get; private set; }

        readonly Sprite[] tools = new Sprite[RigModules.Count + 1];
        readonly AsyncOperationHandle<IList<Sprite>>[] toolHandles = new AsyncOperationHandle<IList<Sprite>>[RigModules.Count + 1];
        FxSheet beamSheet, ghostSheet;
        // U-183: each tool's look by its chain level (RigLooks), re-read when the Skill Tree changes; the Beam's cable to the pack.
        readonly int[] mk = new int[RigModules.Count + 1];
        // U-209: each look's muzzle and the Beam's cable socket, read with the look (they were looked up by a built string every frame)
        readonly Vector2[] muzzleOf = new Vector2[RigModules.Count + 1];
        ArtMaterials.ArtSocket cableSocket;
        int lookVersion = -1;
        public int MkOf(RigModule m) => mk[(int)m];
        public LineRenderer Cable { get; private set; }
        /// <summary>U-183: the grip sits on the drawn frame's hand socket (false: the fixed Hand).</summary>
        public bool HandOnSocket { get; private set; }
        /// <summary>The drawn frame the grip was placed for, and the grip in the surveyor's squash-root space (mirrored with the drawing).</summary>
        public int HandFrame { get; private set; } = -1;
        public Vector2 HandLocal { get; private set; }
        /// <summary>U-209: the tool's direction the drawn frame's socket carries (degrees, as drawn facing right), where it has one.</summary>
        public float HandSocketDegrees { get; private set; }
        public bool HandSocketHasAngle { get; private set; }

        /// <summary>B-246's dig sheet (its clips play in the side sheet's controller as side_b's do; its json's "hand" rows are [x, z, angle]).</summary>
        public const string DigSheetKey = "characters/surveyor/side_dig";
        static readonly Dictionary<Sprite, bool> sheetDig = new Dictionary<Sprite, bool>(64);

        /// <summary>The drawn frame is the dig sheet's (its sprite is named side_dig_&lt;i&gt;).</summary>
        public static bool SheetDig(Sprite s)
        {
            if (s == null) return false;
            if (sheetDig.TryGetValue(s, out bool d)) return d;
            d = s.name.StartsWith("side_dig_", System.StringComparison.Ordinal);
            sheetDig[s] = d;
            return d;
        }

        // the hand's socket tables and the dig sheet's rest poses, read once per registry (a lookup builds its key string)
        ArtMaterials.ArtSocket handTable, handTableB, heldTableB, handTableDig, readyPose, stowPose;
        ArtMaterials tablesOf;
        int tablesCount = -2;

        void ReadTables()
        {
            var reg = ArtMaterials.Active;
            int n = reg != null && reg.sockets != null ? reg.sockets.Count : -1;
            if (reg == tablesOf && n == tablesCount) return;
            tablesOf = reg; tablesCount = n;
            handTable = ArtMaterials.SocketFor("props/rig/hand_socket", "hand_socket");
            handTableB = ArtMaterials.SocketFor("props/rig/hand_socket", "hand_socket_b");
            heldTableB = ArtMaterials.SocketFor("props/rig/hand_socket", "held_b");
            handTableDig = ArtMaterials.SocketFor(DigSheetKey, "hand");
            readyPose = ArtMaterials.SocketFor(DigSheetKey, "ready");
            stowPose = ArtMaterials.SocketFor(DigSheetKey, "carry");
            ReadLookSockets();
        }

        /// <summary>The drawn surveyor's front glove for its current frame (props/rig/hand_socket: hand_socket on the side sheet,
        /// hand_socket_b on side_b; the dig sheet's own "hand"), mirrored with the drawing; `held` where the sheet draws a tool in that hand.</summary>
        Vector2? DrawnHand(out bool onSocket, out bool held)
        {
            onSocket = held = false;
            HandSocketHasAngle = false;
            if (body == null) body = GetComponentInParent<Transform>().GetComponentInChildren<Meridian.View2D.SpriteCharacterView>();
            if (body == null || body.Renderer == null || !body.Renderer.enabled) return null;
            ReadTables();
            var sprite = body.Renderer.sprite;
            bool dig = SheetDig(sprite);
            bool b = !dig && JetpackOverlay.SheetB(sprite); // U-176: the drawn frame's sheet (side_b's clips play under the side key)
            var table = dig ? handTableDig : b ? handTableB : handTable;
            int i = JetpackOverlay.FrameOf(sprite);
            if (b) held = heldTableB != null && heldTableB.Has(i);
            if (table == null || !table.Has(i)) return null;
            bool flip = body.Renderer.flipX;
            onSocket = true;
            HandFrame = i;
            HandLocal = new Vector2(flip ? -table[i, 0] : table[i, 0], table[i, 1]);
            if (table.stride >= 3 && !float.IsNaN(table[i, 2])) { HandSocketHasAngle = true; HandSocketDegrees = table[i, 2] * Mathf.Rad2Deg; }
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
            Tool = Child("RigTool", Meridian.View2D.SpriteCharacterView.SurveyorOrder); // U-200: with the drawn surveyor, in front of the Pilgrim
            Beam = Child("BeamRay", Meridian.View2D.SpriteCharacterView.SurveyorOrder);
            Beam.drawMode = SpriteDrawMode.Tiled;
            Beam.tileMode = SpriteTileMode.Continuous;
            Ghost = Child("BuilderGhost", Meridian.View2D.SpriteCharacterView.SurveyorOrder);
            // U-209: the dig's reticle, the crack mark under it, the Beam's glow at its hit
            Crack = Child("DigCrack", Meridian.View2D.SpriteCharacterView.SurveyorOrder - 1);
            Reticle = Child("DigReticle", Meridian.View2D.SpriteCharacterView.SurveyorOrder);
            Glow = Child("BeamGlow", Meridian.View2D.SpriteCharacterView.SurveyorOrder + 1);
            Fist = Child("GripFist", Meridian.View2D.SpriteCharacterView.SurveyorOrder + 2); // over the tool, which is over the body
            Pip = Child("DigPip", Meridian.View2D.SpriteCharacterView.SurveyorOrder + 1);     // the reticle's mark on the contact point
            for (int i = 0; i < brackets.Length; i++) { brackets[i] = Child("ReticleBracket" + i, Meridian.View2D.SpriteCharacterView.SurveyorOrder + 1); brackets[i].enabled = false; }
            Swish = Child("ShovelSwish", Meridian.View2D.SpriteCharacterView.SurveyorOrder + 2);
            Beam.enabled = Ghost.enabled = Crack.enabled = Reticle.enabled = Glow.enabled = Fist.enabled = Pip.enabled = Swish.enabled = false;
            var mg = new GameObject("DigCrackMask");
            mg.transform.SetParent(transform, false);
            CrackMask = mg.AddComponent<SpriteMask>();
            CrackMask.sprite = MaskSquare;
            CrackMask.enabled = false;
            var cg = new GameObject("BeamCable");
            cg.transform.SetParent(transform, false);
            Cable = cg.AddComponent<LineRenderer>();
            Cable.positionCount = CablePoints;
            Cable.useWorldSpace = true;
            Cable.startWidth = Cable.endWidth = CableWidth;
            Cable.startColor = Cable.endColor = CableInk;
            Cable.numCapVertices = 2;
            Cable.sortingOrder = Meridian.View2D.SpriteCharacterView.SurveyorOrder;
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
            LoadFist();
            LoadDigFx();
        }

        void OnDestroy()
        {
            foreach (var h in toolHandles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            if (fistHandle.IsValid()) global::Meridian.Art.ArtLoad.Release(fistHandle);
        }

        /// <summary>B-246's props/rig/grip_fist (the surveyor's front glove as a fist round a shaft: its pivot on the shaft's centre line at
        /// the hand socket, the shaft along its +x). Probed quietly (D-143): without it the tool rides the drawn glove bare.</summary>
        public const string FistKey = "props/rig/grip_fist";
        public SpriteRenderer Fist { get; private set; }
        AsyncOperationHandle<IList<Sprite>> fistHandle;

        void LoadFist()
        {
            var loc = Addressables.LoadResourceLocationsAsync(FistKey);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(l);
                if (!exists || this == null) return;
                fistHandle = ArtLoad.Asset<IList<Sprite>>(FistKey);
                fistHandle.Completed += op =>
                {
                    if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    Fist.sprite = op.Result[0];
                    var mat = ArtMaterials.MaterialFor(FistKey);
                    if (mat != null) Fist.sharedMaterial = mat;
                };
            };
        }

        /// <summary>U-183: each module's Mk from the bought nodes; a changed look loads its sprite (the old one released) and the Beam's ray.</summary>
        void ReadLooks()
        {
            lookVersion = Meridian.Progress.SkillStats.Version;
            var bought = RigLooks.Bought;
            for (int m = 1; m <= RigModules.Count; m++)
            {
                int want = (RigModule)m == RigModule.Beam ? RigLooks.DigMk(Meridian.Progress.SkillStats.DigTool, bought) : RigLooks.MkOf((RigModule)m, bought); // U-193: the look follows the tool in hand
                if (want == mk[m] && toolHandles[m].IsValid()) continue;
                mk[m] = want;
                LoadTool((RigModule)m, want);
            }
            beamSheet = FxSheet.Get(RigLooks.RayKey(mk[(int)RigModule.Beam]));
            ReadLookSockets();
        }

        /// <summary>Each look's muzzle and the Beam's cable socket from the registry (with the looks, and when the registry changes).</summary>
        void ReadLookSockets()
        {
            for (int m = 1; m <= RigModules.Count; m++) muzzleOf[m] = RigModules.Muzzle((RigModule)m, mk[m]);
            cableSocket = ArtMaterials.SocketFor(RigLooks.ToolKey(RigModule.Beam, mk[(int)RigModule.Beam]), "cable_socket");
        }

        void LoadTool(RigModule m, int level)
        {
            string key = RigLooks.ToolKey(m, level);
            if (key == RigLooks.ShovelKey)
            {
                // U-193: B-226's shovel, probed quietly (D-143); the Beam Mk1 stands in until it is exported
                var loc = UnityEngine.AddressableAssets.Addressables.LoadResourceLocationsAsync(key);
                loc.Completed += l =>
                {
                    bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                    global::Meridian.Art.ArtLoad.Release(l);
                    if (this != null && mk[(int)m] == level) LoadSprite(m, level, exists ? key : RigLooks.ToolKey(m, 1));
                };
                return;
            }
            LoadSprite(m, level, key);
        }

        void LoadSprite(RigModule m, int level, string key)
        {
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

        // ---------- U-209 (D-196): the dig slot's tool in the stroke ----------

        /// <summary>The dig tool's two rest states (LEAD 02:1x, B-246): READY, low in the hand in front, held for ReadySeconds after the
        /// last swing, so a burst of clicks never stows and un-stows it; then STOWED (the shovel's shaft behind the torso, its blade up
        /// behind the helmet: drawn behind the body, no fist), switching on the 12 Hz tick. The Beam keeps the low carry. Both ride the
        /// side sheet's glove; the tool's direction is the pose's angle plus its share of the front arm's own swing (side_dig.json's
        /// "ready" / "carry": radians, counter-clockwise from +x facing right). These are the json's numbers, used where the registry
        /// does not hold them yet.</summary>
        public const float ReadyRadians = -0.25f, ReadySwing = 0.25f, StowRadians = 2.1817f, StowSwing = 0.08f, ReadySeconds = 1.5f;
        /// <summary>The Beam's angle follows its aim critically damped over about this long.</summary>
        public const float BeamDampSeconds = 0.06f;
        /// <summary>How far the tool may slide back through the glove on a swing's contact drawing (a mid-shaft hold), by the swing's clip:
        /// side_dig.json's slide_max (LEAD 02:1x: dig_fwd_near 0.95 m, dig_fwd 0.70, dig_up 0.55, dig_down none: its blade may bury).</summary>
        public static float SlideMaxOf(string clip) =>
            clip == SurveyorAnim.DigFwdNear ? 0.95f : clip == SurveyorAnim.DigFwd ? 0.70f : clip == SurveyorAnim.DigUp ? 0.55f : 0f;
        /// <summary>The slide allowed while no dig clip plays (the tool on the idle glove).</summary>
        public const float FallbackSlideMax = 0.95f;
        /// <summary>The swing's drawings where no dig clip drives the hand: the tool's angle off the line to the target (degrees, + raised):
        /// the wind-up, the CONTACT, the pry, the toss, the recover.</summary>
        static readonly float[] SwingArc = { 55f, 0f, -14f, 26f, 10f };
        /// <summary>The share of the contact's slide and lunge each drawing carries: on the idle glove; on a dig clip (B-246 drew the
        /// slide held over the first four drawings and halved on the recover).</summary>
        static readonly float[] SwingReach = { 0.4f, 1f, 0.8f, 0.3f, 0f };
        static readonly float[] ClipReach = { 1f, 1f, 1f, 1f, 0.5f };

        /// <summary>The forward swing's clip for a target: of dig_fwd (its blade on a face 1.51-2.20 m ahead) and dig_fwd_near (0.57-1.52 m)
        /// the one whose contact glove meets it with the smaller miss. Null where the sheet or its sockets are not in.</summary>
        string ForwardClipFor(Vector2 target, bool left)
        {
            ReadTables();
            if (body == null || handTableDig == null) return null;
            var set = ArtMaterials.ClipsFor(DigSheetKey);
            if (set == null || !set.TryGet(SurveyorAnim.DigFwd, out var far) || !set.TryGet(SurveyorAnim.DigFwdNear, out var near)) return null;
            return Mathf.Abs(ContactMiss(near, target, left)) < Mathf.Abs(ContactMiss(far, target, left)) ? SurveyorAnim.DigFwdNear : SurveyorAnim.DigFwd;
        }

        /// <summary>The tip's miss of `target` on a dig clip's contact drawing, from that drawing's glove (DigPose).</summary>
        float ContactMiss(ArtClip clip, Vector2 target, bool left) =>
            ContactGlove(clip, left, out var glove)
                ? DigPose.Contact(glove, target, RigTools.ShovelBlade, clip.slideMax, RigTools.ShovelLungeM, out _, out _, out _, out _, out _)
                : float.MaxValue;

        /// <summary>The glove of a dig clip's contact drawing in the world, for a facing (the sheet's hand row of that frame under the
        /// surveyor's root as it stands now). False where the sheet's rows are not in.</summary>
        bool ContactGlove(ArtClip clip, bool left, out Vector2 glove)
        {
            glove = default;
            int frame = clip.start + clip.contact;
            if (body == null || handTableDig == null || !handTableDig.Has(frame)) return false;
            glove = body.SquashRoot.TransformPoint(new Vector2(left ? -handTableDig[frame, 0] : handTableDig[frame, 0], handTableDig[frame, 1]));
            return true;
        }
        /// <summary>The body by drawing: its lean toward the target (degrees) and its shift along the line to it (m): back for the
        /// wind-up, into the contact, the recoil, settling. D-196: the lean at most 6 degrees, the recoil at most 0.06 m.</summary>
        static readonly float[] SwingLean = { -3f, 6f, 2f, 1f, 0f };
        static readonly float[] SwingShift = { -0.03f, 0f, -0.06f, -0.02f, 0f };

        /// <summary>The dig tool is at rest (no stroke under way): ready in the hand, or stowed.</summary>
        public bool Carrying { get; private set; }
        /// <summary>At rest and stowed: the shovel over the shoulder, behind the body (ReadySeconds after the last swing).</summary>
        public bool Stowed { get; private set; }
        /// <summary>The slide the swing under way allows (its clip's slide_max).</summary>
        public float SlideMaxNow { get; private set; }
        float readyUntil = -1f;
        /// <summary>The shovel's blade tip now (the tool's place plus its blade along its angle).</summary>
        public Vector2 TipWorld { get; private set; }
        /// <summary>On a swing's contact drawing: how far the tip is from the contact point along the tool (0 on it; above 0 short of it;
        /// under 0 past it, the blade buried). The slide and the lunge that drawing used.</summary>
        public float TipMiss { get; private set; }
        public float SlideNow { get; private set; }
        public float LungeNow { get; private set; }
        /// <summary>The swing under way plays one of the sheet's dig clips (false: the idle glove with the lean, the lunge and the slide).</summary>
        public bool SwingOnClip { get; private set; }
        /// <summary>The held tool is put away this frame: the sheet draws its own in that hand (held_b), or the surveyor flies (U-204 F18).</summary>
        public bool ToolAway { get; private set; }
        /// <summary>U-193 / U-209: the shovel's angle off the line to its target now (degrees; 0 outside a swing and on the contact drawing).</summary>
        public float ScoopArcDegrees { get; private set; }
        public const float ScoopRaise = 55f, ScoopFollow = 14f;

        public SpriteRenderer Reticle { get; private set; }
        public SpriteRenderer Crack { get; private set; }
        public SpriteRenderer Glow { get; private set; }
        public SpriteRenderer Pip { get; private set; }
        public const float PipSize = 0.16f;
        /// <summary>The reticle: the contact its mark stands on (the whiff's point when there is nothing), the middle of its ring (the
        /// brush's circle, or the cell), and what it says: something to dig there; the cursor past the reach.</summary>
        public Vector2 ReticleCentre { get; private set; }
        public Vector2 ReticleAt { get; private set; }
        public bool ReticleDiggable { get; private set; }
        public bool ReticleClamped { get; private set; }
        public int CrackStage { get; private set; }

        /// <summary>DigResponseTests: the frame the last swing was first drawn, the frame the ray last came on, the ray's sheet is in.</summary>
        public int SwingShownFrame { get; private set; } = -1;
        public int RayShownFrame { get; private set; } = -1;
        public bool RayReady => beamSheet != null && beamSheet.Ready;

        float aimVelocity, clipSlide, swingSlide, swingLunge;
        Vector2 swingDir = Vector2.right;
        int swingSeen = -1;
        string strokeClip;

        void LateUpdate()
        {
            if (input == null) return;
            if (lookVersion != Meridian.Progress.SkillStats.Version) { ReadLooks(); Show(input.module); }
            if (shown != input.module || Tool.sprite != tools[(int)input.module]) Show(input.module);

            var stroke = input.Stroke;
            bool digSlot = input.module == RigModule.Beam;
            bool shovel = digSlot && mk[(int)RigModule.Beam] <= 0;
            bool swing = shovel && stroke.Phase == DigPhase.Swing && rig != null;
            bool ray = digSlot && !shovel && stroke.Phase == DigPhase.Beam && rig != null;
            var feet = (Vector2)transform.position;
            // The side the tool is held on: the stroke's target while one runs and the surveyor's own facing at rest (the dig slot); the
            // cursor's side for the other modules.
            bool left = !digSlot ? input.AimWorld.x < feet.x
                : input.StrokeFacing != 0 ? input.StrokeFacing < 0
                : input.controller != null ? input.controller.Facing < 0 : input.AimWorld.x < feet.x;

            // The body's part of the stroke first: the drawn glove moves with it.
            int drawing = swing ? Mathf.Clamp(stroke.Drawing, 0, DigStroke.Drawings - 1) : -1;
            Vector2 target = stroke.Target;
            Vector2 toTarget = swing || ray ? target - rig.DigOrigin : Vector2.zero;
            Vector2 line = toTarget.sqrMagnitude > 1e-6f ? toTarget.normalized : left ? Vector2.left : Vector2.right;
            if (body == null) body = GetComponentInParent<Transform>().GetComponentInChildren<Meridian.View2D.SpriteCharacterView>();
            if (body != null)
            {
                // the surveyor faces the stroke's target for the whole swing; set now, not at the drawn surveyor's own update: the
                // glove is read below, mirrored with the drawing
                int toward = digSlot ? input.StrokeFacing : 0;
                body.StrokeFacing = toward;
                if (toward != 0) body.SetFacing(toward);
            }
            if (swing && input.StrokeStartFrame != swingSeen)
            {
                // a new swing (by the frame it began: the stroke's own counters may be reset): the sheet's dig clip for its direction
                // from its first drawing, where the sheet has one (B-246)
                swingSeen = input.StrokeStartFrame;
                SwingShownFrame = Time.frameCount;
                if (body != null) body.SetStrokePose(Vector2.zero, 0f); // the clips' gloves are measured from the root at rest (a chained swing left its recover's lunge on it)
                strokeClip = SurveyorAnim.DigClipFor(toTarget);
                if (strokeClip == SurveyorAnim.DigFwd || strokeClip == SurveyorAnim.DigFwdNear) strokeClip = ForwardClipFor(target, left) ?? strokeClip;
                SwingOnClip = body != null && body.HasClip(strokeClip);
                clipSlide = SlideMaxOf(strokeClip);
                swingDir = line; swingSlide = swingLunge = 0f;
                if (SwingOnClip && ArtMaterials.ClipsFor(DigSheetKey) is ArtClipSet set && set.TryGet(strokeClip, out var drawn))
                {
                    clipSlide = drawn.slideMax; // the sheet's own number
                    // the swing's slide and lunge, fixed from the clip's CONTACT glove: the other drawings carry them, so the wind-up
                    // holds the blade back by as much as its glove is drawn back and the contact brings it onto the face
                    ReadTables();
                    if (ContactGlove(drawn, left, out var contactGlove))
                        DigPose.Contact(contactGlove, target, RigTools.ShovelBlade, clipSlide, RigTools.ShovelLungeM, out _, out swingDir, out swingSlide, out swingLunge, out _);
                }
            }
            if (!swing && !ray) { SwingOnClip = false; strokeClip = null; }
            // the body's drawing by the stroke's own clock, shown now: the glove read below is this frame's (the Animator on its own
            // clock runs a frame behind the tool)
            if (swing && SwingOnClip) body.ShowStroke(strokeClip, drawing, DigStroke.Drawings, DigStroke.SwingSeconds - stroke.SwingTime + 0.05f);
            else if (ray && body != null)
            {
                // the sheet's aim pose for the direction, held while the ray runs (B-246); shown before the glove is read: the tool is
                // in the raised hand from the press' own frame (played after the read, it stayed at the hip for that frame)
                string pose = SurveyorAnim.AimClipFor(toTarget);
                if (body.HasClip(pose))
                {
                    if (pose != strokeClip) body.PlayStroke(pose, 0.2f); else body.Override(pose, 0.2f);
                    strokeClip = pose;
                }
            }
            float lean = swing && !SwingOnClip ? SwingLean[drawing] * (left ? 1f : -1f) : 0f; // toward the target: clockwise facing right
            Vector2 shift = swing && !SwingOnClip ? line * SwingShift[drawing] : Vector2.zero;
            if (body != null) body.SetStrokePose(shift, lean);

            // U-183 (B-218's hand_socket): the grip on the drawn frame's front glove where BLENDER's pose maths has one, else the fixed hand;
            // hidden where the sheet draws its own tool in that hand (held_b: the dig / build / climb clips).
            bool held;
            HandWorld = DrawnHand(out bool onSocket, out held) is Vector2 h && onSocket ? h : feet + new Vector2(left ? -Hand.x : Hand.x, Hand.y);
            HandOnSocket = onSocket;
            // U-204 F18 (B-228's read of smoke_55): on the jetpack's frames the raised hand held the dig tool straight up over the helmet
            // like a flag: put away while flying, as on the ladder, unless it is in use.
            bool flying = body != null && body.Clip == SurveyorAnim.Jetpack && !input.Using;
            bool away = held || flying;
            ToolAway = away;
            if (Tool.enabled == away) Tool.enabled = !away;

            Vector2 toolAt = HandWorld;
            Carrying = false;
            ScoopArcDegrees = 0f;
            bool stowed = false;
            if (swing || ray) readyUntil = Time.time + ReadySeconds;
            if (swing)
            {
                float blade = RigTools.ShovelBlade;
                // a clip's own slide where the sheet plays it; the idle glove (no dig clip yet) may slide for any direction: it never
                // rises to the stroke as the clips' hand does
                SlideMaxNow = SwingOnClip ? clipSlide : FallbackSlideMax;
                // The contact's slide and lunge: from this frame's glove on the contact drawing (and on the idle glove); on a clip's
                // other drawings the swing's own, fixed from the clip's contact glove. Measured from the wind-up's drawn-back glove the
                // blade would already rest on the face: the thrust would have no travel.
                Vector2 dir = swingDir;
                float slide = swingSlide, lunge = swingLunge, miss = 0f;
                if (!SwingOnClip || drawing == DigStroke.ContactDrawing)
                    miss = DigPose.Contact(HandWorld, target, blade, SlideMaxNow, RigTools.ShovelLungeM, out _, out dir, out slide, out lunge, out _);
                float share = SwingOnClip ? ClipReach[drawing] : SwingReach[drawing];
                // the lunge: the body carries the glove toward a target the blade alone does not reach
                Vector2 carried = dir * (lunge * share);
                if (body != null && carried != Vector2.zero) body.SetStrokePose(shift + carried, lean);
                Vector2 glove = HandWorld + carried;
                float toDeg = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
                float deg;
                if (drawing == DigStroke.ContactDrawing)
                {
                    deg = toDeg;                         // turned to the target, the tip on the contact point
                    toolAt = glove - dir * slide;
                    TipMiss = miss; SlideNow = slide; LungeNow = lunge;
                }
                else
                {
                    // the sheet's own direction for the drawing where a dig clip carries one, else the swing's arc about the line
                    deg = SwingOnClip && HandSocketHasAngle ? (left ? 180f - HandSocketDegrees : HandSocketDegrees)
                        : toDeg + SwingArc[drawing] * (left ? -1f : 1f);
                    if (drawing == DigStroke.Drawings - 1) deg = Mathf.LerpAngle(deg, CarryAngle(left), 0.5f); // the recover meets the ready pose
                    float rad = deg * Mathf.Deg2Rad;
                    toolAt = glove - new Vector2(Mathf.Cos(rad), Mathf.Sin(rad)) * (slide * share);
                }
                HandWorld = glove;
                ScoopArcDegrees = Mathf.DeltaAngle(toDeg, deg);
                AimDegrees = deg;
                aimVelocity = 0f;
            }
            else if (ray)
            {
                Vector2 d = target - HandWorld;
                if (d.sqrMagnitude < 1e-4f) d = left ? Vector2.left : Vector2.right;
                AimDegrees = Mathf.SmoothDampAngle(AimDegrees, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg, ref aimVelocity, BeamDampSeconds);
            }
            else if (digSlot)
            {
                // at rest, whatever the cursor does: ready in the hand for a while after a stroke, then the shovel is stowed
                Carrying = true;
                if (shovel)
                {
                    stowed = Mathf.Floor(Time.time * DigStroke.DrawingsPerSecond) / DigStroke.DrawingsPerSecond >= readyUntil; // on the 12 Hz tick
                    AimDegrees = stowed ? StowAngle(left) : CarryAngle(left);
                    aimVelocity = 0f;
                }
                else AimDegrees = Mathf.SmoothDampAngle(AimDegrees, CarryAngle(left), ref aimVelocity, BeamDampSeconds);
            }
            else
            {
                Vector2 d = input.AimWorld - HandWorld;
                if (d.sqrMagnitude < 1e-4f) d = left ? Vector2.left : Vector2.right;
                AimDegrees = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
                aimVelocity = 0f;
            }
            Stowed = stowed;
            // The dig tool is drawn IN FRONT of the body (LEAD 06:5x: the whole shaft across the torso to its grip, the fist over it;
            // level with the body it was hidden behind the fist and the spade read short); stowed it goes behind. The other modules
            // keep the body's own order.
            int order = Meridian.View2D.SpriteCharacterView.SurveyorOrder + (!digSlot ? 0 : stowed && StowBehind ? -1 : 1);
            if (Tool.sortingOrder != order) Tool.sortingOrder = order;
            var rotation = Quaternion.Euler(0f, 0f, AimDegrees);
            Tool.transform.SetPositionAndRotation(toolAt, rotation);
            Tool.flipY = left; // keep the tool upright when pointing left
            // B-246's fist: the glove closed round the shaft, over the tool at the hand socket and turned with it; not when stowed
            bool fist = digSlot && !away && !stowed && Fist.sprite != null;
            if (Fist.enabled != fist) Fist.enabled = fist;
            if (fist) { Fist.transform.SetPositionAndRotation(HandWorld, rotation); Fist.flipY = left; }
            var muzzle = muzzleOf[(int)input.module];
            if (left) muzzle.y = -muzzle.y;
            MuzzleWorld = toolAt + (Vector2)(rotation * muzzle);
            float a = AimDegrees * Mathf.Deg2Rad;
            TipWorld = toolAt + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * RigTools.ShovelBlade;

            UpdateBeam(ray, target);
            UpdateReticle(digSlot && !away, shovel);
            UpdateSwish(swing, drawing, left);
            UpdateGhost();
            UpdateCable(left);
        }

        /// <summary>The front arm's own angle on the drawn frame (degrees: 0 hanging, positive forward), from the glove's socket where it
        /// carries one (props/rig/hand_socket's third number is the arm's direction, -90 hanging); 0 where it does not.</summary>
        public float ArmDegrees => HandSocketHasAngle ? HandSocketDegrees + 90f : 0f;

        /// <summary>The ready pose's and the stowed pose's tool direction for a side, the arm's swing taken in (degrees, counter-clockwise from +x).</summary>
        public float CarryAngle(bool left) => RestAngle(readyPose, ReadyRadians, ReadySwing, left);
        public float StowAngle(bool left) => RestAngle(stowPose, StowRadians, StowSwing, left);

        float RestAngle(ArtMaterials.ArtSocket pose, float radians, float swing, bool left)
        {
            if (pose != null && pose.stride >= 2 && pose.Has(0)) { radians = pose[0, 0]; swing = pose[0, 1]; }
            float deg = radians * Mathf.Rad2Deg + swing * ArmDegrees;
            return left ? 180f - deg : deg;
        }

        /// <summary>The stowed tool is drawn behind the body (side_dig.json's carry.behind; true where the registry has no carry pose).</summary>
        bool StowBehind => stowPose == null || stowPose.stride < 3 || !stowPose.Has(0) || stowPose[0, 2] > 0.5f;

        /// <summary>U-183: the Beam's cable (B-205: arm-mounted, cable-fed): from the tool's cable_socket to the pack on the surveyor's back
        /// (the jetpack's back socket for the drawn frame; the pack's usual place when there is none), sagging a little.</summary>
        void UpdateCable(bool left)
        {
            bool on = input.module == RigModule.Beam && Tool.sprite != null && Tool.enabled;
            var socket = cableSocket;
            on &= socket != null && socket.Has(0);
            if (Cable.enabled != on) Cable.enabled = on;
            if (!on) return;
            var local = new Vector2(socket[0, 0], left ? -socket[0, 1] : socket[0, 1]);
            CableFrom = (Vector2)Tool.transform.position + (Vector2)(Tool.transform.rotation * local);
            CableTo = JetpackOverlay.PackWorld(body, transform, left);
            var mid = (CableFrom + CableTo) * 0.5f + Vector2.down * CableSag;
            for (int i = 0; i < CablePoints; i++)
            {
                float t = i / (CablePoints - 1f), u = 1f - t;
                var p = u * u * CableFrom + 2f * u * t * mid + t * t * CableTo;
                Cable.SetPosition(i, new Vector3(p.x, p.y, 0.01f));
            }
        }

        /// <summary>Where the ray ends now (its hit on the ground, or its length's end).</summary>
        public Vector2 BeamEnd { get; private set; }

        /// <summary>U-209: the ray runs from the muzzle to the stroke's target (never the tool's damped angle: it is on the target from
        /// the press' own frame), to the first ground it meets; a glow sits on its end where there is something to dig.</summary>
        void UpdateBeam(bool on, Vector2 target)
        {
            on &= beamSheet != null && beamSheet.Ready;
            if (on && !Beam.enabled) RayShownFrame = Time.frameCount;
            if (Beam.enabled != on) Beam.enabled = on;
            bool glow = on && input.Stroke.Diggable;
            if (Glow.enabled != glow) Glow.enabled = glow;
            if (!on) { beamAge = 0f; BeamLength = 0f; return; }
            Vector2 to = target - MuzzleWorld;
            float dist = to.magnitude;
            Vector2 dir = dist > 1e-4f ? to / dist : new Vector2(Mathf.Cos(AimDegrees * Mathf.Deg2Rad), Mathf.Sin(AimDegrees * Mathf.Deg2Rad));
            // To the first terrain hit, at most the Rig's reach, never far past the target.
            float max = Mathf.Min(RigTools.Reach, dist + 0.5f);
            float len = Mathf.Min(max, dist);
            int n = Physics2D.Raycast(MuzzleWorld, dir, AnyCollider, hits, max);
            for (int i = 0; i < n; i++)
                if (hits[i].collider.GetComponentInParent<TerrainChunk>() != null) { len = hits[i].distance; break; }
            BeamLength = len;
            BeamEnd = MuzzleWorld + dir * len;
            beamAge += Time.deltaTime;
            int f = beamSheet.FrameAt(beamAge);
            if (f >= 0 && Beam.sprite != beamSheet.frames[f])
            {
                Beam.sprite = beamSheet.frames[f];
                if (beamSheet.material != null) Beam.sharedMaterial = beamSheet.material;
            }
            Beam.transform.SetPositionAndRotation(MuzzleWorld, Quaternion.Euler(0f, 0f, Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg));
            Beam.size = new Vector2(Mathf.Max(0.01f, len), BeamHeight);
            if (!glow) return;
            bool flare = contactSheet != null && contactSheet.Ready;
            ContactOnArt = flare;
            if (flare)
            {
                // B-246's fx/beam_contact: a six-drawing flare, its up away from the surface (back along the ray), in the Beam's tone
                int k = contactSheet.FrameAt(beamAge);
                if (k >= 0 && Glow.sprite != contactSheet.frames[k]) Glow.sprite = contactSheet.frames[k];
                if (Glow.color != BeamTone) Glow.color = BeamTone;
                Glow.transform.SetPositionAndRotation(new Vector3(BeamEnd.x, BeamEnd.y, 0f), Quaternion.Euler(0f, 0f, Mathf.Atan2(-dir.y, -dir.x) * Mathf.Rad2Deg - 90f));
                Glow.transform.localScale = Vector3.one;
                return;
            }
            if (Glow.sprite != GlowSprite) Glow.sprite = GlowSprite;
            if (Glow.color != GlowTint) Glow.color = GlowTint;
            Glow.transform.SetPositionAndRotation(new Vector3(BeamEnd.x, BeamEnd.y, 0f), Quaternion.identity);
            Glow.transform.localScale = Vector3.one * (GlowSize * (1f + 0.12f * Mathf.Sin(beamAge * 38f))); // a quick flicker: work under way
        }

        // ---------- the reticle ----------

        public static readonly Color ReticleInReach = new Color(1f, 1f, 1f, 0.85f), ReticleAtReach = new Color(1f, 0.78f, 0.35f, 0.9f),
            ReticleNothing = new Color(1f, 1f, 1f, 0.3f), CrackInk = new Color(0.13f, 0.10f, 0.08f, 0.8f), GlowTint = new Color(1f, 0.93f, 0.7f, 0.85f);
        public const float GlowSize = 0.7f, CrackShare = 0.78f, NothingScale = 0.88f, ContactPop = 1.07f;

        /// <summary>Where a dig would land now (the stroke's own target while one runs, else the cursor's through the reach's clamp): the
        /// brush's circle on smooth ground, the cell on block ground; tinted by what it found; the crack mark of the work kept there.</summary>
        void UpdateReticle(bool on, bool shovel)
        {
            // hidden in menus and during a transition (in flight the tool, and the reticle with it, is away)
            on &= rig != null && rig.terrain != null && input.UiFree && !TransitionBusy;
            bool art = reticleSheet != null && reticleSheet.Ready && reticleSheet.frames.Length >= 6;
            ReticleOnArt = on && art;
            if (Reticle.enabled != (on && !art)) Reticle.enabled = on && !art;
            for (int i = 0; i < brackets.Length; i++) if (brackets[i].enabled != (on && art)) brackets[i].enabled = on && art;
            if (!on) { if (Crack.enabled) Crack.enabled = false; if (CrackMask.enabled) CrackMask.enabled = false; if (Pip.enabled) Pip.enabled = false; CrackStage = 0; return; }
            var stroke = input.Stroke;
            Vector2 at; bool diggable, clamped;
            if (stroke.Active) { at = stroke.Target; diggable = stroke.Diggable; clamped = stroke.Clamped; }
            else diggable = rig.DigTarget(input.AimWorld, out at, out clamped);
            bool brush = rig.Brush;
            // D-196b: the reticle's mark is ON the contact; its brackets stand round what opens: the brush's own circle (its centre
            // pushed into the ground from the contact), on block ground the cell the line stops on
            Vector2 centre = diggable ? rig.DigPoint(at) : at;
            if (!brush) { var cell = RigTools.TileOf(centre); centre = new Vector2(cell.x + 0.5f, cell.y + 0.5f); }
            ReticleAt = at; ReticleCentre = centre; ReticleDiggable = diggable; ReticleClamped = clamped;
            // LEAD 06:1x: at full strength while the button is down or the cursor moved in the last 1.5 s, else faded to about 40 %
            bool lively = input.Pressed || stroke.Active || Time.time - input.LastAimMoveTime < ReticleFullSeconds;
            ReticleStrength = Mathf.MoveTowards(ReticleStrength, lively ? 1f : ReticleIdleStrength, Time.deltaTime * ReticleFadePerSecond);
            bool hit = shovel && stroke.Phase == DigPhase.Swing && stroke.Drawing == DigStroke.ContactDrawing; // the hit reads on the mark
            if (art)
            {
                // B-246's fx/dig_reticle: four brackets and a pip, a two-drawing boil; the state by tint and gap
                var tint = !diggable ? ReticleNothingTint : clamped ? ReticleClampedTint : Color.white;
                ReticleTint = tint;
                tint.a = ReticleStrength;
                int boil = (int)(Time.time * ReticleBoilHz) & 1;
                float gap = (!diggable ? NothingGapM : clamped ? ClampedGapM : 0f) + (hit ? ContactGapM : 0f);
                var piece = reticleSheet.frames[(brush ? 0 : 2) + boil];
                for (int i = 0; i < brackets.Length; i++)
                {
                    var b = brackets[i];
                    if (b.sprite != piece) b.sprite = piece;
                    if (b.color != tint) b.color = tint;
                    if (brush)
                    {
                        // an arc sits ON the circle: its pivot on the line, the circle's middle straight below the frame as drawn
                        float a = 45f + 90f * i, rad = a * Mathf.Deg2Rad, r = RigTools.BrushRadius + gap;
                        b.transform.SetPositionAndRotation(new Vector3(centre.x + r * Mathf.Cos(rad), centre.y + r * Mathf.Sin(rad), 0f), Quaternion.Euler(0f, 0f, a - 90f));
                    }
                    else
                    {
                        // a corner's pivot is the cell's top-left corner, its arms right and down; a quarter turn counter-clockwise each for
                        // the bottom-left, the bottom-right, the top-right
                        float h = 0.5f + gap * 0.7071f;
                        float cx = i == 0 || i == 1 ? -h : h, cy = i == 0 || i == 3 ? h : -h;
                        b.transform.SetPositionAndRotation(new Vector3(centre.x + cx, centre.y + cy, 0f), Quaternion.Euler(0f, 0f, 90f * i));
                    }
                }
                if (Pip.enabled != diggable) Pip.enabled = diggable; // no pip where there is nothing to dig
                if (diggable)
                {
                    var cross = reticleSheet.frames[4 + boil];
                    if (Pip.sprite != cross) Pip.sprite = cross;
                    if (Pip.color != tint) Pip.color = tint;
                    Pip.transform.position = new Vector3(at.x, at.y, 0f);
                    Pip.transform.localScale = Vector3.one;
                }
            }
            else
            {
                // the stand-in until the sheet is in: a ring the brush's size (or the cell's box) and a soft dot on the contact
                var tint = !diggable ? ReticleNothing : clamped ? ReticleAtReach : ReticleInReach;
                ReticleTint = tint;
                tint.a *= ReticleStrength;
                if (Pip.enabled != diggable) Pip.enabled = diggable;
                if (diggable)
                {
                    if (Pip.sprite != GlowSprite) Pip.sprite = GlowSprite;
                    if (Pip.color != tint) Pip.color = tint;
                    Pip.transform.position = new Vector3(at.x, at.y, 0f);
                    Pip.transform.localScale = Vector3.one * PipSize;
                }
                var sprite = brush ? Ring : CellBox;
                if (Reticle.sprite != sprite) Reticle.sprite = sprite;
                if (Reticle.color != tint) Reticle.color = tint;
                float size = brush ? 2f * RigTools.BrushRadius : 1f;
                if (!diggable) size *= NothingScale;
                else if (hit) size *= ContactPop;
                Reticle.transform.position = new Vector3(centre.x, centre.y, 0f);
                Reticle.transform.localScale = Vector3.one * size;
            }
            // the crack: the work the target holds, in three stages, on the lump of ground that will open
            int stage = diggable ? DigStroke.StageOf(stroke.WorkAt(at)) : 0;
            CrackStage = stage;
            bool crack = stage > 0;
            if (Crack.enabled != crack) Crack.enabled = crack;
            if (!crack) { if (CrackMask.enabled) CrackMask.enabled = false; return; }
            var chips = brush ? chipRound : chipCell;
            bool chipArt = chips != null && chips.Ready && chips.frames.Length >= DigStroke.ChipStages;
            CrackOnArt = chipArt;
            var mark = chipArt ? chips.frames[stage - 1] : CrackSprite(stage);
            if (Crack.sprite != mark)
            {
                Crack.sprite = mark;
                if (chipArt && chips.material != null) Crack.sharedMaterial = chips.material;
            }
            // B-246: cream and ink, multiplied by the dug ground's tone as the clods are (D-190)
            var ink = chipArt ? Meridian.Mining.DigFeel.ToneAt(rig.terrain, at, rig.D1 ? Meridian.Mining.DigRun.TierAt(rig.terrain, at) : 0) : CrackInk;
            if (Crack.color != ink) Crack.color = ink;
            // LEAD 07:1x: the round crack starts where the blade lands (the contact) and spreads into the ground: shown only on the
            // ground's side of the face there (a mask over the half plane behind the face's own tangent at the contact, from the
            // field's slope; not the ground's exact outline: past an outcrop's corner a line can show over open air). The cell's crack
            // stays on its cell and my stand-in on the brush's centre.
            bool clip = chipArt && brush;
            CrackClipped = clip;
            if (CrackMask.enabled != clip) CrackMask.enabled = clip;
            var inside = clip ? SpriteMaskInteraction.VisibleInsideMask : SpriteMaskInteraction.None;
            if (Crack.maskInteraction != inside) Crack.maskInteraction = inside;
            if (clip)
            {
                if (at != crackAt) { crackAt = at; CrackInto = IntoGround(at, centre - at); }
                var edge = at - CrackInto * CrackMaskBackM; // a hair on the open side: the origin itself is drawn
                CrackMask.transform.SetPositionAndRotation(new Vector3(edge.x, edge.y, 0f), Quaternion.Euler(0f, 0f, Mathf.Atan2(CrackInto.y, CrackInto.x) * Mathf.Rad2Deg - 90f));
                CrackMask.transform.localScale = new Vector3(CrackMaskWideM, CrackMaskDeepM, 1f);
            }
            Vector2 origin = clip ? at : centre;
            Crack.transform.position = new Vector3(origin.x, origin.y, 0f);
            Crack.transform.localScale = Vector3.one * (chipArt ? (brush ? RigTools.BrushRadius / 0.9f : 1f) : (brush ? 2f * RigTools.BrushRadius : 1f) * CrackShare);
        }

        /// <summary>The crack's mask: a square over the ground's side of the face at the contact (its lower edge on the face's tangent).</summary>
        public SpriteMask CrackMask { get; private set; }
        public const float CrackMaskWideM = 4f, CrackMaskDeepM = 2.5f, CrackMaskBackM = 0.04f;
        /// <summary>Tests: the crack is drawn from the contact, clipped to the ground's side; the direction into the ground there.</summary>
        public bool CrackClipped { get; private set; }
        public Vector2 CrackInto { get; private set; } = Vector2.down;
        Vector2 crackAt = new Vector2(float.NaN, float.NaN);

        /// <summary>The direction into the ground at a contact: up the drawn field's slope there (solid is the higher side); the stroke's
        /// own line where the field is flat (a crystal, a built piece, a find standing in open air).</summary>
        Vector2 IntoGround(Vector2 at, Vector2 line)
        {
            const float h = 0.2f;
            var t = rig.terrain;
            var slope = new Vector2(t.FieldAt(at + new Vector2(h, 0f)) - t.FieldAt(at - new Vector2(h, 0f)), t.FieldAt(at + new Vector2(0f, h)) - t.FieldAt(at - new Vector2(0f, h)));
            if (slope.sqrMagnitude > 1e-6f) return slope.normalized;
            return line.sqrMagnitude > 1e-8f ? line.normalized : Vector2.down;
        }

        static Sprite maskSquare;
        /// <summary>A 1 m white square, its pivot the middle of its lower edge (the crack's mask), made once.</summary>
        static Sprite MaskSquare
        {
            get
            {
                if (maskSquare == null)
                {
                    var white = Texture2D.whiteTexture;
                    maskSquare = Sprite.Create(white, new Rect(0f, 0f, white.width, white.height), new Vector2(0.5f, 0f), white.width, 0, SpriteMeshType.FullRect);
                    maskSquare.name = "DigCrackMask";
                }
                return maskSquare;
            }
        }

        // ---------- B-246's dig fx (sheet 2), each a stand-in of mine until its sheet is in ----------

        public const string ReticleKey = "fx/dig_reticle/base", ChipRoundKey = "fx/dig_chip/round", ChipCellKey = "fx/dig_chip/cell",
            BeamContactKey = "fx/beam_contact/base", SwishKey = "fx/shovel_swish/base";
        /// <summary>The reticle's states on the art: untinted and tight in reach; mustard and pushed out 0.09 m where the cursor is past
        /// the reach; red and pushed out 0.2 m with no pip where there is nothing to dig; a small push on the contact drawing.</summary>
        public static readonly Color ReticleClampedTint = new Color(0.851f, 0.663f, 0.247f, 1f), ReticleNothingTint = new Color(0.784f, 0.333f, 0.239f, 1f);
        public const float ClampedGapM = 0.09f, NothingGapM = 0.2f, ContactGapM = 0.05f;
        /// <summary>LEAD's rule: full strength for this long after the cursor moves (and while the button is down), else this share; the
        /// boil's rate (the two drawings on twos).</summary>
        public const float ReticleFullSeconds = 1.5f, ReticleIdleStrength = 0.4f, ReticleFadePerSecond = 4f, ReticleBoilHz = 6f;
        /// <summary>The Beam's own tone its contact flare is multiplied by (the Mk1 ray's teal; the Mks' colours are not in data yet).</summary>
        public static readonly Color BeamTone = new Color(0.36f, 0.78f, 0.72f, 1f);
        /// <summary>The swish is drawn from level to this far below (its json's arc); turned so its end lies on the blade.</summary>
        public const float SwishArcDegrees = 75f;

        FxSheet reticleSheet, chipRound, chipCell, contactSheet, swishSheet;
        readonly SpriteRenderer[] brackets = new SpriteRenderer[4];
        /// <summary>The reticle's four brackets (the art's; off while the stand-in ring draws) and the shovel's swish.</summary>
        public SpriteRenderer Bracket(int i) => brackets[i];
        public SpriteRenderer Swish { get; private set; }
        /// <summary>Tests: the reticle, the crack and the contact flare draw B-246's art (false: my stand-ins); the reticle's strength
        /// (1 lively, 0.4 idle) and its state's tint before the strength.</summary>
        public bool ReticleOnArt { get; private set; }
        public bool CrackOnArt { get; private set; }
        public bool ContactOnArt { get; private set; }
        public float ReticleStrength { get; private set; } = 1f;
        public Color ReticleTint { get; private set; }

        Meridian.Transitions.TransitionDirector director;
        float directorSearchAt;
        /// <summary>A climb or an entry runs (looked for once a second until found).</summary>
        bool TransitionBusy
        {
            get
            {
                if (director == null && Time.unscaledTime >= directorSearchAt)
                {
                    director = FindAnyObjectByType<Meridian.Transitions.TransitionDirector>();
                    directorSearchAt = Time.unscaledTime + 1f;
                }
                return director != null && director.Busy;
            }
        }

        void LoadDigFx()
        {
            reticleSheet = FxSheet.Get(ReticleKey);
            chipRound = FxSheet.Get(ChipRoundKey);
            chipCell = FxSheet.Get(ChipCellKey);
            contactSheet = FxSheet.Get(BeamContactKey);
            swishSheet = FxSheet.Get(SwishKey);
            // the reticle is a mark on the screen, not a thing in the world: unlit, so it reads the same in a dark hole
            var unlit = ArtMaterials.Active != null ? ArtMaterials.Active.unlit : null;
            if (unlit != null) { foreach (var b in brackets) b.sharedMaterial = unlit; Pip.sharedMaterial = unlit; Reticle.sharedMaterial = unlit; Glow.sharedMaterial = unlit; }
        }

        Vector2 swishAt;
        float swishDeg;

        /// <summary>B-246's fx/shovel_swish on the arcs (dig_down, dig_up; not on the thrusts): its three drawings on the contact, the
        /// follow-through and the settle, its pivot (the swing's centre) on the contact drawing's tool origin (the glove where the
        /// tool did not slide), turned so its end lies on the blade, mirrored with the facing; dig_up's swing is upward: mirrored in y.</summary>
        public Vector2 SwishAt => swishAt;
        void UpdateSwish(bool swing, int drawing, bool left)
        {
            bool arc = strokeClip == SurveyorAnim.DigDown || strokeClip == SurveyorAnim.DigUp;
            int f = drawing - DigStroke.ContactDrawing;
            bool on = swing && SwingOnClip && arc && swishSheet != null && swishSheet.Ready && f >= 0 && f < swishSheet.frames.Length;
            if (Swish.enabled != on) Swish.enabled = on;
            if (!on) return;
            // the contact drawing's tool: its own origin (the glove, less the slide a near target took: from the glove itself a slid
            // tool's swish stood a slide's length past the blade, in the ground over a ceiling) and its angle: the arc ends on the blade
            if (f == 0) { swishAt = Tool.transform.position; swishDeg = AimDegrees; }
            if (Swish.sprite != swishSheet.frames[f])
            {
                Swish.sprite = swishSheet.frames[f];
                if (swishSheet.material != null) Swish.sharedMaterial = swishSheet.material;
            }
            bool up = strokeClip == SurveyorAnim.DigUp;
            float asRight = left ? 180f - swishDeg : swishDeg;                   // the tool's angle as drawn facing right
            float turn = up ? asRight - SwishArcDegrees : asRight + SwishArcDegrees;
            Swish.flipX = left; Swish.flipY = up;
            Swish.transform.SetPositionAndRotation(new Vector3(swishAt.x, swishAt.y, 0f), Quaternion.Euler(0f, 0f, left ? -turn : turn));
        }

        static Sprite ring, cellBox, glowSprite;
        static readonly Sprite[] cracks = new Sprite[DigStroke.ChipStages];

        /// <summary>U-157: a 1 m anti-aliased ring (the brush ghost and the dig's reticle until B-246's fx/dig_reticle), made once.</summary>
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

        /// <summary>U-209: a 1 m cell's outline (the reticle on block ground), made once.</summary>
        static Sprite CellBox
        {
            get
            {
                if (cellBox != null) return cellBox;
                const int N = 64;
                var tex = new Texture2D(N, N, TextureFormat.RGBA32, false) { name = "DigCellBox", wrapMode = TextureWrapMode.Clamp };
                var px = new Color32[N * N];
                for (int y = 0; y < N; y++)
                    for (int x = 0; x < N; x++)
                    {
                        int edge = Mathf.Min(Mathf.Min(x, N - 1 - x), Mathf.Min(y, N - 1 - y));
                        float a = edge < 3 ? 1f : edge < 5 ? 0.5f : 0.14f;
                        px[y * N + x] = new Color32(255, 255, 255, (byte)(a * 255f));
                    }
                tex.SetPixels32(px);
                tex.Apply(false, true);
                cellBox = Sprite.Create(tex, new Rect(0, 0, N, N), new Vector2(0.5f, 0.5f), N);
                cellBox.name = "DigCellBox";
                return cellBox;
            }
        }

        /// <summary>U-209: the Beam's glow at its hit until B-246's fx/beam_contact: a soft 1 m disc, made once.</summary>
        static Sprite GlowSprite
        {
            get
            {
                if (glowSprite != null) return glowSprite;
                const int N = 64;
                var tex = new Texture2D(N, N, TextureFormat.RGBA32, false) { name = "BeamGlow", wrapMode = TextureWrapMode.Clamp };
                var px = new Color32[N * N];
                for (int y = 0; y < N; y++)
                    for (int x = 0; x < N; x++)
                    {
                        float d = Mathf.Sqrt((x + 0.5f - N * 0.5f) * (x + 0.5f - N * 0.5f) + (y + 0.5f - N * 0.5f) * (y + 0.5f - N * 0.5f)) / (N * 0.5f);
                        float a = Mathf.Clamp01(1f - d);
                        px[y * N + x] = new Color32(255, 255, 255, (byte)(a * a * 255f));
                    }
                tex.SetPixels32(px);
                tex.Apply(false, true);
                glowSprite = Sprite.Create(tex, new Rect(0, 0, N, N), new Vector2(0.5f, 0.5f), N);
                glowSprite.name = "BeamGlow";
                return glowSprite;
            }
        }

        /// <summary>U-209: the crack mark of a worked target, stage 1..3, until B-246's fx/dig_chip: ink lines running out from the
        /// middle of a 1 m disc (three, five, seven; each longer), drawn once a stage with a fixed seed.</summary>
        static Sprite CrackSprite(int stage)
        {
            int s = Mathf.Clamp(stage, 1, DigStroke.ChipStages) - 1;
            if (cracks[s] != null) return cracks[s];
            const int N = 128;
            var alpha = new float[N * N];
            var rng = new System.Random(209 + s);
            int branches = 3 + 2 * s;
            float reach = N * (0.22f + 0.11f * s);
            for (int k = 0; k < branches; k++)
            {
                float angle = (k + (float)rng.NextDouble() * 0.6f) * 2f * Mathf.PI / branches;
                float x = N * 0.5f, y = N * 0.5f, length = reach * (0.7f + 0.3f * (float)rng.NextDouble());
                for (float run = 0f; run < length; run += 1f)
                {
                    if ((int)run % 7 == 6) angle += ((float)rng.NextDouble() - 0.5f) * 0.9f; // a crack turns as it runs
                    x += Mathf.Cos(angle); y += Mathf.Sin(angle);
                    float half = Mathf.Lerp(1.9f, 0.7f, run / length); // thinner toward its end
                    int x0 = Mathf.Max(0, (int)(x - 3f)), x1 = Mathf.Min(N - 1, (int)(x + 3f)), y0 = Mathf.Max(0, (int)(y - 3f)), y1 = Mathf.Min(N - 1, (int)(y + 3f));
                    for (int py = y0; py <= y1; py++)
                        for (int qx = x0; qx <= x1; qx++)
                        {
                            float d = Mathf.Sqrt((qx + 0.5f - x) * (qx + 0.5f - x) + (py + 0.5f - y) * (py + 0.5f - y));
                            float v = Mathf.Clamp01(half + 0.5f - d);
                            if (v > alpha[py * N + qx]) alpha[py * N + qx] = v;
                        }
                }
            }
            var tex = new Texture2D(N, N, TextureFormat.RGBA32, false) { name = "DigCrack" + (s + 1), wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[N * N];
            for (int i = 0; i < px.Length; i++) px[i] = new Color32(255, 255, 255, (byte)(alpha[i] * 255f));
            tex.SetPixels32(px);
            tex.Apply(false, true);
            cracks[s] = Sprite.Create(tex, new Rect(0, 0, N, N), new Vector2(0.5f, 0.5f), N);
            cracks[s].name = "DigCrack" + (s + 1);
            return cracks[s];
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
