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
            if (AssetDatabase.LoadAssetAtPath<AnimatorController>(path) != null) AssetDatabase.DeleteAsset(path);
            foreach (var stale in Directory.GetFiles(Folder(key), "*.anim")) AssetDatabase.DeleteAsset(stale.Replace('\\', '/')); // clips of a previous sheet
            var controller = AnimatorController.CreateAnimatorControllerAtPath(path);
            var machine = controller.layers[0].stateMachine;

            var binding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
            float step = 1f / Meridian.EditorTools.ArtRules.V3Fps;
            foreach (var c in sheet.animations)
            {
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
            EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssets();

            var guid = AssetDatabase.AssetPathToGUID(path);
            if (!string.IsNullOrEmpty(guid))
            {
                var entry = ArtImporter.Settings.CreateOrMoveEntry(guid, ArtImporter.GroupNamed(ArtRules.GroupFor(key)), false, true);
                string address = Meridian.View2D.SheetClock.ControllerAddress(key);
                if (entry.address != address) entry.SetAddress(address, true);
            }
            return controller;
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
