using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Creatures
{
    public enum Species { Stag, GreyWolf, Dustskater, ScreeStalker }

    /// <summary>What a creature does about the player.</summary>
    public enum Temper { Flees, Hunts }

    public enum ActiveTime { Any, Day, Night }

    /// <summary>
    /// U-027 roster v1 (Bible §7.1 Earth: stag grazer flees, grey wolf pack at night; §7.2 Mars:
    /// dustskater small scavenger, scree stalker pack hunter in canyons). Sizes in metres; speeds in m/s.
    /// </summary>
    public sealed class SpeciesSpec
    {
        public Species id;
        public PlanetId planet;
        public string artKey;
        public Vector2 size;
        public float wanderSpeed, runSpeed, jumpSpeed;
        public Temper temper;
        /// <summary>Flee: distance at which it bolts. Hunt: distance at which it starts the chase.</summary>
        public float senseRange;
        public ActiveTime time;
        public int packMin, packMax;
        public int maxAlive;
        public float biteDamage;
        public Color placeholder;

        static readonly SpeciesSpec[] All =
        {
            new SpeciesSpec { id = Species.Stag, planet = PlanetId.Earth, artKey = "creatures/earth/stag", size = new Vector2(1.9f, 1.6f),
                wanderSpeed = 1.2f, runSpeed = 9f, jumpSpeed = 6.5f, temper = Temper.Flees, senseRange = 8f, time = ActiveTime.Any,
                packMin = 1, packMax = 3, maxAlive = 6, placeholder = new Color(0.55f, 0.38f, 0.22f) },
            new SpeciesSpec { id = Species.GreyWolf, planet = PlanetId.Earth, artKey = "creatures/earth/wolf", size = new Vector2(1.5f, 0.9f),
                wanderSpeed = 1.6f, runSpeed = 7.5f, jumpSpeed = 6f, temper = Temper.Hunts, senseRange = 14f, time = ActiveTime.Night,
                packMin = 2, packMax = 4, maxAlive = 8, biteDamage = 8f, placeholder = new Color(0.45f, 0.47f, 0.5f) },
            new SpeciesSpec { id = Species.Dustskater, planet = PlanetId.Mars, artKey = "creatures/mars/dustskater", size = new Vector2(0.8f, 0.45f),
                wanderSpeed = 2.2f, runSpeed = 8f, jumpSpeed = 5f, temper = Temper.Flees, senseRange = 5f, time = ActiveTime.Any,
                packMin = 1, packMax = 4, maxAlive = 8, placeholder = new Color(0.75f, 0.55f, 0.35f) },
            new SpeciesSpec { id = Species.ScreeStalker, planet = PlanetId.Mars, artKey = "creatures/mars/scree_stalker", size = new Vector2(1.6f, 1.0f),
                wanderSpeed = 1.4f, runSpeed = 7f, jumpSpeed = 7f, temper = Temper.Hunts, senseRange = 12f, time = ActiveTime.Any,
                packMin = 2, packMax = 3, maxAlive = 6, biteDamage = 10f, placeholder = new Color(0.42f, 0.3f, 0.26f) },
        };

        public static SpeciesSpec Get(Species s) => All[(int)s];
        public static int Count => All.Length;

        /// <summary>Whether this species may spawn on a column whose surface tile is `surfaceTile` at height `surfaceY`.</summary>
        public bool BiomeAllows(byte surfaceTile, int surfaceY, int datumY) => id switch
        {
            Species.Stag => surfaceTile == TileId.Grass,                       // meadows and forest floor
            Species.GreyWolf => surfaceTile == TileId.Grass || surfaceTile == TileId.Snow,
            Species.Dustskater => surfaceTile == TileId.Regolith,
            Species.ScreeStalker => surfaceTile == TileId.Regolith && surfaceY <= datumY - 12, // low ground: canyon floors
            _ => false,
        };

        /// <summary>Whether the species is out at this daylight level (0 night … 1 day).</summary>
        public bool ActiveAt(float daylight) => time switch
        {
            ActiveTime.Night => daylight < 0.3f,
            ActiveTime.Day => daylight > 0.7f,
            _ => true,
        };
    }
}
