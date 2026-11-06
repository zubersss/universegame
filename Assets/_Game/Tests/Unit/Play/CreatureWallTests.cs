using System.Collections;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Player;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-099 (PlayMode, Earth): a fleeing creature that runs into the camp's crate stack turns within 0.5 s and keeps
    /// moving; a chasing wolf blocked by a 2-tile wall stays put with a still idle, never bumping through it.
    /// </summary>
    public class CreatureWallTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;
        CreatureDirector creatures;

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            player = side.player;
            creatures = side.creatures;
            player.externalInput = true; player.intent = default;
            side.dayNight.Override = 0.5f;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
        }

        Vector2 OnSurface(float x, Species s)
        {
            int tx = Mathf.FloorToInt(x);
            return new Vector2(tx + 0.5f, side.terrain.TopSolidY(tx) + 1f + SpeciesSpec.Get(s).size.y * 0.5f + 0.05f);
        }

        [UnityTest]
        public IEnumerator AFleeingStagAtTheCampCratesTurnsAndKeepsMoving()
        {
            yield return Boot();
            // The crate stack sits a few metres left of the spawn; a stag between it and the surveyor flees left into it.
            float px = player.Body.position.x;
            var stag = creatures.Spawn(Species.Stag, OnSurface(px - 4f, Species.Stag));
            Assert.NotNull(stag);
            for (int i = 0; i < 300 && stag.Held; i++) yield return new WaitForFixedUpdate();
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(CreatureState.Flee, stag.State, "flees the surveyor");
            // Watch 3 s: it must never stand still for more than 0.5 s while fleeing.
            float still = 0f, worst = 0f, moved = 0f;
            Vector2 last = stag.Body.position;
            int turns = 0, dirLast = Mathf.Abs(stag.Body.linearVelocity.x) > 0.1f ? (int)Mathf.Sign(stag.Body.linearVelocity.x) : 0;
            for (float t = 0f; t < 3f; t += Time.fixedDeltaTime)
            {
                yield return new WaitForFixedUpdate();
                float vx = stag.Body.linearVelocity.x;
                still = Mathf.Abs(vx) < 0.2f ? still + Time.fixedDeltaTime : 0f;
                worst = Mathf.Max(worst, still);
                moved += Vector2.Distance(stag.Body.position, last);
                last = stag.Body.position;
                int dir = Mathf.Abs(vx) > 0.1f ? (int)Mathf.Sign(vx) : dirLast;
                if (dir != dirLast && dirLast != 0) turns++;
                dirLast = dir;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] fleeing stag at the crates: longest standstill {worst:F2} s, moved {moved:F1} m, turns {turns}");
            Assert.LessOrEqual(worst, 0.5f, "turns or hops within 0.5 s of a wall");
            Assert.Greater(moved, 6f, "keeps moving");
            creatures.Despawn(stag);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AChasingWolfBlockedByATwoTileWallWaitsWithAStillIdle()
        {
            yield return Boot();
            // Open ground 40 m east of the camp: a 2-tile stone wall between the surveyor and a wolf.
            int ptx = Mathf.FloorToInt(player.Body.position.x) + 40;
            var feet = new Vector2(ptx + 0.5f, side.terrain.TopSolidY(ptx) + 1.05f);
            player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero;
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            int wx = ptx + 4;
            int top = side.terrain.TopSolidY(wx);
            Assert.IsTrue(side.terrain.SetTile(wx, top + 1, TileId.Stone) && side.terrain.SetTile(wx, top + 2, TileId.Stone), "a 2-tile wall");
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            var wolf = creatures.Spawn(Species.GreyWolf, OnSurface(ptx + 8f, Species.GreyWolf));
            Assert.NotNull(wolf);
            for (int i = 0; i < 300 && wolf.Held; i++) yield return new WaitForFixedUpdate();
            // It runs at the wall, then waits.
            until = Time.realtimeSinceStartup + 4f;
            while (wolf.Body.position.x > wx + 1.6f && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
            Assert.AreEqual(CreatureState.Chase, wolf.State, "chasing");
            for (int i = 0; i < 40; i++) yield return new WaitForFixedUpdate(); // settles at the wall
            float x0 = wolf.Body.position.x;
            int before = player.BumpCount;
            for (int i = 0; i < 100; i++) yield return new WaitForFixedUpdate(); // 2 s
            TestContext.Out.WriteLine($"[MERIDIAN] blocked wolf: x {x0:F2} -> {wolf.Body.position.x:F2}, vx {wolf.Body.linearVelocity.x:F2}, pick {wolf.LastPick}, state {wolf.State}");
            Assert.AreEqual(x0, wolf.Body.position.x, 0.3f, "stays put at the wall");
            Assert.Less(Mathf.Abs(wolf.Body.linearVelocity.x), 0.2f, "not running on the spot");
            Assert.AreEqual(0, wolf.LastPick, "a still idle, not walking legs");
            Assert.Greater(wolf.Body.position.x, wx + 0.5f, "on its side of the wall");
            Assert.AreEqual(before, player.BumpCount, "never bumps through the wall");
            creatures.Despawn(wolf);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
