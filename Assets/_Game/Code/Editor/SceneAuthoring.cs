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
            var spaceCam = AddCamera(spaceRoot.transform, "SpaceCamera", 60f, new Color(0.01f, 0.01f, 0.02f), false);
            spaceCam.transform.localPosition = new Vector3(0f, 0f, -50f);
            AddGlobalLight(spaceRoot.transform);

            var worldGo = new GameObject("SpaceWorld");
            worldGo.transform.SetParent(spaceRoot.transform, false);
            var world = worldGo.AddComponent<Meridian.Space.SpaceWorld>();
            world.catalog = catalog;
            world.discMaterial = EnsureMaterial(PlanetDiscMaterialPath, "MERIDIAN/PlanetDisc");
            world.lineMaterial = AssetDatabase.LoadAssetAtPath<Material>(
                "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Unlit-Default.mat");

            var shipGo = new GameObject("Ship");
            shipGo.transform.SetParent(spaceRoot.transform, false);
            var ship = shipGo.AddComponent<Meridian.Space.SpaceShip>();
            ship.world = world;
            if (!System.IO.File.Exists(InputAuthoring.AssetPath)) InputAuthoring.Run();
            ship.actions = AssetDatabase.LoadAssetAtPath<UnityEngine.InputSystem.InputActionAsset>(InputAuthoring.AssetPath);
            var shipView = new GameObject("View");
            shipView.transform.SetParent(shipGo.transform, false);
            var sr = shipView.AddComponent<SpriteRenderer>();
            sr.sortingOrder = 20;
            var addr = shipGo.AddComponent<Meridian.Art.AddressableSprite>();
            addr.key = Meridian.Art.ArtKeys.Ships.PilgrimTop;
            addr.target = sr;
            addr.worldWidth = 4f;
            spaceCam.gameObject.AddComponent<Meridian.Space.SpaceCamera>().target = shipGo.transform;
            var hudGo = new GameObject("SpaceHud");
            hudGo.transform.SetParent(spaceRoot.transform, false);
            hudGo.AddComponent<Meridian.Space.SpaceHud>().ship = ship;
            EditorSceneManager.SaveScene(space, SpacePath);

            // PlanetSide (one scene for all planets)
            var side = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var sideRoot = new GameObject("PlanetSideRoot");
            var sideComp = sideRoot.AddComponent<PlanetSideRoot>();
            sideComp.sideCamera = AddCamera(sideRoot.transform, "SideCamera", 9f, new Color(0.45f, 0.62f, 0.85f), true);
            var terrainGo = new GameObject("Terrain");
            terrainGo.transform.SetParent(sideRoot.transform, false);
            terrainGo.AddComponent<Grid>();
            sideComp.terrain = terrainGo.AddComponent<Meridian.Terrain.TerrainStreamer>();
            var rigGo = new GameObject("Rig");
            rigGo.transform.SetParent(sideRoot.transform, false);
            sideComp.rig = rigGo.AddComponent<Meridian.Rig.RigTools>();
            sideComp.rig.terrain = sideComp.terrain;
            sideComp.rig.drops = rigGo.AddComponent<Meridian.Rig.ItemDrops>();

            // Player: body + view + Rig input; the camera follows it.
            if (!System.IO.File.Exists(InputAuthoring.AssetPath)) InputAuthoring.Run();
            var input = AssetDatabase.LoadAssetAtPath<UnityEngine.InputSystem.InputActionAsset>(InputAuthoring.AssetPath);
            var playerGo = new GameObject("Player");
            playerGo.transform.SetParent(sideRoot.transform, false);
            playerGo.AddComponent<Rigidbody2D>();
            playerGo.AddComponent<CapsuleCollider2D>();
            playerGo.AddComponent<Meridian.Player.PlayerVitals>();
            var pc = playerGo.AddComponent<Meridian.Player.PlayerController>();
            pc.actions = input;
            sideComp.player = pc;
            var viewGo = new GameObject("View");
            viewGo.transform.SetParent(playerGo.transform, false);
            var pv = playerGo.AddComponent<Meridian.Player.PlayerView>();
            pv.controller = pc;
            pv.view = viewGo.AddComponent<SpriteRenderer>();
            pv.view.sortingOrder = 10;
            var ri = playerGo.AddComponent<Meridian.Player.PlayerRigInput>();
            ri.controller = pc;
            ri.rig = sideComp.rig;
            ri.view = sideComp.sideCamera;
            sideComp.rig.owner = playerGo.transform;
            var follow = sideComp.sideCamera.gameObject.AddComponent<Meridian.Player.CameraFollow>();
            follow.target = playerGo.transform;

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

        static Camera AddCamera(Transform parent, string name, float size, Color background, bool listener)
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
            return cam;
        }

        public const string PlanetDiscMaterialPath = "Assets/_Game/Settings/Materials/PlanetDisc.mat";

        static Material EnsureMaterial(string path, string shaderName)
        {
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat != null) return mat;
            System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path));
            mat = new Material(Shader.Find(shaderName)) { name = System.IO.Path.GetFileNameWithoutExtension(path) };
            AssetDatabase.CreateAsset(mat, path);
            return mat;
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
