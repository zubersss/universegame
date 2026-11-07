using System;
using System.Collections;
using System.IO;
using Meridian.UI;
using UnityEngine;

namespace Meridian.Core
{
    /// <summary>
    /// Opt-in smoke run of a built player (U-017): with `-meridianSmoke &lt;folder&gt;` it screenshots the
    /// main menu, Earth by day and night, a biome border, the Mars canyon in a storm and Saturn (U-044), writes smoke_done.txt and quits.
    /// Without the argument it does nothing. Used by tools/unity_smoke.ps1.
    /// </summary>
    public sealed class BuildSmoke : MonoBehaviour
    {
        public SceneDirector scenes;

        static string Folder()
        {
            var args = Environment.GetCommandLineArgs();
            int i = Array.IndexOf(args, "-meridianSmoke");
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
        }

        void Start()
        {
            var folder = Folder();
            if (folder == null) { enabled = false; return; }
            Directory.CreateDirectory(folder);
            StartCoroutine(Run(folder));
        }

        IEnumerator Run(string folder)
        {
            while (scenes == null || !scenes.IsReady) yield return null;
            yield return Wait(1.5f);
            yield return Shot(folder, "smoke_1_menu.png");

            if (MenuController.Instance != null && MenuController.Instance.MainMenuOpen) MenuController.Instance.NewGame();
            yield return Wait(2.5f);

            // U-044 (M2 playtest build): the camp by day and by night, a biome border, the Mars canyon in a
            // dust storm, and space at Saturn.
            var side = scenes.PlanetSide;
            if (side != null && side.dayNight != null)
            {
                side.dayNight.Override = 0.5f;
                yield return Wait(1f);
                yield return Shot(folder, "smoke_2_earth_day.png");
                // U-080: the same view from the depth preset (yaw/pitch orbit), so reviews see block relief and the back wall.
                {
                    var cam = side.sideCamera;
                    var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                    var railPos = cam.transform.position;
                    if (follow != null) follow.enabled = false;
                    var pivot = side.player != null ? side.player.transform.position + new Vector3(0f, 1.2f, 0f) : new Vector3(railPos.x, railPos.y, 0f);
                    Meridian.CameraRig.PhotoOrbit.Depth(cam, pivot);
                    yield return Wait(0.5f);
                    yield return Shot(folder, "smoke_2b_earth_day_depth.png");
                    cam.transform.SetPositionAndRotation(railPos, Quaternion.identity);
                    if (follow != null) { follow.enabled = true; follow.SnapToTarget(); }
                }
                // U-093 smoke (D-087): a wolf reaches the surveyor and bumps them (0.8 m knock, the bump clip); no meter changes.
                if (side.creatures != null && side.player != null && side.player.Body != null)
                {
                    var feet = side.player.Body.position;
                    var w1 = side.creatures.Spawn(Meridian.Creatures.Species.GreyWolf, feet + new Vector2(2.5f, 0.6f));
                    int before = side.player.BumpCount;
                    float bumpUntil = Time.realtimeSinceStartup + 4f;
                    while (side.player.BumpCount == before && Time.realtimeSinceStartup < bumpUntil) yield return null;
                    yield return Wait(0.05f);
                    Debug.Log($"[MERIDIAN] smoke bump: {side.player.BumpCount - before} bump(s)");
                    yield return Shot(folder, "smoke_2c_earth_bump.png");
                    if (w1 != null) side.creatures.Despawn(w1);
                    yield return Wait(0.3f);
                }
                side.dayNight.Override = 0f;
                yield return Wait(1f);
                yield return Shot(folder, "smoke_3_earth_night.png");
                side.dayNight.Override = 0.45f;
                // U-077 smoke: a dig ahead of the surveyor (the Beam), then the Pilgrim airborne with its gear up.
                if (side.player != null && side.rig != null)
                {
                    var p = side.player.transform.position;
                    bool dug = side.rig.Dig(new Vector2(p.x - 1.5f, p.y - 1.2f));
                    yield return Wait(0.6f);
                    Debug.Log($"[MERIDIAN] smoke dig: {dug}");
                    yield return Shot(folder, "smoke_3b_earth_dig.png");
                }
                // U-089 smoke: a hard landing (the squash, one frame after touchdown).
                if (side.player != null && side.player.Body != null)
                {
                    var pv = side.player.GetComponentInChildren<Meridian.Player.PlayerView>();
                    var feet = side.player.Body.position;
                    var up = feet + new Vector2(0f, 3.5f);
                    side.player.Body.position = up; side.player.transform.position = up; side.player.Body.linearVelocity = Vector2.zero;
                    float until = Time.realtimeSinceStartup + 4f;
                    while (side.player.Grounded && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate(); // the drop begins
                    while (!side.player.Grounded && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
                    Debug.Log($"[MERIDIAN] smoke landing: {side.player.LastImpactSpeed:F1} m/s, visual y {(pv != null && pv.VisualRoot != null ? pv.VisualRoot.localScale.y : 1f):F2}");
                    yield return Shot(folder, "smoke_3d_landing_squash.png");
                }
                if (side.ship != null && side.ship.Body != null)
                {
                    var rest = side.ship.Body.position;
                    var air = rest + new Vector2(0f, 16f);
                    // Held in the air for the shot (gravity off): LookAt's settle lasts seconds, long enough to fall back onto the pad.
                    float gravity = side.ship.Body.gravityScale;
                    side.ship.Body.gravityScale = 0f;
                    side.ship.Body.position = air; side.ship.transform.position = air; side.ship.Body.linearVelocity = Vector2.zero;
                    yield return LookAt(side, air.x, 12f, 9f);
                    side.ship.Body.position = air; side.ship.transform.position = air; side.ship.Body.linearVelocity = Vector2.zero;
                    yield return Wait(0.6f); // the legs retract above LegsAltitude
                    Debug.Log($"[MERIDIAN] smoke ship airborne: altitude {side.ship.AltitudeAboveGround:F1} m, legs deployed {side.ship.LegsDeployed}");
                    yield return Shot(folder, "smoke_3c_ship_airborne.png");
                    side.ship.Body.gravityScale = gravity;
                    side.ship.Body.position = rest; side.ship.transform.position = rest; side.ship.Body.linearVelocity = Vector2.zero;
                    yield return Wait(0.5f);
                }
            }

            // U-045: the Tab inventory panel with a few stacks (the selected one is the Builder's).
            var hud = FindAnyObjectByType<SideHud>();
            if (hud != null && hud.Inventory != null && GameState.Instance != null)
            {
                var inv = GameState.Instance.inventory;
                inv.Clear();
                inv.Add(Meridian.Terrain.TileId.Soil, 64);
                inv.Add(Meridian.Terrain.TileId.Stone, 999);
                inv.Add(Meridian.Terrain.TileId.Stone, 210);
                foreach (var key in new[] { "iron", "copper", "carbon", "silica", "water_ice", "oxygen", "wood", "clay" })
                {
                    var def = Meridian.Items.ItemRegistry.Get(key);
                    if (def != null) inv.Add(def.id, 3 + key.Length * 7);
                }
                inv.Select(1);
                hud.Inventory.SetOpen(true);
                yield return Wait(1.5f); // icons arrive
                yield return Shot(folder, "smoke_8_inventory.png");
                hud.Inventory.SetOpen(false);

                // U-051: the crafting panel with the Blueprint Tree (some ore and bars in hand).
                if (hud.Crafting != null)
                {
                    inv.Add(Meridian.Items.ItemRegistry.Get("hematite").id, 6);
                    inv.Add(Meridian.Items.ItemRegistry.Get("smelter_bar_iron").id, 2);
                    // Stand at the camp's Smelter so the shot shows a live CRAFT next to the unavailable ones.
                    foreach (var st in FindObjectsByType<Meridian.Crafting.CraftingStation>(FindObjectsInactive.Exclude))
                        if (st.kind == Meridian.Crafting.Station.Smelter && side != null && side.player != null)
                        {
                            var at = new Vector2(st.transform.position.x + 1f, side.player.Body.position.y);
                            side.player.Body.position = at; side.player.transform.position = at;
                        }
                    hud.Crafting.SetOpen(true);
                    yield return Wait(1f);
                    yield return Shot(folder, "smoke_9_crafting.png");
                    hud.Crafting.SetOpen(false);
                }
            }

            // U-054: a Survey pulse at the camp, then the catalogue (N).
            if (hud != null && hud.Catalogue != null && side != null && side.scanner != null)
            {
                side.scanner.Scan(side.player.Body.position);
                hud.Catalogue.SetOpen(true);
                yield return Wait(1.5f); // icons arrive
                yield return Shot(folder, "smoke_11_catalogue.png");
                hud.Catalogue.SetOpen(false);
            }

            // U-132 (U-124 / U-102): the pause card and the settings paper, then Earth's title card, for the owner's page.
            var menus = MenuController.Instance;
            if (menus != null)
            {
                menus.OpenPause();
                yield return Wait(0.6f);
                yield return Shot(folder, "smoke_19_pause.png");
                menus.OpenSettings();
                yield return Wait(0.6f);
                yield return Shot(folder, "smoke_20_settings.png");
                menus.CloseSettings();
                menus.Resume();
                yield return Wait(0.3f);
            }
            yield return Card(folder, Meridian.Planets.PlanetId.Earth);

            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Ocean, out int coast, out _);
            yield return LookAt(side, coast - 10f, 8f);
            yield return Shot(folder, "smoke_4_desert_ocean.png");

            var mars = GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mars);
            yield return scenes.LoadPlanetSide(mars);
            side = scenes.PlanetSide;
            if (side.dayNight != null) side.dayNight.Override = 0.45f;
            yield return Card(folder, Meridian.Planets.PlanetId.Mars); // U-132
            // U-053: the Mars Warden outpost, its patrol and a sentinel called by over-mining, hovering beside the surveyor (D-087: it never fires).
            if (side.wardens != null)
            {
                float outpost = Meridian.Planet.POI.PoiCatalog.WardenOutpost.CenterX;
                yield return LookAt(side, outpost + 10f, 3f, 9f);
                if (side.hazards != null) side.hazards.enabled = false;
                var feet = side.player.Body.position;
                var hunter = side.wardens.Spawn(feet + new Vector2(5f, 4.5f), feet, Meridian.Creatures.Wardens.SentinelState.Hunt);
                yield return Wait(1.4f);
                yield return Shot(folder, "smoke_12_warden.png");
                side.wardens.DespawnAll();
                if (side.hazards != null) side.hazards.enabled = true;
            }
            // U-064 evidence (U-060): a sealed shelter on the Mars plains at night, lit from inside by a lamp.
            if (side.bases != null)
            {
                int sx = side.spawnX + 200;
                yield return LookAt(side, sx + 0.5f, 3f, 7f);
                var t = side.terrain;
                int top = t.TopSolidY(sx);
                for (int dx = -3; dx <= 3; dx++) top = Mathf.Max(top, t.TopSolidY(sx + dx));
                int roof = top + 5;
                foreach (int wx in new[] { sx - 3, sx + 3 })
                    for (int wy = t.TopSolidY(wx) + 1; wy < roof; wy++)
                        if (side.bases.PieceAt(new Vector2Int(wx, wy)) == null) side.bases.Place(new Vector2(wx + 0.5f, wy + 0.5f), Meridian.Building.PieceKind.Wall);
                for (int wx = sx - 3; wx <= sx + 3; wx++) side.bases.Place(new Vector2(wx + 0.5f, roof + 0.5f), Meridian.Building.PieceKind.Wall);
                side.bases.Place(new Vector2(sx + 1.5f, t.TopSolidY(sx + 1) + 1.5f), Meridian.Building.PieceKind.Lamp);
                if (side.dayNight != null) side.dayNight.Override = 0f;
                yield return Wait(1f);
                yield return Shot(folder, "smoke_18_mars_shelter_night_lamp.png");
                if (side.dayNight != null) side.dayNight.Override = 0.45f;
            }
            // U-139 (LEAD 16:1x): the Halcyon hauler wreck, a stamped Mars POI: the painted set stands at its stamped ground.
            var hauler = Meridian.Planet.POI.PoiCatalog.HalcyonHauler;
            yield return LookAt(side, hauler.CenterX, 4f, 10f);
            yield return Shot(folder, "smoke_22_mars_hauler.png");
            // On the canyon wall's terraces (as the U-039 capture): wall, ledges and the far rim in one view.
            int canyon = Meridian.Terrain.MarsLandforms.CanyonStart + 60;
            yield return LookAt(side, canyon, 6f, 24f);
            yield return Shot(folder, "smoke_5_mars_canyon.png");
            // Storm onset (8 s ramp): early on the haze is up and the canyon still reads through it.
            if (side.dustStorm != null) side.dustStorm.Force(0f, 60f);
            yield return Wait(1f);
            yield return Shot(folder, "smoke_6_mars_canyon_storm.png");

            // U-060 (M3 playtest build): Mercury by day and on the twilight line at the flare shelter, the
            // Cinderhulk after nightfall; Venus's Meridian station with the Veil Serpent, and a surface vent field.
            yield return scenes.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mercury));
            side = scenes.PlanetSide;
            if (side.hazards != null) side.hazards.enabled = false;
            if (side.wardens != null) side.wardens.enabled = false;
            int mw = side.Config.worldWidth;
            var solarField = Meridian.Planet.POI.PoiCatalog.SolariteField;
            yield return Dawn(side, solarField.CenterX + mw / 4f);                  // the field a quarter world behind the dawn line: full day
            yield return LookAt(side, solarField.CenterX, 4f, 10f);
            yield return Shot(folder, "smoke_13_mercury_day.png");
            yield return Card(folder, Meridian.Planets.PlanetId.Mercury); // U-132: over the day side
            var shelter = Meridian.Planet.POI.PoiCatalog.FlareShelterPoi;
            yield return Dawn(side, shelter.CenterX);                               // the dawn line through the shelter: violet twilight
            yield return LookAt(side, shelter.CenterX, 4f, 10f);
            yield return Shot(folder, "smoke_14_mercury_twilight_shelter.png");
            // U-138 (D-150): the night shot is the Shadewyrm at its burrow in the first cold trap (the Cinderhulk left the spawn table).
            side.creatures.DespawnAll();
            int trapX = Meridian.Terrain.MercuryLandforms.ColdTrapCentre(0, mw);
            yield return LookAt(side, trapX - 4f, 4f, 9f);
            float wyrmY = side.terrain.TopSolidY(trapX) + 1f + Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.Shadewyrm).size.y * 0.5f + 0.05f;
            side.creatures.Spawn(Meridian.Creatures.Species.Shadewyrm, new Vector2(trapX + 0.5f, wyrmY)); // the director stands its burrow in front (D-126)
            yield return Wait(1.5f);
            yield return Shot(folder, "smoke_15_shadewyrm_burrow.png");

            yield return scenes.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Venus));
            side = scenes.PlanetSide;
            if (side.hazards != null) side.hazards.enabled = false;
            if (side.dayNight != null) side.dayNight.Override = 0.5f;
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            float deck = station.floatY + (336f - 62f) / 128f;
            yield return Stand(side, new Vector2(station.x + 10f, deck + 1.5f), 3f, 10f);
            side.creatures.Spawn(Meridian.Creatures.Species.VeilSerpent, new Vector2(station.x + 9f, deck + 9f));
            side.creatures.Spawn(Meridian.Creatures.Species.SulfurDrifter, new Vector2(station.x - 2f, deck + 7f));
            yield return Wait(0.8f);
            yield return Shot(folder, "smoke_16_venus_station.png");
            side.creatures.DespawnAll();
            var vent = Meridian.Terrain.VenusLandforms.Vents[0];
            yield return LookAt(side, (vent.x0 + vent.x1) * 0.5f, 4f, 9f);
            yield return Shot(folder, "smoke_17_venus_vent.png");

            scenes.SetView(ViewMode.Space);
            var craft = scenes.Space.GetComponentInChildren<Meridian.Space.SpaceShip>();
            if (craft != null)
            {
                craft.externalInput = true;
                craft.intent = default;
                var saturn = craft.world.Find("saturn").Value;
                // Held just outside the atmosphere ring: the planet and its rings fill the view.
                var hold = saturn.position + new Vector2(0f, saturn.RingRadius + 20f);
                float until = Time.realtimeSinceStartup + 3f;
                while (Time.realtimeSinceStartup < until)
                {
                    craft.Position = hold;
                    craft.Velocity = Vector2.zero;
                    yield return null;
                }
            }
            else yield return Wait(3f);
            yield return Shot(folder, "smoke_7_space_saturn.png");

            // U-052: docked at the Earth Waystation, the Halcyon market open (some goods aboard, a dented hull).
            var bay = scenes.Space != null ? scenes.Space.GetComponent<Meridian.Trade.DockingBay>() : null;
            if (bay != null && GameState.Instance != null)
            {
                var st = GameState.Instance;
                st.inventory.Add(Meridian.Items.ItemRegistry.Get("iron").id, 12);
                st.inventory.Add(Meridian.Items.ItemRegistry.Get("suit_patch").id, 3);
                st.hull = 82f;
                yield return Wait(0.5f);
                if (bay.Dock("earth"))
                {
                    yield return Wait(1.5f); // bay art and icons arrive
                    yield return Shot(folder, "smoke_10_waystation.png");
                    bay.Undock();
                }
            }

            File.WriteAllText(Path.Combine(folder, "smoke_done.txt"), $"OK {GameInfo.Version} {DateTime.Now:s}");
            Application.Quit();
        }

        /// <summary>Points the side camera at column x, a few metres above the ground, and waits for the terrain there.</summary>
        static IEnumerator LookAt(PlanetSideRoot side, float x, float above, float size = 0f)
        {
            var follow = side.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
            if (follow != null) follow.enabled = false;
            if (size > 0f) Meridian.CameraRig.SideView.SetHalfHeight(side.sideCamera, size);
            var cam = side.sideCamera.transform;
            // The generator's surface: TopSolidY reads loaded chunks, and none are loaded there yet after a planet switch.
            int ground = side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(Mathf.FloorToInt(x)));
            cam.position = new Vector3(x, ground + above, cam.position.z);
            // Bring the surveyor along: streaming and hazards follow the player, not a free camera.
            if (side.player != null)
            {
                var feet = new Vector2(x, ground + 1.05f);
                side.player.Body.position = feet;
                side.player.transform.position = feet;
                side.player.Body.linearVelocity = Vector2.zero;
            }
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            yield return Wait(2f); // backdrop sets and creatures arrive
        }

        /// <summary>Mercury: puts the dawn line at x (Mercury's shared clock: lighting, backdrop and creatures follow).</summary>
        static IEnumerator Dawn(PlanetSideRoot side, float x)
        {
            Meridian.Terrain.MercuryTerminator.ClockOffset = 0;
            var clock = FindAnyObjectByType<TimeSystem>();
            double now = Meridian.Terrain.MercuryTerminator.Now(clock != null ? clock.GameSeconds : 0);
            float dawn = Meridian.Terrain.MercuryTerminator.Dawn(now, side.Config.worldWidth);
            Meridian.Terrain.MercuryTerminator.ClockOffset = (x - dawn) * Meridian.Terrain.MercuryTerminator.CreepSecondsPerMetre;
            yield return null;
        }

        /// <summary>Stands the surveyor at `feet` (a deck, a platform) with the camera `above` it, and waits for the ground.</summary>
        static IEnumerator Stand(PlanetSideRoot side, Vector2 feet, float above, float size)
        {
            var follow = side.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
            if (follow != null) follow.enabled = false;
            Meridian.CameraRig.SideView.SetHalfHeight(side.sideCamera, size);
            side.player.Body.position = feet; side.player.transform.position = feet; side.player.Body.linearVelocity = Vector2.zero;
            var cam = side.sideCamera.transform;
            cam.position = new Vector3(feet.x, feet.y + above, cam.position.z);
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            yield return Wait(2f);
        }

        /// <summary>U-132 (U-124): the planet's title card held centred over its surface; skipped (no shot) when the planet has no card art.</summary>
        static IEnumerator Card(string folder, Meridian.Planets.PlanetId planet)
        {
            var cards = MenuController.Instance != null ? MenuController.Instance.TitleCards : null;
            if (cards == null) yield break;
            cards.Show(planet);
            string key = Meridian.Art.ArtKeys.Ui.TitleCard(planet);
            float until = Time.realtimeSinceStartup + 4f;
            while (cards.Showing != key && Time.realtimeSinceStartup < until) yield return null;
            if (cards.Showing != key) yield break;
            cards.Seek(TitleCard.SlideSeconds);
            yield return Shot(folder, "smoke_21_titlecard_" + planet.ToString().ToLowerInvariant() + ".png");
            cards.Hide();
        }

        static IEnumerator Wait(float seconds)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while (Time.realtimeSinceStartup < until) yield return null;
        }

        static IEnumerator Shot(string folder, string name)
        {
            ScreenCapture.CaptureScreenshot(Path.Combine(folder, name));
            yield return null; // the capture is written at the end of the frame
            yield return null;
        }
    }
}
