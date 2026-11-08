using System.Collections;
using Meridian.Core;
using Meridian.Hazards;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-068 (PlayMode): the suit meter shows a giant's band level when the surveyor stands at that height. The
    /// cloud column arrives with U-061, so (like HazardV2PlayTests for Mercury) the hazards are configured for a
    /// giant on the Earth scene and read a stub body placed at each band's height.
    /// </summary>
    public class GiantBandsPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator SuitMeterShowsTheBandLevel()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            var hazards = side.hazards;
            hazards.enabled = false; // stepped by hand
            var hud = Object.FindAnyObjectByType<Meridian.UI.SideHud>();
            hud.enabled = true;

            var stub = new GameObject("GiantBandStub").transform;
            float x = side.player.Body.position.x - 30f; // away from the ship's warmth
            hazards.body = stub;
            hazards.Equip(0);

            var cases = new (PlanetId planet, float y, string kind, string level)[]
            {
                (PlanetId.Jupiter, 1000f, "RADIATION", "3"), // Deck 1: belts
                (PlanetId.Jupiter, 750f, "RADIATION", "1"),  // Deck 2: shielded to 1
                (PlanetId.Jupiter, 280f, "THERMAL", "2"),    // Deep
                (PlanetId.Saturn, 1000f, "CRYO", "2"),       // Deck 1
                (PlanetId.Uranus, 750f, "CRYO", "3"),        // Deck 2
                (PlanetId.Neptune, 120f, "PRESSURE", "3"),   // low Deep
            };
            foreach (var c in cases)
            {
                hazards.ConfigureFor(GameState.Instance.catalog.Get(c.planet));
                stub.position = new Vector3(x, c.y, 0f);
                hazards.Step(0f);
                yield return null;
                Assert.AreEqual(c.kind, hud.HazardLabel.text, $"{c.planet} y {c.y}");
                Assert.AreEqual(c.level, hud.CryoText.text, $"{c.planet} y {c.y}");
            }
            Object.Destroy(stub.gameObject);
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>
        /// U-153 (P-52, the u127 finding): on Jupiter, standing on a Deck 2 floe at least 200 m above its band's floor, the deck set hangs off
        /// the floe under the camera (its datum the floe's top, not the band's floor 200 m below), so its far layer covers the frame from the
        /// floe line to the frame's top; the floe draws its own strip with both caps (no block tiles, no column strip on a floe out of frame).
        /// </summary>
        [UnityTest, Timeout(180000)]
        public IEnumerator JupiterDeckSetHangsOffTheFloeUnderTheCamera()
        {
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
                yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Jupiter));
                var side = director.PlanetSide;
                timeout = Time.realtimeSinceStartup + 20f;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
                if (side.hazards != null) side.hazards.enabled = false;
                side.creatures.autoSpawn = false;
                side.creatures.DespawnAll();
                var stage = side.cartoon;
                Assert.IsTrue(stage != null && stage.Active, "the cartoon stage is on for Jupiter");
                var t = side.terrain;
                bool Solid(int x, int y) => Meridian.Terrain.TileId.IsSolid(t.GetTile(x, y));
                const int Floor = Meridian.Terrain.CloudColumn.CloudLayout.Deck2Bottom;
                int fx = 0, fy = 0;
                bool found = false;
                for (int x = side.spawnX; x < side.spawnX + 2000 && !found; x++)
                    for (int y = Meridian.Terrain.CloudColumn.CloudLayout.Deck1Bottom - 2; y >= Floor + 200 && !found; y--)
                    {
                        if (!Solid(x, y) || Solid(x, y + 1) || Solid(x - 1, y)) continue; // a floe's left end column, its top row
                        bool wide = true;
                        for (int k = 1; k < 6 && wide; k++) wide = Solid(x + k, y) && !Solid(x + k, y + 1);
                        if (wide) { fx = x; fy = y + 1; found = true; }
                    }
                Assert.IsTrue(found, "a Deck 2 floe 200 m or more above the band's floor");
                var body = side.player.Body;
                body.simulated = false;
                var feet = new Vector2(fx + 2.5f, fy + 0.05f);
                body.position = feet; side.player.transform.position = feet;
                var cam = side.sideCamera;
                timeout = Time.realtimeSinceStartup + 15f;
                while ((stage.Fading || stage.Layers.placeholders.Contains(true) || Mathf.Abs(stage.Layers.datumY - fy) > 0.25f
                        || Mathf.Abs(cam.transform.position.y - Meridian.View2D.ParallaxMath.AnchorY(fy)) > 0.25f) && Time.realtimeSinceStartup < timeout)
                    yield return null;
                for (int i = 0; i < 10; i++) yield return null;
                var far = stage.Layers.renderers[0];
                float half = cam.orthographicSize, top = cam.transform.position.y + half;
                TestContext.Out.WriteLine($"[MERIDIAN] u153 floe at ({fx}, {fy}), {fy - Floor} m above deck2's floor: scene {stage.Scene}, datum {stage.Layers.datumY:F2} (floe datum {stage.FloeDatum:F2}), camera y {cam.transform.position.y:F2}, layer0 {far.bounds.min.y:F2}–{far.bounds.max.y:F2} vs frame {top - 2f * half:F2}–{top:F2}; floes {stage.Ground.FloesShown}, floe columns {stage.Ground.FloeColumnsShown}, caps {stage.Ground.CapsShown}");
                Assert.AreEqual(fy, stage.Layers.datumY, 0.25f, "the deck set hangs off the floe under the camera, not the band's floor");
                Assert.LessOrEqual(far.bounds.min.y, fy + 0.05f, "the far layer reaches down to the floe line");
                Assert.GreaterOrEqual(far.bounds.max.y, top - 0.05f, "and up to the frame's top: no flat wash");
                Assert.GreaterOrEqual(stage.Ground.FloesShown, 1, "the floe in view is laid");
                Assert.AreEqual(Meridian.View2D.GroundStrip.JupiterStripFor(fx + 2, Meridian.Terrain.TileId.FloeIce), stage.Ground.FloeMaterialAt(fx + 2), "its own kind's strip");
                Assert.GreaterOrEqual(stage.Ground.CapsShown, 2, "with its caps");
                body.simulated = true;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }
    }
}
