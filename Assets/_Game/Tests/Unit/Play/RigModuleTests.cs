using System.Collections;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.FX;
using Meridian.Player;
using Meridian.Rig;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-046 (PlayMode): tool in hand turned to the aim; Beam ray to the hit; Survey pulses once (the Lance case is archived, D-087); Builder ghost red when blocked.</summary>
    public class RigModuleTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerRigInput rig;
        RigToolView tool;

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
            side.dayNight.Override = 0.5f;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            rig = side.player.GetComponent<PlayerRigInput>();
            Assert.NotNull(rig, "PlayerRigInput on the surveyor");
            tool = rig.ToolView;
            Assert.NotNull(tool, "RigToolView created with the rig");
            timeout = Time.realtimeSinceStartup + 10f;
            while (tool.Tool.sprite == null && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.NotNull(tool.Tool.sprite, "tool art loaded");
        }

        Vector2 Feet => side.player.Body.position;

        [UnityTest]
        public IEnumerator ToolSitsInTheHandAndTurnsToTheAim()
        {
            yield return Boot();
            foreach (RigModule m in System.Enum.GetValues(typeof(RigModule)))
            {
                rig.module = m;
                rig.AimAt(Feet + new Vector2(3f, 2.5f));
                for (int i = 0; i < 3; i++) yield return null;
                var loadKey = RigModules.LoadKey(m); // U-093: the Grapple shows the old slot-2 sprite until its art exists
                Assert.That(tool.Tool.sprite.name, Does.Contain(loadKey.Substring(loadKey.LastIndexOf('/') + 1)), "module art " + m);
                var s = tool.Tool.sprite;
                Assert.AreEqual(0.375f, s.pivot.x / s.rect.width, 0.01f, "grip pivot x (D-041)");
                Assert.AreEqual(0.5f, s.pivot.y / s.rect.height, 0.01f, "grip pivot y");
                Assert.Less(Vector2.Distance(tool.Tool.transform.position, tool.HandWorld), 1e-3f, "tool at the hand");
                Vector2 toAim = rig.AimWorld - tool.HandWorld;
                Assert.AreEqual(Mathf.Atan2(toAim.y, toAim.x) * Mathf.Rad2Deg, tool.AimDegrees, 0.5f, "turned to the aim");
                Assert.AreEqual(RigModules.Muzzle(m).magnitude, Vector2.Distance(tool.HandWorld, tool.MuzzleWorld), 0.005f, "muzzle offset " + m);
                Assert.IsFalse(tool.Tool.flipY);
            }
            rig.AimAt(Feet + new Vector2(-3f, 1f));
            yield return null;
            Assert.IsTrue(tool.Tool.flipY, "aiming left keeps the tool upright");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator BeamRayRunsFromTheMuzzleToTheHit()
        {
            yield return Boot();
            rig.module = RigModule.Beam;
            // Aim at the ground 3 m ahead, below the feet: the ray ends where it meets terrain.
            int x = Mathf.FloorToInt(Feet.x) + 3;
            int top = side.terrain.TopSolidY(x);
            rig.AimAt(new Vector2(x + 0.5f, top + 0.5f));
            for (int i = 0; i < 3; i++) yield return null;
            rig.holdUse = true;
            float until = Time.realtimeSinceStartup + 5f;
            yield return null;
            while (!tool.Beam.enabled && Time.realtimeSinceStartup < until) yield return null; // ray sheet loads
            Assert.IsTrue(tool.Beam.enabled, "ray drawn while the Beam fires");
            Assert.That(tool.BeamLength, Is.GreaterThan(0.3f).And.LessThanOrEqualTo(RigTools.Reach));
            Assert.Less(Vector2.Distance(tool.Beam.transform.position, tool.MuzzleWorld), 1e-3f, "ray starts at the muzzle");
            Assert.AreEqual(tool.BeamLength, tool.Beam.size.x, 1e-3f, "tiled to the hit length");
            Assert.AreEqual(SpriteDrawMode.Tiled, tool.Beam.drawMode);
            rig.holdUse = false;
            yield return null;
            yield return null;
            Assert.IsFalse(tool.Beam.enabled, "off when released");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator SurveyPulsesOncePerPress()
        {
            yield return Boot();
            int pulses = 0;
            rig.Surveyed += _ => pulses++;
            rig.module = RigModule.Survey;
            float ready = Time.realtimeSinceStartup + 5f;
            while (!FxSheet.Get(Meridian.Art.ArtKeys.Fx.SurveyScan).Ready && Time.realtimeSinceStartup < ready) yield return null;
            rig.AimAt(Feet + new Vector2(2f, 1f));
            rig.holdUse = true;
            for (int i = 0; i < 30; i++) yield return null; // held: still one pulse
            rig.holdUse = false;
            Assert.AreEqual(1, pulses, "one pulse per press");
            Assert.IsTrue(rig.LastSurveyRing, "the scan ring plays from the FX pool (one-shots free their slot: FxTests)");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator BuilderGhostTurnsRedWhenBlocked()
        {
            yield return Boot();
            var inv = GameState.Instance.inventory;
            inv.Clear();
            inv.Add(TileId.Soil, 10);
            inv.Select(0);
            rig.module = RigModule.Builder;
            int x = Mathf.FloorToInt(Feet.x) + 3;
            int top = side.terrain.TopSolidY(x);
            rig.AimAt(new Vector2(x + 0.5f, top + 2.5f)); // open air
            float until = Time.realtimeSinceStartup + 5f;
            yield return null;
            while (!tool.Ghost.enabled && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsTrue(tool.Ghost.enabled, "ghost shown with the Builder");
            Assert.Less(Vector2.Distance(new Vector2(x + 0.5f, top + 2.5f), tool.Ghost.transform.position), 1e-3f, "on the target cell");
            Assert.IsFalse(tool.GhostBlocked);
            Assert.AreEqual(Color.white, tool.Ghost.color);
            rig.AimAt(new Vector2(x + 0.5f, top + 0.5f)); // solid ground
            yield return null;
            Assert.IsTrue(tool.GhostBlocked, "blocked on solid ground");
            Assert.AreEqual(RigToolView.Blocked, tool.Ghost.color, "tinted red");
            rig.AimAt(new Vector2(x + 0.5f, top + 2.5f));
            inv.Clear();
            yield return null;
            Assert.IsTrue(tool.GhostBlocked, "nothing to place");
            rig.module = RigModule.Beam;
            yield return null;
            Assert.IsFalse(tool.Ghost.enabled, "only with the Builder");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
