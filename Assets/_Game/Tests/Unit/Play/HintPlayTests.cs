using System.Collections;
using System.Collections.Generic;
using System.IO;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Player;
using Meridian.Save;
using Meridian.Terrain;
using Meridian.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-185 (PlayMode; B-213): the first hour's hints. Each fires once on its trigger (DIG DOWN at Earth's camp, THE SURFACE LINE on the
    /// first crossing below it, PACK FULL on the first refused pickup and CLIMB BACK UP after it, SELL topside with a haul, THE SKILL TREE
    /// after the first sale), goes when its action is done or its time is up, and never fires again, not after a save and a load either;
    /// none shows during a transition or a panel; "Show hints" off shows none; "Reset hints" lets them fire again.
    /// </summary>
    public class HintPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string root;
        bool showHints0;
        PlanetSideRoot side;
        PlayerController player;
        GameState state;
        SideHud hud;
        HintCards hints;
        readonly List<string> fired = new List<string>();

        [SetUp]
        public void SetUp()
        {
            root = Path.Combine(Application.temporaryCachePath, "meridian_hint_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = root;
            showHints0 = GameSettings.ShowHints;
            GameSettings.ShowHints = true;
            HintCards.Suppressed = false;
            HintCards.Blocked = null;
        }

        [TearDown]
        public void TearDown()
        {
            HintCards.Suppressed = true;
            HintCards.Blocked = null;
            GameSettings.ShowHints = showHints0;
            SaveSystem.RootOverride = null;
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }

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
            if (side.hazards != null) side.hazards.enabled = false;
            side.creatures.autoSpawn = false; side.creatures.DespawnAll();
            player = side.player;
            state = GameState.Instance;
            hud = side.sideHud;
            hints = hud.Hints;
            Assert.NotNull(hints, "the hint cards beside the HUD");
            // a fresh first hour: whatever came up while the scene loaded goes, and nothing has been seen
            hints.Dismiss();
            state.hintsSeen.Clear();
            state.inventory.Clear();
            hints.History.Clear();
            fired.Clear();
            hints.Fired += id => fired.Add(id);
            player.externalInput = true;
        }

        IEnumerator Frames(int n) { for (int i = 0; i < n; i++) yield return null; }

        IEnumerator Until(System.Func<bool> ok, float seconds)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while (!ok() && Time.realtimeSinceStartup < until) yield return null;
        }

        void Put(Vector2 feet) { player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero; }

        /// <summary>A 3-wide hole 12 m deep beside the camp (its floor under the Surface Line).</summary>
        int Hole(int x0)
        {
            float top = side.terrain.SurfaceAt(x0 + 1.5f);
            int floor = Mathf.FloorToInt(top) - 12;
            for (int y = floor; y <= Mathf.CeilToInt(top) + 2; y++) for (int x = x0; x < x0 + 3; x++) side.terrain.SetTile(x, y, TileId.Air);
            return floor;
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator EachHintFiresOnceOnItsTriggerAndNeverAgain()
        {
            yield return Boot();
            int camp = Mathf.FloorToInt(Meridian.Planet.POI.PoiCatalog.SpawnCamp.CenterX);
            var topside = new Vector2(camp + 14.5f, side.terrain.SurfaceAt(camp + 14.5f) + 0.3f);
            Put(topside);

            // DIG DOWN at the camp; the first dig takes it down
            yield return Until(() => hints.Showing != null, 4f);
            Assert.AreEqual(HintCards.DigDown, hints.Showing, "DIG DOWN on landing at Earth's camp");
            Assert.IsTrue(hints.Card.gameObject.activeSelf);
            StringAssert.Contains("DIG DOWN", hints.TitleText.text);
            var rig = player.GetComponent<PlayerRigInput>();
            rig.rig.Dig(player.Body.position + new Vector2(1.5f, -0.5f));
            yield return Frames(3);
            Assert.IsNull(hints.Showing, "its action done: the first dig");

            // THE SURFACE LINE on the first crossing below it: up its full ShowSeconds
            int x0 = camp + 20;
            int floor = Hole(x0);
            yield return Frames(3);
            Put(new Vector2(x0 + 1.5f, floor + 0.05f));
            yield return Until(() => hints.Showing != null, 2f);
            Assert.AreEqual(HintCards.SurfaceLine, hints.Showing);
            Assert.IsTrue(hints.Arrow.enabled, "its arrow at the depth readout");
            Assert.IsFalse(hints.ArrowOverCard, "U-188: the arrow leaves from the card's edge, never over the card");
            float t0 = Time.realtimeSinceStartup;
            yield return Until(() => hints.Showing == null, HintCards.ShowSeconds + 2f);
            Assert.AreEqual(HintCards.ShowSeconds, Time.realtimeSinceStartup - t0, 0.6f, "about 6 s");

            // PACK FULL on the first refused pickup, CLIMB BACK UP right after it (still under the line)
            int clay = ItemRegistry.Get(D1Tables.Current.materials[0].item).id;
            state.inventory.Add(clay, state.inventory.FitsByWeight(clay));
            state.inventory.Add(clay, 1); // refused
            yield return Until(() => hints.Showing != null, 2f);
            Assert.AreEqual(HintCards.PackFull, hints.Showing);
            Assert.IsTrue(hints.Arrow.enabled, "U-188: its arrow at the HUD's pack tag");
            Assert.IsFalse(hints.ArrowOverCard, "U-188: PACK FULL's arrow off its card (it lay over the words in 0.6.0's dev smoke)");
            StringAssert.Contains(" kg", hud.PackKg.text, "U-188: the pack's load on the HUD");
            hints.Dismiss();
            yield return Until(() => hints.Showing != null, 2f);
            Assert.AreEqual(HintCards.ClimbUp, hints.Showing, "CLIMB BACK UP right after");
            Assert.AreEqual("SPC", hints.KeyCap.text, "the jetpack's key on the cap (shortened to fit)");
            StringAssert.Contains("Hold SPACE", hints.BodyText.text, "and named in full in the words");
            Put(topside);
            yield return Frames(4);
            Assert.AreNotEqual(HintCards.ClimbUp, hints.Showing, "topside: its action done");

            // SELL topside with the haul; the Sell panel takes it down; THE SKILL TREE after the first sale, once the panel closes
            yield return Until(() => hints.Showing == HintCards.Sell, 2f);
            Assert.AreEqual(HintCards.Sell, hints.Showing);
            Assert.AreEqual("G", hints.KeyCap.text, "its key cap: the Sell key");
            hud.Sell.SetOpen(true);
            yield return Frames(3);
            Assert.IsNull(hints.Showing, "the Sell panel opened: done");
            Assert.Greater(hud.Sell.SellAll(), 0, "the first sale");
            yield return Frames(10);
            Assert.IsNull(hints.Showing, "nothing shows over an open panel");
            hud.Sell.SetOpen(false);
            yield return Until(() => hints.Showing != null, 2f);
            Assert.AreEqual(HintCards.SkillTree, hints.Showing);
            Assert.IsTrue(hints.Arrow.enabled, "its arrow at the Rank slot");
            Assert.IsFalse(hints.ArrowOverCard, "U-188: the arrow off the card");
            hud.Skills.SetOpen(true);
            yield return Frames(3);
            Assert.IsNull(hints.Showing, "the tree opened: done");
            hud.Skills.SetOpen(false);
            CollectionAssert.AreEqual(HintCards.All, fired, "each once, in the first hour's order");

            // never again: every trigger once more, and after a save and a load
            IEnumerator Retrigger()
            {
                Put(new Vector2(x0 + 1.5f, floor + 0.05f)); yield return Frames(5);
                state.inventory.Add(clay, state.inventory.FitsByWeight(clay)); state.inventory.Add(clay, 1); yield return Frames(5);
                Put(topside); yield return Frames(5);
                hud.Sell.SellAll(); yield return Frames(5);
                rig.rig.Dig(player.Body.position + new Vector2(-1.5f, -0.5f)); yield return Frames(5);
            }
            yield return Retrigger();
            Assert.AreEqual(6, fired.Count, "none fires twice");
            SaveSystem.Instance.Save();
            state.hintsSeen.Clear();
            yield return SaveSystem.Instance.Load();
            Assert.AreEqual(6, state.hintsSeen.Count, "the seen hints come back with the file");
            side = Object.FindAnyObjectByType<SceneDirector>().PlanetSide; player = side.player; player.externalInput = true;
            hud = side.sideHud; hints = hud.Hints; hints.Fired += id => fired.Add(id);
            rig = player.GetComponent<PlayerRigInput>();
            yield return Frames(10);
            yield return Retrigger();
            Assert.AreEqual(6, fired.Count, "not after a save and a load either");
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>U-188 (BLENDER's 0.6.0 smoke read: THE SURFACE LINE over the ship's climb): no card is asked for or shown aboard the ship,
        /// and a card asked for whose condition has passed by its turn is dropped, never shown late.</summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator NoCardAboardAndAStaleOneIsDropped()
        {
            yield return Boot();
            int camp = Mathf.FloorToInt(Meridian.Planet.POI.PoiCatalog.SpawnCamp.CenterX);
            // 75 m from the camp: DIG DOWN no longer applies there (a copy queued while booting is dropped too)
            var away = new Vector2(camp + 75.5f, side.terrain.SurfaceAt(camp + 75.5f) + 0.3f);
            Put(away);
            yield return Frames(5);
            hints.Dismiss();
            yield return Frames(5);
            Assert.IsNull(hints.Showing, "away from the camp: nothing up");
            state.hintsSeen.Add(HintCards.DigDown);
            // a card queued under the line, then the surveyor back topside before its turn: dropped
            HintCards.Blocked = () => true;
            hints.Request(HintCards.SurfaceLine);
            yield return Frames(3);
            HintCards.Blocked = null;
            yield return Frames(10);
            Assert.AreNotEqual(HintCards.SurfaceLine, hints.Showing, "topside again: THE SURFACE LINE dropped, not shown late");
            Assert.IsFalse(state.hintsSeen.Contains(HintCards.SurfaceLine), "dropped, not spent: it can come when it applies");
            // aboard the ship with a haul topside: SELL is neither asked for nor shown
            int clay = ItemRegistry.Get(D1Tables.Current.materials[0].item).id;
            state.inventory.Add(clay, 3);
            var boarding = side.ship.GetComponent<Meridian.Ship.ShipBoarding>();
            boarding.ForceAboard();
            yield return Frames(30);
            Assert.IsNull(hints.Showing, "no card aboard the ship");
            boarding.TryExit();
            yield return Until(() => hints.Showing != null, 3f);
            Assert.AreEqual(HintCards.Sell, hints.Showing, "on foot again: SELL");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator NoneFiresDuringATransitionOrAPanelAndTheToggleHidesThem()
        {
            HintCards.Blocked = () => true; // from the load on: a transition (the director's Busy, stood in by the hook) holds every card back
            yield return Boot();
            int camp = Mathf.FloorToInt(Meridian.Planet.POI.PoiCatalog.SpawnCamp.CenterX);
            Put(new Vector2(camp + 14.5f, side.terrain.SurfaceAt(camp + 14.5f) + 0.3f));
            yield return Frames(90);
            Assert.IsNull(hints.Showing, "nothing during a transition");
            HintCards.Blocked = null;
            yield return Until(() => hints.Showing != null, 2f);
            Assert.AreEqual(HintCards.DigDown, hints.Showing, "it shows once the transition is over");
            hints.Dismiss();

            // a panel holds it back too (the default rule)
            SettingsPanel.ResetHints();
            hud.Skills.SetOpen(true);
            yield return Frames(30);
            Assert.IsNull(hints.Showing, "nothing over the Skill Tree");
            hud.Skills.SetOpen(false);
            yield return Until(() => hints.Showing != null, 2f);
            Assert.AreEqual(HintCards.DigDown, hints.Showing, "Reset hints: it fires again");
            hints.Dismiss();

            // "Show hints" off: none
            SettingsPanel.ResetHints();
            GameSettings.ShowHints = false;
            Assert.AreEqual("SHOW HINTS: OFF", SettingsPanel.HintsLabel());
            yield return Frames(60);
            Assert.IsNull(hints.Showing, "off: no card");
            Assert.IsFalse(hints.Card.gameObject.activeSelf);
            GameSettings.ShowHints = true;
            yield return Until(() => hints.Showing != null, 2f);
            Assert.AreEqual(HintCards.DigDown, hints.Showing, "on again: it fires");
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>
        /// U-204 F4 / F13 (B-228's read of 0.6.1's smoke): a card in the upper band leaves the tool slot readable (its paper, its name plate
        /// and both key caps clear of the card: at -160 the card covered the name), and while a planet's title card is on the screen the
        /// hint and its arrow step aside (the arrow had stuck out over the title card), back when it leaves.
        /// </summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator ACardLeavesTheToolSlotReadableAndStepsAsideForATitleCard()
        {
            var titles0 = TitleCard.ShowOverride;
            yield return Boot();
            try
            {
                yield return Frames(5);
                hints.Show(HintCards.PackFull); // a card with an arrow (to the PACK readout)
                yield return Frames(5);
                Assert.AreEqual(HintCards.PackFull, hints.Showing);
                Assert.IsTrue(hints.AtTop, "the surveyor stands at camp: the card is in the upper band");
                var slot = hud.ToolSlot;
                Assert.IsTrue(slot.Root.gameObject.activeInHierarchy, "the tool slot shows on foot");
                var cardRect = hints.CardScreenRect;
                Assert.Greater(cardRect.width, 0f, "the card's rect");
                foreach (var part in new[] { slot.Slot.rectTransform, slot.NameTag.rectTransform, slot.Name.rectTransform, slot.PrevKey.rectTransform, slot.NextKey.rectTransform })
                {
                    var r = HintCards.ScreenRect(part);
                    Assert.IsFalse(cardRect.Overlaps(r), $"the card {cardRect} covers the tool slot's {part.name} {r}");
                }
                Assert.IsTrue(hints.Arrow.enabled, "PACK FULL's arrow shows with its card");

                TitleCard.ShowOverride = true;
                var titles = MenuController.Instance.TitleCards;
                titles.Show(Meridian.Planets.PlanetId.Earth);
                yield return Until(() => titles.Showing != null, 6f);
                Assert.NotNull(titles.Showing, "Earth's title card is up");
                yield return Frames(3);
                Assert.IsFalse(hints.Card.gameObject.activeSelf, "the hint steps aside under a title card");
                Assert.IsFalse(hints.Arrow.enabled, "and its arrow with it");
                Assert.AreEqual(HintCards.PackFull, hints.Showing, "it is held, not dismissed");
                titles.Hide();
                yield return Until(() => titles.Showing == null && hints.Card.gameObject.activeSelf, 6f);
                yield return Frames(3);
                Assert.IsTrue(hints.Card.gameObject.activeSelf, "the hint is back when the title leaves");
                Assert.IsTrue(hints.Arrow.enabled, "with its arrow");
                hints.Dismiss();
                LogAssert.NoUnexpectedReceived();
            }
            finally { TitleCard.ShowOverride = titles0; }
        }
    }
}
