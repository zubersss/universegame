using UnityEngine;

namespace Meridian.Core
{
    /// <summary>
    /// U-088 (Bible §4.2 Feel): the hit-stop clock, pure C#. The game clock pauses PlayerHit when the player is hit
    /// and LanceHit when the player lands a Lance or parry hit; stops that run into each other share one ChainCap,
    /// so no chain ever freezes the game for more than 90 ms. A chain ends after ChainGap of running time.
    /// </summary>
    public sealed class HitStopClock
    {
        public const float PlayerHit = 0.05f, LanceHit = 0.033f, ParryHit = 0.033f;
        public const float ChainCap = 0.09f, ChainGap = 0.25f;

        public bool Stopped => remaining > 0f;
        public float ChainUsed => chainUsed;

        float remaining, chainUsed, sinceStop = ChainGap + 1f;

        public void Request(float seconds)
        {
            if (!Stopped && sinceStop >= ChainGap) chainUsed = 0f;
            float allowed = Mathf.Max(0f, ChainCap - chainUsed);
            remaining = Mathf.Min(Mathf.Max(remaining, seconds), allowed);
        }

        /// <summary>Advances by unscaled `dt`; returns the time scale to apply (0 while stopped, else 1).</summary>
        public float Step(float dt)
        {
            if (remaining > 0f)
            {
                float used = Mathf.Min(dt, remaining);
                remaining -= used;
                chainUsed += used;
                sinceStop = 0f;
                if (remaining < 1e-6f) remaining = 0f;
                return 0f;
            }
            sinceStop += dt;
            return 1f;
        }
    }

    /// <summary>
    /// U-088: the one HitStop in the game (created on the first request, kept across scenes): drives Time.timeScale from
    /// the HitStopClock on unscaled time, and never touches a clock the menu has already paused. No allocation per hit.
    /// </summary>
    public sealed class HitStop : MonoBehaviour
    {
        public static HitStop Instance { get; private set; }
        public readonly HitStopClock Clock = new HitStopClock();
        bool stopping;

        public static void Request(float seconds)
        {
            if (Instance == null)
            {
                if (!Application.isPlaying) return;
                var go = new GameObject("HitStop");
                DontDestroyOnLoad(go);
                Instance = go.AddComponent<HitStop>();
            }
            Instance.Clock.Request(seconds);
        }

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        void OnDestroy()
        {
            if (Instance != this) return;
            if (stopping) Time.timeScale = 1f;
            Instance = null;
        }

        void Update()
        {
            float scale = Clock.Step(Time.unscaledDeltaTime);
            var menu = Meridian.UI.MenuController.Instance;
            if (menu != null && menu.Blocking) { stopping = false; return; } // the pause menu owns the clock
            if (scale <= 0f)
            {
                if (!stopping) { stopping = true; Time.timeScale = 0f; }
            }
            else if (stopping)
            {
                stopping = false;
                Time.timeScale = 1f;
            }
        }
    }
}
