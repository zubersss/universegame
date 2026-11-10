using Meridian.Core;
using Meridian.Player;
using Meridian.Space;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Audio
{
    public enum Sfx { Jump, Land, Dig, Place, UiClick, Boom, Shovel, ClodFall, PackTick, Swish, Chip } // U-150: Boom, U-193: Shovel, U-195: ClodFall, PackTick, U-209: Swish, Chip appended (every older value stays)

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
        /// <summary>U-193 (D-182): the shovel's scoop, for a dig while the shovel is the tool (the Beam keeps `dig`); unset, SfxSynth's placeholder.</summary>
        public AudioClip shovel;
        /// <summary>U-195 (D-183): a scoop's clods landing and the pack's tick as a material arrives; unset, SfxSynth's placeholders (U-198 wires
        /// D-186's recorded samples).</summary>
        public AudioClip clodFall, packTick;
        /// <summary>U-209 (D-196): the dig swing's whoosh, a chip on a contact that does not open the cell (pitched by tier), and the Beam's
        /// hum while its ray runs; unset, SfxSynth's placeholders (U-198 wires the recorded samples).</summary>
        public AudioClip swish, chip, beamHum;
        /// <summary>U-209: the Beam's hum is sounding (independent of the audio device); on within the frame the ray starts.</summary>
        public bool BeamHumOn { get; private set; }
        public const float BeamHumVolume = 0.35f;
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
            beamSource = Source("BeamHum", true); // U-209
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
                digInput = player != null ? player.GetComponent<PlayerRigInput>() : null; // U-209: the Beam's hum follows its stroke
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
            player = null; terrain = null; sideShip = null; digInput = null;
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
        void OnTileChanged(int x, int y, byte oldId, byte newId) =>
            Play(newId != TileId.Air ? Sfx.Place : Meridian.Progress.SkillStats.DigTool == Meridian.Rig.DigTool.Shovel ? Sfx.Shovel : Sfx.Dig);
        void OnBoom() { Play(Sfx.Boom); Rise = 1f; }

        public void Play(Sfx id, float volume = 1f) => Play(id, volume, 1f);

        /// <summary>U-209: a one-shot at a pitch (a chip by its depth tier). The voice's pitch is its own until its next sound.</summary>
        public void Play(Sfx id, float volume, float pitch)
        {
            var clip = id switch
            {
                Sfx.Jump => jump, Sfx.Land => land, Sfx.Dig => dig, Sfx.Place => place, Sfx.Boom => boom != null ? boom : (boom = SfxSynth.BoomClip()),
                Sfx.Shovel => shovel != null ? shovel : (shovel = SfxSynth.ShovelClip()),
                Sfx.ClodFall => clodFall != null ? clodFall : (clodFall = SfxSynth.Clip("clod_fall_placeholder", SfxSynth.ClodFall())),
                Sfx.PackTick => packTick != null ? packTick : (packTick = SfxSynth.Clip("pack_tick_placeholder", SfxSynth.PackTick())),
                Sfx.Swish => swish != null ? swish : (swish = SfxSynth.Clip("swish_placeholder", SfxSynth.Swish())),
                Sfx.Chip => chip != null ? chip : (chip = SfxSynth.Clip("chip_placeholder", SfxSynth.Chip())),
                _ => uiClick,
            };
            LastPlayed = id;
            LastPitch = pitch;
            PlayCount++;
            if (clip == null) return;
            var v = voices[nextVoice];
            nextVoice = (nextVoice + 1) % Voices;
            if (v.pitch != pitch) v.pitch = pitch;
            v.PlayOneShot(clip, volume * SfxLevel);
        }

        /// <summary>The last one-shot's pitch (tests).</summary>
        public float LastPitch { get; private set; } = 1f;

        /// <summary>U-209: the Beam's hum follows the dig stroke: on the frame its ray starts, off when it stops.</summary>
        void StepBeamHum()
        {
            bool on = digInput != null && digInput.isActiveAndEnabled && digInput.Stroke.Phase == DigPhase.Beam;
            if (on == BeamHumOn) return;
            BeamHumOn = on;
            if (beamSource == null) return;
            if (on)
            {
                if (beamSource.clip == null) beamSource.clip = beamHum != null ? beamHum : (beamHum = SfxSynth.Clip("beam_hum_placeholder", SfxSynth.BeamHum()));
                beamSource.volume = BeamHumVolume * SfxLevel;
                beamSource.Play();
            }
            else beamSource.Stop();
        }
        AudioSource beamSource;
        PlayerRigInput digInput;

        void Update()
        {
            bool spaceThrust = ship != null && ship.isActiveAndEnabled && ship.intent.thrust > 0f && !ship.Destroyed;
            // U-150: the Pilgrim's engine on the planet too (it had none): louder with the throttle and the boost.
            bool sideThrust = sideShip != null && sideShip.isActiveAndEnabled && sideShip.piloted && sideShip.Flight.Throttle > 0.01f;
            bool thrusting = spaceThrust || sideThrust;
            Rise = Mathf.MoveTowards(Rise, 0f, Time.deltaTime / RiseSeconds);
            StepBeamHum();
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
