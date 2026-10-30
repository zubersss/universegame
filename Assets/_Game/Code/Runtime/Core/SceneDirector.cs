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
        public PlanetSideRoot PlanetSide { get; private set; }
        public event Action Ready;

        IEnumerator Start()
        {
            if (gameState == null) gameState = GameState.Instance;

            if (!SceneManager.GetSceneByName(SpaceScene).isLoaded)
                yield return SceneManager.LoadSceneAsync(SpaceScene, LoadSceneMode.Additive);
            Space = FindRoot<SpaceRoot>(SpaceScene);
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
        public IEnumerator LoadPlanetSide(PlanetConfig config, int entryX = -1)
        {
            if (config == null)
            {
                Debug.LogError("[MERIDIAN] SceneDirector: no PlanetConfig for the current planet.");
                yield break;
            }
            var scene = SceneManager.GetSceneByName(PlanetSideScene);
            if (!scene.isLoaded)
                yield return SceneManager.LoadSceneAsync(PlanetSideScene, LoadSceneMode.Additive);
            PlanetSide = FindRoot<PlanetSideRoot>(PlanetSideScene);
            if (PlanetSide != null)
            {
                if (entryX >= 0) PlanetSide.ConfigureForEntry(config, entryX);
                else PlanetSide.Configure(config);
                SceneManager.SetActiveScene(SceneManager.GetSceneByName(PlanetSideScene));
                // Warm-up behind the boot cover or the entry fade (U-028): wait for the tile sheets, then render once off-screen.
                float until = Time.realtimeSinceStartup + 1f;
                while (!PlanetSide.terrain.TileSet.IsReady && Time.realtimeSinceStartup < until) yield return null;
                LastPlanetWarmupMs = RenderWarmup.WarmUp(PlanetSide.sideCamera, PlanetSide.terrain.TileSet);
            }
            PlanetSideLoaded?.Invoke();
        }

        /// <summary>Unloads PlanetSide (launch, Bible §5.2). Terrain edits live on in GameState.</summary>
        public AsyncOperation UnloadPlanetSide()
        {
            var scene = SceneManager.GetSceneByName(PlanetSideScene);
            PlanetSide = null;
            return scene.isLoaded ? SceneManager.UnloadSceneAsync(scene) : null;
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
