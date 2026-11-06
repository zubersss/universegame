using System.Collections;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Player;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-088 (PlayMode, Earth): one dash per airtime. The parry cases are archived with the parry (D-087, U-093: Archive/Combat~/Tests).</summary>
    public class FeelPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;

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
            player = side.player;
            player.externalInput = true;
            player.intent = default;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Grounded, "standing at the camp");
        }

        IEnumerator Until(System.Func<bool> done, float seconds)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while (!done() && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
        }

        [UnityTest]
        public IEnumerator OneDashPerAirtimeRefreshedByLanding()
        {
            yield return Boot();
            player.PressJump();
            yield return Until(() => !player.Grounded, 2f);
            Assert.IsFalse(player.Grounded, "took off");
            float x0 = player.Body.position.x;
            player.PressDash();
            yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Dash.Active, "dash on");
            yield return Until(() => !player.Dash.Active, 1f);
            float dashed = player.Body.position.x - x0;
            Debug.Log($"[MERIDIAN] air dash moved {dashed:F2} m (facing {player.Facing})");
            Assert.AreEqual(AirDash.Distance * player.Facing, dashed, 0.15f, "about 1.62 m in the facing direction");
            if (!player.Grounded)
            {
                player.PressDash();
                yield return new WaitForFixedUpdate();
                Assert.IsFalse(player.Dash.Active, "no second dash in the same airtime");
            }
            yield return Until(() => player.Grounded, 4f);
            Assert.IsTrue(player.Grounded, "landed");
            yield return Until(() => player.Dash.CooldownLeft <= 0f, 1f);
            player.PressJump();
            yield return Until(() => !player.Grounded, 2f);
            player.PressDash();
            yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Dash.Active, "landing refreshed the dash");
            yield return Until(() => player.Grounded, 4f);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
