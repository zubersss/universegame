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

        /// <summary>
        /// The overlay's alpha `d` metres from the painted edge (negative = under it, over the painting): 0 at −fadeM and below,
        /// rising (a smoothstep) to 1 at the edge, 0 again at and above it, where the flat gradient behind the painting is the sky.
        /// The painting's grain fades into its own top-band colour over its last metres, so the join has no seam, no sampled
        /// repeat and no tonal step (the 04:21 / 04:46 / 05:02 climb frames). Pure.
        /// </summary>
        public static float OverlayAlpha(float d, float fadeM)
        {
            if (d >= 0f) return 0f;
            float k = fadeM > 0f ? Mathf.Clamp01(1f + d / fadeM) : 1f;
            return k * k * (3f - 2f * k);
        }
    }

    /// <summary>
    /// U-109 (Bible §5.1 launch, cartoon path): the sky above the painted plains. A vertex-coloured strip mesh parented to the
    /// side camera fills the frame behind ParallaxLayers (sorting BackOrder − 3) with ClimbSkyMath.Shade per row, measured
    /// against layer0's top edge each frame; a second strip in front of the layers (the overlay) fades the painting's own grain
    /// into that colour over its top FadeM metres (ClimbSkyMath.OverlayAlpha), so the join has no seam; the colour at the edge
    /// is the mean of layer0's own top band, read once from its texture when
    /// the art lands (the planet's PlanetBackdrop.SkyColor until then, and for a placeholder: Mars butterscotch, Mercury black
    /// from the ground). The B-120 starfield (`backgrounds/space/starfield/layer0`) is one tiled SpriteRenderer at BackOrder − 1,
    /// loaded the first time the camera passes half the climb and shown at StarAlpha. No new texture; nothing allocates per frame.
    /// </summary>
    public sealed class ClimbSky : MonoBehaviour
    {
        public const string StarsKey = "backgrounds/space/starfield/layer0";
        /// <summary>The starfield's scroll factor (its Space-scene parallax, starfield.json).</summary>
        public const float StarsParallax = 0.05f;
        /// <summary>Rows of the strip mesh, each BandM tall: the frame plus a spare row above and below (a taller frame stretches them). U-148: 72, so the
        /// widest ship frame (60 m × 1.04 + spares) keeps 1 m rows and the fade at the painted edge stays as fine as on foot.</summary>
        public const int Rows = 72;
        /// <summary>The top band of layer0 whose mean colour the sky continues (its top BandPx rows under the two edge texels: 1 m at PPU 64); also the strip's row height.</summary>
        public const int BandPx = 64;
        public const float BandM = BandPx / 64f;
        /// <summary>Metres under the painted edge over which the overlay fades the painting's grain into the top-band colour (ClimbSkyMath.OverlayAlpha); under the clouds' tops.</summary>
        public const float FadeM = 1.5f;
        /// <summary>The climb fraction at which the starfield loads (before it is ever visible, after the boot rows are measured).</summary>
        public const float LoadStarsAt = 0.5f;

        public Camera view;
        public ParallaxLayers layers;
        public PlanetId planet;
        public float datumY, escapeY, anchorY;

        /// <summary>True while the overlay fades layer0's own painting into the sky (the art is in); false on the flat fallback (a placeholder strip has no grain to fade).</summary>
        public bool Textured { get; private set; }
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
        /// <summary>The flat strip in front of the painted layers that fades the painting's top FadeM metres into the sky colour (ClimbSkyMath.OverlayAlpha).</summary>
        public MeshRenderer Overlay => overlay;
        public SpriteRenderer Stars => stars;
        public bool StarsReady => stars != null && stars.sprite != null;
        public bool StarsRequested => starsRequested;

        MeshRenderer gradient, overlay;
        Mesh mesh, overlayMesh;
        Color[] colours, overlayColours;
        SpriteRenderer stars;
        bool starsRequested;
        AsyncOperationHandle<Sprite> starsHandle;
        Texture2D measuredFrom;
        static readonly int MainTexId = Shader.PropertyToID("_MainTex");

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
                // Two strips of the same rows: the flat shade behind the painted layers (BackOrder − 3) and the overlay in front of them
                // (its order follows the layer count in Place), fading the painting's top metres into the shade's colour.
                gradient = BuildStrip("ClimbGradient", ParallaxLayers.BackOrder - 3, out mesh, out colours, out _);
                overlay = BuildStrip("ClimbOverlay", ParallaxLayers.BackOrder + 3, out overlayMesh, out overlayColours, out _);
                // Both strips share the painted layers' lit material, whose main texture is whatever sprite bound last; bind a white
                // texel so the vertex colours draw flat (the 05:21 frame showed layer0's top texel row stretched into vertical streaks).
                var white = new MaterialPropertyBlock();
                white.SetTexture(MainTexId, Texture2D.whiteTexture);
                gradient.SetPropertyBlock(white);
                overlay.SetPropertyBlock(white);
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
            overlay.enabled = isActiveAndEnabled && Textured;
        }

        /// <summary>One strip mesh of Rows rows, BandM tall each, parented to the camera: x spans the frame (scaled), y counts rows from its foot.</summary>
        MeshRenderer BuildStrip(string name, int order, out Mesh m, out Color[] cols, out Vector2[] uv)
        {
            var go = new GameObject(name);
            go.transform.SetParent(view.transform, false);
            m = new Mesh { name = name };
            // Four vertices per row (bottom-left, bottom-right, top-left, top-right): each row carries its own texture phase.
            var verts = new Vector3[Rows * 4];
            uv = new Vector2[verts.Length];
            cols = new Color[verts.Length];
            var tris = new int[Rows * 6];
            for (int r = 0; r < Rows; r++)
            {
                int v = 4 * r;
                verts[v] = new Vector3(-0.5f, r * BandM, 0f);
                verts[v + 1] = new Vector3(0.5f, r * BandM, 0f);
                verts[v + 2] = new Vector3(-0.5f, (r + 1) * BandM, 0f);
                verts[v + 3] = new Vector3(0.5f, (r + 1) * BandM, 0f);
                uv[v] = uv[v + 2] = new Vector2(0f, 1f);
                uv[v + 1] = uv[v + 3] = new Vector2(1f, 1f);
                cols[v] = cols[v + 1] = cols[v + 2] = cols[v + 3] = Color.white;
                int t = r * 6;
                tris[t] = v; tris[t + 1] = v + 2; tris[t + 2] = v + 1;      // clockwise toward the camera, like SpaceWorld.Quad
                tris[t + 3] = v + 1; tris[t + 4] = v + 2; tris[t + 5] = v + 3;
            }
            m.MarkDynamic();
            m.vertices = verts; m.uv = uv; m.colors = cols; m.triangles = tris;
            m.RecalculateBounds();
            go.AddComponent<MeshFilter>().sharedMesh = m;
            var mr = go.AddComponent<MeshRenderer>();
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            mr.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
            mr.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;
            mr.sortingOrder = order;
            mr.sharedMaterial = GradientMaterial();
            return mr;
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

        void OnEnable() { if (gradient != null) gradient.enabled = true; if (overlay != null) overlay.enabled = Textured; }
        void OnDisable() { if (gradient != null) gradient.enabled = false; if (overlay != null) overlay.enabled = false; if (stars != null) stars.enabled = false; }

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

            // The strips fill the frame (any aspect): the shade behind the painted layers, the overlay in front of them. Rows are
            // BandM tall and in phase with layer0's top edge (a row boundary sits on it); the overlay's rows under the edge fade the
            // painting into the shade's edge colour, its rows above the edge are clear. Without art the overlay stays off.
            float depth = SideView.BackdropDepth(view);
            float h = SideView.HalfHeightAtDepth(view, depth) * 2f * 1.04f, w = h * Mathf.Max(view.aspect, 2.5f);
            var t = gradient.transform;
            float bottom = cameraY - h * 0.5f;
            float first = EdgeY + Mathf.Floor((bottom - EdgeY) / BandM) * BandM; // the row boundary at or under the frame bottom, in phase with the edge
            float needed = Mathf.Ceil((cameraY + h * 0.5f - first) / BandM) + 1f;
            float rowM = needed > Rows ? BandM * needed / Rows : BandM;          // a taller frame (a perspective rail) stretches the rows rather than leaving a gap
            t.localPosition = new Vector3(0f, first - cameraY, depth);
            t.localScale = new Vector3(w, rowM / BandM, 1f);
            var ot = overlay.transform;
            ot.localPosition = t.localPosition;
            ot.localScale = t.localScale;
            int layerCount = layers != null && layers.Layout != null && layers.Layout.layers != null ? layers.Layout.layers.Length : 3;
            int overlayOrder = ParallaxLayers.BackOrder + Mathf.Max(3, layerCount); // in front of every painted layer, behind the terrain
            if (overlay.sortingOrder != overlayOrder) overlay.sortingOrder = overlayOrder;
            if (Textured != painted) { Textured = painted; overlay.enabled = painted && gradient.enabled; }
            for (int r = 0; r < Rows; r++)
            {
                float y0 = first + r * rowM, y1 = y0 + rowM;
                int v = 4 * r;
                float d0 = y0 - EdgeY, d1 = y1 - EdgeY;
                var shade0 = ClimbSkyMath.Shade(TopColour, d0, Span).linear; // vertex colours go to the GPU raw: linear
                var shade1 = ClimbSkyMath.Shade(TopColour, d1, Span).linear;
                colours[v] = shade0; colours[v + 1] = shade0; colours[v + 2] = shade1; colours[v + 3] = shade1;
                // The overlay: the row under the edge ends opaque on it (its top boundary sits on the edge within float error).
                bool under = d1 <= 1e-3f;
                var o0 = shade0; var o1 = shade1;
                o0.a = under ? ClimbSkyMath.OverlayAlpha(d0, FadeM) : 0f;
                o1.a = under ? ClimbSkyMath.OverlayAlpha(Mathf.Min(d1, -1e-4f), FadeM) : 0f;
                overlayColours[v] = o0; overlayColours[v + 1] = o0; overlayColours[v + 2] = o1; overlayColours[v + 3] = o1;
            }
            mesh.SetColors(colours);
            overlayMesh.SetColors(overlayColours);
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

        /// <summary>A tile block of the starfield (3 × 3 on foot; U-148: as many odd tiles as the wide ship frame needs) kept within half a tile
        /// of the camera, scrolling at StarsParallax in both axes.</summary>
        void PlaceStars(float cameraX, float cameraY)
        {
            var sp = stars.sprite;
            float w = sp.bounds.size.x, h = sp.bounds.size.y;
            if (w <= 0f || h <= 0f) return;
            float halfH = SideView.HalfHeight(view);
            var size = new Vector2(w * ParallaxLayers.TilesFor(halfH * 2f * view.aspect + 2f, w), h * ParallaxLayers.TilesFor(halfH * 2f + 2f, h));
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
        /// Reads the sprite's top band (BandPx rows under the two edge texels: the rows the strip samples) through a tiny render
        /// texture (the sheet is BC7 and not CPU-readable) and averages its at-least-half-opaque texels, in the texture's own sRGB
        /// encoding, so the textured band and the flat shade share one mean and the fade between them shows no tonal step. Falls
        /// back to the highest half-opaque row when the band is mostly clear. False without a graphics device (-nographics runs)
        /// or on any failure; the caller falls back to the planet's sky colour.
        /// </summary>
        public static bool TryMeasureTopRow(Sprite sprite, out Color colour)
        {
            colour = default;
            if (sprite == null || sprite.texture == null) return false;
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null) return false;
            const int Samples = 64, Band = BandPx + 2;
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
                {
                    // The band under the two edge rows (rows 0 … Band − 3 from the bottom of the blit; the top two are the inset).
                    float r = 0f, g = 0f, b = 0f; int n = 0;
                    for (int row = 0; row < Band - 2; row++)
                        for (int x = 0; x < Samples; x++)
                        {
                            var p = px[row * Samples + x];
                            if (p.a < 128) continue;
                            r += p.r; g += p.g; b += p.b; n++;
                        }
                    if (n * 2 >= Samples * (Band - 2))
                    {
                        colour = new Color(r / (255f * n), g / (255f * n), b / (255f * n), 1f);
                        return true;
                    }
                }
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
            if (overlay != null) Destroy(overlay.gameObject);
            if (mesh != null) Destroy(mesh);
            if (overlayMesh != null) Destroy(overlayMesh);
        }
    }
}
