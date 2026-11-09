using System;
using System.Collections.Generic;
using Meridian.Items;
using Meridian.Planets;
using UnityEngine;

namespace Meridian.Mining
{
    /// <summary>
    /// U-174 (D-174, Bible 5.2 §8.1): the D1 dig run's numbers, read from Resources/D1/D1Tables.json, the data form of LEAD's
    /// docs/D1_TABLES.md. LEAD retunes the json, never this code: the depth tiers (hardness and material chance), each planet's base hardness
    /// and tier tables (the last row of a tier is its pocket item), the materials' Scrip and kg, the pack, the dirt store and the stroke.
    /// </summary>
    [Serializable]
    public sealed class D1Tables
    {
        [Serializable] public sealed class Tier
        {
            public string name; public float fromM; public float hardness = 1f; public float materialChance;
            /// <summary>The tier's colour chip on the HUD's depth tag (#RRGGBB).</summary>
            public string chip;
            public Color ChipColor => ColorUtility.TryParseHtmlString(chip, out var c) ? c : Color.gray;
        }
        [Serializable] public sealed class Row { public string item; public float weight; public bool coldTrapOnly; public string elseItem; }
        [Serializable] public sealed class TierTable { public Row[] rows; }
        [Serializable] public sealed class Planet { public string id; public float hardness = 1f; public TierTable[] tiers; }
        [Serializable] public sealed class Material { public string item; public float scrip; public float kg; }

        public float surfaceLineDepth = 2f, strokeBaseSeconds = 0.25f, strokeCapSeconds = 8f, beamPowerStart = 1f;
        public float packLimitKg = 30f, loadK = 0.5f, waystationBonus = 0.25f;
        public int dirtStoreStart = 60, pocketCount = 3;

        /// <summary>U-176 (D1_TABLES §4 "Climbing", LEAD 23:5x): the ways back up. The pack's load factor scales every speed here.</summary>
        [Serializable] public sealed class AscentTable
        {
            /// <summary>The ladder's climb (m/s, × the Climb stat) and the dirt a ladder metre costs (asc_ladder_2 lowers it).</summary>
            public float ladderClimb = 2.5f, ladderDirtPerM = 2f;
            /// <summary>The Grapple's reel (m/s, × the reel stat) and the hook's flight (m/s).</summary>
            public float grappleReel = 4f, hookSpeed = 40f;
            /// <summary>The winch's ride (m/s): the ring-5 reward beats the grapple.</summary>
            public float winchSpeed = 6f;
            /// <summary>The recall beacon's wait before it lifts the surveyor topside (s).</summary>
            public float recallSeconds = 5f;
            /// <summary>The steepest ground (degrees) the surveyor stands and walks on; steeper slides (asc_climb_1 sets 40).</summary>
            public float walkRampDeg = 35f;
        }
        public AscentTable ascent = new AscentTable();
        /// <summary>D1_TABLES §7 (D-175): the Scrip earned this expedition (sales only) for Surveyor Rank 1..10.</summary>
        public int[] rankScrip = { 0, 300, 800, 1800, 3500, 7000, 14000, 28000, 50000, 80000 };

        /// <summary>The Surveyor Rank (1..10) for the Scrip earned this expedition.</summary>
        public int Rank(int scripEarned)
        {
            int r = 1;
            for (int i = 1; i < rankScrip.Length; i++) if (scripEarned >= rankScrip[i]) r = i + 1;
            return r;
        }
        public Tier[] tiers = new Tier[0];
        public Planet[] planets = new Planet[0];
        public Material[] materials = new Material[0];

        public const string ResourcePath = "D1/D1Tables";
        static D1Tables current;

        /// <summary>The tables in use (loaded once from Resources; tests may set their own).</summary>
        public static D1Tables Current
        {
            get { if (current == null) current = Load(); return current; }
            set { current = value; if (current != null) current.Index(); }
        }

        public static D1Tables Load()
        {
            var t = Resources.Load<TextAsset>(ResourcePath);
            var d = t != null ? JsonUtility.FromJson<D1Tables>(t.text) : new D1Tables();
            if (t == null) Debug.LogError($"[MERIDIAN] D1Tables: Resources/{ResourcePath}.json is missing.");
            d.Index();
            return d;
        }

        public static D1Tables FromJson(string json)
        {
            var d = JsonUtility.FromJson<D1Tables>(json);
            d.Index();
            return d;
        }

        Dictionary<int, Material> byItem;

        void Index()
        {
            byItem = new Dictionary<int, Material>();
            if (materials == null) return;
            foreach (var m in materials)
            {
                var def = ItemRegistry.Get(m.item);
                if (def != null) byItem[def.id] = m;
                else Debug.LogError($"[MERIDIAN] D1Tables: '{m.item}' is not an item.");
            }
        }

        /// <summary>The depth tier (0 = T1 Topsoil … 4 = T5 Core) at `depthM` metres under the Surface Line.</summary>
        public int TierIndex(float depthM)
        {
            int k = 0;
            for (int i = 0; i < tiers.Length; i++) if (depthM >= tiers[i].fromM) k = i;
            return k;
        }

        public Planet PlanetOf(PlanetId id)
        {
            string s = id.ToString();
            foreach (var p in planets) if (p.id == s) return p;
            return null;
        }

        /// <summary>The planet's base hardness (1 where the tables do not list it: the giants are not dug).</summary>
        public float PlanetHardness(PlanetId id) => PlanetOf(id)?.hardness ?? 1f;

        /// <summary>A Beam stroke's time: base × planet hardness × tier hardness ÷ Beam power, capped (no depth gate).</summary>
        public float StrokeSeconds(PlanetId id, float depthM, float beamPower)
        {
            float h = tiers.Length > 0 ? tiers[TierIndex(depthM)].hardness : 1f;
            return Mathf.Min(strokeCapSeconds, strokeBaseSeconds * PlanetHardness(id) * h / Mathf.Max(0.01f, beamPower));
        }

        /// <summary>The item's weight in the pack (kg; 0 for anything the tables do not list: crafted goods, tools).</summary>
        public float Kg(int itemId) => byItem != null && byItem.TryGetValue(itemId, out var m) ? m.kg : 0f;

        /// <summary>The item's topside price (Scrip; 0 when not sellable).</summary>
        public float Scrip(int itemId) => byItem != null && byItem.TryGetValue(itemId, out var m) ? m.scrip : 0f;

        public bool Sellable(int itemId) => byItem != null && byItem.ContainsKey(itemId);

        /// <summary>
        /// What a dug tile gives: 0 for dirt (the dirt store), else a material's item id. `materialRoll` (0..1) below the tier's material
        /// chance gives a material; `pickRoll` (0..1) picks its row by weight. A cold-trap-only row gives its `elseItem` outside a cold trap.
        /// </summary>
        public int Roll(PlanetId id, int tier, float materialRoll, float pickRoll, bool coldTrap)
        {
            if (tiers.Length == 0 || materialRoll >= tiers[Mathf.Clamp(tier, 0, tiers.Length - 1)].materialChance) return 0;
            var rows = Rows(id, tier);
            if (rows == null || rows.Length == 0) return 0;
            float total = 0f;
            foreach (var r in rows) total += r.weight;
            float pick = pickRoll * total;
            foreach (var r in rows)
            {
                pick -= r.weight;
                if (pick < 0f) return ItemId(r.coldTrapOnly && !coldTrap ? r.elseItem : r.item);
            }
            var last = rows[rows.Length - 1];
            return ItemId(last.coldTrapOnly && !coldTrap ? last.elseItem : last.item);
        }

        /// <summary>A pocket's item: its tier's rarest (the tier table's last row).</summary>
        public int Rarest(PlanetId id, int tier)
        {
            var rows = Rows(id, tier);
            return rows == null || rows.Length == 0 ? 0 : ItemId(rows[rows.Length - 1].item);
        }

        public Row[] Rows(PlanetId id, int tier)
        {
            var p = PlanetOf(id);
            if (p == null || p.tiers == null || p.tiers.Length == 0) return null;
            return p.tiers[Mathf.Clamp(tier, 0, p.tiers.Length - 1)].rows;
        }

        static int ItemId(string key) => ItemRegistry.Get(key)?.id ?? 0;
    }
}
