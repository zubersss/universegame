using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.Player
{
    /// <summary>What the player wants this step. Filled from the Input System, or by tests.</summary>
    public struct PlayerIntent
    {
        public float move;       // -1..1
        public bool sprint;
        public bool jumpHeld;
        public bool jumpPressed; // went down since the last fixed step
        public bool dashPressed; // U-088: Shift tapped in the air, for one fixed step
    }

    /// <summary>
    /// Side-view player body (Bible §4.2): fixed jump impulse under the planet's real gravity,
    /// walk/sprint, coyote time and jump buffer, terminal velocity, hard landings (Suit power), Jetpack, the air dash.
    /// D-087: no combat; a creature, Warden or hazard contact is a Bump (a knock with dizzy stars, never a meter).
    /// Gravity comes from Physics2D.gravity, which PlanetSideRoot sets per planet.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D), typeof(CapsuleCollider2D))]
    public sealed class PlayerController : MonoBehaviour
    {
        public InputActionAsset actions;
        /// <summary>Air speed (m/s, +x) the surveyor drifts with (U-050 Venus wind; 0 elsewhere).</summary>
        [System.NonSerialized] public float windX;
        /// <summary>Share of the wind that moves a grounded surveyor.</summary>
        public const float WindGrip = 0.35f;
        [Tooltip("Tests drive the controller through `intent` instead of devices.")]
        public bool externalInput;
        public PlayerIntent intent;
        public float terminalVelocity = 50f;
        public int jetpackMark = 1;

        public Rigidbody2D Body { get; private set; }
        public PlayerVitals Vitals { get; private set; }
        public bool Grounded { get; private set; }
        public float LastImpactSpeed { get; private set; }
        public Jetpack Jetpack { get; private set; }
        public int Facing { get; private set; } = 1;
        public event System.Action Jumped;
        /// <summary>Raised on touchdown with the impact speed (m/s).</summary>
        public event System.Action<float> Landed;
        /// <summary>U-088 (Bible §4.2 Feel): the air dash, a pure solver stepped in FixedUpdate.</summary>
        public AirDash Dash { get; } = new AirDash();
        /// <summary>
        /// U-093 (D-087): bumped by a creature, a Warden or a hazard: knocked KnockDistance away from `from` over KnockTime
        /// (a velocity override), the `bump` clip and dizzy stars (Bumped). No meter changes: there is no health.
        /// </summary>
        public event System.Action Bumped;
        public const float KnockDistance = 0.8f, KnockTime = 0.12f;
        /// <summary>Bumps taken since load (tests, the dizzy-stars FX hook).</summary>
        public int BumpCount { get; private set; }
        float knockFor, knockVx;
        bool knockEnded;

        public void Bump(Vector2 from)
        {
            float x = Body != null ? Body.position.x : transform.position.x;
            knockFor = KnockTime;
            knockVx = (x >= from.x ? 1f : -1f) * (KnockDistance / KnockTime);
            BumpCount++;
            Bumped?.Invoke();
        }

        readonly JumpTimer jumpTimer = new JumpTimer();
        readonly ContactPoint2D[] contacts = new ContactPoint2D[8];
        InputAction moveAction, sprintAction, jumpAction, dashAction;
        bool jumpLatched, dashLatched, jumpHeldLast;
        float airTimeSinceJump;
        float fallSpeed;

        void Awake()
        {
            Body = GetComponent<Rigidbody2D>();
            Body.gravityScale = 1f;
            Body.freezeRotation = true;
            Body.interpolation = RigidbodyInterpolation2D.Interpolate;
            Body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            var capsule = GetComponent<CapsuleCollider2D>();
            capsule.size = new Vector2(PlayerTuning.Width, PlayerTuning.Height);
            capsule.offset = new Vector2(0f, PlayerTuning.Height * 0.5f); // pivot at the feet
            capsule.sharedMaterial = new PhysicsMaterial2D("PlayerNoFriction") { friction = 0f, bounciness = 0f };
            Jetpack = new Jetpack(jetpackMark);

            if (!externalInput)
            {
                if (actions == null) actions = MeridianInput.Build();
                var foot = actions.FindActionMap(MeridianInput.OnFoot, true);
                moveAction = foot.FindAction("Move");
                sprintAction = foot.FindAction("Sprint");
                jumpAction = foot.FindAction("Jump");
                dashAction = foot.FindAction("Dash", false);
                foot.Enable();
            }
        }

        void Update()
        {
            if (externalInput || moveAction == null) return;
            intent.move = moveAction.ReadValue<float>();
            intent.sprint = sprintAction.IsPressed();
            intent.jumpHeld = jumpAction.IsPressed();
            if (jumpAction.WasPressedThisFrame()) jumpLatched = true;
            if (dashAction != null && dashAction.WasPressedThisFrame()) dashLatched = true;
        }

        /// <summary>Tests: press jump for the next fixed step.</summary>
        public void PressJump() => jumpLatched = true;
        public void PressDash() => dashLatched = true;

        void FixedUpdate()
        {
            float dt = Time.fixedDeltaTime;
            float g = -Physics2D.gravity.y * Body.gravityScale;
            bool wasGrounded = Grounded;
            Grounded = CheckGrounded();

            var v = Body.linearVelocity;
            if (Grounded && !wasGrounded) Land(fallSpeed);
            fallSpeed = v.y < 0f ? -v.y : 0f;

            // Horizontal: accelerate toward the target speed.
            // U-093: the knock stops dead when it ends, so a bump moves the surveyor KnockDistance, not a braking slide more.
            if (knockEnded) { v.x = 0f; knockEnded = false; }
            float target = Mathf.Clamp(intent.move, -1f, 1f) * (intent.sprint ? PlayerTuning.SprintSpeed : PlayerTuning.WalkSpeed);
            // U-050: moving air (Venus super-rotation) carries the surveyor; on the ground the feet resist two thirds of it.
            float goalX = target + windX * (Grounded ? WindGrip : 1f);
            // U-088 (Bible §4.2 Feel v3): 60 m/s² to speed, 80 braking, a turn reverses within 0.08 s; 30 in the air.
            float accel = PlayerTuning.AirAcceleration;
            if (Grounded)
            {
                bool braking = Mathf.Abs(target) < 0.01f;
                bool turning = !braking && Mathf.Abs(v.x) > 0.1f && Mathf.Sign(target) != Mathf.Sign(v.x);
                accel = braking ? PlayerTuning.Braking : turning ? PlayerTuning.TurnAcceleration : PlayerTuning.GroundAcceleration;
            }
            v.x = Mathf.MoveTowards(v.x, goalX, accel * dt);
            if (Mathf.Abs(intent.move) > 0.01f) Facing = intent.move > 0 ? 1 : -1;

            // Jump. Physics applies gravity before moving the body, so starting at v₀ + g·dt/2
            // makes every step move at the true mid-step velocity: the arc peaks at exactly v₀²/2g.
            bool pressed = jumpLatched || intent.jumpPressed;
            jumpLatched = false; intent.jumpPressed = false;
            bool jumped = jumpTimer.Step(dt, Grounded, pressed);
            if (jumped)
            {
                v.y = PlayerTuning.JumpStartSpeed(g, dt);
                Grounded = false;
                airTimeSinceJump = 0f;
                Jumped?.Invoke();
            }
            else airTimeSinceJump += dt;

            // Jetpack: jump held in the air past 0.25 s, or a fresh press while airborne.
            // A tap is only a jump.
            bool jetHeld = intent.jumpHeld && !Grounded && !jumped && (airTimeSinceJump > 0.25f || pressed);
            v.y += Jetpack.Step(dt, jetHeld, Grounded) * dt;

            // U-088: jump cut: releasing the jump while rising keeps 40 % of the upward speed (the full height is unchanged).
            if (jumpHeldLast && !intent.jumpHeld && !Grounded && !jumped && v.y > 0f) v.y *= PlayerTuning.JumpCutFactor;
            jumpHeldLast = intent.jumpHeld;

            // U-088: air dash: a velocity override (9 m/s facing for 0.18 s, vertical held at 0), then the planet's g resumes at once.
            bool dashNow = dashLatched || intent.dashPressed;
            dashLatched = false; intent.dashPressed = false;
            if (dashNow) Dash.TryStart(!Grounded, Facing);
            if (Dash.Step(dt, Grounded, out float dashShare))
            {
                v.x = Dash.Direction * AirDash.Speed * dashShare;
                v.y = g * dt * dashShare; // physics applies g·dt before moving: this leaves the step's vertical motion at 0
            }

            // U-093: the bump knock (0.8 m away over 0.12 s).
            if (knockFor > 0f)
            {
                knockFor -= dt;
                v.x = knockVx;
                if (knockFor <= dt * 0.5f) { knockFor = 0f; knockEnded = true; } // whole steps only: 0.12 s = 6 steps at 50 Hz
            }

            if (v.y < -terminalVelocity) v.y = -terminalVelocity;
            Body.linearVelocity = v;
        }

        void Land(float impactSpeed)
        {
            LastImpactSpeed = impactSpeed;
            Landed?.Invoke(impactSpeed);
            if (Vitals == null) Vitals = GetComponent<PlayerVitals>();
            if (Vitals != null) Vitals.TakeFallImpact(impactSpeed);
        }

        bool CheckGrounded()
        {
            int n = Body.GetContacts(contacts);
            for (int i = 0; i < n; i++)
                if (contacts[i].normal.y > 0.7f) return true;
            return false;
        }

        /// <summary>Apply a planet's movement-related numbers (called on planet load).</summary>
        public void ConfigureFor(Meridian.Planets.PlanetConfig planet)
        {
            terminalVelocity = planet.terminalVelocity;
        }
    }
}
