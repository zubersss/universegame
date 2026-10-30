using System.IO;
using System.Linq;
using Meridian.EditorTools;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-016 (EditMode): the placeholder set exists, imports as Vorbis, fits 10 MB, and is credited.</summary>
    public class AudioTests
    {
        static string[] All => AudioSynth.Sfx.Concat(new[] { AudioSynth.Ambient }).ToArray();

        [Test]
        public void EveryRequiredClipExists()
        {
            foreach (var name in All)
                Assert.NotNull(AssetDatabase.LoadAssetAtPath<AudioClip>(AudioSynth.PathOf(name)), name);
        }

        [Test]
        public void ClipsImportAsVorbisWithTheRightLoadType()
        {
            foreach (var name in All)
            {
                var ai = (AudioImporter)AssetImporter.GetAtPath(AudioSynth.PathOf(name));
                var s = ai.defaultSampleSettings;
                Assert.AreEqual(AudioCompressionFormat.Vorbis, s.compressionFormat, name);
                var expected = name == AudioSynth.Ambient ? AudioClipLoadType.Streaming : AudioClipLoadType.CompressedInMemory;
                Assert.AreEqual(expected, s.loadType, name);
            }
        }

        [Test]
        public void AudioFolderIsUnderTenMegabytes()
        {
            long bytes = Directory.GetFiles(AudioSynth.Folder, "*.*", SearchOption.AllDirectories)
                .Where(f => !f.EndsWith(".meta")).Sum(f => new FileInfo(f).Length);
            TestContext.Out.WriteLine($"[MERIDIAN] audio source files: {bytes / 1024} KB");
            Assert.LessOrEqual(bytes, 10L * 1024 * 1024);
        }

        [Test]
        public void EveryAudioFileIsCreditedWithALicense()
        {
            var credits = File.ReadAllText("docs/credits/unity.md");
            foreach (var f in Directory.GetFiles(AudioSynth.Folder, "*.wav", SearchOption.AllDirectories))
            {
                var path = f.Replace('\\', '/');
                var line = credits.Split('\n').FirstOrDefault(l => l.Contains(path));
                Assert.NotNull(line, $"{path} missing from docs/credits/unity.md");
                StringAssert.Contains("CC0", line, $"{path} license");
            }
        }

        [Test]
        public void LoopsAreSeamless()
        {
            // Compressed clips can't be read back, so check the 16-bit PCM source: last sample → first.
            foreach (var name in new[] { "thrust", AudioSynth.Ambient })
            {
                var bytes = File.ReadAllBytes(AudioSynth.PathOf(name));
                const int header = 44;
                float first = System.BitConverter.ToInt16(bytes, header) / 32768f;
                float last = System.BitConverter.ToInt16(bytes, bytes.Length - 2) / 32768f;
                Assert.Less(Mathf.Abs(last - first), 0.1f, $"{name}: no click at the loop point");
            }
        }
    }
}
