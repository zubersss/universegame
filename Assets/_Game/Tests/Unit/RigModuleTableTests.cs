using Meridian.Rig;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-046 (EditMode): module cycling (1–4, Q/E wrap) and the B-037 muzzle table.</summary>
    public class RigModuleTableTests
    {
        [Test]
        public void QAndECycleThroughAllFourAndWrap()
        {
            Assert.AreEqual(RigModule.Grapple, RigModules.Next(RigModule.Beam, +1));
            Assert.AreEqual(RigModule.Beam, RigModules.Next(RigModule.Builder, +1), "E wraps");
            Assert.AreEqual(RigModule.Builder, RigModules.Next(RigModule.Beam, -1), "Q wraps");
            var m = RigModule.Survey;
            for (int i = 0; i < RigModules.Count; i++) m = RigModules.Next(m, +1);
            Assert.AreEqual(RigModule.Survey, m, "a full turn returns");
        }

        [Test]
        public void MuzzleOffsetsAndArtMatchTheHandOff()
        {
            Assert.AreEqual(new Vector2(0.47f, 0.03f), RigModules.Muzzle(RigModule.Beam));
            Assert.AreEqual(new Vector2(0.52f, 0.035f), RigModules.Muzzle(RigModule.Grapple));
            Assert.AreEqual(new Vector2(0.30f, 0.06f), RigModules.Muzzle(RigModule.Survey));
            Assert.AreEqual(new Vector2(0.44f, 0.03f), RigModules.Muzzle(RigModule.Builder));
            Assert.AreEqual("props/rig/grapple", RigModules.ArtKey(RigModule.Grapple));
        }
    }
}
