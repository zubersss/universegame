using System.Collections;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Player;
using Meridian.Rig;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-174 (D-174, Bible 5.2 §8.1) on Earth: the Surface Line 2 m under the drawn surface and topside toggling at it (the Sell panel refuses
    /// below it); a held Beam stroke takes the table's time at T1 and at T5 with Beam power 1 and 4 (a tier-5 stroke possible with the
    /// starting Beam); dug tiles fill the dirt store; a loaded pack slows the jetpack's climb.
    /// </summary>
    public class DigRunPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;
        TerrainStreamer t;

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            player = side.player;
            t = side.terrain;
            player.externalInput = true; player.intent = default;
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();
            Assert.IsTrue(t.SmoothGround);
            GameState.Instance.inventory.ReadFrom(new System.Collections.Generic.List<ItemStack>(), 0);
            GameState.Instance.dirt.count = 0;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
        }

        /// <summary>The surveyor held still in a dug pocket `depth` m under the Surface Line at x (a 3 × 3 m hollow), its feet on the floor.</summary>
        IEnumerator StandAtDepth(float x, float depth)
        {
            float floorY = DigRun.LineAt(t, x) - depth;
            int fx = Mathf.FloorToInt(x), fy = Mathf.FloorToInt(floorY);
            var b = player.Body;
            b.simulated = false;
            b.position = new Vector2(fx + 0.5f, fy + 1.05f); player.transform.position = b.position;
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int c = fx - 1; c <= fx + 1; c++) for (int y = fy; y <= fy + 2; y++) t.SetTile(c, y, TileId.Air);
            yield return new WaitForFixedUpdate();
            b.position = new Vector2(fx + 0.5f, fy + 0.05f); player.transform.position = b.position;
            b.linearVelocity = Vector2.zero;
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator TheSurfaceLineTopsideAndTheStrokeTimes()
        {
            yield return Boot();
            float x = player.Body.position.x;
            float line = DigRun.LineAt(t, x);
            Assert.AreEqual(t.SurfaceAt(x) - 2f, line, 1e-4f, "the Surface Line 2 m under the drawn surface");
            Assert.IsTrue(DigRun.Topside(t, new Vector2(x, line + 0.1f)), "just over the line: topside");
            Assert.IsFalse(DigRun.Topside(t, new Vector2(x, line - 0.1f)), "just under it: not");
            Assert.AreEqual(12f, DigRun.Depth(t, new Vector2(x, line - 12f)), 1e-4f, "depth counts from 0 at the line");
            Assert.AreEqual(1, DigRun.TierAt(t, new Vector2(x, line - 12f)), "12 m down: T2");
            var sell = side.sideHud.Sell;
            Assert.NotNull(sell, "the Sell panel on the HUD");
            Assert.IsTrue(sell.Topside, "the surveyor at the camp is topside");

            var input = player.GetComponent<PlayerRigInput>();
            var rig = side.rig;
            int spot = 0;
            foreach (var (depth, power) in new[] { (5f, 1f), (5f, 4f), (215f, 1f), (215f, 4f) })
            {
                yield return StandAtDepth(x + 40f + 12f * spot++, depth); // a fresh wall each time
                Assert.IsFalse(sell.Topside, $"{depth} m down: not topside");
                rig.BeamPower = power;
                var feet = player.Body.position;
                var target = new Vector2(Mathf.Floor(feet.x) + 2.5f, Mathf.Floor(feet.y) + 0.5f); // the wall beside the hollow
                float expect = D1Tables.Current.StrokeSeconds(Meridian.Planets.PlanetId.Earth, DigRun.Depth(t, target), power);
                int dirt0 = GameState.Instance.dirt.count;
                input.module = RigModule.Beam;
                input.AimAt(target);
                input.holdUse = true;
                float t0 = Time.time, dugAt = -1f;
                int solid0 = CountSolid(target);
                while (Time.time - t0 < expect + 2f && dugAt < 0f)
                {
                    yield return null;
                    if (CountSolid(target) < solid0) dugAt = Time.time - t0;
                }
                input.holdUse = false;
                yield return null;
                TestContext.Out.WriteLine($"[MERIDIAN] u174 stroke at {depth} m (T{DigRun.TierAt(t, target) + 1}), power {power}: expected {expect:F2} s, dug after {dugAt:F2} s; dirt +{GameState.Instance.dirt.count - dirt0}");
                Assert.Greater(dugAt, 0f, $"{depth} m, power {power}: the held Beam digs");
                Assert.AreEqual(expect, dugAt, 0.15f + expect * 0.05f, $"{depth} m, power {power}: the stroke takes the table's time");
                Assert.LessOrEqual(dugAt, D1Tables.Current.strokeCapSeconds + 0.2f, "never past the cap");
            }
            rig.BeamPower = D1Tables.Current.beamPowerStart;
            Assert.Greater(GameState.Instance.dirt.count, 0, "dug tiles fill the dirt store");
            // The Surface Line draws in the cutaway while the camera is below the surface (the camera follows the surveyor down).
            var follow = side.sideCamera.GetComponent<CameraFollow>();
            if (follow != null) { follow.enabled = true; follow.SnapToTarget(); }
            for (int i = 0; i < 10; i++) yield return null;
            var lineView = side.cartoon.SurfaceLine;
            Assert.NotNull(lineView, "the Surface Line's view on the smooth ground");
            TestContext.Out.WriteLine($"[MERIDIAN] u174 the Surface Line below: showing {lineView.Showing}, {lineView.Placed} tiles");
            Assert.IsTrue(lineView.Showing && lineView.Placed > 0, "the Surface Line draws with the camera below the surface");
            Assert.AreEqual(-1, DigRun.SellPack(GameState.Instance, sell.Topside, false), "the Sell refuses below the line");
            LogAssert.NoUnexpectedReceived();
        }

        int CountSolid(Vector2 p)
        {
            int n = 0;
            for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++) if (TileId.IsSolid(t.GetTile(Mathf.FloorToInt(p.x) + dx, Mathf.FloorToInt(p.y) + dy))) n++;
            return n;
        }

        [UnityTest, Timeout(180000)]
        public IEnumerator ALoadedPackSlowsTheJetpackClimb()
        {
            yield return Boot();
            int iron = ItemRegistry.Get("iron").id;
            float empty = 0f, loaded = 0f;
            foreach (bool full in new[] { false, true })
            {
                var inv = GameState.Instance.inventory;
                inv.ReadFrom(new System.Collections.Generic.List<ItemStack>(), 0);
                if (full) Assert.AreEqual(0, inv.Add(iron, 15), "30 kg of iron in the pack");
                yield return new WaitForSeconds(0.5f);
                float y0 = player.Body.position.y;
                player.intent = new PlayerIntent { jumpHeld = true };
                player.PressJump();
                for (int i = 0; i < 75; i++) yield return new WaitForFixedUpdate(); // 1.5 s: the jump, then the jetpack
                float rise = player.Body.position.y - y0;
                player.intent = default;
                for (int i = 0; i < 150 && !player.Grounded; i++) yield return new WaitForFixedUpdate();
                if (full) loaded = rise; else empty = rise;
                TestContext.Out.WriteLine($"[MERIDIAN] u174 jetpack 1.5 s with {(full ? "30 kg (load factor " + player.LoadFactor.ToString("F2") + ")" : "an empty pack")}: rose {rise:F2} m");
            }
            Assert.Less(loaded, empty * 0.9f, "a full pack climbs slower");
            GameState.Instance.inventory.ReadFrom(new System.Collections.Generic.List<ItemStack>(), 0);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
