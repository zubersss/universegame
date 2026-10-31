using System.Collections.Generic;
using UnityEngine;

namespace Meridian.Rendering
{
    /// <summary>
    /// Which material an art key draws with (U-019). ArtImporter records every key that has an
    /// `_emission` map; renderers ask MaterialFor(key) and get Sprite_LitEmissive for those,
    /// Sprite-Lit-Default otherwise. Lives in Resources so tools and tests find it without Core.
    /// </summary>
    [CreateAssetMenu(menuName = "MERIDIAN/Art Materials", fileName = "ArtMaterials")]
    public sealed class ArtMaterials : ScriptableObject
    {
        public const string ResourceName = "ArtMaterials";

        public Material lit;
        public Material litEmissive;
        public List<string> emissiveKeys = new List<string>();
        /// <summary>Animation clips of frame sheets (U-032), copied from each sheet's .json by ArtImporter.</summary>
        public List<ArtClipSet> clipSets = new List<ArtClipSet>();

        static ArtMaterials active;
        static HashSet<string> lookup;

        public static ArtMaterials Active
        {
            get
            {
                if (active == null) active = Resources.Load<ArtMaterials>(ResourceName);
                return active;
            }
        }

        public bool IsEmissive(string key)
        {
            if (lookup == null || lookup.Count != emissiveKeys.Count) lookup = new HashSet<string>(emissiveKeys);
            return lookup.Contains(key);
        }

        /// <summary>The material for a key, or null when the registry is missing (renderer keeps its default).</summary>
        public static Material MaterialFor(string key)
        {
            var a = Active;
            if (a == null) return null;
            return a.IsEmissive(key) && a.litEmissive != null ? a.litEmissive : a.lit;
        }

        /// <summary>The clips of a frame sheet key, or null (no sheet, or no registry).</summary>
        public static ArtClipSet ClipsFor(string key)
        {
            var a = Active;
            if (a == null) return null;
            foreach (var s in a.clipSets) if (s.key == key) return s;
            return null;
        }

        /// <summary>Editor: called by ArtImporter with a sheet's clips. Returns true when they changed.</summary>
        public bool SetClips(string key, int fps, List<ArtClip> clips)
        {
            int i = clipSets.FindIndex(s => s.key == key);
            if (clips == null || clips.Count == 0)
            {
                if (i < 0) return false;
                clipSets.RemoveAt(i);
                return true;
            }
            var set = new ArtClipSet { key = key, fps = fps, clips = clips };
            if (i >= 0 && JsonUtility.ToJson(clipSets[i]) == JsonUtility.ToJson(set)) return false;
            if (i >= 0) clipSets[i] = set; else clipSets.Add(set);
            clipSets.Sort((a, b) => string.CompareOrdinal(a.key, b.key));
            return true;
        }

        /// <summary>Editor: called by ArtImporter. Returns true when the list changed.</summary>
        public bool SetEmissive(string key, bool emissive)
        {
            bool has = emissiveKeys.Contains(key);
            if (has == emissive) return false;
            if (emissive) emissiveKeys.Add(key); else emissiveKeys.Remove(key);
            emissiveKeys.Sort(System.StringComparer.Ordinal);
            lookup = null;
            return true;
        }
    }
}

namespace Meridian.Rendering
{
    /// <summary>One animation clip of a frame sheet: frames start..start+length-1 (contract §5).</summary>
    [System.Serializable]
    public struct ArtClip
    {
        public string name;
        public int start, length;
        public bool loop;
    }

    [System.Serializable]
    public sealed class ArtClipSet
    {
        public string key;
        public int fps = 12;
        public List<ArtClip> clips = new List<ArtClip>();

        public bool TryGet(string name, out ArtClip clip)
        {
            for (int i = 0; i < clips.Count; i++) if (clips[i].name == name) { clip = clips[i]; return true; }
            clip = default;
            return false;
        }
    }
}
