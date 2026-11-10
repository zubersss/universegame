using System.Collections.Generic;
using Meridian.EditorTools;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// D-190 (1): the ground fills' main tones ("tone_hex" at the top level of terrain/&lt;planet&gt;/ground_fill*.json, BLENDER's db44edd1)
    /// are in the ArtMaterials registry exactly as the jsons on disk say: a fill re-exported with another tone and not registered
    /// (ArtTones.Run, or CheckSetup) fails here, not in a playtest's dust colour.
    /// </summary>
    public class GroundToneTests
    {
        [Test]
        public void EveryGroundFillsToneIsRegisteredAsItsJsonSays()
        {
            var reg = AssetDatabase.LoadAssetAtPath<ArtMaterials>(DiscSetup.RegistryPath);
            Assert.NotNull(reg, "the ArtMaterials registry");
            var onDisk = ArtTones.Scan();
            // 22 fills carry the field: ground_fill and ground_fill_t2..t5 on the four inner planets, Earth's sand, Mars's basalt
            Assert.GreaterOrEqual(onDisk.Count, 22, "the ground fills with a tone_hex");
            var seen = new HashSet<string>();
            foreach (var (key, hex) in onDisk)
            {
                Assert.IsTrue(ColorUtility.TryParseHtmlString(hex, out var want), $"{key}: '{hex}' is a colour");
                var entry = reg.tones.Find(t => t.key == key);
                Assert.NotNull(entry, $"{key}: its tone {hex} is not in the registry (run MERIDIAN/Art/Register ground tones)");
                var c = (Color32)want;
                Assert.IsTrue(entry.color.r == c.r && entry.color.g == c.g && entry.color.b == c.b, $"{key}: the registry holds {(Color)entry.color}, the json says {hex}");
                seen.Add(key);
            }
            foreach (var t in reg.tones) Assert.IsTrue(seen.Contains(t.key), $"{t.key}: registered, but its json carries no tone_hex any more");
            foreach (var planet in new[] { "earth", "mars", "mercury", "venus" })
            {
                Assert.IsTrue(seen.Contains($"terrain/{planet}/ground_fill"), $"{planet}: ground_fill's tone");
                for (int tier = 2; tier <= 5; tier++) Assert.IsTrue(seen.Contains($"terrain/{planet}/ground_fill_t{tier}"), $"{planet}: ground_fill_t{tier}'s tone");
            }
            Assert.IsTrue(seen.Contains("terrain/earth/ground_fill_sand"), "Earth's sand");
            Assert.IsTrue(seen.Contains("terrain/mars/ground_fill_basalt"), "Mars's basalt");
        }
    }
}
