using Meridian.View2D;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-187: the ground's back wall draws only where it can show - behind the cells dug (or a cave's air) under the natural surface and one
    /// cell round them - so the solid ground's pixels draw once. A dug cell always has its back wall; an undug cell with no dug neighbour none.
    /// </summary>
    public class BackWallTests
    {
        const int C = 8, W = C + 2;

        static bool[] Air(params (int i, int j)[] dug)
        {
            var air = new bool[W * W];
            foreach (var (i, j) in dug) air[(i + 1) + (j + 1) * W] = true;
            return air;
        }

        [Test]
        public void ADugCellAlwaysHasItsBackWallAnUndugInteriorCellNone()
        {
            var mask = new bool[C * C];
            SmoothGround.BackMask(C, Air(), mask);
            foreach (var m in mask) Assert.IsFalse(m, "solid ground: no back wall at all (the body covers it)");

            SmoothGround.BackMask(C, Air((3, 3), (4, 3)), mask);
            for (int j = 0; j < C; j++)
                for (int i = 0; i < C; i++)
                {
                    bool near = i >= 2 && i <= 5 && j >= 2 && j <= 4; // the two dug cells and their one-cell ring
                    Assert.AreEqual(near, mask[i + j * C], $"cell ({i}, {j})");
                }
            Assert.IsTrue(mask[3 + 3 * C] && mask[4 + 3 * C], "the dug cells themselves");

            // air in the neighbouring chunk's ring still shows its back wall on this side of the border
            SmoothGround.BackMask(C, Air((-1, 5)), mask);
            Assert.IsTrue(mask[0 + 5 * C] && mask[0 + 4 * C] && mask[0 + 6 * C], "the margin reaches across the chunk border");
            Assert.IsFalse(mask[1 + 5 * C], "one cell only");
        }
    }
}
