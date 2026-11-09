using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Sprites;
using UnityEngine.UI;

namespace Meridian.Space
{
    /// <summary>
    /// U-184 (D-178; B-209's ui/map/well_dash and orbit_dot): circles drawn as a chain of the tile's dashes, one quad per dash at the tile's
    /// own length (its whole sprite rect, so atlas packing never matters), for the maps' orbits and Gravity Wells. With a clip radius only
    /// the arc inside the porthole is built (the angular window solved per circle), so a 15 000-unit orbit costs a dozen quads.
    /// </summary>
    [RequireComponent(typeof(CanvasRenderer))] // UGUI 2's Graphic asks only for a RectTransform: without this the canvas never builds the mesh
    public sealed class MapLines : MaskableGraphic
    {
        Sprite sprite;
        /// <summary>A dash's length and thickness on the canvas (the tile at 1x).</summary>
        public float dashPx = 16f, thickPx = 8f;
        /// <summary>Circles are only built where they lie within this radius of the graphic's origin (≤ 0: everywhere).</summary>
        public float clipRadius = -1f;
        readonly List<Vector3> circles = new List<Vector3>(16); // (x, y, r) on the canvas
        public int Quads { get; private set; }

        public Sprite Sprite
        {
            get => sprite;
            set { sprite = value; SetMaterialDirty(); SetVerticesDirty(); }
        }

        public override Texture mainTexture => sprite != null ? sprite.texture : s_WhiteTexture;

        public void Clear() => circles.Clear();
        public void Add(Vector2 centre, float radius) { if (radius > 0.5f) circles.Add(new Vector3(centre.x, centre.y, radius)); }
        public void Commit() => SetVerticesDirty();

        /// <summary>The arc of a circle (centre c, radius r) inside the clip disc (radius R at the origin): its middle angle and half-width
        /// (radians). False when none of it is inside; half-width π when all of it is.</summary>
        public static bool Window(Vector2 c, float r, float R, out float mid, out float half)
        {
            mid = 0f; half = Mathf.PI;
            if (R <= 0f) return true;
            float d = c.magnitude;
            if (d > r + R || r > d + R) return false;  // the disc lies wholly outside, or wholly inside, the circle
            if (d + r <= R) return true;               // the circle lies wholly inside the disc
            float cos = (r * r + d * d - R * R) / (2f * r * d);
            mid = Mathf.Atan2(-c.y, -c.x);              // towards the disc's centre
            half = Mathf.Acos(Mathf.Clamp(cos, -1f, 1f));
            return true;
        }

        protected override void OnPopulateMesh(VertexHelper vh)
        {
            vh.Clear();
            Quads = 0;
            var uv = sprite != null ? DataUtility.GetOuterUV(sprite) : new Vector4(0f, 0f, 1f, 1f);
            var col = (Color32)color;
            float h = thickPx * 0.5f;
            foreach (var cr in circles)
            {
                var c = new Vector2(cr.x, cr.y);
                float r = cr.z;
                if (!Window(c, r, clipRadius, out float mid, out float half)) continue;
                int n = Mathf.Max(8, Mathf.RoundToInt(2f * Mathf.PI * r / Mathf.Max(1f, dashPx)));
                float step = 2f * Mathf.PI / n;
                int i0 = Mathf.FloorToInt((mid - half) / step), i1 = Mathf.CeilToInt((mid + half) / step);
                if (i1 - i0 > n) i1 = i0 + n;
                for (int i = i0; i < i1; i++)
                {
                    float a = i * step, b = a + step;
                    var p = c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r;
                    var q = c + new Vector2(Mathf.Cos(b), Mathf.Sin(b)) * r;
                    var nrm = new Vector2(-(q.y - p.y), q.x - p.x).normalized * h;
                    int v = vh.currentVertCount;
                    vh.AddVert(p - nrm, col, new Vector2(uv.x, uv.y));
                    vh.AddVert(p + nrm, col, new Vector2(uv.x, uv.w));
                    vh.AddVert(q + nrm, col, new Vector2(uv.z, uv.w));
                    vh.AddVert(q - nrm, col, new Vector2(uv.z, uv.y));
                    vh.AddTriangle(v, v + 1, v + 2);
                    vh.AddTriangle(v + 2, v + 3, v);
                    Quads++;
                }
            }
        }
    }
}
