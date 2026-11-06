using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Creatures
{
    /// <summary>Append only: the order is the art/handle index.</summary>
    public enum Species
    {
        Stag, GreyWolf, Dustskater, ScreeStalker,
        // U-055 inner planets (Bible §7.3, §7.4)
        Glassback, Cinderling, Flarewing, Shadewyrm, Cinderhulk,
        SulfurDrifter, Acidmoth, PressureCrab, VentEel, VeilSerpent,
    }

    /// <summary>What a creature does about the player.</summary>
    public enum Temper { Flees, Hunts }

    public enum ActiveTime { Any, Day, Night }

    /// <summary>
    /// Where a creature lives (U-055): on the ground under gravity; in the air a few metres over the ground
    /// (hoverMin..hoverMax); or on Venus's cloud deck (VenusLandforms.DeckY ± DeckHalfBand).
    /// </summary>
    public enum Habitat { Ground, Air, Deck }

    /// <summary>What a spawn rule sees of one candidate column (U-055).</summary>
    public struct SpawnSite
    {
        public int x, surfaceY, datumY, worldWidth;
        public byte surfaceTile;
        public PlanetId planet;
        /// <summary>Mercury: the zone at x and its local time (0.25 dawn line, 0.75 dusk line).</summary>
        public MercuryZone zone;
        public float localTime;
        public float playerY;
    }

    /// <summary>
    /// U-027 roster v1 (Bible §7.1 Earth: stag grazer flees, grey wolf pack at night; §7.2 Mars:
    /// dustskater small scavenger, scree stalker pack hunter in canyons). U-055 adds Mercury (§7.3: glassback
    /// rides the twilight band, cinderlings swarm at dawn, flarewings fly the day side and turn on you during a
    /// flare, shadewyrms in the polar cold traps, the Cinderhulk apex) and Venus (§7.4: sulfur drifters and
    /// acidmoths on the cloud deck, pressure crabs on the plains, vent eels in the vent fields, the Veil
    /// Serpent apex on the deck). Sizes in metres; speeds in m/s.
    /// </summary>
    public sealed class SpeciesSpec
    {
        public Species id;
        public PlanetId planet;
        public string artKey;
        /// <summary>Cinderhulk: the cooled-shell sheet worn on the night side.</summary>
        public string nightArtKey;
        public Vector2 size;
        public float wanderSpeed, runSpeed, jumpSpeed;
        public Temper temper;
        /// <summary>Flee: distance at which it bolts. Hunt: distance at which it starts the chase.</summary>
        public float senseRange;
        public ActiveTime time;
        public int packMin, packMax;
        public int maxAlive;
        public Color placeholder;
        public Habitat habitat;
        /// <summary>Air: the height band above the ground it keeps (m).</summary>
        public float hoverMin = 3f, hoverMax = 7f;
        /// <summary>Flarewing: hunts while a solar flare is active, keeps clear otherwise.</summary>
        public bool huntsDuringFlare;
        public bool apex;
        /// <summary>Drawn scale over the sheet's true size (ppu kept). The Veil Serpent is drawn 3× so the apex dominates the deck (LEAD, U-055 review).</summary>
        public float artScale = 1f;

        public bool Flies => habitat != Habitat.Ground;

        static readonly SpeciesSpec[] All =
        {
            new SpeciesSpec { id = Species.Stag, planet = PlanetId.Earth, artKey = "creatures/earth/stag", size = new Vector2(1.9f, 1.6f),
                wanderSpeed = 1.2f, runSpeed = 9f, jumpSpeed = 6.5f, temper = Temper.Flees, senseRange = 8f, time = ActiveTime.Any,
                packMin = 1, packMax = 3, maxAlive = 6, placeholder = new Color(0.55f, 0.38f, 0.22f) },
            new SpeciesSpec { id = Species.GreyWolf, planet = PlanetId.Earth, artKey = "creatures/earth/wolf", size = new Vector2(1.5f, 0.9f),
                wanderSpeed = 1.6f, runSpeed = 7.5f, jumpSpeed = 6f, temper = Temper.Hunts, senseRange = 14f, time = ActiveTime.Night,
                packMin = 2, packMax = 4, maxAlive = 8, placeholder = new Color(0.45f, 0.47f, 0.5f) },
            new SpeciesSpec { id = Species.Dustskater, planet = PlanetId.Mars, artKey = "creatures/mars/dustskater", size = new Vector2(0.8f, 0.45f),
                wanderSpeed = 2.2f, runSpeed = 8f, jumpSpeed = 5f, temper = Temper.Flees, senseRange = 5f, time = ActiveTime.Any,
                packMin = 1, packMax = 4, maxAlive = 8, placeholder = new Color(0.75f, 0.55f, 0.35f) },
            new SpeciesSpec { id = Species.ScreeStalker, planet = PlanetId.Mars, artKey = "creatures/mars/scree_stalker", size = new Vector2(1.6f, 1.0f),
                wanderSpeed = 1.4f, runSpeed = 7f, jumpSpeed = 7f, temper = Temper.Hunts, senseRange = 12f, time = ActiveTime.Any,
                packMin = 2, packMax = 3, maxAlive = 6, placeholder = new Color(0.42f, 0.3f, 0.26f) },

            // Mercury (Bible §7.3). Mercury's low gravity (0.38 g) carries every hop further.
            new SpeciesSpec { id = Species.Glassback, planet = PlanetId.Mercury, artKey = "creatures/mercury/glassback", size = new Vector2(1.6f, 1.2f),
                wanderSpeed = 1.0f, runSpeed = 5f, jumpSpeed = 4f, temper = Temper.Flees, senseRange = 7f, time = ActiveTime.Any,
                packMin = 1, packMax = 3, maxAlive = 6, placeholder = new Color(0.7f, 0.75f, 0.8f) },
            new SpeciesSpec { id = Species.Cinderling, planet = PlanetId.Mercury, artKey = "creatures/mercury/cinderling", size = new Vector2(0.55f, 0.35f),
                wanderSpeed = 2.4f, runSpeed = 7.5f, jumpSpeed = 4f, temper = Temper.Hunts, senseRange = 10f, time = ActiveTime.Any,
                packMin = 3, packMax = 6, maxAlive = 10, placeholder = new Color(0.9f, 0.45f, 0.2f) },
            new SpeciesSpec { id = Species.Flarewing, planet = PlanetId.Mercury, artKey = "creatures/mercury/flarewing", size = new Vector2(1.0f, 0.75f),
                wanderSpeed = 3f, runSpeed = 9f, temper = Temper.Flees, senseRange = 9f, time = ActiveTime.Any, habitat = Habitat.Air,
                hoverMin = 4f, hoverMax = 9f, huntsDuringFlare = true,
                packMin = 1, packMax = 2, maxAlive = 4, placeholder = new Color(1f, 0.85f, 0.4f) },
            new SpeciesSpec { id = Species.Shadewyrm, planet = PlanetId.Mercury, artKey = "creatures/mercury/shadewyrm", size = new Vector2(2.3f, 0.7f),
                wanderSpeed = 1.2f, runSpeed = 6f, jumpSpeed = 4f, temper = Temper.Hunts, senseRange = 11f, time = ActiveTime.Any,
                packMin = 1, packMax = 2, maxAlive = 3, placeholder = new Color(0.55f, 0.65f, 0.8f) },
            new SpeciesSpec { id = Species.Cinderhulk, planet = PlanetId.Mercury, artKey = "creatures/mercury/cinderhulk_day", nightArtKey = "creatures/mercury/cinderhulk_night",
                size = new Vector2(3.0f, 1.9f), wanderSpeed = 0.8f, runSpeed = 2.6f, jumpSpeed = 4f, temper = Temper.Hunts, senseRange = 16f, time = ActiveTime.Any,
                packMin = 1, packMax = 1, maxAlive = 1, apex = true, placeholder = new Color(0.95f, 0.95f, 0.9f) },

            // Venus (Bible §7.4).
            new SpeciesSpec { id = Species.SulfurDrifter, planet = PlanetId.Venus, artKey = "creatures/venus/sulfur_drifter", size = new Vector2(1.6f, 1.6f),
                wanderSpeed = 1.0f, runSpeed = 2.5f, temper = Temper.Flees, senseRange = 6f, time = ActiveTime.Any, habitat = Habitat.Deck,
                packMin = 1, packMax = 3, maxAlive = 6, placeholder = new Color(0.9f, 0.85f, 0.4f) },
            new SpeciesSpec { id = Species.Acidmoth, planet = PlanetId.Venus, artKey = "creatures/venus/acidmoth", size = new Vector2(0.4f, 0.4f),
                wanderSpeed = 2.5f, runSpeed = 5f, temper = Temper.Hunts, senseRange = 12f, time = ActiveTime.Any, habitat = Habitat.Deck,
                packMin = 3, packMax = 6, maxAlive = 10, placeholder = new Color(0.8f, 0.9f, 0.5f) },
            new SpeciesSpec { id = Species.PressureCrab, planet = PlanetId.Venus, artKey = "creatures/venus/pressure_crab", size = new Vector2(1.9f, 1.2f),
                wanderSpeed = 0.7f, runSpeed = 2.2f, jumpSpeed = 4f, temper = Temper.Hunts, senseRange = 5f, time = ActiveTime.Any,
                packMin = 1, packMax = 2, maxAlive = 4, placeholder = new Color(0.4f, 0.3f, 0.3f) },
            new SpeciesSpec { id = Species.VentEel, planet = PlanetId.Venus, artKey = "creatures/venus/vent_eel", size = new Vector2(2.0f, 0.55f),
                wanderSpeed = 1.6f, runSpeed = 6f, jumpSpeed = 5f, temper = Temper.Hunts, senseRange = 10f, time = ActiveTime.Any,
                packMin = 1, packMax = 3, maxAlive = 5, placeholder = new Color(0.8f, 0.35f, 0.2f) },
            new SpeciesSpec { id = Species.VeilSerpent, planet = PlanetId.Venus, artKey = "creatures/venus/veil_serpent", size = new Vector2(9.8f, 2.3f), artScale = 3f,
                wanderSpeed = 2.5f, runSpeed = 6.5f, temper = Temper.Hunts, senseRange = 18f, time = ActiveTime.Any, habitat = Habitat.Deck,
                packMin = 1, packMax = 1, maxAlive = 1, apex = true, placeholder = new Color(0.95f, 0.7f, 0.5f) },
        };

        public static SpeciesSpec Get(Species s) => All[(int)s];
        public static int Count => All.Length;

        /// <summary>Whether this species may spawn on a column whose surface tile is `surfaceTile` at height `surfaceY`.</summary>
        public bool BiomeAllows(byte surfaceTile, int surfaceY, int datumY) =>
            Allows(new SpawnSite { surfaceTile = surfaceTile, surfaceY = surfaceY, datumY = datumY, planet = planet });

        /// <summary>The spawn rule (U-055: Mercury zones and cold traps, Venus features and the deck).</summary>
        public bool Allows(SpawnSite s) => id switch
        {
            Species.Stag => s.surfaceTile == TileId.Grass,                       // meadows and forest floor
            Species.GreyWolf => s.surfaceTile == TileId.Grass || s.surfaceTile == TileId.Snow,
            Species.Dustskater => s.surfaceTile == TileId.Regolith,
            Species.ScreeStalker => s.surfaceTile == TileId.Regolith && s.surfaceY <= s.datumY - 12, // low ground: canyon floors
            Species.Glassback => s.zone == MercuryZone.Twilight && !InColdTrap(s),
            // Dawn side of the band: local time just around the dawn line (0.25).
            Species.Cinderling => s.zone == MercuryZone.Twilight && s.localTime > 0.15f && s.localTime < 0.35f && !InColdTrap(s),
            Species.Flarewing => s.zone != MercuryZone.Night && !InColdTrap(s),
            Species.Shadewyrm => InColdTrap(s),
            Species.Cinderhulk => s.zone == MercuryZone.Twilight && !InColdTrap(s),
            Species.SulfurDrifter or Species.Acidmoth or Species.VeilSerpent => OnDeck(s.playerY),
            // The real surface, far under the deck stations (whose platforms also count as "top solid").
            Species.PressureCrab => s.surfaceY < VenusLandforms.DeckY - 200f && VenusLandforms.At(s.x) != VenusFeature.VentField,
            Species.VentEel => s.surfaceY < VenusLandforms.DeckY - 200f && VenusLandforms.At(s.x) == VenusFeature.VentField,
            _ => false,
        };

        static bool InColdTrap(SpawnSite s) => s.worldWidth > 0 && MercuryLandforms.InColdTrap(s.x, s.worldWidth);

        /// <summary>Whether height y lies in reach of the cloud deck (the band plus a margin).</summary>
        public static bool OnDeck(float y) => Mathf.Abs(y - VenusLandforms.DeckY) <= VenusLandforms.DeckHalfBand + 20f;

        /// <summary>Whether the species is out at this daylight level (0 night … 1 day).</summary>
        public bool ActiveAt(float daylight) => time switch
        {
            ActiveTime.Night => daylight < 0.3f,
            ActiveTime.Day => daylight > 0.7f,
            _ => true,
        };
    }

    /// <summary>U-055 apex rules (Bible §7.3, §7.4). Pure.</summary>
    public static class ApexRules
    {
        /// <summary>The Cinderhulk's shell cools and cracks for this long after it crosses into night.</summary>
        public const float CinderhulkWindow = 120f;

        /// <summary>The Cinderhulk takes damage only on the night side, within the window after it crossed over.</summary>
        public static bool CinderhulkVulnerable(MercuryZone zone, float secondsSinceNightfall) =>
            zone == MercuryZone.Night && secondsSinceNightfall >= 0f && secondsSinceNightfall <= CinderhulkWindow;

        /// <summary>The Veil Serpent takes damage only from Cryo rounds (it flees cold).</summary>
        public static bool VeilSerpentHurtBy(bool cryo) => cryo;

        /// <summary>Whether a hit of this kind can hurt this species right now.</summary>
        public static bool CanHurt(Species s, bool cryo, MercuryZone zone, float secondsSinceNightfall) => s switch
        {
            Species.Cinderhulk => CinderhulkVulnerable(zone, secondsSinceNightfall),
            Species.VeilSerpent => VeilSerpentHurtBy(cryo),
            _ => true,
        };
    }
}
