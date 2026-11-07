using System;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Player;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.Space
{
    /// <summary>What the pilot wants this step (Input System or tests).</summary>
    public struct ShipIntent
    {
        public float thrust;  // 0..1 (W)
        public float retro;   // 0..1 (S)
        public float rotate;  // -1..1, positive = counter-clockwise (A)
        public bool boost;    // Shift
    }

    /// <summary>
    /// Top-down ship (Bible §3, §4.4): thrust Mk1 30 u/s² along the nose, cruise cap 80 u/s,
    /// boost cap 160 u/s (no fuel, D-103), every body's Gravity Well pulls, the Sun kills inside 1.2R.
    /// </summary>
    public sealed class SpaceShip : MonoBehaviour
    {
        public const float RotateSpeedDeg = 180f;

        public SpaceWorld world;
        public InputActionAsset actions;
        public bool externalInput;
        public ShipIntent intent;
        public int thrusterMark = 1;
        /// <summary>U-063: skip speed while the Skip Drive runs (0: normal flight). Set by SkipDrive.</summary>
        public float skipSpeed;

        public Vector2 Velocity { get; set; }
        public Vector2 Position { get => transform.position; set => transform.position = new Vector3(value.x, value.y, 0f); }
        public float Heading { get; set; } // degrees, 0 = +x
        public Vector2 LastPull { get; private set; }
        /// <summary>Body whose well pulls hardest right now, or null.</summary>
        public string InWellOf { get; private set; }
        public bool Destroyed { get; private set; }
        public bool Invulnerable => Time.time < invulnerableUntil;
        float invulnerableUntil;
        public event Action SunDeath;

        InputAction thrustA, retroA, rotateA, boostA;
        /// <summary>U-107: frames whose input this ship read (tests: the "no input lock" probe across a launch).</summary>
        public int InputFrames { get; private set; }

        /// <summary>U-065: the fitted Thruster mark is shared with the side view (GameState; the field only without one).</summary>
        int Mark => GameState.Instance != null ? GameState.Instance.thrusterMark : thrusterMark;
        public float Thrust => Mark >= 3 ? 70f : Mark == 2 ? 45f : 30f;

        void Awake()
        {
            if (externalInput) return;
            if (actions == null) actions = MeridianInput.Build();
            var map = actions.FindActionMap(MeridianInput.ShipTop, true);
            thrustA = map.FindAction("Thrust"); retroA = map.FindAction("Retro");
            rotateA = map.FindAction("Rotate"); boostA = map.FindAction("Boost");
            map.Enable();
        }

        void Update()
        {
            if (externalInput || thrustA == null) return;
            intent.thrust = thrustA.IsPressed() ? 1f : 0f;
            intent.retro = retroA.IsPressed() ? 1f : 0f;
            intent.rotate = rotateA.ReadValue<float>();
            intent.boost = boostA.IsPressed();
            InputFrames++;
        }

        /// <summary>Waystation start (Bible §3: Earth orbit): just outside the planet's Atmosphere Ring, at rest.</summary>
        public void PlaceAtWaystation(string planet)
        {
            var b = world != null ? world.Find(planet) : null;
            if (b == null) return;
            Position = b.Value.position + new Vector2(0f, b.Value.RingRadius + 30f);
            Velocity = Vector2.zero;
            Heading = 0f;
            Destroyed = false;
        }

        /// <summary>
        /// Launch arrival (Bible §5.2): on the body's Atmosphere Ring at `angleDeg`, moving outward at
        /// `speed`, nose outward, invulnerable for `invulnerableSeconds`.
        /// </summary>
        public void PlaceOnRing(BodyInfo body, float angleDeg, float speed, float invulnerableSeconds)
        {
            float a = angleDeg * Mathf.Deg2Rad;
            var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            Position = body.position + dir * body.RingRadius;
            Velocity = dir * speed;
            Heading = angleDeg;
            transform.rotation = Quaternion.Euler(0f, 0f, Heading);
            Destroyed = false;
            invulnerableUntil = Time.time + invulnerableSeconds;
            placedByTransition = true;
        }

        bool placedByTransition;

        void Start()
        {
            if (placedByTransition) return;
            if (!externalInput) PlaceAtWaystation("earth");
        }

        void FixedUpdate() => Step(Time.fixedDeltaTime);

        public void Step(float dt)
        {
            if (Destroyed) return;
            Heading += intent.rotate * RotateSpeedDeg * dt;
            float h = Heading * Mathf.Deg2Rad;
            var nose = new Vector2(Mathf.Cos(h), Mathf.Sin(h));

            bool boosting = intent.boost && intent.thrust > 0f; // U-107 (D-103): boost costs nothing

            var accel = nose * (Thrust * (intent.thrust - intent.retro));
            int strongest = -1;
            LastPull = world != null ? SpaceLayout.Pull(world.Bodies, Position, out strongest) : Vector2.zero;
            InWellOf = strongest >= 0 ? world.Bodies[strongest].name : null;
            Vector2 v;
            if (skipSpeed > 0f) v = nose * skipSpeed; // U-063: in skip, straight along the heading; no pull, no cap
            else
            {
                v = Velocity + (accel + LastPull) * dt;
                float cap = boosting ? SpaceLayout.BoostSpeed : SpaceLayout.CruiseSpeed;
                if (v.sqrMagnitude > cap * cap) v = v.normalized * cap;
            }
            Velocity = v;
            Position += v * dt;
            transform.rotation = Quaternion.Euler(0f, 0f, Heading);

            if (world != null && !Invulnerable && Position.magnitude < WellMath.SunKillFactor * WellMath.SunRadius)
            {
                Destroyed = true;
                Velocity = Vector2.zero;
                if (GameState.Instance != null) GameState.Instance.hull = 0f;
                SunDeath?.Invoke();
            }
        }
    }
}
