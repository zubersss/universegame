using System;
using System.Collections.Generic;
using System.IO;
using Meridian.Rendering;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-075 (contract v2.1 §9.1, D-063/D-065): ArtImporter's model side. A .glb under Art/ imports with glTFast in
    /// Mecanim mode; for each model key ArtImporter writes a URP/Lit material from the four maps beside it (or from the
    /// folder's shared atlas_* maps, B-085) to Generated/Models/&lt;key&gt;.mat, addresses the .glb (GameObject) and that
    /// material under the key (Addressables picks by type, so the key's 2D placeholder sprite stays loadable too), and
    /// records the clips of &lt;key&gt;.json (name, frames, loop at fps) in ArtMaterials.modelClipSets.
    /// </summary>
    public sealed partial class ArtImporter
    {
        public const string GeneratedModels = "Assets/_Game/Generated/Models/";
        const int MecanimIndex = 2; // GLTFast.AnimationMethod: None, Legacy, Mecanim, Playables

        void OnPreprocessAsset()
        {
            if (!assetPath.EndsWith(".glb", StringComparison.OrdinalIgnoreCase)) return;
            if (Classify(assetPath, out _) != RootKind.Art) return;
            var so = new SerializedObject(assetImporter);
            var method = so.FindProperty("importSettings.animationMethod");
            if (method != null && method.intValue != MecanimIndex)
            {
                method.intValue = MecanimIndex; // clips as Mecanim clips for the Animator/Playables model views
                so.ApplyModifiedPropertiesWithoutUndo();
            }
        }

        [Serializable] sealed class ModelManifest { public int fps = 30; public ModelClipJson[] clips; public bool alpha_clip; } // alpha_clip: contract v2.6 ruling 10 (D-082)
        [Serializable] sealed class ModelClipJson { public string name; public int frames; public bool loop; }

        /// <summary>Model keys touched by this import batch: a .glb, its json, or one of its maps (incl. a shared atlas).</summary>
        static void CollectModelKeys(IEnumerable<string> paths, HashSet<string> keys)
        {
            foreach (var raw in paths)
            {
                if (Classify(raw, out var rel) != RootKind.Art) continue;
                if (rel.EndsWith(".glb", StringComparison.Ordinal)) { keys.Add(rel.Substring(0, rel.Length - 4)); continue; }
                if (rel.EndsWith(".json", StringComparison.Ordinal))
                {
                    var k = rel.Substring(0, rel.Length - 5);
                    if (File.Exists(Active.art + k + ".glb")) keys.Add(k);
                    continue;
                }
                if (!ArtRules.TryParse(rel, out var key, out _) || !IsModelKey(key)) continue;
                if (File.Exists(Active.art + key + ".glb")) keys.Add(key);
                else
                {
                    // A shared atlas changed: every model in its folder uses it.
                    int slash = key.LastIndexOf('/');
                    var dir = Active.art + key.Substring(0, slash);
                    foreach (var glb in Directory.GetFiles(dir, "*.glb"))
                        keys.Add(key.Substring(0, slash) + "/" + Path.GetFileNameWithoutExtension(glb));
                }
            }
        }

        static void GenerateModels(HashSet<string> keys)
        {
            if (keys.Count == 0) return;
            var reg = Registry();
            bool regDirty = false;
            foreach (var key in keys)
            {
                var glb = Active.art + key + ".glb";
                if (!File.Exists(glb)) continue;
                var model = AssetDatabase.LoadMainAssetAtPath(glb) as GameObject;
                if (model == null) continue; // glTF importer missing or the import failed

                // Material from the maps beside the model, or the folder's shared atlas.
                string basePath = Active.art + key, atlasBase = Active.art + key.Substring(0, key.LastIndexOf('/')) + "/atlas";
                // The sidecar first: its alpha_clip flag (D-082) shapes the material below; its clips go to the registry.
                var json = basePath + ".json";
                ModelManifest manifest = null;
                if (File.Exists(json)) manifest = JsonUtility.FromJson<ModelManifest>(File.ReadAllText(json));

                string maps = File.Exists(basePath + "_color.png") ? basePath : File.Exists(atlasBase + "_color.png") ? atlasBase : null;
                Material mat = null;
                if (maps != null)
                {
                    Texture2D Map(string m) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{maps}_{m}.png");
                    var built = ModelMaterials.FromMaps(Map("color"), Map("normal"), Map("mask"), Map("emission"), key.Replace('/', '_'));
                    if (manifest != null && manifest.alpha_clip) ModelMaterials.SetAlphaClip(built); // D-082: cut-out leaves, double-sided
                    var matPath = GeneratedModels + key + ".mat";
                    Directory.CreateDirectory(Path.GetDirectoryName(matPath));
                    mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
                    if (mat == null) { AssetDatabase.CreateAsset(built, matPath); mat = built; }
                    else { EditorUtility.CopySerialized(built, mat); UnityEngine.Object.DestroyImmediate(built); EditorUtility.SetDirty(mat); }
                }

                // Address the model and its material under the key (the 2D placeholder keeps the same address; types differ).
                Address(glb, key);
                if (mat != null) Address(AssetDatabase.GetAssetPath(mat), key);

                // Clips from the json (glTF has no loop flag).
                var clips = new List<ArtClip>();
                int fps = 30;
                if (manifest != null)
                {
                    fps = manifest.fps > 0 ? manifest.fps : 30;
                    if (manifest.clips != null) foreach (var c in manifest.clips) if (!string.IsNullOrEmpty(c.name)) clips.Add(new ArtClip { name = c.name, start = 0, length = c.frames, loop = c.loop });
                }
                regDirty |= reg.SetModelClips(key, fps, clips);
            }
            if (regDirty) { EditorUtility.SetDirty(reg); AssetDatabase.SaveAssetIfDirty(reg); }
            AssetDatabase.SaveAssets();
        }

        /// <summary>Addresses one asset under `key` in the key's group, without atlas handling.</summary>
        static void Address(string path, string key)
        {
            var guid = AssetDatabase.AssetPathToGUID(path);
            if (string.IsNullOrEmpty(guid)) return;
            var entry = Settings.CreateOrMoveEntry(guid, GroupNamed(ArtRules.GroupFor(key)), false, true);
            if (entry.address != key) entry.SetAddress(key, true);
        }
    }
}
