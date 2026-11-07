using System.Collections;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Terrain;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-128: on Earth the painted set and its datum follow the camera's band: the camp keeps its stamped surface and the forest set;
    /// carried into the plains the set crossfades to the plains at datum + 6; carried to the coast (column 2096) it crossfades to the
    /// coast set at the water line, so the shore is painted behind the Maw.
    /// </summary>
    public class BandFollowPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            side.creatures.autoSpawn = false;
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
        }

        IEnumerator CarryTo(int tx)
        {
            var stand = new Vector2(tx + 0.5f, side.terrain.TopSolidY(tx) + 1.1f);
            side.player.Body.position = stand; side.player.transform.position = stand; side.player.Body.linearVelocity = Vector2.zero;
            var follow = Object.FindAnyObjectByType<Meridian.Player.CameraFollow>();
            if (follow != null) follow.SnapToTarget();
            float until = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
        }

        [UnityTest]
        public IEnumerator TheSetAndTheDatumFollowTheCamerasBand()
        {
            yield return Boot();
            var stage = side.cartoon;
            Assert.NotNull(stage); Assert.IsTrue(stage.Active);
            Assert.NotNull(stage.Datum, "the per-band datum sampler");
            float camp = stage.Datum.At(side.spawnX);
            Assert.AreEqual(side.terrain.TopSolidY(side.spawnX) + 1f, camp, 1e-3f, "the camp band keeps the stamped camp surface");
            Assert.AreEqual("forest", stage.Scene, "the camp is the forest band");
            yield return null;
            Assert.AreEqual(camp, stage.Layers.datumY, 1e-3f, "the layers sit at the camp datum at the camp");
            // Into the plains: the set crossfades, the datum lands at datum + 6.
            EarthBiomes.Range(Biome.Plains, out int ps, out int pl);
            yield return CarryTo(ps + 60);
            float until = Time.realtimeSinceStartup + 6f;
            while ((stage.Fading || stage.Scene != "plains") && Time.realtimeSinceStartup < until) yield return null;
            TestContext.Out.WriteLine($"[MERIDIAN] band follow: at x {ps + 60} scene {stage.Scene} ({stage.Layers.SceneKey}), crossfades {stage.Crossfades}, datum {stage.Layers.datumY:F1}, camp {camp:F1}");
            Assert.AreEqual("plains", stage.Scene, "the plains set after the border");
            Assert.GreaterOrEqual(stage.Crossfades, 1, "one crossfade");
            Assert.IsFalse(stage.Fading);
            Assert.AreEqual(side.Config.datumY + 6f, stage.Layers.datumY, 1e-3f, "the plains datum (datum + 6)");
            Assert.AreEqual(0, stage.Layers.orderOffset, "the new base set sits at the base orders");
            Assert.IsFalse(stage.Incoming != null && stage.Incoming.gameObject.activeSelf, "the old set released");
            // To the coast at 2096: the coast set at the water line.
            yield return CarryTo(2096);
            until = Time.realtimeSinceStartup + 6f;
            while ((stage.Fading || stage.Scene != "coast") && Time.realtimeSinceStartup < until) yield return null;
            TestContext.Out.WriteLine($"[MERIDIAN] band follow: at x 2096 scene {stage.Scene} ({stage.Layers.SceneKey}), crossfades {stage.Crossfades}, datum {stage.Layers.datumY:F1}, placeholders {stage.Layers.placeholders.Contains(true)}");
            Assert.AreEqual("coast", stage.Scene, "the coast set on the shore (the Maw's frames)");
            Assert.AreEqual(stage.Datum.At(2096), stage.Layers.datumY, 1e-3f, "the sampler's datum at the shore (16 columns into the band: still blending down from the desert)");
            Assert.Greater(stage.Layers.datumY, side.Config.datumY + 1f - 1e-3f); Assert.Less(stage.Layers.datumY, side.Config.datumY + 8f);
            Assert.AreEqual(side.Config.datumY + 1f, stage.Datum.At(2080 + 60), 1e-3f, "60 columns in: the water line");
            Assert.GreaterOrEqual(stage.Crossfades, 2);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
