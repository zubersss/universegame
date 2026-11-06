using UnityEngine;

namespace Meridian.Space
{
    /// <summary>
    /// U-078: meshes for the Space view. A planet is a unit spheroid: a UV sphere whose positions are flattened in
    /// z (the top-down camera at z = -10 and the backdrop at z = 0 leave no room for a 300 u Sun in depth) while
    /// its normals stay those of the round sphere, so SpaceLit shades it exactly as a globe: silhouette a disc of
    /// radius 0.5, terminator and rim from the real normals. UVs are the equirect mapping with the pole along +y
    /// (screen up), as PlanetDisc projected it.
    /// </summary>
    public static class SpaceMeshes
    {
        /// <summary>Depth of the spheroid as a share of its radius (0.02 = 6 u for the Sun).</summary>
        public const float Flatten = 0.02f;
        public const int Segments = 48, Rings = 24;

        static Mesh spheroid;

        /// <summary>The shared unit spheroid (diameter 1; scale by 2 R).</summary>
        public static Mesh Spheroid()
        {
            if (spheroid != null) return spheroid;
            spheroid = Build(Segments, Rings, Flatten);
            spheroid.name = "Spheroid";
            return spheroid;
        }

        /// <summary>
        /// A UV sphere of radius 0.5 with (segments + 1) × (rings + 1) vertices (the seam column is doubled so the
        /// equirect wraps). Positions are scaled by <paramref name="flatten"/> in z; normals are the round ones.
        /// The camera looks down +z, so the visible hemisphere is z &lt; 0: normals there point to -z.
        /// </summary>
        public static Mesh Build(int segments, int rings, float flatten)
        {
            int cols = segments + 1, rows = rings + 1;
            var verts = new Vector3[cols * rows];
            var normals = new Vector3[cols * rows];
            var uv = new Vector2[cols * rows];
            for (int r = 0; r < rows; r++)
            {
                float v = (float)r / rings;              // 0 at the south pole, 1 at the north
                float lat = (v - 0.5f) * Mathf.PI;        // -π/2 .. π/2
                float y = Mathf.Sin(lat), c = Mathf.Cos(lat);
                for (int s = 0; s < cols; s++)
                {
                    float u = (float)s / segments;        // 0 .. 1 around, the seam at the far side
                    float lon = (u - 0.5f) * 2f * Mathf.PI; // u 0.5 faces the camera (-z)
                    var n = new Vector3(Mathf.Sin(lon) * c, y, -Mathf.Cos(lon) * c);
                    int i = r * cols + s;
                    normals[i] = n;
                    verts[i] = new Vector3(n.x * 0.5f, n.y * 0.5f, n.z * 0.5f * flatten);
                    uv[i] = new Vector2(u, v);
                }
            }
            var tris = new int[segments * rings * 6];
            int t = 0;
            for (int r = 0; r < rings; r++)
                for (int s = 0; s < segments; s++)
                {
                    int a = r * cols + s, b = a + 1, c2 = a + cols, d = c2 + 1;
                    // Wound so the faces at z < 0 (toward the camera) are front faces.
                    tris[t++] = a; tris[t++] = c2; tris[t++] = b;
                    tris[t++] = b; tris[t++] = c2; tris[t++] = d;
                }
            var m = new Mesh { name = "Spheroid" + segments + "x" + rings };
            m.SetVertices(verts);
            m.SetNormals(normals);
            m.SetUVs(0, uv);
            m.SetTriangles(tris, 0);
            m.bounds = new Bounds(Vector3.zero, new Vector3(1f, 1f, Mathf.Max(flatten, 0.01f)));
            return m;
        }
    }
}
