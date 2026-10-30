using System.Collections;
using Meridian.Core;
using Meridian.Hazards;
using Meridian.Planet.Weather;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-026 (PlayMode): a Mars dust storm warns 60 s ahead, cuts visibility to 15 m, adds Cryo +1, ends in 2–6 min.</summary>
    public class DustStormPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const float G = TimeSystem.GameSecondsPerRealSecond;

        SceneDirector director;
        TimeSystem time;
        DustStorm storm;
        int warnings, starts, ends;

        IEnumerator BootOnMars()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Mars));
            time = Object.FindAnyObjectByType<TimeSystem>();
            storm = director.PlanetSide.dustStorm;
            Assert.NotNull(storm, "DustStorm on PlanetSide");
            Assert.IsTrue(storm.OnMars);
            warnings = starts = ends = 0;
            storm.Warning += () => warnings++;
            storm.Started += () => starts++;
            storm.Ended += () => ends++;
        }

        /// <summary>Moves the game clock by `realSeconds` (as if that much play time passed) and lets a frame run.</summary>
        IEnumerator Pass(float realSeconds)
        {
            time.Advance(realSeconds);
            yield return null;
        }

        int CryoNow() => Cryo.Level(PlanetId.Mars, director.PlanetSide.dayNight.LocalTime, storm.CryoBonus);

        [UnityTest]
        public IEnumerator ForcedStormWarnsBlowsAndEnds()
        {
            yield return BootOnMars();
            int cryoBefore = CryoNow();
            storm.Force(61f, 180f); // warning starts in 1 s, storm in 61 s, lasts 3 min
            yield return Pass(0.5f);
            Assert.AreEqual(StormPhase.Clear, storm.Phase);
            Assert.AreEqual(0, warnings, "no warning yet");
            yield return Pass(0.6f);
            Assert.AreEqual(StormPhase.Warning, storm.Phase);
            Assert.AreEqual(1, warnings, "warning raised once");
            double lead = (storm.Current.start - time.GameSeconds) / G;
            Assert.That(lead, Is.InRange(59.0, 60.0), "warning comes 60 s before the storm");
            yield return null;
            StringAssert.StartsWith("DUST STORM IN", director.PlanetSide.sideHud.StormText.text, "HUD counts down");

            yield return Pass(30f);
            Assert.AreEqual(1, warnings, "still one warning");
            Assert.AreEqual(0, starts);
            yield return Pass(30f);
            Assert.AreEqual(StormPhase.Storm, storm.Phase);
            Assert.AreEqual(1, starts, "storm started");
            yield return Pass(DustStorm.RampRealSeconds + 0.5f);
            yield return null;
            Assert.AreEqual(1f, storm.Intensity, 1e-4f, "full storm after the ramp");
            Assert.AreEqual(DustStorm.StormVisibility, storm.Visibility, 1e-3f, "visibility 15 m");
            var fog = director.PlanetSide.sideCamera.transform.Find("DustFog").GetComponent<MeshRenderer>();
            Assert.IsTrue(fog.enabled, "dust fog drawn");
            var block = new MaterialPropertyBlock();
            fog.GetPropertyBlock(block);
            Assert.AreEqual(15f, block.GetFloat("_Visibility"), 1e-3f, "fog clears only within 15 m");
            Assert.AreEqual(cryoBefore + 1, CryoNow(), "Cryo +1 in the storm");
            Assert.GreaterOrEqual(storm.Discharges, 1, "static discharges");
            Assert.IsTrue(storm.PuffsLoaded, "fx/dust puffs loaded");
            Assert.AreEqual("DUST STORM", director.PlanetSide.sideHud.StormText.text);

            float startedAt = (float)(storm.Current.start / G);
            for (int i = 0; i < 400 && ends == 0; i++) yield return Pass(1f);
            Assert.AreEqual(1, ends, "storm ended");
            float length = (float)(time.GameSeconds / G) - startedAt;
            Assert.That(length, Is.InRange(120f, 362f), "ends inside 2–6 min");
            yield return null;
            Assert.AreEqual(StormPhase.Clear, storm.Phase);
            Assert.AreEqual(DustStorm.ClearVisibility, storm.Visibility, 1e-3f, "visibility back");
            Assert.IsFalse(fog.enabled, "fog off");
            Assert.AreEqual(cryoBefore, CryoNow(), "Cryo back down");
            Assert.AreEqual("", director.PlanetSide.sideHud.StormText.text);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator ScheduledStormComesOnItsOwn()
        {
            yield return BootOnMars();
            var mars = director.PlanetSide.Config;
            double day = mars.dayLengthRealMinutes * 60.0 * G;
            var first = DustStormSchedule.Current(GameState.Instance.worldSeed, time.GameSeconds, day, default);
            time.SetGameSeconds(first.WarningStart - 2 * G);
            yield return null;
            Assert.AreEqual(StormPhase.Clear, storm.Phase);
            yield return Pass(3f);
            Assert.AreEqual(StormPhase.Warning, storm.Phase);
            Assert.AreEqual(1, warnings);
            yield return Pass(60f);
            Assert.AreEqual(StormPhase.Storm, storm.Phase);
            Assert.AreEqual(first.index, storm.Current.index, "the scheduled storm");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
