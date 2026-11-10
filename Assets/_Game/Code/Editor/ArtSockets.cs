using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-183: the art jsons' sockets into the ArtMaterials registry, so the game reads BLENDER's numbers, not code constants: a tool's muzzle and
    /// cable_socket (props/rig/*), the jetpack's back_socket / back_socket_b per surveyor frame, a sheet's hand_socket when BLENDER adds one.
    /// CheckSetup runs it (or -ExecuteMethod Meridian.EditorTools.ArtSockets.Run). JsonUtility reads no arrays of arrays, so a small parser
    /// reads the fields (numbers and nulls).
    /// </summary>
    public static class ArtSockets
    {
        public static readonly string[] Fields = { "muzzle", "cable_socket", "back_socket", "back_socket_b", "hand_socket", "hand_socket_b", "held_b", "reel", // U-176: side_b's reel (reel_up's hands)
            "blade_tip", "hand", // U-209: the shovel's blade tip; B-246's side_dig "hand" rows ([x, z, angle] a frame)
            "stow_socket" }; // U-212 (H8): props/rig/stow_socket: the stowed tool's grip end on the body and its direction, a frame of the side sheet
        const string ArtRoot = "Assets/_Game/Art/";

        [MenuItem("MERIDIAN/Art/Register sockets (U-183)")]
        public static void Run() => Register();

        public static int Register()
        {
            var reg = AssetDatabase.LoadAssetAtPath<Meridian.Rendering.ArtMaterials>(DiscSetup.RegistryPath);
            if (reg == null) { Debug.LogError("[MERIDIAN] ArtSockets: no ArtMaterials registry"); return 0; }
            int changed = 0, found = 0;
            var seen = new HashSet<string>();
            foreach (var dir in new[] { "props/rig", "characters/surveyor" })
            {
                if (!Directory.Exists(ArtRoot + dir)) continue;
                foreach (var path in Directory.GetFiles(ArtRoot + dir, "*.json"))
                {
                    string text = File.ReadAllText(path);
                    string key = dir + "/" + Path.GetFileNameWithoutExtension(path);
                    foreach (var field in Fields)
                    {
                        if (text.IndexOf("\"" + field + "\"", System.StringComparison.Ordinal) < 0) continue;
                        var values = Parse(text, field, out int stride);
                        if (values == null) continue;
                        found++;
                        seen.Add(key + "#" + field);
                        if (reg.SetSocket(key, field, stride, values)) changed++;
                    }
                    // U-209 (B-246's side_dig): the rest poses, each an object of numbers: [angle, swing, behind] in one row
                    foreach (var pose in Poses)
                    {
                        var values = ParseObject(text, pose, PoseFields);
                        if (values == null) continue;
                        found++;
                        seen.Add(key + "#" + pose);
                        if (reg.SetSocket(key, pose, PoseFields.Length, values)) changed++;
                    }
                }
            }
            // sockets whose json field is gone
            for (int i = reg.sockets.Count - 1; i >= 0; i--)
                if (!seen.Contains(reg.sockets[i].key + "#" + reg.sockets[i].name)) { reg.sockets.RemoveAt(i); changed++; }
            if (changed > 0) { EditorUtility.SetDirty(reg); AssetDatabase.SaveAssets(); }
            Debug.Log($"[MERIDIAN] ArtSockets: {found} sockets, {changed} changed");
            return changed;
        }

        /// <summary>A json field's numbers: [a, b] (stride 2), or [[...], null, [...]] (stride = the inner length, NaN for a null). Null when
        /// the field is missing or not an array. Pure.</summary>
        public static float[] Parse(string json, string field, out int stride)
        {
            stride = 0;
            int at = json.IndexOf("\"" + field + "\"", System.StringComparison.Ordinal);
            if (at < 0) return null;
            int i = json.IndexOf(':', at) + 1;
            while (i < json.Length && char.IsWhiteSpace(json[i])) i++;
            if (i >= json.Length || json[i] != '[') return null;
            int closeAll = Close(json, i);
            if (closeAll < 0) return null;
            string inner = json.Substring(i + 1, closeAll - i - 1);
            if (inner.IndexOf('[') >= 0)
            {
                // an array of arrays (or nulls)
                var rows = new List<float[]>();
                int depth = 0, k = i;
                for (; k < json.Length; k++)
                {
                    char c = json[k];
                    if (c == '[') { depth++; if (depth == 2) { int end = json.IndexOf(']', k); rows.Add(Numbers(json.Substring(k + 1, end - k - 1))); k = end; depth--; } }
                    else if (c == ']') { depth--; if (depth == 0) break; }
                    else if (depth == 1 && c == 'n' && string.CompareOrdinal(json, k, "null", 0, 4) == 0) { rows.Add(null); k += 3; }
                }
                foreach (var r in rows) if (r != null) { stride = r.Length; break; }
                if (stride == 0) return null;
                var all = new float[rows.Count * stride];
                for (int r = 0; r < rows.Count; r++)
                    for (int c = 0; c < stride; c++)
                        all[r * stride + c] = rows[r] != null && c < rows[r].Length ? rows[r][c] : float.NaN;
                return all;
            }
            // a flat list: numbers ([x, y]: stride its length), or one value a frame (held_b's names and nulls: stride 1, a name reads 1)
            var flat = Numbers(inner);
            bool perFrame = inner.IndexOf('"') >= 0 || inner.Contains("null");
            stride = perFrame ? 1 : flat.Length;
            return flat.Length > 0 ? flat : null;
        }

        /// <summary>U-209: the dig sheet's rest poses ("carry": stowed; "ready": low in front) and the numbers each holds, in the row's order.</summary>
        public static readonly string[] Poses = { "carry", "ready" };
        public static readonly string[] PoseFields = { "angle", "swing", "behind" };

        /// <summary>A json object's named numbers as one row (true reads 1, false 0, a missing field 0): "carry": {"angle": 2.18, "swing":
        /// 0.08, "behind": true} → [2.18, 0.08, 1]. Null when the json has no such object, or it has none of the fields. Pure.</summary>
        public static float[] ParseObject(string json, string name, string[] fields)
        {
            int at = json.IndexOf("\"" + name + "\"", System.StringComparison.Ordinal);
            if (at < 0) return null;
            int i = json.IndexOf(':', at) + 1;
            while (i < json.Length && char.IsWhiteSpace(json[i])) i++;
            if (i >= json.Length || json[i] != '{') return null;
            int depth = 0, end = -1;
            bool str = false;
            for (int k = i; k < json.Length; k++)
            {
                char c = json[k];
                if (str) { if (c == '"' && json[k - 1] != '\\') str = false; continue; }
                if (c == '"') str = true;
                else if (c == '{') depth++;
                else if (c == '}' && --depth == 0) { end = k; break; }
            }
            if (end < 0) return null;
            string body = json.Substring(i, end - i + 1);
            var row = new float[fields.Length];
            bool any = false;
            for (int f = 0; f < fields.Length; f++)
            {
                int a = body.IndexOf("\"" + fields[f] + "\"", System.StringComparison.Ordinal);
                if (a < 0) continue;
                int v = body.IndexOf(':', a) + 1;
                while (v < body.Length && char.IsWhiteSpace(body[v])) v++;
                int e = v;
                while (e < body.Length && body[e] != ',' && body[e] != '}' && !char.IsWhiteSpace(body[e])) e++;
                string token = body.Substring(v, e - v);
                if (token == "true") row[f] = 1f;
                else if (token == "false") row[f] = 0f;
                else if (!float.TryParse(token, NumberStyles.Float, CultureInfo.InvariantCulture, out row[f])) continue;
                any = true;
            }
            return any ? row : null;
        }

        /// <summary>The index of the bracket closing the one at `open` (strings skipped), or -1.</summary>
        static int Close(string s, int open)
        {
            int depth = 0;
            bool str = false;
            for (int k = open; k < s.Length; k++)
            {
                char c = s[k];
                if (str) { if (c == '"' && s[k - 1] != '\\') str = false; continue; }
                if (c == '"') str = true;
                else if (c == '[') depth++;
                else if (c == ']' && --depth == 0) return k;
            }
            return -1;
        }

        static float[] Numbers(string s)
        {
            var parts = s.Split(',');
            var list = new List<float>(parts.Length);
            foreach (var p in parts)
            {
                var t = p.Trim();
                if (t.Length == 0) continue;
                list.Add(t == "null" ? float.NaN : t[0] == '"' ? 1f : float.Parse(t, NumberStyles.Float, CultureInfo.InvariantCulture));
            }
            return list.ToArray();
        }
    }
}
