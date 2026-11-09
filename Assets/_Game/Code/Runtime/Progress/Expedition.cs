using Meridian.Core;
using Meridian.Mining;
using UnityEngine;

namespace Meridian.Progress
{
    /// <summary>
    /// U-178 (D-175, Bible 5.3 §8.1, D1_TABLES §7): the Surveyor Rank and the New Expedition. The Rank (1–10) comes from the Scrip earned by
    /// selling in this expedition (D1Tables.rankScrip). At Rank 10, topside, a New Expedition wipes the bought nodes, the Scrip, the Rank,
    /// the pack and the rocket's hold, keeps the Catalogue, the story, the Datacores, the discovered planets and the buildings (bases,
    /// ladders, the winch: base storage holds no goods in this build, so nothing more is wiped), and makes every Skill Tree stat
    /// × (1 + 0.25 × (n − 1)) (SkillStats; SkillTree.notMultiplied names the stats it leaves alone). The tree has no other way to unbuy a node.
    /// SceneDirector.ReturnToEarthCamp takes the surveyor to Earth's camp.
    /// </summary>
    public static class Expedition
    {
        public const int MaxRank = 10;

        /// <summary>What a New Expedition wipes and keeps (the panel's confirmation lists them).</summary>
        public static readonly string[] Wiped = { "the bought Skill Tree nodes", "your Scrip", "your Surveyor Rank", "the pack", "the rocket's hold" };
        public static readonly string[] Kept = { "the Catalogue", "the story chapters", "your Datacores", "the planets you found", "your buildings" };

        /// <summary>Raised after a New Expedition begins, with its number.</summary>
        public static event System.Action<int> Began;

        public static int Rank(GameState s) => s != null ? D1Tables.Current.Rank(s.scripEarned) : 1;

        /// <summary>The Scrip earned that reaches the next Rank (-1 at Rank 10).</summary>
        public static int NextRankScrip(GameState s)
        {
            int r = Rank(s);
            var t = D1Tables.Current.rankScrip;
            return r < MaxRank && r < t.Length ? t[r] : -1;
        }

        /// <summary>Expedition n's stat multiplier: 1 + step × (n − 1) (step 0.25).</summary>
        public static float Multiplier(int n) => 1f + SkillTree.Current.expeditionStep * Mathf.Max(0, n - 1);

        /// <summary>A New Expedition is offered at Rank 10, topside, only.</summary>
        public static bool CanBegin(GameState s, bool topside) => s != null && topside && Rank(s) >= MaxRank;

        /// <summary>Begins expedition n + 1 (false unless CanBegin): the wipe, the number, the stats re-applied under the new multiplier.</summary>
        public static bool Begin(GameState s, bool topside)
        {
            if (!CanBegin(s, topside)) return false;
            Wipe(s);
            s.expedition = Mathf.Max(1, s.expedition) + 1;
            SkillStats.Apply(s);
            Began?.Invoke(s.expedition);
            return true;
        }

        /// <summary>The wipe: nodes, Scrip (to a new surveyor's 200), Rank (the Scrip earned), the pack, the rocket's hold; the tree's marks
        /// back to the start (else SkillTree.MapOldUnlocks would map them back to nodes on a load).</summary>
        static void Wipe(GameState s)
        {
            s.skillNodes.Clear();
            s.scrip = Meridian.Trade.Market.StartingScrip; // the purse a new surveyor starts with
            s.scripEarned = 0;
            s.inventory.Clear();
            s.cargo.Clear();
            // the thruster mark and the suit tier come from the tree (U-175): back to the start, so wiped nodes keep nothing
            s.thrusterMark = 1;
            s.suitTier = 0;
        }

        static readonly string[] Ones = { "", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX" };
        static readonly string[] Tens = { "", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC" };

        /// <summary>The expedition's numeral on B-206's badge (I–XCIX; the laurel badge from XI).</summary>
        public static string Roman(int n)
        {
            n = Mathf.Clamp(n, 1, 99);
            return Tens[n / 10] + Ones[n % 10];
        }

        /// <summary>B-206's badge for expedition n: the plain one to X, the laurel from XI.</summary>
        public static string BadgeKey(int n) => n >= 11 ? "ui/rank/expedition_badge_laurel" : "ui/rank/expedition_badge";
        public static string InsigniaKey(int rank) => "ui/rank/insignia_" + Mathf.Clamp(rank, 1, MaxRank);
    }
}
