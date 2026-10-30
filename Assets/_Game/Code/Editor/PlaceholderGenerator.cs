using System.IO;
using Meridian.Art;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// Writes contract-shaped placeholder PNGs (and sheet .json) for every ArtKeys.M1 key under
    /// Placeholders/, so systems run before the real art exists. Skips files already present.
    /// </summary>
    public static class PlaceholderGenerator
    {
        static readonly Color32 FlatNormal = new Color32(128, 128, 255, 255);
        static readonly Color32 Clear = new Color32(0, 0, 0, 0);

        [MenuItem("MERIDIAN/Generate Placeholders")]
        public static void Run() => Generate(false);

        public static void Generate(bool overwrite)
        {
            AssetDatabase.StartAssetEditing();
            try
            {
                foreach (var key in ArtKeys.M1) Write(key, overwrite);
            }
            finally
            {
                AssetDatabase.StopAssetEditing();
            }
            AssetDatabase.Refresh();
            Debug.Log($"[MERIDIAN] PlaceholderGenerator: {ArtKeys.M1.Count} keys under {ArtImporter.Active.placeholders}");
        }

        public static void Write(string key, bool overwrite)
        {
            var color = ArtImporter.PlaceholderColorPath(key);
            if (File.Exists(color) && !overwrite) return;
            Directory.CreateDirectory(Path.GetDirectoryName(color));
            var tint = Tint(key);
            var rule = ArtRules.RuleFor(key);

            switch (ArtKeys.Category(key))
            {
                case "characters":
                    WriteSheet(key, color, tint, 256, 48, 7);
                    break;
                case "terrain":
                    Save(color, TileSet(tint));
                    break;
                case "backgrounds":
                case "planets":
                    bool small = key.EndsWith("/clouds");
                    Save(color, Bands(tint, small ? 256 : 512, small ? 128 : 256, key.EndsWith("/clouds")));
                    break;
                case "ships":
                    Save(color, key.EndsWith("/side") ? Box(tint, 1536, 512) : Box(tint, 448, 448));
                    break;
                case "props":
                    Save(color, Box(tint, 160, 288));
                    break;
                default: // fx, icons, ui
                    Save(color, Box(tint, 128, 128));
                    break;
            }

            if (rule.lit)
            {
                var src = Load(color);
                var n = new Color32[src.Length];
                for (int i = 0; i < n.Length; i++) n[i] = FlatNormal;
                SaveRaw(ArtRules.SiblingPath(color, ArtMap.Normal), n, Size(color));
            }
        }

        static Color32 Tint(string key)
        {
            uint h = 2166136261; // FNV-1a: same tint on every machine and run
            foreach (var ch in key) h = (h ^ ch) * 16777619;
            var c = Color.HSVToRGB(h % 360 / 360f, 0.45f, 0.8f);
            return c;
        }

        // ---------- shapes ----------

        struct Img { public int w, h; public Color32[] px; }

        static Img New(int w, int h, Color32 fill)
        {
            var px = new Color32[w * h];
            for (int i = 0; i < px.Length; i++) px[i] = fill;
            return new Img { w = w, h = h, px = px };
        }

        /// <summary>Filled rect inside an 8 px transparent margin, 4 px darker border (contract §2 padding).</summary>
        static Img Box(Color32 tint, int w, int h)
        {
            var img = New(w, h, Clear);
            var edge = Darken(tint);
            const int m = 8;
            for (int y = m; y < h - m; y++)
            for (int x = m; x < w - m; x++)
            {
                bool border = x < m + 4 || x >= w - m - 4 || y < m + 4 || y >= h - m - 4;
                img.px[y * w + x] = border ? edge : tint;
            }
            return img;
        }

        /// <summary>64 tiles of 128 px, 8 columns; each tile solid with a 2 px edge so seams read.</summary>
        static Img TileSet(Color32 tint)
        {
            const int tile = 128, cols = 8, size = tile * cols;
            var img = New(size, size, tint);
            var edge = Darken(tint);
            for (int y = 0; y < size; y++)
            for (int x = 0; x < size; x++)
            {
                int tx = x % tile, ty = y % tile;
                if (tx < 2 || ty < 2 || tx >= tile - 2 || ty >= tile - 2) img.px[y * size + x] = edge;
            }
            return img;
        }

        /// <summary>Horizontal bands, identical at x = 0 and x = w, so it tiles in x.</summary>
        static Img Bands(Color32 tint, int w, int h, bool alpha)
        {
            var img = New(w, h, tint);
            for (int y = 0; y < h; y++)
            {
                float t = y / (float)(h - 1);
                var c = Color.Lerp(Darken(tint), tint, t);
                if (alpha) c.a = 0.35f + 0.3f * Mathf.Sin(t * 12f);
                Color32 c32 = c;
                for (int x = 0; x < w; x++) img.px[y * w + x] = c32;
            }
            return img;
        }

        static void WriteSheet(string key, string colorPath, Color32 tint, int frame, int frames, int cols)
        {
            const int gutter = 4;
            int rows = (frames + cols - 1) / cols;
            int w = cols * frame + (cols - 1) * gutter, h = rows * frame + (rows - 1) * gutter;
            var img = New(w, h, Clear);
            var dark = Darken(tint);
            for (int i = 0; i < frames; i++)
            {
                int ox = i % cols * (frame + gutter);
                int oyTop = i / cols * (frame + gutter);
                int oy = h - oyTop - frame;
                // A body-sized block standing on the 8 px padding line, shifted per frame so playback reads.
                int bw = frame / 3, bh = frame * 3 / 4, bx = ox + (frame - bw) / 2 + (i % 8) - 4, by = oy + 8;
                for (int y = by; y < by + bh; y++)
                for (int x = bx; x < bx + bw; x++)
                    img.px[y * w + x] = y > by + bh - bw / 2 ? dark : tint;
            }
            Save(colorPath, img);

            var json = "{\n" +
                $"  \"key\": \"{key}\",\n" +
                $"  \"frame_width\": {frame}, \"frame_height\": {frame}, \"columns\": {cols}, \"frames\": {frames},\n" +
                $"  \"gutter\": {gutter}, \"fps\": 12, \"pivot\": [0.5, {8f / frame:0.######}], \"facing\": \"right\",\n" +
                "  \"animations\": [\n" +
                "    {\"name\": \"idle\", \"start\": 0, \"length\": 6, \"loop\": true},\n" +
                "    {\"name\": \"walk\", \"start\": 6, \"length\": 8, \"loop\": true},\n" +
                "    {\"name\": \"run\", \"start\": 14, \"length\": 8, \"loop\": true},\n" +
                "    {\"name\": \"jump\", \"start\": 22, \"length\": 3, \"loop\": false},\n" +
                "    {\"name\": \"fall\", \"start\": 25, \"length\": 2, \"loop\": true},\n" +
                "    {\"name\": \"land\", \"start\": 27, \"length\": 3, \"loop\": false},\n" +
                "    {\"name\": \"dig\", \"start\": 30, \"length\": 6, \"loop\": true},\n" +
                "    {\"name\": \"aim\", \"start\": 36, \"length\": 2, \"loop\": true},\n" +
                "    {\"name\": \"hurt\", \"start\": 38, \"length\": 2, \"loop\": false},\n" +
                "    {\"name\": \"death\", \"start\": 40, \"length\": 8, \"loop\": false}\n" +
                "  ]\n}\n";
            File.WriteAllText(ArtRules.SheetJsonPath(colorPath), json);
        }

        static Color32 Darken(Color32 c) => new Color32((byte)(c.r * 0.55f), (byte)(c.g * 0.55f), (byte)(c.b * 0.55f), c.a);

        // ---------- io ----------

        static void Save(string path, Img img) => SaveRaw(path, img.px, new Vector2Int(img.w, img.h));

        static void SaveRaw(string path, Color32[] px, Vector2Int size)
        {
            var tex = new Texture2D(size.x, size.y, TextureFormat.RGBA32, false);
            tex.SetPixels32(px);
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
        }

        static Color32[] Load(string path)
        {
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            tex.LoadImage(File.ReadAllBytes(path));
            var px = tex.GetPixels32();
            Object.DestroyImmediate(tex);
            return px;
        }

        static Vector2Int Size(string path)
        {
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            tex.LoadImage(File.ReadAllBytes(path));
            var s = new Vector2Int(tex.width, tex.height);
            Object.DestroyImmediate(tex);
            return s;
        }
    }
}
