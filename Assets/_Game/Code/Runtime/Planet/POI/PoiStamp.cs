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
        /// <summary>The stamp's ground line: the median surface under it (or the lowest, seatLow), never below Earth's sea.</summary>
        public static int GroundY(PoiDef poi, IWorldGenerator world, int datumY)
        {
            if (poi.Floating) return poi.floatY - 1; // props stand on floatY
            // U-057: the median surface under the stamp (a centre column on a crater rim raised whole mesas).
            var hs = new int[poi.Width];
            for (int i = 0; i < hs.Length; i++) hs[i] = world.SurfaceHeight(Wrap(poi.x + i, world.Width));
            System.Array.Sort(hs);
            int s = poi.seatLow ? hs[0] : hs[hs.Length / 2];
            // Never below sea level, where there is a sea (Earth); dry worlds seat pads in hollows below their Datum (U-057).
            return poi.planet == PlanetId.Earth && s < datumY + 1 ? datumY + 1 : s;
        }

        /// <summary>World tile y of stamp row `row` (rows run top to bottom).</summary>
        public static int RowY(PoiDef poi, int row, int groundY) => groundY + (poi.groundRow - row);

        /// <summary>The tile a stamp cell asks for, or null for ' ' (keep the generated tile).</summary>
        public static byte? CellTile(char c, PlanetId planet) => c switch
        {
            '.' => TileId.Air,
            '#' => planet == PlanetId.Earth ? TileId.Stone : planet == PlanetId.Mercury ? TileId.MercuryBasalt : planet == PlanetId.Venus ? TileId.VenusBasalt : TileId.Basalt,
            'g' => planet == PlanetId.Earth ? TileId.Grass : planet == PlanetId.Mercury ? TileId.MercuryRegolith : planet == PlanetId.Venus ? TileId.VenusBasalt : TileId.Regolith,
            's' => planet == PlanetId.Earth ? TileId.Soil : planet == PlanetId.Mercury ? TileId.MercuryRegolith : planet == PlanetId.Venus ? TileId.VenusBasalt : TileId.Regolith,
            _ => (byte?)null,
        };

        /// <summary>U-057: the steepest step (m) between neighbouring columns at a pad's shoulders.</summary>
        public const int MaxStep = 2;
        /// <summary>How far a shoulder may reach from the pad edge before it gives up blending (m).</summary>
        public const int MaxShoulder = 48;

        /// <summary>
        /// U-057: the ground line a column ends up with around a stamped POI: the pad's ground line across
        /// the stamp, then shoulders that step toward the natural surface by at most MaxStep per column.
        /// False outside the stamp and its shoulders (the natural surface stands).
        /// </summary>
        public static bool ShapedGround(PoiDef poi, IWorldGenerator world, int datumY, int x, out int ground, int padGround = int.MinValue)
        {
            ground = 0;
            if (poi.Floating || poi.stamp == null) return false;
            int w = world.Width, gy = padGround != int.MinValue ? padGround : GroundY(poi, world, datumY); // callers that know it pass it (no per-call median)
            int d = Wrap(x - poi.x, w);
            if (d < poi.Width) { ground = gy; return true; }
            // Right shoulder: d - Width + 1 columns past the right edge; left: w - d columns before the left edge.
            int right = d - poi.Width + 1, left = w - d;
            int k = right <= left ? right : left, dir = right <= left ? 1 : -1;
            if (k > MaxShoulder) return false;
            int edge = dir > 0 ? poi.x + poi.Width - 1 : poi.x;
            int h = gy;
            for (int i = 1; i <= k; i++)
            {
                int natural = world.SurfaceHeight(Wrap(edge + dir * i, w));
                if (natural > h + MaxStep) h += MaxStep;
                else if (natural < h - MaxStep) h -= MaxStep;
                else return false; // blended: the natural surface takes over from here
            }
            ground = h;
            return true;
        }

        /// <summary>Writes the stamp's diffs (pad, the solid fill under it, the cleared air above it and the shoulders). Returns the ground line used.</summary>
        public static int Apply(PoiDef poi, IWorldGenerator baseWorld, TerrainEdits edits, int datumY)
        {
            int gy = GroundY(poi, baseWorld, datumY);
            if (poi.stamp == null) return gy; // floating POIs have no terrain stamp
            byte rock = CellTile('#', poi.planet).Value, top = CellTile('g', poi.planet).Value;
            int bottomRow = RowY(poi, poi.stamp.Length - 1, gy);
            for (int col = -MaxShoulder; col < poi.Width + MaxShoulder; col++)
            {
                int x = Wrap(poi.x + col, baseWorld.Width);
                int natural = baseWorld.SurfaceHeight(x);
                bool inStamp = col >= 0 && col < poi.Width;
                if (!inStamp && !ShapedGround(poi, baseWorld, datumY, x, out _, gy)) continue;
                int ground = gy;
                if (!inStamp) ShapedGround(poi, baseWorld, datumY, x, out ground, gy);
                int fillFrom = inStamp ? bottomRow - 1 : ground;
                // Fill: solid rock down to the natural ground (no gap under a pad or a raised shoulder).
                for (int y = fillFrom; y > natural && y >= 0; y--)
                    if (baseWorld.TileAt(x, y) == TileId.Air) edits.Set(x, y, rock, TileId.Air);
                if (!inStamp)
                {
                    // Shoulder: a surface tile on its ground line, open air above it up to the natural surface.
                    edits.Set(x, ground, top, baseWorld.TileAt(x, ground)); // raised or cut: a surface tile on top
                    for (int y = ground + 1; y <= natural; y++) edits.Set(x, y, TileId.Air, baseWorld.TileAt(x, y));
                }
                else
                {
                    // Above the pad: clear up to the natural surface (no notch with hillside hanging over it).
                    int padTop = RowY(poi, 0, gy);
                    for (int y = padTop + 1; y <= natural; y++) edits.Set(x, y, TileId.Air, baseWorld.TileAt(x, y));
                }
            }
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
