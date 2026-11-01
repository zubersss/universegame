using System.Collections;
using System.Linq;
using Meridian.Core;
using Meridian.Hazards;
using Meridian.Items;
using Meridian.Planet.POI;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-059 (PlayMode): the Beam cuts Solarite from Mercury's crystals 30 s after a flare, and glances off at 120 s.</summary>
    public class SolariteTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator SolariteOnlyInsideTheWindowAfterAFlare()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Mercury));
            var side = director.PlanetSide;
            side.hazards.enabled = false;
            var crystals = side.solarite;
            Assert.NotNull(crystals, "SolariteCrystals on PlanetSide");
            Assert.NotNull(crystals.flares, "bound to the flare clock");

            // Stand at the Solarite field.
            var field = PoiCatalog.For(PlanetId.Mercury).First(p => p.id == SolariteCrystals.FieldId);
            int x = Mathf.FloorToInt(field.x + 7f);
            var player = side.player;
            var feet = new Vector2(x + 0.5f, side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(x)) + 1.05f);
            player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero;
            yield return null;
            timeout = Time.realtimeSinceStartup + 15f;
            while ((!side.terrain.IsSettled || crystals.Clusters == 0) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
            Assert.Greater(crystals.Clusters, 0, "the field's crystal clusters");
            var near = crystals.Centres.OrderBy(c => (c - player.Body.position).sqrMagnitude).First();
            Assert.LessOrEqual(Vector2.Distance(near, player.Body.position), Meridian.Rig.RigTools.Reach, "a cluster in reach");
            var rig = side.rig;
            int solarite = ItemRegistry.Get("solarite").id;

            // +30 s after a flare: the crystals glow and the Beam cuts Solarite.
            crystals.flares.EndedAt(Time.time - 30f);
            yield return null;
            Assert.IsTrue(crystals.Harvestable);
            int dropsBefore = side.rig.drops.Live.Count(d => d.itemId == solarite);
            Assert.IsTrue(rig.Dig(near), "the Beam cuts Solarite at +30 s");
            Assert.AreEqual(SolariteCrystals.Result.Harvested, crystals.LastResult);
            Assert.AreEqual(dropsBefore + 1, side.rig.drops.Live.Count(d => d.itemId == solarite), "a Solarite drop");

            // +120 s: crusted over; the Beam glances off (and doesn't dig the ground behind).
            crystals.flares.EndedAt(Time.time - 120f);
            yield return null;
            Assert.IsFalse(crystals.Harvestable);
            var t = Meridian.Rig.RigTools.TileOf(near);
            byte behind = side.terrain.GetTile(t.x, t.y);
            Assert.IsFalse(rig.Dig(near), "nothing at +120 s");
            Assert.AreEqual(SolariteCrystals.Result.Crusted, crystals.LastResult);
            Assert.AreEqual(behind, side.terrain.GetTile(t.x, t.y), "the crust shields the ground behind");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
