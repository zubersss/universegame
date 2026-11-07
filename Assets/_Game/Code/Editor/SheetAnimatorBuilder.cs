using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-094 (contract v3.0 §11.2/§11.8): turns a v3 sprite sheet into Animator clips sampled at 12 fps (one sprite key
    /// per drawing, on twos) and one AnimatorController with a state per clip (default: idle), written to
    /// Generated/Sheets/&lt;key&gt;/ and addressed as "&lt;key&gt;/animator" in the key's group. SpriteCharacterView loads it.
    /// The clips bind SpriteRenderer.m_Sprite on the Animator's own GameObject.
    /// </summary>
    public static class SheetAnimatorBuilder
    {
        public const string Root = "Assets/_Game/Generated/Sheets/";

        public static string Folder(string key) => Root + key + "/";
        public static string ControllerPath(string key) => Folder(key) + "animator.controller";
        public static string ClipPath(string key, string clip) => Folder(key) + clip + ".anim";

        /// <summary>Builds the clips and controller when `colorPath` is a valid v3 sheet; returns the controller, else null.</summary>
        public static AnimatorController BuildIfV3(string colorPath, string key)
        {
            var sheet = ArtImporter.SheetFor(colorPath, key);
            if (sheet == null || !sheet.IsV3 || !sheet.IsSheet || sheet.animations == null || sheet.animations.Length == 0) return null;
            // A placeholder never overrides the art's controller: the clips bind sprite objects, so a later placeholder
            // re-import would put placeholder drawings back in front of the real sheet (C0 capture, 2026-11-06).
            bool placeholder = colorPath.StartsWith(ArtImporter.Active.placeholders, System.StringComparison.Ordinal);
            if (placeholder && File.Exists(ArtImporter.ArtColorPath(key))) return null;
            string variant = key.Substring(key.LastIndexOf('/') + 1);
            var sprites = AssetDatabase.LoadAllAssetsAtPath(colorPath).OfType<Sprite>()
                .GroupBy(s => s.name).ToDictionary(g => g.Key, g => g.First());
            if (sprites.Count == 0) return null; // sliced on the next import pass

            Directory.CreateDirectory(Folder(key));
            var path = ControllerPath(key);
            // U-108: never delete-and-recreate the controller: Addressables' post-processor handles the deleted path by its CURRENT
            // guid, i.e. the re-created asset, and drops the <key>/animator entry CreateOrMoveEntry just re-added (the gull, surveyor
            // and calibration entries vanished that way). Load it and empty its base layer instead (RigSetBuilder.ClearStates).
            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(path);
            if (controller != null) RigSetBuilder.ClearStates(controller);
            else controller = AnimatorController.CreateAnimatorControllerAtPath(path);
            foreach (var stale in Directory.GetFiles(Folder(key), "*.anim")) AssetDatabase.DeleteAsset(stale.Replace('\\', '/')); // clips of a previous sheet (no address: safe)
            var machine = controller.layers[0].stateMachine;

            var have = new System.Collections.Generic.HashSet<string>();
            foreach (var c in sheet.animations)
                if (have.Add(c.name)) AddClipState(machine, key, variant, c, sprites);
            // U-115 (D-121): a `side` sheet's controller also takes the clips of its sibling `side_b` (B-134: dig, build, surprise,
            // jetpack, climb_in; a stand-in placeholder until it lands). Those clips bind side_b's drawings, so the one SpriteRenderer
            // swaps texture with the clip and SurveyorAnim.ResolveOn finds the five as real states. A name `side` already has wins.
            if (variant == "side")
            {
                string bKey = key + "_b";
                string bColor = File.Exists(ArtImporter.ArtColorPath(bKey)) ? ArtImporter.ArtColorPath(bKey) : ArtImporter.PlaceholderColorPath(bKey);
                var bSheet = File.Exists(bColor) ? ArtImporter.SheetFor(bColor, bKey) : null;
                if (bSheet != null && bSheet.IsV3 && bSheet.IsSheet && bSheet.animations != null)
                {
                    var bSprites = AssetDatabase.LoadAllAssetsAtPath(bColor).OfType<Sprite>().GroupBy(sp => sp.name).ToDictionary(g => g.Key, g => g.First());
                    if (bSprites.Count > 0)
                        foreach (var c in bSheet.animations)
                            if (have.Add(c.name)) AddClipState(machine, key, variant + "_b", c, bSprites);
                }
            }
            EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssets();

            var guid = AssetDatabase.AssetPathToGUID(path);
            if (!string.IsNullOrEmpty(guid))
            {
                var entry = ArtImporter.Settings.CreateOrMoveEntry(guid, ArtImporter.GroupNamed(ArtRules.GroupFor(key)), false, true);
                string address = Meridian.View2D.SheetClock.ControllerAddress(key);
                if (entry.address != address) entry.SetAddress(address, true);
            }
            AssetDatabase.SaveAssets(); // the address must reach disk before the Editor quits (an -ExecuteMethod run)
            // U-115: when the second sheet (re)imports, the `side` controller that carries its clips is rebuilt with the new drawings.
            if (variant == "side_b")
            {
                string sideKey = key.Substring(0, key.Length - 2);
                string sideColor = File.Exists(ArtImporter.ArtColorPath(sideKey)) ? ArtImporter.ArtColorPath(sideKey) : ArtImporter.PlaceholderColorPath(sideKey);
                if (File.Exists(sideColor)) BuildIfV3(sideColor, sideKey);
            }
            return controller;
        }

        /// <summary>One clip state: one key per drawing (`&lt;variant&gt;_&lt;frame&gt;` of `sprites`), the U-105 events, loop per the json; idle is the default state.</summary>
        static void AddClipState(AnimatorStateMachine machine, string key, string variant, ArtImporter.SheetClip c, System.Collections.Generic.Dictionary<string, Sprite> sprites)
        {
            var binding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
            float step = 1f / Meridian.EditorTools.ArtRules.V3Fps;
            // One key per drawing; Unity holds a sprite curve's last key for one more frame (1/12 s), so a clip of n lasts n/12 s.
            var keys = new ObjectReferenceKeyframe[c.length];
            for (int i = 0; i < c.length; i++)
            {
                int frame = c.start + i;
                sprites.TryGetValue($"{variant}_{frame}", out var sprite);
                keys[i] = new ObjectReferenceKeyframe { time = i * step, value = sprite };
            }
            var clip = new AnimationClip { name = c.name, frameRate = Meridian.EditorTools.ArtRules.V3Fps };
            AnimationUtility.SetObjectReferenceCurve(clip, binding, keys);
            var events = EventsFor(c.name, c.length); // U-105: eye-pop and smear hooks as animation events
            if (events.Length > 0)
                AnimationUtility.SetAnimationEvents(clip, events.Select(e => new AnimationEvent { functionName = e.function, time = e.frame * step }).ToArray());
            var settings = AnimationUtility.GetAnimationClipSettings(clip);
            settings.loopTime = c.loop;
            AnimationUtility.SetAnimationClipSettings(clip, settings);
            var clipPath = ClipPath(key, c.name);
            if (File.Exists(clipPath)) AssetDatabase.DeleteAsset(clipPath);
            AssetDatabase.CreateAsset(clip, clipPath);
            var state = machine.AddState(c.name);
            state.motion = clip;
            if (c.name == "idle") machine.defaultState = state;
        }

        /// <summary>
        /// U-105: the animation events a clip carries, by frame: `surprise` pops the eyes on its first drawing (OnEyePop);
        /// `dash` smears from its first drawing to its last (OnSmear, OnSmearEnd). Pure: SurveyorAnimTests checks the frames.
        /// </summary>
        public static (string function, int frame)[] EventsFor(string clip, int length)
        {
            if (length <= 0) return System.Array.Empty<(string, int)>();
            switch (clip)
            {
                case "surprise": return new[] { ("OnEyePop", 0) };
                case "dash": return new[] { ("OnSmear", 0), ("OnSmearEnd", length - 1) };
                default: return System.Array.Empty<(string, int)>();
            }
        }

        /// <summary>
        /// Rebuilds every v3 sheet's clips and controller from the live sheet (art, else placeholder): MERIDIAN menu, or
        /// `tools/unity_check.ps1 -ExecuteMethod Meridian.EditorTools.SheetAnimatorBuilder.RebuildAll`. Returns the count.
        /// </summary>
        [MenuItem("MERIDIAN/Rebuild Sheet Animators")]
        public static int RebuildAll()
        {
            int built = 0;
            foreach (var root in new[] { ArtImporter.Active.art, ArtImporter.Active.placeholders })
            {
                var dir = root.TrimEnd('/');
                if (!Directory.Exists(dir)) continue;
                foreach (var png in Directory.GetFiles(dir, "*_color.png", SearchOption.AllDirectories))
                {
                    var colorPath = png.Replace('\\', '/');
                    var rel = colorPath.Substring(root.Length);
                    if (!ArtRules.TryParse(rel, out var key, out var map) || map != Meridian.Art.ArtMap.Color) continue;
                    if (BuildIfV3(colorPath, key) != null) built++;
                }
            }
            Debug.Log($"[MERIDIAN] SheetAnimatorBuilder: rebuilt {built} controller(s)");
            return built;
        }
    }
}
