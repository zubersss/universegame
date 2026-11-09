using System.Collections;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Progress;
using Meridian.Rig;
using Meridian.Save;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests.LeadQA
{
    /// <summary>
    /// L-014: the D1 exit scenario (D-174, Bible 5.3 §8.1, docs/D1_TABLES.md). On Earth, one first dig run end to end:
    /// topside at the camp; a held Beam stroke at tier 1 and at tier 3 takes the tables' time; the pack refuses past its limit;
    /// a full pack climbs out of a shaft above the Surface Line by the jetpack; selling topside pays the tables' Scrip and counts
    /// toward the Surveyor Rank; a ring-1 node bought raises its stat; save and load keep the pack, Scrip, nodes and Rank.
    /// Written by LEAD against the D1 APIs; the ladder step (6b) uses U-176's Ladders.Place and the Climb intent.
    /// </summary>
    public class D1DigRunTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string saveRoot;
        PlanetSideRoot side;
        PlayerController player;
        TerrainStreamer t;

        [SetUp]
        public void SetUp()
        {
            saveRoot = System.IO.Path.Combine(Application.temporaryCachePath, "meridian_leadqa_d1_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = saveRoot;
        }

        [TearDown]
        public void TearDown()
        {
            SaveSystem.RootOverride = null;
            if (System.IO.Directory.Exists(saveRoot)) System.IO.Directory.Delete(saveRoot, true);
        }

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady, "boot");
            side = director.PlanetSide;
            player = side.player;
            t = side.terrain;
            player.externalInput = true; player.intent = default;
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();
            Assert.IsTrue(t.SmoothGround, "Earth on smooth ground");
            GameState.Instance.inventory.ReadFrom(new System.Collections.Generic.List<ItemStack>(), 0);
            GameState.Instance.dirt.count = 0;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
        }

        /// <summary>The surveyor held in a dug 3 × 3 m hollow whose floor is `depth` m under the Surface Line at x.</summary>
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

        /// <summary>A held Beam stroke at the wall beside the surveyor; returns the seconds until the wall opened (-1 if it never did).</summary>
        IEnumerator HeldStroke(System.Action<float, float> done)
        {
            var input = player.GetComponent<PlayerRigInput>();
            var feet = player.Body.position;
            var target = new Vector2(Mathf.Floor(feet.x) + 2.5f, Mathf.Floor(feet.y) + 0.5f);
            float expect = D1Tables.Current.StrokeSeconds(PlanetId.Earth, DigRun.Depth(t, target), SkillStats.BeamPower);
            int solid0 = CountSolid(target);
            input.module = RigModule.Beam;
            input.AimAt(target);
            input.holdUse = true;
            float t0 = Time.time, dugAt = -1f;
            while (Time.time - t0 < expect + 2f && dugAt < 0f)
            {
                yield return null;
                if (CountSolid(target) < solid0) dugAt = Time.time - t0;
            }
            input.holdUse = false;
            yield return null;
            done(expect, dugAt);
        }

        int CountSolid(Vector2 p)
        {
            int n = 0;
            for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++) if (TileId.IsSolid(t.GetTile(Mathf.FloorToInt(p.x) + dx, Mathf.FloorToInt(p.y) + dy))) n++;
            return n;
        }

        [UnityTest, Timeout(600000)]
        public IEnumerator AFirstDigRunEndToEnd()
        {
            yield return Boot();
            var state = GameState.Instance;
            var sell = side.sideHud.Sell;
            float camp = player.Body.position.x;
            int scrip0 = state.scrip, earned0 = state.scripEarned;
            Assert.IsTrue(sell.Topside, "1. at the camp: topside");

            // 2. Held strokes at tier 1 (5 m) and tier 3 (55 m) take the tables' time at the starting Beam.
            foreach (float depth in new[] { 5f, 55f })
            {
                yield return StandAtDepth(camp + 40f + depth, depth);
                Assert.IsFalse(sell.Topside, $"2. {depth} m down: not topside");
                float expect = 0f, dugAt = -1f;
                yield return HeldStroke((e, d) => { expect = e; dugAt = d; });
                TestContext.Out.WriteLine($"[LEADQA] D1 stroke at {depth} m (T{DigRun.TierAt(t, player.Body.position) + 1}): expected {expect:F2} s, dug after {dugAt:F2} s");
                Assert.Greater(dugAt, 0f, $"2. {depth} m: the held Beam digs");
                Assert.AreEqual(expect, dugAt, 0.15f + expect * 0.05f, $"2. {depth} m: the stroke takes the tables' time");
            }
            Assert.Greater(state.dirt.count, 0, "2. dug tiles fill the dirt store");

            // 3. The pack refuses past its limit.
            var inv = state.inventory;
            int iron = ItemRegistry.Get("iron").id;
            int fits = inv.FitsByWeight(iron);
            Assert.Greater(fits, 0, "3. an empty pack takes iron");
            Assert.AreEqual(0, inv.Add(iron, fits), "3. the pack fills to its limit");
            Assert.AreEqual(0, inv.FitsByWeight(iron), "3. a full pack fits no more iron");
            Assert.Greater(inv.Add(iron, 1), 0, "3. a full pack refuses the next piece");
            TestContext.Out.WriteLine($"[LEADQA] D1 pack full: {fits} iron, {inv.Weight:F1} kg of {SkillStats.PackKg:F0}; load factor {player.LoadFactor:F2}");

            // 4. A full pack climbs out of a 6 m shaft above the Surface Line by the jetpack.
            float sx = camp - 60f;
            float line = DigRun.LineAt(t, sx);
            int bottom = Mathf.FloorToInt(line - 6f);
            yield return StandAtDepth(sx, 6f);
            for (int c = Mathf.FloorToInt(sx) - 1; c <= Mathf.FloorToInt(sx) + 1; c++)
                for (int y = bottom; y <= Mathf.CeilToInt(t.SurfaceAt(sx)) + 2; y++) t.SetTile(c, y, TileId.Air);
            yield return new WaitForFixedUpdate();
            player.Body.simulated = true;
            Assert.IsFalse(sell.Topside, "4. at the shaft's foot: not topside");
            float t0 = Time.time;
            player.intent = new PlayerIntent { jumpHeld = true };
            player.PressJump();
            while (!sell.Topside && Time.time - t0 < 12f) yield return new WaitForFixedUpdate();
            float climb = Time.time - t0;
            player.intent = default;
            for (int i = 0; i < 200 && !player.Grounded; i++) yield return new WaitForFixedUpdate();
            TestContext.Out.WriteLine($"[LEADQA] D1 jetpack climb out of 6 m with a full pack: {climb:F2} s");
            Assert.IsTrue(sell.Topside, "4. the full pack reached topside by the jetpack");

            // 5. Selling topside pays the tables' Scrip and counts toward the Rank.
            int value = DigRun.PackValue(inv, false);
            int paid = DigRun.SellPack(state, sell.Topside, false);
            Assert.AreEqual(value, paid, "5. the sale pays the pack's table value");
            Assert.AreEqual(scrip0 + paid, state.scrip, "5. the Scrip rises by the sale");
            Assert.AreEqual(earned0 + paid, state.scripEarned, "5. the sale counts as earned this expedition");
            Assert.AreEqual(0f, inv.Weight, 0.001f, "5. the pack is empty after the sale");
            int rank = D1Tables.Current.Rank(state.scripEarned);
            TestContext.Out.WriteLine($"[LEADQA] D1 sold for {paid} Scrip; purse {state.scrip}; earned {state.scripEarned}; Rank {rank}");

            // 6. A ring-1 node bought topside raises its stat.
            var tree = SkillTree.Load();
            float power0 = SkillStats.BeamPower;
            Assert.AreEqual(SkillTree.BuyResult.NotTopside, tree.CanBuy(state, "dig_power_1", false), "6. no buying below the line");
            Assert.AreEqual(SkillTree.BuyResult.Ok, tree.Buy(state, "dig_power_1", true), "6. dig_power_1 bought topside");
            Assert.AreEqual(power0 + 0.5f, SkillStats.BeamPower, 1e-4f, "6. Beam power +0.5");

            // 6b. Ladders (U-176): bought topside, built from the dirt store up a 6 m shaft, climbed out above the Surface Line.
            Assert.AreEqual(SkillTree.BuyResult.Ok, tree.Buy(state, "asc_ladder_1", true), "6b. asc_ladder_1 bought topside");
            state.dirt.Add(40);
            float lx = camp - 100f;
            int lbottom = Mathf.FloorToInt(DigRun.LineAt(t, lx) - 6f);
            yield return StandAtDepth(lx, 6f);
            for (int c = Mathf.FloorToInt(lx) - 1; c <= Mathf.FloorToInt(lx) + 1; c++)
                for (int y = lbottom; y <= Mathf.CeilToInt(t.SurfaceAt(lx)) + 2; y++) t.SetTile(c, y, TileId.Air);
            yield return new WaitForFixedUpdate();
            player.Body.simulated = true;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            var ladders = Meridian.Building.Ladders.Instance;
            Assert.NotNull(ladders, "6b. the ladders on the planet");
            int dirtBefore = state.dirt.count, metres = 0;
            Vector2 foot = player.Body.position + new Vector2(0f, 0.5f);
            for (int k = 0; k < 9; k++) metres += ladders.Place(foot); // 6 m to the line, 2 m to the surface, 1 m over it
            TestContext.Out.WriteLine($"[LEADQA] D1 ladder: {metres} m placed for {dirtBefore - state.dirt.count} dirt");
            Assert.GreaterOrEqual(metres, 8, "6b. a ladder from the shaft's foot past the Surface Line");
            Assert.AreEqual(metres * 2, dirtBefore - state.dirt.count, "6b. 2 dirt a metre at asc_ladder_1");
            Assert.IsFalse(sell.Topside, "6b. at the shaft's foot: not topside");
            float l0 = Time.time;
            player.intent = new PlayerIntent { climb = 1f };
            while (!sell.Topside && Time.time - l0 < 20f) yield return new WaitForFixedUpdate();
            float ladderClimb = Time.time - l0;
            player.intent = default;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            TestContext.Out.WriteLine($"[LEADQA] D1 ladder climb out of 6 m (empty pack): {ladderClimb:F2} s");
            Assert.IsTrue(sell.Topside, "6b. the ladder climb reached topside");
            Assert.Less(ladderClimb, 6f / 2.5f + 2f, "6b. about 2.5 m/s up the ladder with an empty pack");
            int scripAfterBuy = state.scrip;

            // 7. Save, disturb, load: the nodes, Scrip, earnings and the stat come back.
            var save = SaveSystem.Instance;
            int copper = ItemRegistry.Get("copper").id;
            Assert.AreEqual(0, inv.Add(copper, 2), "7. two copper in the pack before the save");
            save.Save();
            state.skillNodes.Clear(); state.scrip = 0; state.scripEarned = 0;
            inv.ReadFrom(new System.Collections.Generic.List<ItemStack>(), 0);
            yield return save.Load();
            state = GameState.Instance;
            Assert.IsTrue(state.skillNodes.Contains("dig_power_1"), "7. the bought node survives a load");
            Assert.AreEqual(scripAfterBuy, state.scrip, "7. the Scrip survives a load");
            Assert.AreEqual(earned0 + paid, state.scripEarned, "7. the expedition's earnings survive a load");
            Assert.AreEqual(rank, D1Tables.Current.Rank(state.scripEarned), "7. the Rank survives a load");
            Assert.AreEqual(2, state.inventory.Count(copper), "7. the pack survives a load");
            Assert.AreEqual(power0 + 0.5f, SkillStats.BeamPower, 1e-4f, "7. the node's stat applies after a load");
            Assert.IsTrue(state.skillNodes.Contains("asc_ladder_1"), "7. the ladder node survives a load");
            Assert.Greater(state.ascentPieces.Count, 0, "7. the placed ladder survives a load");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
