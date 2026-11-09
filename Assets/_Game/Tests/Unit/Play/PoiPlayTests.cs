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
            int expected = System.Linq.Enumerable.Count(PoiCatalog.For(planet));
            Assert.AreEqual(expected, side.pois.placed.Count, $"{planet}: every POI placed");
            foreach (var p in side.pois.placed)
            {
                var poi = p.def;
                Assert.AreEqual(planet, poi.planet);
                Assert.IsTrue(state.HasFlag(poi.StampedFlag), $"{poi.id} stamped flag");
                Assert.AreEqual(poi.props.Length, p.props.Count, $"{poi.id} props");
                foreach (var sr in p.props) Assert.NotNull(sr.sprite, $"{poi.id}/{sr.name} has art or its placeholder");
                Assert.IsTrue(StampIntact(poi, p.groundY, -1, -1), $"{poi.id} tiles in the terrain: {lastMismatch}");
            }
            var hud = side.sideHud;
            int shown = 0;
            foreach (var t in hud.MarkerNames)
                foreach (var p in side.pois.placed)
                    if (p.def.marker && t.text.EndsWith(p.def.label)) shown++;
            Assert.AreEqual(side.pois.placed.FindAll(x => x.def.marker).Count, shown, $"{planet}: a HUD marker per POI (not the camp)");
        }

        readonly RaycastHit2D[] groundHits = new RaycastHit2D[8];

        /// <summary>The ground under x, from `fromY` down: the drawn outline (the terrain colliders) or a solid POI prop it stands on (the camp's
        /// pad under the crates), never `self`; NaN when none within 12 m.</summary>
        float OutlineUnder(float x, float fromY, Collider2D self = null)
        {
            int n = Physics2D.Raycast(new Vector2(x, fromY), Vector2.down, new ContactFilter2D { useTriggers = false }, groundHits, 12f);
            var pois = director.PlanetSide.pois;
            float best = float.NaN, dist = float.MaxValue;
            for (int i = 0; i < n; i++)
            {
                var c = groundHits[i].collider;
                if (c == null || c == self || groundHits[i].distance >= dist || groundHits[i].distance <= 0f) continue; // a ray that starts inside a collider says nothing
                bool ground = c.GetComponentInParent<Meridian.Terrain.TerrainChunk>() != null || (c is BoxCollider2D b && System.Linq.Enumerable.Contains(pois.Solids, b));
                if (!ground) continue;
                dist = groundHits[i].distance; best = groundHits[i].point.y;
            }
            return best;
        }

        /// <summary>
        /// U-180: every POI structure on a smooth planet stands on the drawn ground: its base within 0.1 m of the highest ground under its
        /// footprint (the outline, or a solid prop it stands on), so none hovers over a gap and none sinks into a hill; props sunk by design
        /// (a hull in its gouge: dy between −3 and 0) are left out. Visits each POI so its chunks are built.
        /// </summary>
        readonly System.Collections.Generic.List<string> failures = new System.Collections.Generic.List<string>();

        IEnumerator AssertStructuresStand(PlanetId planet, System.Text.StringBuilder log)
        {
            var side = director.PlanetSide;
            var player = side.player;
            foreach (var p in side.pois.placed)
            {
                if (p.def.Floating) continue; // a floating station (Venus's aerostat) stands on nothing by design
                var at = new Vector2(p.def.CenterX, side.terrain.SurfaceAt(p.def.CenterX) + 2f);
                player.Body.position = at; player.transform.position = at; player.Body.linearVelocity = Vector2.zero;
                float until = Time.realtimeSinceStartup + 12f;
                yield return null;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                for (int i = 0; i < 5; i++) yield return new WaitForFixedUpdate();
                for (int k = 0; k < p.props.Count; k++)
                {
                    var prop = p.def.props[k];
                    if (prop.sunk) continue; // embedded by design (a hull in its gouge)
                    var basePt = (Vector2)p.props[k].transform.position;
                    var self = side.pois.ColliderOf(p.props[k]);
                    // it rests on the highest ground under its footprint (its middle and its quarter points: a crate stacked on two crates)
                    float ground = float.NaN;
                    foreach (float q in new[] { 0f, -0.4f, 0.4f })
                    {
                        float g = OutlineUnder(basePt.x + q * prop.size.x, basePt.y + 0.3f, self); // from just above the base: never from inside a crate stacked on it
                        if (!float.IsNaN(g) && (float.IsNaN(ground) || g > ground)) ground = g;
                    }
                    float gap = float.IsNaN(ground) ? float.NaN : basePt.y - ground;
                    log.Append($" {p.def.id}/{p.props[k].name} {gap:+0.00;-0.00}");
                    if (float.IsNaN(gap) || Mathf.Abs(gap) > 0.1f) failures.Add($"{planet} {p.def.id}/{p.props[k].name} (dx {prop.dx}, dy {prop.dy}): base {basePt.y:0.00}, ground {ground:0.00}");
                }
            }
        }

        [UnityTest, Timeout(480000)]
        public IEnumerator EveryPoiStructureStandsOnTheDrawnGround()
        {
            yield return Boot();
            var log = new System.Text.StringBuilder("[MERIDIAN] u180 base gaps (m):");
            try
            {
                foreach (var planet in new[] { PlanetId.Earth, PlanetId.Mars, PlanetId.Mercury, PlanetId.Venus })
                {
                    if (planet != PlanetId.Earth) yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(planet));
                    var side = director.PlanetSide;
                    if (side.hazards != null) { side.hazards.enabled = false; side.hazards.RestoreSuit(); }
                    side.creatures.autoSpawn = false; side.creatures.DespawnAll();
                    yield return AssertStructuresStand(planet, log);
                }
            }
            finally { TestContext.Out.WriteLine(log.ToString()); }
            Assert.IsEmpty(failures, "hovering over a gap or sunk into it (base more than 0.1 m off the ground under it): " + string.Join("; ", failures));
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>Every stamp cell in the live terrain (edits included), except the one at (skipCol, skipRow).</summary>
        string lastMismatch = "";

        bool StampIntact(PoiDef poi, int gy, int skipCol, int skipRow)
        {
            var t = director.PlanetSide.terrain;
            for (int row = 0; row < poi.stamp.Length; row++)
            for (int col = 0; col < poi.Width; col++)
            {
                if (col == skipCol && row == skipRow) continue;
                var want = PoiStamp.CellTile(poi.stamp[row][col], poi.planet);
                if (want == null) continue;
                if (t.GetTile(poi.x + col, PoiStamp.RowY(poi, row, gy)) != want.Value)
                {
                    lastMismatch = $"cell (col {col}, row {row}) at ({poi.x + col}, {PoiStamp.RowY(poi, row, gy)}): want {want.Value}, found {t.GetTile(poi.x + col, PoiStamp.RowY(poi, row, gy))}; ground y {gy}, the column's top {t.TopSolidY(poi.x + col)}";
                    return false;
                }
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
            var marker = side.sideHud.MarkerDistances[side.pois.placed.FindAll(x => x.def.marker).IndexOf(archive)];
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
