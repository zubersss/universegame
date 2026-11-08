namespace Meridian.Planet
{
    /// <summary>
    /// U-130 (Bible §7.8 the sideways winter, D-142): Uranus's season clock. The lit hemisphere is one half of the world's x range and swaps every
    /// SeasonDays of the planet's own days; inside the lit half the sun lines the scene from the left in its morning (the season's first half) and
    /// from the right in its evening, and the dark half is the night. The stage picks B-158's deck set by this light (deck_sun_left / _sun_right /
    /// _night, all one geometry) and the U-128 crossfade turns it; the floes take the dark half's strip. Pure.
    /// </summary>
    public static class UranusSeason
    {
        public const int SeasonDays = 6;
        public const string SunLeft = "sun_left", SunRight = "sun_right", Night = "night", Survey = "survey";
        /// <summary>The four lights a Uranus deck ships (D-142): three seasons plus the survey's banded layer0, all one geometry.</summary>
        public static readonly string[] Lights = { SunLeft, SunRight, Night, Survey };
        /// <summary>Columns past a hemisphere's border the light shown holds (no flicker when the camera stands on the line).</summary>
        public const int BorderHold = 20;

        /// <summary>A season's length in game seconds: SeasonDays of the planet's day (its real minutes at the TimeSystem's rate).</summary>
        public static double SeasonSeconds(float dayLengthRealMinutes) =>
            SeasonDays * (double)dayLengthRealMinutes * 60.0 * Meridian.Core.TimeSystem.GameSecondsPerRealSecond;

        /// <summary>The season's index at game time t (each season the lit half swaps).</summary>
        public static long SeasonIndex(double t, double season) => season > 0 ? (long)System.Math.Floor(t / season) : 0;

        /// <summary>0..1 through the current season.</summary>
        public static double SeasonFraction(double t, double season) => season > 0 ? (t - SeasonIndex(t, season) * season) / season : 0;

        /// <summary>Whether column x lies in the lit half now: x in [0, width/2) in an even season, [width/2, width) in an odd one (the column wraps).</summary>
        public static bool InLitHalf(int x, int width, double t, double season)
        {
            if (width <= 0) return true;
            int wx = ((x % width) + width) % width;
            bool first = wx < width / 2;
            return (SeasonIndex(t, season) & 1) == 0 ? first : !first;
        }

        /// <summary>The light at column x now: the night in the dark half; in the lit half sun_left through the season's first half, sun_right after.</summary>
        public static string LightAt(int x, int width, double t, double season) =>
            !InLitHalf(x, width, t, season) ? Night : SeasonFraction(t, season) < 0.5 ? SunLeft : SunRight;

        /// <summary>The light for a camera at column x given the light shown now: near a hemisphere's border the shown light holds while a column
        /// BorderHold into either side still has it (a season's swap flips both sides at once, so the turn still happens). Pure.</summary>
        public static string LightFor(int x, int width, double t, double season, string current)
        {
            string at = LightAt(x, width, t, season);
            if (string.IsNullOrEmpty(current) || current == at) return at;
            if (LightAt(x - BorderHold, width, t, season) == current || LightAt(x + BorderHold, width, t, season) == current) return current;
            return at;
        }
    }
}
