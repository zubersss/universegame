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
        public CreatureDirector creatures;

        public const float HostileRange = 14f, ApexRange = 25f;
        /// <summary>How far below the feet the stage floor is looked for (tiles).</summary>
        public const int FloorScan = 64;

        public StageCamera Stage { get; } = new StageCamera();
        /// <summary>The player's own zoom as a frame height (m); the wheel changes it in 1 m steps.</summary>
        public float BaseFrame { get; private set; } = SideView.DefaultHalfHeight * 2f;

        Vector3 velocity;
        Camera cam;
        PlayerVitals vitals;

        void Awake()
        {
            cam = GetComponent<Camera>();
            if (cam != null && perspectiveRail) SideView.Configure(cam);
        }

        void OnEnable()
        {
            Hook();
            Meridian.Creatures.Creature.Killed += OnKilled;
        }

        void OnDisable()
        {
            Meridian.Creatures.Creature.Killed -= OnKilled;
            if (vitals != null) vitals.Damaged -= OnDamaged;
            vitals = null;
        }

        void Hook()
        {
            if (vitals != null) return;
            vitals = target != null ? target.GetComponent<PlayerVitals>() : null;
            if (vitals != null) vitals.Damaged += OnDamaged;
        }

        void OnDamaged(float _) => Stage.Impact(StageCamera.HitShake);
        void OnKilled(Meridian.Creatures.Creature _) => Stage.Impact(StageCamera.KillShake);

        bool StageActive => stage && player != null && cam != null && !cam.orthographic;

        void LateUpdate()
        {
            if (target == null) return;
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
            transform.position = new Vector3(Stage.X + Stage.Shake.x, Stage.Y + Stage.Shake.y, -SideView.DistanceFor(Stage.Frame * 0.5f));
        }

        StageInput BuildInput(float dt)
        {
            var feet = player.Body != null ? player.Body.position : (Vector2)target.position;
            var v = player.Body != null ? player.Body.linearVelocity : Vector2.zero;
            int hostiles = 0;
            bool apex = false;
            if (creatures != null)
            {
                var all = creatures.All;
                for (int k = 0; k < all.Count; k++)
                {
                    var c = all[k];
                    if (c == null || !c.Alive || c.Body == null || c.Spec == null) continue;
                    float d2 = ((Vector2)c.Body.position - feet).sqrMagnitude;
                    if (c.Spec.apex) { if (d2 <= ApexRange * ApexRange) apex = true; }
                    else if (c.Spec.temper == Temper.Hunts && d2 <= HostileRange * HostileRange) hostiles++;
                }
            }
            return new StageInput
            {
                playerX = feet.x, playerY = feet.y, facing = player.Facing, speedX = v.x, speedY = v.y,
                grounded = player.Grounded, floorY = FloorUnder(feet), hostilesNear = hostiles, apexNear = apex,
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
