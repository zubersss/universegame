using UnityEngine;

namespace Meridian.View2D
{
    /// <summary>
    /// U-094 (Bible §9.5 v4, contract v3.0 §11): the v4 numbers and the 12 fps sheet clock, pure C#. Characters play on
    /// twos at 12 fps; v4 art is 64 px per metre, so a 1080 px screen is 16.875 m tall on the orthographic side camera.
    /// </summary>
    public static class SheetClock
    {
        public const int Fps = 12;
        public const float PixelsPerUnit = 64f;
        /// <summary>The side camera's frame height (m): 1080 / 64.</summary>
        public const float FrameHeight = 1080f / PixelsPerUnit;

        /// <summary>Address of the AnimatorController the importer builds for a v3 sheet (SheetAnimatorBuilder).</summary>
        public static string ControllerAddress(string key) => key + "/animator";

        /// <summary>
        /// The drawing (0-based within the clip) shown `t` seconds after the clip started: whole 1/12 s steps; a looping
        /// clip wraps back to `loopFrom`, a one-off holds its last drawing.
        /// </summary>
        public static int Frame(float t, int length, bool loop, int loopFrom = 0)
        {
            if (length <= 0) return 0;
            int step = Mathf.FloorToInt(Mathf.Max(0f, t) * Fps + 1e-4f);
            if (step < length) return step;
            if (!loop) return length - 1;
            int from = Mathf.Clamp(loopFrom, 0, length - 1);
            return from + (step - length) % (length - from);
        }
    }
}
