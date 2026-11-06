using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rendering;
using Meridian.Rig;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Player
{
    /// <summary>
    /// Draws the surveyor (U-032): plays the characters/surveyor/base clips by name (frame ranges and
    /// fps from the sheet's .json via the ArtMaterials registry, no hard-coded indices) for the state
    /// SurveyorAnim picks, and faces the aim point while the rig is in use, else the move direction.
    /// No allocation per frame; renderer properties are written only when they change.
    /// </summary>
    public sealed class PlayerView : MonoBehaviour
    {
        public PlayerController controller;
        public SpriteRenderer view;
        public RigTools rig;
        public PlayerRigInput rigInput;

        /// <summary>The playing clip's name and the frame index shown (tests, capture).</summary>
        public string Clip { get; private set; } = SurveyorAnim.Idle;
        /// <summary>U-075: the surveyor's 3D model view (Ready once B-078's model has loaded; until then the sheet draws).</summary>
        public Meridian.Art.ModelView Model { get; private set; }
        public int Frame { get; private set; }
        public double LastUpdateMs { get; private set; }
        /// <summary>Part of LastUpdateMs spent inside SpriteRenderer setters (Unity work, not ours).</summary>
        public double LastRendererMs { get; private set; }
        /// <summary>U-089: the scaled visual root (sheet + model); the collider and body never scale.</summary>
        public Transform VisualRoot { get; private set; }
        public SquashStretch Squash { get; } = new SquashStretch();
        /// <summary>U-089: the 2-frame white flash of a hit reaction is showing.</summary>
        public bool Flashing => Time.time < flashUntil;
        public const float FlashSeconds = 2f / 60f;
        static readonly Color FlashTint = new Color(1.6f, 1.6f, 1.6f, 1f);
        float flashUntil = -1f, sinceHitReact = 99f, sinceJump = 99f, sinceParryHit = 99f, landSpeed;
        bool flashShown;

        AsyncOperationHandle<IList<Sprite>> handle;
        Sprite[] frames;
        ArtClipSet clips;
        ArtClip current;
        bool hasCurrent;
        int shown = -1;
        float clipTime, sinceHurt = 99f, sinceLand = 99f, sinceDig = 99f;
        bool hooked;
        readonly System.Diagnostics.Stopwatch watch = new System.Diagnostics.Stopwatch();

        void Start()
        {
            var tier = Meridian.Core.GameState.Instance != null ? Meridian.Core.GameState.Instance.suitTier : 0;
            LoadSheet(ArtKeys.Characters.SurveyorSheet(tier));
            // U-075: the surveyor's 3D model (B-078) replaces the sheet once it has loaded.
            // U-089: a visual root (scaled by SquashStretch about the feet) holds the sheet and the model; the collider and body never scale.
            VisualRoot = new GameObject("Visual").transform;
            VisualRoot.SetParent(view.transform.parent, false);
            VisualRoot.localPosition = Vector3.zero;
            var viewLocal = view.transform.localPosition;
            if (view.transform != VisualRoot.parent) { view.transform.SetParent(VisualRoot, false); view.transform.localPosition = viewLocal; }
            var modelGo = new GameObject("Model");
            modelGo.transform.SetParent(VisualRoot, false);
            modelGo.transform.localPosition = viewLocal;
            Model = modelGo.AddComponent<Meridian.Art.ModelView>();
            Model.Load(ArtKeys.Characters.Surveyor);
            Meridian.Hazards.HazardSystem.SuitEquipped += OnSuitEquipped;
            Hook();
        }

        /// <summary>The loaded sheet's key (U-049: base, mk1, mk2, mk3).</summary>
        public string SheetKey { get; private set; }

        void OnSuitEquipped(int tier) => LoadSheet(ArtKeys.Characters.SurveyorSheet(tier));

        /// <summary>Loads a surveyor sheet (all share the clip layout); the old one is released once the new one shows.</summary>
        void LoadSheet(string key)
        {
            if (key == SheetKey) return;
            SheetKey = key;
            var old = handle;
            clips = ArtMaterials.ClipsFor(key) ?? ArtMaterials.ClipsFor(ArtKeys.Characters.Surveyor);
            var h = ArtLoad.Asset<IList<Sprite>>(key);
            handle = h;
            h.Completed += op =>
            {
                if (view != null && SheetKey != key) { Addressables.Release(h); return; } // superseded by another suit
                if (view == null) return; // scene unloaded before the load finished
                if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                var list = new Sprite[op.Result.Count];
                foreach (var s in op.Result)
                {
                    int u = s.name.LastIndexOf('_');
                    if (u >= 0 && int.TryParse(s.name.Substring(u + 1), out int n) && n >= 0 && n < list.Length) list[n] = s;
                }
                for (int i = 0; i < list.Length; i++) if (list[i] == null) list[i] = op.Result[0];
                frames = list;
                // Show every frame once now: a sprite's first use builds its mesh (a ms-scale hitch mid-animation otherwise).
                for (int i = list.Length - 1; i >= 0; i--) view.sprite = list[i];
                bool f0 = view.flipX; view.flipX = !f0; view.flipX = f0; // the first flip has a one-off cost too
                shown = 0;
                var mat = ArtMaterials.MaterialFor(key);
                if (mat != null) view.sharedMaterial = mat;
                if (old.IsValid()) Addressables.Release(old);
            };
        }

        void Hook()
        {
            if (hooked || controller == null) return;
            hooked = true;
            controller.Landed += OnLanded;
            controller.Jumped += OnJumped;
            controller.Knocked += OnKnocked;
            controller.ParryLanded += OnParryLanded;
            if (controller.Vitals != null) controller.Vitals.Damaged += OnDamaged;
            if (rig != null) rig.Dug += OnDug;
        }

        void OnLanded(float speed) { sinceLand = 0f; landSpeed = speed; Squash.Land(speed); }
        void OnJumped() { sinceJump = 0f; Squash.TakeOff(); }
        void OnKnocked() { sinceHitReact = 0f; flashUntil = Time.time + FlashSeconds; }
        void OnParryLanded() => sinceParryHit = 0f;
        void OnDamaged(float amount) => sinceHurt = 0f;
        void OnDug(Vector2 at) => sinceDig = 0f;

        /// <summary>U-089: a feel clip the sheet lacks falls back to its stand-in (the model shares the sheet's names, B-103 fills both).</summary>
        string Resolve(string clip)
        {
            if (clips == null || clips.TryGet(clip, out _)) return clip;
            return SurveyorAnim.StandIn(clip);
        }

        void LateUpdate()
        {
            watch.Restart();
            if (controller == null) return;
            if (!hooked) Hook();
            float dt = Time.deltaTime;
            sinceHurt += dt; sinceLand += dt; sinceDig += dt;
            sinceHitReact += dt; sinceJump += dt; sinceParryHit += dt;
            // U-089: squash and stretch on the visual root only; the dash stretches along x while it runs.
            if (controller.Dash.Active && !Squash.Dashing) Squash.Dash(AirDash.Duration);
            if (VisualRoot != null) VisualRoot.localScale = Squash.Step(dt);

            var body = controller.Body;
            var v = body != null ? body.linearVelocity : Vector2.zero;
            bool usingRig = rigInput != null && rigInput.Using;
            var input = new AnimInputs
            {
                dead = controller.Vitals != null && controller.Vitals.Dead,
                grounded = controller.Grounded,
                usingRig = usingRig,
                vx = v.x, vy = v.y,
                sinceHurt = sinceHurt, sinceLand = sinceLand, sinceDig = sinceDig,
                sinceHitReact = sinceHitReact, sinceJump = sinceJump, sinceParryHit = sinceParryHit, landSpeed = landSpeed,
                dashing = controller.Dash.Active, parrying = controller.Parry.Active || controller.Parry.Recovering,
            };
            string clip = Resolve(SurveyorAnim.Pick(input));
            bool changed = !ReferenceEquals(clip, Clip);
            if (changed) { Clip = clip; clipTime = 0f; }
            else clipTime += dt;
            if (changed || (!hasCurrent && clips != null))
                hasCurrent = clips != null && clips.TryGet(Clip, out current) && current.length > 0; // lookup only on a change

            // Facing: toward the aim point while using the rig, else the move direction.
            bool aimFacing = usingRig || sinceDig < SurveyorAnim.DigTime;
            bool flip = aimFacing ? rigInput != null && rigInput.AimWorld.x < transform.position.x : controller.Facing < 0;
            if (Model != null && Model.Ready)
            {
                // U-075: the model plays the same clip names; the sheet is hidden.
                if (view.enabled) view.enabled = false;
                bool flashing = Flashing;
                if (flashing && !flashShown) Model.Flash(FlashSeconds);
                flashShown = flashing;
                Model.Play(Clip);
                Model.SetFacing(!flip);
                LastRendererMs = 0;
                LastUpdateMs = watch.Elapsed.TotalMilliseconds;
                return;
            }
            double before = watch.Elapsed.TotalMilliseconds;
            if (flip != view.flipX) view.flipX = flip;
            bool fl = Flashing;
            if (fl != flashShown) { flashShown = fl; view.color = fl ? FlashTint : Color.white; }
            double renderer = watch.Elapsed.TotalMilliseconds - before;

            if (frames != null && hasCurrent)
            {
                int step = (int)(clipTime * clips.fps);
                int f = current.loop ? step % current.length : Mathf.Min(step, current.length - 1);
                Frame = Mathf.Clamp(current.start + f, 0, frames.Length - 1);
                if (Frame != shown)
                {
                    shown = Frame;
                    before = watch.Elapsed.TotalMilliseconds;
                    view.sprite = frames[Frame];
                    renderer += watch.Elapsed.TotalMilliseconds - before;
                }
            }
            LastRendererMs = renderer;
            LastUpdateMs = watch.Elapsed.TotalMilliseconds;
        }

        void OnDestroy()
        {
            if (hooked && controller != null)
            {
                controller.Landed -= OnLanded;
                controller.Jumped -= OnJumped;
                controller.Knocked -= OnKnocked;
                controller.ParryLanded -= OnParryLanded;
                if (controller.Vitals != null) controller.Vitals.Damaged -= OnDamaged;
                if (rig != null) rig.Dug -= OnDug;
            }
            Meridian.Hazards.HazardSystem.SuitEquipped -= OnSuitEquipped;
            if (handle.IsValid()) Addressables.Release(handle);
        }
    }
}
