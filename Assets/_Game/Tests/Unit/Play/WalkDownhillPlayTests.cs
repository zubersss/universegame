using System.Collections;
using Meridian.Core;
using Meridian.Player;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-172 (the owner's 0.5.0 report: "the walking animation glitches when walking downhill"). On Earth's smooth ground the surveyor walks
    /// along the camp's flat pad (its outline's vertices kicked the capsule up), then walks and runs down a real slope (10 m of the drawn curve
    /// falling 0.25-0.65 m a metre, off every pad): no fixed step is airborne and the drawn surveyor never shows fall or land (the ground snap
    /// and the grounded no-rise). Then a real ledge (a 3 m pit dug ahead) still falls.
    /// </summary>
    public class WalkDownhillPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;

        [UnityTest, Timeout(180000)]
        public IEnumerator WalkAndRunDownhillStayOnTheGroundAndALedgeStillFalls()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            player = side.player;
            player.externalInput = true; player.intent = default;
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();
            var t = side.terrain;
            Assert.IsTrue(t.SmoothGround, "Earth's ground is the traced outline");

            // The camp's flat pad first: the outline's quarter-metre vertices kicked a walking capsule off the ground every metre or so.
            {
                float sx = player.Body.position.x;
                yield return Stand(sx);
                int air = 0;
                player.intent = new PlayerIntent { move = 1f };
                for (int i = 0; i < 70; i++) { yield return new WaitForFixedUpdate(); if (i > 3 && !player.Grounded) air++; }
                player.intent = default;
                TestContext.Out.WriteLine($"[MERIDIAN] u172 flat pad walk from x {sx:F1}: {air} airborne steps of 66, to x {player.Body.position.x:F2}");
                Assert.AreEqual(0, air, "walking the camp's flat pad: no airborne step");
            }

            // A downhill run east of the camp: 10 columns falling 2.5-6.5 m, no step over the walkable 0.68, no pad, dry.
            int x0 = -1;
            for (int x = Mathf.FloorToInt(player.Body.position.x) + 40; x < 1200 && x0 < 0; x++)
            {
                float drop = t.CurveAt(x) - t.CurveAt(x + 10);
                if (drop < 2.5f || drop > 6.5f) continue;
                bool ok = true;
                for (int k = 0; k < 12 && ok; k++)
                    ok = t.PadTop(x + k) == int.MinValue && t.CurveAt(x + k) - t.CurveAt(x + k + 1) >= -0.05f && t.CurveAt(x + k) - t.CurveAt(x + k + 1) <= 0.68f
                         && t.GetTile(x + k, t.TopSolidY(x + k) + 1) != TileId.Water;
                if (ok) x0 = x;
            }
            Assert.GreaterOrEqual(x0, 0, "a downhill run east of the camp");
            TestContext.Out.WriteLine($"[MERIDIAN] u172 slope at x {x0}: {t.CurveAt(x0):F2} → {t.CurveAt(x0 + 10):F2} over 10 m");

            foreach (bool sprint in new[] { false, true })
            {
                yield return Stand(x0 + 0.5f);
                var drawn = side.cartoon != null ? side.cartoon.Surveyor : null;
                int airborne = 0, snaps0 = player.Snaps, steps = 0;
                string badClip = null;
                player.intent = new PlayerIntent { move = 1f, sprint = sprint };
                while (player.Body.position.x < x0 + 10.5f && steps < 400)
                {
                    yield return new WaitForFixedUpdate();
                    steps++;
                    if (steps <= 3) continue; // the first steps pick up speed from rest
                    if (!player.Grounded) airborne++;
                    if (drawn != null && (drawn.Clip == SurveyorAnim.Fall || drawn.Clip == SurveyorAnim.Land)) badClip ??= $"{drawn.Clip} at x {player.Body.position.x:F2}";
                }
                player.intent = default;
                TestContext.Out.WriteLine($"[MERIDIAN] u172 {(sprint ? "run" : "walk")} downhill: {steps} steps, {airborne} airborne, {player.Snaps - snaps0} snaps, clip {(badClip ?? "never fall / land")}");
                Assert.Less(steps, 400, "reached the slope's foot");
                Assert.AreEqual(0, airborne, $"{(sprint ? "running" : "walking")} downhill: no airborne step");
                Assert.IsNull(badClip, $"{(sprint ? "running" : "walking")} downhill: walk / run never flicker into fall / land");
            }

            // A real ledge still falls: a pit 3 m deep and 3 m wide dug 2 m ahead.
            yield return Stand(x0 + 0.5f);
            int px = x0 + 3;
            for (int c = px; c < px + 3; c++)
                for (int y = t.TopSolidY(c); y > t.TopSolidY(c) - 3; y--) t.SetTile(c, y, TileId.Air);
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            bool fell = false;
            player.intent = new PlayerIntent { move = 1f };
            for (int i = 0; i < 150 && !fell; i++)
            {
                yield return new WaitForFixedUpdate();
                fell = !player.Grounded && player.Body.linearVelocity.y < -1f;
            }
            player.intent = default;
            Assert.IsTrue(fell, "walking into a 3 m pit falls (the snap reaches only 0.3 m)");
            LogAssert.NoUnexpectedReceived();
        }

        IEnumerator Stand(float x)
        {
            var b = player.Body;
            b.simulated = false;
            b.position = new Vector2(x, side.terrain.SurfaceAt(x) + 0.05f); player.transform.position = b.position;
            b.linearVelocity = Vector2.zero;
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            yield return new WaitForFixedUpdate();
            b.position = new Vector2(x, side.terrain.SurfaceAt(x) + 0.05f); player.transform.position = b.position;
            b.simulated = true;
            for (int i = 0; i < 40; i++) yield return new WaitForFixedUpdate();
        }
    }
}
