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
            var locs = Addressables.LoadResourceLocationsAsync(key, typeof(GameObject));
            locs.Completed += l =>
            {
                // The key also addresses its 2D placeholder and its material: load the model and its clip sub-assets
                // from the GameObject location itself, never by the bare key.
                IResourceLocation modelLoc = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0 ? l.Result[0] : null;
                Addressables.Release(l);
                if (modelLoc == null || this == null) return; // no model: the caller keeps its 2D view
                pending = 3;
                modelHandle = Addressables.LoadAssetAsync<GameObject>(modelLoc);
                modelHandle.Completed += op => { prefab = op.Status == AsyncOperationStatus.Succeeded ? op.Result : null; Done(); };
                clipsHandle = Addressables.LoadAssetAsync<IList<AnimationClip>>(modelLoc);
                clipsHandle.Completed += op => { clips = op.Status == AsyncOperationStatus.Succeeded ? op.Result : null; Done(); };
                LoadOptional(key, typeof(Material), () =>
                {
                    materialHandle = Addressables.LoadAssetAsync<Material>(key);
                    materialHandle.Completed += op => { material = op.Status == AsyncOperationStatus.Succeeded ? op.Result : null; Done(); };
                });
            };
        }

        void LoadOptional(string key, System.Type type, System.Action load)
        {
            var locs = Addressables.LoadResourceLocationsAsync(key, type);
            locs.Completed += l =>
            {
                bool has = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                Addressables.Release(l);
                if (has && this != null) load(); else Done();
            };
        }

        void Done()
        {
            if (--pending > 0 || this == null || prefab == null) return;
            Instance = Instantiate(prefab, transform, false);
            Instance.transform.localPosition = Vector3.zero;
            renderers = Instance.GetComponentsInChildren<Renderer>();
            if (material != null) foreach (var r in renderers) r.sharedMaterial = material;
            block = new MaterialPropertyBlock();
            BuildGraph();
            Ready = true;
            SetFacing(facingRight);
            Loaded?.Invoke();
        }

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
            if (name == Current) return true;
            if (!playables.TryGetValue(name, out var p)) return false;
            Current = name;
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

        void LateUpdate()
        {
            if (!Ready) return;
            // One-shots hold their last frame (Mecanim import loops every clip; the json says which ones don't).
            if (!playingLoops && playing.IsValid() && playing.GetTime() >= playingLength)
            {
                playing.SetTime(Mathf.Max(0f, playingLength - 0.001f));
                playing.SetSpeed(0);
            }
            bool flashing = Time.time < flashUntil;
            if (flashing != flashShown && renderers != null)
            {
                flashShown = flashing;
                foreach (var r in renderers)
                {
                    r.GetPropertyBlock(block);
                    if (flashing) block.SetColor(EmissionId, new Color(2f, 1.6f, 1.4f)); else block.Clear();
                    r.SetPropertyBlock(block);
                }
            }
        }

        bool flashShown;

        void OnDestroy()
        {
            if (graph.IsValid()) graph.Destroy();
            if (modelHandle.IsValid()) Addressables.Release(modelHandle);
            if (materialHandle.IsValid()) Addressables.Release(materialHandle);
            if (clipsHandle.IsValid()) Addressables.Release(clipsHandle);
        }
    }
}
