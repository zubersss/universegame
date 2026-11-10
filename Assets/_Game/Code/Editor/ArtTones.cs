using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// D-190 (1): the ground fills' main tones into the ArtMaterials registry, so the dig's clods and dust take the colour of the fill
    /// drawn at the dug cell, read from BLENDER's jsons ("tone_hex": "#RRGGBB" at the top level of terrain/&lt;planet&gt;/ground_fill*.json,
    /// db44edd1), not from code constants. CheckSetup runs it (or -ExecuteMethod Meridian.EditorTools.ArtTones.Run, or the menu);
    /// GroundToneTests fails when the registry and the jsons differ (a fill re-exported without this step).
    /// </summary>
    public static class ArtTones
    {
        const string ArtRoot = "Assets/_Game/Art/";
        static readonly Regex Field = new Regex("\"tone_hex\"\\s*:\\s*\"(#[0-9A-Fa-f]{6})\"", RegexOptions.Compiled);

        [MenuItem("MERIDIAN/Art/Register ground tones (D-190)")]
        public static void Run() => Register();

        /// <summary>The fills' tones on disk: (key, "#RRGGBB"), ordered by key. Pure (reads the jsons).</summary>
        public static List<(string key, string hex)> Scan()
        {
            var found = new List<(string, string)>();
            string root = ArtRoot + "terrain";
            if (!Directory.Exists(root)) return found;
            foreach (var path in Directory.GetFiles(root, "ground_fill*.json", SearchOption.AllDirectories))
            {
                var m = Field.Match(File.ReadAllText(path));
                if (!m.Success) continue;
                string p = path.Replace('\\', '/');
                found.Add((p.Substring(ArtRoot.Length, p.Length - ArtRoot.Length - ".json".Length), m.Groups[1].Value.ToUpperInvariant()));
            }
            found.Sort((a, b) => string.CompareOrdinal(a.Item1, b.Item1));
            return found;
        }

        public static int Register()
        {
            var reg = AssetDatabase.LoadAssetAtPath<Meridian.Rendering.ArtMaterials>(DiscSetup.RegistryPath);
            if (reg == null) { Debug.LogError("[MERIDIAN] ArtTones: no ArtMaterials registry"); return 0; }
            int changed = 0;
            var seen = new HashSet<string>();
            var found = Scan();
            foreach (var (key, hex) in found)
            {
                if (!ColorUtility.TryParseHtmlString(hex, out var c)) continue;
                seen.Add(key);
                if (reg.SetTone(key, (Color32)c)) changed++;
            }
            // tones whose json field is gone
            for (int i = reg.tones.Count - 1; i >= 0; i--)
                if (!seen.Contains(reg.tones[i].key)) { reg.SetTone(reg.tones[i].key, null); changed++; }
            if (changed > 0) { EditorUtility.SetDirty(reg); AssetDatabase.SaveAssets(); }
            Debug.Log($"[MERIDIAN] ArtTones: {found.Count} ground fill tones, {changed} changed");
            return changed;
        }
    }
}
