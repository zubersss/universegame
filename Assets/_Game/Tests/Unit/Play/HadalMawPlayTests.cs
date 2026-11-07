using System.Collections;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-119: the Hadal Maw in the coast deep builds its rig (six bones under a flipping pivot, the placeholder box hidden), plays the
    /// four-beat sway, opens its jaw and flares the lure when the surveyor comes inside 12 m, closes it again when they leave, and never
    /// bumps (D-087). The surveyor is carried to the ocean band's shore first so the shelf's chunks stream in.
    /// </summary>
    public class HadalMawPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        CreatureDirector creatures;

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            creatures = side.creatures;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
        }

        [UnityTest]
        public IEnumerator TheMawBuildsItsRigInTheCoastDeepAndReactsWithoutBiting()
        {
            yield return Boot();
            creatures.autoSpawn = false;
            creatures.DespawnAll();
            var spec = SpeciesSpec.Get(Species.HadalMaw);
            EarthBiomes.Range(Biome.Ocean, out int start, out int len);
            float y = side.player.Body.position.y;
            // The shore: the first water column from the band's start; the deep: the first column with the Maw's depth within 400 of it.
            int shore = start;
            while (shore < start + len && creatures.SiteAt(shore, y).aboveTile != TileId.Water) shore++;
            Assert.Less(shore, start + len, "the ocean band has water");
            int deep = shore;
            while (deep < shore + 400 && creatures.SiteAt(deep, y).waterDepth < spec.WaterDepthNeeded) deep++;
            Assert.Less(deep, shore + 400, $"deep water ({spec.WaterDepthNeeded} m) within 400 columns of the shore");
            TestContext.Out.WriteLine($"[MERIDIAN] maw: ocean band {start}+{len}, shore {shore}, deep column {deep} ({creatures.SiteAt(deep, y).waterDepth} m of water)");
            // The surveyor on the shore's last land column (the camera and the chunks follow), then the deep column's collision.
            int land = shore - 1;
            var stand = new Vector2(land + 0.5f, side.terrain.TopSolidY(land) + 1.1f);
            side.player.Body.position = stand; side.player.transform.position = stand; side.player.Body.linearVelocity = Vector2.zero;
            var follow = Object.FindAnyObjectByType<Meridian.Player.CameraFollow>();
            if (follow != null) follow.SnapToTarget();
            float until = Time.realtimeSinceStartup + 25f;
            while (!(side.terrain.IsSettled && side.terrain.IsCollisionReady(deep, side.terrain.TopSolidY(deep))) && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsTrue(side.terrain.IsCollisionReady(deep, side.terrain.TopSolidY(deep)), "the deep column's chunk streamed in");
            float py = side.player.Body.position.y;
            var maw = creatures.SpawnAt(Species.HadalMaw, deep, py);
            Assert.NotNull(maw, "the Maw spawns in the deep");
            Assert.AreEqual(Species.HadalMaw, maw.Spec.id);
            until = Time.realtimeSinceStartup + 15f;
            while (maw.Rig == null && Time.realtimeSinceStartup < until) yield return null;
            Assert.NotNull(maw.Rig, "the rig set (json + parts sheet + controller) builds");
            Assert.AreEqual(6, maw.Rig.Bones.Length, "six bones");
            Assert.IsFalse(maw.View.enabled, "the placeholder box hides behind the rig");
            yield return null; yield return null;
            Assert.NotNull(maw.Rig.Animator, "the sway Animator");
            Assert.IsTrue(maw.Rig.Animator.GetCurrentAnimatorStateInfo(0).IsName("hadal_maw"), "the sway state plays");
            var jaw = maw.Rig.Bone("jaw");
            Assert.NotNull(jaw, "the jaw bone");
            // The react: the surveyor inside the react radius (held still over the water) → the jaw opens; away again → it closes. No bump either way.
            side.player.Body.simulated = false;
            var near = maw.Body.position + new Vector2(6f, 2f);
            side.player.transform.position = near; side.player.Body.position = near;
            for (float t = 0f; t < 0.7f; t += Time.deltaTime) yield return null;
            Assert.IsTrue(maw.RigReacting, "inside 12 m: reacting");
            float open = Quaternion.Angle(Quaternion.identity, jaw.localRotation);
            var lure = maw.RigSlotRenderer("lure"); // a replaces_part slot: the lure bone's own renderer
            TestContext.Out.WriteLine($"[MERIDIAN] maw: jaw {open:F1}° open, lure {(lure != null && lure.sprite != null ? lure.sprite.name : "none")}, state {(maw.Rig.Animator.GetCurrentAnimatorStateInfo(0).IsName("hadal_maw") ? "sway" : "other")}");
            Assert.Greater(open, 15f, "the jaw opens toward −24°");
            Assert.NotNull(lure, "the lure slot resolves to a renderer");
            Assert.AreEqual("lure_flare", lure.sprite.name, "the lure flares while reacting");
            Assert.AreEqual(0, creatures.Bumps, "D-087: the Maw never bumps");
            var far = maw.Body.position + new Vector2(40f, 2f);
            side.player.transform.position = far; side.player.Body.position = far;
            for (float t = 0f; t < 0.7f; t += Time.deltaTime) yield return null;
            Assert.IsFalse(maw.RigReacting, "outside 12 m: calm");
            Assert.Less(Quaternion.Angle(Quaternion.identity, jaw.localRotation), 5f, "the jaw closes");
            Assert.AreNotEqual("lure_flare", lure.sprite.name, "the lure back on its cycle (lit 6 beats / dim 2)");
            Assert.IsTrue(lure.sprite.name == "lure_lit" || lure.sprite.name == "lure_dim", lure.sprite.name);
            side.player.Body.simulated = true;
            creatures.DespawnAll();
            LogAssert.NoUnexpectedReceived();
        }
    }
}
