using System.IO;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.TextCore.LowLevel;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-104 (Bible §9 v4, D-090): the game's two faces, Limelight for titles and Patrick Hand for the HUD and body text,
    /// both SIL OFL from Google Fonts with OFL.txt beside each file and a row in docs/credits/unity.md. Builds a dynamic
    /// TextMeshPro font asset next to each .ttf once (glyphs rasterise on demand, so a batch run needs no graphics) and
    /// hands the four assets to the UiTheme. Runs from SceneAuthoring.Run and CheckSetup.Run.
    /// </summary>
    public static class FontAuthoring
    {
        public const string TitleTtf = "Assets/_Game/Fonts/Limelight/Limelight-Regular.ttf";
        public const string HudTtf = "Assets/_Game/Fonts/PatrickHand/PatrickHand-Regular.ttf";
        public const string TitleSdf = "Assets/_Game/Fonts/Limelight/Limelight-Regular SDF.asset";
        public const string HudSdf = "Assets/_Game/Fonts/PatrickHand/PatrickHand-Regular SDF.asset";

        [MenuItem("MERIDIAN/Authoring/HUD fonts (TMP assets + theme)")]
        public static void Run()
        {
            var theme = AssetDatabase.LoadAssetAtPath<Meridian.UI.UiTheme>(SceneAuthoring.UiThemePath);
            if (theme == null) { Debug.LogError($"[MERIDIAN] FontAuthoring: no UiTheme at {SceneAuthoring.UiThemePath} (run Author Scenes first)."); return; }
            EnsureHudFonts(theme);
            EditorUtility.SetDirty(theme);
            AssetDatabase.SaveAssets();
        }

        /// <summary>Creates the two TMP font assets if missing and sets the theme's title/hud fonts (the caller saves the theme).</summary>
        public static void EnsureHudFonts(Meridian.UI.UiTheme theme)
        {
            // TMP builds a font asset only with its essential resources in the project (TMP Settings, shaders, the default
            // face); a fresh project has none, and CreateFontAsset dies on the missing settings. Import them once.
            if (TMP_Settings.instance == null)
            {
                TMP_PackageResourceImporter.ImportResources(true, false, false);
                AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
                if (TMP_Settings.instance == null) Debug.LogWarning("[MERIDIAN] FontAuthoring: TMP essential resources not in place yet (Assets/TextMesh Pro/Resources/TMP Settings); the HUD font assets wait for the next run.");
            }
            theme.titleTtf = AssetDatabase.LoadAssetAtPath<Font>(TitleTtf);
            theme.hudTtf = AssetDatabase.LoadAssetAtPath<Font>(HudTtf);
            theme.titleFont = Ensure(theme.titleTtf, TitleSdf);
            theme.hudFont = Ensure(theme.hudTtf, HudSdf);
            if (theme.titleTtf == null || theme.hudTtf == null)
                Debug.LogWarning("[MERIDIAN] FontAuthoring: a D-090 font is missing under Assets/_Game/Fonts (Limelight, Patrick Hand).");
        }

        static TMP_FontAsset Ensure(Font font, string path)
        {
            var existing = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(path);
            if (existing != null || font == null) return existing;
            TMP_FontAsset asset;
            try { asset = TMP_FontAsset.CreateFontAsset(font, 90, 9, GlyphRenderMode.SDFAA, 1024, 1024, AtlasPopulationMode.Dynamic, true); }
            catch (System.Exception e)
            {
                // A batch run without a font engine (or a face the engine rejects) must not abort the whole setup: the theme keeps
                // its JetBrains Mono fallback and HudFontsTests says which face is missing.
                Debug.LogWarning($"[MERIDIAN] FontAuthoring: TMP could not build a font asset from {font.name}: {e.GetType().Name}: {e.Message}");
                return null;
            }
            if (asset == null) { Debug.LogWarning($"[MERIDIAN] FontAuthoring: TMP returned no font asset for {font.name}."); return null; }
            string name = Path.GetFileNameWithoutExtension(path);
            asset.name = name;
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            AssetDatabase.CreateAsset(asset, path);
            if (asset.material != null) { asset.material.name = name + " Material"; AssetDatabase.AddObjectToAsset(asset.material, asset); }
            if (asset.atlasTexture != null) { asset.atlasTexture.name = name + " Atlas"; AssetDatabase.AddObjectToAsset(asset.atlasTexture, asset); }
            EditorUtility.SetDirty(asset);
            AssetDatabase.SaveAssets();
            Debug.Log($"[MERIDIAN] FontAuthoring: {path} from {font.name} (dynamic SDF, D-090).");
            return AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(path);
        }
    }
}
