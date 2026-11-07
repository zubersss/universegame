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
        /// <summary>U-076: created at runtime in Configure.</summary>
        public Meridian.Planet.Backdrop.DepthBands depthBands;
        /// <summary>U-090: the stage layer stack (foreground, rocks, hills, region skyline, set-pieces, cloud strip, set streaming).</summary>
        public Meridian.Planet.Backdrop.StageLayers stage { get; private set; }
        public Meridian.Planet.Lighting.DayNightLighting dayNight;
        public Meridian.Planet.Weather.DustStorm dustStorm;
        /// <summary>Venus super-rotation (U-050), created at configure.</summary>
        public Meridian.Planet.Weather.VenusWind wind { get; private set; }
        public Meridian.Survey.SurveyScanner scanner { get; private set; }
        public Meridian.Creatures.Wardens.WardenDirector wardens { get; private set; }
        public Meridian.Hazards.SolariteCrystals solarite { get; private set; }
        public Meridian.Building.BaseBuilder bases { get; private set; }
        /// <summary>U-093: Suit power 0 -> conk out, wake at the last base or the ship (created in Configure).</summary>
        public ConkOut conkOut { get; private set; }
        /// <summary>U-094: the v4 cartoon side view (on for converted planets while CartoonStage.Enabled).</summary>
        public Meridian.View2D.CartoonStage cartoon { get; private set; }
        public Meridian.Creatures.CreatureDirector creatures;
        public Meridian.Hazards.HazardSystem hazards;
        public Meridian.Planet.POI.PoiPlacer pois;
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
            var edits = state != null ? state.EditsFor(config.id) : null;
            if (pois != null && edits != null) pois.StampFor(config, seed, edits); // U-030: once per world, before streaming
            terrain.Begin(config, seed, follow, edits);
            if (pois != null) pois.PlaceFor(config, seed);
            float surface = terrain.TopSolidY(spawnX) + 1f; // stamps included (U-035 spawn camp)
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
            // U-076: the 3D depth bands (ground strip, flora, ridges, skyline) behind the play plane; added here like
            // PhotoOrbit so the scenes need no re-authoring.
            if (depthBands == null && terrain != null)
            {
                var go = new GameObject("DepthBands");
                go.transform.SetParent(transform, false);
                depthBands = go.AddComponent<Meridian.Planet.Backdrop.DepthBands>();
            }
            if (depthBands != null)
            {
                depthBands.view = sideCamera; depthBands.terrain = terrain; depthBands.backdrop = backdrop; depthBands.pois = pois;
                depthBands.ConfigureFor(config);
                if (stage == null)
                {
                    var sgo = new GameObject("StageLayers");
                    sgo.transform.SetParent(transform, false);
                    stage = sgo.AddComponent<Meridian.Planet.Backdrop.StageLayers>();
                }
                stage.view = sideCamera; stage.terrain = terrain; stage.pois = pois; stage.bands = depthBands; stage.backdrop = backdrop;
                stage.ConfigureFor(config);
            }
            // U-050: Venus super-rotation pushes the surveyor (off elsewhere).
            // U-051: the Pilgrim carries a Refinery and a Fabricator.
            if (ship != null && ship.GetComponent<Meridian.Crafting.CraftingStation>() == null)
            {
                foreach (var kind in new[] { Meridian.Crafting.Station.Refinery, Meridian.Crafting.Station.Fabricator })
                {
                    var st = ship.gameObject.AddComponent<Meridian.Crafting.CraftingStation>();
                    st.kind = kind;
                    st.radius = 7f;
                }
            }
            // U-054: Survey pulses fill the catalogue.
            if (scanner == null) { scanner = gameObject.AddComponent<Meridian.Survey.SurveyScanner>(); scanner.side = this; }
            if (wind == null) wind = gameObject.AddComponent<Meridian.Planet.Weather.VenusWind>();
            wind.player = player;
            wind.enabled = config.id == PlanetId.Venus;
            if (dayNight != null) dayNight.ConfigureFor(config);
            if (dustStorm != null) dustStorm.ConfigureFor(config, seed);
            if (creatures != null) { creatures.hazards = hazards; creatures.ConfigureFor(config, seed); }
            // U-053: Wardens patrol their sites and answer over-mining.
            if (wardens == null)
            {
                wardens = gameObject.AddComponent<Meridian.Creatures.Wardens.WardenDirector>();
                wardens.terrain = terrain; wardens.player = player; wardens.hazards = hazards; wardens.pois = pois;
            }
            wardens.ConfigureFor(config);
            if (hazards != null) hazards.ConfigureFor(config);
            // U-059: Solarite crystals answer the flares (Mercury); after the hazards, which own the flare clock.
            if (solarite == null) { solarite = gameObject.AddComponent<Meridian.Hazards.SolariteCrystals>(); solarite.pois = pois; solarite.rig = rig; }
            solarite.flares = hazards != null ? hazards.flares : null;
            solarite.ConfigureFor(config.id);
            // U-056: this planet's base, rebuilt from the save; the Builder and the Beam work on its pieces.
            if (bases == null) { bases = gameObject.AddComponent<Meridian.Building.BaseBuilder>(); bases.terrain = terrain; bases.rig = rig; bases.player = player != null ? player.transform : null; }
            bases.ConfigureFor(config.id);
            if (conkOut == null) conkOut = gameObject.AddComponent<ConkOut>();
            conkOut.player = player; conkOut.hazards = hazards; conkOut.bases = bases; conkOut.ship = ship; conkOut.terrain = terrain; conkOut.view = sideCamera;
            conkOut.vitals = player != null ? player.GetComponent<PlayerVitals>() : null;
            conkOut.Hook();
            if (sideCamera != null)
            {
                sideCamera.transform.position = new Vector3(spawnX + 0.5f, surface + 3f, sideCamera.orthographic ? -10f : -Meridian.CameraRig.SideView.DistanceFor(Meridian.CameraRig.SideView.HalfHeight(sideCamera)));
                var cf = sideCamera.GetComponent<CameraFollow>();
                if (cf != null) { cf.player = player; cf.terrain = terrain; cf.creatures = creatures; cf.SnapToTarget(); } // U-087: the stage camera reads the floor and the creatures
                // U-080: photo-mode orbit for depth reviews (added here so the scenes need no re-authoring).
                var orbit = sideCamera.GetComponent<Meridian.CameraRig.PhotoOrbit>();
                if (orbit == null) orbit = sideCamera.gameObject.AddComponent<Meridian.CameraRig.PhotoOrbit>();
                if (player != null) orbit.target = player.transform;
            }
            // U-094: the v4 2D render path (orthographic 16.875 m frame, painted parallax, sprite surveyor) where converted.
            if (cartoon == null) cartoon = gameObject.AddComponent<Meridian.View2D.CartoonStage>();
            cartoon.ConfigureFor(this, config, surface);
        }

        /// <summary>Skids on the highest ground under the hull's footprint.</summary>
        Vector2 LandedShipPosition(int centerX)
        {
            int half = Mathf.CeilToInt(SideShip.Width * 0.5f);
            int top = int.MinValue;
            for (int x = centerX - half; x <= centerX + half; x++)
                top = Mathf.Max(top, terrain.TopSolidY(x));
            float ground = top + 1f;
            if (pois != null) ground = Mathf.Max(ground, pois.SolidTopOver(centerX + 0.5f - SideShip.Width * 0.5f, centerX + 0.5f + SideShip.Width * 0.5f)); // on the pad (U-035)
            return new Vector2(centerX + 0.5f, ground + SideShip.SkidDrop + 0.05f);
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
