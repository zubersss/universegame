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
            if (ship != null) ship.TouchedDown -= OnTouchdown;
        }

        void OnDug(Vector2 at)
        {
            // U-157: the round brush throws the planet's dirt puff from the scoop; a block planet keeps the tile's sparks.
            bool shovel = rig != null && rig.Tool == Meridian.Rig.DigTool.Shovel;
            int tier = TierAt(at);
            // U-193 / D-190 (4): the shovel's flick comes back with B-238's export (seven crumbs, no torso-sized clod: B-228's F1b), tinted
            // as the clods; until then DigFeel's clods are the scoop's debris alone.
            if (shovel && Meridian.Mining.DigFeel.PuffRedrawn && FxSheet.Get(ArtKeys.Fx.ShovelFlick).Ready)
                pool.Play(ArtKeys.Fx.ShovelFlick, at, 1f, 0f, player != null && at.x < player.Body.position.x, Meridian.Mining.DigFeel.Tone(tier)); // thrown back over the shoulder
            if (PlayPuff(at, tier)) return;
            var t = RigTools.TileOf(at);
            pool.Play(shovel ? ArtKeys.Fx.Dust : ArtKeys.Fx.DigSparks, new Vector2(t.x + 0.5f, t.y + 0.5f), shovel ? 1f : 2f); // sparks are the Beam's
        }

        /// <summary>U-157: a mound's puff where the earth lands (D-190: the one puff, in the tone of the ground there, as a stroke's).</summary>
        void OnMounded(Vector2 at) => PlayPuff(at, TierAt(at));

        int TierAt(Vector2 at) => rig != null && rig.D1 && rig.terrain != null ? Meridian.Mining.DigRun.TierAt(rig.terrain, at) : 0;

        /// <summary>D-190: the planet's one dig puff at `at`, drawn in cream and ink and coloured here: the dug tier's tone lifted toward
        /// white, thin enough to read as dust behind the clods (DigFeel.PuffTone / PuffScaleNow). False while the puff's sheet is not in.</summary>
        public bool PlayPuff(Vector2 at, int tier)
        {
            var puff = Puff();
            if (puff == null || !FxSheet.Get(puff).Ready) return false;
            LastPuffTint = Meridian.Mining.DigFeel.PuffTone(tier);
            LastPuffAt = at;
            Puffs++;
            pool.Play(puff, at, Meridian.Mining.DigFeel.PuffScaleNow, 0f, false, LastPuffTint);
            return true;
        }
        /// <summary>Tests: the last puff's tint and place, the puffs played since this planet came up.</summary>
        public Color LastPuffTint { get; private set; }
        public Vector2 LastPuffAt { get; private set; }
        public int Puffs { get; private set; }

        /// <summary>U-193: the flick's cream-and-ink art multiplied toward the planet's earth (B-226: tinted per ground like the dust).</summary>
        public static Color FlickTint(Meridian.Planets.PlanetId p) => p switch
        {
            Meridian.Planets.PlanetId.Mars => new Color(0.86f, 0.58f, 0.44f, 1f),
            Meridian.Planets.PlanetId.Mercury => new Color(0.74f, 0.72f, 0.70f, 1f),
            Meridian.Planets.PlanetId.Venus => new Color(0.86f, 0.80f, 0.56f, 1f),
            _ => new Color(0.80f, 0.66f, 0.50f, 1f), // Earth's soil
        };

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
            }
            puffPlanet = id;
            return puffKey;
        }

        /// <summary>The brush planet's puff loads as soon as it is up (OnEnable can run before the rig is configured), so the first stroke
        /// already has it. Nothing per frame once loaded (no string is built while the key holds).</summary>
        void LateUpdate()
        {
            if (rig == null || !rig.Brush || rig.terrain == null || rig.terrain.Config == null) return;
            if (puffKey == null || rig.terrain.Config.id != puffPlanet) Puff();
        }

        /// <summary>The puff a stroke at `at` plays: the planet's dig_puff. D-190 (3): the band sets' own puffs (dig_puff_sand, _snow,
        /// _stone, _frost, _basalt, ...) are retired; no code asks for their keys, the one puff takes its colour from its tint.</summary>
        public string PuffAt(Vector2 at) => Puff();

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
