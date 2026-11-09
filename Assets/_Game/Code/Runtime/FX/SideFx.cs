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
            Puff(); // U-157: this planet's dirt puff loaded now
            if (player != null) player.Landed += OnPlayerLanded;
            if (ship != null) ship.TouchedDown += OnTouchdown;
        }

        void OnDisable()
        {
            if (rig != null) { rig.Dug -= OnDug; rig.Mounded -= OnMounded; }
            if (player != null) player.Landed -= OnPlayerLanded;
            FxSheet.Release(puffKey); puffKey = null; // U-159 (Residency): the puff is the planet's art; leaving releases its bundle
            ReleaseVariantPuffs();
            if (ship != null) ship.TouchedDown -= OnTouchdown;
        }

        void OnDug(Vector2 at)
        {
            // U-157: the round brush throws B-175's dirt puff from the scoop; a block planet keeps the tile's sparks. U-186: in the stroke's
            // band set (the desert's sand, the canyon's talus ...) where B-190 / B-191 drew one.
            var puff = PuffAt(at);
            if (puff != null && FxSheet.Get(puff).Ready) { pool.Play(puff, at, 1f); return; }
            var t = RigTools.TileOf(at);
            pool.Play(ArtKeys.Fx.DigSparks, new Vector2(t.x + 0.5f, t.y + 0.5f), 2f);
        }

        /// <summary>U-157: a mound's puff where the earth lands.</summary>
        void OnMounded(Vector2 at)
        {
            var puff = PuffAt(at);
            if (puff != null && FxSheet.Get(puff).Ready) pool.Play(puff, at, 1f);
        }

        string puffKey;
        Meridian.Planets.PlanetId puffPlanet;

        /// <summary>U-159: the current planet's puff key (built once per planet; the previous planet's sheet released when the planet changes).</summary>
        string Puff()
        {
            var id = rig != null && rig.terrain != null && rig.terrain.Config != null ? rig.terrain.Config.id : default;
            if (puffKey != null && id == puffPlanet) return puffKey;
            var key = PuffKey();
            if (key != puffKey)
            {
                FxSheet.Release(puffKey); puffKey = key; if (key != null) FxSheet.Get(key);
                ReleaseVariantPuffs();
                if (key != null) // U-186: the planet's band sets' puffs load with its base puff (a set without one plays the base)
                    for (int v = 1; v < Meridian.View2D.SmoothGround.Variants; v++)
                        if (Meridian.View2D.SmoothGround.VariantSuffix(id, v) != null) { variantPuffs[v] = Meridian.View2D.SmoothGround.PuffKey(id, v); FxSheet.Get(variantPuffs[v]); }
            }
            puffPlanet = id;
            return puffKey;
        }

        // ---------- U-186: the puff by the stroke's band set ----------

        /// <summary>The brush planet's puffs load as soon as it is up (OnEnable can run before the rig is configured), so the first stroke
        /// already has its band set's puff. Nothing per frame once loaded (no string is built while the key holds).</summary>
        void LateUpdate()
        {
            if (rig == null || !rig.Brush || rig.terrain == null || rig.terrain.Config == null) return;
            if (puffKey == null || rig.terrain.Config.id != puffPlanet) Puff();
        }

        readonly string[] variantPuffs = new string[Meridian.View2D.SmoothGround.Variants];
        Meridian.View2D.SmoothGround ground;

        void ReleaseVariantPuffs()
        {
            for (int v = 0; v < variantPuffs.Length; v++) { if (variantPuffs[v] != null) FxSheet.Release(variantPuffs[v]); variantPuffs[v] = null; }
            ground = null;
        }

        /// <summary>The puff for a stroke at `at`: its column's band set's (dig_puff_sand ...) once loaded, else the planet's dig_puff.</summary>
        public string PuffAt(Vector2 at)
        {
            var basePuff = Puff();
            if (basePuff == null) return null;
            if (ground == null || !ground.Active) ground = FindAnyObjectByType<Meridian.View2D.SmoothGround>();
            if (ground == null) return basePuff;
            int v = ground.VariantAt(Mathf.RoundToInt(at.x));
            var key = v > 0 && v < variantPuffs.Length ? variantPuffs[v] : null;
            return key != null && FxSheet.Get(key).Ready ? key : basePuff;
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
