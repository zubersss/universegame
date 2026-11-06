using Meridian.CameraRig;
using Meridian.Creatures;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.Player
{
    /// <summary>
    /// Keeps the side camera on the player. U-072: a perspective camera on a side rail (SideView); zoom dollies it
    /// along z (mouse wheel, frame 12–28 m tall). U-087 (Bible §5.1 v3): the StageCamera solver drives it: dead zone,
    /// look-ahead, the stage-floor height hold, fight zoom and the position-only impact shake. With `stage` off (or
    /// no player wired) the old centred SmoothDamp follow remains for archive scenes.
    /// </summary>
    public sealed class CameraFollow : MonoBehaviour
    {
        public Transform target;
        public Vector2 offset = new Vector2(0f, 1.5f);
        public float smoothTime = 0.12f;
        public float minSize = 6f, maxSize = 14f;
        /// <summary>U-072: perspective side rail (false keeps the 2D orthographic camera, archive scenes only).</summary>
        public bool perspectiveRail = true;
        /// <summary>U-087: the stage camera rules (Bible §5.1 v3); off = the old centred follow.</summary>
        public bool stage = true;
        public PlayerController player;
        public TerrainStreamer terrain;
        /// <summary>Kept for the scene wiring; D-087 removed the fight zoom that read it.</summary>
        public CreatureDirector creatures;

        /// <summary>How far below the feet the stage floor is looked for (tiles).</summary>
        public const int FloorScan = 64;

        public StageCamera Stage { get; } = new StageCamera();
        /// <summary>The player's own zoom as a frame height (m); the wheel changes it in 1 m steps.</summary>
        public float BaseFrame { get; private set; } = SideView.DefaultHalfHeight * 2f;

        /// <summary>U-093/U-094: a target that moved farther than this in one frame was teleported (a load, a wake, a test): the camera snaps, so the terrain streaming around it follows at once.</summary>
        public const float Teleport = 15f;
        Vector3 velocity, lastTarget;
        bool haveLast;
        Camera cam;
        PlayerController hooked;

        void Awake()
        {
            cam = GetComponent<Camera>();
            if (cam != null && perspectiveRail) SideView.Configure(cam);
        }

        void OnEnable() => Hook();

        void OnDisable()
        {
            if (hooked != null) hooked.Bumped -= OnBumped;
            hooked = null;
        }

        /// <summary>U-093: a bump shakes the frame (position only).</summary>
        void Hook()
        {
            if (hooked == player || player == null) return;
            if (hooked != null) hooked.Bumped -= OnBumped;
            hooked = player;
            hooked.Bumped += OnBumped;
        }

        void OnBumped() => Stage.Impact(StageCamera.BumpShake);

        /// <summary>U-094 (Bible §9.5 v4): the cartoon side view is orthographic, 16.875 m tall, with the same stage rules.</summary>
        public bool Cartoon { get; private set; }

        bool StageActive => stage && player != null && cam != null && (Cartoon || !cam.orthographic);

        /// <summary>U-094: switch this camera to the v4 orthographic frame (1080 px = 16.875 m at PPU 64), snapped on the player.</summary>
        public void UseCartoonFrame()
        {
            if (cam == null) cam = GetComponent<Camera>();
            Cartoon = true;
            perspectiveRail = false;
            if (cam != null) { cam.orthographic = true; cam.orthographicSize = Meridian.View2D.SheetClock.FrameHeight * 0.5f; }
            BaseFrame = Meridian.View2D.SheetClock.FrameHeight;
            SnapToTarget();
        }

        void LateUpdate()
        {
            if (target == null) return;
            if (haveLast && (target.position - lastTarget).sqrMagnitude > Teleport * Teleport) SnapToTarget();
            lastTarget = target.position; haveLast = true;
            var mouse = Mouse.current;
            if (cam != null && mouse != null)
            {
                float scroll = mouse.scroll.ReadValue().y;
                if (Mathf.Abs(scroll) > 0.01f)
                {
                    BaseFrame = Mathf.Clamp(BaseFrame - Mathf.Sign(scroll) * 1f, minSize * 2f, maxSize * 2f);
                    if (!StageActive) SideView.SetHalfHeight(cam, BaseFrame * 0.5f);
                }
            }
            if (!StageActive)
            {
                var goal = new Vector3(target.position.x + offset.x, target.position.y + offset.y, transform.position.z);
                transform.position = Vector3.SmoothDamp(transform.position, goal, ref velocity, smoothTime);
                return;
            }
            Hook();
            Stage.Step(BuildInput(Time.deltaTime));
            Apply();
        }

        void Apply()
        {
            if (Cartoon)
            {
                if (cam.orthographicSize != Stage.Frame * 0.5f) cam.orthographicSize = Stage.Frame * 0.5f;
                transform.position = new Vector3(Stage.X + Stage.Shake.x, Stage.Y + Stage.Shake.y, -10f);
                return;
            }
            transform.position = new Vector3(Stage.X + Stage.Shake.x, Stage.Y + Stage.Shake.y, -SideView.DistanceFor(Stage.Frame * 0.5f));
        }

        StageInput BuildInput(float dt)
        {
            var feet = player.Body != null ? player.Body.position : (Vector2)target.position;
            var v = player.Body != null ? player.Body.linearVelocity : Vector2.zero;
            return new StageInput
            {
                playerX = feet.x, playerY = feet.y, facing = player.Facing, speedX = v.x, speedY = v.y,
                grounded = player.Grounded, floorY = FloorUnder(feet),
                baseFrame = BaseFrame, dt = dt,
            };
        }

        /// <summary>The stage floor: the top of the first solid tile under the feet (digs included); the feet when none is near.</summary>
        public float FloorUnder(Vector2 feet)
        {
            if (terrain == null || terrain.Config == null) return feet.y;
            int x = Mathf.FloorToInt(feet.x);
            int y0 = Mathf.FloorToInt(feet.y - 0.05f);
            for (int y = y0; y > y0 - FloorScan && y >= 0; y--)
                if (TileId.IsSolid(terrain.GetTile(x, y))) return y + 1f;
            return feet.y;
        }

        public void SnapToTarget()
        {
            if (target == null) return;
            velocity = Vector3.zero;
            if (StageActive)
            {
                Hook();
                Stage.Snap(BuildInput(0f));
                Apply();
                return;
            }
            transform.position = new Vector3(target.position.x + offset.x, target.position.y + offset.y, transform.position.z);
        }
    }
}
