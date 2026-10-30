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
        public float thrust;  // 0..1, W
        public float retro;   // 0..1, S
        public float lateral; // -1..1, A/D
    }

    /// <summary>
    /// Pilgrim in side view (Bible §4.3): Mk1 12 m/s² vertical, lateral 60%; the launch fuel cost
    /// (§4.1) burns over the first 3 s of thrust from rest on the surface; landing damage by
    /// touchdown speed; EscapeLineCrossed when the ship's center crosses the Escape Line going up.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D), typeof(BoxCollider2D))]
    public sealed class SideShip : MonoBehaviour
    {
        public const float LateralFactor = 0.6f;
        public const float LaunchBurnSeconds = 3f;
        public const float CleanTouchdown = 6f, CrashTouchdown = 15f;
        public const float CrashHullFraction = 0.30f;
        public const float LegsAltitude = 10f;
        /// <summary>Skid bottoms sit this far below the ship's pivot (BLENDER B-006 handoff).</summary>
        public const float SkidDrop = 1.8f;
        public const float HullLength = 11.4f, HullHeight = 3.4f;

        public InputActionAsset actions;
        public bool externalInput;
        public bool piloted;
        public ShipSideIntent intent;
        public int thrusterMark = 1;
        public PlanetConfig planet;

        [Header("State when no GameState exists (tests)")]
        public float localHull = 100f, localFuel = 100f, localTank = 100f;

        public Rigidbody2D Body { get; private set; }
        public bool Grounded { get; private set; }
        public bool AtRest => Grounded && Body.linearVelocity.sqrMagnitude < 0.01f;
        public float LaunchBurnElapsed { get; private set; } = LaunchBurnSeconds;
        public bool LegsDeployed { get; private set; } = true;
        public float AltitudeAboveGround { get; private set; }
        public float LastTouchdownSpeed { get; private set; }

        /// <summary>Raised once each time the ship's center crosses the Escape Line moving up.</summary>
        public event Action EscapeLineCrossed;
        public event Action<float> TouchedDown;

        public float Thrust => thrusterMark >= 3 ? 35f : thrusterMark == 2 ? 20f : 12f;
        public float Gravity => -Physics2D.gravity.y;
        public bool ThrustBelowGravity => Thrust < Gravity;

        public float Hull
        {
            get => GameState.Instance != null ? GameState.Instance.hull : localHull;
            set { if (GameState.Instance != null) GameState.Instance.hull = value; else localHull = value; }
        }

        public float Fuel
        {
            get => GameState.Instance != null ? GameState.Instance.fuel : localFuel;
            set { if (GameState.Instance != null) GameState.Instance.fuel = value; else localFuel = value; }
        }

        public float Tank => GameState.Instance != null ? GameState.Instance.tankCapacity : localTank;

        readonly ContactPoint2D[] contacts = new ContactPoint2D[8];
        readonly RaycastHit2D[] hits = new RaycastHit2D[4];
        static readonly ContactFilter2D NoFilter = ContactFilter2D.noFilter;
        InputAction thrustA, retroA, lateralA;
        float fallSpeed;
        float lastY;

        void Awake()
        {
            Body = GetComponent<Rigidbody2D>();
            Body.freezeRotation = true;
            Body.mass = 20f;
            Body.interpolation = RigidbodyInterpolation2D.Interpolate;
            Body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            var box = GetComponent<BoxCollider2D>();
            box.size = new Vector2(HullLength * 0.92f, HullHeight);
            box.offset = new Vector2(0f, HullHeight * 0.5f - SkidDrop);
            box.sharedMaterial = new PhysicsMaterial2D("ShipSkids") { friction = 0.8f, bounciness = 0f };
            lastY = transform.position.y;

            if (externalInput) return;
            if (actions == null) actions = MeridianInput.Build();
            var map = actions.FindActionMap(MeridianInput.ShipSide, true);
            thrustA = map.FindAction("Thrust"); retroA = map.FindAction("Retro"); lateralA = map.FindAction("Lateral");
        }

        void Update()
        {
            if (externalInput || thrustA == null) return;
            if (!piloted) { intent = default; return; }
            intent.thrust = thrustA.IsPressed() ? 1f : 0f;
            intent.retro = retroA.IsPressed() ? 1f : 0f;
            intent.lateral = lateralA.ReadValue<float>();
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


            float up = Mathf.Clamp01(intent.thrust), down = Mathf.Clamp01(intent.retro);
            bool firing = up > 0f || down > 0f || Mathf.Abs(intent.lateral) > 0.01f;
            // A new launch burn arms while the ship sits at rest with the throttle released, so a
            // ship that can't lift (thrust < g) pays the cost once, not every step.
            if (AtRest && !firing) LaunchBurnElapsed = 0f;
            if (firing && LaunchBurnElapsed < LaunchBurnSeconds)
            {
                // §4.3: the §4.1 launch cost is consumed over the first 3 s of thrust; flight is then free.
                float cost = planet != null ? planet.LaunchFuelCost : 0f;
                float step = Mathf.Min(dt, LaunchBurnSeconds - LaunchBurnElapsed);
                float need = cost * step / LaunchBurnSeconds;
                if (Fuel <= 0f || Fuel < need * 0.999f) { up = down = 0f; firing = false; } // out of fuel: no thrust
                else { Fuel = Mathf.Max(0f, Fuel - need); LaunchBurnElapsed += step; }
            }

            if (firing)
            {
                v.y += (up - down) * Thrust * dt;
                v.x += Mathf.Clamp(intent.lateral, -1f, 1f) * Thrust * LateralFactor * dt;
            }
            Body.linearVelocity = v;

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

        public void ConfigureFor(PlanetConfig config) => planet = config;
    }
}
