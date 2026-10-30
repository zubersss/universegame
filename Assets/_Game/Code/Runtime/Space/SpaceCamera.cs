using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.Space
{
    /// <summary>Top-down camera: follows the ship, mouse-wheel zoom between 30 and 400 units of half-height.</summary>
    public sealed class SpaceCamera : MonoBehaviour
    {
        public Transform target;
        public float minSize = 30f, maxSize = 400f;
        Camera cam;

        void Awake() => cam = GetComponent<Camera>();

        void LateUpdate()
        {
            if (target != null)
                transform.position = new Vector3(target.position.x, target.position.y, transform.position.z);
            var mouse = Mouse.current;
            if (cam == null || mouse == null) return;
            float scroll = mouse.scroll.ReadValue().y;
            if (Mathf.Abs(scroll) > 0.01f)
                cam.orthographicSize = Mathf.Clamp(cam.orthographicSize * (scroll > 0 ? 0.9f : 1.1f), minSize, maxSize);
        }
    }
}
