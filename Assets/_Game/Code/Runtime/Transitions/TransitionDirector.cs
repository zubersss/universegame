using System.Collections;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Ship;
using Meridian.Space;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Meridian.Transitions
{
    /// <summary>
    /// Side ↔ top-down transitions (Bible §5.2, §5.3). Launch: Escape Line crossed going up → input
    /// lock and camera ease-out (0.3 s), fade through white (0.5 s), PlanetSide unloads, ship on the
    /// Atmosphere Ring at its longitude + the planet's rotation, 20 u/s outward, 1 s invulnerable.
    /// Entry: inward ring crossing or F held inside the ring → push in and fade (0.8 s), PlanetSide
    /// loads at longitude = angle − rotation, ship at Escape Line + 20 m descending 15 m/s.
    /// Hull, fuel and cargo stay in GameState throughout (never re-read from disk).
    /// </summary>
    public sealed class TransitionDirector : MonoBehaviour
    {
        public const float LaunchLock = 0.3f, LaunchFade = 0.5f, LaunchReveal = 0.25f; // total 1.05 s ≤ 1.5 s
        public const float EntryFade = 0.8f, EntryReveal = 0.3f;
        public const float RingOutwardSpeed = 20f;
        public const float InvulnerableSeconds = 1f;
        public const float EnterHoldSeconds = 0.5f;
        public const float SideZoomOut = 14f, SpaceDefaultSize = 60f, SpacePushIn = 20f;

        public SceneDirector scenes;
        public TimeSystem time;
        public InputActionAsset actions;

        public bool Busy { get; private set; }
        public float LastLaunchSeconds { get; private set; }
        public float LastEntrySeconds { get; private set; }
        public float LastLaunchAngle { get; private set; }
        public float LastEntryAngle { get; private set; }
        /// <summary>Ship state at the instant of the launch placement (before any physics step).</summary>
        public Vector2 LaunchPlacement { get; private set; }
        public Vector2 LaunchVelocity { get; private set; }
        public BodyInfo? LaunchBody { get; private set; }

        SideShip sideShip;
        SpaceShip spaceShip;
        Image fade;
        float[] prevDistance;
        float enterHeld;
        InputAction enterAction;

        GameState State => scenes != null ? scenes.gameState : GameState.Instance;

        void Awake()
        {
            var canvasGo = new GameObject("TransitionFade");
            canvasGo.transform.SetParent(transform, false);
            var canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 1000;
            var imgGo = new GameObject("White");
            imgGo.transform.SetParent(canvasGo.transform, false);
            fade = imgGo.AddComponent<Image>();
            fade.color = new Color(1f, 1f, 1f, 0f);
            fade.raycastTarget = false;
            var rt = fade.rectTransform;
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one;
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            fade.enabled = false;
        }

        void Start()
        {
            if (scenes == null) scenes = FindAnyObjectByType<SceneDirector>();
            if (time == null) time = FindAnyObjectByType<TimeSystem>();
            if (actions == null) actions = MeridianInput.Build();
            enterAction = actions.FindActionMap(MeridianInput.ShipTop, true).FindAction("Enter");
            actions.FindActionMap(MeridianInput.ShipTop).Enable();
            scenes.PlanetSideLoaded += HookSide;
            if (scenes.IsReady) HookAll(); else scenes.Ready += HookAll;
        }

        void OnDestroy()
        {
            if (scenes != null) { scenes.PlanetSideLoaded -= HookSide; scenes.Ready -= HookAll; }
            if (sideShip != null) sideShip.EscapeLineCrossed -= OnEscapeLine;
        }

        void HookAll()
        {
            HookSide();
            if (scenes.Space != null) spaceShip = scenes.Space.GetComponentInChildren<SpaceShip>(true);
        }

        void HookSide()
        {
            if (sideShip != null) sideShip.EscapeLineCrossed -= OnEscapeLine;
            sideShip = scenes.PlanetSide != null ? scenes.PlanetSide.ship : null;
            if (sideShip != null) sideShip.EscapeLineCrossed += OnEscapeLine;
        }

        void OnEscapeLine()
        {
            if (!Busy && State.view == ViewMode.PlanetSide) StartCoroutine(Launch());
        }

        public static float RotationDegrees(TimeSystem t, PlanetConfig p) => t != null ? t.DayFraction(p) * 360f : 0f;

        /// <summary>Longitude (deg) of a tile column: x / width × 360.</summary>
        public static float Longitude(float x, int width) => Mathf.Repeat(x / width * 360f, 360f);

        /// <summary>Tile column under a longitude (deg).</summary>
        public static int ColumnAt(float longitudeDeg, int width) =>
            Mathf.Clamp(Mathf.FloorToInt(Mathf.Repeat(longitudeDeg, 360f) / 360f * width), 0, width - 1);

        // ---------- launch (§5.2) ----------

        IEnumerator Launch()
        {
            Busy = true;
            float t0 = Time.realtimeSinceStartup;
            var side = scenes.PlanetSide;
            var planet = side.Config;
            var cam = side.sideCamera;
            sideShip.SetPiloted(false); // input locked

            float startSize = cam.orthographicSize;
            for (float t = 0f; t < LaunchLock; t += Time.unscaledDeltaTime)
            {
                cam.orthographicSize = Mathf.Lerp(startSize, SideZoomOut, t / LaunchLock);
                yield return null;
            }
            yield return Fade(0f, 1f, LaunchFade);

            float angle = Longitude(sideShip.Body.position.x, planet.worldWidth) + RotationDegrees(time, planet);
            var body = FindBody(planet.id);
            sideShip.EscapeLineCrossed -= OnEscapeLine;
            sideShip = null;
            side.gameObject.SetActive(false); // its global 2D light goes now, not when the async unload ends
            scenes.UnloadPlanetSide(); // finishes in the background; nothing waits on it
            scenes.SetView(ViewMode.Space);

            if (spaceShip == null) spaceShip = scenes.Space.GetComponentInChildren<SpaceShip>(true);
            if (body.HasValue) spaceShip.PlaceOnRing(body.Value, angle, RingOutwardSpeed, InvulnerableSeconds);
            LaunchPlacement = spaceShip.Position;
            LaunchVelocity = spaceShip.Velocity;
            LaunchBody = body;
            LastLaunchAngle = Mathf.Repeat(angle, 360f);
            var spaceCam = scenes.Space.GetComponentInChildren<Camera>();
            if (spaceCam != null) spaceCam.orthographicSize = SpaceDefaultSize;
            ResetCrossings();

            yield return Fade(1f, 0f, LaunchReveal);
            LastLaunchSeconds = Time.realtimeSinceStartup - t0;
            Busy = false;
        }

        // ---------- entry (§5.3) ----------

        void Update()
        {
            if (Busy || State == null || State.view != ViewMode.Space || spaceShip == null || spaceShip.world == null) return;
            var bodies = spaceShip.world.Bodies;
            if (prevDistance == null || prevDistance.Length != bodies.Count) ResetCrossings();
            bool holdingEnter = !spaceShip.externalInput && enterAction != null && enterAction.IsPressed();
            enterHeld = holdingEnter ? enterHeld + Time.unscaledDeltaTime : 0f;

            for (int i = 0; i < bodies.Count; i++)
            {
                var b = bodies[i];
                if (!b.landable) continue;
                var offset = spaceShip.Position - b.position;
                float d = offset.magnitude;
                float radial = Vector2.Dot(spaceShip.Velocity, offset / Mathf.Max(d, 1e-4f));
                bool crossedIn = prevDistance[i] > b.RingRadius && d <= b.RingRadius && radial < 0f;
                bool heldInside = d <= b.RingRadius && enterHeld >= EnterHoldSeconds;
                prevDistance[i] = d;
                if ((crossedIn || heldInside) && !spaceShip.Invulnerable)
                {
                    StartCoroutine(Enter(b));
                    return;
                }
            }
        }

        /// <summary>Tests and tools: begin an entry into a body now (as if its ring were crossed).</summary>
        public void BeginEntry(BodyInfo body)
        {
            if (!Busy) StartCoroutine(Enter(body));
        }

        IEnumerator Enter(BodyInfo body)
        {
            Busy = true;
            float t0 = Time.realtimeSinceStartup;
            var spaceCam = scenes.Space.GetComponentInChildren<Camera>();
            float startSize = spaceCam != null ? spaceCam.orthographicSize : SpaceDefaultSize;
            var offset = spaceShip.Position - body.position;
            float angle = Mathf.Atan2(offset.y, offset.x) * Mathf.Rad2Deg;
            spaceShip.Velocity = Vector2.zero;

            // Heat shimmer stand-in: the fade starts warm and goes white (fx/heat_shimmer arrives with B-012 polish).
            for (float t = 0f; t < EntryFade; t += Time.unscaledDeltaTime)
            {
                float k = t / EntryFade;
                if (spaceCam != null) spaceCam.orthographicSize = Mathf.Lerp(startSize, SpacePushIn, k);
                fade.enabled = true;
                fade.color = new Color(1f, Mathf.Lerp(0.75f, 1f, k), Mathf.Lerp(0.5f, 1f, k), k);
                yield return null;
            }
            fade.color = Color.white;

            var config = State.catalog.Get(body.planet);
            float longitude = angle - RotationDegrees(time, config);
            int x = ColumnAt(longitude, config.worldWidth);
            LastEntryAngle = Mathf.Repeat(angle, 360f);
            State.currentPlanet = body.planet;
            State.view = ViewMode.PlanetSide;
            scenes.Space.gameObject.SetActive(false); // before PlanetSide loads: one global 2D light at a time
            if (spaceCam != null) spaceCam.orthographicSize = SpaceDefaultSize;
            yield return scenes.LoadPlanetSide(config, x);

            yield return Fade(1f, 0f, EntryReveal);
            LastEntrySeconds = Time.realtimeSinceStartup - t0;
            Busy = false;
        }

        // ---------- helpers ----------

        IEnumerator Fade(float from, float to, float seconds)
        {
            fade.enabled = true;
            for (float t = 0f; t < seconds; t += Time.unscaledDeltaTime)
            {
                fade.color = new Color(1f, 1f, 1f, Mathf.Lerp(from, to, t / seconds));
                yield return null;
            }
            fade.color = new Color(1f, 1f, 1f, to);
            fade.enabled = to > 0f;
        }

        BodyInfo? FindBody(PlanetId id)
        {
            if (spaceShip == null) spaceShip = scenes.Space.GetComponentInChildren<SpaceShip>(true);
            var world = spaceShip != null ? spaceShip.world : null;
            if (world == null) return null;
            foreach (var b in world.Bodies) if (b.landable && b.planet == id) return b;
            return null;
        }

        void ResetCrossings()
        {
            var bodies = spaceShip != null && spaceShip.world != null ? spaceShip.world.Bodies : null;
            if (bodies == null) return;
            prevDistance = new float[bodies.Count];
            for (int i = 0; i < bodies.Count; i++) prevDistance[i] = Vector2.Distance(spaceShip.Position, bodies[i].position);
        }
    }
}
