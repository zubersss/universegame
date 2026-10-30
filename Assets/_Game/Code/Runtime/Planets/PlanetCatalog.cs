using UnityEngine;

namespace Meridian.Planets
{
    /// <summary>All eight PlanetConfigs, indexed by PlanetId. Referenced from Core.</summary>
    [CreateAssetMenu(menuName = "MERIDIAN/Planet Catalog", fileName = "PlanetCatalog")]
    public sealed class PlanetCatalog : ScriptableObject
    {
        public PlanetConfig[] planets = new PlanetConfig[8];

        public PlanetConfig Get(PlanetId id)
        {
            foreach (var p in planets) if (p != null && p.id == id) return p;
            return null;
        }
    }
}
