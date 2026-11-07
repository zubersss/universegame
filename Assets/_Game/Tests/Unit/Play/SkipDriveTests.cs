using System.Collections;
using Meridian.Core;
using Meridian.Items;
using Meridian.Space;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-063, U-107 (PlayMode, D-105): Earth → Neptune at skip speed; refuses inside a well; consumes nothing (no skip
    /// fuel of any kind); after a skip the drive cools down for 10 s before it spools again.
    /// </summary>
    public class SkipDriveTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator EarthToNeptuneInElevenSeconds()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            director.SetView(ViewMode.Space);
            for (int i = 0; i < 10; i++) yield return null;
            var ship = director.Space.GetComponentInChildren<SpaceShip>();
            var drive = ship.GetComponent<SkipDrive>();
            Assert.NotNull(drive, "SkipDrive on the ship");
            ship.externalInput = true;
            ship.intent = default;
            while (ship.Invulnerable) yield return null;
            var state = GameState.Instance;
            state.inventory.Clear();

            // Inside Earth's well: no spool.
            var earth = ship.world.Find("earth").Value;
            ship.Position = earth.position + new Vector2(0f, earth.WellRadius * 0.5f);
            ship.Velocity = Vector2.zero;
            state.inventory.Add(ItemRegistry.Get("helium3_condensate").id, 3); // a crafting ingredient now: the drive never touches it
            drive.holdOverride = true;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(SkipDrive.Mode.Idle, drive.Current, "refuses inside a gravity well");
            StringAssert.Contains("GRAVITY WELL", drive.Refusal);

            // Outside the well, nose on Neptune: spool 3 s, then skip.
            var neptune = ship.world.Find("neptune").Value;
            var start = earth.position + (neptune.position - earth.position).normalized * (earth.WellRadius + 5f);
            ship.Position = start;
            ship.Velocity = Vector2.zero;
            var to = neptune.position - start;
            ship.Heading = Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg;
            yield return new WaitForFixedUpdate();
            Assert.AreEqual(SkipDrive.Mode.Spooling, drive.Current, "spooling");
            yield return new WaitForSeconds(1.5f);
            Assert.AreEqual(0.5f, drive.Spool, 0.1f, "half spooled after 1.5 s");
            float until = Time.time + SkipDrive.SpoolSeconds + 1f;
            while (drive.Current != SkipDrive.Mode.Skipping && Time.time < until) yield return new WaitForFixedUpdate();
            Assert.AreEqual(SkipDrive.Mode.Skipping, drive.Current, "skipping after the spool");
            float t0 = Time.time;
            int he3Before = state.inventory.Count(ItemRegistry.Get("helium3_condensate").id);
            until = t0 + 30f;
            while (drive.Current == SkipDrive.Mode.Skipping && Time.time < until) yield return new WaitForFixedUpdate();
            float skipSeconds = Time.time - t0;
            float left = Vector2.Distance(ship.Position, neptune.position);
            TestContext.Out.WriteLine($"[MERIDIAN] skip Earth → Neptune: {skipSeconds:F1} s, stopped by {(ship.InWellOf ?? "-")}, {left:F0} u from Neptune");
            Assert.AreEqual("neptune", ship.InWellOf, "dropped out of skip at Neptune's well");
            // Bible §3: 1,200 u/s; its "≈ 11 s" assumes Earth and Neptune in line. With the fixed angles of
            // SpaceLayout (P-13: Neptune 110° from Earth) the run is longer (≈ 13.2 s), see P-25.
            float expected = (Vector2.Distance(start, neptune.position) - neptune.WellRadius) / SkipDrive.Speed;
            Assert.AreEqual(expected, skipSeconds, 0.5f, $"skip at {SkipDrive.Speed} u/s over the layout's distance");
            Assert.LessOrEqual(ship.Velocity.magnitude, SpaceLayout.CruiseSpeed + 1f, "back to cruise speed");
            Assert.AreEqual(he3Before, state.inventory.Count(ItemRegistry.Get("helium3_condensate").id), "the skip consumed nothing");

            // Cool-down: out of every well again, J held, the drive refuses for 10 s.
            Assert.AreEqual(SkipDrive.CooldownSeconds, drive.Cooldown, 0.5f, "a 10 s cool-down after the skip");
            ship.Position = start; ship.Velocity = Vector2.zero;
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(SkipDrive.Mode.Idle, drive.Current, "no spool while cooling");
            StringAssert.Contains("COOLING", drive.Refusal);
            until = Time.time + SkipDrive.CooldownSeconds + 1f;
            while (drive.Current == SkipDrive.Mode.Idle && Time.time < until) yield return new WaitForFixedUpdate();
            Assert.AreEqual(SkipDrive.Mode.Spooling, drive.Current, "spools again once cool");
            drive.holdOverride = false;
            LogAssert.NoUnexpectedReceived();
        }
    }
}
