using System;
using System.Collections.Generic;
using Meridian.Core;
using UnityEngine;

namespace Meridian.Save
{
    /// <summary>
    /// state.json (Bible §10.7): player, ship, inventory, story, catalogue, bases, timers. Terrain
    /// lives beside it as terrain_&lt;planet&gt;.bin diffs. `version` drives migrations on load.
    /// </summary>
    [Serializable]
    public sealed class SaveData
    {
        public const int CurrentVersion = 1;

        public int version = CurrentVersion;
        public string savedAtUtc;
        public string gameVersion;
        public int worldSeed;

        public string currentPlanet;  // PlanetId name
        public string view;           // ViewMode name

        public PlayerSave player = new PlayerSave();
        public ShipSave ship = new ShipSave();
        public List<CargoStack> cargo = new List<CargoStack>();
        public StorySave story = new StorySave();
        public List<string> catalogue = new List<string>();
        public List<string> bases = new List<string>();
        public TimerSave timers = new TimerSave();
        public List<string> terrainFiles = new List<string>();
    }

    [Serializable]
    public sealed class PlayerSave
    {
        public Vector2 position;
        public float health = 100f;
        public bool aboard;
    }

    [Serializable]
    public sealed class ShipSave
    {
        public float hull = 100f;
        public float fuel = 100f;
        public float tankCapacity = 100f;
        public Vector2 sidePosition;
        public Vector2 sideVelocity;
        public Vector2 spacePosition;
        public Vector2 spaceVelocity;
        public float spaceHeading;
    }

    /// <summary>Story flags arrive with M5; the field exists now so v1 files already carry it.</summary>
    [Serializable]
    public sealed class StorySave
    {
        public List<string> flags = new List<string>();
    }

    [Serializable]
    public sealed class TimerSave
    {
        public double gameSeconds;
        public double playSeconds;
    }

    /// <summary>Upgrades older state.json files step by step; refuses files from a newer build.</summary>
    public static class SaveMigrations
    {
        public static SaveData Migrate(SaveData data)
        {
            if (data.version > SaveData.CurrentVersion)
                throw new InvalidOperationException($"save version {data.version} is newer than this build ({SaveData.CurrentVersion})");
            // v0 (pre-release) had no version field and no cargo list: JsonUtility reads version 0.
            if (data.version < 1)
            {
                data.cargo ??= new List<CargoStack>();
                data.story ??= new StorySave();
                data.timers ??= new TimerSave();
                data.version = 1;
            }
            return data;
        }
    }
}
