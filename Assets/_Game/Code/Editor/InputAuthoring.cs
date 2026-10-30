using System.IO;
using Meridian.Player;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>Writes MeridianInput.Build() to Settings/Input/MERIDIAN.inputactions (U-009).</summary>
    public static class InputAuthoring
    {
        public const string AssetPath = "Assets/_Game/Settings/Input/MERIDIAN.inputactions";

        [MenuItem("MERIDIAN/Author Input Actions")]
        public static void Run()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(AssetPath));
            var asset = MeridianInput.Build();
            File.WriteAllText(AssetPath, asset.ToJson());
            Object.DestroyImmediate(asset);
            AssetDatabase.ImportAsset(AssetPath);
            Debug.Log($"[MERIDIAN] InputAuthoring wrote {AssetPath}");
        }
    }
}
