using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.CameraRig
{
    /// <summary>
    /// U-080: a review camera for depth. Photo mode (P) lets a mouse drag orbit the side camera around the player,
    /// ±30° yaw and ±15° pitch at the rail's current distance; leaving photo mode snaps back to the side rail. The
    /// gameplay camera is unchanged (CameraFollow is paused only while the orbit is on). Depth() is the preset the
    /// build smoke and captures use (*_depth.png). No allocation per frame.
    /// </summary>
    public sealed class PhotoOrbit : MonoBehaviour
    {
        public const float MaxYaw = 30f, MaxPitch = 15f;
        /// <summary>The smoke/capture preset: enough yaw and pitch to show block sides, tops and the back wall.</summary>
        public const float DepthYaw = 25f, DepthPitch = 10f;

        public Transform target;
        public Vector3 pivotOffset = new Vector3(0f, 1.2f, 0f);
        public float degreesPerPixel = 0.15f;

        public bool Active { get; private set; }
        public float Yaw { get; private set; }
        public float Pitch { get; private set; }

        Camera cam;
        Meridian.Player.CameraFollow follow;
        InputAction toggle;
        float distance;

        void Awake()
        {
            cam = GetComponent<Camera>();
            follow = GetComponent<Meridian.Player.CameraFollow>();
        }

        void OnEnable()
        {
            var input = FindAnyObjectByType<PlayerInput>();
            var map = input != null && input.actions != null ? input.actions.FindActionMap(Meridian.Player.MeridianInput.Always, false) : null;
            toggle = map?.FindAction("PhotoMode");
            if (toggle != null) toggle.performed += OnToggle;
        }

        void OnDisable()
        {
            if (toggle != null) toggle.performed -= OnToggle;
            if (Active) SetActive(false);
        }

        void OnToggle(InputAction.CallbackContext _) => SetActive(!Active);

        public void SetActive(bool on)
        {
            if (on == Active) return;
            Active = on;
            if (on)
            {
                distance = cam != null ? SideView.PlaneDistance(cam) : SideView.DistanceFor(SideView.DefaultHalfHeight);
                Yaw = Pitch = 0f;
                if (follow != null) follow.enabled = false;
            }
            else
            {
                Yaw = Pitch = 0f;
                transform.rotation = Quaternion.identity;
                if (follow != null) { follow.enabled = true; follow.SnapToTarget(); }
                var p = transform.position;
                transform.position = new Vector3(p.x, p.y, -distance);
            }
        }

        void LateUpdate()
        {
            if (!Active || target == null) return;
            var mouse = Mouse.current;
            if (mouse != null && mouse.leftButton.isPressed)
            {
                var d = mouse.delta.ReadValue();
                Yaw = Mathf.Clamp(Yaw + d.x * degreesPerPixel, -MaxYaw, MaxYaw);
                Pitch = Mathf.Clamp(Pitch - d.y * degreesPerPixel, -MaxPitch, MaxPitch);
            }
            Place(transform, target.position + pivotOffset, distance, Yaw, Pitch);
        }

        /// <summary>Puts a camera on the orbit: `pivot` seen from `distance` m at yaw/pitch (0/0 = the side rail).</summary>
        public static void Place(Transform cam, Vector3 pivot, float distance, float yaw, float pitch)
        {
            var rot = Quaternion.Euler(Mathf.Clamp(pitch, -MaxPitch, MaxPitch), Mathf.Clamp(yaw, -MaxYaw, MaxYaw), 0f);
            cam.SetPositionAndRotation(pivot + rot * new Vector3(0f, 0f, -distance), rot);
        }

        /// <summary>The depth preset for captures: the orbit at DepthYaw/DepthPitch around `pivot` at the rail distance.</summary>
        public static void Depth(Camera cam, Vector3 pivot) =>
            Place(cam.transform, pivot, SideView.PlaneDistance(cam), DepthYaw, DepthPitch);
    }
}
