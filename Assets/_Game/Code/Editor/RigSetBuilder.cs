using System.Collections.Generic;
using System.IO;
using System.Linq;
using Meridian.Flora;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.U2D.Sprites;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-097 (contract v3.0 §11.3): a rig set's sheet (`flora/&lt;planet&gt;/rigset_color.png` + `rigset.json`) is sliced into
    /// its named parts, and one AnimatorController per set is generated under Generated/Rigs/&lt;key&gt;/ with a sway clip per
    /// plant: every bone's z rotation sampled stepped at 12 Hz over a two-beat cycle of the plant's beat, plus the beat
    /// squash on the root; addressed as "&lt;key&gt;/animator" in the planet's group. Placeholders never override the art's.
    /// </summary>
    public static class RigSetBuilder
    {
        public const string Root = "Assets/_Game/Generated/Rigs/";
        public const int Fps = 12;

        public static bool IsRigSet(string key) => key != null && key.EndsWith("/rigset", System.StringComparison.Ordinal);
        public static string Folder(string key) => Root + key + "/";
        public static string ControllerPath(string key) => Folder(key) + "animator.controller";
        public static string JsonPath(string colorPath) => colorPath.Substring(0, colorPath.Length - "_color.png".Length) + ".json";

        /// <summary>The bone's path under the plant root ("root/stem2/head").</summary>
        public static string BonePath(RigSet.Plant plant, RigSet.Bone bone)
        {
            var chain = new List<string>();
            var b = bone;
            int guard = 0;
            while (b != null && guard++ < RigSet.MaxBones + 1)
            {
                chain.Insert(0, b.name);
                b = string.IsNullOrEmpty(b.parent) ? null : System.Array.Find(plant.bones, x => x.name == b.parent);
            }
            return string.Join("/", chain);
        }

        public static int Depth(RigSet.Plant plant, RigSet.Bone bone)
        {
            int d = 0; var b = bone;
            while (!string.IsNullOrEmpty(b.parent) && d < RigSet.MaxBones) { b = System.Array.Find(plant.bones, x => x.name == b.parent); if (b == null) break; d++; }
            return d;
        }

        /// <summary>Two beats of sway (period 120 / bpm s) sampled stepped at 12 Hz: the bone's z angle, deeper bones a little later (a whip).</summary>
        public static AnimationCurve SwayCurve(float amplitudeDeg, float bpm, int depth, int chainLength)
        {
            float period = 120f / Mathf.Max(1f, bpm);
            int n = Mathf.Max(1, Mathf.RoundToInt(period * Fps));
            float share = amplitudeDeg / Mathf.Max(1, chainLength);
            var keys = new Keyframe[n + 1];
            for (int i = 0; i <= n; i++)
            {
                float t = i / (float)Fps;
                float angle = share * Mathf.Sin(2f * Mathf.PI * (t / period) - depth * 0.35f);
                keys[i] = new Keyframe(t, angle);
            }
            keys[n].value = keys[0].value; // seamless loop
            var curve = new AnimationCurve(keys);
            for (int i = 0; i < curve.length; i++)
            {
                AnimationUtility.SetKeyLeftTangentMode(curve, i, AnimationUtility.TangentMode.Constant);
                AnimationUtility.SetKeyRightTangentMode(curve, i, AnimationUtility.TangentMode.Constant);
            }
            return curve;
        }

        /// <summary>One squash per beat on the root (y: 1 ± squash, x the inverse), stepped at 12 Hz over the same two beats.</summary>
        public static AnimationCurve SquashCurve(float squash, float bpm, bool y)
        {
            float period = 120f / Mathf.Max(1f, bpm);
            int n = Mathf.Max(1, Mathf.RoundToInt(period * Fps));
            var keys = new Keyframe[n + 1];
            for (int i = 0; i <= n; i++)
            {
                float t = i / (float)Fps;
                float s = squash * Mathf.Sin(2f * Mathf.PI * t / (period * 0.5f));
                keys[i] = new Keyframe(t, y ? 1f + s : 1f / (1f + s));
            }
            keys[n].value = keys[0].value;
            var curve = new AnimationCurve(keys);
            for (int i = 0; i < curve.length; i++)
            {
                AnimationUtility.SetKeyLeftTangentMode(curve, i, AnimationUtility.TangentMode.Constant);
                AnimationUtility.SetKeyRightTangentMode(curve, i, AnimationUtility.TangentMode.Constant);
            }
            return curve;
        }

        /// <summary>Slices the sheet into the set's parts (rects from the json, bottom-left origin); true when the rects changed (a re-import follows).</summary>
        static bool SliceParts(string colorPath, RigSet set)
        {
            var ti = AssetImporter.GetAtPath(colorPath) as TextureImporter;
            if (ti == null) return false;
            if (ti.spriteImportMode != SpriteImportMode.Multiple) { ti.spriteImportMode = SpriteImportMode.Multiple; ti.SaveAndReimport(); return true; }
            var factory = new SpriteDataProviderFactories();
            factory.Init();
            var dp = factory.GetSpriteEditorDataProviderFromObject(ti);
            dp.InitSpriteEditorDataProvider();
            var current = dp.GetSpriteRects();
            // The provider hands the rects back in its own order: compare by name, so an already-sliced sheet is left alone
            // (an ordered compare re-sliced and re-imported BLENDER's sheet on every pass).
            var byName = current.GroupBy(r => r.name).ToDictionary(g => g.Key, g => g.First());
            var rects = new SpriteRect[set.parts.Length];
            bool same = current.Length == rects.Length;
            for (int i = 0; i < set.parts.Length; i++)
            {
                var p = set.parts[i];
                var rect = new Rect(p.rect[0], p.rect[1], p.rect[2], p.rect[3]);
                var pivot = p.pivot != null && p.pivot.Length == 2 ? new Vector2(p.pivot[0], p.pivot[1]) : new Vector2(0.5f, 0f);
                byName.TryGetValue(p.name, out var have);
                rects[i] = new SpriteRect { name = p.name, rect = rect, alignment = SpriteAlignment.Custom, pivot = pivot, spriteID = have != null ? have.spriteID : GUID.Generate() };
                if (same && (have == null || have.rect != rect || (have.pivot - pivot).sqrMagnitude > 1e-6f)) same = false;
            }
            if (same) return false;
            dp.SetSpriteRects(rects);
            dp.GetDataProvider<ISpriteNameFileIdDataProvider>()?.SetNameFileIdPairs(rects.Select(r => new SpriteNameFileIdPair(r.name, r.spriteID)));
            dp.Apply();
            ti.SaveAndReimport();
            return true;
        }

        /// <summary>Builds (or rebuilds) the set's parts and controller when `colorPath` is a rig-set sheet; returns the controller, else null.</summary>
        public static AnimatorController BuildIfRigSet(string colorPath, string key)
        {
            if (!IsRigSet(key)) return null;
            bool placeholder = colorPath.StartsWith(ArtImporter.Active.placeholders, System.StringComparison.Ordinal);
            if (placeholder && File.Exists(ArtImporter.ArtColorPath(key))) return null;
            var jsonPath = JsonPath(colorPath);
            if (!File.Exists(jsonPath)) { Debug.LogError($"[ArtImporter] {colorPath}: a rig set needs {Path.GetFileName(jsonPath)} (contract §11.3)."); return null; }
            var set = RigSet.Parse(File.ReadAllText(jsonPath), out var error);
            if (set == null) { Debug.LogError($"[ArtImporter] Rejected {jsonPath}: {error} (contract §11.3)."); return null; }
            if (SliceParts(colorPath, set)) return null; // the re-import comes back through here with the parts in place

            Directory.CreateDirectory(Folder(key));
            var path = ControllerPath(key);
            if (AssetDatabase.LoadAssetAtPath<AnimatorController>(path) != null) AssetDatabase.DeleteAsset(path);
            foreach (var stale in Directory.GetFiles(Folder(key), "*.anim")) AssetDatabase.DeleteAsset(stale.Replace('\\', '/'));
            var controller = AnimatorController.CreateAnimatorControllerAtPath(path);
            var machine = controller.layers[0].stateMachine;
            foreach (var plant in set.plants)
            {
                var clip = new AnimationClip { name = plant.name, frameRate = Fps };
                foreach (var bone in plant.bones)
                {
                    var bonePath = BonePath(plant, bone);
                    AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve(bonePath, typeof(Transform), "localEulerAnglesRaw.z"),
                        SwayCurve(plant.idle.amplitude_deg, plant.idle.beat_bpm, Depth(plant, bone), plant.BoneCount));
                    if (string.IsNullOrEmpty(bone.parent) && plant.idle.squash > 0f)
                    {
                        AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve(bonePath, typeof(Transform), "m_LocalScale.y"), SquashCurve(plant.idle.squash, plant.idle.beat_bpm, true));
                        AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve(bonePath, typeof(Transform), "m_LocalScale.x"), SquashCurve(plant.idle.squash, plant.idle.beat_bpm, false));
                    }
                }
                var settings = AnimationUtility.GetAnimationClipSettings(clip);
                settings.loopTime = true;
                AnimationUtility.SetAnimationClipSettings(clip, settings);
                AssetDatabase.CreateAsset(clip, Folder(key) + plant.name + ".anim");
                var state = machine.AddState(plant.name);
                state.motion = clip;
                if (machine.defaultState == null || plant == set.plants[0]) machine.defaultState = state;
            }
            EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssets();
            var guid = AssetDatabase.AssetPathToGUID(path);
            if (!string.IsNullOrEmpty(guid))
            {
                var entry = ArtImporter.Settings.CreateOrMoveEntry(guid, ArtImporter.GroupNamed(ArtRules.GroupFor(key)), false, true);
                string address = key + "/animator";
                if (entry.address != address) entry.SetAddress(address, true);
            }
            return controller;
        }
    }
}
