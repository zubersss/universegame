using Meridian.Audio;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-195 (D-183): the two synthesized stand-ins the stroke's feel plays until D-186's recorded samples (U-198): the clods' fall after a
    /// shovel scoop (quiet while they fly, thuds from 0.16 s) and the pack's tick. Deterministic, inside [−1, 1], their stated lengths.
    /// </summary>
    public class DigFeelSoundTests
    {
        static float Peak(float[] s, int from, int to)
        {
            float peak = 0f;
            for (int i = from; i < to && i < s.Length; i++) peak = Mathf.Max(peak, Mathf.Abs(s[i]));
            return peak;
        }

        [Test]
        public void TheClodFallIsQuietWhileTheClodsFlyThenThuds()
        {
            var s = SfxSynth.ClodFall();
            Assert.AreEqual(Mathf.CeilToInt(SfxSynth.ClodFallSeconds * SfxSynth.Rate), s.Length, "0.5 s at 44.1 kHz");
            Assert.AreEqual(0f, Peak(s, 0, (int)(0.15f * SfxSynth.Rate)), 1e-6f, "silent for the clods' flight");
            Assert.Greater(Peak(s, (int)(0.16f * SfxSynth.Rate), (int)(0.22f * SfxSynth.Rate)), 0.2f, "the first thud lands at 0.16 s");
            Assert.LessOrEqual(Peak(s, 0, s.Length), 0.8f + 1e-4f, "inside [-1, 1] with headroom");
            Assert.Less(Peak(s, s.Length - 441, s.Length), 0.05f, "it has died away by the end (no click)");
            CollectionAssert.AreEqual(s, SfxSynth.ClodFall(), "deterministic");
        }

        [Test]
        public void ThePackTickIsShortAndBright()
        {
            var s = SfxSynth.PackTick();
            Assert.AreEqual(Mathf.CeilToInt(SfxSynth.PackTickSeconds * SfxSynth.Rate), s.Length, "70 ms");
            Assert.That(Peak(s, 0, s.Length), Is.InRange(0.3f, 0.6f + 1e-4f), "audible, with headroom");
            Assert.AreEqual(0f, s[0], 1e-6f, "starts at zero (no click)");
            Assert.Less(Peak(s, s.Length - 220, s.Length), 0.02f, "gone by the end");
            int crossings = 0;
            for (int i = 1; i < 441; i++) if (s[i - 1] <= 0f != s[i] <= 0f) crossings++;
            Assert.That(crossings, Is.InRange(30, 46), "about 1.9 kHz over the first 10 ms (38 zero crossings)");
            CollectionAssert.AreEqual(s, SfxSynth.PackTick(), "deterministic");
        }

        [Test]
        public void TheNewSoundsKeepTheOlderEnumValues()
        {
            Assert.AreEqual(6, (int)Sfx.Shovel, "U-193's value stays");
            Assert.AreEqual(7, (int)Sfx.ClodFall);
            Assert.AreEqual(8, (int)Sfx.PackTick);
        }
    }
}
