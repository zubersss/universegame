using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>
    /// Mercury solar flares (Bible §7.3, D-048): a 45 s warning, then 20 s of Radiation 4 in the open.
    /// Flares come every 8–12 real minutes (seeded; the Bible leaves the rate open). Only runs on Mercury
    /// (HazardSystem enables it per planet). Real time, so pausing the game clock doesn't skip one.
    /// </summary>
    public sealed class SolarFlares : MonoBehaviour
    {
        public const float WarningSeconds = 45f, ActiveSeconds = 20f;
        public const float MinGap = 480f, MaxGap = 720f;

        public enum Phase { Quiet, Warning, Active }

        public Phase Current { get; private set; }
        /// <summary>Seconds until the flare starts (Warning) or ends (Active).</summary>
        public float SecondsLeft { get; private set; }
        public bool Running { get; private set; }
        /// <summary>Time.time the last flare ended (U-059: Solarite is harvestable for 90 s after). -inf before the first.</summary>
        public float LastEnded { get; private set; } = float.NegativeInfinity;
        public float SinceLastFlare => Time.time - LastEnded;

        /// <summary>Tests and scripted scenes: a flare ended at `time` (Time.time).</summary>
        public void EndedAt(float time) => LastEnded = time;

        float nextStart = float.MaxValue, end;
        System.Random rng = new System.Random(1969);

        /// <summary>Starts the cycle for a planet that has flares; stops it otherwise.</summary>
        public void Run(bool on, int seed)
        {
            Running = on;
            Current = Phase.Quiet;
            rng = new System.Random(seed);
            nextStart = on ? Time.time + Gap() : float.MaxValue;
        }

        float Gap() => MinGap + (float)rng.NextDouble() * (MaxGap - MinGap);

        /// <summary>Seconds until the next flare starts (negative while one is under way); saved with the game (U-048).</summary>
        public float NextIn => Current == Phase.Active ? -(end - Time.time) : nextStart - Time.time;

        /// <summary>Load: restore the schedule (a flare under way resumes with its remaining time).</summary>
        public void Restore(float nextIn)
        {
            if (!Running) return;
            if (nextIn < 0f) { Current = Phase.Active; end = Time.time - nextIn; nextStart = end - ActiveSeconds; }
            else { Current = Phase.Quiet; nextStart = Time.time + nextIn; }
            Step();
        }

        /// <summary>Schedules a flare to start in `leadSeconds` (≥ 0; tests and scripted events).</summary>
        public void Force(float leadSeconds)
        {
            Running = true;
            nextStart = Time.time + Mathf.Max(0f, leadSeconds);
            Step();
        }

        void Update() { if (Running) Step(); }

        void Step()
        {
            float now = Time.time;
            if (Current == Phase.Active)
            {
                SecondsLeft = end - now;
                if (now < end) return;
                Current = Phase.Quiet;
                LastEnded = end;
                nextStart = now + Gap();
            }
            if (now >= nextStart)
            {
                Current = Phase.Active;
                end = nextStart + ActiveSeconds;
                SecondsLeft = end - now;
                return;
            }
            float lead = nextStart - now;
            Current = lead <= WarningSeconds ? Phase.Warning : Phase.Quiet;
            SecondsLeft = lead;
        }
    }
}
