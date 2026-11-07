using Meridian.EditorTools;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-117 (cycle 257): the painted discs and moons draw with MERIDIAN/Sprite_LitDisc, which resolves the 64-px frames' hard alpha
    /// limb at its iso-line (the near-range stairs in space_6_pilgrim); rings and rig sets keep the plain lit material; alpha blend,
    /// no cutoff.
    /// </summary>
    public class DiscMaterialTests
    {
        [Test]
        public void DiscAndMoonKeysTakeTheDiscMaterial()
        {
            Assert.IsTrue(ArtMaterials.IsDiscKey("planets/earth/disc"));
            Assert.IsTrue(ArtMaterials.IsDiscKey("planets/earth/luna"));
            Assert.IsTrue(ArtMaterials.IsDiscKey("planets/saturn/disc"));
            Assert.IsFalse(ArtMaterials.IsDiscKey("planets/saturn/rings_back"), "the rings keep their soft alpha");
            Assert.IsFalse(ArtMaterials.IsDiscKey("planets/sun/disc_rig"), "the Sun rig set is drawn by RigBuild");
            Assert.IsFalse(ArtMaterials.IsDiscKey("backgrounds/space/starfield/layer0"));
            Assert.IsFalse(ArtMaterials.IsDiscKey("creatures/earth/disc"), "planets only");
            Assert.IsFalse(ArtMaterials.IsDiscKey(null));
        }

        [Test]
        public void TheRegistryCarriesTheDiscMaterialOnItsShader()
        {
            var shader = Shader.Find(DiscSetup.ShaderName);
            Assert.NotNull(shader, DiscSetup.ShaderName + " compiles");
            DiscSetup.Run();
            var reg = AssetDatabase.LoadAssetAtPath<ArtMaterials>(DiscSetup.RegistryPath);
            Assert.NotNull(reg, "the registry");
            Assert.NotNull(reg.disc, "the registry's disc material");
            Assert.AreEqual(DiscSetup.ShaderName, reg.disc.shader.name);
            Assert.AreEqual(0.75f, reg.disc.GetFloat("_EdgeSoftness"), 1e-4f, "about a pixel of anti-aliasing at the iso-line");
            Assert.IsFalse(reg.disc.IsKeywordEnabled("_ALPHATEST_ON"), "alpha blend, no cutoff");
            Assert.AreSame(reg.disc, ArtMaterials.MaterialFor("planets/earth/luna"), "Luna draws with it");
            Assert.AreSame(reg.disc, ArtMaterials.MaterialFor("planets/jupiter/disc"));
            Assert.AreSame(reg.lit, ArtMaterials.MaterialFor("planets/saturn/rings_front"), "the rings do not");
        }
    }
}
