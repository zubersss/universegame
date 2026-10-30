using Meridian.Core;

namespace Meridian.Planet.Weather
{
    public enum StormPhase { Clear, Warning, Storm }

    /// <summary>
    /// Mars dust storms (U-026, Bible §7.2): planet-wide, one every 4–7 Mars days, lasting 2–6 real
    /// minutes, announced 60 real seconds ahead. Derived from the world seed and the game clock only,
    /// so a save needs nothing extra and every session sees the same weather. Times are game seconds.
    /// </summary>
    public static class DustStormSchedule
    {
        public const float WarningRealSeconds = 60f;
        public const float MinGapDays = 4f, MaxGapDays = 7f;
        public const float MinDurationRealSeconds = 120f, MaxDurationRealSeconds = 360f;

        public const double WarningGameSeconds = WarningRealSeconds * TimeSystem.GameSecondsPerRealSecond;

        public readonly struct Storm
        {
            public readonly int index;
            public readonly double after, start, end;
            public Storm(int index, double after, double start, double end) { this.index = index; this.after = after; this.start = start; this.end = end; }
            public double WarningStart => start - WarningGameSeconds;
            public double Duration => end - start;
        }

        /// <summary>Storm k: its gap after the previous storm's end (storm 0: after the clock's start) and its length.</summary>
        public static Storm Get(int seed, int index, double dayGameSeconds)
        {
            double t = 0;
            Storm s = default;
            for (int k = 0; k <= index; k++) { s = Next(seed, k, t, dayGameSeconds); t = s.end; }
            return s;
        }

        static Storm Next(int seed, int k, double after, double dayGameSeconds)
        {
            double gap = Lerp(MinGapDays, MaxGapDays, Hash01(seed, k, 0)) * dayGameSeconds;
            double length = Lerp(MinDurationRealSeconds, MaxDurationRealSeconds, Hash01(seed, k, 1)) * TimeSystem.GameSecondsPerRealSecond;
            double start = after + gap;
            return new Storm(k, after, start, start + length);
        }

        /// <summary>
        /// The storm that is current or next at `now`: the first whose end is after `now`. `cursor` is a
        /// cache (pass the same storm back each frame) so a frame costs O(1); a default cursor starts over.
        /// </summary>
        public static Storm Current(int seed, double now, double dayGameSeconds, Storm cursor)
        {
            // Reuse the cursor unless the clock is before its gap (a load of an older save).
            Storm s = cursor.end > 0 && cursor.after <= now ? cursor : Get(seed, 0, dayGameSeconds);
            while (s.end <= now) s = Next(seed, s.index + 1, s.end, dayGameSeconds);
            return s;
        }

        public static StormPhase PhaseAt(Storm s, double now) =>
            now >= s.start && now < s.end ? StormPhase.Storm :
            now >= s.WarningStart && now < s.start ? StormPhase.Warning : StormPhase.Clear;

        static double Lerp(double a, double b, double k) => a + (b - a) * k;

        /// <summary>Stable 0..1 hash (no System.Random: no allocation, same on every platform).</summary>
        public static double Hash01(int seed, int k, int salt)
        {
            unchecked
            {
                uint h = (uint)seed * 0x9E3779B1u ^ (uint)k * 0x85EBCA77u ^ (uint)salt * 0xC2B2AE3Du;
                h ^= h >> 16; h *= 0x7FEB352Du; h ^= h >> 15; h *= 0x846CA68Bu; h ^= h >> 16;
                return (h & 0xFFFFFF) / (double)0x1000000;
            }
        }
    }
}
