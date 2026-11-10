using System.Collections.Generic;
using Meridian.Items;
using Meridian.Planet.POI;
using Meridian.Rig;
using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>
    /// U-059 Solarite (Bible §7.3): the crystal clusters of Mercury's Solarite field are fused by each flare.
    /// For OnlyHere.SolariteWindow seconds after a flare ends they glow and the Beam cuts Solarite from them
    /// (ChargesPerFlare per cluster); then they crust over and the Beam glances off until the next flare.
    /// Binds to the field's props once they're placed; hooks RigTools.harvest. Idle off Mercury.
    /// </summary>
    public sealed class SolariteCrystals : MonoBehaviour
    {
        public const int ChargesPerFlare = 3;
        public const string FieldId = "solarite_field";
        static readonly Color Crusted = new Color(0.42f, 0.4f, 0.44f);

        public PoiPlacer pois;
        public RigTools rig;
        public SolarFlares flares;

        public enum Result { NotCrystal = -1, Crusted = 0, Harvested = 1 }

        sealed class Cluster { public SpriteRenderer view; public int charges; }
        readonly List<Cluster> clusters = new List<Cluster>(4);
        bool active, bound, lastGlow;
        float window = float.NaN;

        public int Clusters => clusters.Count;
        public bool Harvestable => flares != null && OnlyHere.SolariteHarvestable(flares.SinceLastFlare);
        public Result LastResult { get; private set; } = Result.NotCrystal;

        /// <summary>The cluster centres (the Survey scanner reads them).</summary>
        public IEnumerable<Vector2> Centres { get { foreach (var c in clusters) if (c.view != null) yield return c.view.bounds.center; } }

        public void ConfigureFor(Meridian.Planets.PlanetId planet)
        {
            active = planet == Meridian.Planets.PlanetId.Mercury;
            bound = false;
            clusters.Clear();
            window = float.NaN;
            if (rig != null) rig.harvest = active ? (System.Func<Vector2, int>)(w => (int)TryHarvest(w)) : null;
            if (rig != null)
            {
                // U-209: the dig's target probe (a crystal is something to swing at, in or out of its window)
                probe ??= CrystalAt;
                rig.workables.Remove(probe);
                if (active) rig.workables.Add(probe);
            }
            enabled = active;
        }
        System.Func<Vector2, bool> probe;

        /// <summary>U-209: a crystal cluster stands at the point (TryHarvest's own hit test, nothing harvested).</summary>
        public bool CrystalAt(Vector2 world)
        {
            if (!active) return false;
            if (!bound) Bind();
            for (int i = 0; i < clusters.Count; i++)
            {
                var c = clusters[i];
                if (c.view == null) continue;
                var b = c.view.bounds;
                b.Expand(0.3f);
                if (b.Contains(new Vector3(world.x, world.y, b.center.z))) return true;
            }
            return false;
        }

        void Bind()
        {
            if (pois == null) return;
            foreach (var p in pois.placed)
            {
                if (p.def.id != FieldId || p.props.Count == 0) continue;
                foreach (var sr in p.props) if (sr != null) clusters.Add(new Cluster { view = sr });
                bound = true;
            }
        }

        void Update()
        {
            if (!active) return;
            if (!bound) { Bind(); if (!bound) return; lastGlow = !Harvestable; }
            // A new flare: every cluster is fused afresh.
            if (flares != null && flares.LastEnded != window)
            {
                window = flares.LastEnded;
                foreach (var c in clusters) c.charges = ChargesPerFlare;
            }
            bool glow = Harvestable;
            if (glow == lastGlow) return;
            lastGlow = glow;
            foreach (var c in clusters) if (c.view != null) c.view.color = glow && c.charges > 0 ? Color.white : Crusted;
        }

        /// <summary>The Beam at `world`: a crystal hit yields Solarite inside the window, glances off outside it.</summary>
        public Result TryHarvest(Vector2 world)
        {
            LastResult = Result.NotCrystal;
            if (!active) return LastResult;
            if (!bound) Bind();
            foreach (var c in clusters)
            {
                if (c.view == null) continue;
                var b = c.view.bounds;
                b.Expand(0.3f);
                if (!b.Contains(new Vector3(world.x, world.y, b.center.z))) continue;
                if (!Harvestable || c.charges <= 0) return LastResult = Result.Crusted;
                c.charges--;
                if (c.charges == 0) c.view.color = Crusted;
                var item = ItemRegistry.Get("solarite");
                if (item != null && rig != null && rig.drops != null) rig.drops.Spawn(item.id, world, null);
                else if (item != null && rig != null && rig.inventory != null) rig.inventory.Add(item.id, 1);
                return LastResult = Result.Harvested;
            }
            return LastResult;
        }
    }
}
