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

        public PlanetConfig CurrentPlanetConfig => catalog != null ? catalog.Get(currentPlanet) : null;

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
