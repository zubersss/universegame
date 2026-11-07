using Meridian.Crafting;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-051: creates Settings/Resources/RecipeBook.asset from CraftingDefaults when it is missing or empty.
    /// An authored book is left alone (it is data: edit it in the Inspector); `force` rewrites it.
    /// </summary>
    public static class CraftingAuthoring
    {
        public const string Path = "Assets/_Game/Settings/Resources/RecipeBook.asset";

        [MenuItem("MERIDIAN/Authoring/Recipe Book (fill if empty)")]
        public static void Run() => Ensure(false);

        [MenuItem("MERIDIAN/Authoring/Recipe Book (reset to defaults)")]
        public static void Reset() => Ensure(true);

        public static RecipeBook Ensure(bool force)
        {
            var book = AssetDatabase.LoadAssetAtPath<RecipeBook>(Path);
            if (book == null)
            {
                book = ScriptableObject.CreateInstance<RecipeBook>();
                AssetDatabase.CreateAsset(book, Path);
            }
            var recipes = CraftingDefaults.Recipes();
            var blueprints = CraftingDefaults.Blueprints();
            // U-107: a book whose recipe or blueprint ids no longer match the defaults (retired fuel and tank recipes) is rewritten.
            bool stale = !SameIds(book.recipes.ConvertAll(r => r.id), recipes.ConvertAll(r => r.id))
                      || !SameIds(book.blueprints.ConvertAll(b => b.id), blueprints.ConvertAll(b => b.id));
            if (force || stale || book.recipes.Count == 0 || book.blueprints.Count == 0)
            {
                book.recipes = recipes;
                book.blueprints = blueprints;
                EditorUtility.SetDirty(book);
                AssetDatabase.SaveAssetIfDirty(book);
                Debug.Log($"[MERIDIAN] RecipeBook: {book.recipes.Count} recipes, {book.blueprints.Count} blueprints written.");
            }
            return book;
        }

        static bool SameIds(System.Collections.Generic.List<string> a, System.Collections.Generic.List<string> b)
        {
            if (a.Count != b.Count) return false;
            var set = new System.Collections.Generic.HashSet<string>(a);
            foreach (var id in b) if (!set.Contains(id)) return false;
            return true;
        }
    }
}
