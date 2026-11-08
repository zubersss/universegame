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
    /// <summary>U-089 (PlayMode, Earth): a 7 m/s landing squashes the visual root to 0.7 at once and is back by 0.2 s with the collider untouched; a wolf hit shows the knock, the flash and the creature's squash.</summary>
    public class SquashPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;
        PlayerView view;
        Meridian.View2D.SpriteCharacterView drawn;
        Transform squashRoot;

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
            view = player.GetComponentInChildren<PlayerView>();
            Assert.NotNull(view, "PlayerView");
            // D-133: on the cartoon path the drawn surveyor (SpriteCharacterView) owns the squash root; PlayerView's is the 3D path's.
            drawn = side.cartoon != null && side.cartoon.Active ? side.cartoon.Surveyor : null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Grounded, "standing at the camp");
            squashRoot = drawn != null ? drawn.SquashRoot : view.VisualRoot;
            Assert.NotNull(squashRoot, "visual root");
        }

        [UnityTest]
        public IEnumerator ASevenMetrePerSecondLandingSquashesTheVisualRootOnly()
        {
            yield return Boot();
            var capsule = player.GetComponent<CapsuleCollider2D>();
            var size0 = capsule.size; var offset0 = capsule.offset; float g0 = player.Body.gravityScale;
            float drop = 7f * 7f / (2f * 9.81f); // 2.5 m: lands at 7.0 m/s on Earth
            var feet = player.Body.position;
            var up = feet + new Vector2(0f, drop);
            player.Body.position = up; player.transform.position = up; player.Body.linearVelocity = Vector2.zero;
            bool landed = false; float impact = 0f;
            void OnLanded(float s) { landed = true; impact = s; }
            player.Landed += OnLanded;
            float until = Time.realtimeSinceStartup + 4f;
            while (!landed && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
            player.Landed -= OnLanded;
            Assert.IsTrue(landed, "landed");
            yield return null; // the same frame's LateUpdate applied the squash
            float squashed = squashRoot.localScale.y;
            TestContext.Out.WriteLine($"[MERIDIAN] landing {impact:F1} m/s: visual y {squashed:F2} one frame after touchdown");
            Assert.AreEqual(7f, impact, 0.6f, "about 7 m/s");
            Assert.LessOrEqual(squashed, 0.76f, "squashed to ≈ 0.7 within one frame");
            Assert.AreEqual(size0, capsule.size, "capsule size unchanged");
            Assert.AreEqual(offset0, capsule.offset, "capsule offset unchanged");
            Assert.AreEqual(g0, player.Body.gravityScale, "body unchanged");
            float t0 = Time.time;
            while (Time.time - t0 < 0.2f) yield return null;
            Assert.AreEqual(1f, squashRoot.localScale.y, 0.02f, "1.0 ± 0.02 by 0.2 s");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AWolfBumpShowsKnockFlashAndTheCreatureSquashInTheSameFrame()
        {
            yield return Boot();
            var creatures = side.creatures;
            var feet = player.Body.position;
            var wolf = creatures.Spawn(Species.GreyWolf, feet + new Vector2(1.2f, 0.6f)); // to the right
            Assert.NotNull(wolf, "a wolf beside the surveyor");
            yield return new WaitForFixedUpdate();
            creatures.Bump(wolf, Time.time); // U-093 (D-087): a bump; the surveyor and the wolf both react
            yield return null;
            string clip = drawn != null ? drawn.Clip : view.Clip;
            bool flashing = drawn != null ? drawn.Flashing : view.Flashing;
            Assert.IsTrue(flashing, "the 2-frame white flash (U-122: on the drawn surveyor too)");
            Assert.IsTrue(clip == SurveyorAnim.Bump || clip == SurveyorAnim.Hurt, "bump (or its hurt stand-in)");
            yield return new WaitForFixedUpdate(); // the knock velocity lands in the fixed step (a fast frame may hold none)
            TestContext.Out.WriteLine($"[MERIDIAN] bump: player vx {player.Body.linearVelocity.x:F2} after the fixed step, flashing {flashing}, clip {clip}");
            Assert.Less(player.Body.linearVelocity.x, -3f, "knocked away from the wolf (left)");
            // The wolf bounces back: knock and squash on its visual root, the same frame.
            TestContext.Out.WriteLine($"[MERIDIAN] creature bump: visual y {wolf.Visual.localScale.y:F2}, vx {wolf.Body.linearVelocity.x:F2}");
            Assert.AreEqual(SquashStretch.HitScale, wolf.Visual.localScale.y, 0.03f, "0.85 squash");
            Assert.Greater(wolf.Body.linearVelocity.x, 2f, "bounced away from the surveyor (right)");
            var footprint = wolf.Box.size + Vector2.one * (2f * wolf.Box.edgeRadius); // U-156: rounded corners, the same footprint
            Assert.AreEqual(wolf.Spec.size.x, footprint.x, 1e-4f, "the creature's collider never scales"); Assert.AreEqual(wolf.Spec.size.y, footprint.y, 1e-4f, "the creature's collider never scales");
            creatures.Despawn(wolf);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
