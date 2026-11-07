using System.Collections;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Creatures.Wardens;
using Meridian.Player;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-093 (PlayMode, Earth; D-087 no combat): a creature or Warden contact is a bump: the surveyor is knocked
    /// 0.8 m away from it over 0.12 s with the bump clip, and no meter moves (Suit power, hull, the pack).
    /// </summary>
    public class BumpTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;
        PlayerVitals vitals;

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
            vitals = player.GetComponent<PlayerVitals>();
            player.externalInput = true;
            player.intent = default;
            side.hazards.enabled = false; // only the bump acts on the surveyor here
            side.hazards.RestoreSuit();
            vitals.Restore();
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Grounded, "standing at the camp");
        }

        struct Meters { public float reserve, suit, hull; public int pack; }

        Meters Read()
        {
            var state = GameState.Instance;
            int pack = 0;
            if (state != null && state.inventory != null)
                for (int s = 0; s < Meridian.Items.Inventory.SlotCount; s++) pack += state.inventory[s].count;
            return new Meters { reserve = vitals.health, suit = side.hazards.SuitIntegrity, hull = state != null ? state.hull : 0f, pack = pack };
        }

        void AssertUnchanged(Meters a, Meters b)
        {
            Assert.AreEqual(a.reserve, b.reserve, 1e-4f, "Suit power reserve unchanged");
            Assert.AreEqual(a.suit, b.suit, 1e-4f, "suit integrity unchanged");
            Assert.AreEqual(a.hull, b.hull, 1e-4f, "hull unchanged");
            Assert.AreEqual(a.pack, b.pack, "the pack unchanged");
        }

        [UnityTest]
        public IEnumerator ACreatureBumpKnocksPointEightMetresAndChangesNoMeter()
        {
            yield return Boot();
            var feet = player.Body.position;
            var wolf = side.creatures.Spawn(Species.GreyWolf, feet + new Vector2(-1.2f, 0.6f)); // on the left: the knock goes right
            Assert.NotNull(wolf, "a wolf beside the surveyor");
            var before = Read();
            int bumps = player.BumpCount;
            float x0 = player.Body.position.x;
            side.creatures.Bump(wolf, Time.time);
            Assert.AreEqual(bumps + 1, player.BumpCount, "one bump");
            side.creatures.Despawn(wolf); // nothing else touches the surveyor while the knock runs
            for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate(); // 0.5 s: the knock and any settling
            float moved = player.Body.position.x - x0;
            TestContext.Out.WriteLine($"[MERIDIAN] bump knock {moved:F3} m");
            Assert.AreEqual(PlayerController.KnockDistance, moved, 0.05f, "0.8 m away from the creature");
            AssertUnchanged(before, Read());
            var view = player.GetComponentInChildren<PlayerView>();
            Assert.Greater(side.creatures.Bumps, 0, "the director counted it");
            if (view != null) TestContext.Out.WriteLine($"[MERIDIAN] clip after the bump: {view.Clip}");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AChasingWolfBumpsOnContactAndNeverDrainsSuitPower()
        {
            yield return Boot();
            var feet = player.Body.position;
            var before = Read();
            var wolf = side.creatures.Spawn(Species.GreyWolf, feet + new Vector2(3f, 0.6f));
            Assert.NotNull(wolf);
            int bumps = player.BumpCount;
            float until = Time.realtimeSinceStartup + 6f;
            while (player.BumpCount == bumps && Time.realtimeSinceStartup < until) yield return null;
            Assert.Greater(player.BumpCount, bumps, "the wolf reached the surveyor and bumped them");
            var view = player.GetComponentInChildren<PlayerView>();
            yield return null;
            // D-132: on the cartoon path the drawn surveyor (SpriteCharacterView) plays the clip; PlayerView is the 3D path's.
            var drawn = side.cartoon != null && side.cartoon.Active ? side.cartoon.Surveyor : null;
            string clip = drawn != null ? drawn.Clip : view != null ? view.Clip : null;
            if (clip != null)
                Assert.IsTrue(clip == SurveyorAnim.Bump || clip == SurveyorAnim.Hurt, $"the bump clip (or its stand-in), got {clip}");
            for (int i = 0; i < 120; i++) yield return null; // more contact, more bumps: still no meter moves
            AssertUnchanged(before, Read());
            Assert.IsFalse(vitals.Dead);
            side.creatures.Despawn(wolf);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AWardenSentinelBumpsOnContactAndNeverShoots()
        {
            yield return Boot();
            var wardens = side.wardens;
            Assert.NotNull(wardens, "WardenDirector on PlanetSide");
            var before = Read();
            var centre = player.Body.position + new Vector2(0f, 0.9f);
            var s = wardens.Spawn(centre + new Vector2(0.3f, 0f), centre, SentinelState.Hunt);
            Assert.NotNull(s, "a hunting sentinel right on the surveyor");
            int bumps = player.BumpCount;
            float until = Time.realtimeSinceStartup + 3f;
            while (player.BumpCount == bumps && Time.realtimeSinceStartup < until) yield return null;
            Assert.Greater(player.BumpCount, bumps, "contact bumps");
            Assert.Greater(wardens.Bumps, 0);
            for (int i = 0; i < 90; i++) yield return null;
            AssertUnchanged(before, Read());
            LogAssert.NoUnexpectedReceived();
        }
    }
}
