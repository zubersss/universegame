using Meridian.Space;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.Tests
{
    /// <summary>
    /// U-184: MapLines, the maps' dashed circles: the arc window inside a clip disc (none / all / part), and a canvas update builds one
    /// quad per dash of the visible arc.
    /// </summary>
    public class MapLinesTests
    {
        [Test]
        public void TheArcWindowInsideTheClipDisc()
        {
            Assert.IsTrue(MapLines.Window(new Vector2(10f, 0f), 20f, 99f, out _, out float half));
            Assert.AreEqual(Mathf.PI, half, 1e-5f, "wholly inside: the full circle");
            Assert.IsFalse(MapLines.Window(new Vector2(300f, 0f), 50f, 99f, out _, out _), "wholly outside");
            Assert.IsFalse(MapLines.Window(Vector2.zero, 500f, 99f, out _, out _), "the disc wholly inside the circle");
            Assert.IsTrue(MapLines.Window(new Vector2(-400f, 0f), 400f, 99f, out float mid, out half), "an orbit passing through");
            Assert.AreEqual(0f, Mathf.DeltaAngle(mid * Mathf.Rad2Deg, 0f), 1e-3f, "its middle faces the disc");
            Assert.Less(half, 0.3f);
            // the window's ends lie on the clip circle
            var c = new Vector2(-400f, 0f);
            var end = c + new Vector2(Mathf.Cos(mid + half), Mathf.Sin(mid + half)) * 400f;
            Assert.AreEqual(99f, end.magnitude, 0.01f);
        }

        [Test]
        public void ACanvasUpdateBuildsTheDashes()
        {
            var go = new GameObject("U184Canvas", typeof(RectTransform));
            try
            {
                go.AddComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
                var lg = new GameObject("Lines", typeof(RectTransform));
                lg.transform.SetParent(go.transform, false);
                var lines = lg.AddComponent<MapLines>();
                lines.dashPx = 16f; lines.thickPx = 8f; lines.clipRadius = 99f;
                lines.Clear();
                lines.Add(Vector2.zero, 50f);                    // wholly inside: 2π·50 / 16 ≈ 20 dashes
                lines.Add(new Vector2(-400f, 0f), 400f);         // an arc through the disc
                lines.Commit();
                Canvas.ForceUpdateCanvases();
                TestContext.Out.WriteLine($"[MERIDIAN] u184 MapLines: {lines.Quads} quads after a canvas update (active {lines.IsActive()})");
                Assert.Greater(lines.Quads, 20, "the circle and the arc's dashes");
                Assert.Less(lines.Quads, 40, "only the arc inside the disc, not the orbit's 157 dashes");
            }
            finally { Object.DestroyImmediate(go); }
        }
    }
}
