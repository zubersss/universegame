using System.Collections.Generic;
using Meridian.Flora;
using Meridian.Rendering;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Creatures
{
    public enum CreatureState { Idle, Wander, Flee, Chase }

    /// <summary>
    /// One creature (U-027): a dynamic Rigidbody2D under the planet's real gravity (fliers: none), a box
    /// collider and a sprite. It has no Update of its own: CreatureDirector thinks, steers and animates for
    /// all creatures in one loop (so the AI cost is one measured number). Pooled.
    /// U-108 (B-127 gull): a sheet whose clips include `fly` plays it while the creature is airborne (ground contact
    /// reported by the director each tick, with hysteresis so a hop or a bump never flickers it); species without a
    /// fly clip are untouched.
    /// </summary>
    public sealed class Creature : MonoBehaviour
    {
        public SpeciesSpec Spec { get; private set; }
        public Rigidbody2D Body { get; private set; }
        public BoxCollider2D Box { get; private set; }
        public SpriteRenderer View { get; private set; }
        /// <summary>U-089: the visual root (sheet + model) SquashStretch scales about the feet; the box and body never scale.</summary>
        public Transform Visual { get; private set; }
        public Meridian.Player.SquashStretch Squash { get; } = new Meridian.Player.SquashStretch();
        public const string HitReactClip = "hit_react";
        static readonly Color FlashTint = new Color(1.6f, 1.6f, 1.6f, 1f);
        /// <summary>U-075: the species' 3D model (B-082 …), Ready once loaded; until then (or without a model) the sprite draws.</summary>
        public Meridian.Art.ModelView Model { get; private set; }
        /// <summary>U-119: a rig-set creature's rig (RigBuild under Visual), null until its json, parts sheet and controller are in.</summary>
        public RigInstance Rig { get; private set; }
        /// <summary>U-119: the surveyor is inside the species' react radius (the director sets it): the jaw opens, the lure flares.</summary>
        public bool RigReacting { get; private set; }
        public const float RigReactEase = 0.25f;
        Transform rigPivot, rigJaw;
        SpriteRenderer rigLureSlot;
        RigSet.SwapCycle rigCycle;
        Sprite[] rigCycleSprites;
        Sprite rigReactSprite;
        Dictionary<string, Sprite> rigSprites;
        TextAsset rigJson;
        RuntimeAnimatorController rigController;
        string rigKey;
        int rigPending;
        float rigReactK, rigCyclePhase;
        readonly List<AsyncOperationHandle> rigHandles = new List<AsyncOperationHandle>();
        static readonly string[] ModelClips = { "idle", "walk", "attack", "hurt" }; // same order as the sheet clips
        public CreatureState State { get; internal set; }
        /// <summary>U-153: a staged shot (captures, the smoke) holds the creature still, facing StagedFacing (+1 right, −1 left), until
        /// StagedUntil (Time.time); its steering and reactions (a Flees species turning tail) wait meanwhile.</summary>
        public float StagedUntil { get; private set; } = float.NegativeInfinity;
        public int StagedFacing { get; private set; } = 1;
        public void Stage(int facing, float seconds) { StagedFacing = facing < 0 ? -1 : 1; StagedUntil = Time.time + seconds; }
        /// <summary>Held: its chunk isn't loaded with collision, so the body is paused in place.</summary>
        public bool Held { get; internal set; }
        public bool Alive => gameObject.activeSelf;
        internal float knockFor, knockVx, flashFor;
        /// <summary>U-099: seconds the body has stood still while wanting to move (a wall the terrain check cannot see: props, pieces).</summary>
        internal float blockedFor, keepDirUntil, blockAnchorX, blockAnchorT, waitUntil;
        /// <summary>
        /// U-099: the clip picked last frame (0 idle, 1 walk, 2 attack/bump, 3 hurt); tests read it.
        /// U-108: while Airborne on a sheet with a `fly` clip it is that clip's index (4 on the B-127 gull's v3 sheet).
        /// </summary>
        public int LastPick { get; private set; }
        /// <summary>U-108: the name of the sheet clip drawn now ("idle", "walk", "fly" …); null before the first animated frame or without a sheet. Tests read it.</summary>
        public string CurrentClip => clips != null && lastClip >= 0 && lastClip < clips.clips.Count ? clips.clips[lastClip].name : null;
        /// <summary>
        /// U-108: off the ground by hysteresis: FlyAfter seconds without ground contact to lift off, LandAfter seconds of
        /// contact to land, so a one-tile hop or a bump never flickers the fly clip. The director reports contact each tick.
        /// </summary>
        public bool Airborne { get; private set; }
        public const float FlyAfter = 0.12f, LandAfter = 0.06f;
        /// <summary>U-108: the sheet clip a flier plays while airborne (B-127 gull: frames 40–51, loop).</summary>
        public const string FlyClip = "fly";
        /// <summary>U-114 (D-119, B-132): the bolt and the wolf's trot-after, found by name (idle 0, walk 1, react 2, bump 3 stay by index).</summary>
        public const string FleeClip = "flee", FollowClip = "follow";
        /// <summary>U-118 (D-126): a den species' idle away from its mound (cycle 258: `idle` is the peek at the den, `idle_open` elsewhere).</summary>
        public const string IdleOpenClip = "idle_open";
        int idleOpenClip = -1;
        /// <summary>U-118: the den's x for a den species (NaN without one); the director sets it at spawn.</summary>
        public float DenX { get; internal set; } = float.NaN;
        public bool AtDen => !float.IsNaN(DenX) && Spec != null && Mathf.Abs(Body.position.x - DenX) < Spec.denRange;
        int fleeClip = -1, followClip = -1;
        internal float nextHuff;

        /// <summary>The index of a clip by name in a sheet's set, or −1. Pure.</summary>
        public static int ClipIndex(ArtClipSet clips, string name)
        {
            if (clips == null) return -1;
            for (int i = 0; i < clips.clips.Count; i++) if (clips.clips[i].name == name) return i;
            return -1;
        }
        Color baseColor = Color.white;
        internal CreatureDirector director;

        /// <summary>Mercury zone at the creature (U-055: Cinderhulk sheet and window).</summary>
        public MercuryZone Zone { get; internal set; }
        /// <summary>Time (Time.time) it last crossed into night; NegativeInfinity if it never has.</summary>
        public float NightfallAt { get; internal set; } = float.NegativeInfinity;
        /// <summary>Cinderhulk: the cracked-shell window is open now.</summary>
        public bool Vulnerable => ApexRules.CanHurt(Spec.id, true, Zone, Time.time - NightfallAt);
        // D-087 (U-093): no hit points, no Hurt, no Killed: the Lance is archived (Assets/_Game/Archive/Combat~).

        internal int dir = 1;
        internal float nextThink, biteReady, hurtFor, attackFor, chillFor, fleeUntil, anim, altitude;
        internal int serial;
        internal Sprite[] frames, nightFrames;
        internal ArtClipSet clips;
        internal int lastClip = -1;
        /// <summary>U-108: index of the sheet's `fly` clip, resolved once at Setup (−1 when the sheet has none); seconds without / with ground contact.</summary>
        internal int flyClip = -1;
        internal float airFor, groundFor;

        static PhysicsMaterial2D slick;

        internal static Creature Create(Transform parent, int index)
        {
            var go = new GameObject("Creature" + index);
            go.transform.SetParent(parent, false);
            var c = go.AddComponent<Creature>();
            c.Body = go.AddComponent<Rigidbody2D>();
            c.Body.freezeRotation = true;
            c.Body.interpolation = RigidbodyInterpolation2D.Interpolate;
            c.Body.collisionDetectionMode = CollisionDetectionMode2D.Continuous; // fast runners vs thin ledges
            c.Box = go.AddComponent<BoxCollider2D>();
            if (slick == null) slick = new PhysicsMaterial2D("CreatureSlick") { friction = 0f, bounciness = 0f };
            c.Box.sharedMaterial = slick; // no sticking to walls mid-jump
            var visual = new GameObject("Visual");
            visual.transform.SetParent(go.transform, false);
            c.Visual = visual.transform;
            var view = new GameObject("View");
            view.transform.SetParent(visual.transform, false);
            c.View = view.AddComponent<SpriteRenderer>();
            c.View.sortingOrder = 5; // with the player and ship, in front of terrain
            go.SetActive(false);
            return c;
        }

        /// <summary>U-108: true while the body shows the director's placeholder box (its sheet was not loaded when it spawned).</summary>
        public bool IsPlaceholder => View != null && View.sprite != null && View.sprite.name.StartsWith("CreaturePlaceholder", System.StringComparison.Ordinal);

        /// <summary>U-108: the species' sheet arrived after this body spawned (the stage's load-time gull): swap the box for the art in place.</summary>
        internal void ApplyArt(Sprite sprite, Sprite[] frames, Sprite[] nightFrames, ArtClipSet clips)
        {
            if (sprite == null || Spec == null) return;
            this.frames = frames;
            this.nightFrames = nightFrames;
            this.clips = clips;
            flyClip = -1;
            if (clips != null) for (int i = 0; i < clips.clips.Count; i++) if (clips.clips[i].name == FlyClip) { flyClip = i; break; }
            fleeClip = ClipIndex(clips, FleeClip); followClip = ClipIndex(clips, FollowClip); idleOpenClip = ClipIndex(clips, IdleOpenClip);
            lastClip = -1;
            View.sprite = sprite;
            View.transform.localScale = Vector3.one * Spec.artScale;
            View.transform.localPosition = Vector3.zero;
            View.color = Color.white;
            baseColor = View.color;
        }

        internal void Setup(SpeciesSpec spec, Vector2 position, Sprite sprite, int serial) => Setup(spec, position, sprite, null, null, null, serial);

        internal void Setup(SpeciesSpec spec, Vector2 position, Sprite sprite, Sprite[] frames, Sprite[] nightFrames, ArtClipSet clips, int serial)
        {
            Spec = spec;
            this.serial = serial;
            this.frames = frames;
            this.nightFrames = nightFrames;
            this.clips = clips;
            // U-108: the fly clip by name, once per spawn (a pooled body comes back as another species: reset when the sheet has none).
            flyClip = -1;
            if (clips != null) for (int i = 0; i < clips.clips.Count; i++) if (clips.clips[i].name == FlyClip) { flyClip = i; break; }
            fleeClip = ClipIndex(clips, FleeClip); followClip = ClipIndex(clips, FollowClip); idleOpenClip = ClipIndex(clips, IdleOpenClip);
            DenX = float.NaN;
            airFor = groundFor = 0f;
            Airborne = false;
            State = CreatureState.Wander;
            Held = false;
            dir = (serial & 1) == 0 ? 1 : -1;
            // Batch B (the InnerCreatureTests worst frame): the first think is staggered by serial, so a pack spawned in one frame never
            // thinks in one frame again (every Think() then keeps its own phase: nextThink = now + ThinkInterval).
            nextThink = Time.time + (serial & 7) * (CreatureDirector.ThinkInterval / 8f);
            biteReady = 0f;
            hurtFor = attackFor = chillFor = anim = knockFor = flashFor = blockedFor = keepDirUntil = blockAnchorT = waitUntil = nextHuff = 0f;
            blockAnchorX = position.x;
            fleeUntil = 0f;
            lastClip = -1;
            altitude = position.y;
            NightfallAt = float.NegativeInfinity;
            Box.size = spec.size;
            Box.offset = Vector2.zero;
            // U-089: the visual root sits at the feet (walkers) or the centre (fliers), so squashes keep the feet planted.
            Visual.localPosition = spec.Flies ? Vector3.zero : new Vector3(0f, -spec.size.y * 0.5f, 0f);
            Visual.localScale = Vector3.one;
            View.sprite = sprite;
            bool placeholder = sprite == null || sprite.name.StartsWith("CreaturePlaceholder");
            if (placeholder && sprite != null)
            {
                // The tinted box fills the body.
                var b = sprite.bounds.size;
                View.transform.localScale = new Vector3(spec.size.x / Mathf.Max(0.01f, b.x), spec.size.y / Mathf.Max(0.01f, b.y), 1f);
                View.transform.localPosition = -Visual.localPosition; // the box fills the body: centred on it
            }
            else
            {
                // Real art: true size from the sheet's ppu (U-036). Walkers: the bottom pivot stands on the
                // body's feet. Fliers (U-055): the centred pivot sits on the body's centre.
                View.transform.localScale = Vector3.one * spec.artScale;
                View.transform.localPosition = Vector3.zero; // under Visual, which already sits at the feet
            }
            View.color = placeholder ? spec.placeholder : Color.white;
            baseColor = View.color;
            View.enabled = true;
            EnsureModel(spec);
            EnsureRig(spec);
            transform.position = position;
            gameObject.SetActive(true);
            Body.gravityScale = spec.Flies ? 0f : 1f;
            Body.simulated = true;
            Body.position = position;
            Body.linearVelocity = Vector2.zero;
        }

        /// <summary>U-119: a rig-set species builds its rig once its three assets are in (the json at key/json, the parts sheet at key, the controller at key/animator); a pooled body coming back as another species drops the old rig.</summary>
        void EnsureRig(SpeciesSpec spec)
        {
            if (!spec.rig) { if (Rig != null || rigPending > 0) DropRig(); return; }
            if (rigKey == spec.artKey && (Rig != null || rigPending > 0)) return;
            DropRig();
            rigKey = spec.artKey;
            rigPending = 3;
            FetchRig<TextAsset>(rigKey + FloraRigs.JsonSuffix, a => rigJson = a);
            FetchRig<IList<Sprite>>(rigKey, a => rigSprites = RigBuild.ByName(a));
            FetchRig<RuntimeAnimatorController>(rigKey + FloraRigs.AnimatorSuffix, a => rigController = a);
        }

        void FetchRig<T>(string address, System.Action<T> set) where T : class
        {
            var h = global::Meridian.Art.ArtLoad.Asset<T>(address);
            rigHandles.Add(h);
            h.Completed += op =>
            {
                if (this == null) return;
                if (op.Status == AsyncOperationStatus.Succeeded && op.Result != null) set(op.Result);
                else Debug.LogWarning($"[MERIDIAN] Creature: {address} failed to load (run CheckSetup).");
                if (--rigPending == 0) BuildRig();
            };
        }

        void BuildRig()
        {
            if (Spec == null || !Spec.rig || rigJson == null || rigSprites == null || rigSprites.Count == 0) return;
            var set = RigSet.Parse(rigJson.text, out var error);
            var def = set != null && set.plants != null && set.plants.Length > 0 ? set.plants[0] : null;
            if (def == null) { Debug.LogError($"[MERIDIAN] Creature: {rigKey}: {error ?? "no plants"}."); return; }
            // The rig under a pivot at the body's centre: the pivot flips with the facing, the rig inside it is shifted so its drawing is centred on the body.
            var pgo = new GameObject("RigPivot");
            pgo.transform.SetParent(Visual, false);
            rigPivot = pgo.transform;
            Rig = RigBuild.Build(def, rigSprites, rigPivot, rigController, View.sortingLayerID, View.sortingOrder, ArtMaterials.MaterialFor(rigKey));
            bool any = false; var all = new Bounds();
            foreach (var r in Rig.Parts) if (r != null) { if (!any) { all = r.bounds; any = true; } else all.Encapsulate(r.bounds); }
            foreach (var r in Rig.Slots.Values) if (r != null) { if (!any) { all = r.bounds; any = true; } else all.Encapsulate(r.bounds); }
            if (any) { var centre = rigPivot.InverseTransformPoint(all.center); Rig.Root.localPosition = new Vector3(-centre.x, -centre.y, 0f); }
            rigJaw = Rig.Bone("jaw");
            rigCycle = def.Cycle;
            rigLureSlot = null; rigCycleSprites = null; rigReactSprite = null;
            if (rigCycle != null && (rigLureSlot = RigSlotRenderer(rigCycle.slot)) != null)
            {
                rigCycleSprites = new Sprite[rigCycle.sequence.Length];
                for (int i = 0; i < rigCycleSprites.Length; i++) rigSprites.TryGetValue(rigCycle.sequence[i], out rigCycleSprites[i]);
            }
            foreach (var kv in def.react.also)
            {
                var slotRenderer = RigSlotRenderer(kv.Key);
                if (slotRenderer != null && rigSprites.TryGetValue(kv.Value, out var reactSprite)) { if (rigLureSlot == null) rigLureSlot = slotRenderer; if (slotRenderer == rigLureSlot) rigReactSprite = reactSprite; break; }
            }
            rigCyclePhase = Time.time;
            rigReactK = 0f;
            View.enabled = false; // the placeholder box hides behind the rig
        }

        void DropRig()
        {
            if (rigPivot != null) Destroy(rigPivot.gameObject);
            rigPivot = null; Rig = null; rigJaw = null; rigLureSlot = null; rigCycle = null; rigCycleSprites = null; rigReactSprite = null;
            rigJson = null; rigSprites = null; rigController = null; rigKey = null; rigPending = 0; rigReactK = 0f; RigReacting = false;
            foreach (var h in rigHandles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            rigHandles.Clear();
        }

        /// <summary>U-119: the renderer a swap slot draws on: RigBuild's own slot renderer, or — for a v3.1 `replaces_part` slot — the bone's part renderer (the Maw's lure). Null without a rig or slot.</summary>
        public SpriteRenderer RigSlotRenderer(string slot)
        {
            if (Rig == null || string.IsNullOrEmpty(slot)) return null;
            if (Rig.Slots.TryGetValue(slot, out var r)) return r;
            var s = Rig.Def.FindSlot(slot);
            if (s == null || !s.replaces_part) return null;
            int bi = Rig.Def.BoneIndex(s.bone);
            return bi >= 0 && bi < Rig.Parts.Length ? Rig.Parts[bi] : null;
        }

        internal void SetRigReacting(bool on) => RigReacting = on;
        internal void SetRigFacing(bool right) { if (rigPivot != null) { var s = rigPivot.localScale; s.x = right ? 1f : -1f; rigPivot.localScale = s; } }

        /// <summary>U-119: the rig's frame: the Animator sways the bones; here the react eases the jaw to jaw_deg and tilts the rig head_deg, and the lure shows the react's part or the idle swap cycle's entry on the beat.</summary>
        void AnimateRig(float dt)
        {
            if (View.enabled) View.enabled = false;
            if (hurtFor > 0f) hurtFor -= dt;
            if (attackFor > 0f) attackFor -= dt;
            if (flashFor > 0f) flashFor -= dt;
            var react = Rig.Def.react;
            rigReactK = Mathf.MoveTowards(rigReactK, RigReacting ? 1f : 0f, dt / RigReactEase);
            if (rigJaw != null) rigJaw.localRotation = Quaternion.Euler(0f, 0f, react.jaw_deg * rigReactK);
            if (react.head_deg != 0f) Rig.Root.localRotation = Quaternion.Euler(0f, 0f, react.head_deg * rigReactK);
            if (rigLureSlot != null)
            {
                Sprite want = RigReacting && rigReactSprite != null ? rigReactSprite
                    : rigCycle != null && rigCycleSprites != null ? rigCycleSprites[rigCycle.IndexAt((Time.time - rigCyclePhase) * Rig.Def.idle.beat_bpm / 60f)] : null;
                if (want != null && rigLureSlot.sprite != want) rigLureSlot.sprite = want;
            }
        }

        void OnDestroy() => DropRig();

        /// <summary>U-075: one model view per creature, swapped when a pooled body comes back as another species.</summary>
        void EnsureModel(SpeciesSpec spec)
        {
            if (Model != null && Model.Key == spec.artKey) return;
            if (Model != null) Destroy(Model.gameObject);
            var go = new GameObject("Model");
            go.transform.SetParent(Visual, false);
            // The model's origin is its feet (contract §9): Visual already sits on the body's bottom (walkers) or its centre (fliers).
            go.transform.localPosition = Vector3.zero;
            Model = go.AddComponent<Meridian.Art.ModelView>();
            Model.Load(spec.artKey);
        }

        /// <summary>U-093: the bump reaction (U-089 squash kept): knocked 0.5 m along `away` over 0.12 s, a 2-frame flash, a 0.85 squash.</summary>
        public void React(Vector2 away)
        {
            knockFor = Meridian.Player.PlayerController.KnockTime;
            knockVx = (away.x >= 0f ? 1f : -1f) * (0.5f / Meridian.Player.PlayerController.KnockTime);
            Squash.Hit();
            if (Model != null && Model.Ready) Model.Flash(Meridian.Player.PlayerView.FlashSeconds);
            else flashFor = Meridian.Player.PlayerView.FlashSeconds;
        }

        /// <summary>U-114: the territorial rear-up (the react clip for `seconds`), no knock, no flash.</summary>
        internal void Rear(float seconds) => attackFor = seconds;

        /// <summary>
        /// One frame of animation (the director calls it once per tick). `grounded`: ground contact this tick (walkers: still and
        /// a solid tile under the feet; fliers: a solid tile under the feet), feeding the U-108 airborne hysteresis.
        /// </summary>
        internal void Animate(float dt, float speed, bool grounded)
        {
            // U-108: airborne by hysteresis (FlyAfter off the ground, LandAfter on it); no allocation.
            if (grounded) { groundFor += dt; airFor = 0f; if (groundFor >= LandAfter) Airborne = false; }
            else { airFor += dt; groundFor = 0f; if (airFor >= FlyAfter) Airborne = true; }
            if (Visual != null) Visual.localScale = Squash.Step(dt); // U-089: visual root only
            if (Rig != null) { AnimateRig(dt); return; } // U-119: a rig-set creature
            if (Model != null && Model.Ready)
            {
                // U-075: the model plays the same clip choice by name; the sheet stays hidden.
                if (hurtFor > 0f) hurtFor -= dt;
                if (attackFor > 0f) attackFor -= dt;
                if (chillFor > 0f) { chillFor -= dt; if (chillFor > 0f) Model.Flash(0.05f); }
                if (View.enabled) View.enabled = false;
                int pick = hurtFor > 0f ? 3 : attackFor > 0f ? 2 : speed > 0.3f ? 1 : 0;
                LastPick = pick;
                // U-089: hit_react when the model has it, else the hurt stand-in.
                if (pick == 3) { if (!Model.Play(HitReactClip)) Model.Play(ModelClips[3]); }
                else Model.Play(ModelClips[pick]);
                return;
            }
            anim += dt;
            if (flashFor > 0f) { flashFor -= dt; View.color = flashFor > 0f ? FlashTint : baseColor; } // U-089: the 2-frame flash on the sheet
            if (hurtFor > 0f) hurtFor -= dt;
            if (attackFor > 0f) attackFor -= dt;
            if (chillFor > 0f)
            {
                chillFor -= dt;
                View.color = chillFor > 0f ? new Color(0.6f, 0.85f, 1f) : Color.white; // the Veil Serpent's chilled flash
            }
            var sheet = nightFrames != null && Zone == MercuryZone.Night ? nightFrames : frames;
            if (sheet == null || clips == null || clips.clips.Count == 0) return;
            // Clip order in every B-0xx creature sheet: idle, walk, attack, hurt, death. U-108: a sheet with a `fly` clip
            // (B-127 gull: idle, walk, react, bump, fly) plays it while airborne, under the bump and hurt reactions.
            // U-114: a bolting creature with a `flee` clip runs it, a chasing wolf its `follow`; walk and idle otherwise.
            int want = hurtFor > 0f ? 3 : attackFor > 0f ? 2 : (Airborne && flyClip >= 0) ? flyClip
                     : (State == CreatureState.Flee && fleeClip >= 0 && speed > 0.3f) ? fleeClip
                     : (State == CreatureState.Chase && followClip >= 0 && speed > 0.3f) ? followClip
                     : speed > 0.3f ? 1 : (idleOpenClip >= 0 && !AtDen) ? idleOpenClip : 0; // U-118: a den species peeks only at its mound
            LastPick = want;
            if (want >= clips.clips.Count) want = 0;
            if (want != lastClip) { lastClip = want; anim = 0f; }
            var clip = clips.clips[want];
            int step = Mathf.FloorToInt(anim * (clips.fps > 0 ? clips.fps : 12));
            int f = clip.start + (clip.loop ? step % Mathf.Max(1, clip.length) : Mathf.Min(step, clip.length - 1));
            if (f >= 0 && f < sheet.Length && sheet[f] != null) View.sprite = sheet[f];
        }
    }
}
