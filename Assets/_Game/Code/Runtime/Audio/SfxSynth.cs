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

        public const float ShovelSeconds = 0.28f;

        /// <summary>U-193 (D-182): the shovel's scoop: the blade's scrape into soil (a short band of low-passed noise, rising then cut) and the
        /// clod coming loose (a soft 90 Hz thud and a crumble of grit after it). Deterministic, mono at `rate`, in [−1, 1].</summary>
        public static float[] Shovel(int rate = Rate)
        {
            var s = new float[Mathf.CeilToInt(ShovelSeconds * rate)];
            var rng = new System.Random(193);
            double lp = 0, hp = 0, prev = 0;
            for (int i = 0; i < s.Length; i++)
            {
                float t = i / (float)rate;
                float noise = (float)rng.NextDouble() * 2f - 1f;
                lp += (noise - lp) * 0.18;                                    // the scrape: soil, not metal (no bright top)
                float scrape = (float)lp * Mathf.Clamp01(t / 0.05f) * Mathf.Exp(-Mathf.Max(0f, t - 0.07f) * 38f);
                float tc = t - 0.08f;                                         // the clod comes loose
                float thud = tc >= 0f ? 0.6f * Mathf.Sin(2f * Mathf.PI * 90f * tc) * Mathf.Exp(-tc * 28f) : 0f;
                hp = 0.7 * (hp + noise - prev); prev = noise;                 // the grit: sparse high clicks after the thud
                float grit = tc >= 0.02f && rng.NextDouble() < 0.05 ? (float)hp * 0.5f * Mathf.Exp(-(tc - 0.02f) * 16f) : 0f;
                s[i] = Mathf.Clamp(1.6f * scrape + thud + grit, -1f, 1f) * 0.8f;
            }
            return s;
        }

        /// <summary>The shovel's scoop as a clip (allocates once per call: callers keep it).</summary>
        public static AudioClip ShovelClip()
        {
            var data = Shovel(Rate);
            var clip = AudioClip.Create("shovel_placeholder", data.Length, 1, Rate, false);
            clip.SetData(data, 0);
            return clip;
        }
    }
}
