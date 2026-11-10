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
    /// U-209 (07:5x): where a frame's managed bytes come from on Earth's surface, by Unity's own counter ("GC Allocated In Frame", every
    /// thread, the Editor's own share included). System.GC.GetAllocatedBytesForCurrentThread, the measure of every "0 B" row before
    /// today, reads 0 for a known array in this runtime: those rows proved nothing. This is a READING for the perf report, not a bar:
    /// the game's parts are switched off one after another (each row holds the ones before it) and the bytes a frame are read at each
    /// step, so a part's share is the drop at its row.
    /// </summary>
    public class AllocBreakdownTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest, Timeout(300000)]
        public IEnumerator WhereAFramesBytesComeFrom()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            var player = side.player;
            var toolWas = SkillStats.ToolOverride;
            try
            {
                var input = player.GetComponent<PlayerRigInput>();
                for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
                var view = input.ToolView;
                timeout = Time.realtimeSinceStartup + 15f;
                while ((view.Tool.sprite == null || view.Body == null) && Time.realtimeSinceStartup < timeout) yield return null;
                Time.captureDeltaTime = 1f / 60f;
                for (int i = 0; i < 150; i++) yield return null; // settled

                using (var gc = Unity.Profiling.ProfilerRecorder.StartNew(Unity.Profiling.ProfilerCategory.Memory, "GC Allocated In Frame"))
                {
                    Assert.IsTrue(gc.Valid, "Unity's 'GC Allocated In Frame' counter is there");
                    var log = new System.Text.StringBuilder();
                    long last = -1;
                    int frames = 40;
                    IEnumerator Row(string what)
                    {
                        for (int i = 0; i < 6; i++) yield return null;
                        long sum = 0, least = long.MaxValue, most = 0;
                        int above = 0;
                        for (int i = 0; i < frames; i++)
                        {
                            yield return null;
                            long v = gc.LastValue;
                            sum += v; least = System.Math.Min(least, v); most = System.Math.Max(most, v);
                            if (v > 400) above++;
                        }
                        long avg = sum / frames;
                        log.Append($"\n  {avg,8} B a frame (least {least}, most {most}, {above} of {frames} frames over 400 B){(last >= 0 ? $", {avg - last:+0;-0;0} on the row before" : "")}: {what}");
                        last = avg;
                    }

                    // The game as it runs (TerrainStreamingTests' settled row, red on the live counter at 08:2x: 90 B a frame of the
                    // game's own): 300 frames a row, then its creatures, its hazards and the player's own input taken away in turn.
                    frames = 300;
                    yield return Row("the game as it runs, settled: creatures, hazards, the player's own input (300 frames a row)");
                    side.creatures.autoSpawn = false;
                    side.creatures.DespawnAll();
                    yield return Row("+ the creatures despawned, none spawning");
                    if (side.hazards != null) side.hazards.enabled = false;
                    yield return Row("+ the hazards off");
                    player.externalInput = true; player.intent = default;
                    yield return Row("+ the player's input scripted (externalInput), standing");
                    frames = 40;

                    SkillStats.ToolOverride = DigTool.Shovel;
                    input.module = RigModule.Beam;
                    input.holdUse = false;
                    var feet = player.Body.position;
                    input.AimAt(feet + new Vector2(1.2f, -0.4f)); // the ground in front of the feet
                    for (int i = 0; i < 150; i++) yield return null; // the shovel stowed

                    yield return Row("the shovel in the dig slot at rest (stowed), the cursor still, scripted (40 frames a row from here)");
                    input.holdUse = true;
                    yield return Row("the shovel swinging, held (the surface: cells open)");
                    input.holdUse = false;
                    for (int i = 0; i < 120; i++) yield return null;
                    yield return Row("at rest again (stowed)");
                    input.module = RigModule.Survey;
                    yield return Row("the Survey module in hand (no reticle; the tool on the cursor)");
                    input.module = RigModule.Beam;
                    yield return Row("the dig slot at rest again");
                    view.enabled = false;
                    yield return Row("+ the tool view off (RigToolView: the tool, the reticle)");
                    input.enabled = false;
                    yield return Row("+ the rig's input off (PlayerRigInput)");
                    if (view.Body != null) view.Body.enabled = false;
                    yield return Row("+ the drawn surveyor off (SpriteCharacterView)");
                    player.enabled = false;
                    yield return Row("+ the player controller off");
                    foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
                    yield return Row("+ every Canvas off (the HUD)");
                    foreach (var a in Object.FindObjectsByType<Animator>(FindObjectsSortMode.None)) a.enabled = false;
                    yield return Row("+ every Animator off");
                    if (side.cartoon != null) side.cartoon.enabled = false;
                    yield return Row("+ the cartoon stage off (CartoonStage's own update)");
                    if (side.dayNight != null) side.dayNight.enabled = false;
                    yield return Row("+ the day and night off");
                    side.terrain.enabled = false;
                    yield return Row("+ the terrain streamer off");
                    foreach (var m in side.GetComponentsInChildren<MonoBehaviour>(true)) m.enabled = false;
                    yield return Row("+ every script under the planet side off");
                    foreach (var m in Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None))
                        if (m != null && m.gameObject.scene.name != "DontDestroyOnLoad" && m.GetType().Namespace != null && m.GetType().Namespace.StartsWith("Meridian")) m.enabled = false;
                    yield return Row("+ every Meridian script in the scene off");
                    foreach (var cam in Object.FindObjectsByType<Camera>(FindObjectsSortMode.None)) cam.enabled = false;
                    yield return Row("+ every camera off (nothing drawn)");
                    foreach (var root in SceneManager.GetActiveScene().GetRootGameObjects()) root.SetActive(false);
                    yield return Row("+ every root object of the scene inactive (the Editor and the test runner alone)");
                    TestContext.Out.WriteLine($"[MERIDIAN] alloc breakdown (Unity's 'GC Allocated In Frame', the Editor at a 60 fps step; each row holds the ones before it):{log}");
                }
            }
            finally
            {
                Time.captureDeltaTime = 0f;
                SkillStats.ToolOverride = toolWas;
            }
        }
    }
}
