using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Items;
using Meridian.Save;
using Meridian.Space;
using Meridian.Trade;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-052 (PlayMode): dock at the Earth Waystation → sell 10 iron → Scrip rises → repair → undock; Mars prices differ; save/load keeps Scrip and contracts.</summary>
    public class WaystationPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string root;

        [SetUp] public void SetUp() { root = Path.Combine(Application.temporaryCachePath, "meridian_way_" + System.Guid.NewGuid().ToString("N").Substring(0, 6)); SaveSystem.RootOverride = root; }
        [TearDown] public void TearDown() { SaveSystem.RootOverride = null; if (Directory.Exists(root)) Directory.Delete(root, true); }

        [UnityTest]
        public IEnumerator DockTradeRepairUndockAndSave()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            director.SetView(ViewMode.Space);
            for (int i = 0; i < 10; i++) yield return null;
            var bay = director.Space.GetComponent<DockingBay>();
            Assert.NotNull(bay, "DockingBay on the Space root");
            Assert.AreEqual(2, Waystation.All.Count, "Earth and Mars Waystations");
            var ship = director.Space.GetComponentInChildren<SpaceShip>();
            var state = GameState.Instance;
            var inv = state.inventory;
            inv.Clear();

            // Fly up to the Earth Waystation, slowly: it can dock.
            var earth = Waystation.All.Find(w => w.planet == "earth");
            ship.externalInput = true;
            ship.Position = (Vector2)earth.transform.position + new Vector2(4f, -3f);
            ship.Velocity = new Vector2(1f, 0f);
            Assert.AreSame(earth, Waystation.DockableFrom(ship.Position, ship.Velocity), "in range and slow");
            Assert.IsNull(Waystation.DockableFrom(ship.Position, new Vector2(30f, 0f)), "too fast to dock");
            Assert.IsTrue(bay.Dock("earth"));
            Assert.IsTrue(bay.Docked && DockingBay.AnyOpen);
            yield return null;
            Assert.AreEqual(Vector2.zero, ship.Velocity, "held in the bay");

            // Sell 10 iron: Scrip rises by Earth's price.
            inv.Add(ItemRegistry.Get("iron").id, 10);
            int scrip0 = state.scrip;
            Assert.IsTrue(bay.SellItem("iron", 10), bay.LastMessage);
            Assert.AreEqual(scrip0 + 10 * Market.SellPrice("earth", "iron"), state.scrip, "Scrip rises");
            // Repair the hull (no refuelling since U-107).
            state.hull = 80f;
            int scrip1 = state.scrip;
            Assert.AreEqual(20f, bay.Repair(), 1e-3f, "patched up");
            Assert.AreEqual(100f, state.hull, 1e-3f);
            Assert.AreEqual(scrip1 - 20 * Market.RepairPrice("earth"), state.scrip);
            // A contract to carry to Mars.
            Assert.IsTrue(bay.Accept("earth_mars_patches"));
            bay.Undock();
            Assert.IsFalse(bay.Docked);
            yield return null;

            // Mars prices differ: what Halcyon charges (its local factor). U-174 (D1_TABLES §2): what a Waystation pays for a raw material is the
            // tables' Scrip + 25 % at every station (crafted goods keep their local prices).
            Assert.IsTrue(bay.Dock("mars"));
            Assert.AreNotEqual(Market.BuyPrice("earth", "iron"), Market.BuyPrice("mars", "iron"));
            Assert.AreEqual(Market.SellPrice("earth", "iron"), Market.SellPrice("mars", "iron"), "a raw material sells at the tables' price + 25 % anywhere");
            Assert.AreNotEqual(Market.SellPrice("earth", "circuit_board"), Market.SellPrice("mars", "circuit_board"), "crafted goods keep the local prices");
            bay.Undock();

            // Save → change → load: Scrip and contracts come back.
            int scrip2 = state.scrip;
            SaveSystem.Instance.Save();
            state.scrip = 1; state.contracts.Clear();
            yield return SaveSystem.Instance.Load();
            Assert.AreEqual(scrip2, state.scrip, "Scrip saved");
            Assert.AreEqual(1, state.contracts.Count, "contract saved");
            Assert.AreEqual("earth_mars_patches", state.contracts[0].id);
            Assert.IsTrue(state.contracts[0].accepted);
            LogAssert.NoUnexpectedReceived();
        }
    }
}
