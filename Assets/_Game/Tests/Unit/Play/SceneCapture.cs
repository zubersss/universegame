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
            // U-103 (B-122): the drawn top-down Pilgrim (pilgrim_top, fin_wobble) parked outside Earth's well.
            if (parkedShip != null)
            {
                var topView = parkedShip.GetComponent<Meridian.Space.ShipTopView>();
                until = Time.realtimeSinceStartup + 10f;
                while (topView != null && topView.UsesRig && !topView.RigReady && Time.realtimeSinceStartup < until) yield return null;
                Debug.Log($"[MERIDIAN] space pilgrim: {(topView != null && topView.RigReady ? $"rig fit {topView.FitScale:F3}, playing {topView.Rig.Playing}" : "legacy sprite")}");
                // D-128: a disc in the ship view is magnified far past its far frame; the nearest body should be on its near frame.
                Meridian.Space.DiscSprite nearest = null; float best = float.MaxValue;
                foreach (var d in world.Discs)
                {
                    if (d == null) continue;
                    float dist = ((Vector2)d.transform.position - (Vector2)cam.transform.position).magnitude;
                    if (dist < best) { best = dist; nearest = d; }
                }
                parkedShip.intent = new Meridian.Space.ShipIntent { thrust = 1f };
                for (int i = 0; i < 6; i++) yield return null;
                if (nearest != null)
                {
                    // The ship view's zoom (the 6_pilgrim shot's): the nearest disc asks for its near frame; wait for it, then shoot on it.
                    Meridian.CameraRig.SideView.SetHalfHeight(cam, 6f);
                    cam.transform.position = new Vector3(parkedShip.Position.x, parkedShip.Position.y, cam.transform.position.z);
                    yield return null; yield return null;
                    until = Time.realtimeSinceStartup + 10f;
                    while (Meridian.Space.DiscSprite.WantsNear(nearest.LastMagnification, nearest.UsingNear) && !nearest.UsingNear && Time.realtimeSinceStartup < until) { Meridian.CameraRig.SideView.SetHalfHeight(cam, 6f); yield return null; }
                    Debug.Log($"[MERIDIAN] space disc near: {nearest.Key} at {nearest.LastMagnification:F1} px/texel, near frame {(nearest.NearSprite != null ? nearest.NearSprite.name : "none")}, using near {nearest.UsingNear}");
                }
                yield return Shot("6_pilgrim", parkedShip.Position, 6f);
                parkedShip.intent = default;
            }
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
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
            finally { Meridian.View2D.CartoonStage.Enabled = wasCartoon; }
        }

        /// <summary>U-096 evidence: a 6-frame strip of the iris-out on the surveyor (t = 0 … 0.35 s), 320×180 each, in reports/unity/c0_&lt;date&gt;/iris_strip.png.</summary>
        [UnityTest]
        public IEnumerator CaptureIrisStrip()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
            finally { Meridian.View2D.CartoonStage.Enabled = wasCartoon; }
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
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
            finally { Meridian.View2D.CartoonStage.Enabled = wasCartoon; }
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
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
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
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
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
            // Batch mode: the camera's aspect is the Editor's default screen (4:3) until the 1920x1080 target is set, so the strips and the layer tiling had laid
            // out for a narrower frame (the leftmost 1.5 m of every 1x frame showed bare block faces). Frame at 16:9 and let one LateUpdate lay out at it first.
            cam.aspect = 1920f / 1080f;
            yield return null;
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
                all &= legs != null && legs.Ready;
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
        public IEnumerator CaptureU107Ship() => CaptureShip("u107");

        /// <summary>
        /// U-103 (D-111, B-122): the same three ship frames with the drawn Pilgrim rig (fin_wobble in the climb, the puff loop at the
        /// tail_exhaust socket, the attitude puffs while tilting) → coordination/reports/unity/u103/.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU103Ship() => CaptureShip("u103");

        /// <summary>
        /// U-109: the climb sky. Three frames of the straight climb: on the pad, half-way to the Escape Line and just under it
        /// → coordination/reports/unity/u109/; the log carries the measured top-row colour, the edge, the span, the frame-top and
        /// frame-bottom shades and the starfield's alpha per frame.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU109Climb()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                var sky = side.cartoon != null ? side.cartoon.Sky : null;
                Assert.NotNull(sky, "ClimbSky on the cartoon stage");
                timeout = Time.realtimeSinceStartup + 15f;
                while ((legs == null || !legs.Ready || (sky.layers != null && sky.layers.placeholders.Count > 0 && sky.layers.placeholders[0])) && Time.realtimeSinceStartup < timeout) yield return null;
                foreach (var c in side.creatures.All) if (c.Alive) side.creatures.Despawn(c);
                ship.GetComponent<Meridian.Ship.ShipBoarding>().ForceAboard();
                ship.externalInput = true;
                ship.intent = default;
                for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
                var cam = side.sideCamera;
                var dir = "coordination/reports/unity/u109";
                Directory.CreateDirectory(dir);
                float line = side.Config.EscapeLineY;
                float half = side.Config.datumY + side.Config.escapeAltitude * 0.5f;

                string Hex(Color c) => $"#{(int)(c.r * 255f):X2}{(int)(c.g * 255f):X2}{(int)(c.b * 255f):X2}";
                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] u109 {label}: ship alt {ship.AltitudeAboveGround:F1} m, camera y {cam.transform.position.y:F1}, edge {sky.EdgeY:F1} (rest {sky.EdgeRestY:F1}), span {sky.Span:F1} m, top {(sky.TopMeasured ? "measured" : "sky colour")} {Hex(sky.TopColour)}, frame bottom {Hex(sky.FrameBottom)} top {Hex(sky.FrameTop)}, stars {(sky.StarsReady ? "loaded" : "not loaded")} alpha {sky.StarAlpha:F2} shown {(sky.Stars != null && sky.Stars.enabled)}");
                }

                // 1. On the pad: the painted sky fills the frame; the gradient starts above its top row.
                yield return Shot("1_ground");
                Assert.AreEqual(0f, sky.StarAlpha, 1e-4f, "no stars on the ground");

                // 2. Low in the climb (~28 m, LEAD cycle 254): layer0's top edge is still in the frame, the strip continues it.
                ship.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f };
                timeout = Time.realtimeSinceStartup + 120f;
                float low = ship.Body.position.y + 28f;
                while (ship.Body.position.y < low && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                yield return Shot("2_climb_28m");
                Assert.IsTrue(sky.Textured, "the overlay fades layer0's own painting into the sky at the join (no flat band)");
                // 3. Half-way: straight up under full thrust.
                while (ship.Body.position.y < half && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                yield return Shot("3_halfway");
                Assert.Less(Meridian.View2D.ClimbSkyMath.Luma(sky.FrameTop), Meridian.View2D.ClimbSkyMath.Luma(sky.FrameBottom), "darker at the top of the frame half-way up");

                // 4. Just under the Escape Line (the next metres launch).
                while (ship.Body.position.y < line - 2f && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                ship.intent = default;
                Assert.Less(ship.Body.position.y, line, "still under the Escape Line");
                float until = Time.realtimeSinceStartup + 10f;
                while (!sky.StarsReady && Time.realtimeSinceStartup < until) yield return null;
                yield return Shot("4_escape_line");
                Assert.IsTrue(sky.StarsReady && sky.Stars.enabled, "stars visible at the Escape Line");
                Assert.Greater(sky.StarAlpha, 0.4f, "the starfield near its full alpha at the line");
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-148 (D-158 (2)): the ship frame → coordination/reports/unity/u148/: 1_earth_pad_30m (boarded 1.5 s: the 30 m frame, the hull low
        /// in it, sky ahead), 2_earth_climb_45m (mid-climb with the climb held at 60 m/s for a moment, so the frame reaches its 45 m speed width
        /// as a faster mark would; Earth's Mk1 tops out near 42 m/s), 3_mars_climb (Mars mid-climb). Each shot asserts every painted strip spans
        /// the frame's width (no set edge) and logs the frame, the tile counts and the sky's span.
        /// </summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator CaptureU148Climb()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                var dir = "coordination/reports/unity/u148";
                Directory.CreateDirectory(dir);

                IEnumerator Board(PlanetSideRoot side)
                {
                    if (side.hazards != null) side.hazards.enabled = false;
                    if (side.dayNight != null) side.dayNight.Override = 0.45f;
                    side.creatures.autoSpawn = false;
                    side.creatures.DespawnAll();
                    var stage = side.cartoon;
                    float until = Time.realtimeSinceStartup + 15f;
                    while (stage != null && stage.Layers != null && stage.Layers.placeholders.Contains(true) && Time.realtimeSinceStartup < until) yield return null;
                    side.ship.GetComponent<Meridian.Ship.ShipBoarding>().ForceAboard();
                    side.ship.externalInput = true;
                    side.ship.intent = default;
                    for (int i = 0; i < 75; i++) yield return new WaitForFixedUpdate(); // 1.5 s: the boarding ease to the ship frame
                }
                IEnumerator Shot(PlanetSideRoot side, string label)
                {
                    yield return null;
                    var cam = side.sideCamera;
                    var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                    var layers = side.cartoon != null ? side.cartoon.Layers : null;
                    float halfW = cam.orthographicSize * cam.aspect, cx = cam.transform.position.x;
                    var tiles = new System.Text.StringBuilder();
                    if (layers != null)
                        for (int i = 0; i < layers.renderers.Count; i++)
                        {
                            var sr = layers.renderers[i];
                            if (sr == null || !sr.enabled) continue;
                            tiles.Append($" L{i} {layers.TileCount(i)}×{layers.TileWidth(i):F0} m");
                            Assert.LessOrEqual(sr.bounds.min.x, cx - halfW + 0.01f, $"{label}: layer {i}'s strip reaches the frame's left edge");
                            Assert.GreaterOrEqual(sr.bounds.max.x, cx + halfW - 0.01f, $"{label}: layer {i}'s strip reaches the frame's right edge");
                        }
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    var sky = side.cartoon != null ? side.cartoon.Sky : null;
                    TestContext.Out.WriteLine($"[MERIDIAN] u148 {label}: frame {cam.orthographicSize * 2f:F1} m (stage {follow.Stage.Frame:F1}, base {follow.ShipBase:F0}), speed {side.ship.Body.linearVelocity.magnitude:F1} m/s, alt {side.ship.AltitudeAboveGround:F1} m, hull centre {(follow.Stage.Y - (side.ship.transform.position.y + Meridian.Ship.SideShip.Height * 0.5f - Meridian.Ship.SideShip.SkidDrop)):F1} m under the camera; tiles{tiles}; sky span {(sky != null ? sky.Span : 0f):F0} m");
                }

                // 1. Earth on the pad: the 30 m ship frame.
                var earth = director.PlanetSide;
                yield return Board(earth);
                yield return Shot(earth, "1_earth_pad_30m");
                Assert.AreEqual(Meridian.CameraRig.StageCamera.ShipFrame, earth.sideCamera.orthographicSize * 2f, 0.5f, "the 30 m ship frame on the pad");

                // 2. Earth mid-climb at the 45 m frame: full thrust to 35 % of the climb, then the climb held at 60 m/s until the frame is 45 m wide
                // (or 75 % of the climb).
                var ship = earth.ship;
                float datum = earth.Config.datumY, esc = earth.Config.escapeAltitude;
                ship.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f };
                timeout = Time.realtimeSinceStartup + 120f;
                while (ship.Body.position.y < datum + esc * 0.35f && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                var follow1 = earth.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
                while (follow1.Stage.Frame < Meridian.CameraRig.StageCamera.ShipFrameFast - 0.5f && ship.Body.position.y < datum + esc * 0.75f && Time.realtimeSinceStartup < timeout)
                {
                    ship.Body.linearVelocity = new Vector2(0f, Meridian.CameraRig.StageCamera.ShipFastSpeed);
                    yield return new WaitForFixedUpdate();
                }
                yield return Shot(earth, "2_earth_climb_45m");
                Assert.GreaterOrEqual(earth.sideCamera.orthographicSize * 2f, Meridian.CameraRig.StageCamera.ShipFrameFast - 1f, "the frame near its 45 m speed width");
                ship.intent = default;
                ship.Body.linearVelocity = Vector2.zero;
                ship.Body.simulated = false;

                // 3. Mars mid-climb (its own Mk1 climb, nothing held).
                yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mars));
                var mars = director.PlanetSide;
                timeout = Time.realtimeSinceStartup + 20f;
                while (!mars.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
                yield return Board(mars);
                var mship = mars.ship;
                mship.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f };
                timeout = Time.realtimeSinceStartup + 120f;
                while (mship.Body.position.y < mars.Config.datumY + mars.Config.escapeAltitude * 0.45f && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                yield return Shot(mars, "3_mars_climb");
                mship.intent = default;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-150 (D-158 (4)): accelerating vs cruising and the sound barrier on Earth → coordination/reports/unity/u150/: 1_earth_boost
        /// (full thrust off the pad: the long flame, the speed lines), 2_earth_boom (0.15 s after the barrier breaks: the vapor cone round
        /// the hull, the shock ring opening), 3_earth_cruise (near the Escape Line with the throttle holding the speed: the cruise puff, no
        /// lines). Placeholders where B-171's sheets are not in yet.
        /// </summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator CaptureU150Boom()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                if (side.hazards != null) side.hazards.enabled = false;
                side.dayNight.Override = 0.45f;
                side.creatures.autoSpawn = false;
                side.creatures.DespawnAll();
                var ship = side.ship;
                var fx = ship.GetComponent<Meridian.FX.ShipFx>();
                Assert.NotNull(fx, "ShipFx on the Pilgrim");
                ship.GetComponent<Meridian.Ship.ShipBoarding>().ForceAboard();
                ship.externalInput = true;
                ship.intent = default;
                for (int i = 0; i < 75; i++) yield return new WaitForFixedUpdate();
                var cam = side.sideCamera;
                var dir = "coordination/reports/unity/u150";
                Directory.CreateDirectory(dir);
                int booms = 0;
                ship.SoundBarrierBroken += () => booms++;
                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] u150 {label}: speed {ship.Body.linearVelocity.magnitude:F1} m/s, along-track {ship.AlongTrackAccel:F2} m/s², boost {ship.Boost:F2} ({(ship.Boosting ? "boosting" : "cruise")}), throttle {ship.Flight.Throttle:F2}, ρ {ship.AirDensity:F2}, rumble {ship.Rumble:F3} m, lines α {fx.SpeedLineAlpha:F2}, flame {fx.FlameKey} ×{fx.Main.stretchY:F2}, vapor {fx.VaporShown}, ring {fx.RingShown}, booms {booms}, frame {cam.orthographicSize * 2f:F1} m");
                }

                // 1. Full thrust off the pad until the hull is boosting at speed: the long flame and the speed lines.
                ship.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f };
                timeout = Time.realtimeSinceStartup + 60f;
                while ((ship.Body.linearVelocity.magnitude < 15f || ship.Boost < 0.95f) && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                yield return Shot("1_earth_boost");
                Assert.IsTrue(ship.Boosting, "boosting off the pad");
                Assert.Greater(fx.SpeedLineAlpha, 0.05f, "the speed lines show while accelerating");

                // 2. The sound barrier (Earth 30 m/s): 0.15 s after it breaks, the vapor cone and the shock ring.
                while (booms == 0 && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                Assert.AreEqual(1, booms, "the barrier broke once on the climb");
                float until = Time.time + 0.15f;
                while (Time.time < until) yield return null;
                yield return Shot("2_earth_boom");
                Assert.IsTrue(fx.VaporShown && fx.RingShown, "the vapor cone and the shock ring show");

                // 3. Near the Escape Line, the throttle set each step to hold the speed (thrust = g + drag): calm.
                float line = side.Config.EscapeLineY, hold = side.Config.datumY + side.Config.escapeAltitude * 0.72f;
                while (ship.Body.position.y < hold && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                for (int i = 0; i < 90; i++)
                {
                    var v = ship.Body.linearVelocity;
                    float drag = Meridian.Ship.RocketFlight.DragK * ship.AirDensity * v.sqrMagnitude;
                    ship.intent = new Meridian.Ship.ShipSideIntent { thrust = Mathf.Clamp01((ship.Gravity + drag) / ship.Thrust) };
                    yield return new WaitForFixedUpdate();
                }
                Assert.Less(ship.Body.position.y, line, "still under the Escape Line");
                yield return Shot("3_earth_cruise");
                Assert.IsFalse(ship.Boosting, "cruising: not boosting");
                Assert.Less(fx.SpeedLineAlpha, 0.02f, "the speed lines eased off");
                ship.intent = default;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-104: the cartoon HUD at 1080p → coordination/reports/unity/u104/: on foot beside the ship (the three dials, the
        /// suit rows, the markers, every string in Patrick Hand) and aboard just under the Escape Line (the ship rows, the
        /// painted dotted line with its lettered sign). The overlay canvases draw through the side camera for the shots.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU104Hud()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            var canvases = new System.Collections.Generic.List<Canvas>();
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
                var hud = side.sideHud;
                var band = side.escapeBand;
                timeout = Time.realtimeSinceStartup + 20f;
                while ((legs == null || !legs.Ready || !hud.GaugesReady || !band.UsesArt || band.Sign == null || band.Sign.sprite == null) && Time.realtimeSinceStartup < timeout) yield return null;
                TestContext.Out.WriteLine($"[MERIDIAN] u104 art: gauges {hud.GaugesReady}, line {band.UsesArt}, sign {(band.Sign != null && band.Sign.sprite != null)}, ship {(legs != null && legs.Ready)}");
                foreach (var c in side.creatures.All) if (c.Alive) side.creatures.Despawn(c);
                var cam = side.sideCamera;
                var dir = "coordination/reports/unity/u104";
                Directory.CreateDirectory(dir);
                // A camera render never includes a screen-space overlay canvas: draw the HUD canvases through the side camera.
                foreach (var c in side.GetComponentsInChildren<Canvas>(true))
                    if (c.renderMode == RenderMode.ScreenSpaceOverlay) { canvases.Add(c); c.renderMode = RenderMode.ScreenSpaceCamera; c.worldCamera = cam; c.planeDistance = 1f; }

                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] u104 {label}: suit {hud.SuitGauge.Motion.Shown:F2}, o2 {hud.OxygenGauge.Motion.Shown:F2}, g {hud.GravityGauge.Motion.Shown:F2} (dials {hud.SuitGauge.Size:F0} px), sign y {band.SignY:F1} lettered '{band.SignLettering}', face {hud.HealthText.font.name}, ship rows {(side.shipHud != null && side.shipHud.VerticalSpeed.gameObject.activeInHierarchy ? $"V/S {side.shipHud.VerticalSpeed.text} T/W {side.shipHud.ThrustToWeight.text} AGL {side.shipHud.Altitude.text} TILT {side.shipHud.Tilt.text}" : "hidden (on foot)")}");
                }

                // 1. On foot beside the ship: the dials and the suit rows.
                float tickUntil = Time.time + 0.3f;
                while (Time.time < tickUntil) yield return null;
                yield return Shot("hud_1080p");

                // 2. Aboard, just under the Escape Line: the ship rows, the painted line and its sign.
                ship.GetComponent<Meridian.Ship.ShipBoarding>().ForceAboard();
                ship.externalInput = true;
                ship.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f };
                float line = side.Config.EscapeLineY;
                timeout = Time.realtimeSinceStartup + 120f;
                while (ship.Body.position.y < line - 75f && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                ship.intent = default; // coast: at T/W 1.22 the climb's 36 m/s bleeds off in ~67 m, so the apex sits a few metres under the line (a 0.3 s batch frame under thrust would climb 12 m past the shot)
                while (ship.Body.linearVelocity.y > 4f && ship.Body.position.y < line - 3f && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
                yield return Shot("hud_escape_line");
                Assert.Less(ship.Body.position.y, line, "still under the Escape Line");
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                foreach (var c in canvases) if (c != null) { c.renderMode = RenderMode.ScreenSpaceOverlay; c.worldCamera = null; }
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-106: the C1 flight strip. The whole loop under scripted input (pad → climb → Escape Line → Space → entry → descent →
        /// touchdown), sampled into at most 40 stills of 320 × 180 that favour the moments (2 Hz within 2.5 s of a phase change,
        /// one still every 2.5 s through the long climb and descent) and a 6 × 7 contact sheet, in
        /// reports/unity/c1_&lt;date&gt;/flight_strip/ with stills.md naming each still's phase, time, height and speed.
        /// </summary>
        [UnityTest, Timeout(360000)]
        public IEnumerator CaptureC1FlightStrip()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            const int Max = 40, Cols = 6, Rows = 7, W = 320, H = 180;
            var sheet = new Texture2D(W * Cols, H * Rows, TextureFormat.RGB24, false);
            var full = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            var small = new RenderTexture(W, H, 0, RenderTextureFormat.ARGB32);
            var still = new Texture2D(W, H, TextureFormat.RGB24, false);
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var state = Meridian.Core.GameState.Instance;
                var transitions = UnityEngine.Object.FindAnyObjectByType<Meridian.Transitions.TransitionDirector>();
                var side = director.PlanetSide;
                side.dayNight.Override = 0.45f;
                side.creatures.autoSpawn = false;
                var ship = side.ship;
                var legs = ship.GetComponent<Meridian.Ship.ShipLegsView>();
                timeout = Time.realtimeSinceStartup + 15f;
                while ((legs == null || !legs.Ready) && Time.realtimeSinceStartup < timeout) yield return null;
                foreach (var c in side.creatures.All) if (c.Alive) side.creatures.Despawn(c);
                var space = director.Space.GetComponentInChildren<Meridian.Space.SpaceShip>(true);
                space.externalInput = true; space.intent = default;
                ship.GetComponent<Meridian.Ship.ShipBoarding>().ForceAboard();
                ship.externalInput = true; ship.intent = default;
                for (int i = 0; i < 30; i++) yield return null;

                var dir = $"coordination/reports/unity/c1_{DateTime.Now:yyyy-MM-dd}/flight_strip";
                Directory.CreateDirectory(dir);
                var lines = new System.Collections.Generic.List<string> { "# C1 flight strip (U-106)", "", "| still | t (s) | phase |", "|---|---|---|" };
                int count = 0;
                float t0 = Time.time, lastStill = -10f, phaseAt = Time.time;
                string phase = "pad";
                float datum = side.Config.datumY, line = side.Config.EscapeLineY;

                Camera Cam() => state.view == Meridian.Core.ViewMode.Space
                    ? director.Space.GetComponentInChildren<Camera>()
                    : director.PlanetSide != null ? director.PlanetSide.sideCamera : null;
                void Still(string label)
                {
                    if (count >= Max) return;
                    var cam = Cam();
                    if (cam == null) return;
                    cam.targetTexture = full; cam.Render(); cam.targetTexture = null;
                    Graphics.Blit(full, small);
                    var prev = RenderTexture.active;
                    RenderTexture.active = small;
                    still.ReadPixels(new Rect(0, 0, W, H), 0, 0); still.Apply();
                    int cx = count % Cols, cy = Rows - 1 - count / Cols;
                    sheet.SetPixels(cx * W, cy * H, W, H, still.GetPixels());
                    RenderTexture.active = prev;
                    File.WriteAllBytes($"{dir}/still_{count:D2}.png", still.EncodeToPNG());
                    lines.Add($"| {count:D2} | {Time.time - t0:F1} | {label} |");
                    count++;
                    lastStill = Time.time;
                }
                void SetPhase(string p) { if (p != phase) { phase = p; phaseAt = Time.time; } }
                bool Due() => Time.time - lastStill >= (Time.time - phaseAt < 2.5f ? 0.5f : 2.5f) - 1e-3f;

                // 1. On the pad, aboard.
                Still("pad, aboard, drawn Pilgrim at rest");
                while (Time.time - lastStill < 0.5f) yield return null;
                Still("pad");

                // 2. The climb under held thrust, through the Escape Line and the launch iris into Space.
                ship.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f };
                SetPhase("climb");
                float guard = Time.time + 150f;
                while (!(state.view == Meridian.Core.ViewMode.Space && !transitions.Busy) && Time.time < guard)
                {
                    yield return null;
                    var s = director.PlanetSide != null ? director.PlanetSide.ship : null;
                    if (transitions.Busy) SetPhase("launch (iris)");
                    else if (state.view != Meridian.Core.ViewMode.Space && s != null && s.Body.position.y > line - 40f) SetPhase("escape line");
                    if (Due()) Still(s != null && state.view != Meridian.Core.ViewMode.Space ? $"{phase}: alt {s.Body.position.y - datum:F0} m, v {s.Body.linearVelocity.y:F0} m/s, tilt {s.Tilt:F0}°" : phase);
                }
                Assert.AreEqual(Meridian.Core.ViewMode.Space, state.view, "launched through the Escape Line");

                // 3. Space: thrust on for a second past the invulnerability, then the entry back to Earth.
                SetPhase("space");
                space.intent = new Meridian.Space.ShipIntent { thrust = 1f };
                for (int i = 0; i < 70; i++)
                {
                    yield return new WaitForFixedUpdate();
                    if (Due()) Still($"space: v {space.Velocity.magnitude:F0} u/s, well {space.InWellOf ?? "none"}");
                }
                var earth = space.world.Find("earth").Value;
                transitions.BeginEntry(earth);
                SetPhase("entry (iris)");
                Meridian.Ship.SideShip landing = null;
                guard = Time.time + 30f;
                while (transitions.Busy && Time.time < guard)
                {
                    yield return null;
                    var ps = director.PlanetSide;
                    if (landing == null && ps != null && ps.gameObject.activeInHierarchy && ps.ship != null) { landing = ps.ship; landing.externalInput = true; landing.intent = new Meridian.Ship.ShipSideIntent { thrust = 1f }; }
                    if (Due()) Still(phase);
                }
                Assert.NotNull(landing, "the side ship after the entry");
                space.intent = default;

                // 4. The descent on FlightPlayTests' key profile (thrust while falling faster than √(2·1.2·AGL), 2.5–15 m/s) to a clean touchdown.
                SetPhase("descent");
                guard = Time.time + 150f;
                while (!landing.Grounded && Time.time < guard)
                {
                    float alt = landing.AltitudeAboveGround;
                    float target = -Mathf.Clamp(Mathf.Sqrt(2f * 1.2f * Mathf.Max(0f, alt)), 2.5f, 15f);
                    landing.intent = new Meridian.Ship.ShipSideIntent { thrust = landing.Body.linearVelocity.y < target ? 1f : 0f };
                    yield return new WaitForFixedUpdate();
                    if (alt < 25f) SetPhase("touchdown");
                    if (Due()) Still($"{phase}: AGL {alt:F0} m, v {landing.Body.linearVelocity.y:F1} m/s, tilt {landing.Tilt:F0}°");
                }
                landing.intent = default;
                yield return null;
                Still($"down: {landing.LastTouchdownSpeed:F1} m/s, legs flexed");
                Assert.IsTrue(landing.Grounded, "touched down");
                Assert.LessOrEqual(landing.LastTouchdownSpeed, Meridian.Ship.SideShip.CleanTouchdown, "a clean touchdown on the profile");

                sheet.Apply();
                File.WriteAllBytes($"{dir}/contact_sheet.png", sheet.EncodeToPNG());
                Directory.CreateDirectory("logs");
                File.WriteAllBytes($"logs/capture_{name}_contact_sheet.png", sheet.EncodeToPNG());
                lines.Add(""); lines.Add($"{count} stills over {Time.time - t0:F1} s; launch {transitions.LastLaunchSeconds:F2} s, entry {transitions.LastEntrySeconds:F2} s, touchdown {landing.LastTouchdownSpeed:F2} m/s.");
                File.WriteAllLines($"{dir}/stills.md", lines);
                TestContext.Out.WriteLine($"[MERIDIAN] CAPTURE OK: logs/capture_{name}_contact_sheet.png ({count} stills in {dir}; {Time.time - t0:F1} s of flight; launch {transitions.LastLaunchSeconds:F2} s, entry {transitions.LastEntrySeconds:F2} s, touchdown {landing.LastTouchdownSpeed:F2} m/s)");
                if (director.PlanetSide != null && director.PlanetSide.dayNight != null) director.PlanetSide.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                UnityEngine.Object.Destroy(sheet); UnityEngine.Object.Destroy(still); full.Release(); small.Release();
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-114 evidence: stag, wolf and bear on their B-132 sheets at 1x beside the surveyor on the plains (creatures_1x), then the
        /// nearest pool with pike / shark / squid spawned by the natural rule (swimmers_1x; skipped with a log line when the plains
        /// have no water deep enough within 400 columns). Writes reports/unity/u114/.
        /// </summary>
        [UnityTest, Timeout(240000)]
        public IEnumerator CaptureU114Creatures()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                foreach (var c in side.creatures.All) if (c.Alive) side.creatures.Despawn(c);
                for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
                var cam = side.sideCamera;
                var dir = "coordination/reports/unity/u114";
                Directory.CreateDirectory(dir);
                var creatures = side.creatures;

                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                }
                Meridian.Creatures.Creature PutOnGround(Meridian.Creatures.Species sp, float x)
                {
                    int tx = Mathf.FloorToInt(x);
                    int s = side.terrain.TopSolidY(tx);
                    return creatures.Spawn(sp, new Vector2(tx + 0.5f, s + 1f + Meridian.Creatures.SpeciesSpec.Get(sp).size.y * 0.5f + 0.05f));
                }
                IEnumerator SheetsIn(Meridian.Creatures.Creature[] cs)
                {
                    float until = Time.realtimeSinceStartup + 15f;
                    while (Time.realtimeSinceStartup < until)
                    {
                        bool all = true;
                        foreach (var c in cs) if (c != null && c.Alive && (c.View == null || c.View.sprite == null || c.View.sprite.name.StartsWith("ph_", StringComparison.Ordinal))) all = false;
                        if (all) break;
                        yield return null;
                    }
                }
                string Line(Meridian.Creatures.Creature c) => c == null ? "none" : $"{c.Spec.artKey.Substring(c.Spec.artKey.LastIndexOf('/') + 1)} {(c.View != null && c.View.sprite != null ? c.View.sprite.name : "no sprite")} {c.View.bounds.size.x:F2} x {c.View.bounds.size.y:F2} m at ({c.Body.position.x:F1}, {c.Body.position.y:F1})";

                // 1. Land: stag, wolf, bear beside the surveyor.
                float px = side.player.transform.position.x;
                var stag = PutOnGround(Meridian.Creatures.Species.Stag, px - 7f);
                var wolf = PutOnGround(Meridian.Creatures.Species.GreyWolf, px - 3.5f);
                var bear = PutOnGround(Meridian.Creatures.Species.BrownBear, px + 4.5f);
                yield return SheetsIn(new[] { stag, wolf, bear });
                for (int i = 0; i < 6; i++) yield return new WaitForFixedUpdate();
                TestContext.Out.WriteLine($"[MERIDIAN] u114 land: {Line(stag)}; {Line(wolf)}; {Line(bear)}; bear temper {Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.BrownBear).temper}");
                yield return Shot("creatures_1x");

                // 2. Water: the nearest column with a pool deep enough for the pike; the surveyor steps to its shore so the camera follows.
                int found = int.MinValue, foundDepth = 0;
                for (int d = 0; d < 400 && found == int.MinValue; d++)
                    foreach (int tx in new[] { Mathf.FloorToInt(px) + d, Mathf.FloorToInt(px) - d })
                    {
                        var site = creatures.SiteAt(tx, side.player.transform.position.y);
                        if (site.aboveTile == Meridian.Terrain.TileId.Water && site.waterDepth >= 2) { found = tx; foundDepth = site.waterDepth; break; }
                    }
                if (found == int.MinValue)
                {
                    TestContext.Out.WriteLine("[MERIDIAN] u114 water: no pool at least 2 m deep within 400 columns of the camp; the swimmers' frame is skipped");
                }
                else
                {
                    // Walk the pool to its widest deep column (within 24 of the first), so the big swimmers have room.
                    int best = found, bestDepth = foundDepth;
                    for (int tx = found - 24; tx <= found + 24; tx++)
                    {
                        var site = creatures.SiteAt(tx, side.player.transform.position.y);
                        if (site.aboveTile == Meridian.Terrain.TileId.Water && site.waterDepth > bestDepth) { best = tx; bestDepth = site.waterDepth; }
                    }
                    // The surveyor to the shore first (the camera follows, the pool's collision chunks stream in), then the spawns by the natural rule.
                    int shore = best;
                    while (creatures.SiteAt(shore, side.player.transform.position.y).aboveTile == Meridian.Terrain.TileId.Water && shore > best - 60) shore--;
                    int shoreTop = side.terrain.TopSolidY(shore - 1);
                    side.player.Body.position = new Vector2(shore - 0.5f, shoreTop + 1.1f);
                    side.player.transform.position = side.player.Body.position;
                    side.player.Body.linearVelocity = Vector2.zero;
                    var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                    if (follow != null) follow.SnapToTarget();
                    float ready = Time.realtimeSinceStartup + 10f;
                    while (!(side.terrain.IsCollisionReady(best - 2, floorAt(best - 2)) && side.terrain.IsCollisionReady(best + 6, floorAt(best + 6))) && Time.realtimeSinceStartup < ready) yield return null;
                    int floorAt(int tx) => side.terrain.TopSolidY(tx);
                    var pike = creatures.SpawnAt(Meridian.Creatures.Species.Pike, best - 2, side.player.transform.position.y);
                    var shark = creatures.SpawnAt(Meridian.Creatures.Species.Shark, best + 2, side.player.transform.position.y);
                    var squid = creatures.SpawnAt(Meridian.Creatures.Species.Squid, best + 6, side.player.transform.position.y);
                    yield return SheetsIn(new[] { pike, shark, squid });
                    for (int i = 0; i < 12; i++) yield return new WaitForFixedUpdate();
                    int floor = side.terrain.TopSolidY(best);
                    // The camera over the pool itself (the follow keeps the surveyor centred and the pool under the frame's bottom edge).
                    if (follow != null) follow.enabled = false;
                    cam.transform.position = new Vector3(best + 1f, floor + 1f + bestDepth * 0.5f + 1.5f, cam.transform.position.z);
                    yield return null;
                    TestContext.Out.WriteLine($"[MERIDIAN] u114 water: pool at column {best}, floor y {floor}, depth {bestDepth} m; {Line(pike)}; {Line(shark)}; {Line(squid)}; clearances {(pike != null ? pike.Body.position.y - (floor + 1f) - pike.Spec.size.y * 0.5f : -1f):F2} / {(shark != null ? shark.Body.position.y - (floor + 1f) - shark.Spec.size.y * 0.5f : -1f):F2} / {(squid != null ? squid.Body.position.y - (floor + 1f) - squid.Spec.size.y * 0.5f : -1f):F2} m");
                    yield return Shot("swimmers_1x");
                    if (follow != null) { follow.enabled = true; follow.SnapToTarget(); }
                }
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        // ---------------- C2 batch B captures ----------------

        /// <summary>
        /// U-122 (D-135): the painted layers at 15 m and 40 m under the datum hold their datum pose (sky over hills over near; the
        /// swimmers' frame at −9 m had the hills over the sky) → coordination/reports/unity/u122/. The camera parks over the nearest pool.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU122Pool()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                foreach (var c in side.creatures.All) if (c.Alive) side.creatures.Despawn(c);
                var cam = side.sideCamera;
                var layers = side.cartoon.Layers;
                var dir = "coordination/reports/unity/u122";
                Directory.CreateDirectory(dir);
                timeout = Time.realtimeSinceStartup + 15f;
                while (layers.placeholders.Contains(true) && Time.realtimeSinceStartup < timeout) yield return null;
                for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
                string Tops()
                {
                    var sb = new System.Text.StringBuilder();
                    for (int i = 0; i < layers.renderers.Count; i++) sb.Append(i > 0 ? ", " : "").Append($"layer{i} top {layers.renderers[i].bounds.max.y:F1} (y {layers.renderers[i].transform.position.y:F1})");
                    return sb.ToString();
                }
                void AssertInOrder(string where)
                {
                    for (int i = 0; i + 1 < layers.renderers.Count; i++)
                        Assert.GreaterOrEqual(layers.renderers[i].bounds.max.y + 0.01f, layers.renderers[i + 1].bounds.max.y, $"layer{i} over layer{i + 1} {where}: {Tops()}");
                }
                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] u122 {label}: camera y {cam.transform.position.y:F1}, datum {layers.datumY:F1}, anchor {layers.anchorY:F1}; {Tops()}");
                }
                // 1. The camp at the datum: the reference pose.
                yield return Shot("1_datum");
                AssertInOrder("at the datum");
                // 2. The nearest pool (U-114's search): the surveyor on its shore so its chunks stream in, the camera parked 15 m under the datum over it.
                int px = Mathf.FloorToInt(side.player.transform.position.x), found = int.MinValue;
                for (int d = 0; d < 400 && found == int.MinValue; d++)
                    foreach (int tx in new[] { px + d, px - d })
                    {
                        var site = side.creatures.SiteAt(tx, side.player.transform.position.y);
                        if (site.aboveTile == Meridian.Terrain.TileId.Water && site.waterDepth >= 2) { found = tx; break; }
                    }
                float over = found == int.MinValue ? px + 0.5f : found + 0.5f;
                if (found != int.MinValue)
                {
                    int shore = found;
                    while (side.creatures.SiteAt(shore, side.player.transform.position.y).aboveTile == Meridian.Terrain.TileId.Water && shore > found - 60) shore--;
                    var stand = new Vector2(shore - 0.5f, side.terrain.TopSolidY(shore - 1) + 1.1f);
                    side.player.Body.position = stand; side.player.transform.position = stand; side.player.Body.linearVelocity = Vector2.zero;
                }
                else TestContext.Out.WriteLine("[MERIDIAN] u122: no pool within 400 columns of the camp; the frames park under the camp instead (a dig looks the same to the layers)");
                var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                if (follow != null) { follow.SnapToTarget(); follow.enabled = false; }
                float until = Time.realtimeSinceStartup + 10f;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                float datum = layers.datumY;
                cam.transform.position = new Vector3(over, datum - 15f, cam.transform.position.z);
                yield return null; yield return null;
                yield return Shot("2_pool_minus15");
                Assert.Less(cam.transform.position.y, datum - 10f, "the camera 10 m or more under the datum (the D-135 case)");
                AssertInOrder("15 m under the datum");
                // 3. A deep dig: 40 m under; the pose is the same.
                cam.transform.position = new Vector3(over, datum - 40f, cam.transform.position.z);
                yield return null; yield return null;
                yield return Shot("3_minus40");
                AssertInOrder("40 m under the datum");
                if (follow != null) follow.enabled = true;
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-110 (B-129 / B-133): the camp as its biome paints it (the spawn's band picks the scene set and the plant kinds), then the
        /// other two Earth sets on the same camp → coordination/reports/unity/u110/.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU110Scenes()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                foreach (var c in side.creatures.All) if (c.Alive) side.creatures.Despawn(c);
                var stage = side.cartoon;
                var layers = stage.Layers;
                var cam = side.sideCamera;
                var dir = "coordination/reports/unity/u110";
                Directory.CreateDirectory(dir);
                timeout = Time.realtimeSinceStartup + 15f;
                while ((layers.placeholders.Contains(true) || !stage.Flora.Ready) && Time.realtimeSinceStartup < timeout) yield return null;
                for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                }
                string Kinds()
                {
                    var tally = new System.Collections.Generic.SortedDictionary<string, int>();
                    foreach (Transform t in stage.Flora.transform) { tally.TryGetValue(t.name, out int n); tally[t.name] = n + 1; }
                    var sb = new System.Text.StringBuilder();
                    foreach (var kv in tally) sb.Append(sb.Length > 0 ? ", " : "").Append($"{kv.Key} ×{kv.Value}");
                    return sb.Length > 0 ? sb.ToString() : "none";
                }
                string biome = Meridian.Flora.FloraRigs.BiomeNameAt(Meridian.Planets.PlanetId.Earth, side.spawnX);
                TestContext.Out.WriteLine($"[MERIDIAN] u110 camp x {side.spawnX}: biome {biome}, scene {stage.Scene} ({layers.SceneKey}), plants {Kinds()}");
                Assert.AreEqual(Meridian.View2D.CartoonStage.SceneFor(Meridian.Terrain.EarthBiomes.At(side.spawnX)), stage.Scene, "the scene set follows the spawn's biome");
                // Every plant at the camp is a kind its biome lists (or the whole set when the biome lists fewer than two).
                var allowed = Meridian.Flora.FloraRigs.PlantsFor(stage.Flora.Set, biome);
                var names = new System.Collections.Generic.HashSet<string>();
                foreach (var p in allowed) names.Add(p.name);
                foreach (Transform t in stage.Flora.transform) Assert.IsTrue(names.Contains(t.name), $"{t.name} grows in the {biome}");
                yield return Shot($"1_camp_{stage.Scene}");
                float surface = side.terrain.TopSolidY(side.spawnX) + 1f;
                int shot = 2;
                foreach (var scene in new[] { "plains", "forest", "coast" })
                {
                    if (scene == stage.Scene) continue;
                    layers.ConfigureFor("earth", scene, surface);
                    timeout = Time.realtimeSinceStartup + 15f;
                    while (layers.placeholders.Contains(true) && Time.realtimeSinceStartup < timeout) yield return null;
                    for (int i = 0; i < 3; i++) yield return null;
                    TestContext.Out.WriteLine($"[MERIDIAN] u110 {scene}: {layers.SceneKey}, {layers.renderers.Count} layers, placeholders {layers.placeholders.Contains(true)}");
                    yield return Shot($"{shot++}_{scene}");
                }
                layers.ConfigureFor("earth", stage.Scene, surface); // the camp's own set back
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-116 (D-123, B-137): the painted Sun rig in Space — close (the corona in frame) and with Earth and Mars at one scale →
        /// coordination/reports/unity/u116/. The ship parks outside Earth's well as in CaptureSpaceArt.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU116Sun()
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
            while ((world.Sun == null || !world.Sun.Built) && Time.realtimeSinceStartup < until) yield return null;
            Assert.NotNull(world.Sun, "the Sun rig (planets/sun/disc_rig found)");
            Assert.IsTrue(world.Sun.Built, "the Sun rig built from its sheet and json");
            for (int i = 0; i < 30; i++) yield return null;
            var dir = "coordination/reports/unity/u116";
            Directory.CreateDirectory(dir);
            IEnumerator Shot(string label, Vector2 at, float size)
            {
                Meridian.CameraRig.SideView.SetHalfHeight(cam, size);
                cam.transform.position = new Vector3(at.x, at.y, cam.transform.position.z);
                for (int i = 0; i < 3; i++) yield return null;
                yield return Save(cam, $"{name}_{label}");
                File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
            }
            var sun = world.Find("sun");
            Assert.IsTrue(sun.HasValue, "the Sun body");
            var S = world.Sun;
            TestContext.Out.WriteLine($"[MERIDIAN] u116 sun: R {sun.Value.radius:F0} u, body scale {S.Body.transform.localScale.x:F2} ({S.Body.sprite.rect.width} px → {S.Body.sprite.rect.width / S.Body.sprite.pixelsPerUnit * S.Body.transform.localScale.x:F0} u), tongues {S.Tongues.Count} at r {(S.Tongues.Count > 0 ? S.Tongues[0].localPosition.magnitude : 0f):F0} u, prominences {S.Prominences.Count}, corona scale {(S.CoronaRenderer != null ? S.CoronaRenderer.transform.localScale.x : 0f):F1}, step {S.LastStep:F3}, spin {S.Json.ring.spin_deg_per_s}°/s, pulse {S.Json.ring.pulse}, {S.Json.ring.stepped_hz} Hz");
            Assert.AreEqual(14, S.Tongues.Count, "the 14-tongue ring");
            Assert.AreEqual(2, S.Prominences.Count, "two prominences");
            Assert.NotNull(S.CoronaRenderer, "the corona wash");
            Assert.AreEqual(sun.Value.radius * 0.97f, S.Tongues[0].localPosition.magnitude, 0.5f, "tongues at base_r R");
            // 1. Close: the corona (1.42 R) fills the frame's height.
            yield return Shot("1_sun", sun.Value.position, sun.Value.radius * 1.6f);
            // 2. The Sun, Earth and Mars at one scale: the camera midway to Mars.
            var earth = world.Find("earth"); var mars = world.Find("mars");
            Assert.IsTrue(earth.HasValue && mars.HasValue);
            var mid = (sun.Value.position + mars.Value.position) * 0.5f;
            yield return Shot("2_sun_earth_mars", mid, (mars.Value.position - sun.Value.position).magnitude * 0.62f);
            TestContext.Out.WriteLine($"[MERIDIAN] u116 ratio: Sun R {sun.Value.radius:F0}, Earth R {earth.Value.radius:F1}, Mars R {mars.Value.radius:F1} (true ratio, one camera)");
            // 3. A 12 Hz step holds between frames closer than 1/12 s.
            float step = S.LastStep;
            yield return null;
            Assert.IsTrue(S.LastStep == step || S.LastStep - step >= 1f / 12f - 1e-3f, "poses change in 1/12 s steps");
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>
        /// U-119 (B-136): the Hadal Maw in the coast deep with a shark and the surveyor at 1x → coordination/reports/unity/u119/: the shore,
        /// the Maw's head, and its react (jaw open, lure flaring) with the surveyor inside 12 m.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU119Maw()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                foreach (var c in side.creatures.All) if (c.Alive) side.creatures.Despawn(c);
                var cam = side.sideCamera;
                var creatures = side.creatures;
                var dir = "coordination/reports/unity/u119";
                Directory.CreateDirectory(dir);
                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                }
                var spec = Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.HadalMaw);
                Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Ocean, out int start, out int len);
                float y = side.player.Body.position.y;
                int shore = start;
                while (shore < start + len && creatures.SiteAt(shore, y).aboveTile != Meridian.Terrain.TileId.Water) shore++;
                int deep = shore;
                while (deep < shore + 400 && creatures.SiteAt(deep, y).waterDepth < spec.WaterDepthNeeded) deep++;
                Assert.Less(deep, shore + 400, "deep water within 400 columns of the shore");
                int land = shore - 1;
                var stand = new Vector2(land + 0.5f, side.terrain.TopSolidY(land) + 1.1f);
                side.player.Body.position = stand; side.player.transform.position = stand; side.player.Body.linearVelocity = Vector2.zero;
                var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                if (follow != null) follow.SnapToTarget();
                float until = Time.realtimeSinceStartup + 25f;
                while (!(side.terrain.IsSettled && side.terrain.IsCollisionReady(deep, side.terrain.TopSolidY(deep))) && Time.realtimeSinceStartup < until) yield return null;
                float py = side.player.Body.position.y;
                var maw = creatures.SpawnAt(Meridian.Creatures.Species.HadalMaw, deep, py);
                int sharkAt = deep - 10 > shore + 2 ? deep - 10 : deep + 10;
                var shark = creatures.SpawnAt(Meridian.Creatures.Species.Shark, sharkAt, py);
                Assert.NotNull(maw, "the Maw spawns in the deep");
                until = Time.realtimeSinceStartup + 15f;
                while ((maw.Rig == null || (shark != null && shark.Alive && (shark.View.sprite == null || shark.View.sprite.name.StartsWith("CreaturePlaceholder", StringComparison.Ordinal)))) && Time.realtimeSinceStartup < until) yield return null;
                Assert.NotNull(maw.Rig, "the Maw's rig built");
                // It follows: a few seconds for the Maw to come toward the shore and hold its distance.
                for (int i = 0; i < 200; i++) yield return new WaitForFixedUpdate();
                if (follow != null) follow.enabled = false;
                float z = cam.transform.position.z;
                TestContext.Out.WriteLine($"[MERIDIAN] u119: ocean {start}+{len}, shore {shore}, deep {deep} ({creatures.SiteAt(deep, y).waterDepth} m), maw at {maw.Body.position} ({maw.Rig.Bones.Length} bones, state {maw.State}, reacting {maw.RigReacting}), shark {(shark != null ? shark.Body.position.ToString() : "none")}, surveyor {side.player.Body.position}");
                // 1. The shore at 1x: the surveyor on the sand, the deep opening to the right.
                cam.transform.position = new Vector3(shore + 7f, side.terrain.TopSolidY(land) - 1f, z);
                yield return Shot("1_shore");
                // 2. The Maw at 1x: the camera on its head (it is ~34 m long: a set piece over two screens).
                cam.transform.position = new Vector3(maw.Body.position.x, maw.Body.position.y, z);
                yield return Shot("2_maw_1x");
                // 3. The react: the surveyor's body held still inside 12 m over the water.
                side.player.Body.simulated = false;
                var near = maw.Body.position + new Vector2(7f, 2.5f);
                side.player.transform.position = near; side.player.Body.position = near;
                for (float t = 0f; t < 0.8f; t += Time.deltaTime) yield return null;
                cam.transform.position = new Vector3(maw.Body.position.x + 4f, maw.Body.position.y + 1f, z);
                yield return Shot("3_react");
                var jaw = maw.Rig.Bone("jaw");
                var lure = maw.RigSlotRenderer("lure");
                TestContext.Out.WriteLine($"[MERIDIAN] u119 react: reacting {maw.RigReacting}, jaw {(jaw != null ? Quaternion.Angle(Quaternion.identity, jaw.localRotation) : 0f):F1}°, lure {(lure != null && lure.sprite != null ? lure.sprite.name : "none")}, bumps {creatures.Bumps}");
                Assert.IsTrue(maw.RigReacting, "inside the react radius");
                Assert.AreEqual(0, creatures.Bumps, "D-087: no bump");
                side.player.Body.simulated = true;
                if (follow != null) follow.enabled = true;
                creatures.DespawnAll();
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// A den creature caught in its peek: standing still at its mound (the director's Idle, not a wander turn, whose one slow
        /// frame also draws the idle clip) with at least 0.8 s of the director's 2 s wander window left, so the shot a few frames
        /// later still has it (CreatureDirector.Think re-rolls Idle / Wander on floor(Time.time × 0.5)).
        /// </summary>
        static bool Peeking(Meridian.Creatures.Creature c) =>
            c.AtDen && c.State == Meridian.Creatures.CreatureState.Idle && c.CurrentClip == "idle" && Mathf.Repeat(Time.time, 2f) <= 1.2f;

        /// <summary>
        /// U-118: Mars on the cartoon stage → coordination/reports/unity/u118/: the spawn's set at 1x with the B-140 plants and a dustskater,
        /// the canyon floor after the border crossfade, a tube lurker at its mound (D-126), and the storm set's veil at full intensity.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU118Mars()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
                yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mars));
                var side = director.PlanetSide;
                timeout = Time.realtimeSinceStartup + 20f;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
                side.dayNight.Override = 0.45f;
                side.hazards.enabled = false;
                if (side.wardens != null) side.wardens.enabled = false;
                var creatures = side.creatures;
                creatures.autoSpawn = false;
                foreach (var c in creatures.All) if (c.Alive) creatures.Despawn(c);
                var stage = side.cartoon;
                var cam = side.sideCamera;
                var dir = "coordination/reports/unity/u118";
                Directory.CreateDirectory(dir);
                timeout = Time.realtimeSinceStartup + 15f;
                while ((stage.Layers.placeholders.Contains(true) || !stage.Flora.Ready || !stage.Ground.Ready) && Time.realtimeSinceStartup < timeout) yield return null;
                for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] u118 {label}: x {cam.transform.position.x:F0}, region {Meridian.Planet.Backdrop.StageRegions.At(Meridian.Planets.PlanetId.Mars, Mathf.FloorToInt(cam.transform.position.x))}, scene {stage.Scene} ({stage.Layers.SceneKey}, fallback {stage.Layers.UsedFallback}), datum {stage.Layers.datumY:F1}, placeholders {stage.Layers.placeholders.Contains(true)}, veil alpha {(stage.StormLayers != null ? stage.StormLayers.alpha : 0f):F2}");
                }
                IEnumerator CarryTo(int tx)
                {
                    var stand = new Vector2(tx + 0.5f, side.terrain.TopSolidY(tx) + 1.1f);
                    side.player.Body.position = stand; side.player.transform.position = stand; side.player.Body.linearVelocity = Vector2.zero;
                    var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                    if (follow != null) follow.SnapToTarget();
                    float until = Time.realtimeSinceStartup + 20f;
                    while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                    until = Time.realtimeSinceStartup + 6f;
                    yield return null; yield return null;
                    while ((stage.Fading || stage.Layers.placeholders.Contains(true)) && Time.realtimeSinceStartup < until) yield return null;
                }
                string Kinds()
                {
                    var tally = new System.Collections.Generic.SortedDictionary<string, int>();
                    foreach (Transform t in stage.Flora.transform) { tally.TryGetValue(t.name, out int n); tally[t.name] = n + 1; }
                    var sb = new System.Text.StringBuilder();
                    foreach (var kv in tally) sb.Append(sb.Length > 0 ? ", " : "").Append($"{kv.Key} ×{kv.Value}");
                    return sb.Length > 0 ? sb.ToString() : "none";
                }
                // 1. The spawn: the region's set, the B-140 plants, a dustskater beside the surveyor.
                int px = Mathf.FloorToInt(side.player.transform.position.x);
                var skater = creatures.SpawnAt(Meridian.Creatures.Species.Dustskater, px + 3, side.player.Body.position.y);
                float art = Time.realtimeSinceStartup + 10f;
                while (skater != null && skater.Alive && skater.IsPlaceholder && !(skater.Model != null && skater.Model.Ready) && Time.realtimeSinceStartup < art) yield return null;
                int spawnTop = side.terrain.TopSolidY(side.spawnX);
                TestContext.Out.WriteLine($"[MERIDIAN] u118 spawn column {side.spawnX}: top solid y {spawnTop} tile {side.terrain.GetTile(side.spawnX, spawnTop)} (ice {Meridian.Terrain.TileId.Ice}, basalt {Meridian.Terrain.TileId.Basalt}, regolith {Meridian.Terrain.TileId.Regolith}), strip material {stage.Ground.MaterialAt(side.spawnX)} (0 regolith, 1 basalt), band {Meridian.Flora.FloraRigs.BiomeNameAt(Meridian.Planets.PlanetId.Mars, side.spawnX)}");
                { var row = new System.Text.StringBuilder(); foreach (int dx in new[] { -16, -8, -3, 0, 3, 8, 16 }) { int cx = side.spawnX + dx; int ty = side.terrain.TopSolidY(cx); row.Append($" x{cx}: y{ty} t{side.terrain.GetTile(cx, ty)} m{stage.Ground.MaterialAt(cx)};"); } TestContext.Out.WriteLine("[MERIDIAN] u118 spawn row (top solid y, tile, strip material):" + row); }
                TestContext.Out.WriteLine($"[MERIDIAN] u118 spawn x {side.spawnX}: plants {Kinds()}; dustskater {(skater == null ? "none" : skater.IsPlaceholder ? "placeholder" : skater.View.enabled ? "sheet " + (skater.View.sprite != null ? skater.View.sprite.name : "?") : "model")}");
                yield return Shot($"1_{stage.Scene}_1x");
                // 2. The canyon floor: the border crossfade has run by the time the chunks are in.
                int canyonX = (Meridian.Terrain.MarsLandforms.CanyonStart + Meridian.Terrain.MarsLandforms.CanyonEnd) / 2;
                yield return CarryTo(canyonX);
                yield return Shot("2_canyon_1x");
                // 3. A tube lurker at its mound over the first lava tube (the surveyor and the camera on the surface past the skylight shaft, not down it), a dustskater on the plains beside it.
                var tube = Meridian.Terrain.MarsLandforms.Tubes[0];
                int lurkerX = tube.x0 + Meridian.Terrain.MarsLandforms.SkylightInset + Meridian.Terrain.MarsLandforms.SkylightWidth + 8;
                yield return CarryTo(lurkerX + 12); // outside the lurker's 6 m sense range: it peeks instead of fleeing
                float ready = Time.realtimeSinceStartup + 10f;
                while (!side.terrain.IsCollisionReady(lurkerX, side.terrain.TopSolidY(lurkerX)) && Time.realtimeSinceStartup < ready) yield return null;
                var lurker = creatures.SpawnAt(Meridian.Creatures.Species.TubeLurker, lurkerX, side.player.Body.position.y);
                var skater2 = creatures.SpawnAt(Meridian.Creatures.Species.Dustskater, lurkerX - 6, side.player.Body.position.y);
                art = Time.realtimeSinceStartup + 10f;
                while (((lurker != null && lurker.Alive && lurker.IsPlaceholder) || (skater2 != null && skater2.Alive && skater2.IsPlaceholder)) && Time.realtimeSinceStartup < art) yield return null;
                art = Time.realtimeSinceStartup + 30f;
                while (lurker != null && lurker.Alive && !Peeking(lurker) && Time.realtimeSinceStartup < art) yield return null; // the peek at the den (take 4 timed out at 10 s mid-walk; the 11:29 / 11:47 takes stopped on a turn's one idle frame)
                var denSprite = creatures.Dens.Count > 0 ? creatures.Dens[0].GetComponent<SpriteRenderer>() : null;
                art = Time.realtimeSinceStartup + 10f;
                while (denSprite != null && (denSprite.sprite == null || !denSprite.enabled) && Time.realtimeSinceStartup < art) yield return null; // the mound's sheet
                var follow3 = cam.GetComponent<Meridian.Player.CameraFollow>();
                if (follow3 != null) follow3.enabled = false;
                if (lurker != null) cam.transform.position = new Vector3(lurker.Body.position.x, lurker.Body.position.y + 3f, cam.transform.position.z);
                yield return null;
                TestContext.Out.WriteLine($"[MERIDIAN] u118 lurker at {lurkerX}: {(lurker == null ? "no spawn" : $"at den {lurker.AtDen}, clip {lurker.CurrentClip ?? "none"}, {(lurker.IsPlaceholder ? "placeholder" : "sheet")}, state {lurker.State}")}, dens {creatures.Dens.Count} (mound sprite {(denSprite != null && denSprite.sprite != null ? denSprite.sprite.name + (denSprite.enabled ? "" : " (renderer off)") : "none")}), dustskater {(skater2 == null ? "none" : skater2.IsPlaceholder ? "placeholder" : "sheet")}");
                yield return Shot("3_lurker_den");
                // 4. The storm: forced, the veil at full intensity over the base set.
                var storm = side.dustStorm;
                if (storm != null)
                {
                    storm.Force(1f, 120f);
                    float full = Time.realtimeSinceStartup + 25f;
                    while (storm.Intensity < 0.95f && Time.realtimeSinceStartup < full) yield return null;
                    yield return null;
                    TestContext.Out.WriteLine($"[MERIDIAN] u118 storm: phase {storm.Phase}, intensity {storm.Intensity:F2}, veil alpha {(stage.StormLayers != null ? stage.StormLayers.alpha : 0f):F2}, scroll {(stage.StormLayers != null ? stage.StormLayers.scrollX : 0f):F1} m");
                }
                yield return Shot("4_storm_1x");
                if (follow3 != null) follow3.enabled = true;
                creatures.DespawnAll();
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-128: the camp frame (unchanged), the forest → plains border mid-crossfade, and the shore at column 2096 with the coast set painted at the
        /// water line behind the Maw → coordination/reports/unity/u128/.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU128Shore()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                var creatures = side.creatures;
                creatures.autoSpawn = false;
                foreach (var c in creatures.All) if (c.Alive) creatures.Despawn(c);
                var stage = side.cartoon;
                var cam = side.sideCamera;
                var dir = "coordination/reports/unity/u128";
                Directory.CreateDirectory(dir);
                timeout = Time.realtimeSinceStartup + 15f;
                while ((stage.Layers.placeholders.Contains(true) || !stage.Flora.Ready) && Time.realtimeSinceStartup < timeout) yield return null;
                for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] u128 {label}: camera ({cam.transform.position.x:F1}, {cam.transform.position.y:F1}), scene {stage.Scene} ({stage.Layers.SceneKey}), datum {stage.Layers.datumY:F1}, anchor {stage.Layers.anchorY:F1}, fading {stage.Fading} (incoming alpha {(stage.Incoming != null && stage.Incoming.gameObject.activeSelf ? stage.Incoming.alpha : 0f):F2}), crossfades {stage.Crossfades}");
                }
                void Put(int tx)
                {
                    var stand = new Vector2(tx + 0.5f, side.terrain.TopSolidY(tx) + 1.1f);
                    side.player.Body.position = stand; side.player.transform.position = stand; side.player.Body.linearVelocity = Vector2.zero;
                    var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                    if (follow != null) follow.SnapToTarget();
                }
                IEnumerator Settle()
                {
                    float until = Time.realtimeSinceStartup + 20f;
                    while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                }
                // 1. The camp: unchanged (the camp band keeps the stamped surface, the forest set).
                yield return Shot("1_camp");
                // 2. The forest → plains border at 700: step across and shoot mid-crossfade.
                Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Plains, out int ps, out int pl);
                Put(ps - 12); yield return Settle();
                float wait = Time.realtimeSinceStartup + 6f;
                while (stage.Fading && Time.realtimeSinceStartup < wait) yield return null; // any fade from the carry settles first
                Put(ps + 12);
                wait = Time.realtimeSinceStartup + 6f;
                while (!(stage.Fading && stage.Incoming != null && stage.Incoming.alpha >= 0.35f) && Time.realtimeSinceStartup < wait) yield return null;
                yield return Shot("2_border_mid");
                wait = Time.realtimeSinceStartup + 6f;
                while (stage.Fading && Time.realtimeSinceStartup < wait) yield return null;
                yield return Shot("3_plains");
                // 3. The shore at 2096 with the Maw in the deep: the coast set at the water line.
                var spec = Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.HadalMaw);
                Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Ocean, out int os, out int ol);
                float y = side.player.Body.position.y;
                int shore = os;
                while (shore < os + ol && creatures.SiteAt(shore, y).aboveTile != Meridian.Terrain.TileId.Water) shore++;
                int deep = shore;
                while (deep < shore + 400 && creatures.SiteAt(deep, y).waterDepth < spec.WaterDepthNeeded) deep++;
                Put(shore - 1); yield return Settle();
                wait = Time.realtimeSinceStartup + 10f;
                while (!(side.terrain.IsCollisionReady(deep, side.terrain.TopSolidY(deep))) && Time.realtimeSinceStartup < wait) yield return null;
                var maw = creatures.SpawnAt(Meridian.Creatures.Species.HadalMaw, deep, side.player.Body.position.y);
                wait = Time.realtimeSinceStartup + 15f;
                while ((maw != null && maw.Rig == null || stage.Fading || stage.Layers.placeholders.Contains(true)) && Time.realtimeSinceStartup < wait) yield return null;
                for (int i = 0; i < 150; i++) yield return new WaitForFixedUpdate(); // the Maw comes in to hold its distance
                var follow2 = cam.GetComponent<Meridian.Player.CameraFollow>();
                if (follow2 != null) follow2.enabled = false;
                cam.transform.position = new Vector3(shore + 7f, side.terrain.TopSolidY(shore - 1) - 1f, cam.transform.position.z);
                yield return Shot("4_shore_coast");
                Assert.AreEqual("coast", stage.Scene, "the coast set on the shore");
                Assert.IsFalse(stage.Layers.placeholders.Contains(true), "the coast layers painted");
                if (follow2 != null) follow2.enabled = true;
                creatures.DespawnAll();
                side.dayNight.Override = null;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        IEnumerator CaptureShip(string folder)
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
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
                while ((legs == null || !legs.Ready) && Time.realtimeSinceStartup < timeout) yield return null;
                var fx = ship.GetComponent<Meridian.FX.ShipFx>();
                TestContext.Out.WriteLine($"[MERIDIAN] {folder} ship art: {(legs != null && legs.RigReady ? $"rig ({legs.Rig.Bones.Length} bones, playing {legs.Rig.Playing}, animator {(legs.Rig.Animator != null ? "on" : "missing")})" : legs != null && legs.Model != null && legs.Model.Ready ? "legacy model" : "none")}, fx on rig {(fx != null && fx.OnRig)}");
                // Clean shots: whatever the stage spawned at load is logged, then despawned.
                foreach (var c in side.creatures.All)
                    if (c.Alive) { TestContext.Out.WriteLine($"[MERIDIAN] {folder} despawning {c.Spec.id} at {c.Body.position} (view {(c.View != null && c.View.sprite != null ? c.View.sprite.name : "none")})"); side.creatures.Despawn(c); }
                ship.GetComponent<Meridian.Ship.ShipBoarding>().ForceAboard();
                ship.externalInput = true;
                ship.intent = default;
                for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
                var cam = side.sideCamera;
                var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                TestContext.Out.WriteLine($"[MERIDIAN] {folder} camera: follow {(follow != null ? follow.enabled.ToString() : "none")}, target {(follow != null && follow.target != null ? follow.target.name : "none")}, vehicle {(follow != null && follow.Vehicle != null)}, cartoon {(follow != null && follow.Cartoon)}");
                var dir = "coordination/reports/unity/" + folder;
                Directory.CreateDirectory(dir);

                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    var lead = (Vector2)cam.transform.position - ship.Body.position;
                    TestContext.Out.WriteLine($"[MERIDIAN] {folder} {label}: tilt {ship.Tilt:F1}°, v ({ship.Body.linearVelocity.x:F1}, {ship.Body.linearVelocity.y:F1}) m/s, T/W {ship.ThrustToWeight:F2}, alt {ship.AltitudeAboveGround:F1} m, camera − hull ({lead.x:F1}, {lead.y:F1}), stage ({(follow != null ? follow.Stage.X : 0f):F1}, {(follow != null ? follow.Stage.Y : 0f):F1}) vs cam ({cam.transform.position.x:F1}, {cam.transform.position.y:F1}), follow {(follow != null && follow.enabled)}/{(follow != null && follow.isActiveAndEnabled)}/{(follow != null && follow.gameObject.activeInHierarchy)}, entries {(follow != null ? follow.Entries : -1)}, steps {(follow != null ? follow.StepsApplied : -1)}, dt {Time.deltaTime:F4}, scale {Time.timeScale}, camGO {cam.gameObject.activeInHierarchy}/{cam.enabled}, vehicle {(follow != null && follow.Vehicle != null)}, stand-in {(legs != null && legs.StandIn)}");
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
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-123: Mercury on the cartoon stage → coordination/reports/unity/u123/: the camp at noon (the day set, the Mercury plants, a Glassback beside the
        /// surveyor — spawned on the band, which is its rule, before the clock turns to noon), the dawn line at the camp (the twilight set, a Flarewing over the
        /// surveyor), and the first cold trap's floor at night with the Shadewyrm peeking from its burrow. Shot once B-148 / B-149 / B-150 are in.
        /// </summary>
        [UnityTest]
        public IEnumerator CaptureU123Mercury()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
                yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Mercury));
                var side = director.PlanetSide;
                timeout = Time.realtimeSinceStartup + 20f;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
                side.hazards.enabled = false;
                if (side.wardens != null) side.wardens.enabled = false;
                var creatures = side.creatures;
                creatures.autoSpawn = false;
                foreach (var c in creatures.All) if (c.Alive) creatures.Despawn(c);
                var stage = side.cartoon;
                var cam = side.sideCamera;
                int w = side.Config.worldWidth;
                var dir = "coordination/reports/unity/u123";
                Directory.CreateDirectory(dir);
                // The dawn line sits where LocalTime = 0.25: dawn = x + (localTime − 0.25) × W; the hazards' offset moves the clock the stage, the creatures and the flares share.
                IEnumerator Clock(float x, float localTime)
                {
                    side.hazards.mercuryClockOffset = 0;
                    float dawn = Meridian.Terrain.MercuryTerminator.Dawn(stage.MercuryClock, w);
                    float wantDawn = Mathf.Repeat(x + (localTime - 0.25f) * w, w);
                    side.hazards.mercuryClockOffset = Mathf.Repeat(wantDawn - dawn, w) * Meridian.Terrain.MercuryTerminator.CreepSecondsPerMetre;
                    yield return null; yield return null;
                    float until = Time.realtimeSinceStartup + 8f;
                    while ((stage.Fading || stage.Layers.placeholders.Contains(true)) && Time.realtimeSinceStartup < until) yield return null;
                }
                IEnumerator CarryTo(int tx)
                {
                    var stand = new Vector2(tx + 0.5f, side.terrain.TopSolidY(tx) + 1.1f);
                    side.player.Body.position = stand; side.player.transform.position = stand; side.player.Body.linearVelocity = Vector2.zero;
                    var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                    if (follow != null) follow.SnapToTarget();
                    float until = Time.realtimeSinceStartup + 20f;
                    while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                    until = Time.realtimeSinceStartup + 6f;
                    yield return null; yield return null;
                    while ((stage.Fading || stage.Layers.placeholders.Contains(true)) && Time.realtimeSinceStartup < until) yield return null;
                }
                string Kinds()
                {
                    var tally = new System.Collections.Generic.SortedDictionary<string, int>();
                    foreach (Transform t in stage.Flora.transform) { tally.TryGetValue(t.name, out int n); tally[t.name] = n + 1; }
                    var sb = new System.Text.StringBuilder();
                    foreach (var kv in tally) sb.Append(sb.Length > 0 ? ", " : "").Append($"{kv.Key} ×{kv.Value}");
                    return sb.Length > 0 ? sb.ToString() : "none";
                }
                IEnumerator Shot(string label)
                {
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    int cx = Mathf.FloorToInt(cam.transform.position.x);
                    TestContext.Out.WriteLine($"[MERIDIAN] u123 {label}: x {cx}, zone {Meridian.Terrain.MercuryTerminator.ZoneAt(cx, stage.MercuryClock, w)}, local time {Meridian.Terrain.MercuryTerminator.LocalTime(cx, stage.MercuryClock, w):F2}, scene {stage.Scene} ({stage.Layers.SceneKey}, fallback {stage.Layers.UsedFallback}), datum {stage.Datum.At(cx):F1}, placeholders {stage.Layers.placeholders.Contains(true)}, strip {stage.Ground.MaterialAt(cx)} ({stage.Ground.MaterialsLoaded} in), plants {Kinds()}");
                }
                IEnumerator WaitArt(Meridian.Creatures.Creature c)
                {
                    float art = Time.realtimeSinceStartup + 10f;
                    while (c != null && c.Alive && c.IsPlaceholder && !(c.Model != null && c.Model.Ready) && Time.realtimeSinceStartup < art) yield return null;
                }
                // 1. The camp at noon: the day set and the plants, a Glassback beside the surveyor (spawned on the band — its rule — then the clock turns to noon).
                int px = Mathf.FloorToInt(side.player.transform.position.x);
                yield return Clock(px + 0.5f, 0.25f);
                timeout = Time.realtimeSinceStartup + 15f;
                while ((stage.Layers.placeholders.Contains(true) || !stage.Flora.Ready || !stage.Ground.Ready) && Time.realtimeSinceStartup < timeout) yield return null;
                for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
                var glassback = creatures.SpawnAt(Meridian.Creatures.Species.Glassback, px + 3, side.player.Body.position.y);
                yield return WaitArt(glassback);
                yield return Clock(px + 0.5f, 0.5f);
                // D-146: the plants grow by the zone of the moment they are placed: grow the camp's again at noon (the day kinds).
                stage.Flora.ClearPlants();
                yield return null;
                stage.Flora.Populate(Meridian.View2D.CartoonStage.FloraCount, Meridian.View2D.CartoonStage.FloraSpacing, side.spawnX + 0.5f, Meridian.Planets.PlanetId.Mercury.GetHashCode() * 31 + 7);
                yield return null;
                TestContext.Out.WriteLine($"[MERIDIAN] u123 camp x {px}: glassback {(glassback == null ? "none" : glassback.IsPlaceholder ? "placeholder" : "sheet")}{(glassback != null && !glassback.Alive ? " (gone)" : "")}");
                yield return Shot("1_day_1x");
                // 2. The dawn line at the camp: the twilight set, a Flarewing over the surveyor.
                yield return Clock(px + 0.5f, 0.25f);
                stage.Flora.ClearPlants(); // D-146: the dawn line's own kinds
                yield return null;
                stage.Flora.Populate(Meridian.View2D.CartoonStage.FloraCount, Meridian.View2D.CartoonStage.FloraSpacing, side.spawnX + 0.5f, Meridian.Planets.PlanetId.Mercury.GetHashCode() * 31 + 7);
                yield return null;
                var wing = creatures.SpawnAt(Meridian.Creatures.Species.Flarewing, px - 3, side.player.Body.position.y + 5f);
                yield return WaitArt(wing);
                TestContext.Out.WriteLine($"[MERIDIAN] u123 dawn line x {px}: flarewing {(wing == null ? "none" : wing.IsPlaceholder ? "placeholder" : "sheet")}, glassback {(glassback != null && glassback.Alive ? "alive" : "gone")}");
                yield return Shot("2_twilight_1x");
                // 3. The night side: the first cold trap's floor, the Shadewyrm peeking from its burrow (the surveyor 14 m off: it hunts inside its 11 m sense range).
                int trapX = Meridian.Terrain.MercuryLandforms.ColdTrapCentre(0, w);
                yield return CarryTo(trapX + 14);
                yield return Clock(trapX, 0f);
                stage.Flora.ClearPlants(); // D-146: the trap's own plants (the "polar" kinds in a cold trap)
                yield return null;
                stage.Flora.Populate(6, 3f, trapX - 10f, Meridian.Planets.PlanetId.Mercury.GetHashCode() * 31 + 7); // six on the wyrm's left (trapX − 19 … − 4): the peek and the burrow stay clear
                yield return null;
                float ready = Time.realtimeSinceStartup + 10f;
                while (!side.terrain.IsCollisionReady(trapX, side.terrain.TopSolidY(trapX)) && Time.realtimeSinceStartup < ready) yield return null;
                var wyrm = creatures.SpawnAt(Meridian.Creatures.Species.Shadewyrm, trapX, side.terrain.TopSolidY(trapX) + 1.35f);
                yield return WaitArt(wyrm);
                float art = Time.realtimeSinceStartup + 30f;
                while (wyrm != null && wyrm.Alive && !Peeking(wyrm) && Time.realtimeSinceStartup < art) yield return null; // the peek from the burrow
                var denSprite = creatures.Dens.Count > 0 ? creatures.Dens[0].GetComponent<SpriteRenderer>() : null;
                art = Time.realtimeSinceStartup + 10f;
                while (denSprite != null && (denSprite.sprite == null || !denSprite.enabled) && Time.realtimeSinceStartup < art) yield return null; // the burrow's sheet
                var follow3 = cam.GetComponent<Meridian.Player.CameraFollow>();
                if (follow3 != null) follow3.enabled = false;
                if (wyrm != null) cam.transform.position = new Vector3(wyrm.Body.position.x, wyrm.Body.position.y + 3f, cam.transform.position.z);
                yield return null;
                TestContext.Out.WriteLine($"[MERIDIAN] u123 shadewyrm at {trapX}: {(wyrm == null ? "no spawn" : $"at den {wyrm.AtDen}, clip {wyrm.CurrentClip ?? "none"}, {(wyrm.IsPlaceholder ? "placeholder" : "sheet")}, state {wyrm.State}")}, dens {creatures.Dens.Count} (burrow sprite {(denSprite != null && denSprite.sprite != null ? denSprite.sprite.name : "none")})");
                yield return Shot("3_night_burrow");
                if (follow3 != null) follow3.enabled = true;
                creatures.DespawnAll();
                side.hazards.mercuryClockOffset = 0;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-124 (B-151): the C3 UI at 1080p in reports/unity/u124/: each planet's title card over its own surface, held centred
        /// (titlecard_mars, titlecard_mercury, titlecard_earth), then on Earth the pause card, the settings paper with the Film switch,
        /// the inventory paper, the catalogue on the scroll and the crafting panel on the inventory paper (D-149). The overlay canvases draw through the
        /// side camera (a camera render never includes a screen-space overlay canvas).
        /// </summary>
        [UnityTest, Timeout(240000)]
        public IEnumerator CaptureU124Ui()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            var canvases = new System.Collections.Generic.List<Canvas>();
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
                var menu = Meridian.UI.MenuController.Instance;
                Assert.NotNull(menu, "the menus in Core");
                var dir = "coordination/reports/unity/u124";
                Directory.CreateDirectory(dir);

                void Overlays(Camera cam)
                {
                    foreach (var c in UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsInactive.Include))
                    {
                        if (c.renderMode == RenderMode.ScreenSpaceOverlay) { canvases.Add(c); c.renderMode = RenderMode.ScreenSpaceCamera; c.planeDistance = 1f; }
                        if (canvases.Contains(c)) c.worldCamera = cam;
                    }
                }
                IEnumerator Shot(Camera cam, string label)
                {
                    Overlays(cam);
                    yield return null;
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                }

                var cards = menu.TitleCards;
                foreach (var p in new[] { Meridian.Planets.PlanetId.Mars, Meridian.Planets.PlanetId.Mercury, Meridian.Planets.PlanetId.Earth })
                {
                    yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(p));
                    var side = director.PlanetSide;
                    timeout = Time.realtimeSinceStartup + 20f;
                    while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
                    side.creatures.autoSpawn = false;
                    side.creatures.DespawnAll();
                    if (side.hazards != null) side.hazards.enabled = false;
                    timeout = Time.realtimeSinceStartup + 8f;
                    while (side.cartoon != null && side.cartoon.Layers != null && side.cartoon.Layers.placeholders.Contains(true) && Time.realtimeSinceStartup < timeout) yield return null;
                    cards.Show(p);
                    timeout = Time.realtimeSinceStartup + 5f;
                    var cardKey = Meridian.Art.ArtKeys.Ui.TitleCard(p);
                    while (cards.Showing != cardKey && Time.realtimeSinceStartup < timeout) yield return null; // this planet's card, not the last one still sliding out
                    cards.Seek(Meridian.UI.TitleCard.SlideSeconds); // the held frame, centred
                    var label = "titlecard_" + p.ToString().ToLowerInvariant();
                    yield return Shot(side.sideCamera, label);
                    TestContext.Out.WriteLine($"[MERIDIAN] u124 {label}: showing {cards.Showing ?? "none (no card art)"}, size {cards.Card.rectTransform.sizeDelta}, x {cards.Card.rectTransform.anchoredPosition.x:F0}");
                }

                cards.Hide(); // the panels are shot without the last card over them
                var earth = director.PlanetSide;
                var cam = earth.sideCamera;
                var inventory = UnityEngine.Object.FindAnyObjectByType<Meridian.UI.InventoryPanel>();
                var catalogue = UnityEngine.Object.FindAnyObjectByType<Meridian.UI.CataloguePanel>();
                var crafting = UnityEngine.Object.FindAnyObjectByType<Meridian.UI.CraftingPanel>();
                timeout = Time.realtimeSinceStartup + 10f;
                while ((!menu.PausePaper.HasValue || !menu.Settings.Paper.HasValue || (inventory != null && !inventory.Paper.HasValue)
                        || (catalogue != null && !catalogue.Paper.HasValue) || (crafting != null && !crafting.Paper.HasValue)) && Time.realtimeSinceStartup < timeout) yield return null;
                TestContext.Out.WriteLine($"[MERIDIAN] u124 paper: pause {menu.PausePaper}, settings {menu.Settings.Paper}, inventory {inventory?.Paper}, scroll {catalogue?.Paper}, sign {crafting?.Paper}; film switch {(menu.Settings.FilmSwitch.enabled ? menu.Settings.FilmSwitch.sprite.name : "none")}");

                menu.OpenPause();
                yield return Shot(cam, "pause");
                menu.OpenSettings();
                yield return Shot(cam, "settings");
                menu.CloseSettings();
                menu.Resume();
                if (inventory != null) { inventory.SetOpen(true); yield return Shot(cam, "inventory"); inventory.SetOpen(false); }
                if (catalogue != null) { catalogue.SetOpen(true); yield return Shot(cam, "catalogue_scroll"); catalogue.SetOpen(false); }
                if (crafting != null) { crafting.SetOpen(true); yield return Shot(cam, "crafting_paper"); crafting.SetOpen(false); }
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                foreach (var c in canvases) if (c != null) { c.renderMode = RenderMode.ScreenSpaceOverlay; c.worldCamera = null; }
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-125 (B-152 / B-153 / B-154): Venus on the cartoon stage at 1x in reports/unity/u125/: 1_deck_1x (the surveyor on the Meridian station's
        /// deck: the deck set off the cloud deck, the deck-plank strip, a Sulfur drifter), 2_surface_vent_1x (the first vent field: the surface set,
        /// the basalt crust, a Pressure crab and the Vent eel at its vent mouth).
        /// </summary>
        [UnityTest, Timeout(180000)]
        public IEnumerator CaptureU125Venus()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
                yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Venus));
                var side = director.PlanetSide;
                timeout = Time.realtimeSinceStartup + 20f;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
                if (side.hazards != null) side.hazards.enabled = false;
                if (side.wardens != null) side.wardens.enabled = false;
                var creatures = side.creatures;
                creatures.autoSpawn = false;
                creatures.DespawnAll();
                var stage = side.cartoon;
                var cam = side.sideCamera;
                var body = side.player.GetComponent<Rigidbody2D>();
                var dir = "coordination/reports/unity/u125";
                Directory.CreateDirectory(dir);

                IEnumerator Carry(float x, float y)
                {
                    if (body != null) { body.simulated = false; body.position = new Vector2(x, y); }
                    side.player.transform.position = new Vector3(x, y, side.player.transform.position.z);
                    yield return null; yield return null;
                }
                IEnumerator Settle(string scene)
                {
                    float until = Time.realtimeSinceStartup + 10f;
                    while ((stage.Scene != scene || stage.Fading || stage.Layers.placeholders.Contains(true)) && Time.realtimeSinceStartup < until) yield return null;
                    until = Time.realtimeSinceStartup + 1.5f;
                    while (Time.realtimeSinceStartup < until) yield return null;
                }
                IEnumerator Shot(string label)
                {
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] u125 {label}: scene {stage.Scene} → {stage.Layers.SceneKey} (fallback {stage.Layers.UsedFallback}), datum {stage.Layers.datumY:F1}, strips {stage.Ground.MaterialsLoaded}, plank frames {stage.Ground.DeckFramesShown}, plants {stage.Flora.SpriteCount}");
                }

                // 1. On the Meridian station's deck with a Sulfur drifter.
                var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
                float deckTop = station.floatY + Meridian.Planet.POI.PoiCatalog.DeckTop;
                float sx = station.x + station.floatWidth * 0.5f;
                yield return Carry(sx, deckTop + 0.05f);
                yield return Settle(Meridian.View2D.CartoonStage.VenusDeckScene);
                creatures.Spawn(Meridian.Creatures.Species.SulfurDrifter, new Vector2(sx + 5f, deckTop + 4f));
                yield return Shot("1_deck_1x");
                creatures.DespawnAll();

                // 2. The first vent field: a Pressure crab beside the vent, the Vent eel at its mouth.
                var vent = Meridian.Terrain.VenusLandforms.Vents[0];
                int vx = (vent.x0 + vent.x1) / 2;
                float ground = side.terrain.TopSolidY(vx) + 1f;
                yield return Carry(vx - 4f, side.terrain.TopSolidY(vx - 4) + 1.05f);
                yield return Settle(Meridian.View2D.CartoonStage.VenusSurfaceScene);
                var eel = Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.VentEel);
                creatures.Spawn(Meridian.Creatures.Species.VentEel, new Vector2(vx + 0.5f, ground + eel.size.y * 0.5f + 0.05f)); // its vent mouth in front (D-126)
                var crab = Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.PressureCrab);
                int cx = vx - 9;
                creatures.Spawn(Meridian.Creatures.Species.PressureCrab, new Vector2(cx + 0.5f, side.terrain.TopSolidY(cx) + 1f + crab.size.y * 0.5f + 0.05f));
                float wait = Time.realtimeSinceStartup + 1.5f;
                while (Time.realtimeSinceStartup < wait) yield return null;
                yield return Shot("2_surface_vent_1x");
                creatures.DespawnAll();
                if (body != null) body.simulated = true;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }

        /// <summary>
        /// U-127 (B-159 / B-160 / B-156): Jupiter on the cartoon stage at 1x in reports/unity/u127/: 1_floe_kit_tortoise (a Deck 2 floe with its capped
        /// strip, the aerostat kit's deck card on it, a Ballast tortoise over it), 2_storm_deck_glider (a Deck 3 floe, a Stormglider), 3_deep_crush (a
        /// Deep floe, the deep set's CRUSH band on the Crush Line), 4_red_spot (a floe in the Great Red Spot under the spot overlay), 5_whale_crossing
        /// (the Vortex Whale in passing, D-138: never both ends).
        /// </summary>
        [UnityTest, Timeout(240000)]
        public IEnumerator CaptureU127Jupiter()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled;
            Meridian.View2D.CartoonStage.Enabled = true;
            var kitHandle = default(UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationHandle<System.Collections.Generic.IList<Sprite>>);
            GameObject kit = null;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
                yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(Meridian.Planets.PlanetId.Jupiter));
                var side = director.PlanetSide;
                timeout = Time.realtimeSinceStartup + 20f;
                while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
                if (side.hazards != null) side.hazards.enabled = false;
                if (side.wardens != null) side.wardens.enabled = false;
                var creatures = side.creatures;
                creatures.autoSpawn = false;
                creatures.DespawnAll();
                var stage = side.cartoon;
                var cam = side.sideCamera;
                var body = side.player.GetComponent<Rigidbody2D>();
                var t = side.terrain;
                var dir = "coordination/reports/unity/u127";
                Directory.CreateDirectory(dir);

                bool Solid(int x, int y) => Meridian.Terrain.TileId.IsSolid(t.GetTile(x, y));
                // A floe at least 6 columns wide whose top lies in [y0, y1], searched rightward from x0: its left column and standing height.
                bool FindFloe(int x0, int y0, int y1, out int fx, out int fy)
                {
                    for (int x = x0; x < x0 + 1200; x++)
                        for (int y = y1; y >= y0; y--)
                        {
                            if (!Solid(x, y) || Solid(x, y + 1)) continue;
                            bool wide = true;
                            for (int k = 1; k < 6 && wide; k++) wide = Solid(x + k, y) && !Solid(x + k, y + 1);
                            if (wide) { fx = x; fy = y + 1; return true; }
                        }
                    fx = x0; fy = y1; return false;
                }
                IEnumerator Carry(float x, float y)
                {
                    if (body != null) { body.simulated = false; body.position = new Vector2(x, y); }
                    side.player.transform.position = new Vector3(x, y, side.player.transform.position.z);
                    yield return null; yield return null;
                }
                IEnumerator Settle()
                {
                    float until = Time.realtimeSinceStartup + 10f;
                    while ((stage.Fading || stage.Layers.placeholders.Contains(true)) && Time.realtimeSinceStartup < until) yield return null;
                    until = Time.realtimeSinceStartup + 1.5f;
                    while (Time.realtimeSinceStartup < until) yield return null;
                }
                IEnumerator Shot(string label)
                {
                    yield return Save(cam, $"{name}_{label}");
                    File.Copy($"logs/capture_{name}_{label}.png", $"{dir}/{label}.png", true);
                    TestContext.Out.WriteLine($"[MERIDIAN] u127 {label}: scene {stage.Scene} → {stage.Layers.SceneKey} (fallback {stage.Layers.UsedFallback}), datum {stage.Layers.datumY:F0}, camera y {cam.transform.position.y:F0}, strips {stage.Ground.MaterialsLoaded}, caps {stage.Ground.CapsShown}, spot alpha {(stage.StormLayers != null ? stage.StormLayers.alpha : 0f):F2}, plants {stage.Flora.SpriteCount}");
                }
                float Above(Meridian.Creatures.Species s) => Meridian.Creatures.SpeciesSpec.Get(s).size.y * 0.5f + 3f;

                int sx = side.spawnX;
                // 1. A Deck 2 floe: the kit's deck card on it, a Ballast tortoise over it.
                if (FindFloe(sx, Meridian.Terrain.CloudColumn.CloudLayout.Deck2Bottom + 40, Meridian.Terrain.CloudColumn.CloudLayout.Deck1Bottom - 40, out int fx, out int fy))
                {
                    yield return Carry(fx + 2.5f, fy + 0.05f);
                    kitHandle = Meridian.Art.ArtLoad.Asset<System.Collections.Generic.IList<Sprite>>("props/common/aerostat_deck");
                    yield return kitHandle;
                    if (kitHandle.Status == UnityEngine.ResourceManagement.AsyncOperations.AsyncOperationStatus.Succeeded && kitHandle.Result != null && kitHandle.Result.Count > 0)
                    {
                        kit = new GameObject("U127Kit");
                        var sr = kit.AddComponent<SpriteRenderer>();
                        sr.sprite = kitHandle.Result[0];
                        sr.sortingOrder = 4;
                        kit.transform.position = new Vector3(fx + 4.5f, fy, 0f);
                    }
                    creatures.Spawn(Meridian.Creatures.Species.BallastTortoise, new Vector2(fx + 8f, fy + Above(Meridian.Creatures.Species.BallastTortoise)));
                    yield return Settle();
                    yield return Shot("1_floe_kit_tortoise");
                    creatures.DespawnAll();
                    if (kit != null) UnityEngine.Object.Destroy(kit);
                }
                else TestContext.Out.WriteLine("[MERIDIAN] u127: no Deck 2 floe found");

                // 2. A Deck 3 floe (the storm deck) with a Stormglider.
                if (FindFloe(sx, Meridian.Terrain.CloudColumn.CloudLayout.Deck3Bottom + 40, Meridian.Terrain.CloudColumn.CloudLayout.Deck2Bottom - 40, out fx, out fy))
                {
                    yield return Carry(fx + 2.5f, fy + 0.05f);
                    creatures.Spawn(Meridian.Creatures.Species.Stormglider, new Vector2(fx + 7f, fy + Above(Meridian.Creatures.Species.Stormglider)));
                    yield return Settle();
                    yield return Shot("2_storm_deck_glider");
                    creatures.DespawnAll();
                }
                else TestContext.Out.WriteLine("[MERIDIAN] u127: no Deck 3 floe found");

                // 3. The Deep, low over the Crush Line: the CRUSH band on the deep set's near layer.
                if (FindFloe(sx, Meridian.Terrain.CloudColumn.CloudLayout.CrushLine + 4, Meridian.Terrain.CloudColumn.CloudLayout.CrushLine + 60, out fx, out fy))
                {
                    yield return Carry(fx + 2.5f, fy + 0.05f);
                    yield return Settle();
                    yield return Shot("3_deep_crush");
                }
                else TestContext.Out.WriteLine("[MERIDIAN] u127: no floe found just over the Crush Line");

                // 4. A floe inside the Great Red Spot, under its overlay.
                int spot = Meridian.Terrain.CloudColumn.CloudLayout.RedSpotCentre - 200;
                if (FindFloe(spot, Meridian.Terrain.CloudColumn.CloudLayout.Deck2Bottom + 40, Meridian.Terrain.CloudColumn.CloudLayout.Deck1Bottom - 40, out fx, out fy))
                {
                    yield return Carry(fx + 2.5f, fy + 0.05f);
                    yield return Settle();
                    yield return Shot("4_red_spot");
                    // 5. D-138 / U-153: the Vortex Whale crossing the Spot in passing, head first: staged facing −x with its centre 13.5 m ahead of the
                    // surveyor (a Flees whale left alone turns tail on the surveyor), so its head and flank cross the 32 m frame and the flukes stay out.
                    creatures.Spawn(Meridian.Creatures.Species.VortexWhale, new Vector2(fx + 16f, fy + 9f))?.Stage(-1, 15f);
                    yield return Settle();
                    yield return Shot("5_whale_crossing");
                    creatures.DespawnAll();
                }
                else TestContext.Out.WriteLine("[MERIDIAN] u127: no Deck 2 floe found in the Red Spot");
                if (body != null) body.simulated = true;
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                if (kit != null) UnityEngine.Object.Destroy(kit);
                if (kitHandle.IsValid()) Meridian.Art.ArtLoad.Release(kitHandle);
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
            }
        }
    }
}
