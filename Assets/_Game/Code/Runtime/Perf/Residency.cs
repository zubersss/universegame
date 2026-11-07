using System.Collections.Generic;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Perf
{
    /// <summary>
    /// U-086 (Bible §11.1 v3, Residency row): which Addressable groups hold live handles. Every asset load goes
    /// through ArtLoad, which registers (group, handle); a handle counts while it IsValid (a released handle's
    /// operation is destroyed). The group table is ArtKeys.GroupOf (U-091: one table with ArtRules.GroupFor at import).
    /// "session" holds what the game keeps on purpose for the whole run (the film overlays, FilmFeature) and is reported,
    /// not judged; terrain sheets are per visit since U-091 (TerrainTileSet.Prefetch, taken over by the planet's set).
    /// </summary>
    public static class Residency
    {
        public const string Session = "session";

        struct Entry { public string group, key; public AsyncOperationHandle handle; }
        static readonly List<Entry> entries = new List<Entry>(256);
        static readonly List<string> groups = new List<string>(8);

        public static void Track(string key, AsyncOperationHandle handle) => Track(handle, GroupOf(key), key);

        public static void Track(AsyncOperationHandle handle, string group, string key = null)
        {
            if (!handle.IsValid()) return;
            entries.Add(new Entry { group = group, key = key ?? group, handle = handle });
        }

        /// <summary>U-091: a handle is being released (ArtLoad.Release): drop one entry of it. No allocation.</summary>
        public static void Untrack(AsyncOperationHandle handle)
        {
            for (int i = entries.Count - 1; i >= 0; i--)
                if (entries[i].handle.Equals(handle)) { entries.RemoveAt(i); return; }
        }

        /// <summary>The keys still held in a planet's groups, with counts (reports only: allocates). U-091 evidence.</summary>
        public static string Holders(string planetGroup)
        {
            Prune();
            var counts = new Dictionary<string, int>();
            foreach (var e in entries)
                if (PlanetOf(e.group) == planetGroup) counts[e.key] = counts.TryGetValue(e.key, out var n) ? n + 1 : 1;
            var parts = new List<string>(counts.Count);
            foreach (var kv in counts) parts.Add(kv.Value > 1 ? kv.Key + " x" + kv.Value : kv.Key);
            parts.Sort(string.CompareOrdinal);
            return parts.Count == 0 ? "none" : string.Join(", ", parts);
        }

        /// <summary>Live handles into `group` ("planet_earth", "common", …).</summary>
        public static int Count(string group)
        {
            Prune();
            int n = 0;
            foreach (var e in entries) if (e.group == group) n++;
            return n;
        }

        public static int Total { get { Prune(); return entries.Count; } }

        /// <summary>Groups with at least one live handle, sorted, comma-separated (reports only: allocates).</summary>
        public static string ResidentGroups()
        {
            Prune();
            groups.Clear();
            foreach (var e in entries) if (!groups.Contains(e.group)) groups.Add(e.group);
            groups.Sort(string.CompareOrdinal);
            return string.Join(", ", groups);
        }

        /// <summary>
        /// True when no other planet's groups are resident. A planet's groups are "planet_<name>" and "planet_<name>_<suffix>"
        /// (props/mars_flora → planet_mars_flora); "planet_warden", "planet_waystation" and "planet_space" are not planets.
        /// common, ui, icons, space and session are always allowed.
        /// </summary>
        public static bool OnlyPlanet(string currentPlanetGroup)
        {
            Prune();
            foreach (var e in entries)
            {
                var other = PlanetOf(e.group);
                if (other != null && other != currentPlanetGroup) return false;
            }
            return true;
        }

        static readonly string[] planetGroups = BuildPlanetGroups();

        static string[] BuildPlanetGroups()
        {
            var ids = (Meridian.Planets.PlanetId[])System.Enum.GetValues(typeof(Meridian.Planets.PlanetId));
            var g = new string[ids.Length];
            for (int i = 0; i < ids.Length; i++) g[i] = PlanetGroup(ids[i]);
            return g;
        }

        /// <summary>"planet_<name>" when `group` belongs to a planet (its own group or a suffixed one), else null. No allocation (U-091: per-frame callers).</summary>
        public static string PlanetOf(string group)
        {
            if (group == null || !group.StartsWith("planet_", System.StringComparison.Ordinal)) return null;
            foreach (var g in planetGroups)
                if (group == g || (group.Length > g.Length && group[g.Length] == '_' && group.StartsWith(g, System.StringComparison.Ordinal))) return g;
            return null;
        }

        /// <summary>Live handles into any of a planet's groups (its own and the suffixed ones).</summary>
        public static int CountPlanet(string planetGroup)
        {
            Prune();
            int n = 0;
            foreach (var e in entries) if (PlanetOf(e.group) == planetGroup) n++;
            return n;
        }

        /// <summary>U-120: the keys of a planet's loads still in flight, with counts (reports only: allocates); "none" when nothing is pending.</summary>
        public static string PendingKeys(string planetGroup)
        {
            Prune();
            var counts = new Dictionary<string, int>();
            foreach (var e in entries)
                if (!e.handle.IsDone && PlanetOf(e.group) == planetGroup) counts[e.key] = counts.TryGetValue(e.key, out var n) ? n + 1 : 1;
            if (counts.Count == 0) return "none";
            var parts = new List<string>(counts.Count);
            foreach (var kv in counts) parts.Add(kv.Value > 1 ? kv.Key + " x" + kv.Value : kv.Key);
            parts.Sort(string.CompareOrdinal);
            return string.Join(", ", parts);
        }

        /// <summary>Loads into a planet's groups still in flight (U-091: the planet-load watch in SceneDirector). No allocation.</summary>
        public static int PendingPlanet(string planetGroup)
        {
            Prune();
            int n = 0;
            foreach (var e in entries) if (!e.handle.IsDone && PlanetOf(e.group) == planetGroup) n++;
            return n;
        }

        public static string PlanetGroup(Meridian.Planets.PlanetId id) => "planet_" + id.ToString().ToLowerInvariant();

        /// <summary>Addressables group of a key: the one table is ArtKeys.GroupOf (U-091).</summary>
        public static string GroupOf(string key) => Meridian.Art.ArtKeys.GroupOf(key);

        static void Prune()
        {
            for (int i = entries.Count - 1; i >= 0; i--)
                if (!entries[i].handle.IsValid()) entries.RemoveAt(i);
        }
    }
}
