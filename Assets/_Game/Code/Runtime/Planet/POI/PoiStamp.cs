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
            '#' => planet == PlanetId.Earth ? TileId.Stone : planet == PlanetId.Mercury ? TileId.MercuryBasalt : planet == PlanetId.Venus ? TileId.VenusBasalt : planet == PlanetId.Mars ? TileId.Regolith : TileId.Basalt, // D-143 (2): the Mars pad sits on regolith
            'g' => planet == PlanetId.Earth ? TileId.Grass : planet == PlanetId.Mercury ? TileId.MercuryRegolith : planet == PlanetId.Venus ? TileId.VenusBasalt : TileId.Regolith,
            's' => planet == PlanetId.Earth ? TileId.Soil : planet == PlanetId.Mercury ? TileId.MercuryRegolith : planet == PlanetId.Venus ? TileId.VenusBasalt : TileId.Regolith,
            _ => (byte?)null,
        };

        /// <summary>U-057: the steepest step (m) between neighbouring columns at a pad's shoulders.</summary>
        public const int MaxStep = 2;
        /// <summary>How far a shoulder may reach from the pad edge before it gives up blending (m).</summary>
        public const int MaxShoulder = 48;
        /// <summary>U-159: column x (wrapped) lies inside another ground POI's stamp on the same planet.</summary>
        static bool InOtherStamp(PoiDef poi, int x, int width)
        {
            foreach (var o in PoiCatalog.For(poi.planet))
            {
                if (o == poi || o.Floating || o.stamp == null) continue;
                int d = ((x - o.x) % width + width) % width;
                if (d < o.Width) return true;
            }
            return false;
        }

        /// <summary>U-156: a smooth planet's shoulder grade (metres per column): under the walkable limit (tan 35°) once the curve eases it.</summary>
        public const float SmoothShoulder = 0.65f; // steeper than the natural hills' 0.6 (GroundField.SurfaceSlope), so a shoulder always meets them
        /// <summary>U-156: how far a smooth planet's shoulder may reach (columns): 0.65 over 240 columns blends 156 m.</summary>
        public const int SmoothMaxShoulder = 240;

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
            // U-156 (D-161): on a smooth planet the shoulder eases at 1 in 2 (the drawn curve stays walkable) and may run SmoothMaxShoulder
            // columns (80 m of height) so it always meets the natural surface; else MaxStep per column over MaxShoulder as before.
            bool smoothShoulder = world is Meridian.Terrain.SolidWorldGenerator s && s.SmoothGround;
            if (k > (smoothShoulder ? SmoothMaxShoulder : MaxShoulder)) return false;
            int edge = dir > 0 ? poi.x + poi.Width - 1 : poi.x;
            int h = gy;
            float slope = smoothShoulder ? SmoothShoulder : MaxStep;
            for (int i = 1; i <= k; i++)
            {
                int natural = world.SurfaceHeight(Wrap(edge + dir * i, w));
                int reach = (int)(slope * i);
                if (natural > gy + reach) h = gy + reach;
                else if (natural < gy - reach) h = gy - reach;
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
            int reachCols = baseWorld is Meridian.Terrain.SolidWorldGenerator sg && sg.SmoothGround ? SmoothMaxShoulder : MaxShoulder; // U-156: the smooth shoulders' longer reach
            for (int col = -reachCols; col < poi.Width + reachCols; col++)
            {
                int x = Wrap(poi.x + col, baseWorld.Width);
                int natural = baseWorld.SurfaceHeight(x);
                bool inStamp = col >= 0 && col < poi.Width;
                int ground = gy;
                if (!inStamp && InOtherStamp(poi, x, baseWorld.Width)) continue; // U-159: another POI's stamp owns its columns (a 240-column smooth shoulder crossed the camp and filled its soil rows with rock)
                if (!inStamp)
                {
                    // U-156: a smooth planet's shoulders are joint across neighbouring POIs (JointGround); else this POI's own shoulder.
                    bool shaped = reachCols == SmoothMaxShoulder ? JointGround(baseWorld, datumY, poi.planet, x, out ground) : ShapedGround(poi, baseWorld, datumY, x, out ground, gy);
                    if (!shaped) continue;
                }
                int fillFrom = inStamp ? bottomRow - 1 : ground;
                // Fill: solid rock down to the natural ground (no gap under a pad or a raised shoulder).
                for (int y = fillFrom; y > natural && y >= 0; y--)
                    if (baseWorld.TileAt(x, y) == TileId.Air) edits.Set(x, y, rock, TileId.Air);
                if (!inStamp)
                {
                    // Shoulder: a surface tile on its ground line, open air above it up to the natural surface.
                    edits.Set(x, ground, top, baseWorld.TileAt(x, ground)); // raised or cut: a surface tile on top
                    int keep = baseWorld is Meridian.Terrain.SolidWorldGenerator fg && fg.FillTopAt(x) > ground ? fg.FillTopAt(x) : ground; // U-169: the rows under the curve stay
                    for (int y = keep + 1; y <= natural; y++) edits.Set(x, y, TileId.Air, baseWorld.TileAt(x, y));
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

        // U-156: the smooth planet's POIs and their pad heights, per world (main thread: the stamping and the outline both run there).
        static IWorldGenerator jointWorld;
        static PoiDef[] jointPois;
        static int[] jointPads;

        static void Joint(IWorldGenerator world, int datumY, Meridian.Planets.PlanetId planet)
        {
            if (ReferenceEquals(jointWorld, world)) return;
            var list = new System.Collections.Generic.List<PoiDef>();
            foreach (var p in PoiCatalog.For(planet)) if (!p.Floating && p.stamp != null) list.Add(p);
            jointPois = list.ToArray();
            jointPads = new int[jointPois.Length];
            for (int i = 0; i < jointPois.Length; i++) jointPads[i] = GroundY(jointPois[i], world, datumY);
            jointWorld = world;
        }

        /// <summary>U-156: the pad height (the stamp's ground row) where column x lies across a stamped POI; int.MinValue elsewhere. The drawn
        /// curve holds pad + 1 across the whole stamp (GroundField.Curve), so its props never stand over the shoulders' easing.</summary>
        public static int PadAt(IWorldGenerator world, int datumY, Meridian.Planets.PlanetId planet, int x)
        {
            Joint(world, datumY, planet);
            int w = world.Width;
            for (int i = 0; i < jointPois.Length; i++) if (Wrap(x - jointPois[i].x, w) < jointPois[i].Width) return jointPads[i];
            return int.MinValue;
        }

        /// <summary>
        /// U-156 (D-161): on a smooth planet the ground round its stamped POIs is joint, so neighbouring shoulders meet without a step: across a
        /// stamp its own pad; elsewhere the natural surface clamped into every reaching POI's cone (its pad height ± SmoothShoulder per column off
        /// its edge, out to SmoothMaxShoulder); cones that cannot meet split the difference. False where no cone reaches (the natural surface
        /// stands). TerrainStreamer.WallTop and Apply both use it, so the drawn curve and the hidden grid agree.
        /// </summary>
        public static bool JointGround(IWorldGenerator world, int datumY, Meridian.Planets.PlanetId planet, int x, out int ground)
        {
            Joint(world, datumY, planet);
            int w = world.Width;
            x = Wrap(x, w);
            int natural = world.SurfaceHeight(x);
            int lo = int.MinValue, hi = int.MaxValue;
            bool any = false;
            for (int i = 0; i < jointPois.Length; i++)
            {
                var poi = jointPois[i];
                int d = Wrap(x - poi.x, w);
                if (d < poi.Width) { ground = jointPads[i]; return true; } // across a stamp its own pad
                int right = d - poi.Width + 1, left = w - d, k = right <= left ? right : left;
                if (k > SmoothMaxShoulder) continue;
                int reach = (int)(SmoothShoulder * k);
                any = true;
                if (jointPads[i] - reach > lo) lo = jointPads[i] - reach;
                if (jointPads[i] + reach < hi) hi = jointPads[i] + reach;
            }
            ground = natural;
            if (!any) return false;
            if (lo > hi) { int mid = (int)(((long)lo + hi) / 2); lo = hi = mid; }
            ground = natural < lo ? lo : natural > hi ? hi : natural;
            return true;
        }
    }
}
