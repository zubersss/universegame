using System.Collections.Generic;
using Meridian.Planets;
using UnityEngine;

namespace Meridian.Space
{
    /// <summary>Gravity Well pull (Bible §4.4): a(r) = k_well × g × (R / r)², inside r ≤ wellFactor × R.</summary>
    public static class WellMath
    {
        public const float KWell = 1.63f;
        /// <summary>The Sun's own constant (D-022): 14.9 u/s² at Mercury's orbit, Mk1 thrust (30) at r ≈ 810.</summary>
        public const float KSun = 0.80f;
        public const float PlanetWellFactor = 4f;
        public const float MoonWellFactor = 3f;
        public const float RingFactor = 1.2f;
        public const float SunGravity = 274f;
        public const float SunRadius = 300f;
        public const float SunKillFactor = 1.2f;

        public static float Acceleration(float g, float radius, float r, float wellFactor = PlanetWellFactor, float k = KWell)
        {
            if (r > wellFactor * radius || r <= 0f) return 0f;
            float q = radius / r;
            return k * g * q * q;
        }
    }

    /// <summary>One body on the top-down map.</summary>
    public struct BodyInfo
    {
        public string name;          // lowercase, matches asset keys (planets/<name>/surface)
        public Vector2 position;
        public float radius;         // visual radius R (units)
        public float gravity;        // m/s², drives the well
        public float wellFactor;     // 4 for planets and the Sun, 3 for moons
        public float k;              // well constant: KWell, or KSun for the Sun
        public bool landable;
        public bool isSun;
        public PlanetId planet;      // valid when landable
        public string parent;        // moons: parent planet name
        public float WellRadius => wellFactor * radius;
        public float RingRadius => WellMath.RingFactor * radius;
    }

    /// <summary>
    /// The compressed top-down solar system (Bible §3). Positions are static in M1. Orbit radii and
    /// R come from PlanetConfig; angles are fixed here. Earth and Mars share an angle so the
    /// Earth → Mars cruise matches the Bible's ≈ 7 s (550 u at 80 u/s).
    /// </summary>
    public static class SpaceLayout
    {
        public const float CruiseSpeed = 80f;
        public const float BoostSpeed = 160f;
        public const float BeltInner = 3200f, BeltOuter = 4000f;

        static readonly Dictionary<PlanetId, float> AngleDeg = new Dictionary<PlanetId, float>
        {
            { PlanetId.Mercury, 140f }, { PlanetId.Venus, 250f }, { PlanetId.Earth, 0f }, { PlanetId.Mars, 0f },
            { PlanetId.Jupiter, 60f }, { PlanetId.Saturn, 200f }, { PlanetId.Uranus, 300f }, { PlanetId.Neptune, 110f },
        };

        // name, parent, R, real surface g, offset angle (deg) from the parent, distance beyond the parent's well
        static readonly (string name, PlanetId parent, float r, float g, float angle, float gap)[] Moons =
        {
            ("luna", PlanetId.Earth, 7f, 1.62f, 90f, 40f),
            ("phobos", PlanetId.Mars, 3f, 0.0057f, 120f, 15f),
            ("deimos", PlanetId.Mars, 3f, 0.003f, 250f, 40f),
            ("io", PlanetId.Jupiter, 8f, 1.80f, 30f, 40f),
            ("europa", PlanetId.Jupiter, 7f, 1.31f, 160f, 90f),
            ("titan", PlanetId.Saturn, 8f, 1.35f, 300f, 60f),
            ("triton", PlanetId.Neptune, 6f, 0.78f, 45f, 40f),
        };

        public static Vector2 PlanetPosition(PlanetConfig c)
        {
            float a = AngleDeg[c.id] * Mathf.Deg2Rad;
            return new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * c.orbitRadius;
        }

        public static List<BodyInfo> Build(PlanetCatalog catalog)
        {
            var list = new List<BodyInfo>
            {
                new BodyInfo { name = "sun", position = Vector2.zero, radius = WellMath.SunRadius, gravity = WellMath.SunGravity,
                               wellFactor = WellMath.PlanetWellFactor, k = WellMath.KSun, isSun = true },
            };
            foreach (var c in catalog.planets)
            {
                if (c == null) continue;
                list.Add(new BodyInfo
                {
                    name = c.id.ToString().ToLowerInvariant(), position = PlanetPosition(c), radius = c.visualRadius,
                    gravity = c.gravity, wellFactor = WellMath.PlanetWellFactor, k = WellMath.KWell, landable = c.landable, planet = c.id,
                });
            }
            foreach (var m in Moons)
            {
                var parent = catalog.Get(m.parent);
                if (parent == null) continue;
                float a = m.angle * Mathf.Deg2Rad;
                float d = WellMath.PlanetWellFactor * parent.visualRadius + WellMath.MoonWellFactor * m.r + m.gap;
                list.Add(new BodyInfo
                {
                    name = m.name, parent = m.parent.ToString().ToLowerInvariant(),
                    position = PlanetPosition(parent) + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * d,
                    radius = m.r, gravity = m.g, wellFactor = WellMath.MoonWellFactor, k = WellMath.KWell,
                });
            }
            return list;
        }

        /// <summary>Total well pull at a point from every body (u/s²).</summary>
        public static Vector2 Pull(IReadOnlyList<BodyInfo> bodies, Vector2 at) => Pull(bodies, at, out _);

        /// <summary>As Pull; strongest = index of the body pulling hardest, or -1 outside every well.</summary>
        public static Vector2 Pull(IReadOnlyList<BodyInfo> bodies, Vector2 at, out int strongest)
        {
            var sum = Vector2.zero;
            strongest = -1;
            float best = 0f;
            for (int i = 0; i < bodies.Count; i++)
            {
                var d = bodies[i].position - at;
                float r = d.magnitude;
                float a = WellMath.Acceleration(bodies[i].gravity, bodies[i].radius, r, bodies[i].wellFactor, bodies[i].k);
                if (a > 0f) { sum += d / r * a; if (a > best) { best = a; strongest = i; } }
            }
            return sum;
        }
    }
}
