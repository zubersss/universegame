using System.Collections;
using Meridian.Core;
using Meridian.Crafting;
using Meridian.Items;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-051 (PlayMode): mine iron ore → smelt at the camp's Smelter → craft a suit patch at the Pilgrim's Fabricator.</summary>
    public class CraftingPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator MineIronSmeltCraftASuitPatch()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            var player = side.player;
            var rig = side.rig;
            var t = side.terrain;
            var inv = GameState.Instance.inventory;
            inv.Clear();
            var hud = Object.FindAnyObjectByType<Meridian.UI.SideHud>();
            var panel = hud.Crafting;
            var book = RecipeBook.Active;
            Assert.NotNull(book, "RecipeBook in Resources");
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();

            // Mine iron ore: three hematite seams beside the surveyor, dug with the Beam and picked up.
            int hematite = ItemRegistry.Get("hematite").id;
            for (int n = 0; n < 3; n++)
            {
                Vector2 feet = player.Body.position;
                int x = Mathf.FloorToInt(feet.x) + 1, y = Mathf.FloorToInt(feet.y);
                Assert.IsTrue(rig.Place(new Vector2(x + 0.5f, y + 0.5f), TileId.Hematite), "an ore seam");
                Assert.IsTrue(rig.Dig(new Vector2(x + 0.5f, y + 0.5f)), "Beam digs the ore");
                float until = Time.realtimeSinceStartup + 5f;
                while (inv.Count(hematite) < n + 1 && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
            }
            Assert.AreEqual(3, inv.Count(hematite), "three ore picked up");

            // Smelt at the camp's Smelter.
            var smelter = Object.FindObjectsByType<CraftingStation>(FindObjectsInactive.Exclude);
            CraftingStation camp = null;
            foreach (var s in smelter) if (s.kind == Station.Smelter) camp = s;
            Assert.NotNull(camp, "the spawn camp offers a Smelter");
            var smelt = book.FindRecipe("smelt_hematite");
            panel.SetOpen(true);
            player.Body.position = new Vector2(camp.transform.position.x + 30f, player.Body.position.y);
            yield return new WaitForFixedUpdate();
            Assert.AreEqual(CraftingSystem.Result.NoStation, panel.Craft(smelt), "too far from the Smelter");
            player.Body.position = new Vector2(camp.transform.position.x + 1f, camp.transform.position.y + 0.5f);
            player.transform.position = player.Body.position;
            yield return new WaitForFixedUpdate();
            Assert.AreEqual(CraftingSystem.Result.Crafted, panel.Craft(smelt), panel.LastMessage);
            Assert.AreEqual(0, inv.Count(hematite));
            Assert.AreEqual(2, inv.Count(ItemRegistry.Get("smelter_bar_iron").id), "two iron bars");

            // Craft a suit patch at the Pilgrim's Fabricator.
            var patch = book.FindRecipe("fab_suit_patch");
            Vector2 ship = side.ship.transform.position;
            player.Body.position = new Vector2(ship.x - 3f, ship.y - 1f);
            player.transform.position = player.Body.position;
            yield return new WaitForFixedUpdate();
            Assert.AreEqual(CraftingSystem.Result.Crafted, panel.Craft(patch), panel.LastMessage);
            Assert.AreEqual(1, inv.Count(ItemRegistry.Get("suit_patch").id), "a suit patch");
            Assert.AreEqual(0, inv.Count(ItemRegistry.Get("smelter_bar_iron").id), "the bars went into it");

            // A story blueprint stays locked until its beacon.
            var perchlorate = book.FindRecipe("refine_fuel_perchlorate");
            Assert.AreEqual(CraftingSystem.Result.Locked, panel.Craft(perchlorate));
            Assert.IsTrue(panel.Nodes["smelting"].color.a > 0.5f, "Smelting lit in the tree");
            Assert.IsTrue(panel.Nodes["perchlorate_oxidizer"].color.a < 0.5f, "Perchlorate oxidizer dim until the Mars beacon");
            panel.SetOpen(false);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
