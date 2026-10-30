using System.Collections;
using Meridian.Planets;
using Meridian.Player;
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
        public PlayerController player;
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
            float surface = terrain.Generator.SurfaceHeight(spawnX) + 1f;

            if (player != null)
            {
                player.ConfigureFor(config);
                player.Body.position = new Vector2(spawnX + 0.5f, surface + 0.05f);
                player.transform.position = player.Body.position;
                player.Body.linearVelocity = Vector2.zero;
                StopAllCoroutines();
                StartCoroutine(HoldUntilGroundLoads());
            }
            if (sideCamera != null)
            {
                sideCamera.transform.position = new Vector3(spawnX + 0.5f, surface + 3f, -10f);
                var cf = sideCamera.GetComponent<CameraFollow>();
                if (cf != null) cf.SnapToTarget();
            }
        }

        // The body waits frozen until the chunks around it exist, so it never falls through unloaded ground.
        IEnumerator HoldUntilGroundLoads()
        {
            player.Body.simulated = false;
            while (!terrain.IsSettled) yield return null;
            player.Body.simulated = true;
        }
    }
}
