using Meridian.Player;
using UnityEngine;

namespace Meridian.Planet.Weather
{
    /// <summary>
    /// Venus super-rotation (Bible §7.4, U-050): a constant lateral push that swells and fades over an 80-minute
    /// real cycle (never reversing: the upper atmosphere always streams one way), strongest on the cloud deck and
    /// nothing at the surface. Driven by the saved game clock, so it survives save/load.
    /// </summary>
    public sealed class VenusWind : MonoBehaviour
    {
        public const float CycleRealSeconds = 80f * 60f;
        /// <summary>Air speed at the deck: the floor of the cycle, and the swell on top of it (m/s, +x).</summary>
        public const float BaseSpeed = 2.5f, SwellSpeed = 1.5f;
        /// <summary>Below FullAt the wind falls off; below CalmBelow (the thick lower atmosphere) it is gone.</summary>
        public const float CalmBelow = 520f, FullAt = 720f;

        public PlayerController player;
        Meridian.Core.TimeSystem clock;

        /// <summary>The wind's air speed at height y and real time t (s).</summary>
        public static float SpeedAt(float y, double realSeconds)
        {
            float altitude = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(CalmBelow, FullAt, y));
            float swell = 0.5f - 0.5f * Mathf.Cos((float)(realSeconds / CycleRealSeconds * 2.0 * System.Math.PI));
            return altitude * (BaseSpeed + SwellSpeed * swell);
        }

        public float Current { get; private set; }

        void OnDisable()
        {
            if (player != null) player.windX = 0f;
            Current = 0f;
        }

        void FixedUpdate()
        {
            if (player == null) return;
            if (clock == null) clock = FindAnyObjectByType<Meridian.Core.TimeSystem>();
            double t = clock != null ? clock.GameSeconds / Meridian.Core.TimeSystem.GameSecondsPerRealSecond : 0;
            Current = SpeedAt(player.Body.position.y, t);
            player.windX = Current;
        }
    }
}
