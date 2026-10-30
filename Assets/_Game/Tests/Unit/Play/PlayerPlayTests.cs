using System.Collections;
using Meridian.Planets;
using Meridian.Player;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-009 (PlayMode): the real Rigidbody2D under each planet's gravity on flat test ground.
    /// Gravity and terminal velocity are typed here from Bible §4.1/§4.2 (independent of PlanetConfig).
    /// </summary>
    public class PlayerPlayTests
    {
        Scene scene;
        Vector2 savedGravity;

        [SetUp]
        public void SetUp()
        {
            savedGravity = Physics2D.gravity;
            scene = SceneManager.CreateScene("PlayerTest_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SceneManager.SetActiveScene(scene);
            var ground = new GameObject("Ground");
            var box = ground.AddComponent<BoxCollider2D>();
            box.size = new Vector2(400f, 1f);
            ground.transform.position = new Vector3(0f, -0.5f, 0f); // top surface at y = 0
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            Physics2D.gravity = savedGravity;
            yield return SceneManager.UnloadSceneAsync(scene);
        }

        static PlayerController Spawn(float g, float terminal, Vector2 at)
        {
            Physics2D.gravity = new Vector2(0f, -g);
            var go = new GameObject("Player");
            go.transform.position = at;
            go.AddComponent<Rigidbody2D>();
            go.AddComponent<CapsuleCollider2D>();
            go.AddComponent<PlayerVitals>();
            var p = go.AddComponent<PlayerController>();
            p.externalInput = true;
            p.terminalVelocity = terminal;
            return p;
        }

        static IEnumerator Fixed(int steps) { for (int i = 0; i < steps; i++) yield return new WaitForFixedUpdate(); }

        [UnityTest]
        public IEnumerator JumpHeightWithin3PercentOnEarth() => JumpHeight(9.81f, 50f);
        [UnityTest]
        public IEnumerator JumpHeightWithin3PercentOnMars() => JumpHeight(3.72f, 55f);
        [UnityTest]
        public IEnumerator JumpHeightWithin3PercentOnJupiter() => JumpHeight(24.79f, 45f);

        IEnumerator JumpHeight(float g, float terminal)
        {
            var p = Spawn(g, terminal, Vector2.zero);
            yield return Fixed(10);
            Assert.IsTrue(p.Grounded, "standing on the ground");
            float start = p.Body.position.y;
            p.PressJump();
            float apex = start;
            for (int i = 0; i < 400; i++)
            {
                yield return new WaitForFixedUpdate();
                apex = Mathf.Max(apex, p.Body.position.y);
                if (i > 5 && p.Grounded) break;
            }
            float expected = PlayerTuning.JumpSpeed * PlayerTuning.JumpSpeed / (2f * g);
            float h = apex - start;
            TestContext.Out.WriteLine($"[MERIDIAN] g {g}: jump {h:F3} m, expected {expected:F3} m ({(h / expected - 1f) * 100f:+0.00;-0.00}%)");
            Assert.That(h, Is.EqualTo(expected).Within(3).Percent);
        }

        [UnityTest]
        public IEnumerator WalkAndSprintSpeeds()
        {
            var p = Spawn(9.81f, 50f, Vector2.zero);
            yield return Fixed(10);
            p.intent.move = 1f;
            yield return Fixed(25);
            Assert.AreEqual(PlayerTuning.WalkSpeed, p.Body.linearVelocity.x, 0.04f, "walk 4.0 m/s");
            p.intent.sprint = true;
            yield return Fixed(25);
            Assert.AreEqual(PlayerTuning.SprintSpeed, p.Body.linearVelocity.x, 0.065f, "sprint 6.5 m/s");
            p.intent.move = 0f; p.intent.sprint = false;
            yield return Fixed(25);
            Assert.AreEqual(0f, p.Body.linearVelocity.x, 0.01f, "stops");
        }

        [UnityTest]
        public IEnumerator TerminalVelocityOnEarthAndVenus()
        {
            foreach (var (g, terminal) in new[] { (9.81f, 50f), (8.87f, 20f) })
            {
                var p = Spawn(g, terminal, new Vector2(50f, 2000f)); // nothing below for a long way
                int steps = Mathf.CeilToInt(terminal / g / Time.fixedDeltaTime) + 50;
                yield return Fixed(steps);
                Assert.AreEqual(-terminal, p.Body.linearVelocity.y, terminal * 0.01f, $"terminal {terminal} m/s at g {g}");
                Object.Destroy(p.gameObject);
            }
        }

        [UnityTest]
        public IEnumerator FallDamageFromRealDrops()
        {
            // Earth drops: 6 m → ~10.8 m/s (safe), 16.5 m → ~18 m/s (half), 30 m → ~24.3 m/s (lethal).
            float[] heights = { 6f, 16.5f, 30f };
            float[] expectHealth = { 100f, 50f, 0f };
            float[] tolerance = { 0.01f, 6f, 0.01f };
            for (int i = 0; i < heights.Length; i++)
            {
                var p = Spawn(9.81f, 50f, new Vector2(i * 20f, heights[i]));
                for (int s = 0; s < 400 && !(p.Grounded && p.LastImpactSpeed > 0f); s++) yield return new WaitForFixedUpdate();
                var v = p.GetComponent<PlayerVitals>();
                TestContext.Out.WriteLine($"[MERIDIAN] drop {heights[i]} m: impact {p.LastImpactSpeed:F2} m/s, health {v.health:F1}");
                Assert.AreEqual(FallDamage.Fraction(p.LastImpactSpeed), 1f - v.health / 100f, 1e-4f, "damage follows the impact speed");
                Assert.AreEqual(expectHealth[i], v.health, tolerance[i], $"drop {heights[i]} m");
            }
        }

        [UnityTest]
        public IEnumerator JetpackMk1ClimbsOnEarthAtNetLift()
        {
            var p = Spawn(9.81f, 50f, new Vector2(0f, 10f));
            // Fire from a standing start in the air: hold jump while airborne.
            p.intent.jumpHeld = true;
            yield return Fixed(15); // ≥ 0.25 s airborne → jetpack engaged
            Assert.IsTrue(p.Jetpack.Firing, "Jetpack firing while held in the air");
            float v0 = p.Body.linearVelocity.y;
            yield return Fixed(50); // 1 s
            float net = (p.Body.linearVelocity.y - v0) / (50 * Time.fixedDeltaTime);
            Assert.AreEqual(14f - 9.81f, net, 0.1f, "Mk1 net lift on Earth +4.2 m/s²");
            yield return Fixed(120); // burn out at 3 s
            Assert.IsFalse(p.Jetpack.Firing, "Mk1 burn ends at 3 s");
            Assert.AreEqual(0f, p.Jetpack.Remaining, 1e-4f);
        }

        [UnityTest]
        public IEnumerator CleanConsole()
        {
            var p = Spawn(9.81f, 50f, Vector2.zero);
            p.intent.move = 1f;
            p.PressJump();
            yield return Fixed(60);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
