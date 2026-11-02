using System.Collections.Generic;
using Meridian.Crafting;
using Meridian.Items;
using Meridian.Planets;
using Meridian.Survey;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-069 (EditMode): M4 materials and gear (Bible §7.6–7.9, §4.2): registered, icon keyed, sourced, catalogued.</summary>
    public class M4ItemsTests
    {
        static readonly string[] Raw =
            { "metallic_hydrogen", "ammonia_ice", "phosphorus_pigment", "ring_ice", "ring_rock", "methane_ice", "deep_diamond", "superionic_ice" };
        static readonly string[] Gear = { "float_cell_mk2", "jetpack_mk2", "jetpack_mk3" };

        [Test]
        public void EveryNewItemIsRegisteredWithItsIconKey()
        {
            var ids = new HashSet<int>();
            foreach (var d in ItemRegistry.All) Assert.IsTrue(ids.Add(d.id), "unique item id " + d.id + " " + d.key);
            foreach (var key in Concat(Raw, Gear, new[] { "helium3_condensate", "deuterium" }))
            {
                var d = ItemRegistry.Get(key);
                Assert.NotNull(d, key);
                Assert.AreEqual($"icons/{key}/base", d.icon, key + ": icon key = item id (B-061)");
                Assert.AreEqual(0, d.placeTile, key + " is not a tile");
            }
        }

        [Test]
        public void EveryRawItemHasASourceAndACatalogueEntry()
        {
            foreach (var key in Raw)
            {
                Assert.IsTrue(GiantResources.TryGet(key, out var g), key + ": source in GiantResources");
                Assert.IsNotEmpty(g.planets, key);
                CollectionAssert.Contains(CraftingDefaults.RawItems, key, key + " counts as a world item");
                int id = ItemRegistry.Get(key).id;
                foreach (var p in g.planets)
                    Assert.IsNotNull(Catalogue.Find(p, Catalogue.MineralId(id)), $"{key} catalogued on {p}");
            }
            // Bible "Only here" lines.
            Assert.IsTrue(GiantResources.TryGet("metallic_hydrogen", out var mh) && mh.source == ResourceSource.DeepVein && mh.planets.Length == 1 && mh.planets[0] == PlanetId.Jupiter);
            Assert.IsTrue(GiantResources.TryGet("deep_diamond", out var dd) && dd.planets[0] == PlanetId.Uranus);
            Assert.IsTrue(GiantResources.TryGet("superionic_ice", out var si) && si.planets[0] == PlanetId.Neptune);
            Assert.IsTrue(GiantResources.TryGet("ring_ice", out var ri) && ri.source == ResourceSource.RingMining);
            Assert.IsNull(Catalogue.Find(PlanetId.Earth, Catalogue.MineralId(ItemRegistry.Get("metallic_hydrogen").id)), "giant finds stay on the giants");
        }

        [Test]
        public void GearHasARecipeWithItsBlueprint()
        {
            var recipes = CraftingDefaults.Recipes();
            var blueprints = CraftingDefaults.Blueprints();
            foreach (var key in Gear)
            {
                var r = recipes.Find(x => x.output.item == key);
                Assert.NotNull(r, key + ": recipe");
                Assert.NotNull(blueprints.Find(b => b.id == r.blueprint), key + ": blueprint " + r.blueprint);
            }
            Assert.AreEqual("beacon:uranus", blueprints.Find(b => b.id == "jetpack_mk3").unlockFlag, "§4.2: Jetpack Mk3 is story-gated at the Uranus beacon");
        }

        [Test]
        public void DefaultsHaveNoDuplicateIds()
        {
            var ids = new HashSet<string>();
            foreach (var r in CraftingDefaults.Recipes()) Assert.IsTrue(ids.Add(r.id), "recipe " + r.id);
            ids.Clear();
            foreach (var b in CraftingDefaults.Blueprints()) Assert.IsTrue(ids.Add(b.id), "blueprint " + b.id);
        }

        [Test]
        public void RecipeBookAssetLoadsWithTheM4Recipes()
        {
            var book = RecipeBook.Active;
            Assert.NotNull(book, "RecipeBook.asset (MERIDIAN/Authoring/Recipe Book reset)");
            var ids = new HashSet<string>();
            foreach (var r in book.recipes) Assert.IsTrue(ids.Add(r.id), "unique recipe id " + r.id);
            foreach (var id in new[] { "fab_float_cell_mk2", "fab_jetpack_mk2", "fab_jetpack_mk3", "refine_ring_ice", "smelt_ring_rock" })
                Assert.IsTrue(ids.Contains(id), id + " in the authored book");
        }

        static IEnumerable<string> Concat(params string[][] parts)
        {
            foreach (var p in parts) foreach (var s in p) yield return s;
        }
    }
}
