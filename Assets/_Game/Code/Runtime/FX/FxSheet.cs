using System.Collections.Generic;
using Meridian.Rendering;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.FX
{
    /// <summary>
    /// U-033: one fx frame sheet (fx/&lt;name&gt;/base) loaded once and shared: its frames in index order,
    /// its first clip (range, loop, fps from the sheet's .json via the ArtMaterials registry) and its
    /// material (Sprite_LitEmissive when it has an emission map). Missing art just never becomes Ready.
    /// </summary>
    public sealed class FxSheet
    {
        public readonly string key;
        public Sprite[] frames;
        public ArtClip clip;
        public int fps = 12;
        public Material material;
        public bool Ready => frames != null;

        static readonly Dictionary<string, FxSheet> cache = new Dictionary<string, FxSheet>();

        FxSheet(string key) { this.key = key; }

        public static FxSheet Get(string key)
        {
            if (cache.TryGetValue(key, out var s)) return s;
            s = new FxSheet(key);
            cache[key] = s;
            s.Load();
            return s;
        }

        /// <summary>The frame of the clip `seconds` after it started; -1 once a one-shot clip has finished.</summary>
        public int FrameAt(float seconds)
        {
            int step = (int)(seconds * fps);
            if (clip.loop) return clip.start + step % clip.length;
            return step < clip.length ? clip.start + step : -1;
        }

        void Load()
        {
            var set = ArtMaterials.ClipsFor(key);
            if (set != null && set.clips.Count > 0) { clip = set.clips[0]; fps = set.fps; }
            material = ArtMaterials.MaterialFor(key);
            var loc = Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                Addressables.Release(l);
                if (!exists) return;
                Addressables.LoadAssetAsync<IList<Sprite>>(key).Completed += op =>
                {
                    if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    var list = new Sprite[op.Result.Count];
                    foreach (var sp in op.Result)
                    {
                        int u = sp.name.LastIndexOf('_');
                        if (u >= 0 && int.TryParse(sp.name.Substring(u + 1), out int n) && n >= 0 && n < list.Length) list[n] = sp;
                    }
                    for (int i = 0; i < list.Length; i++) if (list[i] == null) list[i] = op.Result[0];
                    if (clip.length <= 0) clip = new ArtClip { name = "all", start = 0, length = list.Length, loop = true };
                    frames = list; // kept for the session: fx sheets are small and shared by every scene
                };
            };
        }
    }
}
