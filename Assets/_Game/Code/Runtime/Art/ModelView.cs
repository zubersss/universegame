using System.Collections.Generic;
using Meridian.Rendering;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.Animations;
using UnityEngine.Playables;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.Art
{
    /// <summary>
    /// U-075 (Bible 2.0 §10.6, contract v2.1 §9): the 3D view of an art key. Loads the key's model (GameObject), its
    /// generated URP/Lit material and its clips through Addressables (the key also addresses its 2D placeholder; the
    /// type picks which), and plays clips by the same names as the v1 sheet clips through a PlayableGraph: one
    /// clip playable per clip, built once, so a clip change allocates nothing. Clip loop flags come from the model's
    /// json (ArtMaterials.ModelClipsFor): one-shots hold their last frame. Facing is a 180° yaw; hits flash the
    /// emission through a property block. When the key has no model, Ready stays false and the caller keeps its sprite.
    /// </summary>
    public sealed class ModelView : MonoBehaviour
    {
        public string Key { get; private set; }
        public bool Ready { get; private set; }
        /// <summary>U-090: a load is in flight (the key may still turn out to have no model).</summary>
        public bool Loading { get; private set; }
        public GameObject Instance { get; private set; }
        public string Current { get; private set; }
        /// <summary>Names of the clips the model carries (tests).</summary>
        public IReadOnlyCollection<string> ClipNames => playables.Keys;
        public event System.Action Loaded;

        AsyncOperationHandle<GameObject> modelHandle;
        AsyncOperationHandle<Material> materialHandle;
        AsyncOperationHandle<IList<AnimationClip>> clipsHandle;
        int pending;
        GameObject prefab;
        Material material;
        IList<AnimationClip> clips;

        PlayableGraph graph;
        AnimationPlayableOutput output;
        readonly Dictionary<string, AnimationClipPlayable> playables = new Dictionary<string, AnimationClipPlayable>();
        readonly Dictionary<string, bool> loops = new Dictionary<string, bool>();
        AnimationClipPlayable playing;
        bool playingLoops = true;
        float playingLength;
        bool facingRight = true;
        Renderer[] renderers;
        MaterialPropertyBlock block;
        float flashUntil;
        static readonly int EmissionId = Shader.PropertyToID("_EmissionColor");

        /// <summary>Starts loading `key`'s model; Ready turns true (and Loaded fires) when it is placed and playable.</summary>
        public void Load(string key)
        {
            Key = key;
            Loading = true;
            var locs = Addressables.LoadResourceLocationsAsync(key, typeof(GameObject));
            locs.Completed += l =>
            {
                // The key also addresses its 2D placeholder and its material: load the model and its clip sub-assets
                // from the GameObject location itself, never by the bare key.
                IResourceLocation modelLoc = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0 ? l.Result[0] : null;
                global::Meridian.Art.ArtLoad.Release(l);
                if (modelLoc == null || this == null) { Loading = false; return; } // no model: the caller keeps its 2D view
                pending = 3;
                modelHandle = ArtLoad.Asset<GameObject>(modelLoc, key);
                modelHandle.Completed += op => { prefab = op.Status == AsyncOperationStatus.Succeeded ? op.Result : null; Done(); };
                clipsHandle = ArtLoad.Asset<IList<AnimationClip>>(modelLoc, key);
                clipsHandle.Completed += op => { clips = op.Status == AsyncOperationStatus.Succeeded ? op.Result : null; Done(); };
                LoadGeneratedMaterial(key);
            };
        }

        /// <summary>
        /// The key's generated material (Generated/Models/&lt;key&gt;.mat). The .glb carries glTFast's own material as a
        /// sub-asset, which also matches a Material lookup on the key, so pick the location of the .mat file itself.
        /// </summary>
        void LoadGeneratedMaterial(string key)
        {
            var locs = Addressables.LoadResourceLocationsAsync(key, typeof(Material));
            locs.Completed += l =>
            {
                IResourceLocation matLoc = null;
                if (l.Status == AsyncOperationStatus.Succeeded && l.Result != null)
                    foreach (var loc in l.Result)
                        if (loc.InternalId != null && loc.InternalId.EndsWith(".mat", System.StringComparison.OrdinalIgnoreCase)) { matLoc = loc; break; }
                global::Meridian.Art.ArtLoad.Release(l);
                if (matLoc == null || this == null) { Done(); return; }
                materialHandle = ArtLoad.Asset<Material>(matLoc, key);
                materialHandle.Completed += op => { material = op.Status == AsyncOperationStatus.Succeeded ? op.Result : null; Done(); };
            };
        }

        void Done()
        {
            if (--pending > 0 || this == null || prefab == null) return;
            Instance = Instantiate(prefab, transform, false);
            Instance.transform.localPosition = Vector3.zero;
            renderers = Instance.GetComponentsInChildren<Renderer>();
            var wear = CartoonMaterial != null ? CartoonMaterial : material; // U-100: the cartoon path dresses every model in one silhouette material
            if (wear != null) foreach (var r in renderers) r.sharedMaterial = wear;
            block = new MaterialPropertyBlock();
            SetUpLods();
            if (clips != null && clips.Count > 0) BuildGraph(); // static props: no animator, no graph
            Ready = true;
            Loading = false;
            SetFacing(facingRight);
            if (tint != Color.white) ApplyTint();
            if (!shadows) SetShadows(false);
            Loaded?.Invoke();
        }

        /// <summary>U-076: a model with a "*_LOD1" node (contract v2.2) gets a LODGroup: that node's renderers are LOD1.</summary>
        void SetUpLods()
        {
            Transform lod1 = null;
            foreach (var t in Instance.GetComponentsInChildren<Transform>(true))
                if (t.name.EndsWith("_LOD1")) { lod1 = t; break; }
            if (lod1 == null) return;
            var near = new List<Renderer>();
            var far = new List<Renderer>();
            foreach (var r in renderers) (r.transform.IsChildOf(lod1) ? far : near).Add(r);
            if (near.Count == 0 || far.Count == 0) return;
            var group = Instance.AddComponent<LODGroup>();
            group.SetLODs(new[] { new LOD(LodSwitch, near.ToArray()), new LOD(LodCull, far.ToArray()) });
            group.RecalculateBounds();
        }

        /// <summary>Screen-height fractions: LOD0 above 10 %, LOD1 down to 0.5 % (a rail-camera prop is rarely below).</summary>
        public const float LodSwitch = 0.10f, LodCull = 0.005f;

        /// <summary>
        /// U-076: runs one-shot `name` forward to its end (true) or backward to its start (false) and holds there:
        /// the door's `open` clip opens and closes it. Returns false if unknown.
        /// </summary>
        public bool PlayToward(string name, bool forward)
        {
            if (!Ready || name == null || !playables.TryGetValue(name, out var p)) return false;
            if (name != Current)
            {
                Current = name;
                if (playing.IsValid()) playing.Pause();
                playing = p;
                playingLength = (float)p.GetAnimationClip().length;
                p.SetTime(0); // a fresh one-shot starts at its first pose (a door that was never opened is closed)
                p.Play();
                output.SetSourcePlayable(p);
            }
            playingLoops = false;
            Towards = forward ? 1 : -1;
            playing.SetSpeed(Towards);
            return true;
        }

        /// <summary>+1 running to (or held at) the end, −1 to the start; 0 after a plain Play.</summary>
        public int Towards { get; private set; }

        void BuildGraph()
        {
            var animator = Instance.GetComponentInChildren<Animator>();
            if (animator == null) animator = Instance.AddComponent<Animator>();
            animator.runtimeAnimatorController = null;
            var legacy = Instance.GetComponentInChildren<Animation>();
            if (legacy != null) legacy.enabled = false; // Mecanim clips play through the graph
            graph = PlayableGraph.Create("ModelView " + Key);
            graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
            output = AnimationPlayableOutput.Create(graph, "Model", animator);
            var set = ArtMaterials.ModelClipsFor(Key);
            if (clips != null)
                foreach (var c in clips)
                {
                    if (c == null || playables.ContainsKey(c.name)) continue;
                    playables[c.name] = AnimationClipPlayable.Create(graph, c);
                    loops[c.name] = set == null || !set.TryGet(c.name, out var info) || info.loop;
                }
            graph.Play();
        }

        /// <summary>Plays clip `name` from its start (no-op if it is already playing or unknown). Returns false if unknown.</summary>
        public bool Play(string name)
        {
            if (!Ready || name == null) return false;
            if (name == Current && Towards == 0) return true;
            if (!playables.TryGetValue(name, out var p)) return false;
            Current = name;
            Towards = 0;
            if (playing.IsValid()) playing.Pause();
            playing = p;
            playingLoops = loops.TryGetValue(name, out var l) && l;
            playingLength = (float)p.GetAnimationClip().length;
            p.SetTime(0);
            p.SetSpeed(1);
            p.Play();
            output.SetSourcePlayable(p);
            return true;
        }

        /// <summary>The model faces +X; facing left is a 180° yaw about the vertical (contract v2 §9, D-065).</summary>
        public void SetFacing(bool right)
        {
            facingRight = right;
            if (Instance != null) Instance.transform.localRotation = right ? Quaternion.identity : Quaternion.Euler(0f, 180f, 0f);
        }

        /// <summary>A short emissive hit flash (seconds).</summary>
        public void Flash(float seconds = 0.12f) => flashUntil = Time.time + seconds;

        Color tint = Color.white;
        bool shadows = true;
        static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");

        /// <summary>U-100: set while the cartoon path is on: every model loads with this material instead of its own (CartoonStage).</summary>
        public static Material CartoonMaterial;

        /// <summary>U-100: swaps every renderer's material now (models that loaded before the switch).</summary>
        public void Wear(Material m)
        {
            if (renderers == null || m == null) return;
            foreach (var r in renderers) r.sharedMaterial = m;
        }

        /// <summary>U-090: a colour multiplier on every renderer (the stage haze tint); kept through the hit flash.</summary>
        public void SetTint(Color c)
        {
            tint = c;
            if (Ready) ApplyTint();
        }

        void ApplyTint()
        {
            if (renderers == null) return;
            foreach (var r in renderers)
            {
                r.GetPropertyBlock(block);
                block.SetColor(BaseColorId, tint);
                r.SetPropertyBlock(block);
            }
        }

        /// <summary>U-090: shadow casting on every renderer (stage layers and foreground pieces cast none).</summary>
        public void SetShadows(bool on)
        {
            shadows = on;
            if (renderers == null) return;
            foreach (var r in renderers) r.shadowCastingMode = on ? UnityEngine.Rendering.ShadowCastingMode.On : UnityEngine.Rendering.ShadowCastingMode.Off;
        }

        void LateUpdate()
        {
            if (!Ready) return;
            // One-shots hold their last frame (Mecanim import loops every clip; the json says which ones don't).
            if (!playingLoops && playing.IsValid())
            {
                double t = playing.GetTime();
                if (Towards >= 0 && t >= playingLength) { playing.SetTime(Mathf.Max(0f, playingLength - 0.001f)); playing.SetSpeed(0); }
                else if (Towards < 0 && t <= 0) { playing.SetTime(0); playing.SetSpeed(0); }
            }
            bool flashing = Time.time < flashUntil;
            if (flashing != flashShown && renderers != null)
            {
                flashShown = flashing;
                foreach (var r in renderers)
                {
                    r.GetPropertyBlock(block);
                    if (flashing) block.SetColor(EmissionId, new Color(2f, 1.6f, 1.4f)); else { block.Clear(); if (tint != Color.white) block.SetColor(BaseColorId, tint); }
                    r.SetPropertyBlock(block);
                }
            }
        }

        bool flashShown;

        void OnDestroy()
        {
            if (graph.IsValid()) graph.Destroy();
            if (modelHandle.IsValid()) global::Meridian.Art.ArtLoad.Release(modelHandle);
            if (materialHandle.IsValid()) global::Meridian.Art.ArtLoad.Release(materialHandle);
            if (clipsHandle.IsValid()) global::Meridian.Art.ArtLoad.Release(clipsHandle);
        }
    }
}
