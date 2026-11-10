using System.Collections.Generic;
using Meridian.Art;
using Meridian.Player;
using Meridian.Rendering;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.View2D
{
    /// <summary>
    /// U-094 (Bible §9.4 v4, contract v3.0 §11.2): draws a v3 sprite-sheet character (the surveyor, a critter). A squash
    /// root at the feet (SquashStretch scales it, never the collider) holds one SpriteRenderer + Animator. The importer's
    /// controller ("&lt;key&gt;/animator", 12 fps clips) plays the clips; until it exists the sheet's frames step on the
    /// SheetClock from the clip registry, so placeholders animate too. Facing is a runtime flip (sheets face right).
    /// With `player` set it picks the surveyor's clip each frame (SurveyorAnim → the v3 clip set). No allocation per frame.
    /// </summary>
    public sealed class SpriteCharacterView : MonoBehaviour
    {
        public string key;
        /// <summary>Optional: drive the clip from this surveyor (PlanetSideRoot sets it in cartoon mode).</summary>
        public PlayerController player;
        /// <summary>U-200 (LEAD's read of 0.6.1's smoke_47 / 65 / 66: the surveyor stood half hidden behind the rocket's fin and foot pad at
        /// the camp's first view): the drawn surveyor draws in front of the Pilgrim's side rig, whose parts take 10..17 from the ship's
        /// renderer (at 6 it was behind all of them), and in front of every flora part (3..8); still under the underwater veil (20) and
        /// the weather tints (30). The tool in the hand and the Grapple's line follow it.</summary>
        public const int SurveyorOrder = 18;
        public int sortingOrder = SurveyorOrder;

        public Transform SquashRoot { get; private set; }
        public SpriteRenderer Renderer { get; private set; }
        public Animator Animator { get; private set; }
        public SquashStretch Squash { get; } = new SquashStretch();
        public string Clip { get; private set; } = "idle";
        /// <summary>The drawing shown now, within the current clip (fallback stepping) or -1 while the Animator draws.</summary>
        public int Frame { get; private set; }
        public bool Ready => frames != null || Animator.runtimeAnimatorController != null;
        public bool UsesAnimator => Animator != null && Animator.runtimeAnimatorController != null;

        AsyncOperationHandle<IList<Sprite>> sheetHandle;
        AsyncOperationHandle<RuntimeAnimatorController> controllerHandle;
        Sprite[] frames;
        ArtClipSet clips;
        ArtClip current;
        bool hasCurrent;
        float clipTime, sinceLand = 99f, sinceBump = 99f, sinceJump = 99f, landSpeed;
        int facing = 1;
        bool hooked;

        void Awake()
        {
            var root = new GameObject("SquashRoot");
            root.transform.SetParent(transform, false);
            SquashRoot = root.transform;
            Renderer = root.AddComponent<SpriteRenderer>();
            Renderer.sortingOrder = sortingOrder;
            Animator = root.AddComponent<Animator>();
            Animator.cullingMode = AnimatorCullingMode.AlwaysAnimate; // an empty renderer has no bounds: a culled Animator would never set its first sprite
            root.AddComponent<AnimationEventRelay>().view = this; // U-105: the clips' events land on the Animator's object
            // U-122 (c): the suit badge on the pack (a tier-coloured chip; the tint rides the renderer colour).
            var bgo = new GameObject("SuitBadge");
            bgo.transform.SetParent(root.transform, false);
            bgo.transform.localPosition = new Vector3(-BadgeBack, BadgeHeight, 0f);
            bgo.transform.localScale = Vector3.one * (BadgeSize / BadgeSprite().bounds.size.x);
            Badge = bgo.AddComponent<SpriteRenderer>();
            Badge.sprite = BadgeSprite();
            Badge.sortingOrder = sortingOrder + 1;
            Badge.enabled = false;
            var state = Meridian.Core.GameState.Instance;
            SetSuitTier(state != null ? state.suitTier : 0);
            Meridian.Hazards.HazardSystem.SuitEquipped += SetSuitTier;
        }

        /// <summary>U-105: the surprise clip's eye-pop frame (an animation event from SheetAnimatorBuilder); FX hook.</summary>
        public event System.Action EyePop;
        /// <summary>U-105: the dash clip's smear start and end frames; FX hook.</summary>
        public event System.Action SmearStart, SmearEnd;
        internal void RaiseEyePop() => EyePop?.Invoke();
        internal void RaiseSmear(bool start) { if (start) SmearStart?.Invoke(); else SmearEnd?.Invoke(); }

        void Start() { if (!string.IsNullOrEmpty(key)) Load(key); }

        /// <summary>Loads (or swaps to) a sheet key: its frames and, when the importer built one, its 12 fps controller.</summary>
        public void Load(string sheetKey)
        {
            Release();
            key = sheetKey;
            clips = ArtMaterials.ClipsFor(sheetKey);
            hasCurrent = false;
            Probe<IList<Sprite>>(sheetKey, h => { sheetHandle = h; h.Completed += op => { if (this != null && op.Status == AsyncOperationStatus.Succeeded && op.Result != null) { frames = new Sprite[op.Result.Count]; op.Result.CopyTo(frames, 0); Apply(); } }; });
            Probe<RuntimeAnimatorController>(SheetClock.ControllerAddress(sheetKey), h => { controllerHandle = h; h.Completed += op => { if (this != null && op.Status == AsyncOperationStatus.Succeeded && op.Result != null) { Animator.runtimeAnimatorController = op.Result; Play(Clip, true); } }; });
        }

        /// <summary>A sprite list cannot be found by type (an Editor location probe for IList&lt;Sprite&gt; returns nothing): probe untyped and load by key.</summary>
        void Probe<T>(string address, System.Action<AsyncOperationHandle<T>> load)
        {
            bool spriteList = typeof(T) == typeof(IList<Sprite>);
            var probe = spriteList ? Addressables.LoadResourceLocationsAsync(address) : Addressables.LoadResourceLocationsAsync(address, typeof(T));
            probe.Completed += l =>
            {
                IResourceLocation loc = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0 ? l.Result[0] : null;
                ArtLoad.Release(l);
                if (loc == null || this == null) return;
                load(spriteList ? ArtLoad.Asset<T>(address) : ArtLoad.Asset<T>(loc, key));
            };
        }

        /// <summary>Plays `clip` (or the nearest v3 stand-in the sheet has) from its start; no-op when it already plays.</summary>
        public void Play(string clip, bool restart = false)
        {
            string want = Resolve(clip);
            if (!restart && want == Clip) return;
            Clip = want;
            clipTime = 0f;
            hasCurrent = clips != null && clips.TryGet(want, out current) && current.length > 0;
            if (UsesAnimator)
            {
                int hash = UnityEngine.Animator.StringToHash(want);
                if (Animator.HasState(0, hash)) Animator.Play(hash, 0, 0f);
            }
        }

        /// <summary>U-101: plays `clip` for `seconds` whatever the surveyor does (the contact sheet's look_camera); 0 clears it.</summary>
        public void Override(string clip, float seconds) { overrideClip = clip; overrideUntil = Time.time + seconds; }
        string overrideClip; float overrideUntil;

        // ---- U-209 (D-196): the dig stroke on the drawn surveyor ----

        /// <summary>The sheet (or its controller) has this clip by its own name (no stand-in).</summary>
        public bool HasClip(string clip) => !string.IsNullOrEmpty(clip) && Has(clip);

        /// <summary>Plays a stroke's clip from its first drawing for `seconds` (a swing's dig_down / dig_fwd / dig_up, a Beam aim pose)
        /// when the sheet has it by name; false, and nothing changes, when it has not (B-246's clips arrive by key).</summary>
        public bool PlayStroke(string clip, float seconds)
        {
            if (!HasClip(clip)) return false;
            Override(clip, seconds);
            Play(clip, true);
            return true;
        }

        /// <summary>The side the stroke under way faces (-1 / 1; 0: the surveyor's own facing). The flip waits for the swing's end.</summary>
        public int StrokeFacing { get; set; }
        /// <summary>The stroke's pose on the squash root: an offset from the feet (the lunge toward a far target, the recoil at the
        /// contact; m) and a lean about the feet (degrees, counter-clockwise). Zero outside a stroke.</summary>
        public Vector2 StrokeOffset { get; private set; }
        public float StrokeLean { get; private set; }
        /// <summary>Sets the stroke's pose now (RigToolView, before it places the tool on the drawn hand); held off while climb_in
        /// carries the root to the ship's door.</summary>
        public void SetStrokePose(Vector2 offset, float leanDegrees)
        {
            if (ClimbingIn) { offset = Vector2.zero; leanDegrees = 0f; }
            if (offset != StrokeOffset) { StrokeOffset = offset; if (climbUntil <= 0f) SquashRoot.localPosition = new Vector3(offset.x, offset.y, 0f); }
            if (!Mathf.Approximately(leanDegrees, StrokeLean)) { StrokeLean = leanDegrees; SquashRoot.localRotation = Quaternion.Euler(0f, 0f, leanDegrees); }
        }

        public void SetFacing(int dir)
        {
            if (dir == 0) return;
            facing = dir > 0 ? 1 : -1;
            Renderer.flipX = facing < 0;
            if (Badge != null) { var p = Badge.transform.localPosition; p.x = -facing * BadgeBack; Badge.transform.localPosition = p; } // the pack is on the back
        }

        /// <summary>A v3 sheet has its own clip set (contract §11.2); old names fall back to the closest one it has.</summary>
        /// <summary>The clip itself, else its named stand-in on this sheet (SurveyorAnim.ResolveOn, U-105), else idle.</summary>
        string Resolve(string clip) => SurveyorAnim.ResolveOn(clip, Has);

        bool Has(string clip)
        {
            if (clips != null && clips.TryGet(clip, out _)) return true;
            return UsesAnimator && Animator.HasState(0, UnityEngine.Animator.StringToHash(clip));
        }

        void Hook()
        {
            if (hooked || player == null) return;
            hooked = true;
            player.Landed += OnLanded;
            player.Jumped += OnJumped;
            player.Bumped += OnBumped;
            // U-203: no dig hook. side_b's dig and build clips carry a baked pick and hammer (props/rig/hand_socket held_b), and the held
            // tool hides on those frames: since U-121 every stroke had ended in a pick swing with the shovel or the Beam gone from the hand
            // (BLENDER's read of 0.6.1's smoke_66). The body keeps its stand / walk pose through a stroke and the tool in the hand carries it
            // (RigToolView: the shovel's scoop arc, the Beam's ray).
        }

        void OnLanded(float speed) { sinceLand = 0f; landSpeed = speed; Squash.Land(speed); }
        void OnJumped() { sinceJump = 0f; Squash.TakeOff(); }
        void OnBumped() { sinceBump = 0f; Squash.Hit(); flashFrames = FlashFrames; }

        /// <summary>U-122 (U-089): the two white frames on a bump; Flashing while they last. Tests read it.</summary>
        public const int FlashFrames = 2;
        public bool Flashing => flashFrames > 0;
        int flashFrames;
        static readonly Color FlashTint = new Color(1.6f, 1.6f, 1.6f, 1f); // U-089's over-white, as PlayerView and Creature
        Color suitTint = Color.white;

        // ---- U-122 (c) (D-135): Envirosuit tiers on the drawn surveyor are a tint and a badge on the pack, not new sheets ----
        public int SuitTier { get; private set; }
        public SpriteRenderer Badge { get; private set; }
        public bool BadgeShown => Badge != null && Badge.enabled;
        public const float BadgeSize = 0.16f, BadgeBack = 0.26f, BadgeHeight = 1.05f;
        /// <summary>The suit tint per tier: none at 0, a faint cool wash at Mk1, steel at Mk2, warm gold at Mk3. Pure.</summary>
        public static Color TintFor(int tier) => tier >= 3 ? new Color(1f, 0.92f, 0.78f) : tier == 2 ? new Color(0.84f, 0.9f, 1f) : tier == 1 ? new Color(0.92f, 0.97f, 1f) : Color.white;
        /// <summary>The badge colour per tier (clear = no badge at 0): Mk1 teal, Mk2 steel blue, Mk3 gold. Pure.</summary>
        public static Color BadgeFor(int tier) => tier >= 3 ? new Color(1f, 0.8f, 0.25f) : tier == 2 ? new Color(0.45f, 0.65f, 0.95f) : tier == 1 ? new Color(0.3f, 0.75f, 0.7f) : Color.clear;
        static Sprite badgeSprite;
        static Sprite BadgeSprite()
        {
            if (badgeSprite == null) { badgeSprite = Sprite.Create(Texture2D.whiteTexture, new Rect(0, 0, 4, 4), new Vector2(0.5f, 0.5f), 100f); badgeSprite.name = "SuitBadge"; }
            return badgeSprite;
        }
        /// <summary>Sets the tier (HazardSystem.SuitEquipped, and the saved tier at Awake): the tint on the renderer, the badge on the pack.</summary>
        public void SetSuitTier(int tier)
        {
            SuitTier = Mathf.Clamp(tier, 0, 3);
            suitTint = TintFor(SuitTier);
            if (Renderer != null && flashFrames == 0) Renderer.color = suitTint;
            if (Badge != null)
            {
                Badge.enabled = SuitTier >= 1;
                Badge.color = BadgeFor(SuitTier);
                if (Renderer != null && Badge.sharedMaterial != Renderer.sharedMaterial) Badge.sharedMaterial = Renderer.sharedMaterial;
            }
        }

        // ---- U-115 follow-up: climb_in carries the drawn surveyor from the ground to the ship's door socket over the clip ----
        public bool ClimbingIn => climbUntil > 0f && Time.time < climbUntil;
        Vector3 climbFrom, climbTo; float climbStart, climbUntil;
        /// <summary>Seconds of a clip: the sheet's own at the contract's 12 fps, else the controller's clip of that name (D-121: side_b's clips live only in the controller); 0 when neither has it.</summary>
        public float ClipSeconds(string clip)
        {
            if (clips != null && clips.TryGet(clip, out var c) && c.length > 0) return c.length / 12f;
            var controller = Animator != null ? Animator.runtimeAnimatorController : null;
            if (controller == null) return 0f;
            foreach (var ac in controller.animationClips)
                if (ac != null && (ac.name == clip || ac.name.EndsWith("_" + clip, System.StringComparison.Ordinal))) return ac.length;
            return 0f;
        }
        /// <summary>Plays climb_in for its length (0.75 s when the sheet has none yet) while the sprite root rises from the feet to `doorWorld` (eased in); the root snaps back when it ends. Returns the seconds.</summary>
        public float ClimbTo(Vector3 doorWorld)
        {
            float seconds = ClipSeconds(SurveyorAnim.ClimbIn);
            if (seconds <= 0f) seconds = 0.75f;
            climbFrom = SquashRoot.localPosition;
            climbTo = transform.InverseTransformPoint(doorWorld);
            climbStart = Time.time; climbUntil = Time.time + seconds;
            Override(SurveyorAnim.ClimbIn, seconds);
            return seconds;
        }
        void StepClimb()
        {
            if (climbUntil <= 0f) return;
            if (Time.time < climbUntil)
            {
                float k = Mathf.Clamp01((Time.time - climbStart) / Mathf.Max(0.01f, climbUntil - climbStart));
                SquashRoot.localPosition = Vector3.Lerp(climbFrom, climbTo, k * k);
            }
            else { SquashRoot.localPosition = climbFrom; climbUntil = 0f; }
        }

        void LateUpdate()
        {
            float dt = Time.deltaTime;
            StepFlash();
            if (player != null)
            {
                Hook();
                sinceLand += dt; sinceBump += dt; sinceJump += dt;
                var v = player.Body != null ? player.Body.linearVelocity : Vector2.zero;
                var vitals = player.Vitals;
                var input = new AnimInputs
                {
                    dead = vitals != null && vitals.Dead, grounded = player.Grounded, vx = v.x, vy = v.y,
                    sinceBuild = 99f, sinceSurprise = 99f, sinceHurt = 99f, sinceLand = sinceLand, sinceDig = 99f, sinceBump = sinceBump, sinceJump = sinceJump,
                    landSpeed = landSpeed, dashing = player.Dash.Active, jetpacking = player.Jetpack != null && player.Jetpack.Firing, climbingIn = ClimbingIn,
                    ladder = player.ClimbingOn == Meridian.Player.ClimbKind.Ladder, reeling = player.Reeling || player.ClimbingOn == Meridian.Player.ClimbKind.Winch,
                };
                Play(overrideClip != null && Time.time < overrideUntil ? overrideClip : SurveyorAnim.Pick(input));
                SetFacing(StrokeFacing != 0 ? StrokeFacing : player.Facing); // U-209: a swing holds the side of its target
            }
            SquashRoot.localScale = Squash.Step(dt);
            // U-176 (B-210): climb_ladder steps 0.5 m a cycle (8 frames at 12 fps): it paces with the climb, still on a rung; reel_up runs
            // while a line pulls, still while the surveyor hangs
            float pace = 1f;
            if (player != null && Clip == Meridian.Player.SurveyorAnim.ClimbLadder) pace = Mathf.Min(4f, Mathf.Abs(player.ClimbRate) / LadderCycle);
            else if (player != null && Clip == Meridian.Player.SurveyorAnim.ReelUp) pace = player.Reeling || Mathf.Abs(player.ClimbRate) > 0.05f ? 1.5f : 0f;
            if (UsesAnimator && !Mathf.Approximately(Animator.speed, pace)) Animator.speed = pace;
            clipTime += dt * pace;
            Apply();
            StepClimb();
        }

        /// <summary>U-176: climb_ladder's climb a second at its own pace (B-210: 0.5 m a cycle of 8 frames at 12 fps).</summary>
        public const float LadderCycle = 0.75f;

        /// <summary>Fallback drawing while no controller is loaded: the clip's frame on the 12 fps clock.</summary>
        void Apply()
        {
            if (frames == null || frames.Length == 0) return;
            if (UsesAnimator) { Frame = -1; if (Renderer.sprite == null) Renderer.sprite = frames[0]; return; } // the controller draws from its next update
            int f = hasCurrent ? current.start + SheetClock.Frame(clipTime, current.length, current.loop) : 0;
            if (f < 0 || f >= frames.Length) f = 0;
            Frame = hasCurrent ? f - current.start : 0;
            if (Renderer.sprite != frames[f]) Renderer.sprite = frames[f];
        }

        void Release()
        {
            if (sheetHandle.IsValid()) ArtLoad.Release(sheetHandle);
            if (controllerHandle.IsValid()) ArtLoad.Release(controllerHandle);
            sheetHandle = default; controllerHandle = default;
            frames = null;
            if (Animator != null) Animator.runtimeAnimatorController = null;
        }

        /// <summary>The flash: the renderer white for FlashFrames frames after a bump, its own tint back after (no material swap, no allocation).</summary>
        void StepFlash()
        {
            if (Renderer == null) return;
            if (flashFrames > 0)
            {
                Renderer.color = FlashTint;
                flashFrames--;
                if (flashFrames == 0) Renderer.color = suitTint;
            }
        }

        void OnDestroy()
        {
            Meridian.Hazards.HazardSystem.SuitEquipped -= SetSuitTier;
            if (hooked && player != null) { player.Landed -= OnLanded; player.Jumped -= OnJumped; player.Bumped -= OnBumped; }
            Release();
        }
    }
    /// <summary>U-105: receives the sheet clips' animation events on the Animator's object and hands them to the view.</summary>
    public sealed class AnimationEventRelay : MonoBehaviour
    {
        public SpriteCharacterView view;
        void OnEyePop() { if (view != null) view.RaiseEyePop(); }
        void OnSmear() { if (view != null) view.RaiseSmear(true); }
        void OnSmearEnd() { if (view != null) view.RaiseSmear(false); }
    }
}
