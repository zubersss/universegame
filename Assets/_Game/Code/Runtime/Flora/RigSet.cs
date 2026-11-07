using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;

namespace Meridian.Flora
{
    /// <summary>
    /// U-097 (contract v3.0 §11.3): a planet's rig set, `flora/&lt;planet&gt;/rigset.json`: the parts on one sheet and the
    /// plants built from them (≤ 6 bones each, swap slots, a sway idle on the planet beat, a react within a radius).
    /// U-108 (contract v3.1, B-126 snoozle, D-101 no faces): a slot may replace its bone's own part (`replaces_part`),
    /// the idle may step a slot through a `swap_cycle` on the beat, and the react may show `also` parts on other slots.
    /// Pure data; parsed with JsonUtility plus small readers for the `swaps` and `also` maps it cannot read.
    /// </summary>
    [System.Serializable]
    public sealed class RigSet
    {
        public const int MaxBones = 6;

        [System.Serializable] public sealed class Part { public string name; public int[] rect; public float[] pivot; }
        /// <summary>`offset_m`: where the bone sits on its parent (m; default: the parent's tip, straight up); `order`: draw order within the plant (default: bone index).</summary>
        [System.Serializable] public sealed class Bone { public string name; public string part; public string parent; public float length = 0.5f; public float[] offset_m; public int order = -1; }
        /// <summary>
        /// A swap slot's anchor: the bone it hangs on, its offset (m) and draw order (B-112 json; optional). v3.1 (B-126, U-108):
        /// `replaces_part` true means the slot IS that bone's part: its states swap the bone's own sprite, no extra renderer
        /// (the bone's part must be one of the slot's swaps; offset and order are then the bone's).
        /// </summary>
        [System.Serializable] public sealed class Slot { public string slot; public string bone; public float[] offset_m; public int order = -1; public bool replaces_part; }

        /// <summary>
        /// U-103 (B-122, D-111): an authored keyframe clip, `frames` at `fps` stepped (12), per-bone `tracks`: `rot_deg`
        /// (local z degrees per frame, + = counter-clockwise) and `scale` ([x, y] per frame on the bone's local scale).
        /// A looping clip wraps to frame 0; a one-shot holds its last frame. Read with a small reader (JsonUtility has no maps).
        /// </summary>
        [System.Serializable]
        public sealed class Clip
        {
            public string name;
            public float fps = 12f;
            public bool loop;
            public int frames;
            [System.NonSerialized] public Dictionary<string, Track> tracks = new Dictionary<string, Track>();
            public float Seconds => frames / Mathf.Max(1f, fps);
        }

        public sealed class Track { public float[] rot_deg; public Vector2[] scale; }

        /// <summary>The Animator state of an authored clip: `&lt;plant&gt;_&lt;clip&gt;` (a sway-only plant's state is the plant's name).</summary>
        public static string StateName(string plant, string clip) => plant + "_" + clip;

        /// <summary>
        /// v3.1 `idle.swap_cycle` (B-126, U-108): `slot` steps through `sequence` on the plant's beat (60 / beat_bpm s), each
        /// entry held for its `beats` count, looping (the snoozle: head_open 8, head_half 1, head_closed 3, head_half 1 = 13 beats).
        /// </summary>
        [System.Serializable]
        public sealed class SwapCycle
        {
            public string slot;
            public string[] sequence;
            public int[] beats;

            /// <summary>True when the json carried no cycle (JsonUtility may hand back an empty instance for an absent object).</summary>
            public bool IsEmpty => string.IsNullOrEmpty(slot) && (sequence == null || sequence.Length == 0) && (beats == null || beats.Length == 0);
            public int TotalBeats => Total(beats);

            public static int Total(int[] beats)
            {
                int total = 0;
                if (beats != null) foreach (var b in beats) total += b;
                return total;
            }

            /// <summary>The sequence index showing `beatsElapsed` beats into the loop; see the static overload.</summary>
            public int IndexAt(float beatsElapsed) => IndexAt(beatsElapsed, beats, TotalBeats);

            /// <summary>
            /// The index showing `beatsElapsed` beats into a loop of `beats` (sum `totalBeats`): entry i holds for beats[i]
            /// whole beats, the index changes only on a beat boundary and wraps at the total. With beats [8, 1, 3, 1]: 0 on
            /// [0, 8), 1 on [8, 9), 2 on [9, 12), 3 on [12, 13), 0 again at 13. O(entries), no allocation (a LateUpdate path).
            /// </summary>
            public static int IndexAt(float beatsElapsed, int[] beats, int totalBeats)
            {
                if (beats == null || beats.Length == 0 || totalBeats <= 0) return 0;
                float t = Mathf.Repeat(beatsElapsed, totalBeats);
                for (int i = 0; i < beats.Length; i++) { t -= beats[i]; if (t < 0f) return i; }
                return beats.Length - 1; // Repeat may return exactly totalBeats: the last entry's final instant
            }
        }

        [System.Serializable]
        public sealed class Idle
        {
            public string type = "sway"; public float amplitude_deg = 10f; public float beat_bpm = 110f; public float squash = 0.08f; public SwapCycle swap_cycle;
            /// <summary>v3.2 (D-127): one swing of the sway spans this many beats (default 1: a swing per beat, the whole sway two beats, as every plant before it).</summary>
            public int cycle_beats = 1;
            /// <summary>v3.2 (B-136): the phase each bone trails its parent by, in radians of the sway (default 0.35, the whip every plant had).</summary>
            public float lag = DefaultLag;
            public const float DefaultLag = 0.35f;
            /// <summary>v3.2 (B-136): `amplitude_deg` as a bone → degrees object instead of one number; filled by Parse, null when the json gives a number.</summary>
            [System.NonSerialized] public Dictionary<string, float> amplitude_by_bone;
            public bool HasBoneAmplitudes => amplitude_by_bone != null && amplitude_by_bone.Count > 0;
            /// <summary>Seconds of one whole sway (two swings): 2 × cycle_beats beats. Pure.</summary>
            public float SwaySeconds => 2f * Mathf.Max(1, cycle_beats) * 60f / Mathf.Max(1f, beat_bpm);
            /// <summary>The bone's own amplitude from the map (0 for a bone the map leaves out: it stays still), or −1 when there is no map (the builder shares `amplitude_deg` down the chain).</summary>
            public float AmplitudeFor(string bone) => HasBoneAmplitudes ? (amplitude_by_bone.TryGetValue(bone, out var a) ? a : 0f) : -1f;
        }
        [System.Serializable]
        public sealed class React
        {
            public float radius_m = 3f;
            public string action = "turn_look";
            public string swap;
            /// <summary>v3.2 (B-136) `jaw_open`: the jaw bone's angle while reacting and the whole rig's tilt (degrees).</summary>
            public float jaw_deg = -20f, head_deg = 0f;
            /// <summary>v3.1 `also`: slot → the part it shows while reacting (the snoozle: leaves → leaves_up); filled by Parse from the json's `also` object.</summary>
            [System.NonSerialized] public Dictionary<string, string> also = new Dictionary<string, string>();
        }
        [System.Serializable]
        public sealed class Plant
        {
            public string name;
            /// <summary>U-110 (B-129): the biomes this plant grows in, in EarthBiomes' lower-case names (the ocean band's shore is "coast"); null or empty = anywhere.</summary>
            public string[] biomes;
            public Bone[] bones;
            public Slot[] slots;
            public Idle idle = new Idle();
            public React react = new React();
            /// <summary>U-103: authored clips (fin_wobble / leg_flex / hatch_open); null or empty for a sway-only plant.</summary>
            public Clip[] clips;
            /// <summary>U-103: named points in metres from the rig origin (the ground line under the pads, ship centre); they follow the root transform, not the clips. Filled by Parse from `sockets`.</summary>
            [System.NonSerialized] public Dictionary<string, Vector2> sockets = new Dictionary<string, Vector2>();
            public bool HasClips => clips != null && clips.Length > 0;
            public Clip FindClip(string name)
            {
                if (clips == null) return null;
                foreach (var c in clips) if (c != null && c.name == name) return c;
                return null;
            }
            /// <summary>Swap slots → part names (first = the resting state); filled by Parse from the json's `swaps` object.</summary>
            [System.NonSerialized] public Dictionary<string, string[]> swaps = new Dictionary<string, string[]>();
            public int BoneCount => bones != null ? bones.Length : 0;
            /// <summary>The idle's swap cycle, or null when the plant has none (U-108).</summary>
            public SwapCycle Cycle => idle != null && idle.swap_cycle != null && !idle.swap_cycle.IsEmpty ? idle.swap_cycle : null;

            public Slot FindSlot(string slot)
            {
                if (slots == null) return null;
                foreach (var s in slots) if (s != null && s.slot == slot) return s;
                return null;
            }

            public int BoneIndex(string bone)
            {
                if (bones == null || string.IsNullOrEmpty(bone)) return -1;
                for (int i = 0; i < bones.Length; i++) if (bones[i].name == bone) return i;
                return -1;
            }
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

        /// <summary>
        /// Null with `error` set when the json breaks §11.3 (no parts, no plants, a plant over 6 bones, a bone without a part,
        /// a swap naming a missing part) or its v3.1 additions (U-108): a `replaces_part` slot must name a bone of the plant
        /// whose part is one of the slot's swaps; a `swap_cycle` must name a swap slot, every sequence entry one of its
        /// swaps, with one beat count ≥ 1 per entry; every react `also` key must be a swap slot and its value one of its swaps.
        /// </summary>
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
                // v3.2 (D-127, B-136): amplitude_deg as a bone → degrees object, cycle_beats ≥ 1.
                plant.idle.amplitude_by_bone = ReadAmplitudes(json, plant.name);
                if (plant.idle.amplitude_by_bone != null)
                    foreach (var kv in plant.idle.amplitude_by_bone)
                        if (plant.BoneIndex(kv.Key) < 0) { error = $"plant '{plant.name}': amplitude_deg names an unknown bone '{kv.Key}'"; return null; }
                if (plant.idle.cycle_beats < 1) { error = $"plant '{plant.name}': idle.cycle_beats must be at least 1 (got {plant.idle.cycle_beats})"; return null; }
                foreach (var kv in plant.swaps)
                    foreach (var partName in kv.Value)
                        if (set.FindPart(partName) == null) { error = $"plant '{plant.name}': swap '{kv.Key}' names a missing part '{partName}'"; return null; }
                if (!string.IsNullOrEmpty(plant.react.swap) && set.FindPart(plant.react.swap) == null) { error = $"plant '{plant.name}': react swap names a missing part '{plant.react.swap}'"; return null; }

                // v3.1 (U-108, B-126): replaced-part slots, the idle swap cycle, the react's `also` map.
                if (plant.slots != null)
                    foreach (var s in plant.slots)
                    {
                        if (s == null || !s.replaces_part) continue;
                        if (string.IsNullOrEmpty(s.slot)) { error = $"plant '{plant.name}': a replaces_part slot needs a slot name"; return null; }
                        int bi = plant.BoneIndex(s.bone);
                        if (bi < 0) { error = $"plant '{plant.name}': slot '{s.slot}' replaces the part of an unknown bone '{s.bone}'"; return null; }
                        if (!plant.swaps.TryGetValue(s.slot, out var states) || states.Length == 0) { error = $"plant '{plant.name}': slot '{s.slot}' replaces a part but has no swaps"; return null; }
                        if (System.Array.IndexOf(states, plant.bones[bi].part) < 0) { error = $"plant '{plant.name}': slot '{s.slot}' replaces bone '{s.bone}' whose part '{plant.bones[bi].part}' is not among its swaps"; return null; }
                    }
                var cycle = plant.idle.swap_cycle;
                if (cycle != null && !cycle.IsEmpty)
                {
                    if (string.IsNullOrEmpty(cycle.slot) || !plant.swaps.TryGetValue(cycle.slot, out var states)) { error = $"plant '{plant.name}': swap_cycle slot '{cycle.slot}' is not a swap slot"; return null; }
                    if (cycle.sequence == null || cycle.sequence.Length == 0) { error = $"plant '{plant.name}': swap_cycle needs a sequence"; return null; }
                    foreach (var entry in cycle.sequence)
                        if (System.Array.IndexOf(states, entry) < 0) { error = $"plant '{plant.name}': swap_cycle entry '{entry}' is not a '{cycle.slot}' swap"; return null; }
                    int beatCount = cycle.beats != null ? cycle.beats.Length : 0;
                    if (beatCount != cycle.sequence.Length) { error = $"plant '{plant.name}': swap_cycle has {cycle.sequence.Length} entries but {beatCount} beats (one count per entry)"; return null; }
                    foreach (var beat in cycle.beats)
                        if (beat < 1) { error = $"plant '{plant.name}': swap_cycle beats must be at least 1 (got {beat})"; return null; }
                }
                plant.react.also = ReadAlso(json, plant.name);
                if (string.IsNullOrEmpty(plant.react.swap))
                    foreach (var kv in ReadReactSwapObject(json, plant.name)) plant.react.also[kv.Key] = kv.Value; // B-136 writes the react's `swap` as a slot → part object
                foreach (var kv in plant.react.also)
                {
                    if (!plant.swaps.TryGetValue(kv.Key, out var states)) { error = $"plant '{plant.name}': react also names '{kv.Key}', not a swap slot"; return null; }
                    if (System.Array.IndexOf(states, kv.Value) < 0) { error = $"plant '{plant.name}': react also shows '{kv.Value}', not a '{kv.Key}' swap"; return null; }
                }

                // U-103 (B-122): sockets and authored clips.
                plant.sockets = ReadSockets(json, plant.name);
                if (plant.clips != null)
                    foreach (var c in plant.clips)
                    {
                        if (c == null || string.IsNullOrEmpty(c.name)) { error = $"plant '{plant.name}': a clip needs a name"; return null; }
                        if (c.frames < 1) { error = $"plant '{plant.name}': clip '{c.name}' needs frames ≥ 1"; return null; }
                        if (c.fps <= 0f) c.fps = 12f;
                        c.tracks = ReadTracks(json, plant.name, c.name);
                        foreach (var kv in c.tracks)
                        {
                            if (plant.BoneIndex(kv.Key) < 0) { error = $"plant '{plant.name}': clip '{c.name}' drives an unknown bone '{kv.Key}'"; return null; }
                            var t = kv.Value;
                            if ((t.rot_deg == null || t.rot_deg.Length == 0) && (t.scale == null || t.scale.Length == 0)) { error = $"plant '{plant.name}': clip '{c.name}' track '{kv.Key}' has neither rot_deg nor scale"; return null; }
                        }
                    }
            }
            return set;
        }

        /// <summary>
        /// The span of the plant object named `plant` in `json`: from its `"name": "…", "bones"` to the next plant's "bones"
        /// (or the end). False when the plant is not found. The readers below scan only inside it (JsonUtility has no dictionaries).
        /// </summary>
        static bool PlantSpan(string json, string plant, out int start, out int end)
        {
            // U-109 check fix (B-129): the plant object is found by its exact name inside `plants` whatever its key order (B-129
            // writes `biomes` before `bones`) and spans its own braces, so a part named `<plant>_<x>` in `parts` never matches.
            start = end = -1;
            if (string.IsNullOrEmpty(plant)) return false;
            int plantsAt = json.IndexOf("\"plants\"", System.StringComparison.Ordinal);
            int from = plantsAt >= 0 ? plantsAt : 0;
            var nameMatch = Regex.Match(json.Substring(from), "\"name\"\\s*:\\s*\"" + Regex.Escape(plant) + "\"");
            if (!nameMatch.Success) return false;
            int at = from + nameMatch.Index;
            int open = -1, depth = 0;
            for (int i = at; i >= 0; i--)
            {
                if (json[i] == '}') depth++;
                else if (json[i] == '{') { if (depth == 0) { open = i; break; } depth--; }
            }
            int close = open >= 0 ? Matching(json, open, '{', '}') : -1;
            if (close < 0) return false;
            start = open;
            end = close + 1;
            return true;
        }

        /// <summary>The body of the flat object at the first `"key"` in [from, end): between its '{' and the first '}' after it (it nests nothing); null when absent.</summary>
        static string FlatObjectBody(string json, string key, int from, int end)
        {
            int at = json.IndexOf("\"" + key + "\"", from, System.StringComparison.Ordinal);
            if (at < 0 || at >= end) return null;
            int open = json.IndexOf('{', at);
            int close = open >= 0 ? json.IndexOf('}', open) : -1;
            if (open < 0 || close < 0) return null;
            return json.Substring(open + 1, close - open - 1);
        }

        /// <summary>Reads `"swaps": { "slot": ["a", "b"], ... }` of the plant object named `plant`.</summary>
        static Dictionary<string, string[]> ReadSwaps(string json, string plant)
        {
            var result = new Dictionary<string, string[]>();
            if (!PlantSpan(json, plant, out int start, out int end)) return result;
            var body = FlatObjectBody(json, "swaps", start, end); // the swaps object holds only arrays: its first '}' closes it
            if (body == null) return result;
            foreach (Match m in Regex.Matches(body, "\"([^\"]+)\"\\s*:\\s*\\[([^\\]]*)\\]"))
            {
                var names = new List<string>();
                foreach (Match n in Regex.Matches(m.Groups[2].Value, "\"([^\"]+)\"")) names.Add(n.Groups[1].Value);
                result[m.Groups[1].Value] = names.ToArray();
            }
            return result;
        }

        /// <summary>v3.2 (B-136): `"idle": { "amplitude_deg": { "head": 2, ... } }` of the plant — bone → degrees; null when amplitude_deg is a number or absent.</summary>
        static Dictionary<string, float> ReadAmplitudes(string json, string plant)
        {
            if (!PlantSpan(json, plant, out int start, out int end)) return null;
            int idleAt = json.IndexOf("\"idle\"", start, System.StringComparison.Ordinal);
            if (idleAt < 0 || idleAt >= end) return null;
            var body = ObjectBodyAfter(json, "amplitude_deg", idleAt, end);
            if (body == null) return null;
            var result = new Dictionary<string, float>();
            foreach (Match m in Regex.Matches(body, "\"([^\"]+)\"\\s*:\\s*(-?[0-9]+(?:\\.[0-9]+)?)"))
                if (float.TryParse(m.Groups[2].Value, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float v)) result[m.Groups[1].Value] = v;
            return result.Count > 0 ? result : null;
        }

        /// <summary>v3.2 (B-136): the react's `"swap": { "slot": "part" }` object of the plant (empty when `swap` is a string or absent).</summary>
        static Dictionary<string, string> ReadReactSwapObject(string json, string plant)
        {
            var result = new Dictionary<string, string>();
            if (!PlantSpan(json, plant, out int start, out int end)) return result;
            int reactAt = json.IndexOf("\"react\"", start, System.StringComparison.Ordinal);
            if (reactAt < 0 || reactAt >= end) return result;
            var body = ObjectBodyAfter(json, "swap", reactAt, end);
            if (body == null) return result;
            foreach (Match m in Regex.Matches(body, "\"([^\"]+)\"\\s*:\\s*\"([^\"]+)\"")) result[m.Groups[1].Value] = m.Groups[2].Value;
            return result;
        }

        /// <summary>The body of `"key": { ... }` at the first `key` in [from, end) whose value is a flat object (a number or string value → null).</summary>
        static string ObjectBodyAfter(string json, string key, int from, int end)
        {
            int at = json.IndexOf("\"" + key + "\"", from, System.StringComparison.Ordinal);
            if (at < 0 || at >= end) return null;
            int i = at + key.Length + 2;
            while (i < end && (char.IsWhiteSpace(json[i]) || json[i] == ':')) i++;
            if (i >= end || json[i] != '{') return null;
            int close = json.IndexOf('}', i);
            if (close < 0 || close > end) return null;
            return json.Substring(i + 1, close - i - 1);
        }

        /// <summary>U-103: reads `"sockets": { "name": [x, y], ... }` of the plant object named `plant` (metres from the rig origin).</summary>
        static Dictionary<string, Vector2> ReadSockets(string json, string plant)
        {
            var result = new Dictionary<string, Vector2>();
            if (!PlantSpan(json, plant, out int start, out int end)) return result;
            var body = FlatObjectBody(json, "sockets", start, end);
            if (body == null) return result;
            foreach (Match m in Regex.Matches(body, "\"([^\"]+)\"\\s*:\\s*\\[([^\\]]*)\\]"))
            {
                var v = Floats(m.Groups[2].Value);
                if (v.Length == 2) result[m.Groups[1].Value] = new Vector2(v[0], v[1]);
            }
            return result;
        }

        /// <summary>
        /// U-103: reads `"tracks": { "bone": { "rot_deg": [...], "scale": [[x, y], ...] }, ... }` of the clip named `clip` inside
        /// the `clips` array of the plant object named `plant`. Braces and brackets are matched by counting (no string holds one).
        /// </summary>
        static Dictionary<string, Track> ReadTracks(string json, string plant, string clip)
        {
            var result = new Dictionary<string, Track>();
            if (!PlantSpan(json, plant, out int start, out int end)) return result;
            int clipsAt = json.IndexOf("\"clips\"", start, System.StringComparison.Ordinal);
            if (clipsAt < 0 || clipsAt >= end) return result;
            var nameMatch = Regex.Match(json.Substring(clipsAt, end - clipsAt), "\"name\"\\s*:\\s*\"" + Regex.Escape(clip) + "\"");
            if (!nameMatch.Success) return result;
            int tracksAt = json.IndexOf("\"tracks\"", clipsAt + nameMatch.Index, System.StringComparison.Ordinal);
            if (tracksAt < 0 || tracksAt >= end) return result;
            int open = json.IndexOf('{', tracksAt);
            int close = Matching(json, open, '{', '}');
            if (open < 0 || close < 0) return result;
            int i = open + 1;
            while (i < close)
            {
                var bm = Regex.Match(json.Substring(i, close - i), "\"([^\"]+)\"\\s*:\\s*\\{");
                if (!bm.Success) break;
                int bOpen = i + bm.Index + bm.Length - 1;
                int bClose = Matching(json, bOpen, '{', '}');
                if (bClose < 0) break;
                var body = json.Substring(bOpen + 1, bClose - bOpen - 1);
                var t = new Track();
                var rot = Regex.Match(body, "\"rot_deg\"\\s*:\\s*\\[([^\\]]*)\\]");
                if (rot.Success) t.rot_deg = Floats(rot.Groups[1].Value);
                int scaleAt = body.IndexOf("\"scale\"", System.StringComparison.Ordinal);
                if (scaleAt >= 0)
                {
                    int sOpen = body.IndexOf('[', scaleAt);
                    int sClose = Matching(body, sOpen, '[', ']');
                    if (sOpen >= 0 && sClose > sOpen)
                    {
                        var pairs = new List<Vector2>();
                        foreach (Match pm in Regex.Matches(body.Substring(sOpen + 1, sClose - sOpen - 1), "\\[([^\\]]*)\\]"))
                        {
                            var v = Floats(pm.Groups[1].Value);
                            pairs.Add(v.Length >= 2 ? new Vector2(v[0], v[1]) : v.Length == 1 ? new Vector2(v[0], v[0]) : Vector2.one);
                        }
                        t.scale = pairs.ToArray();
                    }
                }
                result[bm.Groups[1].Value] = t;
                i = bClose + 1;
            }
            return result;
        }

        /// <summary>Index of the `close` matching the `open` at `at` (depth counting), or -1.</summary>
        static int Matching(string s, int at, char open, char close)
        {
            if (at < 0 || at >= s.Length || s[at] != open) return -1;
            int depth = 0;
            for (int i = at; i < s.Length; i++)
            {
                if (s[i] == open) depth++;
                else if (s[i] == close && --depth == 0) return i;
            }
            return -1;
        }

        static float[] Floats(string list)
        {
            var parts = list.Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries);
            var result = new List<float>(parts.Length);
            foreach (var p in parts)
                if (float.TryParse(p.Trim(), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float f)) result.Add(f);
            return result.ToArray();
        }

        /// <summary>U-108: reads `"react": { ..., "also": { "slot": "part", ... } }` of the plant object named `plant` (v3.1; flat string → string).</summary>
        static Dictionary<string, string> ReadAlso(string json, string plant)
        {
            var result = new Dictionary<string, string>();
            if (!PlantSpan(json, plant, out int start, out int end)) return result;
            int reactAt = json.IndexOf("\"react\"", start, System.StringComparison.Ordinal);
            if (reactAt < 0 || reactAt >= end) return result;
            var body = FlatObjectBody(json, "also", reactAt, end);
            if (body == null) return result;
            foreach (Match m in Regex.Matches(body, "\"([^\"]+)\"\\s*:\\s*\"([^\"]+)\"")) result[m.Groups[1].Value] = m.Groups[2].Value;
            return result;
        }
    }
}
