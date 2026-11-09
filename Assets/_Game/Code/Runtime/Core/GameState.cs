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
        /// <summary>U-065 ship marks (Bible §4.3 v4.1): Thruster Mk1–Mk3. U-107 (D-103): no launch fuel and no tanks.</summary>
        public int thrusterMark = 1;
        /// <summary>The surveyor's inventory (U-045, SaveData v2).</summary>
        public readonly Meridian.Items.Inventory inventory = new Meridian.Items.Inventory();
        /// <summary>Envirosuit tier (U-049): 0 none, 1–3 Mk1–Mk3; lowers every hazard by its tier.</summary>
        public int suitTier;
        /// <summary>Halcyon Scrip (U-052).</summary>
        public int scrip = Meridian.Trade.Market.StartingScrip;
        /// <summary>U-174 (D-175): the Scrip earned by selling in this expedition (sales only; Surveyor Rank).</summary>
        public int scripEarned;
        /// <summary>U-174 (D-174): the dirt store (dug matrix tiles for the Builder; weightless, not sellable).</summary>
        public readonly Meridian.Mining.DirtStore dirt = new Meridian.Mining.DirtStore();

        /// <summary>U-174: the D1 tables' pack limit, item weights and dirt store size on the surveyor's inventory and store.</summary>
        public void ApplyD1()
        {
            var t = Meridian.Mining.D1Tables.Current;
            Meridian.Items.Inventory.KgOf = t.Kg;
            inventory.LimitKg = t.packLimitKg;
            dirt.capacity = t.dirtStoreStart;
        }
        /// <summary>Survey Datacores and the catalogue of scanned entries (U-054).</summary>
        public int datacores;
        /// <summary>Bases (U-056): placed pieces and aerostats, every planet.</summary>
        public readonly System.Collections.Generic.List<Meridian.Building.BasePieceSave> basePieces = new System.Collections.Generic.List<Meridian.Building.BasePieceSave>();
        public readonly System.Collections.Generic.List<Meridian.Building.AerostatSave> aerostats = new System.Collections.Generic.List<Meridian.Building.AerostatSave>();
        public readonly System.Collections.Generic.HashSet<string> catalogue = new System.Collections.Generic.HashSet<string>();
        /// <summary>Accepted Halcyon cargo contracts (U-052; done ones stay for the log).</summary>
        public readonly System.Collections.Generic.List<Meridian.Trade.Contract> contracts = new System.Collections.Generic.List<Meridian.Trade.Contract>();
        /// <summary>Items carried in the ship (item id → count).</summary>
        public System.Collections.Generic.List<CargoStack> cargo = new System.Collections.Generic.List<CargoStack>();
        /// <summary>Story and world flags (saved as story.flags), e.g. "poi_stamped:survey_archive" (U-030).</summary>
        public readonly System.Collections.Generic.List<string> storyFlags = new System.Collections.Generic.List<string>();
        /// <summary>U-158: harvested resource nodes per planet (charges left, when the last was taken), so a node does not regrow by leaving.</summary>
        public readonly System.Collections.Generic.List<Meridian.Mining.NodeSave> nodeStates = new System.Collections.Generic.List<Meridian.Mining.NodeSave>();
        public bool HasFlag(string f) => storyFlags.Contains(f);
        public void SetFlag(string f) { if (!storyFlags.Contains(f)) storyFlags.Add(f); }
        /// <summary>U-156: drops a world flag (a re-stamp after the ground changed shape; the before / after captures).</summary>
        public void ClearFlag(string f) => storyFlags.Remove(f);

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
            ApplyD1(); // U-174: the pack's weight limit and the dirt store from the D1 tables
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
