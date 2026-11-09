using System.Collections;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-188 (BLENDER's 0.6.0 smoke read, smoke_43): a brown bear swam underwater beside the shark and a gull flew under the water line.
    /// A land walker turns at the shore (even fleeing), a flier keeps its band over the water line, and no walker spawns on a flooded column.
    /// </summary>
    public class ShoreCreatureTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest, Timeout(300000)]
        public IEnumerator LandCreaturesStayOutOfTheSeaAndBirdsAboveIt()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            if (side.hazards != null) side.hazards.enabled = false;
            var creatures = side.creatures;
            creatures.autoSpawn = false; creatures.DespawnAll();
            var t = side.terrain;
            int datum = side.Config.datumY;
            float water = datum + 1f;
            EarthBiomes.Range(Biome.Ocean, out int os, out _);
            // the shore: the first column (walking east) whose datum row holds the sea
            int edge = -1;
            for (int x = os - 60; x < os + 200 && edge < 0; x++) if (t.Generator.TileAt(t.WrapX(x), datum) == TileId.Water) edge = x;
            Assert.Greater(edge, 0, "Earth's sea found");
            var player = side.player;
            player.externalInput = true; player.intent = default;
            void Put(Vector2 p) { player.Body.position = p; player.transform.position = p; player.Body.linearVelocity = Vector2.zero; }
            Put(new Vector2(edge - 10.5f, t.SurfaceAt(edge - 10.5f) + 0.3f)); // 5 m behind the stag (it senses at 8 m)
            float until = Time.realtimeSinceStartup + 15f;
            yield return null;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();

            // a stag between the surveyor and the sea flees east toward the water: it turns at the shore, never wades in
            float sx = edge - 5.5f;
            var stagSpec = SpeciesSpec.Get(Species.Stag);
            var stag = creatures.Spawn(Species.Stag, new Vector2(sx, t.SurfaceAt(sx) + stagSpec.size.y * 0.5f + 0.1f));
            Assert.NotNull(stag);
            stag.dir = 1;
            float maxX = float.MinValue;
            for (int i = 0; i < 400; i++) { yield return new WaitForFixedUpdate(); maxX = Mathf.Max(maxX, stag.Body.position.x); }
            TestContext.Out.WriteLine($"[MERIDIAN] u188 the stag from {sx:0.0} toward the shore at {edge}: furthest x {maxX:0.00}, state {stag.State}");
            Assert.Less(maxX, edge + 0.5f, "the stag never stands over the sea");

            // a gull over the sea keeps its hover band over the water line
            float gx = edge + 24.5f;
            var gull = creatures.Spawn(Species.Gull, new Vector2(gx, water + 3f));
            Assert.NotNull(gull);
            float minY = float.MaxValue;
            for (int i = 0; i < 300; i++) { yield return new WaitForFixedUpdate(); minY = Mathf.Min(minY, gull.Body.position.y); }
            TestContext.Out.WriteLine($"[MERIDIAN] u188 the gull over the sea at {gx:0.0}: lowest y {minY:0.00} (the water line {water})");
            Assert.Greater(minY, water + 0.5f, "the gull flies above the water line");

            // no walker spawns on a flooded column (the shore's drowned turf keeps its grass tile)
            int drowned = 0;
            for (int x = edge; x < edge + 30; x++)
            {
                int top = t.TopSolidY(x);
                if (t.GetTile(x, top + 1) != TileId.Water || t.GetTile(x, top) != TileId.Grass) continue;
                drowned++;
                Assert.IsNull(creatures.SpawnAt(Species.BrownBear, x, player.Body.position.y), $"no bear on the drowned turf at x {x}");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u188 drowned grass columns by the shore: {drowned}");
            creatures.DespawnAll();
            LogAssert.NoUnexpectedReceived();
        }
    }
}
