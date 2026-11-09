using System;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Items;
using UnityEngine;

namespace Meridian.Progress
{
    /// <summary>
    /// U-175 (D-174, Bible 5.2 §8.1; D1_TABLES §5): the Skill Tree as data (Resources/D1/SkillTree.json, generated from the doc; LEAD
    /// retunes it). Six branches, five rings, 66 nodes; a node needs one bought node among its links (ring 1: the centre; a sideways link is
    /// one more option) and its cost: Scrip, materials from the pack, Datacores. Buying is topside only; it re-applies SkillStats.
    /// </summary>
    [Serializable]
    public sealed class SkillTree
    {
        [Serializable] public sealed class Cost { public string item; public int count; }
        [Serializable] public sealed class Mod { public string stat; public string op; public float value; }
        [Serializable]
        public sealed class Node
        {
            public string id, branch, effect, sideways;
            public int ring, slot, scrip, datacores;
            public Cost[] items = new Cost[0];
            public string[] requires = new string[0];
            public Mod[] mods = new Mod[0];
        }

        public float expeditionStep = 0.25f;
        public string[] notMultiplied = new string[0];
        public Node[] nodes = new Node[0];

        public static readonly string[] Branches = { "dig", "haul", "ascent", "survey", "endurance", "voyage" };
        public const string ResourcePath = "D1/SkillTree";
        static SkillTree current;

        public static SkillTree Current
        {
            get { if (current == null) current = Load(); return current; }
            set { current = value; current?.Index(); }
        }

        public static SkillTree Load()
        {
            var t = Resources.Load<TextAsset>(ResourcePath);
            if (t == null) Debug.LogError($"[MERIDIAN] SkillTree: Resources/{ResourcePath}.json is missing.");
            var d = t != null ? JsonUtility.FromJson<SkillTree>(t.text) : new SkillTree();
            d.Index();
            return d;
        }

        Dictionary<string, Node> byId;
        HashSet<string> notMul;

        void Index()
        {
            byId = new Dictionary<string, Node>();
            foreach (var n in nodes) byId[n.id] = n;
            notMul = new HashSet<string>(notMultiplied ?? new string[0]);
        }

        public Node Get(string id) => id != null && byId != null && byId.TryGetValue(id, out var n) ? n : null;
        public bool Multiplied(string stat) => notMul == null || !notMul.Contains(stat);

        /// <summary>The node's link condition: ring 1 (no links) or any one linked node bought.</summary>
        public bool Linked(Node n, ICollection<string> bought)
        {
            if (n.requires == null || n.requires.Length == 0) return true;
            foreach (var r in n.requires) if (bought.Contains(r)) return true;
            return false;
        }

        public enum BuyResult { Ok, Unknown, AlreadyBought, Locked, NotTopside, Scrip, Materials, Datacores }

        /// <summary>Whether the node can be bought now (and why not).</summary>
        public BuyResult CanBuy(GameState s, string id, bool topside)
        {
            var n = Get(id);
            if (n == null || s == null) return BuyResult.Unknown;
            if (s.skillNodes.Contains(id)) return BuyResult.AlreadyBought;
            if (!Linked(n, s.skillNodes)) return BuyResult.Locked;
            if (!topside) return BuyResult.NotTopside;
            if (s.scrip < n.scrip) return BuyResult.Scrip;
            foreach (var c in n.items)
            {
                var def = ItemRegistry.Get(c.item);
                if (def == null || s.inventory.Count(def.id) < c.count) return BuyResult.Materials;
            }
            if (s.datacores < n.datacores) return BuyResult.Datacores;
            return BuyResult.Ok;
        }

        /// <summary>Buys the node: spends its cost and applies the stats. Topside only.</summary>
        public BuyResult Buy(GameState s, string id, bool topside)
        {
            var r = CanBuy(s, id, topside);
            if (r != BuyResult.Ok) return r;
            var n = Get(id);
            s.scrip -= n.scrip;
            foreach (var c in n.items) s.inventory.Remove(ItemRegistry.Get(c.item).id, c.count);
            s.datacores -= n.datacores;
            s.skillNodes.Add(id);
            SkillStats.Apply(s);
            return BuyResult.Ok;
        }

        /// <summary>The save version the tree arrived in (SaveData v4): an older file maps its unlocks on load.</summary>
        public const int SaveVersion = 4;

        /// <summary>The Blueprint Tree's tool / ship blueprints and the node each becomes (D1_TABLES §5's nearest effect). The crafting
        /// intermediates (smelting, refining, fabrication, the survey module, the oxidizer, the capacitor, the float cells) have no node.</summary>
        public static readonly (string blueprint, string node)[] OldBlueprints =
        {
            ("thruster_mk2", "voy_thrust_2"), ("thruster_mk3", "voy_thrust_3"), ("skip_drive_mk2", "voy_skip_1"),
            ("jetpack_mk2", "asc_jet_1"), ("jetpack_mk3", "asc_jet_2"), ("deep_diamond_tip", "dig_power_2"),
        };

        /// <summary>U-175: a pre-tree save's unlocks as bought nodes (the tree replaces the Blueprint Tree): a blueprint counts when the file
        /// earned it (its story flag or "blueprint:id"; a trade blueprint open from the start says nothing); the fitted thruster mark and the
        /// Mk3 envirosuit count too. Returns how many nodes were granted.</summary>
        public static int MapOldUnlocks(GameState s)
        {
            int before = s.skillNodes.Count;
            if (s.thrusterMark >= 2) s.skillNodes.Add("voy_thrust_2");
            if (s.thrusterMark >= 3) s.skillNodes.Add("voy_thrust_3");
            if (s.suitTier >= 3) s.skillNodes.Add("end_suit_mk3");
            var book = Meridian.Crafting.CraftingDefaults.Blueprints();
            foreach (var (bp, node) in OldBlueprints)
            {
                var b = book.Find(x => x.id == bp);
                bool earned = s.storyFlags.Contains("blueprint:" + bp) || (b != null && !string.IsNullOrEmpty(b.unlockFlag) && s.storyFlags.Contains(b.unlockFlag));
                if (earned) s.skillNodes.Add(node);
            }
            return s.skillNodes.Count - before;
        }
    }
}
