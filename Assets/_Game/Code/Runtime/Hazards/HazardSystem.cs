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
            if (flares == null) flares = gameObject.AddComponent<SolarFlares>();
            flares.Run(p.id == PlanetId.Mercury, p.id.GetHashCode() * 7919 + 17);
            var state = Meridian.Core.GameState.Instance;
            if (state != null && state.suitTier != SuitTier) Equip(state.suitTier);
            Evaluate();
        }

        public void RestoreSuit() => SuitIntegrity = HazardRules.SuitMax;
        /// <summary>Load (SaveData v2): the saved integrity, clamped to 0..SuitMax.</summary>
        public void SetSuit(float value) => SuitIntegrity = Mathf.Clamp(value, 0f, HazardRules.SuitMax);

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
            Context = Where(p);
            HazardTable.Levels(Context, levels);

            Warm = aboard || WarmthSource.AnyCovers(p);
            var kind = HazardKind.Cryo;
            int worst = Warm ? 0 : HazardTable.Worst(levels, protection, out kind);
            WorstKind = Warm ? HazardKind.Cryo : kind;
            EffectiveLevel = worst;
            SuitRate = Warm ? (SuitIntegrity < HazardRules.SuitMax ? HazardRules.WarmRecharge : 0f) : -HazardRules.DrainPerSecond(worst);
        }

        /// <summary>U-049: what the hazards need to know about a place (planet, time, depth, zone, flare).</summary>
        HazardContext Where(Vector2 p)
        {
            int x = Mathf.FloorToInt(p.x), y = Mathf.FloorToInt(p.y);
            var c = new HazardContext
            {
                planet = planet.id,
                localTime = dayNight != null ? dayNight.LocalTime : 0.5f,
                stormCryo = storm != null ? storm.CryoBonus : 0,
                tundra = InTundra(p),
                y = p.y,
                sheltered = FlareShelter.AnyCovers(p),
            };
            if (terrain != null && terrain.Generator != null)
            {
                // Rock overhead: the original ground line (or a built roof) is above the surveyor's head.
                c.underground = terrain.TopSolidY(x) > y + 1;
                if (planet.id == PlanetId.Mars)
                {
                    surfaceAt ??= sx => terrain.Generator.SurfaceHeight(terrain.WrapX(sx)); // built once: no per-frame closure
                    c.lavaTube = MarsLandforms.InTube(terrain.WrapX(x), y, surfaceAt);
                }
            }
            if (planet.id == PlanetId.Mercury)
            {
                if (clock == null) clock = FindAnyObjectByType<Meridian.Core.TimeSystem>();
                double now = MercuryTerminator.Now(clock != null ? clock.GameSeconds : 0) + mercuryClockOffset;
                // Cold-trap floors (U-048) are in permanent shadow: night whatever the terminator does.
                c.mercury = MercuryLandforms.PermanentShadow(terrain != null ? terrain.WrapX(x) : x, planet.worldWidth)
                    ? MercuryZone.Night : MercuryTerminator.ZoneAt(p.x, now, planet.worldWidth);
                c.flare = flares != null && flares.Current == SolarFlares.Phase.Active;
            }
            return c;
        }

        /// <summary>Tests and scripted scenes move the terminator by shifting Mercury's clock (seconds).</summary>
        public double mercuryClockOffset;

        System.Func<int, int> surfaceAt;
        Meridian.Core.TimeSystem clock;

        public HazardContext Context { get; private set; }
        /// <summary>The hazard that is draining the suit now (U-049 HUD).</summary>
        public HazardKind WorstKind { get; private set; }

        /// <summary>Mercury's flares (created on demand; run only on Mercury).</summary>
        public SolarFlares flares;

        // ---------- Envirosuit (U-049) ----------

        /// <summary>Envirosuit tier 0–3 (Mk1–Mk3): every hazard's level drops by the tier.</summary>
        public int SuitTier { get; private set; }
        /// <summary>Raised with the tier when a suit is equipped (the surveyor's sheet swaps).</summary>
        public static event System.Action<int> SuitEquipped;

        public void Equip(int tier)
        {
            tier = Mathf.Clamp(tier, 0, 3);
            SuitTier = tier;
            for (int i = 0; i < protection.Length; i++) protection[i] = tier;
            var state = Meridian.Core.GameState.Instance;
            if (state != null) state.suitTier = tier;
            SuitEquipped?.Invoke(tier);
            Evaluate();
        }

        /// <summary>Earth's tundra biome (U-037; Bible §7.1, D-032).</summary>
        bool InTundra(Vector2 p) => planet.id == PlanetId.Earth && EarthBiomes.At(Mathf.FloorToInt(p.x)) == Biome.Tundra;
    }
}
