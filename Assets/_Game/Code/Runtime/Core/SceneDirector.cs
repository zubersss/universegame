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
            if (Space != null) Space.gameObject.SetActive(gameState.view == ViewMode.Space);

            yield return LoadPlanetSide(gameState.CurrentPlanetConfig);

            IsReady = true;
            Ready?.Invoke();
        }

        public IEnumerator LoadPlanetSide(PlanetConfig config)
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
                PlanetSide.Configure(config);
                SceneManager.SetActiveScene(SceneManager.GetSceneByName(PlanetSideScene));
            }
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
