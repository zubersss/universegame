using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// Synthesizes the M1 placeholder sounds (U-016) as original, CC0-dedicated WAVs: jump, land,
    /// dig, place, thrust (loop), UI click, and an ambient wind loop. Deterministic: same seed, same
    /// bytes. Unity imports them as Vorbis (AudioImportRules).
    /// </summary>
    public static class AudioSynth
    {
        public const string Folder = "Assets/_Game/Audio";
        public const int Rate = 44100;

        public static readonly string[] Sfx = { "jump", "land", "dig", "place", "thrust", "ui_click" };
        public const string Ambient = "ambient_wind";

        [MenuItem("MERIDIAN/Synthesize Placeholder Audio")]
        public static void Run()
        {
            Directory.CreateDirectory(Folder + "/sfx");
            Directory.CreateDirectory(Folder + "/ambient");
            Write("sfx/jump", Jump());
            Write("sfx/land", Land());
            Write("sfx/dig", Dig());
            Write("sfx/place", Place());
            Write("sfx/thrust", Thrust());
            Write("sfx/ui_click", Click());
            Write("ambient/" + Ambient, Wind());
            AssetDatabase.Refresh();
            Debug.Log("[MERIDIAN] AudioSynth wrote 7 placeholder clips.");
        }

        public static string PathOf(string name) =>
            name == Ambient ? $"{Folder}/ambient/{name}.wav" : $"{Folder}/sfx/{name}.wav";

        // ---------- sounds ----------

        static float[] Buffer(float seconds) => new float[Mathf.CeilToInt(seconds * Rate)];

        static float[] Jump()
        {
            var s = Buffer(0.22f);
            var rng = new System.Random(1);
            double phase = 0;
            for (int i = 0; i < s.Length; i++)
            {
                float t = i / (float)s.Length;
                phase += 2 * Math.PI * (180 + 420 * t) / Rate; // rising chirp
                float noise = (float)rng.NextDouble() * 2f - 1f;
                s[i] = (0.35f * (float)Math.Sin(phase) + 0.25f * noise * (1f - t)) * Env(t, 0.03f, 0.6f);
            }
            return LowPass(s, 0.25f);
        }

        static float[] Land()
        {
            var s = Buffer(0.3f);
            var rng = new System.Random(2);
            double phase = 0;
            for (int i = 0; i < s.Length; i++)
            {
                float t = i / (float)s.Length;
                phase += 2 * Math.PI * (90 - 40 * t) / Rate; // low thump
                float noise = (float)rng.NextDouble() * 2f - 1f;
                s[i] = (0.7f * (float)Math.Sin(phase) + 0.35f * noise) * Env(t, 0.005f, 0.15f);
            }
            return LowPass(s, 0.08f);
        }

        static float[] Dig()
        {
            var s = Buffer(0.35f);
            var rng = new System.Random(3);
            for (int i = 0; i < s.Length; i++)
            {
                float t = i / (float)s.Length;
                float noise = (float)rng.NextDouble() * 2f - 1f;
                float grit = (i / 220) % 3 == 0 ? 1f : 0.45f; // crunchy grains
                s[i] = noise * grit * 0.6f * Env(t, 0.01f, 0.35f);
            }
            return LowPass(s, 0.35f);
        }

        static float[] Place()
        {
            var s = Buffer(0.18f);
            var rng = new System.Random(4);
            double phase = 0;
            for (int i = 0; i < s.Length; i++)
            {
                float t = i / (float)s.Length;
                phase += 2 * Math.PI * 140 / Rate;
                float noise = (float)rng.NextDouble() * 2f - 1f;
                float click = i < 300 ? noise * 0.8f : 0f;
                s[i] = (0.6f * (float)Math.Sin(phase) * Env(t, 0.002f, 0.25f)) + click;
            }
            return LowPass(s, 0.3f);
        }

        /// <summary>Engine rumble, 2 s, loops seamlessly (ends where it starts).</summary>
        static float[] Thrust()
        {
            var s = Buffer(2f);
            var rng = new System.Random(5);
            for (int i = 0; i < s.Length; i++) s[i] = ((float)rng.NextDouble() * 2f - 1f) * 0.5f;
            s = LowPass(s, 0.05f);
            for (int i = 0; i < s.Length; i++)
            {
                float t = i / (float)Rate;
                s[i] *= 1.6f * (0.85f + 0.15f * Mathf.Sin(2f * Mathf.PI * 7f * t)); // 7 Hz throb, whole cycles in 2 s
            }
            return LoopCrossfade(s, 0.15f);
        }

        static float[] Click()
        {
            var s = Buffer(0.05f);
            double phase = 0;
            for (int i = 0; i < s.Length; i++)
            {
                float t = i / (float)s.Length;
                phase += 2 * Math.PI * 2200 / Rate;
                s[i] = 0.35f * (float)Math.Sin(phase) * Env(t, 0.01f, 0.2f);
            }
            return s;
        }

        /// <summary>Soft wind, 20 s, seamless loop.</summary>
        static float[] Wind()
        {
            var s = Buffer(20f);
            var rng = new System.Random(6);
            for (int i = 0; i < s.Length; i++) s[i] = (float)rng.NextDouble() * 2f - 1f;
            s = LowPass(s, 0.02f);
            s = LowPass(s, 0.03f);
            for (int i = 0; i < s.Length; i++)
            {
                float t = i / (float)Rate;
                float gust = 0.55f + 0.3f * Mathf.Sin(2f * Mathf.PI * t / 10f) + 0.15f * Mathf.Sin(2f * Mathf.PI * t / 4f);
                s[i] *= 2.2f * gust;
            }
            return LoopCrossfade(s, 1.5f);
        }

        // ---------- helpers ----------

        /// <summary>Attack/decay envelope over t in 0..1.</summary>
        static float Env(float t, float attack, float decayShape)
        {
            float a = attack > 0f ? Mathf.Clamp01(t / attack) : 1f;
            float d = Mathf.Pow(1f - t, 1f / Mathf.Max(decayShape, 0.01f) * 0.5f);
            return a * d;
        }

        static float[] LowPass(float[] s, float alpha)
        {
            var o = new float[s.Length];
            float y = 0f;
            for (int i = 0; i < s.Length; i++) { y += alpha * (s[i] - y); o[i] = y; }
            return o;
        }

        /// <summary>Blends the tail into the head so the clip loops without a click.</summary>
        static float[] LoopCrossfade(float[] s, float seconds)
        {
            int n = Mathf.Min(Mathf.CeilToInt(seconds * Rate), s.Length / 2);
            int len = s.Length - n;
            var o = new float[len];
            Array.Copy(s, o, len);
            for (int i = 0; i < n; i++)
            {
                float w = i / (float)n;
                o[i] = s[i] * w + s[len + i] * (1f - w);
            }
            return o;
        }

        static void Write(string name, float[] samples)
        {
            var path = $"{Folder}/{name}.wav";
            float peak = 1e-6f;
            foreach (var x in samples) peak = Mathf.Max(peak, Mathf.Abs(x));
            float gain = 0.89f / peak; // normalize to -1 dBFS
            using (var w = new BinaryWriter(File.Create(path)))
            {
                int bytes = samples.Length * 2;
                w.Write(new[] { 'R', 'I', 'F', 'F' }); w.Write(36 + bytes);
                w.Write(new[] { 'W', 'A', 'V', 'E' }); w.Write(new[] { 'f', 'm', 't', ' ' });
                w.Write(16); w.Write((short)1); w.Write((short)1); w.Write(Rate); w.Write(Rate * 2);
                w.Write((short)2); w.Write((short)16);
                w.Write(new[] { 'd', 'a', 't', 'a' }); w.Write(bytes);
                foreach (var x in samples) w.Write((short)Mathf.Clamp(Mathf.RoundToInt(x * gain * 32767f), -32768, 32767));
            }
        }
    }

    /// <summary>Import rules for Assets/_Game/Audio (Bible §11.1): Vorbis; SFX compressed in memory, loops streamed.</summary>
    public sealed class AudioImportRules : AssetPostprocessor
    {
        void OnPreprocessAudio()
        {
            if (!assetPath.StartsWith(AudioSynth.Folder + "/", StringComparison.Ordinal)) return;
            var ai = (AudioImporter)assetImporter;
            bool ambient = assetPath.Contains("/ambient/");
            ai.forceToMono = true;
            ai.loadInBackground = ambient;
            var s = ai.defaultSampleSettings;
            s.compressionFormat = AudioCompressionFormat.Vorbis;
            s.quality = ambient ? 0.4f : 0.6f;
            s.loadType = ambient ? AudioClipLoadType.Streaming : AudioClipLoadType.CompressedInMemory;
            s.preloadAudioData = !ambient;
            ai.defaultSampleSettings = s;
        }
    }
}
