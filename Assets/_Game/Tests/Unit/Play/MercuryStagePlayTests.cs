using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-123: a Mercury entry on the cartoon stage — the set picked by the terminator's zone at the spawn, the 3D stage and backdrop off, no error for art not
    /// exported yet (every Mercury key is probed), and the set and the strips re-picked when the clock moves the band over the camp (midnight: the night set and
    /// the slate strip; noon: the day set and the regolith).
    /// </summary>
    public class MercuryStagePlayTests
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
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Mercury));
            side = director.PlanetSide;
            Assert.AreEqual(PlanetId.Mercury, side.Config.id);
            side.hazards.enabled = false;
            if (side.wardens != null) side.wardens.enabled = false;
            timeout = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
        }

        /// <summary>The dawn line sits where LocalTime = 0.25 (LocalTime(x) = 0.25 − (x − dawn) / W): for the camp at `localTime`, dawn = x + (localTime − 0.25) × W. The hazards' offset moves the clock the stage, the creatures and the flares share.</summary>
        IEnumerator SetCampLocalTime(float localTime)
        {
            int w = side.Config.worldWidth;
            side.hazards.mercuryClockOffset = 0;
            float dawn = MercuryTerminator.Dawn(side.cartoon.MercuryClock, w);
            float wantDawn = Mathf.Repeat(side.spawnX + 0.5f + (localTime - 0.25f) * w, w);
            side.hazards.mercuryClockOffset = Mathf.Repeat(wantDawn - dawn, w) * MercuryTerminator.CreepSecondsPerMetre;
            yield return null;
        }

        IEnumerator WaitScene(string scene, float seconds)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while ((side.cartoon.Scene != scene || side.cartoon.Fading) && Time.realtimeSinceStartup < until) yield return null;
        }

        [UnityTest]
        public IEnumerator MercuryPaintsByTheTerminatorAndFollowsItsCreep()
        {
            yield return Boot();
            var stage = side.cartoon;
            Assert.NotNull(stage, "CartoonStage on PlanetSide");
            Assert.IsTrue(stage.Active, "Mercury runs the cartoon path (U-123)");
            Assert.IsTrue(side.stage == null || !side.stage.gameObject.activeSelf, "the 3D stage layers are off");
            Assert.IsTrue(side.backdrop == null || !side.backdrop.enabled || !side.backdrop.gameObject.activeInHierarchy, "the 3D backdrop (its Sun sprite with it) is off");
            var layers = stage.Layers;
            Assert.NotNull(layers);
            StringAssert.StartsWith("backgrounds/mercury/", layers.SceneKey, "a Mercury set");
            int w = side.Config.worldWidth;
            Assert.Greater(w, 0, "the world width reaches the stage");
            string want = Meridian.View2D.CartoonStage.MercurySceneFor(side.spawnX, stage.MercuryClock, w);
            Assert.AreEqual(want, stage.Scene, "the spawn's zone picks the set");
            Assert.AreEqual(stage.Datum.At(side.spawnX), stage.Datum.At(side.spawnX + Meridian.View2D.BandDatum.PadHold), 1e-3f, "U-139: the pad holds its surface for PadHold columns (D-146's one-band plain now follows the averaged surface past it)");
            float ground = side.terrain.TopSolidY(side.spawnX) + 1f;
            TestContext.Out.WriteLine($"[MERIDIAN] D-146 pad: ground {ground:F1}, datum {stage.Datum.At(side.spawnX):F1} (Mercury datumY {side.Config.datumY})");
            Assert.AreEqual(ground, stage.Datum.At(side.spawnX), 2f, "D-146: the camp is on the plain, so the plain's datum is the ground at the pad (no 9 m crater under it)");
            bool sets = File.Exists($"Assets/_Game/Art/backgrounds/mercury/{want}/{want}.json");
            bool strips = File.Exists("Assets/_Game/Art/terrain/mercury/ground_strip.json") && File.Exists("Assets/_Game/Art/terrain/mercury/ground_strip_slate.json");
            bool rig = File.Exists("Assets/_Game/Art/flora/mercury/rigset.json");
            float until = Time.realtimeSinceStartup + 15f;
            while (((sets && layers.placeholders.Contains(true)) || (strips && stage.Ground.MaterialsLoaded < 2) || (rig && !stage.Flora.Ready)) && Time.realtimeSinceStartup < until) yield return null;
            TestContext.Out.WriteLine($"[MERIDIAN] mercury stage: spawn x {side.spawnX}, zone {MercuryTerminator.ZoneAt(side.spawnX, stage.MercuryClock, w)}, scene {stage.Scene} → {layers.SceneKey} (fallback used: {layers.UsedFallback}; set on disk {sets}), strips {(strips ? stage.Ground.MaterialsLoaded + " in" : "not exported yet (B-148)")}, rig set {(rig ? (stage.Flora.Ready ? stage.Flora.transform.childCount + " plants" : "not ready") : "not exported yet (B-148)")}, datum {stage.Datum.At(side.spawnX):F1}");
            if (sets) Assert.IsFalse(layers.placeholders.Contains(true), "the painted Mercury set is in");
            if (strips) { Assert.IsTrue(stage.Ground.Ready, "the Mercury strips"); Assert.AreEqual(2, stage.Ground.MaterialsLoaded, "regolith + slate"); }
            if (rig) Assert.IsTrue(stage.Flora.Ready, "the Mercury rig set");
            // The clock: the camp at midnight — the night set fades in and the strips go slate; then noon — the day set and the regolith.
            yield return SetCampLocalTime(0f);
            yield return WaitScene("night", 6f);
            Assert.AreEqual("night", stage.Scene, "midnight at the camp: the night set after the crossfade");
            Assert.AreEqual(Meridian.View2D.GroundStrip.Slate, Meridian.View2D.GroundStrip.MercuryStripFor(side.spawnX, stage.MercuryClock, w), "the rule says slate in the dark");
            if (strips) Assert.AreEqual(Meridian.View2D.GroundStrip.Slate, stage.Ground.MaterialAt(side.spawnX), "the slate strip drawn under the camp");
            yield return SetCampLocalTime(0.5f);
            yield return WaitScene("day", 6f);
            Assert.AreEqual("day", stage.Scene, "noon: the day set");
            Assert.AreEqual(Meridian.View2D.GroundStrip.MercuryRegolith, Meridian.View2D.GroundStrip.MercuryStripFor(side.spawnX, stage.MercuryClock, w));
            if (strips) Assert.AreEqual(Meridian.View2D.GroundStrip.MercuryRegolith, stage.Ground.MaterialAt(side.spawnX), "the blinding regolith in the sun");
            Assert.GreaterOrEqual(stage.Crossfades, 2, "two border crossfades ran (night, then day)");
            TestContext.Out.WriteLine($"[MERIDIAN] mercury creep: crossfades {stage.Crossfades}, scene {stage.Scene} → {stage.Layers.SceneKey}, strip at the camp {stage.Ground.MaterialAt(side.spawnX)}");
            side.hazards.mercuryClockOffset = 0;
            LogAssert.NoUnexpectedReceived();
        }
    }
}
