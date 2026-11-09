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
            try
            {
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

                // the held stroke: the shovel in hand swings its arc
                var input = player.GetComponent<PlayerRigInput>();
                var view = player.GetComponentInChildren<RigToolView>();
                Assert.NotNull(view, "the tool view");
                input.module = RigModule.Beam;
                input.AimAt(p + new Vector2(1.2f, -0.8f));
                float until = Time.realtimeSinceStartup + 10f;
                while ((view.Tool.sprite == null || !view.Tool.sprite.name.Contains("shovel")) && Time.realtimeSinceStartup < until) yield return null;
                StringAssert.Contains("shovel", view.Tool.sprite != null ? view.Tool.sprite.name : "(none)", "B-226's shovel in hand");
                input.holdUse = true;
                float lo = float.MaxValue, hi = float.MinValue;
                for (int i = 0; i < 40; i++) { yield return null; lo = Mathf.Min(lo, view.ScoopArcDegrees); hi = Mathf.Max(hi, view.ScoopArcDegrees); }
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
            }
        }
    }
}
