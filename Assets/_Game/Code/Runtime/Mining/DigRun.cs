using Meridian.Items;
using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Mining
{
    /// <summary>
    /// U-174 (D-174, Bible 5.2 §8.1): the dig run. The Surface Line lies SurfaceLineDepth (2 m) under the drawn natural surface everywhere:
    /// above it is topside (selling, the tree), below it the run's depth counts from 0 and picks the tier (hardness, material chance).
    /// Pure helpers over the streamer and the tables; no allocation.
    /// </summary>
    public static class DigRun
    {
        /// <summary>The Surface Line's height at world x (the drawn natural surface, undug, minus the tables' depth).</summary>
        public static float LineAt(TerrainStreamer t, float x) => t.SurfaceAt(x) - D1Tables.Current.surfaceLineDepth;

        /// <summary>Metres under the Surface Line at p (0 at and above it).</summary>
        public static float Depth(TerrainStreamer t, Vector2 p) => Mathf.Max(0f, LineAt(t, p.x) - p.y);

        /// <summary>Feet at or above the Surface Line: topside.</summary>
        public static bool Topside(TerrainStreamer t, Vector2 feet) => feet.y >= LineAt(t, feet.x);

        /// <summary>The depth tier (0 = T1 … 4 = T5) at p.</summary>
        public static int TierAt(TerrainStreamer t, Vector2 p) => D1Tables.Current.TierIndex(Depth(t, p));

        /// <summary>A stroke's time (s) at p for the planet and Beam power.</summary>
        public static float StrokeSeconds(TerrainStreamer t, Vector2 p, float beamPower) =>
            D1Tables.Current.StrokeSeconds(t.Config != null ? t.Config.id : PlanetId.Earth, Depth(t, p), beamPower);

        /// <summary>U-193: a stroke's time (s) at p with the given tool and its power.</summary>
        public static float StrokeSeconds(TerrainStreamer t, Vector2 p, float power, Meridian.Rig.DigTool tool) =>
            D1Tables.Current.StrokeSeconds(t.Config != null ? t.Config.id : PlanetId.Earth, Depth(t, p), power, tool);

        /// <summary>A dug tile's two rolls, hashed from its cell and a salt (the same tile always gives the same: no save-scum).</summary>
        public static void Rolls(int x, int y, int salt, out float materialRoll, out float pickRoll)
        {
            materialRoll = Hash01(x, y, salt * 2 + 1);
            pickRoll = Hash01(x, y, salt * 2 + 2);
        }

        public static float Hash01(int x, int y, int salt)
        {
            unchecked
            {
                uint h = (uint)x * 0x8DA6B343u ^ (uint)y * 0xD8163841u ^ (uint)salt * 0xCB1AB31Fu;
                h ^= h >> 13; h *= 0x5BD1E995u; h ^= h >> 15;
                return (h & 0xFFFFFF) / 16777216f;
            }
        }

        /// <summary>
        /// The load factor on climbing (climb speed, jetpack lift, grapple reel): 1 − k × load ÷ limit (never under 0); 1 with no limit.
        /// </summary>
        public static float LoadFactor(Inventory inv)
        {
            if (inv == null || float.IsPositiveInfinity(inv.LimitKg) || inv.LimitKg <= 0f) return 1f;
            return Mathf.Max(0f, 1f - Meridian.Progress.SkillStats.LoadK * inv.Weight / inv.LimitKg); // U-175: the Haul branch's k
        }

        /// <summary>
        /// Sells the pack's sellable materials topside for Scrip (a Waystation pays the tables' bonus); -1 and nothing sold below the
        /// Surface Line. Returns the Scrip paid; the paid Scrip also counts as earned this expedition (Surveyor Rank, D-175).
        /// </summary>
        public static int SellPack(Meridian.Core.GameState state, bool topside, bool atWaystation)
        {
            if (state == null) return 0;
            if (!topside) return -1;
            var tables = D1Tables.Current;
            var inv = state.inventory;
            float total = 0f;
            for (int s = 0; s < Inventory.SlotCount; s++)
            {
                var st = inv[s];
                if (st.IsEmpty || !tables.Sellable(st.itemId)) continue;
                total += st.count * tables.Scrip(st.itemId);
                inv.TakeFrom(s, st.count);
            }
            int paid = Mathf.RoundToInt(total * (atWaystation ? 1f + Meridian.Progress.SkillStats.WaystationBonus : 1f)); // U-175: Voyage's prices
            state.scrip += paid;
            state.scripEarned += paid;
            return paid;
        }

        /// <summary>What the pack's sellable materials would fetch now (the Sell panel's total).</summary>
        public static int PackValue(Inventory inv, bool atWaystation)
        {
            var tables = D1Tables.Current;
            float total = 0f;
            for (int s = 0; s < Inventory.SlotCount; s++)
            {
                var st = inv[s];
                if (!st.IsEmpty && tables.Sellable(st.itemId)) total += st.count * tables.Scrip(st.itemId);
            }
            return Mathf.RoundToInt(total * (atWaystation ? 1f + Meridian.Progress.SkillStats.WaystationBonus : 1f));
        }
    }

    /// <summary>
    /// U-174 (D1_TABLES §1): the dirt store: dug matrix tiles (soil, regolith, stone, basalt …), weightless, not sellable; the Builder spends
    /// it on mounds. Full: dug dirt is dropped as a puff (nothing lost but the dirt).
    /// </summary>
    [System.Serializable]
    public sealed class DirtStore
    {
        public int count;
        public int capacity = 60;

        public bool Full => count >= capacity;

        /// <summary>Adds up to n; returns how many fit.</summary>
        public int Add(int n)
        {
            int put = Mathf.Clamp(capacity - count, 0, Mathf.Max(0, n));
            count += put;
            return put;
        }

        /// <summary>Spends up to n; returns how many were spent.</summary>
        public int Spend(int n)
        {
            int take = Mathf.Clamp(n, 0, count);
            count -= take;
            return take;
        }
    }
}
