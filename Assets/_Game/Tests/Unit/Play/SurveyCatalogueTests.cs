using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Player;
using Meridian.Rig;
using Meridian.Save;
using Meridian.Survey;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-054 (PlayMode): Survey a stag → its entry and Datacores; a rescan pays nothing; save/load keeps the catalogue; the panel shows it.</summary>
    public class SurveyCatalogueTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string root;

        [SetUp] public void SetUp() { root = Path.Combine(Application.temporaryCachePath, "meridian_cat_" + System.Guid.NewGuid().ToString("N").Substring(0, 6)); SaveSystem.RootOverride = root; }
        [TearDown] public void TearDown() { SaveSystem.RootOverride = null; if (Directory.Exists(root)) Directory.Delete(root, true); }

        [UnityTest]
        public IEnumerator ScanAStagForDatacores()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            side.dayNight.Override = 0.5f;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            var state = GameState.Instance;
            state.catalogue.Clear();
            state.datacores = 0;
            var player = side.player;
            var rig = player.GetComponent<PlayerRigInput>();
            Assert.NotNull(side.scanner, "SurveyScanner on PlanetSide");

            // A stag 4 m away, then a Survey pulse. U-169: no other creature about (the camp's gull or a spawned critter walking into the
            // rescan's reach was a new entry, paid as it should be, not a repeat).
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();
            int sx = Mathf.FloorToInt(player.Body.position.x) - 4;
            var spec = SpeciesSpec.Get(Species.Stag);
            var stag = side.creatures.Spawn(Species.Stag, new Vector2(sx + 0.5f, side.terrain.TopSolidY(sx) + 1f + spec.size.y * 0.5f + 0.05f));
            Assert.NotNull(stag);
            yield return new WaitForFixedUpdate();
            float ready = Time.realtimeSinceStartup + 5f;
            while (!Meridian.FX.FxSheet.Get(Meridian.Art.ArtKeys.Fx.SurveyScan).Ready && Time.realtimeSinceStartup < ready) yield return null;
            rig.module = RigModule.Survey;
            rig.holdUse = true;
            yield return null;
            yield return null;
            rig.holdUse = false;
            string stagId = Catalogue.CreatureId(Species.Stag);
            TestContext.Out.WriteLine($"[MERIDIAN] first pulse: {string.Join(", ", side.scanner.LastNew)} = {side.scanner.LastPaid} DC");
            Assert.IsTrue(state.catalogue.Contains(stagId), "the stag is catalogued");
            Assert.Contains(stagId, side.scanner.LastNew);
            Assert.GreaterOrEqual(state.datacores, 25, "Datacores paid (25 for the stag, more for minerals/sites around)");
            Assert.AreEqual(side.scanner.LastPaid, state.datacores);

            // A rescan pays nothing.
            int before = state.datacores;
            yield return new WaitForSeconds(PlayerRigInput.SurveyCooldown + 0.1f);
            side.scanner.Scan(player.Body.position + new Vector2(0f, 0.9f));
            Assert.AreEqual(0, side.scanner.LastPaid, $"rescans pay nothing (new: {string.Join(", ", side.scanner.LastNew)})");
            Assert.AreEqual(before, state.datacores);

            // The panel shows the entry and Earth's completion.
            var hud = Object.FindAnyObjectByType<Meridian.UI.SideHud>();
            hud.Catalogue.SetOpen(true);
            yield return null;
            Assert.AreEqual(Meridian.Planets.PlanetId.Earth, hud.Catalogue.Shown);
            Assert.IsTrue(hud.Catalogue.EntryNames.Exists(t => t.text == "Stag"), "Stag listed by name");
            Assert.AreNotEqual("0%", hud.Catalogue.Completion[Meridian.Planets.PlanetId.Earth].text);
            hud.Catalogue.SetOpen(false);

            // Save → change → load.
            int dc = state.datacores, count = state.catalogue.Count;
            SaveSystem.Instance.Save();
            state.catalogue.Clear(); state.datacores = 0;
            yield return SaveSystem.Instance.Load();
            Assert.AreEqual(dc, state.datacores, "Datacores saved");
            Assert.AreEqual(count, state.catalogue.Count, "catalogue saved");
            Assert.IsTrue(state.catalogue.Contains(stagId));
            LogAssert.NoUnexpectedReceived();
        }
    }
}
