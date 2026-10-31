using System.Collections.Generic;
using Meridian.Art;
using Meridian.FX;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Rig
{
    /// <summary>
    /// The Lance's projectiles (U-046): pooled fx/lance_bolt sprites (pivot [0.75, 0.5]: the glowing head
    /// leads) that fly straight from the muzzle, stop on terrain, and hurt the first creature they meet.
    /// They pass through the surveyor, drops and the ship. No allocation per shot.
    /// </summary>
    public sealed class LanceBolts : MonoBehaviour
    {
        public const float Speed = 40f, Range = 30f, Damage = 25f;
        /// <summary>Drawn length of a bolt (m): the 128 × 32 px sheet at ppu 128 is 1 × 0.25 m.</summary>
        public const int PoolSize = 8;

        sealed class Bolt
        {
            public SpriteRenderer view;
            public Vector2 pos, dir;
            public float travelled, age;
            public bool live;
        }

        readonly List<Bolt> bolts = new List<Bolt>(PoolSize);
        readonly RaycastHit2D[] hits = new RaycastHit2D[8];
        static readonly ContactFilter2D AnyCollider = ContactFilter2D.noFilter;
        FxSheet sheet;

        /// <summary>Raised when a bolt hits a creature (the creature, whether it died).</summary>
        public event System.Action<Meridian.Creatures.Creature, bool> HitCreature;
        public int Live { get; private set; }

        void Awake()
        {
            for (int i = 0; i < PoolSize; i++)
            {
                var go = new GameObject("LanceBolt" + i);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = 7;
                go.SetActive(false);
                bolts.Add(new Bolt { view = sr });
            }
        }

        void Start() => sheet = FxSheet.Get(ArtKeys.Fx.LanceBolt);

        /// <summary>Fires one bolt; false if all are in flight.</summary>
        public bool Fire(Vector2 from, Vector2 direction)
        {
            if (direction.sqrMagnitude < 1e-6f) return false;
            foreach (var b in bolts)
            {
                if (b.live) continue;
                b.live = true;
                b.pos = from;
                b.dir = direction.normalized;
                b.travelled = 0f;
                b.age = 0f;
                b.view.transform.position = from;
                b.view.transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(b.dir.y, b.dir.x) * Mathf.Rad2Deg);
                if (sheet != null && sheet.Ready)
                {
                    b.view.sprite = sheet.frames[0];
                    if (sheet.material != null) b.view.sharedMaterial = sheet.material;
                }
                b.view.gameObject.SetActive(true);
                Live++;
                return true;
            }
            return false;
        }

        void FixedUpdate()
        {
            float step = Speed * Time.fixedDeltaTime;
            foreach (var b in bolts)
            {
                if (!b.live) continue;
                b.age += Time.fixedDeltaTime;
                int n = Physics2D.Raycast(b.pos, b.dir, AnyCollider, hits, step);
                bool stop = false;
                for (int i = 0; i < n && !stop; i++)
                {
                    var col = hits[i].collider;
                    var creature = col.GetComponentInParent<Meridian.Creatures.Creature>();
                    if (creature != null && creature.Alive)
                    {
                        bool killed = creature.Hurt(Damage);
                        HitCreature?.Invoke(creature, killed);
                        stop = true;
                    }
                    else if (col.GetComponentInParent<TerrainChunk>() != null) stop = true;
                }
                b.pos += b.dir * step;
                b.travelled += step;
                if (stop || b.travelled >= Range) { Retire(b); continue; }
                b.view.transform.position = b.pos;
                if (sheet != null && sheet.Ready)
                {
                    int f = sheet.FrameAt(b.age);
                    if (f >= 0) b.view.sprite = sheet.frames[f];
                }
            }
        }

        void Retire(Bolt b)
        {
            b.live = false;
            b.view.gameObject.SetActive(false);
            Live--;
        }
    }
}
