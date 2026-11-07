using UnityEngine;

namespace Meridian.Core
{
    /// <summary>
    /// U-095 / U-102: player settings that persist across runs (PlayerPrefs). The film effects toggle (default on), the
    /// master / music / SFX volumes (0..1, stepped by the settings panel in tenths) and the language (one language until
    /// localisation exists: a placeholder the panel shows, never stored).
    /// </summary>
    public static class GameSettings
    {
        public const string FilmKey = "meridian.settings.film";
        public const string MasterKey = "meridian.settings.master", MusicKey = "meridian.settings.music", SfxKey = "meridian.settings.sfx";
        /// <summary>The defaults a fresh install starts from: the mix as tuned (AudioDirector's own levels at full).</summary>
        public const float DefaultMaster = 1f, DefaultMusic = 1f, DefaultSfx = 1f;
        /// <summary>One press of − / + on the settings panel.</summary>
        public const float VolumeStep = 0.1f;
        /// <summary>The one language until localisation exists (U-102's placeholder row).</summary>
        public const string Language = "English";

        static bool? film;
        static float? master, music, sfx;

        /// <summary>Raised after any setting changes.</summary>
        public static event System.Action Changed;

        /// <summary>Bible §9.4: the film pass (grain, vignette, dust, scratches, flicker, grade). Default on.</summary>
        public static bool FilmEffects
        {
            get { if (!film.HasValue) film = PlayerPrefs.GetInt(FilmKey, 1) != 0; return film.Value; }
            set
            {
                if (film.HasValue && film.Value == value) return;
                film = value;
                PlayerPrefs.SetInt(FilmKey, value ? 1 : 0);
                PlayerPrefs.Save();
                Changed?.Invoke();
            }
        }

        /// <summary>Everything the game plays (AudioListener.volume).</summary>
        public static float MasterVolume { get => Read(ref master, MasterKey, DefaultMaster); set => Write(ref master, MasterKey, value); }
        /// <summary>The music and ambient beds.</summary>
        public static float MusicVolume { get => Read(ref music, MusicKey, DefaultMusic); set => Write(ref music, MusicKey, value); }
        /// <summary>The one-shots and the thrust loop.</summary>
        public static float SfxVolume { get => Read(ref sfx, SfxKey, DefaultSfx); set => Write(ref sfx, SfxKey, value); }

        /// <summary>A volume as the panel prints it: "70%".</summary>
        public static string Percent(float v) => Mathf.RoundToInt(Mathf.Clamp01(v) * 100f) + "%";

        /// <summary>One step up or down, clamped to 0..1 and kept on the tenths (no 0.30000001 drift after many presses).</summary>
        public static float Stepped(float v, int steps) => Mathf.Clamp01(Mathf.Round((v + steps * VolumeStep) * 10f) / 10f);

        static float Read(ref float? cache, string key, float fallback)
        {
            if (!cache.HasValue) cache = Mathf.Clamp01(PlayerPrefs.GetFloat(key, fallback));
            return cache.Value;
        }

        static void Write(ref float? cache, string key, float value)
        {
            value = Mathf.Clamp01(value);
            if (cache.HasValue && Mathf.Approximately(cache.Value, value)) return;
            cache = value;
            PlayerPrefs.SetFloat(key, value);
            PlayerPrefs.Save();
            Changed?.Invoke();
        }

        /// <summary>Drops the cached values so the next read comes from PlayerPrefs (tests; a restart reads the same way).</summary>
        public static void Reload() { film = null; master = null; music = null; sfx = null; }
    }
}
