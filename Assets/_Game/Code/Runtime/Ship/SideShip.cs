using System;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Player;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.Ship
{
    /// <summary>What the pilot wants this step (Input System or tests).</summary>
    public struct ShipSideIntent
    {
        public float thrust;  // 0..1, W or Space held (a trigger gives the throttle)
        public float lateral; // -1..1, A/D: tilt the rocket (A nose left, D nose right); released, it springs upright
    }

    /// <summary>
    /// The Pilgrim in side view (Bible §4.3 v4.1, U-107): an upright rocket standing on its tail. Thrust (Mk1/2/3: 12 /
    /// 20 / 35 m/s²) acts along its own up axis; A/D tilt it up to ±35° with a spring back (RocketFlight); the planet's
    /// real gravity pulls it down, so it hovers where thrust = g, climbs above and sinks below. No fuel, no launch burn,
    /// no gate: thrust-to-weight is the only limit (D-103, D-106). Landing damage by touchdown speed; a touchdown tilted
    /// more than 20° tips it, and it rights itself over 0.5 s with a wobble (no damage). EscapeLineCrossed fires when the
    /// ship's centre crosses the Escape Line going up under the player's own thrust; nothing locks the controls.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D), typeof(BoxCollider2D))]
    public sealed class SideShip : MonoBehaviour
    {
        public const float CleanTouchdown = 6f, CrashTouchdown = 15f;
        public const float CrashHullFraction = 0.30f;
        public const float LegsAltitude = 10f;
        /// <summary>The leg feet sit this far below the ship's pivot (the pivot is near the tail).</summary>
        public const float SkidDrop = 1.8f;
        /// <summary>The rocket stands Height tall (≈ 12 m, B-123) on legs spanning Width.</summary>
        public const float Height = 11.4f, Width = 4f, BodyWidth = 3.4f;

        public InputActionAsset actions;
        public bool externalInput;
        public bool piloted;
        public ShipSideIntent intent;
        public int thrusterMark = 1;
        public PlanetConfig planet;

        [Header("State when no GameState exists (tests)")]
        public float localHull = 100f;

        public Rigidbody2D Body { get; private set; }
        public bool Grounded { get; private set; }
        public bool AtRest => Grounded && Body.linearVelocity.sqrMagnitude < 0.01f;
        public bool LegsDeployed { get; private set; } = true;
        public float AltitudeAboveGround { get; private set; }
        /// <summary>U-149: the air's density at the hull this step (ρ(h), relative to Earth's Datum; 0 on Mercury and above the Escape Line).</summary>
        public float AirDensity { get; private set; }

        /// <summary>U-150 (D-158 (4)): accelerating reads differently from cruising. Boosting starts when the hull's along-track acceleration
        /// (smoothed over ~0.15 s) passes BoostAccel under thrust in the air and ends when it falls under CruiseAccel (or the thrust stops).</summary>
        public const float BoostAccel = 1.5f, CruiseAccel = 0.5f, AccelSmoothing = 0.15f;
        /// <summary>U-150: the engine rumble's largest position-only camera shake (m), at full throttle, boosting, in air of density ≥ 1.</summary>
        public const float RumbleMax = 0.08f;
        /// <summary>U-150: the hull's acceleration along its velocity (m/s², smoothed).</summary>
        public float AlongTrackAccel { get; private set; }
        public bool Boosting { get; private set; }
        /// <summary>U-150: 0..1, eases up over 0.25 s while boosting and back over 0.5 s at cruise: the flame's length, the speed lines, the rumble.</summary>
        public float Boost { get; private set; }
        /// <summary>U-150: the engine rumble's amplitude now (m): RumbleMax × throttle × min(ρ, 1) × Boost.</summary>
        public float Rumble => RumbleMax * Flight.Throttle * Mathf.Min(1f, AirDensity) * Boost;
        /// <summary>U-150: the sound barrier (the planet's speed of sound, where ρ ≥ 0.1).</summary>
        public SoundBarrier Barrier { get; } = new SoundBarrier();
        /// <summary>U-150: raised on the physics step the hull breaks the sound barrier.</summary>
        public event Action SoundBarrierBroken;
        Vector2 prevVelocity;
        bool havePrev;
        public float LastTouchdownSpeed { get; private set; }
        /// <summary>The upright flight model (tilt, spring back, righting).</summary>
        public RocketFlight Flight { get; } = new RocketFlight();
        public float Tilt => Flight.Tilt;
        /// <summary>Input frames the controller read this session (tests: the "no input lock" probe).</summary>
        public int InputFrames { get; private set; }

        /// <summary>Raised once each time the ship's center crosses the Escape Line moving up.</summary>
        public event Action EscapeLineCrossed;
        public event Action<float> TouchedDown;
        /// <summary>Raised when a tilted touchdown tips the ship (it rights itself over RocketFlight.RightingSeconds).</summary>
        public event Action TippedOver;

        /// <summary>U-065: the fitted Thruster mark (GameState; the serialized field only when there is none, tests).</summary>
        public int ThrusterMark => GameState.Instance != null ? GameState.Instance.thrusterMark : thrusterMark;
        public float Thrust => ShipMarks.Thrust(ThrusterMark);
        public float Gravity => -Physics2D.gravity.y;
        public float ThrustToWeight => Thrust / Mathf.Max(0.01f, Gravity);
        /// <summary>§4.3: true where this mark cannot climb (thrust ≤ g); the HUD warns.</summary>
        public bool ThrustBelowGravity => !ShipMarks.CanClimb(ThrusterMark, Gravity);

        public float Hull
        {
            get => GameState.Instance != null ? GameState.Instance.hull : localHull;
            set { if (GameState.Instance != null) GameState.Instance.hull = value; else localHull = value; }
        }

        readonly ContactPoint2D[] contacts = new ContactPoint2D[8];
        readonly RaycastHit2D[] hits = new RaycastHit2D[4];
        static readonly ContactFilter2D NoFilter = ContactFilter2D.noFilter;
        InputAction thrustA, lateralA;
        float fallSpeed;
        float lastY;

        void Awake()
        {
            Body = GetComponent<Rigidbody2D>();
            Body.mass = 20f;
            // The tilt is RocketFlight's: each step sets the spin that reaches it (so the pose interpolates), and a huge
            // inertia keeps contacts from twisting the hull in between.
            Body.freezeRotation = false;
            Body.useAutoMass = false;
            Body.inertia = 1e5f;
            Body.interpolation = RigidbodyInterpolation2D.Interpolate;
            Body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            var box = GetComponent<BoxCollider2D>();
            box.size = new Vector2(Width, Height);
            box.offset = new Vector2(0f, Height * 0.5f - SkidDrop);
            box.sharedMaterial = new PhysicsMaterial2D("ShipFeet") { friction = 0.8f, bounciness = 0f };
            lastY = transform.position.y;

            if (externalInput) return;
            if (actions == null) actions = MeridianInput.Build();
            var map = actions.FindActionMap(MeridianInput.ShipSide, true);
            thrustA = map.FindAction("Thrust"); lateralA = map.FindAction("Lateral");
        }

        void Update()
        {
            if (externalInput || thrustA == null) return;
            if (!piloted) { intent = default; return; }
            intent.thrust = Mathf.Clamp01(thrustA.ReadValue<float>()); // a key gives 1, a trigger its throttle
            intent.lateral = lateralA.ReadValue<float>();
            InputFrames++;
        }

        public void SetPiloted(bool on)
        {
            piloted = on;
            var map = actions != null ? actions.FindActionMap(MeridianInput.ShipSide) : null;
            if (map != null) { if (on) map.Enable(); else map.Disable(); }
            if (!on) intent = default;
        }

        void FixedUpdate()
        {
            float dt = Time.fixedDeltaTime;
            bool wasGrounded = Grounded;
            Grounded = CheckGrounded();
            var v = Body.linearVelocity;
            if (Grounded && !wasGrounded) Touchdown(fallSpeed);
            fallSpeed = v.y < 0f ? -v.y : 0f;
            // U-150: the acceleration the last physics step gave the hull (thrust, gravity, drag, contacts), along its velocity, smoothed.
            float raw = 0f, speedNow = v.magnitude;
            if (havePrev && speedNow > 0.5f) raw = Vector2.Dot((v - prevVelocity) / dt, v / speedNow);
            prevVelocity = v; havePrev = true;
            AlongTrackAccel += (raw - AlongTrackAccel) * (1f - Mathf.Exp(-dt / AccelSmoothing));

            // The intent is the pilot's (Update clears it when nobody is aboard) or a test's (externalInput).
            // U-149 (D-158 (3)): the thruster spools toward the intent (0.35 s up, 0.2 s down) and the air drags the hull.
            Flight.StepThrottle(intent.thrust, dt);
            float throttle = Flight.Throttle;
            Flight.StepTilt(intent.lateral, Grounded && throttle <= 0f, dt);
            Body.angularVelocity = Mathf.DeltaAngle(Body.rotation, Flight.Tilt) / dt;
            if (throttle > 0f) v += Flight.ThrustAccel(throttle, Thrust) * dt; // gravity is the Rigidbody's (Physics2D.gravity)
            AirDensity = planet != null ? planet.AirDensityAt(Body.position.y) : 0f;
            if (AirDensity > 0f) v += RocketFlight.DragAccel(v, AirDensity) * dt; // D-106: drag only limits speed; it never stops a climb
            Body.linearVelocity = v;

            // U-150: boosting vs cruising (hysteresis between BoostAccel and CruiseAccel), and the sound barrier.
            bool thrusting = throttle > 0.05f && !Grounded;
            if (!Boosting && thrusting && AlongTrackAccel > BoostAccel) Boosting = true;
            else if (Boosting && (!thrusting || Mathf.Abs(AlongTrackAccel) < CruiseAccel)) Boosting = false;
            Boost = Mathf.MoveTowards(Boost, Boosting ? 1f : 0f, dt / (Boosting ? 0.25f : 0.5f));
            if (planet != null && Barrier.Step(v.magnitude, AirDensity, planet.SpeedOfSound)) SoundBarrierBroken?.Invoke();

            // Escape Line: the ship's center crossing upward (Bible §5.2 trigger).
            if (planet != null)
            {
                float line = planet.EscapeLineY;
                float y = Body.position.y;
                if (lastY < line && y >= line && v.y > 0f) EscapeLineCrossed?.Invoke();
                lastY = y;
            }

            AltitudeAboveGround = ProbeGround();
            LegsDeployed = AltitudeAboveGround <= LegsAltitude;
        }

        void Touchdown(float speed)
        {
            LastTouchdownSpeed = speed;
            Hull = HullAfterTouchdown(Hull, speed, 100f);
            if (Flight.Touchdown()) TippedOver?.Invoke();
            TouchedDown?.Invoke(speed);
        }

        /// <summary>
        /// §4.3 landing rule. Clean ≤ 6 m/s; 6–15 m/s takes up to 70% of max hull in proportion;
        /// above 15 m/s the ship crashes to 30% hull. A landing never takes the hull below 30% (P-14).
        /// </summary>
        public static float HullAfterTouchdown(float hull, float speed, float maxHull)
        {
            float floor = CrashHullFraction * maxHull;
            if (speed <= CleanTouchdown) return hull;
            if (speed > CrashTouchdown) return Mathf.Min(hull, floor);
            float damage = (speed - CleanTouchdown) / (CrashTouchdown - CleanTouchdown) * (maxHull - floor);
            return Mathf.Max(Mathf.Min(hull, floor), hull - damage);
        }

        bool CheckGrounded()
        {
            int n = Body.GetContacts(contacts);
            for (int i = 0; i < n; i++)
                if (contacts[i].normal.y > 0.7f) return true;
            return false;
        }

        float ProbeGround()
        {
            var from = Body.position + Vector2.down * (SkidDrop - 0.05f);
            int n = Physics2D.Raycast(from, Vector2.down, NoFilter, hits, 200f);
            for (int i = 0; i < n; i++)
                if (hits[i].rigidbody != Body) return hits[i].distance;
            return float.PositiveInfinity;
        }

        public void ConfigureFor(PlanetConfig config) { planet = config; Barrier.Reset(); }
    }
}
