using Meridian.Planets;
using UnityEngine;

namespace Meridian.Core
{
    /// <summary>Game clock: 1 real second = 72 game seconds (Bible §3).</summary>
    public sealed class TimeSystem : MonoBehaviour
    {
        public const float GameSecondsPerRealSecond = 72f;

        [SerializeField] double gameSeconds;
        public bool paused;

        public double GameSeconds => gameSeconds;

        public void SetGameSeconds(double value) => gameSeconds = value;

        void Update()
        {
            if (!paused) Advance(Time.deltaTime);
        }

        public void Advance(float realSeconds) => gameSeconds += realSeconds * GameSecondsPerRealSecond;

        /// <summary>0..1 position in the planet's day; 0 when the planet has a special rule (Mercury).</summary>
        public float DayFraction(PlanetConfig planet)
        {
            if (planet == null || planet.dayLengthRealMinutes <= 0f) return 0f;
            double dayGameSeconds = planet.dayLengthRealMinutes * 60.0 * GameSecondsPerRealSecond;
            return (float)(gameSeconds % dayGameSeconds / dayGameSeconds);
        }
    }
}
