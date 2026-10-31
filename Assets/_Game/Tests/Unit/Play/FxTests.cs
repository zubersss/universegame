using System.Collections;
using Meridian.Art;
using Meridian.Core;
using Meridian.FX;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-033 (PlayMode): pooled one-shots play once and free their slot; emissive fx draw with Sprite_LitEmissive; ship flames follow thrust.</summary>
    public class FxTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
        }

        static IEnumerator Ready(string key)
        {
            var s = FxSheet.Get(key);
            float timeout = Time.realtimeSinceStartup + 10f;
            while (!s.Ready && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(s.Ready, key + " loaded");
        }

        [UnityTest]
        public IEnumerator OneShotsPlayOnceAndFreeTheirSlot()
        {
            yield return Boot();
            yield return Ready(ArtKeys.Fx.Dust);
            var pool = Object.FindAnyObjectByType<FxPool>();
            Assert.NotNull(pool, "FxPool on PlanetSide");
            int before = pool.Alive;
            Assert.IsTrue(pool.Play(ArtKeys.Fx.Dust, Vector2.zero));
            Assert.AreEqual(before + 1, pool.Alive);
            var dust = FxSheet.Get(ArtKeys.Fx.Dust);
            float clipSeconds = dust.clip.length / (float)dust.fps;
            float t0 = Time.time;
            while (Time.time - t0 < clipSeconds + 0.2f) yield return null;
            Assert.AreEqual(before, pool.Alive, "freed after its clip");

            for (int i = 0; i < FxPool.Size + 10; i++) pool.Play(ArtKeys.Fx.Dust, new Vector2(i, 0f));
            Assert.AreEqual(FxPool.Size, pool.Alive, "a full pool reuses its oldest slot instead of growing");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator EmissiveFxUseTheEmissiveMaterial()
        {
            yield return Boot();
            yield return Ready(ArtKeys.Fx.Thruster);
            yield return Ready(ArtKeys.Fx.Dust);
            var reg = ArtMaterials.Active;
            Assert.AreSame(reg.litEmissive, FxSheet.Get(ArtKeys.Fx.Thruster).material, "thruster has an emission map");
            Assert.AreSame(reg.litEmissive, FxSheet.Get(ArtKeys.Fx.DigSparks).material, "dig sparks have an emission map");
            Assert.AreSame(reg.lit, FxSheet.Get(ArtKeys.Fx.Dust).material, "dust has none");
        }

        [UnityTest]
        public IEnumerator SideFlamesFollowThrust()
        {
            yield return Boot();
            yield return Ready(ArtKeys.Fx.Thruster);
            var side = Object.FindAnyObjectByType<SceneDirector>().PlanetSide;
            var fx = side.ship.GetComponent<ShipFx>();
            Assert.NotNull(fx, "ShipFx on the Pilgrim");
            yield return null;
            Assert.IsFalse(fx.PodFore.active, "no flame on the pad");
            side.hazards.boarding.ForceAboard();
            side.ship.externalInput = true;
            side.ship.intent.thrust = 1f;
            for (int i = 0; i < 3; i++) yield return null;
            Assert.IsTrue(fx.Main.active && fx.PodFore.active && fx.PodAft.active, "main engine and both pods while thrusting");
            Assert.IsTrue(fx.PodFore.target.enabled, "drawn");
            Assert.AreSame(ArtMaterials.Active.litEmissive, fx.PodFore.target.sharedMaterial, "flames glow (emissive)");
            side.ship.intent.thrust = 0f;
            for (int i = 0; i < 3; i++) yield return null;
            Assert.IsFalse(fx.PodFore.active, "off with the throttle");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
