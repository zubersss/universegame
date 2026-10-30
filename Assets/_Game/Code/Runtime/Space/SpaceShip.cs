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
    /// boost cap 160 u/s (burns main fuel), every body's Gravity Well pulls, the Sun kills inside 1.2R.
    /// </summary>
    public sealed class SpaceShip : MonoBehaviour
    {
        public const float RotateSpeedDeg = 180f;
        /// <summary>Main-fuel use while boosting, units per second (Bible silent; P-11).</summary>
        public const float BoostFuelPerSecond = 0.5f;

        public SpaceWorld world;
        public InputActionAsset actions;
        public bool externalInput;
        public ShipIntent intent;
        public int thrusterMark = 1;

        public Vector2 Velocity { get; set; }
        public Vector2 Position { get => transform.position; set => transform.position = new Vector3(value.x, value.y, 0f); }
        public float Heading { get; set; } // degrees, 0 = +x
        public Vector2 LastPull { get; private set; }
        /// <summary>Body whose well pulls hardest right now, or null.</summary>
        public string InWellOf { get; private set; }
        public bool Destroyed { get; private set; }
        public event Action SunDeath;

        InputAction thrustA, retroA, rotateA, boostA;

        public float Thrust => thrusterMark >= 3 ? 70f : thrusterMark == 2 ? 45f : 30f;

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

        void Start()
        {
            if (!externalInput) PlaceAtWaystation("earth");
        }

        void FixedUpdate() => Step(Time.fixedDeltaTime);

        public void Step(float dt)
        {
            if (Destroyed) return;
            Heading += intent.rotate * RotateSpeedDeg * dt;
            float h = Heading * Mathf.Deg2Rad;
            var nose = new Vector2(Mathf.Cos(h), Mathf.Sin(h));

            var state = GameState.Instance;
            bool boosting = intent.boost && intent.thrust > 0f && (state == null || state.fuel > 0f);
            if (boosting && state != null) state.fuel = Mathf.Max(0f, state.fuel - BoostFuelPerSecond * dt);

            var accel = nose * (Thrust * (intent.thrust - intent.retro));
            int strongest = -1;
            LastPull = world != null ? SpaceLayout.Pull(world.Bodies, Position, out strongest) : Vector2.zero;
            InWellOf = strongest >= 0 ? world.Bodies[strongest].name : null;
            var v = Velocity + (accel + LastPull) * dt;
            float cap = boosting ? SpaceLayout.BoostSpeed : SpaceLayout.CruiseSpeed;
            if (v.sqrMagnitude > cap * cap) v = v.normalized * cap;
            Velocity = v;
            Position += v * dt;
            transform.rotation = Quaternion.Euler(0f, 0f, Heading);

            if (world != null && Position.magnitude < WellMath.SunKillFactor * WellMath.SunRadius)
            {
                Destroyed = true;
                Velocity = Vector2.zero;
                if (state != null) state.hull = 0f;
                SunDeath?.Invoke();
            }
        }
    }
}
