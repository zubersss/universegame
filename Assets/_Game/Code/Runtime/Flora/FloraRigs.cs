using System.Collections.Generic;
using Meridian.Art;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.Flora
{
    /// <summary>
    /// One rigged plant: bone Transforms carrying part sprites, an Animator on the shared controller, swap slots. U-108
    /// (v3.1, B-126): a `replaces_part` slot drives its bone's own renderer (Parts[bone]); the legacy "eyes"/"mouth" slots
    /// of the placeholder set keep their extra renderers (Mouth, Eyes). Everything a frame needs is resolved at Spawn.
    /// </summary>
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
        /// <summary>The replaced-part slots (Def.slots with replaces_part, in order) and the bone renderer each one swaps (null when the bone has no part).</summary>
        public string[] SlotNames = System.Array.Empty<string>();
        public SpriteRenderer[] SlotRenderers = System.Array.Empty<SpriteRenderer>();
        /// <summary>The swap cycle's sequence index this plant shows (-1: no cycle). Tests read it; FloraRigs writes it.</summary>
        public int CycleIndex = -1;
        internal float reactUntil, blinkAt, blinkUntil, nextCheapPose;
        /// <summary>U-108: Time.time the last react began (the turn_bounce squash runs BounceSeconds from it); far in the past before the first.</summary>
        internal float bounceAt = -10f;
        /// <summary>U-108: the deepest squash applied since the last react began (tests: a frame of any length sees the pop).</summary>
        public float BouncePeak { get; internal set; }
        internal int cheapPose;
        // Swap cycle (idle.swap_cycle), resolved at Spawn: the renderer it drives, its sprites, its beat counts, the beat clock.
        internal SpriteRenderer cycleRenderer;
        internal Sprite[] cycleSprites;
        internal int[] cycleBeats;
        internal int cycleTotal, cycleSlot = -1;
        internal float cycleBeatRate, cyclePhaseBeats;
        internal bool cycleReactHolds;
        // Per replaced slot: the resting part (the bone's own) and the part shown while reacting (null: the react leaves it alone).
        internal Sprite[] slotRest = System.Array.Empty<Sprite>(), slotReact = System.Array.Empty<Sprite>();

        /// <summary>The renderer a swap slot drives: a replaced part's bone renderer (v3.1), else the eyes/mouth extra renderer, else null. String lookup: Spawn and tests, not per frame.</summary>
        public SpriteRenderer SlotRenderer(string slot)
        {
            int i = System.Array.IndexOf(SlotNames, slot);
            if (i >= 0) return SlotRenderers[i];
            return slot == "eyes" ? Eyes : slot == "mouth" ? Mouth : null;
        }

        /// <summary>The part a swap slot shows right now (its sprite's name), or null when the slot drives nothing.</summary>
        public string SlotSpriteName(string slot)
        {
            var r = SlotRenderer(slot);
            return r != null && r.sprite != null ? r.sprite.name : null;
        }
    }

    /// <summary>
    /// U-097 (Bible §9.4 v4, contract §11.3): a planet's rigged flora from its rig set (one sheet, one controller). Every
    /// plant is a ≤ 6-bone Transform chain with part sprites; the sway idle is the set's 12 Hz stepped clip started at a
    /// staggered phase. One loop per frame ranks the plants by distance to the camera: the nearest FullRateCap animate at
    /// full rate, the next band falls back to a 3-pose cheap idle at CheapRateHz, the rest stand still (Bible §9.6).
    /// Within a plant's react radius the surveyor is looked at (a flip) and the react swap shows.
    /// U-108 (contract v3.1, B-126 snoozle, D-101 no faces): a `replaces_part` slot swaps its bone's own sprite, never an
    /// extra renderer; the idle's `swap_cycle` steps that slot on the plant's beat (60 / bpm s per beat, offset by the plant's
    /// phase so a field never opens in unison), every frame at full rate and at CheapRateHz in the cheap band; a react shows
    /// `react.swap` on its slot and each `react.also` part, then returns to the cycle's current entry / the resting part. The
    /// placeholder's "eyes"/"mouth" slots keep their extra renderers (blink timer, react mouth). Sprite swaps never fight the
    /// Animator: the sway clip binds only Transform rotation and scale (RigSetBuilder).
    /// No allocation per frame after Populate: sprites, renderers and beat counts are resolved at Spawn.
    /// </summary>
    public sealed class FloraRigs : MonoBehaviour
    {
        /// <summary>Seconds added to the swap-cycle clock (0 in the game). Tests advance it to step a cycle deterministically instead of waiting out beats.</summary>
        [System.NonSerialized] internal float CycleClockOffset; // U-108: tests only (InternalsVisibleTo), never a tuning knob
        float CycleClock => Time.time + CycleClockOffset;
        public const int FullRateCap = 40, CheapBand = 160;
        /// <summary>Animated objects that are not flora (the surveyor, critters): the flora's full-rate share is FullRateCap minus this (Bible §9.6: ≤ 40 on screen in all).</summary>
        public int Reserved;
        public const float CheapRateHz = 4f, RankEvery = 0.25f, ReactSeconds = 0.6f, BlinkSeconds = 0.12f;
        /// <summary>U-108 (Bible §9.3 v4): a `turn_bounce` react squashes the plant root for BounceSeconds, BounceAmount deep, area-preserving.</summary>
        public const float BounceSeconds = 0.15f, BounceAmount = 0.12f;
        public const string TurnBounce = "turn_bounce";

        /// <summary>The squash depth `age` seconds into a bounce: the full BounceAmount pop on the react's first frame, easing back to 0 by BounceSeconds (a quarter cosine), 0 outside it. Pure.</summary>
        public static float BounceK(float age) => age < 0f || age >= BounceSeconds ? 0f : BounceAmount * Mathf.Cos(age / BounceSeconds * Mathf.PI * 0.5f);

        /// <summary>The root's local scale for a facing (±1) and a bounce depth k: squashed down by k, widened by k (area kept).</summary>
        public static Vector3 BounceScale(int facing, float k) => new Vector3(facing * (1f + k), 1f - k, 1f);
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

        /// <summary>The planet the set belongs to (its biome bands pick the plants); null = no biome filter.</summary>
        public Meridian.Planets.PlanetId? planet;
        /// <summary>U-123: a per-column biome rule that overrides BiomeNameAt while set (Mercury: the terminator's zone when the plants are placed; they stay where they grew as the band creeps).</summary>
        public System.Func<int, string> biomeRule;
        readonly Dictionary<string, RigSet.Plant[]> byBiome = new Dictionary<string, RigSet.Plant[]>(8);

        /// <summary>U-110: the biome name a column belongs to, in the rig set's vocabulary (Earth: the band at x; the ocean band's land is the coast). Pure.</summary>
        public static string BiomeNameAt(Meridian.Planets.PlanetId? planet, int x)
        {
            if (planet == Meridian.Planets.PlanetId.Earth)
            {
                var b = Meridian.Terrain.EarthBiomes.At(x);
                return b == Meridian.Terrain.Biome.Ocean ? "coast" : b.ToString().ToLowerInvariant();
            }
            if (planet == Meridian.Planets.PlanetId.Mars)
            {
                // U-118 (B-140): the region names in the rig set's vocabulary — plains / canyon / polar, Tharsis the highlands.
                var r = Meridian.Planet.Backdrop.StageRegions.At(Meridian.Planets.PlanetId.Mars, x);
                return r == "mars_tharsis" ? "highlands" : r.StartsWith("mars_", System.StringComparison.Ordinal) ? r.Substring(5) : r;
            }
            if (planet == Meridian.Planets.PlanetId.Venus) return VenusBiomeFor(x); // U-125 (B-153)
            return null; // Mercury: the zone moves with the clock — MercuryBiomeFor through biomeRule
        }

        /// <summary>U-125 (B-153): Venus's ground biomes in the rig set's vocabulary — "vent_fields" over a vent field, "surface_plains" elsewhere (the
        /// tesserae included); "cloud_deck" and "station_rails" are the floating station's, never a terrain column's. Pure.</summary>
        public const string VenusVents = "vent_fields", VenusPlains = "surface_plains", VenusDeck = "cloud_deck", VenusRails = "station_rails";
        public static string VenusBiomeFor(int x) => Meridian.Terrain.VenusLandforms.At(x) == Meridian.Terrain.VenusFeature.VentField ? VenusVents : VenusPlains;

        /// <summary>U-127 (B-155): Jupiter's biome names for its rig set — "red_spot" inside the Great Red Spot, else the floe's deck ("deck1",
        /// "deck2", "deck3"; the deep grows nothing). Pure.</summary>
        public static string JupiterBiomeFor(int x, float surfaceY)
        {
            if (Meridian.Terrain.CloudColumn.CloudLayout.InRedSpot(x)) return "red_spot";
            var band = Meridian.Terrain.CloudColumn.CloudLayout.BandAt(surfaceY);
            return band == Meridian.Terrain.CloudColumn.CloudBand.Deck2 ? "deck2" : band == Meridian.Terrain.CloudColumn.CloudBand.Deck3 ? "deck3"
                : band == Meridian.Terrain.CloudColumn.CloudBand.Deck1 || band == Meridian.Terrain.CloudColumn.CloudBand.Sky ? "deck1" : null;
        }

        /// <summary>U-129 (B-157): Saturn's biome names — "hexagon" inside the North Polar Hexagon, else the floe's deck (deck1 / deck2 / deck3; the
        /// deep grows nothing). Pure.</summary>
        public static string SaturnBiomeFor(int x, float surfaceY)
        {
            if (Meridian.Terrain.CloudColumn.CloudLayout.InHexagon(x)) return "hexagon";
            var band = Meridian.Terrain.CloudColumn.CloudLayout.BandAt(surfaceY);
            return band == Meridian.Terrain.CloudColumn.CloudBand.Deck2 ? "deck2" : band == Meridian.Terrain.CloudColumn.CloudBand.Deck3 ? "deck3"
                : band == Meridian.Terrain.CloudColumn.CloudBand.Deck1 || band == Meridian.Terrain.CloudColumn.CloudBand.Sky ? "deck1" : null;
        }

        /// <summary>U-123 (B-148): Mercury's biome names for its rig set — "polar" in a cold trap, else the terminator's zone at that clock: "day", "twilight", "night". Pure.</summary>
        public static string MercuryBiomeFor(int x, double realSeconds, int width)
        {
            if (width <= 0) return null;
            if (Meridian.Terrain.MercuryLandforms.InColdTrap(x, width)) return "polar";
            return Meridian.Terrain.MercuryTerminator.ZoneAt(x, realSeconds, width).ToString().ToLowerInvariant();
        }

        /// <summary>
        /// U-110: the plants of `set` whose `biomes` list names `biome` (one kind is a kind: the desert is all Shiverbarrel); the whole set only when
        /// the biome is unknown or null, or no plant lists it. Pure.
        /// </summary>
        public static RigSet.Plant[] PlantsFor(RigSet set, string biome)
        {
            if (set == null || set.plants == null) return System.Array.Empty<RigSet.Plant>();
            if (string.IsNullOrEmpty(biome)) return set.plants;
            var list = new List<RigSet.Plant>(set.plants.Length);
            foreach (var p in set.plants)
                if (p.biomes != null && System.Array.IndexOf(p.biomes, biome) >= 0) list.Add(p);
            return list.Count >= 1 ? list.ToArray() : set.plants;
        }

        RigSet.Plant[] CandidatesAt(int tx)
        {
            string biome = (biomeRule != null ? biomeRule(tx) : BiomeNameAt(planet, tx)) ?? "";
            if (!byBiome.TryGetValue(biome, out var list)) { list = PlantsFor(Set, biome); byBiome[biome] = list; }
            return list;
        }

        /// <summary>`count` plants every `spacing` m (jittered ± 40 %) around `aroundX`, feet on the terrain's top solid tile, each kind from its
        /// column's biome (U-110); runs once the set is Ready.</summary>
        public void Populate(int count, float spacing, float aroundX, int seed)
        {
            if (!Ready) { pendingPopulate = (count, spacing, aroundX, seed); return; }
            byBiome.Clear();
            float x0 = aroundX - count * spacing * 0.5f;
            for (int i = 0; i < count; i++)
            {
                float x = x0 + i * spacing + (Hash01(seed, i * 3 + 1) - 0.5f) * spacing * 0.8f;
                int tx = Mathf.FloorToInt(x);
                float y = terrain != null ? terrain.TopSolidY(tx) + 1f : 0f;
                var pool = CandidatesAt(tx);
                var def = pool[Mathf.FloorToInt(Hash01(seed, i * 3 + 2) * pool.Length) % pool.Length];
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
            plant.Phase = Hash01(seed, 5);
            // Legacy face swaps (the placeholder daisy; never a replaced part): extra renderers on the slot's bone at its offset
            // (B-112 json), else on the last bone's tip (the head). Absent from a v3.1 set (D-101): both stay null.
            var head = plant.Bones[def.bones.Length - 1];
            float headUp = def.bones[def.bones.Length - 1].length * 0.5f;
            if (!IsReplacedPart(def, "eyes")) plant.Eyes = Swap(plant, SlotBone(plant, "eyes", head), "eyes", SlotOffset(def, "eyes", new Vector3(0f, headUp + 0.08f, 0f)), SlotOrder(def, "eyes", def.bones.Length + 1));
            if (!IsReplacedPart(def, "mouth")) plant.Mouth = Swap(plant, SlotBone(plant, "mouth", head), "mouth", SlotOffset(def, "mouth", new Vector3(0f, headUp - 0.12f, 0f)), SlotOrder(def, "mouth", def.bones.Length + 2));
            // v3.1 replaced-part slots and the swap cycle (U-108): resolved once here, read without lookups per frame.
            ResolveSlots(plant);
            plant.Animator = go.AddComponent<Animator>();
            plant.Animator.runtimeAnimatorController = Controller;
            plant.Animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            plant.Animator.Play(Animator.StringToHash(def.name), 0, plant.Phase);
            plant.blinkAt = Time.time + 2f + Hash01(seed, 6) * 4f;
            plant.FullRate = true;
            Plants.Add(plant);
            return plant;
        }

        static RigSet.Slot FindSlot(RigSet.Plant def, string slot) => def.FindSlot(slot);

        static bool IsReplacedPart(RigSet.Plant def, string slot)
        {
            var s = def.FindSlot(slot);
            return s != null && s.replaces_part;
        }

        Sprite SpriteOf(string part) => !string.IsNullOrEmpty(part) && sprites.TryGetValue(part, out var s) ? s : null;

        /// <summary>
        /// U-108: fills the plant's replaced-part slots (each one's bone renderer, resting part, react part) and its swap
        /// cycle (renderer, sprites, beat counts, phase offset), and shows the cycle's entry for this instant. The react part
        /// of a slot is `react.swap` when that names one of the slot's swaps, else the slot's `react.also` part, else none.
        /// A slot whose bone has no renderer, or a cycle with a missing sprite, is left inert rather than drawing nothing.
        /// </summary>
        void ResolveSlots(RigPlant plant)
        {
            var def = plant.Def;
            int n = 0;
            if (def.slots != null) foreach (var s in def.slots) if (s != null && s.replaces_part) n++;
            if (n > 0)
            {
                plant.SlotNames = new string[n];
                plant.SlotRenderers = new SpriteRenderer[n];
                plant.slotRest = new Sprite[n];
                plant.slotReact = new Sprite[n];
                int k = 0;
                foreach (var s in def.slots)
                {
                    if (s == null || !s.replaces_part) continue;
                    int bi = def.BoneIndex(s.bone);
                    def.swaps.TryGetValue(s.slot, out var states);
                    plant.SlotNames[k] = s.slot;
                    plant.SlotRenderers[k] = bi >= 0 ? plant.Parts[bi] : null;
                    plant.slotRest[k] = SpriteOf(bi >= 0 ? def.bones[bi].part : null) ?? (states != null && states.Length > 0 ? SpriteOf(states[0]) : null);
                    string reactPart = states != null && !string.IsNullOrEmpty(def.react.swap) && System.Array.IndexOf(states, def.react.swap) >= 0 ? def.react.swap : null;
                    if (reactPart == null && def.react.also != null && def.react.also.TryGetValue(s.slot, out var alsoPart)) reactPart = alsoPart;
                    plant.slotReact[k] = plant.SlotRenderers[k] != null && plant.slotRest[k] != null ? SpriteOf(reactPart) : null;
                    k++;
                }
            }
            var cycle = def.Cycle;
            if (cycle == null) return;
            var renderer = plant.SlotRenderer(cycle.slot);
            if (renderer == null) return;
            var cycleSprites = new Sprite[cycle.sequence.Length];
            for (int i = 0; i < cycleSprites.Length; i++) { cycleSprites[i] = SpriteOf(cycle.sequence[i]); if (cycleSprites[i] == null) return; }
            plant.cycleRenderer = renderer;
            plant.cycleSprites = cycleSprites;
            plant.cycleSlot = System.Array.IndexOf(plant.SlotNames, cycle.slot);
            plant.cycleBeats = cycle.beats;
            plant.cycleTotal = cycle.TotalBeats;
            plant.cycleBeatRate = def.idle.beat_bpm / 60f;
            plant.cyclePhaseBeats = plant.Phase * plant.cycleTotal;
            plant.cycleReactHolds = plant.cycleSlot >= 0 && plant.slotReact[plant.cycleSlot] != null;
            plant.CycleIndex = RigSet.SwapCycle.IndexAt(CycleClock * plant.cycleBeatRate + plant.cyclePhaseBeats, plant.cycleBeats, plant.cycleTotal);
            renderer.sprite = cycleSprites[plant.CycleIndex];
        }

        /// <summary>Where the plant's swap cycle stands now, in beats into its loop [0, total) (phase and CycleClockOffset included); 0 without a cycle. Tests.</summary>
        public float CycleBeats(RigPlant plant) => plant.cycleRenderer != null ? Mathf.Repeat(CycleClock * plant.cycleBeatRate + plant.cyclePhaseBeats, plant.cycleTotal) : 0f;

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
                    bool wantFull = i < Mathf.Max(0, FullRateCap - Reserved);
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
            float cycleNow = CycleClock;
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
                    if (reacting && p.Def.react.action == TurnBounce) { p.bounceAt = now; p.BouncePeak = 0f; } // U-108: the bounce starts on the react's rising edge
                    if (p.Mouth != null && p.Def.swaps.TryGetValue("mouth", out var mouths) && mouths.Length > 0)
                    {
                        string want = reacting && !string.IsNullOrEmpty(p.Def.react.swap) ? p.Def.react.swap : mouths[0];
                        if (sprites.TryGetValue(want, out var ms)) p.Mouth.sprite = ms;
                    }
                    // v3.1 replaced parts (U-108): react.swap on its slot and every react.also part while reacting; back to the
                    // cycle's current entry (the cycle slot) or the bone's resting part when it ends.
                    for (int i = 0; i < p.SlotRenderers.Length; i++)
                    {
                        var reactSprite = p.slotReact[i];
                        if (reactSprite == null) continue;
                        p.SlotRenderers[i].sprite = reacting ? reactSprite : i == p.cycleSlot ? p.cycleSprites[p.CycleIndex] : p.slotRest[i];
                    }
                }
                // U-108: the turn_bounce squash on the plant root (the facing sign rides along; the bones' sway is untouched).
                if (now - p.bounceAt <= BounceSeconds + dt)
                {
                    float k = BounceK(now - p.bounceAt);
                    if (k > p.BouncePeak) p.BouncePeak = k;
                    var want = BounceScale(p.Facing, k);
                    if (p.Root.localScale != want) p.Root.localScale = want;
                }
                // Blink.
                if (p.Eyes != null && p.Def.swaps.TryGetValue("eyes", out var eyes) && eyes.Length > 1)
                {
                    if (now >= p.blinkAt) { p.blinkAt = now + 2.5f + Hash01(p.Rank, Mathf.FloorToInt(now)) * 4f; p.blinkUntil = now + BlinkSeconds; if (sprites.TryGetValue(eyes[1], out var closed)) p.Eyes.sprite = closed; }
                    else if (p.blinkUntil > 0f && now >= p.blinkUntil) { p.blinkUntil = 0f; if (sprites.TryGetValue(eyes[0], out var open)) p.Eyes.sprite = open; }
                }
                // Cheap idle: three poses at CheapRateHz for the band past the full-rate cap; beyond it the pose holds.
                bool cheapTick = false;
                if (!p.FullRate && p.Rank < FullRateCap + CheapBand && now >= p.nextCheapPose)
                {
                    cheapTick = true;
                    p.nextCheapPose = now + 1f / CheapRateHz;
                    p.cheapPose = (p.cheapPose + 1) % 3;
                    float angle = p.Def.idle.amplitude_deg / Mathf.Max(1, p.Def.BoneCount) * Mathf.Sin(p.cheapPose * 2f * Mathf.PI / 3f + p.Phase * 6.28f);
                    for (int i = 0; i < p.Bones.Length; i++) p.Bones[i].localRotation = Quaternion.Euler(0f, 0f, angle);
                }
                // Swap cycle (v3.1, U-108): the entry for this beat, written only when the index changes; held by the react swap
                // while reacting (re-applied on the react's falling edge above). Full rate every frame, the cheap band on its tick.
                if (p.cycleRenderer != null && (p.FullRate || cheapTick))
                {
                    int idx = RigSet.SwapCycle.IndexAt(cycleNow * p.cycleBeatRate + p.cyclePhaseBeats, p.cycleBeats, p.cycleTotal);
                    if (idx != p.CycleIndex)
                    {
                        p.CycleIndex = idx;
                        if (!(p.Reacting && p.cycleReactHolds)) p.cycleRenderer.sprite = p.cycleSprites[idx];
                    }
                }
            }
            watch.Stop();
            LastMs = (float)watch.Elapsed.TotalMilliseconds;
        }

        /// <summary>D-146 (U-123 capture): the plants go, the rig set stays loaded, so Populate can grow them again at once (Mercury's
        /// plants take the zone of the moment they are placed).</summary>
        public void ClearPlants()
        {
            foreach (var p in Plants) if (p.Root != null) Destroy(p.Root.gameObject);
            Plants.Clear();
        }

        public void Clear()
        {
            ClearPlants();
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
