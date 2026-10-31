using UnityEngine;

namespace Meridian.Creatures
{
    public enum CreatureState { Idle, Wander, Flee, Chase }

    /// <summary>
    /// One creature (U-027): a dynamic Rigidbody2D under the planet's real gravity, a box collider and a
    /// sprite. It has no Update of its own: CreatureDirector thinks and steers for all creatures in one
    /// loop (so the AI cost is one measured number). Pooled.
    /// </summary>
    public sealed class Creature : MonoBehaviour
    {
        public SpeciesSpec Spec { get; private set; }
        public Rigidbody2D Body { get; private set; }
        public BoxCollider2D Box { get; private set; }
        public SpriteRenderer View { get; private set; }
        public CreatureState State { get; internal set; }
        /// <summary>Held: its chunk isn't loaded with collision, so the body is paused in place.</summary>
        public bool Held { get; internal set; }
        public bool Alive => gameObject.activeSelf;

        internal int dir = 1;
        internal float nextThink, biteReady;
        internal int serial;

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

        internal void Setup(SpeciesSpec spec, Vector2 position, Sprite sprite, int serial)
        {
            Spec = spec;
            this.serial = serial;
            State = CreatureState.Wander;
            Held = false;
            dir = (serial & 1) == 0 ? 1 : -1;
            nextThink = 0f;
            biteReady = 0f;
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
                // Real art: true size from the sheet's ppu (U-036); its bottom pivot stands on the body's feet.
                View.transform.localScale = Vector3.one;
                View.transform.localPosition = new Vector3(0f, -spec.size.y * 0.5f, 0f);
            }
            View.color = placeholder ? spec.placeholder : Color.white;
            transform.position = position;
            gameObject.SetActive(true);
            Body.simulated = true;
            Body.position = position;
            Body.linearVelocity = Vector2.zero;
        }
    }
}
