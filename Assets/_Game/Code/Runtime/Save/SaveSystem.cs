using System;
using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Ship;
using Meridian.Space;
using Meridian.Terrain;
using Meridian.Transitions;
using UnityEngine;

namespace Meridian.Save
{
    /// <summary>
    /// Save/load (Bible §10.7). Slot folder: %USERPROFILE%/AppData/LocalLow/Zubers/MERIDIAN/saves/slot&lt;N&gt;/
    /// (Application.persistentDataPath; company per D-011) with state.json and terrain_&lt;planet&gt;.bin.
    /// Autosaves after every transition and every 5 minutes; keeps 3 rotating backups; writes
    /// atomically; migrates older versions on load.
    /// </summary>
    public sealed class SaveSystem : MonoBehaviour
    {
        public const int Backups = 3;
        public const float AutosaveSeconds = 300f;
        public const string StateFile = "state.json";

        public static SaveSystem Instance { get; private set; }
        /// <summary>Tests point saves at a temporary folder instead of the player's real saves.</summary>
        public static string RootOverride;

        public SceneDirector scenes;
        public TimeSystem time;
        public TransitionDirector transitions;
        public int slot;
        [Tooltip("Seconds between autosaves (Bible §10.7: every 5 minutes).")]
        public float autosaveInterval = AutosaveSeconds;

        public int SaveCount { get; private set; }
        public bool Loading { get; private set; }
        float sinceAutosave;
        double playSeconds;

        public static string Root => RootOverride ?? Path.Combine(Application.persistentDataPath, "saves");
        public string SlotFolder => Path.Combine(Root, "slot" + slot);
        public static string TerrainFile(PlanetId id) => $"terrain_{id.ToString().ToLowerInvariant()}.bin";

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        void OnDestroy() { if (Instance == this) Instance = null; }

        void Start()
        {
            if (scenes == null) scenes = FindAnyObjectByType<SceneDirector>();
            if (time == null) time = FindAnyObjectByType<TimeSystem>();
            if (transitions == null) transitions = FindAnyObjectByType<TransitionDirector>();
            if (transitions != null) transitions.Completed += OnTransitionCompleted;
        }

        void OnTransitionCompleted() { if (!Loading) Save(); }

        void Update()
        {
            playSeconds += Time.unscaledDeltaTime;
            sinceAutosave += Time.unscaledDeltaTime;
            if (sinceAutosave >= autosaveInterval && !Loading && (transitions == null || !transitions.Busy)) Save();
        }

        // ---------- save ----------

        /// <summary>Writes the slot now (after rotating the previous save into the backups).</summary>
        public void Save()
        {
            sinceAutosave = 0f;
            var state = GameState.Instance;
            if (state == null) return;
            var data = Capture(state);
            Directory.CreateDirectory(SlotFolder);
            RotateBackups();
            foreach (var kv in state.AllEdits)
            {
                if (kv.Value.Count == 0) continue;
                var file = TerrainFile(kv.Key);
                kv.Value.SaveFile(Path.Combine(SlotFolder, file));
                data.terrainFiles.Add(file);
            }
            // Drop terrain files of planets whose edits are now empty.
            foreach (var f in Directory.GetFiles(SlotFolder, "terrain_*.bin"))
                if (!data.terrainFiles.Contains(Path.GetFileName(f))) File.Delete(f);
            WriteAtomic(Path.Combine(SlotFolder, StateFile), JsonUtility.ToJson(data, true));
            SaveCount++;
        }

        SaveData Capture(GameState state)
        {
            var data = new SaveData
            {
                savedAtUtc = DateTime.UtcNow.ToString("o"),
                gameVersion = GameInfo.Version,
                worldSeed = state.worldSeed,
                currentPlanet = state.currentPlanet.ToString(),
                view = state.view.ToString(),
            };
            data.ship.hull = state.hull;
            data.ship.fuel = state.fuel;
            data.ship.tankCapacity = state.tankCapacity;
            data.cargo.AddRange(state.cargo);
            data.timers.gameSeconds = time != null ? time.GameSeconds : 0;
            data.timers.playSeconds = playSeconds;

            var side = scenes != null ? scenes.PlanetSide : null;
            if (side != null)
            {
                if (side.player != null)
                {
                    data.player.position = side.player.Body.position;
                    var vitals = side.player.Vitals ?? side.player.GetComponent<Meridian.Player.PlayerVitals>();
                    if (vitals != null) data.player.health = vitals.health;
                }
                if (side.ship != null)
                {
                    data.ship.sidePosition = side.ship.Body.position;
                    data.ship.sideVelocity = side.ship.Body.linearVelocity;
                    var boarding = side.ship.GetComponent<ShipBoarding>();
                    data.player.aboard = boarding != null && boarding.Aboard;
                }
            }
            var spaceShip = scenes != null && scenes.Space != null ? scenes.Space.GetComponentInChildren<SpaceShip>(true) : null;
            if (spaceShip != null)
            {
                data.ship.spacePosition = spaceShip.Position;
                data.ship.spaceVelocity = spaceShip.Velocity;
                data.ship.spaceHeading = spaceShip.Heading;
            }
            return data;
        }

        /// <summary>slot → backup1 → backup2 → backup3 (oldest dropped). Backups live in slotN/backups/k/.</summary>
        void RotateBackups()
        {
            if (!File.Exists(Path.Combine(SlotFolder, StateFile))) return;
            var backups = Path.Combine(SlotFolder, "backups");
            var oldest = Path.Combine(backups, Backups.ToString());
            if (Directory.Exists(oldest)) Directory.Delete(oldest, true);
            for (int k = Backups - 1; k >= 1; k--)
            {
                var from = Path.Combine(backups, k.ToString());
                if (Directory.Exists(from)) Directory.Move(from, Path.Combine(backups, (k + 1).ToString()));
            }
            var first = Path.Combine(backups, "1");
            Directory.CreateDirectory(first);
            foreach (var f in Directory.GetFiles(SlotFolder))
                File.Copy(f, Path.Combine(first, Path.GetFileName(f)), true);
        }

        static void WriteAtomic(string path, string text)
        {
            var tmp = path + ".tmp";
            File.WriteAllText(tmp, text);
            if (File.Exists(path)) File.Replace(tmp, path, null);
            else File.Move(tmp, path);
        }

        // ---------- load ----------

        public bool HasSave => File.Exists(Path.Combine(SlotFolder, StateFile));

        public static SaveData ReadState(string folder)
        {
            var json = File.ReadAllText(Path.Combine(folder, StateFile));
            return SaveMigrations.Migrate(JsonUtility.FromJson<SaveData>(json));
        }

        /// <summary>Restores the slot: GameState, terrain diffs, then the planet or space view with positions.</summary>
        public IEnumerator Load()
        {
            Loading = true;
            var data = ReadState(SlotFolder);
            var state = GameState.Instance;
            state.worldSeed = data.worldSeed;
            state.currentPlanet = Enum.TryParse(data.currentPlanet, out PlanetId p) ? p : PlanetId.Earth;
            state.view = Enum.TryParse(data.view, out ViewMode v) ? v : ViewMode.PlanetSide;
            state.hull = data.ship.hull;
            state.fuel = data.ship.fuel;
            state.tankCapacity = data.ship.tankCapacity;
            state.cargo.Clear();
            state.cargo.AddRange(data.cargo);
            if (time != null) time.SetGameSeconds(data.timers.gameSeconds);
            playSeconds = data.timers.playSeconds;

            state.ClearAllEdits();
            foreach (var file in data.terrainFiles)
            {
                var path = Path.Combine(SlotFolder, file);
                var name = file.Substring("terrain_".Length, file.Length - "terrain_".Length - ".bin".Length);
                foreach (PlanetId id in Enum.GetValues(typeof(PlanetId)))
                    if (id.ToString().ToLowerInvariant() == name && File.Exists(path)) state.EditsFor(id).LoadFile(path);
            }

            var config = state.CurrentPlanetConfig;
            if (state.view == ViewMode.PlanetSide)
            {
                if (scenes.Space != null) scenes.Space.gameObject.SetActive(false);
                yield return scenes.LoadPlanetSide(config);
                PlaceSideBodies(scenes.PlanetSide, data);
            }
            else
            {
                if (scenes.PlanetSide != null) scenes.PlanetSide.gameObject.SetActive(false);
                scenes.UnloadPlanetSide();
                scenes.SetView(ViewMode.Space);
                var ship = scenes.Space.GetComponentInChildren<SpaceShip>(true);
                ship.Position = data.ship.spacePosition;
                ship.Velocity = data.ship.spaceVelocity;
                ship.Heading = data.ship.spaceHeading;
            }
            sinceAutosave = 0f;
            Loading = false;
        }

        static void PlaceSideBodies(PlanetSideRoot side, SaveData data)
        {
            if (side == null) return;
            if (side.ship != null)
            {
                side.ship.Body.position = data.ship.sidePosition;
                side.ship.transform.position = data.ship.sidePosition;
                side.ship.Body.linearVelocity = data.ship.sideVelocity;
            }
            if (side.player != null)
            {
                side.player.Body.position = data.player.position;
                side.player.transform.position = data.player.position;
                side.player.Body.linearVelocity = Vector2.zero;
                var vitals = side.player.GetComponent<Meridian.Player.PlayerVitals>();
                if (vitals != null) vitals.health = data.player.health;
                if (data.player.aboard && side.ship != null)
                {
                    var boarding = side.ship.GetComponent<ShipBoarding>();
                    if (boarding != null) boarding.ForceAboard();
                }
            }
            var cam = side.sideCamera;
            if (cam != null)
            {
                var target = data.player.aboard ? data.ship.sidePosition : data.player.position;
                cam.transform.position = new Vector3(target.x, target.y + 1.5f, cam.transform.position.z);
            }
        }
    }
}
