using UnityEngine;

namespace Meridian.CameraRig
{
    /// <summary>
    /// U-072 (Bible 2.0 §9, §10.1): the side view's perspective camera on a rail. Gameplay stays on the z = 0
    /// plane; the camera looks along +z from z = −PlaneDistance. "Half height" is the half of the view's height
    /// on the play plane (what orthographicSize was), so every caller keeps working in metres on the plane:
    /// zoom changes the rail distance, not the field of view. 60 px/m at 1080p ⇒ 18 m visible ⇒ half height 9.
    /// An orthographic camera (Space, old captures) still answers with its orthographicSize.
    /// </summary>
    public static class SideView
    {
        public const float FieldOfView = 35f;          // vertical, degrees (U-072)
        public const float DefaultHalfHeight = 9f;     // 18 m on the plane at 1080p ⇒ 60 px/m (Bible §9)
        public const float NearClip = 0.3f, FarClip = 1200f;
        /// <summary>Camera-attached backdrop quads sit this far behind the play plane (beyond the 1 m back wall).</summary>
        public const float BackdropBehindPlane = 60f;

        static float TanHalf => Mathf.Tan(FieldOfView * 0.5f * Mathf.Deg2Rad);

        /// <summary>Rail distance from the play plane that shows `halfHeight` metres above and below the centre.</summary>
        public static float DistanceFor(float halfHeight) => halfHeight / TanHalf;

        /// <summary>The camera's distance to the play plane (z = 0).</summary>
        public static float PlaneDistance(Camera cam) => Mathf.Max(0.01f, -cam.transform.position.z);

        /// <summary>Half the view height on the play plane (orthographic: orthographicSize).</summary>
        public static float HalfHeight(Camera cam) =>
            cam.orthographic ? cam.orthographicSize : PlaneDistance(cam) * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);

        /// <summary>Half the view height at `depth` metres in front of the camera (camera-attached quads).</summary>
        public static float HalfHeightAtDepth(Camera cam, float depth) =>
            cam.orthographic ? cam.orthographicSize : depth * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);

        /// <summary>Zoom: orthographic sets the size; perspective moves the camera along its rail (z).</summary>
        public static void SetHalfHeight(Camera cam, float halfHeight)
        {
            if (cam.orthographic) { cam.orthographicSize = halfHeight; return; }
            var p = cam.transform.position;
            cam.transform.position = new Vector3(p.x, p.y, -DistanceFor(halfHeight));
        }

        /// <summary>Local z for a camera-attached backdrop quad: behind the play plane (perspective) or the old 20 (orthographic).</summary>
        public static float BackdropDepth(Camera cam) => cam.orthographic ? 20f : PlaneDistance(cam) + BackdropBehindPlane;

        /// <summary>Pixels per metre on the play plane for a screen `pixelHeight` tall.</summary>
        public static float PixelsPerMetre(Camera cam, float pixelHeight) => pixelHeight / (2f * HalfHeight(cam));

        /// <summary>Makes `cam` the side-rail perspective camera at the default zoom (keeps x/y).</summary>
        public static void Configure(Camera cam, float halfHeight = DefaultHalfHeight)
        {
            cam.orthographic = false;
            cam.fieldOfView = FieldOfView;
            cam.nearClipPlane = NearClip;
            cam.farClipPlane = FarClip;
            cam.transform.rotation = Quaternion.identity; // looks along +z at the plane
            SetHalfHeight(cam, halfHeight);
        }
    }
}
