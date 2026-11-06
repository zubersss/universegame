using UnityEngine;

namespace Meridian.Core
{
    /// <summary>
    /// U-095: player settings that persist across runs (PlayerPrefs; a settings panel arrives with its own card). The
    /// film effects toggle (default on) is the first.
    /// </summary>
    public static class GameSettings
    {
        public const string FilmKey = "meridian.settings.film";
        static bool? film;

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

        /// <summary>Drops the cached values so the next read comes from PlayerPrefs (tests).</summary>
        public static void Reload() => film = null;
    }
}
