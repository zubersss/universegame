using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;

namespace Meridian.Flora
{
    /// <summary>
    /// U-097 (contract v3.0 §11.3): a planet's rig set, `flora/&lt;planet&gt;/rigset.json`: the parts on one sheet and the
    /// plants built from them (≤ 6 bones each, face swaps, a sway idle on the planet beat, a react within a radius).
    /// Pure data; parsed with JsonUtility plus a small reader for the `swaps` map it cannot read.
    /// </summary>
    [System.Serializable]
    public sealed class RigSet
    {
        public const int MaxBones = 6;

        [System.Serializable] public sealed class Part { public string name; public int[] rect; public float[] pivot; }
        /// <summary>`offset_m`: where the bone sits on its parent (m; default: the parent's tip, straight up); `order`: draw order within the plant (default: bone index).</summary>
        [System.Serializable] public sealed class Bone { public string name; public string part; public string parent; public float length = 0.5f; public float[] offset_m; public int order = -1; }
        /// <summary>A face swap slot's anchor: the bone it hangs on, its offset (m) and draw order (B-112 json; optional).</summary>
        [System.Serializable] public sealed class Slot { public string slot; public string bone; public float[] offset_m; public int order = -1; }
        [System.Serializable] public sealed class Idle { public string type = "sway"; public float amplitude_deg = 10f; public float beat_bpm = 110f; public float squash = 0.08f; }
        [System.Serializable] public sealed class React { public float radius_m = 3f; public string action = "turn_look"; public string swap; }
        [System.Serializable]
        public sealed class Plant
        {
            public string name;
            public Bone[] bones;
            public Slot[] slots;
            public Idle idle = new Idle();
            public React react = new React();
            /// <summary>Face swap slots → part names (first = the resting face); filled by Parse from the json's `swaps` object.</summary>
            [System.NonSerialized] public Dictionary<string, string[]> swaps = new Dictionary<string, string[]>();
            public int BoneCount => bones != null ? bones.Length : 0;
        }

        public string key;
        public string style;
        public float ppu = 64f;
        public Part[] parts;
        public Plant[] plants;

        public Part FindPart(string name)
        {
            if (parts == null) return null;
            foreach (var p in parts) if (p.name == name) return p;
            return null;
        }

        public Plant FindPlant(string name)
        {
            if (plants == null) return null;
            foreach (var p in plants) if (p.name == name) return p;
            return null;
        }

        /// <summary>Null with `error` set when the json breaks §11.3 (no parts, no plants, a plant over 6 bones, a bone without a part, a swap naming a missing part).</summary>
        public static RigSet Parse(string json, out string error)
        {
            error = null;
            RigSet set;
            try { set = JsonUtility.FromJson<RigSet>(json); }
            catch (System.Exception e) { error = "invalid JSON: " + e.Message; return null; }
            if (set == null || set.parts == null || set.parts.Length == 0) { error = "no parts"; return null; }
            if (set.plants == null || set.plants.Length == 0) { error = "no plants"; return null; }
            foreach (var part in set.parts)
                if (string.IsNullOrEmpty(part.name) || part.rect == null || part.rect.Length != 4) { error = $"part '{part.name}' needs a name and rect [x, y, w, h]"; return null; }
            foreach (var plant in set.plants)
            {
                if (plant.BoneCount == 0) { error = $"plant '{plant.name}' has no bones"; return null; }
                if (plant.BoneCount > MaxBones) { error = $"plant '{plant.name}' has {plant.BoneCount} bones, over {MaxBones} (contract §11.3)"; return null; }
                foreach (var b in plant.bones)
                {
                    if (string.IsNullOrEmpty(b.name)) { error = $"plant '{plant.name}': a bone needs a name"; return null; }
                    if (!string.IsNullOrEmpty(b.part) && set.FindPart(b.part) == null) { error = $"plant '{plant.name}': bone '{b.name}' names a missing part '{b.part}'"; return null; }
                    if (!string.IsNullOrEmpty(b.parent) && System.Array.FindIndex(plant.bones, x => x.name == b.parent) < 0) { error = $"plant '{plant.name}': bone '{b.name}' has an unknown parent '{b.parent}'"; return null; }
                }
                if (plant.idle == null) plant.idle = new Idle();
                if (plant.react == null) plant.react = new React();
                plant.swaps = ReadSwaps(json, plant.name);
                foreach (var kv in plant.swaps)
                    foreach (var partName in kv.Value)
                        if (set.FindPart(partName) == null) { error = $"plant '{plant.name}': swap '{kv.Key}' names a missing part '{partName}'"; return null; }
                if (!string.IsNullOrEmpty(plant.react.swap) && set.FindPart(plant.react.swap) == null) { error = $"plant '{plant.name}': react swap names a missing part '{plant.react.swap}'"; return null; }
            }
            return set;
        }

        /// <summary>Reads `"swaps": { "slot": ["a", "b"], ... }` of the plant object named `plant` (JsonUtility has no dictionaries).</summary>
        static Dictionary<string, string[]> ReadSwaps(string json, string plant)
        {
            var result = new Dictionary<string, string[]>();
            if (string.IsNullOrEmpty(plant)) return result;
            var nameMatch = Regex.Match(json, "\"name\"\\s*:\\s*\"" + Regex.Escape(plant) + "\"\\s*,\\s*\"bones\"");
            if (!nameMatch.Success) return result;
            // This plant's swaps object: the first "swaps" after its name, before the next plant starts (its "bones" array).
            int swapsAt = json.IndexOf("\"swaps\"", nameMatch.Index, System.StringComparison.Ordinal);
            int nextPlant = json.IndexOf("\"bones\"", nameMatch.Index + nameMatch.Length, System.StringComparison.Ordinal);
            if (swapsAt < 0 || (nextPlant >= 0 && swapsAt > nextPlant)) return result;
            int open = json.IndexOf('{', swapsAt);
            int close = open >= 0 ? json.IndexOf('}', open) : -1; // the swaps object holds only arrays: its first '}' closes it
            if (open < 0 || close < 0) return result;
            var body = json.Substring(open + 1, close - open - 1);
            foreach (Match m in Regex.Matches(body, "\"([^\"]+)\"\\s*:\\s*\\[([^\\]]*)\\]"))
            {
                var names = new List<string>();
                foreach (Match n in Regex.Matches(m.Groups[2].Value, "\"([^\"]+)\"")) names.Add(n.Groups[1].Value);
                result[m.Groups[1].Value] = names.ToArray();
            }
            return result;
        }
    }
}
