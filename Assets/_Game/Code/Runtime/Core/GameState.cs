using Meridian.Planets;
using UnityEngine;

namespace Meridian.Core
{
    public enum ViewMode { PlanetSide, Space }

    /// <summary>
    /// The player's run state, carried across transitions in memory (Bible §5.2); never re-read
    /// from disk mid-session. Lives in Core.unity.
    /// </summary>
    public sealed class GameState : MonoBehaviour
    {
        public static GameState Instance { get; private set; }

        public PlanetCatalog catalog;
        public PlanetId currentPlanet = PlanetId.Earth;
        public ViewMode view = ViewMode.PlanetSide;
        public int worldSeed = 1969;

        [Header("Ship")]
        public float hull = 100f;
        public float fuel = 100f;
        public float tankCapacity = 100f;
        /// <summary>Items carried in the ship (item id → count). Inventory proper arrives in M3.</summary>
        public System.Collections.Generic.List<CargoStack> cargo = new System.Collections.Generic.List<CargoStack>();

        public PlanetConfig CurrentPlanetConfig => catalog != null ? catalog.Get(currentPlanet) : null;

        readonly System.Collections.Generic.Dictionary<PlanetId, Meridian.Terrain.TerrainEdits> terrainEdits =
            new System.Collections.Generic.Dictionary<PlanetId, Meridian.Terrain.TerrainEdits>();

        /// <summary>Every planet that has a diff store this session (save writes one file each).</summary>
        public System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<PlanetId, Meridian.Terrain.TerrainEdits>> AllEdits => terrainEdits;

        /// <summary>Empties every planet's diffs in place (load replaces them from disk).</summary>
        public void ClearAllEdits() { foreach (var e in terrainEdits.Values) e.Clear(); }

        /// <summary>Player terrain diffs for a planet; created empty on first visit, kept for the session.</summary>
        public Meridian.Terrain.TerrainEdits EditsFor(PlanetId id)
        {
            if (!terrainEdits.TryGetValue(id, out var e)) terrainEdits[id] = e = new Meridian.Terrain.TerrainEdits();
            return e;
        }

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }
    }
}

namespace Meridian.Core
{
    [System.Serializable]
    public struct CargoStack
    {
        public int itemId;
        public int count;
    }
}
