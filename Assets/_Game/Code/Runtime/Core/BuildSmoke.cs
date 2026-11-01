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
                side.dayNight.Override = 0f;
                yield return Wait(1f);
                yield return Shot(folder, "smoke_3_earth_night.png");
                side.dayNight.Override = 0.45f;
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
                foreach (var key in new[] { "iron", "copper", "carbon", "silica", "water_ice", "oxygen", "launch_fuel", "wood", "clay" })
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

            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Ocean, out int coast, out _);
            yield return LookAt(side, coast - 10f, 8f);
            yield return Shot(folder, "smoke_4_desert_ocean.png");

            var mars = GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mars);
            yield return scenes.LoadPlanetSide(mars);
            side = scenes.PlanetSide;
            if (side.dayNight != null) side.dayNight.Override = 0.45f;
            // U-053: the Mars Warden outpost, its patrol and a sentinel called by over-mining, firing.
            if (side.wardens != null)
            {
                float outpost = Meridian.Planet.POI.PoiCatalog.WardenOutpost.CenterX;
                yield return LookAt(side, outpost + 10f, 3f, 9f);
                if (side.hazards != null) side.hazards.enabled = false;
                var feet = side.player.Body.position;
                var hunter = side.wardens.Spawn(feet + new Vector2(5f, 4.5f), feet, Meridian.Creatures.Wardens.SentinelState.Hunt);
                yield return Wait(1.4f);
                if (hunter != null) side.wardens.Fire(hunter.Body.position, side.player.Body.position + new Vector2(0f, 0.9f) - hunter.Body.position);
                yield return Wait(0.15f);
                yield return Shot(folder, "smoke_12_warden.png");
                side.wardens.DespawnAll();
                if (side.hazards != null) side.hazards.enabled = true;
            }
            // On the canyon wall's terraces (as the U-039 capture): wall, ledges and the far rim in one view.
            int canyon = Meridian.Terrain.MarsLandforms.CanyonStart + 60;
            yield return LookAt(side, canyon, 6f, 24f);
            yield return Shot(folder, "smoke_5_mars_canyon.png");
            // Storm onset (8 s ramp): early on the haze is up and the canyon still reads through it.
            if (side.dustStorm != null) side.dustStorm.Force(0f, 60f);
            yield return Wait(1f);
            yield return Shot(folder, "smoke_6_mars_canyon_storm.png");

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

            // U-052: docked at the Earth Waystation, the Halcyon market open (some goods aboard, a thirsty tank).
            var bay = scenes.Space != null ? scenes.Space.GetComponent<Meridian.Trade.DockingBay>() : null;
            if (bay != null && GameState.Instance != null)
            {
                var st = GameState.Instance;
                st.inventory.Add(Meridian.Items.ItemRegistry.Get("iron").id, 12);
                st.inventory.Add(Meridian.Items.ItemRegistry.Get("suit_patch").id, 3);
                st.fuel = st.tankCapacity * 0.4f;
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
            if (size > 0f) side.sideCamera.orthographicSize = size;
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
