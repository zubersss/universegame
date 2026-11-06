using System.Collections.Generic;
using Meridian.Art;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.Flora
{
    /// <summary>One rigged plant: bone Transforms carrying part sprites, an Animator on the shared controller, face swaps.</summary>
    public sealed class RigPlant
    {
        public RigSet.Plant Def;
        public Transform Root;
        public Animator Animator;
        public Transform[] Bones;
        public SpriteRenderer[] Parts;
        public SpriteRenderer Mouth, Eyes;
        public float Phase;
        public int Rank;
        public bool FullRate;
        public bool Reacting;
        public int Facing = 1;
        internal float reactUntil, blinkAt, blinkUntil, nextCheapPose;
        internal int cheapPose;
    }

    /// <summary>
    /// U-097 (Bible §9.4 v4, contract §11.3): a planet's rigged flora from its rig set (one sheet, one controller). Every
    /// plant is a ≤ 6-bone Transform chain with part sprites; the sway idle is the set's 12 Hz stepped clip started at a
    /// staggered phase. One loop per frame ranks the plants by distance to the camera: the nearest FullRateCap animate at
    /// full rate, the next band falls back to a 3-pose cheap idle at CheapRateHz, the rest stand still (Bible §9.6).
    /// Within a plant's react radius the surveyor is looked at (a flip) and the react face shows; eyes blink on their own.
    /// No allocation per frame after Populate.
    /// </summary>
    public sealed class FloraRigs : MonoBehaviour
    {
        public const int FullRateCap = 40, CheapBand = 160;
        public const float CheapRateHz = 4f, RankEvery = 0.25f, ReactSeconds = 0.6f, BlinkSeconds = 0.12f;
        public const int SortingOrder = 3;
        public const string JsonSuffix = "/json", AnimatorSuffix = "/animator";

        public Camera view;
        public Transform player;
        public TerrainStreamer terrain;

        public string Key { get; private set; }
        public RigSet Set { get; private set; }
        public RuntimeAnimatorController Controller { get; private set; }
        public bool Ready => Set != null && sprites.Count > 0 && Controller != null;
        public int SpriteCount => sprites.Count;
        /// <summary>Addresses the probes found nothing for (tests): "json", "sprites", "controller".</summary>
        public string Missing { get; private set; } = "";
        public string ParseError { get; private set; }
        public readonly List<RigPlant> Plants = new List<RigPlant>(320);
        /// <summary>Last frame's loop time (ms): the budget line is 1.0 ms for 300 plants (Animator evaluation is Unity's, outside this).</summary>
        public float LastMs { get; private set; }
        public int FullRateCount { get; private set; }
        public int CheapCount { get; private set; }

        readonly Dictionary<string, Sprite> sprites = new Dictionary<string, Sprite>();
        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>(3);
        readonly List<(RigPlant plant, float d2)> order = new List<(RigPlant, float)>(320);
        readonly System.Diagnostics.Stopwatch watch = new System.Diagnostics.Stopwatch();
        float nextRank;
        (int count, float spacing, float aroundX, int seed)? pendingPopulate;

        /// <summary>Loads the set (json, part sprites, controller) at `key` (flora/&lt;planet&gt;/rigset); plants can be spawned once Ready.</summary>
        public void Load(string key)
        {
            Clear();
            Key = key;
            Probe<TextAsset>(key + JsonSuffix, h => h.Completed += op => { if (this != null && op.Status == AsyncOperationStatus.Succeeded && op.Result != null) { Set = RigSet.Parse(op.Result.text, out var err); ParseError = err; if (Set == null) Debug.LogError($"[FloraRigs] {key}: {err}"); TryPending(); } });
            Probe<IList<Sprite>>(key, h => h.Completed += op => { if (this != null && op.Status == AsyncOperationStatus.Succeeded && op.Result != null) { foreach (var s in op.Result) sprites[s.name] = s; TryPending(); } });
            Probe<RuntimeAnimatorController>(key + AnimatorSuffix, h => h.Completed += op => { if (this != null && op.Status == AsyncOperationStatus.Succeeded) { Controller = op.Result; TryPending(); } });
        }

        /// <summary>A sprite list cannot be found by type (an Editor location probe for IList&lt;Sprite&gt; returns nothing): probe the key untyped and load by key, as CreatureDirector does.</summary>
        void Probe<T>(string address, System.Action<AsyncOperationHandle<T>> load)
        {
            bool spriteList = typeof(T) == typeof(IList<Sprite>);
            var probe = spriteList ? Addressables.LoadResourceLocationsAsync(address) : Addressables.LoadResourceLocationsAsync(address, typeof(T));
            probe.Completed += l =>
            {
                IResourceLocation loc = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0 ? l.Result[0] : null;
                ArtLoad.Release(l);
                if (this == null) return;
                if (loc == null) { Missing += address + " "; return; }
                var h = spriteList ? ArtLoad.Asset<T>(address) : ArtLoad.Asset<T>(loc, Key);
                handles.Add(h);
                load(h);
            };
        }

        void TryPending()
        {
            if (!Ready || !pendingPopulate.HasValue) return;
            var p = pendingPopulate.Value;
            pendingPopulate = null;
            Populate(p.count, p.spacing, p.aroundX, p.seed);
        }

        /// <summary>`count` plants every `spacing` m (jittered ± 40 %) around `aroundX`, feet on the terrain's top solid tile; runs once the set is Ready.</summary>
        public void Populate(int count, float spacing, float aroundX, int seed)
        {
            if (!Ready) { pendingPopulate = (count, spacing, aroundX, seed); return; }
            float x0 = aroundX - count * spacing * 0.5f;
            for (int i = 0; i < count; i++)
            {
                float x = x0 + i * spacing + (Hash01(seed, i * 3 + 1) - 0.5f) * spacing * 0.8f;
                int tx = Mathf.FloorToInt(x);
                float y = terrain != null ? terrain.TopSolidY(tx) + 1f : 0f;
                var def = Set.plants[Mathf.FloorToInt(Hash01(seed, i * 3 + 2) * Set.plants.Length) % Set.plants.Length];
                Spawn(def, new Vector2(x, y), seed * 977 + i);
            }
        }

        /// <summary>Builds one plant of `def` with its feet at `feet`; its sway starts at a phase hashed from `seed`.</summary>
        public RigPlant Spawn(RigSet.Plant def, Vector2 feet, int seed)
        {
            if (!Ready) return null;
            var go = new GameObject(def.name);
            go.transform.SetParent(transform, false);
            go.transform.position = new Vector3(feet.x, feet.y, 0f);
            var plant = new RigPlant { Def = def, Root = go.transform, Bones = new Transform[def.bones.Length], Parts = new SpriteRenderer[def.bones.Length] };
            // Bones: each under its parent at the parent's tip (length up its local y); the plant root bone is the Animator's child "root"...
            for (int i = 0; i < def.bones.Length; i++)
            {
                var b = def.bones[i];
                var bgo = new GameObject(b.name);
                Transform parent = go.transform;
                float up = 0f;
                if (!string.IsNullOrEmpty(b.parent))
                {
                    int pi = System.Array.FindIndex(def.bones, x => x.name == b.parent);
                    if (pi >= 0 && pi < i && plant.Bones[pi] != null) { parent = plant.Bones[pi]; up = def.bones[pi].length; }
                }
                bgo.transform.SetParent(parent, false);
                bgo.transform.localPosition = b.offset_m != null && b.offset_m.Length == 2 ? new Vector3(b.offset_m[0], b.offset_m[1], 0f) : new Vector3(0f, up, 0f);
                plant.Bones[i] = bgo.transform;
                if (!string.IsNullOrEmpty(b.part) && sprites.TryGetValue(b.part, out var sprite))
                {
                    var sr = bgo.AddComponent<SpriteRenderer>();
                    sr.sprite = sprite;
                    sr.sortingOrder = SortingOrder + (b.order >= 0 ? b.order : i);
                    plant.Parts[i] = sr;
                }
            }
            // Face swaps: on the slot's bone at its offset (B-112 json), else on the last bone's tip (the head).
            var head = plant.Bones[def.bones.Length - 1];
            float headUp = def.bones[def.bones.Length - 1].length * 0.5f;
            plant.Eyes = Swap(plant, SlotBone(plant, "eyes", head), "eyes", SlotOffset(def, "eyes", new Vector3(0f, headUp + 0.08f, 0f)), SlotOrder(def, "eyes", def.bones.Length + 1));
            plant.Mouth = Swap(plant, SlotBone(plant, "mouth", head), "mouth", SlotOffset(def, "mouth", new Vector3(0f, headUp - 0.12f, 0f)), SlotOrder(def, "mouth", def.bones.Length + 2));
            plant.Animator = go.AddComponent<Animator>();
            plant.Animator.runtimeAnimatorController = Controller;
            plant.Animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            plant.Phase = Hash01(seed, 5);
            plant.Animator.Play(Animator.StringToHash(def.name), 0, plant.Phase);
            plant.blinkAt = Time.time + 2f + Hash01(seed, 6) * 4f;
            plant.FullRate = true;
            Plants.Add(plant);
            return plant;
        }

        static RigSet.Slot FindSlot(RigSet.Plant def, string slot)
        {
            if (def.slots == null) return null;
            foreach (var s in def.slots) if (s.slot == slot) return s;
            return null;
        }

        static Transform SlotBone(RigPlant plant, string slot, Transform fallback)
        {
            var s = FindSlot(plant.Def, slot);
            if (s == null || string.IsNullOrEmpty(s.bone)) return fallback;
            int i = System.Array.FindIndex(plant.Def.bones, b => b.name == s.bone);
            return i >= 0 && plant.Bones[i] != null ? plant.Bones[i] : fallback;
        }

        static Vector3 SlotOffset(RigSet.Plant def, string slot, Vector3 fallback)
        {
            var s = FindSlot(def, slot);
            return s != null && s.offset_m != null && s.offset_m.Length == 2 ? new Vector3(s.offset_m[0], s.offset_m[1], 0f) : fallback;
        }

        static int SlotOrder(RigSet.Plant def, string slot, int fallback)
        {
            var s = FindSlot(def, slot);
            return s != null && s.order >= 0 ? s.order : fallback;
        }

        SpriteRenderer Swap(RigPlant plant, Transform head, string slot, Vector3 local, int order)
        {
            if (!plant.Def.swaps.TryGetValue(slot, out var names) || names.Length == 0 || !sprites.TryGetValue(names[0], out var first)) return null;
            var go = new GameObject(slot);
            go.transform.SetParent(head, false);
            go.transform.localPosition = local;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = first;
            sr.sortingOrder = SortingOrder + order;
            return sr;
        }

        public static float Hash01(int seed, int salt)
        {
            uint h = (uint)(seed * 73856093) ^ (uint)(salt * 19349663);
            h ^= h >> 13; h *= 0x5bd1e995u; h ^= h >> 15;
            return (h & 0xffffffu) / (float)0xffffff;
        }

        void LateUpdate()
        {
            watch.Restart();
            float now = Time.time;
            Vector2 eye = view != null ? (Vector2)view.transform.position : Vector2.zero;
            if (now >= nextRank)
            {
                nextRank = now + RankEvery;
                order.Clear();
                foreach (var p in Plants) order.Add((p, ((Vector2)p.Root.position - eye).sqrMagnitude));
                order.Sort((a, b) => a.d2.CompareTo(b.d2));
                int full = 0, cheap = 0;
                for (int i = 0; i < order.Count; i++)
                {
                    var p = order[i].plant;
                    p.Rank = i;
                    bool wantFull = i < FullRateCap;
                    if (wantFull != p.FullRate)
                    {
                        p.FullRate = wantFull;
                        p.Animator.enabled = wantFull;
                        if (wantFull) p.Animator.Play(Animator.StringToHash(p.Def.name), 0, p.Phase);
                    }
                    if (wantFull) full++; else if (i < FullRateCap + CheapBand) cheap++;
                }
                FullRateCount = full; CheapCount = cheap;
            }
            Vector2 who = player != null ? (Vector2)player.position : eye;
            float dt = Time.deltaTime;
            foreach (var p in Plants)
            {
                // React: the surveyor within the radius: look at them, show the react face for ReactSeconds after they leave.
                float dx = who.x - p.Root.position.x;
                bool near = dx * dx + (who.y - p.Root.position.y) * (who.y - p.Root.position.y) <= p.Def.react.radius_m * p.Def.react.radius_m;
                if (near)
                {
                    p.reactUntil = now + ReactSeconds;
                    int face = dx >= 0f ? 1 : -1;
                    if (face != p.Facing) { p.Facing = face; var s = p.Root.localScale; s.x = Mathf.Abs(s.x) * face; p.Root.localScale = s; }
                }
                bool reacting = now < p.reactUntil;
                if (reacting != p.Reacting)
                {
                    p.Reacting = reacting;
                    if (p.Mouth != null && p.Def.swaps.TryGetValue("mouth", out var mouths) && mouths.Length > 0)
                    {
                        string want = reacting && !string.IsNullOrEmpty(p.Def.react.swap) ? p.Def.react.swap : mouths[0];
                        if (sprites.TryGetValue(want, out var ms)) p.Mouth.sprite = ms;
                    }
                }
                // Blink.
                if (p.Eyes != null && p.Def.swaps.TryGetValue("eyes", out var eyes) && eyes.Length > 1)
                {
                    if (now >= p.blinkAt) { p.blinkAt = now + 2.5f + Hash01(p.Rank, Mathf.FloorToInt(now)) * 4f; p.blinkUntil = now + BlinkSeconds; if (sprites.TryGetValue(eyes[1], out var closed)) p.Eyes.sprite = closed; }
                    else if (p.blinkUntil > 0f && now >= p.blinkUntil) { p.blinkUntil = 0f; if (sprites.TryGetValue(eyes[0], out var open)) p.Eyes.sprite = open; }
                }
                // Cheap idle: three poses at CheapRateHz for the band past the full-rate cap; beyond it the pose holds.
                if (!p.FullRate && p.Rank < FullRateCap + CheapBand && now >= p.nextCheapPose)
                {
                    p.nextCheapPose = now + 1f / CheapRateHz;
                    p.cheapPose = (p.cheapPose + 1) % 3;
                    float angle = p.Def.idle.amplitude_deg / Mathf.Max(1, p.Def.BoneCount) * Mathf.Sin(p.cheapPose * 2f * Mathf.PI / 3f + p.Phase * 6.28f);
                    for (int i = 0; i < p.Bones.Length; i++) p.Bones[i].localRotation = Quaternion.Euler(0f, 0f, angle);
                }
            }
            watch.Stop();
            LastMs = (float)watch.Elapsed.TotalMilliseconds;
        }

        public void Clear()
        {
            foreach (var p in Plants) if (p.Root != null) Destroy(p.Root.gameObject);
            Plants.Clear();
            sprites.Clear();
            Set = null; Controller = null;
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
        }
    }
}
