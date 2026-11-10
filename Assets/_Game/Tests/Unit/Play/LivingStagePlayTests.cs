using System.Collections;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.View2D.Living;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-216 (PlayMode, the cartoon path at Earth's camp): with the flag off the living stage does not exist and the shader's wind
    /// is still; on, it stands in four layers (one mesh each), the wind's clock runs, the vine swings, no piece of near, play or
    /// play_front is mirrored, nothing of it can stop the surveyor, a rooted piece whose ground is dug away goes, and each of
    /// the four parts switches off alone; off again, it is gone.
    /// </summary>
    public class LivingStagePlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest, Timeout(300000)]
        public IEnumerator TheLivingStageStandsOnlyBehindItsFlag()
        {
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled, wasOn = LivingStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            LivingStage.Enabled = false;
            Meridian.Rig.RigTools rig = null; Transform owner = null;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var side = director.PlanetSide;
                if (side.hazards != null) side.hazards.enabled = false;
                side.creatures.autoSpawn = false; side.creatures.DespawnAll();
                var t = side.terrain;
                rig = side.rig; owner = rig.owner;
                var body = side.player.Body;
                float sx = side.spawnX + 14.5f;
                body.position = new Vector2(sx, t.SurfaceAt(sx) + 0.05f); side.player.transform.position = body.position; body.linearVelocity = Vector2.zero;
                for (int k = 0; k < 60; k++) yield return null;

                // the flag off: nothing of it exists, the shader's wind is still
                Assert.IsNull(GameObject.Find("LivingStage"), "the flag off: no living stage object");
                Assert.IsFalse(LivingStage.Instance != null && LivingStage.Instance.Built);
                Assert.AreEqual(0f, Shader.GetGlobalVector(LivingWind.WindId).z, "the shader's wind strength is 0");
                var feetBefore = body.position;

                // the flag on
                LivingStage.Enabled = true;
                float until = Time.realtimeSinceStartup + 10f;
                while ((LivingStage.Instance == null || !LivingStage.Instance.Built) && Time.realtimeSinceStartup < until) yield return null;
                var stage = LivingStage.Instance;
                Assert.NotNull(stage); Assert.IsTrue(stage.Built, "the stage builds at the camp");
                int total = 0, vertices = 0;
                var packed = new List<Vector4>();
                for (int l = 0; l < LivingStage.Layers; l++)
                {
                    var layer = (LivingStage.Layer)l;
                    Assert.Greater(stage.InstanceCount(layer), 0, $"{layer} holds pieces");
                    Assert.Greater(stage.VertexCount(layer), 0, $"{layer} is a mesh");
                    total += stage.InstanceCount(layer); vertices += stage.VertexCount(layer);
                    Assert.AreEqual(LivingStage.Orders[l], stage.LayerRoot(layer).GetComponent<MeshRenderer>().sortingOrder);
                    if (layer == LivingStage.Layer.Foreground) continue;
                    stage.MeshOf(layer).GetUVs(2, packed);
                    foreach (var v in packed) Assert.AreEqual(1f, v.y, $"{layer}: no piece is mirrored (D-206)");
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u216 the stage: {total} pieces in {LivingStage.Layers} layers, {vertices} vertices, {stage.DrawCalls} draw calls; near {stage.InstanceCount(LivingStage.Layer.Near)}, play {stage.InstanceCount(LivingStage.Layer.Play)}, play_front {stage.InstanceCount(LivingStage.Layer.PlayFront)}, foreground {stage.InstanceCount(LivingStage.Layer.Foreground)}; the lamp reads the normal map: {stage.LampUsesNormals}");
                Assert.AreEqual(LivingStage.Layers + 2 + 1 + 1, stage.DrawCalls, "four layers, the motes, the shafts, the vine, the lit piece");
                Assert.AreEqual(0, stage.GetComponentsInChildren<Collider2D>(true).Length, "the stage never collides (D-206)");
                Assert.AreEqual(0, stage.GetComponentsInChildren<Rigidbody2D>(true).Length);

                // the wind runs and the vine swings
                float clock0 = Shader.GetGlobalVector(LivingWind.WindId).w;
                float most = 0f;
                float gameUntil = Time.time + 3f; // three seconds of the game's time (a batch run draws hundreds of frames a second)
                while (Time.time < gameUntil) { yield return null; most = Mathf.Max(most, Mathf.Abs(stage.Chain.Swing)); }
                var wind = Shader.GetGlobalVector(LivingWind.WindId);
                Assert.Greater(wind.w, clock0 + 1f, "the wind's clock runs");
                Assert.AreEqual(LivingStage.WindStrength, wind.z, 1e-5f, "the wind blows");
                Assert.Greater(most, 0.05f, "the vine swings in it");
                Assert.AreEqual(stage.Wind.Clock, wind.w, 1e-4f, "the shader has the field's own clock");
                Assert.AreEqual(0f, (body.position - feetBefore).magnitude, 0.05f, "the surveyor stands where they stood: the stage moves nothing of the game");

                // a rooted piece whose ground is dug away goes with the dig
                var playMesh = stage.MeshOf(LivingStage.Layer.Play);
                var roots = new List<Vector4>();
                playMesh.GetUVs(1, roots);
                Vector2 root = default; bool found = false;
                foreach (var v in roots)
                {
                    if (v.z <= 0f || Mathf.Abs(v.x - sx) < 3f || Mathf.Abs(v.x - sx) > 12f) continue; // a swaying piece near, not under the surveyor
                    root = new Vector2(v.x, v.y); found = true; break;
                }
                Assert.IsTrue(found, "a swaying piece stands within 12 m of the surveyor");
                int before = stage.VertexCount(LivingStage.Layer.Play), removedBefore = stage.Removed;
                rig.owner = null; // the staging's reach, for this dig
                bool dug = rig.Dig(new Vector2(root.x, t.SurfaceAt(root.x) - 0.3f));
                rig.owner = owner;
                Assert.IsTrue(dug, "the ground under it is dug");
                yield return null;
                TestContext.Out.WriteLine($"[MERIDIAN] u216 a dig at a root: {stage.Removed - removedBefore} piece(s) gone, the play layer {before} -> {stage.VertexCount(LivingStage.Layer.Play)} vertices; the check asked {stage.LastDigAsked} pieces and read the ground for {stage.LastDigRead}");
                Assert.Greater(stage.Removed, removedBefore, "its piece is gone");
                Assert.Less(stage.VertexCount(LivingStage.Layer.Play), before, "and no longer drawn");

                // each part switches off alone
                LivingStage.WindOn = false;
                yield return null; yield return null;
                Assert.AreEqual(0f, Shader.GetGlobalVector(LivingWind.WindId).z, "the wind off: still air");
                LivingStage.WindOn = true;
                LivingStage.AirOn = false; LivingStage.VineOn = false; LivingStage.LightOn = false;
                yield return null; yield return null;
                Assert.AreEqual(LivingStage.Layers, stage.DrawCalls, "the air, the vine and the lit piece off: the four layers alone");
                LivingStage.AirOn = LivingStage.VineOn = LivingStage.LightOn = true;
                yield return null;

                // the flag off again: gone
                LivingStage.Enabled = false;
                yield return null; yield return null;
                Assert.IsFalse(stage.Built, "the flag off: the stage is taken down");
                Assert.AreEqual(0, stage.transform.childCount, "nothing of it is left");
                Assert.AreEqual(0f, Shader.GetGlobalVector(LivingWind.WindId).z, "and the shader's wind is still");
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                LivingStage.WindOn = LivingStage.AirOn = LivingStage.VineOn = LivingStage.LightOn = true;
                LivingStage.Enabled = wasOn;
                if (!wasOn && LivingStage.Instance != null) Object.Destroy(LivingStage.Instance.gameObject);
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
                if (rig != null) rig.owner = owner;
            }
        }
    }
}
