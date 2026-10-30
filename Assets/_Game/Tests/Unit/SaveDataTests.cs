using System;
using Meridian.Core;
using Meridian.Save;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-013 (EditMode): state.json shape, version field, migrations, autosave interval.</summary>
    public class SaveDataTests
    {
        [Test]
        public void JsonRoundTripKeepsEveryField()
        {
            var d = new SaveData { worldSeed = 7, currentPlanet = "Mars", view = "Space" };
            d.player.position = new Vector2(64.5f, 338f); d.player.health = 51f; d.player.aboard = true;
            d.ship.hull = 73f; d.ship.fuel = 41.5f; d.ship.spacePosition = new Vector2(2550f, 30f); d.ship.spaceHeading = 90f;
            d.cargo.Add(new CargoStack { itemId = 3, count = 12 });
            d.timers.gameSeconds = 12345.5; d.terrainFiles.Add("terrain_earth.bin");
            var back = JsonUtility.FromJson<SaveData>(JsonUtility.ToJson(d));
            Assert.AreEqual(SaveData.CurrentVersion, back.version);
            Assert.AreEqual("Mars", back.currentPlanet); Assert.AreEqual("Space", back.view);
            Assert.AreEqual(d.player.position, back.player.position); Assert.IsTrue(back.player.aboard);
            Assert.AreEqual(73f, back.ship.hull); Assert.AreEqual(41.5f, back.ship.fuel);
            Assert.AreEqual(d.ship.spacePosition, back.ship.spacePosition);
            Assert.AreEqual(12, back.cargo[0].count);
            Assert.AreEqual(12345.5, back.timers.gameSeconds);
            Assert.AreEqual("terrain_earth.bin", back.terrainFiles[0]);
        }

        [Test]
        public void VersionFieldIsWrittenAndOldFilesMigrate()
        {
            StringAssert.Contains("\"version\": 1", JsonUtility.ToJson(new SaveData(), true));
            var v0 = JsonUtility.FromJson<SaveData>("{\"currentPlanet\":\"Earth\",\"view\":\"PlanetSide\"}");
            v0.version = 0; v0.cargo = null; v0.timers = null;
            var migrated = SaveMigrations.Migrate(v0);
            Assert.AreEqual(1, migrated.version);
            Assert.NotNull(migrated.cargo); Assert.NotNull(migrated.timers);
        }

        [Test]
        public void NewerSaveVersionIsRefused()
        {
            var future = new SaveData { version = SaveData.CurrentVersion + 1 };
            Assert.Throws<InvalidOperationException>(() => SaveMigrations.Migrate(future));
        }

        [Test]
        public void AutosaveEveryFiveMinutesAndThreeBackups()
        {
            Assert.AreEqual(300f, SaveSystem.AutosaveSeconds);
            Assert.AreEqual(3, SaveSystem.Backups);
            Assert.AreEqual("terrain_earth.bin", SaveSystem.TerrainFile(Meridian.Planets.PlanetId.Earth));
        }

        [Test]
        public void SaveRootIsLocalLowZubersMeridian()
        {
            SaveSystem.RootOverride = null;
            var root = SaveSystem.Root.Replace('\\', '/');
            StringAssert.EndsWith("/Zubers/MERIDIAN/saves", root, "Bible §10.7 + D-011");
            StringAssert.Contains("AppData/LocalLow", root);
        }
    }
}
