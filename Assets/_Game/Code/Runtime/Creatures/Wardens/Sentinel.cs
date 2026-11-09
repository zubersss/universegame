using Meridian.FX;
using Meridian.Rendering;
using UnityEngine;

namespace Meridian.Creatures.Wardens
{
    public enum SentinelState { Patrol, Hunt }

    /// <summary>
    /// U-053: a Warden sentinel (B-043 creatures/warden/sentinel). It hovers (no gravity): on patrol it sweeps
    /// PatrolHalfWidth either side of its post; called, it closes in on the surveyor, rings its bell (the `attack`
    /// clip) and bumps them on contact. D-087: it never shoots and can't be destroyed (the Lance is archived); the tow
    /// and the 5-minute Beam lock arrive with their own task. Moved by the director, not by its own Update.
    /// </summary>
    public sealed class Sentinel : MonoBehaviour
    {
        public const float PatrolSpeed = 2f, HuntSpeed = 6f, PatrolHalfWidth = 8f;
        public const float Size = 1.6f;
        public const string ArtKey = "creatures/warden/sentinel";

        public SentinelState State { get; internal set; }
        public bool Alive => gameObject.activeSelf;
        public Vector2 Post { get; internal set; }
        public Rigidbody2D Body { get; private set; }

        internal WardenDirector director;
        internal float ringIn, bumpReady, anim;
        internal int sweep = 1;
        /// <summary>U-190: the hunt's way through open air (WardenDirector re-plans it).</summary>
        internal Vector2 goal;
        internal float replanAt;
        internal bool direct;
        SpriteRenderer view;
        FxSheet sheet;
        ArtClipSet clips;
        string playing;

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
            Post = post;
            State = state;
            ringIn = 1.2f;
            bumpReady = 0f;
            anim = 0f;
            playing = null;
            Body.position = at;
            transform.position = at;
            gameObject.SetActive(true);
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
                if (playing == "attack") playing = null;
                step = clip.length - 1;
            }
            int f = clip.start + (clip.loop ? step % clip.length : Mathf.Min(step, clip.length - 1));
            if (f >= 0 && f < sheet.frames.Length) view.sprite = sheet.frames[f];
        }
    }
}
