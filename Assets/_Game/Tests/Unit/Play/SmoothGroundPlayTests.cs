using System.Collections;
using System.Collections.Generic;
using Meridian.Player;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-156 (PlayMode, D-161 (5)): the surveyor on the smooth ground's edge colliders. A jump from traced flat ground peaks within 1 cm of the
    /// same jump from the old box ground (Bible §4.2's heights unchanged); a walk up and down a 30° ramp keeps the feet on it every step (no
    /// bounce off the slope or its crest), and standing still on it the surveyor does not slide.
    /// </summary>
    public class SmoothGroundPlayTests
    {
        Scene scene;
        Vector2 savedGravity;

        [SetUp]
        public void SetUp()
        {
            savedGravity = Physics2D.gravity;
            scene = SceneManager.CreateScene("SmoothGroundTest_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SceneManager.SetActiveScene(scene);
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            Physics2D.gravity = savedGravity;
            yield return SceneManager.UnloadSceneAsync(scene);
        }

        static PlayerController Spawn(Vector2 at)
        {
            Physics2D.gravity = new Vector2(0f, -9.81f);
            var go = new GameObject("Player");
            go.transform.position = at;
            go.AddComponent<Rigidbody2D>();
            go.AddComponent<CapsuleCollider2D>();
            go.AddComponent<PlayerVitals>();
            var p = go.AddComponent<PlayerController>();
            p.externalInput = true;
            p.terminalVelocity = 50f;
            return p;
        }

        static GameObject Edge(string name, params Vector2[] points)
        {
            var go = new GameObject(name);
            go.AddComponent<Rigidbody2D>().bodyType = RigidbodyType2D.Static;
            go.AddComponent<EdgeCollider2D>().SetPoints(new List<Vector2>(points));
            return go;
        }

        static IEnumerator Fixed(int steps) { for (int i = 0; i < steps; i++) yield return new WaitForFixedUpdate(); }

        static IEnumerator Jump(PlayerController p, System.Action<float> height)
        {
            yield return Fixed(15);
            Assert.IsTrue(p.Grounded, "standing on the ground");
            float start = p.Body.position.y, apex = start;
            p.PressJump();
            for (int i = 0; i < 300; i++)
            {
                yield return new WaitForFixedUpdate();
                apex = Mathf.Max(apex, p.Body.position.y);
                if (i > 5 && p.Grounded) break;
            }
            height(apex - start);
        }

        [UnityTest]
        public IEnumerator AJumpFromTracedFlatGroundMatchesTheBoxGround()
        {
            // The old ground: a box with its top at y = 0.
            var box = new GameObject("Box").AddComponent<BoxCollider2D>();
            box.size = new Vector2(40f, 1f); box.transform.position = new Vector3(0f, -0.5f, 0f);
            float boxJump = 0f;
            var a = Spawn(new Vector2(0f, 0.05f));
            yield return Jump(a, h => boxJump = h);
            Object.Destroy(a.gameObject); Object.Destroy(box.gameObject);
            yield return null;

            // The new ground: a chunk-sized outline traced from flat natural ground at y = 10 (exactly as TerrainChunk traces it).
            var c = new GroundContour();
            var d = new float[33 * 33];
            for (int y = 0; y <= 32; y++) for (int x = 0; x <= 32; x++) d[y * 33 + x] = GroundField.Density(false, true, 10f, y);
            c.Build(d, 32, new Vector2(-16.5f, 0.5f));
            var pts = new Vector2[c.lineCount[0]];
            for (int i = 0; i < pts.Length; i++) pts[i] = c.points[c.lineStart[0] + i];
            Edge("Traced", pts);
            float tracedJump = 0f;
            var b = Spawn(new Vector2(0f, 10.1f));
            yield return Jump(b, h => tracedJump = h);
            TestContext.Out.WriteLine($"[MERIDIAN] u156 jump: box ground {boxJump:F4} m, traced ground {tracedJump:F4} m");
            Assert.AreEqual(boxJump, tracedJump, 0.01f, "the flat-ground jump height is unchanged (±1 cm)");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AThirtyDegreeRampIsWalkedWithoutSlideOrBounce()
        {
            float rise = 20f * Mathf.Tan(30f * Mathf.Deg2Rad);
            var ramp = Edge("Ramp", new Vector2(-30f, 0f), new Vector2(0f, 0f), new Vector2(20f, rise), new Vector2(50f, rise)).GetComponent<EdgeCollider2D>();
            var p = Spawn(new Vector2(-6f, 0.05f));
            var foot = p.GetComponent<CapsuleCollider2D>();
            float tan = Mathf.Tan(30f * Mathf.Deg2Rad);
            // The gap is the capsule's own distance to the line along its normal (Physics2D.Distance), not its pivot's height over the line: a
            // round foot touching a 30° line holds its pivot r(sec θ − 1) = 4.6 cm above it (logged as "pivot"), with no gap at all.
            float pivotRide = PlayerTuning.Width * 0.5f * (1f / Mathf.Cos(30f * Mathf.Deg2Rad) - 1f), upPivot = 0f, downPivot = 0f, upSum = 0f, downSum = 0f;
            yield return Fixed(15);
            Assert.IsTrue(p.Grounded);

            // Up: on the ramp's middle (2 m clear of each corner), grounded every step and on the line.
            p.intent.move = 1f;
            int upSteps = 0, upAir = 0; float upGap = 0f;
            for (int i = 0; i < 600 && p.Body.position.x < 24f; i++)
            {
                yield return new WaitForFixedUpdate();
                float x = p.Body.position.x;
                if (x > 2f && x < 18f)
                {
                    upSteps++;
                    if (!p.Grounded) upAir++;
                    float g = Mathf.Abs(Physics2D.Distance(foot, ramp).distance);
                    upGap = Mathf.Max(upGap, g); upSum += g;
                    upPivot = Mathf.Max(upPivot, Mathf.Abs(p.Body.position.y - x * tan));
                }
            }
            Assert.Greater(upSteps, 20, "walked the ramp up");
            // Standing on the slope: no slide.
            p.intent.move = -1f;
            while (p.Body.position.x > 10f) yield return new WaitForFixedUpdate();
            p.intent.move = 0f;
            yield return Fixed(20);
            float x0 = p.Body.position.x;
            yield return Fixed(100);
            float slide = Mathf.Abs(p.Body.position.x - x0);
            // Down: grounded every step on the ramp's middle.
            p.intent.move = -1f;
            int downSteps = 0, downAir = 0; float downGap = 0f;
            for (int i = 0; i < 600 && p.Body.position.x > -4f; i++)
            {
                yield return new WaitForFixedUpdate();
                float x = p.Body.position.x;
                if (x > 2f && x < 8f)
                {
                    downSteps++;
                    if (!p.Grounded) downAir++;
                    float g = Mathf.Abs(Physics2D.Distance(foot, ramp).distance);
                    downGap = Mathf.Max(downGap, g); downSum += g;
                    downPivot = Mathf.Max(downPivot, Mathf.Abs(p.Body.position.y - x * tan));
                }
            }
            p.intent.move = 0f;
            TestContext.Out.WriteLine($"[MERIDIAN] u156 ramp 30°: up {upSteps} steps, {upAir} airborne, contact gap max {upGap:F4} mean {upSum / Mathf.Max(1, upSteps):F4} m, pivot over the line max {upPivot:F4} m (round-foot geometry {pivotRide:F4}); standing slide {slide:F4} m over 2 s; down {downSteps} steps, {downAir} airborne, contact gap max {downGap:F4} mean {downSum / Mathf.Max(1, downSteps):F4} m, pivot max {downPivot:F4} m");
            Assert.AreEqual(0, upAir, "no bounce walking up");
            Assert.Less(upGap, 0.05f, "the feet stay on the slope walking up");
            Assert.Less(slide, 0.01f, "no slide standing on the slope");
            Assert.Greater(downSteps, 10, "walked the ramp down");
            Assert.AreEqual(0, downAir, "no bounce walking down");
            Assert.Less(downGap, 0.05f, "the feet stay on the slope walking down");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
