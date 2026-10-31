using Meridian.Art;
using Meridian.Ship;
using Meridian.Space;
using UnityEngine;

namespace Meridian.FX
{
    /// <summary>
    /// U-033 ship effects. Side view (SideShip): main engine flame aft and two belly-pod flames while
    /// thrusting; heat shimmer under the hull while it comes down fast high above the ground (entry).
    /// Top-down (SpaceShip): the engine flame behind the hull while thrusting.
    /// </summary>
    public sealed class ShipFx : MonoBehaviour
    {
        public SideShip side;
        public SpaceShip top;

        /// <summary>Entry shimmer: descending faster than this (m/s) and higher than ShimmerAltitude above ground.</summary>
        public const float ShimmerSpeed = 8f, ShimmerAltitude = 30f;

        public FxLoop Main { get; private set; }
        public FxLoop PodFore { get; private set; }
        public FxLoop PodAft { get; private set; }
        public FxLoop Shimmer { get; private set; }

        void Awake()
        {
            if (side != null)
            {
                // Positions on the 11.4 × 3.4 m hull (B-008 side sheet): nozzle at the stern, lift vents under the belly.
                Main = Make("Main", ArtKeys.Fx.Thruster, new Vector2(-SideShip.HullLength * 0.5f + 0.3f, -0.1f), -90f, new Vector2(2.2f, 2.4f));
                PodAft = Make("PodAft", ArtKeys.Fx.Thruster, new Vector2(-2.8f, -1.3f), 0f, new Vector2(1.6f, 1.8f));
                PodFore = Make("PodFore", ArtKeys.Fx.Thruster, new Vector2(2.45f, -1.3f), 0f, new Vector2(1.6f, 1.8f));
                // B-030 entry heat: a 1 m square frame (ppu 128) with the bow-shock arc low in it and the plasma
                // trailing up. At 13 m the arc (~85% of the width) spans the 11.4 m hull and sits ~0.7 m under
                // the belly. Its emission map makes it glow through night and dust (Sprite_LitEmissive).
                Shimmer = Make("Shimmer", ArtKeys.Fx.HeatShimmer, new Vector2(0.5f, 2.4f), 0f, new Vector2(13f, 13f));
                Shimmer.flicker = 0f;
            }
            else if (top != null)
            {
                Main = Make("Main", ArtKeys.Fx.Thruster, new Vector2(-2.1f, 0f), -90f, new Vector2(1.2f, 1.6f)); // ship drawn 4 u wide
            }
        }

        FxLoop Make(string name, string key, Vector2 local, float rot, Vector2 scale)
        {
            var go = new GameObject("Fx" + name);
            go.transform.SetParent(transform, false);
            go.transform.localPosition = local;
            go.transform.localRotation = Quaternion.Euler(0f, 0f, rot);
            go.transform.localScale = new Vector3(scale.x, scale.y, 1f);
            var loop = go.AddComponent<FxLoop>(); // its Awake adds the SpriteRenderer
            loop.key = key;
            loop.target.sortingOrder = name == "Shimmer" ? 12 : -1; // flames tuck behind the hull, shimmer over it
            loop.flicker = 0.18f;
            return loop;
        }

        void LateUpdate()
        {
            if (side != null)
            {
                bool flying = side.piloted && !side.Grounded;
                bool lift = side.piloted && side.intent.thrust > 0.05f;
                Main.active = lift || (flying && Mathf.Abs(side.intent.lateral) > 0.05f);
                PodAft.active = PodFore.active = lift;
                var v = side.Body != null ? side.Body.linearVelocity : Vector2.zero;
                Shimmer.active = v.y < -ShimmerSpeed && side.AltitudeAboveGround > ShimmerAltitude;
            }
            else if (top != null)
            {
                Main.active = !top.Destroyed && top.intent.thrust > 0.05f;
            }
        }
    }
}
