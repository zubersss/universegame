using System.Collections.Generic;
using UnityEngine;

namespace Meridian.Flora
{
    /// <summary>
    /// U-103 (D-111, B-122): one plant of a rig set built as a bone hierarchy (a SpriteRenderer per part, the static slots as
    /// extra renderers) with an Animator on the plant root playing the set's controller: authored clips as
    /// `&lt;plant&gt;_&lt;clip&gt;` states (RigSet.StateName), a sway-only plant as the state named after it. Shared by the Pilgrim's
    /// side and top views; FloraRigs keeps its own spawner (ranking, swaps, the beat cycle).
    /// </summary>
    public sealed class RigInstance
    {
        public RigSet.Plant Def;
        public Transform Root;
        public Animator Animator;
        public Transform[] Bones;
        public SpriteRenderer[] Parts;
        public readonly Dictionary<string, SpriteRenderer> Slots = new Dictionary<string, SpriteRenderer>();

        /// <summary>The clip last started with Play (null before the first).</summary>
        public string Playing { get; private set; }
        public bool Loops { get; private set; }
        /// <summary>Time.time when a one-shot clip has shown its last frame (float.MaxValue while a loop plays).</summary>
        public float PlayingUntil { get; private set; } = float.MaxValue;
        public bool OneShotDone => Playing != null && !Loops && Time.time >= PlayingUntil;

        public bool Has(string clip) => Def != null && Def.FindClip(clip) != null;
        public Transform Bone(string name) { int i = Def.BoneIndex(name); return i >= 0 ? Bones[i] : null; }
        /// <summary>A socket in metres from the rig origin (the plant root's parent frame), or `fallback` when the set has none.</summary>
        public Vector2 Socket(string name, Vector2 fallback) => Def != null && Def.sockets.TryGetValue(name, out var s) ? s : fallback;

        /// <summary>Starts one of the plant's authored clips (a missing name or Animator is a no-op).</summary>
        public void Play(string clip, float normalizedTime = 0f)
        {
            var c = Def.FindClip(clip);
            if (c == null || Animator == null) return;
            Animator.Play(Animator.StringToHash(RigSet.StateName(Def.name, clip)), 0, normalizedTime);
            Playing = clip;
            Loops = c.loop;
            PlayingUntil = c.loop ? float.MaxValue : Time.time + c.Seconds * (1f - normalizedTime);
        }
    }

    public static class RigBuild
    {
        public static Dictionary<string, Sprite> ByName(IList<Sprite> sprites)
        {
            var d = new Dictionary<string, Sprite>(sprites != null ? sprites.Count : 0);
            if (sprites != null) foreach (var s in sprites) if (s != null) d[s.name] = s;
            return d;
        }

        /// <summary>
        /// Builds `def` under `parent` at the parent's origin (= the rig origin). Bones sit at their `offset_m` in the parent
        /// bone's frame (the root's from the rig origin; none → the parent's tip); each part renderer draws at
        /// `sortingBase + bone.order` on `sortingLayerID` with `material` (null keeps the default). Non-replacing slots
        /// (bell, porthole) draw their first swap state on their bone at their offset and order.
        /// </summary>
        public static RigInstance Build(RigSet.Plant def, IReadOnlyDictionary<string, Sprite> sprites, Transform parent,
            RuntimeAnimatorController controller, int sortingLayerID, int sortingBase, Material material)
        {
            var go = new GameObject(def.name);
            go.transform.SetParent(parent, false);
            var inst = new RigInstance { Def = def, Root = go.transform, Bones = new Transform[def.bones.Length], Parts = new SpriteRenderer[def.bones.Length] };
            for (int i = 0; i < def.bones.Length; i++)
            {
                var b = def.bones[i];
                var bgo = new GameObject(b.name);
                Transform p = go.transform;
                float up = 0f;
                if (!string.IsNullOrEmpty(b.parent))
                {
                    int pi = def.BoneIndex(b.parent);
                    if (pi >= 0 && pi < i && inst.Bones[pi] != null) { p = inst.Bones[pi]; up = def.bones[pi].length; }
                }
                bgo.transform.SetParent(p, false);
                bgo.transform.localPosition = b.offset_m != null && b.offset_m.Length == 2 ? new Vector3(b.offset_m[0], b.offset_m[1], 0f) : new Vector3(0f, up, 0f);
                inst.Bones[i] = bgo.transform;
                if (!string.IsNullOrEmpty(b.part) && sprites.TryGetValue(b.part, out var sprite))
                    inst.Parts[i] = Renderer(bgo, sprite, sortingLayerID, sortingBase + (b.order >= 0 ? b.order : i), material);
            }
            if (def.slots != null)
                foreach (var s in def.slots)
                {
                    if (s == null || s.replaces_part || string.IsNullOrEmpty(s.slot)) continue;
                    if (!def.swaps.TryGetValue(s.slot, out var states) || states.Length == 0 || !sprites.TryGetValue(states[0], out var sp)) continue;
                    int bi = def.BoneIndex(s.bone);
                    var sgo = new GameObject(s.slot);
                    sgo.transform.SetParent(bi >= 0 ? inst.Bones[bi] : go.transform, false);
                    sgo.transform.localPosition = s.offset_m != null && s.offset_m.Length == 2 ? new Vector3(s.offset_m[0], s.offset_m[1], 0f) : Vector3.zero;
                    inst.Slots[s.slot] = Renderer(sgo, sp, sortingLayerID, sortingBase + Mathf.Max(0, s.order), material);
                }
            if (controller != null)
            {
                inst.Animator = go.AddComponent<Animator>();
                inst.Animator.runtimeAnimatorController = controller;
                inst.Animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            }
            return inst;
        }

        /// <summary>
        /// U-192: a rig's bind pose as flat draw items, for a place that cannot hold the renderers Build makes (the docking bay's canvas):
        /// each bone's part and each non-replacing slot's first state with its position from the rig origin (m, as Build places it) and
        /// its draw order, lowest order first (ties in the rig's own sequence). Pure over the definition.
        /// </summary>
        public static List<(string sprite, Vector2 at, int order)> BindPose(RigSet.Plant def)
        {
            var items = new List<(string sprite, Vector2 at, int order, int seq)>();
            if (def == null || def.bones == null) return new List<(string, Vector2, int)>();
            var pos = new Vector2[def.bones.Length];
            for (int i = 0; i < def.bones.Length; i++)
            {
                var b = def.bones[i];
                Vector2 p = Vector2.zero;
                float up = 0f;
                if (!string.IsNullOrEmpty(b.parent))
                {
                    int pi = def.BoneIndex(b.parent);
                    if (pi >= 0 && pi < i) { p = pos[pi]; up = def.bones[pi].length; }
                }
                pos[i] = p + (b.offset_m != null && b.offset_m.Length == 2 ? new Vector2(b.offset_m[0], b.offset_m[1]) : new Vector2(0f, up));
                if (!string.IsNullOrEmpty(b.part)) items.Add((b.part, pos[i], b.order >= 0 ? b.order : i, items.Count));
            }
            if (def.slots != null)
                foreach (var s in def.slots)
                {
                    if (s == null || s.replaces_part || string.IsNullOrEmpty(s.slot)) continue;
                    if (def.swaps == null || !def.swaps.TryGetValue(s.slot, out var states) || states.Length == 0) continue;
                    int bi = def.BoneIndex(s.bone);
                    var at = (bi >= 0 ? pos[bi] : Vector2.zero) + (s.offset_m != null && s.offset_m.Length == 2 ? new Vector2(s.offset_m[0], s.offset_m[1]) : Vector2.zero);
                    items.Add((states[0], at, Mathf.Max(0, s.order), items.Count));
                }
            items.Sort((a, b) => a.order != b.order ? a.order.CompareTo(b.order) : a.seq.CompareTo(b.seq));
            var pose = new List<(string, Vector2, int)>(items.Count);
            foreach (var it in items) pose.Add((it.sprite, it.at, it.order));
            return pose;
        }

        static SpriteRenderer Renderer(GameObject go, Sprite sprite, int layer, int order, Material material)
        {
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingLayerID = layer;
            sr.sortingOrder = order;
            if (material != null) sr.sharedMaterial = material;
            return sr;
        }
    }
}
