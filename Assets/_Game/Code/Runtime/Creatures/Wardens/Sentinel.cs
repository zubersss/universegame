using Meridian.FX;
using Meridian.Rendering;
using UnityEngine;

namespace Meridian.Creatures.Wardens
{
    public enum SentinelState { Patrol, Hunt, Dying }

    /// <summary>
    /// U-053: a Warden sentinel (B-043 creatures/warden/sentinel). It hovers (no gravity): on patrol it sweeps
    /// PatrolHalfWidth either side of its post; hunting, it holds a firing point above and beside the surveyor
    /// and the director fires its bolts. The Lance kills it (Hurt). Moved by the director, not by its own Update.
    /// </summary>
    public sealed class Sentinel : MonoBehaviour
    {
        public const float MaxHealth = 75f, PatrolSpeed = 2f, HuntSpeed = 6f, PatrolHalfWidth = 8f;
        public const float Size = 1.6f, DeathSeconds = 0.5f;
        public const string ArtKey = "creatures/warden/sentinel";

        public SentinelState State { get; internal set; }
        public float Health { get; private set; }
        public bool Alive => gameObject.activeSelf && State != SentinelState.Dying;
        public Vector2 Post { get; internal set; }
        public Rigidbody2D Body { get; private set; }

        internal WardenDirector director;
        internal float fireIn, anim, dyingFor;
        internal int sweep = 1;
        SpriteRenderer view;
        FxSheet sheet;
        ArtClipSet clips;
        string playing;

        public static event System.Action<Sentinel> Destroyed;

        internal void Build()
        {
            Body = gameObject.AddComponent<Rigidbody2D>();
            Body.bodyType = RigidbodyType2D.Kinematic;
            Body.interpolation = RigidbodyInterpolation2D.Interpolate;
            var box = gameObject.AddComponent<BoxCollider2D>();
            box.size = new Vector2(Size * 0.5f, Size * 0.4f);
            box.isTrigger = true;
            view = gameObject.AddComponent<SpriteRenderer>();
            view.sortingOrder = 6;
            sheet = FxSheet.Get(ArtKey);
            clips = ArtMaterials.ClipsFor(ArtKey);
        }

        internal void Begin(Vector2 at, Vector2 post, SentinelState state)
        {
            Health = MaxHealth;
            Post = post;
            State = state;
            fireIn = 1.2f;
            anim = 0f;
            dyingFor = 0f;
            playing = null;
            Body.position = at;
            transform.position = at;
            gameObject.SetActive(true);
        }

        /// <summary>Damage (the Lance). True if this destroyed it.</summary>
        public bool Hurt(float damage)
        {
            if (!Alive || damage <= 0f) return false;
            Health -= damage;
            if (Health > 0f) { Play("hurt"); return false; }
            Health = 0f;
            State = SentinelState.Dying;
            Play("death");
            Destroyed?.Invoke(this);
            return true;
        }

        internal void Play(string clip) { if (playing != clip) { playing = clip; anim = 0f; } }

        /// <summary>Picks the frame; called by the director each frame.</summary>
        internal void Animate(float dt, float faceX)
        {
            anim += dt;
            if (view == null || sheet == null || !sheet.Ready) return;
            if (view.sprite == null && sheet.material != null) view.sharedMaterial = sheet.material;
            float w = sheet.frames[0].bounds.size.x;
            if (w > 0f) transform.localScale = Vector3.one * (Size / w);
            if (faceX != 0f) view.flipX = faceX < 0f;
            string name = playing ?? (State == SentinelState.Hunt ? "walk" : "idle");
            if (clips == null || !clips.TryGet(name, out var clip)) { view.sprite = sheet.frames[0]; return; }
            int step = Mathf.FloorToInt(anim * (clips.fps > 0 ? clips.fps : 12));
            if (!clip.loop && step >= clip.length)
            {
                if (playing == "hurt" || playing == "attack") playing = null;
                step = clip.length - 1;
            }
            int f = clip.start + (clip.loop ? step % clip.length : Mathf.Min(step, clip.length - 1));
            if (f >= 0 && f < sheet.frames.Length) view.sprite = sheet.frames[f];
        }
    }
}
