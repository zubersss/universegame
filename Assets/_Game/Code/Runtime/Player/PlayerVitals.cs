using System;
using UnityEngine;

namespace Meridian.Player
{
    /// <summary>
    /// U-093 (Bible v4, D-087): the surveyor has no health. Suit power is the one survival meter besides oxygen; it is
    /// the suit's integrity (HazardSystem.SuitIntegrity, drained first) plus this reserve (the last 100, drained by
    /// hazards after the integrity and by hard landings). At 0 the surveyor conks out (ConkOut: iris-out, wake at the
    /// last base or the ship, cargo kept) and the reserve refills. The field names stay `health` for the save format
    /// and LeadQA; read them as "suit reserve".
    /// </summary>
    public sealed class PlayerVitals : MonoBehaviour
    {
        public float maxHealth = 100f;
        public float health = 100f;

        /// <summary>Suit power is empty: conked out until ConkOut wakes the surveyor.</summary>
        public bool Dead => health <= 0f;
        /// <summary>Raised once when Suit power reaches 0 (ConkOut listens).</summary>
        public event Action Died;
        /// <summary>Raised with the amount whenever the reserve drops (the `hurt` clip).</summary>
        public event Action<float> Damaged;

        /// <summary>A hard landing (12–24 m/s, PlayerTuning) drains the reserve; 24 m/s or more empties it.</summary>
        public void TakeFallImpact(float impactSpeed)
        {
            float f = FallDamage.Fraction(impactSpeed) * Meridian.Progress.SkillStats.FallDamageFactor; // U-175: Endurance's fall cut
            float safe = Meridian.Progress.SkillStats.SafeFallM, g = -Physics2D.gravity.y;
            if (safe > 0f && g > 0f && impactSpeed * impactSpeed / (2f * g) < safe) f = 0f; // no fall damage under its height
            if (f > 0f) Damage(f * maxHealth);
        }

        /// <summary>Drains the reserve (hazards once the suit's integrity is gone, hard landings). Never from a creature.</summary>
        public void Damage(float amount)
        {
            if (Dead) return;
            health = Mathf.Max(0f, health - amount);
            if (amount > 0f) Damaged?.Invoke(amount);
            if (Dead) Died?.Invoke();
        }

        public void Restore() => health = maxHealth;
    }
}
