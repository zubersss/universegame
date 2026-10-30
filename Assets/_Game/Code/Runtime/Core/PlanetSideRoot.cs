using Meridian.Planets;
using UnityEngine;

namespace Meridian.Core
{
    /// <summary>Root of PlanetSide.unity (one scene for all planets, Bible §10.3).</summary>
    public sealed class PlanetSideRoot : MonoBehaviour
    {
        public PlanetConfig Config { get; private set; }

        public void Configure(PlanetConfig config)
        {
            Config = config;
            Physics2D.gravity = config.GravityVector;
        }
    }
}
