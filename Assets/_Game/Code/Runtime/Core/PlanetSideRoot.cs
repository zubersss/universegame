using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Core
{
    /// <summary>Root of PlanetSide.unity (one scene for all planets, Bible §10.3).</summary>
    public sealed class PlanetSideRoot : MonoBehaviour
    {
        public TerrainStreamer terrain;
        public Meridian.Rig.RigTools rig;
        public Camera sideCamera;
        [Tooltip("Spawn column (tiles) when no save or transition gives one.")]
        public int spawnX = 64;

        public PlanetConfig Config { get; private set; }

        public void Configure(PlanetConfig config)
        {
            Config = config;
            Physics2D.gravity = config.GravityVector;
            if (terrain == null) return;

            var state = GameState.Instance;
            int seed = state != null ? state.worldSeed : 1969;
            var follow = sideCamera != null ? sideCamera.transform : transform;
            terrain.Begin(config, seed, follow, state != null ? state.EditsFor(config.id) : null);
            if (sideCamera != null)
            {
                float y = terrain.Generator.SurfaceHeight(spawnX) + 4f;
                sideCamera.transform.position = new Vector3(spawnX + 0.5f, y, -10f);
            }
        }
    }
}
