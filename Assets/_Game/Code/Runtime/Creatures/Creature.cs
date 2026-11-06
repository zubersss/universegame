using Meridian.Rendering;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Creatures
{
    public enum CreatureState { Idle, Wander, Flee, Chase }

    /// <summary>
    /// One creature (U-027): a dynamic Rigidbody2D under the planet's real gravity (fliers: none), a box
    /// collider and a sprite. It has no Update of its own: CreatureDirector thinks, steers and animates for
    /// all creatures in one loop (so the AI cost is one measured number). Pooled.
    /// </summary>
    public sealed class Creature : MonoBehaviour
    {
        public SpeciesSpec Spec { get; private set; }
        public Rigidbody2D Body { get; private set; }
        public BoxCollider2D Box { get; private set; }
        public SpriteRenderer View { get; private set; }
        /// <summary>U-075: the species' 3D model (B-082 …), Ready once loaded; until then (or without a model) the sprite draws.</summary>
        public Meridian.Art.ModelView Model { get; private set; }
        static readonly string[] ModelClips = { "idle", "walk", "attack", "hurt" }; // same order as the sheet clips
        public CreatureState State { get; internal set; }
        /// <summary>Held: its chunk isn't loaded with collision, so the body is paused in place.</summary>
        public bool Held { get; internal set; }
        public bool Alive => gameObject.activeSelf;
        /// <summary>Hit points left (U-046); reset at spawn from the species.</summary>
        public float Health { get; private set; }
        /// <summary>U-088: a parried attacker stands staggered this long.</summary>
        public const float StaggerSeconds = 1.2f, StaggerBrake = 20f;
        public bool IsStaggered => staggerFor > 0f;
        internal float staggerFor;
        internal CreatureDirector director;

        /// <summary>Mercury zone at the creature (U-055: Cinderhulk sheet and window).</summary>
        public MercuryZone Zone { get; internal set; }
        /// <summary>Time (Time.time) it last crossed into night; NegativeInfinity if it never has.</summary>
        public float NightfallAt { get; internal set; } = float.NegativeInfinity;
        /// <summary>Cinderhulk: the cracked-shell window is open now.</summary>
        public bool Vulnerable => ApexRules.CanHurt(Spec.id, true, Zone, Time.time - NightfallAt);
        /// <summary>The last hit didn't land (the Cinderhulk's hot shell, the Veil Serpent without Cryo).</summary>
        public bool LastHitShrugged { get; private set; }

        /// <summary>Damage from the player (the Lance). At 0 the creature dies (despawns) and Killed fires. True if this killed it.</summary>
        public bool Hurt(float damage) => Hurt(damage, false);

        /// <summary>A hit; `cryo` for Cryo rounds (U-055). The apex rules decide whether it lands.</summary>
        public bool Hurt(float damage, bool cryo)
        {
            if (!Alive || damage <= 0f) return false;
            LastHitShrugged = !ApexRules.CanHurt(Spec.id, cryo, Zone, Time.time - NightfallAt);
            if (LastHitShrugged) return false;
            Health -= damage;
            hurtFor = 0.3f;
            if (cryo) { chillFor = 0.35f; if (Spec.id == Species.VeilSerpent) fleeUntil = Time.time + 4f; }
            if (Health > 0f) return false;
            Health = 0f;
            Killed?.Invoke(this);
            if (director != null) director.Despawn(this); else gameObject.SetActive(false);
            return true;
        }

        public static event System.Action<Creature> Killed;

        internal int dir = 1;
        internal float nextThink, biteReady, hurtFor, attackFor, chillFor, fleeUntil, anim, altitude;
        internal int serial;
        internal Sprite[] frames, nightFrames;
        internal ArtClipSet clips;
        internal int lastClip = -1;

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
            var view = new GameObject("View");
            view.transform.SetParent(go.transform, false);
            c.View = view.AddComponent<SpriteRenderer>();
            c.View.sortingOrder = 5; // with the player and ship, in front of terrain
            go.SetActive(false);
            return c;
        }

        internal void Setup(SpeciesSpec spec, Vector2 position, Sprite sprite, int serial) => Setup(spec, position, sprite, null, null, null, serial);

        internal void Setup(SpeciesSpec spec, Vector2 position, Sprite sprite, Sprite[] frames, Sprite[] nightFrames, ArtClipSet clips, int serial)
        {
            Spec = spec;
            Health = spec.maxHealth;
            this.serial = serial;
            this.frames = frames;
            this.nightFrames = nightFrames;
            this.clips = clips;
            State = CreatureState.Wander;
            Held = false;
            dir = (serial & 1) == 0 ? 1 : -1;
            nextThink = 0f;
            biteReady = 0f;
            hurtFor = attackFor = chillFor = anim = staggerFor = 0f;
            fleeUntil = 0f;
            lastClip = -1;
            altitude = position.y;
            NightfallAt = float.NegativeInfinity;
            LastHitShrugged = false;
            Box.size = spec.size;
            Box.offset = Vector2.zero;
            View.sprite = sprite;
            bool placeholder = sprite == null || sprite.name.StartsWith("CreaturePlaceholder");
            if (placeholder && sprite != null)
            {
                // The tinted box fills the body.
                var b = sprite.bounds.size;
                View.transform.localScale = new Vector3(spec.size.x / Mathf.Max(0.01f, b.x), spec.size.y / Mathf.Max(0.01f, b.y), 1f);
                View.transform.localPosition = Vector3.zero;
            }
            else
            {
                // Real art: true size from the sheet's ppu (U-036). Walkers: the bottom pivot stands on the
                // body's feet. Fliers (U-055): the centred pivot sits on the body's centre.
                View.transform.localScale = Vector3.one * spec.artScale;
                View.transform.localPosition = spec.Flies ? Vector3.zero : new Vector3(0f, -spec.size.y * 0.5f, 0f);
            }
            View.color = placeholder ? spec.placeholder : Color.white;
            View.enabled = true;
            EnsureModel(spec);
            transform.position = position;
            gameObject.SetActive(true);
            Body.gravityScale = spec.Flies ? 0f : 1f;
            Body.simulated = true;
            Body.position = position;
            Body.linearVelocity = Vector2.zero;
        }

        /// <summary>U-075: one model view per creature, swapped when a pooled body comes back as another species.</summary>
        void EnsureModel(SpeciesSpec spec)
        {
            if (Model != null && Model.Key == spec.artKey) return;
            if (Model != null) Destroy(Model.gameObject);
            var go = new GameObject("Model");
            go.transform.SetParent(transform, false);
            // The model's origin is its feet (contract §9): walkers stand on the body's bottom, fliers sit on its centre.
            go.transform.localPosition = spec.Flies ? Vector3.zero : new Vector3(0f, -spec.size.y * 0.5f, 0f);
            Model = go.AddComponent<Meridian.Art.ModelView>();
            Model.Load(spec.artKey);
        }

        /// <summary>Picks this frame's sprite (idle / walk / attack / hurt) and the chill tint. No allocation.</summary>
        internal void Animate(float dt, float speed)
        {
            if (Model != null && Model.Ready)
            {
                // U-075: the model plays the same clip choice by name; the sheet stays hidden.
                if (hurtFor > 0f) hurtFor -= dt;
                if (attackFor > 0f) attackFor -= dt;
                if (chillFor > 0f) { chillFor -= dt; if (chillFor > 0f) Model.Flash(0.05f); }
                if (View.enabled) View.enabled = false;
                int pick = hurtFor > 0f ? 3 : attackFor > 0f ? 2 : speed > 0.3f ? 1 : 0;
                Model.Play(ModelClips[pick]);
                return;
            }
            anim += dt;
            if (hurtFor > 0f) hurtFor -= dt;
            if (attackFor > 0f) attackFor -= dt;
            if (chillFor > 0f)
            {
                chillFor -= dt;
                View.color = chillFor > 0f ? new Color(0.6f, 0.85f, 1f) : Color.white; // the Veil Serpent's chilled flash
            }
            var sheet = nightFrames != null && Zone == MercuryZone.Night ? nightFrames : frames;
            if (sheet == null || clips == null || clips.clips.Count == 0) return;
            // Clip order in every B-0xx creature sheet: idle, walk, attack, hurt, death.
            int want = hurtFor > 0f ? 3 : attackFor > 0f ? 2 : speed > 0.3f ? 1 : 0;
            if (want >= clips.clips.Count) want = 0;
            if (want != lastClip) { lastClip = want; anim = 0f; }
            var clip = clips.clips[want];
            int step = Mathf.FloorToInt(anim * (clips.fps > 0 ? clips.fps : 12));
            int f = clip.start + (clip.loop ? step % Mathf.Max(1, clip.length) : Mathf.Min(step, clip.length - 1));
            if (f >= 0 && f < sheet.Length && sheet[f] != null) View.sprite = sheet[f];
        }
    }
}
