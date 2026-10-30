using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Meridian.Art;
using UnityEditor;
using UnityEditor.AddressableAssets;
using UnityEditor.AddressableAssets.Settings;
using UnityEditor.AddressableAssets.Settings.GroupSchemas;
using UnityEditor.U2D;
using UnityEditor.U2D.Sprites;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// Enforces the asset contract §6 on every PNG under Art/ and Placeholders/: import settings
    /// per category, secondary textures, frame-sheet slicing, Addressable address = key, atlas
    /// membership, and placeholder retirement. No manual step.
    /// </summary>
    public sealed class ArtImporter : AssetPostprocessor
    {
        /// <summary>Folders the importer watches. Tests point these at a sandbox and restore them.</summary>
        public sealed class Roots
        {
            public string art = "Assets/_Game/Art/";
            public string placeholders = "Assets/_Game/Placeholders/";
            public string atlasFolder = "Assets/_Game/Settings/Atlases/";
            public string groupPrefix = "";
            public string blenderManifest = "blender/manifest.json";
        }

        public static Roots Active = new Roots();

        [Serializable] class SheetClip { public string name; public int start, length; public bool loop; }

        [Serializable]
        public class SheetManifest
        {
            public string key;
            public int frame_width, frame_height, columns, frames, fps = 12;
            public int gutter = 4;
            public float[] pivot;
            public string facing = "right";
        }

        [Serializable] class BlenderAsset { public string key; public float[] pivot; }
        [Serializable] class BlenderManifest { public BlenderAsset[] assets; }

        // ---------- path helpers ----------

        enum RootKind { None, Art, Placeholder }

        static RootKind Classify(string path, out string relative)
        {
            path = ArtRules.Normalize(path);
            relative = null;
            if (path.StartsWith(Active.art, StringComparison.Ordinal)) { relative = path.Substring(Active.art.Length); return RootKind.Art; }
            if (path.StartsWith(Active.placeholders, StringComparison.Ordinal)) { relative = path.Substring(Active.placeholders.Length); return RootKind.Placeholder; }
            return RootKind.None;
        }

        public static string ArtColorPath(string key) => Active.art + key + "_color.png";
        public static string PlaceholderColorPath(string key) => Active.placeholders + key + "_color.png";

        // ---------- preprocess: import settings ----------

        void OnPreprocessTexture()
        {
            var kind = Classify(assetPath, out var rel);
            if (kind == RootKind.None || !rel.EndsWith(".png", StringComparison.Ordinal)) return;
            var ti = (TextureImporter)assetImporter;

            if (!ArtRules.TryParse(rel, out var key, out var map))
            {
                Debug.LogError($"[ArtImporter] Rejected {assetPath}: name must be <category>/<name>/<variant>_<color|normal|emission|mask>.png, lowercase a-z 0-9 _ (contract §1).");
                return;
            }
            ti.GetSourceTextureWidthAndHeight(out int w, out int h);
            var reason = ArtRules.Validate(ArtRules.FileBytes(assetPath), w, h);
            if (reason != null)
            {
                Debug.LogError($"[ArtImporter] Rejected {assetPath}: {reason} (contract §2).");
                return;
            }

            var rule = ArtRules.RuleFor(key);
            ti.mipmapEnabled = rule.mips;
            ti.filterMode = FilterMode.Bilinear;
            ti.wrapMode = rule.repeat ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
            ti.maxTextureSize = ArtRules.MaxDimension;
            ti.textureCompression = TextureImporterCompression.CompressedHQ;

            switch (map)
            {
                case ArtMap.Color: ConfigureColor(ti, key, rule, w, h); break;
                case ArtMap.Normal:
                    ti.textureType = TextureImporterType.NormalMap;
                    ti.sRGBTexture = false;
                    SetStandaloneFormat(ti, TextureImporterFormat.BC5);
                    break;
                case ArtMap.Emission:
                    ti.textureType = TextureImporterType.Default;
                    ti.sRGBTexture = true;
                    SetStandaloneFormat(ti, TextureImporterFormat.BC7);
                    break;
                case ArtMap.Mask:
                    ti.textureType = TextureImporterType.Default;
                    ti.sRGBTexture = false;
                    SetStandaloneFormat(ti, TextureImporterFormat.BC7);
                    break;
            }
        }

        void ConfigureColor(TextureImporter ti, string key, CategoryRule rule, int w, int h)
        {
            ti.textureType = TextureImporterType.Sprite;
            ti.sRGBTexture = true;
            ti.alphaIsTransparency = true;
            ti.spritePixelsPerUnit = ArtRules.PixelsPerUnit;
            SetStandaloneFormat(ti, TextureImporterFormat.BC7);

            var sheet = LoadSheet(ArtRules.SheetJsonPath(assetPath));
            if (sheet == null && rule.requiresSheet)
                Debug.LogError($"[ArtImporter] {assetPath}: frame sheet has no {Path.GetFileName(ArtRules.SheetJsonPath(assetPath))} (contract §5); imported as a single sprite.");

            var pivot = PivotFor(key, sheet, h);
            var s = new TextureImporterSettings();
            ti.ReadTextureSettings(s);
            s.spriteMeshType = rule.fullRect ? SpriteMeshType.FullRect : SpriteMeshType.Tight;
            s.spriteAlignment = (int)SpriteAlignment.Custom;
            s.spritePivot = pivot;
            s.spriteMode = sheet != null ? (int)SpriteImportMode.Multiple : (int)SpriteImportMode.Single;
            ti.SetTextureSettings(s);
            ti.spriteImportMode = sheet != null ? SpriteImportMode.Multiple : SpriteImportMode.Single;
            // Rects are applied in postprocess (SliceIfNeeded): sprite data written during
            // preprocess is not picked up by the import already in flight.
        }

        static void SetStandaloneFormat(TextureImporter ti, TextureImporterFormat format)
        {
            var p = ti.GetPlatformTextureSettings("Standalone");
            p.overridden = true;
            p.format = format;
            p.compressionQuality = 100;
            p.maxTextureSize = ArtRules.MaxDimension;
            ti.SetPlatformTextureSettings(p);
        }

        public static SheetManifest LoadSheet(string jsonPath)
        {
            if (!File.Exists(jsonPath)) return null;
            try
            {
                var m = JsonUtility.FromJson<SheetManifest>(File.ReadAllText(jsonPath));
                if (m == null || m.frame_width <= 0 || m.frame_height <= 0 || m.columns <= 0 || m.frames <= 0)
                {
                    Debug.LogError($"[ArtImporter] {jsonPath}: needs frame_width, frame_height, columns, frames > 0 (contract §5).");
                    return null;
                }
                return m;
            }
            catch (Exception e)
            {
                Debug.LogError($"[ArtImporter] {jsonPath}: invalid JSON ({e.Message}).");
                return null;
            }
        }

        static Vector2 PivotFor(string key, SheetManifest sheet, int height)
        {
            if (sheet?.pivot != null && sheet.pivot.Length == 2) return new Vector2(sheet.pivot[0], sheet.pivot[1]);
            var fromBlender = BlenderPivot(key);
            if (fromBlender.HasValue) return fromBlender.Value;
            return ArtRules.DefaultPivot(key, sheet != null ? sheet.frame_height : height);
        }

        static Vector2? BlenderPivot(string key)
        {
            var path = Active.blenderManifest;
            if (string.IsNullOrEmpty(path) || !File.Exists(path)) return null;
            try
            {
                var m = JsonUtility.FromJson<BlenderManifest>(File.ReadAllText(path));
                var a = m?.assets?.FirstOrDefault(x => x.key == key);
                if (a?.pivot != null && a.pivot.Length == 2) return new Vector2(a.pivot[0], a.pivot[1]);
            }
            catch (Exception) { /* malformed manifest: fall back to the category default */ }
            return null;
        }

        /// <summary>Frame rects: row-major from the top-left, gutters between frames, no outer margin.</summary>
        public static List<Rect> FrameRects(SheetManifest m, int textureHeight)
        {
            var rects = new List<Rect>(m.frames);
            for (int i = 0; i < m.frames; i++)
            {
                int col = i % m.columns, row = i / m.columns;
                float x = col * (m.frame_width + m.gutter);
                float yTop = row * (m.frame_height + m.gutter);
                rects.Add(new Rect(x, textureHeight - yTop - m.frame_height, m.frame_width, m.frame_height));
            }
            return rects;
        }

        /// <summary>Applies the sheet's frame rects; returns true when they changed (caller reimports).</summary>
        static bool SliceIfNeeded(string colorPath, string key)
        {
            var m = LoadSheet(ArtRules.SheetJsonPath(colorPath));
            var ti = AssetImporter.GetAtPath(colorPath) as TextureImporter;
            if (m == null || ti == null || ti.spriteImportMode != SpriteImportMode.Multiple) return false;
            ti.GetSourceTextureWidthAndHeight(out int w, out int h);
            var pivot = PivotFor(key, m, h);

            var factory = new SpriteDataProviderFactories();
            factory.Init();
            var dp = factory.GetSpriteEditorDataProviderFromObject(ti);
            dp.InitSpriteEditorDataProvider();

            var current = dp.GetSpriteRects();
            var existing = current.GroupBy(r => r.name).ToDictionary(g => g.Key, g => g.First().spriteID);
            var variant = key.Substring(key.LastIndexOf('/') + 1);
            var frames = FrameRects(m, h);
            if (current.Length == frames.Count && current.Select((r, i) =>
                    r.name == $"{variant}_{i}" && r.rect == frames[i] && r.pivot == pivot).All(x => x))
                return false;

            var rects = new SpriteRect[frames.Count];
            for (int i = 0; i < frames.Count; i++)
            {
                var name = $"{variant}_{i}";
                rects[i] = new SpriteRect
                {
                    name = name,
                    rect = frames[i],
                    alignment = SpriteAlignment.Custom,
                    pivot = pivot,
                    spriteID = existing.TryGetValue(name, out var id) ? id : GUID.Generate(),
                };
                if (frames[i].xMax > w || frames[i].y < 0)
                    Debug.LogError($"[ArtImporter] {colorPath}: frame {i} lies outside the {w}×{h} sheet; check columns/gutter in the .json.");
            }
            dp.SetSpriteRects(rects);
            var names = dp.GetDataProvider<ISpriteNameFileIdDataProvider>();
            names?.SetNameFileIdPairs(rects.Select(r => new SpriteNameFileIdPair(r.name, r.spriteID)));
            dp.Apply();
            ti.SaveAndReimport();
            return true;
        }

        // ---------- postprocess: secondaries, addresses, atlases, placeholders ----------

        static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            var colors = new HashSet<string>();
            var retireKeys = new HashSet<string>();
            var restoreKeys = new HashSet<string>();

            foreach (var raw in imported.Concat(moved))
            {
                var kind = Classify(raw, out var rel);
                if (kind == RootKind.None) continue;
                var path = ArtRules.Normalize(raw);
                if (rel.EndsWith(".json", StringComparison.Ordinal))
                {
                    // A new or edited sheet manifest re-slices its color sheet.
                    var color = path.Substring(0, path.Length - ".json".Length) + "_color.png";
                    if (File.Exists(color)) AssetDatabase.ImportAsset(color, ImportAssetOptions.ForceUpdate);
                    continue;
                }
                if (!ArtRules.TryParse(rel, out var key, out var map)) continue;
                var colorPath = (kind == RootKind.Art ? Active.art : Active.placeholders) + key + "_color.png";
                if (File.Exists(colorPath)) colors.Add(colorPath);
            }

            foreach (var raw in deleted.Concat(movedFrom))
            {
                var kind = Classify(raw, out var rel);
                if (kind == RootKind.Art && ArtRules.TryParse(rel, out var key, out var map) && map == ArtMap.Color)
                    restoreKeys.Add(key);
            }

            foreach (var colorPath in colors)
            {
                Classify(colorPath, out var rel);
                ArtRules.TryParse(rel, out var key, out _);
                if (!PassesValidation(colorPath)) continue;
                SliceIfNeeded(colorPath, key);
                LinkSecondaries(colorPath, key);
                bool isArt = colorPath.StartsWith(Active.art, StringComparison.Ordinal);
                if (isArt)
                {
                    Register(colorPath, key);
                    retireKeys.Add(key);
                }
                else if (!File.Exists(ArtColorPath(key)))
                {
                    Register(colorPath, key);
                }
            }

            foreach (var key in retireKeys) RetirePlaceholder(key);
            foreach (var key in restoreKeys)
            {
                var ph = PlaceholderColorPath(key);
                if (File.Exists(ph) && !File.Exists(ArtColorPath(key))) Register(ph, key);
            }
        }

        static bool PassesValidation(string colorPath)
        {
            var ti = AssetImporter.GetAtPath(colorPath) as TextureImporter;
            if (ti == null) return false;
            ti.GetSourceTextureWidthAndHeight(out int w, out int h);
            return ArtRules.Validate(ArtRules.FileBytes(colorPath), w, h) == null;
        }

        static void LinkSecondaries(string colorPath, string key)
        {
            var ti = AssetImporter.GetAtPath(colorPath) as TextureImporter;
            if (ti == null) return;
            var wanted = new List<SecondarySpriteTexture>();
            Add(ArtMap.Normal, "_NormalMap");
            Add(ArtMap.Emission, "_EmissionMap");
            Add(ArtMap.Mask, "_MaskTex");

            if (ArtRules.RuleFor(key).lit && !File.Exists(ArtRules.SiblingPath(colorPath, ArtMap.Normal)))
                Debug.LogWarning($"[ArtImporter] {colorPath}: lit category without a _normal.png (contract §1).");

            var current = ti.secondarySpriteTextures ?? Array.Empty<SecondarySpriteTexture>();
            bool same = current.Length == wanted.Count &&
                        current.Zip(wanted, (a, b) => a.name == b.name && a.texture == b.texture).All(x => x);
            if (same) return;
            ti.secondarySpriteTextures = wanted.ToArray();
            ti.SaveAndReimport();

            void Add(ArtMap map, string name)
            {
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(ArtRules.SiblingPath(colorPath, map));
                if (tex != null) wanted.Add(new SecondarySpriteTexture { name = name, texture = tex });
            }
        }

        // ---------- Addressables ----------

        public static AddressableAssetSettings Settings => AddressableAssetSettingsDefaultObject.GetSettings(true);

        public static AddressableAssetGroup GroupNamed(string name)
        {
            var settings = Settings;
            var full = Active.groupPrefix + name;
            var group = settings.FindGroup(full);
            if (group == null)
                group = settings.CreateGroup(full, false, false, true, null,
                    typeof(BundledAssetGroupSchema), typeof(ContentUpdateGroupSchema));
            return group;
        }

        static void Register(string colorPath, string key)
        {
            var guid = AssetDatabase.AssetPathToGUID(colorPath);
            if (string.IsNullOrEmpty(guid)) return;
            var entry = Settings.CreateOrMoveEntry(guid, GroupNamed(ArtRules.GroupFor(key)), false, true);
            if (entry.address != key) entry.SetAddress(key, true);
            var atlas = ArtRules.AtlasFor(key);
            if (atlas != null) AddToAtlas(atlas, colorPath);
        }

        static void RetirePlaceholder(string key)
        {
            var ph = PlaceholderColorPath(key);
            var guid = AssetDatabase.AssetPathToGUID(ph);
            if (string.IsNullOrEmpty(guid)) return;
            if (Settings.FindAssetEntry(guid) != null) Settings.RemoveAssetEntry(guid, true);
            var atlas = ArtRules.AtlasFor(key);
            if (atlas != null) RemoveFromAtlas(atlas, ph);
        }

        // ---------- atlases (Sprite Atlas v2) ----------

        public static string AtlasPath(string atlas) => Active.atlasFolder + Active.groupPrefix + atlas + ".spriteatlasv2";

        static void AddToAtlas(string atlas, string texturePath)
        {
            var path = AtlasPath(atlas);
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
            if (tex == null) return;
            var guid = AssetDatabase.AssetPathToGUID(texturePath);
            SpriteAtlasAsset asset;
            if (File.Exists(path))
            {
                if (File.ReadAllText(path).Contains(guid)) return;
                asset = SpriteAtlasAsset.Load(path);
            }
            else
            {
                Directory.CreateDirectory(Active.atlasFolder);
                asset = new SpriteAtlasAsset();
            }
            asset.Add(new UnityEngine.Object[] { tex });
            SpriteAtlasAsset.Save(asset, path);
            AssetDatabase.ImportAsset(path);
        }

        static void RemoveFromAtlas(string atlas, string texturePath)
        {
            var path = AtlasPath(atlas);
            var guid = AssetDatabase.AssetPathToGUID(texturePath);
            if (!File.Exists(path) || !File.ReadAllText(path).Contains(guid)) return;
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
            var asset = SpriteAtlasAsset.Load(path);
            asset.Remove(new UnityEngine.Object[] { tex });
            SpriteAtlasAsset.Save(asset, path);
            AssetDatabase.ImportAsset(path);
        }
    }
}
