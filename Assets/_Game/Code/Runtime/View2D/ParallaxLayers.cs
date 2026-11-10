using System.Collections.Generic;
using Meridian.Art;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.View2D
{
    /// <summary>U-094 (contract §11.4): a painted scene's &lt;scene&gt;.json.</summary>
    [System.Serializable]
    public sealed class SceneLayout
    {
        /// <summary>One layer: U-103 (D-108) adds `tile` / `tile_y` (a repeating tile in x / and y), `height_px` and `role` (starfield, nebula) for the Space scene; the side scenes ignore them.</summary>
        /// <summary>U-205 (B-225's sea_under layer4, the shallow seabed): `shore_m` (the layer shows only within that many metres of the shore, 0: everywhere)
        /// and `draw_before` (the layer draws just before layer k, 0: by its n).</summary>
        [System.Serializable] public sealed class Layer { public int n; public float parallax; public float y_m; public bool tile, tile_y; public int height_px; public string role; public Pulse pulse; public int ground_row, continue_rows; public float shore_m; public int draw_before; }
        /// <summary>U-205 (B-225): a layer's place in its set's draw order. A set with no `draw_before` draws by n, as always. Where a layer
        /// states draw_before k (sea_under's shallow seabed: 3, under the surface seen from below), the orders are the layers' ranks by
        /// (k − ½ for such a layer, n for the others). 0 is "none" (JsonUtility's default): a layer cannot ask to draw before layer 0. Pure.</summary>
        public static int DrawOrder(Layer[] layers, int index)
        {
            if (layers == null || index < 0 || index >= layers.Length) return 0;
            bool any = false;
            for (int j = 0; j < layers.Length; j++) if (layers[j].draw_before > 0) { any = true; break; }
            if (!any) return layers[index].n;
            float key = DrawKey(layers[index]);
            int rank = 0;
            for (int j = 0; j < layers.Length; j++)
            {
                if (j == index) continue;
                float kj = DrawKey(layers[j]);
                if (kj < key || (kj == key && j < index)) rank++;
            }
            return rank;
        }
        static float DrawKey(Layer l) => l.draw_before > 0 ? l.draw_before - 0.5f : l.n;
        /// <summary>U-164 (D-169): the rows a layer's continuation repeats: its json continue_rows (default DefaultContinueRows), never rows above its
        /// painted ground line (height − ground_row) when the json states one, at least 2. Pure.</summary>
        public const int DefaultContinueRows = 64;
        public static int ContinueRows(Layer l, int heightPx)
        {
            int rows = l != null && l.continue_rows > 0 ? l.continue_rows : DefaultContinueRows;
            if (l != null && l.ground_row > 0 && heightPx > l.ground_row) rows = Mathf.Min(rows, heightPx - l.ground_row);
            return Mathf.Clamp(rows, 2, Mathf.Max(2, heightPx));
        }
        /// <summary>U-133 (D-148): a layer that breathes: its scale and alpha swing between the pairs over `beats` beats at `bpm`, about pivot_uv
        /// (B-161's storm rim: scale 0.97–1.03, alpha 0.85–1.0, 8 beats at 110 bpm, the centre). Absent: an empty block (beats 0), not pulsed.</summary>
        [System.Serializable] public sealed class Pulse { public float[] scale; public float[] alpha; public int beats; public float bpm; public float[] pivot_uv; }
        public Layer[] layers;
        /// <summary>U-103: the scene's pixels per unit and anchor ("center" for the Space sky) from the json; 0 / null when the json omits them.</summary>
        public float ppu;
        public string anchor;

        /// <summary>Three layers (far, mid, near) when a scene has no json yet.</summary>
        public static SceneLayout Default() => new SceneLayout
        {
            layers = new[] { new Layer { n = 0, parallax = 0.1f, y_m = 4f }, new Layer { n = 1, parallax = 0.3f, y_m = 2f }, new Layer { n = 2, parallax = 0.6f, y_m = 0f } },
        };

        public static SceneLayout Parse(string json)
        {
            if (string.IsNullOrEmpty(json)) return Default();
            try
            {
                var s = JsonUtility.FromJson<SceneLayout>(json);
                return s != null && s.layers != null && s.layers.Length > 0 ? s : Default();
            }
            catch (System.Exception) { return Default(); }
        }
    }

    /// <summary>
    /// U-094: where a parallax layer sits, pure C#. `parallax` is the layer's scroll factor against the ground: 1 scrolls with
    /// the ground, 0.1 drifts at a tenth of it (far), 0 stays fixed to the screen. The layer's bottom rests y_m above the
    /// planet's surface datum when the camera sits at its resting height over that datum (`anchorY`: the stage camera's
    /// centre over flat ground, frame/2 − 3 m above the floor) and moves vertically by the same factor.
    /// </summary>
    public static class ParallaxMath
    {
        /// <summary>U-133: whether a layer's pulse block is complete (two scales, two alphas, beats and bpm). Pure.</summary>
        public static bool Pulsed(SceneLayout.Pulse p) => p != null && p.beats > 0 && p.bpm > 0f && p.scale != null && p.scale.Length == 2 && p.alpha != null && p.alpha.Length == 2;
        /// <summary>U-133 (D-148): the pulse at time t (s): a smooth breath from the first value to the second and back over beats × 60 / bpm seconds
        /// (starting at the first). Pure.</summary>
        public static void PulseAt(SceneLayout.Pulse p, double t, out float scale, out float alpha)
        {
            double cycle = p.beats * 60.0 / p.bpm;
            double phase = ((t % cycle) + cycle) % cycle / cycle;
            float v = 0.5f - 0.5f * Mathf.Cos((float)(phase * 2.0 * System.Math.PI));
            scale = Mathf.Lerp(p.scale[0], p.scale[1], v);
            alpha = Mathf.Lerp(p.alpha[0], p.alpha[1], v);
        }
        /// <summary>U-133: the step from a sprite's pivot to the pulse's pivot (both as uv of a drawn size); scaling by s about the pulse's pivot
        /// moves the sprite by (1 − s) × this. Pure.</summary>
        public static Vector2 PulseOffset(Vector2 spritePivotUv, Vector2 pulsePivotUv, Vector2 size) => Vector2.Scale(pulsePivotUv - spritePivotUv, size);
        public static float LayerX(float cameraX, float parallax) => cameraX * (1f - parallax);
        public static float LayerY(float cameraY, float anchorY, float datumY, float yM, float parallax) => datumY + yM + (cameraY - anchorY) * (1f - parallax);
        /// <summary>The stage camera's resting centre over a floor at `datumY` (Bible §5.1: the frame bottom 3 m under the floor).</summary>
        public static float AnchorY(float datumY) => datumY + SheetClock.FrameHeight * 0.5f - Meridian.CameraRig.StageCamera.FloorBelow;
    }

    /// <summary>
    /// U-094 (Bible §9.4 v4, contract §11.4): 3–5 painted layers behind the side view from backgrounds/&lt;planet&gt;/&lt;scene&gt;/:
    /// each layer is one tiled SpriteRenderer (3 widths wide, so it always covers the frame) placed every LateUpdate by
    /// ParallaxMath. A layer whose PNG is missing draws a flat tinted placeholder strip, so the scene runs before the art
    /// lands. Draw order: layer 0 (farthest) at the back. No allocation per frame.
    /// </summary>
    public sealed class ParallaxLayers : MonoBehaviour
    {
        public Camera view;
        /// <summary>World height of the planet's surface datum (the layers' y_m are above it).</summary>
        public float datumY;
        /// <summary>ParallaxMath.AnchorY(datumY): where the camera rests over the datum.</summary>
        public float anchorY;
        public const int BackOrder = -200;
        /// <summary>Placeholder strip size (m) and tints far → near (muted Earth plains: sky haze, hills, meadow).</summary>
        public const float PlaceholderWidth = 32f, PlaceholderHeight = 8f;
        static readonly Color[] PlaceholderTints = { new Color(0.78f, 0.80f, 0.70f), new Color(0.62f, 0.68f, 0.50f), new Color(0.48f, 0.58f, 0.36f), new Color(0.40f, 0.50f, 0.30f), new Color(0.34f, 0.42f, 0.26f) };

        public string SceneKey { get; private set; }
        public SceneLayout Layout { get; private set; } = SceneLayout.Default();
        public readonly List<SpriteRenderer> renderers = new List<SpriteRenderer>(5);
        public readonly List<bool> placeholders = new List<bool>(5);
        // U-148: each strip's tile width and how many tiles it draws (3 in the walking frame; more in the wide ship frame).
        readonly List<float> tileW = new List<float>(5);
        readonly List<int> tileN = new List<int>(5);
        /// <summary>U-148: layer i's tile width (m), the art's width once loaded, the placeholder's before.</summary>
        public float TileWidth(int i) => i >= 0 && i < tileW.Count ? tileW[i] : 0f;
        /// <summary>U-148: how many tiles layer i's strip draws now.</summary>
        public int TileCount(int i) => i >= 0 && i < tileN.Count ? tileN[i] : 0;

        /// <summary>U-148 (D-158): the tiles a strip needs so a frame `frameWidth` wide never shows its end. The strip is kept within half a tile
        /// of the camera, so ceil(frameWidth / w) + 1, at least 3 (the walking frame's count), and odd, so the pattern keeps its phase when the
        /// count changes. Pure.</summary>
        public static int TilesFor(float frameWidth, float tileWidth)
        {
            if (tileWidth <= 0f) return 3;
            int n = Mathf.CeilToInt(frameWidth / tileWidth) + 1;
            if (n < 3) n = 3;
            if ((n & 1) == 0) n++;
            return n;
        }
        /// <summary>U-118: the renderers' alpha (the storm veil fades in with the dust storm's intensity); applied in LateUpdate when it changes.</summary>
        public float alpha = 1f;
        /// <summary>U-118: a scroll along x added to every layer (the storm's wind), metres.</summary>
        public float scrollX;
        /// <summary>U-118: added to the sorting orders (BackOrder + orderOffset + n): the storm veil draws over the base set.</summary>
        public int orderOffset;
        /// <summary>U-171: the layers follow the camera below the anchor too (the sea from below: the seabed rises past as the camera dives); a land
        /// set holds its datum pose under it. Set before ConfigureFor.</summary>
        public bool followBelow;
        /// <summary>U-171: the nearest layer and its continuation fade by this on top of `alpha` (Earth's land set out over the sea: no beach or
        /// meadow on or under the water).</summary>
        public float nearAlpha = 1f;
        float appliedNear = -1f;
        /// <summary>U-171: when set, exactly these layers (by n) go on down past their sheets with their continue_rows (U-164's strips), and no
        /// other fill draws (sea_under: the water column and the two seabeds continue, the surface band does not). Set before ConfigureFor.</summary>
        public int[] continueOnly;
        /// <summary>The nearest drawn layer's index (-1 before the layers are built).</summary>
        int NearestIndex()
        {
            int k = -1;
            for (int i = 0; i < renderers.Count && i < Layout.layers.Length; i++)
                if (renderers[i] != null && (onlyLayer < 0 || Layout.layers[i].n == onlyLayer) && (k < 0 || Layout.layers[i].n > Layout.layers[k].n)) k = i;
            return k;
        }
        /// <summary>U-118: true when the scene asked for had no json and the fallback scene was configured instead (B-141's plains until it lands).</summary>
        public bool UsedFallback { get; private set; }
        float appliedAlpha = -1f;

        /// <summary>U-205 (B-225): one layer's own alpha on top of the set's (sea_under's shallow seabed fades out by its shore_m), by layer n;
        /// 1 until set and after each rebuild. At 0 the layer and its continued strip are not drawn at all.</summary>
        readonly List<float> layerAlpha = new List<float>(5);
        public void SetLayerAlpha(int n, float a)
        {
            for (int i = 0; i < renderers.Count && i < Layout.layers.Length; i++)
            {
                if (Layout.layers[i].n != n) continue;
                while (layerAlpha.Count <= i) layerAlpha.Add(1f);
                if (layerAlpha[i] == a) return;
                layerAlpha[i] = a;
                appliedAlpha = -1f; // LateUpdate re-tints
                if (renderers[i] != null && (onlyLayer < 0 || n == onlyLayer)) renderers[i].enabled = a > 0f;
                return;
            }
        }
        /// <summary>Layer n's own alpha (1 when never set or the set has no such layer); tests read it.</summary>
        public float LayerAlphaOf(int n)
        {
            for (int i = 0; i < Layout.layers.Length; i++) if (Layout.layers[i].n == n) return LayerAlphaAt(i);
            return 1f;
        }
        float LayerAlphaAt(int i) => i < layerAlpha.Count ? layerAlpha[i] : 1f;

        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>(6);
        static Sprite white;

        // ---------- U-207's trial (LEAD 11-09 23:1x): the backdrop uncompressed in the same binary ----------

        /// <summary>The launch flag of U-207's trial: `-meridianBackdropTrial rgba32` or `-meridianBackdropTrial dxt5`. It exists in
        /// development builds and the Editor only (compiled out of a release build, LEAD's condition) and is off unless given. The
        /// Editor capture read the painted backdrop at 9-14 ms a frame in BC7 and 1-2.5 ms as RGBA32 or DXT5 on the integrated GPU
        /// (perf_2026-11-09.md): with the flag the dev player's probe reads the same binary both ways.</summary>
        public const string TrialArg = "-meridianBackdropTrial";
        /// <summary>The trial's formats: off (the layers as imported, BC7), RGBA32 (four times the layer's memory), DXT5 (the same
        /// size as BC7; compressed at load by Texture2D.Compress, not by the importer).</summary>
        public enum TrialFormat { Off, Rgba32, Dxt5 }
        /// <summary>Parses the flag's value ("rgba32", "dxt5"; anything else: off). Pure.</summary>
        public static TrialFormat ParseTrial(string value) =>
            value == "rgba32" ? TrialFormat.Rgba32 : value == "dxt5" ? TrialFormat.Dxt5 : TrialFormat.Off;
#if DEVELOPMENT_BUILD || UNITY_EDITOR
        /// <summary>True where the trial is compiled in (a development build, the Editor).</summary>
        public const bool TrialCompiled = true;
        /// <summary>The trial's switch, never on in play: each layer is copied to a texture of this format as it loads and the copy
        /// is drawn; the import rule and the art are untouched.</summary>
        public static TrialFormat Trial = TrialFormat.Off;
        /// <summary>Layers converted since the launch (the probe's log).</summary>
        public static int TrialConverted { get; private set; }
        readonly List<Object> trialMade = new List<Object>(12);

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void ReadTrialFlag()
        {
            var args = System.Environment.GetCommandLineArgs();
            int at = System.Array.IndexOf(args, TrialArg);
            if (at < 0 || at + 1 >= args.Length) return;
            Trial = ParseTrial(args[at + 1]);
            if (Trial != TrialFormat.Off) Debug.Log($"[MERIDIAN] U-207 trial: the painted backdrops are copied to {Trial} as they load ({TrialArg} {args[at + 1]}).");
        }

        /// <summary>The layer's sprite on a copy of its texture in the trial's format (the imported texture is not readable: it is
        /// drawn into a render texture and read back; DXT5 is then compressed on the CPU), with the same rect, pivot, size and sampler
        /// settings; the sprite itself when the copy cannot be made.</summary>
        Sprite TrialCopy(Sprite s)
        {
            var src = s != null ? s.texture : null;
            if (src == null) return s;
            var rt = RenderTexture.GetTemporary(src.width, src.height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            Graphics.Blit(src, rt);
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var dst = new Texture2D(src.width, src.height, TextureFormat.RGBA32, false, false)
            { name = src.name + "_" + Trial, wrapModeU = src.wrapModeU, wrapModeV = src.wrapModeV, filterMode = src.filterMode, anisoLevel = src.anisoLevel };
            dst.ReadPixels(new Rect(0, 0, src.width, src.height), 0, 0, false);
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
            if (Trial == TrialFormat.Dxt5) dst.Compress(true);
            dst.Apply(false, true); // uploaded, the CPU copy dropped
            var copy = Sprite.Create(dst, s.rect, new Vector2(s.pivot.x / s.rect.width, s.pivot.y / s.rect.height), s.pixelsPerUnit, 0, SpriteMeshType.FullRect);
            copy.name = s.name;
            trialMade.Add(dst); trialMade.Add(copy);
            TrialConverted++;
            if (TrialConverted <= 12) Debug.Log($"[MERIDIAN] U-207 trial: {src.name} {src.width} x {src.height} {src.format} -> {dst.format}");
            return copy;
        }
#else
        public const bool TrialCompiled = false;
#endif

        /// <summary>U-122 (D-135): the camera height the layers follow: the camera from the anchor up, the anchor itself below it (a dig, a pool, a
        /// trench), so the layers never cross — the ground hides them there anyway. Pure.</summary>
        public static float FollowY(float cameraY, float anchorY) => Mathf.Max(cameraY, anchorY);

        /// <summary>Builds the layers of backgrounds/&lt;planet&gt;/&lt;scene&gt; (placeholders at once, art as it loads).</summary>
        public void ConfigureFor(string planet, string scene, float surfaceDatum, string fallbackScene = null)
        {
            Clear();
            UsedFallback = false;
            datumY = surfaceDatum;
            anchorY = ParallaxMath.AnchorY(surfaceDatum);
            SceneKey = $"backgrounds/{planet}/{scene}";
            Build(SceneLayout.Default());
            Probe<TextAsset>(SceneKey, h => h.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                Build(SceneLayout.Parse(op.Result.text));
            }, () =>
            {
                // U-118: a set not exported yet (B-141's plains) takes the fallback set rather than the placeholder tints.
                if (this == null || string.IsNullOrEmpty(fallbackScene) || fallbackScene == scene) return;
                ConfigureFor(planet, fallbackScene, surfaceDatum);
                UsedFallback = true;
            });
        }

        /// <summary>U-130 (D-142): a sibling set layer0 loads from (Uranus's survey layer0: the methane bands lifted, one geometry with the set); null:
        /// the set's own. Set before ConfigureFor.</summary>
        public string layer0Scene;
        /// <summary>U-133 (B-161): a sibling set layers 1 and up load from (Neptune's spot shares the storm's rim and near streaks, byte-identical);
        /// null: the set's own. Set before ConfigureFor.</summary>
        public string upperScene;
        /// <summary>U-146: draw only this layer of the set (the survey pulse's banded layer0 over the view); -1: every layer. Set before ConfigureFor.</summary>
        public int onlyLayer = -1;
        /// <summary>U-144 (D-148): every layer drawn flipped in x (Neptune's −x wind zone; tileable art stays tileable). Set before ConfigureFor.</summary>
        public bool mirrorX;
        string LayerKey(int n)
        {
            string prefix = SceneKey != null ? SceneKey.Substring(0, SceneKey.LastIndexOf('/') + 1) : null;
            if (n == 0 && !string.IsNullOrEmpty(layer0Scene) && prefix != null) return prefix + layer0Scene + "/layer0";
            if (n >= 1 && !string.IsNullOrEmpty(upperScene) && prefix != null) return prefix + upperScene + "/layer" + n;
            return SceneKey + "/layer" + n;
        }

        void Build(SceneLayout layout)
        {
            foreach (var r in renderers) if (r != null) Destroy(r.gameObject);
            renderers.Clear(); placeholders.Clear(); tileW.Clear(); tileN.Clear(); layerAlpha.Clear();
            Layout = layout;
            for (int i = 0; i < layout.layers.Length; i++)
            {
                var l = layout.layers[i];
                var go = new GameObject("Layer" + l.n);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = BackOrder + orderOffset + SceneLayout.DrawOrder(layout.layers, i); // by n, unless the json states draw_before (U-205)
                SetPlaceholder(sr, l.n);
                sr.flipX = mirrorX; // U-144
                renderers.Add(sr);
                placeholders.Add(true);
                tileW.Add(PlaceholderWidth); tileN.Add(3);
                int index = i;
                if (onlyLayer >= 0 && l.n != onlyLayer) { sr.enabled = false; placeholders[index] = false; continue; } // U-146: not drawn, not loaded
                Probe<Sprite>(LayerKey(l.n), h => h.Completed += op =>
                {
                    if (this == null || index >= renderers.Count || renderers[index] != sr || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                    var layerSprite = op.Result;
#if DEVELOPMENT_BUILD || UNITY_EDITOR
                    if (Trial != TrialFormat.Off) layerSprite = TrialCopy(layerSprite); // U-207's trial only
#endif
                    sr.color = new Color(1f, 1f, 1f, alpha);
                    sr.drawMode = SpriteDrawMode.Tiled;
                    sr.sprite = layerSprite;
                    tileW[index] = layerSprite.bounds.size.x;
                    tileN[index] = TilesFor(FrameWidth(), tileW[index]);
                    sr.size = new Vector2(tileW[index] * tileN[index], layerSprite.bounds.size.y);
                    placeholders[index] = false;
                    appliedAlpha = -1f; // the nearest layer's and a layer's own alpha go back on at the next LateUpdate
                });
            }
            appliedAlpha = -1f;
            LateUpdate();
        }

        static void SetPlaceholder(SpriteRenderer sr, int n)
        {
            if (white == null)
            {
                var tex = Texture2D.whiteTexture;
                white = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0f), tex.width, 0, SpriteMeshType.FullRect);
                white.name = "ParallaxPlaceholder";
            }
            sr.sprite = white;
            sr.drawMode = SpriteDrawMode.Tiled;
            sr.size = new Vector2(PlaceholderWidth * 3f, PlaceholderHeight - n);
            sr.color = PlaceholderTints[Mathf.Clamp(n, 0, PlaceholderTints.Length - 1)];
        }

        void Probe<T>(string address, System.Action<AsyncOperationHandle<T>> load, System.Action missing = null)
        {
            var probe = Addressables.LoadResourceLocationsAsync(address, typeof(T));
            probe.Completed += l =>
            {
                IResourceLocation loc = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0 ? l.Result[0] : null;
                ArtLoad.Release(l);
                if (loc == null) { if (this != null) missing?.Invoke(); return; }
                if (this == null) return;
                var h = ArtLoad.Asset<T>(loc, SceneKey);
                handles.Add(h);
                load(h);
            };
        }

        /// <summary>U-139: the planet's ground colour painted under the set's lowest bottom edge, so a camera in a dip or a trench sees ground, not a
        /// black band; null (the storm veil, tests) paints nothing.</summary>
        public Color? groundFill;
        /// <summary>U-141: the ground strip's fill tile; when set the under-fill tiles it (the ground the strips stand on, not a flat dark grey), the
        /// flat groundFill colour the fallback until the strip loads.</summary>
        public Sprite groundTile;
        /// <summary>U-153 (LEAD 02:5x): a decked giant's under-fill continues the set's lowest layer downward (its bottom rows stretched, in phase
        /// with it) instead of the ground strip's fill tile: there is no ground under the floes.</summary>
        public bool fillFromSet;
        /// <summary>U-164 (D-169): on the smooth ground the NEAREST layer goes on down under its bottom edge (its bottom strip repeated, in front of
        /// the farther layers), when the importer found that strip opaque; else the lowest layer's rows as before (U-153).</summary>
        public bool continueNearest;
        /// <summary>U-159: a translucent overlay (Mars's storm veil) continues its nearest layer's bottom strip whether or not it is opaque.</summary>
        public bool continueAnyBottom;
        /// <summary>U-164: the layer the fill continued on the last frame (-1: the lowest layer's rows or the colour; tests read it).</summary>
        public int FillLayer { get; private set; } = -1;
        /// <summary>U-164: the fill renderer (tests read its sprite, size and order).</summary>
        public SpriteRenderer Fill => fill;
        Sprite setFillFrom, setFill;
        Sprite nearFillFrom, nearFill;
        bool nearOpaque;
        /// <summary>How deep the ground fill reaches under the set (m): past the frame bottom from any dip the camera can drop into.</summary>
        public const float FillDepth = 200f;
        SpriteRenderer fill;
        static Sprite fillSprite;
        /// <summary>U-139: the fill's top edge on the last frame (NaN when none drew; tests read it).</summary>
        public float FillTop { get; private set; } = float.NaN;

        void PlaceFill(Vector3 c)
        {
            if (continueOnly != null)
            {
                if (fill != null && fill.enabled) fill.enabled = false;
                FillTop = float.NaN;
                ContinueOthers(-1);
                return;
            }
            if (!groundFill.HasValue) { if (fill != null && fill.enabled) fill.enabled = false; FillTop = float.NaN; HideOthers(); return; }
            if (fill == null)
            {
                if (fillSprite == null)
                {
                    var tex = Texture2D.whiteTexture;
                    fillSprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 1f), tex.width, 0, SpriteMeshType.FullRect);
                    fillSprite.name = "ParallaxGroundFill";
                }
                var go = new GameObject("GroundFill");
                go.transform.SetParent(transform, false);
                fill = go.AddComponent<SpriteRenderer>();
                fill.sprite = fillSprite;
            }
            float bottom = float.MaxValue;
            SpriteRenderer lowest = null;
            for (int i = 0; i < renderers.Count; i++) if (renderers[i] != null && renderers[i].transform.position.y < bottom) { bottom = renderers[i].transform.position.y; lowest = renderers[i]; }
            if (bottom == float.MaxValue) { fill.enabled = false; FillTop = float.NaN; return; }
            if (fillFromSet && continueNearest && ContinueNearest()) return;
            HideOthers();
            FillLayer = -1;
            if (fillFromSet && lowest.sprite != null && lowest.sprite != white)
            {
                // U-153 (LEAD 02:5x): the lowest layer's bottom rows stretched down, in phase with it: the clouds go on under the floes.
                var sp = lowest.sprite;
                if (setFillFrom != sp) { setFillFrom = sp; var r = sp.rect; setFill = Sprite.Create(sp.texture, new Rect(r.x, r.y + 1f, r.width, 2f), new Vector2(0.5f, 1f), sp.pixelsPerUnit, 0, SpriteMeshType.FullRect); }
                if (fill.sprite != setFill) { fill.sprite = setFill; fill.drawMode = SpriteDrawMode.Tiled; }
                var tint = new Color(1f, 1f, 1f, alpha);
                if (fill.color != tint) fill.color = tint;
                fill.flipX = lowest.flipX;
                fill.sortingOrder = BackOrder + orderOffset - 1;
                float rowH = 2f / sp.pixelsPerUnit;
                FillTop = bottom + 0.05f;
                fill.size = new Vector2(lowest.size.x, rowH);
                fill.transform.position = new Vector3(lowest.transform.position.x, FillTop, 0f);
                fill.transform.localScale = new Vector3(1f, FillDepth / rowH, 1f);
                fill.enabled = true;
                return;
            }
            var col = groundFill.Value; col.a *= alpha;
            if (groundTile != null) { col = new Color(1f, 1f, 1f, alpha); if (fill.sprite != groundTile) { fill.sprite = groundTile; fill.drawMode = SpriteDrawMode.Tiled; } }
            else if (fill.sprite != fillSprite) { fill.sprite = fillSprite; fill.drawMode = SpriteDrawMode.Simple; }
            if (fill.color != col) fill.color = col;
            fill.sortingOrder = BackOrder + orderOffset - 1; // behind the far layer
            float width = view.orthographic ? view.orthographicSize * view.aspect * 2f + 4f : 200f;
            FillTop = bottom + 0.05f; // a hair over the set's edge: no seam between them
            fill.transform.position = new Vector3(c.x, FillTop, 0f);
            if (groundTile != null)
            {
                // Tiled across the width only, the uniform band stretched down: tiling a 0.1 m tile 200 m deep asked for ~80 k quads ("Cannot generate
                // 9 slice", the 17:35 capture). The tile's pivot is its top edge (GroundStrip.FillRect), so the stretch grows downward.
                float th = Mathf.Max(0.01f, groundTile.bounds.size.y);
                fill.size = new Vector2(width, th);
                fill.transform.localScale = new Vector3(1f, FillDepth / th, 1f);
            }
            else fill.transform.localScale = new Vector3(width, FillDepth, 1f);
            fill.enabled = true;
        }

        /// <summary>U-164 (D-169): repeats the nearest layer's bottom strip (ContinueRows) from its bottom edge down, tiled (never a stretched
        /// row), at the nearest layer's order (in front of the farther layers, behind the ground band). False when that layer has no art yet or
        /// its strip is not opaque.</summary>
        bool ContinueNearest()
        {
            int k = -1;
            for (int i = 0; i < renderers.Count && i < Layout.layers.Length; i++)
                if (renderers[i] != null && renderers[i].enabled && (k < 0 || Layout.layers[i].n > Layout.layers[k].n)) k = i;
            if (k < 0) return false;
            var near = renderers[k];
            var l = Layout.layers[k];
            var sp = near.sprite;
            if (sp == null || sp == white) return false;
            if (nearFillFrom != sp)
            {
                nearFillFrom = sp; // the key and the strip once per sprite (no per-frame string)
                nearOpaque = continueAnyBottom || Meridian.Rendering.ArtMaterials.OpaqueBottom(LayerKey(l.n));
                if (!nearOpaque) return false;
                var r = sp.rect;
                int rows = SceneLayout.ContinueRows(l, Mathf.RoundToInt(r.height));
                nearFill = Sprite.Create(sp.texture, new Rect(r.x, r.y, r.width, rows), new Vector2(0.5f, 1f), sp.pixelsPerUnit, 0, SpriteMeshType.FullRect);
                nearFill.name = sp.name + "_continue";
            }
            if (!nearOpaque) return false;
            if (fill.sprite != nearFill) { fill.sprite = nearFill; fill.drawMode = SpriteDrawMode.Tiled; }
            var tint = new Color(1f, 1f, 1f, alpha * nearAlpha); // U-171: the near layer's strip fades with it
            if (fill.color != tint) fill.color = tint;
            fill.flipX = near.flipX;
            fill.sortingOrder = BackOrder + orderOffset + SceneLayout.DrawOrder(Layout.layers, k);
            float stripH = nearFill.bounds.size.y;
            int strips = Mathf.Max(1, Mathf.CeilToInt(ContinueDepth / stripH));
            var size = new Vector2(near.size.x, strips * stripH);
            if (fill.size != size) fill.size = size;
            fill.transform.localScale = Vector3.one;
            FillTop = near.transform.position.y + Overlap; // a hair over an opaque layer's edge: no seam
            fill.transform.position = new Vector3(near.transform.position.x, FillTop, 0f);
            fill.enabled = true;
            FillLayer = l.n;
            if (continueAnyBottom) ContinueOthers(k); else HideOthers();
            return true;
        }

        /// <summary>An opaque layer's continuation overlaps its edge by a hair; a translucent one abuts it (an overlap would draw a brighter line).</summary>
        float Overlap => continueAnyBottom ? 0f : 0.02f;

        // U-159 (LEAD 15:2x): a translucent set (continueAnyBottom: Mars's storm veil) continues every layer, not only the nearest: through
        // the veil the farther layers' bottom edges showed as straight lines across a deep view (layer1 one metre over the others).
        readonly List<SpriteRenderer> layerFills = new List<SpriteRenderer>(4);
        readonly List<Sprite> layerFillFrom = new List<Sprite>(4), layerFillSprite = new List<Sprite>(4);
        /// <summary>U-159: the farther layers' continuations drawn on the last frame (tests read it).</summary>
        public int OtherFills { get; private set; }

        void ContinueOthers(int nearIndex)
        {
            OtherFills = 0;
            for (int i = 0; i < renderers.Count && i < Layout.layers.Length; i++)
            {
                while (layerFills.Count <= i) { layerFills.Add(null); layerFillFrom.Add(null); layerFillSprite.Add(null); }
                var r = renderers[i];
                var f = layerFills[i];
                bool listed = continueOnly != null ? System.Array.IndexOf(continueOnly, Layout.layers[i].n) >= 0 : i != nearIndex;
                bool want = listed && r != null && r.enabled && r.sprite != null && r.sprite != white;
                if (!want) { if (f != null && f.enabled) f.enabled = false; continue; }
                if (f == null)
                {
                    var go = new GameObject("LayerContinue" + i);
                    go.transform.SetParent(transform, false);
                    f = layerFills[i] = go.AddComponent<SpriteRenderer>();
                }
                var l = Layout.layers[i];
                var sp = r.sprite;
                if (layerFillFrom[i] != sp)
                {
                    layerFillFrom[i] = sp;
                    int rows = SceneLayout.ContinueRows(l, Mathf.RoundToInt(sp.rect.height));
                    // A plain strip, made per sprite change (cheap: an animated layer changes its sprite every few frames; U-173's build gate
                    // read a mirrored strip's GPU copy per change as +3 ms a frame at Earth's camp).
                    layerFillSprite[i] = Sprite.Create(sp.texture, new Rect(sp.rect.x, sp.rect.y, sp.rect.width, rows), new Vector2(0.5f, 1f), sp.pixelsPerUnit, 0, SpriteMeshType.FullRect);
                }
                var strip = layerFillSprite[i];
                if (f.sprite != strip) { f.sprite = strip; f.drawMode = SpriteDrawMode.Tiled; }
                var tint = new Color(1f, 1f, 1f, alpha * LayerAlphaAt(i)); // U-205: a layer's strip fades with it
                if (f.color != tint) f.color = tint;
                f.flipX = r.flipX;
                f.sortingOrder = BackOrder + orderOffset + SceneLayout.DrawOrder(Layout.layers, i);
                float stripH = strip.bounds.size.y;
                var size = new Vector2(r.size.x, Mathf.Max(1, Mathf.CeilToInt(ContinueDepth / stripH)) * stripH);
                if (f.size != size) f.size = size;
                f.transform.position = new Vector3(r.transform.position.x, r.transform.position.y + Overlap, 0f);
                f.enabled = true;
                OtherFills++;
            }
        }

        void HideOthers()
        {
            OtherFills = 0;
            foreach (var f in layerFills) if (f != null && f.enabled) f.enabled = false;
        }

        void DropOthers()
        {
            for (int i = 0; i < layerFillFrom.Count; i++) { layerFillFrom[i] = null; layerFillSprite[i] = null; }
        }

        /// <summary>U-164: how far the nearest layer goes on under its bottom edge (m): deeper than any valley the frame shows under it.</summary>
        public const float ContinueDepth = 24f;

        void LateUpdate()
        {
            if (view == null) return;
            var c = view.transform.position;
            if (alpha != appliedAlpha || nearAlpha != appliedNear)
            {
                int near = NearestIndex();
                for (int i = 0; i < renderers.Count; i++) { var r = renderers[i]; if (r == null) continue; var col = r.color; col.a = alpha * (i == near ? nearAlpha : 1f) * LayerAlphaAt(i); r.color = col; }
                appliedAlpha = alpha; appliedNear = nearAlpha;
            }
            float frameW = FrameWidth();
            for (int i = 0; i < renderers.Count && i < Layout.layers.Length; i++)
            {
                var l = Layout.layers[i];
                var sr = renderers[i];
                if (sr == null) continue;
                float w = i < tileW.Count ? tileW[i] : sr.size.x / 3f;
                if (i < tileN.Count)
                {
                    // U-148: the wide ship frame draws more tiles (only when the count changes: no per-frame mesh rebuild).
                    int n = TilesFor(frameW, w);
                    if (n != tileN[i]) { tileN[i] = n; sr.size = new Vector2(w * n, sr.size.y); }
                }
                float x = ParallaxMath.LayerX(c.x, l.parallax) + scrollX; // U-118: the storm's wind
                // Keep the 3-wide strip centred on the camera: shift by whole tile widths (tileable art, no seam).
                if (w > 0f) x += Mathf.Round((c.x - x) / w) * w;
                var pos = new Vector3(x, ParallaxMath.LayerY(followBelow ? c.y : FollowY(c.y, anchorY), anchorY, datumY, l.y_m, l.parallax), 0f);
                if (ParallaxMath.Pulsed(l.pulse))
                {
                    // U-133 (D-148): the storm rim breathes about its pulse pivot; its alpha rides on the set's.
                    ParallaxMath.PulseAt(l.pulse, Time.time, out float ps, out float pa);
                    var want = l.pulse.pivot_uv != null && l.pulse.pivot_uv.Length == 2 ? new Vector2(l.pulse.pivot_uv[0], l.pulse.pivot_uv[1]) : new Vector2(0.5f, 0.5f);
                    var spr = sr.sprite;
                    var have = spr != null && spr.rect.width > 0f && spr.rect.height > 0f ? new Vector2(spr.pivot.x / spr.rect.width, spr.pivot.y / spr.rect.height) : want;
                    pos += (Vector3)((1f - ps) * ParallaxMath.PulseOffset(have, want, sr.size));
                    sr.transform.localScale = new Vector3(ps, ps, 1f);
                    var col = sr.color; col.a = alpha * pa; sr.color = col;
                }
                sr.transform.position = pos; // U-122: under the anchor the painting holds its datum pose
            }
            PlaceFill(c); // U-139: after the layers moved
        }

        /// <summary>U-148: the frame's width (m) with a metre's margin either side; 0 without a camera.</summary>
        float FrameWidth() => view != null ? Meridian.CameraRig.SideView.HalfHeight(view) * 2f * view.aspect + 2f : 0f;

        void Clear()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
#if DEVELOPMENT_BUILD || UNITY_EDITOR
            foreach (var o in trialMade) if (o != null) Destroy(o); // U-207's trial copies go with the set
            trialMade.Clear();
#endif
            nearFillFrom = null; nearFill = null;
            DropOthers();
        }

        /// <summary>U-128: moves the live layers to another sorting offset (the incoming set becomes the base set after its crossfade).</summary>
        public void SetOrderOffset(int offset)
        {
            orderOffset = offset;
            for (int i = 0; i < renderers.Count && i < Layout.layers.Length; i++) if (renderers[i] != null) renderers[i].sortingOrder = BackOrder + offset + SceneLayout.DrawOrder(Layout.layers, i);
        }

        /// <summary>U-128: drops the art and the renderers (the outgoing set after a crossfade); ConfigureFor builds anew.</summary>
        public void Release()
        {
            Clear();
            foreach (var r in renderers) if (r != null) Destroy(r.gameObject);
            renderers.Clear(); placeholders.Clear(); tileW.Clear(); tileN.Clear();
            SceneKey = null;
        }

        void OnDestroy() => Clear();
    }
}
