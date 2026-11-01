using System.Collections.Generic;
using Meridian.Creatures;
using Meridian.Items;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Terrain;

namespace Meridian.Survey
{
    public enum EntryKind { Creature, Mineral, Site }

    /// <summary>One thing the Survey pays to catalogue: a creature species, a mineral (a planet's terrain material) or a site (a POI).</summary>
    public sealed class CatalogueEntry
    {
        public string id;        // "creature:stag", "mineral:hematite", "site:survey_archive"
        public EntryKind kind;
        public PlanetId planet;
        public string name;
        public int itemId;       // minerals: their item (icon); 0 otherwise
        public string artKey;    // creatures: their sheet (first frame as the icon)
        public int Datacores => Catalogue.Payout(kind);
    }

    /// <summary>
    /// U-054 Survey Catalogue (Bible §2: the Survey pays in Datacores for scans). Every planet's possible entries
    /// come from the game's own data: creature species, the planet's terrain materials, its POIs. First scans pay;
    /// rescans pay nothing. The scanned ids live in GameState.catalogue (saved).
    /// </summary>
    public static class Catalogue
    {
        public static int Payout(EntryKind k) => k switch { EntryKind.Creature => 25, EntryKind.Site => 50, _ => 10 };

        public static string CreatureId(Species s) => "creature:" + SpeciesSpec.Get(s).artKey.Substring(SpeciesSpec.Get(s).artKey.LastIndexOf('/') + 1);
        public static string MineralId(int itemId) => "mineral:" + (ItemRegistry.Get(itemId)?.key ?? itemId.ToString());
        public static string SiteId(PoiDef poi) => "site:" + poi.id;

        static readonly Dictionary<PlanetId, List<CatalogueEntry>> cache = new Dictionary<PlanetId, List<CatalogueEntry>>();

        public static List<CatalogueEntry> For(PlanetId p)
        {
            if (cache.TryGetValue(p, out var list)) return list;
            list = new List<CatalogueEntry>();
            foreach (Species s in System.Enum.GetValues(typeof(Species)))
            {
                var spec = SpeciesSpec.Get(s);
                if (spec.planet != p) continue;
                list.Add(new CatalogueEntry { id = CreatureId(s), kind = EntryKind.Creature, planet = p, name = Pretty(spec.artKey.Substring(spec.artKey.LastIndexOf('/') + 1)), artKey = spec.artKey });
            }
            var seen = new HashSet<int>();
            foreach (byte tile in TerrainStreamer.MaterialsFor(p))
            {
                int item = ItemRegistry.DropOf(tile);
                if (item == 0 || !seen.Add(item)) continue;
                list.Add(new CatalogueEntry { id = MineralId(item), kind = EntryKind.Mineral, planet = p, name = ItemRegistry.Get(item).name, itemId = item });
            }
            // U-059: the planet's "only here" find, when it isn't a terrain material already (Solarite, perchlorate, living seed).
            var only = Meridian.Items.ItemRegistry.Get(Meridian.Items.OnlyHere.KeyFor(p) ?? "");
            if (only != null && seen.Add(only.id))
                list.Add(new CatalogueEntry { id = MineralId(only.id), kind = EntryKind.Mineral, planet = p, name = only.name, itemId = only.id });
            foreach (var poi in PoiCatalog.For(p))
                list.Add(new CatalogueEntry { id = SiteId(poi), kind = EntryKind.Site, planet = p, name = Pretty(poi.label.ToLowerInvariant()) });
            cache[p] = list;
            return list;
        }

        public static CatalogueEntry Find(PlanetId p, string id) => For(p).Find(e => e.id == id);

        /// <summary>Records a scan. Returns the Datacores paid (0 for a rescan or an unknown id).</summary>
        public static int Record(PlanetId p, string id, ICollection<string> scanned, ref int datacores)
        {
            var e = Find(p, id);
            if (e == null || scanned.Contains(id)) return 0;
            scanned.Add(id);
            datacores += e.Datacores;
            return e.Datacores;
        }

        /// <summary>Share of a planet's entries already catalogued (0..1).</summary>
        public static float Completion(PlanetId p, ICollection<string> scanned)
        {
            var list = For(p);
            if (list.Count == 0) return 0f;
            int n = 0;
            foreach (var e in list) if (scanned.Contains(e.id)) n++;
            return n / (float)list.Count;
        }

        static string Pretty(string s)
        {
            s = s.Replace('_', ' ');
            return s.Length > 0 ? char.ToUpperInvariant(s[0]) + s.Substring(1) : s;
        }
    }
}
