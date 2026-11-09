using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Items;
using Meridian.Player;
using Meridian.Progress;
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
    /// U-178 (PlayMode; D-175, D1_TABLES §7): the New Expedition through the tree panel: NEW EXPEDITION shows only at Rank 10 and topside;
    /// its confirmation is the panel's own (no system dialog) and lists what goes and what stays; CONFIRM presses the seal, begins expedition
    /// II, wipes, keeps, sets the surveyor down at Earth's camp and saves. A save mid-expedition III loads with its multiplier; the HUD's
    /// Rank slot shows the insignia and plays the rank-up when the Rank rises.
    /// </summary>
    public class ExpeditionPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string root;
        SceneDirector director;
        PlanetSideRoot side;
        PlayerController player;
        GameState state;
        SideHud hud;
        SkillTreePanel panel;

        [SetUp] public void SetUp() { root = Path.Combine(Application.temporaryCachePath, "meridian_exp_" + System.Guid.NewGuid().ToString("N").Substring(0, 6)); SaveSystem.RootOverride = root; }
        [TearDown] public void TearDown() { SaveSystem.RootOverride = null; if (Directory.Exists(root)) Directory.Delete(root, true); }

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            if (side.hazards != null) side.hazards.enabled = false;
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();
            player = side.player;
            state = GameState.Instance;
            hud = Object.FindAnyObjectByType<SideHud>();
            Assert.NotNull(hud, "the planet-side HUD");
            panel = hud.Skills;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
        }

        static int Id(string key) => ItemRegistry.Get(key).id;

        [UnityTest, Timeout(300000)]
        public IEnumerator TheNewExpeditionFromTheTreePanel()
        {
            yield return Boot();
            state.skillNodes.Clear(); state.skillNodes.Add("dig_power_1"); state.skillNodes.Add("haul_pack_1");
            state.expedition = 1; state.scrip = 5000; state.datacores = 4;
            SkillStats.Apply(state);
            state.inventory.Add(Id("clay"), 3);
            state.cargo.Add(new CargoStack { itemId = Id("iron"), count = 2 });
            state.catalogue.Add("u178_entry");
            state.scripEarned = 79999;
            panel.SetOpen(true);
            yield return null;
            Assert.IsFalse(panel.NewExpedition.gameObject.activeSelf, "Rank 9: no New Expedition");
            state.scripEarned = 80000;
            panel.Select(panel.Selected);
            Assert.IsTrue(panel.NewExpedition.gameObject.activeSelf, "Rank 10, topside: offered");

            // under the Surface Line: neither the button nor its confirmation
            var feet0 = player.Body.position;
            int px = Mathf.FloorToInt(feet0.x) + 6;
            int py = Mathf.FloorToInt(side.terrain.SurfaceAt(px + 0.5f)) - 7;
            for (int x = px - 1; x <= px + 1; x++) for (int y = py; y <= py + 2; y++) side.terrain.SetTile(x, y, TileId.Air);
            for (int i = 0; i < 3; i++) yield return null;
            player.Body.position = new Vector2(px + 0.5f, py + 0.05f); player.Body.linearVelocity = Vector2.zero;
            for (int i = 0; i < 5; i++) yield return new WaitForFixedUpdate();
            panel.Select(panel.Selected);
            Assert.IsFalse(panel.Topside);
            Assert.IsFalse(panel.NewExpedition.gameObject.activeSelf, "below the Surface Line: not offered");
            panel.ShowConfirm(true);
            Assert.IsFalse(panel.Confirming, "nor its confirmation");
            player.Body.position = feet0; player.Body.linearVelocity = Vector2.zero;
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            panel.Select(panel.Selected);
            Assert.IsTrue(panel.NewExpedition.gameObject.activeSelf);

            // the header's insignia and badge (B-206)
            float until = Time.realtimeSinceStartup + 8f;
            while ((panel.Insignia.sprite == null || panel.Badge.sprite == null) && Time.realtimeSinceStartup < until) yield return null;
            Assert.NotNull(panel.Insignia.sprite); StringAssert.Contains("insignia_10", panel.Insignia.sprite.name);
            Assert.NotNull(panel.Badge.sprite); Assert.AreEqual("I", panel.BadgeNumeral.text);

            // the confirmation, in the panel
            panel.ShowConfirm(true);
            Assert.IsTrue(panel.Confirming, "the panel's own confirmation");
            foreach (var w in Expedition.Wiped) StringAssert.Contains(w, panel.CertificateText.text);
            foreach (var k in Expedition.Kept) StringAssert.Contains(k, panel.CertificateText.text);
            StringAssert.Contains("×1.25", panel.CertificateText.text);
            panel.ShowConfirm(false);
            Assert.IsFalse(panel.Confirming, "CANCEL closes it, nothing changes");
            Assert.AreEqual(1, state.expedition); Assert.AreEqual(2, state.skillNodes.Count);

            panel.ShowConfirm(true);
            int saves = SaveSystem.Instance != null ? SaveSystem.Instance.SaveCount : 0;
            int ups = hud.RankUps;
            panel.Confirm();
            Assert.IsTrue(panel.Sealing, "the seal presses first");
            until = Time.realtimeSinceStartup + 6f;
            while (state.expedition == 1 && Time.realtimeSinceStartup < until) yield return null;
            Assert.AreEqual(2, state.expedition, "expedition II");
            Assert.IsFalse(panel.IsOpen);
            until = Time.realtimeSinceStartup + 40f;
            while (SaveSystem.Instance != null && SaveSystem.Instance.SaveCount == saves && Time.realtimeSinceStartup < until) yield return null;
            Assert.Greater(SaveSystem.Instance.SaveCount, saves, "saved at the camp");
            side = director.PlanetSide;
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(Meridian.Planets.PlanetId.Earth, state.currentPlanet);
            Assert.AreEqual(PlanetSideRoot.CampSpawnX + 0.5f, side.player.Body.position.x, 2f, "at Earth's camp");
            Assert.AreEqual(0, state.skillNodes.Count); Assert.AreEqual(Meridian.Trade.Market.StartingScrip, state.scrip); Assert.AreEqual(0, state.scripEarned);
            Assert.AreEqual(0, state.inventory.Count(Id("clay"))); Assert.AreEqual(0, state.cargo.Count);
            Assert.AreEqual(4, state.datacores); Assert.IsTrue(state.catalogue.Contains("u178_entry"));
            Assert.AreEqual(1.25f, Expedition.Multiplier(state.expedition));
            yield return null; yield return null;
            Assert.AreEqual(1, hud.ShownRank, "the HUD's Rank back to 1");
            Assert.AreEqual(ups, hud.RankUps, "a new expedition's Rank 1 is no rank-up");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator ASaveMidExpeditionThreeLoadsWithItsMultiplierAndTheRankRises()
        {
            yield return Boot();
            state.skillNodes.Clear(); state.skillNodes.Add("dig_power_1");
            state.expedition = 1; SkillStats.Apply(state);
            float b1 = SkillStats.BeamPower;
            state.expedition = 3; SkillStats.Apply(state);
            float b3 = SkillStats.BeamPower;
            Assert.AreEqual(b1 * 1.5f, b3, 1e-4f, "expedition III: ×1.5");
            SaveSystem.Instance.Save();
            state.expedition = 1; state.skillNodes.Clear(); SkillStats.Apply(state);
            yield return SaveSystem.Instance.Load();
            Assert.AreEqual(3, state.expedition);
            Assert.IsTrue(state.skillNodes.Contains("dig_power_1"));
            Assert.AreEqual(b3, SkillStats.BeamPower, 1e-4f, "loaded with its multiplier");

            // the HUD's Rank: the insignia in the slot; the rank-up when it rises
            hud = Object.FindAnyObjectByType<SideHud>();
            state.scripEarned = 0;
            yield return null; yield return null;
            Assert.AreEqual(1, hud.ShownRank);
            float until = Time.realtimeSinceStartup + 8f;
            while (hud.RankInsignia.sprite == null && Time.realtimeSinceStartup < until) yield return null;
            StringAssert.Contains("insignia_1", hud.RankInsignia.sprite.name);
            int ups = hud.RankUps;
            for (int i = 0; i < 30; i++) yield return null; // the rank_up frames load
            state.scripEarned = 300;
            yield return null; yield return null;
            Assert.AreEqual(ups + 1, hud.RankUps, "Rank 2: a rank-up");
            Assert.AreEqual(2, hud.ShownRank);
            StringAssert.Contains("insignia_2", hud.RankInsignia.sprite.name);
            until = Time.realtimeSinceStartup + 1f;
            bool shown = false;
            while (Time.realtimeSinceStartup < until && !shown) { shown = hud.RankUpFx.enabled && hud.RankUpFx.sprite != null && hud.RankUpInsignia.enabled; yield return null; }
            Assert.IsTrue(shown, "B-214's rank_up with the new insignia on top");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
