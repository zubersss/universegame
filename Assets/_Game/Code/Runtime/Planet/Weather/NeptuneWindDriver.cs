using Meridian.Player;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Meridian.Planet.Weather
{
    /// <summary>
    /// U-144 (Bible §7.9): Neptune's wind on the surveyor, on foot and in the air: the drift is NeptuneWind.Drift of the wind at the feet (the
    /// player's own wind input, as Venus's push; the ground's grip applies on foot), nothing in the lee of a solid upwind or while holding a wind
    /// anchor (Interact within its reach; Interact again or walking off lets go). The same clock as the flora's lean and the HUD's gust warning.
    /// </summary>
    public sealed class NeptuneWindDriver : MonoBehaviour
    {
        public PlayerController player;
        public Meridian.Terrain.TerrainStreamer terrain;

        public float Wind { get; private set; }
        public float Drift { get; private set; }
        public bool Sheltered { get; private set; }
        public WindAnchor Holding { get; private set; }

        InputAction interact;
        System.Func<int, int, bool> solid;

        void OnDisable()
        {
            if (player != null) { player.windX = 0f; player.leanDegrees = 0f; }
            Wind = Drift = 0f; Sheltered = false; Holding = null;
        }

        /// <summary>Takes or lets go of the nearest anchor within reach (Interact; tests may call it).</summary>
        public void ToggleHold()
        {
            if (player == null) return;
            Holding = Holding != null ? null : WindAnchor.Near(player.Body.position);
        }

        void Update()
        {
            if (player == null) return;
            if (interact == null && player.actions != null) interact = player.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("Interact");
            if (Holding != null && !WindAnchor.WithinReach(Holding.transform.position, player.Body.position, WindAnchor.LetGo)) Holding = null;
            if (interact != null && interact.WasPressedThisFrame()) ToggleHold();
        }

        void FixedUpdate()
        {
            if (player == null) return;
            if (solid == null && terrain != null) solid = (x, y) => Meridian.Terrain.TileId.IsSolid(terrain.GetTile(x, y));
            double t = Time.timeSinceLevelLoad;
            Vector2 feet = player.Body.position;
            Wind = NeptuneWind.At(Mathf.FloorToInt(feet.x), t);
            Sheltered = NeptuneWind.Sheltered(solid, feet, Wind > 0f ? 1 : Wind < 0f ? -1 : 0);
            Drift = NeptuneWind.Drift(Wind, Sheltered, Holding != null);
            player.windX = Drift;
            // D-157 (c): the drawn surveyor leans into it (quarter-degree steps: the view writes only on a change).
            player.leanDegrees = Mathf.Round(NeptuneWind.SurveyorLean(Wind, NeptuneWind.Gusting(t), Holding != null) * 4f) * 0.25f;
        }
    }
}
