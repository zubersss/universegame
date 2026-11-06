using System;
using System.Collections;
using System.IO;
using Meridian.Core;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// Boots Core (Earth) and saves what the side camera sees at 1920×1080 to
    /// logs/capture_&lt;name&gt;.png. Run by tools/unity_capture.ps1 (sets MERIDIAN_CAPTURE); skipped otherwise.
    /// </summary>
    public class SceneCapture
    {
        public const string Variable = "MERIDIAN_CAPTURE";
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        /// <summary>Top-down view at Earth: saves a frame and asserts ≤ 80 draw calls (Bible §11.1).</summary>
        [UnityTest]
        public IEnumerator CaptureSpace()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            director.SetView(ViewMode.Space);
            var cam = director.Space.GetComponentInChildren<Camera>();
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 260f); // Earth, Luna, Mars and both wells in one frame
            for (int i = 0; i < 30; i++) yield return null; // textures load

            using (var draws = Unity.Profiling.ProfilerRecorder.StartNew(Unity.Profiling.ProfilerCategory.Render, "Draw Calls Count"))
            {
                // Batch mode doesn't render cameras on its own: render the view explicitly each frame.
                var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
                cam.targetTexture = rt;
                long worst = 0;
                for (int i = 0; i < 10; i++)
                {
                    cam.Render();
                    yield return null;
                    worst = Math.Max(worst, draws.LastValue);
                }
                cam.targetTexture = null;
                rt.Release();
                TestContext.Out.WriteLine($"[MERIDIAN] Space draw calls: {worst} (recorder valid {draws.Valid})");
                Assert.IsTrue(draws.Valid, "draw call recorder available");
                Assert.Greater(worst, 0, "the recorder actually saw the frame");
                Assert.LessOrEqual(worst, 80, "≤ 80 draw calls top-down");
            }
            yield return Save(cam, name);
        }

        /// <summary>U-024 evidence: Earth and Mars backdrops, each before and after a 12 m pan.</summary>
        [UnityTest]
        public IEnumerator CaptureBackdrop()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            foreach (var planet in new[] { Meridian.Planets.PlanetId.Earth, Meridian.Planets.PlanetId.Mars })
            {
                if (director.PlanetSide.Config.id != planet)
                    yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(planet));
                var side = director.PlanetSide;
                var cam = side.sideCamera;
                cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
                float until = Time.realtimeSinceStartup + 10f;
                while ((side.backdrop.LayersLoaded < 3 || !side.terrain.IsSettled) && Time.realtimeSinceStartup < until) yield return null;
                var start = cam.transform.position;
                // Where a player sees it: a few metres above the local surface.
                float surface = side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(Mathf.FloorToInt(start.x)));
                cam.transform.position = new Vector3(start.x, surface + 6f, start.z);
                for (int i = 0; i < 5; i++) yield return null;
                string p = planet.ToString().ToLowerInvariant();
                yield return Save(cam, $"{name}_{p}_a");
                cam.transform.position += new Vector3(12f, 0f, 0f);
                for (int i = 0; i < 5; i++) yield return null;
                yield return Save(cam, $"{name}_{p}_b");
            }
        }

        /// <summary>U-025 evidence: Earth at dawn, noon, dusk and night (local time pinned).</summary>
        [UnityTest]
        public IEnumerator CaptureDayNight()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady || !director.PlanetSide.terrain.IsSettled) { if (Time.realtimeSinceStartup > timeout) break; yield return null; }
            var side = director.PlanetSide;
            float until = Time.realtimeSinceStartup + 10f;
            while (side.backdrop.LayersLoaded < 3 && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate(); // player settles
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            var times = new[] { ("dawn", 0.27f), ("noon", 0.5f), ("dusk", 0.73f), ("night", 0.02f) };
            foreach (var (label, t) in times)
            {
                side.dayNight.Override = t;
                for (int i = 0; i < 3; i++) yield return null;
                TestContext.Out.WriteLine($"[MERIDIAN] {label}: t {t:F2} sun {side.dayNight.sun.intensity:F2} ambient {side.dayNight.ambient.intensity:F2}");
                yield return Save(cam, $"{name}_{label}");
            }
            side.dayNight.Override = null;
        }

        /// <summary>U-026 evidence: Mars at noon, clear and in a full dust storm.</summary>
        [UnityTest]
        public IEnumerator CaptureDustStorm()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mars));
            var side = director.PlanetSide;
            float until = Time.realtimeSinceStartup + 10f;
            while ((side.backdrop.LayersLoaded < 3 || !side.terrain.IsSettled || !side.dustStorm.PuffsLoaded) && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            side.dayNight.Override = 0.5f;
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            for (int i = 0; i < 3; i++) yield return null;
            yield return Save(cam, $"{name}_clear");
            var time = UnityEngine.Object.FindAnyObjectByType<TimeSystem>();
            side.dustStorm.Force(0.5f, 300f);
            time.Advance(0.5f + Meridian.Planet.Weather.DustStorm.RampRealSeconds + 1f);
            for (int i = 0; i < 10; i++) yield return null;
            TestContext.Out.WriteLine($"[MERIDIAN] storm: intensity {side.dustStorm.Intensity:F2} visibility {side.dustStorm.Visibility:F1} m");
            yield return Save(cam, $"{name}_storm");
            side.dayNight.Override = null;
        }

        /// <summary>U-036 evidence: B-015 stag and wolf at true size next to the surveyor (Earth, noon).</summary>
        [UnityTest]
        public IEnumerator CaptureCreatures()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            side.dayNight.Override = 0.5f;
            var creatures = side.creatures;
            for (int i = 0; i < 120; i++) yield return null; // creature sheets load
            float px = side.player.transform.position.x;
            Meridian.Creatures.Creature Put(Meridian.Creatures.Species sp, float x)
            {
                int tx = Mathf.FloorToInt(x);
                int s = side.terrain.TopSolidY(tx);
                return creatures.Spawn(sp, new Vector2(tx + 0.5f, s + 1f + Meridian.Creatures.SpeciesSpec.Get(sp).size.y * 0.5f + 0.05f));
            }
            var stag = Put(Meridian.Creatures.Species.Stag, px - 4f);
            var wolf = Put(Meridian.Creatures.Species.GreyWolf, px + 4f);
            for (int i = 0; i < 6; i++) yield return new WaitForFixedUpdate();
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            var playerView = side.player.GetComponentInChildren<SpriteRenderer>();
            TestContext.Out.WriteLine($"[MERIDIAN] stag sprite {stag.View.sprite.name} {stag.View.bounds.size.x:F2} x {stag.View.bounds.size.y:F2} m, wolf {wolf.View.sprite.name} {wolf.View.bounds.size.x:F2} x {wolf.View.bounds.size.y:F2} m, surveyor {playerView.bounds.size.y:F2} m tall");
            yield return Save(cam, name);
            side.dayNight.Override = null;
        }

        /// <summary>U-032 evidence: the surveyor in walk, run, jump, fall, land and dig (camera close in).</summary>
        [UnityTest]
        public IEnumerator CaptureSurveyorStates()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            var player = side.player;
            var view = player.GetComponent<Meridian.Player.PlayerView>();
            for (int i = 0; i < 90; i++) yield return new WaitForFixedUpdate();
            side.dayNight.Override = 0.5f;
            player.externalInput = true;
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 3f);
            IEnumerator Shot(string label)
            {
                var p = player.transform.position;
                cam.transform.position = new Vector3(p.x, p.y + 0.5f, cam.transform.position.z);
                TestContext.Out.WriteLine($"[MERIDIAN] {label}: clip {view.Clip} frame {view.Frame}");
                yield return Save(cam, $"{name}_{label}");
            }
            player.intent.move = -1f; // the Pilgrim is to the right
            for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate();
            yield return Shot("1_walk");
            player.intent.sprint = true;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            yield return Shot("2_run");
            player.intent.move = 0f; player.intent.sprint = false;
            for (int i = 0; i < 40; i++) yield return new WaitForFixedUpdate();
            player.PressJump();
            for (int i = 0; i < 8; i++) yield return new WaitForFixedUpdate();
            yield return Shot("3_jump");
            for (int i = 0; i < 200 && player.Body.linearVelocity.y > -2f; i++) yield return new WaitForFixedUpdate();
            yield return Shot("4_fall");
            for (int i = 0; i < 300 && !player.Grounded; i++) yield return new WaitForFixedUpdate();
            yield return null;
            yield return Shot("5_land");
            for (int i = 0; i < 30; i++) yield return null;
            var b = player.Body.position;
            side.rig.Dig(new Vector2(b.x - 1.5f, b.y - 1.2f));
            for (int i = 0; i < 3; i++) yield return null;
            yield return Shot("6_dig");
            side.dayNight.Override = null;
        }

        /// <summary>U-033 evidence: each effect (dig sparks, landing dust, ship flames, entry shimmer, Escape band, top-down flame).</summary>
        [UnityTest]
        public IEnumerator CaptureFx()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            for (int i = 0; i < 90; i++) yield return new WaitForFixedUpdate();
            side.dayNight.Override = 0.75f; // late light: flames and sparks read
            var cam = side.sideCamera;
            var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
            follow.enabled = false;
            var player = side.player;
            void Frame(Vector2 at, float size) { Meridian.CameraRig.SideView.SetHalfHeight(cam, size); cam.transform.position = new Vector3(at.x, at.y, cam.transform.position.z); }

            // 1 dig sparks
            var b = player.Body.position;
            side.rig.Dig(new Vector2(b.x - 1.5f, b.y - 1.2f));
            Frame(b, 4f);
            for (int i = 0; i < 4; i++) yield return null;
            yield return Save(cam, $"{name}_1_dig_sparks");

            // 2 hard-landing dust: drop the surveyor from 10 m
            int col = Mathf.FloorToInt(b.x - 4f);
            int surface = side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(col));
            player.Body.position = new Vector2(col + 0.5f, surface + 11f);
            player.Body.linearVelocity = Vector2.zero;
            for (int i = 0; i < 200 && player.Grounded; i++) yield return new WaitForFixedUpdate(); // the drop starts (Grounded is stale right after the move)
            for (int i = 0; i < 200 && !player.Grounded; i++) yield return new WaitForFixedUpdate();
            for (int i = 0; i < 4; i++) yield return null;
            Frame(player.Body.position, 4f);
            int under = Mathf.FloorToInt(player.Body.position.y - 1.1f);
            Debug.Log($"[MERIDIAN] landing at {player.LastImpactSpeed:F1} m/s, grounded {player.Grounded}, at {player.Body.position}, tile below {side.terrain.GetTile(Mathf.FloorToInt(player.Body.position.x), under)}, surface {surface}, settled {side.terrain.IsSettled}, fx alive {Meridian.FX.FxPool.TotalAlive}");
            yield return Save(cam, $"{name}_2_landing_dust");

            // 3 side flames: aboard, lift off
            var ship = side.ship;
            side.hazards.boarding.ForceAboard();
            follow.enabled = false;
            ship.externalInput = true;
            ship.intent.thrust = 1f;
            for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate();
            Frame(ship.Body.position + new Vector2(0f, -1f), 7f);
            yield return null;
            yield return Save(cam, $"{name}_3_ship_flames");

            // 4 entry shimmer: high and falling fast, engines off
            ship.intent.thrust = 0f;
            ship.Body.position = new Vector2(ship.Body.position.x, ship.Body.position.y + 60f);
            ship.Body.linearVelocity = new Vector2(0f, -15f);
            for (int i = 0; i < 3; i++) yield return new WaitForFixedUpdate();
            Frame(ship.Body.position, 7f);
            yield return null;
            var sfx = ship.GetComponent<Meridian.FX.ShipFx>();
            Debug.Log($"[MERIDIAN] shimmer active {sfx.Shimmer.active} shown {sfx.Shimmer.target.enabled} sprite {(sfx.Shimmer.target.sprite != null)} color {sfx.Shimmer.target.color} alt {ship.AltitudeAboveGround:F0} vy {ship.Body.linearVelocity.y:F1}");
            yield return Save(cam, $"{name}_4_entry_shimmer");

            // 5 Escape band
            Frame(new Vector2(ship.Body.position.x, side.Config.EscapeLineY), 7f);
            for (int i = 0; i < 3; i++) yield return null;
            yield return Save(cam, $"{name}_5_escape_band");

            // 6 top-down engine flame
            var top = UnityEngine.Object.FindAnyObjectByType<Meridian.Space.SpaceShip>(FindObjectsInactive.Include);
            top.PlaceAtWaystation("earth");
            top.Velocity = Vector2.zero;
            director.SetView(ViewMode.Space);
            top.externalInput = true;
            top.intent.thrust = 1f;
            var spaceCam = director.Space.GetComponentInChildren<Camera>();
            var shipView = top.GetComponentInChildren<SpriteRenderer>(true);
            float wait = Time.realtimeSinceStartup + 10f;
            while (shipView.sprite == null && Time.realtimeSinceStartup < wait) yield return null; // its sheet loads when Space first shows
            for (int i = 0; i < 10; i++) yield return null;
            Meridian.CameraRig.SideView.SetHalfHeight(spaceCam, 8f);
            spaceCam.transform.position = new Vector3(top.transform.position.x, top.transform.position.y, spaceCam.transform.position.z);
            var topView = top.GetComponentInChildren<SpriteRenderer>(true);
            Debug.Log($"[MERIDIAN] space ship destroyed {top.Destroyed} active {top.gameObject.activeInHierarchy} view {topView.name} enabled {topView.enabled} sprite {(topView.sprite != null ? topView.sprite.name : "null")} at {top.Position} cam {spaceCam.transform.position}");
            yield return Save(spaceCam, $"{name}_6_space_flame");
            top.intent.thrust = 0f;
            side.dayNight.Override = null;
        }

        /// <summary>U-034 evidence: Saturn with its rings, Jupiter, Neptune and a belt segment (top-down).</summary>
        [UnityTest]
        public IEnumerator CaptureSpaceArt()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            director.SetView(ViewMode.Space);
            var world = UnityEngine.Object.FindAnyObjectByType<Meridian.Space.SpaceWorld>();
            var cam = director.Space.GetComponentInChildren<Camera>();
            var follow = cam.GetComponent<Meridian.Space.SpaceCamera>();
            if (follow != null) follow.enabled = false;
            float until = Time.realtimeSinceStartup + 15f;
            while ((!world.RingsReady || !world.BeltReady) && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 30; i++) yield return null;
            IEnumerator Shot(string label, Vector2 at, float size)
            {
                Meridian.CameraRig.SideView.SetHalfHeight(cam, size);
                cam.transform.position = new Vector3(at.x, at.y, cam.transform.position.z);
                for (int i = 0; i < 3; i++) yield return null;
                yield return Save(cam, $"{name}_{label}");
            }
            yield return Shot("1_saturn", world.Find("saturn").Value.position, 260f);
            yield return Shot("2_jupiter", world.Find("jupiter").Value.position, 110f);
            yield return Shot("3_neptune", world.Find("neptune").Value.position, 120f);
            var belt = world.BeltClusters.Count > 0 ? world.BeltClusters[0] : new Vector2(Meridian.Space.SpaceLayout.BeltInner + 300f, 0f);
            foreach (var k in world.Belt) Debug.Log($"[MERIDIAN] belt {k.key}: {k.count} rocks × {k.triangles} tris, mat {k.material.name}"); Debug.Log($"[MERIDIAN] belt rocks {world.BeltRocks}, rings ready {world.RingsReady} ({(world.Rings != null ? world.Rings.bounds.size.x : 0f):F1} u), shells {world.Shells.Count}");
            var fb = world.transform.Find("Belt");
            Debug.Log($"[MERIDIAN] fallback belt enabled {(fb != null ? fb.GetComponent<MeshRenderer>().enabled.ToString() : "none")}");
            yield return Shot("4_belt", belt, Meridian.Transitions.TransitionDirector.SpaceDefaultSize);
            yield return Shot("5_earth_luna", world.Find("earth").Value.position + new Vector2(60f, 60f), 120f);
        }

        /// <summary>U-035 evidence: the Earth spawn camp by day and by night (lamps glow).</summary>
        [UnityTest]
        public IEnumerator CaptureSpawnCamp()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            for (int i = 0; i < 120; i++) yield return new WaitForFixedUpdate();
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            var camp = side.pois.placed.Find(p => p.def == Meridian.Planet.POI.PoiCatalog.SpawnCamp);
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 10f);
            cam.transform.position = new Vector3(camp.def.CenterX, camp.groundY + 6f, cam.transform.position.z);
            side.dayNight.Override = 0.5f;
            for (int i = 0; i < 5; i++) yield return null;
            yield return Save(cam, $"{name}_day");
            side.dayNight.Override = 0.02f;
            for (int i = 0; i < 5; i++) yield return null;
            yield return Save(cam, $"{name}_night");
            side.dayNight.Override = null;
        }

        /// <summary>U-037 evidence: the middle of each Earth biome (forest, plains, desert, ocean, taiga, tundra).</summary>
        [UnityTest]
        public IEnumerator CaptureBiomes()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            side.dayNight.Override = 0.45f;
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 14f);
            int i = 0;
            foreach (Meridian.Terrain.Biome b in Enum.GetValues(typeof(Meridian.Terrain.Biome)))
            {
                i++;
                Meridian.Terrain.EarthBiomes.Range(b, out int start, out int len);
                int x = b == Meridian.Terrain.Biome.Forest ? 64 : start + len / 2;
                if (b == Meridian.Terrain.Biome.Ocean) x = start + 50; // the sloping shelf (~26 m deep here): sea surface and seabed in one view
                int top = side.terrain.TopSolidY(x);
                float y = b == Meridian.Terrain.Biome.Ocean ? side.Config.datumY - 13f : top + 6f;
                cam.transform.position = new Vector3(x + 0.5f, y, cam.transform.position.z);
                float until = Time.realtimeSinceStartup + 15f;
                yield return null;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                for (int k = 0; k < 5; k++) yield return null;
                yield return Save(cam, $"{name}_{i}_{b.ToString().ToLowerInvariant()}");
            }
            side.dayNight.Override = null;
        }

        /// <summary>
        /// U-038 evidence: the plains/desert border before, half-way through and past the 20 m cross-fade,
        /// and the camera walked across it at sprint speed with no frame over 33 ms (the sets load ahead).
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureBiomeBorder()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            side.dayNight.Override = 0.45f;
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 14f);
            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Desert, out int border, out _);

            IEnumerator ShootAt(float x, string label)
            {
                int top = side.terrain.TopSolidY(Mathf.FloorToInt(x));
                cam.transform.position = new Vector3(x, top + 6f, cam.transform.position.z);
                float until = Time.realtimeSinceStartup + 15f;
                yield return null;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                for (int k = 0; k < 90; k++) yield return null; // neighbour sets arrive
                yield return Save(cam, $"{name}_{label}");
            }
            yield return ShootAt(border - 40f, "1_plains");
            yield return ShootAt(border + 0.5f, "2_crossfade");
            TestContext.Out.WriteLine($"[MERIDIAN] at the border: main {side.backdrop.MainSet}, overlay {side.backdrop.OverlaySet}, weight {side.backdrop.FadeWeight:F2}");
            yield return ShootAt(border + 40f, "3_desert");

            // Walk the camera across the border at sprint speed (≈ 9 m/s) and watch every frame.
            float x0 = border - 80f, x1 = border + 80f, worst = 0f, worstAt = 0f;
            cam.transform.position = new Vector3(x0, cam.transform.position.y, cam.transform.position.z);
            for (int k = 0; k < 30; k++) yield return null;
            float pos = x0;
            while (pos < x1)
            {
                float t0 = Time.realtimeSinceStartup;
                yield return null;
                float ms = (Time.realtimeSinceStartup - t0) * 1000f;
                if (ms > worst) { worst = ms; worstAt = pos; }
                pos += 9f * Mathf.Min(Time.unscaledDeltaTime, 1f / 30f);
                cam.transform.position = new Vector3(pos, side.terrain.TopSolidY(Mathf.FloorToInt(pos)) + 6f, cam.transform.position.z);
            }
            TestContext.Out.WriteLine($"[MERIDIAN] border walk: worst frame {worst:F1} ms at x {worstAt:F0} (border {border})");
            side.dayNight.Override = null;
            Assert.LessOrEqual(worst, 33f, "no hitch > 33 ms crossing the border (U-038)");
        }

        /// <summary>U-046 evidence: each Rig module in the hand, in use: Beam ray, Lance bolt, Survey ring, Builder ghost (clear and blocked).</summary>
        [UnityTest]
        public IEnumerator CaptureRigModules()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            side.dayNight.Override = 0.45f;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            var cam = side.sideCamera;
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 5f);
            var rig = side.player.GetComponent<Meridian.Player.PlayerRigInput>();
            var inv = GameState.Instance.inventory;
            inv.Clear();
            inv.Add(Meridian.Terrain.TileId.Stone, 20);
            for (int i = 0; i < 90; i++) yield return null; // tool and fx sheets arrive
            Vector2 feet = side.player.Body.position;
            int gx = Mathf.FloorToInt(feet.x) + 3, top = side.terrain.TopSolidY(gx);

            IEnumerator Use(Meridian.Rig.RigModule m, Vector2 aim, bool hold, int frames, string label)
            {
                rig.module = m;
                rig.AimAt(aim);
                rig.holdUse = hold;
                for (int k = 0; k < frames; k++) yield return null;
                yield return Save(cam, $"{name}_{label}");
                rig.holdUse = false;
                float rest = Time.realtimeSinceStartup + 1.2f; // the scan ring and bolts finish
                while (Time.realtimeSinceStartup < rest) yield return null;
            }
            yield return Use(Meridian.Rig.RigModule.Beam, new Vector2(gx + 0.5f, top + 0.5f), true, 8, "1_beam");
            yield return Use(Meridian.Rig.RigModule.Lance, feet + new Vector2(6f, 1.2f), true, 2, "2_lance");
            yield return Use(Meridian.Rig.RigModule.Survey, feet + new Vector2(2f, 1f), true, 5, "3_survey");
            yield return Use(Meridian.Rig.RigModule.Builder, new Vector2(gx + 0.5f, top + 1.5f), false, 6, "4_builder");
            yield return Use(Meridian.Rig.RigModule.Builder, new Vector2(gx + 1.5f, side.terrain.TopSolidY(gx + 1) + 0.5f), false, 6, "5_builder_blocked");
            side.dayNight.Override = null;
        }

        /// <summary>U-050 evidence: the Meridian station on Venus's cloud deck, and the surface by a vent field.</summary>
        [UnityTest]
        public IEnumerator CaptureVenus()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Venus));
            var side = director.PlanetSide;
            side.hazards.enabled = false;
            side.dayNight.Override = 0.45f;
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            var t = side.terrain;
            IEnumerator Shot(string label, float x, float y, float size)
            {
                Meridian.CameraRig.SideView.SetHalfHeight(cam, size);
                cam.transform.position = new Vector3(x, y, cam.transform.position.z);
                var p = new Vector2(x - 2f, y - 3f);
                side.player.Body.position = p; side.player.transform.position = p; // streaming follows the surveyor too
                float until = Time.realtimeSinceStartup + 15f;
                yield return null;
                while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                // Stand the surveyor on whatever is there now (pads included), not inside it.
                int px = Mathf.FloorToInt(x - 2f);
                var feet = new Vector2(px + 0.5f, t.TopSolidY(px) + 1.05f);
                if (feet.y < y + 6f) { side.player.Body.position = feet; side.player.transform.position = feet; side.player.Body.linearVelocity = Vector2.zero; }
                for (int k = 0; k < 60; k++) yield return null;
                yield return Save(cam, $"{name}_{label}");
            }
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            yield return Shot("1_deck_station", station.x + 10f, station.floatY + 6f, 12f);
            var vent = Meridian.Terrain.VenusLandforms.Vents[0];
            int vx = (vent.x0 + vent.x1) / 2;
            yield return Shot("2_surface_vent", vx, t.Generator.SurfaceHeight(t.WrapX(vx)) + 6f, 12f);
            side.dayNight.Override = null;
        }

        /// <summary>U-048 evidence: Mercury's day side, twilight band, night side and a polar cold trap.</summary>
        [UnityTest]
        public IEnumerator CaptureMercury()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            var mercury = GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mercury);
            yield return director.LoadPlanetSide(mercury);
            var side = director.PlanetSide;
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            var t = side.terrain;
            var clock = UnityEngine.Object.FindAnyObjectByType<TimeSystem>();
            int W = mercury.worldWidth;
            IEnumerator Shot(string label, int x, float above, float size, float localDawnOffset)
            {
                // Put the dawn line `localDawnOffset` m ahead of x (0: twilight; +W/4: day, which trails the dawn line; -W/4: night).
                Meridian.Terrain.MercuryTerminator.ClockOffset = 0;
                double now = Meridian.Terrain.MercuryTerminator.Now(clock.GameSeconds);
                Meridian.Terrain.MercuryTerminator.ClockOffset = (x + localDawnOffset) * Meridian.Terrain.MercuryTerminator.CreepSecondsPerMetre - now;
                Meridian.CameraRig.SideView.SetHalfHeight(cam, size);
                cam.transform.position = new Vector3(x + 0.5f, t.Generator.SurfaceHeight(t.WrapX(x)) + above, cam.transform.position.z);
                float until = Time.realtimeSinceStartup + 15f;
                yield return null;
                while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                for (int k = 0; k < 30; k++) yield return null;
                yield return Save(cam, $"{name}_{label}");
            }
            yield return Shot("1_day", 1900, 5f, 12f, W / 4f);             // the solarite field under the Sun
            yield return Shot("2_twilight", 600, 5f, 12f, 0f);             // the flare shelter on the dawn line
            yield return Shot("3_night", 1000, 5f, 12f, -W / 4f);          // the Warden vault in the dark
            int trap = Meridian.Terrain.MercuryLandforms.ColdTrapCentre(0, W);
            yield return Shot("4_cold_trap", trap, 14f, 24f, W / 4f);      // a crater floor in permanent shadow on the day side
            Meridian.Terrain.MercuryTerminator.ClockOffset = 0;
        }

        /// <summary>
        /// U-055 evidence: the Mercury twilight band (glassback, cinderlings, flarewing, the Cinderhulk by day and
        /// after nightfall) and Venus (drifters, acidmoths and the Veil Serpent on the deck; crab and vent eels below).
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureInnerCreatures()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;

            PlanetSideRoot side = null;
            IEnumerator Go(Meridian.Planets.PlanetId planet)
            {
                yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(planet));
                side = director.PlanetSide;
                side.hazards.enabled = false;
                if (side.wardens != null) side.wardens.enabled = false;
                var v = side.player.GetComponent<Meridian.Player.PlayerVitals>();
                v.maxHealth = v.health = 1e6f;
                side.sideCamera.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
                float until = Time.realtimeSinceStartup + 10f;
                foreach (Meridian.Creatures.Species s in Enum.GetValues(typeof(Meridian.Creatures.Species)))
                    if (Meridian.Creatures.SpeciesSpec.Get(s).planet == planet)
                        while (!side.creatures.ArtReady(s) && Time.realtimeSinceStartup < until) yield return null;
            }
            IEnumerator Stand(Vector2 feet, float camAbove, float size)
            {
                var p = side.player;
                p.Body.position = feet; p.transform.position = feet; p.Body.linearVelocity = Vector2.zero;
                Meridian.CameraRig.SideView.SetHalfHeight(side.sideCamera, size);
                side.sideCamera.transform.position = new Vector3(feet.x, feet.y + camAbove, side.sideCamera.transform.position.z);
                float until = Time.realtimeSinceStartup + 15f;
                yield return null;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                for (int k = 0; k < 30; k++) yield return new WaitForFixedUpdate();
            }
            void Put(Meridian.Creatures.Species s, float x, float y)
            {
                var c = side.creatures.Spawn(s, new Vector2(x, y));
                if (c != null) c.Body.linearVelocity = Vector2.zero;
            }
            float Ground(float x, Meridian.Creatures.Species s) =>
                side.terrain.TopSolidY(Mathf.FloorToInt(x)) + 1f + Meridian.Creatures.SpeciesSpec.Get(s).size.y * 0.5f + 0.05f;

            // Mercury: the dawn line through the frame.
            yield return Go(Meridian.Planets.PlanetId.Mercury);
            var t = side.terrain;
            int x0 = 2600;
            yield return Stand(new Vector2(x0 + 0.5f, t.Generator.SurfaceHeight(t.WrapX(x0)) + 1.05f), 3f, 9f);
            // Mercury's shared clock: the lighting, the backdrop and the creatures all read it.
            Meridian.Terrain.MercuryTerminator.ClockOffset = 0;
            double now = side.creatures.MercuryNow;
            float dawn = Meridian.Terrain.MercuryTerminator.Dawn(now, side.Config.worldWidth);
            Meridian.Terrain.MercuryTerminator.ClockOffset = (x0 - dawn) * Meridian.Terrain.MercuryTerminator.CreepSecondsPerMetre;
            Put(Meridian.Creatures.Species.Glassback, x0 - 9f, Ground(x0 - 9f, Meridian.Creatures.Species.Glassback));
            for (int i = 0; i < 4; i++) Put(Meridian.Creatures.Species.Cinderling, x0 - 4f + i * 1.1f, Ground(x0 - 4f + i * 1.1f, Meridian.Creatures.Species.Cinderling));
            Put(Meridian.Creatures.Species.Flarewing, x0 + 3f, t.TopSolidY(x0 + 3) + 7f);
            Put(Meridian.Creatures.Species.Cinderhulk, x0 + 9f, Ground(x0 + 9f, Meridian.Creatures.Species.Cinderhulk));
            for (int k = 0; k < 20; k++) yield return null;
            yield return Save(side.sideCamera, $"{name}_1_mercury_twilight");
            // Night falls on the Cinderhulk: its cooled, cracked shell.
            Meridian.Terrain.MercuryTerminator.ClockOffset -= 400f * Meridian.Terrain.MercuryTerminator.CreepSecondsPerMetre;
            float settle = Time.realtimeSinceStartup + 0.8f; // the lighting eases; the hulk swaps its sheet at once
            while (Time.realtimeSinceStartup < settle) yield return null;
            yield return Save(side.sideCamera, $"{name}_2_mercury_cinderhulk_night");
            Meridian.Terrain.MercuryTerminator.ClockOffset = 0;
            int trap = Meridian.Terrain.MercuryLandforms.ColdTrapCentre(0, side.Config.worldWidth);
            side.creatures.DespawnAll();
            yield return Stand(new Vector2(trap + 0.5f, t.Generator.SurfaceHeight(t.WrapX(trap)) + 1.05f), 2f, 7f);
            Put(Meridian.Creatures.Species.Shadewyrm, trap + 4.5f, Ground(trap + 4.5f, Meridian.Creatures.Species.Shadewyrm));
            for (int k = 0; k < 20; k++) yield return null;
            yield return Save(side.sideCamera, $"{name}_3_mercury_shadewyrm");

            // Venus: the deck of the Meridian station.
            yield return Go(Meridian.Planets.PlanetId.Venus);
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            float until2 = Time.realtimeSinceStartup + 5f;
            while (side.pois.Solids.Count < 5 && Time.realtimeSinceStartup < until2) yield return null;
            float deck = station.floatY + (336f - 62f) / 128f;
            float sx = station.x + 10f;
            yield return Stand(new Vector2(sx, deck + 1.5f), 3f, 10f);
            Put(Meridian.Creatures.Species.SulfurDrifter, sx - 8f, deck + 7f);
            Put(Meridian.Creatures.Species.SulfurDrifter, sx + 10f, deck + 9f);
            for (int i = 0; i < 4; i++) Put(Meridian.Creatures.Species.Acidmoth, sx + 2f + i * 0.8f, deck + 3.5f + (i % 2) * 0.6f);
            Put(Meridian.Creatures.Species.VeilSerpent, sx - 1f, deck + 9f); // drawn 3×: it spans the deck
            for (int k = 0; k < 15; k++) yield return null;
            yield return Save(side.sideCamera, $"{name}_4_venus_deck");
            // The surface by a vent field.
            side.creatures.DespawnAll();
            var vent = Meridian.Terrain.VenusLandforms.Vents[0];
            int vx = vent.x0 - 6;
            t = side.terrain;
            yield return Stand(new Vector2(vx + 0.5f, t.Generator.SurfaceHeight(t.WrapX(vx)) + 1.05f), 2f, 8f);
            Put(Meridian.Creatures.Species.PressureCrab, vx - 6f, Ground(vx - 6f, Meridian.Creatures.Species.PressureCrab));
            Put(Meridian.Creatures.Species.VentEel, vx + 7f, Ground(vx + 7f, Meridian.Creatures.Species.VentEel));
            for (int k = 0; k < 20; k++) yield return null;
            yield return Save(side.sideCamera, $"{name}_5_venus_surface");
        }

        /// <summary>U-056 evidence: a shelter on the Mars plains at night (walls, door, lamp, crate) and a Venus aerostat beside the station.</summary>
        [UnityTest]
        public IEnumerator CaptureBases()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            GameState.Instance.basePieces.Clear();
            GameState.Instance.aerostats.Clear();

            // Mars plains at night: a shelter around the surveyor.
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mars));
            var side = director.PlanetSide;
            side.hazards.enabled = false;
            if (side.wardens != null) side.wardens.enabled = false;
            var t = side.terrain;
            int px = Mathf.FloorToInt(side.player.Body.position.x) + 200;
            var feet = new Vector2(px + 0.5f, t.Generator.SurfaceHeight(t.WrapX(px)) + 1.05f);
            side.player.Body.position = feet; side.player.transform.position = feet;
            float until = Time.realtimeSinceStartup + 15f;
            yield return null;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            feet = new Vector2(px + 0.5f, t.TopSolidY(px) + 1.05f);
            side.player.Body.position = feet; side.player.transform.position = feet;
            side.dayNight.Override = 0.02f;
            var b = side.bases;
            int x0 = px - 4, x1 = px + 4, top = 0;
            for (int x = x0; x <= x1; x++) top = Mathf.Max(top, t.TopSolidY(x));
            int roof = top + 4;
            for (int y = t.TopSolidY(x0) + 1; y < roof; y++) b.Place(new Vector2(x0 + 0.5f, y + 0.5f), Meridian.Building.PieceKind.Wall);
            int dg = t.TopSolidY(x1) + 1;
            b.Place(new Vector2(x1 + 0.5f, dg + 0.5f), Meridian.Building.PieceKind.Door);
            for (int y = dg + 2; y < roof; y++) b.Place(new Vector2(x1 + 0.5f, y + 0.5f), Meridian.Building.PieceKind.Wall);
            for (int x = x0; x <= x1; x++) b.Place(new Vector2(x + 0.5f, roof + 0.5f), Meridian.Building.PieceKind.Wall);
            b.Place(new Vector2(px - 2 + 0.5f, t.TopSolidY(px - 2) + 1.5f), Meridian.Building.PieceKind.Lamp);
            b.Place(new Vector2(px + 2 + 0.5f, t.TopSolidY(px + 2) + 1.5f), Meridian.Building.PieceKind.Crate);
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 6f);
            cam.transform.position = new Vector3(px + 0.5f, top + 3f, cam.transform.position.z);
            for (int k = 0; k < 60; k++) yield return new WaitForFixedUpdate();
            Debug.Log($"[MERIDIAN] Mars shelter: sheltered {b.Sheltered(side.player.Body.position)} ({b.LastFlood})");
            yield return Save(cam, $"{name}_1_mars_shelter");

            // Venus: an aerostat in open air beside the Meridian station.
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Venus));
            side = director.PlanetSide;
            side.hazards.enabled = false;
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            until = Time.realtimeSinceStartup + 5f;
            while (side.pois.Solids.Count < 5 && Time.realtimeSinceStartup < until) yield return null;
            float deck = station.floatY + (336f - 62f) / 128f;
            feet = new Vector2(station.x + 6f, deck + 1.5f);
            side.dayNight.Override = 0.5f;
            side.player.Body.position = feet; side.player.transform.position = feet;
            b = side.bases;
            int ax = Mathf.FloorToInt(station.x - 14f), ay = Mathf.FloorToInt(deck);
            for (int i = 0; i < 4; i++) b.Place(new Vector2(ax + i * 2 + 0.5f, ay + 0.5f), Meridian.Building.PieceKind.Deck);
            b.Place(new Vector2(ax + 0.5f, ay + 1.5f), Meridian.Building.PieceKind.FloatCell);
            b.Place(new Vector2(ax + 6.5f, ay + 1.5f), Meridian.Building.PieceKind.FloatCell);
            b.Place(new Vector2(ax + 3.5f, ay + 1.5f), Meridian.Building.PieceKind.Crate);
            b.Place(new Vector2(ax + 2.5f, ay + 1.5f), Meridian.Building.PieceKind.Lamp);
            cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 8f);
            cam.transform.position = new Vector3(station.x - 6f, deck + 3f, cam.transform.position.z);
            for (int k = 0; k < 60; k++) yield return new WaitForFixedUpdate();
            yield return Save(cam, $"{name}_2_venus_aerostat");
            GameState.Instance.basePieces.Clear();
            GameState.Instance.aerostats.Clear();
        }

        /// <summary>U-039 evidence: Mars canyon wall, Olympus flank, polar cap and a lava tube.</summary>
        [UnityTest]
        public IEnumerator CaptureMarsLandforms()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mars));
            var side = director.PlanetSide;
            side.dayNight.Override = 0.42f;
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            var t = side.terrain;
            System.Func<int, int> surf = x => t.Generator.SurfaceHeight(t.WrapX(x));
            IEnumerator Shot(string label, float x, float y, float size)
            {
                Meridian.CameraRig.SideView.SetHalfHeight(cam, size);
                cam.transform.position = new Vector3(x, y, cam.transform.position.z);
                float until = Time.realtimeSinceStartup + 15f;
                yield return null;
                while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                for (int k = 0; k < 5; k++) yield return null;
                yield return Save(cam, $"{name}_{label}");
            }
            int wx = Meridian.Terrain.MarsLandforms.CanyonStart + 60;
            yield return Shot("1_canyon_wall", wx, surf(wx) + 6f, 40f);
            int ox = Meridian.Terrain.MarsLandforms.OlympusCenter - 140;
            yield return Shot("2_olympus_flank", ox, surf(ox) + 4f, 40f);
            yield return Shot("3_polar_cap", 40f, surf(40) + 4f, 14f);
            var tube = Meridian.Terrain.MarsLandforms.Tubes[0];
            int ceil = Meridian.Terrain.MarsLandforms.TubeCeiling(tube, surf);
            yield return Shot("4_lava_tube", tube.x0 + Meridian.Terrain.MarsLandforms.SkylightInset + 6f, ceil - 1f, 12f);
            int floor = (Meridian.Terrain.MarsLandforms.CanyonStart + Meridian.Terrain.MarsLandforms.CanyonEnd) / 2;
            yield return Shot("5_canyon_floor", floor, surf(floor) + 5f, 14f); // U-047: sky sliver over the floor
            side.dayNight.Override = null;
        }

        static IEnumerator Save(Camera cam, string name)
        {
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt;
            cam.Render();
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            cam.targetTexture = null;
            Directory.CreateDirectory("logs");
            var output = $"logs/capture_{name}.png";
            File.WriteAllBytes(output, tex.EncodeToPNG());
            TestContext.Out.WriteLine($"[MERIDIAN] CAPTURE OK: {output}");
            UnityEngine.Object.Destroy(tex);
            rt.Release();
            yield return null;
        }

        [UnityTest]
        public IEnumerator CaptureEarthSurface()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");

#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            yield return SceneManager.LoadSceneAsync("Core", LoadSceneMode.Single);
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout)
                yield return null;
            Assert.IsTrue(director.PlanetSide.terrain.IsSettled, "terrain settled");

            // Give the player time to be released onto the loaded ground and come to rest.
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            var player = director.PlanetSide.player;
            if (player != null)
                TestContext.Out.WriteLine($"[MERIDIAN] player grounded {player.Grounded} at {player.Body.position}, health {player.Vitals?.health}");
            var cam = director.PlanetSide.sideCamera;
            var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
            if (follow != null) follow.enabled = false;
            Assert.AreEqual(9f, Meridian.CameraRig.SideView.HalfHeight(cam), 0.01f, "default half height on the play plane (Bible §5.1)");
            // Look a little below the surface so the shot shows surface, soil and stone seams.
            cam.transform.position += new Vector3(0f, -5f, 0f);
            for (int i = 0; i < 5; i++) yield return null;

            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt;
            cam.Render();
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            cam.targetTexture = null;

            Directory.CreateDirectory("logs");
            var output = $"logs/capture_{name}.png";
            File.WriteAllBytes(output, tex.EncodeToPNG());
            TestContext.Out.WriteLine($"[MERIDIAN] CAPTURE OK: {output}");

            // U-080: the same spot from the depth preset (yaw/pitch orbit around the surveyor): block relief, back wall.
            var pivot = player != null ? (Vector3)player.Body.position + new Vector3(0f, 1.2f, 0f) : cam.transform.position + Vector3.forward * Meridian.CameraRig.SideView.PlaneDistance(cam);
            Meridian.CameraRig.PhotoOrbit.Depth(cam, pivot);
            for (int i = 0; i < 3; i++) yield return null;
            cam.targetTexture = rt;
            cam.Render();
            RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            cam.targetTexture = null;
            var depthOut = $"logs/capture_{name}_depth.png";
            File.WriteAllBytes(depthOut, tex.EncodeToPNG());
            TestContext.Out.WriteLine($"[MERIDIAN] CAPTURE OK: {depthOut}");
            UnityEngine.Object.Destroy(tex);
            rt.Release();
        }

        /// <summary>U-076 evidence: the Earth camp with models, depth bands and flora (day, then the depth preset), and the Mars shelter at night with its lamp, wall and door models.</summary>
        [UnityTest]
        public IEnumerator CaptureDepthBands()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            for (int i = 0; i < 120; i++) yield return new WaitForFixedUpdate();
            // Every prop swap, the Pilgrim and the bands load asynchronously: wait for them all.
            float until = Time.realtimeSinceStartup + 30f;
            while (Time.realtimeSinceStartup < until)
            {
                bool all = side.depthBands != null && side.depthBands.RidgeReady && side.depthBands.SkylineReady;
                foreach (var s in side.pois.ModelSwaps) all &= s.Ready;
                var legs = side.ship.GetComponentInChildren<Meridian.Ship.ShipLegsView>();
                all &= legs != null && legs.Model != null && legs.Model.Ready;
                if (all) break;
                yield return null;
            }
            for (int i = 0; i < 30; i++) yield return null; // flora views settle
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            var camp = side.pois.placed.Find(p => p.def == Meridian.Planet.POI.PoiCatalog.SpawnCamp);
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 10f);
            var pivot = new Vector3(camp.def.CenterX, camp.groundY + 6f, 0f);
            cam.transform.position = new Vector3(pivot.x, pivot.y, cam.transform.position.z);
            side.dayNight.Override = 0.5f;
            for (int i = 0; i < 5; i++) yield return null;
            Debug.Log($"[MERIDIAN] U-076 Earth: ridge {side.depthBands.RidgeKey} depth {side.depthBands.RidgeDepth} mirrored {side.depthBands.RidgeMirrored}, flora {side.depthBands.FloraCount}, swaps {side.pois.ModelSwaps.Count}, sky quad bands {side.backdrop.DepthBandsOn}");
            yield return Save(cam, $"{name}_1_earth_camp_day");
            // Flora on its own (ridge band hidden): the band's low-poly trees otherwise fill the frame (U-076 review, 2026-11-05).
            side.depthBands.SetRidgeVisible(false);
            for (int i = 0; i < 3; i++) yield return null;
            yield return Save(cam, $"{name}_1b_earth_camp_flora");
            side.depthBands.SetRidgeVisible(true);
            for (int i = 0; i < 3; i++) yield return null;
            var pos = cam.transform.position;
            Meridian.CameraRig.PhotoOrbit.Depth(cam, pivot);
            for (int i = 0; i < 3; i++) yield return null;
            yield return Save(cam, $"{name}_2_earth_camp_depth");
            cam.transform.position = pos; cam.transform.rotation = Quaternion.identity;
            side.dayNight.Override = null;

            // The U-074 Mars shelter at night, re-shot with the lamp, wall and door models.
            GameState.Instance.basePieces.Clear();
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mars));
            side = director.PlanetSide;
            side.hazards.enabled = false;
            if (side.wardens != null) side.wardens.enabled = false;
            var t = side.terrain;
            int px = Mathf.FloorToInt(side.player.Body.position.x) + 200;
            var feet = new Vector2(px + 0.5f, t.Generator.SurfaceHeight(t.WrapX(px)) + 1.05f);
            side.player.Body.position = feet; side.player.transform.position = feet;
            until = Time.realtimeSinceStartup + 15f;
            yield return null;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            feet = new Vector2(px + 0.5f, t.TopSolidY(px) + 1.05f);
            side.player.Body.position = feet; side.player.transform.position = feet;
            side.dayNight.Override = 0.02f;
            var b = side.bases;
            int x0 = px - 4, x1 = px + 4, top = 0;
            for (int x = x0; x <= x1; x++) top = Mathf.Max(top, t.TopSolidY(x));
            int roof = top + 4;
            for (int y = t.TopSolidY(x0) + 1; y < roof; y++) b.Place(new Vector2(x0 + 0.5f, y + 0.5f), Meridian.Building.PieceKind.Wall);
            int dg = t.TopSolidY(x1) + 1;
            b.Place(new Vector2(x1 + 0.5f, dg + 0.5f), Meridian.Building.PieceKind.Door);
            for (int y = dg + 2; y < roof; y++) b.Place(new Vector2(x1 + 0.5f, y + 0.5f), Meridian.Building.PieceKind.Wall);
            for (int x = x0; x <= x1; x++) b.Place(new Vector2(x + 0.5f, roof + 0.5f), Meridian.Building.PieceKind.Wall);
            var lamp = b.Place(new Vector2(px - 2 + 0.5f, t.TopSolidY(px - 2) + 1.5f), Meridian.Building.PieceKind.Lamp);
            b.Place(new Vector2(px + 2 + 0.5f, t.TopSolidY(px + 2) + 1.5f), Meridian.Building.PieceKind.Crate);
            cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 6f);
            cam.transform.position = new Vector3(px + 0.5f, top + 3f, cam.transform.position.z);
            until = Time.realtimeSinceStartup + 20f;
            while (Time.realtimeSinceStartup < until && (lamp == null || lamp.model == null || !lamp.model.Ready)) yield return null;
            for (int k = 0; k < 60; k++) yield return new WaitForFixedUpdate();
            var lightT = lamp != null && lamp.go != null ? lamp.go.transform.Find("Light") : null;
            Debug.Log($"[MERIDIAN] U-076 Mars shelter: lamp model {(lamp != null && lamp.model != null && lamp.model.Ready)}, light at {(lightT != null ? lightT.position.ToString("F2") : "none")}, sheltered {b.Sheltered(side.player.Body.position)}");
            yield return Save(cam, $"{name}_3_mars_shelter_night");
            side.dayNight.Override = null;
        }
    }
}
