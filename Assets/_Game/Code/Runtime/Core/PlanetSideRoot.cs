using System.Collections;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Ship;
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
        public SideShip ship;
        public EscapeLineBand escapeBand;
        public ShipHud shipHud;
        public Meridian.UI.SideHud sideHud;
        public Meridian.Planet.PlanetBackdrop backdrop;
        public Meridian.Planet.Lighting.DayNightLighting dayNight;
        public Meridian.Planet.Weather.DustStorm dustStorm;
        public Meridian.Creatures.CreatureDirector creatures;
        [Tooltip("Spawn column (tiles) when no save or transition gives one.")]
        public int spawnX = 64;
        [Tooltip("The landed ship sits this many tiles right of the spawn column.")]
        public int shipOffsetX = 10;

        public PlanetConfig Config { get; private set; }

        /// <summary>Set when the planet loads from an entry (Bible §5.3); null for a normal start.</summary>
        public Arrival? LastArrival { get; private set; }

        public struct Arrival
        {
            public int x;               // wrapped tile column under the ship
            public Vector2 shipPosition;
            public Vector2 shipVelocity;
        }

        public const float EntryAboveEscapeLine = 20f;
        public const float EntryDescentSpeed = 15f;

        /// <summary>Entry from orbit: terrain streams around `entryX`; the ship flies in at Escape Line + 20 m descending 15 m/s with the player aboard.</summary>
        public void ConfigureForEntry(PlanetConfig config, int entryX)
        {
            spawnX = entryX;
            Configure(config);
            if (ship == null) return;
            StopAllCoroutines(); // the ship is airborne: it doesn't wait for the ground
            ship.Body.simulated = true;
            var pos = new Vector2(entryX + 0.5f, config.EscapeLineY + EntryAboveEscapeLine);
            ship.Body.position = pos;
            ship.transform.position = pos;
            ship.Body.linearVelocity = new Vector2(0f, -EntryDescentSpeed);
            if (player != null) StartCoroutine(HoldUntilGroundLoads(player.Body));
            var boarding = ship.GetComponent<ShipBoarding>();
            if (boarding != null) boarding.ForceAboard();
            LastArrival = new Arrival { x = entryX, shipPosition = pos, shipVelocity = ship.Body.linearVelocity };
        }

        public void Configure(PlanetConfig config)
        {
            Config = config;
            LastArrival = null;
            Physics2D.gravity = config.GravityVector;
            if (terrain == null) return;

            var state = GameState.Instance;
            int seed = state != null ? state.worldSeed : 1969;
            var follow = sideCamera != null ? sideCamera.transform : transform;
            terrain.Begin(config, seed, follow, state != null ? state.EditsFor(config.id) : null);
            float surface = terrain.Generator.SurfaceHeight(spawnX) + 1f;
            StopAllCoroutines();

            if (player != null)
            {
                player.ConfigureFor(config);
                player.Body.position = new Vector2(spawnX + 0.5f, surface + 0.05f);
                player.transform.position = player.Body.position;
                player.Body.linearVelocity = Vector2.zero;
                StartCoroutine(HoldUntilGroundLoads(player.Body));
            }
            if (ship != null)
            {
                ship.ConfigureFor(config);
                ship.Body.position = LandedShipPosition(spawnX + shipOffsetX);
                ship.transform.position = ship.Body.position;
                ship.Body.linearVelocity = Vector2.zero;
                StartCoroutine(HoldUntilGroundLoads(ship.Body));
            }
            if (escapeBand != null) escapeBand.ConfigureFor(config);
            if (sideHud != null) sideHud.ConfigureFor(config);
            if (backdrop != null) backdrop.ConfigureFor(config);
            if (dayNight != null) dayNight.ConfigureFor(config);
            if (dustStorm != null) dustStorm.ConfigureFor(config, seed);
            if (creatures != null) creatures.ConfigureFor(config, seed);
            if (sideCamera != null)
            {
                sideCamera.transform.position = new Vector3(spawnX + 0.5f, surface + 3f, -10f);
                var cf = sideCamera.GetComponent<CameraFollow>();
                if (cf != null) cf.SnapToTarget();
            }
        }

        /// <summary>Skids on the highest ground under the hull's footprint.</summary>
        Vector2 LandedShipPosition(int centerX)
        {
            int half = Mathf.CeilToInt(SideShip.HullLength * 0.5f);
            int top = int.MinValue;
            for (int x = centerX - half; x <= centerX + half; x++)
                top = Mathf.Max(top, terrain.Generator.SurfaceHeight(terrain.WrapX(x)));
            return new Vector2(centerX + 0.5f, top + 1f + SideShip.SkidDrop + 0.05f);
        }

        // Bodies wait frozen until the chunks around them exist, so nothing falls through unloaded ground.
        IEnumerator HoldUntilGroundLoads(Rigidbody2D body)
        {
            body.simulated = false;
            while (!terrain.IsSettled) yield return null;
            yield return new WaitForFixedUpdate(); // let the new chunk colliders reach the physics world
            body.simulated = true;
        }
    }
}
