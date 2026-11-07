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
        public void SurveyorClipsMatchItsSheetJsonAndEveryClipTheCodeUses()
        {
            // D-120 (P-30 / P-32): the surveyor is a frame sheet again (B-125): names and lengths from side.json within the §11.2 caps,
            // one generated clip per drawing set, and every clip SurveyorAnim picks resolves to a drawing the sheet has (U-105).
            var path = "Assets/_Game/Art/characters/surveyor/side.json";
            Assert.IsTrue(File.Exists(path), "the live surveyor sheet sidecar");
            var sheet = JsonUtility.FromJson<Meridian.EditorTools.ArtImporter.SheetManifest>(File.ReadAllText(path));
            Assert.IsTrue(sheet.IsV3 && sheet.IsSheet, "a v3 frame sheet");
            Assert.AreEqual(12, sheet.fps, "on twos");
            var names = new System.Collections.Generic.HashSet<string>();
            foreach (var c in sheet.animations)
            {
                Assert.IsTrue(names.Add(c.name), $"clip '{c.name}' listed once");
                Meridian.EditorTools.ArtRules.ClipCap(c.name, out int min, out int max);
                Assert.IsTrue(c.length >= 1 && c.length <= max, $"{c.name}: {c.length} frames within its cap of {max}");
                var clipPath = Meridian.EditorTools.SheetAnimatorBuilder.ClipPath(Meridian.View2D.CartoonStage.SurveyorKey, c.name);
                Assert.IsTrue(File.Exists(clipPath), $"generated clip {clipPath}");
            }
            foreach (var name in SurveyorAnim.AllClips)
                Assert.IsTrue(names.Contains(SurveyorAnim.ResolveOn(name, names.Contains)), $"'{name}' resolves to a drawing the sheet has");
        }
    }
}
#endif
