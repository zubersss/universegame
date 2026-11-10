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
        /// <summary>Self-lit sprites (fx glows, U-033); set by scene authoring so builds include the shader.</summary>
        public Material unlit;
        /// <summary>U-072 (Bible 2.0 §10.5): URP/Lit for 3D models and placeholder meshes; the emissive variant has emission on.</summary>
        public Material meshLit;
        public Material meshLitEmissive;
        /// <summary>U-073: MERIDIAN/TerrainBlocks (block mesh, Texture2DArray per planet); referenced here so builds keep the shader.</summary>
        public Material terrainBlocks;
        /// <summary>U-100: the flat ink-outlined silhouette every 3D model wears on the cartoon path (MERIDIAN/CartoonSilhouette).</summary>
        public Material cartoon;
        /// <summary>U-117: MERIDIAN/Sprite_LitDisc for the painted planet discs and moons (planets/*/disc, luna): the limb resolved at the sampled alpha's iso-line, so the 64-px frames' hard edge is a smooth contour at the near-range zoom, not texel stairs.</summary>
        public Material disc;
        /// <summary>U-182: MERIDIAN/GroundTiers, the smooth ground's fill by depth tier (B-203's ground_fill_t2..t5 under the Surface Line).</summary>
        public Material groundTiers;
        /// <summary>U-073 / B-080: block material textures per planet (ArtImporter fills it; the arrays are built at runtime).</summary>
        public List<BlockTexture> blockTextures = new List<BlockTexture>();

        [System.Serializable]
        public sealed class BlockTexture
        {
            public string planet;   // "earth"
            public string material; // "soil" … or "backwall"
            public string face;     // "top", "side" or "wall"
            public Texture2D color, normal, mask;
        }

        /// <summary>The registered block texture for a planet/material/face, or null.</summary>
        public BlockTexture FindBlock(string planet, string material, string face)
        {
            foreach (var b in blockTextures)
                if (b != null && b.planet == planet && b.material == material && b.face == face) return b;
            return null;
        }
        public List<string> emissiveKeys = new List<string>();
        /// <summary>U-164 (D-169): painted-set layers (backgrounds/.../layer&lt;n&gt;) whose bottom strip is opaque, so the stage may repeat it below the
        /// layer's bottom edge (ArtImporter.RecordOpaqueBottoms reads the source PNGs at import).</summary>
        public List<string> opaqueBottoms = new List<string>();
        public static bool OpaqueBottom(string layerKey) { var a = Active; return a != null && layerKey != null && a.opaqueBottoms.Contains(layerKey); }
        /// <summary>Animation clips of frame sheets (U-032), copied from each sheet's .json by ArtImporter.</summary>
        public List<ArtClipSet> clipSets = new List<ArtClipSet>();

        /// <summary>U-183: a json's named point(s), copied by ArtImporter.RegisterSockets: a tool's muzzle / cable_socket ([x, y] m from its
        /// pivot, stride 2), the jetpack's back_socket per surveyor frame ([x, z, swing rad, sx, sz], stride 5, NaN where the json says null).</summary>
        [System.Serializable]
        public sealed class ArtSocket
        {
            public string key, name;
            public int stride;
            public float[] values;
            public int Count => stride > 0 && values != null ? values.Length / stride : 0;
            public bool Has(int i) => i >= 0 && i < Count && !float.IsNaN(values[i * stride]);
            public float this[int i, int c] => values[i * stride + c];
        }
        public List<ArtSocket> sockets = new List<ArtSocket>();
        static Dictionary<(string, string), ArtSocket> socketLookup;
        static int socketLookupCount = -1;

        /// <summary>A key's named socket, or null (no json field, or no registry). No allocation: the lookup's key is the pair itself
        /// (it was the two joined into a new string each call: 88 B a frame from the Beam's cable alone, read every frame; found
        /// by Unity's allocation counter, 08:2x).</summary>
        public static ArtSocket SocketFor(string key, string name)
        {
            var a = Active;
            if (a == null || a.sockets == null || key == null) return null;
            if (socketLookup == null || socketLookupCount != a.sockets.Count)
            {
                socketLookup = new Dictionary<(string, string), ArtSocket>(a.sockets.Count);
                foreach (var s in a.sockets) if (s != null) socketLookup[(s.key, s.name)] = s;
                socketLookupCount = a.sockets.Count;
            }
            return socketLookup.TryGetValue((key, name), out var found) ? found : null;
        }

        /// <summary>A tool's [x, y] socket, or `fallback` where the json has none.</summary>
        public static Vector2 PointFor(string key, string name, Vector2 fallback)
        {
            var s = SocketFor(key, name);
            return s != null && s.stride >= 2 && s.Has(0) ? new Vector2(s[0, 0], s[0, 1]) : fallback;
        }

        /// <summary>Editor: ArtImporter records a json's socket. Returns true when it changed.</summary>
        public bool SetSocket(string key, string name, int stride, float[] values)
        {
            sockets ??= new List<ArtSocket>();
            int i = sockets.FindIndex(s => s.key == key && s.name == name);
            if (values == null || values.Length == 0)
            {
                if (i < 0) return false;
                sockets.RemoveAt(i);
                return true;
            }
            var set = new ArtSocket { key = key, name = name, stride = stride, values = values };
            if (i >= 0 && JsonUtility.ToJson(sockets[i]) == JsonUtility.ToJson(set)) return false;
            if (i >= 0) sockets[i] = set; else sockets.Add(set);
            sockets.Sort((x, y) => string.CompareOrdinal(x.key + "#" + x.name, y.key + "#" + y.name));
            socketLookupCount = -1;
            return true;
        }

        /// <summary>D-190 (1): a ground fill's main tone (its json's "tone_hex": the fill's opaque pixels snapped to the planet's palette,
        /// the tone with the largest share). The dig's clods and dust are coloured by the fill drawn at the dug cell. ArtTones registers
        /// them from the jsons (CheckSetup, or -ExecuteMethod Meridian.EditorTools.ArtTones.Run).</summary>
        [System.Serializable]
        public sealed class ArtTone
        {
            public string key;
            public Color32 color;
        }
        public List<ArtTone> tones = new List<ArtTone>();
        static Dictionary<string, Color> toneLookup;
        static int toneLookupCount = -1;

        /// <summary>A key's registered tone; false where its json has none (or no registry).</summary>
        public static bool ToneFor(string key, out Color tone)
        {
            tone = Color.white;
            var a = Active;
            if (a == null || a.tones == null || key == null) return false;
            if (toneLookup == null || toneLookupCount != a.tones.Count)
            {
                toneLookup = new Dictionary<string, Color>(a.tones.Count);
                foreach (var t in a.tones) if (t != null && t.key != null) toneLookup[t.key] = t.color;
                toneLookupCount = a.tones.Count;
            }
            return toneLookup.TryGetValue(key, out tone);
        }

        /// <summary>Editor: ArtTones records a json's tone (null: the field is gone). Returns true when it changed.</summary>
        public bool SetTone(string key, Color32? color)
        {
            tones ??= new List<ArtTone>();
            int i = tones.FindIndex(t => t.key == key);
            if (color == null)
            {
                if (i < 0) return false;
                tones.RemoveAt(i);
                toneLookupCount = -1;
                return true;
            }
            var c = color.Value;
            if (i >= 0 && tones[i].color.r == c.r && tones[i].color.g == c.g && tones[i].color.b == c.b && tones[i].color.a == c.a) return false;
            if (i >= 0) tones[i].color = c; else tones.Add(new ArtTone { key = key, color = c });
            tones.Sort((x, y) => string.CompareOrdinal(x.key, y.key));
            toneLookupCount = -1;
            toneLookup = null;
            return true;
        }

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

        /// <summary>U-117: a painted disc or moon key (planets/&lt;name&gt;/disc, planets/&lt;name&gt;/luna); rings and rig sets keep the plain lit material.</summary>
        public static bool IsDiscKey(string key) =>
            key != null && key.StartsWith("planets/", System.StringComparison.Ordinal)
            && (key.EndsWith("/disc", System.StringComparison.Ordinal) || key.EndsWith("/luna", System.StringComparison.Ordinal));

        /// <summary>The material for a key, or null when the registry is missing (renderer keeps its default).</summary>
        public static Material MaterialFor(string key)
        {
            var a = Active;
            if (a == null) return null;
            if (a.disc != null && IsDiscKey(key)) return a.disc;
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

        /// <summary>U-075: clips of 3D models (from each model's json: name, frames, loop, fps), kept apart from sheet clips.</summary>
        public List<ArtClipSet> modelClipSets = new List<ArtClipSet>();

        /// <summary>The clips of a model key (start 0, length = frames), or null.</summary>
        public static ArtClipSet ModelClipsFor(string key)
        {
            var a = Active;
            if (a == null || a.modelClipSets == null) return null;
            foreach (var s in a.modelClipSets) if (s.key == key) return s;
            return null;
        }

        /// <summary>Editor: ArtImporter v9 records a model's clips. Returns true when they changed.</summary>
        public bool SetModelClips(string key, int fps, List<ArtClip> clips)
        {
            modelClipSets ??= new List<ArtClipSet>();
            int i = modelClipSets.FindIndex(s => s.key == key);
            if (clips == null || clips.Count == 0)
            {
                if (i < 0) return false;
                modelClipSets.RemoveAt(i);
                return true;
            }
            var set = new ArtClipSet { key = key, fps = fps, clips = clips };
            if (i >= 0 && JsonUtility.ToJson(modelClipSets[i]) == JsonUtility.ToJson(set)) return false;
            if (i >= 0) modelClipSets[i] = set; else modelClipSets.Add(set);
            modelClipSets.Sort((a, b) => string.CompareOrdinal(a.key, b.key));
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
        /// <summary>U-209 (B-246's side_dig): the drawing inside the clip on which a swing makes its contact (its json's "contact",
        /// 0-based; 0 where the json gives none) and how far the tool may slide back through the glove on it (its "slide_max", m).</summary>
        public int contact;
        public float slideMax;
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
