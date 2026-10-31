using System.Collections.Generic;
using Meridian.Crafting;
using Meridian.Items;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>U-051 (EditMode): the authored RecipeBook is a sound graph: known items, no unreachable item, no cycles, a well-formed Blueprint Tree.</summary>
    public class CraftingGraphTests
    {
        static RecipeBook Book()
        {
            var book = AssetDatabase.LoadAssetAtPath<RecipeBook>("Assets/_Game/Settings/Resources/RecipeBook.asset");
            Assert.NotNull(book, "RecipeBook.asset authored (MERIDIAN/Authoring)");
            Assert.IsNotEmpty(book.recipes); Assert.IsNotEmpty(book.blueprints);
            return book;
        }

        [Test]
        public void EveryItemAndBlueprintIsKnown()
        {
            var book = Book();
            var ids = new HashSet<string>();
            foreach (var r in book.recipes)
            {
                Assert.IsTrue(ids.Add(r.id), "unique recipe id " + r.id);
                Assert.NotNull(ItemRegistry.Get(r.output.item), $"{r.id}: output {r.output.item}");
                Assert.Greater(r.output.count, 0, r.id);
                Assert.IsNotEmpty(r.inputs, r.id);
                foreach (var a in r.inputs) { Assert.NotNull(ItemRegistry.Get(a.item), $"{r.id}: input {a.item}"); Assert.Greater(a.count, 0); }
                if (!string.IsNullOrEmpty(r.blueprint)) Assert.NotNull(book.FindBlueprint(r.blueprint), $"{r.id}: blueprint {r.blueprint}");
            }
            foreach (var raw in CraftingDefaults.RawItems) Assert.NotNull(ItemRegistry.Get(raw), "raw item " + raw);
        }

        [Test]
        public void NoUnreachableItem()
        {
            var book = Book();
            var have = new HashSet<string>(CraftingDefaults.RawItems);
            bool grew = true;
            while (grew)
            {
                grew = false;
                foreach (var r in book.recipes)
                {
                    if (have.Contains(r.output.item)) continue;
                    bool ok = true;
                    foreach (var a in r.inputs) ok &= have.Contains(a.item);
                    if (ok) { have.Add(r.output.item); grew = true; }
                }
            }
            foreach (var r in book.recipes)
            {
                Assert.IsTrue(have.Contains(r.output.item), $"{r.id}: {r.output.item} can't be made from world items");
                foreach (var a in r.inputs) Assert.IsTrue(have.Contains(a.item), $"{r.id}: input {a.item} is never obtainable");
            }
        }

        [Test]
        public void NoCycles()
        {
            var book = Book();
            // Item graph: input → output. A cycle would let an item be made from itself.
            var edges = new Dictionary<string, List<string>>();
            foreach (var r in book.recipes)
                foreach (var a in r.inputs)
                {
                    if (!edges.TryGetValue(a.item, out var list)) edges[a.item] = list = new List<string>();
                    list.Add(r.output.item);
                }
            var state = new Dictionary<string, int>(); // 1 visiting, 2 done
            bool Visit(string n)
            {
                if (state.TryGetValue(n, out int s)) return s == 2;
                state[n] = 1;
                if (edges.TryGetValue(n, out var next)) foreach (var m in next) if (!Visit(m)) return false;
                state[n] = 2;
                return true;
            }
            foreach (var n in edges.Keys) Assert.IsTrue(Visit(n), "recipe cycle through " + n);

            // Blueprint Tree: requirements exist, sit in earlier tiers (so no cycles).
            foreach (var b in book.blueprints)
                if (b.requires != null)
                    foreach (var req in b.requires)
                    {
                        var r = book.FindBlueprint(req);
                        Assert.NotNull(r, $"{b.id} requires {req}");
                        Assert.Less(r.tier, b.tier, $"{b.id} comes after {req}");
                    }
        }

        [Test]
        public void StoryBlueprintsFollowTheBeacons()
        {
            var book = Book();
            var expected = new Dictionary<string, string>
            {
                { "survey_module", "beacon:earth" }, { "perchlorate_oxidizer", "beacon:mars" }, { "solarite_capacitor", "beacon:mercury" },
                { "float_cell_mk1", "beacon:venus" }, { "skip_drive_mk2", "beacon:saturn" }, { "deep_diamond_tip", "beacon:uranus" },
                { "thruster_mk3", "beacon:jupiter" },
            };
            foreach (var kv in expected) Assert.AreEqual(kv.Value, book.FindBlueprint(kv.Key)?.unlockFlag, $"Bible §2: {kv.Key}");
            Assert.IsTrue(CraftingSystem.IsUnlocked(book.FindBlueprint("smelting"), new List<string>()), "basics are known from the start");
            Assert.IsFalse(CraftingSystem.IsUnlocked(book.FindBlueprint("perchlorate_oxidizer"), new List<string>()));
            Assert.IsTrue(CraftingSystem.IsUnlocked(book.FindBlueprint("perchlorate_oxidizer"), new List<string> { "beacon:mars" }));
        }
    }
}
