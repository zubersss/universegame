using System.Collections;
using Meridian.Core;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-165 (P-56): a boot never buries the surveyor. BudgetGate's graphics boot had the solid rescue lift the surveyor 0.76 m at the camp
    /// (64.5, 337.8) right after the PlanetSide load, every run; the headless boots never did. From the first physics step after Core loads,
    /// for 3 s, each step records the surveyor's body (simulated, y, vertical speed), its feet against the traced outline under it, the
    /// terrain's state and the rescue count; the surveyor's feet never sink more than 0.1 m under the outline, and nothing is rescued.
    /// The trace prints when it fails (run it with -Graphics too: tools/unity_test.ps1 -Graphics).
    /// </summary>
    public class BootTracePlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest, Timeout(120000)]
        public IEnumerator ABootNeverBuriesTheSurveyor()
        {
            int rescues0 = SolidRescue.Rescues;
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var trace = new System.Text.StringBuilder();
            float worstSink = 0f; string worstAt = "";
            float until = -1f;
            for (int step = 0; step < 2000; step++)
            {
                var player = Object.FindAnyObjectByType<Meridian.Player.PlayerController>();
                var terrain = Object.FindAnyObjectByType<TerrainStreamer>();
                if (player != null && player.Body != null)
                {
                    if (until < 0f) until = Time.time + 3f;
                    var b = player.Body;
                    float feet = float.NaN;
                    foreach (var c in player.GetComponents<Collider2D>()) if (c.enabled && !c.isTrigger) feet = float.IsNaN(feet) ? c.bounds.min.y : Mathf.Min(feet, c.bounds.min.y);
                    float floor = float.NaN;
                    foreach (var h in Physics2D.RaycastAll(b.position + Vector2.up * 4f, Vector2.down, 12f))
                        if (h.collider is EdgeCollider2D && h.collider.GetComponent<TerrainChunk>() != null) { floor = h.point.y; break; }
                    bool settled = terrain != null && terrain.IsSettled;
                    float sink = !float.IsNaN(floor) && !float.IsNaN(feet) ? floor - feet : 0f;
                    string line = $"s{step} t{Time.time:F2} dt{Time.deltaTime * 1000f:F0} sim {b.simulated} y {b.position.y:F2} vy {b.linearVelocity.y:F2} feet {feet:F2} floor {floor:F2} settled {settled} rescues {SolidRescue.Rescues - rescues0}";
                    if (trace.Length < 60000) trace.Append(line).Append('\n');
                    if (sink > worstSink) { worstSink = sink; worstAt = line; }
                    if (Time.time >= until) break;
                }
                yield return new WaitForFixedUpdate();
            }
            int rescued = SolidRescue.Rescues - rescues0;
            TestContext.Out.WriteLine($"[MERIDIAN] u165 boot: graphics {SystemInfo.graphicsDeviceType}, worst sink {worstSink:F3} m at [{worstAt}], rescues {rescued}");
            if (rescued > 0 || worstSink > 0.1f) TestContext.Out.WriteLine("[MERIDIAN] u165 trace:\n" + trace);
            if (rescued > 0) LogAssert.Expect(LogType.Log, new System.Text.RegularExpressions.Regex("solid rescue"));
            Assert.AreEqual(0, rescued, $"the boot rescued the surveyor (worst sink {worstSink:F2} m at [{worstAt}])");
            Assert.LessOrEqual(worstSink, 0.1f, $"the surveyor's feet sank under the outline: [{worstAt}]");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
