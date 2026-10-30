using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Core
{
    /// <summary>Root of PlanetSide.unity (one scene for all planets, Bible §10.3).</summary>
    public sealed class PlanetSideRoot : MonoBehaviour
    {
        public TerrainStreamer terrain;
        public Camera sideCamera;
        [Tooltip("Spawn column (tiles) when no save or transition gives one.")]
        public int spawnX = 64;

        public PlanetConfig Config { get; private set; }

        public void Configure(PlanetConfig config)
        {
            Config = config;
            Physics2D.gravity = config.GravityVector;
            if (terrain == null) return;

            int seed = GameState.Instance != null ? GameState.Instance.worldSeed : 1969;
            var follow = sideCamera != null ? sideCamera.transform : transform;
            terrain.Begin(config, seed, follow);
            if (sideCamera != null)
            {
                float y = terrain.Generator.SurfaceHeight(spawnX) + 4f;
                sideCamera.transform.position = new Vector3(spawnX + 0.5f, y, -10f);
            }
        }
    }
}
