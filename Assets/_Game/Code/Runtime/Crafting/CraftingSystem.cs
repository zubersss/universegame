using System.Collections.Generic;
using Meridian.Items;
using UnityEngine;

namespace Meridian.Crafting
{
    /// <summary>
    /// U-051: crafting rules. A recipe needs its blueprint unlocked (no unlock flag, the flag "blueprint:&lt;id&gt;",
    /// or the blueprint's own story flag), its station in reach, and every input in the inventory. Crafting
    /// takes the inputs and adds the output (instant in v1). Pure apart from the station lookup.
    /// </summary>
    public static class CraftingSystem
    {
        public enum Result { Crafted, Locked, NoStation, MissingInputs, NoRoom, UnknownItem }

        /// <summary>A blueprint is unlocked when it has no unlock flag, or its flag (or "blueprint:id") is set.</summary>
        public static bool IsUnlocked(Blueprint b, ICollection<string> flags)
        {
            if (b == null) return true;
            if (string.IsNullOrEmpty(b.unlockFlag)) return true;
            return flags != null && (flags.Contains(b.unlockFlag) || flags.Contains("blueprint:" + b.id));
        }

        public static bool IsUnlocked(RecipeBook book, Recipe r, ICollection<string> flags) =>
            string.IsNullOrEmpty(r.blueprint) || IsUnlocked(book.FindBlueprint(r.blueprint), flags);

        public static bool HasInputs(Recipe r, Inventory inv)
        {
            foreach (var a in r.inputs)
            {
                var def = ItemRegistry.Get(a.item);
                if (def == null || inv.Count(def.id) < a.count) return false;
            }
            return true;
        }

        public static Result Check(RecipeBook book, Recipe r, Inventory inv, ICollection<string> flags, Vector2 at)
        {
            if (!IsUnlocked(book, r, flags)) return Result.Locked;
            if (r.station != Station.Hand && !CraftingStation.AnyNear(r.station, at)) return Result.NoStation;
            if (ItemRegistry.Get(r.output.item) == null) return Result.UnknownItem;
            if (!HasInputs(r, inv)) return Result.MissingInputs;
            return Result.Crafted;
        }

        /// <summary>Crafts once if everything checks out; the inventory is untouched otherwise.</summary>
        public static Result Craft(RecipeBook book, Recipe r, Inventory inv, ICollection<string> flags, Vector2 at)
        {
            var check = Check(book, r, inv, flags, at);
            if (check != Result.Crafted) return check;
            foreach (var a in r.inputs) inv.Remove(ItemRegistry.Get(a.item).id, a.count);
            int left = inv.Add(ItemRegistry.Get(r.output.item).id, r.output.count);
            if (left > 0)
            {
                // No room for the output: put the inputs back (they just left, so they fit).
                inv.Remove(ItemRegistry.Get(r.output.item).id, r.output.count - left);
                foreach (var a in r.inputs) inv.Add(ItemRegistry.Get(a.item).id, a.count);
                return Result.NoRoom;
            }
            return Result.Crafted;
        }
    }
}
