using UnityEngine;

namespace Meridian.Player
{
    /// <summary>
    /// U-088 (Bible §4.2 Feel, D-078): the air dash, a velocity override like the jetpack's thrust, never a gravity
    /// change. Shift tapped while airborne: Speed in the facing direction for Duration with the vertical speed held
    /// at 0, then the planet's g resumes at once. One per airtime, refreshed by landing or a successful parry;
    /// Cooldown between dashes. Pure C#, stepped by PlayerController in FixedUpdate.
    /// </summary>
    public sealed class AirDash
    {
        public const float Speed = 9f, Duration = 0.18f, Cooldown = 0.35f;
        /// <summary>1.62 m on every planet.</summary>
        public const float Distance = Speed * Duration;

        public bool Active => remaining > 0f;
        public bool Available { get; private set; } = true;
        public int Direction { get; private set; } = 1;
        public float CooldownLeft => cooldown;

        float remaining, cooldown;

        /// <summary>Landing or a successful parry gives the dash back.</summary>
        public void Refresh() => Available = true;

        public bool TryStart(bool airborne, int facing)
        {
            if (!airborne || !Available || Active || cooldown > 0f) return false;
            Available = false;
            remaining = Duration;
            Direction = facing < 0 ? -1 : 1;
            return true;
        }

        /// <summary>
        /// Advances by `dt`. True while the dash owns this step's velocity; `share` is the fraction of the step inside
        /// the dash (1 except for the step it ends in), so the distance is exact at any fixed step.
        /// </summary>
        public bool Step(float dt, bool grounded, out float share)
        {
            share = 0f;
            if (cooldown > 0f) cooldown = Mathf.Max(0f, cooldown - dt);
            if (grounded && !Active) Available = true;
            if (!Active) return false;
            float used = Mathf.Min(dt, remaining);
            remaining -= used;
            share = dt > 0f ? used / dt : 1f;
            if (remaining <= 1e-6f) { remaining = 0f; cooldown = Cooldown; }
            return true;
        }
    }
}
