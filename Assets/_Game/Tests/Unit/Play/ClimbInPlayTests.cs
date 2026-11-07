using System.Collections;
using Meridian.Core;
using Meridian.Player;
using Meridian.Ship;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-115 follow-up: boarding on the cartoon path plays climb_in while the drawn surveyor's sprite root rises from the feet to the
    /// ship's door socket (the legs rig's `door`, else the hull fallback); the player object stays, frozen, until the clip ends and then
    /// goes away aboard; an exit puts the surveyor back beside the hull with the root at the feet.
    /// </summary>
    public class ClimbInPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
        }

        [UnityTest]
        public IEnumerator TheDrawnSurveyorClimbsToTheHatchBeforeTheObjectGoesAway()
        {
            yield return Boot();
            var boarding = side.ship.GetComponent<ShipBoarding>();
            Assert.NotNull(boarding, "ShipBoarding on the ship");
            var drawn = side.cartoon != null ? side.cartoon.Surveyor : null;
            if (drawn == null) { TestContext.Out.WriteLine("[MERIDIAN] climb_in: no drawn surveyor (3D path); the climb is the cartoon path's"); yield break; }
            if (boarding.Aboard) { Assert.IsTrue(boarding.TryExit(), "out of the ship first"); for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate(); }
            // Beside the hull, on the ground, within boarding range.
            var ship = side.ship;
            int tx = Mathf.FloorToInt(ship.Body.position.x + SideShip.Width * 0.5f + 1.5f);
            var stand = new Vector2(tx + 0.5f, side.terrain.TopSolidY(tx) + 1.05f);
            side.player.Body.position = stand; side.player.transform.position = stand; side.player.Body.linearVelocity = Vector2.zero;
            float until = Time.realtimeSinceStartup + 5f;
            while (!side.player.Grounded && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
            Assert.IsTrue(side.player.Grounded, "standing beside the hull");
            Assert.IsTrue(boarding.InRange, "within boarding range");
            var door = boarding.DoorWorld();
            Assert.Greater(door.y, ship.Body.position.y - SideShip.SkidDrop + 1.5f, "the hatch sits up the hull (the rig's door socket or the fallback)");
            Vector3 feet = drawn.SquashRoot.position;
            float seconds = drawn.ClipSeconds(SurveyorAnim.ClimbIn);
            Assert.IsTrue(boarding.TryBoard(), "boards");
            Assert.IsTrue(boarding.Aboard, "aboard at once (the ship is piloted)");
            Assert.IsTrue(boarding.Climbing, "the drawn surveyor climbs first");
            Assert.IsTrue(drawn.ClimbingIn, "the view runs climb_in");
            Assert.IsTrue(side.player.gameObject.activeSelf, "the object stays while the clip plays");
            TestContext.Out.WriteLine($"[MERIDIAN] climb_in {(seconds > 0f ? seconds.ToString("F2") + " s (the side_b clip)" : "0.75 s (no clip yet: the stand-in length)")}, door {door}, feet {feet}");
            for (float t = 0f; t < 0.3f; t += Time.deltaTime) yield return null;
            Assert.Greater(drawn.SquashRoot.position.y, feet.y + 0.1f, "the sprite root rises toward the hatch");
            if (seconds > 0f) Assert.AreEqual(SurveyorAnim.ClimbIn, drawn.Clip, "climb_in plays");
            until = Time.realtimeSinceStartup + 5f;
            while (boarding.Climbing && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsFalse(boarding.Climbing, "the climb ends");
            Assert.IsFalse(side.player.gameObject.activeSelf, "aboard: the object is away");
            // Out again: the surveyor steps out beside the hull with the root back at the feet.
            Assert.IsTrue(boarding.TryExit(), "exits");
            yield return null; yield return null;
            Assert.IsTrue(side.player.gameObject.activeSelf);
            Assert.AreEqual(0f, drawn.SquashRoot.localPosition.y, 0.01f, "the root is back at the feet");
            Assert.IsFalse(drawn.ClimbingIn);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
