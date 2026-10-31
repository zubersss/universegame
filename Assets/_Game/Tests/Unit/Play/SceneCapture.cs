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
            cam.orthographicSize = 260f; // Earth, Luna, Mars and both wells in one frame
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
            cam.orthographicSize = 3f;
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
            void Frame(Vector2 at, float size) { cam.orthographicSize = size; cam.transform.position = new Vector3(at.x, at.y, cam.transform.position.z); }

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
            spaceCam.orthographicSize = 8f;
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
            while ((world.Rings == null || world.Rings.sprite == null || world.BeltArt.Count < Meridian.Space.SpaceWorld.AsteroidKinds) && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 30; i++) yield return null;
            IEnumerator Shot(string label, Vector2 at, float size)
            {
                cam.orthographicSize = size;
                cam.transform.position = new Vector3(at.x, at.y, cam.transform.position.z);
                for (int i = 0; i < 3; i++) yield return null;
                yield return Save(cam, $"{name}_{label}");
            }
            yield return Shot("1_saturn", world.Find("saturn").Value.position, 260f);
            yield return Shot("2_jupiter", world.Find("jupiter").Value.position, 110f);
            yield return Shot("3_neptune", world.Find("neptune").Value.position, 120f);
            var belt = world.BeltClusters.Count > 0 ? world.BeltClusters[0] : new Vector2(Meridian.Space.SpaceLayout.BeltInner + 300f, 0f);
            foreach (var mr in world.BeltArt) Debug.Log($"[MERIDIAN] {mr.name}: enabled {mr.enabled} visible {mr.isVisible} verts {mr.GetComponent<MeshFilter>().sharedMesh.vertexCount} bounds {mr.bounds} mat {mr.sharedMaterial?.name} layer {mr.sortingLayerName}/{mr.sortingOrder}");
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
            cam.orthographicSize = 10f;
            cam.transform.position = new Vector3(camp.def.CenterX, camp.groundY + 6f, cam.transform.position.z);
            side.dayNight.Override = 0.5f;
            for (int i = 0; i < 5; i++) yield return null;
            yield return Save(cam, $"{name}_day");
            side.dayNight.Override = 0.02f;
            for (int i = 0; i < 5; i++) yield return null;
            yield return Save(cam, $"{name}_night");
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
            Assert.AreEqual(9f, cam.orthographicSize, "default ortho size (Bible §5.1)");
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
            UnityEngine.Object.Destroy(tex);
            rt.Release();
        }
    }
}
