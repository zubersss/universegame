using UnityEngine;

namespace Meridian.Audio
{
    /// <summary>
    /// U-150 (D-158 (4)): placeholder sounds synthesized at run time, original and CC0-dedicated like AudioSynth's (U-016). The sonic boom:
    /// the double crack of an N-wave (two noise bursts 0.11 s apart) over a 45 Hz thump and a low rumble that dies away over ~1.2 s.
    /// Deterministic (fixed seed). Built once, the first time it is needed; a wired clip (AudioDirector.boom) replaces it.
    /// </summary>
    public static class SfxSynth
    {
        public const int Rate = 44100;
        public const float BoomSeconds = 1.4f;

        /// <summary>The boom's samples, mono at `rate`, in [−1, 1].</summary>
        public static float[] Boom(int rate = Rate)
        {
            var s = new float[Mathf.CeilToInt(BoomSeconds * rate)];
            var rng = new System.Random(158);
            double lp = 0, lp2 = 0;
            for (int i = 0; i < s.Length; i++)
            {
                float t = i / (float)rate;
                float noise = (float)rng.NextDouble() * 2f - 1f;
                float crack = Mathf.Exp(-t * 45f);
                float t2 = t - 0.11f;
                if (t2 >= 0f) crack += 0.8f * Mathf.Exp(-t2 * 45f);
                lp += (noise - lp) * 0.02;
                lp2 += (lp - lp2) * 0.05;
                float rumble = (float)lp2 * 7f * Mathf.Exp(-t * 2.2f);
                float thump = 0.55f * Mathf.Sin(2f * Mathf.PI * 45f * t) * Mathf.Exp(-t * 6f);
                s[i] = Mathf.Clamp(0.7f * noise * crack + rumble + thump, -1f, 1f) * 0.9f;
            }
            return s;
        }

        /// <summary>The boom as a clip (allocates once per call: callers keep it).</summary>
        public static AudioClip BoomClip()
        {
            var data = Boom(Rate);
            var clip = AudioClip.Create("boom_placeholder", data.Length, 1, Rate, false);
            clip.SetData(data, 0);
            return clip;
        }
    }
}
