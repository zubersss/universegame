using System;
using System.Collections;
using System.IO;
using Meridian.UI;
using UnityEngine;

namespace Meridian.Core
{
    /// <summary>
    /// Opt-in smoke run of a built player (U-017): with `-meridianSmoke &lt;folder&gt;` it screenshots the
    /// main menu, the Earth HUD, the ship HUD and the top-down view, writes smoke_done.txt and quits.
    /// Without the argument it does nothing. Used by tools/unity_smoke.ps1.
    /// </summary>
    public sealed class BuildSmoke : MonoBehaviour
    {
        public SceneDirector scenes;

        static string Folder()
        {
            var args = Environment.GetCommandLineArgs();
            int i = Array.IndexOf(args, "-meridianSmoke");
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
        }

        void Start()
        {
            var folder = Folder();
            if (folder == null) { enabled = false; return; }
            Directory.CreateDirectory(folder);
            StartCoroutine(Run(folder));
        }

        IEnumerator Run(string folder)
        {
            while (scenes == null || !scenes.IsReady) yield return null;
            yield return Wait(1.5f);
            yield return Shot(folder, "smoke_1_menu.png");

            if (MenuController.Instance != null && MenuController.Instance.MainMenuOpen) MenuController.Instance.NewGame();
            yield return Wait(2.5f);
            yield return Shot(folder, "smoke_2_earth.png");

            var ship = scenes.PlanetSide != null ? scenes.PlanetSide.ship : null;
            var boarding = ship != null ? ship.GetComponent<Meridian.Ship.ShipBoarding>() : null;
            if (boarding != null) boarding.ForceAboard();
            yield return Wait(1.5f);
            yield return Shot(folder, "smoke_3_ship.png");

            scenes.SetView(ViewMode.Space);
            yield return Wait(2.5f);
            yield return Shot(folder, "smoke_4_space.png");

            File.WriteAllText(Path.Combine(folder, "smoke_done.txt"), $"OK {GameInfo.Version} {DateTime.Now:s}");
            Application.Quit();
        }

        static IEnumerator Wait(float seconds)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while (Time.realtimeSinceStartup < until) yield return null;
        }

        static IEnumerator Shot(string folder, string name)
        {
            ScreenCapture.CaptureScreenshot(Path.Combine(folder, name));
            yield return null; // the capture is written at the end of the frame
            yield return null;
        }
    }
}
