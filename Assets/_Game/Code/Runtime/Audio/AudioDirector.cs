using Meridian.Core;
using Meridian.Player;
using Meridian.Space;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Audio
{
    public enum Sfx { Jump, Land, Dig, Place, UiClick, Boom } // U-150: Boom appended (every older value stays)

    /// <summary>
    /// Plays the game's sounds (Bible §10.3, Core): pooled one-shot sources, a thrust loop and an
    /// ambient loop. Listens to the player, terrain edits and the top-down ship; UI calls Play(UiClick).
    /// </summary>
    public sealed class AudioDirector : MonoBehaviour
    {
        public static AudioDirector Instance { get; private set; }

        public SceneDirector scenes;
        public AudioClip jump, land, dig, place, uiClick, thrust, ambient;
        /// <summary>U-150 (D-158 (4)): the sonic boom; unset, SfxSynth's placeholder is built the first time it sounds.</summary>
        public AudioClip boom;
        /// <summary>U-150: after a boom the engine sound rises (louder, higher) and settles back over RiseSeconds.</summary>
        public const float RiseSeconds = 0.6f, RiseVolume = 0.35f, RisePitch = 0.12f;
        /// <summary>U-150: 1 right after a boom, back to 0 over RiseSeconds (tests read it).</summary>
        public float Rise { get; private set; }
        [Range(0f, 1f)] public float sfxVolume = 0.8f, ambientVolume = 0.35f;
        public const int Voices = 8;
        /// <summary>Landings softer than this (m/s) make no sound.</summary>
        public const float QuietLanding = 2f;

        public Sfx LastPlayed { get; private set; }
        public int PlayCount { get; private set; }
        /// <summary>True while the thrust loop should be sounding (independent of the audio device).</summary>
        public bool ThrustOn { get; private set; }

        readonly AudioSource[] voices = new AudioSource[Voices];
        AudioSource thrustSource, ambientSource;
        int nextVoice;
        PlayerController player;
        TerrainStreamer terrain;
        SpaceShip ship;
        Meridian.Ship.SideShip sideShip; // U-150: the Pilgrim on the planet: its engine and its boom

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            for (int i = 0; i < Voices; i++) voices[i] = Source("Voice" + i, false);
            thrustSource = Source("Thrust", true);
            thrustSource.clip = thrust;
            ambientSource = Source("Ambient", true);
            ambientSource.clip = ambient;
            ApplySettings();
            GameSettings.Changed += ApplySettings;
        }

        /// <summary>U-102: the settings panel's volumes. Master is the listener (everything); music scales the ambient bed;
        /// SFX scales the one-shots and the thrust loop on top of the mix levels above.</summary>
        void ApplySettings()
        {
            AudioListener.volume = GameSettings.MasterVolume;
            if (ambientSource != null) ambientSource.volume = ambientVolume * GameSettings.MusicVolume;
        }

        /// <summary>The one-shot level after the SFX setting (tests read it).</summary>
        public float SfxLevel => sfxVolume * GameSettings.SfxVolume;
        /// <summary>The ambient bed's level after the music setting (tests read it).</summary>
        public float AmbientLevel => ambientSource != null ? ambientSource.volume : ambientVolume * GameSettings.MusicVolume;

        AudioSource Source(string name, bool loop)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var s = go.AddComponent<AudioSource>();
            s.playOnAwake = false;
            s.loop = loop;
            s.spatialBlend = 0f; // 2D mix in M1
            return s;
        }

        void Start()
        {
            if (scenes == null) scenes = FindAnyObjectByType<SceneDirector>();
            if (scenes == null) return;
            if (scenes.IsReady) Hook(); else scenes.Ready += Hook;
        }

        // Runs at boot and after every PlanetSide load (entries bring a new player and terrain).
        void Hook()
        {
            scenes.PlanetSideLoaded -= Hook;
            scenes.PlanetSideLoaded += Hook;
            Unhook();
            if (scenes.PlanetSide != null)
            {
                player = scenes.PlanetSide.player;
                terrain = scenes.PlanetSide.terrain;
                if (player != null) { player.Jumped += OnJumped; player.Landed += OnLanded; }
                if (terrain != null) terrain.TileChanged += OnTileChanged;
                sideShip = scenes.PlanetSide.ship;
                if (sideShip != null) sideShip.SoundBarrierBroken += OnBoom;
            }
            if (scenes.Space != null) ship = scenes.Space.GetComponentInChildren<SpaceShip>(true);
            if (ambient != null && !ambientSource.isPlaying) ambientSource.Play();
        }

        void Unhook()
        {
            if (player != null) { player.Jumped -= OnJumped; player.Landed -= OnLanded; }
            if (terrain != null) terrain.TileChanged -= OnTileChanged;
            if (sideShip != null) sideShip.SoundBarrierBroken -= OnBoom;
            player = null; terrain = null; sideShip = null;
        }

        void OnDestroy()
        {
            Unhook();
            GameSettings.Changed -= ApplySettings;
            if (scenes != null) { scenes.Ready -= Hook; scenes.PlanetSideLoaded -= Hook; }
            if (Instance == this) Instance = null;
        }

        void OnJumped() => Play(Sfx.Jump);
        void OnLanded(float impact) { if (impact >= QuietLanding) Play(Sfx.Land, Mathf.Clamp01(impact / 12f)); }
        void OnTileChanged(int x, int y, byte oldId, byte newId) => Play(newId == TileId.Air ? Sfx.Dig : Sfx.Place);
        void OnBoom() { Play(Sfx.Boom); Rise = 1f; }

        public void Play(Sfx id, float volume = 1f)
        {
            var clip = id switch
            {
                Sfx.Jump => jump, Sfx.Land => land, Sfx.Dig => dig, Sfx.Place => place, Sfx.Boom => boom != null ? boom : (boom = SfxSynth.BoomClip()), _ => uiClick,
            };
            LastPlayed = id;
            PlayCount++;
            if (clip == null) return;
            var v = voices[nextVoice];
            nextVoice = (nextVoice + 1) % Voices;
            v.PlayOneShot(clip, volume * SfxLevel);
        }

        void Update()
        {
            bool spaceThrust = ship != null && ship.isActiveAndEnabled && ship.intent.thrust > 0f && !ship.Destroyed;
            // U-150: the Pilgrim's engine on the planet too (it had none): louder with the throttle and the boost.
            bool sideThrust = sideShip != null && sideShip.isActiveAndEnabled && sideShip.piloted && sideShip.Flight.Throttle > 0.01f;
            bool thrusting = spaceThrust || sideThrust;
            Rise = Mathf.MoveTowards(Rise, 0f, Time.deltaTime / RiseSeconds);
            if (thrusting != ThrustOn)
            {
                ThrustOn = thrusting;
                if (thrusting && thrust != null) thrustSource.Play(); else thrustSource.Stop();
            }
            if (spaceThrust) { thrustSource.volume = SfxLevel * (ship.intent.boost ? 1f : 0.7f); thrustSource.pitch = 1f; }
            else if (sideThrust)
            {
                float level = 0.45f + 0.4f * sideShip.Flight.Throttle + 0.15f * sideShip.Boost;
                thrustSource.volume = SfxLevel * level * (1f + RiseVolume * Rise);
                thrustSource.pitch = 1f + 0.08f * sideShip.Boost + RisePitch * Rise;
            }
        }
    }
}
