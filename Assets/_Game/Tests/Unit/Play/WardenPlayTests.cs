using System.Collections;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Creatures.Wardens;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Rig;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-053 (PlayMode): digging past the threshold near the Mercury Warden vault calls a sentinel within 10 s;
    /// its bolts come off the suit; the Lance destroys it; six hunting sentinels cost ≤ 0.3 ms of AI (D-047: median and p99).
    /// </summary>
    public class WardenPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const float AiBudgetMs = 0.3f;

        [UnityTest]
        public IEnumerator OverMiningAtTheVaultCallsASentinel()
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
            var wardens = side.wardens;
            Assert.NotNull(wardens, "WardenDirector on PlanetSide");
            side.hazards.enabled = false; // only the bolts touch the suit here
            side.hazards.RestoreSuit();

            // The vault's patrol.
            for (int i = 0; i < 10; i++) yield return null;
            Assert.AreEqual(1, wardens.Active, "one sentinel patrols the vault");
            var patrol = wardens.sentinels.Find(s => s.Alive);
            Assert.AreEqual(SentinelState.Patrol, patrol.State);

            // Stand 20 m from the vault and dig 15 tiles beside the surveyor (the guarded threshold).
            float vaultX = PoiCatalog.WardenVault.CenterX;
            int x = Mathf.FloorToInt(vaultX) + 20;
            var player = side.player;
            var feet = new Vector2(x + 0.5f, side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(x)) + 1.05f);
            player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero;
            yield return null;
            timeout = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(wardens.meter.IsGuarded(x));
            int dug = 0;
            for (int dx = 3; dx <= 8 && dug < WardenMeter.GuardedThreshold; dx++)
            {
                int top = side.terrain.TopSolidY(x + dx);
                for (int y = top; y > top - 4 && dug < WardenMeter.GuardedThreshold; y--)
                    if (TileId.IsSolid(side.terrain.GetTile(x + dx, y)) && side.terrain.SetTile(x + dx, y, TileId.Air)) dug++;
            }
            Assert.AreEqual((int)WardenMeter.GuardedThreshold, dug);
            Assert.AreEqual(1, wardens.Trips, "the area tripped");
            float tripped = Time.time;

            // A sentinel arrives within 10 s, and the patrol wakes.
            Sentinel hunter = null;
            while (hunter == null && Time.time - tripped < 10f)
            {
                hunter = wardens.sentinels.Find(s => s.Alive && s != patrol && s.State == SentinelState.Hunt);
                yield return null;
            }
            Assert.NotNull(hunter, "a sentinel within 10 s");
            TestContext.Out.WriteLine($"[MERIDIAN] sentinel after {Time.time - tripped:F1} s");
            Assert.AreEqual(SentinelState.Hunt, patrol.State, "the vault patrol joins the hunt");

            // Its bolts come off the suit.
            float suit0 = side.hazards.SuitIntegrity, health0 = player.GetComponent<Meridian.Player.PlayerVitals>().health;
            float until = Time.time + 12f;
            while (side.hazards.SuitIntegrity >= suit0 && Time.time < until) yield return null;
            Assert.Less(side.hazards.SuitIntegrity, suit0, "a bolt hit the suit");
            Assert.AreEqual(health0, player.GetComponent<Meridian.Player.PlayerVitals>().health, "the suit takes it first");

            // The Lance brings it down: three bolts of 25.
            var lance = Object.FindAnyObjectByType<LanceBolts>();
            Assert.NotNull(lance);
            int destroyed = 0;
            System.Action<Sentinel> count = s => { if (s == hunter) destroyed++; };
            Sentinel.Destroyed += count;
            until = Time.time + 10f;
            while (hunter.Alive && Time.time < until)
            {
                var at = hunter.Body.position;
                lance.Fire(at + new Vector2(-1.5f, 0f), Vector2.right);
                for (int i = 0; i < 4; i++) yield return new WaitForFixedUpdate();
            }
            Sentinel.Destroyed -= count;
            Assert.IsFalse(hunter.Alive, "the Lance destroyed it");
            Assert.AreEqual(1, destroyed);
            yield return new WaitForSeconds(Sentinel.DeathSeconds + 0.1f);
            Assert.IsFalse(hunter.gameObject.activeSelf, "gone after its death animation");

            // Budget: six hunting sentinels.
            while (wardens.Active < WardenDirector.MaxSentinels)
                Assert.NotNull(wardens.Spawn(player.Body.position + new Vector2(wardens.Active * 2f - 6f, 8f), player.Body.position, SentinelState.Hunt));
            Assert.IsNull(wardens.Spawn(Vector2.zero, Vector2.zero, SentinelState.Hunt), "pool of six");
            var samples = new List<float>();
            for (int i = 0; i < 30; i++) yield return null; // warm-up
            for (int i = 0; i < 240; i++) { yield return null; samples.Add(wardens.LastAiMs); }
            samples.Sort();
            float median = samples[samples.Count / 2], p99 = samples[Mathf.FloorToInt(samples.Count * 0.99f)], worst = samples[samples.Count - 1];
            TestContext.Out.WriteLine($"[MERIDIAN] Warden AI with 6 sentinels: median {median:F3} ms, p99 {p99:F3} ms, worst {worst:F3} ms");
            Assert.LessOrEqual(median, AiBudgetMs, "median");
            Assert.LessOrEqual(p99, AiBudgetMs, "p99");
            if (worst > AiBudgetMs) Assert.LessOrEqual(worst, 2f * AiBudgetMs, "a single frame up to 2× is logged, not failed (D-047)");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
