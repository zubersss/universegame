using Meridian.Art;
using Meridian.CameraRig;
using Meridian.Planets;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.View2D
{
    /// <summary>
    /// U-109: the climb sky, pure. The painted layer0 ends at its top row; above it the sky is that row's colour continued
    /// upward in layer0's own parallax frame and darkened to space black over `span` metres of that frame, so the frame top
    /// is black when the camera reaches the Escape Line and the join at the painted edge can never open (the gradient is the
    /// painting, extended). The starfield fades in over the last third of the climb; the descent on entry rides the same
    /// curves backwards.
    /// </summary>
    public static class ClimbSkyMath
    {
        /// <summary>Space black: the Space camera's clear colour (SceneAuthoring), gamma.</summary>
        public static readonly Color SpaceBlack = new Color(0.01f, 0.01f, 0.02f, 1f);
        /// <summary>The starfield's alpha at the Escape Line ("at low alpha": the painted sky still reads over it).</summary>
        public const float MaxStarAlpha = 0.6f;
        /// <summary>The climb fraction where the stars start fading in (the last third).</summary>
        public const float StarsFrom = 2f / 3f;

        /// <summary>Where layer0's top edge sits when the camera is at `cameraY` (ParallaxMath.LayerY plus the layer's height).</summary>
        public static float EdgeY(float cameraY, float anchorY, float edgeRestY, float parallax) => edgeRestY + (cameraY - anchorY) * (1f - parallax);

        /// <summary>
        /// Layer0-frame metres from the painted edge to the frame's top row when the camera centre is on the Escape Line:
        /// the gradient is black there. Never under 1 m (a scene whose far layer towers over the line still fades).
        /// </summary>
        public static float Span(float parallax, float escapeY, float anchorY, float edgeRestY, float halfHeight)
            => Mathf.Max(1f, halfHeight + parallax * (escapeY - anchorY) - (edgeRestY - anchorY));

        /// <summary>0 on the datum, 1 on the Escape Line (clamped either side).</summary>
        public static float Climb(float cameraY, float datumY, float escapeY) => escapeY > datumY ? Mathf.Clamp01((cameraY - datumY) / (escapeY - datumY)) : 0f;

        /// <summary>The sky `d` metres above the painted edge (gamma): the top-row colour at and below it, space black at `span` and beyond, smooth between.</summary>
        public static Color Shade(Color top, float d, float span)
        {
            float k = span > 0f ? Mathf.Clamp01(d / span) : 1f;
            k = k * k * (3f - 2f * k);
            var c = Color.Lerp(top, SpaceBlack, k);
            c.a = 1f;
            return c;
        }

        /// <summary>The starfield's alpha for a climb fraction: 0 through the first two thirds, MaxStarAlpha at the line.</summary>
        public static float StarAlpha(float climb)
        {
            float k = Mathf.Clamp01((climb - StarsFrom) / (1f - StarsFrom));
            return MaxStarAlpha * k * k * (3f - 2f * k);
        }

        /// <summary>Perceived brightness (gamma), for the tests' ordering checks.</summary>
        public static float Luma(Color c) => 0.299f * c.r + 0.587f * c.g + 0.114f * c.b;
    }

    /// <summary>
    /// U-109 (Bible §5.1 launch, cartoon path): the sky above the painted plains. A vertex-coloured strip mesh parented to the
    /// side camera fills the frame behind ParallaxLayers (sorting BackOrder − 2) with ClimbSkyMath.Shade per row, measured
    /// against layer0's top edge each frame; the colour at the edge is layer0's own top row, read once from its texture when
    /// the art lands (the planet's PlanetBackdrop.SkyColor until then, and for a placeholder: Mars butterscotch, Mercury black
    /// from the ground). The B-120 starfield (`backgrounds/space/starfield/layer0`) is one tiled SpriteRenderer at BackOrder − 1,
    /// loaded the first time the camera passes half the climb and shown at StarAlpha. No new texture; nothing allocates per frame.
    /// </summary>
    public sealed class ClimbSky : MonoBehaviour
    {
        public const string StarsKey = "backgrounds/space/starfield/layer0";
        /// <summary>The starfield's scroll factor (its Space-scene parallax, starfield.json).</summary>
        public const float StarsParallax = 0.05f;
        /// <summary>Strips in the gradient mesh (the shade curve is smooth, so rows interpolate without banding).</summary>
        public const int Rows = 16;
        /// <summary>The climb fraction at which the starfield loads (before it is ever visible, after the boot rows are measured).</summary>
        public const float LoadStarsAt = 0.5f;

        public Camera view;
        public ParallaxLayers layers;
        public PlanetId planet;
        public float datumY, escapeY, anchorY;

        /// <summary>The colour at the painted edge (gamma): layer0's measured top row, else the planet's sky colour.</summary>
        public Color TopColour { get; private set; }
        public bool TopMeasured { get; private set; }
        /// <summary>Layer0's top edge when the camera rests at anchorY, derived from the live edge each frame.</summary>
        public float EdgeRestY { get; private set; }
        public float EdgeY { get; private set; }
        public float Span { get; private set; }
        public float StarAlpha { get; private set; }
        /// <summary>The shade at the frame's bottom and top rows after the last Place (gamma).</summary>
        public Color FrameBottom { get; private set; }
        public Color FrameTop { get; private set; }
        public MeshRenderer Gradient => gradient;
        public SpriteRenderer Stars => stars;
        public bool StarsReady => stars != null && stars.sprite != null;
        public bool StarsRequested => starsRequested;

        MeshRenderer gradient;
        Mesh mesh;
        Color[] colours;
        SpriteRenderer stars;
        bool starsRequested;
        AsyncOperationHandle<Sprite> starsHandle;
        Texture2D measuredFrom;

        /// <summary>Called by CartoonStage after the layers: the planet's numbers and the frame's resting anchor.</summary>
        public void ConfigureFor(PlanetConfig config, float surfaceDatum)
        {
            planet = config.id;
            datumY = config.datumY;
            escapeY = config.EscapeLineY;
            anchorY = ParallaxMath.AnchorY(surfaceDatum);
            TopColour = Meridian.Planet.PlanetBackdrop.SkyColor(config.id);
            TopMeasured = false;
            measuredFrom = null;
            Build();
            Place(view != null ? view.transform.position.y : anchorY);
        }

        void Build()
        {
            if (view == null) return;
            if (gradient == null)
            {
                var go = new GameObject("ClimbGradient");
                go.transform.SetParent(view.transform, false);
                mesh = new Mesh { name = "ClimbGradient" };
                var verts = new Vector3[(Rows + 1) * 2];
                var uv = new Vector2[verts.Length];
                colours = new Color[verts.Length];
                var tris = new int[Rows * 6];
                for (int r = 0; r <= Rows; r++)
                {
                    float f = r / (float)Rows;
                    verts[2 * r] = new Vector3(-0.5f, f - 0.5f, 0f);
                    verts[2 * r + 1] = new Vector3(0.5f, f - 0.5f, 0f);
                    uv[2 * r] = new Vector2(0f, f);
                    uv[2 * r + 1] = new Vector2(1f, f);
                    colours[2 * r] = colours[2 * r + 1] = Color.white;
                }
                for (int r = 0; r < Rows; r++)
                {
                    int a = 2 * r, b = a + 1, c = a + 2, d = a + 3, t = r * 6;
                    tris[t] = a; tris[t + 1] = c; tris[t + 2] = b;      // clockwise toward the camera, like SpaceWorld.Quad
                    tris[t + 3] = b; tris[t + 4] = c; tris[t + 5] = d;
                }
                mesh.vertices = verts; mesh.uv = uv; mesh.colors = colours; mesh.triangles = tris;
                mesh.RecalculateBounds();
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                gradient = go.AddComponent<MeshRenderer>();
                gradient.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                gradient.receiveShadows = false;
                gradient.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
                gradient.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;
                gradient.sortingOrder = ParallaxLayers.BackOrder - 2;
                gradient.sharedMaterial = GradientMaterial();
            }
            if (stars == null)
            {
                var go = new GameObject("ClimbStars");
                go.transform.SetParent(transform, false);
                stars = go.AddComponent<SpriteRenderer>();
                stars.sortingOrder = ParallaxLayers.BackOrder - 1;
                stars.drawMode = SpriteDrawMode.Tiled;
                stars.color = new Color(1f, 1f, 1f, 0f);
                stars.enabled = false;
                var unlit = Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.unlit : null; // the stars never dim with the night
                if (unlit != null) stars.sharedMaterial = unlit;
            }
            gradient.enabled = isActiveAndEnabled;
        }

        /// <summary>
        /// The painted layers' own material (the 2D lit sprite default), so the gradient takes the day/night light exactly as
        /// layer0's top row does; vertex colour × the material's white default texture. The 2D unlit default as the fallback.
        /// </summary>
        Material GradientMaterial()
        {
            if (layers != null && layers.renderers.Count > 0 && layers.renderers[0] != null && layers.renderers[0].sharedMaterial != null) return layers.renderers[0].sharedMaterial;
            var shader = Shader.Find("Universal Render Pipeline/2D/Sprite-Lit-Default") ?? Shader.Find("Universal Render Pipeline/2D/Sprite-Unlit-Default");
            return shader != null ? new Material(shader) { name = "ClimbSky" } : null;
        }

        void OnEnable() { if (gradient != null) gradient.enabled = true; }
        void OnDisable() { if (gradient != null) gradient.enabled = false; if (stars != null) stars.enabled = false; }

        void LateUpdate()
        {
            if (view != null) Place(view.transform.position.y);
        }

        /// <summary>
        /// One frame of the sky for a camera centred at `cameraY`: the edge from layer0's live bounds, the span, the row colours
        /// and the starfield's alpha and tile position. Public so a test rides the climb without flying it.
        /// </summary>
        public void Place(float cameraY)
        {
            if (view == null || gradient == null) return;
            // Layer0: its edge and its top row.
            SpriteRenderer far = layers != null && layers.renderers.Count > 0 ? layers.renderers[0] : null;
            float p0 = layers != null && layers.Layout != null && layers.Layout.layers.Length > 0 ? layers.Layout.layers[0].parallax : 0.1f;
            bool painted = far != null && far.sprite != null && layers.placeholders.Count > 0 && !layers.placeholders[0];
            if (painted && far.sprite.texture != measuredFrom)
            {
                measuredFrom = far.sprite.texture;
                TopMeasured = TryMeasureTopRow(far.sprite, out var top);
                TopColour = TopMeasured ? top : Meridian.Planet.PlanetBackdrop.SkyColor(planet);
            }
            EdgeY = far != null ? far.bounds.max.y : anchorY + SheetClock.FrameHeight * 0.5f;
            EdgeRestY = EdgeY - (cameraY - anchorY) * (1f - p0);
            float halfH = SideView.HalfHeight(view);
            Span = ClimbSkyMath.Span(p0, escapeY, anchorY, EdgeRestY, halfH);

            // The strip mesh fills the frame (any aspect) just behind the painted layers; rows are coloured by their world height.
            float depth = SideView.BackdropDepth(view);
            float h = SideView.HalfHeightAtDepth(view, depth) * 2f * 1.04f, w = h * Mathf.Max(view.aspect, 2.5f);
            var t = gradient.transform;
            t.localPosition = new Vector3(0f, 0f, depth);
            t.localScale = new Vector3(w, h, 1f);
            float bottom = cameraY - h * 0.5f;
            for (int r = 0; r <= Rows; r++)
            {
                var c = ClimbSkyMath.Shade(TopColour, bottom + h * (r / (float)Rows) - EdgeY, Span).linear; // vertex colours go to the GPU raw: linear
                colours[2 * r] = c; colours[2 * r + 1] = c;
            }
            mesh.SetColors(colours);
            FrameBottom = ClimbSkyMath.Shade(TopColour, cameraY - halfH - EdgeY, Span);
            FrameTop = ClimbSkyMath.Shade(TopColour, cameraY + halfH - EdgeY, Span);

            // The starfield over the gradient, under the painting.
            float climb = ClimbSkyMath.Climb(cameraY, datumY, escapeY);
            StarAlpha = ClimbSkyMath.StarAlpha(climb);
            if (!starsRequested && climb >= LoadStarsAt) RequestStars();
            if (stars == null) return;
            bool show = isActiveAndEnabled && StarAlpha > 0.001f && stars.sprite != null;
            if (stars.enabled != show) stars.enabled = show;
            if (!show) return;
            stars.color = new Color(1f, 1f, 1f, StarAlpha);
            PlaceStars(view.transform.position.x, cameraY);
        }

        /// <summary>A 3 × 3 tile block of the starfield kept within half a tile of the camera, scrolling at StarsParallax in both axes.</summary>
        void PlaceStars(float cameraX, float cameraY)
        {
            var sp = stars.sprite;
            float w = sp.bounds.size.x, h = sp.bounds.size.y;
            if (w <= 0f || h <= 0f) return;
            var size = new Vector2(w * 3f, h * 3f);
            if (stars.size != size) stars.size = size;
            float cx = ParallaxMath.LayerX(cameraX, StarsParallax);
            cx += Mathf.Round((cameraX - cx) / w) * w;
            float cy = cameraY * (1f - StarsParallax);
            cy += Mathf.Round((cameraY - cy) / h) * h;
            // A tiled sprite keeps its pivot fraction: place the block's centre, whatever the sprite's pivot.
            var pivot = new Vector2(sp.rect.width > 0f ? sp.pivot.x / sp.rect.width : 0.5f, sp.rect.height > 0f ? sp.pivot.y / sp.rect.height : 0.5f);
            stars.transform.position = new Vector3(cx - size.x * (0.5f - pivot.x), cy - size.y * (0.5f - pivot.y), 0f);
        }

        void RequestStars()
        {
            starsRequested = true;
            var probe = Addressables.LoadResourceLocationsAsync(StarsKey, typeof(Sprite));
            probe.Completed += l =>
            {
                IResourceLocation loc = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0 ? l.Result[0] : null;
                ArtLoad.Release(l);
                if (loc == null || this == null) return;
                starsHandle = ArtLoad.Asset<Sprite>(loc, StarsKey);
                starsHandle.Completed += op =>
                {
                    if (this == null || stars == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                    stars.sprite = op.Result;
                };
            };
        }

        /// <summary>
        /// Reads the sprite's top rows through a tiny render texture (the sheet is BC7 and not CPU-readable) and averages the
        /// highest row that is at least half opaque, in the texture's own sRGB encoding. False without a graphics device
        /// (-nographics runs) or on any failure; the caller falls back to the planet's sky colour.
        /// </summary>
        public static bool TryMeasureTopRow(Sprite sprite, out Color colour)
        {
            colour = default;
            if (sprite == null || sprite.texture == null) return false;
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null) return false;
            const int Samples = 64, Band = 16;
            var tex = sprite.texture;
            var rect = sprite.textureRect;
            var prev = RenderTexture.active;
            RenderTexture rt = null;
            Texture2D band = null;
            try
            {
                rt = RenderTexture.GetTemporary(Samples, Band, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
                var scale = new Vector2(rect.width / tex.width, Band / (float)tex.height);
                var offset = new Vector2(rect.xMin / tex.width, (rect.yMax - Band) / tex.height);
                Graphics.Blit(tex, rt, scale, offset);
                RenderTexture.active = rt;
                band = new Texture2D(Samples, Band, TextureFormat.RGBA32, false, false);
                band.ReadPixels(new Rect(0, 0, Samples, Band), 0, 0, false);
                band.Apply(false, false);
                var px = band.GetPixels32();
                for (int row = Band - 1; row >= 0; row--)
                {
                    float r = 0f, g = 0f, b = 0f; int n = 0;
                    for (int x = 0; x < Samples; x++)
                    {
                        var p = px[row * Samples + x];
                        if (p.a < 128) continue;
                        r += p.r; g += p.g; b += p.b; n++;
                    }
                    if (n * 2 < Samples) continue;
                    colour = new Color(r / (255f * n), g / (255f * n), b / (255f * n), 1f);
                    return true;
                }
                return false;
            }
            catch (System.Exception) { return false; }
            finally
            {
                RenderTexture.active = prev;
                if (rt != null) RenderTexture.ReleaseTemporary(rt);
                if (band != null) Destroy(band);
            }
        }

        void OnDestroy()
        {
            if (starsHandle.IsValid()) ArtLoad.Release(starsHandle);
            if (gradient != null) Destroy(gradient.gameObject);
            if (mesh != null) Destroy(mesh);
        }
    }
}
