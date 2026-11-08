using Meridian.Art;
using Meridian.Player;
using Meridian.Rig;
using Meridian.Ship;
using UnityEngine;

namespace Meridian.FX
{
    /// <summary>
    /// U-033 one-shot effects on PlanetSide: dig sparks where the Beam removes a tile, dust under the
    /// surveyor on a hard landing (≥ 8 m/s) and under the skids when the Pilgrim touches down.
    /// </summary>
    public sealed class SideFx : MonoBehaviour
    {
        public const float HardLanding = 8f;

        public FxPool pool;
        public RigTools rig;
        public PlayerController player;
        public SideShip ship;

        void OnEnable()
        {
            FxSheet.Get(ArtKeys.Fx.DigSparks); // load now: the first burst would otherwise find the sheet not ready
            FxSheet.Get(ArtKeys.Fx.Dust);
            if (rig != null) { rig.Dug += OnDug; rig.Mounded += OnMounded; }
            var puff = PuffKey(); if (puff != null) FxSheet.Get(puff); // U-157
            if (player != null) player.Landed += OnPlayerLanded;
            if (ship != null) ship.TouchedDown += OnTouchdown;
        }

        void OnDisable()
        {
            if (rig != null) { rig.Dug -= OnDug; rig.Mounded -= OnMounded; }
            if (player != null) player.Landed -= OnPlayerLanded;
            if (ship != null) ship.TouchedDown -= OnTouchdown;
        }

        void OnDug(Vector2 at)
        {
            // U-157: the round brush throws B-175's dirt puff from the scoop; a block planet keeps the tile's sparks.
            var puff = PuffKey();
            if (puff != null && FxSheet.Get(puff).Ready) { pool.Play(puff, at, 1f); return; }
            var t = RigTools.TileOf(at);
            pool.Play(ArtKeys.Fx.DigSparks, new Vector2(t.x + 0.5f, t.y + 0.5f), 2f);
        }

        /// <summary>U-157: a mound's puff where the earth lands.</summary>
        void OnMounded(Vector2 at)
        {
            var puff = PuffKey();
            if (puff != null && FxSheet.Get(puff).Ready) pool.Play(puff, at, 1f);
        }

        /// <summary>U-157: terrain/&lt;planet&gt;/dig_puff on a smooth planet; null elsewhere.</summary>
        string PuffKey() =>
            rig != null && rig.Brush && rig.terrain.Config != null ? $"terrain/{rig.terrain.Config.id.ToString().ToLowerInvariant()}/dig_puff" : null;

        void OnPlayerLanded(float speed)
        {
            if (speed < HardLanding) return;
            var p = player.Body.position;
            pool.Play(ArtKeys.Fx.Dust, new Vector2(p.x, p.y), Mathf.Lerp(2f, 3.5f, Mathf.InverseLerp(HardLanding, 20f, speed))); // body origin = feet
        }

        void OnTouchdown(float speed)
        {
            var p = ship.Body.position;
            float y = p.y - SideShip.SkidDrop;
            float s = speed > 3f ? 4f : 3f;
            pool.Play(ArtKeys.Fx.Dust, new Vector2(p.x - 3.2f, y), s);
            pool.Play(ArtKeys.Fx.Dust, new Vector2(p.x + 3.2f, y), s);
        }
    }
}
