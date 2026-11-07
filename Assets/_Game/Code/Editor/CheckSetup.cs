using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// The one-time data steps a batched check needs, in one -ExecuteMethod (an -ExecuteMethod run quits before the
    /// auto-save, so each step saves): U-091 shared terrain sheets to `common` (D-110), U-103 planet sidecars addressed,
    /// every v3 sheet's clips and controller rebuilt (U-105 events, B-125/B-127 re-inks), every rig set rebuilt (U-108).
    /// `tools/unity_check.ps1 -ExecuteMethod Meridian.EditorTools.CheckSetup.Run`.
    /// </summary>
    public static class CheckSetup
    {
        [MenuItem("MERIDIAN/Check Setup (shared terrain, planet sidecars, sheet animators, rig sets)")]
        public static void Run()
        {
            ArtImporter.RegisterSharedTerrain();
            int sidecars = ArtImporter.AddressPlanetSidecars();
            int sheets = SheetAnimatorBuilder.RebuildAll();
            int rigs = RigSetBuilder.RebuildAll();
            int discs = ArtImporter.ReimportSpaceDiscs(); // U-117: the discs' full-rect mesh reaches the metas
            DiscSetup.Run(); // U-117: the disc material (MERIDIAN/Sprite_LitDisc) in the registry
            int sceneLayers = ArtImporter.ReimportSceneLayers(); // U-109: the side-scene layers clamp in y (the climb frames' thin line)
            if (sceneLayers > 0) Debug.Log($"[CheckSetup] re-imported {sceneLayers} scene layer(s): wrap-in-y per U-109.");
            var theme = AssetDatabase.LoadAssetAtPath<Meridian.UI.UiTheme>(SceneAuthoring.UiThemePath);
            if (theme != null) { FontAuthoring.EnsureHudFonts(theme); EditorUtility.SetDirty(theme); } // U-104 (D-090) fonts
            AssetDatabase.SaveAssets();
            Debug.Log($"[MERIDIAN] CheckSetup: {sidecars} planet sidecars, {sheets} sheet animators, {rigs} rig sets, {discs} space discs re-imported.");
        }
    }
}
