using System.Collections;
using Meridian.Core;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-118: a Mars entry on the cartoon stage — the painted Mars set in place of the 3D stage (the canyon set, or the plains set once
    /// B-141 lands it), the Mars strips, the Mars rig set's plants, and the storm veil bound to the dust storm's intensity.
    /// </summary>
    public class MarsStagePlayTests
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
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Mars));
            side = director.PlanetSide;
            Assert.AreEqual(PlanetId.Mars, side.Config.id);
            side.hazards.enabled = false;
            if (side.wardens != null) side.wardens.enabled = false;
            timeout = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
        }

        [UnityTest]
        public IEnumerator MarsPaintsItsSetStripsPlantsAndStormVeil()
        {
            yield return Boot();
            var stage = side.cartoon;
            Assert.NotNull(stage, "CartoonStage on PlanetSide");
            Assert.IsTrue(stage.Active, "Mars runs the cartoon path (U-118)");
            Assert.IsTrue(side.stage == null || !side.stage.gameObject.activeSelf, "the 3D stage layers are off");
            var layers = stage.Layers;
            Assert.NotNull(layers);
            StringAssert.StartsWith("backgrounds/mars/", layers.SceneKey, "a Mars set");
            float until = Time.realtimeSinceStartup + 15f;
            while ((layers.placeholders.Contains(true) || !stage.Ground.Ready || !stage.Flora.Ready) && Time.realtimeSinceStartup < until) yield return null;
            TestContext.Out.WriteLine($"[MERIDIAN] mars stage: spawn x {side.spawnX}, region {Meridian.Planet.Backdrop.StageRegions.At(PlanetId.Mars, side.spawnX)}, scene {stage.Scene} → {layers.SceneKey} (fallback used: {layers.UsedFallback}), placeholders {layers.placeholders.Contains(true)}, ground {stage.Ground.MaterialsLoaded}/{Meridian.View2D.GroundStrip.KeysFor(PlanetId.Mars).Length} strips, flora ready {stage.Flora.Ready}");
            Assert.IsFalse(layers.placeholders.Contains(true), "the painted Mars layers are in (canyon, or plains once B-141 lands it)");
            Assert.IsTrue(stage.Ground.Ready, "the Mars strips");
            Assert.AreEqual(1, stage.Ground.MaterialsLoaded, "smooth Mars loads only its regolith strip, SmoothGround's placeholder (U-186, LEAD 22:1x: the basalt / frost strips retired; a stale count, not a loosened bound)");
            Assert.IsTrue(stage.Flora.Ready, "the Mars rig set (B-140)");
            int plants = stage.Flora.transform.childCount;
            Assert.Greater(plants, 0, "Mars plants around the camp");
            var allowed = Meridian.Flora.FloraRigs.PlantsFor(stage.Flora.Set, Meridian.Flora.FloraRigs.BiomeNameAt(PlanetId.Mars, side.spawnX));
            var names = new System.Collections.Generic.HashSet<string>();
            foreach (var p in allowed) names.Add(p.name);
            foreach (Transform t in stage.Flora.transform) Assert.IsTrue(names.Contains(t.name), $"{t.name} grows in this region");
            // The storm veil: the storm set loaded behind, its alpha the dust storm's intensity (0 while clear).
            Assert.NotNull(stage.StormLayers, "the storm veil layers");
            Assert.AreEqual("backgrounds/mars/storm", stage.StormLayers.SceneKey);
            var storm = side.dustStorm;
            Assert.NotNull(storm, "DustStorm on PlanetSide");
            yield return null;
            Assert.AreEqual(Meridian.View2D.CartoonStage.StormAlpha(storm.Intensity), stage.StormLayers.alpha, 1e-4f, "the veil's alpha follows the storm");
            TestContext.Out.WriteLine($"[MERIDIAN] mars storm veil: phase {storm.Phase}, intensity {storm.Intensity:F2}, alpha {stage.StormLayers.alpha:F2}, plants {plants}");
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>U-118 (D-126): a tube lurker spawned over a lava tube gets its mound (a prop in front, order 6) and counts as at its den; the creatures and the den go with the planet.</summary>
        [UnityTest]
        public IEnumerator TheLurkerSpawnsAtItsMound()
        {
            yield return Boot();
            var creatures = side.creatures;
            creatures.autoSpawn = false;
            creatures.DespawnAll();
            var tube = Meridian.Terrain.MarsLandforms.Tubes[0];
            int tx = tube.x0 + Meridian.Terrain.MarsLandforms.SkylightInset + 6; // over the tube, past the skylight shaft
            float y = side.player.Body.position.y;
            var stand = new Vector2(tx + 4 + 0.5f, side.terrain.TopSolidY(tx + 4) + 1.1f); // U-159: east of the den, clear of the skylight's funnel
            side.player.Body.position = stand; side.player.transform.position = stand; side.player.Body.linearVelocity = Vector2.zero;
            var follow = Object.FindAnyObjectByType<Meridian.Player.CameraFollow>();
            if (follow != null) follow.SnapToTarget();
            float until = Time.realtimeSinceStartup + 25f;
            while (!(side.terrain.IsSettled && side.terrain.IsCollisionReady(tx, side.terrain.TopSolidY(tx))) && Time.realtimeSinceStartup < until) yield return null;
            var site = creatures.SiteAt(tx, side.player.Body.position.y);
            TestContext.Out.WriteLine($"[MERIDIAN] lurker site x {tx}: tile {site.surfaceTile} y {site.surfaceY}, over tube {Meridian.Terrain.MarsLandforms.OverTube(tx)}, allows {Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.TubeLurker).Allows(site)}");
            var lurker = creatures.SpawnAt(Meridian.Creatures.Species.TubeLurker, tx, side.player.Body.position.y);
            Assert.NotNull(lurker, "the lurker spawns over the tube");
            Assert.AreEqual(1, creatures.Dens.Count, "one mound placed");
            var den = creatures.Dens[0];
            Assert.AreEqual("props/mars/tube_mound", den.name);
            Assert.AreEqual(Meridian.Creatures.CreatureDirector.DenOrder, den.GetComponent<SpriteRenderer>().sortingOrder, "the mound draws in front of the creature");
            Assert.IsTrue(lurker.AtDen, "spawned at its den");
            Assert.AreEqual(den.position.x, lurker.DenX, 1e-3f);
            var second = creatures.SpawnAt(Meridian.Creatures.Species.TubeLurker, tx + 2, side.player.Body.position.y);
            if (second != null) Assert.AreEqual(1, creatures.Dens.Count, "a second lurker within 6 m shares the mound");
            creatures.DespawnAll();
            LogAssert.NoUnexpectedReceived();
        }
    }
}
