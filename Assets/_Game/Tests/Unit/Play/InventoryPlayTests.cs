using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Items;
using Meridian.Save;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-045 (PlayMode): dig → pickup → count rises → place → count falls → save → load identical; the Tab panel; no GC while it's closed.</summary>
    public class InventoryPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string root;

        [SetUp]
        public void SetUp()
        {
            root = Path.Combine(Application.temporaryCachePath, "meridian_inv_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = root;
        }

        [TearDown]
        public void TearDown()
        {
            SaveSystem.RootOverride = null;
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }

        static IEnumerator Boot(System.Action<SceneDirector> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady);
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate(); // surveyor settles
            done(director);
        }

        [UnityTest]
        public IEnumerator DigPickupPlaceSaveLoad()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var side = director.PlanetSide;
            var state = GameState.Instance;
            var inv = state.inventory;
            inv.Clear();
            var rig = side.rig;
            var t = side.terrain;
            var player = side.player;

            // Dig the tile under the surveyor's feet: its item drops right there and is picked up.
            Vector2 feet = player.Body.position;
            int x = Mathf.FloorToInt(feet.x), y = t.TopSolidY(x);
            byte dug = t.GetTile(x, y);
            int item = ItemRegistry.DropOf(dug);
            Assert.AreNotEqual(0, item, "the surface tile drops an item");
            Assert.IsTrue(rig.Dig(new Vector2(x + 0.5f, y + 0.5f)), "Beam digs");
            float until = Time.realtimeSinceStartup + 5f;
            while (inv.Count(item) == 0 && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
            Assert.AreEqual(1, inv.Count(item), "picked up: count rises");
            Assert.AreEqual(0, rig.drops.Live.Count, "the drop left the world");

            // Place it back: the Builder uses the selected slot and its count falls.
            int slot = -1;
            for (int i = 0; i < Inventory.SlotCount; i++) if (inv[i].itemId == item && !inv[i].IsEmpty) slot = i;
            inv.Select(slot);
            inv.Add(item, 4); // 5 in the stack
            int px = x + 2, py = t.TopSolidY(px) + 1; // U-157 P-54: on the ground 2 m off (the round scoop under the feet lowers the surveyor; the Builder reaches 5 m)
            Assert.AreEqual(TileId.Air, t.GetTile(px, py));
            Assert.IsTrue(rig.Place(new Vector2(px + 0.5f, py + 0.5f)), "Builder places from the inventory");
            // U-157 (D-162 (3)): on Earth's smooth ground the Builder piles the planet's one ground material, spending a carried ground item.
            Assert.AreEqual(rig.Brush ? rig.GroundMaterial : ItemRegistry.Get(item).placeTile, t.GetTile(px, py));
            Assert.AreEqual(4, inv.Count(item), "count falls");

            // A non-placeable selection places nothing.
            inv.Add(ItemRegistry.Get("iron").id, 7);
            for (int i = 0; i < Inventory.SlotCount; i++) if (inv[i].itemId == ItemRegistry.Get("iron").id) inv.Select(i);
            if (rig.Brush)
            {
                // U-157: no block is chosen (no hotbar of blocks): with iron selected the mound still piles from the ground items carried,
                // and the iron is never spent.
                Assert.IsTrue(rig.Place(new Vector2(px + 0.5f, py + 1.5f)), $"the mound piles from the ground items, whatever is selected (target {Vector2.Distance(new Vector2(px + 0.5f, py + 1.5f), player.transform.position):F2} m from the surveyor)");
                Assert.AreEqual(3, inv.Count(item), "a ground item spent");
            }
            else Assert.IsFalse(rig.Place(new Vector2(px + 0.5f, py + 1.5f)), "iron isn't a tile");
            Assert.AreEqual(7, inv.Count(ItemRegistry.Get("iron").id));

            // Save → change → load: identical.
            side.hazards.SetSuit(61f);
            var before = new ItemStack[Inventory.SlotCount];
            for (int i = 0; i < Inventory.SlotCount; i++) before[i] = inv[i];
            int selected = inv.Selected;
            var save = SaveSystem.Instance;
            save.Save();
            inv.Clear();
            inv.Add(ItemRegistry.Get("copper").id, 99);
            side.hazards.SetSuit(100f);
            yield return save.Load();
            side = director.PlanetSide;
            float settle = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < settle) yield return null;
            for (int i = 0; i < Inventory.SlotCount; i++)
            {
                Assert.AreEqual(before[i].count, inv[i].count, $"slot {i} count");
                if (!before[i].IsEmpty) Assert.AreEqual(before[i].itemId, inv[i].itemId, $"slot {i} item");
            }
            Assert.AreEqual(selected, inv.Selected, "Builder slot");
            Assert.AreEqual(61f, side.hazards.SuitIntegrity, 0.5f, "suit integrity saved (D-032, SaveData v2)");
            Assert.AreEqual(SaveData.CurrentVersion, SaveSystem.ReadState(save.SlotFolder).version);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator TabPanelShowsTheSlotsAndAllocatesNothingWhileClosed()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var hud = Object.FindAnyObjectByType<Meridian.UI.SideHud>();
            Assert.NotNull(hud.Inventory, "panel built with the HUD");
            var panel = hud.Inventory;
            var inv = GameState.Instance.inventory;
            inv.Clear();
            inv.Add(ItemRegistry.Get("iron").id, 1200);
            inv.Add(TileId.Stone, 3);
            Assert.IsFalse(panel.IsOpen);

            // Closed: the panel has no Update at all (BudgetGate's 0 B GC rows run with it closed).
            for (int i = 0; i < 60; i++) { inv.Select(i % 2); yield return null; }
            Assert.IsFalse(panel.enabled, "closed: disabled, no Update");

            panel.SetOpen(true);
            Assert.IsTrue(panel.IsOpen && Meridian.UI.InventoryPanel.AnyOpen);
            float until = Time.realtimeSinceStartup + 5f;
            while (!(panel.Icons[0].enabled && panel.Icons[2].enabled) && Time.realtimeSinceStartup < until) yield return null; // both icons arrive (shared cache, U-058)
            Assert.AreEqual("999", panel.Counts[0].text);
            Assert.AreEqual("201", panel.Counts[1].text);
            Assert.AreEqual("3", panel.Counts[2].text);
            Assert.IsTrue(panel.Icons[0].enabled, "iron icon (B-013)");
            Assert.IsTrue(panel.Icons[2].enabled, "stone icon");
            Assert.AreEqual("", panel.Counts[3].text, "empty slot");
            panel.SetOpen(false);
            Assert.IsFalse(Meridian.UI.InventoryPanel.AnyOpen);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
