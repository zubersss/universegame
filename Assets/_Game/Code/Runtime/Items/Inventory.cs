using System;
using System.Collections.Generic;

namespace Meridian.Items
{
    /// <summary>One inventory slot: an item and how many (count 0 = empty).</summary>
    [Serializable]
    public struct ItemStack
    {
        public int itemId;
        public int count;
        public bool IsEmpty => count <= 0;
    }

    /// <summary>
    /// The surveyor's inventory v1 (U-045): 40 slots, stacks of up to 999. Adding fills existing stacks
    /// of the item first, then empty slots in order; removing takes from the last stacks first. No
    /// allocation per call (the HUD reads it every frame).
    /// </summary>
    public sealed class Inventory
    {
        public const int SlotCount = 40, StackMax = 999;

        readonly ItemStack[] slots = new ItemStack[SlotCount];

        /// <summary>Raised after any change (the panel redraws then, not every frame).</summary>
        public event Action Changed;

        /// <summary>The slot the Builder places from.</summary>
        public int Selected { get; private set; }

        public ItemStack this[int slot] => slots[slot];

        static int MaxOf(int itemId) => ItemRegistry.Get(itemId)?.stackMax ?? StackMax;

        /// <summary>U-174 (D-174): an item's weight in the pack (kg; D1Tables, 0 for what they do not list). Null: weightless.</summary>
        public static Func<int, float> KgOf;
        /// <summary>U-174: the pack's weight limit (kg; 30 at the start, Haul raises it). Infinite: no limit (a plain inventory).</summary>
        public float LimitKg = float.PositiveInfinity;
        /// <summary>U-174: raised when an Add is cut short by the weight limit (the HUD's "pack full" cue).</summary>
        public event Action Refused;
        /// <summary>U-188: Refused's listeners (tests: none may be a destroyed planet-scene object; the inventory outlives every planet).</summary>
        public Delegate[] RefusedListeners() => Refused != null ? Refused.GetInvocationList() : Array.Empty<Delegate>();

        /// <summary>U-174: what the pack weighs now (kg).</summary>
        public float Weight
        {
            get
            {
                if (KgOf == null) return 0f;
                float w = 0f;
                for (int i = 0; i < SlotCount; i++) if (!slots[i].IsEmpty) w += slots[i].count * KgOf(slots[i].itemId);
                return w;
            }
        }

        /// <summary>U-174: how many of the item still fit under the weight limit (int.MaxValue when weightless or unlimited).</summary>
        public int FitsByWeight(int itemId)
        {
            if (KgOf == null || float.IsPositiveInfinity(LimitKg)) return int.MaxValue;
            float kg = KgOf(itemId);
            if (kg <= 0f) return int.MaxValue;
            return Math.Max(0, (int)Math.Floor((LimitKg - Weight) / kg + 1e-4));
        }

        /// <summary>Adds up to `count`; returns how many didn't fit (the slots, or U-174's weight limit).</summary>
        public int Add(int itemId, int count)
        {
            if (itemId <= 0 || count <= 0) return Math.Max(0, count);
            int over = 0, fits = FitsByWeight(itemId);
            if (fits < count) { over = count - fits; count = fits; Refused?.Invoke(); if (count == 0) return over; }
            int max = MaxOf(itemId), left = count;
            for (int i = 0; i < SlotCount && left > 0; i++)
            {
                if (slots[i].itemId != itemId || slots[i].IsEmpty || slots[i].count >= max) continue;
                int put = Math.Min(max - slots[i].count, left);
                slots[i].count += put;
                left -= put;
            }
            for (int i = 0; i < SlotCount && left > 0; i++)
            {
                if (!slots[i].IsEmpty) continue;
                int put = Math.Min(max, left);
                slots[i] = new ItemStack { itemId = itemId, count = put };
                left -= put;
            }
            if (left != count) Changed?.Invoke();
            return left + over;
        }

        /// <summary>Removes exactly `count` if there are that many (from the last stacks first); false and no change otherwise.</summary>
        public bool Remove(int itemId, int count)
        {
            if (count <= 0) return true;
            if (Count(itemId) < count) return false;
            int left = count;
            for (int i = SlotCount - 1; i >= 0 && left > 0; i--)
            {
                if (slots[i].itemId != itemId || slots[i].IsEmpty) continue;
                int take = Math.Min(slots[i].count, left);
                slots[i].count -= take;
                left -= take;
                if (slots[i].count == 0) slots[i] = default;
            }
            Changed?.Invoke();
            return true;
        }

        /// <summary>Takes `count` from one slot (the Builder uses its selected stack); false and no change if it holds fewer.</summary>
        public bool TakeFrom(int slot, int count)
        {
            if (slot < 0 || slot >= SlotCount || count <= 0 || slots[slot].count < count) return false;
            slots[slot].count -= count;
            if (slots[slot].count == 0) slots[slot] = default;
            Changed?.Invoke();
            return true;
        }

        public int Count(int itemId)
        {
            int n = 0;
            for (int i = 0; i < SlotCount; i++) if (slots[i].itemId == itemId && !slots[i].IsEmpty) n += slots[i].count;
            return n;
        }

        /// <summary>Moves `count` from a slot into the first empty slot; false if there's none or the count is bad.</summary>
        public bool Split(int slot, int count)
        {
            if (slot < 0 || slot >= SlotCount || count <= 0 || count >= slots[slot].count) return false;
            for (int i = 0; i < SlotCount; i++)
            {
                if (!slots[i].IsEmpty) continue;
                slots[i] = new ItemStack { itemId = slots[slot].itemId, count = count };
                slots[slot].count -= count;
                Changed?.Invoke();
                return true;
            }
            return false;
        }

        /// <summary>Drops slot `from` onto `to`: merges the same item up to the stack cap, otherwise swaps.</summary>
        public void Move(int from, int to)
        {
            if (from == to || from < 0 || to < 0 || from >= SlotCount || to >= SlotCount || slots[from].IsEmpty) return;
            if (slots[to].itemId == slots[from].itemId && !slots[to].IsEmpty)
            {
                int put = Math.Min(MaxOf(slots[to].itemId) - slots[to].count, slots[from].count);
                slots[to].count += put;
                slots[from].count -= put;
                if (slots[from].count == 0) slots[from] = default;
            }
            else (slots[from], slots[to]) = (slots[to], slots[from]);
            Changed?.Invoke();
        }

        public void Select(int slot)
        {
            if (slot < 0 || slot >= SlotCount || slot == Selected) return;
            Selected = slot;
            Changed?.Invoke();
        }

        /// <summary>The selected stack's item if the Builder can place it (0 otherwise).</summary>
        public byte SelectedTile
        {
            get
            {
                var s = slots[Selected];
                return s.IsEmpty ? (byte)0 : ItemRegistry.Get(s.itemId)?.placeTile ?? 0;
            }
        }

        public void Clear()
        {
            Array.Clear(slots, 0, SlotCount);
            Selected = 0;
            Changed?.Invoke();
        }

        /// <summary>Save form (SaveData v2): every slot in order, empty ones included, so positions survive.</summary>
        public void WriteTo(List<ItemStack> list)
        {
            list.Clear();
            for (int i = 0; i < SlotCount; i++) list.Add(slots[i].IsEmpty ? default : slots[i]);
        }

        /// <summary>Loads slots in order; unknown items (from a newer build) are dropped, stacks clamped.</summary>
        public void ReadFrom(List<ItemStack> list, int selected)
        {
            Array.Clear(slots, 0, SlotCount);
            if (list != null)
                for (int i = 0; i < SlotCount && i < list.Count; i++)
                {
                    var s = list[i];
                    if (s.IsEmpty || ItemRegistry.Get(s.itemId) == null) continue;
                    slots[i] = new ItemStack { itemId = s.itemId, count = Math.Min(s.count, MaxOf(s.itemId)) };
                }
            Selected = selected >= 0 && selected < SlotCount ? selected : 0;
            Changed?.Invoke();
        }
    }
}
