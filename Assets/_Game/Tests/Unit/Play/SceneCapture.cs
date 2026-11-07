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
        // U-091 (D-110 (4)): review captures force-load every mip, so streamed model maps are never shot reduced under the
        // 512 MB mip budget; the smoke shots (BuildSmoke) keep the budget and show what the player sees.
        bool savedForceAllMips;

        [SetUp]
        public void ForceAllMipsForTheCapture() { savedForceAllMips = Texture.streamingTextureForceLoadAll; Texture.streamingTextureForceLoadAll = true; }

        [TearDown]
        public void RestoreMipStreaming() { Texture.streamingTextureForceLoadAll = savedForceAllMips; }

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
            // U-103: park the ship outside Earth's well for the shots; left at the Waystation it drifts into the Atmosphere Ring and an entry fires mid-capture.
            var parkedShip = director.Space.GetComponentInChildren<Meridian.Space.SpaceShip>();
            if (parkedShip != null)
            {
                parkedShip.externalInput = true;
                parkedShip.intent = default;
                var earthBody = parkedShip.world != null ? parkedShip.world.Find("earth") : null;
                if (earthBody.HasValue) { parkedShip.Position = earthBody.Value.position + new Vector2(0f, earthBody.Value.WellRadius + 50f); parkedShip.Velocity = Vector2.zero; }
            }
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

        /// <summary>U-090 evidence: the Earth camp stage stack from the rail and in the depth preset, and a wide frame at the forest/plains border.</summary>
        [UnityTest]
        public IEnumerator CaptureStageLayers()
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
            var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
            follow.enabled = false;
            var camp = side.pois.placed.Find(p => p.def == Meridian.Planet.POI.PoiCatalog.SpawnCamp);
            var pivot = new Vector3(camp.def.CenterX, camp.groundY + 6f, 0f);
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 10f);
            cam.transform.position = new Vector3(pivot.x, pivot.y, cam.transform.position.z);
            side.dayNight.Override = 0.5f;
            float until = Time.realtimeSinceStartup + 25f;
            while (Time.realtimeSinceStartup < until && side.stage.DrawnSlots() < 7) yield return null;
            for (int i = 0; i < 30; i++) yield return null;
            var sb = new System.Text.StringBuilder();
            foreach (var l in side.stage.Layers) sb.Append($"{l.slot}:{(l.ready ? "art" : l.placeholder ? "placeholder" : "missing")}@{l.z:F0} ");
            Debug.Log($"[MERIDIAN] U-090 stage {side.stage.Region}: {side.stage.DrawnSlots()} slots: {sb}");
            yield return Save(cam, $"{name}_1_earth_camp_stage");
            var railPos = cam.transform.position;
            Meridian.CameraRig.PhotoOrbit.Depth(cam, pivot);
            for (int i = 0; i < 3; i++) yield return null;
            yield return Save(cam, $"{name}_2_earth_camp_stage_depth");
            cam.transform.SetPositionAndRotation(railPos, Quaternion.identity);
            // Wide: the forest/plains border, 28 m frame.
            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Plains, out int border, out _);
            Meridian.CameraRig.SideView.SetHalfHeight(cam, 14f);
            cam.transform.position = new Vector3(border - 40f, side.terrain.OriginalTop(border - 40) + 8f, cam.transform.position.z);
            until = Time.realtimeSinceStartup + 20f;
            while (Time.realtimeSinceStartup < until && side.stage.DrawnSlots() < 7) yield return null;
            for (int i = 0; i < 30; i++) yield return null;
            yield return Save(cam, $"{name}_3_border_wide");
            side.dayNight.Override = null;
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

        /// <summary>U-046 evidence: each Rig module in the hand, in use: Beam ray, Grapple (slot 2, D-087), Survey ring, Builder ghost (clear and blocked).</summary>
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
                float rest = Time.realtimeSinceStartup + 1.2f; // the scan ring finishes
                while (Time.realtimeSinceStartup < rest) yield return null;
            }
            yield return Use(Meridian.Rig.RigModule.Beam, new Vector2(gx + 0.5f, top + 0.5f), true, 8, "1_beam");
            yield return Use(Meridian.Rig.RigModule.Grapple, feet + new Vector2(6f, 1.2f), true, 2, "2_grapple"); // D-087: slot 2 is the Grapple (no action yet)
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

        /// <summary>U-094 evidence: Earth on the v4 path with placeholders (ortho 16.875 m frame, parallax strips, v3 surveyor sheet), copied to reports/unity/c0_&lt;date&gt;/earth_c0_placeholder.png.</summary>
        [UnityTest]
        public IEnumerator CaptureC0Earth()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            Meridian.View2D.CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var side = director.PlanetSide;
                side.dayNight.Override = 0.45f;
                var view = side.cartoon != null ? side.cartoon.Surveyor : null;
                timeout = Time.realtimeSinceStartup + 10f;
                while (view != null && !view.Ready && Time.realtimeSinceStartup < timeout) yield return null;
                for (int i = 0; i < 60; i++) yield return null;
                Debug.Log($"[MERIDIAN] c0 capture: cartoon {(side.cartoon != null && side.cartoon.Active)}, ortho {side.sideCamera.orthographicSize:F3}, layers {(side.cartoon != null && side.cartoon.Layers != null ? side.cartoon.Layers.renderers.Count : 0)}, surveyor clip {(view != null ? view.Clip : "none")}");
                var dir = $"coordination/reports/unity/c0_{DateTime.Now:yyyy-MM-dd}";
                Directory.CreateDirectory(dir);
                // U-095: the before/after pair: film off (also the U-094 placeholder shot) and film on.
                bool film = Meridian.Core.GameSettings.FilmEffects;
                Meridian.Core.GameSettings.FilmEffects = false;
                for (int i = 0; i < 3; i++) yield return null;
                yield return Save(side.sideCamera, $"{name}_earth_c0_placeholder");
                File.Copy($"logs/capture_{name}_earth_c0_placeholder.png", $"{dir}/earth_c0_placeholder.png", true);
                File.Copy($"logs/capture_{name}_earth_c0_placeholder.png", $"{dir}/earth_c0_film_off.png", true);
                Meridian.Core.GameSettings.FilmEffects = true;
                for (int i = 0; i < 3; i++) yield return null;
                yield return Save(side.sideCamera, $"{name}_earth_c0_film_on");
                File.Copy($"logs/capture_{name}_earth_c0_film_on.png", $"{dir}/earth_c0_film_on.png", true);
                Meridian.Core.GameSettings.FilmEffects = film;
                // U-100: the cartoon ground after two digs beside the surveyor: the strip follows the dug column heights.
                if (side.rig != null && side.player != null)
                {
                    var p = side.player.transform.position;
                    side.rig.Dig(new Vector2(p.x - 2.5f, p.y - 0.5f));
                    side.rig.Dig(new Vector2(p.x - 2.5f, p.y - 1.5f));
                    for (int i = 0; i < 20; i++) yield return null;
                    Debug.Log($"[MERIDIAN] c0 ground: strip ready {(side.cartoon != null && side.cartoon.Ground != null && side.cartoon.Ground.Ready)}, columns {(side.cartoon != null && side.cartoon.Ground != null ? side.cartoon.Ground.Columns : 0)}");
                    yield return Save(side.sideCamera, $"{name}_earth_c0_ground");
                    File.Copy($"logs/capture_{name}_earth_c0_ground.png", $"{dir}/earth_c0_ground.png", true);
                }
                side.dayNight.Override = null;
            }
            finally { Meridian.View2D.CartoonStage.Enabled = false; }
        }

        /// <summary>U-096 evidence: a 6-frame strip of the iris-out on the surveyor (t = 0 … 0.35 s), 320×180 each, in reports/unity/c0_&lt;date&gt;/iris_strip.png.</summary>
        [UnityTest]
        public IEnumerator CaptureIrisStrip()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            Meridian.View2D.CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var side = director.PlanetSide;
                side.dayNight.Override = 0.45f;
                for (int i = 0; i < 60; i++) yield return null;
                var iris = Meridian.Transitions.IrisWipe.Instance;
                Assert.NotNull(iris, "IrisWipe on the transition canvas");
                var canvas = iris.GetComponentInParent<Canvas>();
                var mode = canvas.renderMode;
                // A camera render never includes a screen-space overlay canvas: draw it through the side camera for the shots.
                canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = side.sideCamera; canvas.planeDistance = 1f;
                var cam = side.sideCamera;
                var centre = Meridian.Transitions.IrisWipe.ScreenCentre(cam, side.player.Body.position + new Vector2(0f, 0.9f));
                const int frames = 6, w = 320, h = 180;
                var strip = new Texture2D(w * frames, h, TextureFormat.RGB24, false);
                var full = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
                var small = new RenderTexture(w, h, 0, RenderTextureFormat.ARGB32);
                try
                {
                    for (int i = 0; i < frames; i++)
                    {
                        float t = Meridian.Transitions.IrisMath.Seconds * i / (frames - 1);
                        iris.Preview(centre, t, true);
                        yield return null;
                        cam.targetTexture = full; cam.Render(); cam.targetTexture = null;
                        Graphics.Blit(full, small);
                        var prev = RenderTexture.active;
                        RenderTexture.active = small;
                        strip.ReadPixels(new Rect(0, 0, w, h), i * w, 0);
                        RenderTexture.active = prev;
                        Debug.Log($"[MERIDIAN] iris strip frame {i}: t {t:F3} s, radius {iris.Radius:F3} screen heights");
                    }
                    strip.Apply();
                    Directory.CreateDirectory("logs");
                    var output = $"logs/capture_{name}_iris_strip.png";
                    File.WriteAllBytes(output, strip.EncodeToPNG());
                    TestContext.Out.WriteLine($"[MERIDIAN] CAPTURE OK: {output}");
                    var dir = $"coordination/reports/unity/c0_{DateTime.Now:yyyy-MM-dd}";
                    Directory.CreateDirectory(dir);
                    File.Copy(output, $"{dir}/iris_strip.png", true);
                }
                finally
                {
                    iris.SetOpen();
                    canvas.renderMode = mode;
                    UnityEngine.Object.Destroy(strip); full.Release(); small.Release();
                }
                side.dayNight.Override = null;
            }
            finally { Meridian.View2D.CartoonStage.Enabled = false; }
        }

        /// <summary>
        /// U-101 (for U-098): 20 s of the C0 scene at 2 stills per second (320×180 into reports/unity/c0_&lt;date&gt;/strip/) and a
        /// 6 × 7 contact sheet: idle → walk → jump/land → walk back past a plant → look_camera. Runs on whatever art the keys hold.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureC0Strip()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            Meridian.View2D.CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var side = director.PlanetSide;
                side.dayNight.Override = 0.45f;
                var player = side.player;
                player.externalInput = true; player.intent = default;
                var view = side.cartoon != null ? side.cartoon.Surveyor : null;
                var flora = side.cartoon != null ? side.cartoon.Flora : null;
                timeout = Time.realtimeSinceStartup + 15f;
                while (((view != null && !view.Ready) || (flora != null && !flora.Ready)) && Time.realtimeSinceStartup < timeout) yield return null;
                for (int i = 0; i < 60; i++) yield return null;
                float startX = player.Body.position.x;
                // The nearest plant on the surveyor's left: the walk back passes it.
                float plantX = startX - 6f;
                if (flora != null) foreach (var p in flora.Plants) if (p.Root.position.x < startX - 2f && p.Root.position.x > plantX) plantX = p.Root.position.x;

                var dir = $"coordination/reports/unity/c0_{DateTime.Now:yyyy-MM-dd}/strip";
                Directory.CreateDirectory(dir);
                const int stills = 40, cols = 6, rows = 7, w = 320, h = 180;
                var sheet = new Texture2D(w * cols, h * rows, TextureFormat.RGB24, false);
                var full = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
                var small = new RenderTexture(w, h, 0, RenderTextureFormat.ARGB32);
                var still = new Texture2D(w, h, TextureFormat.RGB24, false);
                var cam = side.sideCamera;
                float t0 = Time.time;
                try
                {
                    for (int i = 0; i < stills; i++)
                    {
                        float t = i * 0.5f;
                        // The script: 0–3 s idle, 3–8 s walk right, 8 s jump, 10–16 s walk back past the plant, 16–20 s look_camera.
                        if (t < 3f) player.intent = default;
                        else if (t < 8f) player.intent = new Meridian.Player.PlayerIntent { move = 1f };
                        else if (t < 10f) { player.intent = default; if (Mathf.Approximately(t, 8f)) player.PressJump(); }
                        else if (t < 16f) player.intent = new Meridian.Player.PlayerIntent { move = player.Body.position.x > plantX - 1.5f ? -1f : 0f };
                        else { player.intent = default; if (view != null && Mathf.Approximately(t, 16f)) view.Override("look_camera", 4f); }
                        while (Time.time - t0 < t) yield return null;
                        cam.targetTexture = full; cam.Render(); cam.targetTexture = null;
                        Graphics.Blit(full, small);
                        var prev = RenderTexture.active;
                        RenderTexture.active = small;
                        still.ReadPixels(new Rect(0, 0, w, h), 0, 0); still.Apply();
                        int cx = i % cols, cy = rows - 1 - i / cols;
                        sheet.SetPixels(cx * w, cy * h, w, h, still.GetPixels());
                        RenderTexture.active = prev;
                        File.WriteAllBytes($"{dir}/still_{i:D2}.png", still.EncodeToPNG());
                    }
                    sheet.Apply();
                    File.WriteAllBytes($"{dir}/contact_sheet.png", sheet.EncodeToPNG());
                    Directory.CreateDirectory("logs");
                    File.WriteAllBytes($"logs/capture_{name}_contact_sheet.png", sheet.EncodeToPNG());
                    TestContext.Out.WriteLine($"[MERIDIAN] CAPTURE OK: logs/capture_{name}_contact_sheet.png ({stills} stills in {dir}; plant anchor x {plantX:F1}, start x {startX:F1}, end x {player.Body.position.x:F1}, clip {(view != null ? view.Clip : "n/a")})");
                }
                finally
                {
                    player.intent = default;
                    UnityEngine.Object.Destroy(sheet); UnityEngine.Object.Destroy(still); full.Release(); small.Release();
                }
                side.dayNight.Override = null;
            }
            finally { Meridian.View2D.CartoonStage.Enabled = false; }
        }

        /// <summary>
        /// U-098: the C0 style-test stills into reports/unity/c0_&lt;date&gt;/u098/: idle, walk, jump, land, plant react, critter
        /// idle (one gull framed on purpose, B-113), iris mid-wipe, film off / film on. Each shot logs what it shows.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureC0Set()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            Meridian.View2D.CartoonStage.Enabled = true;
            bool film = Meridian.Core.GameSettings.FilmEffects;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var side = director.PlanetSide;
                side.dayNight.Override = 0.45f;
                side.creatures.autoSpawn = false;
                var player = side.player;
                player.externalInput = true; player.intent = default;
                var view = side.cartoon.Surveyor;
                var flora = side.cartoon.Flora;
                timeout = Time.realtimeSinceStartup + 15f;
                while ((!view.Ready || flora == null || !flora.Ready) && Time.realtimeSinceStartup < timeout) yield return null;
                Assert.IsTrue(view.Ready && flora != null && flora.Ready, "surveyor sheet and flora loaded");
                for (int i = 0; i < 60; i++) yield return null;
                Meridian.Core.GameSettings.FilmEffects = true;
                var cam = side.sideCamera;
                var dir = $"coordination/reports/unity/c0_{DateTime.Now:yyyy-MM-dd}/u098";
                Directory.CreateDirectory(dir);

                IEnumerator Shot(string label, string what)
                {
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] u098 {label}: {what}");
                }

                // 1. idle
                for (int i = 0; i < 24; i++) yield return null;
                yield return Shot("1_idle", $"clip {view.Clip}");

                // 2. walk (right, mid-stride)
                player.intent = new Meridian.Player.PlayerIntent { move = 1f };
                for (int i = 0; i < 35; i++) yield return new WaitForFixedUpdate();
                yield return Shot("2_walk", $"clip {view.Clip}, vx {player.Body.linearVelocity.x:F1} m/s");
                player.intent = default;
                for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate();

                // 3. jump (rising) and 4. land (the frame after touchdown)
                player.PressJump();
                float until = Time.realtimeSinceStartup + 3f;
                while (player.Grounded && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
                for (int i = 0; i < 8; i++) yield return new WaitForFixedUpdate();
                yield return Shot("3_jump", $"clip {view.Clip}, vy {player.Body.linearVelocity.y:F1} m/s");
                until = Time.realtimeSinceStartup + 4f;
                while (!player.Grounded && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
                yield return null;
                yield return Shot("4_land", $"clip {view.Clip}, impact {player.LastImpactSpeed:F1} m/s, squash y {view.SquashRoot.localScale.y:F2}");
                for (int i = 0; i < 40; i++) yield return null;

                // 5. plant react: stand 1.5 m right of the nearest plant on the left
                Meridian.Flora.RigPlant plant = null;
                float px = player.Body.position.x;
                foreach (var p in flora.Plants)
                    if (p.Root.position.x < px - 2f && (plant == null || p.Root.position.x > plant.Root.position.x)) plant = p;
                Assert.NotNull(plant, "a plant to the left of the surveyor");
                var stand = new Vector2(plant.Root.position.x + 1.5f, side.terrain.TopSolidY(Mathf.FloorToInt(plant.Root.position.x + 1.5f)) + 1.05f);
                player.Body.position = stand; player.transform.position = stand; player.Body.linearVelocity = Vector2.zero;
                for (int i = 0; i < 12; i++) yield return null;
                yield return Shot("5_plant_react", $"reacting {plant.Reacting}, facing {plant.Facing}, mouth {(plant.Mouth != null ? plant.Mouth.sprite.name : "none")}");
                Assert.IsTrue(plant.Reacting, "the plant reacts within its radius");

                // 6. critter idle: one gull 8 m off (outside its 6 m flee range), framed on purpose
                foreach (var c in side.creatures.All) if (c.Alive) side.creatures.Despawn(c);
                var gullAt = player.Body.position + new Vector2(8f, 3f);
                var gull = side.creatures.Spawn(Meridian.Creatures.Species.Gull, gullAt);
                Assert.NotNull(gull, "a gull");
                for (int i = 0; i < 30; i++) yield return null;
                var vp = cam.WorldToViewportPoint(gull.Body.position);
                yield return Shot("6_critter_gull", $"gull at {gull.Body.position}, viewport ({vp.x:F2}, {vp.y:F2}), state {gull.State}, model/sheet {(gull.View != null && gull.View.sprite != null ? gull.View.sprite.name : "none")}");
                Assert.IsTrue(vp.x > 0.05f && vp.x < 0.95f && vp.y > 0.05f && vp.y < 0.95f, "the gull is in the frame");

                // 7. iris mid-wipe (0.175 s into the 0.35 s close, on the surveyor)
                var iris = Meridian.Transitions.IrisWipe.Instance;
                Assert.NotNull(iris);
                var canvas = iris.GetComponentInParent<Canvas>();
                var mode = canvas.renderMode;
                canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = cam; canvas.planeDistance = 1f;
                iris.Preview(Meridian.Transitions.IrisWipe.ScreenCentre(cam, player.Body.position + new Vector2(0f, 0.9f)), Meridian.Transitions.IrisMath.Seconds * 0.5f, true);
                yield return null;
                yield return Shot("7_iris_mid", $"radius {iris.Radius:F3} screen heights");
                iris.SetOpen();
                canvas.renderMode = mode;
                yield return null;

                // 8. film off / 9. film on (the same frame)
                Meridian.Core.GameSettings.FilmEffects = false;
                for (int i = 0; i < 3; i++) yield return null;
                yield return Shot("8_film_off", "film effects off");
                Meridian.Core.GameSettings.FilmEffects = true;
                for (int i = 0; i < 3; i++) yield return null;
                yield return Shot("9_film_on", "film effects on");
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.Core.GameSettings.FilmEffects = film;
                Meridian.View2D.CartoonStage.Enabled = false;
            }
        }

        /// <summary>
        /// U-108: the C0 v4.1 re-shoot into reports/unity/c0_&lt;date&gt;/v41/: CaptureC0Set's nine shots (U-098 numbering and labels)
        /// with BLENDER's v3.1 re-inks in the scene (D-100 thinner ink, D-101 the faceless snoozle, D-102 the upright Pilgrim):
        /// B-125 surveyor, B-126 snoozle rig set (replaces_part head/leaves, swap_cycle on the beat; Bible §9.4), B-127 gull
        /// (52 frames, fly 40–51). Every shot logs the U-098 facts plus the nearest snoozle's head sprite (its swap_cycle / react
        /// position; 'n/a' when the live set has no head bone) and, for the gull, its sheet frame and the clip that frame belongs
        /// to. The stage's load-time gull is despawned at boot (it kept the placeholder frames it was spawned with) and shot 6
        /// waits for the gull sheet. Afterwards the test writes v41/README.md: the date, a shot table and the sheets in play with
        /// their sidecar sizes. CaptureC0Set and CaptureU107Ship are untouched.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureV41Set()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            Meridian.View2D.CartoonStage.Enabled = true;
            bool film = Meridian.Core.GameSettings.FilmEffects;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var side = director.PlanetSide;
                side.dayNight.Override = 0.45f;
                side.creatures.autoSpawn = false;
                // The stage's load-time gull (CartoonStage.ConfigureFor) is spawned before its sheet arrives and Creature.Setup keeps
                // the frames it was given, so it drew as a white quad in the U-107 captures: clear the stage; shot 6 spawns its own.
                foreach (var c in side.creatures.All)
                    if (c.Alive) { TestContext.Out.WriteLine($"[MERIDIAN] v41 despawning {c.Spec.id} at {c.Body.position} (view {SpriteName(c.View)})"); side.creatures.Despawn(c); }
                var player = side.player;
                player.externalInput = true; player.intent = default;
                var view = side.cartoon.Surveyor;
                var flora = side.cartoon.Flora;
                timeout = Time.realtimeSinceStartup + 15f;
                while ((!view.Ready || flora == null || !flora.Ready) && Time.realtimeSinceStartup < timeout) yield return null;
                string floraState = flora != null
                    ? $"json {flora.Set != null} (parse error: {flora.ParseError ?? "none"}), parts {flora.SpriteCount}, controller {flora.Controller != null}; nothing found at: {flora.Missing}"
                    : "no FloraRigs (cartoon stage off?)";
                Assert.IsTrue(view.Ready && flora != null && flora.Ready, $"surveyor sheet and flora loaded: surveyor {view.Ready}, flora {floraState}");
                Assert.AreEqual(Meridian.View2D.CartoonStage.FloraCount, flora.Plants.Count, "the C0 flora: 48 rigged instances (U-108 accept)");
                for (int i = 0; i < 60; i++) yield return null;
                Meridian.Core.GameSettings.FilmEffects = true;
                var cam = side.sideCamera;
                var dir = $"coordination/reports/unity/c0_{DateTime.Now:yyyy-MM-dd}/v41";
                Directory.CreateDirectory(dir);
                var rows = new System.Text.StringBuilder();
                int shots = 0;

                IEnumerator Shot(string label, string shows, string facts)
                {
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] v41 {label}: {shows}; {facts}");
                    rows.AppendLine($"| {++shots} | {label}.png | {shows} | {facts} |");
                }

                Meridian.Flora.RigPlant Nearest(float x)
                {
                    Meridian.Flora.RigPlant best = null;
                    foreach (var p in flora.Plants)
                        if (best == null || Mathf.Abs(p.Root.position.x - x) < Mathf.Abs(best.Root.position.x - x)) best = p;
                    return best;
                }

                // The head and leaves bones' own renderers carry the replaces_part swaps (B-126); the mouth is the daisy fallback (none for the snoozle, D-101).
                string PlantFacts(Meridian.Flora.RigPlant p) => p == null ? "no plant"
                    : $"{p.Def.name} head {BonePart(p, "head")}, leaves {BonePart(p, "leaves")}, mouth {SpriteName(p.Mouth)}, swaps [{string.Join(" ", p.Def.swaps.Keys)}], beat {60f / Mathf.Max(1f, p.Def.idle.beat_bpm):F3} s";

                // 1. idle
                for (int i = 0; i < 24; i++) yield return null;
                yield return Shot("1_idle", "the surveyor idle among the snoozles",
                    $"clip {view.Clip}, plants {flora.Plants.Count} (full rate {flora.FullRateCount}, cheap {flora.CheapCount}), set {flora.Set.style} {flora.Key}, nearest {PlantFacts(Nearest(player.Body.position.x))}");

                // 2. walk (right, mid-stride)
                player.intent = new Meridian.Player.PlayerIntent { move = 1f };
                for (int i = 0; i < 35; i++) yield return new WaitForFixedUpdate();
                yield return Shot("2_walk", "walking right, mid-stride", $"clip {view.Clip}, vx {player.Body.linearVelocity.x:F1} m/s, nearest {PlantFacts(Nearest(player.Body.position.x))}");
                player.intent = default;
                for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate();

                // 3. jump (rising) and 4. land (the frame after touchdown)
                player.PressJump();
                float until = Time.realtimeSinceStartup + 3f;
                while (player.Grounded && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
                for (int i = 0; i < 8; i++) yield return new WaitForFixedUpdate();
                yield return Shot("3_jump", "the jump, rising", $"clip {view.Clip}, vy {player.Body.linearVelocity.y:F1} m/s, nearest {PlantFacts(Nearest(player.Body.position.x))}");
                until = Time.realtimeSinceStartup + 4f;
                while (!player.Grounded && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
                yield return null;
                yield return Shot("4_land", "the frame after touchdown (squash)",
                    $"clip {view.Clip}, impact {player.LastImpactSpeed:F1} m/s, squash y {view.SquashRoot.localScale.y:F2}, nearest {PlantFacts(Nearest(player.Body.position.x))}");
                for (int i = 0; i < 40; i++) yield return null;

                // 5. plant react: stand 1.5 m right of the nearest plant on the left (inside its 3 m radius)
                Meridian.Flora.RigPlant plant = null;
                float px = player.Body.position.x;
                foreach (var p in flora.Plants)
                    if (p.Root.position.x < px - 2f && (plant == null || p.Root.position.x > plant.Root.position.x)) plant = p;
                Assert.NotNull(plant, "a plant to the left of the surveyor");
                var stand = new Vector2(plant.Root.position.x + 1.5f, side.terrain.TopSolidY(Mathf.FloorToInt(plant.Root.position.x + 1.5f)) + 1.05f);
                player.Body.position = stand; player.transform.position = stand; player.Body.linearVelocity = Vector2.zero;
                for (int i = 0; i < 12; i++) yield return null;
                yield return Shot("5_plant_react", "the nearest snoozle reacting to the surveyor (turned, react swap on the head, leaves up)",
                    $"reacting {plant.Reacting}, facing {plant.Facing}, {PlantFacts(plant)}, react action {plant.Def.react.action} swap {plant.Def.react.swap ?? "none"}");
                Assert.IsTrue(plant.Reacting, "the plant reacts within its radius");

                // 6. critter: one gull 8 m off (outside its 6 m flee range), framed on purpose, from the B-127 sheet
                foreach (var c in side.creatures.All) if (c.Alive) side.creatures.Despawn(c);
                until = Time.realtimeSinceStartup + 10f;
                while (!side.creatures.ArtReady(Meridian.Creatures.Species.Gull) && Time.realtimeSinceStartup < until) yield return null;
                Assert.IsTrue(side.creatures.ArtReady(Meridian.Creatures.Species.Gull), "the gull sheet (creatures/earth/gull, B-127) loaded: a placeholder quad is not the v4.1 evidence");
                var gullAt = player.Body.position + new Vector2(8f, 3f);
                var gull = side.creatures.Spawn(Meridian.Creatures.Species.Gull, gullAt);
                Assert.NotNull(gull, "a gull");
                // U-108: spawned in the air it lifts into `fly` after its airborne hysteresis; the still waits for that drawing.
                until = Time.realtimeSinceStartup + 3f;
                while (gull.CurrentClip != "fly" && Time.realtimeSinceStartup < until) yield return null;
                for (int i = 0; i < 3; i++) yield return null;
                var vp = cam.WorldToViewportPoint(gull.Body.position);
                float ground = side.terrain.TopSolidY(Mathf.FloorToInt(gull.Body.position.x)) + 1f;
                yield return Shot("6_critter_gull", "one gull framed on purpose, 8 m off (outside its 6 m flee range), airborne",
                    $"gull at {gull.Body.position}, viewport ({vp.x:F2}, {vp.y:F2}), {gull.Body.position.y - ground:F1} m over the ground, state {gull.State}, pick {gull.LastPick}, flies {gull.Spec.Flies}, sprite {SpriteName(gull.View)}, clip {ClipOf(gull)}");
                Assert.IsTrue(vp.x > 0.05f && vp.x < 0.95f && vp.y > 0.05f && vp.y < 0.95f, "the gull is in the frame");

                // 7. iris mid-wipe (0.175 s into the 0.35 s close, on the surveyor)
                var iris = Meridian.Transitions.IrisWipe.Instance;
                Assert.NotNull(iris);
                var canvas = iris.GetComponentInParent<Canvas>();
                var mode = canvas.renderMode;
                canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = cam; canvas.planeDistance = 1f;
                iris.Preview(Meridian.Transitions.IrisWipe.ScreenCentre(cam, player.Body.position + new Vector2(0f, 0.9f)), Meridian.Transitions.IrisMath.Seconds * 0.5f, true);
                yield return null;
                yield return Shot("7_iris_mid", "the iris 0.175 s into its 0.35 s close, centred on the surveyor", $"radius {iris.Radius:F3} screen heights");
                iris.SetOpen();
                canvas.renderMode = mode;
                yield return null;

                // 8. film off / 9. film on (the same frame)
                Meridian.Core.GameSettings.FilmEffects = false;
                for (int i = 0; i < 3; i++) yield return null;
                yield return Shot("8_film_off", "the same frame without the film pass", "film effects off");
                Meridian.Core.GameSettings.FilmEffects = true;
                for (int i = 0; i < 3; i++) yield return null;
                yield return Shot("9_film_on", "the same frame with the film pass (B-115 grain, vignette, dust, scratches)", "film effects on");

                // The README beside the stills: what each shows and the sheets (sidecar sizes) in play.
                var sb = new System.Text.StringBuilder();
                sb.AppendLine($"# C0 v4.1 re-shoot · U-108 · {DateTime.Now:yyyy-MM-dd HH:mm}");
                sb.AppendLine();
                sb.AppendLine("v4.1 (D-100/D-101/D-102: thinner ink, faceless snoozle, upright Pilgrim). `SceneCapture.CaptureV41Set` via " +
                              "`tools/unity_capture.ps1 -Name v41 -Test CaptureV41Set`; the film pass is on in every still but 8. Art in the scene: " +
                              "B-125 surveyor, B-126 snoozle rig set v3.1 (`replaces_part` head/leaves, `swap_cycle` on the beat), B-127 gull " +
                              "(52 frames, fly 40–51), B-114 plains layers, B-115 film overlays.");
                sb.AppendLine();
                sb.AppendLine($"Run: plants {flora.Plants.Count} (full rate {flora.FullRateCount}, cheap {flora.CheapCount}), rig set style {flora.Set.style}, daylight override 0.45, 1920×1080.");
                sb.AppendLine();
                sb.AppendLine("| Shot | File | What it shows | Logged facts |");
                sb.AppendLine("|---|---|---|---|");
                sb.Append(rows);
                sb.AppendLine();
                sb.AppendLine("Sheets in play: " + SidecarSize("characters/surveyor/side", false) + ", " + SidecarSize("creatures/earth/gull", false) + ", "
                              + SidecarSize("flora/earth/rigset", true) + ", " + SidecarSize("characters/calibration_v3/side", false) + ".");
                File.WriteAllText($"{dir}/README.md", sb.ToString());
                TestContext.Out.WriteLine($"[MERIDIAN] v41 README: {dir}/README.md ({shots} shots)");
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.Core.GameSettings.FilmEffects = film;
                Meridian.View2D.CartoonStage.Enabled = false;
            }
        }

        static string SpriteName(SpriteRenderer r) => r != null && r.sprite != null ? r.sprite.name : "none";

        /// <summary>U-108: the sprite the bone named `bone` draws (sliced part names equal sprite names, so a replaces_part swap shows here), or 'n/a' without such a bone.</summary>
        static string BonePart(Meridian.Flora.RigPlant plant, string bone)
        {
            if (plant == null || plant.Def == null || plant.Def.bones == null || plant.Parts == null) return "n/a";
            for (int i = 0; i < plant.Def.bones.Length && i < plant.Parts.Length; i++)
                if (plant.Def.bones[i].name == bone)
                    return plant.Parts[i] != null && plant.Parts[i].sprite != null ? plant.Parts[i].sprite.name : "n/a";
            return "n/a";
        }

        /// <summary>U-108: the clip a creature's current sheet frame (`&lt;sheet&gt;_N`) belongs to, by the sheet's registered clips (ArtMaterials); 'n/a' off a sheet.</summary>
        static string ClipOf(Meridian.Creatures.Creature c)
        {
            if (c == null || c.Spec == null || c.View == null || c.View.sprite == null) return "n/a";
            var set = Meridian.Rendering.ArtMaterials.ClipsFor(c.Spec.artKey);
            string sprite = c.View.sprite.name;
            int u = sprite.LastIndexOf('_');
            if (set == null || u < 0 || !int.TryParse(sprite.Substring(u + 1), out int frame)) return "n/a";
            foreach (var clip in set.clips)
                if (frame >= clip.start && frame < clip.start + clip.length) return $"{clip.name} ({clip.start}-{clip.start + clip.length - 1})";
            return $"frame {frame} in no clip";
        }

        [System.Serializable] sealed class SheetMeta { public int frame_width, frame_height, frames; }
        [System.Serializable] sealed class RigMeta { public RigPartMeta[] parts; public RigPlantMeta[] plants; }
        [System.Serializable] sealed class RigPartMeta { public string name; }
        [System.Serializable] sealed class RigPlantMeta { public string name; }

        /// <summary>U-108: "key W×H×frames" from a sheet's sidecar json, or the rig set's part and plant counts; read from disk (Assets/_Game/Art/&lt;key&gt;.json).</summary>
        static string SidecarSize(string key, bool rigSet)
        {
            var path = $"Assets/_Game/Art/{key}.json";
            if (!File.Exists(path)) return $"{key} (no sidecar)";
            try
            {
                var json = File.ReadAllText(path);
                if (rigSet)
                {
                    var r = JsonUtility.FromJson<RigMeta>(json);
                    return $"{key} {(r != null && r.parts != null ? r.parts.Length : 0)} parts, {(r != null && r.plants != null ? r.plants.Length : 0)} plant(s)";
                }
                var s = JsonUtility.FromJson<SheetMeta>(json);
                return s != null ? $"{key} {s.frame_width}×{s.frame_height}×{s.frames}" : $"{key} (unreadable)";
            }
            catch (Exception e) { return $"{key} (unreadable: {e.Message})"; }
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
        /// <summary>
        /// U-107: the upright Pilgrim in side view, into reports/unity/u107/: on the pad (aboard, at rest), tilted mid-climb
        /// (D held at full thrust: 35°, drifting right), and just under the Escape Line still climbing. Each shot logs tilt,
        /// vertical speed, T/W and the camera's lead on the hull.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU107Ship()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            Meridian.View2D.CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var side = director.PlanetSide;
                side.dayNight.Override = 0.45f;
                side.creatures.autoSpawn = false;
                var ship = side.ship;
                var legs = ship.GetComponent<Meridian.Ship.ShipLegsView>();
                timeout = Time.realtimeSinceStartup + 15f;
                while ((legs == null || legs.Model == null || !legs.Model.Ready) && Time.realtimeSinceStartup < timeout) yield return null;
                // Clean shots: whatever the stage spawned at load is logged, then despawned.
                foreach (var c in side.creatures.All)
                    if (c.Alive) { TestContext.Out.WriteLine($"[MERIDIAN] u107 despawning {c.Spec.id} at {c.Body.position} (view {(c.View != null && c.View.sprite != null ? c.View.sprite.name : "none")})"); side.creatures.Despawn(c); }
                ship.GetComponent<Meridian.Ship.ShipBoarding>().ForceAboard();
                ship.externalInput = true;
                ship.intent = default;
                for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
                var cam = side.sideCamera;
                var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                TestContext.Out.WriteLine($"[MERIDIAN] u107 camera: follow {(follow != null ? follow.enabled.ToString() : "none")}, target {(follow != null && follow.target != null ? follow.target.name : "none")}, vehicle {(follow != null && follow.Vehicle != null)}, cartoon {(follow != null && follow.Cartoon)}");
                var dir = "coordination/reports/unity/u107";
                Directory.CreateDirectory(dir);

                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    var lead = (Vector2)cam.transform.position - ship.Body.position;
                    TestContext.Out.WriteLine($"[MERIDIAN] u107 {label}: tilt {ship.Tilt:F1}°, v ({ship.Body.linearVelocity.x:F1}, {ship.Body.linearVelocity.y:F1}) m/s, T/W {ship.ThrustToWeight:F2}, alt {ship.AltitudeAboveGround:F1} m, camera − hull ({lead.x:F1}, {lead.y:F1}), stage ({(follow != null ? follow.Stage.X : 0f):F1}, {(follow != null ? follow.Stage.Y : 0f):F1}) vs cam ({cam.transform.position.x:F1}, {cam.transform.position.y:F1}), follow {(follow != null && follow.enabled)}/{(follow != null && follow.isActiveAndEnabled)}/{(follow != null && follow.gameObject.activeInHierarchy)}, entries {(follow != null ? follow.Entries : -1)}, steps {(follow != null ? follow.StepsApplied : -1)}, dt {Time.deltaTime:F4}, scale {Time.timeScale}, camGO {cam.gameObject.activeInHierarchy}/{cam.enabled}, vehicle {(follow != null && follow.Vehicle != null)}, stand-in {(legs != null && legs.StandIn)}");
                }

                // 1. On the pad, aboard, at rest.
                Assert.IsTrue(ship.AtRest, "at rest on the pad");
                yield return Shot("1_pad");

                // 2. Tilted mid-climb: full thrust, D held (nose right), 3 s.
                ship.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f, lateral = 1f };
                for (float t = 0f; t < 3f; t += Time.fixedDeltaTime) yield return new WaitForFixedUpdate();
                Assert.AreEqual(-Meridian.Ship.RocketFlight.MaxTilt, ship.Tilt, 0.5f, "leaning 35° right");
                yield return Shot("2_tilted_climb");

                // 3. Upright again, climbing to just under the Escape Line (the next metres launch).
                ship.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f };
                float line = side.Config.EscapeLineY;
                timeout = Time.realtimeSinceStartup + 120f;
                while (ship.Body.position.y < line - 2f && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                ship.intent = default;
                Assert.Less(ship.Body.position.y, line, "still under the Escape Line");
                yield return Shot("3_escape_line");
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = false;
            }
        }
    }
}
