using Meridian.Items;
using Meridian.Trade;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-052 (EditMode): Halcyon prices per station, buy/sell, repair limited by the purse (no refuelling since U-107), cargo contracts.</summary>
    public class MarketTests
    {
        static int Id(string key) => ItemRegistry.Get(key).id;

        [Test]
        public void PricesDifferBetweenEarthAndMars()
        {
            Assert.Greater(Market.BuyPrice("mars", "circuit_board"), Market.BuyPrice("earth", "circuit_board"), "goods are dear on Mars");
            Assert.Less(Market.BuyPrice("mars", "perchlorate"), Market.BuyPrice("earth", "perchlorate"), "perchlorate is cheap on Mars");
            Assert.AreNotEqual(Market.BuyPrice("earth", "iron"), Market.BuyPrice("mars", "iron"));
            Assert.Less(Market.SellPrice("earth", "iron"), Market.BuyPrice("earth", "iron"), "Halcyon buys below its price");
            Assert.AreEqual(0, Market.BuyPrice("earth", "soil"), "not every item trades");
            foreach (var key in Market.Goods) Assert.NotNull(ItemRegistry.Get(key), "traded good " + key);
        }

        [Test]
        public void SellAndBuyMoveScripAndCargo()
        {
            var inv = new Inventory();
            inv.Add(Id("iron"), 10);
            int scrip = 100;
            Assert.IsTrue(Market.Sell("earth", "iron", 10, inv, ref scrip));
            Assert.AreEqual(100 + 10 * Market.SellPrice("earth", "iron"), scrip);
            Assert.AreEqual(0, inv.Count(Id("iron")));
            Assert.IsFalse(Market.Sell("earth", "iron", 1, inv, ref scrip), "nothing left to sell");
            int before = scrip;
            Assert.IsTrue(Market.Buy("earth", "suit_patch", 1, inv, ref scrip));
            Assert.AreEqual(before - Market.BuyPrice("earth", "suit_patch"), scrip);
            int poor = 5;
            Assert.IsFalse(Market.Buy("earth", "solarite", 1, inv, ref poor), "can't afford");
            Assert.AreEqual(5, poor);
        }

        [Test]
        public void RepairStopsAtTheHullAndThePurse()
        {
            float hull = 70f; int scrip = 1000;
            Assert.AreEqual(30f, Market.Repair("earth", ref hull, 100f, ref scrip));
            Assert.AreEqual(100f, hull);
            hull = 50f; scrip = 10;
            Market.Repair("mars", ref hull, 100f, ref scrip);
            Assert.AreEqual(52f, hull, "10 Scrip buys 2 points at 4 each on Mars");
            Assert.AreEqual(2, scrip);
        }

        [Test]
        public void ContractsPayOnDeliveryAtTheDestination()
        {
            var offer = Market.OffersAt("mars").Find(c => c.item == "perchlorate");
            Assert.NotNull(offer);
            Assert.AreEqual("earth", offer.to);
            offer.accepted = true;
            var inv = new Inventory();
            inv.Add(Id("perchlorate"), offer.count);
            int scrip = 0;
            Assert.IsFalse(Market.Deliver(offer, "mars", inv, ref scrip), "not at the destination");
            Assert.IsTrue(Market.Deliver(offer, "earth", inv, ref scrip));
            Assert.AreEqual(offer.reward, scrip);
            Assert.IsTrue(offer.done);
            Assert.AreEqual(0, inv.Count(Id("perchlorate")));
            Assert.IsFalse(Market.Deliver(offer, "earth", inv, ref scrip), "paid once");
            Assert.AreEqual(2, Market.OffersAt("earth").Count, "each station posts two runs");
        }
    }
}
