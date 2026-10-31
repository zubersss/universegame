using Meridian.Planets;
using Meridian.Terrain;

namespace Meridian.Planet.POI
{
    /// <summary>
    /// U-030: merges a POI's tile stamp into a planet's terrain as diffs (TerrainEdits), once per world.
    /// Pure: works on the base generator and an edits store, before or after the terrain streams.
    /// </summary>
    public static class PoiStamp
    {
        /// <summary>The stamp's ground line: the surface at its center column, never below sea level (the Datum).</summary>
        public static int GroundY(PoiDef poi, IWorldGenerator world, int datumY)
        {
            int cx = Wrap(poi.x + poi.Width / 2, world.Width);
            int s = world.SurfaceHeight(cx);
            return s < datumY + 1 ? datumY + 1 : s;
        }

        /// <summary>World tile y of stamp row `row` (rows run top to bottom).</summary>
        public static int RowY(PoiDef poi, int row, int groundY) => groundY + (poi.groundRow - row);

        /// <summary>The tile a stamp cell asks for, or null for ' ' (keep the generated tile).</summary>
        public static byte? CellTile(char c, PlanetId planet) => c switch
        {
            '.' => TileId.Air,
            '#' => planet == PlanetId.Earth ? TileId.Stone : TileId.Basalt,
            'g' => planet == PlanetId.Earth ? TileId.Grass : TileId.Regolith,
            _ => (byte?)null,
        };

        /// <summary>Writes the stamp's diffs. Returns the ground line used.</summary>
        public static int Apply(PoiDef poi, IWorldGenerator baseWorld, TerrainEdits edits, int datumY)
        {
            int gy = GroundY(poi, baseWorld, datumY);
            for (int row = 0; row < poi.stamp.Length; row++)
            {
                int y = RowY(poi, row, gy);
                if (y < 0 || y >= baseWorld.Height) continue;
                string line = poi.stamp[row];
                for (int col = 0; col < line.Length; col++)
                {
                    var tile = CellTile(line[col], poi.planet);
                    if (tile == null) continue;
                    int x = Wrap(poi.x + col, baseWorld.Width);
                    edits.Set(x, y, tile.Value, baseWorld.TileAt(x, y));
                }
            }
            return gy;
        }

        public static int Wrap(int x, int w) => ((x % w) + w) % w;
    }
}
