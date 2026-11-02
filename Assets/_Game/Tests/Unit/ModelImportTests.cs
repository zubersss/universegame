#if UNITY_EDITOR
using System.IO;
using System.Linq;
using Meridian.Art;
using Meridian.EditorTools;
using Meridian.Player;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.AddressableAssets;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-075 (EditMode, contract v2.1 §9.1): ArtImporter's model side on real art: the B-077 calibration model and
    /// the B-078 surveyor import as Mecanim, are addressed under their keys with a generated URP/Lit material, and the
    /// registry holds their clips exactly as their json lists them (D-069: the old sheet test's intent lives here).
    /// </summary>
    public class ModelImportTests
    {
        const string Calibration = "characters/calibration/base";

        [System.Serializable] class Manifest { public int fps; public Clip[] clips; }
        [System.Serializable] class Clip { public string name; public int frames; public bool loop; }

        static Manifest Json(string key) => JsonUtility.FromJson<Manifest>(File.ReadAllText($"Assets/_Game/Art/{key}.json"));

        static string Address(string path)
        {
            var guid = AssetDatabase.AssetPathToGUID(path);
            return AddressableAssetSettingsDefaultObject.Settings?.FindAssetEntry(guid)?.address;
        }

        [Test]
        public void CalibrationModelImportsAsMecanimWithMaterialAddressAndClips()
        {
            var glb = $"Assets/_Game/Art/{Calibration}.glb";
            Assert.IsTrue(File.Exists(glb), "B-077 model present");
            Assert.AreEqual(Calibration, Address(glb), "the model is addressed under its key");
            var clips = AssetDatabase.LoadAllAssetsAtPath(glb).OfType<AnimationClip>().ToArray();
            CollectionAssert.AreEquivalent(new[] { "idle", "walk" }, clips.Select(c => c.name));
            foreach (var c in clips) Assert.IsFalse(c.legacy, $"{c.name}: Mecanim clip (v9)");

            var mat = AssetDatabase.LoadAssetAtPath<Material>($"{ArtImporter.GeneratedModels}{Calibration}.mat");
            Assert.NotNull(mat, "generated material");
            Assert.NotNull(mat.GetTexture("_BaseMap"), "colour map");
            Assert.NotNull(mat.GetTexture("_BumpMap"), "normal map");
            Assert.NotNull(mat.GetTexture("_MetallicGlossMap"), "mask map");
            Assert.IsTrue(mat.IsKeywordEnabled("_EMISSION"), "emission map");
            Assert.AreEqual(Calibration, Address(AssetDatabase.GetAssetPath(mat)), "the material is addressed under the key too");

            var set = ArtMaterials.ModelClipsFor(Calibration);
            Assert.NotNull(set, "registry has the model's clips");
            Assert.AreEqual(30, set.fps);
            Assert.IsTrue(set.TryGet("idle", out var idle) && idle.loop);
            Assert.AreEqual(1.0f, idle.length / (float)set.fps, 1e-4f, "idle 1.0 s");
            Assert.IsTrue(set.TryGet("walk", out var walk) && walk.loop);
            Assert.AreEqual(0.8f, walk.length / (float)set.fps, 1e-4f, "walk 0.8 s");
        }

        [Test]
        public void SurveyorClipsMatchItsJsonAndEveryClipTheCodeUses()
        {
            // D-069: names, count and lengths from base.json; every clip name SurveyorAnim picks must exist.
            var json = Json(ArtKeys.Characters.Surveyor);
            var set = ArtMaterials.ModelClipsFor(ArtKeys.Characters.Surveyor);
            Assert.NotNull(set, "registry has the surveyor model's clips");
            Assert.AreEqual(json.fps, set.fps);
            Assert.AreEqual(json.clips.Length, set.clips.Count, "clip count");
            foreach (var c in json.clips)
            {
                Assert.IsTrue(set.TryGet(c.name, out var r), c.name);
                Assert.AreEqual(c.frames, r.length, $"{c.name} frames");
                Assert.AreEqual(c.loop, r.loop, $"{c.name} loop");
            }
            var modelClips = AssetDatabase.LoadAllAssetsAtPath($"Assets/_Game/Art/{ArtKeys.Characters.Surveyor}.glb").OfType<AnimationClip>().Select(c => c.name).ToList();
            foreach (var name in new[] { SurveyorAnim.Idle, SurveyorAnim.Walk, SurveyorAnim.Run, SurveyorAnim.Jump, SurveyorAnim.Fall,
                                         SurveyorAnim.Land, SurveyorAnim.Dig, SurveyorAnim.Aim, SurveyorAnim.Hurt, SurveyorAnim.Death })
            {
                Assert.IsTrue(set.TryGet(name, out _), $"json has '{name}'");
                CollectionAssert.Contains(modelClips, name, $"the model carries '{name}'");
            }
        }
    }
}
#endif
