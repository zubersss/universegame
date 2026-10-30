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
    }

    /// <summary>
    /// Side-view player body (Bible §4.2): fixed jump impulse under the planet's real gravity,
    /// walk/sprint, coyote time and jump buffer, terminal velocity, fall damage, Jetpack.
    /// Gravity comes from Physics2D.gravity, which PlanetSideRoot sets per planet.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D), typeof(CapsuleCollider2D))]
    public sealed class PlayerController : MonoBehaviour
    {
        public InputActionAsset actions;
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

        readonly JumpTimer jumpTimer = new JumpTimer();
        readonly ContactPoint2D[] contacts = new ContactPoint2D[8];
        InputAction moveAction, sprintAction, jumpAction;
        bool jumpLatched;
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
        }

        /// <summary>Tests: press jump for the next fixed step.</summary>
        public void PressJump() => jumpLatched = true;

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
            float target = Mathf.Clamp(intent.move, -1f, 1f) * (intent.sprint ? PlayerTuning.SprintSpeed : PlayerTuning.WalkSpeed);
            float accel = Grounded ? PlayerTuning.GroundAcceleration : PlayerTuning.AirAcceleration;
            v.x = Mathf.MoveTowards(v.x, target, accel * dt);
            if (Mathf.Abs(intent.move) > 0.01f) Facing = intent.move > 0 ? 1 : -1;

            // Jump. Physics applies gravity before moving the body, so starting at v₀ + g·dt/2
            // makes every step move at the true mid-step velocity: the arc peaks at exactly v₀²/2g.
            bool pressed = jumpLatched || intent.jumpPressed;
            jumpLatched = false; intent.jumpPressed = false;
            bool jumped = jumpTimer.Step(dt, Grounded, pressed);
            if (jumped)
            {
                v.y = PlayerTuning.JumpSpeed + 0.5f * g * dt;
                Grounded = false;
                airTimeSinceJump = 0f;
                Jumped?.Invoke();
            }
            else airTimeSinceJump += dt;

            // Jetpack: jump held in the air past 0.25 s, or a fresh press while airborne.
            // A tap is only a jump.
            bool jetHeld = intent.jumpHeld && !Grounded && !jumped && (airTimeSinceJump > 0.25f || pressed);
            v.y += Jetpack.Step(dt, jetHeld, Grounded) * dt;

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
