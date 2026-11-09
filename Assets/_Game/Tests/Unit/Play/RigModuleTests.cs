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

        /// <summary>U-183 (B-205 / B-218): the looks follow the tree (the Beam Mk3 at dig_power_2, the Grapple Mk2 at asc_grapple_2, the Mk2
        /// pack at asc_jet_2), the archived Lance is never requested, the grip sits on the drawn frame's hand socket and the pack on its back
        /// socket within 1 px on every frame of walk, run and jump.</summary>
        [UnityTest]
        public IEnumerator ToolLooksFollowTheTreeAndSitOnTheSockets()
        {
            Meridian.Perf.Residency.Requested.Clear();
            Meridian.Perf.Residency.RecordRequests = true;
            try
            {
                yield return Boot();
                var state = GameState.Instance;
                foreach (var id in new[] { "dig_power_1", "dig_power_2", "asc_grapple_1", "asc_grapple_2", "asc_jet_1", "asc_jet_2" }) state.skillNodes.Add(id);
                Meridian.Progress.SkillStats.Apply(state);
                rig.module = RigModule.Beam;
                float until = Time.realtimeSinceStartup + 10f;
                while ((tool.Tool.sprite == null || !tool.Tool.sprite.name.Contains("beam_mk3")) && Time.realtimeSinceStartup < until) yield return null;
                Assert.AreEqual(3, tool.MkOf(RigModule.Beam));
                StringAssert.Contains("beam_mk3", tool.Tool.sprite.name, "the Beam Mk3 in hand");
                rig.module = RigModule.Grapple;
                until = Time.realtimeSinceStartup + 10f;
                while ((tool.Tool.sprite == null || !tool.Tool.sprite.name.Contains("grapple_mk2")) && Time.realtimeSinceStartup < until) yield return null;
                StringAssert.Contains("grapple_mk2", tool.Tool.sprite.name, "the Grapple Mk2");
                rig.module = RigModule.Beam;

                var view = side.player.GetComponentInChildren<Meridian.View2D.SpriteCharacterView>();
                Assert.NotNull(view, "the cartoon surveyor");
                var pack = view.GetComponent<JetpackOverlay>();
                Assert.NotNull(pack, "the jetpack overlay on the drawn surveyor");
                until = Time.realtimeSinceStartup + 10f;
                while ((pack.Mk != 2 || pack.Overlay.sprite == null) && Time.realtimeSinceStartup < until) yield return null;
                Assert.AreEqual(2, pack.Mk);

                var back = JetpackOverlay.SocketTable(view.Renderer.sprite);
                var hand = Meridian.Rendering.ArtMaterials.SocketFor("props/rig/hand_socket", "hand_socket");
                Assert.NotNull(back); Assert.NotNull(hand);
                const float Px = 1f / 64f;
                int packChecked = 0, handChecked = 0;
                var player = side.player;
                player.externalInput = true;
                // walk right, run left, jump: every drawn frame's pack and grip on their sockets
                for (int step = 0; step < 240; step++)
                {
                    player.intent = new PlayerIntent { move = step < 80 ? 1f : -1f, sprint = step >= 80, jumpPressed = step % 70 == 40, jumpHeld = step % 70 >= 40 && step % 70 < 50 };
                    yield return new WaitForFixedUpdate();
                    yield return null;
                    int i = JetpackOverlay.FrameOf(view.Renderer.sprite);
                    back = JetpackOverlay.SocketTable(view.Renderer.sprite); // U-176: the drawn frame's sheet (side_b's clips under the side key)
                    bool flip = view.Renderer.flipX;
                    if (pack.Overlay.enabled && back.Has(i))
                    {
                        var want = view.SquashRoot.TransformPoint(new Vector3(flip ? -back[i, 0] : back[i, 0], back[i, 1], 0f));
                        Assert.Less(Vector2.Distance(pack.Overlay.transform.position, want), Px, $"the pack on frame {i}'s back socket");
                        packChecked++;
                    }
                    int hf = tool.HandFrame;
                    if (tool.HandOnSocket && hand.Has(hf))
                    {
                        // the grip as placed in LateUpdate (the surveyor's squash-root space: the walk moves the root between then and now)
                        var want = new Vector2(flip ? -hand[hf, 0] : hand[hf, 0], hand[hf, 1]);
                        Assert.Less(Vector2.Distance(tool.HandLocal, want), Px, $"the grip on frame {hf}'s hand socket");
                        handChecked++;
                    }
                }
                player.externalInput = false;
                TestContext.Out.WriteLine($"[MERIDIAN] u183 sockets: the pack checked on {packChecked} frames, the grip on {handChecked}");
                Assert.Greater(packChecked, 100, "the pack placed through the walk, run and jump");
                Assert.Greater(handChecked, 100, "the grip on the drawn hand through them");
                foreach (var key in Meridian.Perf.Residency.Requested) StringAssert.DoesNotContain("lance", key, "the archived Lance is never loaded");
                LogAssert.NoUnexpectedReceived();
            }
            finally { Meridian.Perf.Residency.RecordRequests = false; }
        }

        [UnityTest]
        public IEnumerator ToolSitsInTheHandAndTurnsToTheAim()
        {
            yield return Boot();
            foreach (RigModule m in System.Enum.GetValues(typeof(RigModule)))
            {
                rig.module = m;
                rig.AimAt(Feet + new Vector2(3f, 2.5f));
                for (int i = 0; i < 3; i++) yield return null;
                var loadKey = RigModules.LoadKey(m); // U-183: every module its own art (the Grapple off the v2 Lance)
                Assert.AreEqual(RigModules.ArtKey(m), loadKey, "no stand-in left");
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
