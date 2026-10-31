using System;
using System.Collections.Generic;
using UnityEngine;

namespace Meridian.Crafting
{
    /// <summary>Where a recipe is made (Bible §8 economy): by hand, at a Smelter, a Refinery or a Fabricator.</summary>
    public enum Station { Hand, Smelter, Refinery, Fabricator }

    [Serializable]
    public struct Amount
    {
        public string item;  // ItemRegistry key
        public int count;
        public Amount(string item, int count) { this.item = item; this.count = count; }
    }

    [Serializable]
    public sealed class Recipe
    {
        public string id;
        public Station station;
        public Amount[] inputs;
        public Amount output;
        /// <summary>Blueprint that must be unlocked first (null or empty: none).</summary>
        public string blueprint;
    }

    /// <summary>A node of the Blueprint Tree (Bible §2: one story blueprint per beacon, plus the basic trades).</summary>
    [Serializable]
    public sealed class Blueprint
    {
        public string id, name;
        /// <summary>Icon item key (or null).</summary>
        public string icon;
        public string[] requires;
        /// <summary>Story flag that unlocks it (e.g. "beacon:mars"); null/empty: unlocked from the start.</summary>
        public string unlockFlag;
        /// <summary>Column in the tree panel (0 = basics).</summary>
        public int tier;
    }

    /// <summary>
    /// U-051: the game's recipes and Blueprint Tree as data (Settings/Resources/RecipeBook.asset, authored by
    /// MERIDIAN/Authoring from CraftingDefaults and editable in the Inspector afterwards).
    /// </summary>
    [CreateAssetMenu(menuName = "MERIDIAN/Recipe Book")]
    public sealed class RecipeBook : ScriptableObject
    {
        public const string ResourcePath = "RecipeBook";
        public List<Recipe> recipes = new List<Recipe>();
        public List<Blueprint> blueprints = new List<Blueprint>();

        static RecipeBook active;
        public static RecipeBook Active => active != null ? active : (active = Resources.Load<RecipeBook>(ResourcePath));

        public Blueprint FindBlueprint(string id)
        {
            foreach (var b in blueprints) if (b.id == id) return b;
            return null;
        }

        public Recipe FindRecipe(string id)
        {
            foreach (var r in recipes) if (r.id == id) return r;
            return null;
        }
    }
}
