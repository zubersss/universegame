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
            Vector2.Distance(player.Body.position, ship.Body.position) <= BoardRange + SideShip.HullLength * 0.5f;

        public bool TryBoard()
        {
            if (Aboard || ship == null || player == null || !player.Grounded || !InRange) return false;
            Aboard = true;
            player.gameObject.SetActive(false);
            ship.SetPiloted(true);
            if (cameraFollow != null) { cameraFollow.target = ship.transform; cameraFollow.offset = new Vector2(0f, 2f); }
            return true;
        }

        /// <summary>Exit only when landed (Bible §6); the surveyor steps out beside the hull.</summary>
        public bool TryExit()
        {
            if (!Aboard || !ship.Grounded) return false;
            Aboard = false;
            ship.SetPiloted(false);
            var p = ship.Body.position + new Vector2(SideShip.HullLength * 0.5f + 1f, -SideShip.SkidDrop + 0.05f);
            player.transform.position = p;
            player.gameObject.SetActive(true);
            player.Body.position = p;
            player.Body.linearVelocity = Vector2.zero;
            if (cameraFollow != null) { cameraFollow.target = player.transform; cameraFollow.offset = new Vector2(0f, 1.5f); }
            return true;
        }
    }
}
