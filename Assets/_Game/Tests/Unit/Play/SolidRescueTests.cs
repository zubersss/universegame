using System.Collections;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Player;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-156 / D-165 (a) (PlayMode, Earth): falling out of the world is impossible. A body buried 3 m under the smooth outline (which, unlike
    /// box colliders, has no inside to push it out) is lifted onto the surface within a few physics steps: the surveyor, a creature and a plain
    /// dynamic body (an item drop's shape). The surface is read off the outline's own edge collider.
    /// </summary>
    public class SolidRescueTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const float Depth = 3f, OnSurface = 0.1f; // on the outline, not under it: a round foot on a 35° slope rides 6.6 cm over the line at its centre
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
            player.externalInput = true; player.intent = default;
            side.dayNight.Override = 0.5f;
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();
            Assert.IsTrue(side.terrain.SmoothGround, "Earth's ground is the traced outline");
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
        }

        /// <summary>The outline's height over world x, off the chunk's edge collider.</summary>
        float Surface(float x)
        {
            int col = Mathf.FloorToInt(x);
            foreach (var h in Physics2D.RaycastAll(new Vector2(x, side.terrain.TopSolidY(col) + 4f), Vector2.down, 10f))
                if (h.collider is EdgeCollider2D && h.collider.GetComponent<TerrainChunk>() != null) return h.point.y;
            return float.NaN;
        }

        static float Bottom(Rigidbody2D b)
        {
            var list = new System.Collections.Generic.List<Collider2D>();
            b.GetAttachedColliders(list);
            float y = float.PositiveInfinity;
            foreach (var c in list) if (!c.isTrigger) y = Mathf.Min(y, c.bounds.min.y);
            return y;
        }

        IEnumerator SettleNear(float x)
        {
            // Walk the streamer there: the surveyor stands over the column first, so its chunks and their outlines are built.
            float s0 = side.terrain.TopSolidY(Mathf.FloorToInt(x)) + 2f;
            player.Body.position = new Vector2(x, s0); player.transform.position = player.Body.position;
            float timeout = Time.realtimeSinceStartup + 15f;
            yield return null;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 40; i++) yield return new WaitForFixedUpdate();
        }

        IEnumerator Lifted(Rigidbody2D body, string who, float x, float surface, int rescuesBefore)
        {
            for (int i = 0; i < 10 && SolidRescue.Rescues == rescuesBefore; i++) yield return new WaitForFixedUpdate();
            Assert.Greater(SolidRescue.Rescues, rescuesBefore, $"{who}: lifted");
            for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate();
            float bottom = Bottom(body), ex = body.position.x, under = Surface(ex); // where it stands now (a creature may have walked on)
            TestContext.Out.WriteLine($"[MERIDIAN] u156 rescue {who}: buried at x {x:F1} to {surface - Depth:F2} (outline {surface:F2}); ends at x {ex:F2}, feet {bottom:F2}, outline there {under:F2}");
            Assert.AreEqual(under, bottom, OnSurface, $"{who}: ends on the surface");
        }

        [UnityTest]
        public IEnumerator BodiesBuriedThreeMetresUnderTheOutlineEndOnTheSurface()
        {
            yield return Boot();
            float x = Mathf.Floor(player.Body.position.x) + 48.5f; // natural ground past the camp's pad and props
            yield return SettleNear(x);
            float surface = Surface(x);
            Assert.IsFalse(float.IsNaN(surface), "an outline under the column");

            // The surveyor: its feet 3 m under the outline.
            int before = SolidRescue.Rescues;
            player.Body.linearVelocity = Vector2.zero;
            player.Body.position = new Vector2(x, surface - Depth); player.transform.position = player.Body.position;
            yield return Lifted(player.Body, "surveyor", x, surface, before);
            Assert.IsTrue(player.Grounded, "the surveyor stands on the outline");

            // A creature beside it.
            float cx = x + 3f, cs = Surface(cx);
            var spec = SpeciesSpec.Get(Species.Stag);
            before = SolidRescue.Rescues; // any lift from the spawn on (a held creature is lifted in the step it is released)
            var stag = side.creatures.Spawn(Species.Stag, new Vector2(cx, cs - Depth + spec.size.y * 0.5f));
            Assert.NotNull(stag);
            for (int i = 0; i < 300 && stag.Held; i++) yield return new WaitForFixedUpdate();
            yield return Lifted(stag.Body, "stag", cx, cs, before);
            side.creatures.Despawn(stag);

            // A plain dynamic body (an item drop's shape).
            float bx = x - 3f, bs = Surface(bx);
            var go = new GameObject("RescueBox");
            var box = go.AddComponent<Rigidbody2D>();
            go.AddComponent<BoxCollider2D>().size = Vector2.one * 0.4f;
            box.position = new Vector2(bx, bs - Depth); go.transform.position = box.position;
            before = SolidRescue.Rescues;
            SolidRescue.Register(box);
            yield return Lifted(box, "box", bx, bs, before);
            SolidRescue.Unregister(box);
            Object.Destroy(go);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
