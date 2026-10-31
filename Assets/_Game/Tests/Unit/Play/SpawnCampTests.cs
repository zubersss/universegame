using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Planet.POI;
using Meridian.Rendering;
using Meridian.Save;
using Meridian.Ship;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-035 (PlayMode): the Earth spawn camp: the Pilgrim rests on the pad, the surveyor stands on the crates, lamps glow, the stamp survives dig/save/load.</summary>
    public class SpawnCampTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string root;
        SceneDirector director;
        PlanetSideRoot side;
        PoiPlacer.Placed camp;

        [SetUp] public void SetUp() { root = Path.Combine(Application.temporaryCachePath, "meridian_camp_" + System.Guid.NewGuid().ToString("N").Substring(0, 6)); SaveSystem.RootOverride = root; }
        [TearDown] public void TearDown() { SaveSystem.RootOverride = null; if (Directory.Exists(root)) Directory.Delete(root, true); }

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            camp = side.pois.placed.Find(p => p.def == PoiCatalog.SpawnCamp);
            Assert.NotNull(camp, "spawn camp placed on Earth");
            for (int i = 0; i < 90; i++) yield return new WaitForFixedUpdate();
        }

        float Top(string propName)
        {
            float top = float.NegativeInfinity;
            foreach (var c in side.pois.Solids) if (c.name.StartsWith(propName)) top = Mathf.Max(top, c.bounds.max.y);
            return top;
        }

        [UnityTest]
        public IEnumerator ShipOnThePadSurveyorOnTheCampGround()
        {
            yield return Boot();
            Assert.AreEqual(4, side.pois.Solids.Count, "pad + 3 crates are solid");
            float padTop = Top("landing_pad");
            float skids = side.ship.Body.position.y - SideShip.SkidDrop;
            TestContext.Out.WriteLine($"[MERIDIAN] pad top {padTop:F2}, skids {skids:F2}, ground line {camp.groundY + 1}, player feet {side.player.Body.position.y:F2}");
            Assert.AreEqual(padTop, skids, 0.15f, "the Pilgrim rests on the pad deck");
            Assert.AreEqual(100f, GameState.Instance.hull, 1e-3f, "no damage settling");
            Assert.IsTrue(side.player.Grounded, "surveyor standing");
            Assert.AreEqual(camp.groundY + 1f, side.player.Body.position.y, 0.15f, "on the camp's levelled ground");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator SurveyorCanStandOnTheCrates()
        {
            yield return Boot();
            float crateTop = Top("storage_crate");
            var p = PoiCatalog.SpawnCamp;
            var player = side.player;
            player.Body.position = new Vector2(p.x + 3.25f, crateTop + 2f);
            player.Body.linearVelocity = Vector2.zero;
            for (int i = 0; i < 30 && player.Grounded; i++) yield return new WaitForFixedUpdate();
            for (int i = 0; i < 200 && !player.Grounded; i++) yield return new WaitForFixedUpdate();
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Grounded);
            Assert.AreEqual(crateTop, player.Body.position.y, 0.1f, "standing on the top crate");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator LampsGlowAndADigSurvivesSaveLoad()
        {
            yield return Boot();
            foreach (var sr in camp.props)
                if (sr.name == "lamp")
                {
                    float until = Time.realtimeSinceStartup + 5f;
                    while (sr.sharedMaterial != ArtMaterials.Active.litEmissive && Time.realtimeSinceStartup < until) yield return null;
                    Assert.AreSame(ArtMaterials.Active.litEmissive, sr.sharedMaterial, "lamps glow by their emission map");
                }

            int x = PoiCatalog.SpawnCamp.x + 1, y = camp.groundY;
            Assert.AreEqual(TileId.Grass, side.terrain.GetTile(x, y));
            Assert.IsTrue(side.terrain.SetTile(x, y, TileId.Air));
            SaveSystem.Instance.Save();
            side.terrain.SetTile(x, y, TileId.Grass);
            yield return SaveSystem.Instance.Load();
            float t = Time.realtimeSinceStartup + 20f;
            while (!director.PlanetSide.terrain.IsSettled && Time.realtimeSinceStartup < t) yield return null;
            Assert.AreEqual(TileId.Air, director.PlanetSide.terrain.GetTile(x, y), "the dig survives (stamp written once)");
            Assert.AreEqual(TileId.Grass, director.PlanetSide.terrain.GetTile(x + 5, y), "rest of the camp intact");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
