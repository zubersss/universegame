using System.Collections;
using Meridian.Core;
using Meridian.Player;
using Meridian.Progress;
using Meridian.Rig;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-193 (D-182, the owner 11-09): at Earth's camp a new surveyor's shovel digs within 2 m and no further, swinging its scoop arc over
    /// the held stroke (B-226's sprite in hand); The Beam bought topside reaches past that.
    /// </summary>
    public class ShovelPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest, Timeout(240000)]
        public IEnumerator TheShovelDigsWithinTwoMetresAndTheBeamFurther()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            if (side.hazards != null) side.hazards.enabled = false;
            side.creatures.autoSpawn = false; side.creatures.DespawnAll();
            var state = GameState.Instance;
            var suiteTool = SkillStats.ToolOverride;
            try
            {
                SkillStats.ToolOverride = null; // a new surveyor's own tool (PlayModeDefaults gives the older suites the Beam)
                state.skillNodes.Clear();
                SkillStats.Apply(state);
                var player = side.player;
                player.externalInput = true; player.intent = default;
                int camp = Mathf.FloorToInt(Meridian.Planet.POI.PoiCatalog.SpawnCamp.CenterX);
                float x = camp + 14.5f;
                var feet = new Vector2(x, side.terrain.SurfaceAt(x) + 0.05f);
                player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero;
                for (int i = 0; i < 40; i++) yield return new WaitForFixedUpdate();
                var rig = side.rig;
                Assert.AreEqual(DigTool.Shovel, rig.Tool, "a new surveyor's shovel");
                var p = player.Body.position;
                Assert.IsFalse(rig.Dig(p + new Vector2(3.5f, -0.5f)), "3.5 m: past the shovel's 2 m");
                Assert.IsTrue(rig.Dig(p + new Vector2(1.5f, -0.5f)), "1.6 m: the shovel digs");

                // the reach is measured from the body: a body set while not simulated is ahead of its transform until the next physics step
                var b = player.Body;
                b.simulated = false;
                b.position = p + new Vector2(-0.8f, 0f);
                var held = b.position;
                float wx = held.x - 1.3f;
                var wall = new Vector2(wx, side.terrain.SurfaceAt(wx) - 0.4f);
                TestContext.Out.WriteLine($"[MERIDIAN] u193 reach origin: body x {held.x:0.00}, transform x {player.transform.position.x:0.00}, the cell {Vector2.Distance(held, wall):0.00} m from the body, {Vector2.Distance(player.transform.position, wall):0.00} m from the transform");
                Assert.LessOrEqual(Vector2.Distance(held, wall), 2f, "the cell within 2 m of the body");
                Assert.IsTrue(rig.Dig(wall), "within 2 m of the body: the shovel digs");
                b.position = p; player.transform.position = p; b.simulated = true;
                for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();

                // the held stroke: the shovel in hand swings its arc
                var input = player.GetComponent<PlayerRigInput>();
                var view = player.GetComponentInChildren<RigToolView>();
                Assert.NotNull(view, "the tool view");
                input.module = RigModule.Beam;
                input.AimAt(p + new Vector2(1.2f, -0.8f));
                float until = Time.realtimeSinceStartup + 10f;
                while ((view.Tool.sprite == null || !view.Tool.sprite.name.Contains("shovel")) && Time.realtimeSinceStartup < until) yield return null;
                StringAssert.Contains("shovel", view.Tool.sprite != null ? view.Tool.sprite.name : "(none)", "B-226's shovel in hand");
                // sampled over one whole stroke in game time (batch frames are a few ms: 40 frames saw ~0.06 s of a 0.5 s stroke)
                float need = rig.StrokeSeconds(input.AimWorld);
                Assert.Greater(need, 0f, "Earth digs by the tables: the stroke takes time");
                input.holdUse = true;
                float lo = float.MaxValue, hi = float.MinValue, t0 = Time.time;
                until = Time.realtimeSinceStartup + 20f;
                while (Time.time - t0 < need * 0.95f && Time.realtimeSinceStartup < until)
                {
                    yield return null;
                    lo = Mathf.Min(lo, view.ScoopArcDegrees); hi = Mathf.Max(hi, view.ScoopArcDegrees);
                }
                input.holdUse = false;
                TestContext.Out.WriteLine($"[MERIDIAN] u193 the scoop arc over a held stroke: {lo:0.0} .. {hi:0.0} degrees off the aim");
                Assert.Greater(hi - lo, 20f, "the shovel swings over the stroke");
                Assert.IsFalse(view.Beam.enabled, "no ray from a shovel");

                // The Beam bought topside: it reaches past 2 m
                state.scrip = 1000;
                Assert.AreEqual(SkillTree.BuyResult.Ok, SkillTree.Current.Buy(state, "dig_power_1", true));
                Assert.AreEqual(DigTool.Beam, rig.Tool);
                Assert.IsTrue(rig.Dig(p + new Vector2(3.5f, -0.5f)), "3.5 m: within the Beam's reach");
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                state.skillNodes.Clear();
                SkillStats.Apply(state);
                SkillStats.ToolOverride = suiteTool;
            }
        }

        /// <summary>LEAD 11:3x: the HUD's tool slot shows the held tool: SHOVEL with B-226's icon at a new game, the module's name and its
        /// stand-in icon on a switch (B-227 draws icons/tools/grapple), BEAM MK1 once The Beam is bought; the Q / E caps as bound.</summary>
        [UnityTest, Timeout(240000)]
        public IEnumerator TheToolSlotShowsTheHeldTool()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            side.creatures.autoSpawn = false; side.creatures.DespawnAll();
            var state = GameState.Instance;
            var suiteTool = SkillStats.ToolOverride;
            try
            {
                SkillStats.ToolOverride = null;
                state.skillNodes.Clear();
                SkillStats.Apply(state);
                var slot = side.sideHud.ToolSlot;
                Assert.NotNull(slot, "the HUD's tool slot");
                var input = side.player.GetComponent<PlayerRigInput>();
                input.module = RigModule.Beam;
                IEnumerator Until(System.Func<bool> ok) { float t = Time.realtimeSinceStartup + 10f; while (!ok() && Time.realtimeSinceStartup < t) yield return null; }
                int frames = 0; // LEAD 13:1x: the real sprite within a few frames, not a stand-in
                float realUntil = Time.realtimeSinceStartup + 10f;
                while ((slot.ShownTool != DigTool.Shovel || slot.IconKey == null) && Time.realtimeSinceStartup < realUntil) { frames++; yield return null; } // the slot showed the suites' Beam until this frame
                TestContext.Out.WriteLine($"[MERIDIAN] u193 tool slot: the shovel's icon after {frames} frames");
                Assert.LessOrEqual(frames, 30, "the shovel's icon within a few frames");
                Assert.NotNull(slot.Icon.sprite, "a sprite in the slot");
                StringAssert.Contains("shovel", slot.Icon.sprite.name, "B-226's shovel icon, not a stand-in");
                TestContext.Out.WriteLine($"[MERIDIAN] u193 tool slot at start: root {slot.Root.gameObject.activeInHierarchy}, module {slot.ShownModule}, tool {slot.ShownTool}, name '{slot.Name.text}', icon {slot.IconKey ?? "-"}, sprite {(slot.Icon.sprite != null ? slot.Icon.sprite.name : "-")}, input {input.module}, aboard {(side.sideHud.boarding != null && side.sideHud.boarding.Aboard)}, player {(side.sideHud.player != null ? "set" : "null")}; {slot.Describe()}");
                Assert.IsTrue(slot.Root.gameObject.activeInHierarchy, "shown on foot");
                Assert.AreEqual("SHOVEL", slot.Name.text);
                Assert.AreEqual("icons/tools/shovel", slot.IconKey, "B-226's icon");
                Assert.AreEqual(Color.white, slot.Icon.color);
                StringAssert.Contains("Q", slot.PrevKey.text); StringAssert.Contains("E", slot.NextKey.text);

                input.module = RigModule.Grapple;
                yield return Until(() => slot.ShownModule == RigModule.Grapple && slot.IconKey != null);
                Assert.AreEqual("GRAPPLE", slot.Name.text);
                Assert.IsTrue(slot.IconKey == "icons/tools/grapple" || slot.IconKey == "icons/nodes/asc_grapple_1", $"the grapple's icon or its stand-in: {slot.IconKey}");

                input.module = RigModule.Beam;
                state.scrip = 1000;
                Assert.AreEqual(SkillTree.BuyResult.Ok, SkillTree.Current.Buy(state, "dig_power_1", true));
                yield return Until(() => slot.ShownTool == DigTool.Beam && slot.IconKey != null);
                Assert.AreEqual("BEAM MK1", slot.Name.text, "The Beam bought: the slot follows");
                Assert.IsTrue(slot.IconKey == "icons/tools/beam" || slot.IconKey == "icons/nodes/dig_power_1", $"the Beam's icon or its stand-in: {slot.IconKey}");
                TestContext.Out.WriteLine($"[MERIDIAN] u193 tool slot: SHOVEL icons/tools/shovel -> GRAPPLE -> {slot.Name.text} {slot.IconKey}; caps '{slot.PrevKey.text}' '{slot.NextKey.text}'");
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                state.skillNodes.Clear();
                SkillStats.Apply(state);
                SkillStats.ToolOverride = suiteTool;
            }
        }
    }
}
