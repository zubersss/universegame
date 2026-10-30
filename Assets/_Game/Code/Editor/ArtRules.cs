using System.IO;
using System.Text.RegularExpressions;
using Meridian.Art;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>Per-category import rules from the asset contract §2 and §4 (pure, testable).</summary>
    public readonly struct CategoryRule
    {
        public readonly bool lit, mips, fullRect, bottomPivot, requiresSheet, repeat;

        public CategoryRule(bool lit, bool mips, bool fullRect, bool bottomPivot, bool requiresSheet, bool repeat)
        {
            this.lit = lit; this.mips = mips; this.fullRect = fullRect;
            this.bottomPivot = bottomPivot; this.requiresSheet = requiresSheet; this.repeat = repeat;
        }
    }

    public static class ArtRules
    {
        public const int PixelsPerUnit = 128;
        public const int MaxDimension = 2048;
        public const long MaxFileBytes = 4L * 1024 * 1024;
        public const int DefaultPaddingPx = 8;

        // <root>/<category>/<name>/<variant>_<map>.png, lowercase a-z 0-9 _ (contract §1).
        static readonly Regex KeyPattern = new Regex(@"^[a-z0-9_]+(/[a-z0-9_]+){2}$");
        static readonly Regex FilePattern = new Regex(@"^(?<key>.+)_(?<map>color|normal|emission|mask)\.png$");

        public static readonly string[] Categories =
            { "planets", "terrain", "backgrounds", "ships", "characters", "creatures", "props", "fx", "icons", "ui" };

        /// <summary>Splits a path relative to a root into key and map. False if the name breaks §1.</summary>
        public static bool TryParse(string relativePath, out string key, out ArtMap map)
        {
            key = null; map = ArtMap.Color;
            var m = FilePattern.Match(relativePath);
            if (!m.Success) return false;
            key = m.Groups["key"].Value;
            if (!KeyPattern.IsMatch(key)) return false;
            if (System.Array.IndexOf(Categories, ArtKeys.Category(key)) < 0) return false;
            map = m.Groups["map"].Value switch
            {
                "normal" => ArtMap.Normal,
                "emission" => ArtMap.Emission,
                "mask" => ArtMap.Mask,
                _ => ArtMap.Color,
            };
            return true;
        }

        public static CategoryRule RuleFor(string key)
        {
            switch (ArtKeys.Category(key))
            {
                //                                 lit    mips   full   bottom sheet  repeat
                case "planets": return new CategoryRule(false, true, true, false, false, true);
                case "terrain": return new CategoryRule(true, true, true, false, false, false);
                case "backgrounds": return new CategoryRule(false, true, true, false, false, true);
                case "ships": return new CategoryRule(true, true, false, false, false, false);
                case "characters": return new CategoryRule(true, true, false, true, true, false);
                case "creatures": return new CategoryRule(true, true, false, true, true, false);
                case "props": return new CategoryRule(true, true, false, true, false, false);
                case "fx": return new CategoryRule(false, false, true, false, false, false);
                default: return new CategoryRule(false, false, true, false, false, false); // icons, ui
            }
        }

        static string Segment(string key, int i)
        {
            var parts = key.Split('/');
            return i < parts.Length ? parts[i] : "";
        }

        /// <summary>Addressables group (Bible §10.3): planet_&lt;name&gt; loads with the planet, common stays resident.</summary>
        public static string GroupFor(string key)
        {
            var second = Segment(key, 1);
            switch (ArtKeys.Category(key))
            {
                case "terrain":
                case "creatures": return "planet_" + second;
                case "props": return second == "common" ? "common" : "planet_" + second;
                case "backgrounds": return second == "space" ? "space" : "planet_" + second;
                case "planets": return "space";
                case "icons": return "icons";
                case "ui": return "ui";
                default: return "common"; // ships, characters, fx
            }
        }

        /// <summary>Sprite atlas from contract §4, or null for categories without one.</summary>
        public static string AtlasFor(string key)
        {
            var second = Segment(key, 1);
            switch (ArtKeys.Category(key))
            {
                case "terrain":
                case "creatures": return "planet_" + second;
                case "props": return second == "common" ? "common" : "planet_" + second;
                case "ships":
                case "characters":
                case "fx": return "common";
                case "icons": return "icons";
                case "ui": return "ui";
                default: return null; // planets, backgrounds: shader textures / full-screen layers
            }
        }

        /// <summary>Null when the file meets §2; otherwise the one-line rejection reason.</summary>
        public static string Validate(long fileBytes, int width, int height)
        {
            if (fileBytes > MaxFileBytes) return $"file is {fileBytes / 1024} KB, over the 4 MB limit";
            if (width > MaxDimension || height > MaxDimension) return $"{width}×{height} exceeds {MaxDimension}×{MaxDimension}";
            return null;
        }

        /// <summary>Default pivot when neither the sheet .json nor blender/manifest.json gives one.</summary>
        public static Vector2 DefaultPivot(string key, int height)
        {
            if (!RuleFor(key).bottomPivot || height <= 0) return new Vector2(0.5f, 0.5f);
            return new Vector2(0.5f, Mathf.Min(DefaultPaddingPx, height) / (float)height);
        }

        public static string SiblingPath(string colorPath, ArtMap map) =>
            colorPath.Substring(0, colorPath.Length - "color.png".Length) + ArtKeys.MapSuffix(map) + ".png";

        public static string SheetJsonPath(string colorPath) =>
            colorPath.Substring(0, colorPath.Length - "_color.png".Length) + ".json";

        public static string Normalize(string path) => path.Replace('\\', '/');

        public static long FileBytes(string assetPath)
        {
            var fi = new FileInfo(assetPath);
            return fi.Exists ? fi.Length : 0;
        }
    }
}
