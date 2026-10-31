using System.Collections;
using Meridian.Audio;
using Meridian.Core;
using Meridian.Space;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-016 (PlayMode): AudioDirector in Core reacts to jump, dig, place and ship thrust.</summary>
    public class AudioDirectorTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator SoundsFollowGameplayEvents()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var audio = AudioDirector.Instance;
            Assert.NotNull(audio, "AudioDirector in Core");
            Assert.NotNull(audio.jump); Assert.NotNull(audio.dig); Assert.NotNull(audio.ambient);
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate(); // player released and standing

            var side = director.PlanetSide;
            int count = audio.PlayCount;
            side.player.PressJump();
            for (int i = 0; i < 3; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(Sfx.Jump, audio.LastPlayed, "jump sound");
            Assert.Greater(audio.PlayCount, count);

            int x = side.spawnX + 2, y = side.terrain.TopSolidY(x);
            bool dug = side.rig.Dig(new Vector2(x + 0.5f, y + 0.5f));
            Assert.IsTrue(dug, $"dig: tile {side.terrain.GetTile(x, y)} at ({x},{y}), player at {side.player.Body.position}, active {side.player.gameObject.activeInHierarchy}");
            Assert.AreEqual(Sfx.Dig, audio.LastPlayed, "dig sound");
            // Open air above the hole (the dug item now lies in the hole and blocks the Builder).
            Assert.IsTrue(side.rig.Place(new Vector2(x + 0.5f, y + 3.5f), TileId.Stone), "place");
            Assert.AreEqual(Sfx.Place, audio.LastPlayed, "place sound");

            director.SetView(ViewMode.Space);
            yield return null;
            var ship = director.Space.GetComponentInChildren<SpaceShip>();
            ship.externalInput = true;
            ship.intent.thrust = 1f;
            yield return null; yield return null;
            Assert.IsTrue(audio.ThrustOn, "thrust loop on");
            ship.intent.thrust = 0f;
            yield return null; yield return null;
            Assert.IsFalse(audio.ThrustOn, "thrust loop off");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
