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
    /// <summary>U-088 (PlayMode, Earth): one dash per airtime; a parried wolf bite does 0 damage and staggers it; a parried Warden bolt flies back along the aim.</summary>
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

        [UnityTest]
        public IEnumerator AParriedWolfBiteDoesNoDamageAndStaggersIt()
        {
            yield return Boot();
            var creatures = side.creatures;
            var feet = player.Body.position;
            var wolf = creatures.Spawn(Species.GreyWolf, feet + new Vector2(1.2f * player.Facing, 0.6f));
            Assert.NotNull(wolf, "a wolf beside the surveyor");
            var vitals = player.GetComponent<PlayerVitals>();
            float health = vitals.health;
            player.PressParry();
            yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Parry.Active, "parry window open");
            creatures.Bite(wolf, Time.time);
            Assert.AreEqual(health, vitals.health, 1e-4f, "a parried bite does 0 damage");
            Assert.IsTrue(wolf.IsStaggered, "the wolf staggers");
            Assert.IsTrue(player.Dash.Available, "the parry refreshes the dash");
            float t0 = Time.time;
            yield return Until(() => !wolf.IsStaggered, 2f);
            Debug.Log($"[MERIDIAN] wolf staggered {Time.time - t0:F2} s");
            Assert.AreEqual(Creature.StaggerSeconds, Time.time - t0, 0.1f, "1.2 s stagger");
            // Outside the window the same bite lands.
            yield return Until(() => player.Parry.Ready, 1f);
            creatures.Bite(wolf, Time.time);
            Assert.Less(vitals.health, health, "an unparried bite hurts");
            creatures.Despawn(wolf);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AParriedWardenBoltFliesBackAlongTheAim()
        {
            yield return Boot();
            var wardens = side.wardens;
            Assert.NotNull(wardens, "WardenDirector on PlanetSide");
            var feet = player.Body.position;
            var target = feet + new Vector2(0f, 0.9f);
            player.Aim = new Vector2(0.6f, 0.8f).normalized;
            var from = target + new Vector2(-2.8f, 0f);
            Assert.IsTrue(wardens.Fire(from, Vector2.right), "a bolt flies at the surveyor");
            float suit = side.hazards.SuitIntegrity;
            // Open the window just before the bolt arrives (14 m/s over 2.8 m ≈ 0.2 s; the window lasts 0.12 s).
            yield return Until(() => wardens.TryGetBolt(0, out var p, out _, out _) && (p - target).x > -1.4f, 1f);
            player.PressParry();
            yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Parry.Active, "parry window open");
            yield return Until(() => wardens.TryGetBolt(0, out _, out _, out bool r) && r, 1f);
            Assert.IsTrue(wardens.TryGetBolt(0, out _, out var dir, out bool reflected) && reflected, "the bolt was reflected");
            Debug.Log($"[MERIDIAN] reflected bolt direction {dir} (aim {player.Aim})");
            Assert.AreEqual(1f, Vector2.Dot(dir, player.Aim), 0.02f, "back along the aim");
            Assert.AreEqual(suit, side.hazards.SuitIntegrity, 1e-4f, "no suit damage");
            yield return Until(() => wardens.BoltsLive == 0, 3f);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
