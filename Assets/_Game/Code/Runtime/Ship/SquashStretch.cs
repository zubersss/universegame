using UnityEngine;

namespace Meridian.Ship
{
    /// <summary>
    /// U-103 (Bible §9.3 v4, D-100): the Pilgrim's cartoon squash and stretch, pure. Thrust held stretches the hull along
    /// its own up axis to ThrustStretch; cutting the thrust squashes it to CutSquash for CutHold seconds; both ease over
    /// EaseSeconds. Area-preserving: the across scale is the inverse. Applied as the view root's local scale (the root
    /// turns with the tilt, so "along" is always the ship's up axis); the physics never sees it.
    /// </summary>
    public sealed class SquashStretch
    {
        public const float ThrustStretch = 1.15f, CutSquash = 0.9f, EaseSeconds = 0.12f, CutHold = 0.08f;

        /// <summary>Scale along the up axis (1 at rest).</summary>
        public float Along { get; private set; } = 1f;
        /// <summary>Scale across the up axis: area-preserving.</summary>
        public float Across => 1f / Along;
        public bool Squashing => holdLeft > 0f;

        bool wasThrusting;
        float holdLeft;

        /// <summary>Advances by dt; `thrusting` is the throttle held this step.</summary>
        public void Step(bool thrusting, float dt)
        {
            if (wasThrusting && !thrusting) { Along = CutSquash; holdLeft = CutHold; } // the cut: a drawn pop to the squash, held, then eased back
            wasThrusting = thrusting;
            if (holdLeft > 0f) { holdLeft = Mathf.Max(0f, holdLeft - dt); return; }
            float target = thrusting ? ThrustStretch : 1f;
            Along += (target - Along) * (1f - Mathf.Exp(-dt / EaseSeconds));
        }

        public void Reset() { Along = 1f; holdLeft = 0f; wasThrusting = false; }

        /// <summary>The local scale for a view whose local y is the ship's up axis.</summary>
        public Vector3 LocalScale => new Vector3(Across, Along, 1f);
    }
}
