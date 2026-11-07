using UnityEngine;

namespace Meridian.Space
{
    /// <summary>
    /// U-103 (D-098, B-119 `planets/saturn/disc_rig.json`): Saturn's ring sprites breathe on the beat: a vertical scale of
    /// 1 ± scale_y and a roll of ± rotate_deg on a sine at beat_bpm, held at stepped_hz (12 Hz: the cartoon clock), so the
    /// rings move like drawings, not a tween. Pure; the disc rig json parses into Wobble.
    /// </summary>
    public static class RingWobble
    {
        [System.Serializable]
        public sealed class Wobble
        {
            public string[] parts;
            public float scale_y = 0.04f, rotate_deg = 1.5f, beat_bpm = 110f;
            public int stepped_hz = 12;
        }

        [System.Serializable]
        public sealed class DiscRig
        {
            public string key, style;
            public float space_ppu;
            public Wobble wobble;
        }

        public static DiscRig Parse(string json) => string.IsNullOrEmpty(json) ? null : JsonUtility.FromJson<DiscRig>(json);

        /// <summary>The ring pose at `seconds`: (scale y, rotation degrees), stepped to the wobble's clock.</summary>
        public static (float scaleY, float rotateDeg) At(float seconds, Wobble w)
        {
            if (w == null) return (1f, 0f);
            float hz = Mathf.Max(1, w.stepped_hz);
            float t = Mathf.Floor(seconds * hz) / hz;
            float phase = t * w.beat_bpm / 60f * 2f * Mathf.PI;
            float s = Mathf.Sin(phase);
            return (1f + w.scale_y * s, w.rotate_deg * s);
        }

        /// <summary>True when `part` is one of the wobbling parts.</summary>
        public static bool Wobbles(Wobble w, string part)
        {
            if (w?.parts == null) return false;
            foreach (var p in w.parts) if (p == part) return true;
            return false;
        }
    }
}
