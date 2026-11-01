using Meridian.Building;
using Meridian.Items;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-056 (EditMode): the buoyancy budget and the base-piece table.</summary>
    public class BuoyancyTests
    {
        [Test]
        public void SinksOnlyWhenTheLoadOutweighsTheLift()
        {
            Assert.AreEqual(0f, Buoyancy.SinkSpeed(6f, 4f), "lift ≥ load holds height");
            Assert.AreEqual(0f, Buoyancy.SinkSpeed(6f, 6f));
            Assert.AreEqual(2f * Buoyancy.SinkPerUnit, Buoyancy.SinkSpeed(6f, 8f), 1e-5f, "sinks with the shortfall");
            Assert.AreEqual(Buoyancy.MaxSink, Buoyancy.SinkSpeed(0f, 100f), "capped");
            Assert.AreEqual(-2f, Buoyancy.Margin(6f, 8f));
        }

        [Test]
        public void EveryPieceIsAnItemWithArt()
        {
            for (int i = 0; i < PieceSpec.Count; i++)
            {
                var spec = PieceSpec.Get((PieceKind)i);
                Assert.AreEqual((PieceKind)i, spec.kind, "table order");
                Assert.NotNull(ItemRegistry.Get(spec.itemKey), spec.itemKey);
                Assert.AreSame(spec, PieceSpec.ForItem(spec.itemKey));
                Assert.IsTrue(System.IO.File.Exists($"Assets/_Game/Art/{spec.artKey}_color.png"), spec.artKey);
            }
            Assert.IsNull(PieceSpec.ForItem("iron"), "ordinary items aren't pieces");
            Assert.Greater(PieceSpec.Get(PieceKind.FloatCell).lift, 0f);
            Assert.IsTrue(PieceSpec.Get(PieceKind.Door).seals && !PieceSpec.Get(PieceKind.Door).solid, "the door seals but lets you through");
        }
    }
}
