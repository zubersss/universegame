using System.Collections;
using Meridian.Building;
using Meridian.Core;
using Meridian.Hazards;
using Meridian.Items;
using Meridian.Player;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-093 (PlayMode, Earth; Bible v4, D-087): Suit power at 0 conks the surveyor out; after the iris they wake at the
    /// last base piece placed (or beside the ship when there is none) with Suit power full and the pack untouched.
    /// </summary>
    public class ConkOutTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        PlayerController player;
        PlayerVitals vitals;

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            player = side.player;
            vitals = player.GetComponent<PlayerVitals>();
            player.externalInput = true;
            player.intent = default;
            side.hazards.enabled = false;
            side.hazards.RestoreSuit();
            vitals.Restore();
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            Assert.NotNull(side.conkOut, "ConkOut on the PlanetSide root");
        }

        /// <summary>Empties Suit power the way a hazard does: the suit's integrity first, then the reserve.</summary>
        void Drain() => side.hazards.DamageSuit(HazardRules.SuitMax + vitals.maxHealth + 1f);

        static int PackTotal()
        {
            var inv = GameState.Instance.inventory;
            int n = 0;
            for (int s = 0; s < Inventory.SlotCount; s++) n += inv[s].count;
            return n;
        }

        IEnumerator WaitWake(int count)
        {
            float until = Time.realtimeSinceStartup + ConkOut.OutSeconds + 3f;
            while ((side.conkOut.Out || side.conkOut.Count < count) && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 5; i++) yield return new WaitForFixedUpdate();
        }

        [UnityTest]
        public IEnumerator SuitPowerZeroWakesAtTheLastBaseWithTheCargoKept()
        {
            yield return Boot();
            // Cargo in the pack.
            var inv = GameState.Instance.inventory;
            inv.Add(ItemRegistry.Get("graphite").id, 7);
            int pack = PackTotal();
            // A crate 12 m left of the surveyor, on the ground: the base.
            var feet = player.Body.position;
            int bx = Mathf.FloorToInt(feet.x) - 12;
            int by = side.terrain.TopSolidY(bx) + 1;
            var crate = side.bases.Place(new Vector2(bx + 0.5f, by + 0.5f), PieceKind.Crate);
            Assert.NotNull(crate, "a crate placed as the base");
            // Walk away from it, then run out of Suit power.
            var away = feet + new Vector2(6f, 0f);
            player.Body.position = away; player.transform.position = away;
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            Drain();
            Assert.IsTrue(vitals.Dead, "Suit power 0");
            Assert.AreEqual(0f, side.hazards.SuitIntegrity, 1e-4f);
            Assert.IsTrue(side.conkOut.Out, "conked out");
            Assert.IsFalse(player.Body.simulated, "the body rests while the iris is closed");
            yield return WaitWake(1);
            Assert.AreEqual(1, side.conkOut.Count);
            Assert.IsFalse(side.conkOut.Out, "awake");
            Assert.IsTrue(side.conkOut.LastWakeAtBase, "woke at the base");
            TestContext.Out.WriteLine($"[MERIDIAN] conk out: woke at {player.Body.position} (crate x {crate.go.transform.position.x:F1})");
            Assert.AreEqual(Mathf.Floor(crate.go.transform.position.x) + crate.spec.size.x + 0.5f, player.Body.position.x, 0.6f, "standing just right of the base piece");
            Assert.IsTrue(player.Body.simulated);
            Assert.AreEqual(vitals.maxHealth, vitals.health, 1e-4f, "reserve full");
            Assert.AreEqual(HazardRules.SuitMax, side.hazards.SuitIntegrity, 1e-4f, "suit full");
            Assert.AreEqual(pack, PackTotal(), "cargo kept");
            Assert.GreaterOrEqual(inv.Count(ItemRegistry.Get("graphite").id), 7, "the graphite is still in the pack");
            side.bases.Dismantle(crate.go.transform.position); // leave no base for the next case
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator WithNoBaseTheSurveyorWakesBesideTheShip()
        {
            yield return Boot();
            for (int guard = 0; side.bases.pieces.Count > 0 && guard < 64; guard++) side.bases.Dismantle(side.bases.pieces[0].go.transform.position);
            Assert.AreEqual(0, side.bases.pieces.Count, "no base here");
            Assert.NotNull(side.ship);
            var away = player.Body.position + new Vector2(-15f, 0f);
            player.Body.position = away; player.transform.position = away;
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            int pack = PackTotal();
            Drain();
            Assert.IsTrue(side.conkOut.Out);
            yield return WaitWake(1);
            Assert.IsFalse(side.conkOut.LastWakeAtBase, "the ship");
            float shipX = side.ship.transform.position.x;
            TestContext.Out.WriteLine($"[MERIDIAN] conk out: woke at {player.Body.position}, ship x {shipX:F1}");
            Assert.AreEqual(shipX - ConkOut.BesideShip, player.Body.position.x, 1.0f, "beside the ship");
            Assert.IsFalse(vitals.Dead);
            Assert.AreEqual(pack, PackTotal(), "cargo kept");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
