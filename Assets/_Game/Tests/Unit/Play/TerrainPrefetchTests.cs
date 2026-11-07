using System.Collections;
using Meridian.Art;
using Meridian.Perf;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-091 (PlayMode, no scene of its own): TerrainTileSet.Prefetch loads a planet's sheets ahead of the visit, each tracked
    /// under its own group; the planet's set takes the handles over in Load (one handle per sheet, ready at once when the
    /// prefetch finished), Dispose releases them, and a prefetch nobody takes over is dropped by the next Load.
    /// </summary>
    public class TerrainPrefetchTests
    {
        [SetUp]
        public void SetUp() => TerrainTileSet.ReleasePrefetch();

        [TearDown]
        public void TearDown() => TerrainTileSet.ReleasePrefetch();

        static int Keys(PlanetId p)
        {
            int n = 0;
            foreach (var id in TerrainStreamer.MaterialsFor(p)) if (TileId.ArtKey(id) != null) n++;
            return n;
        }

        static int Own(PlanetId p)
        {
            int n = 0;
            foreach (var id in TerrainStreamer.MaterialsFor(p)) { var k = TileId.ArtKey(id); if (k != null && !ArtKeys.IsSharedTerrain(k)) n++; }
            return n;
        }

        [UnityTest]
        public IEnumerator PrefetchIsTakenOverByThePlanetsSetAndReleasedWithIt()
        {
            int before = Residency.CountPlanet("planet_mars");
            int commonBefore = Residency.Count("common");
            TerrainTileSet.Prefetch(TerrainStreamer.MaterialsFor(PlanetId.Mars));
            Assert.AreEqual(Keys(PlanetId.Mars), TerrainTileSet.PrefetchedCount, "one handle per Mars sheet");
            Assert.AreEqual(before + Own(PlanetId.Mars), Residency.CountPlanet("planet_mars"), "tracked under planet_mars (the shared snow under common)");
            Assert.AreEqual(commonBefore + (Keys(PlanetId.Mars) - Own(PlanetId.Mars)), Residency.Count("common"), "the shared sheet counts for common");
            float until = Time.realtimeSinceStartup + 20f;
            while (!TerrainTileSet.PrefetchDone && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsTrue(TerrainTileSet.PrefetchDone, "the prefetch finished");

            var set = new TerrainTileSet();
            set.Load(TerrainStreamer.MaterialsFor(PlanetId.Mars));
            Assert.AreEqual(0, TerrainTileSet.PrefetchedCount, "the set took the handles over");
            Assert.IsTrue(set.IsReady, "finished handles make the set ready at once");
            Assert.AreEqual(before + Own(PlanetId.Mars), Residency.CountPlanet("planet_mars"), "still one handle per sheet (no double tracking)");
            Assert.NotNull(set.Get(TileId.Regolith, 0), "Mars regolith tiles built");

            set.Dispose();
            Assert.AreEqual(before, Residency.CountPlanet("planet_mars"), "Dispose releases the taken-over handles");
            Assert.AreEqual(commonBefore, Residency.Count("common"), "and the shared one");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator APrefetchForAnotherPlanetIsDroppedByTheNextLoad()
        {
            int earthBefore = Residency.CountPlanet("planet_earth"), marsBefore = Residency.CountPlanet("planet_mars");
            TerrainTileSet.Prefetch(TerrainStreamer.MaterialsFor(PlanetId.Earth));
            Assert.AreEqual(earthBefore + Own(PlanetId.Earth), Residency.CountPlanet("planet_earth"));
            TerrainTileSet.Prefetch(TerrainStreamer.MaterialsFor(PlanetId.Mars));
            Assert.AreEqual(earthBefore, Residency.CountPlanet("planet_earth"), "a new prefetch drops the old one");
            float until = Time.realtimeSinceStartup + 20f;
            while (!TerrainTileSet.PrefetchDone && Time.realtimeSinceStartup < until) yield return null;
            var set = new TerrainTileSet();
            set.Load(TerrainStreamer.MaterialsFor(PlanetId.Earth)); // the player went to Earth after all
            Assert.AreEqual(0, TerrainTileSet.PrefetchedCount, "Mars's prefetch is dropped by Earth's load");
            Assert.AreEqual(marsBefore, Residency.CountPlanet("planet_mars"), "nothing of Mars stays tracked");
            until = Time.realtimeSinceStartup + 20f;
            while (!set.IsReady && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsTrue(set.IsReady);
            Assert.AreEqual(earthBefore + Own(PlanetId.Earth), Residency.CountPlanet("planet_earth"));
            set.Dispose();
            Assert.AreEqual(earthBefore, Residency.CountPlanet("planet_earth"));
            LogAssert.NoUnexpectedReceived();
        }
    }
}
