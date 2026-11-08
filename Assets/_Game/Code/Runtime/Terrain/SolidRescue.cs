using System.Collections.Generic;
using UnityEngine;

namespace Meridian.Terrain
{
    /// <summary>
    /// U-156 / D-165 (a): no body falls out of the world. A smooth planet's ground is an edge outline with no inside to push a buried body back
    /// out (box colliders used to), so every awake dynamic body (the surveyor, the ship, creatures, item drops: Register) whose foot lies inside
    /// the drawn solid is lifted onto the surface above it on the next physics step, logged once per body. TerrainStreamer ticks it from
    /// FixedUpdate on smooth planets only (a block planet's box colliders still push a buried body out): a few tile reads and two curve
    /// samples per awake body.
    /// </summary>
    public static class SolidRescue
    {
        /// <summary>How far past the iso the probe must sit to count as buried: 0.2 m into natural ground, 0.05 m into a dug or built edge.</summary>
        public const float Margin = 0.05f;
        /// <summary>The lift lands the body's lowest collider this far over the surface.</summary>
        public const float Clearance = 0.02f;
        /// <summary>How far up the surface is sought (a body deeper than this stays put; the world's crust is far thinner).</summary>
        public const float MaxLift = 96f;

        static readonly List<Rigidbody2D> bodies = new List<Rigidbody2D>();
        static readonly HashSet<Rigidbody2D> logged = new HashSet<Rigidbody2D>();
        static readonly List<Collider2D> shapes = new List<Collider2D>();

        /// <summary>Lifts so far (tests and the profiler's log).</summary>
        public static int Rescues { get; private set; }

        static readonly HashSet<Rigidbody2D> parks = new HashSet<Rigidbody2D>(), parked = new HashSet<Rigidbody2D>();

        /// <summary>Watches a dynamic body. parkOverUnloadedGround: the body is held still (not simulated) while the ground under it is not
        /// streamed in, and let go once it is (the Pilgrim left parked a kilometre away; a creature holds itself, CreatureDirector).</summary>
        public static void Register(Rigidbody2D body, bool parkOverUnloadedGround = false)
        {
            if (body == null) return;
            if (!bodies.Contains(body)) bodies.Add(body);
            if (parkOverUnloadedGround) parks.Add(body);
        }

        public static void Unregister(Rigidbody2D body)
        {
            if (body == null) return;
            if (parked.Remove(body)) body.simulated = true;
            bodies.Remove(body); logged.Remove(body); parks.Remove(body);
        }

        /// <summary>The ground under a body's pivot is streamed in (its chunk and the one 2 m below its feet).</summary>
        static bool GroundReady(TerrainStreamer t, Rigidbody2D b)
        {
            int x = Mathf.FloorToInt(b.position.x), y = Mathf.FloorToInt(b.position.y);
            return t.IsCollisionReady(x, y) && t.IsCollisionReady(x, y - 2);
        }

        /// <summary>Bodies held over unloaded ground right now (tests).</summary>
        public static int Parked => parked.Count;

        /// <summary>The drawn ground's density at p (the outline is its iso, GroundField.Iso): the four tile-centre nodes round p, bilinear.</summary>
        public static float Density(TerrainStreamer t, Vector2 p)
        {
            float fx = p.x - 0.5f, fy = p.y - 0.5f;
            int i = Mathf.FloorToInt(fx), j = Mathf.FloorToInt(fy);
            float u = fx - i, v = fy - j, c0 = t.CurveAt(i), c1 = t.CurveAt(i + 1);
            float bottom = Mathf.Lerp(Node(t, i, j, c0), Node(t, i + 1, j, c1), u);
            float top = Mathf.Lerp(Node(t, i, j + 1, c0), Node(t, i + 1, j + 1, c1), u);
            return Mathf.Lerp(bottom, top, v);
        }

        static float Node(TerrainStreamer t, int x, int y, float curve)
        {
            bool solid = TileId.IsSolid(t.GetTile(x, y));
            int top = t.OriginalTop(x);
            return GroundField.Density(solid, top != int.MinValue && solid == (y <= top), curve, y);
        }

        /// <summary>True where p is buried in the ground (past the margin); false in the open, in a dug hole, under water.</summary>
        public static bool Inside(TerrainStreamer t, Vector2 p) => Density(t, p) > GroundField.Iso + Margin;

        /// <summary>The ground's surface straight above a buried p (the first open point, to a millimetre on the outline); NaN past MaxLift.</summary>
        public static float SurfaceAbove(TerrainStreamer t, Vector2 p)
        {
            const float Step = 0.25f;
            float lo = p.y;
            for (float up = Step; up <= MaxLift; up += Step)
            {
                float hi = p.y + up;
                if (Density(t, new Vector2(p.x, hi)) > GroundField.Iso) { lo = hi; continue; }
                for (int k = 0; k < 8; k++) // bisect the crossing to ~1 mm
                {
                    float mid = (lo + hi) * 0.5f;
                    if (Density(t, new Vector2(p.x, mid)) > GroundField.Iso) lo = mid; else hi = mid;
                }
                return hi;
            }
            return float.NaN;
        }

        /// <summary>One pass over the registered bodies (TerrainStreamer.FixedUpdate); returns how many were lifted.</summary>
        public static int Tick(TerrainStreamer t)
        {
            int lifted = 0;
            for (int k = bodies.Count - 1; k >= 0; k--)
            {
                var b = bodies[k];
                if (b == null) { bodies.RemoveAt(k); continue; }
                if (parked.Contains(b)) { if (GroundReady(t, b)) { b.simulated = true; parked.Remove(b); } continue; }
                if (parks.Contains(b) && b.simulated && !GroundReady(t, b)) { b.simulated = false; parked.Add(b); continue; }
                if (!b.simulated || b.bodyType != RigidbodyType2D.Dynamic || !b.gameObject.activeInHierarchy || b.IsSleeping()) continue;
                if (!Bounds(b, out Bounds box)) continue;
                // The probe: up to ½ m over the body's lowest point (a tall rocket counts as buried once its foot is, not its middle).
                Vector2 centre = new Vector2(box.center.x, box.min.y + Mathf.Min(0.5f, box.extents.y));
                if (!Inside(t, centre)) continue;
                float surface = SurfaceAbove(t, centre);
                if (float.IsNaN(surface)) continue;
                // A wide body (the ship; a creature on a slope) clears the ground under its whole footprint, not just its centre column.
                float inset = Mathf.Min(0.05f, box.extents.x);
                float left = SurfaceAbove(t, new Vector2(box.min.x + inset, centre.y)), right = SurfaceAbove(t, new Vector2(box.max.x - inset, centre.y));
                if (!float.IsNaN(left)) surface = Mathf.Max(surface, left);
                if (!float.IsNaN(right)) surface = Mathf.Max(surface, right);
                float rise = surface + Clearance - box.min.y;
                if (rise <= 0f) continue;
                b.position += new Vector2(0f, rise);
                b.transform.position += new Vector3(0f, rise, 0f);
                var v = b.linearVelocity; if (v.y < 0f) b.linearVelocity = new Vector2(v.x, 0f);
                lifted++; Rescues++;
                if (logged.Add(b))
                    Debug.Log($"[MERIDIAN] solid rescue: {b.name} buried at ({centre.x:F1}, {centre.y:F1}), lifted {rise:F2} m onto the ground at {surface:F2}");
            }
            return lifted;
        }

        static bool Bounds(Rigidbody2D b, out Bounds box)
        {
            box = default;
            bool any = false;
            shapes.Clear();
            b.GetAttachedColliders(shapes);
            foreach (var c in shapes)
            {
                if (c == null || c.isTrigger || !c.enabled) continue;
                if (!any) { box = c.bounds; any = true; } else box.Encapsulate(c.bounds);
            }
            return any;
        }
    }
}
