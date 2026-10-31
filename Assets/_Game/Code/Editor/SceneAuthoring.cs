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
            if (!System.IO.File.Exists(AudioSynth.PathOf("jump"))) AudioSynth.Run();
            var audioGo = new GameObject("AudioDirector");
            var audio = audioGo.AddComponent<Meridian.Audio.AudioDirector>();
            audioGo.AddComponent<AudioListener>(); // the one listener, in Core, alive through every load and view
            audio.scenes = director;
            audio.jump = Clip("jump"); audio.land = Clip("land"); audio.dig = Clip("dig"); audio.place = Clip("place");
            audio.uiClick = Clip("ui_click"); audio.thrust = Clip("thrust"); audio.ambient = Clip(AudioSynth.Ambient);
            InputAuthoring.Run(); // keep the .inputactions asset identical to MeridianInput.Build()
            var transitions = coreGo.AddComponent<Meridian.Transitions.TransitionDirector>();
            transitions.scenes = director;
            transitions.time = coreGo.GetComponent<TimeSystem>();
            transitions.actions = AssetDatabase.LoadAssetAtPath<UnityEngine.InputSystem.InputActionAsset>(InputAuthoring.AssetPath);
            var save = coreGo.AddComponent<Meridian.Save.SaveSystem>();
            save.scenes = director;
            save.time = coreGo.GetComponent<TimeSystem>();
            save.transitions = transitions;
            coreGo.AddComponent<Meridian.Perf.BudgetMonitor>();
            coreGo.AddComponent<BuildSmoke>().scenes = director;
            EnsureUiTheme();
            var menu = coreGo.AddComponent<Meridian.UI.MenuController>();
            menu.actions = transitions.actions;
            menu.save = save;
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
            var backdrop = spaceCam.gameObject.AddComponent<Meridian.Space.SpaceBackdrop>();
            backdrop.view = spaceCam;
            backdrop.layerMaterial = EnsureMaterial("Assets/_Game/Settings/Materials/ParallaxLayer.mat", "MERIDIAN/ParallaxLayer");
            var hudGo = new GameObject("SpaceHud");
            hudGo.transform.SetParent(spaceRoot.transform, false);
            hudGo.AddComponent<Meridian.Space.SpaceHud>().ship = ship;
            EditorSceneManager.SaveScene(space, SpacePath);

            // PlanetSide (one scene for all planets)
            var side = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var sideRoot = new GameObject("PlanetSideRoot");
            var sideComp = sideRoot.AddComponent<PlanetSideRoot>();
            sideComp.sideCamera = AddCamera(sideRoot.transform, "SideCamera", 9f, new Color(0.45f, 0.62f, 0.85f), false);
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
            pv.rig = sideComp.rig;      // U-032: dig clip and aim facing
            pv.rigInput = ri;
            var follow = sideComp.sideCamera.gameObject.AddComponent<Meridian.Player.CameraFollow>();
            follow.target = playerGo.transform;

            // Pilgrim (prefab) + boarding, Escape Line band, ship HUD (U-010).
            var shipPrefab = EnsurePilgrimPrefab(input);
            var pilgrimGo = (GameObject)PrefabUtility.InstantiatePrefab(shipPrefab, side);
            pilgrimGo.transform.SetParent(sideRoot.transform, false);
            sideComp.ship = pilgrimGo.GetComponent<Meridian.Ship.SideShip>();
            var boarding = pilgrimGo.AddComponent<Meridian.Ship.ShipBoarding>();
            boarding.ship = sideComp.ship;
            boarding.player = pc;
            boarding.cameraFollow = follow;

            var bandGo = new GameObject("EscapeLine");
            bandGo.transform.SetParent(sideRoot.transform, false);
            var band = bandGo.AddComponent<Meridian.Ship.EscapeLineBand>();
            band.view = sideComp.sideCamera;
            var bandView = new GameObject("Band");
            bandView.transform.SetParent(bandGo.transform, false);
            band.band = bandView.AddComponent<SpriteRenderer>();
            band.band.drawMode = SpriteDrawMode.Tiled;
            band.band.color = new Color(0.6f, 0.85f, 1f, 0.25f);
            band.band.sortingOrder = 30;
            var bandArt = bandGo.AddComponent<Meridian.Art.AddressableSprite>();
            bandArt.key = Meridian.Art.ArtKeys.Fx.EscapeBand;
            bandArt.target = band.band;
            var labelGo = new GameObject("Label");
            labelGo.transform.SetParent(bandGo.transform, false);
            band.label = labelGo.AddComponent<TextMesh>();
            band.label.text = "ESCAPE";
            band.label.font = AssetDatabase.LoadAssetAtPath<Font>("Assets/_Game/UI/Fonts/JetBrainsMono-Regular.ttf");
            labelGo.GetComponent<MeshRenderer>().sharedMaterial = band.label.font.material;
            labelGo.GetComponent<MeshRenderer>().sortingOrder = 31;
            band.label.fontSize = 48;
            band.label.characterSize = 0.08f;
            band.label.anchor = TextAnchor.MiddleCenter;
            band.label.color = new Color(0.7f, 0.9f, 1f, 0.6f);
            sideComp.escapeBand = band;

            var shipHudGo = new GameObject("ShipHud");
            shipHudGo.transform.SetParent(sideRoot.transform, false);
            var shipHud = shipHudGo.AddComponent<Meridian.Ship.ShipHud>();
            shipHud.ship = sideComp.ship;
            shipHud.boarding = boarding;
            sideComp.shipHud = shipHud;
            var sideHudGo = new GameObject("SideHud");
            sideHudGo.transform.SetParent(sideRoot.transform, false);
            var sideHud = sideHudGo.AddComponent<Meridian.UI.SideHud>();
            sideHud.player = pc;
            sideHud.ship = sideComp.ship;
            sideHud.boarding = boarding;
            sideComp.sideHud = sideHud;
            var planetBackdrop = sideComp.sideCamera.gameObject.AddComponent<Meridian.Planet.PlanetBackdrop>();
            planetBackdrop.view = sideComp.sideCamera;
            planetBackdrop.terrain = sideComp.terrain;
            planetBackdrop.layerMaterial = EnsureMaterial("Assets/_Game/Settings/Materials/SideParallax.mat", "MERIDIAN/SideParallax");
            sideComp.backdrop = planetBackdrop;

            var sideAmbient = AddGlobalLight(sideRoot.transform);
            var dayNight = sideRoot.AddComponent<Meridian.Planet.Lighting.DayNightLighting>();
            dayNight.ambient = sideAmbient;
            dayNight.sun = AddSunLight(sideRoot.transform);
            dayNight.view = sideComp.sideCamera;
            dayNight.backdrop = planetBackdrop;
            sideComp.dayNight = dayNight;
            var dustStorm = sideRoot.AddComponent<Meridian.Planet.Weather.DustStorm>();
            dustStorm.view = sideComp.sideCamera;
            dustStorm.focus = pc.transform;
            dustStorm.dayNight = dayNight;
            dustStorm.fogMaterial = EnsureMaterial("Assets/_Game/Settings/Materials/DustFog.mat", "MERIDIAN/DustFog");
            sideComp.dustStorm = dustStorm;
            sideHud.storm = dustStorm;
            var creaturesGo = new GameObject("Creatures");
            creaturesGo.transform.SetParent(sideRoot.transform, false);
            var creatures = creaturesGo.AddComponent<Meridian.Creatures.CreatureDirector>();
            creatures.terrain = sideComp.terrain;
            creatures.player = pc;
            creatures.dayNight = dayNight;
            sideComp.creatures = creatures;
            var hazards = sideRoot.AddComponent<Meridian.Hazards.HazardSystem>();
            hazards.body = pc.transform;
            hazards.vitals = pc.GetComponent<Meridian.Player.PlayerVitals>();
            hazards.boarding = boarding;
            hazards.terrain = sideComp.terrain;
            hazards.dayNight = dayNight;
            hazards.storm = dustStorm;
            sideComp.hazards = hazards;
            sideHud.hazards = hazards;
            var poisGo = new GameObject("POIs");
            poisGo.transform.SetParent(sideRoot.transform, false);
            var pois = poisGo.AddComponent<Meridian.Planet.POI.PoiPlacer>();
            pois.view = sideComp.sideCamera;
            sideComp.pois = pois;
            sideHud.pois = pois;
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

        public const string UiThemePath = "Assets/_Game/UI/Resources/UiTheme.asset";

        /// <summary>UI theme with the OFL JetBrains Mono fonts (Bible §9).</summary>
        static void EnsureUiTheme()
        {
            var theme = AssetDatabase.LoadAssetAtPath<Meridian.UI.UiTheme>(UiThemePath);
            if (theme == null)
            {
                System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(UiThemePath));
                theme = ScriptableObject.CreateInstance<Meridian.UI.UiTheme>();
                AssetDatabase.CreateAsset(theme, UiThemePath);
            }
            theme.regular = AssetDatabase.LoadAssetAtPath<Font>("Assets/_Game/UI/Fonts/JetBrainsMono-Regular.ttf");
            theme.bold = AssetDatabase.LoadAssetAtPath<Font>("Assets/_Game/UI/Fonts/JetBrainsMono-Bold.ttf");
            EditorUtility.SetDirty(theme);
            AssetDatabase.SaveAssets();
        }

        public const string PilgrimPrefabPath = "Assets/_Game/Prefabs/Ship/Pilgrim.prefab";

        /// <summary>Pilgrim side-view prefab: body, collider, SideShip, sprite view by asset key. Rebuilt each run.</summary>
        static GameObject EnsurePilgrimPrefab(UnityEngine.InputSystem.InputActionAsset input)
        {
            System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(PilgrimPrefabPath));
            var root = new GameObject("Pilgrim");
            root.AddComponent<Rigidbody2D>();
            root.AddComponent<BoxCollider2D>();
            var ship = root.AddComponent<Meridian.Ship.SideShip>();
            ship.actions = input;
            var view = new GameObject("View");
            view.transform.SetParent(root.transform, false);
            var sr = view.AddComponent<SpriteRenderer>();
            sr.sortingOrder = 8;
            root.AddComponent<Meridian.Hazards.WarmthSource>().radius = 6f; // U-029: the ship keeps the cold off nearby
            var legsView = root.AddComponent<Meridian.Ship.ShipLegsView>();
            legsView.ship = ship;
            legsView.target = sr;
            var prefab = PrefabUtility.SaveAsPrefabAsset(root, PilgrimPrefabPath);
            Object.DestroyImmediate(root);
            return prefab;
        }

        static AudioClip Clip(string name) => AssetDatabase.LoadAssetAtPath<AudioClip>(AudioSynth.PathOf(name));

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

        static Light2D AddGlobalLight(Transform parent)
        {
            var go = new GameObject("GlobalLight2D");
            go.transform.SetParent(parent, false);
            var light = go.AddComponent<Light2D>();
            light.lightType = Light2D.LightType.Global;
            light.intensity = 1f;
            return light;
        }

        /// <summary>U-025: the Sun as a far point light (Bible §10.5). Radius covers the view from SunDistance; no falloff; normal maps on.</summary>
        static Light2D AddSunLight(Transform parent)
        {
            var go = new GameObject("SunLight2D");
            go.transform.SetParent(parent, false);
            var light = go.AddComponent<Light2D>();
            light.lightType = Light2D.LightType.Point;
            float r = Meridian.Planet.Lighting.DayNightLighting.SunDistance + 40f;
            light.pointLightInnerRadius = r;
            light.pointLightOuterRadius = r;
            light.falloffIntensity = 0f;
            light.shadowsEnabled = false;
            light.volumetricEnabled = false;
            // Normal-map quality and distance have no runtime setters: set the serialized fields.
            var so = new SerializedObject(light);
            so.FindProperty("m_NormalMapQuality").intValue = (int)Light2D.NormalMapQuality.Fast; // Accurate cost ~+1 ms p99 on Intel UHD (BudgetGate red)
            so.FindProperty("m_NormalMapDistance").floatValue = 30f;
            var useNormal = so.FindProperty("m_UseNormalMap");
            if (useNormal != null) useNormal.boolValue = true;
            so.ApplyModifiedPropertiesWithoutUndo();
            return light;
        }
    }
}
