using Meridian.Core;
using Meridian.Player;
using Meridian.Space;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Audio
{
    public enum Sfx { Jump, Land, Dig, Place, UiClick }

    /// <summary>
    /// Plays the game's sounds (Bible §10.3, Core): pooled one-shot sources, a thrust loop and an
    /// ambient loop. Listens to the player, terrain edits and the top-down ship; UI calls Play(UiClick).
    /// </summary>
    public sealed class AudioDirector : MonoBehaviour
    {
        public static AudioDirector Instance { get; private set; }

        public SceneDirector scenes;
        public AudioClip jump, land, dig, place, uiClick, thrust, ambient;
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

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            for (int i = 0; i < Voices; i++) voices[i] = Source("Voice" + i, false);
            thrustSource = Source("Thrust", true);
            thrustSource.clip = thrust;
            ambientSource = Source("Ambient", true);
            ambientSource.clip = ambient;
            ambientSource.volume = ambientVolume;
        }

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

        void Hook()
        {
            if (scenes.PlanetSide != null)
            {
                player = scenes.PlanetSide.player;
                terrain = scenes.PlanetSide.terrain;
                if (player != null) { player.Jumped += OnJumped; player.Landed += OnLanded; }
                if (terrain != null) terrain.TileChanged += OnTileChanged;
            }
            if (scenes.Space != null) ship = scenes.Space.GetComponentInChildren<SpaceShip>(true);
            if (ambient != null && !ambientSource.isPlaying) ambientSource.Play();
        }

        void OnDestroy()
        {
            if (player != null) { player.Jumped -= OnJumped; player.Landed -= OnLanded; }
            if (terrain != null) terrain.TileChanged -= OnTileChanged;
            if (scenes != null) scenes.Ready -= Hook;
            if (Instance == this) Instance = null;
        }

        void OnJumped() => Play(Sfx.Jump);
        void OnLanded(float impact) { if (impact >= QuietLanding) Play(Sfx.Land, Mathf.Clamp01(impact / 12f)); }
        void OnTileChanged(int x, int y, byte oldId, byte newId) => Play(newId == TileId.Air ? Sfx.Dig : Sfx.Place);

        public void Play(Sfx id, float volume = 1f)
        {
            var clip = id switch
            {
                Sfx.Jump => jump, Sfx.Land => land, Sfx.Dig => dig, Sfx.Place => place, _ => uiClick,
            };
            LastPlayed = id;
            PlayCount++;
            if (clip == null) return;
            var v = voices[nextVoice];
            nextVoice = (nextVoice + 1) % Voices;
            v.PlayOneShot(clip, volume * sfxVolume);
        }

        void Update()
        {
            bool thrusting = ship != null && ship.isActiveAndEnabled && ship.intent.thrust > 0f && !ship.Destroyed;
            if (thrusting != ThrustOn)
            {
                ThrustOn = thrusting;
                if (thrusting && thrust != null) thrustSource.Play(); else thrustSource.Stop();
            }
            if (thrusting) thrustSource.volume = sfxVolume * (ship.intent.boost ? 1f : 0.7f);
        }
    }
}
