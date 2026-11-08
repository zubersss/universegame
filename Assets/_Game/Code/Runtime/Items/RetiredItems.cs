using System.Collections.Generic;

namespace Meridian.Items
{
    /// <summary>
    /// U-170 (D-173): a save's retired items, refunded on load. Cryo rounds (the Veil Serpent's ammunition, retired with combat, D-087) go back
    /// into what the Fabricator made them from: each 6 as 2 polar ice and 1 iron bar, rounded down.
    /// </summary>
    public static class RetiredItems
    {
        public const int CryoRoundsPerBatch = 6, PolarIcePerBatch = 2, IronBarsPerBatch = 1;

        /// <summary>Empties every cryo-round stack in `list` and returns the batches they refund (rounds / 6, rounded down).</summary>
        public static int TakeCryoRoundBatches(List<ItemStack> list)
        {
            int id = ItemRegistry.CryoRoundRetiredId, rounds = 0;
            if (list == null || id < 0) return 0;
            for (int i = 0; i < list.Count; i++)
                if (!list[i].IsEmpty && list[i].itemId == id) { rounds += list[i].count; list[i] = default; }
            return rounds / CryoRoundsPerBatch;
        }

        /// <summary>Refunds the batches into the inventory (what does not fit is lost, as any full pack).</summary>
        public static void Refund(Inventory inventory, int batches)
        {
            if (inventory == null || batches <= 0) return;
            var ice = ItemRegistry.Get("polar_ice");
            var bar = ItemRegistry.Get("smelter_bar_iron");
            if (ice != null) inventory.Add(ice.id, batches * PolarIcePerBatch);
            if (bar != null) inventory.Add(bar.id, batches * IronBarsPerBatch);
        }
    }
}
