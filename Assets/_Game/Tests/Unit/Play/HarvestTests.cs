using System.Collections;
using Meridian.Core;
using Meridian.Mining;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-158 (D-161 (3), D-162 (5), D-167 (1)-(2)): Earth's surface nodes and buried finds. A node gives one item per Beam stroke for three
    /// strokes, then glances off (harvested) until a game day later; the Builder never harvests (the module gate); its state survives the
    /// planet being rebuilt (leaving and coming back). A pocket stays hidden until a Survey pulse reaches it, then shows with the scan X above
    /// and gives three of its item when the brush opens it; a relic gives a Datacore and a flag; the vault door opens when dug to. Mercury's
    /// Solarite node is cut only in the twilight window. The yield densities are logged for the items-per-minute table (D-167 (2)).
    /// </summary>
    public class HarvestTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static IEnumerator Boot(System.Action<PlanetSideRoot> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            yield return SceneManager.LoadSceneAsync("Core", LoadSceneMode.Single);
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 10f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady);
            timeout = Time.realtimeSinceStartup + 20f;
            while (!director.PlanetSide.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            done(director.PlanetSide);
        }

        static ResourceFinds.Node Nearest(ResourceFinds f, int x)
        {
            ResourceFinds.Node best = null;
            foreach (var n in f.nodes) if (best == null || Mathf.Abs(n.x - x) < Mathf.Abs(best.x - x)) best = n;
            return best;
        }

        static ResourceFinds.Pocket NearestFind(ResourceFinds f, ResourceFinds.Kind kind, int x)
        {
            ResourceFinds.Pocket best = null;
            foreach (var p in f.pockets) if (p.kind == kind && (best == null || Mathf.Abs(p.x - x) < Mathf.Abs(best.x - x))) best = p;
            return best;
        }

        /// <summary>Walks the surveyor to x (the ground streams in round it), as the Beam's 5 m reach would: a dug item drops onto loaded ground.</summary>
        static IEnumerator Near(PlanetSideRoot side, int x)
        {
            var body = side.player.Body;
            body.simulated = false;
            body.position = new Vector2(x + 0.5f, side.terrain.TopSolidY(x) + 2f); side.player.transform.position = body.position;
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            body.simulated = true;
            for (int k = 0; k < 20; k++) yield return new WaitForFixedUpdate();
        }

        [UnityTest]
        public IEnumerator ANodeGivesThreeStrokesThenRegrowsAfterAGameDay()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var finds = side.finds;
            Assert.NotNull(finds, "ResourceFinds on PlanetSide");
            Assert.IsTrue(finds.Active, "Earth is smooth: its nodes and finds are placed");
            Assert.Greater(finds.nodes.Count, 30, "nodes every 50-90 m round Earth");
            var rig = side.rig;
            var owner = rig.owner;
            rig.owner = null; // the strokes at a node far from the surveyor (reach is PlayerRigInput's business)
            try
            {
                var n = Nearest(finds, side.spawnX + 120);
                yield return Near(side, n.x - 3);
                var at = new Vector2(n.x + 0.5f, n.y + 0.6f);
                int paid = finds.Paid;
                // The module gate: the Builder at the node piles earth, never harvests.
                rig.Place(at);
                Assert.AreEqual(ResourceFinds.NodeCharges, n.charges, "the Builder does not harvest");
                Assert.AreEqual(paid, finds.Paid);
                for (int i = 1; i <= ResourceFinds.NodeCharges; i++)
                {
                    Assert.IsTrue(rig.Dig(at), $"stroke {i} cuts the node");
                    Assert.AreEqual(paid + i, finds.Paid, $"stroke {i}: one {n.item}");
                }
                Assert.AreEqual(0, n.charges, "harvested");
                int tiles = GameState.Instance.EditsFor(PlanetId.Earth).Count;
                Assert.IsFalse(rig.Dig(at), "a harvested node glances off the Beam");
                Assert.AreEqual(paid + ResourceFinds.NodeCharges, finds.Paid, "nothing more until it regrows");
                Assert.AreEqual(tiles, GameState.Instance.EditsFor(PlanetId.Earth).Count, "the glancing stroke digs no ground under the node");
                var saved = GameState.Instance.nodeStates.Find(s => s.planet == "earth" && s.x == n.x);
                Assert.NotNull(saved, "the harvested node is in the save");
                Assert.AreEqual(0, saved.charges);
                // Leaving and coming back (the planet rebuilt from the state): still harvested.
                side.Configure(side.Config);
                yield return null;
                var again = Nearest(side.finds, n.x);
                Assert.AreEqual(n.x, again.x, "the same node from the seed");
                Assert.AreEqual(0, again.charges, "still harvested after the planet is rebuilt");
                // A game day later it regrows.
                var clock = Object.FindAnyObjectByType<TimeSystem>();
                Assert.NotNull(clock);
                clock.SetGameSeconds(again.spentAt + ResourceFinds.RegrowGameSeconds + 1.0);
                yield return new WaitForSeconds(2.3f);
                Assert.AreEqual(ResourceFinds.NodeCharges, again.charges, "regrown a game day later");
                Assert.IsTrue(rig.Dig(new Vector2(again.x + 0.5f, again.y + 0.6f)), "cut again");
            }
            finally { rig.owner = owner; }
            // Mercury's Solarite node: only in the twilight window after a flare (U-059's rule); every other node any time.
            Assert.IsTrue(ResourceFinds.Workable(PlanetId.Mercury, "solarite", 1f), "just after a flare: the window");
            Assert.IsFalse(ResourceFinds.Workable(PlanetId.Mercury, "solarite", Meridian.Items.OnlyHere.SolariteWindow + 1f), "past the window: crusted");
            Assert.IsFalse(ResourceFinds.Workable(PlanetId.Mercury, "solarite", -1f), "during the flare");
            Assert.IsTrue(ResourceFinds.Workable(PlanetId.Mercury, "nickel", -1f), "nickel any time");
            Assert.IsTrue(ResourceFinds.Workable(PlanetId.Earth, "iron", float.PositiveInfinity));
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator SurveyedFindsShowAndPayWhenDug()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var finds = side.finds;
            Assert.IsTrue(finds.Active);
            var rig = side.rig;
            var owner = rig.owner;
            rig.owner = null;
            try
            {
                // A pocket: hidden, then revealed by the pulse (its X above), then three of its item when dug.
                var p = NearestFind(finds, ResourceFinds.Kind.Pocket, side.spawnX + 200);
                Assert.NotNull(p, "pockets placed");
                yield return Near(side, p.x - 3);
                int depth = side.terrain.OriginalTop(p.x) - p.y;
                Assert.That(depth, Is.InRange(ResourceFinds.PocketDepthMin, ResourceFinds.PocketDepthMax), "2-10 m under the original surface");
                Assert.IsFalse(p.view.enabled || p.mark.enabled, "hidden before the scan");
                var centre = new Vector2(p.x + 0.5f, p.y + 0.5f);
                var found = finds.Reveal(centre + Vector2.up * 4f, 8f);
                Assert.Contains(p.item, found, "the pulse reports the pocket's item (the scanner catalogues it)");
                Assert.IsTrue(p.revealed && p.view.enabled && p.mark.enabled, "shown in the cutaway, the scan X pulsing above");
                Assert.AreEqual(side.terrain.SurfaceAt(p.x + 0.5f), p.mark.transform.position.y, 0.05f, "the X on the ground above");
                int paid = finds.Paid;
                Assert.IsTrue(rig.Dig(centre), "the brush opens the pocket");
                Assert.AreEqual(paid + ResourceFinds.PocketYield, finds.Paid, "three of its item");
                Assert.IsTrue(p.spent);
                Assert.IsFalse(p.view.enabled || p.mark.enabled, "a dug pocket is gone");
                rig.Dig(centre + Vector2.left);
                Assert.AreEqual(paid + ResourceFinds.PocketYield, finds.Paid, "it pays once");

                // A relic (Earth's data cache): one Datacore and a flag.
                var r = NearestFind(finds, ResourceFinds.Kind.Relic, side.spawnX);
                Assert.NotNull(r, "a data cache every 400 m");
                yield return Near(side, r.x - 3);
                int cores = GameState.Instance.datacores;
                Assert.IsTrue(rig.Dig(new Vector2(r.x + 0.5f, r.y + 0.5f)));
                Assert.AreEqual(cores + 1, GameState.Instance.datacores, "one Datacore");
                Assert.IsTrue(GameState.Instance.HasFlag($"relic:earth:{r.x}"), "the relic's story flag");

                // The Warden vault door: opens when dug to (its clip runs), and stays open.
                var v = NearestFind(finds, ResourceFinds.Kind.Vault, side.spawnX);
                Assert.NotNull(v, "a vault door on Earth");
                yield return Near(side, v.x - 3);
                Assert.AreEqual(-1, v.openFrame);
                Assert.IsTrue(rig.Dig(new Vector2(v.x + 0.5f, v.y + 0.5f)), "dug to");
                Assert.GreaterOrEqual(v.openFrame, 0, "the door opens");
                Assert.IsTrue(GameState.Instance.HasFlag($"vault_door:earth:{v.x}"));
                yield return new WaitForSeconds(1f);
                Assert.AreEqual(ResourceFinds.VaultOpenFrames - 1, v.openFrame, "its open clip played through");
                Assert.IsTrue(v.view.enabled, "the open door stays drawn");

                // After a rebuild the dug pocket stays spent and the vault stays open.
                side.Configure(side.Config);
                yield return null;
                Assert.IsTrue(NearestFind(side.finds, ResourceFinds.Kind.Pocket, p.x).spent, "the dug pocket stays spent (its tile stays dug)");
                Assert.AreEqual(ResourceFinds.VaultOpenFrames - 1, NearestFind(side.finds, ResourceFinds.Kind.Vault, v.x).openFrame, "the vault stays open");
            }
            finally { rig.owner = owner; }

            // D-167 (2): the yield densities for the items-per-minute table (the 0.4.8 digging rate is the ore tiles the brush still reaches).
            var t = side.terrain;
            int w = side.Config.worldWidth, ore = 0;
            var oreItems = new System.Collections.Generic.HashSet<int>();
            // 0.4.8's ore on Earth: the tiles that drop an ore item (hematite seams, ice) or a node item; raw iron / copper / carbon / silica had no dig source.
            foreach (var key in new[] { "hematite", "water_ice", "iron", "copper", "carbon", "silica" }) { var d = Meridian.Items.ItemRegistry.Get(key); if (d != null) oreItems.Add(d.id); }
            for (int x = 0; x < w; x++)
            {
                int top = t.OriginalTop(x);
                if (top == int.MinValue) continue;
                for (int y = top - 9; y <= top; y++) if (oreItems.Contains(Meridian.Items.ItemRegistry.DropOf(t.BaseGenerator.TileAt(x, y)))) ore++;
            }
            int pockets = 0;
            foreach (var q in side.finds.pockets) if (q.kind == ResourceFinds.Kind.Pocket) pockets++;
            TestContext.Out.WriteLine($"[MERIDIAN] u158 yields per 100 m of Earth: ore tiles in the top 10 m {ore * 100f / w:F2}; node items {side.finds.nodes.Count * ResourceFinds.NodeCharges * 100f / w:F2}; pocket items {pockets * ResourceFinds.PocketYield * 100f / w:F2}; nodes {side.finds.nodes.Count}, pockets {pockets}, width {w}");
            // D-170: the items-per-minute table for the owner's page (walking at PlayerTuning.WalkSpeed, every node cut, every pocket surveyed and dug).
            float perMin = Meridian.Player.PlayerTuning.WalkSpeed * 60f / 100f;
            TestContext.Out.WriteLine($"[MERIDIAN] u158 items per minute at walking pace ({Meridian.Player.PlayerTuning.WalkSpeed * 60f:F0} m a minute): 0.4.8 digging {ore * 100f / w * perMin:F1}; 0.5.0 nodes {side.finds.nodes.Count * ResourceFinds.NodeCharges * 100f / w * perMin:F1}, pockets (upper bound) {pockets * ResourceFinds.PocketYield * 100f / w * perMin:F1}");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
