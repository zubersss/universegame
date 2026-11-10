using System.Collections;
using Meridian.Core;
using Meridian.Space;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-184 (D-178, the owner's USER-34): the space minimap and the system map. Every planet, the Sun, the Moon and each Waystation sits at
    /// its true position within 1 px of its map's scale; the ship's arrow turns to its heading; off-edge planets show as rim arrows pointing
    /// at them; the zoom fits the nearest two planets and widens with speed; M toggles the system map and Esc closes it (no pause); the
    /// minimap is absent during an entry transition.
    /// </summary>
    public class SpaceMapTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        SceneDirector director;
        SpaceShip ship;
        SpaceMap map;

        IEnumerator Boot()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            director.SetView(ViewMode.Space);
            for (int i = 0; i < 10; i++) yield return null;
            ship = director.Space.GetComponentInChildren<SpaceShip>();
            map = director.Space.GetComponentInChildren<SpaceHud>().Map;
            Assert.NotNull(map, "SpaceHud adds the map");
            ship.externalInput = true;
            ship.intent = default;
            timeout = Time.realtimeSinceStartup + 10f;
            while ((!map.Built || ship.Invulnerable) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(map.Built, "the maps build once the world has");
        }

        /// <summary>Parks the ship (still, out of every well) and lets the zoom settle.</summary>
        IEnumerator Park(Vector2 at, float heading)
        {
            ship.Position = at;
            ship.Velocity = Vector2.zero;
            ship.Heading = heading;
            for (int i = 0; i < 90; i++) { ship.Velocity = Vector2.zero; ship.Position = at; yield return null; }
            // the range eases: wait until it holds still frame to frame
            float last = -1f;
            for (int i = 0; i < 240 && Mathf.Abs(map.Range - last) > 0.01f; i++) { last = map.Range; ship.Velocity = Vector2.zero; ship.Position = at; yield return null; }
        }

        Vector2 BetweenEarthAndMars()
        {
            var earth = ship.world.Find("earth").Value;
            return earth.position + new Vector2(earth.WellRadius + 140f, -60f);
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator MarksSitAtTheirTruePositions()
        {
            yield return Boot();
            yield return Park(BetweenEarthAndMars(), 30f);
            Assert.IsTrue(map.MinimapShown, "the minimap shows in the top-down view");
            Vector2 at = ship.Position;
            int inside = 0;
            foreach (var m in map.Marks)
            {
                var want = SpaceMap.MiniPosition(m.body.position, at, map.Scale);
                bool shown = m.disc.gameObject.activeSelf;
                Assert.AreEqual(want.magnitude <= SpaceMap.ClearPx - SpaceMap.InsideMargin, shown, $"{m.name}: shown inside the porthole only");
                if (!shown) continue;
                inside++;
                Assert.Less(Vector2.Distance(m.disc.anchoredPosition, want), 1f, $"{m.name} at its true position (range {map.Range:F0} u)");
            }
            Assert.GreaterOrEqual(inside, 3, "Earth, the Moon and Mars inside");
            foreach (var (w, mark, _) in map.Stations)
            {
                if (!mark.gameObject.activeSelf) continue;
                Assert.Less(Vector2.Distance(mark.anchoredPosition, SpaceMap.MiniPosition(w.transform.position, at, map.Scale)), 1f, $"Waystation {w.planet}");
            }

            map.SetSystemOpen(true);
            yield return null;
            int marks = 0, stations = 0;
            foreach (var sm in map.SystemMarks)
            {
                var want = SpaceMap.SystemPosition(sm.world, out bool inset);
                if (sm.name == "sun") { var p = sm.world * (sm.inset ? SpaceMap.InsetScale : SpaceMap.FullScale) + (sm.inset ? SpaceMap.InsetCentre : SpaceMap.FullCentre); want = p; }
                else Assert.AreEqual(inset, sm.inset, $"{sm.name} on the chart that holds it");
                Assert.Less(Vector2.Distance(SpaceMap.PanelPosition(sm.disc), want), 1f, $"{sm.name} on the system map");
                marks++;
                if (sm.name.StartsWith("station:")) stations++;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u184 marks: minimap range {map.Range:F0} u ({inside} inside), system map {marks} marks ({stations} Waystations)");
            Assert.GreaterOrEqual(marks, 10, "the Sun on both charts and the eight planets");
            Assert.AreEqual(Meridian.Trade.Waystation.All.Count, stations, "every Waystation on the system map");
            Assert.IsFalse(map.SystemMarks.Exists(sm => sm.name == "luna"), "the Moon only on the minimap (LEAD 20:4x)");
            // LEAD 20:4x: the tags placed clear (no tag over another tag or a disc on its chart); a moved tag has its leader.
            foreach (var a in map.SystemMarks)
            {
                if (a.tag == null) continue;
                var ra = new Rect(a.tag.anchoredPosition - a.tag.sizeDelta * 0.5f, a.tag.sizeDelta);
                foreach (var b in map.SystemMarks)
                {
                    if (b == a || b.inset != a.inset) continue;
                    Assert.IsFalse(ra.Overlaps(new Rect(b.disc.anchoredPosition - b.disc.sizeDelta * 0.5f, b.disc.sizeDelta)), $"{a.name}'s tag clear of {b.name}'s mark");
                    if (b.tag != null) Assert.IsFalse(ra.Overlaps(new Rect(b.tag.anchoredPosition - b.tag.sizeDelta * 0.5f, b.tag.sizeDelta)), $"{a.name}'s tag clear of {b.name}'s tag");
                }
                if (a.moved) Assert.IsTrue(a.leader.gameObject.activeSelf || Vector2.Distance(a.tag.anchoredPosition, a.disc.anchoredPosition) < 40f, $"{a.name}: a moved tag has its leader");
            }
            // U-204 F20 (B-228's read of smoke_63: every label read as struck through): a name stands inside its plate, the plate's
            // height set by the type's size (18 px names were taller than their 22 px plates).
            int lettered = 0;
            foreach (var sm in map.SystemMarks)
            {
                if (sm.tag == null) continue;
                var label = sm.tag.GetComponentInChildren<UnityEngine.UI.Text>(true);
                Assert.NotNull(label, $"{sm.name}'s lettering");
                Assert.AreEqual(SpaceMap.TagHeight(label), sm.tag.sizeDelta.y, 0.01f, $"{sm.name}: the plate for {label.fontSize} px type");
                Assert.GreaterOrEqual(sm.tag.sizeDelta.y, label.preferredHeight + 1.5f, $"{sm.name}: '{label.text}' is {label.preferredHeight:F1} px tall in a {sm.tag.sizeDelta.y} px plate");
                Assert.Greater(sm.tag.sizeDelta.y, SpaceMap.MinimapTagHeight, $"{sm.name}: taller than the minimap's 22 px plate");
                Assert.AreEqual(sm.tag.sizeDelta.y, label.rectTransform.sizeDelta.y, 0.01f, $"{sm.name}: the lettering's box is the plate's");
                Assert.LessOrEqual(label.preferredWidth, sm.tag.sizeDelta.x - 8f, $"{sm.name}: '{label.text}' across its plate");
                lettered++;
            }
            Assert.GreaterOrEqual(lettered, 10, "the system map's name plates checked");
            foreach (var m in map.GetComponentsInChildren<UnityEngine.UI.Text>(true))
                if (m.name == "Label" && m.transform.parent.name.StartsWith("RimTag_"))
                    Assert.AreEqual(SpaceMap.MinimapTagHeight, ((RectTransform)m.transform.parent).sizeDelta.y, 0.01f, "the minimap's tags keep their height");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator TheShipArrowTurnsToItsHeadingAndRimArrowsPointOut()
        {
            yield return Boot();
            yield return Park(BetweenEarthAndMars(), 37f);
            Assert.AreEqual(0f, Mathf.DeltaAngle(map.ShipArrow.localEulerAngles.z, 37f - 90f), 0.5f, "the arrow points up at 0: heading − 90°");
            ship.Heading = 200f;
            yield return null;
            Assert.AreEqual(0f, Mathf.DeltaAngle(map.ShipArrow.localEulerAngles.z, 200f - 90f), 0.5f);

            Vector2 at = ship.Position;
            int rims = 0, tags = 0;
            foreach (var m in map.Marks)
            {
                if (m.rim == null) continue;
                var off = m.body.position - at;
                bool off_edge = off.magnitude * map.Scale > SpaceMap.ClearPx - SpaceMap.InsideMargin;
                float bearing = Mathf.Atan2(off.y, off.x) * Mathf.Rad2Deg;
                if (!off_edge) { Assert.IsFalse(m.rim.gameObject.activeSelf, $"{m.name}: inside, no rim arrow"); continue; }
                if (!m.rim.gameObject.activeSelf)
                {
                    // folded into a nearer body's arrow on (nearly) the same bearing
                    bool shared = false;
                    foreach (var o in map.Marks)
                    {
                        if (o == m || o.rim == null || !o.rim.gameObject.activeSelf) continue;
                        var oo = o.body.position - at;
                        if (oo.sqrMagnitude < off.sqrMagnitude && Mathf.Abs(Mathf.DeltaAngle(Mathf.Atan2(oo.y, oo.x) * Mathf.Rad2Deg, bearing)) < SpaceMap.RimClusterDeg) shared = true;
                    }
                    Assert.IsTrue(shared, $"{m.name} is off the edge: its own arrow, or a nearer one's on its bearing");
                    continue;
                }
                rims++;
                var rp = m.rim.anchoredPosition;
                Assert.AreEqual(0f, Mathf.DeltaAngle(Mathf.Atan2(rp.y, rp.x) * Mathf.Rad2Deg, bearing), 0.5f, $"{m.name}'s arrow on its bearing");
                Assert.AreEqual(0f, Mathf.DeltaAngle(m.rim.localEulerAngles.z, bearing - 90f), 0.5f, $"{m.name}'s arrow points at it");
                Assert.AreEqual(SpaceMap.RimPx, rp.magnitude, 0.5f, "on the rim");
                if (!m.rimTag.gameObject.activeSelf) continue;
                tags++;
                StringAssert.Contains($"{Mathf.RoundToInt(off.magnitude / 100f) / 10f:0.0}k", m.rimLabel.text, $"{m.name}'s distance");
                Assert.IsTrue(SpaceMap.Fits(m.rimTag.anchoredPosition, m.rimTag.sizeDelta), $"{m.name}'s distance tag inside the porthole");
                Assert.Less(Vector2.Distance(m.rimTag.anchoredPosition, rp), 80f, $"{m.name}'s tag beside its arrow");
            }
            Assert.GreaterOrEqual(rims, 4, "the Sun and the far planets on the rim");
            Assert.That(tags, Is.InRange(1, SpaceMap.RimTags), "the nearest off-edge bodies carry their distance");
            LogAssert.NoUnexpectedReceived();
        }

        [Test]
        public void TheZoomFitsTheNearestPlanetsAndWidensWithSpeed()
        {
            var catalog = Resources.FindObjectsOfTypeAll<Meridian.Planets.PlanetCatalog>();
            Meridian.Planets.PlanetCatalog cat = catalog.Length > 0 ? catalog[0] : null;
#if UNITY_EDITOR
            if (cat == null)
            {
                foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:PlanetCatalog"))
                { cat = UnityEditor.AssetDatabase.LoadAssetAtPath<Meridian.Planets.PlanetCatalog>(UnityEditor.AssetDatabase.GUIDToAssetPath(guid)); if (cat != null) break; }
            }
#endif
            Assert.NotNull(cat, "the planet catalogue");
            var bodies = SpaceLayout.Build(cat);
            var earth = bodies.Find(b => b.name == "earth");
            var mars = bodies.Find(b => b.name == "mars");
            var at = earth.position + new Vector2(earth.WellRadius + 20f, 0f);
            float still = SpaceMap.TargetRange(bodies, at, 0f);
            Assert.GreaterOrEqual(still, Vector2.Distance(at, mars.position), "Earth and Mars both fit at rest");
            Assert.LessOrEqual(still, SpaceMap.FitRange);
            float cruise = SpaceMap.TargetRange(bodies, at, SpaceLayout.CruiseSpeed), boost = SpaceMap.TargetRange(bodies, at, SpaceLayout.BoostSpeed);
            Assert.Greater(cruise, still, "wider at cruise");
            Assert.Greater(boost, cruise, "wider again at boost");
            Assert.AreEqual(SpaceMap.MaxRange, SpaceMap.TargetRange(bodies, at, 5000f), 1e-3f, "capped at skip speed");
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator MTogglesTheSystemMapEscClosesItAndNothingPauses()
        {
            // As MenuHudTests: a batch-mode Editor has no focus, so the probe keyboard needs the game view's input and focus ignored, and it
            // goes in before the scene so every map resolves with it.
            var settings = InputSystem.settings;
            var savedEditor = settings.editorInputBehaviorInPlayMode;
            var savedBackground = settings.backgroundBehavior;
            settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
            settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
            var keys = InputSystem.AddDevice<Keyboard>("U184Keys");
            try
            {
                yield return Boot();
                yield return Park(BetweenEarthAndMars(), 0f);
                ship.externalInput = false;
                Assert.IsFalse(map.SystemOpen);
                yield return Tap(keys, Key.M);
                Assert.IsTrue(map.SystemOpen, "M opens the system map");
                Assert.AreEqual(1f, Time.timeScale, "nothing pauses");
                Assert.IsTrue(ship.actions.FindActionMap(Meridian.Player.MeridianInput.ShipTop).enabled, "the ship keeps its controls");
                yield return Tap(keys, Key.M);
                Assert.IsFalse(map.SystemOpen, "M closes it");
                yield return Tap(keys, Key.M);
                Assert.IsTrue(map.SystemOpen);
                yield return Tap(keys, Key.Escape);
                Assert.IsFalse(map.SystemOpen, "Esc closes it");
                Assert.IsFalse(Meridian.UI.MenuController.Instance != null && Meridian.UI.MenuController.Instance.PauseOpen, "Esc closed the map, not opened the pause menu");
                yield return Tap(keys, Key.Escape);
                Assert.IsTrue(Meridian.UI.MenuController.Instance.PauseOpen, "with the map closed, Esc pauses as before");
                Assert.IsFalse(map.MinimapShown, "the minimap hides under the pause menu");
                Meridian.UI.MenuController.Instance.Resume();
                yield return null;
            }
            finally
            {
                InputSystem.RemoveDevice(keys);
                settings.editorInputBehaviorInPlayMode = savedEditor;
                settings.backgroundBehavior = savedBackground;
                if (ship != null) ship.externalInput = true;
            }
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator TheMinimapIsAbsentDuringATransition()
        {
            yield return Boot();
            yield return Park(BetweenEarthAndMars(), 0f);
            Assert.IsTrue(map.MinimapShown);
            // As a launch leaves it (TransitionDirector.Launch): the planet side unloaded, so the entry loads it fresh.
            yield return director.UnloadPlanetSide();
            map.SetSystemOpen(true);
            var transitions = Object.FindAnyObjectByType<Meridian.Transitions.TransitionDirector>();
            transitions.BeginEntry(ship.world.Find("mars").Value);
            int busyFrames = 0;
            float until = Time.realtimeSinceStartup + 20f;
            while (transitions.Busy && Time.realtimeSinceStartup < until)
            {
                yield return null;
                if (!transitions.Busy) break;
                busyFrames++;
                Assert.IsFalse(map.MinimapShown, $"no minimap during the entry (frame {busyFrames})");
                Assert.IsFalse(map.SystemOpen, "the system map closes for the entry");
            }
            Assert.Greater(busyFrames, 3);
            Assert.IsTrue(GameState.Instance.HasFlag(SpaceMap.LandedFlag(Meridian.Planets.PlanetId.Mars)), "the entry ticks Mars as landed");
            Assert.IsTrue(SpaceMap.Landed(GameState.Instance, Meridian.Planets.PlanetId.Mars));
        }

        static IEnumerator Tap(Keyboard keys, Key key)
        {
            InputSystem.QueueStateEvent(keys, new KeyboardState(key));
            yield return null;
            InputSystem.QueueStateEvent(keys, new KeyboardState());
            yield return null;
        }
    }
}
