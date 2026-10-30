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
