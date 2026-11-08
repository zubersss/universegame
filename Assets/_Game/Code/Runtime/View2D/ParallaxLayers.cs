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
        [System.Serializable] public sealed class Layer { public int n; public float parallax; public float y_m; public bool tile, tile_y; public int height_px; public string role; public Pulse pulse; }
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
        /// <summary>U-118: the renderers' alpha (the storm veil fades in with the dust storm's intensity); applied in LateUpdate when it changes.</summary>
        public float alpha = 1f;
        /// <summary>U-118: a scroll along x added to every layer (the storm's wind), metres.</summary>
        public float scrollX;
        /// <summary>U-118: added to the sorting orders (BackOrder + orderOffset + n): the storm veil draws over the base set.</summary>
        public int orderOffset;
        /// <summary>U-118: true when the scene asked for had no json and the fallback scene was configured instead (B-141's plains until it lands).</summary>
        public bool UsedFallback { get; private set; }
        float appliedAlpha = -1f;

        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>(6);
        static Sprite white;

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
            renderers.Clear(); placeholders.Clear();
            Layout = layout;
            for (int i = 0; i < layout.layers.Length; i++)
            {
                var l = layout.layers[i];
                var go = new GameObject("Layer" + l.n);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = BackOrder + orderOffset + l.n;
                SetPlaceholder(sr, l.n);
                renderers.Add(sr);
                placeholders.Add(true);
                int index = i;
                if (onlyLayer >= 0 && l.n != onlyLayer) { sr.enabled = false; placeholders[index] = false; continue; } // U-146: not drawn, not loaded
                Probe<Sprite>(LayerKey(l.n), h => h.Completed += op =>
                {
                    if (this == null || index >= renderers.Count || renderers[index] != sr || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                    sr.color = new Color(1f, 1f, 1f, alpha);
                    sr.drawMode = SpriteDrawMode.Tiled;
                    sr.sprite = op.Result;
                    sr.size = new Vector2(op.Result.bounds.size.x * 3f, op.Result.bounds.size.y);
                    placeholders[index] = false;
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
        /// <summary>How deep the ground fill reaches under the set (m): past the frame bottom from any dip the camera can drop into.</summary>
        public const float FillDepth = 200f;
        SpriteRenderer fill;
        static Sprite fillSprite;
        /// <summary>U-139: the fill's top edge on the last frame (NaN when none drew; tests read it).</summary>
        public float FillTop { get; private set; } = float.NaN;

        void PlaceFill(Vector3 c)
        {
            if (!groundFill.HasValue) { if (fill != null && fill.enabled) fill.enabled = false; FillTop = float.NaN; return; }
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
            for (int i = 0; i < renderers.Count; i++) if (renderers[i] != null) bottom = Mathf.Min(bottom, renderers[i].transform.position.y);
            if (bottom == float.MaxValue) { fill.enabled = false; FillTop = float.NaN; return; }
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

        void LateUpdate()
        {
            if (view == null) return;
            var c = view.transform.position;
            if (alpha != appliedAlpha)
            {
                for (int i = 0; i < renderers.Count; i++) { var r = renderers[i]; if (r == null) continue; var col = r.color; col.a = alpha; r.color = col; }
                appliedAlpha = alpha;
            }
            for (int i = 0; i < renderers.Count && i < Layout.layers.Length; i++)
            {
                var l = Layout.layers[i];
                var sr = renderers[i];
                if (sr == null) continue;
                float w = sr.size.x / 3f;
                float x = ParallaxMath.LayerX(c.x, l.parallax) + scrollX; // U-118: the storm's wind
                // Keep the 3-wide strip centred on the camera: shift by whole tile widths (tileable art, no seam).
                if (w > 0f) x += Mathf.Round((c.x - x) / w) * w;
                var pos = new Vector3(x, ParallaxMath.LayerY(FollowY(c.y, anchorY), anchorY, datumY, l.y_m, l.parallax), 0f);
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

        void Clear()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
            handles.Clear();
        }

        /// <summary>U-128: moves the live layers to another sorting offset (the incoming set becomes the base set after its crossfade).</summary>
        public void SetOrderOffset(int offset)
        {
            orderOffset = offset;
            for (int i = 0; i < renderers.Count && i < Layout.layers.Length; i++) if (renderers[i] != null) renderers[i].sortingOrder = BackOrder + offset + Layout.layers[i].n;
        }

        /// <summary>U-128: drops the art and the renderers (the outgoing set after a crossfade); ConfigureFor builds anew.</summary>
        public void Release()
        {
            Clear();
            foreach (var r in renderers) if (r != null) Destroy(r.gameObject);
            renderers.Clear(); placeholders.Clear();
            SceneKey = null;
        }

        void OnDestroy() => Clear();
    }
}
