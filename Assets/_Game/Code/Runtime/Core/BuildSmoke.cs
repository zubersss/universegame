using System;
using System.Collections;
using System.IO;
using Meridian.UI;
using UnityEngine;
using CloudLayout = Meridian.Terrain.CloudColumn.CloudLayout;

namespace Meridian.Core
{
    /// <summary>
    /// Opt-in smoke run of a built player (U-017): with `-meridianSmoke &lt;folder&gt;` it screenshots the
    /// main menu, Earth by day and night, a biome border, the Mars canyon in a storm and Saturn (U-044), writes smoke_done.txt and quits.
    /// Without the argument it does nothing. Used by tools/unity_smoke.ps1.
    /// </summary>
    public sealed partial class BuildSmoke : MonoBehaviour
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
                // U-204 F6 (LEAD 18:4x): the shot is named for what it shows, the camp by day. The cartoon stage's painted set and unlit
                // sheets take no light from DayNight (only Mercury has a night set), so "smoke_3_earth_night" showed the day at local
                // midnight; a stage tint driven by DayNight is a Backlog line, not this script's to stage.
                yield return Wait(0.5f);
                yield return Shot(folder, "smoke_3_earth_camp_day.png");
                // U-077 smoke: a dig ahead of the surveyor (the Beam), then the Pilgrim airborne with its gear up.
                if (side.player != null && side.rig != null)
                {
                    var p = side.player.transform.position;
                    // U-205 (BLENDER's 0.6.2 read, G7): on the smooth ground the strokes open the ground from its surface, as a player's dig
                    // does. The one stroke was aimed 1.2 m under the surveyor and carved a closed pocket under unbroken grass: with B-230's
                    // wall and the rim's shadow inside it that read as a buried boulder in every later camp shot (3b, 3d, 29, 59, 67).
                    float gx = p.x - 1.5f;
                    bool open = side.terrain != null && side.terrain.SmoothGround;
                    float gy = open ? side.terrain.SurfaceAt(gx) : p.y;
                    bool dug = side.rig.Dig(open ? new Vector2(gx, gy - 0.25f) : new Vector2(gx, p.y - 1.2f));
                    if (open) side.rig.Dig(new Vector2(gx, gy - 0.9f)); // one stroke deeper: an open bowl
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
                inv.Add(Meridian.Terrain.TileId.Sand, 210); // U-204 F9: it was a second stack of Stone: two like lumps side by side read as an art fault
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
                    // U-194 (B-222): the page holding the Thruster Mk2's row, its v3 icon (a flat teal square in 0.6.0)
                    int page = hud.Crafting.PageOf("fab_thruster_mk2");
                    if (page >= 0) hud.Crafting.ShowPage(page);
                    yield return Wait(0.6f);
                    yield return Shot(folder, "smoke_64_crafting_thruster_mk2.png");
                    Debug.Log($"[MERIDIAN] smoke crafting: fab_thruster_mk2 on page {page + 1} of {hud.Crafting.Pages}");
                    hud.Crafting.ShowPage(0);
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
            if (side != null) yield return EarthGround(folder, side); // U-163: Earth on the smooth ground (smoke_29-41)
            if (side != null) yield return EarthDigRun(folder, side); // U-188: the digging game (smoke_47-60, BuildSmokeD1)

            // U-142 (D-158, U-148 / U-150): the climb in the ship frame: full thrust off the pad until the hull boosts at speed (the long flame,
            // the speed lines, the frame widening), then the sound barrier breaking at Earth's 30 m/s (the vapor cone, the shock ring).
            {
                var pilgrim = side.ship;
                var follow = side.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
                if (pilgrim != null && follow != null)
                {
                    int booms = 0;
                    System.Action onBoom = () => booms++;
                    pilgrim.SoundBarrierBroken += onBoom;
                    var boarding = pilgrim.GetComponent<Meridian.Ship.ShipBoarding>();
                    var pad = pilgrim.Body.position;
                    boarding.ForceAboard();
                    follow.enabled = true; // LookAt froze it
                    follow.SnapToTarget();
                    pilgrim.externalInput = true;
                    pilgrim.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f };
                    float until = Time.realtimeSinceStartup + 45f;
                    while ((pilgrim.Body.linearVelocity.magnitude < 15f || pilgrim.Boost < 0.95f) && Time.realtimeSinceStartup < until) yield return null;
                    yield return Shot(folder, "smoke_27_climb_boost.png");
                    while (booms == 0 && Time.realtimeSinceStartup < until) yield return null;
                    if (booms > 0) { yield return Wait(0.28f); yield return Shot(folder, "smoke_28_sound_barrier.png"); }
                    else Debug.Log("[MERIDIAN] smoke: the climb broke no sound barrier");
                    pilgrim.intent = default;
                    pilgrim.SoundBarrierBroken -= onBoom;
                    // 0.4.8's smoke finding: the surveyor stayed aboard into every later planet (no surveyor, the ship's HUD rows). Back on the
                    // pad and out of the ship, so Mars, Mercury, Venus and Jupiter are walked as before.
                    pilgrim.Body.linearVelocity = Vector2.zero;
                    pilgrim.Body.position = pad; pilgrim.transform.position = pad;
                    float settle = Time.realtimeSinceStartup + 5f;
                    while (!pilgrim.Grounded && Time.realtimeSinceStartup < settle) yield return null;
                    yield return Wait(0.3f);
                    if (!boarding.TryExit()) Debug.Log("[MERIDIAN] smoke: the surveyor could not step out after the climb");
                    yield return Wait(0.5f);
                }
            }

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
                LogSmallThingsNearTheSurveyor("G5", 3f); // U-205: the two soft ground pieces beside the surveyor in this shot
                yield return Shot(folder, "smoke_18_mars_shelter_night_lamp.png");
                if (side.dayNight != null) side.dayNight.Override = 0.45f;
            }
            // U-139 (LEAD 16:1x): the Halcyon hauler wreck, a stamped Mars POI: the painted set stands at its stamped ground.
            var hauler = Meridian.Planet.POI.PoiCatalog.HalcyonHauler;
            yield return LookAt(side, hauler.CenterX, 4f, 10f);
            yield return Shot(folder, "smoke_22_mars_hauler.png");
            yield return MarsRoom(folder, side); // U-188: a T4 room (smoke_61)
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
            yield return Card(folder, Meridian.Planets.PlanetId.Venus); // U-142: B-170's card over the vent field

            // U-142 (U-127): Jupiter on the cartoon stage, framed as the u127 captures frame it: a Deck 2 floe with B-156's aerostat deck module
            // staged on it and a Ballast tortoise over it, the storm deck with a Stormglider, the Deep over the Crush Line with its CRUSH band,
            // the Vortex Whale crossing the Great Red Spot in passing, head first (D-138 / U-153: staged facing −x, its centre 13.5 m ahead of the surveyor in
            // the 32 m frame, so its head and flank cross and the flukes stay out). A floe the search misses leaves its shot out, so the count check fails the smoke.
            yield return scenes.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Jupiter));
            side = scenes.PlanetSide;
            if (side.hazards != null) side.hazards.enabled = false;
            if (side.wardens != null) side.wardens.enabled = false;
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();
            int jx = side.spawnX;
            float jh = Meridian.CameraRig.SideView.DefaultHalfHeight;
            if (Floe(side, jx, CloudLayout.Deck2Bottom + 40, CloudLayout.Deck1Bottom - 40, out int fx, out int fy))
            {
                yield return Stand(side, new Vector2(fx + 2.5f, fy + 0.05f), 1.5f, jh);
                var kit = Meridian.Art.ArtLoad.Asset<System.Collections.Generic.IList<Sprite>>("props/common/aerostat_deck");
                yield return kit;
                GameObject deckCard = null;
                if (kit.Status == UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationStatus.Succeeded && kit.Result != null && kit.Result.Count > 0)
                {
                    deckCard = new GameObject("SmokeAerostatDeck");
                    var sr = deckCard.AddComponent<SpriteRenderer>();
                    sr.sprite = kit.Result[0];
                    sr.sortingOrder = 4;
                    deckCard.transform.position = new Vector3(fx + 4.5f, fy, 0f);
                }
                side.creatures.Spawn(Meridian.Creatures.Species.BallastTortoise, new Vector2(fx + 8f, fy + Above(Meridian.Creatures.Species.BallastTortoise)));
                yield return Staged(side);
                yield return Shot(folder, "smoke_23_jupiter_floe_kit.png");
                yield return Card(folder, Meridian.Planets.PlanetId.Jupiter); // U-142: B-170's card over the floe
                side.creatures.DespawnAll();
                if (deckCard != null) Destroy(deckCard);
                if (kit.IsValid()) Meridian.Art.ArtLoad.Release(kit);
            }
            else Debug.Log("[MERIDIAN] smoke: no Deck 2 floe found on Jupiter");
            if (Floe(side, jx, CloudLayout.Deck3Bottom + 40, CloudLayout.Deck2Bottom - 40, out fx, out fy))
            {
                yield return Stand(side, new Vector2(fx + 2.5f, fy + 0.05f), 1.5f, jh);
                side.creatures.Spawn(Meridian.Creatures.Species.Stormglider, new Vector2(fx + 7f, fy + Above(Meridian.Creatures.Species.Stormglider)));
                yield return Staged(side);
                yield return Shot(folder, "smoke_24_jupiter_storm_deck.png");
                side.creatures.DespawnAll();
            }
            else Debug.Log("[MERIDIAN] smoke: no Deck 3 floe found on Jupiter");
            if (Floe(side, jx, CloudLayout.CrushLine + 4, CloudLayout.CrushLine + 60, out fx, out fy))
            {
                yield return Stand(side, new Vector2(fx + 2.5f, fy + 0.05f), 1.5f, jh);
                yield return Staged(side);
                yield return Shot(folder, "smoke_25_jupiter_deep_crush.png");
            }
            else Debug.Log("[MERIDIAN] smoke: no floe found over Jupiter's Crush Line");
            if (Floe(side, CloudLayout.RedSpotCentre - 200, CloudLayout.Deck2Bottom + 40, CloudLayout.Deck1Bottom - 40, out fx, out fy))
            {
                yield return Stand(side, new Vector2(fx + 2.5f, fy + 0.05f), 1.5f, jh);
                side.creatures.Spawn(Meridian.Creatures.Species.VortexWhale, new Vector2(fx + 16f, fy + 9f))?.Stage(-1, 15f); // U-153: staged facing −x, head first
                yield return Staged(side);
                yield return Shot(folder, "smoke_26_jupiter_red_spot_whale.png");
                side.creatures.DespawnAll();
            }
            else Debug.Log("[MERIDIAN] smoke: no Deck 2 floe found in Jupiter's Red Spot");
            side.creatures.autoSpawn = true;

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
            yield return SpaceMaps(folder, scenes, craft); // U-188 (U-184): the minimap and the system map (smoke_62 / 63)

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

            File.WriteAllText(Path.Combine(folder, "smoke_done.txt"), $"OK {GameInfo.Version} {(Debug.isDebugBuild ? "development" : "release")} {DateTime.Now:s}"); // U-143: which player the shots are from
            Application.Quit();
        }

        /// <summary>
        /// U-163 (Build 0.5.0, D-161 / D-162): Earth on the smooth ground, staged after smoke_4. smoke_29 the camp on the curve (wide), smoke_30 a
        /// hill, smoke_31 a fresh scoop, smoke_32 a short tunnel, smoke_33 a mound ramp, smoke_34 / 35 an iron node full and harvested, smoke_36 a
        /// surveyed pocket (its scan X above), smoke_37 the pocket dug, smoke_38 / 39 / 40 the desert, taiga and tundra sets on the ground,
        /// smoke_42 a forest valley (U-164: the set's nearest layer going on down), smoke_41 the coast cliff. The Rig's reach is lifted for the staging and restored; the climb after it boards the Pilgrim itself.
        /// </summary>
        static IEnumerator EarthGround(string folder, PlanetSideRoot side)
        {
            var t = side.terrain;
            var rig = side.rig;
            if (t == null || rig == null || !t.SmoothGround) yield break;
            var owner = rig.owner;
            rig.owner = null;
            try
            {
                var cam = side.sideCamera;
                float half = cam.orthographicSize;
                yield return LookAt(side, side.spawnX + 6f, 5f, half * 1.25f);
                yield return Staged(side);
                yield return Shot(folder, "smoke_29_earth_camp_curve.png");
                Meridian.CameraRig.SideView.SetHalfHeight(cam, half);

                // A hill: the highest natural ground between the camp's band and the desert.
                int hill = 600, top = int.MinValue;
                for (int x = 400; x < 1250; x++) { int h = t.OriginalTop(x); if (t.PadTop(x) == int.MinValue && h > top) { top = h; hill = x; } }
                yield return LookAt(side, hill - 6f, 3f);
                yield return Staged(side);
                yield return Shot(folder, "smoke_30_earth_hill.png");

                // A gentle stretch east of the camp: a scoop, then a tunnel down and along into the cross-section, then a mound ramp.
                int bx = side.spawnX + 40;
                for (int x = side.spawnX + 40; x < side.spawnX + 300; x++)
                {
                    bool flat = t.PadTop(x) == int.MinValue;
                    for (int k = 0; k < 20 && flat; k++) flat = Mathf.Abs(t.OriginalTop(x + k + 1) - t.OriginalTop(x + k)) <= 1 && t.PadTop(x + k) == int.MinValue;
                    if (flat) { bx = x; break; }
                }
                yield return LookAt(side, bx + 0.5f, 1f);
                int sx = bx + 4;
                float sy = t.SurfaceAt(sx + 0.5f);
                bool scooped = rig.Dig(new Vector2(sx + 0.5f, sy - 0.25f)); // D-168: aimed into the ground (0.1 m above it nothing was in reach where the drawn surface stands over the grid top)
                yield return Wait(0.8f);
                yield return Shot(folder, "smoke_31_earth_scoop.png");
                int strokes = 0;
                for (int k = 0; k < 12; k++) if (rig.Dig(new Vector2(sx + 1.1f + k * 0.6f, sy - 0.5f - Mathf.Min(k, 6) * 0.5f))) strokes++; // from the scoop down and along
                yield return Wait(0.8f);
                yield return Shot(folder, "smoke_32_earth_tunnel.png");
                int mx = bx + 16, piled = 0;
                for (int row = 0; row < 3; row++) // a held Builder's sweep: a stroke every 0.3 m (D-168)
                    for (float px = mx - 3f + row; px <= mx + 3f - row + 1e-3f; px += 0.3f)
                        piled += rig.Mound(new Vector2(px, t.CurveAt(Mathf.FloorToInt(px)) + 0.5f + row * 0.6f), rig.GroundMaterial, false);
                yield return LookAt(side, mx - 5.5f, 1.5f);
                yield return Shot(folder, "smoke_33_earth_mound.png");
                Debug.Log($"[MERIDIAN] smoke ground: scoop {scooped} at {sx}, tunnel {strokes} of 12 strokes, mound {piled} tiles at {mx}");

                // An iron node (else the nearest node) east of the camp, full and harvested.
                var finds = side.finds;
                if (finds != null && finds.Active)
                {
                    Meridian.Mining.ResourceFinds.Node node = null;
                    foreach (var n in finds.nodes)
                    {
                        if (n.x <= side.spawnX + 30) continue;
                        bool better = node == null || (n.item == "iron" && node.item != "iron") || ((n.item == "iron") == (node.item == "iron") && n.x < node.x);
                        if (better) node = n;
                    }
                    if (node != null)
                    {
                        yield return LookAt(side, node.x - 2f, 2f);
                        yield return Staged(side);
                        yield return Shot(folder, "smoke_34_earth_node_full.png");
                        for (int k = 0; k < Meridian.Mining.ResourceFinds.NodeCharges; k++) rig.Dig(new Vector2(node.x + 0.5f, node.y + 0.6f));
                        yield return Wait(0.8f);
                        yield return Shot(folder, "smoke_35_earth_node_harvested.png");
                        Debug.Log($"[MERIDIAN] smoke node: {node.item} at {node.x}, charges {node.charges}");
                    }
                    // A shallow pocket, surveyed (the scan X above it), then dug to.
                    Meridian.Mining.ResourceFinds.Pocket pocket = null;
                    foreach (var p in finds.pockets)
                        if (p.kind == Meridian.Mining.ResourceFinds.Kind.Pocket && p.x > side.spawnX + 30 && t.OriginalTop(p.x) - p.y <= 5 && (pocket == null || p.x < pocket.x)) pocket = p;
                    if (pocket != null)
                    {
                        yield return LookAt(side, pocket.x - 3f, -1.5f);
                        finds.Reveal(new Vector2(pocket.x + 0.5f, pocket.y + 0.5f), 6f);
                        var c = cam.transform.position;
                        cam.transform.position = new Vector3(pocket.x + 0.5f, c.y, c.z);
                        yield return Wait(0.5f);
                        yield return Shot(folder, "smoke_36_earth_scan_x.png");
                        float x = pocket.x + 0.5f;
                        for (float y = t.SurfaceAt(x) - 0.3f; y > pocket.y + 1f; y -= 0.7f) rig.Dig(new Vector2(x, y));
                        rig.Dig(new Vector2(x, pocket.y + 0.5f));
                        yield return Wait(0.8f);
                        yield return Shot(folder, "smoke_37_earth_pocket_dug.png");
                        Debug.Log($"[MERIDIAN] smoke pocket: {pocket.item} at ({pocket.x}, {pocket.y}), spent {pocket.spent}");
                    }
                }

                // B-179's sets on the smooth ground (U-161): the desert, the taiga and the tundra, each mid-band.
                foreach (var (biome, name) in new[] { (Meridian.Terrain.Biome.Desert, "smoke_38_earth_desert.png"), (Meridian.Terrain.Biome.Taiga, "smoke_39_earth_taiga.png"), (Meridian.Terrain.Biome.Tundra, "smoke_40_earth_tundra.png") })
                {
                    Meridian.Terrain.EarthBiomes.Range(biome, out int bs, out int bl);
                    yield return LookAt(side, bs + bl / 2, 3f);
                    yield return Staged(side);
                    yield return Shot(folder, name);
                }

                // U-164 (D-169): a valley beside a hill in the forest band, the forest set's nearest layer going on down under its edge.
                Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Forest, out int fs, out int fl);
                int valley = fs + fl / 2; float dip = 0f;
                for (int x = fs + 60; x < fs + fl - 60; x += 3)
                {
                    if (x > side.spawnX - 80 && x < side.spawnX + 80) continue; // away from the camp's pad
                    float here = t.CurveAt(x), low = here;
                    for (int dx = -12; dx <= 12; dx += 2) low = Mathf.Min(low, t.CurveAt(x + dx));
                    if (here - low > dip) { dip = here - low; valley = x; }
                }
                // LEAD (the release's order for 0.6.2's smoke): the pack is emptied before the valley shot. The inventory, crafting and
                // catalogue stagings above leave it loaded, and the HUD then reads a heavy pack over a landscape frame.
                if (GameState.Instance != null && GameState.Instance.inventory != null) GameState.Instance.inventory.Clear();
                yield return LookAt(side, valley, 3f);
                yield return Staged(side);
                yield return Shot(folder, "smoke_42_earth_forest_valley.png");
                Debug.Log($"[MERIDIAN] smoke forest valley at {valley} (dip {dip:F1} m), fill layer {(side.cartoon != null && side.cartoon.Layers != null ? side.cartoon.Layers.FillLayer : -1)}");

                // The coast cliff: the steepest drop of the curve where the land meets the sea.
                Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Ocean, out int os, out _);
                int cliff = os; float steep = 0f;
                for (int x = os - 40; x < os + 80; x++) { float s = Mathf.Abs(t.CurveAt(x + 1) - t.CurveAt(x)); if (s > steep) { steep = s; cliff = x; } }
                yield return LookAt(side, cliff - 4f, 3f);
                yield return Staged(side);
                yield return Shot(folder, "smoke_41_earth_coast_cliff.png");
                Debug.Log($"[MERIDIAN] smoke coast cliff at {cliff} (step {steep:F2} m per m)");

                // U-166 (D-171): the surveyor in the sea, 4+ m under the water line off the shore (only the sea holds water now).
                int datum = side.Config.datumY, swim = os + 16;
                for (int x = os + 16; x < os + 400; x++) if (t.Generator.SurfaceHeight(t.WrapX(x)) <= datum - 4) { swim = x; break; }
                yield return LookAt(side, swim, 3f);
                yield return Staged(side);
                yield return Shot(folder, "smoke_43_earth_sea.png");
                Debug.Log($"[MERIDIAN] smoke sea at {swim}: the floor {t.Generator.SurfaceHeight(t.WrapX(swim))}, the water line {datum + 1}");

                // U-173 (B-195): the Earth POI props drawn as v3 sheets (the grey v2 models are gone): the Survey Archive and the Launch Complex.
                yield return LookAt(side, Meridian.Planet.POI.PoiCatalog.SurveyArchive.CenterX, 3f);
                yield return Staged(side);
                yield return Shot(folder, "smoke_44_earth_survey_archive.png");
                yield return LookAt(side, Meridian.Planet.POI.PoiCatalog.LaunchComplex.CenterX, 4f);
                yield return Staged(side);
                yield return Shot(folder, "smoke_45_earth_launch_complex.png");

                // U-173 (U-172, the owner's report): a downhill walk as a strip of four frames 0.3 s apart down a 10 m slope east of the camp:
                // walk all the way, never fall / land.
                int hx = -1;
                for (int x = side.spawnX + 40; x < side.spawnX + 1200 && hx < 0; x++)
                {
                    float drop = t.CurveAt(x) - t.CurveAt(x + 10);
                    if (drop < 2.5f || drop > 6.5f) continue;
                    bool ok = true;
                    for (int k = 0; k < 12 && ok; k++) ok = t.PadTop(x + k) == int.MinValue && t.CurveAt(x + k) - t.CurveAt(x + k + 1) >= -0.05f && t.CurveAt(x + k) - t.CurveAt(x + k + 1) <= 0.68f;
                    if (ok) hx = x;
                }
                if (hx >= 0)
                {
                    yield return LookAt(side, hx + 5f, 3f);
                    var walker = side.player;
                    var wb = walker.Body;
                    wb.position = new Vector2(hx + 0.5f, t.SurfaceAt(hx + 0.5f) + 0.05f); walker.transform.position = wb.position; wb.linearVelocity = Vector2.zero;
                    bool ext = walker.externalInput;
                    walker.externalInput = true; walker.intent = default;
                    var follow = side.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
                    if (follow != null) { follow.enabled = true; follow.SnapToTarget(); }
                    yield return Wait(0.6f);
                    walker.intent = new Meridian.Player.PlayerIntent { move = 1f };
                    for (int f = 0; f < 4; f++)
                    {
                        yield return Wait(0.3f);
                        yield return Shot(folder, $"smoke_46{(char)('a' + f)}_earth_downhill_walk.png");
                        Debug.Log($"[MERIDIAN] smoke downhill walk frame {f + 1}: x {wb.position.x:F2}, grounded {walker.Grounded}, clip {(side.cartoon != null && side.cartoon.Surveyor != null ? side.cartoon.Surveyor.Clip : "?")}, snaps {walker.Snaps}");
                    }
                    walker.intent = default; walker.externalInput = ext;
                }
                else Debug.Log("[MERIDIAN] smoke downhill walk: no slope found");
            }
            finally { rig.owner = owner; }
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

        /// <summary>U-142: a floe at least 6 columns wide whose top lies in [y0, y1], searched rightward from x0 (the u127 capture's search): its left column and standing height.</summary>
        static bool Floe(PlanetSideRoot side, int x0, int y0, int y1, out int fx, out int fy)
        {
            var t = side.terrain;
            for (int x = x0; x < x0 + 1200; x++)
                for (int y = y1; y >= y0; y--)
                {
                    if (!Solid(t, x, y) || Solid(t, x, y + 1)) continue;
                    bool wide = true;
                    for (int k = 1; k < 6 && wide; k++) wide = Solid(t, x + k, y) && !Solid(t, x + k, y + 1);
                    if (wide) { fx = x; fy = y + 1; return true; }
                }
            fx = x0; fy = y1; return false;
        }

        static bool Solid(Meridian.Terrain.TerrainStreamer t, int x, int y) => Meridian.Terrain.TileId.IsSolid(t.GetTile(x, y));

        static float Above(Meridian.Creatures.Species s) => Meridian.Creatures.SpeciesSpec.Get(s).size.y * 0.5f + 3f;

        /// <summary>U-142: waits (up to 10 s) for the cartoon stage's crossfade and for its layers and the active storm veil to swap their placeholders for art, then 1.5 s for the creatures.</summary>
        static IEnumerator Staged(PlanetSideRoot side)
        {
            var stage = side.cartoon;
            float until = Time.realtimeSinceStartup + 10f;
            while (stage != null && Time.realtimeSinceStartup < until)
            {
                bool layers = stage.Layers != null && stage.Layers.placeholders.Contains(true);
                var veil = stage.StormLayers;
                bool veiled = veil != null && veil.isActiveAndEnabled && veil.alpha > 0f && veil.placeholders.Contains(true);
                if (!stage.Fading && !layers && !veiled) break;
                yield return null;
            }
            yield return Wait(1.5f);
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
            if (planet == Meridian.Planets.PlanetId.Mars) LogSmallThingsNearTheShip(); // U-204 F14
            cards.Hide();
        }

        /// <summary>U-204 F14 (B-228's read of smoke_21 Mars, in 0.6.0's shot too: a flat pale square, about 0.7 x 0.5 m, floats behind the
        /// Pilgrim at hatch height). A loaded, creature-free Mars shows no such thing (CaptureU196Holes' probe), so it belongs to this
        /// moment: every small drawn thing round the landed ship is named in the log, so the object and its art key can be told.</summary>
        static void LogSmallThingsNearTheShip()
        {
            var director = FindAnyObjectByType<SceneDirector>();
            var side = director != null ? director.PlanetSide : null;
            if (side == null || side.ship == null || side.ship.Body == null) return;
            var shipAt = side.ship.Body.position;
            int found = 0;
            foreach (var r in FindObjectsByType<Renderer>(FindObjectsInactive.Exclude))
            {
                if (!r.enabled) continue;
                var b = r.bounds;
                if (Mathf.Abs(b.center.x - shipAt.x) > 9f || b.center.y < shipAt.y + 0.5f || b.center.y > shipAt.y + 9f) continue;
                if (b.size.x > 1.8f || b.size.y > 1.8f || b.size.x < 0.15f) continue;
                var sr = r as SpriteRenderer;
                string path = r.name;
                for (var up = r.transform.parent; up != null && path.Length < 160; up = up.parent) path = up.name + "/" + path;
                string drawn = sr != null ? (sr.sprite != null ? sr.sprite.name + " (" + (sr.sprite.texture != null ? sr.sprite.texture.name : "no texture") + ")" : "NO SPRITE")
                    : (r.sharedMaterial != null && r.sharedMaterial.mainTexture != null ? r.sharedMaterial.mainTexture.name : "no main texture");
                Debug.Log($"[MERIDIAN] smoke F14 near the Pilgrim: {path}: {r.GetType().Name} {b.size.x:0.00} x {b.size.y:0.00} m at ({b.center.x - shipAt.x:+0.0;-0.0}, {b.center.y - shipAt.y:+0.0;-0.0}) from the ship, drawing {drawn}, order {r.sortingOrder}{(sr != null ? ", colour " + ColorUtility.ToHtmlStringRGBA(sr.color) : "")}");
                found++;
            }
            Debug.Log($"[MERIDIAN] smoke F14: {found} small drawn thing(s) within 9 m of the landed Pilgrim");
        }

        /// <summary>U-205 (BLENDER's read of 0.6.2's smoke_18, G5: beside the surveyor a dark rounded lump and a tan grooved mound are
        /// drawn soft, their edges stepping in 4-5 px blocks, while the surveyor and the lamp are crisp): every small drawn thing round
        /// the surveyor is named in the log with its texture's size, the mip it is drawn from (a streamed map still at a low mip is a
        /// low-resolution copy) and its scale, so the two objects and the reason can be told from the next smoke.</summary>
        static void LogSmallThingsNearTheSurveyor(string tag, float reach)
        {
            var director = FindAnyObjectByType<SceneDirector>();
            var side = director != null ? director.PlanetSide : null;
            if (side == null || side.player == null) return;
            Vector2 at = side.player.transform.position;
            int found = 0;
            foreach (var r in FindObjectsByType<Renderer>(FindObjectsInactive.Exclude))
            {
                if (!r.enabled) continue;
                var b = r.bounds;
                if (Mathf.Abs(b.center.x - at.x) > reach || b.center.y < at.y - 1.5f || b.center.y > at.y + 2.5f) continue;
                if (b.size.x > 2.5f || b.size.y > 2.5f || b.size.x < 0.15f) continue;
                if (r.transform.IsChildOf(side.player.transform)) continue; // the surveyor's own parts
                var sr = r as SpriteRenderer;
                string path = r.name;
                for (var up = r.transform.parent; up != null && path.Length < 160; up = up.parent) path = up.name + "/" + path;
                var tex = (sr != null ? (sr.sprite != null ? sr.sprite.texture : null) : (r.sharedMaterial != null ? r.sharedMaterial.mainTexture : null)) as Texture2D;
                string drawn = sr != null ? (sr.sprite != null ? sr.sprite.name : "NO SPRITE") : (r.sharedMaterial != null ? r.sharedMaterial.name : "no material");
                string map = tex != null ? $"{tex.name} {tex.width} x {tex.height} {tex.format}, {tex.mipmapCount} mip(s), drawn from mip {tex.loadedMipmapLevel} (asked {tex.requestedMipmapLevel}, streamed {tex.streamingMipmaps})" : "no texture";
                Debug.Log($"[MERIDIAN] smoke {tag} near the surveyor: {path}: {r.GetType().Name} {b.size.x:0.00} x {b.size.y:0.00} m at ({b.center.x - at.x:+0.0;-0.0}, {b.center.y - at.y:+0.0;-0.0}), drawing {drawn} on {map}, scale {r.transform.lossyScale.x:0.00}, order {r.sortingOrder}");
                found++;
            }
            Debug.Log($"[MERIDIAN] smoke {tag}: {found} small drawn thing(s) within {reach:0} m of the surveyor");
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
