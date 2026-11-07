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
        public const float MaxTilt = 35f, TiltRate = 140f, SpringTime = 0.12f;
        public const float TipOverTilt = 20f, RightingSeconds = 0.5f;

        public float Tilt { get; private set; }
        public bool Righting => rightingLeft > 0f;
        float tiltVel, rightingLeft, rightingFrom;

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
                Tilt = Mathf.MoveTowards(Tilt, -s * MaxTilt, TiltRate * dt);
                tiltVel = 0f;
            }
            else Tilt = Mathf.SmoothDamp(Tilt, 0f, ref tiltVel, SpringTime, Mathf.Infinity, dt);
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

        public void Reset() { Tilt = 0f; tiltVel = 0f; rightingLeft = 0f; }
    }
}
