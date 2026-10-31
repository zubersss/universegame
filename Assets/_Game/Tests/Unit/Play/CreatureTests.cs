using System.Collections;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Player;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-027 (PlayMode): stag flees within 8 m, wolf packs only at night, no creature falls through streamed chunks, AI ≤ 0.5 ms with 20.</summary>
    public class CreatureTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        CreatureDirector creatures;
        PlayerController player;

        IEnumerator BootEarth()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            creatures = side.creatures;
            Assert.NotNull(creatures, "CreatureDirector on PlanetSide");
            Assert.IsFalse(creatures.autoSpawn, "batch runs don't spawn on their own");
            player = side.player;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate(); // player settles
            var vitals = player.GetComponent<PlayerVitals>();
            vitals.maxHealth = vitals.health = 1e6f; // bites must not end the test
        }

        Vector2 OnSurface(float x, Species s)
        {
            int tx = Mathf.FloorToInt(x);
            int surface = side.terrain.TopSolidY(tx);
            return new Vector2(tx + 0.5f, surface + 1f + SpeciesSpec.Get(s).size.y * 0.5f + 0.05f);
        }

        [UnityTest]
        public IEnumerator StagFleesWithin8Metres()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.5f;
            float px = player.transform.position.x;
            var near = creatures.Spawn(Species.Stag, OnSurface(px + 7f, Species.Stag)); // tile-snapped: 6.5–7.5 m away
            var far = creatures.Spawn(Species.Stag, OnSurface(px - 10f, Species.Stag));
            // A chunk still being rebuilt holds its creatures (no thinking): start the clock once both are free.
            for (int i = 0; i < 300 && (near.Held || far.Held); i++) yield return new WaitForFixedUpdate();
            for (int i = 0; i < 40; i++) yield return new WaitForFixedUpdate();
            string where = $"near held {near.Held} at {Mathf.Abs(near.Body.position.x - player.Body.position.x):F1} m, far held {far.Held} at {Mathf.Abs(far.Body.position.x - player.Body.position.x):F1} m";
            Assert.AreEqual(CreatureState.Flee, near.State, "inside 8 m: flees (" + where + ")");
            Assert.AreNotEqual(CreatureState.Flee, far.State, "10 m: doesn't");
            float d0 = Mathf.Abs(near.Body.position.x - player.Body.position.x);
            Assert.Greater(near.Body.linearVelocity.x, 1f, "runs away (player is to its left)");
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            float d1 = Mathf.Abs(near.Body.position.x - player.Body.position.x);
            TestContext.Out.WriteLine($"[MERIDIAN] stag: {d0:F1} m → {d1:F1} m in 1.2 s");
            Assert.Greater(d1, d0 + 3f, "distance opens");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator WolfPacksSpawnOnlyAtNight()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.5f; // noon
            yield return null;
            for (int i = 0; i < 300; i++) creatures.SpawnTick();
            Assert.AreEqual(0, creatures.CountOf(Species.GreyWolf), "no wolves by day");
            Assert.Greater(creatures.CountOf(Species.Stag), 0, "stags by day (the spawner works)");
            creatures.DespawnAll();

            side.dayNight.Override = 0.0f; // midnight
            yield return null;
            for (int i = 0; i < 300 && creatures.CountOf(Species.GreyWolf) < 2; i++) creatures.SpawnTick();
            int wolves = creatures.CountOf(Species.GreyWolf);
            TestContext.Out.WriteLine($"[MERIDIAN] wolves at midnight: {wolves}");
            Assert.GreaterOrEqual(wolves, 2, "a pack at night");

            side.dayNight.Override = 0.5f; // dawn comes: off-screen wolves leave
            for (int i = 0; i < 10; i++) yield return null;
            foreach (var c in creatures.All)
                if (c.Alive && c.Spec.id == Species.GreyWolf)
                    Assert.Less(Mathf.Abs(c.Body.position.x - player.Body.position.x), 22f, "only on-screen wolves stay after dawn");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator CreaturesNeverFallThroughStreamedChunks()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.5f;
            float px = player.transform.position.x;
            var spawned = new List<Creature>();
            for (int i = 0; i < CreatureDirector.MaxCreatures; i++)
            {
                float x = px - 50f + i * 5f + (i % 2) * 0.3f;
                if (Mathf.Abs(x - px) < 10f) x += 20f; // keep them calm (outside flee range)
                var c = creatures.Spawn(Species.Stag, OnSurface(x, Species.Stag));
                Assert.NotNull(c);
                spawned.Add(c);
            }
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();

            // Send the streaming focus 300 m away: the creatures' chunks unload; then come back.
            var cam = side.sideCamera;
            cam.GetComponent<CameraFollow>().enabled = false;
            var home = cam.transform.position;
            cam.transform.position = home + new Vector3(300f, 0f, 0f);
            float until = Time.realtimeSinceStartup + 10f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            int held = 0;
            foreach (var c in spawned) if (c.Alive && c.Held) held++;
            Assert.Greater(held, 0, "creatures without loaded ground are held");

            cam.transform.position = home;
            yield return null;
            until = Time.realtimeSinceStartup + 10f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 120; i++) yield return new WaitForFixedUpdate();

            int checkedCount = 0;
            foreach (var c in spawned)
            {
                if (!c.Alive) continue;
                checkedCount++;
                Assert.IsFalse(c.Held, $"{c.name} released when its ground is back");
                var p = c.Body.position;
                int surface = side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(Mathf.FloorToInt(p.x)));
                float feet = p.y - c.Spec.size.y * 0.5f;
                Assert.GreaterOrEqual(feet, surface + 1f - 0.25f, $"{c.name} at x {p.x:F1} stands on the ground (feet {feet:F2}, surface top {surface + 1})");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] {checkedCount} creatures checked after the round trip, {held} were held while away");
            Assert.Greater(checkedCount, 10);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AiTakesAtMostHalfAMillisecondWith20Creatures()
        {
            yield return BootEarth();
            side.dayNight.Override = 0.0f; // night: wolves hunt, stags flee
            float px = player.transform.position.x;
            for (int i = 0; i < CreatureDirector.MaxCreatures; i++)
            {
                var s = i % 2 == 0 ? Species.Stag : Species.GreyWolf;
                Assert.NotNull(creatures.Spawn(s, OnSurface(px - 18f + i * 1.9f, s)));
            }
            Assert.AreEqual(CreatureDirector.MaxCreatures, creatures.AliveCount);
            Assert.IsNull(creatures.Spawn(Species.Stag, OnSurface(px, Species.Stag)), "20 is the cap");
            for (int i = 0; i < 30; i++) yield return null; // warm
            var samples = new List<double>(300);
            for (int i = 0; i < 300; i++) { yield return null; samples.Add(creatures.LastAiMs); }
            samples.Sort();
            double avg = 0; foreach (var s in samples) avg += s; avg /= samples.Count;
            double p99 = samples[(int)(samples.Count * 0.99) - 1], max = samples[samples.Count - 1];
            TestContext.Out.WriteLine($"[MERIDIAN] AI with 20 creatures: avg {avg:F3} ms, p99 {p99:F3} ms, max {max:F3} ms");
            Assert.LessOrEqual(max, 0.5, "≤ 0.5 ms AI in every frame (board U-027)");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
