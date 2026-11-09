using System.Collections;
using Meridian.Building;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Player;
using Meridian.Progress;
using Meridian.Rig;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-176 (PlayMode; D1_TABLES §4 "Climbing"): the ways back up in a real shaft. A 3 m wide shaft 38 m deep is carved beside the camp; the
    /// surveyor climbs 30 m of it by the Builder's ladder (W held), the Grapple (thrown at the wall, reeled, thrown again) and the winch's line,
    /// with an empty and a full pack, against the tables' times (AscentTests); asc_climb_1 and asc_grapple_2 change theirs by their amounts.
    /// Placement: right click with the Builder fills open cells upward from the aim at the tables' dirt; a mound buries a piece. The recall
    /// beacon lifts the surveyor topside after 5 s, pack kept, one charge a run. Too steep ground slides; asc_climb_1 holds 37.5°.
    /// </summary>
    public class AscentPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const int Depth = 38;
        PlanetSideRoot side;
        PlayerController player;
        PlayerRigInput rig;
        GameState state;
        int x0, yb;
        float surface;

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
            if (side.hazards != null) side.hazards.enabled = false;
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();
            player = side.player;
            rig = player.GetComponent<PlayerRigInput>();
            state = GameState.Instance;
            state.skillNodes.Clear();
            SkillStats.Apply(state);
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
            // the shaft: 3 cells wide, Depth deep under the natural surface, open to the sky
            x0 = Mathf.FloorToInt(player.Body.position.x) + 18;
            surface = side.terrain.SurfaceAt(x0 + 1.5f);
            yb = Mathf.FloorToInt(surface) - Depth;
            for (int y = yb; y <= Mathf.CeilToInt(surface) + 2; y++)
                for (int x = x0; x < x0 + 3; x++) side.terrain.SetTile(x, y, TileId.Air);
            for (int i = 0; i < 10; i++) yield return null;
            player.externalInput = true;
            yield return Bottom();
        }

        void Buy(params string[] ids)
        {
            state.skillNodes.Clear();
            foreach (var id in ids) state.skillNodes.Add(id);
            SkillStats.Apply(state);
        }

        /// <summary>Puts the surveyor on the shaft's floor at its middle, still, holding nothing.</summary>
        IEnumerator Bottom()
        {
            player.LetGo();
            player.intent = default;
            rig.holdUse = false;
            var at = new Vector2(x0 + 1.5f, yb + 0.05f);
            player.Body.position = at; player.transform.position = at; player.Body.linearVelocity = Vector2.zero;
            for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Grounded, "on the shaft's floor");
        }

        /// <summary>Fills the pack to its limit with the tables' first material (load factor ~0.5).</summary>
        void FillPack()
        {
            int id = ItemRegistry.Get(D1Tables.Current.materials[0].item).id;
            state.inventory.Add(id, state.inventory.FitsByWeight(id));
            Assert.Less(player.LoadFactor, 0.55f, "a full pack");
        }

        float Seconds(int steps) => steps * Time.fixedDeltaTime;

        /// <summary>Holds W until the feet are 30 m over the floor (or the cap); returns the seconds.</summary>
        IEnumerator ClimbColumn(System.Action<float> done, int cap = 2400)
        {
            player.intent = new PlayerIntent { climb = 1f };
            int steps = 0;
            while (player.Body.position.y < yb + 30f && steps < cap) { yield return new WaitForFixedUpdate(); steps++; }
            player.intent = default;
            done(Seconds(steps));
        }

        /// <summary>The Grapple: thrown at the shaft's wall as high as the line reaches (under the rim), reeled to the hook, thrown again,
        /// until the feet are 30 m up; returns the seconds.</summary>
        IEnumerator ClimbGrapple(System.Action<float> done, int cap = 2400)
        {
            rig.module = RigModule.Grapple;
            var line = rig.Grapple;
            int steps = 0;
            while (player.Body.position.y < yb + 30f && steps < cap)
            {
                var hands = line.Hands;
                // the far wall (the reel leaves the surveyor against the near one: a throw up that one runs along it)
                float left = WallOf(hands, -1f), right = WallOf(hands, 1f);
                float face = hands.x - left >= right - hands.x ? left : right;
                float dx = Mathf.Abs(hands.x - face);
                float reach = Mathf.Sqrt(Mathf.Max(1f, SkillStats.GrappleM * SkillStats.GrappleM - dx * dx)) - 0.25f;
                float up = Mathf.Min(hands.y + reach, surface - 3f); // well under the rim's rounded corner
                var onWall = new Vector2(face, up);
                rig.AimAt(hands + (onWall - hands) * 1.3f); // through the wall's face at `up`: the hook catches there
                rig.holdUse = true;
                // hold until the reel reaches the hook (or the throw missed)
                int fired = line.Fired;
                while (steps < cap && player.Body.position.y < yb + 30f && (line.Flying || line.Attached && !line.AtHook || line.Fired == fired))
                { yield return new WaitForFixedUpdate(); steps++; }
                if (player.Body.position.y >= yb + 30f) break;
                Assert.IsTrue(line.Attached, $"the hook caught the wall (aim {up - hands.y:0.0} m up at {up - yb:0.0} m, the face at x {face - x0:0.00}, the feet {player.Body.position.y - yb:0.0} m up)");
                rig.holdUse = false; // let go and throw again
                while (line.Attached && steps < cap) { yield return new WaitForFixedUpdate(); steps++; }
            }
            rig.holdUse = false;
            done(Seconds(steps));
        }

        readonly RaycastHit2D[] wallHits = new RaycastHit2D[8];

        /// <summary>The shaft's wall face level with `from` on the side `dirX` (the first terrain collider that way).</summary>
        float WallOf(Vector2 from, float dirX)
        {
            int n = Physics2D.Raycast(from, new Vector2(dirX, 0f), new ContactFilter2D { useTriggers = false }, wallHits, 6f);
            float best = float.MaxValue, x = dirX < 0f ? x0 : x0 + 3;
            for (int i = 0; i < n; i++)
                if (wallHits[i].collider != null && wallHits[i].collider.GetComponentInParent<TerrainChunk>() != null && wallHits[i].distance < best)
                { best = wallHits[i].distance; x = wallHits[i].point.x; }
            return x;
        }

        [UnityTest, Timeout(600000)]
        public IEnumerator EachWayClimbsTheShaftInTheTablesTime()
        {
            yield return Boot();
            float scale = Time.timeScale;
            Time.timeScale = 2f; // simulated seconds are counted in fixed steps: the speed-up only saves wall time
            try
            {
                var ladders = side.ladders;
                Assert.NotNull(ladders, "the ladders on the planet side");
                // ---- the ladder: 30 m placed from the floor up (asc_ladder_1: 1 m at 2 dirt each), climbed with W ----
                Buy("asc_ladder_1");
                state.dirt.capacity = 200; state.dirt.count = 200;
                var reachFrom = ladders.player;
                ladders.player = null; // placed out of reach from the floor (the reach is checked by LadderPlacementTests)
                int metres = 0;
                for (int k = 0; k < 32; k++) metres += ladders.Place(new Vector2(x0 + 1.5f, yb + k + 0.5f));
                ladders.player = reachFrom;
                Assert.AreEqual(32, metres); Assert.AreEqual(200 - 64, state.dirt.count, "2 dirt a metre");
                float tLadder = 0, tLadderFull = 0, tLadderClimb = 0;
                yield return ClimbColumn(t => tLadder = t);
                Assert.AreEqual(ClimbKind.Ladder, player.ClimbingOn, "still on the ladder at 30 m");
                yield return Bottom();
                FillPack();
                float lf = player.LoadFactor;
                yield return ClimbColumn(t => tLadderFull = t);
                state.inventory.Clear();
                yield return Bottom();
                Buy("asc_ladder_1", "asc_climb_1");
                yield return ClimbColumn(t => tLadderClimb = t);
                yield return Bottom();
                TestContext.Out.WriteLine($"[MERIDIAN] u176 ladder 30 m: {tLadder:0.00} s empty, {tLadderFull:0.00} s full (load {lf:0.00}), {tLadderClimb:0.00} s with asc_climb_1");
                Assert.AreEqual(12f, tLadder, 0.4f, "ladder, empty: 12 s");
                Assert.AreEqual(30f / (2.5f * lf), tLadderFull, 0.6f, "ladder, full: ~24 s");
                Assert.AreEqual(30f / (2.5f * 1.3f), tLadderClimb, 0.4f, "asc_climb_1: ×1.3");
                foreach (var c in new System.Collections.Generic.List<Vector2Int>(ladders.Cells)) ladders.Remove(c);

                // ---- the Grapple: 12 m line, reel 4 m/s; then asc_grapple_2 (24 m, ×1.5) ----
                Buy("asc_grapple_1");
                float tG = 0, tGFull = 0, tG2 = 0;
                yield return ClimbGrapple(t => tG = t);
                yield return Bottom();
                FillPack();
                lf = player.LoadFactor;
                yield return ClimbGrapple(t => tGFull = t);
                state.inventory.Clear();
                yield return Bottom();
                Buy("asc_grapple_1", "asc_grapple_2");
                yield return ClimbGrapple(t => tG2 = t);
                yield return Bottom();
                float wantG = Ascent.GrappleSeconds(30f, 12f, 4f, Ascent.HookSpeed, 1f), wantGFull = Ascent.GrappleSeconds(30f, 12f, 4f, Ascent.HookSpeed, lf);
                float wantG2 = Ascent.GrappleSeconds(30f, 24f, 6f, Ascent.HookSpeed, 1f);
                TestContext.Out.WriteLine($"[MERIDIAN] u176 grapple 30 m: {tG:0.00} s empty (tables {wantG:0.0}), {tGFull:0.00} s full ({wantGFull:0.0}), {tG2:0.00} s with asc_grapple_2 ({wantG2:0.0})");
                Assert.AreEqual(wantG, tG, wantG * 0.15f, "grapple, empty: ~8.5 s");
                Assert.AreEqual(wantGFull, tGFull, wantGFull * 0.15f, "grapple, full: ~16 s");
                Assert.AreEqual(wantG2, tG2, wantG2 * 0.15f, "asc_grapple_2: 24 m line, reel ×1.5");
                Assert.Less(tG2, tG);

                // ---- the winch (asc_winch): the post at the shaft's mouth, its line to the floor, 6 m/s ----
                Buy("asc_winch");
                var winch = side.winch;
                var wFrom = winch.player;
                winch.player = null;
                Assert.IsTrue(winch.Place(new Vector2(x0 + 1.5f, surface - 0.5f)), "the post stands at the shaft's mouth");
                winch.player = wFrom;
                Assert.AreEqual(x0 + 1.5f, winch.LineX, 0.01f, "the line hangs down the shaft's middle");
                Assert.AreEqual(yb, winch.LineFoot, 0.01f, "to its floor");
                Assert.Greater(winch.RideTop, DigRun.LineAt(side.terrain, winch.LineX), "the ride ends topside");
                float tW = 0, tWFull = 0;
                yield return ClimbColumn(t => tW = t);
                Assert.AreEqual(ClimbKind.Winch, player.ClimbingOn);
                yield return Bottom();
                FillPack();
                lf = player.LoadFactor;
                yield return ClimbColumn(t => tWFull = t);
                state.inventory.Clear();
                yield return Bottom();
                TestContext.Out.WriteLine($"[MERIDIAN] u176 winch 30 m: {tW:0.00} s empty, {tWFull:0.00} s full (load {lf:0.00})");
                Assert.AreEqual(5f, tW, 0.3f, "winch, empty: 5 s");
                Assert.AreEqual(30f / (6f * lf), tWFull, 0.4f, "winch, full: ~10 s");
                Assert.Less(tW, tG, "the ring-5 winch beats the grapple");
                winch.Remove();
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Time.timeScale = scale;
                if (player != null) player.externalInput = false;
                state.skillNodes.Clear(); SkillStats.Apply(state); state.inventory.Clear();
            }
        }

        /// <summary>U-190 (D1_TABLES §4, 01:5x): the jetpack out of a 6 m starter hole on Earth and on Mars, empty and with a full pack (the load
        /// slows the climb above gravity, never strands it): jump, then hold.</summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator TheJetpackClimbsASixMetreHoleEmptyAndFull()
        {
            yield return Boot();
            var director = Object.FindAnyObjectByType<SceneDirector>();
            var row = new System.Text.StringBuilder("[MERIDIAN] u190 jetpack 6 m:");
            try
            {
                foreach (var planet in new[] { Meridian.Planets.PlanetId.Earth, Meridian.Planets.PlanetId.Mars })
                {
                    if (planet != Meridian.Planets.PlanetId.Earth)
                    {
                        yield return director.LoadPlanetSide(state.catalog.Get(planet));
                        side = director.PlanetSide; player = side.player; rig = player.GetComponent<PlayerRigInput>();
                        if (side.hazards != null) side.hazards.enabled = false;
                        side.creatures.autoSpawn = false; side.creatures.DespawnAll();
                        float until = Time.realtimeSinceStartup + 15f;
                        while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                        player.externalInput = true;
                    }
                    // 25 m past the landed ship (on Mars the Pilgrim sits over the camp's first columns: its hull would cap the hole)
                    int hx = Mathf.FloorToInt(side.ship != null ? side.ship.transform.position.x : player.Body.position.x) + 25;
                    float top = side.terrain.SurfaceAt(hx + 1.5f);
                    int floor = Mathf.FloorToInt(top) - 6;
                    for (int y = floor; y <= Mathf.CeilToInt(top) + 2; y++)
                        for (int x = hx; x < hx + 3; x++) side.terrain.SetTile(x, y, TileId.Air);
                    for (int i = 0; i < 5; i++) yield return null;
                    float g = -Physics2D.gravity.y;
                    foreach (bool full in new[] { false, true })
                    {
                        state.inventory.Clear();
                        if (full) FillPack();
                        float lf = player.LoadFactor;
                        var at = new Vector2(hx + 1.5f, floor + 0.05f);
                        player.LetGo(); player.intent = default;
                        side.creatures.DespawnAll();
                        player.Body.simulated = true; // a planet load can leave the body held (aboard / waiting for the ground)
                        player.Body.position = at; player.transform.position = at; player.Body.linearVelocity = Vector2.zero;
                        for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate(); // on the floor: the charge refills
                        player.intent = new PlayerIntent { jumpHeld = true };
                        player.PressJump();
                        int steps = 0;
                        while (player.Body.position.y < floor + 6f && steps < 400) { yield return new WaitForFixedUpdate(); steps++; }
                        player.intent = default;
                        float t = Seconds(steps);
                        row.Append($" {planet} {(full ? "full" : "empty")} (load {lf:0.00}, g {g:0.00}) {(steps < 400 ? t.ToString("0.00") + " s" : "never")};");
                        if (steps >= 400)
                        {
                            var hit = Physics2D.Raycast(player.Body.position + new Vector2(0f, 1.9f), Vector2.up, 8f);
                            TestContext.Out.WriteLine($"[MERIDIAN] u190 stuck at {player.Body.position} (floor {floor}, hole x {hx}), grounded {player.Grounded}, above: {(hit.collider != null ? hit.collider.name + " at " + hit.point : "nothing")}");
                        }
                        Assert.Less(steps, 400, $"{planet}, {(full ? "a full" : "an empty")} pack: out of 6 m by the jetpack (a load slows, never strands)");
                    }
                }
                TestContext.Out.WriteLine(row.ToString());
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                TestContext.Out.WriteLine(row.ToString());
                if (player != null) player.externalInput = false;
                state.inventory.Clear();
            }
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator PlacementRecallAndTheGrip()
        {
            yield return Boot();
            try
            {
                var ladders = side.ladders;
                // ---- placement by the Builder's right click: nothing before asc_ladder_1; 1 m at 2 dirt; 3 m at 1 dirt with asc_ladder_2 ----
                rig.module = RigModule.Builder;
                state.dirt.capacity = 100; state.dirt.count = 10;
                var aim = new Vector2(x0 + 0.5f, yb + 1.5f);
                rig.AimAt(aim);
                Assert.IsFalse(rig.Secondary(), "no ladders before asc_ladder_1");
                Buy("asc_ladder_1");
                Assert.IsTrue(rig.Secondary()); Assert.AreEqual(1, rig.LastLadderMetres); Assert.AreEqual(8, state.dirt.count);
                Assert.IsTrue(ladders.Has(new Vector2Int(x0, yb + 1)));
                Assert.IsTrue(rig.Secondary(), "aimed at a ladder: it extends from its top");
                Assert.IsTrue(ladders.Has(new Vector2Int(x0, yb + 2))); Assert.AreEqual(6, state.dirt.count);
                Buy("asc_ladder_1", "asc_ladder_2");
                Assert.IsTrue(rig.Secondary()); Assert.AreEqual(3, rig.LastLadderMetres, "asc_ladder_2: 3 m at once"); Assert.AreEqual(3, state.dirt.count, "1 dirt a metre");
                Assert.AreEqual(5, ladders.Count);
                state.dirt.count = 0;
                Assert.IsFalse(rig.Secondary(), "no dirt, no ladder");
                state.dirt.count = 10;
                rig.AimAt(new Vector2(x0 + 0.5f, yb + 12.5f));
                Assert.IsFalse(rig.Secondary(), "out of the Builder's reach");
                rig.AimAt(new Vector2(x0 - 1.5f, yb + 1.5f));
                Assert.IsFalse(rig.Secondary(), "solid ground: no open cell");
                for (int i = 0; i < 3; i++) yield return null;
                Assert.AreEqual(7, ladders.Drawn, "a piece a metre, a top and a foot");
                // the save keeps them; a mound buries one
                Assert.AreEqual(5, state.ascentPieces.FindAll(a => a.kind == Ladders.Kind).Count);
                side.terrain.SetTile(x0, yb + 3, TileId.Stone);
                Assert.IsFalse(ladders.Has(new Vector2Int(x0, yb + 3)), "a mound buries its piece");
                Assert.AreEqual(4, state.ascentPieces.FindAll(a => a.kind == Ladders.Kind).Count);
                side.terrain.SetTile(x0, yb + 3, TileId.Air);
                foreach (var c in new System.Collections.Generic.List<Vector2Int>(ladders.Cells)) ladders.Remove(c);

                // ---- the recall beacon (asc_recall): 5 s, topside, pack kept, one charge a run ----
                var recall = side.recall;
                Assert.NotNull(recall);
                Assert.IsFalse(recall.Activate(), "none before asc_recall");
                Buy("asc_recall");
                int id = ItemRegistry.Get(D1Tables.Current.materials[0].item).id;
                state.inventory.Add(id, 3);
                Vector2 landed = Vector2.zero; recall.Recalled += p => landed = p;
                Assert.IsTrue(recall.Activate());
                Assert.IsFalse(recall.Activate(), "one charge a run");
                float t0 = Time.time;
                for (float w = Time.time + 1f; Time.time < w;) yield return null;
                Assert.IsTrue(recall.Beacon.enabled && recall.Beacon.sprite != null, "the beacon drawn while it waits (B-210's pulse)");
                Assert.Less(Vector2.Distance(recall.Beacon.transform.position, recall.Planted), 0.01f, "where it was planted (beside the feet)");
                while (recall.Waiting && Time.time - t0 < 8f) yield return null;
                Assert.AreEqual(5f, Time.time - t0, 0.25f, "topside in 5 s");
                Assert.IsTrue(DigRun.Topside(side.terrain, player.Body.position), "lifted topside");
                Assert.Less(Vector2.Distance(landed, player.Body.position), 0.5f, "set down where a conk-out wakes");
                Assert.AreEqual(3, state.inventory.Count(id), "the pack kept");
                for (int i = 0; i < 5; i++) yield return null;
                Assert.AreEqual(1, recall.Left, "refilled topside");
                state.inventory.Clear();

                // ---- the grip: a 37.5° ramp slides at the start, holds with asc_climb_1 (40°) ----
                var ramp = new GameObject("Ramp375").AddComponent<EdgeCollider2D>();
                float a = 37.5f * Mathf.Deg2Rad;
                var foot = new Vector2(player.Body.position.x, surface + 40f);
                ramp.points = new[] { foot, foot + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * 12f };
                Vector2 mid = foot + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * 6f;
                IEnumerator StandOnRamp(System.Action<float> slid)
                {
                    player.Body.position = mid + new Vector2(-Mathf.Sin(a), Mathf.Cos(a)) * 0.02f; player.Body.linearVelocity = Vector2.zero;
                    for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
                    var from = player.Body.position;
                    for (int i = 0; i < 50; i++) yield return new WaitForFixedUpdate();
                    slid(Vector2.Distance(from, player.Body.position));
                }
                float slideBase = 0, slideGrip = 0;
                Buy();
                yield return StandOnRamp(d => slideBase = d);
                bool slidingBase = player.Sliding;
                Buy("asc_ladder_1", "asc_climb_1");
                yield return StandOnRamp(d => slideGrip = d);
                Object.Destroy(ramp.gameObject);
                yield return Bottom();
                TestContext.Out.WriteLine($"[MERIDIAN] u176 grip on 37.5°: slid {slideBase:0.00} m in 1 s at the start, {slideGrip:0.00} m with asc_climb_1");
                Assert.IsTrue(slidingBase, "steeper than 35°: sliding");
                Assert.Greater(slideBase, 1f, "slides down it");
                Assert.Less(slideGrip, 0.05f, "asc_climb_1 holds it");
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                if (player != null) player.externalInput = false;
                state.skillNodes.Clear(); SkillStats.Apply(state); state.inventory.Clear();
            }
        }
    }
}
