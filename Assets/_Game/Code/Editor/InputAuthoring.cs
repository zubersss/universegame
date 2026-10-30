using System.IO;
using System.Text;
using Meridian.Player;
using UnityEditor;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.EditorTools
{
    /// <summary>
    /// Writes MeridianInput.Build() to Settings/Input/MERIDIAN.inputactions (U-009). Rewrites only when
    /// maps, actions or bindings differ: every Build() makes new random ids, which would churn the file.
    /// </summary>
    public static class InputAuthoring
    {
        public const string AssetPath = "Assets/_Game/Settings/Input/MERIDIAN.inputactions";

        [MenuItem("MERIDIAN/Author Input Actions")]
        public static void Run()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(AssetPath));
            var fresh = MeridianInput.Build();
            try
            {
                if (File.Exists(AssetPath))
                {
                    var existing = InputActionAsset.FromJson(File.ReadAllText(AssetPath));
                    bool same = Signature(existing) == Signature(fresh);
                    Object.DestroyImmediate(existing);
                    if (same) return;
                }
                File.WriteAllText(AssetPath, fresh.ToJson());
            }
            finally { Object.DestroyImmediate(fresh); }
            AssetDatabase.ImportAsset(AssetPath);
            Debug.Log($"[MERIDIAN] InputAuthoring wrote {AssetPath}");
        }

        /// <summary>Everything that matters about the map, without the random ids.</summary>
        static string Signature(InputActionAsset asset)
        {
            var sb = new StringBuilder();
            foreach (var map in asset.actionMaps)
            {
                sb.Append('#').Append(map.name);
                foreach (var a in map.actions) sb.Append('|').Append(a.name).Append(':').Append(a.type).Append(':').Append(a.expectedControlType);
                foreach (var b in map.bindings) sb.Append('&').Append(b.action).Append('>').Append(b.path).Append('/').Append(b.name).Append(b.isComposite).Append(b.isPartOfComposite);
            }
            return sb.ToString();
        }
    }
}
