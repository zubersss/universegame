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
    public sealed partial class ArtImporter : AssetPostprocessor
    {
        /// <summary>Bump when the import rules change so Unity re-imports the art everywhere (2: U-036 per-sheet ppu, 3: U-032 clips).</summary>
        public override uint GetVersion() => 13; // 13: U-094 v3 cartoon assets (contract v3.0 §11.8: Sprite at the json PPU 64, no mips, BC7, overlays 512², sheets ≤ 2048 at 12 fps with capped clips, Animator controllers, scene json addressed); 12: model maps flagged for mip streaming (P-36; the QualitySettings switch comes with U-091) and the Saturn ring sheet trilinear (U-086); 11: U-076 model colour maps are Default/sRGB with mips (ConfigureModelColor); 10: D-072 model maps exempt from the 4 MB cap (the flora atlases reimport); 3: U-032 clips; 4: U-060 mips only on POT; 5: U-075 model maps beside a .glb are not sprites; 6: B-080 block material textures; 7: model keys get a placeholder; 8: shared model atlases (B-085); 9: model materials, addresses, clips

        /// <summary>Folders the importer watches. Tests point these at a sandbox and restore them.</summary>
        public sealed class Roots
        {
            public string art = "Assets/_Game/Art/";
            public string placeholders = "Assets/_Game/Placeholders/";
            public string atlasFolder = "Assets/_Game/Settings/Atlases/";
            public string groupPrefix = "";
            public string blenderManifest = "blender/manifest.json";
            public string materialRegistry = "Assets/_Game/Settings/Resources/ArtMaterials.asset";
        }

        public static Roots Active = new Roots();

        [Serializable] public class SheetClip { public string name; public int start, length; public bool loop; public int loop_from; }

        [Serializable]
        public class SheetManifest
        {
            public string key;
            public int frame_width, frame_height, columns, frames, fps = 12;
            public int gutter = 4;
            /// <summary>Texels trimmed from every side of each frame rect (terrain: 1, see TerrainTileSet.FitToCell).</summary>
            public int inset;
            public float[] pivot;
            public string facing = "right";
            /// <summary>Optional pixels per metre for this sheet (D-031/D-034: creature sheets); 0 = the 128 default.</summary>
            public float ppu;
            /// <summary>Animation clips (contract §5); recorded in the runtime registry for U-032.</summary>
            public SheetClip[] animations;
            /// <summary>Contract v3.0 §11: "v3" routes the asset to the cartoon rules (ArtImporter v13).</summary>
            public string style;
            /// <summary>§11.6 film overlay / tileable image (no frames).</summary>
            public bool overlay, tile, squash_root;
            public bool IsV3 => style == "v3";
            /// <summary>A frame sheet (frames &gt; 0); a v3 sidecar without frames describes a single image.</summary>
            public bool IsSheet => frames > 0 && frame_width > 0 && frame_height > 0 && columns > 0;
        }

        [Serializable] class BlenderAsset { public string key; public float[] pivot; }
        [Serializable] class BlenderManifest { public BlenderAsset[] assets; }

        /// <summary>Re-applies every rule to all art and placeholders (after an importer change).</summary>
        [MenuItem("MERIDIAN/Reimport All Art")]
        public static void ReimportAll()
        {
            foreach (var root in new[] { Active.art, Active.placeholders })
            {
                var dir = root.TrimEnd('/');
                if (!AssetDatabase.IsValidFolder(dir)) continue;
                foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { dir }))
                    AssetDatabase.ImportAsset(AssetDatabase.GUIDToAssetPath(guid), ImportAssetOptions.ForceUpdate);
            }
            AssetDatabase.SaveAssets();
            Debug.Log("[MERIDIAN] ArtImporter reimported all art and placeholders.");
        }

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

        /// <summary>
        /// U-075 / B-085: the key's maps belong to a 3D model, not a sprite: its own &lt;key&gt;.glb exists, or it is a
        /// shared "atlas" material in a folder of models (props/earth_flora/atlas_* serves 11 flora models).
        /// </summary>
        public static bool IsModelKey(string key)
        {
            if (string.IsNullOrEmpty(key)) return false;
            if (File.Exists(Active.art + key + ".glb")) return true;
            int slash = key.LastIndexOf('/');
            if (slash < 0 || key.Substring(slash + 1) != "atlas") return false;
            var dir = Active.art + key.Substring(0, slash);
            return Directory.Exists(dir) && Directory.GetFiles(dir, "*.glb").Length > 0;
        }
        public static string PlaceholderColorPath(string key) => Active.placeholders + key + "_color.png";

        /// <summary>
        /// P-36 (U-077): a model map streams its mips (QualitySettings.streamingMipmapsActive), so maps of creatures and
        /// props that are off screen keep only their low mips in the build. Not the belt asteroids: they draw through
        /// Graphics.RenderMeshInstanced, which has no renderer for the streaming system to track.
        /// </summary>
        public static bool StreamsMips(string key) =>
            IsModelKey(key) && !key.StartsWith("props/space/asteroid_", StringComparison.Ordinal);

        /// <summary>
        /// U-077: a model's maps (its own, or its folder's shared atlas) that imported before the model existed were
        /// treated as sheets (B-101: the Venus scenery atlas came one commit before the Venus models, so its normal map
        /// was rejected by the 4 MB cap and kept Unity's default import). Re-imports every such map; returns the count.
        /// </summary>
        public static int EnsureModelMapsImported(string key)
        {
            int slash = key.LastIndexOf('/');
            var bases = new[] { key, slash < 0 ? null : key.Substring(0, slash) + "/atlas" };
            int count = 0;
            foreach (var mapKey in bases)
            {
                if (mapKey == null || !IsModelKey(mapKey)) continue;
                bool streams = StreamsMips(mapKey);
                foreach (ArtMap map in Enum.GetValues(typeof(ArtMap)))
                {
                    var path = Active.art + mapKey + "_" + map.ToString().ToLowerInvariant() + ".png";
                    if (!(AssetImporter.GetAtPath(path) is TextureImporter ti)) continue;
                    var want = map == ArtMap.Normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                    var fmt = ti.GetPlatformTextureSettings("Standalone").format;
                    bool ok = ti.textureType == want && ti.streamingMipmaps == streams
                              && fmt == (map == ArtMap.Normal ? TextureImporterFormat.BC5 : TextureImporterFormat.BC7);
                    if (ok) continue;
                    AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate);
                    count++;
                }
            }
            return count;
        }

        // ---------- preprocess: import settings ----------

        void OnPreprocessTexture()
        {
            var kind = Classify(assetPath, out var rel);
            if (kind == RootKind.None || !rel.EndsWith(".png", StringComparison.Ordinal)) return;
            var ti = (TextureImporter)assetImporter;

            // U-073 / B-080: block material textures are plain repeat-wrapped textures for the block arrays.
            if (kind == RootKind.Art && ArtRules.IsBlockTexture(rel, out _, out _, out _, out var blockMap))
            {
                ConfigureBlockTexture(ti, blockMap);
                return;
            }

            if (!ArtRules.TryParse(rel, out var key, out var map))
            {
                Debug.LogError($"[ArtImporter] Rejected {assetPath}: name must be <category>/<name>/<variant>_<color|normal|emission|mask>.png, lowercase a-z 0-9 _ (contract §1).");
                return;
            }
            ti.GetSourceTextureWidthAndHeight(out int w, out int h);
            var reason = ArtRules.Validate(ArtRules.FileBytes(assetPath), w, h, kind == RootKind.Art && IsModelKey(key)); // D-072: model maps are not capped by PNG bytes
            if (reason != null)
            {
                Debug.LogError($"[ArtImporter] Rejected {assetPath}: {reason} (contract §2).");
                return;
            }

            // U-094 (contract v3.0 §11, v13): cartoon assets take their own rules and skip the v2 lit/model paths.
            if (map == ArtMap.Color && ConfigureV3(ti, key, w, h)) return;

            // U-091 (contract §10): a planet's stage-layer textures stay under 700 MB stored; the newest layer over the cap is rejected.
            if (kind == RootKind.Art && ArtRules.IsStageLayer(key, out var layerPlanet))
            {
                long stored = StageLayerBytes(layerPlanet, assetPath) + ArtRules.StoredBytes(w, h);
                if (stored > ArtRules.LayerCapBytes)
                {
                    Debug.LogError($"[ArtImporter] Rejected {assetPath}: {layerPlanet}'s stage layers would store {stored / 1048576} MB, over the 700 MB cap (contract §10).");
                    return;
                }
            }
            var rule = ArtRules.RuleFor(key);
            // U-060 (ArtCompressionProbe): Unity stores a non-power-of-two texture with mipmaps UNCOMPRESSED
            // (RGBA32/RGB24, ~4× the memory) whatever the BC7/BC5 setting, because its smaller mips stop being
            // multiples of 4. Mips only for power-of-two art; NPOT sheets (1940×1616 …) import as BC7/BC5 without.
            ti.mipmapEnabled = rule.mips && Mathf.IsPowerOfTwo(w) && Mathf.IsPowerOfTwo(h);
            ti.filterMode = FilterMode.Bilinear;
            ti.wrapMode = rule.repeat ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
            ti.maxTextureSize = ArtRules.MaxDimension;
            ti.textureCompression = TextureImporterCompression.CompressedHQ;
            // U-086 (LEAD cycle 221): the Saturn ring sheet covers a 435 u annulus; trilinear + aniso keep its bands clean at any zoom.
            if (key == "planets/saturn/rings") { ti.mipmapEnabled = true; ti.filterMode = FilterMode.Trilinear; ti.anisoLevel = 8; }

            switch (map)
            {
                case ArtMap.Color:
                    if (kind == RootKind.Art && IsModelKey(key)) ConfigureModelColor(ti); // U-076: a model map is a plain sRGB texture, not a sprite
                    else ConfigureColor(ti, key, rule, w, h);
                    break;
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
            // P-36 (U-077): model maps stream their mips (power-of-two only: NPOT + mips is stored uncompressed, D-061).
            if (kind == RootKind.Art && IsModelKey(key))
            {
                ti.mipmapEnabled = Mathf.IsPowerOfTwo(w) && Mathf.IsPowerOfTwo(h);
                ti.streamingMipmaps = ti.mipmapEnabled && StreamsMips(key);
            }
        }

        void ConfigureColor(TextureImporter ti, string key, CategoryRule rule, int w, int h)
        {
            ti.textureType = TextureImporterType.Sprite;
            ti.sRGBTexture = true;
            ti.alphaIsTransparency = true;
            ti.spritePixelsPerUnit = ArtRules.PixelsPerUnit;
            SetStandaloneFormat(ti, TextureImporterFormat.BC7);

            var sheet = SheetFor(assetPath, key);
            if (sheet != null && sheet.ppu > 0f) ti.spritePixelsPerUnit = sheet.ppu; // world size stays true (U-036)
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

        /// <summary>
        /// U-094 (contract v3.0 §11.8, ArtImporter v13): a v3 asset (sidecar "style": "v3", a background layer or a palette
        /// strip) imports as a Sprite at the json PPU (64 by default), no mips, BC7, bilinear; tileable images repeat.
        /// Rejected with one console line: a sheet over 2048, fps other than 12, a clip over its cap, an overlay not 512².
        /// Returns false for v2 assets (the caller carries on with the old rules).
        /// </summary>
        bool ConfigureV3(TextureImporter ti, string key, int w, int h)
        {
            var sheet = SheetFor(assetPath, key);
            if (!IsV3(key, sheet)) return false;
            string reason = V3Reason(key, sheet, w, h);
            if (reason != null)
            {
                Debug.LogError($"[ArtImporter] Rejected {assetPath}: {reason} (contract §11.8).");
                return true; // handled: the texture keeps Unity's defaults and is never registered
            }

            ti.textureType = TextureImporterType.Sprite;
            ti.sRGBTexture = true;
            ti.alphaIsTransparency = true;
            ti.mipmapEnabled = false;
            ti.streamingMipmaps = false;
            ti.filterMode = FilterMode.Bilinear;
            bool tiles = ArtRules.IsOverlayKey(key) || ArtRules.SceneKeyOf(key) != null || (sheet != null && sheet.tile);
            ti.wrapMode = tiles ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
            ti.maxTextureSize = ArtRules.MaxDimension;
            ti.textureCompression = TextureImporterCompression.CompressedHQ;
            ti.spritePixelsPerUnit = sheet != null && sheet.ppu > 0f ? sheet.ppu : ArtRules.V3PixelsPerUnit;
            SetStandaloneFormat(ti, TextureImporterFormat.BC7);

            bool frames = sheet != null && sheet.IsSheet;
            var pivot = frames && sheet.pivot != null && sheet.pivot.Length == 2 ? new Vector2(sheet.pivot[0], sheet.pivot[1])
                : ArtRules.SceneKeyOf(key) != null ? new Vector2(0.5f, 0f) : new Vector2(0.5f, 0.5f); // layers stand on their y_m line
            var s = new TextureImporterSettings();
            ti.ReadTextureSettings(s);
            s.spriteMeshType = tiles ? SpriteMeshType.FullRect : SpriteMeshType.Tight;
            s.spriteAlignment = (int)SpriteAlignment.Custom;
            s.spritePivot = pivot;
            s.spriteMode = frames ? (int)SpriteImportMode.Multiple : (int)SpriteImportMode.Single;
            ti.SetTextureSettings(s);
            ti.spriteImportMode = frames ? SpriteImportMode.Multiple : SpriteImportMode.Single;
            return true;
        }

        /// <summary>U-094: "backgrounds/earth/plains/plains.json" → "backgrounds/earth/plains"; null for any other path.</summary>
        public static string V3SceneKey(string relativePath)
        {
            if (relativePath == null || !relativePath.StartsWith("backgrounds/", StringComparison.Ordinal) || !relativePath.EndsWith(".json", StringComparison.Ordinal)) return null;
            var parts = relativePath.Substring(0, relativePath.Length - ".json".Length).Split('/');
            if (parts.Length != 4 || parts[3] != parts[2]) return null;
            return parts[0] + "/" + parts[1] + "/" + parts[2];
        }

        /// <summary>U-094: a v3 asset: its sidecar says "style": "v3", or its key is a v3 background layer / palette strip.</summary>
        public static bool IsV3(string key, SheetManifest sheet) => ArtRules.IsV3FourSegmentKey(key) || (sheet != null && sheet.IsV3);

        /// <summary>U-094: contract §11.8 rejection reason for a v3 asset, or null.</summary>
        public static string V3Reason(string key, SheetManifest sheet, int w, int h)
        {
            if (ArtRules.IsOverlayKey(key)) return ArtRules.ValidateOverlay(w, h);
            if (ArtRules.SceneKeyOf(key) != null) return ArtRules.ValidateBackgroundLayer(w, h);
            if (sheet == null || !sheet.IsSheet) return w > ArtRules.MaxDimension || h > ArtRules.MaxDimension ? $"{w}×{h} is over 2048×2048" : null;
            int n = sheet.animations != null ? sheet.animations.Length : 0;
            var names = new string[n]; var starts = new int[n]; var lengths = new int[n];
            for (int i = 0; i < n; i++) { names[i] = sheet.animations[i].name; starts[i] = sheet.animations[i].start; lengths[i] = sheet.animations[i].length; }
            return ArtRules.ValidateV3Sheet(w, h, sheet.fps, sheet.frames, names, starts, lengths);
        }

        /// <summary>U-076: a model key's color map (beside a .glb, or a model folder's shared atlas): Default/sRGB, mips, trilinear, BC7; no sprite settings.</summary>
        static void ConfigureModelColor(TextureImporter ti)
        {
            ti.textureType = TextureImporterType.Default;
            ti.sRGBTexture = true;
            ti.alphaIsTransparency = false;
            ti.mipmapEnabled = true;
            ti.filterMode = FilterMode.Trilinear;
            ti.anisoLevel = 2;
            SetStandaloneFormat(ti, TextureImporterFormat.BC7);
        }

        /// <summary>U-073 / B-080: a block material map: Default/NormalMap texture, mips, repeat, trilinear, BC7/BC5 at 512.</summary>
        static void ConfigureBlockTexture(TextureImporter ti, ArtMap map)
        {
            ti.textureType = map == ArtMap.Normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
            ti.sRGBTexture = map == ArtMap.Color;
            ti.alphaIsTransparency = false;
            ti.mipmapEnabled = true;                 // 512² is power-of-two: mips and BC compression both hold (D-061)
            ti.wrapMode = TextureWrapMode.Repeat;
            ti.filterMode = FilterMode.Trilinear;
            ti.anisoLevel = 4;
            ti.maxTextureSize = 512;
            ti.isReadable = false;
            ti.textureCompression = TextureImporterCompression.CompressedHQ;
            var p = ti.GetPlatformTextureSettings("Standalone");
            p.overridden = true;
            p.format = map == ArtMap.Normal ? TextureImporterFormat.BC5 : TextureImporterFormat.BC7;
            p.compressionQuality = 100;
            p.maxTextureSize = 512;
            ti.SetPlatformTextureSettings(p);
        }

        /// <summary>U-073 / B-080: records block material textures in the registry (planet/material/face → maps).</summary>
        static void RegisterBlockTextures(System.Collections.Generic.List<string> paths)
        {
            var reg = Registry();
            bool dirty = false;
            foreach (var path in paths)
            {
                Classify(path, out var rel);
                if (!ArtRules.IsBlockTexture(rel, out var planet, out var material, out var face, out var map)) continue;
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                if (tex == null) continue;
                var e = reg.FindBlock(planet, material, face);
                if (e == null) { e = new Meridian.Rendering.ArtMaterials.BlockTexture { planet = planet, material = material, face = face }; reg.blockTextures.Add(e); }
                switch (map)
                {
                    case ArtMap.Normal: e.normal = tex; break;
                    case ArtMap.Mask: e.mask = tex; break;
                    default: e.color = tex; break;
                }
                dirty = true;
            }
            if (dirty) { EditorUtility.SetDirty(reg); AssetDatabase.SaveAssetIfDirty(reg); }
        }

        /// <summary>U-091: stored bytes of every stage-layer PNG of `planet` already in Art/ (IHDR dimensions), `except` one path.</summary>
        public static long StageLayerBytes(string planet, string except)
        {
            long sum = 0;
            foreach (var root in new[] { Active.art + "backgrounds", Active.art + "props" })
            {
                if (!Directory.Exists(root)) continue;
                foreach (var file in Directory.GetFiles(root, "*.png", SearchOption.AllDirectories))
                {
                    var path = ArtRules.Normalize(file);
                    if (path == ArtRules.Normalize(except)) continue;
                    if (Classify(path, out var rel) != RootKind.Art || !ArtRules.TryParse(rel, out var k, out _)) continue;
                    if (!ArtRules.IsStageLayer(k, out var p) || p != planet) continue;
                    if (PngSize(path, out int pw, out int ph)) sum += ArtRules.StoredBytes(pw, ph);
                }
            }
            return sum;
        }

        /// <summary>Width and height from a PNG's IHDR chunk (no decode).</summary>
        static bool PngSize(string path, out int width, out int height)
        {
            width = height = 0;
            try
            {
                using (var f = File.OpenRead(path))
                {
                    var b = new byte[24];
                    if (f.Read(b, 0, 24) < 24) return false;
                    width = (b[16] << 24) | (b[17] << 16) | (b[18] << 8) | b[19];
                    height = (b[20] << 24) | (b[21] << 16) | (b[22] << 8) | b[23];
                    return width > 0 && height > 0;
                }
            }
            catch (IOException) { return false; }
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

        /// <summary>
        /// The frame layout for a color file: its .json, or for terrain the fixed 47-tile grid
        /// (128 px tiles, 8 columns, no gutters; contract §4).
        /// </summary>
        public static SheetManifest SheetFor(string colorPath, string key)
        {
            var json = LoadSheet(ArtRules.SheetJsonPath(colorPath));
            if (json != null || ArtKeys.Category(key) != "terrain") return json;
            return new SheetManifest
            {
                key = key, frame_width = 128, frame_height = 128, columns = 8,
                frames = 47 + TerrainVariantCells(colorPath),
                gutter = 0, inset = 1, pivot = new[] { 0.5f, 0.5f },
            };
        }

        /// <summary>
        /// D-020: cells 47–62 may hold variants of tile 46. Counts the consecutive cells from 47 that
        /// contain art (alpha at a few points inside the cell), reading the source PNG.
        /// </summary>
        public static int TerrainVariantCells(string colorPath)
        {
            if (!File.Exists(colorPath)) return 0;
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            try
            {
                if (!tex.LoadImage(File.ReadAllBytes(colorPath)) || tex.width < 1024 || tex.height < 1024) return 0;
                int n = 0;
                for (int cell = 47; cell < 63; cell++, n++)
                {
                    int col = cell % 8, row = cell / 8;
                    int x0 = col * 128, yTop = tex.height - row * 128;
                    bool filled = false;
                    foreach (var (fx, fy) in new[] { (0.5f, 0.5f), (0.25f, 0.25f), (0.75f, 0.25f), (0.25f, 0.75f), (0.75f, 0.75f) })
                        filled |= tex.GetPixel(x0 + (int)(fx * 128), yTop - (int)(fy * 128) - 1).a > 0.5f;
                    if (!filled) break;
                }
                return n;
            }
            finally { UnityEngine.Object.DestroyImmediate(tex); }
        }

        public static SheetManifest LoadSheet(string jsonPath)
        {
            if (!File.Exists(jsonPath)) return null;
            try
            {
                var m = JsonUtility.FromJson<SheetManifest>(File.ReadAllText(jsonPath));
                if (m != null && m.IsV3 && !m.IsSheet) return m; // U-094: a v3 single image (overlay, layer, strip)
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
                rects.Add(new Rect(x + m.inset, textureHeight - yTop - m.frame_height + m.inset,
                    m.frame_width - 2 * m.inset, m.frame_height - 2 * m.inset));
            }
            return rects;
        }

        /// <summary>Applies the sheet's frame rects; returns true when they changed (caller reimports).</summary>
        static bool SliceIfNeeded(string colorPath, string key)
        {
            var m = SheetFor(colorPath, key);
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
            var blockPaths = new List<string>();
            var retireKeys = new HashSet<string>();
            var restoreKeys = new HashSet<string>();

            foreach (var raw in imported.Concat(moved))
            {
                var kind = Classify(raw, out var rel);
                if (kind == RootKind.None) continue;
                var path = ArtRules.Normalize(raw);
                // U-090 (contract §10): a region's stage.json is addressed as a TextAsset under backgrounds/<planet>_<region>/stage.
                if (rel.EndsWith("/stage.json", StringComparison.Ordinal) && kind == RootKind.Art)
                {
                    var stageKey = rel.Substring(0, rel.Length - ".json".Length);
                    AddressStage(path, stageKey);
                    continue;
                }
                // U-094 (contract §11.4): a painted scene's backgrounds/<planet>/<scene>/<scene>.json is a TextAsset at that scene key.
                var sceneJson = V3SceneKey(rel);
                if (sceneJson != null) { AddressStage(path, sceneJson); continue; }
                if (rel.EndsWith(".json", StringComparison.Ordinal))
                {
                    // A new or edited sheet manifest re-slices its color sheet.
                    var color = path.Substring(0, path.Length - ".json".Length) + "_color.png";
                    if (File.Exists(color)) AssetDatabase.ImportAsset(color, ImportAssetOptions.ForceUpdate);
                    continue;
                }
                // U-073 / B-080: block materials go to the registry, never to the sprite pipeline.
                if (kind == RootKind.Art && ArtRules.IsBlockTexture(rel, out _, out _, out _, out _)) { blockPaths.Add(path); continue; }
                if (!ArtRules.TryParse(rel, out var key, out var map)) continue;
                var colorPath = (kind == RootKind.Art ? Active.art : Active.placeholders) + key + "_color.png";
                if (File.Exists(colorPath)) colors.Add(colorPath);
            }
            if (blockPaths.Count > 0) RegisterBlockTextures(blockPaths);

            var materialKeys = new HashSet<string>();
            foreach (var raw in deleted.Concat(movedFrom))
            {
                var kind = Classify(raw, out var rel);
                if (kind == RootKind.None || !ArtRules.TryParse(rel, out var key, out var map)) continue;
                if (kind == RootKind.Art && map == ArtMap.Color) restoreKeys.Add(key);
                materialKeys.Add(key);
            }

            foreach (var colorPath in colors)
            {
                Classify(colorPath, out var rel);
                ArtRules.TryParse(rel, out var key, out _);
                if (!PassesValidation(colorPath)) continue;
                // U-075 (contract v2 §9): a colour map beside a .glb is a model texture, not a sprite sheet. Until the
                // model views read models (ArtImporter v5), the key stays on its 2D placeholder: un-address the map
                // and keep the placeholder addressed, so 2D views never draw a whole 2048² texture as one sprite.
                if (colorPath.StartsWith(Active.art, StringComparison.Ordinal) && IsModelKey(key))
                {
                    UnregisterArt(colorPath, key);
                    var ph = PlaceholderColorPath(key);
                    if (File.Exists(ph)) { Register(ph, key); UpdateClipRegistry(ph, key); }
                    else
                    {
                        // Contract §1: a key without loadable 2D art gets a placeholder, so 2D loaders never hit an
                        // unknown address (the props/creatures that turned into models had none). Its own import registers it.
                        if (File.Exists(Active.art + key + ".glb")) PlaceholderGenerator.Write(key, false); // not for a shared atlas: no 2D loader asks for it
                        if (File.Exists(ph)) AssetDatabase.ImportAsset(ph, ImportAssetOptions.ForceUpdate);
                    }
                    continue;
                }
                SliceIfNeeded(colorPath, key);
                SheetAnimatorBuilder.BuildIfV3(colorPath, key); // U-094: Animator clips at 12 fps + one controller per sheet
                LinkSecondaries(colorPath, key);
                materialKeys.Add(key);
                bool isArt = colorPath.StartsWith(Active.art, StringComparison.Ordinal);
                if (isArt)
                {
                    Register(colorPath, key);
                    UpdateClipRegistry(colorPath, key);
                    retireKeys.Add(key);
                }
                else if (!File.Exists(ArtColorPath(key)) || IsModelKey(key)) // v5: a model key keeps its placeholder
                {
                    Register(colorPath, key);
                    UpdateClipRegistry(colorPath, key);
                }
            }

            foreach (var key in retireKeys) RetirePlaceholder(key);
            foreach (var key in restoreKeys)
            {
                var ph = PlaceholderColorPath(key);
                if (File.Exists(ph) && !File.Exists(ArtColorPath(key))) Register(ph, key);
            }
            if (materialKeys.Count > 0) UpdateMaterialRegistry(materialKeys);

            // U-075: models (glb + json + maps): generated material, addresses, clip registry.
            // U-077: maps that arrived before their model (B-101's Venus atlas) were imported as sheets; fix them first.
            foreach (var raw in imported.Concat(moved))
                if (Classify(raw, out var rel) == RootKind.Art && rel.EndsWith(".glb", StringComparison.Ordinal))
                    EnsureModelMapsImported(rel.Substring(0, rel.Length - 4));
            var modelKeys = new HashSet<string>();
            CollectModelKeys(imported.Concat(moved), modelKeys);
            GenerateModels(modelKeys);
        }

        // ---------- material registry (U-019) ----------

        public const string LitEmissiveMaterialPath = "Assets/_Game/Settings/Materials/Sprite_LitEmissive.mat";
        const string LitDefaultMaterialPath = "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Lit-Default.mat";

        /// <summary>The ArtMaterials registry for the active roots, created on first use.</summary>
        public static Meridian.Rendering.ArtMaterials Registry()
        {
            var path = Active.materialRegistry;
            var reg = AssetDatabase.LoadAssetAtPath<Meridian.Rendering.ArtMaterials>(path);
            if (reg != null) return reg;
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            reg = ScriptableObject.CreateInstance<Meridian.Rendering.ArtMaterials>();
            reg.lit = AssetDatabase.LoadAssetAtPath<Material>(LitDefaultMaterialPath);
            reg.litEmissive = AssetDatabase.LoadAssetAtPath<Material>(LitEmissiveMaterialPath);
            if (reg.litEmissive == null)
            {
                var shader = Shader.Find("MERIDIAN/Sprite_LitEmissive");
                if (shader != null)
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(LitEmissiveMaterialPath));
                    reg.litEmissive = new Material(shader) { name = "Sprite_LitEmissive" };
                    AssetDatabase.CreateAsset(reg.litEmissive, LitEmissiveMaterialPath);
                }
            }
            AssetDatabase.CreateAsset(reg, path);
            return reg;
        }

        /// <summary>Copies a frame sheet's clips into the registry so the game can play them by name (U-032).</summary>
        static void UpdateClipRegistry(string colorPath, string key)
        {
            var json = ArtRules.SheetJsonPath(colorPath);
            var sheet = File.Exists(json) ? LoadSheet(json) : null;
            var clips = new List<Meridian.Rendering.ArtClip>();
            if (sheet?.animations != null)
                foreach (var c in sheet.animations)
                    clips.Add(new Meridian.Rendering.ArtClip { name = c.name, start = c.start, length = c.length, loop = c.loop });
            if (clips.Count == 0 && !File.Exists(Active.materialRegistry)) return;
            var reg = Registry();
            if (!reg.SetClips(key, sheet != null ? sheet.fps : 12, clips)) return;
            EditorUtility.SetDirty(reg);
            AssetDatabase.SaveAssetIfDirty(reg);
        }

        static bool IsEmissiveNow(string key)
        {
            var color = File.Exists(ArtColorPath(key)) ? ArtColorPath(key) : PlaceholderColorPath(key);
            return File.Exists(color) && File.Exists(ArtRules.SiblingPath(color, ArtMap.Emission));
        }

        /// <summary>A key draws with Sprite_LitEmissive when its addressed color file has an _emission sibling.</summary>
        static void UpdateMaterialRegistry(IEnumerable<string> keys)
        {
            // Don't create a registry just to record "not emissive".
            if (!File.Exists(Active.materialRegistry) && !keys.Any(IsEmissiveNow)) return;
            var reg = Registry();
            bool changed = false;
            foreach (var key in keys) changed |= reg.SetEmissive(key, IsEmissiveNow(key));
            if (!changed) return;
            EditorUtility.SetDirty(reg);
            AssetDatabase.SaveAssetIfDirty(reg);
        }

        static bool PassesValidation(string colorPath)
        {
            var ti = AssetImporter.GetAtPath(colorPath) as TextureImporter;
            if (ti == null) return false;
            ti.GetSourceTextureWidthAndHeight(out int w, out int h);
            if (ArtRules.Validate(ArtRules.FileBytes(colorPath), w, h) != null) return false;
            // U-094: a rejected v3 asset is never addressed.
            Classify(colorPath, out var rel);
            if (!ArtRules.TryParse(rel, out var key, out _)) return true;
            var sheet = SheetFor(colorPath, key);
            return !IsV3(key, sheet) || V3Reason(key, sheet, w, h) == null;
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
            StageLabel(entry, key);
            var atlas = ArtRules.AtlasFor(key);
            if (atlas != null) AddToAtlas(atlas, colorPath);
        }

        /// <summary>U-090 (Bible §10.10): every asset of a region's set carries the label stage_<planet>_<region> (backgrounds/<planet>_<region>/…).</summary>
        static void StageLabel(UnityEditor.AddressableAssets.Settings.AddressableAssetEntry entry, string key)
        {
            if (entry == null || !ArtRules.IsStageLayer(key, out _) || ArtKeys.Category(key) != "backgrounds") return;
            var second = key.Split('/')[1];
            if (second.IndexOf('_') < 0) return; // the planet-wide layers (rocks, clouds) stay in the planet group without a region label
            var label = "stage_" + second;
            Settings.AddLabel(label, false);
            entry.SetLabel(label, true, true, false);
        }

        /// <summary>U-090: a stage.json addressed as a TextAsset under its key, labelled with its region's set.</summary>
        static void AddressStage(string path, string key)
        {
            var guid = AssetDatabase.AssetPathToGUID(path);
            if (string.IsNullOrEmpty(guid)) return;
            var entry = Settings.CreateOrMoveEntry(guid, GroupNamed(ArtRules.GroupFor(key)), false, true);
            if (entry.address != key) entry.SetAddress(key, true);
            StageLabel(entry, key);
        }

        /// <summary>U-075: removes an art colour map's address and atlas entry (model textures aren't sprites).</summary>
        static void UnregisterArt(string colorPath, string key)
        {
            var guid = AssetDatabase.AssetPathToGUID(colorPath);
            if (string.IsNullOrEmpty(guid)) return;
            if (Settings.FindAssetEntry(guid) != null) Settings.RemoveAssetEntry(guid, true);
            var atlas = ArtRules.AtlasFor(key);
            if (atlas != null) RemoveFromAtlas(atlas, colorPath);
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

        /// <summary>U-094: how many sprite atlases a planet has on disk (planet_&lt;name&gt;*.spriteatlasv2 under the atlas folder).</summary>
        public static int AtlasCountFor(string planet)
        {
            if (!Directory.Exists(Active.atlasFolder)) return 0;
            int n = 0;
            foreach (var f in Directory.GetFiles(Active.atlasFolder, "*.spriteatlasv2"))
            {
                var name = Path.GetFileNameWithoutExtension(f);
                if (!string.IsNullOrEmpty(Active.groupPrefix) && name.StartsWith(Active.groupPrefix, StringComparison.Ordinal)) name = name.Substring(Active.groupPrefix.Length);
                if (ArtRules.AtlasPlanet(name) == planet) n++;
            }
            return n;
        }

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
                // U-094 (contract §11.8): a planet gets at most 8 atlases; a ninth is refused and its texture stays unpacked.
                var planet = ArtRules.AtlasPlanet(atlas);
                if (planet != null && ArtRules.AtlasCapReached(AtlasCountFor(planet)))
                {
                    Debug.LogError($"[ArtImporter] Rejected atlas {atlas} for {texturePath}: {planet} already has {ArtRules.MaxAtlasesPerPlanet} sprite atlases (contract §11.8).");
                    return;
                }
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
