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
        // U-118 (B-142, D-126): the Mars lava-tube lurker (a den species) and the polar crawler; appended so every older index stays.
        TubeLurker, PolarCrawler,
        // U-127 (B-160, Bible §7.6): Jupiter's floaters of the cloud decks; appended so every older index stays (the Vortex Whale follows with its re-export, D-153).
        Stormglider, LightningEel, BeltWasp, BallastTortoise,
        // U-127 (B-160, D-138 / D-153): Jupiter's apex, a Grand rig set ~36 m long, appended after the floaters.
        VortexWhale,
    }

    /// <summary>What a creature does about the player.</summary>
    /// <summary>U-114: Territorial holds its ground (faces, rears, huffs) within senseRange and bolts when pushed inside CreatureDirector.PushRange.</summary>
    /// <summary>U-192 (LEAD cycle 291, with B-224's passive redraw): Drifts meanders along its lane and parts around the Pilgrim (or the
    /// surveyor on foot) inside senseRange, swerving away in height with its `attack` clip as the swerve; it never chases and never bumps.</summary>
    public enum Temper { Flees, Hunts, Territorial, Drifts }

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
        /// <summary>U-118 (D-126): a den species' static den prop (props/mars/tube_mound): the creature spawns at one, idles (the peek) and reacts there behind it, walks in the open; null = no den.</summary>
        public string den;
        /// <summary>U-118: how far from its den a den species still counts as at it (the peek clip), metres.</summary>
        public float denRange = 2.5f;
        public bool HasDen => !string.IsNullOrEmpty(den);

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
            new SpeciesSpec { id = Species.Shadewyrm, planet = PlanetId.Mercury, artKey = "creatures/mercury/shadewyrm", den = "props/mercury/ice_burrow", size = new Vector2(2.3f, 0.7f), // U-123 (D-126): it peeks from its burrow, a separate prop (B-150)
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
            new SpeciesSpec { id = Species.VentEel, planet = PlanetId.Venus, artKey = "creatures/venus/vent_eel", den = "props/venus/vent_mouth", size = new Vector2(2.0f, 0.55f), // U-125 (D-126): it peeks from its vent, a separate prop (B-154)
                wanderSpeed = 1.6f, runSpeed = 6f, jumpSpeed = 5f, temper = Temper.Hunts, senseRange = 10f, time = ActiveTime.Any,
                packMin = 1, packMax = 3, maxAlive = 5, placeholder = new Color(0.8f, 0.35f, 0.2f) },
            // U-192 (G6, ruled 11-09): B-224's v3 sheet draws the serpent 224 px long at 64 px a metre: a 3.5 m serpent drawn at 1x (the game
            // still drew it 3x, as for the v2 sheet: about 600 px on screen, its ink three times heavier than the station's and soft). With
            // the redraw's passive look: a gentle drifter (Temper.Drifts) that parts around the ship inside 8 m; it hunted from 18 m.
            new SpeciesSpec { id = Species.VeilSerpent, planet = PlanetId.Venus, artKey = "creatures/venus/veil_serpent", size = new Vector2(3.5f, 1.0f),
                wanderSpeed = 2.5f, runSpeed = 6.5f, temper = Temper.Drifts, senseRange = 8f, time = ActiveTime.Any, habitat = Habitat.Deck,
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
            // U-118 (B-142, D-126): the lava-tube lurker — a shy peeker at its mound over the tubes (idle = the peek at the den, idle_open away from it); the polar crawler — slow and armoured on the ice caps.
            new SpeciesSpec { id = Species.TubeLurker, planet = PlanetId.Mars, artKey = "creatures/mars/tube_lurker", den = "props/mars/tube_mound", size = new Vector2(1.2f, 0.7f),
                wanderSpeed = 1.0f, runSpeed = 4.5f, jumpSpeed = 4f, temper = Temper.Flees, senseRange = 6f, time = ActiveTime.Any,
                packMin = 1, packMax = 1, maxAlive = 2, placeholder = new Color(0.36f, 0.3f, 0.26f) },
            new SpeciesSpec { id = Species.PolarCrawler, planet = PlanetId.Mars, artKey = "creatures/mars/polar_crawler", size = new Vector2(1.4f, 0.8f),
                wanderSpeed = 0.6f, runSpeed = 1.6f, jumpSpeed = 2f, temper = Temper.Flees, senseRange = 4f, time = ActiveTime.Any,
                packMin = 1, packMax = 2, maxAlive = 4, placeholder = new Color(0.55f, 0.6f, 0.45f) },
            // U-127 (B-160, Bible §7.6): Jupiter's floaters over the floes (Air habitat: they hover above the floe they spawn over). The Stormglider
            // rides every deck's wind; the Lightning eel is Deck 2's, curious (it keeps clear: D-087, never a bite); the Belt wasps swarm Deck 1
            // (blunt tails, no sting); the Ballast tortoise paddles slow and huge through Decks 2–3 (its husk prop comes with the hunt card).
            new SpeciesSpec { id = Species.Stormglider, planet = PlanetId.Jupiter, artKey = "creatures/jupiter/stormglider", size = new Vector2(2.4f, 1.0f),
                wanderSpeed = 3f, runSpeed = 8f, temper = Temper.Flees, senseRange = 9f, time = ActiveTime.Any, habitat = Habitat.Air,
                hoverMin = 4f, hoverMax = 10f, packMin = 1, packMax = 2, maxAlive = 4, placeholder = new Color(0.93f, 0.89f, 0.8f) },
            new SpeciesSpec { id = Species.LightningEel, planet = PlanetId.Jupiter, artKey = "creatures/jupiter/lightning_eel", size = new Vector2(1.8f, 0.5f),
                wanderSpeed = 2.2f, runSpeed = 6f, temper = Temper.Flees, senseRange = 8f, time = ActiveTime.Any, habitat = Habitat.Air,
                hoverMin = 2f, hoverMax = 6f, packMin = 1, packMax = 2, maxAlive = 4, placeholder = new Color(0.44f, 0.54f, 0.59f) },
            new SpeciesSpec { id = Species.BeltWasp, planet = PlanetId.Jupiter, artKey = "creatures/jupiter/belt_wasp", size = new Vector2(0.5f, 0.4f),
                wanderSpeed = 2.8f, runSpeed = 6f, temper = Temper.Hunts, senseRange = 10f, time = ActiveTime.Any, habitat = Habitat.Air,
                hoverMin = 2f, hoverMax = 5f, packMin = 3, packMax = 6, maxAlive = 10, placeholder = new Color(0.77f, 0.54f, 0.31f) },
            new SpeciesSpec { id = Species.BallastTortoise, planet = PlanetId.Jupiter, artKey = "creatures/jupiter/ballast_tortoise", size = new Vector2(4f, 2.5f),
                wanderSpeed = 0.6f, runSpeed = 1.4f, temper = Temper.Flees, senseRange = 6f, time = ActiveTime.Any, habitat = Habitat.Air,
                hoverMin = 4f, hoverMax = 9f, packMin = 1, packMax = 1, maxAlive = 2, placeholder = new Color(0.66f, 0.31f, 0.23f) },
            // U-127 (B-160, Bible §7.6): the Vortex Whale, a Grand rig set (six bones) drawn ~36 m long (D-153) and seen in passing (D-138: no shot
            // holds both ends); it glides slow through the Great Red Spot over Decks 1-2, one at a time. Its song and the harpoon are their own cards.
            new SpeciesSpec { id = Species.VortexWhale, planet = PlanetId.Jupiter, artKey = "creatures/jupiter/vortex_whale", rig = true, size = new Vector2(17f, 6f),
                wanderSpeed = 1.2f, runSpeed = 2.5f, temper = Temper.Flees, senseRange = 30f, reactRadius = 14f, time = ActiveTime.Any, habitat = Habitat.Air,
                hoverMin = 8f, hoverMax = 18f, packMin = 1, packMax = 1, maxAlive = 1, placeholder = new Color(0.62f, 0.36f, 0.3f) },
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
            // U-127: by the band of the floe under the spawn (Bible §7.6): the glider in every deck, the eel in Deck 2, the wasps in Deck 1, the tortoise in Decks 2–3.
            Species.Stormglider => JupiterBand(s) == Meridian.Terrain.CloudColumn.CloudBand.Deck1 || JupiterBand(s) == Meridian.Terrain.CloudColumn.CloudBand.Deck2 || JupiterBand(s) == Meridian.Terrain.CloudColumn.CloudBand.Deck3,
            Species.LightningEel => JupiterBand(s) == Meridian.Terrain.CloudColumn.CloudBand.Deck2,
            Species.BeltWasp => JupiterBand(s) == Meridian.Terrain.CloudColumn.CloudBand.Deck1,
            Species.BallastTortoise => JupiterBand(s) == Meridian.Terrain.CloudColumn.CloudBand.Deck2 || JupiterBand(s) == Meridian.Terrain.CloudColumn.CloudBand.Deck3,
            Species.VortexWhale => Meridian.Terrain.CloudColumn.CloudLayout.InRedSpot(s.x) && (JupiterBand(s) == Meridian.Terrain.CloudColumn.CloudBand.Deck1 || JupiterBand(s) == Meridian.Terrain.CloudColumn.CloudBand.Deck2), // U-127: the Red Spot's
            Species.TubeLurker => (s.surfaceTile == TileId.Regolith || s.surfaceTile == TileId.Basalt) && MarsLandforms.OverTube(s.x), // U-118 (D-126): its dens sit over the lava tubes
            Species.PolarCrawler => s.surfaceTile == TileId.Ice, // U-118: the ice caps
            Species.Glassback => s.zone == MercuryZone.Twilight && !InColdTrap(s),
            // Dawn side of the band: local time just around the dawn line (0.25).
            Species.Cinderling => s.zone == MercuryZone.Twilight && s.localTime > 0.15f && s.localTime < 0.35f && !InColdTrap(s),
            Species.Flarewing => s.zone != MercuryZone.Night && !InColdTrap(s),
            Species.Shadewyrm => InColdTrap(s),
            Species.Cinderhulk => false, // U-138 (D-150): out of Mercury's spawn table - a v2 lava model beside the inked set; the Cinderling is its B-145 re-ink
            Species.SulfurDrifter or Species.Acidmoth or Species.VeilSerpent => OnDeck(s.playerY),
            // The real surface, far under the deck stations (whose platforms also count as "top solid").
            Species.PressureCrab => s.surfaceY < VenusLandforms.DeckY - 200f && VenusLandforms.At(s.x) != VenusFeature.VentField,
            Species.VentEel => s.surfaceY < VenusLandforms.DeckY - 200f && VenusLandforms.At(s.x) == VenusFeature.VentField,
            _ => false,
        };

        static bool InColdTrap(SpawnSite s) => s.worldWidth > 0 && MercuryLandforms.InColdTrap(s.x, s.worldWidth);
        /// <summary>U-127: the cloud band of the floe a Jupiter spawn site stands over (its surface height).</summary>
        static Meridian.Terrain.CloudColumn.CloudBand JupiterBand(SpawnSite s) => Meridian.Terrain.CloudColumn.CloudLayout.BandAt(s.surfaceY);

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
