using Meridian.Planet.Lighting;
using Meridian.Planet.Weather;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Ship;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>
    /// U-029 hazard system v1 for the PlanetSide surveyor (lives on the PlanetSide root, not the player,
    /// because boarding deactivates the player object): works out each hazard's level where the player
    /// stands (Cryo now; Thermal/Radiation/Toxic/Pressure return 0 until M3/M4 fill their providers),
    /// lowers it by the suit's protection tiers, and drains the suit's integrity by the worst effective
    /// level (HazardRules), then health once the suit is gone. Aboard the ship or near a WarmthSource
    /// the hazard is cancelled and the suit recharges. No allocation per frame.
    /// </summary>
    public sealed class HazardSystem : MonoBehaviour
    {
        /// <summary>The surveyor; while aboard, the ship's position counts.</summary>
        public Transform body;
        public PlayerVitals vitals;
        public ShipBoarding boarding;
        public TerrainStreamer terrain;
        public DayNightLighting dayNight;
        public DustStorm storm;

        /// <summary>Suit protection tier per HazardKind (Cryo Mk1–Mk3 modules arrive in M3).</summary>
        public readonly int[] protection = new int[HazardRules.Kinds];

        public float SuitIntegrity { get; private set; } = HazardRules.SuitMax;
        /// <summary>Raw level of each hazard where the player is (before protection and warmth).</summary>
        public readonly int[] levels = new int[HazardRules.Kinds];
        public int CryoLevel => levels[(int)HazardKind.Cryo];
        /// <summary>Worst level after protection and warmth: what is draining the suit now.</summary>
        public int EffectiveLevel { get; private set; }
        public bool Warm { get; private set; }
        /// <summary>Signed suit change per second: negative while draining, +5 while warming.</summary>
        public float SuitRate { get; private set; }

        PlanetConfig planet;

        public void ConfigureFor(PlanetConfig p)
        {
            planet = p;
            Evaluate();
        }

        public void RestoreSuit() => SuitIntegrity = HazardRules.SuitMax;

        void Update() => Step(Time.deltaTime);

        /// <summary>One update of `dt` seconds (tests drive it directly to simulate long exposures).</summary>
        public void Step(float dt)
        {
            Evaluate();
            if (vitals != null && vitals.Dead) { SuitRate = 0f; return; }
            if (Warm)
            {
                SuitIntegrity = Mathf.Min(HazardRules.SuitMax, SuitIntegrity + HazardRules.WarmRecharge * dt);
                return;
            }
            float drain = HazardRules.DrainPerSecond(EffectiveLevel) * dt;
            if (drain <= 0f) return;
            float fromSuit = Mathf.Min(SuitIntegrity, drain);
            SuitIntegrity -= fromSuit;
            if (drain > fromSuit && vitals != null) vitals.Damage(drain - fromSuit);
        }

        void Evaluate()
        {
            for (int i = 0; i < levels.Length; i++) levels[i] = 0;
            if (planet == null) { EffectiveLevel = 0; SuitRate = 0f; return; }
            bool aboard = boarding != null && boarding.Aboard;
            var p = aboard && boarding.ship != null ? (Vector2)boarding.ship.transform.position : body != null ? (Vector2)body.position : (Vector2)transform.position;
            float t = dayNight != null ? dayNight.LocalTime : 0.5f;
            levels[(int)HazardKind.Cryo] = Cryo.Level(planet.id, t, storm != null ? storm.CryoBonus : 0, InTundra(p));

            Warm = aboard || WarmthSource.AnyCovers(p);
            int worst = 0;
            if (!Warm)
                for (int i = 0; i < levels.Length; i++)
                    worst = Mathf.Max(worst, HazardRules.Effective(levels[i], protection[i]));
            EffectiveLevel = worst;
            SuitRate = Warm ? (SuitIntegrity < HazardRules.SuitMax ? HazardRules.WarmRecharge : 0f) : -HazardRules.DrainPerSecond(worst);
        }

        /// <summary>Earth tundra until biomes exist: the column's surface is snow (high ground, Bible §7.1).</summary>
        bool InTundra(Vector2 p)
        {
            if (planet.id != PlanetId.Earth || terrain == null || terrain.Generator == null) return false;
            int x = Mathf.FloorToInt(p.x);
            int surface = terrain.Generator.SurfaceHeight(terrain.WrapX(x));
            return terrain.GetTile(x, surface) == TileId.Snow;
        }
    }
}
