using System.Collections;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Planets;
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
    /// U-193: LeadQA D1DigRunTests' step 2 in UNITY's suite, as LeadQA sees it (the real shovel, the hints on): the surveyor held in a dug
    /// 3 × 3 m hollow 5 m under the Surface Line, moved to its right side (body and transform: a body that is not simulated snaps back to its
    /// transform at the next physics step, which put LeadQA's aim inside the hollow's air), a held shovel stroke at the wall ~1.2 m off digs
    /// it in the tables' time (0.5 s at T1). Logs the stroke frame by frame (input, progress, the body and its transform, the reach).
    /// </summary>
    public class ShovelHollowPlayTests
    {
        /// <summary>The tool slot's icons resolve: icons/tools/shovel (B-226) loads as a sprite list as icons/nodes/dig_power_1 does.</summary>
        [UnityTest, Timeout(120000)]
        public IEnumerator TheToolIconsLoad()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            foreach (var key in new[] { "icons/tools/shovel", "icons/nodes/dig_power_1" })
            {
                var probe = UnityEngine.AddressableAssets.Addressables.LoadResourceLocationsAsync(key);
                yield return probe;
                var where = new System.Text.StringBuilder();
                if (probe.Result != null) foreach (var l in probe.Result) where.Append($" [{l.ResourceType?.Name} {l.InternalId} via {l.ProviderId}]");
                TestContext.Out.WriteLine($"[MERIDIAN] u193 icon probe {key}: {probe.Status}, {probe.Result?.Count ?? -1} locations{where}");
                int found = probe.Result?.Count ?? 0;
                Meridian.Art.ArtLoad.Release(probe);
                var h = Meridian.Art.ArtLoad.Asset<System.Collections.Generic.IList<Sprite>>(key);
                yield return h;
                TestContext.Out.WriteLine($"[MERIDIAN] u193 icon load {key}: {h.Status}, {(h.Result != null ? h.Result.Count : -1)} sprites, first {(h.Result != null && h.Result.Count > 0 && h.Result[0] != null ? h.Result[0].name : "-")}, {h.OperationException?.Message}");
                bool ok = h.Status == UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationStatus.Succeeded && h.Result != null && h.Result.Count > 0;
                Meridian.Art.ArtLoad.Release(h);
                Assert.Greater(found, 0, $"{key}: a location");
                Assert.IsTrue(ok, $"{key}: a sprite list");
            }
        }

        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;
        TerrainStreamer t;

        int CountSolid(Vector2 p)
        {
            int n = 0;
            for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++) if (TileId.IsSolid(t.GetTile(Mathf.FloorToInt(p.x) + dx, Mathf.FloorToInt(p.y) + dy))) n++;
            return n;
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator AHeldShovelStrokeDigsTheHollowsWall()
        {
            var suiteTool = SkillStats.ToolOverride;
            bool hints = Meridian.UI.HintCards.Suppressed;
            int dugEvents = 0;
            System.Action<Vector2> onDug = _ => dugEvents++;
            try
            {
                SkillStats.ToolOverride = null;
                Meridian.UI.HintCards.Suppressed = false;
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                side = director.PlanetSide; player = side.player; t = side.terrain;
                player.externalInput = true; player.intent = default;
                side.creatures.autoSpawn = false; side.creatures.DespawnAll();
                GameState.Instance.skillNodes.Clear();
                SkillStats.Apply(GameState.Instance);
                GameState.Instance.inventory.ReadFrom(new System.Collections.Generic.List<ItemStack>(), 0);
                GameState.Instance.dirt.count = 0;
                for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
                Assert.AreEqual(DigTool.Shovel, SkillStats.DigTool, "the shovel");
                side.rig.Dug += onDug;

                // LeadQA's StandAtDepth (5 m under the line, 45 m east of the camp)
                float x = player.Body.position.x + 45f;
                float floorY = DigRun.LineAt(t, x) - 5f;
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

                // LeadQA's HeldStroke
                var input = player.GetComponent<PlayerRigInput>();
                var feet = b.position;
                b.position = new Vector2(Mathf.Floor(feet.x) + 1.3f, feet.y);
                player.transform.position = b.position; // a body that is not simulated snaps back to its transform at the next physics step
                b.linearVelocity = Vector2.zero;
                yield return new WaitForFixedUpdate();
                feet = b.position;
                var target = new Vector2(Mathf.Floor(feet.x) + 1.5f, Mathf.Floor(feet.y) + 0.5f);
                float expect = D1Tables.Current.StrokeSeconds(PlanetId.Earth, DigRun.Depth(t, target), SkillStats.DigPower, SkillStats.DigTool);
                int solid0 = CountSolid(target);
                TestContext.Out.WriteLine($"[MERIDIAN] u193 hollow: fx {fx} fy {fy}, body {feet}, transform {(Vector2)player.transform.position}, target {target} (tile {t.GetTile(Mathf.FloorToInt(target.x), Mathf.FloorToInt(target.y))}), {Vector2.Distance(feet, target):0.00} m from the body, expect {expect:0.00} s, solid {solid0}, reach {SkillStats.DigReach}");
                input.module = RigModule.Beam;
                input.AimAt(target);
                input.holdUse = true;
                float t0 = Time.time, dugAt = -1f;
                int frame = 0;
                var log = new System.Text.StringBuilder();
                while (Time.time - t0 < expect + 2f && dugAt < 0f)
                {
                    yield return null;
                    if (frame++ % 15 == 0)
                        log.Append($"\n  t {Time.time - t0:0.000} using {input.Using} progress {input.StrokeProgress:0.00} module {input.module} aim {input.AimWorld} body {b.position} transform {(Vector2)player.transform.position} enabled {input.enabled} dug {dugEvents}");
                    if (CountSolid(target) < solid0) dugAt = Time.time - t0;
                }
                input.holdUse = false;
                yield return null;
                TestContext.Out.WriteLine($"[MERIDIAN] u193 hollow stroke: dug after {dugAt:0.00} s (expect {expect:0.00}), Dug events {dugEvents}, frames {frame}{log}");
                if (dugAt < 0f)
                {
                    bool direct = side.rig.Dig(target);
                    TestContext.Out.WriteLine($"[MERIDIAN] u193 hollow direct Dig: {direct}, solid {solid0} -> {CountSolid(target)}, Dug events {dugEvents}");
                }
                Assert.Greater(dugAt, 0f, "the held shovel digs the hollow's wall");
                Assert.AreEqual(expect, dugAt, 0.15f + expect * 0.05f, "in the tables' time");
            }
            finally
            {
                if (side != null && side.rig != null) side.rig.Dug -= onDug;
                if (player != null) player.Body.simulated = true;
                SkillStats.ToolOverride = suiteTool;
                Meridian.UI.HintCards.Suppressed = hints;
            }
        }
    }
}
