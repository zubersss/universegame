using Meridian.Core;
using Meridian.Planets;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace Meridian.EditorTools
{
    /// <summary>
    /// Builds Core, Space and PlanetSide scenes (U-004) and registers them in Build Settings.
    /// Re-running rebuilds the scene files from scratch.
    /// </summary>
    public static class SceneAuthoring
    {
        public const string Folder = "Assets/_Game/Scenes";
        public const string CorePath = Folder + "/Core.unity";
        public const string SpacePath = Folder + "/Space.unity";
        public const string PlanetSidePath = Folder + "/PlanetSide.unity";

        [MenuItem("MERIDIAN/Author Scenes")]
        public static void Run()
        {
            System.IO.Directory.CreateDirectory(Folder);
            var catalog = AssetDatabase.LoadAssetAtPath<PlanetCatalog>(PlanetConfigAuthoring.CatalogPath);
            if (catalog == null) { PlanetConfigAuthoring.Run(); catalog = AssetDatabase.LoadAssetAtPath<PlanetCatalog>(PlanetConfigAuthoring.CatalogPath); }

            // Core
            var core = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var coreGo = new GameObject("Core");
            var state = coreGo.AddComponent<GameState>();
            state.catalog = catalog;
            coreGo.AddComponent<TimeSystem>();
            var director = coreGo.AddComponent<SceneDirector>();
            director.gameState = state;
            EditorSceneManager.SaveScene(core, CorePath);

            // Space (kept loaded but inactive by SceneDirector)
            var space = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var spaceRoot = new GameObject("SpaceRoot");
            spaceRoot.AddComponent<SpaceRoot>();
            AddCamera(spaceRoot.transform, "SpaceCamera", 60f, new Color(0.01f, 0.01f, 0.02f), false);
            AddGlobalLight(spaceRoot.transform);
            EditorSceneManager.SaveScene(space, SpacePath);

            // PlanetSide (one scene for all planets)
            var side = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var sideRoot = new GameObject("PlanetSideRoot");
            sideRoot.AddComponent<PlanetSideRoot>();
            AddCamera(sideRoot.transform, "SideCamera", 9f, new Color(0.45f, 0.62f, 0.85f), true);
            AddGlobalLight(sideRoot.transform);
            EditorSceneManager.SaveScene(side, PlanetSidePath);

            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(CorePath, true),
                new EditorBuildSettingsScene(SpacePath, true),
                new EditorBuildSettingsScene(PlanetSidePath, true),
            };
            EditorSceneManager.OpenScene(CorePath, OpenSceneMode.Single);
            AssetDatabase.SaveAssets();
            Debug.Log("[MERIDIAN] SceneAuthoring wrote Core, Space, PlanetSide.");
        }

        static void AddCamera(Transform parent, string name, float size, Color background, bool listener)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = new Vector3(0f, 0f, -10f);
            var cam = go.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = size;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = background;
            go.tag = "MainCamera";
            if (listener) go.AddComponent<AudioListener>();
        }

        static void AddGlobalLight(Transform parent)
        {
            var go = new GameObject("GlobalLight2D");
            go.transform.SetParent(parent, false);
            var light = go.AddComponent<Light2D>();
            light.lightType = Light2D.LightType.Global;
            light.intensity = 1f;
        }
    }
}
