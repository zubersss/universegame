using Meridian.Player;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.Ship
{
    /// <summary>
    /// Board with F next to the ship, exit with F once landed (Bible §6). While aboard, the player
    /// body is parked inside the ship and hidden, and the camera follows the ship.
    /// </summary>
    public sealed class ShipBoarding : MonoBehaviour
    {
        public const float BoardRange = 4f;

        public SideShip ship;
        public PlayerController player;
        public CameraFollow cameraFollow;

        public bool Aboard { get; private set; }

        InputAction interact, exit;
        readonly RaycastHit2D[] hits = new RaycastHit2D[8];

        void Start()
        {
            var actions = player != null ? player.actions : null;
            if (actions == null) return;
            interact = actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("Interact");
            exit = actions.FindActionMap(MeridianInput.ShipSide, true).FindAction("Exit");
        }

        void Update()
        {
            if (interact == null) return;
            if (!Aboard && interact.WasPressedThisFrame()) TryBoard();
            else if (Aboard && exit.WasPressedThisFrame()) TryExit();
        }

        public bool InRange => player != null &&
            Vector2.Distance(player.Body.position, ship.Body.position) <= BoardRange + SideShip.Width * 0.5f;

        public bool TryBoard()
        {
            if (Aboard || ship == null || player == null || !player.Grounded || !InRange) return false;
            Aboard = true;
            ship.SetPiloted(true);
            if (cameraFollow != null) { cameraFollow.target = ship.transform; cameraFollow.offset = new Vector2(0f, 2f); }
            // U-115 follow-up: the drawn surveyor climbs to the hatch (the legs rig's door socket) over the climb_in clip; the player object goes away after.
            var drawn = player.GetComponentInChildren<Meridian.View2D.SpriteCharacterView>(true);
            if (drawn != null && drawn.isActiveAndEnabled && player.gameObject.activeInHierarchy)
            {
                if (climb != null) StopCoroutine(climb);
                climb = StartCoroutine(ClimbIn(drawn));
                return true;
            }
            player.gameObject.SetActive(false);
            return true;
        }

        Coroutine climb;
        /// <summary>True while the drawn surveyor climbs in (the player object is still active, frozen).</summary>
        public bool Climbing => climb != null;
        /// <summary>The hatch socket (rig metres from the ground line under the pads) when the legs rig has none.</summary>
        public static readonly Vector2 DoorFallback = new Vector2(-0.05f, 2.35f);
        /// <summary>The door in world space: the legs rig's `door` socket (B-122 / B-134), else DoorFallback over the ground line.</summary>
        public Vector3 DoorWorld()
        {
            var legs = ship.GetComponentInChildren<ShipLegsView>();
            if (legs != null && legs.Rig != null && legs.Rig.Root != null) return legs.Rig.Root.TransformPoint(legs.Rig.Socket("door", DoorFallback));
            return ship.transform.TransformPoint(new Vector3(DoorFallback.x, DoorFallback.y - SideShip.SkidDrop, 0f));
        }
        System.Collections.IEnumerator ClimbIn(Meridian.View2D.SpriteCharacterView drawn)
        {
            player.Body.linearVelocity = Vector2.zero;
            player.Body.simulated = false;
            player.enabled = false;
            float until = Time.time + drawn.ClimbTo(DoorWorld());
            while (Time.time < until && ship != null && ship.Grounded && Aboard) yield return null; // a lift-off or an exit cuts it short
            player.enabled = true;
            player.Body.simulated = true;
            if (Aboard) player.gameObject.SetActive(false);
            climb = null;
        }

        /// <summary>Arrival from orbit (Bible §5.3): the surveyor is already aboard, wherever the ship is.</summary>
        public void ForceAboard()
        {
            Aboard = true;
            player.gameObject.SetActive(false);
            ship.SetPiloted(true);
            if (cameraFollow != null) { cameraFollow.target = ship.transform; cameraFollow.offset = new Vector2(0f, 2f); cameraFollow.SnapToTarget(); }
        }

        /// <summary>Exit only when landed (Bible §6); the surveyor steps out beside the hull.</summary>
        public bool TryExit()
        {
            if (!Aboard || !ship.Grounded) return false;
            Aboard = false;
            if (climb != null) { StopCoroutine(climb); climb = null; player.enabled = true; player.Body.simulated = true; } // an exit mid-climb
            ship.SetPiloted(false);
            // Step out beside the hull onto the actual ground there (it may be higher or lower than the skids).
            var p = ship.Body.position + new Vector2(SideShip.Width * 0.5f + 1f, -SideShip.SkidDrop + 0.05f);
            int n = Physics2D.Raycast(new Vector2(p.x, ship.Body.position.y + 20f), Vector2.down, ContactFilter2D.noFilter, hits, 60f);
            for (int i = 0; i < n; i++)
                if (hits[i].rigidbody != ship.Body && hits[i].collider.attachedRigidbody != player.Body) { p.y = hits[i].point.y + 0.05f; break; }
            player.transform.position = p;
            player.gameObject.SetActive(true);
            player.Body.position = p;
            player.Body.linearVelocity = Vector2.zero;
            if (cameraFollow != null) { cameraFollow.target = player.transform; cameraFollow.offset = new Vector2(0f, 1.5f); }
            return true;
        }
    }
}
