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
            GroundTiersSetup.Run(); // U-182: the tier fill material (MERIDIAN/GroundTiers) in the registry
            int sceneLayers = ArtImporter.ReimportSceneLayers(); // U-109: the side-scene layers clamp in y (the climb frames' thin line)
            if (sceneLayers > 0) Debug.Log($"[CheckSetup] re-imported {sceneLayers} scene layer(s): wrap-in-y per U-109.");
            var theme = AssetDatabase.LoadAssetAtPath<Meridian.UI.UiTheme>(SceneAuthoring.UiThemePath);
            if (theme != null) { FontAuthoring.EnsureHudFonts(theme); EditorUtility.SetDirty(theme); } // U-104 (D-090) fonts
            int bottoms = RecordOpaqueBottoms(); // U-164 (D-169)
            AssetDatabase.SaveAssets();
            Debug.Log($"[MERIDIAN] CheckSetup: {sidecars} planet sidecars, {sheets} sheet animators, {rigs} rig sets, {discs} space discs re-imported, {bottoms} set layers with an opaque bottom strip.");
        }

        /// <summary>
        /// U-164 (D-169): the painted sets whose nearest layer may go on under its bottom edge: for each backgrounds/&lt;planet&gt;/&lt;scene&gt;/&lt;scene&gt;.json,
        /// the highest layer's bottom strip (SceneLayout.ContinueRows: continue_rows or 64 px, never above its ground line) read from the source
        /// PNG; at least 99.5 % of its pixels opaque puts the layer's key in ArtMaterials.opaqueBottoms (the stage repeats only those).
        /// </summary>
        public static int RecordOpaqueBottoms()
        {
            const string Root = "Assets/_Game/Art/";
            var reg = ArtImporter.Registry();
            var found = new System.Collections.Generic.List<string>();
            if (System.IO.Directory.Exists(Root + "backgrounds"))
                foreach (var json in System.IO.Directory.GetFiles(Root + "backgrounds", "*.json", System.IO.SearchOption.AllDirectories))
                {
                    string dir = System.IO.Path.GetDirectoryName(json).Replace('\\', '/'), scene = System.IO.Path.GetFileNameWithoutExtension(json);
                    if (System.IO.Path.GetFileName(dir) != scene) continue; // a set's json sits in its own folder
                    var layout = Meridian.View2D.SceneLayout.Parse(System.IO.File.ReadAllText(json));
                    Meridian.View2D.SceneLayout.Layer near = null;
                    foreach (var l in layout.layers) if (near == null || l.n > near.n) near = l;
                    string png = $"{dir}/layer{near.n}_color.png";
                    if (!System.IO.File.Exists(png)) continue;
                    var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                    try
                    {
                        if (!tex.LoadImage(System.IO.File.ReadAllBytes(png))) continue;
                        int rows = Meridian.View2D.SceneLayout.ContinueRows(near, tex.height), w = tex.width, opaque = 0;
                        var px = tex.GetPixels32();
                        for (int y = 0; y < rows; y++) for (int x = 0; x < w; x++) if (px[y * w + x].a >= 250) opaque++;
                        if (opaque >= w * rows * 0.995f) found.Add(dir.Substring(Root.Length) + "/layer" + near.n);
                    }
                    finally { Object.DestroyImmediate(tex); }
                }
            found.Sort(System.StringComparer.Ordinal);
            bool same = found.Count == reg.opaqueBottoms.Count;
            for (int i = 0; same && i < found.Count; i++) same = found[i] == reg.opaqueBottoms[i];
            if (!same) { reg.opaqueBottoms = found; EditorUtility.SetDirty(reg); }
            Debug.Log($"[MERIDIAN] CheckSetup: opaque bottom strips: {string.Join(", ", found)}");
            return found.Count;
        }
    }
}
