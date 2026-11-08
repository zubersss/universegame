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
            Assert.IsTrue(stage.Datum.FollowsCurve, "U-161: Earth's ground is smooth, the sets follow its walking curve");
            float cx = stage.Layers.view.transform.position.x;
            Assert.AreEqual(side.terrain.CurveAt(Mathf.FloorToInt(cx)), stage.Layers.datumY, 1f, "U-161: the plains set's ground line within 1 m of the walking surface");
            Assert.AreEqual(Followed(stage, cx), stage.Layers.datumY, 0.05f, "the sampler's datum between the camera's columns");
            Assert.AreEqual(0, stage.Layers.orderOffset, "the new base set sits at the base orders");
            Assert.IsFalse(stage.Incoming != null && stage.Incoming.gameObject.activeSelf, "the old set released");
            // To the coast at 2096: the coast set at the water line.
            yield return CarryTo(2096);
            until = Time.realtimeSinceStartup + 6f;
            while ((stage.Fading || stage.Scene != "coast") && Time.realtimeSinceStartup < until) yield return null;
            TestContext.Out.WriteLine($"[MERIDIAN] band follow: at x 2096 scene {stage.Scene} ({stage.Layers.SceneKey}), crossfades {stage.Crossfades}, datum {stage.Layers.datumY:F1}, placeholders {stage.Layers.placeholders.Contains(true)}");
            Assert.AreEqual("coast", stage.Scene, "the coast set on the shore (the Maw's frames)");
            cx = stage.Layers.view.transform.position.x;
            Assert.AreEqual(Followed(stage, cx), stage.Layers.datumY, 0.05f, "the sampler's datum at the shore");
            Assert.AreEqual(Mathf.Max(side.terrain.CurveAt(Mathf.FloorToInt(cx)), side.Config.datumY + 1f), stage.Layers.datumY, 1f, "U-161: on the shore, the walking surface or the water line");
            Assert.GreaterOrEqual(stage.Datum.At(2080 + 60), side.Config.datumY + 1f - 1e-3f, "60 columns in: never under the water line");
            Assert.GreaterOrEqual(stage.Crossfades, 2);
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>U-161: the stage's datum between the camera's two columns (CartoonStage.FollowBand).</summary>
        static float Followed(Meridian.View2D.CartoonStage stage, float cameraX)
        {
            int x = Mathf.FloorToInt(cameraX);
            return Mathf.Lerp(stage.Datum.At(x), stage.Datum.At(x + 1), cameraX - x);
        }

        /// <summary>
        /// U-164 (D-169): in a valley the stretch between the nearest layer's bottom edge and the ground is that layer going on down (its bottom
        /// strip repeated, in front of the farther layers), never layer0's sky or sea, never layer1. On 3 world seeds, in each of Earth's 6 biomes,
        /// the surveyor is carried to the column whose frame holds the deepest dip, and at every frame column whose dry surface lies under layer2's
        /// bottom edge the fill continues layer 2: its top within 3 cm of that edge, its foot under the surface, its order over layer1's.
        /// </summary>
        [UnityTest, Timeout(360000)]
        public IEnumerator UnderTheNearestLayerAValleyShowsItsStripNeverTheSky()
        {
            yield return Boot();
            var director = Object.FindAnyObjectByType<SceneDirector>();
            int seed0 = GameState.Instance.worldSeed;
            try
            {
                foreach (int seed in new[] { seed0, 7717, 31337 })
                {
                    if (seed != seed0)
                    {
                        GameState.Instance.worldSeed = seed;
                        GameState.Instance.EditsFor(PlanetId.Earth).Clear();
                        foreach (var poi in Meridian.Planet.POI.PoiCatalog.For(PlanetId.Earth)) GameState.Instance.ClearFlag(poi.StampedFlag);
                        yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Earth));
                        side = director.PlanetSide;
                        side.creatures.autoSpawn = false;
                        float settle = Time.realtimeSinceStartup + 20f;
                        while (!side.terrain.IsSettled && Time.realtimeSinceStartup < settle) yield return null;
                    }
                    var t = side.terrain;
                    var stage = side.cartoon;
                    float sea = side.Config.datumY + 1f;
                    foreach (Biome b in System.Enum.GetValues(typeof(Biome)))
                    {
                        EarthBiomes.Range(b, out int bs, out int bl);
                        int best = bs + bl / 2; float dip = 0f;
                        for (int x = bs + 60; x < bs + bl - 60; x += 3)
                        {
                            float here = t.CurveAt(x), low = here;
                            for (int dx = -12; dx <= 12; dx += 2) low = Mathf.Min(low, t.CurveAt(x + dx));
                            if (low > sea && here - low > dip) { dip = here - low; best = x; }
                        }
                        if (dip <= 0f) { TestContext.Out.WriteLine($"[MERIDIAN] u164 seed {seed} {b}: no dry dip in the band (open sea): skipped"); continue; }
                        yield return CarryTo(best);
                        float until = Time.realtimeSinceStartup + 10f;
                        while ((stage.Fading || stage.Layers.placeholders.Contains(true)) && Time.realtimeSinceStartup < until) yield return null;
                        for (int k = 0; k < 10; k++) yield return null;
                        var layers = stage.Layers;
                        int near = 0, mid = -1;
                        for (int i = 0; i < layers.renderers.Count; i++) if (layers.Layout.layers[i].n > layers.Layout.layers[near].n) near = i;
                        for (int i = 0; i < layers.renderers.Count; i++) if (layers.Layout.layers[i].n == layers.Layout.layers[near].n - 1) mid = i;
                        float bottom = layers.renderers[near].transform.position.y;
                        var cam = layers.view;
                        float cx = cam.transform.position.x, half = cam.orthographicSize * cam.aspect;
                        int under = 0;
                        for (float x = cx - half; x <= cx + half; x += 0.5f)
                        {
                            float s = t.SurfaceAt(x);
                            if (s >= bottom - 0.1f || s <= sea) continue;
                            under++;
                            string at = $"seed {seed} {b} ({stage.Scene}) column {x:F1}: surface {s:F2} under layer2's edge {bottom:F2}";
                            Assert.AreEqual(layers.Layout.layers[near].n, layers.FillLayer, at + ": the nearest layer goes on down");
                            Assert.IsTrue(layers.Fill.enabled, at);
                            Assert.AreEqual(bottom, layers.FillTop, 0.03f, at + ": from the layer's edge");
                            Assert.Less(layers.FillTop - layers.Fill.size.y, s - 0.5f, at + ": down under the ground");
                            if (mid >= 0) Assert.Greater(layers.Fill.sortingOrder, layers.renderers[mid].sortingOrder, at + ": in front of layer1");
                        }
                        TestContext.Out.WriteLine($"[MERIDIAN] u164 seed {seed} {b}: column {best} (dip {dip:F1} m), scene {stage.Scene}, layer2 edge {bottom:F2}, {under} columns under it, fill layer {layers.FillLayer}");
                    }
                }
            }
            finally { GameState.Instance.worldSeed = seed0; }
            LogAssert.NoUnexpectedReceived();
        }
    }
}
