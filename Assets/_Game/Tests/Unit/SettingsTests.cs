using Meridian.Core;
using Meridian.Player;
using Meridian.UI;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-102: the settings persist across a restart (a Reload reads PlayerPrefs like a fresh run), the volume steps
    /// stay on the tenths inside 0..1, and the read-only key list names the keyboard keys of every map.</summary>
    public class SettingsTests
    {
        static readonly string[] Keys = { GameSettings.FilmKey, GameSettings.MasterKey, GameSettings.MusicKey, GameSettings.SfxKey };
        readonly string[] saved = new string[4];
        readonly bool[] had = new bool[4];

        [SetUp]
        public void Keep()
        {
            for (int i = 0; i < Keys.Length; i++)
            {
                had[i] = PlayerPrefs.HasKey(Keys[i]);
                saved[i] = !had[i] ? null : i == 0 ? PlayerPrefs.GetInt(Keys[i]).ToString() : PlayerPrefs.GetFloat(Keys[i]).ToString("R", System.Globalization.CultureInfo.InvariantCulture);
                PlayerPrefs.DeleteKey(Keys[i]);
            }
            GameSettings.Reload();
        }

        [TearDown]
        public void Restore()
        {
            for (int i = 0; i < Keys.Length; i++)
            {
                if (!had[i]) PlayerPrefs.DeleteKey(Keys[i]);
                else if (i == 0) PlayerPrefs.SetInt(Keys[i], int.Parse(saved[i]));
                else PlayerPrefs.SetFloat(Keys[i], float.Parse(saved[i], System.Globalization.CultureInfo.InvariantCulture));
            }
            PlayerPrefs.Save();
            GameSettings.Reload();
        }

        [Test]
        public void VolumesDefaultToFullAndPersistAcrossARestart()
        {
            Assert.AreEqual(GameSettings.DefaultMaster, GameSettings.MasterVolume, "a fresh install: master at its default");
            Assert.AreEqual(GameSettings.DefaultMusic, GameSettings.MusicVolume);
            Assert.AreEqual(GameSettings.DefaultSfx, GameSettings.SfxVolume);
            int changes = 0;
            void Count() => changes++;
            GameSettings.Changed += Count;
            try
            {
                GameSettings.MasterVolume = 0.7f;
                GameSettings.MusicVolume = 0.3f;
                GameSettings.SfxVolume = 0f;
                GameSettings.FilmEffects = false;
                GameSettings.MasterVolume = 0.7f; // no change: no event
            }
            finally { GameSettings.Changed -= Count; }
            Assert.AreEqual(4, changes, "one Changed per real change");
            GameSettings.Reload(); // the restart: every value comes back from PlayerPrefs
            Assert.AreEqual(0.7f, GameSettings.MasterVolume, 1e-6f, "master kept");
            Assert.AreEqual(0.3f, GameSettings.MusicVolume, 1e-6f, "music kept");
            Assert.AreEqual(0f, GameSettings.SfxVolume, 1e-6f, "sfx kept (muted)");
            Assert.IsFalse(GameSettings.FilmEffects, "film kept off");
        }

        [Test]
        public void VolumeStepsStayOnTheTenthsInsideZeroToOne()
        {
            float v = 1f;
            for (int i = 0; i < 13; i++) v = GameSettings.Stepped(v, -1);
            Assert.AreEqual(0f, v, "thirteen presses down stop at 0");
            for (int i = 0; i < 7; i++) v = GameSettings.Stepped(v, 1);
            Assert.AreEqual(0.7f, v, 1e-6f, "seven up = 0.7 exactly (no float drift)");
            Assert.AreEqual("70%", GameSettings.Percent(v));
            for (int i = 0; i < 9; i++) v = GameSettings.Stepped(v, 1);
            Assert.AreEqual(1f, v, "the top is 1");
            GameSettings.SfxVolume = 1.6f;
            Assert.AreEqual(1f, GameSettings.SfxVolume, "a stored value clamps to 1");
            GameSettings.SfxVolume = -2f;
            Assert.AreEqual(0f, GameSettings.SfxVolume, "and to 0");
        }

        [Test]
        public void TheKeyListNamesEveryMapsKeyboardKeys()
        {
            var actions = MeridianInput.Build();
            string list = SettingsPanel.KeyList(actions);
            StringAssert.Contains("ON FOOT", list);
            StringAssert.Contains("ANY TIME", list);
            StringAssert.Contains("Move", list, "the walk keys are listed");
            StringAssert.DoesNotContain("position", list.ToLowerInvariant(), "the pointer's position is not a key");
            StringAssert.DoesNotContain("stick", list.ToLowerInvariant(), "gamepad bindings stay out of the keyboard list");
            Object.DestroyImmediate(actions);
        }
    }
}
