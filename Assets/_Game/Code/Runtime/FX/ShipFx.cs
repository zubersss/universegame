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
        /// <summary>U-103 (B-122): true once the loops sit on the drawn rig's sockets (tail_exhaust, attitude_l / attitude_r) with the puff sheet.</summary>
        public bool OnRig { get; private set; }
        Meridian.Ship.ShipLegsView legsView;

        void Awake()
        {
            if (side != null)
            {
                // U-107 (D-102): the rocket stands upright on its tail: the main nozzle points down out of the tail (below the
                // pivot by SkidDrop), two small vents at the leg roots. Children of the ship, so they tilt with it.
                Main = Make("Main", ArtKeys.Fx.Thruster, new Vector2(0f, -SideShip.SkidDrop - 0.9f), 0f, new Vector2(2.2f, 2.4f));
                PodAft = Make("PodAft", ArtKeys.Fx.Thruster, new Vector2(-1.5f, -SideShip.SkidDrop + 0.4f), 0f, new Vector2(1.0f, 1.2f));
                PodFore = Make("PodFore", ArtKeys.Fx.Thruster, new Vector2(1.5f, -SideShip.SkidDrop + 0.4f), 0f, new Vector2(1.0f, 1.2f));
                // B-030 entry heat: a 1 m square frame (ppu 128) with the bow-shock arc low in it and the plasma
                // trailing up. At 13 m the arc (~85% of the width) spans the 11.4 m hull and sits ~0.7 m under
                // the belly. Its emission map makes it glow through night and dust (Sprite_LitEmissive).
                Shimmer = Make("Shimmer", ArtKeys.Fx.HeatShimmer, new Vector2(0f, -SideShip.SkidDrop + 1.2f), 0f, new Vector2(7f, 7f)); // the tail leads on the way down
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
            loop.target.sortingOrder = name == "Shimmer" ? -2 : -1; // all behind the hull: the shimmer's plasma trails around it, its bow shock glows below the belly
            loop.flicker = 0.18f;
            return loop;
        }

        /// <summary>
        /// U-103 (B-122, D-111): with the drawn rig the main flame becomes the puff loop hanging from the tail_exhaust socket
        /// (the puff's pivot is its top centre) and the attitude puffs sit at attitude_l / attitude_r blowing outward, all under
        /// the squash root so they stretch with the hull; sockets are metres from the rig origin on the skid line and never move
        /// with the clips. The entry shimmer stays where it was.
        /// </summary>
        void PlaceOnRig()
        {
            if (legsView == null) legsView = side.GetComponentInChildren<Meridian.Ship.ShipLegsView>();
            if (legsView == null || !legsView.RigReady) return;
            OnRig = true;
            var rig = legsView.Rig;
            var origin = new Vector2(0f, -SideShip.SkidDrop);
            int layer = legsView.target != null ? legsView.target.sortingLayerID : 0;
            int behind = (legsView.target != null ? legsView.target.sortingOrder : 0) - 1;
            Move(Main, ArtKeys.Ships.PilgrimPuff, origin + rig.Socket("tail_exhaust", new Vector2(0f, 0.85f)), 0f, new Vector2(1.3f, 1.3f), legsView.SquashRoot, layer, behind);
            Move(PodAft, ArtKeys.Ships.PilgrimPuff, origin + rig.Socket("attitude_l", new Vector2(-1.5f, 2.6f)), -90f, new Vector2(0.45f, 0.45f), legsView.SquashRoot, layer, behind);
            Move(PodFore, ArtKeys.Ships.PilgrimPuff, origin + rig.Socket("attitude_r", new Vector2(1.5f, 2.6f)), 90f, new Vector2(0.45f, 0.45f), legsView.SquashRoot, layer, behind);
        }

        static void Move(FxLoop loop, string key, Vector2 local, float rot, Vector2 scale, Transform parent, int layer, int order)
        {
            if (parent != null) loop.transform.SetParent(parent, false);
            loop.transform.localPosition = local;
            loop.transform.localRotation = Quaternion.Euler(0f, 0f, rot);
            loop.transform.localScale = new Vector3(scale.x, scale.y, 1f);
            loop.target.sortingLayerID = layer;
            loop.target.sortingOrder = order;
            loop.SetKey(key);
        }

        void LateUpdate()
        {
            if (side != null)
            {
                if (!OnRig) PlaceOnRig();
                bool flying = side.piloted && !side.Grounded;
                bool lift = side.piloted && side.intent.thrust > 0.05f;
                Main.active = lift;
                PodAft.active = PodFore.active = flying && Mathf.Abs(side.intent.lateral) > 0.05f; // attitude puffs while tilting
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
