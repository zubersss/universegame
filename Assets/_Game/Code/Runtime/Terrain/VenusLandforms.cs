using UnityEngine;

namespace Meridian.Terrain
{
    public enum VenusFeature { Plains, Tessera, VentField }

    /// <summary>
    /// Venus's surface (U-050, Bible §7.4): volcanic basalt plains, two tessera highland bands (folded,
    /// raised terrain) and two active vent fields where acid has glassed the silica (Vitriol Glass) under a
    /// sulfur crust. The habitable cloud deck sits far above (y 770 ± 60) and holds the floating stations.
    /// </summary>
    public static class VenusLandforms
    {
        public const float DeckY = 770f, DeckHalfBand = 60f;

        /// <summary>Tessera highlands: [start, end) x ranges, raised by TesseraRise with 60 m ramps.</summary>
        public static readonly (int x0, int x1)[] Tesserae = { (600, 1100), (2400, 3000) };
        public const float TesseraRise = 55f;
        public const int Ramp = 60;
        /// <summary>Vent fields: [start, end) x ranges.</summary>
        public static readonly (int x0, int x1)[] Vents = { (1600, 1700), (3500, 3580) };

        public static VenusFeature At(int x)
        {
            foreach (var v in Vents) if (x >= v.x0 && x < v.x1) return VenusFeature.VentField;
            foreach (var t in Tesserae) if (x >= t.x0 && x < t.x1) return VenusFeature.Tessera;
            return VenusFeature.Plains;
        }

        /// <summary>Surface height: the fBm plain, raised over the tesserae (ramped), dished a little at vents.</summary>
        public static float Height(int x, float plain)
        {
            float h = plain;
            foreach (var t in Tesserae)
            {
                float up = Mathf.Clamp01((x - t.x0) / (float)Ramp) * Mathf.Clamp01((t.x1 - x) / (float)Ramp);
                // Folded ridges on top: tessera is "tile-like" terrain.
                h += up * (TesseraRise + 8f * Mathf.Sin(x * 0.21f) * Mathf.Sin(x * 0.047f));
            }
            foreach (var v in Vents)
            {
                float c = (v.x0 + v.x1) * 0.5f, half = (v.x1 - v.x0) * 0.5f;
                float a = Mathf.Abs(x - c) / half;
                if (a < 1f) h -= 6f * (1f - a * a);
            }
            return h;
        }

        /// <summary>Material by feature and depth below the surface.</summary>
        public static byte Material(int x, int depth, float noise)
        {
            switch (At(x))
            {
                case VenusFeature.VentField:
                    if (depth < 1) return TileId.Sulfur;
                    return depth < 7 ? TileId.VentGlass : TileId.VenusBasalt;
                case VenusFeature.Tessera:
                    return depth < 12 ? TileId.Tessera : TileId.VenusBasalt;
            }
            if (depth < 2 && noise > 0.7f) return TileId.Sulfur; // sulfur frost patches on the plains
            return TileId.VenusBasalt;
        }
    }
}
