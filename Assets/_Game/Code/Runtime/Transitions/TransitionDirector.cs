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
    /// Side ↔ top-down transitions (Bible §5.2, §5.3 v4.1). Launch: the ship's centre crosses the Escape Line going up
    /// under the player's own thrust → the iris closes on it while the player keeps flying (no input lock, no auto-launch,
    /// D-103), PlanetSide unloads, the ship goes on the Atmosphere Ring at its longitude + the planet's rotation, 20 u/s
    /// outward, 1 s invulnerable, and the iris opens with the top-down controls already live (a held key keeps thrusting).
    /// Entry: inward ring crossing or F held inside the ring → the camera pushes in while the iris closes and the player
    /// keeps steering; PlanetSide loads while black at longitude = angle − rotation, the ship upright at Escape Line + 20 m
    /// descending 15 m/s, side controls live on the first visible frame.
    /// Hull and cargo stay in GameState throughout (never re-read from disk).
    /// </summary>
    public sealed class TransitionDirector : MonoBehaviour
    {
        /// <summary>U-096 / U-107: launch = iris-out 0.35 s (still flying) + switch + iris-in 0.35; entry = push-in under the iris-out 0.35 + load + iris-in 0.35.</summary>
        public const float IrisSeconds = IrisMath.Seconds;
        public const float RingOutwardSpeed = 20f;
        public const float InvulnerableSeconds = 1f;
        public const float EnterHoldSeconds = 0.5f;
        public const float SpaceDefaultSize = 60f, SpacePushIn = 20f;

        public SceneDirector scenes;
        public TimeSystem time;
        public InputActionAsset actions;

        public bool Busy { get; private set; }
        /// <summary>Raised when a launch or entry finishes (SaveSystem autosaves here, Bible §10.7).</summary>
        public event System.Action Completed;
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
        IrisWipe iris;
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
            // Boot cover (U-028): opaque until the first planet is loaded and its shaders warmed.
            fade.color = Color.black;
            fade.enabled = true;
            iris = IrisWipe.Create(canvasGo.transform); // U-096: the iris quad, above the fade
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
            StartCoroutine(LiftBootCover());
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
            // U-107 (D-103, §5.2): the player keeps flying through the iris-out; nothing locks the input or moves the camera.
            yield return iris.Close(IrisWipe.ScreenCentre(cam, sideShip.Body.position), IrisSeconds);

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

            yield return iris.Open(IrisWipe.ScreenCentre(spaceCam, spaceShip.Position), IrisSeconds); // iris-in on the ship in space
            LastLaunchSeconds = Time.realtimeSinceStartup - t0;
            Busy = false;
            Completed?.Invoke();
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
            // U-107 (D-103, §5.3): the player keeps steering through the iris-out (no freeze, no lock).

            // U-096: the camera pushes in on the ship while the iris closes on it (0.35 s); the load runs while the screen is black.
            StartCoroutine(iris.Close(IrisWipe.ScreenCentre(spaceCam, spaceShip.Position), IrisSeconds));
            for (float t = 0f; t < IrisSeconds; t += Time.unscaledDeltaTime)
            {
                if (spaceCam != null) spaceCam.orthographicSize = Mathf.Lerp(startSize, SpacePushIn, t / IrisSeconds);
                yield return null;
            }
            while (iris.Busy) yield return null;

            var config = State.catalog.Get(body.planet);
            float longitude = angle - RotationDegrees(time, config);
            int x = ColumnAt(longitude, config.worldWidth);
            LastEntryAngle = Mathf.Repeat(angle, 360f);
            State.currentPlanet = body.planet;
            State.view = ViewMode.PlanetSide;
            scenes.Space.gameObject.SetActive(false); // before PlanetSide loads: one global 2D light at a time
            if (spaceCam != null) spaceCam.orthographicSize = SpaceDefaultSize;
            yield return scenes.LoadPlanetSide(config, x);

            var sideNow = scenes.PlanetSide;
            var landed = sideNow != null && sideNow.ship != null ? sideNow.ship.transform.position : (sideNow != null && sideNow.player != null ? sideNow.player.transform.position : Vector3.zero);
            yield return iris.Open(IrisWipe.ScreenCentre(sideNow != null ? sideNow.sideCamera : null, landed), IrisSeconds); // iris-in on the ship flying in
            LastEntrySeconds = Time.realtimeSinceStartup - t0;
            Busy = false;
            Completed?.Invoke();
        }

        public const float BootReveal = 0.3f;

        IEnumerator LiftBootCover()
        {
            while (!scenes.IsReady) yield return null;
            for (float t = 0f; t < BootReveal; t += Time.unscaledDeltaTime)
            {
                if (Busy) yield break; // a transition now owns the overlay
                fade.color = new Color(0f, 0f, 0f, 1f - t / BootReveal);
                yield return null;
            }
            fade.color = new Color(1f, 1f, 1f, 0f);
            fade.enabled = false;
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
