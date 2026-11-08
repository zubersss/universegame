using System.Collections.Generic;
using UnityEngine;

namespace Meridian.Terrain.CloudColumn
{
    /// <summary>The bands of a giant's cloud column, top down (Bible §7.5).</summary>
    public enum CloudBand { Space, Sky, Deck1, Deck2, Deck3, Deep, Crush }

    /// <summary>One floating ice floe: a solid, mineable platform (bottom-left cell, size in tiles).</summary>
    public struct Floe
    {
        public int x, y, width, height;
        public CloudBand band;
        public bool Contains(int cx, int cy) => cx >= x && cx < x + width && cy >= y && cy < y + height;
    }

    /// <summary>
    /// U-061 cloud-column world type (Bible §7.5, D-004), pure: a Width × Height column with no ground. The
    /// Datum (1 bar, the upper cloud tops) is y 1100; Deck 1 runs 1100–900, Deck 2 900–600, Deck 3 600–300,
    /// the Deep 300–100, and the Crush Line at y 100 is lethal. Floes are seeded per slot (a SlotW × SlotH
    /// grid cell holds at most one), with density by deck: Deck 2 densest, the Deep sparse. A floe is an ice
    /// skin around a denser core. TileAt is O(1): it only looks at the slot the cell is in.
    /// </summary>
    public static class CloudLayout
    {
        public const int Width = 4096, Height = 2000;
        public const int Datum = 1100, Deck1Bottom = 900, Deck2Bottom = 600, Deck3Bottom = 300, CrushLine = 100;
        /// <summary>U-127 (Bible §7.6): the Great Red Spot, a 600 m zone of the column (x RedSpotCentre ± RedSpotHalfWidth, every band): its floes
        /// draw the brick spot strip, its plants are the red_spot kinds, and the stage lays B-155's spot overlay over the deck set there (the wind
        /// push and the floe spin are a gameplay card of their own).</summary>
        public const int RedSpotCentre = 3072, RedSpotHalfWidth = 300;
        public static int RedSpotOffset(int x) { int d = ((x - RedSpotCentre) % Width + Width) % Width; return d > Width / 2 ? d - Width : d; }
        public static bool InRedSpot(int x) => Mathf.Abs(RedSpotOffset(x)) <= RedSpotHalfWidth;

        /// <summary>U-129 (Bible §7.7): Saturn's North Polar Hexagon, a 900 m zone of the column (x HexagonCentre ± HexagonHalfWidth, every band):
        /// its plants are the hexagon kinds and the stage lays B-157's hexagon overlay (the wind-walls, the tilted rings) over the deck set there.</summary>
        public const int HexagonCentre = 1024, HexagonHalfWidth = 450;
        public static int HexagonOffset(int x) { int d = ((x - HexagonCentre) % Width + Width) % Width; return d > Width / 2 ? d - Width : d; }
        public static bool InHexagon(int x) => Mathf.Abs(HexagonOffset(x)) <= HexagonHalfWidth;

        /// <summary>Space edge above the Escape Line (the planet config owns the Escape Line itself).</summary>
        public const int SpaceEdge = 1700;
        public const int SlotW = 32, SlotH = 24;
        public const int MinFloeW = 6, MaxFloeW = 18, MinFloeH = 2, MaxFloeH = 4;

        public static CloudBand BandAt(float y) =>
            y < CrushLine ? CloudBand.Crush :
            y < Deck3Bottom ? CloudBand.Deep :
            y < Deck2Bottom ? CloudBand.Deck3 :
            y < Deck1Bottom ? CloudBand.Deck2 :
            y < Datum ? CloudBand.Deck1 :
            y < SpaceEdge ? CloudBand.Sky : CloudBand.Space;

        /// <summary>Share of slots holding a floe, by band (Deck 2 densest; none above the Datum or in the Crush).</summary>
        public static float Density(CloudBand b) => b switch
        {
            CloudBand.Deck1 => 0.30f,
            CloudBand.Deck2 => 0.45f,
            CloudBand.Deck3 => 0.30f,
            CloudBand.Deep => 0.12f,
            _ => 0f,
        };

        /// <summary>The floe in slot (sx, sy), if the seed puts one there.</summary>
        public static bool FloeInSlot(int sx, int sy, int seed, out Floe floe)
        {
            floe = default;
            int slots = Width / SlotW;
            sx = ((sx % slots) + slots) % slots;
            int y0 = sy * SlotH;
            var band = BandAt(y0 + SlotH * 0.5f);
            if (Hash01(sx, sy, seed, 1) >= Density(band)) return false;
            int w = MinFloeW + (int)(Hash01(sx, sy, seed, 2) * (MaxFloeW - MinFloeW + 1));
            int h = MinFloeH + (int)(Hash01(sx, sy, seed, 3) * (MaxFloeH - MinFloeH + 1));
            int x = sx * SlotW + (int)(Hash01(sx, sy, seed, 4) * (SlotW - w));
            int y = y0 + 2 + (int)(Hash01(sx, sy, seed, 5) * (SlotH - h - 4));
            // A floe never dips into the Crush band or rises above the Datum.
            if (y < CrushLine + 2 || y + h > Datum) return false;
            floe = new Floe { x = x, y = y, width = w, height = h, band = band };
            return true;
        }

        /// <summary>
        /// U-153 (P-52): the standing height (top row + 1) of the floe nearest under a point (x, y): the floes of the point's slot column and
        /// its two neighbours whose top is at or under y + 0.5 and over minY, the nearest across first (wrapped), then the highest. The giant's
        /// deck sets hang off it, so they paint where the floes are. False when none is there. A few dozen slot lookups; no allocation.
        /// </summary>
        public static bool FloeTopUnder(float x, float y, float minY, int seed, out float top)
        {
            top = minY;
            int wx = ((Mathf.FloorToInt(x) % Width) + Width) % Width;
            int sx = wx / SlotW;
            int syTop = Mathf.Clamp(Mathf.FloorToInt(y) / SlotH, 0, Height / SlotH);
            int syLow = Mathf.Max(0, Mathf.FloorToInt(minY) / SlotH);
            bool found = false;
            float best = float.MaxValue;
            for (int dsx = -1; dsx <= 1; dsx++)
                for (int sy = syTop; sy >= syLow; sy--)
                {
                    if (!FloeInSlot(sx + dsx, sy, seed, out var f)) continue;
                    float t = f.y + f.height;
                    if (t > y + 0.5f || t < minY) continue;
                    int d0 = WrapDelta(f.x - wx), d1 = WrapDelta(f.x + f.width - 1 - wx);
                    int across = d0 <= 0 && d1 >= 0 ? 0 : Mathf.Min(Mathf.Abs(d0), Mathf.Abs(d1));
                    float score = across * 4f + (y - t); // a floe right under the point beats a higher one beside it
                    if (score < best) { best = score; top = t; found = true; }
                }
            return found;
        }

        static int WrapDelta(int d) { d %= Width; if (d > Width / 2) d -= Width; if (d < -Width / 2) d += Width; return d; }

        /// <summary>The cloud column's tile at (x, y): floe ice skin, floe core, or air. x wraps.</summary>
        public static byte TileAt(int x, int y, int seed)
        {
            if (y < 0 || y >= Height) return TileId.Air;
            int wx = ((x % Width) + Width) % Width;
            if (!FloeInSlot(wx / SlotW, y / SlotH, seed, out var f) || !f.Contains(wx, y)) return TileId.Air;
            bool edge = wx == f.x || wx == f.x + f.width - 1 || y == f.y || y == f.y + f.height - 1;
            return edge ? TileId.FloeIce : TileId.FloeCore;
        }

        /// <summary>The floes whose slots overlap [x0, x1) × [y0, y1) (spawn search, tests).</summary>
        public static IEnumerable<Floe> FloesIn(int x0, int x1, int y0, int y1, int seed)
        {
            for (int sy = Mathf.Max(0, y0 / SlotH); sy <= Mathf.Min(Height - 1, y1 - 1) / SlotH; sy++)
                for (int sx = Mathf.FloorToInt(x0 / (float)SlotW); sx <= Mathf.FloorToInt((x1 - 1) / (float)SlotW); sx++)
                    if (FloeInSlot(sx, sy, seed, out var f)) yield return f;
        }

        static float Hash01(int a, int b, int seed, int salt)
        {
            unchecked
            {
                uint h = (uint)a * 0x9E3779B1u ^ (uint)b * 0x85EBCA77u ^ (uint)seed * 0xC2B2AE3Du ^ (uint)salt * 0x27D4EB2Fu;
                h ^= h >> 15; h *= 0x2C1B3C6Du; h ^= h >> 12; h *= 0x297A2D39u; h ^= h >> 15;
                return (h & 0xFFFFFF) / (float)0x1000000;
            }
        }
    }
}
