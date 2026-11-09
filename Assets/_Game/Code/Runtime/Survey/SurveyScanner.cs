using System.Collections.Generic;
using Meridian.Core;
using Meridian.Player;
using UnityEngine;

namespace Meridian.Survey
{
    /// <summary>
    /// U-054: turns each Survey pulse (U-046) into catalogue entries: creatures, terrain minerals and sites
    /// within ScanRadius of the pulse. First scans pay Datacores (Catalogue.Record). Lives on the PlanetSide root.
    /// </summary>
    public sealed class SurveyScanner : MonoBehaviour
    {
        public static float ScanRadius => Meridian.Progress.SkillStats.ScanRadius; // U-175: 8 m plus the Survey branch's

        public PlanetSideRoot side;
        PlayerRigInput rig;

        /// <summary>Raised per new entry with the Datacores it paid.</summary>
        public event System.Action<CatalogueEntry, int> Catalogued;
        /// <summary>The ids the last pulse catalogued for the first time (tests, HUD).</summary>
        public readonly List<string> LastNew = new List<string>();
        public int LastPaid { get; private set; }

        readonly HashSet<int> seenItems = new HashSet<int>();

        void Start() => Hook();

        void Hook()
        {
            if (rig != null || side == null || side.player == null) return;
            rig = side.player.GetComponent<PlayerRigInput>();
            if (rig != null) rig.Surveyed += Scan;
        }

        void OnDestroy() { if (rig != null) rig.Surveyed -= Scan; }

        /// <summary>One pulse at `centre` (the Survey module calls it; tests may too).</summary>
        public void Scan(Vector2 centre)
        {
            LastNew.Clear();
            LastPaid = 0;
            var state = GameState.Instance;
            if (state == null || side == null || side.Config == null) return;
            var planet = side.Config.id;

            // Creatures in range.
            if (side.creatures != null)
                foreach (var c in side.creatures.All)
                    if (c.Alive && ((Vector2)c.transform.position - centre).sqrMagnitude <= ScanRadius * ScanRadius)
                        Pay(planet, Catalogue.CreatureId(c.Spec.id), state);

            // Minerals: the distinct terrain materials in the scan circle.
            seenItems.Clear();
            if (side.terrain != null)
            {
                int r = Mathf.CeilToInt(ScanRadius);
                int cx = Mathf.FloorToInt(centre.x), cy = Mathf.FloorToInt(centre.y);
                for (int dx = -r; dx <= r; dx++)
                    for (int dy = -r; dy <= r; dy++)
                    {
                        if (dx * dx + dy * dy > ScanRadius * ScanRadius) continue;
                        byte t = side.terrain.GetTile(cx + dx, cy + dy);
                        int item = Meridian.Items.ItemRegistry.DropOf(t);
                        // U-059: "only here" finds in the ground (perchlorate deposits, living seed turf).
                        if (item != 0)
                        {
                            int wx = side.terrain.WrapX(cx + dx), y = cy + dy;
                            var (replace, bonus) = Meridian.Items.OnlyHere.DropAt(planet, t, wx, y, side.terrain.Generator.SurfaceHeight(wx) - y);
                            if (replace != 0) item = replace;
                            if (bonus != 0 && seenItems.Add(bonus)) Pay(planet, Catalogue.MineralId(bonus), state);
                        }
                        if (item != 0 && seenItems.Add(item)) Pay(planet, Catalogue.MineralId(item), state);
                    }
            }

            // U-059: Solarite crystals in reach.
            if (side.solarite != null && side.solarite.isActiveAndEnabled)
            {
                var solarite = Meridian.Items.ItemRegistry.Get("solarite");
                foreach (var c in side.solarite.Centres)
                    if (solarite != null && (c - centre).sqrMagnitude <= ScanRadius * ScanRadius && seenItems.Add(solarite.id))
                        Pay(planet, Catalogue.MineralId(solarite.id), state);
            }

            // U-158: buried pockets in reach show in the cutaway (their scan_x on the ground above); each new kind is catalogued.
            if (side.finds != null && side.finds.Active)
                foreach (var key in side.finds.Reveal(centre, ScanRadius))
                {
                    var def = Meridian.Items.ItemRegistry.Get(key);
                    if (def != null && seenItems.Add(def.id)) Pay(planet, Catalogue.MineralId(def.id), state);
                }
            // Sites: a POI whose stamp reaches into the scan.
            if (side.pois != null)
                foreach (var p in side.pois.placed)
                {
                    float half = p.def.Width * 0.5f;
                    if (Mathf.Abs(p.nearestX - centre.x) <= ScanRadius + half) Pay(planet, Catalogue.SiteId(p.def), state);
                }
        }

        void Pay(Meridian.Planets.PlanetId planet, string id, GameState state)
        {
            int dc = state.datacores;
            int paid = Catalogue.Record(planet, id, state.catalogue, ref dc);
            state.datacores = dc;
            if (paid <= 0) return;
            LastNew.Add(id);
            LastPaid += paid;
            Catalogued?.Invoke(Catalogue.Find(planet, id), paid);
        }
    }
}
