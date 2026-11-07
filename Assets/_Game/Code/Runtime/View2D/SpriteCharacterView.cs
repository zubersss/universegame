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
        public int sortingOrder = 6;

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
        float clipTime, sinceLand = 99f, sinceBump = 99f, sinceJump = 99f, sinceDig = 99f, landSpeed;
        Meridian.Rig.RigTools rig;
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

        public void SetFacing(int dir) { if (dir != 0) { facing = dir > 0 ? 1 : -1; Renderer.flipX = facing < 0; } }

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
            rig = player.GetComponentInChildren<Meridian.Rig.RigTools>(true);
            if (rig == null) rig = player.GetComponentInParent<Meridian.Rig.RigTools>();
            if (rig == null) rig = FindAnyObjectByType<Meridian.Rig.RigTools>(); // PlanetSideRoot's rig (side.rig), once
            if (rig != null) rig.Dug += OnDug; // U-121: the drawn surveyor digs like PlayerView does (side_b's dig clip, U-115)
        }
        void OnDug(Vector2 at) => sinceDig = 0f;

        void OnLanded(float speed) { sinceLand = 0f; landSpeed = speed; Squash.Land(speed); }
        void OnJumped() { sinceJump = 0f; Squash.TakeOff(); }
        void OnBumped() { sinceBump = 0f; Squash.Hit(); }

        void LateUpdate()
        {
            float dt = Time.deltaTime;
            if (player != null)
            {
                Hook();
                sinceLand += dt; sinceBump += dt; sinceJump += dt; sinceDig += dt;
                var v = player.Body != null ? player.Body.linearVelocity : Vector2.zero;
                var vitals = player.Vitals;
                var input = new AnimInputs
                {
                    dead = vitals != null && vitals.Dead, grounded = player.Grounded, vx = v.x, vy = v.y,
                    sinceBuild = 99f, sinceSurprise = 99f, sinceHurt = 99f, sinceLand = sinceLand, sinceDig = sinceDig, sinceBump = sinceBump, sinceJump = sinceJump,
                    landSpeed = landSpeed, dashing = player.Dash.Active, jetpacking = player.Jetpack != null && player.Jetpack.Firing,
                };
                Play(overrideClip != null && Time.time < overrideUntil ? overrideClip : SurveyorAnim.Pick(input));
                SetFacing(player.Facing);
            }
            SquashRoot.localScale = Squash.Step(dt);
            clipTime += dt;
            Apply();
        }

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

        void OnDestroy()
        {
            if (hooked && player != null) { player.Landed -= OnLanded; if (rig != null) rig.Dug -= OnDug; player.Jumped -= OnJumped; player.Bumped -= OnBumped; }
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
