using Meridian.Art;

namespace Meridian.Terrain
{
    /// <summary>Tile ids stored in chunk data and terrain diffs. 0 is always air.</summary>
    public static class TileId
    {
        public const byte Air = 0;
        public const byte Soil = 1, Grass = 2, Stone = 3, Sand = 4, Snow = 5, Water = 6;
        public const byte Regolith = 7, Basalt = 8, Hematite = 9, Ice = 10;
        public const int Count = 11;

        static readonly string[] Keys =
        {
            null,
            ArtKeys.Terrain.EarthSoil, ArtKeys.Terrain.EarthGrass, ArtKeys.Terrain.EarthStone,
            ArtKeys.Terrain.EarthSand, ArtKeys.Terrain.EarthSnow, ArtKeys.Terrain.EarthWater,
            ArtKeys.Terrain.MarsRegolith, ArtKeys.Terrain.MarsBasalt, ArtKeys.Terrain.MarsHematite,
            ArtKeys.Terrain.MarsIce,
        };

        public static string ArtKey(byte id) => id < Keys.Length ? Keys[id] : null;
        public static bool IsLiquid(byte id) => id == Water;
        public static bool IsSolid(byte id) => id != Air && id != Water;
    }

    public static class TerrainConstants
    {
        public const int ChunkSize = 32;
        public const int TilesPerChunk = ChunkSize * ChunkSize;
        /// <summary>Chunks within this Chebyshev distance of the camera's chunk stay resident (Bible §10.4).</summary>
        public const int ResidentRadius = 2;
        /// <summary>Main-thread budget for applying generated chunks, per frame (Bible §11.1).</summary>
        public const double ApplyBudgetMs = 2.0;
        /// <summary>Bands are planned against this soft limit so one unexpected slow band still lands under ApplyBudgetMs.</summary>
        public const double ApplyPlanMs = 1.0;
        public const int TileSheetColumns = 8;
        public const int TileSheetPixels = 128;
    }
}
