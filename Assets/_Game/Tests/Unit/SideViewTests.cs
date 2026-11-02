using Meridian.CameraRig;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-072 (EditMode): the side-rail perspective camera shows ≈ 60 px/m on the play plane at 1080p (Bible 2.0 §9).</summary>
    public class SideViewTests
    {
        [Test]
        public void DefaultRailGives60PixelsPerMetreAt1080p()
        {
            var go = new GameObject("RailCam");
            try
            {
                var cam = go.AddComponent<Camera>();
                go.transform.position = new Vector3(12f, 340f, -10f);
                SideView.Configure(cam);
                Assert.IsFalse(cam.orthographic);
                Assert.AreEqual(SideView.FieldOfView, cam.fieldOfView, 1e-3f);
                Assert.AreEqual(12f, go.transform.position.x, 1e-4f, "x kept");
                Assert.AreEqual(340f, go.transform.position.y, 1e-4f, "y kept");
                Assert.Less(go.transform.position.z, 0f, "on the rail in front of the play plane");
                float ppm = SideView.PixelsPerMetre(cam, 1080f);
                TestContext.Out.WriteLine($"[MERIDIAN] side rail: z {go.transform.position.z:F2} m, FOV {cam.fieldOfView}°, {ppm:F1} px/m at 1080p");
                Assert.AreEqual(60f, ppm, 3f, "60 ± 3 px/m on the play plane");
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void ZoomDolliesAlongTheRailAndKeepsThePlaneMeasure()
        {
            var go = new GameObject("RailCam");
            try
            {
                var cam = go.AddComponent<Camera>();
                SideView.Configure(cam);
                foreach (float half in new[] { 6f, 9f, 14f })
                {
                    SideView.SetHalfHeight(cam, half);
                    Assert.AreEqual(half, SideView.HalfHeight(cam), 1e-3f, $"half height {half} on the plane");
                    Assert.AreEqual(SideView.FieldOfView, cam.fieldOfView, 1e-3f, "zoom moves the camera, not the FOV");
                }
                Assert.Greater(SideView.BackdropDepth(cam), SideView.PlaneDistance(cam), "backdrop quads sit behind the play plane");
                // Orthographic cameras (Space) still answer with their size.
                cam.orthographic = true;
                SideView.SetHalfHeight(cam, 60f);
                Assert.AreEqual(60f, cam.orthographicSize, 1e-4f);
                Assert.AreEqual(60f, SideView.HalfHeight(cam), 1e-4f);
            }
            finally { Object.DestroyImmediate(go); }
        }
    }
}
