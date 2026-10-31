using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-008: Beam digs (item drops), Builder places, diffs persist through save → load.</summary>
    public class DigPlaceTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static IEnumerator Boot(System.Action<PlanetSideRoot> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            yield return SceneManager.LoadSceneAsync("Core", LoadSceneMode.Single);
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 10f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady);
            yield return Settle(director.PlanetSide.terrain);
            done(director.PlanetSide);
        }

        static IEnumerator Settle(TerrainStreamer t)
        {
            float timeout = Time.realtimeSinceStartup + 20f;
            while (!t.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(t.IsSettled, "terrain settled");
        }

        [UnityTest]
        public IEnumerator DigPlaceSaveLoadKeepsTheChanges()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var t = side.terrain;
            var rig = side.rig;
            Assert.NotNull(rig, "Rig on PlanetSide");

            // Dig the surface tile under the spawn column.
            int x = side.spawnX, y = t.Generator.SurfaceHeight(x);
            byte before = t.GetTile(x, y);
            Assert.IsTrue(TileId.IsSolid(before), "surface tile is solid");
            int diffsBefore = t.Edits.Count; // a new world already holds POI stamp diffs (U-030)
            Assert.IsTrue(rig.Dig(new Vector2(x + 0.5f, y + 0.5f)), "Beam digs");
            Assert.AreEqual(TileId.Air, t.GetTile(x, y));
            Assert.IsNull(t.RenderedTile(x, y), "tile gone from the tilemap");
            Assert.AreEqual(1, rig.drops.Live.Count, "item dropped");
            Assert.AreEqual(before, rig.drops.Live[0].itemId, "drop is the dug material");

            // Place a tile in open air two columns over.
            int px = x + 3, py = t.Generator.SurfaceHeight(px) + 3;
            Assert.AreEqual(TileId.Air, t.GetTile(px, py));
            Assert.IsTrue(rig.Place(new Vector2(px + 0.5f, py + 0.5f), TileId.Stone), "Builder places");
            Assert.AreEqual(TileId.Stone, t.GetTile(px, py));
            Assert.NotNull(t.RenderedTile(px, py));
            Assert.AreEqual(diffsBefore + 2, t.Edits.Count, "two diffs recorded");

            // Save the diffs, start a fresh session, load them, rebuild the planet.
            var path = Path.Combine(Application.temporaryCachePath, "meridian_test", "terrain_earth.bin");
            t.Edits.SaveFile(path);
            yield return Boot(s => side = s);
            t = side.terrain;
            Assert.AreEqual(before, t.GetTile(x, y), "fresh session starts from the seed");
            GameState.Instance.EditsFor(PlanetId.Earth).LoadFile(path);
            side.Configure(side.Config);
            yield return Settle(t);

            Assert.AreEqual(TileId.Air, t.GetTile(x, y), "dug tile still absent after load");
            Assert.IsNull(t.RenderedTile(x, y), "and not drawn");
            Assert.AreEqual(TileId.Stone, t.GetTile(px, py), "placed tile still there after load");
            Assert.NotNull(t.RenderedTile(px, py));
            File.Delete(path);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
