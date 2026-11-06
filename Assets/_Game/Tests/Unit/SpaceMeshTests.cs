using Meridian.Space;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-078 (EditMode): the planet spheroid is a disc of radius 0.5 in the view plane with a globe's normals and equirect UVs.</summary>
    public class SpaceMeshTests
    {
        [Test]
        public void SpheroidIsAFlatDiscWithRoundNormalsAndEquirectUvs()
        {
            var m = SpaceMeshes.Build(SpaceMeshes.Segments, SpaceMeshes.Rings, SpaceMeshes.Flatten);
            Assert.AreEqual((SpaceMeshes.Segments + 1) * (SpaceMeshes.Rings + 1), m.vertexCount);
            Assert.AreEqual(SpaceMeshes.Segments * SpaceMeshes.Rings * 2, m.triangles.Length / 3, "two triangles per cell");
            var v = m.vertices; var n = m.normals; var uv = m.uv;
            float maxR = 0f, maxZ = 0f, maxDot = -1f, minDot = 1f;
            for (int i = 0; i < v.Length; i++)
            {
                maxR = Mathf.Max(maxR, new Vector2(v[i].x, v[i].y).magnitude);
                maxZ = Mathf.Max(maxZ, Mathf.Abs(v[i].z));
                Assert.AreEqual(1f, n[i].magnitude, 1e-4f, "unit normal " + i);
                // The normal is the round sphere's: its xy agrees with the position's xy direction (radius 0.5).
                Assert.AreEqual(n[i].x * 0.5f, v[i].x, 1e-4f, "normal.x matches " + i);
                Assert.AreEqual(n[i].y * 0.5f, v[i].y, 1e-4f, "normal.y matches " + i);
                Assert.That(uv[i].x, Is.InRange(0f, 1f)); Assert.That(uv[i].y, Is.InRange(0f, 1f));
                maxDot = Mathf.Max(maxDot, n[i].z); minDot = Mathf.Min(minDot, n[i].z);
            }
            Assert.AreEqual(0.5f, maxR, 1e-3f, "a disc of radius 0.5 in the view plane");
            Assert.AreEqual(0.5f * SpaceMeshes.Flatten, maxZ, 1e-3f, "flattened to Flatten × R in depth");
            Assert.AreEqual(-1f, minDot, 1e-4f, "a normal faces the camera (-z)");
            Assert.AreEqual(1f, maxDot, 1e-4f, "a normal faces away (+z)");

            // The seam column is doubled (u 0 and u 1 share a position) so the equirect wraps without a gap.
            int cols = SpaceMeshes.Segments + 1, mid = (SpaceMeshes.Rings / 2) * cols;
            Assert.AreEqual(v[mid].x, v[mid + SpaceMeshes.Segments].x, 1e-4f);
            Assert.AreEqual(0f, uv[mid].x, 1e-6f); Assert.AreEqual(1f, uv[mid + SpaceMeshes.Segments].x, 1e-6f);
            // u = 0.5 faces the camera.
            Assert.AreEqual(-1f, n[mid + SpaceMeshes.Segments / 2].z, 1e-4f, "the texture's middle faces the camera");
            Object.DestroyImmediate(m);
        }

        [Test]
        public void SpheroidFrontFacesWindTowardTheCamera()
        {
            var m = SpaceMeshes.Build(8, 4, SpaceMeshes.Flatten);
            var v = m.vertices; var t = m.triangles;
            int front = 0, total = 0;
            for (int i = 0; i < t.Length; i += 3)
            {
                var a = v[t[i]]; var b = v[t[i + 1]]; var c = v[t[i + 2]];
                var faceN = Vector3.Cross(b - a, c - a);
                if (faceN.sqrMagnitude < 1e-12f) continue;
                total++;
                // Unity front faces are clockwise on screen; seen from -z (the camera) that is a face normal toward -z
                // for the near hemisphere, so the geometric normal's sign follows the hemisphere.
                var centre = (a + b + c) / 3f;
                bool near = centre.z < 0f;
                if ((faceN.z < 0f) == near) front++;
            }
            Assert.AreEqual(total, front, "every face is wound as a front face for its hemisphere");
            Object.DestroyImmediate(m);
        }
    }
}
