using System;
using UnityEngine;

namespace Meridian.Player
{
    /// <summary>Player health (oxygen and Cryo arrive with their systems).</summary>
    public sealed class PlayerVitals : MonoBehaviour
    {
        public float maxHealth = 100f;
        public float health = 100f;

        public bool Dead => health <= 0f;
        public event Action Died;

        public void TakeFallImpact(float impactSpeed)
        {
            float f = FallDamage.Fraction(impactSpeed);
            if (f > 0f) Damage(f * maxHealth);
        }

        public void Damage(float amount)
        {
            if (Dead) return;
            health = Mathf.Max(0f, health - amount);
            if (Dead) Died?.Invoke();
        }

        public void Restore() => health = maxHealth;
    }
}
