using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Save;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-030 (PlayMode): Earth and Mars POIs are stamped, have props and HUD markers; a dig into a stamp survives save/load.</summary>
    public class PoiPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string root;
        SceneDirector director;

        [SetUp]
        public void SetUp()
        {
            root = Path.Combine(Application.temporaryCachePath, "meridian_poi_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = root;
        }

        [TearDown]
        public void TearDown()
        {
            SaveSystem.RootOverride = null;
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
        }

        void AssertPlanetPois(PlanetId planet)
        {
            var side = director.PlanetSide;
            var state = GameState.Instance;
            Assert.AreEqual(2, side.pois.placed.Count, $"{planet}: two POIs placed");
            foreach (var p in side.pois.placed)
            {
                var poi = p.def;
                Assert.AreEqual(planet, poi.planet);
                Assert.IsTrue(state.HasFlag(poi.StampedFlag), $"{poi.id} stamped flag");
                Assert.AreEqual(poi.props.Length, p.props.Count, $"{poi.id} props");
                foreach (var sr in p.props) Assert.NotNull(sr.sprite, $"{poi.id}/{sr.name} has art or its placeholder");
                Assert.IsTrue(StampIntact(poi, p.groundY, -1, -1), $"{poi.id} tiles in the terrain");
            }
            var hud = side.sideHud;
            int shown = 0;
            foreach (var t in hud.MarkerNames)
                foreach (var p in side.pois.placed)
                    if (t.text.EndsWith(p.def.label)) shown++;
            Assert.AreEqual(2, shown, $"{planet}: a HUD marker per POI");
        }

        /// <summary>Every stamp cell in the live terrain (edits included), except the one at (skipCol, skipRow).</summary>
        bool StampIntact(PoiDef poi, int gy, int skipCol, int skipRow)
        {
            var t = director.PlanetSide.terrain;
            for (int row = 0; row < poi.stamp.Length; row++)
            for (int col = 0; col < poi.Width; col++)
            {
                if (col == skipCol && row == skipRow) continue;
                var want = PoiStamp.CellTile(poi.stamp[row][col], poi.planet);
                if (want == null) continue;
                if (t.GetTile(poi.x + col, PoiStamp.RowY(poi, row, gy)) != want.Value) return false;
            }
            return true;
        }

        [UnityTest]
        public IEnumerator EarthPoisStampedMarkedAndADigSurvivesSaveLoad()
        {
            yield return Boot();
            for (int i = 0; i < 3; i++) yield return null;
            AssertPlanetPois(PlanetId.Earth);
            var side = director.PlanetSide;
            var archive = side.pois.placed.Find(p => p.def == PoiCatalog.SurveyArchive);
            Assert.NotNull(archive);
            var marker = side.sideHud.MarkerDistances[side.pois.placed.IndexOf(archive)];
            int shownDistance = int.Parse(marker.text);
            Assert.That(shownDistance, Is.InRange(100, 160), "the Archive marker shows ~120 m from spawn");

            // Dig the first grass tile of the Archive's surface row.
            int x = PoiCatalog.SurveyArchive.x, y = PoiStamp.RowY(PoiCatalog.SurveyArchive, PoiCatalog.SurveyArchive.groundRow, archive.groundY);
            Assert.AreEqual(TileId.Grass, side.terrain.GetTile(x, y));
            Assert.IsTrue(side.terrain.SetTile(x, y, TileId.Air), "dug");
            var save = SaveSystem.Instance;
            save.Save();
            side.terrain.SetTile(x, y, TileId.Grass); // change it after the save
            yield return save.Load();
            float until = Time.realtimeSinceStartup + 20f;
            while (!director.PlanetSide.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            side = director.PlanetSide;
            Assert.AreEqual(TileId.Air, side.terrain.GetTile(x, y), "the dig survives save/load (the stamp is not written again)");
            Assert.IsTrue(StampIntact(PoiCatalog.SurveyArchive, archive.groundY, 0, PoiCatalog.SurveyArchive.groundRow), "rest of the Archive intact");
            Assert.IsTrue(GameState.Instance.HasFlag(PoiCatalog.SurveyArchive.StampedFlag), "flag loaded with the save");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator MarsPoisStampedAndMarked()
        {
            yield return Boot();
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Mars));
            for (int i = 0; i < 3; i++) yield return null;
            AssertPlanetPois(PlanetId.Mars);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
