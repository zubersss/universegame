using UnityEngine;

namespace Meridian.Player
{
    /// <summary>Side-view movement numbers, Bible §4.2. Same on every planet; gravity is the planet's.</summary>
    public static class PlayerTuning
    {
        public const float WalkSpeed = 4.0f;
        public const float SprintSpeed = 6.5f;
        public const float JumpSpeed = 7.00f;          // v₀; Servo upgrades scale this, never gravity
        public const float CoyoteTime = 0.10f;
        public const float JumpBuffer = 0.12f;
        public const float SafeImpact = 12f;           // no damage below
        public const float LethalImpact = 24f;         // lethal at or above (unupgraded)
        public const float GroundAcceleration = 40f;   // reach walk speed in 0.1 s
        public const float AirAcceleration = 20f;
        public const float Height = 1.8f, Width = 0.6f;
    }

    /// <summary>Coyote time and jump buffering (Bible §4.2), driven by explicit time steps.</summary>
    public sealed class JumpTimer
    {
        float sinceGrounded = float.MaxValue;
        float sincePressed = float.MaxValue;
        bool jumpedSinceGrounded;

        /// <summary>Advance by dt; returns true when a jump should start this step.</summary>
        public bool Step(float dt, bool grounded, bool pressedThisStep)
        {
            if (grounded) { sinceGrounded = 0f; jumpedSinceGrounded = false; }
            else sinceGrounded += dt;
            if (pressedThisStep) sincePressed = 0f;
            else sincePressed += dt;

            bool canJump = !jumpedSinceGrounded && sinceGrounded <= PlayerTuning.CoyoteTime + 1e-5f;
            bool wantsJump = sincePressed <= PlayerTuning.JumpBuffer + 1e-5f;
            if (!canJump || !wantsJump) return false;
            jumpedSinceGrounded = true;
            sincePressed = float.MaxValue;
            sinceGrounded = float.MaxValue;
            return true;
        }
    }

    /// <summary>Fall damage from impact speed (Bible §4.2): none below 12 m/s, lethal at 24 m/s, linear between.</summary>
    public static class FallDamage
    {
        public static float Fraction(float impactSpeed, float safe = PlayerTuning.SafeImpact, float lethal = PlayerTuning.LethalImpact)
        {
            if (impactSpeed < safe) return 0f;
            if (impactSpeed >= lethal) return 1f;
            return (impactSpeed - safe) / (lethal - safe);
        }

        /// <summary>Highest drop (m) that lands below the safe speed on a planet: 72 / g (Bible §4.2).</summary>
        public static float SafeDrop(float gravity) => PlayerTuning.SafeImpact * PlayerTuning.SafeImpact / (2f * gravity);
    }

    /// <summary>Jetpack thrust and fuel (Bible §4.2 table). Burns while held in the air; refills in 2 s on the ground.</summary>
    public sealed class Jetpack
    {
        public const float RechargeTime = 2f;

        public float Thrust { get; private set; }
        public float BurnTime { get; private set; }
        public float Remaining { get; private set; }
        public bool Firing { get; private set; }

        public Jetpack(int mark = 1) => SetMark(mark);

        public void SetMark(int mark)
        {
            switch (mark)
            {
                case 3: Thrust = 30f; BurnTime = 6f; break;
                case 2: Thrust = 20f; BurnTime = 4.5f; break;
                default: Thrust = 14f; BurnTime = 3f; break;
            }
            Remaining = BurnTime;
        }

        /// <summary>Upward acceleration (m/s²) to apply this step.</summary>
        public float Step(float dt, bool held, bool grounded)
        {
            Firing = false;
            if (grounded)
            {
                Remaining = Mathf.Min(BurnTime, Remaining + BurnTime * dt / RechargeTime);
                return 0f;
            }
            if (!held || Remaining <= 0f) return 0f;
            float used = Mathf.Min(dt, Remaining);
            Remaining -= used;
            if (Remaining < 1e-4f) Remaining = 0f; // float slivers would otherwise add one extra burn step
            Firing = true;
            return Thrust * used / dt;
        }
    }
}
