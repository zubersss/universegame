using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rig;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Player
{
    /// <summary>
    /// Keeps the side camera on the player; half height 9 m on the play plane by default, mouse-wheel zoom 6–14
    /// (Bible §5.1). U-072: the camera is a perspective camera on a side rail (SideView); zoom dollies it along z.
    /// </summary>
    public sealed class CameraFollow : MonoBehaviour
    {
        public Transform target;
        public Vector2 offset = new Vector2(0f, 1.5f);
        public float smoothTime = 0.12f;
        public float minSize = 6f, maxSize = 14f;
        /// <summary>U-072: perspective side rail (false keeps the 2D orthographic camera, archive scenes only).</summary>
        public bool perspectiveRail = true;
        Vector3 velocity;
        Camera cam;

        void Awake()
        {
            cam = GetComponent<Camera>();
            if (cam != null && perspectiveRail) Meridian.CameraRig.SideView.Configure(cam);
        }

        void LateUpdate()
        {
            if (target == null) return;
            var goal = new Vector3(target.position.x + offset.x, target.position.y + offset.y, transform.position.z);
            transform.position = Vector3.SmoothDamp(transform.position, goal, ref velocity, smoothTime);
            var mouse = Mouse.current;
            if (cam != null && mouse != null)
            {
                float scroll = mouse.scroll.ReadValue().y;
                if (Mathf.Abs(scroll) > 0.01f)
                    Meridian.CameraRig.SideView.SetHalfHeight(cam, Mathf.Clamp(Meridian.CameraRig.SideView.HalfHeight(cam) - Mathf.Sign(scroll) * 0.5f, minSize, maxSize));
            }
        }

        public void SnapToTarget()
        {
            if (target == null) return;
            transform.position = new Vector3(target.position.x + offset.x, target.position.y + offset.y, transform.position.z);
            velocity = Vector3.zero;
        }
    }
}
