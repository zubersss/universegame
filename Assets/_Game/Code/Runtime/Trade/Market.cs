using System;
using System.Collections.Generic;
using Meridian.Items;
using UnityEngine;

namespace Meridian.Trade
{
    /// <summary>A Halcyon cargo contract: carry `count` of `item` from one Waystation to another for `reward` Scrip.</summary>
    [Serializable]
    public sealed class Contract
    {
        public string id, item, from, to;
        public int count, reward;
        public bool accepted, done;
    }

    /// <summary>
    /// U-052 Halcyon market (Bible §3, §8): Scrip prices per Waystation, buy/sell, refuel, repair, and cargo
    /// contracts. Pure: callers pass the inventory and the wallet (GameState); no Unity objects needed.
    /// </summary>
    public static class Market
    {
        public const int StartingScrip = 200;
        /// <summary>Halcyon buys at this share of its selling price.</summary>
        public const float SellShare = 0.6f;
        public static readonly string[] Stations = { "earth", "mars" };

        /// <summary>Base prices (Scrip per unit) before a station's local factor.</summary>
        static readonly Dictionary<string, int> Base = new Dictionary<string, int>
        {
            { "iron", 12 }, { "copper", 16 }, { "hematite", 6 }, { "nickel", 14 }, { "carbon", 5 }, { "silica", 8 },
            { "water_ice", 4 }, { "perchlorate", 18 }, { "launch_fuel", 10 }, { "smelter_bar_iron", 30 },
            { "smelter_bar_copper", 38 }, { "suit_patch", 70 }, { "circuit_board", 90 }, { "graphite", 20 },
            { "solarite", 160 }, { "vitriol_glass", 140 },
        };

        /// <summary>Local factors: Earth makes goods and fuel cheaply, Mars is rich in ore and oxidizer and short of goods.</summary>
        static float Factor(string station, string item)
        {
            if (station == "mars")
            {
                switch (item)
                {
                    case "hematite": case "iron": case "nickel": case "perchlorate": case "water_ice": return 0.7f; // ore-rich
                    case "launch_fuel": case "suit_patch": case "circuit_board": case "copper": case "smelter_bar_copper": return 1.4f;
                    default: return 1.1f;
                }
            }
            switch (item) // Earth
            {
                case "launch_fuel": case "suit_patch": case "circuit_board": case "carbon": return 0.85f;
                case "perchlorate": case "hematite": return 1.3f;
                default: return 1f;
            }
        }

        public static IEnumerable<string> Goods => Base.Keys;

        /// <summary>What Halcyon charges at this station (0 if it doesn't trade the item).</summary>
        public static int BuyPrice(string station, string item) =>
            Base.TryGetValue(item, out int p) ? Mathf.Max(1, Mathf.RoundToInt(p * Factor(station, item))) : 0;

        /// <summary>What Halcyon pays for one unit here.</summary>
        public static int SellPrice(string station, string item) => Mathf.Max(1, Mathf.FloorToInt(BuyPrice(station, item) * SellShare));

        /// <summary>Fuel (per unit of the tank) and hull repair (per point).</summary>
        public static int FuelPrice(string station) => station == "mars" ? 3 : 2;
        public static int RepairPrice(string station) => station == "mars" ? 4 : 3;

        public static bool Sell(string station, string item, int count, Inventory inv, ref int scrip)
        {
            var def = ItemRegistry.Get(item);
            if (def == null || BuyPrice(station, item) == 0 || count <= 0 || !inv.Remove(def.id, count)) return false;
            scrip += SellPrice(station, item) * count;
            return true;
        }

        public static bool Buy(string station, string item, int count, Inventory inv, ref int scrip)
        {
            var def = ItemRegistry.Get(item);
            int price = BuyPrice(station, item) * count;
            if (def == null || price == 0 || count <= 0 || scrip < price) return false;
            int left = inv.Add(def.id, count);
            if (left > 0) { inv.Remove(def.id, count - left); return false; } // no room: nothing bought
            scrip -= price;
            return true;
        }

        /// <summary>Tops the tank up as far as the wallet allows. Returns units bought.</summary>
        public static float Refuel(string station, ref float fuel, float tank, ref int scrip)
        {
            float want = Mathf.Max(0f, tank - fuel);
            float afford = scrip / (float)FuelPrice(station);
            float units = Mathf.Floor(Mathf.Min(want, afford));
            fuel += units;
            scrip -= Mathf.RoundToInt(units * FuelPrice(station));
            return units;
        }

        /// <summary>Repairs the hull as far as the wallet allows. Returns points repaired.</summary>
        public static float Repair(string station, ref float hull, float max, ref int scrip)
        {
            float want = Mathf.Max(0f, max - hull);
            float points = Mathf.Floor(Mathf.Min(want, scrip / (float)RepairPrice(station)));
            hull += points;
            scrip -= Mathf.RoundToInt(points * RepairPrice(station));
            return points;
        }

        /// <summary>The contracts a station posts: two runs to the other station (deterministic per station).</summary>
        public static List<Contract> OffersAt(string station)
        {
            string other = station == "earth" ? "mars" : "earth";
            var list = new List<Contract>();
            if (station == "earth")
            {
                list.Add(new Contract { id = "earth_mars_patches", item = "suit_patch", count = 3, from = "earth", to = other, reward = 420 });
                list.Add(new Contract { id = "earth_mars_boards", item = "circuit_board", count = 2, from = "earth", to = other, reward = 380 });
            }
            else
            {
                list.Add(new Contract { id = "mars_earth_perchlorate", item = "perchlorate", count = 10, from = "mars", to = other, reward = 300 });
                list.Add(new Contract { id = "mars_earth_hematite", item = "hematite", count = 20, from = "mars", to = other, reward = 220 });
            }
            return list;
        }

        /// <summary>Delivers an accepted contract at its destination if the cargo is aboard: pays and closes it.</summary>
        public static bool Deliver(Contract c, string station, Inventory inv, ref int scrip)
        {
            var def = ItemRegistry.Get(c.item);
            if (!c.accepted || c.done || c.to != station || def == null || !inv.Remove(def.id, c.count)) return false;
            scrip += c.reward;
            c.done = true;
            return true;
        }
    }
}
