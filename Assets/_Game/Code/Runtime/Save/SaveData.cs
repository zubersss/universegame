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
        public const int CurrentVersion = 3;

        public int version = CurrentVersion;
        /// <summary>U-157: the version the file was written at (set by SaveMigrations.Migrate; never saved).</summary>
        [NonSerialized] public int loadedVersion = CurrentVersion;
        public string savedAtUtc;
        public string gameVersion;
        public int worldSeed;

        public string currentPlanet;  // PlanetId name
        public string view;           // ViewMode name

        public PlayerSave player = new PlayerSave();
        public ShipSave ship = new ShipSave();
        public List<CargoStack> cargo = new List<CargoStack>();
        /// <summary>v2 (U-052): Halcyon Scrip and accepted cargo contracts (absent in early v2 files: the starting purse, none).</summary>
        public int scrip = Meridian.Trade.Market.StartingScrip;
        /// <summary>v2 (U-054): Survey Datacores (the catalogue ids are in `catalogue`).</summary>
        public int datacores;
        /// <summary>U-174 (D-174 / D-175): the Scrip earned by selling this expedition, and the dirt store's tiles (absent in older files: 0).</summary>
        public int scripEarned;
        public int dirt;
        public List<Meridian.Trade.Contract> contracts = new List<Meridian.Trade.Contract>();
        /// <summary>v2 (U-045): the surveyor's 40 slots in order (empty ones included) and the Builder's slot.</summary>
        public List<Meridian.Items.ItemStack> inventory = new List<Meridian.Items.ItemStack>();
        public int selectedSlot;
        public StorySave story = new StorySave();
        public List<string> catalogue = new List<string>();
        public List<string> bases = new List<string>();
        /// <summary>v2 (U-056): base pieces and aerostats.</summary>
        public List<Meridian.Building.BasePieceSave> basePieces = new List<Meridian.Building.BasePieceSave>();
        public List<Meridian.Building.AerostatSave> aerostats = new List<Meridian.Building.AerostatSave>();
        public TimerSave timers = new TimerSave();
        /// <summary>U-158: harvested resource nodes (absent in older files: every node full).</summary>
        public List<Meridian.Mining.NodeSave> nodes = new List<Meridian.Mining.NodeSave>();
        public List<string> terrainFiles = new List<string>();
    }

    [Serializable]
    public sealed class PlayerSave
    {
        public Vector2 position;
        public float health = 100f;
        /// <summary>v2: suit integrity (D-032), 0–100.</summary>
        public float suit = 100f;
        /// <summary>v2 (U-049): Envirosuit tier 0–3 (absent in early v2 files: 0).</summary>
        public int suitTier;
        /// <summary>v2 (U-048): seconds to Mercury's next solar flare (negative: one under way). The terminator follows the saved game clock.</summary>
        public float mercuryFlareIn = 600f;
        public bool aboard;
    }

    [Serializable]
    public sealed class ShipSave
    {
        public float hull = 100f;
        /// <summary>U-065: the Thruster mark (older files read 1, the field default). U-107 (D-103): the fuel, tank and tank-mark fields are gone; older files' values are ignored.</summary>
        public int thrusterMark = 1;
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
            data.loadedVersion = data.version;
            // v0 (pre-release) had no version field and no cargo list: JsonUtility reads version 0.
            if (data.version < 1)
            {
                data.cargo ??= new List<CargoStack>();
                data.story ??= new StorySave();
                data.timers ??= new TimerSave();
                data.version = 1;
            }
            // v1 → v2 (U-045): an empty inventory and a full suit (v1 never saved the suit, D-032).
            if (data.version < 2)
            {
                data.inventory ??= new List<Meridian.Items.ItemStack>();
                data.selectedSlot = 0;
                data.player ??= new PlayerSave();
                data.player.suit = 100f;
                data.version = 2;
            }
            // v2 → v3 (U-157, D-165 (3)): the smooth planets re-stamp their POIs against the smoothed ground: their poi_stamped flags go here,
            // the old stamp diffs once the terrain files load (SmoothGroundMigration.StripOldStamps, SaveSystem.Load).
            if (data.version < 3)
            {
                if (data.story != null) SmoothGroundMigration.DropFlags(data.story.flags);
                data.version = 3;
            }
            return data;
        }
    }
}
