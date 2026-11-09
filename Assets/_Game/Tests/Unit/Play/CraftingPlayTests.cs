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

            // U-174 (D-174): the Beam's dug tiles give dirt or the tier tables' materials (DigRunTests), so the ore comes from a resource node
            // (U-158's harvest, as the game gives it); the smelt and the craft are this test's subject.
            int hematite = ItemRegistry.Get("hematite").id;
            Assert.AreEqual(0, inv.Add(hematite, 3), "three hematite from a node");
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
            var perchlorate = book.FindRecipe("refine_oxygen_perchlorate");
            Assert.AreEqual(CraftingSystem.Result.Locked, panel.Craft(perchlorate));
            Assert.Greater(panel.Nodes["smelting"].color.b, 0.5f, "Smelting lit in the tree");
            // D-167 (5): the paper cards (U-135): a locked node is the Locked card (no gold band) in the Locked paper tint.
            var locked = panel.Nodes["perchlorate_oxidizer"];
            Assert.AreEqual(0.64f, locked.color.b, 0.05f, "Perchlorate oxidizer on the Locked paper until the Mars beacon");
            var band = locked.transform.Find(Meridian.UI.UiKit.BandName);
            if (band != null) Assert.IsFalse(band.GetComponent<UnityEngine.UI.Image>().enabled, "the Locked card: no gold band");
            panel.SetOpen(false);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
