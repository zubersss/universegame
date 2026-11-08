using UnityEngine;

namespace Meridian.Ship
{
    /// <summary>
    /// U-107 (Bible §4.3 v4.1, D-102, D-103, D-106): the upright Pilgrim's flight, pure C#. Thrust acts along the ship's own
    /// up axis; A/D tilt it toward ±MaxTilt at TiltRate and a critically damped spring brings it back upright on release;
    /// gravity is the planet's. No fuel: the ship hovers where throttle × thrust = g, climbs above and sinks below. A
    /// touchdown tilted more than TipOverTilt sets off a 0.5 s righting with a wobble (no damage). Tilt is a z rotation
    /// in degrees: positive = nose to the left (A), negative = nose to the right (D).
    /// </summary>
    public sealed class RocketFlight
    {
        public const float MaxTilt = 35f;
        public const float TipOverTilt = 20f, RightingSeconds = 0.5f;
        /// <summary>U-149 (D-158 (3)): the tilt has angular inertia: steering accelerates the turn up to TurnRate (°/s), reached in
        /// TurnAccelTime, and brakes at BrakeShare of that to stop on the target tilt (replaces the 140°/s MoveTowards).</summary>
        public const float TurnRate = 90f, TurnAccelTime = 0.25f, BrakeShare = 0.6f;
        /// <summary>U-149: released, the tilt returns upright on a critically damped spring (SmoothDamp, carrying the turn's rate): under 2° in
        /// ~0.33 s from 35°, no overshoot (replaces the 0.12 s snap).</summary>
        public const float ReturnTime = 0.15f;
        /// <summary>U-149: the throttle spools: 0 → 1 over SpoolUp with an ease-in (the throttle is the square of a phase rising linearly), 1 → 0
        /// over SpoolDown linearly. A key still means full thrust, reached smoothly; a trigger's value is the target.</summary>
        public const float SpoolUp = 0.35f, SpoolDown = 0.2f;
        /// <summary>U-149: quadratic air drag a = −DragK·ρ(h)·|v|·v, one k for the hull set: a full-thrust upright Mk1 at Earth's Datum (ρ 1)
        /// tends to 45 m/s, (12 − 9.81) / 45². A placeholder tuned on the captures (D-158).</summary>
        public const float DragK = (12f - 9.81f) / (45f * 45f);

        public float Tilt { get; private set; }
        public bool Righting => rightingLeft > 0f;
        /// <summary>U-149: the spooled throttle (0..1) the thruster gives this step.</summary>
        public float Throttle { get; private set; }
        /// <summary>U-149: the tilt's angular rate (°/s).</summary>
        public float TiltRateNow => tiltVel;
        float tiltVel, rightingLeft, rightingFrom;

        /// <summary>U-149: spools the throttle toward `target` (0..1) by one step.</summary>
        public void StepThrottle(float target, float dt)
        {
            target = Mathf.Clamp01(target);
            if (target > Throttle)
            {
                float phase = Mathf.Sqrt(Throttle);
                phase = Mathf.Min(Mathf.Sqrt(target), phase + dt / SpoolUp);
                Throttle = phase * phase;
            }
            else Throttle = Mathf.Max(target, Throttle - dt / SpoolDown);
        }

        /// <summary>U-149: the air's density `altitude` metres above the Datum: ρ_surface·(1 − h/H)², h clamped at 0 below the Datum, 0 at and
        /// above the Escape Line (H) and wherever there is no air. Pure.</summary>
        public static float AirDensity(float surfaceDensity, float altitude, float escapeAltitude)
        {
            if (surfaceDensity <= 0f || escapeAltitude <= 0f) return 0f;
            float k = 1f - Mathf.Max(0f, altitude) / escapeAltitude;
            return k <= 0f ? 0f : surfaceDensity * k * k;
        }

        /// <summary>U-149: the drag acceleration for a velocity in air of `density`: −DragK·ρ·|v|·v. Pure, no allocation.</summary>
        public static Vector2 DragAccel(Vector2 velocity, float density) => density > 0f ? velocity * (-DragK * density * velocity.magnitude) : Vector2.zero;

        /// <summary>The ship's up axis for a tilt (degrees, z rotation).</summary>
        public static Vector2 UpAxis(float tiltDeg)
        {
            float r = tiltDeg * Mathf.Deg2Rad;
            return new Vector2(-Mathf.Sin(r), Mathf.Cos(r));
        }

        /// <summary>The acceleration from the thruster alone (gravity not included): throttle 0..1 along the up axis.</summary>
        public Vector2 ThrustAccel(float throttle, float thrust) => UpAxis(Tilt) * (Mathf.Clamp01(throttle) * thrust);

        /// <summary>
        /// Steps the tilt by `dt`. `steer` is -1 (A, nose left) .. +1 (D, nose right); on the ground the ship stands upright
        /// (no tilting on the pad), and while righting after a tilted touchdown input is ignored.
        /// </summary>
        public void StepTilt(float steer, bool grounded, float dt)
        {
            if (rightingLeft > 0f)
            {
                rightingLeft = Mathf.Max(0f, rightingLeft - dt);
                float k = 1f - rightingLeft / RightingSeconds;              // 0 → 1 over the righting
                Tilt = rightingFrom * (1f - k) * (1f - k) * Mathf.Cos(3f * Mathf.PI * k); // swings past upright and settles
                tiltVel = 0f;
                if (rightingLeft <= 1e-4f) { rightingLeft = 0f; Tilt = 0f; } // float steps: the last one lands exactly upright
                return;
            }
            float s = grounded ? 0f : Mathf.Clamp(steer, -1f, 1f);
            if (Mathf.Abs(s) > 0.01f)
            {
                // U-149: angular inertia: the rate accelerates toward the fastest one that still brakes onto the target tilt in time.
                float target = -s * MaxTilt;
                float accel = TurnRate / TurnAccelTime, brake = accel * BrakeShare;
                float rem = target - Tilt;
                float want = Mathf.Sign(rem) * Mathf.Min(TurnRate * Mathf.Abs(s), Mathf.Sqrt(2f * brake * Mathf.Abs(rem)));
                tiltVel = Mathf.MoveTowards(tiltVel, want, accel * dt);
                Tilt += tiltVel * dt;
                if ((target - Tilt) * rem <= 0f) { Tilt = target; tiltVel = 0f; } // never past the target: it lands on it
            }
            else Tilt = Mathf.SmoothDamp(Tilt, 0f, ref tiltVel, ReturnTime, Mathf.Infinity, dt); // the turn's rate carries into the return
            Tilt = Mathf.Clamp(Tilt, -MaxTilt, MaxTilt);
        }

        /// <summary>Called on touchdown: true (and the righting starts) when the ship landed tilted more than TipOverTilt.</summary>
        public bool Touchdown()
        {
            if (Mathf.Abs(Tilt) <= TipOverTilt) return false;
            rightingFrom = Tilt;
            rightingLeft = RightingSeconds;
            return true;
        }

        public void Reset() { Tilt = 0f; tiltVel = 0f; rightingLeft = 0f; Throttle = 0f; }
    }
}
