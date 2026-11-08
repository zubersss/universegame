using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Save;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-013 (PlayMode): save → load → identical state and terrain; backups; autosaves.</summary>
    public class SaveLoadTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string root;

        [SetUp]
        public void SetUp()
        {
            root = Path.Combine(Application.temporaryCachePath, "meridian_saves_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = root;
        }

        [TearDown]
        public void TearDown()
        {
            SaveSystem.RootOverride = null;
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }

        static IEnumerator Boot(System.Action<SceneDirector> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            done(director);
        }

        static IEnumerator Settle(TerrainStreamer t)
        {
            float timeout = Time.realtimeSinceStartup + 20f;
            while (!t.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
        }

        [UnityTest]
        public IEnumerator SaveThenLoadRestoresIdenticalStateAndTerrain()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var save = SaveSystem.Instance;
            Assert.NotNull(save, "SaveSystem in Core");
            var state = GameState.Instance;
            var side = director.PlanetSide;
            var t = side.terrain;
            var time = Object.FindAnyObjectByType<TimeSystem>();

            // Change the world and the run state.
            int x = side.spawnX - 3, y = t.TopSolidY(x);
            Assert.IsTrue(t.SetTile(x, y, TileId.Air));
            Assert.IsTrue(t.SetTile(x, y - 1, TileId.Air));
            int placedY = t.TopSolidY(x + 6) + 2; // remembered: the stone itself becomes the column's top
            Assert.IsTrue(t.SetTile(x + 6, placedY, TileId.Stone));
            state.hull = 73f; state.thrusterMark = 2;
            state.cargo.Add(new CargoStack { itemId = 3, count = 12 });
            time.SetGameSeconds(12345.0);
            var playerAt = side.player.Body.position;
            int editsBefore = t.Edits.Count;

            save.Save();
            Assert.IsTrue(File.Exists(Path.Combine(save.SlotFolder, "state.json")));
            Assert.IsTrue(File.Exists(Path.Combine(save.SlotFolder, "terrain_earth.bin")));

            // Mess everything up, then load.
            Assert.IsTrue(t.SetTile(x - 4, t.TopSolidY(x - 4), TileId.Air));
            state.hull = 5f; state.thrusterMark = 1; state.cargo.Clear(); time.SetGameSeconds(0);
            side.player.Body.position += new Vector2(20f, 5f);

            float loadStart = Time.realtimeSinceStartup;
            yield return save.Load();
            side = director.PlanetSide;
            t = side.terrain;
            yield return Settle(t);

            Assert.AreEqual(73f, state.hull, 1e-4f, "hull");
            Assert.AreEqual(2, state.thrusterMark, "thruster mark");
            Assert.AreEqual(1, state.cargo.Count); Assert.AreEqual(12, state.cargo[0].count, "cargo");
            // The clock is restored, then keeps running at 72× while the planet loads and settles.
            double ranSince = (Time.realtimeSinceStartup - loadStart) * TimeSystem.GameSecondsPerRealSecond;
            // + one 50 ms frame: the first frame after the load counts time from before loadStart was read.
            double oneFrame = 0.05 * TimeSystem.GameSecondsPerRealSecond;
            Assert.That(time.GameSeconds, Is.InRange(12345.0, 12345.0 + ranSince + oneFrame), "game clock");
            Assert.AreEqual(PlanetId.Earth, state.currentPlanet);
            Assert.AreEqual(editsBefore, t.Edits.Count, "same diffs");
            Assert.AreEqual(TileId.Air, t.GetTile(x, y), "dug tile still dug");
            Assert.AreEqual(TileId.Air, t.GetTile(x, y - 1));
            Assert.AreEqual(TileId.Stone, t.GetTile(x + 6, placedY), "placed tile back");
            Assert.AreNotEqual(TileId.Air, t.GetTile(x - 4, t.TopSolidY(x - 4)), "the post-save dig is undone");
            Assert.IsNull(t.RenderedTile(x, y), "terrain drawn from the loaded diffs");
            Assert.AreEqual(playerAt.x, side.player.Body.position.x, 0.05f, "player position");
            Assert.AreEqual(playerAt.y, side.player.Body.position.y, 0.05f);
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>
        /// U-157 (D-162 (6), D-165 (3)): a 0.4.8 slot (state v2, Earth's terrain diffs stamped against the blocky ground, plus a dig of the
        /// player's) loads onto the smooth ground: the old stamp diffs go, the camp re-stamps on the smoothed ground (its flags set again), and
        /// the player's dig stays.
        /// </summary>
        [UnityTest]
        public IEnumerator AVersionTwoSaveReStampsEarthOnTheSmoothGround()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var save = SaveSystem.Instance;
            var state = GameState.Instance;
            var cfg = director.PlanetSide.Config;
            Assert.IsTrue(director.PlanetSide.terrain.SmoothGround, "Earth's ground is smooth");
            var camp = Meridian.Planet.POI.PoiCatalog.SpawnCamp;
            Assert.IsTrue(state.HasFlag(camp.StampedFlag), "a new world stamps its camp");
            save.Save();

            // The slot as 0.4.8 wrote it: state v2; Earth's diffs from the old stamping, and a dig into solid ground off the stamps.
            var old = new TerrainEdits();
            bool was = GroundField.ForceBlocks;
            GroundField.ForceBlocks = true;
            SolidWorldGenerator raw;
            try
            {
                raw = new SolidWorldGenerator(cfg, state.worldSeed);
                foreach (var poi in Meridian.Planet.POI.PoiCatalog.For(PlanetId.Earth)) Meridian.Planet.POI.PoiStamp.Apply(poi, raw, old, cfg.datumY);
            }
            finally { GroundField.ForceBlocks = was; }
            var oldStamps = old.Cells();
            int digX = camp.x + camp.Width + 300, digY = 0;
            for (; digX < camp.x + camp.Width + 400; digX++)
            {
                digY = raw.SurfaceHeight(digX) - 2;
                if (TileId.IsSolid(raw.TileAt(digX, digY)) && !old.TryGet(digX, digY, out _)) break;
            }
            old.Set(digX, digY, TileId.Air, raw.TileAt(digX, digY));
            old.SaveFile(Path.Combine(save.SlotFolder, "terrain_earth.bin"));
            var statePath = Path.Combine(save.SlotFolder, "state.json");
            File.WriteAllText(statePath, System.Text.RegularExpressions.Regex.Replace(File.ReadAllText(statePath), @"""version"":\s*\d+", "\"version\": 2"));
            Assert.AreEqual(2, SaveSystem.ReadState(save.SlotFolder).loadedVersion, "the slot reads as v2");

            yield return save.Load();
            var side = director.PlanetSide;
            var t = side.terrain;
            yield return Settle(t);

            // The stamping the smooth ground gets, for comparison.
            var smooth = new TerrainEdits();
            var gen = new SolidWorldGenerator(cfg, state.worldSeed);
            foreach (var poi in Meridian.Planet.POI.PoiCatalog.For(PlanetId.Earth)) Meridian.Planet.POI.PoiStamp.Apply(poi, gen, smooth, cfg.datumY);
            int pad = Meridian.Planet.POI.PoiStamp.GroundY(camp, gen, cfg.datumY), mid = camp.x + camp.Width / 2;
            Assert.IsTrue(state.HasFlag(camp.StampedFlag), "the camp re-stamped (its flag set again)");
            Assert.AreEqual(pad, t.TopSolidY(mid), "the camp's pad stands on the smoothed ground");
            Assert.AreEqual(TileId.Air, t.GetTile(digX, digY), "the player's dig stays");
            int stale = 0;
            foreach (var (x, y, id) in oldStamps)
            {
                if (smooth.TryGet(x, y, out byte now) && now == id) continue; // the new stamping writes the same there
                if (t.Edits.TryGet(x, y, out byte cur) && cur == id) stale++;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u157 v2 load: {oldStamps.Count} old stamp diffs, {stale} stale left, camp pad {pad}, edits now {t.Edits.Count}");
            Assert.AreEqual(0, stale, "no 0.4.8 stamp diff is left standing");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator SavesRotateIntoThreeBackups()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var save = SaveSystem.Instance;
            var state = GameState.Instance;
            for (int i = 1; i <= 5; i++)
            {
                state.hull = i * 10f;
                save.Save();
            }
            var backups = Path.Combine(save.SlotFolder, "backups");
            Assert.AreEqual(50f, SaveSystem.ReadState(save.SlotFolder).ship.hull, "current = 5th save");
            Assert.AreEqual(40f, SaveSystem.ReadState(Path.Combine(backups, "1")).ship.hull, "backup 1 = 4th");
            Assert.AreEqual(30f, SaveSystem.ReadState(Path.Combine(backups, "2")).ship.hull, "backup 2 = 3rd");
            Assert.AreEqual(20f, SaveSystem.ReadState(Path.Combine(backups, "3")).ship.hull, "backup 3 = 2nd");
            Assert.IsFalse(Directory.Exists(Path.Combine(backups, "4")), "only three backups");
        }

        [UnityTest]
        public IEnumerator AutosavesOnTimerAndAfterTransition()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var save = SaveSystem.Instance;
            int before = save.SaveCount;
            save.autosaveInterval = 1f; // the 5-minute timer, shortened for the test
            float timeout = Time.realtimeSinceStartup + 5f;
            while (save.SaveCount == before && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.Greater(save.SaveCount, before, "timer autosave");
            save.autosaveInterval = SaveSystem.AutosaveSeconds;

            // Launch → autosave in space.
            var transitions = Object.FindAnyObjectByType<Meridian.Transitions.TransitionDirector>();
            var ship = director.PlanetSide.ship;
            ship.GetComponent<Meridian.Ship.ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, director.PlanetSide.Config.EscapeLineY - 0.5f);
            ship.Body.position = p; ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            int beforeLaunch = save.SaveCount;
            timeout = Time.realtimeSinceStartup + 10f;
            while (save.SaveCount == beforeLaunch && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.Greater(save.SaveCount, beforeLaunch, "autosave after the launch transition");
            Assert.AreEqual("Space", SaveSystem.ReadState(save.SlotFolder).view);
        }
    }
}
