using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Save;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// D-203 (LEAD 11-10): the player's "-meridianSaveRoot &lt;folder&gt;" read for real, before a built player is ever driven with it.
    /// The switch is on Unity's OWN command line here (tools/unity_test.ps1 PlayMode -Filter SaveRootSwitchPlayTests -SaveRootSwitch):
    /// the Core scene's SaveSystem reads it in Awake as the built player's does, logs the line the smoke and the probe scripts look
    /// for, and a save lands in that folder; the newest file under the player's real saves folder does not move. Run ALONE (the
    /// switch is read once a process: a Core loaded by an earlier class has already read it and its TearDown cleared the root).
    /// Without the switch on the command line the row is skipped: every other run.
    /// </summary>
    public class SaveRootSwitchPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static System.DateTime NewestUnder(string folder)
        {
            var newest = System.DateTime.MinValue;
            if (!Directory.Exists(folder)) return newest;
            foreach (var f in Directory.GetFiles(folder, "*", SearchOption.AllDirectories))
            {
                var t = File.GetLastWriteTimeUtc(f);
                if (t > newest) newest = t;
            }
            return newest;
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator ThePlayerLoopTakesTheSwitchFromTheCommandLine()
        {
            string asked = SaveSystem.RootFromArgs(System.Environment.GetCommandLineArgs());
            if (asked == null) Assert.Ignore("Unity was not started with -meridianSaveRoot (tools/unity_test.ps1 PlayMode -Filter SaveRootSwitchPlayTests -SaveRootSwitch).");
            string real = Path.Combine(Application.persistentDataPath, "saves");
            var realBefore = NewestUnder(real); // read only
            string was = SaveSystem.RootOverride;
            SaveSystem.RootOverride = null;
            try
            {
                LogAssert.Expect(LogType.Log, new System.Text.RegularExpressions.Regex(@"\[MERIDIAN\] saves go to")); // the line the scripts check
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var save = SaveSystem.Instance;
                Assert.NotNull(save, "SaveSystem in Core");
                Assert.AreEqual(asked, SaveSystem.RootOverride, "the Core scene's SaveSystem took the root from the command line in Awake (null: an earlier class loaded Core first; run this class alone)");
                Assert.AreEqual(Path.GetFullPath(asked), Path.GetFullPath(SaveSystem.Root));
                int saves = save.SaveCount;
                save.Save();
                Assert.AreEqual(saves + 1, save.SaveCount, "a save was written");
                string state = Path.Combine(asked, "slot" + save.slot, SaveSystem.StateFile);
                Assert.IsTrue(File.Exists(state), $"the save's state file is in the folder the switch named: {state}");
                Assert.AreEqual(realBefore, NewestUnder(real), "nothing under the player's real saves folder was written");
                TestContext.Out.WriteLine($"[MERIDIAN] save root switch: the player loop saved to '{state}'; the newest file under '{real}' is still {realBefore.ToLocalTime():MM-dd HH:mm:ss}");
            }
            finally { SaveSystem.RootOverride = was; }
        }
    }
}
