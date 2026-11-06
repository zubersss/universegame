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
        /// <summary>U-091 (contract §10): a planet's stage-layer textures, all regions, ≤ 700 MB stored (BC7/BC5 with mips).</summary>
        public const long LayerCapBytes = 700L * 1024L * 1024L;
        public const long MaxFileBytes = 4L * 1024 * 1024;
        public const int DefaultPaddingPx = 8;

        // <root>/<category>/<name>/<variant>_<map>.png, lowercase a-z 0-9 _ (contract §1).
        static readonly Regex KeyPattern = new Regex(@"^[a-z0-9_]+(/[a-z0-9_]+){2}$");
        static readonly Regex FilePattern = new Regex(@"^(?<key>.+)_(?<map>color|normal|emission|mask)\.png$");

        public static readonly string[] Categories =
            { "planets", "terrain", "backgrounds", "ships", "characters", "creatures", "props", "fx", "icons", "ui" };

        /// <summary>Splits a path relative to a root into key and map. False if the name breaks §1.</summary>
        // U-073 / B-080 (contract v2): block materials, not sprites.
        static readonly Regex BlockPattern = new Regex(
            @"^terrain/(?<planet>[a-z0-9_]+)/(?:(?<mat>[a-z0-9_]+)/(?<face>top|side)|(?<wall>backwall))_(?<map>color|normal|mask)\.png$");

        /// <summary>
        /// A 3D block material texture: terrain/&lt;planet&gt;/&lt;material&gt;/{top,side}_&lt;map&gt;.png or
        /// terrain/&lt;planet&gt;/backwall_&lt;map&gt;.png (512², tileable at 2 m; color/normal/mask).
        /// face is "top", "side" or "wall"; material is "backwall" for the wall.
        /// </summary>
        public static bool IsBlockTexture(string relativePath, out string planet, out string material, out string face, out ArtMap map)
        {
            planet = material = face = null; map = ArtMap.Color;
            var m = BlockPattern.Match(relativePath ?? "");
            if (!m.Success) return false;
            planet = m.Groups["planet"].Value;
            bool wall = m.Groups["wall"].Success;
            material = wall ? "backwall" : m.Groups["mat"].Value;
            face = wall ? "wall" : m.Groups["face"].Value;
            map = m.Groups["map"].Value switch { "normal" => ArtMap.Normal, "mask" => ArtMap.Mask, _ => ArtMap.Color };
            return true;
        }

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
        public static string Validate(long fileBytes, int width, int height) => Validate(fileBytes, width, height, false);

        /// <summary>
        /// D-072 (P-34, contract v2.4): a model map (beside a .glb, or a model folder's shared atlas) keeps the 2048² cap and the
        /// runtime texture budget but is exempt from the 4 MB PNG-bytes cap: PNG bytes measure source entropy, not
        /// runtime cost (stored BC7/BC5, a 2048² map costs the same whatever its PNG size).
        /// </summary>
        public static string Validate(long fileBytes, int width, int height, bool modelMap)
        {
            if (!modelMap && fileBytes > MaxFileBytes) return $"file is {fileBytes / 1024} KB, over the 4 MB limit";
            if (width > MaxDimension || height > MaxDimension) return $"{width}×{height} exceeds {MaxDimension}×{MaxDimension}";
            return null;
        }

        /// <summary>
        /// U-091 (contract §10): the key is a stage-layer texture of `planet`: backgrounds/<planet>/… (rocks atlas, clouds, sky),
        /// backgrounds/<planet>_<region>/… (ridge, hills, skyline, set-pieces) or props/<planet>_foreground/… (the foreground atlas).
        /// </summary>
        public static bool IsStageLayer(string key, out string planet)
        {
            planet = null;
            var category = ArtKeys.Category(key);
            var second = Segment(key, 1);
            if (category == "backgrounds")
            {
                foreach (PlanetId id in System.Enum.GetValues(typeof(PlanetId)))
                {
                    var p = id.ToString().ToLowerInvariant();
                    if (second == p || second.StartsWith(p + "_", System.StringComparison.Ordinal)) { planet = p; return true; }
                }
                return false;
            }
            if (category == "props" && second.EndsWith("_foreground", System.StringComparison.Ordinal))
            {
                planet = second.Substring(0, second.Length - "_foreground".Length);
                return true;
            }
            return false;
        }

        /// <summary>Stored size of a BC7/BC5 texture with mips: 1 byte per texel × 4/3 (both formats are 8 bits per texel).</summary>
        public static long StoredBytes(int width, int height) => (long)width * height * 4L / 3L;

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
