namespace Meridian.Terrain
{
    /// <summary>
    /// 47-tile "blob" autotiling. Neighbor bits: N=1, NE=2, E=4, SE=8, S=16, SW=32, W=64, NW=128;
    /// a corner counts only when both adjacent edges connect. The 47 reduced masks, sorted
    /// ascending, give the sheet index (row-major from the top-left, 8 columns).
    /// </summary>
    public static class BlobAutotile
    {
        public const int N = 1, NE = 2, E = 4, SE = 8, S = 16, SW = 32, W = 64, NW = 128;
        public const int VariantCount = 47;

        static readonly byte[] IndexOfMask = Build(out MaskOfIndex);
        public static readonly byte[] MaskOfIndex;

        public static int Reduce(int mask)
        {
            if ((mask & N) == 0 || (mask & E) == 0) mask &= ~NE;
            if ((mask & S) == 0 || (mask & E) == 0) mask &= ~SE;
            if ((mask & S) == 0 || (mask & W) == 0) mask &= ~SW;
            if ((mask & N) == 0 || (mask & W) == 0) mask &= ~NW;
            return mask;
        }

        /// <summary>Sheet index 0..46 for any 8-bit neighbor mask.</summary>
        public static byte Index(int mask) => IndexOfMask[mask & 0xFF];

        static byte[] Build(out byte[] maskOfIndex)
        {
            var index = new byte[256];
            maskOfIndex = new byte[VariantCount];
            int next = 0;
            var seen = new int[256];
            for (int m = 0; m < 256; m++) seen[m] = -1;
            for (int m = 0; m < 256; m++)
            {
                int r = Reduce(m);
                if (r != m) continue; // canonical masks only, ascending
                seen[m] = next;
                maskOfIndex[next] = (byte)m;
                next++;
            }
            for (int m = 0; m < 256; m++) index[m] = (byte)seen[Reduce(m)];
            return index;
        }
    }
}
