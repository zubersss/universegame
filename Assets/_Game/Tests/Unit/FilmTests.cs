using Meridian.Core;
using Meridian.EditorTools;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Meridian.Tests
{
    /// <summary>
    /// U-095 (EditMode): the three film overlays import as 512² repeat tiles without mips (contract §11.6); the film
    /// feature sits on the renderer with the MERIDIAN/FilmPass material and HDR is off; the flicker stays within ±2 %;
    /// the Film effects setting defaults to on and persists.
    /// </summary>
    public class FilmTests
    {
        [Test]
        public void OverlaysImportAs512SquareRepeatTilesWithoutMips()
        {
            foreach (var key in new[] { FilmFeature.GrainKey, FilmFeature.DustKey, FilmFeature.ScratchesKey })
            {
                var path = ArtImporter.ArtColorPath(key);
                var ti = AssetImporter.GetAtPath(path) as TextureImporter;
                Assert.NotNull(ti, path);
                ti.GetSourceTextureWidthAndHeight(out int w, out int h);
                Assert.AreEqual(512, w, key + " width");
                Assert.AreEqual(512, h, key + " height");
                Assert.IsNull(ArtRules.ValidateOverlay(w, h));
                Assert.AreEqual(TextureWrapMode.Repeat, ti.wrapMode, key + " tiles");
                Assert.IsFalse(ti.mipmapEnabled, key + " no mips");
                Assert.AreEqual(TextureImporterType.Sprite, ti.textureType, key + " sprite (v13)");
            }
        }

        [Test]
        public void TheFilmFeatureIsOnTheRendererAndHdrIsOff()
        {
            var data = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(FilmSetup.RendererPath);
            Assert.NotNull(data, "MERIDIAN_Renderer3D");
            FilmFeature feature = null;
            foreach (var f in data.rendererFeatures) if (f is FilmFeature ff) feature = ff;
            Assert.NotNull(feature, "FilmFeature on the renderer (FilmSetup.Run)");
            Assert.NotNull(feature.Material, "material");
            Assert.AreEqual(FilmSetup.ShaderName, feature.Material.shader.name);
            var urp = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(FilmSetup.UrpPath);
            Assert.IsFalse(urp.supportsHDR, "HDR off (Bible §9.4 v4)");
            Assert.NotNull(Shader.Find(FilmSetup.ShaderName));
        }

        [Test]
        public void FlickerStaysWithinTwoPercent()
        {
            float min = 2f, max = 0f;
            for (int step = 0; step < 5000; step++)
            {
                float f = FilmFeature.Flicker(step);
                min = Mathf.Min(min, f); max = Mathf.Max(max, f);
            }
            Assert.GreaterOrEqual(min, 1f - FilmFeature.FlickerAmplitude - 1e-6f);
            Assert.LessOrEqual(max, 1f + FilmFeature.FlickerAmplitude + 1e-6f);
            Assert.Less(min, 0.995f, "it does flicker down");
            Assert.Greater(max, 1.005f, "and up");
            Assert.AreEqual(FilmFeature.Flicker(7), FilmFeature.Flicker(7), "deterministic per step");
        }

        [Test]
        public void FilmEffectsDefaultOnAndPersist()
        {
            int before = PlayerPrefs.GetInt(GameSettings.FilmKey, 1);
            try
            {
                PlayerPrefs.DeleteKey(GameSettings.FilmKey);
                GameSettings.Reload();
                Assert.IsTrue(GameSettings.FilmEffects, "default on");
                GameSettings.FilmEffects = false;
                GameSettings.Reload();
                Assert.IsFalse(GameSettings.FilmEffects, "saved off");
                GameSettings.FilmEffects = true;
                GameSettings.Reload();
                Assert.IsTrue(GameSettings.FilmEffects, "saved on");
            }
            finally { PlayerPrefs.SetInt(GameSettings.FilmKey, before); GameSettings.Reload(); }
        }
    }
}
