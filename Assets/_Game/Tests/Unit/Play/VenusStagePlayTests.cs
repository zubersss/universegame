using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Terrain;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-125: a Venus entry on the cartoon stage — the surface set at the ground, the 3D stage and backdrop off, no error for art not exported yet (every
    /// Venus key is probed); the surveyor carried up to the Meridian station: the deck set fades in, hung off the cloud deck, and the deck planks lie along
    /// the station; back down: the surface set again.
    /// </summary>
    public class VenusStagePlayTests
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
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Venus));
            side = director.PlanetSide;
            Assert.AreEqual(PlanetId.Venus, side.Config.id);
            side.hazards.enabled = false;
            if (side.wardens != null) side.wardens.enabled = false;
            timeout = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
        }

        IEnumerator WaitScene(string scene, float seconds)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while ((side.cartoon.Scene != scene || side.cartoon.Fading) && Time.realtimeSinceStartup < until) yield return null;
        }

        /// <summary>Holds the surveyor at (x, y) with physics off, so the camera follows it there and nothing falls while the check reads.</summary>
        IEnumerator Carry(float x, float y)
        {
            var body = side.player.GetComponent<Rigidbody2D>();
            if (body != null) { body.simulated = false; body.position = new Vector2(x, y); }
            side.player.transform.position = new Vector3(x, y, side.player.transform.position.z);
            for (int i = 0; i < 3; i++) yield return null;
        }

        [UnityTest]
        public IEnumerator VenusPaintsTheSurfaceBelowAndTheDeckAboveTheLine()
        {
            yield return Boot();
            var stage = side.cartoon;
            Assert.NotNull(stage, "CartoonStage on PlanetSide");
            Assert.IsTrue(stage.Active, "Venus runs the cartoon path (U-125)");
            Assert.IsTrue(side.stage == null || !side.stage.gameObject.activeSelf, "the 3D stage layers are off");
            Assert.IsTrue(side.backdrop == null || !side.backdrop.enabled || !side.backdrop.gameObject.activeInHierarchy, "the 3D backdrop is off");
            var layers = stage.Layers;
            StringAssert.StartsWith("backgrounds/venus/", layers.SceneKey, "a Venus set");
            float ground = side.terrain.TopSolidY(side.spawnX) + 1f;
            Assert.Less(ground, CartoonStage.VenusDeckLeaveY, "the entry is on the ground, far under the cloud deck");
            Assert.AreEqual(CartoonStage.VenusSurfaceScene, stage.Scene, "at the ground: the surface dive");
            bool surface = File.Exists("Assets/_Game/Art/backgrounds/venus/surface/surface.json");
            bool deck = File.Exists("Assets/_Game/Art/backgrounds/venus/deck/deck.json");
            bool crust = File.Exists("Assets/_Game/Art/terrain/venus/ground_strip.json");
            bool planks = File.Exists("Assets/_Game/Art/terrain/venus/ground_strip_deck.json");
            bool rig = File.Exists("Assets/_Game/Art/flora/venus/rigset.json");
            float until = Time.realtimeSinceStartup + 15f;
            while (((surface && layers.placeholders.Contains(true)) || (crust && !stage.Ground.Ready) || (rig && !stage.Flora.Ready)) && Time.realtimeSinceStartup < until) yield return null;
            TestContext.Out.WriteLine($"[MERIDIAN] venus stage: spawn x {side.spawnX}, ground {ground:F1}, scene {stage.Scene} → {layers.SceneKey} (fallback {layers.UsedFallback}; on disk: surface {surface}, deck {deck}, crust {crust}, planks {planks}, rig {rig}), datum {layers.datumY:F1}, plant sprites {stage.Flora.SpriteCount}");
            if (surface) Assert.IsFalse(layers.placeholders.Contains(true), "the painted surface set is in");
            if (crust) Assert.AreEqual(GroundStrip.VenusCrust, stage.Ground.MaterialAt(side.spawnX), "the basalt crust under the entry");
            if (rig) Assert.IsTrue(stage.Flora.Ready, "the Venus rig set");

            // Up to the Meridian station: the deck set fades in, hung off the cloud deck; the planks lie along the station.
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            float deckTop = station.floatY + Meridian.Planet.POI.PoiCatalog.DeckTop;
            yield return Carry(station.x + station.floatWidth * 0.5f, deckTop + 1f);
            // B-168: the deck's standing surface stays at floatY + DeckTop whatever the art (the json's top_row on the v3 deck, the catalog row before it).
            bool hitTriggers = Physics2D.queriesHitTriggers;
            Physics2D.queriesHitTriggers = false; // the door's and hulls' interaction triggers are not the floor
            var stand = Physics2D.Raycast(new Vector2(station.x + 2.5f, deckTop + 3f), Vector2.down, 6f); // a bare stretch of the first deck (clear of the cell at 1.2 and the hull at 5)
            Physics2D.queriesHitTriggers = hitTriggers;
            Assert.IsNotNull(stand.collider, "the deck is solid under the station");
            Assert.AreEqual(deckTop, stand.point.y, 0.3f, "the surveyor stands on the deck's surface (LEAD's M3Inner tolerance)");
            yield return WaitScene(CartoonStage.VenusDeckScene, 8f);
            Assert.AreEqual(CartoonStage.VenusDeckScene, stage.Scene, "on the station: the deck set after the crossfade");
            StringAssert.StartsWith("backgrounds/venus/", stage.Layers.SceneKey);
            Assert.AreEqual(VenusLandforms.DeckY - 2f, stage.Layers.datumY, 0.01f, "the deck set hangs off the cloud deck");
            if (planks)
            {
                until = Time.realtimeSinceStartup + 5f;
                while (stage.Ground.DeckFramesShown == 0 && Time.realtimeSinceStartup < until) yield return null;
                Assert.Greater(stage.Ground.DeckFramesShown, 0, "the deck planks along the station");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] venus deck: scene {stage.Scene} → {stage.Layers.SceneKey}, datum {stage.Layers.datumY:F1}, plank frames {stage.Ground.DeckFramesShown}, crossfades {stage.Crossfades}");

            // Back down to the entry: the surface set again.
            yield return Carry(side.spawnX + 0.5f, ground + 1f);
            yield return WaitScene(CartoonStage.VenusSurfaceScene, 8f);
            Assert.AreEqual(CartoonStage.VenusSurfaceScene, stage.Scene, "back on the ground: the surface set");
            Assert.AreEqual(0, stage.Ground.DeckFramesShown, "no planks in view on the ground");
            Assert.GreaterOrEqual(stage.Crossfades, 2, "two height crossfades ran (up, then down)");
            var body = side.player.GetComponent<Rigidbody2D>();
            if (body != null) body.simulated = true;
            LogAssert.NoUnexpectedReceived();
        }
    }
}
