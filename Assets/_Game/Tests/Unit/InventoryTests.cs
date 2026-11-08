using System.Collections.Generic;
using Meridian.EditorTools;
using Meridian.Items;
using Meridian.Save;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-045 (EditMode): item registry, stacking, splitting, moving, save round trip, v1 → v2 migration.</summary>
    public class InventoryTests
    {
        static int Iron => ItemRegistry.Get("iron").id;

        [Test]
        public void RegistryKeepsTileIdsAndHasEveryIcon()
        {
            Assert.AreEqual(TileId.Stone, ItemRegistry.Get("stone").id, "tile items keep their TileId (drops and old cargo stay valid)");
            Assert.AreEqual(TileId.Stone, ItemRegistry.Get(TileId.Stone).placeTile);
            Assert.AreEqual(0, ItemRegistry.DropOf(TileId.Water), "water drops nothing");
            Assert.AreEqual(TileId.Basalt, ItemRegistry.DropOf(TileId.Basalt));
            Assert.GreaterOrEqual(Iron, ItemRegistry.FirstResource);
            Assert.AreEqual(0, ItemRegistry.Get("iron").placeTile, "resources aren't placeable");
            var keys = new HashSet<string>();
            var ids = new HashSet<int>();
            foreach (var d in ItemRegistry.All)
            {
                Assert.IsTrue(keys.Add(d.key), "unique key " + d.key);
                Assert.IsTrue(ids.Add(d.id), "unique id " + d.id);
            }
            // Every B-013 icon has an item.
            foreach (var icon in new[] { "aluminium", "carbon", "clay", "copper", "hematite", "iron", "living_seed",
                                         "nickel", "oxygen", "perchlorate", "sand", "silica", "stone", "water_ice", "wood" })
                Assert.AreEqual($"icons/{icon}/base", ItemRegistry.Get(icon)?.icon, icon);
        }

        /// <summary>U-159 (Residency): an item's icon is shared art (icons/ or props/common/): items travel between planets, and a planet's own
        /// key held for the session (ItemIcons) keeps that planet's bundle resident everywhere.</summary>
        [Test]
        public void ItemIconsAreSharedArt()
        {
            // Pending: the wind anchor has only Neptune's prop (B-161); its shared icon is asked of LEAD (U-159 report, 2026-11-08).
            var pending = new HashSet<string> { "wind_anchor" };
            foreach (var d in ItemRegistry.All)
                if (d.icon != null && !pending.Contains(d.key)) Assert.IsTrue(d.icon.StartsWith("icons/") || d.icon.StartsWith("props/common/"), $"{d.key}: icon {d.icon}");
        }

        [Test]
        public void AddFillsStacksThenEmptySlots()
        {
            var inv = new Inventory();
            Assert.AreEqual(0, inv.Add(Iron, 1500));
            Assert.AreEqual(999, inv[0].count);
            Assert.AreEqual(501, inv[1].count);
            Assert.AreEqual(0, inv.Add(TileId.Stone, 10));
            Assert.AreEqual(TileId.Stone, inv[2].itemId, "a new item takes the next empty slot");
            Assert.AreEqual(0, inv.Add(Iron, 498));
            Assert.AreEqual(999, inv[1].count, "tops up the open stack first");
            Assert.AreEqual(0, inv.Add(Iron, 1));
            Assert.AreEqual(1, inv[3].count, "then a new stack");
            Assert.AreEqual(1999, inv.Count(Iron));
        }

        [Test]
        public void FullInventoryReturnsTheRest()
        {
            var inv = new Inventory();
            Assert.AreEqual(0, inv.Add(Iron, Inventory.SlotCount * Inventory.StackMax));
            Assert.AreEqual(7, inv.Add(Iron, 7), "nothing fits");
            Assert.AreEqual(5, inv.Add(TileId.Sand, 5), "no empty slot for a new item either");
        }

        [Test]
        public void RemoveIsAllOrNothingFromTheLastStacks()
        {
            var inv = new Inventory();
            inv.Add(Iron, 1200);
            Assert.IsFalse(inv.Remove(Iron, 1201), "not enough: no change");
            Assert.AreEqual(1200, inv.Count(Iron));
            Assert.IsTrue(inv.Remove(Iron, 250));
            Assert.IsTrue(inv[1].IsEmpty, "the last stack (201) goes first");
            Assert.AreEqual(950, inv[0].count, "then 49 from the first");
            Assert.AreEqual(950, inv.Count(Iron));
        }

        [Test]
        public void SplitAndMove()
        {
            var inv = new Inventory();
            inv.Add(Iron, 100);
            Assert.IsTrue(inv.Split(0, 40));
            Assert.AreEqual(60, inv[0].count);
            Assert.AreEqual(40, inv[1].count);
            Assert.IsFalse(inv.Split(0, 60), "can't split a whole stack");
            Assert.IsFalse(inv.Split(0, 0));
            inv.Move(1, 0);
            Assert.AreEqual(100, inv[0].count, "same item merges");
            Assert.IsTrue(inv[1].IsEmpty);
            inv.Add(TileId.Stone, 3);
            inv.Move(0, 1);
            Assert.AreEqual(TileId.Stone, inv[0].itemId, "different items swap");
            Assert.AreEqual(Iron, inv[1].itemId);
        }

        [Test]
        public void SelectedSlotGivesTheBuilderItsTile()
        {
            var inv = new Inventory();
            inv.Add(Iron, 5);
            inv.Add(TileId.Basalt, 5);
            Assert.AreEqual(0, inv.SelectedTile, "iron isn't placeable");
            inv.Select(1);
            Assert.AreEqual(TileId.Basalt, inv.SelectedTile);
            inv.Remove(TileId.Basalt, 5);
            Assert.AreEqual(0, inv.SelectedTile, "empty slot");
        }

        [Test]
        public void SaveRoundTripKeepsSlotPositions()
        {
            var inv = new Inventory();
            inv.Add(Iron, 1500);
            inv.Add(TileId.Ice, 12);
            inv.Remove(Iron, 999); // last stacks first: slot 1 (501) empties, slot 0 keeps 501; slot 2 (ice) stays
            inv.Select(2);
            var data = new SaveData();
            inv.WriteTo(data.inventory);
            data.selectedSlot = inv.Selected;
            var back = SaveMigrations.Migrate(JsonUtility.FromJson<SaveData>(JsonUtility.ToJson(data)));
            var again = new Inventory();
            again.ReadFrom(back.inventory, back.selectedSlot);
            for (int i = 0; i < Inventory.SlotCount; i++)
            {
                Assert.AreEqual(inv[i].count, again[i].count, $"slot {i} count");
                if (!inv[i].IsEmpty) Assert.AreEqual(inv[i].itemId, again[i].itemId, $"slot {i} item");
            }
            Assert.AreEqual(2, again.Selected);
        }

        [Test]
        public void UnknownItemsAndOversizedStacksAreCleanedOnLoad()
        {
            var list = new List<ItemStack> { new ItemStack { itemId = 9999, count = 3 }, new ItemStack { itemId = Iron, count = 5000 } };
            var inv = new Inventory();
            inv.ReadFrom(list, 77);
            Assert.IsTrue(inv[0].IsEmpty, "an item from a newer build is dropped");
            Assert.AreEqual(Inventory.StackMax, inv[1].count, "clamped to the stack cap");
            Assert.AreEqual(0, inv.Selected, "bad selection resets");
        }

        [Test]
        public void Version1SaveMigratesToVersion2()
        {
            // A v1 state.json: no inventory, no suit.
            var v1 = JsonUtility.FromJson<SaveData>("{\"version\":1,\"currentPlanet\":\"Mars\",\"view\":\"PlanetSide\",\"player\":{\"health\":64.0}}");
            v1.inventory = null;
            var m = SaveMigrations.Migrate(v1);
            Assert.AreEqual(SaveData.CurrentVersion, m.version, "v1 → v2 → … → the current version"); // U-157: v3 follows v2
            Assert.NotNull(m.inventory);
            Assert.AreEqual(0, m.inventory.Count);
            Assert.AreEqual(100f, m.player.suit, "full suit");
            Assert.AreEqual(64f, m.player.health, "health kept");
        }
            /// <summary>B-128 / cycle 257: every item icon the registry names is an Addressables entry (icons/&lt;key&gt;/base in Art or Placeholders, or the prop key whose sprite is the icon), so no slot can draw the tile stand-in by accident.</summary>
        [Test]
        public void EveryItemIconResolvesToAnAddress()
        {
            var addresses = new HashSet<string>();
            foreach (var g in ArtImporter.Settings.groups)
            {
                if (g == null) continue;
                foreach (var e in g.entries) if (e != null && e.address != null) addresses.Add(e.address);
            }
            Assert.Greater(addresses.Count, 0, "the Addressables settings have entries");
            var missing = new List<string>();
            int withIcon = 0;
            foreach (var d in ItemRegistry.All)
            {
                if (string.IsNullOrEmpty(d.icon)) continue;
                withIcon++;
                // icons/<key>/base for most items; a prop key (props/common/shelter_wall) when the prop's own sprite is the icon.
                if (!addresses.Contains(d.icon)) missing.Add($"{d.key} -> {d.icon}");
            }
            Assert.Greater(withIcon, 20, "most items carry an icon");
            Assert.IsEmpty(missing, "icons without an address: " + string.Join(", ", missing));
        }

    }
}
