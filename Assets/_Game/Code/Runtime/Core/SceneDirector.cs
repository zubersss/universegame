using System;
using System.Collections;
using Meridian.Planets;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Meridian.Core
{
    /// <summary>
    /// Owns additive scene loading (Bible §10.3): Space stays loaded but inactive; PlanetSide is
    /// loaded with the current planet's PlanetConfig.
    /// </summary>
    public sealed class SceneDirector : MonoBehaviour
    {
        public const string SpaceScene = "Space";
        public const string PlanetSideScene = "PlanetSide";

        public GameState gameState;

        public bool IsReady { get; private set; }
        public SpaceRoot Space { get; private set; }
        /// <summary>Where the last planet load spent its time (BudgetGate prints it under the entry row).</summary>
        public string LastLoadBreakdown { get; private set; } = "";
        public PlanetSideRoot PlanetSide { get; private set; }
        public event Action Ready;

        IEnumerator Start()
        {
            if (gameState == null) gameState = GameState.Instance;
            // U-091 (D-089): only the boot planet's sheets, overlapping the Space scene load; an entry prefetches its planet's
            // under the iris-out (TransitionDirector.Enter). The U-039 session preload is gone: a planet's bundle closes with its visit.
            Meridian.Terrain.TerrainTileSet.Prefetch(Meridian.Terrain.TerrainStreamer.MaterialsFor(gameState.currentPlanet));

            if (!SceneManager.GetSceneByName(SpaceScene).isLoaded)
                yield return SceneManager.LoadSceneAsync(SpaceScene, LoadSceneMode.Additive);
            Space = FindRoot<SpaceRoot>(SpaceScene);
            // U-052: Waystations and the docking bay live with the top-down view.
            if (Space != null && Space.GetComponent<Meridian.Trade.DockingBay>() == null) Space.gameObject.AddComponent<Meridian.Trade.DockingBay>();
            // U-063: the Skip Drive rides the top-down ship.
            var topShip = Space != null ? Space.GetComponentInChildren<Meridian.Space.SpaceShip>(true) : null;
            if (topShip != null && topShip.GetComponent<Meridian.Space.SkipDrive>() == null) topShip.gameObject.AddComponent<Meridian.Space.SkipDrive>().ship = topShip;
            // Warm the top-down view now, while it is the only view loaded (one global 2D light), so the
            // first launch never stalls on shader/pipeline setup (U-028).
            if (Space != null) RenderWarmup.WarmUp(Space.GetComponentInChildren<Camera>());
            if (Space != null) Space.gameObject.SetActive(gameState.view == ViewMode.Space);

            yield return LoadPlanetSide(gameState.CurrentPlanetConfig);

            // Boot only: the camera starts on the surface, so let the first chunks arrive behind the
            // boot cover and render once more; their tilemap meshes are then built before the first
            // visible frame (U-028). Entries arrive high above the ground and don't need this.
            if (PlanetSide != null)
            {
                float until = Time.realtimeSinceStartup + 10f;
                while (!PlanetSide.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                // The player and ship sheets arrive asynchronously; draw them once here too.
                var playerView = PlanetSide.player != null ? PlanetSide.player.GetComponent<Meridian.Player.PlayerView>() : null;
                var shipView = PlanetSide.ship != null ? PlanetSide.ship.GetComponentInChildren<SpriteRenderer>() : null;
                float spritesBy = Time.realtimeSinceStartup + 3f;
                while (Time.realtimeSinceStartup < spritesBy &&
                       ((playerView != null && playerView.view.sprite == null) || (shipView != null && shipView.sprite == null)))
                    yield return null;
                LastPlanetWarmupMs += RenderWarmup.WarmUp(PlanetSide.sideCamera, PlanetSide.terrain.TileSet);
            }

            IsReady = true;
            Ready?.Invoke();
        }

        /// <summary>Raised after PlanetSide loads and is configured (start or entry).</summary>
        public event Action PlanetSideLoaded;
        public float LastPlanetWarmupMs { get; private set; }

        /// <summary>Loads PlanetSide with a planet. entryX ≥ 0 = arriving from orbit over that column (Bible §5.3).</summary>
        public IEnumerator LoadPlanetSide(PlanetConfig config, int entryX = -1, float startedAt = -1f)
        {
            if (config == null)
            {
                Debug.LogError("[MERIDIAN] SceneDirector: no PlanetConfig for the current planet.");
                yield break;
            }
            float p0 = Time.realtimeSinceStartup;
            float origin = startedAt >= 0f ? startedAt : p0; // U-091: the planet-load clock starts at the request (the entry start)
            int gen = ++loadGeneration;
            LastPlanetLoadSeconds = -1f;
            var scene = SceneManager.GetSceneByName(PlanetSideScene);
            if (!scene.isLoaded)
                yield return SceneManager.LoadSceneAsync(PlanetSideScene, LoadSceneMode.Additive);
            float p1 = Time.realtimeSinceStartup;
            PlanetSide = FindRoot<PlanetSideRoot>(PlanetSideScene);
            if (PlanetSide != null)
            {
                if (entryX >= 0) PlanetSide.ConfigureForEntry(config, entryX);
                else PlanetSide.Configure(config);
                float p2 = Time.realtimeSinceStartup;
                SceneManager.SetActiveScene(SceneManager.GetSceneByName(PlanetSideScene));
                // U-091: one frame behind the closed iris after Configure (the frame the deferred sheet callbacks used to give):
                // the planet's heavy first frame stays black and the iris-in starts on a normal frame.
                yield return null;
                // Warm-up behind the boot cover or the entry fade (U-028): wait for the tile sheets, then render once off-screen.
                float until = Time.realtimeSinceStartup + 1f;
                while (!PlanetSide.terrain.TileSet.IsReady && Time.realtimeSinceStartup < until) yield return null;
                float p3 = Time.realtimeSinceStartup;
                LastPlanetWarmupMs = RenderWarmup.WarmUp(PlanetSide.sideCamera, PlanetSide.terrain.TileSet);
                LastLoadBreakdown = $"scene load {(p1 - p0) * 1000f:F0} ms, configure {(p2 - p1) * 1000f:F0} ms, tile sheets {(p3 - p2) * 1000f:F0} ms, warm-up {LastPlanetWarmupMs:F0} ms";
                LastLoadBreakdown += $", total {(Time.realtimeSinceStartup - p0) * 1000f:F0} ms";
                StartCoroutine(WatchPlanetLoad(gen, origin, PlanetSide, Meridian.Perf.Residency.PlanetGroup(config.id)));
            }
            PlanetSideLoaded?.Invoke();
        }

        int loadGeneration;

        /// <summary>
        /// U-091 (D-089 "planet load"): seconds from the request (the entry start, or the boot LoadPlanetSide) until the
        /// terrain is settled and no load into the planet's groups is pending; -1 while loading.
        /// </summary>
        public float LastPlanetLoadSeconds { get; private set; } = -1f;

        /// <summary>U-120: what the planet's groups were still loading when the terrain had settled (the time after the scene's own
        /// breakdown goes here), and how long after the settle the last of it finished. Report text; "none" when nothing waited.</summary>
        public string LastLoadPending { get; private set; } = "";

        IEnumerator WatchPlanetLoad(int gen, float origin, PlanetSideRoot side, string group)
        {
            float firstDone = -1f, deadline = origin + 30f, settledAt = -1f;
            LastLoadPending = "";
            while (gen == loadGeneration && side != null)
            {
                bool settled = side.terrain != null && side.terrain.IsSettled;
                if (settled && settledAt < 0f)
                {
                    settledAt = Time.realtimeSinceStartup;
                    LastLoadPending = $"terrain settled at {settledAt - origin:F2} s; still loading: {Meridian.Perf.Residency.PendingKeys(group)}";
                }
                bool done = settled && Meridian.Perf.Residency.PendingPlanet(group) == 0;
                if (done && firstDone >= 0f && settledAt >= 0f) LastLoadPending += $"; last load done {firstDone - settledAt:F2} s after the settle";
                if (done && firstDone >= 0f) { LastPlanetLoadSeconds = firstDone - origin; yield break; } // confirmed on the next frame
                firstDone = done ? Time.realtimeSinceStartup : -1f; // a chained load (the stage-set probe) gets one frame to start
                if (Time.realtimeSinceStartup > deadline) { LastPlanetLoadSeconds = Time.realtimeSinceStartup - origin; yield break; } // a slow load fails with a number
                yield return null;
            }
        }

        /// <summary>Unloads PlanetSide (launch, Bible §5.2). Terrain edits live on in GameState.</summary>
        public AsyncOperation UnloadPlanetSide()
        {
            var scene = SceneManager.GetSceneByName(PlanetSideScene);
            PlanetSide = null;
            loadGeneration++;
            if (!scene.isLoaded) return null;
            var op = SceneManager.UnloadSceneAsync(scene);
            // U-060 / U-091: a planet's bundle now closes with its last handle (no session preload); UnloadUnusedAssets still
            // frees released common-bundle art once the scene is gone.
            if (op != null) op.completed += _ => { Meridian.Terrain.TerrainBlockPalette.ReleaseAll(); Resources.UnloadUnusedAssets(); }; // U-112: the block arrays go with the planet (84 MB stayed in Space)
            return op;
        }

        /// <summary>Shows one view and hides the other (the full transitions arrive with U-012).</summary>
        public void SetView(ViewMode view)
        {
            gameState.view = view;
            // Hide the outgoing view first: each view has a global 2D light and URP rejects two at once.
            if (view == ViewMode.Space)
            {
                if (PlanetSide != null) PlanetSide.gameObject.SetActive(false);
                if (Space != null) Space.gameObject.SetActive(true);
            }
            else
            {
                if (Space != null) Space.gameObject.SetActive(false);
                if (PlanetSide != null) PlanetSide.gameObject.SetActive(true);
            }
        }

        static T FindRoot<T>(string sceneName) where T : Component
        {
            var scene = SceneManager.GetSceneByName(sceneName);
            if (!scene.isLoaded) return null;
            foreach (var go in scene.GetRootGameObjects())
            {
                var c = go.GetComponent<T>();
                if (c != null) return c;
            }
            Debug.LogError($"[MERIDIAN] SceneDirector: {sceneName} has no {typeof(T).Name} root.");
            return null;
        }
    }
}
