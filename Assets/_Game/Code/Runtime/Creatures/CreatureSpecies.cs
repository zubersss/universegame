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
        /// <summary>U-101 / B-113: the C0 Earth critter, a small gull that flees (v3 sheet creatures/earth/gull). Last: the table is indexed by this value.</summary>
        Gull,
        // U-114 (D-119, B-132): the brown bear, territorial (Bible §7.1); last so every older index stays.
        BrownBear,
        // U-114 (B-135, cycle 259): the Earth swimmers, Water habitat; appended so every older index stays.
        Pike, Shark, Squid,
        // U-119 (B-136, D-127): the Hadal Maw, a rig-set creature of the coast deep; appended so every older index stays.
        HadalMaw,
    }

    /// <summary>What a creature does about the player.</summary>
    /// <summary>U-114: Territorial holds its ground (faces, rears, huffs) within senseRange and bolts when pushed inside CreatureDirector.PushRange.</summary>
    public enum Temper { Flees, Hunts, Territorial }

    public enum ActiveTime { Any, Day, Night }

    /// <summary>
    /// Where a creature lives (U-055): on the ground under gravity; in the air a few metres over the ground
    /// (hoverMin..hoverMax); or on Venus's cloud deck (VenusLandforms.DeckY ± DeckHalfBand).
    /// </summary>
    /// <summary>U-114: Water swims between its floor clearance and the surface of a water column, turning at the pool's walls.</summary>
    public enum Habitat { Ground, Air, Deck, Water }

    /// <summary>What a spawn rule sees of one candidate column (U-055).</summary>
    public struct SpawnSite
    {
        public int x, surfaceY, datumY, worldWidth;
        public byte surfaceTile;
        /// <summary>U-114: the tile just above the top solid (Water over a pool floor) and how many water tiles stand on it.</summary>
        public byte aboveTile;
        public int waterDepth;
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
        /// <summary>U-114: a swimmer's clearance above the pool floor (B-135: pike 0.38, shark 0.87, squid 0.70 m).</summary>
        public float floorClearance;
        /// <summary>U-114: the water a swimmer needs over the floor: its own height plus its floor clearance.</summary>
        public float WaterDepthNeeded => size.y + floorClearance;
        public bool Swims => habitat == Habitat.Water;
        /// <summary>Flarewing: hunts while a solar flare is active, keeps clear otherwise.</summary>
        public bool huntsDuringFlare;
        public bool apex;
        /// <summary>Drawn scale over the sheet's true size (ppu kept). The Veil Serpent is drawn 3× so the apex dominates the deck (LEAD, U-055 review).</summary>
        public float artScale = 1f;
        /// <summary>U-119: a rig-set creature (a contract §11.3 json under artKey): the view is RigBuild's rig, not a frame sheet; the director loads no sheet for it.</summary>
        public bool rig;
        /// <summary>U-119 (D-087): a hunter that keeps this distance (m) from the surveyor instead of bumping them (0 = none): the Maw follows and startles.</summary>
        public float followDistance;
        /// <summary>U-119: the rig's react (the jaw opens, the lure flares) within this many metres of the surveyor (0 = never).</summary>
        public float reactRadius;

        public bool Flies => habitat != Habitat.Ground;

        static readonly SpeciesSpec[] All =
        {
            new SpeciesSpec { id = Species.Stag, planet = PlanetId.Earth, artKey = "creatures/earth/stag", size = new Vector2(1.5f, 2.0f), // U-114: the B-132 sheet, antler tips at 2 m
                wanderSpeed = 1.2f, runSpeed = 9f, jumpSpeed = 6.5f, temper = Temper.Flees, senseRange = 8f, time = ActiveTime.Any,
                packMin = 1, packMax = 3, maxAlive = 6, placeholder = new Color(0.55f, 0.38f, 0.22f) },
            new SpeciesSpec { id = Species.GreyWolf, planet = PlanetId.Earth, artKey = "creatures/earth/wolf", size = new Vector2(1.2f, 1.0f), // U-114: the B-132 sheet
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
            new SpeciesSpec { id = Species.Gull, planet = PlanetId.Earth, artKey = "creatures/earth/gull", size = new Vector2(0.7f, 0.5f),
                wanderSpeed = 2.5f, runSpeed = 7f, temper = Temper.Flees, senseRange = 6f, time = ActiveTime.Day, habitat = Habitat.Air,
                hoverMin = 2f, hoverMax = 5f, packMin = 1, packMax = 2, maxAlive = 3, placeholder = new Color(0.92f, 0.92f, 0.88f) },
            // U-114 (D-119, B-132): the brown bear, Bible §7.1 territorial: holds its ground, rears and huffs (react) within 6 m, bolts when pushed (D-087: no bites).
            new SpeciesSpec { id = Species.BrownBear, planet = PlanetId.Earth, artKey = "creatures/earth/bear", size = new Vector2(2.1f, 1.3f),
                wanderSpeed = 1.1f, runSpeed = 6.5f, jumpSpeed = 4.5f, temper = Temper.Territorial, senseRange = 6f, time = ActiveTime.Any,
                packMin = 1, packMax = 1, maxAlive = 2, placeholder = new Color(0.45f, 0.28f, 0.18f) },
            // U-114 (B-135): the Earth swimmers on their v3 sheets (idle, swim, react, bump, flee), pivot centre, sizes from the frames at PPU 64;
            // they spawn in water deep enough for their height plus floor clearance and swim between that clearance and the surface.
            new SpeciesSpec { id = Species.Pike, planet = PlanetId.Earth, artKey = "creatures/earth/pike", size = new Vector2(2.0f, 1.25f), floorClearance = 0.38f,
                wanderSpeed = 1.5f, runSpeed = 5f, temper = Temper.Flees, senseRange = 5f, time = ActiveTime.Any, habitat = Habitat.Water,
                packMin = 2, packMax = 4, maxAlive = 6, placeholder = new Color(0.45f, 0.6f, 0.4f) },
            new SpeciesSpec { id = Species.Shark, planet = PlanetId.Earth, artKey = "creatures/earth/shark", size = new Vector2(3.5f, 2.0f), floorClearance = 0.87f,
                wanderSpeed = 1.2f, runSpeed = 6f, temper = Temper.Territorial, senseRange = 7f, time = ActiveTime.Any, habitat = Habitat.Water,
                packMin = 1, packMax = 1, maxAlive = 2, placeholder = new Color(0.5f, 0.55f, 0.62f) },
            new SpeciesSpec { id = Species.Squid, planet = PlanetId.Earth, artKey = "creatures/earth/squid", size = new Vector2(5.0f, 2.25f), floorClearance = 0.70f,
                wanderSpeed = 0.9f, runSpeed = 4.5f, temper = Temper.Flees, senseRange = 6f, time = ActiveTime.Any, habitat = Habitat.Water,
                packMin = 1, packMax = 1, maxAlive = 2, placeholder = new Color(0.8f, 0.5f, 0.55f) },
            // U-119 (B-136, D-127): the Hadal Maw — ~34 m of rig in the coast deep (Bible §7.1: a set piece over two screens). It hunts only in the
            // sense of following: it holds 14 m off and startles with its react (D-087: no attack); the water it needs (5 + 15 m) keeps it out of the camp's pools.
            new SpeciesSpec { id = Species.HadalMaw, planet = PlanetId.Earth, artKey = "creatures/earth/hadal_maw", rig = true, size = new Vector2(16f, 5f), floorClearance = 15f,
                wanderSpeed = 1.5f, runSpeed = 3.5f, temper = Temper.Hunts, senseRange = 40f, followDistance = 14f, reactRadius = 12f, time = ActiveTime.Any, habitat = Habitat.Water,
                packMin = 1, packMax = 1, maxAlive = 1, placeholder = new Color(0.12f, 0.2f, 0.26f) },
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
            Species.BrownBear => s.surfaceTile == TileId.Grass,                  // U-114: forest floor and meadows, like the stag
            Species.Gull => s.surfaceTile == TileId.Grass || s.surfaceTile == TileId.Sand,
            // U-114: a swimmer wants water over the floor at least as deep as its own height plus its floor clearance.
            Species.Pike or Species.Shark or Species.Squid or Species.HadalMaw => s.aboveTile == TileId.Water && s.waterDepth >= WaterDepthNeeded,
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
