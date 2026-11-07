using System.Collections;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Perf;
using Meridian.Planet.Backdrop;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-090 (PlayMode, Earth): every region resolves at least 7 distinct stage slots (placeholders count) at their
    /// §10.10 depths; no foreground piece sits within 6 m of the spawn or a POI; crossing a region border at run speed
    /// hitches less than 33 ms, has the next set resident before arrival and releases the old set within 5 s.
    /// </summary>
    public class StageLayerTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        PlanetSideRoot side;
        StageLayers stage;
        Camera cam;

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
            stage = side.stage;
            Assert.NotNull(stage, "StageLayers on PlanetSide");
            cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
        }

        IEnumerator MoveCameraTo(float x)
        {
            var p = cam.transform.position;
            cam.transform.position = new Vector3(x, p.y, p.z);
            float until = Time.realtimeSinceStartup + 12f;
            // Let the bands, pieces and placeholders (1.5 s grace for a missing model) build.
            while (Time.realtimeSinceStartup < until && stage.DrawnSlots() < 7) yield return null;
            for (int i = 0; i < 5; i++) yield return null;
        }

        static (float lo, float hi) DepthRange(StageLayers.Slot slot)
        {
            switch (slot)
            {
                case StageLayers.Slot.Foreground: return (-3f, -1.5f);
                case StageLayers.Slot.PlayPlane: return (0f, 0f);
                case StageLayers.Slot.NearFlora: return (1.5f, 12f);
                case StageLayers.Slot.NearRocks: return (8f, 14f);
                case StageLayers.Slot.MidRidge: return (15f, 70f);
                case StageLayers.Slot.FarHills: return (80f, 140f);
                case StageLayers.Slot.FarMountains: return (30f, 400f); // set-pieces 30–140, the skyline 150–400
                default: return (450f, 600f);
            }
        }

        [UnityTest]
        [Ignore("D-124: the S1 seven-slot stage was cancelled by D-086; Earth runs the cartoon ParallaxLayers path since C0")]
        public IEnumerator EveryEarthRegionResolvesSevenSlotsAtTheirDepths()
        {
            yield return Boot();
            foreach (Biome b in System.Enum.GetValues(typeof(Biome)))
            {
                EarthBiomes.Range(b, out int start, out int length);
                yield return MoveCameraTo(start + length * 0.5f);
                string region = StageRegions.At(PlanetId.Earth, start + length / 2);
                Assert.AreEqual(region, stage.Region, "region under the camera");
                var layers = stage.Layers;
                int slots = stage.DrawnSlots();
                var seen = new HashSet<StageLayers.Slot>();
                var sb = new System.Text.StringBuilder();
                foreach (var l in layers)
                {
                    sb.Append($"{l.slot}:{(l.ready ? "art" : l.placeholder ? "placeholder" : "missing")}@{l.z:F0} ");
                    if (!l.Drawn) continue;
                    var (lo, hi) = DepthRange(l.slot);
                    Assert.IsTrue(l.z >= lo - 0.01f && l.z <= hi + 0.01f, $"{region} {l.slot} ({l.key}) at z {l.z:F1} within {lo}..{hi}");
                    seen.Add(l.slot);
                }
                TestContext.Out.WriteLine($"[MERIDIAN] stage {region}: {slots} slots drawn: {sb}");
                Assert.GreaterOrEqual(slots, 7, $"{region}: at least 7 distinct slots drawn (placeholders count): {sb}");
            }
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator NoForegroundPieceWithinSixMetresOfTheSpawnOrAPoi()
        {
            yield return Boot();
            float spawn = Meridian.Planet.POI.PoiCatalog.SpawnCamp.CenterX;
            yield return MoveCameraTo(spawn);
            int checkedSlots = 0, placed = 0;
            float spacing = stage.Manifest != null ? stage.Manifest.Spacing : 12f;
            for (int i = Mathf.FloorToInt((spawn - 96f) / spacing); i <= Mathf.CeilToInt((spawn + 96f) / spacing); i++)
            {
                checkedSlots++;
                if (!stage.ForegroundAt(i, out int x, out string key, out float z, out _)) continue;
                placed++;
                Assert.Greater(Mathf.Abs(x - spawn), StageLayers.ForegroundKeepOut, $"piece {key} at x {x} is {Mathf.Abs(x - spawn):F1} m from the spawn {spawn:F1}");
                for (int d = -(int)StageLayers.ForegroundKeepOut; d <= (int)StageLayers.ForegroundKeepOut; d++)
                    Assert.IsFalse(side.pois.StampGroundAt(side.terrain.WrapX(x + d), out _), $"piece {key} at x {x} is within 6 m of a POI stamp");
                Assert.IsTrue(z >= -3f && z <= -1.5f, "foreground depth −3…−1.5");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] foreground around the camp: {placed} pieces in {checkedSlots} slots, none within 6 m of the spawn or a POI");
            Assert.Greater(placed, 0, "pieces exist away from the camp");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator CrossingARegionBorderAtRunSpeedStreamsTheNextSetAndReleasesTheOld()
        {
            yield return Boot();
            // The forest/plains border at x 700 (EarthBiomes): approach from 300 m inside the forest at sprint speed.
            EarthBiomes.Range(Biome.Plains, out int border, out _);
            yield return MoveCameraTo(border - 300f);
            Assert.AreEqual("earth_forest", stage.Region);
            string next = StageRegions.Neighbour(PlanetId.Earth, EarthBiomes.Width, border - 10);
            Assert.AreEqual("earth_plains", next, "the neighbour across the border");
            float worst = 0f;
            bool residentBeforeArrival = false;
            int frames = 0;
            while (cam.transform.position.x < border + 260f)
            {
                cam.transform.position += new Vector3(6.5f * Time.deltaTime, 0f, 0f);
                yield return null;
                frames++;
                if (frames > 5) worst = Mathf.Max(worst, Time.unscaledDeltaTime * 1000f);
                if (cam.transform.position.x < border && stage.IsSetResident("earth_plains")) residentBeforeArrival = true;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] border crossing: worst frame {worst:F1} ms, plains set resident before arrival {residentBeforeArrival}, region now {stage.Region}, forest set held {stage.IsSetHeld("earth_forest")}");
            Assert.Less(worst, 33f, "no hitch > 33 ms at the border");
            Assert.IsTrue(residentBeforeArrival, "the next set was resident before arrival");
            Assert.AreEqual("earth_plains", stage.Region);
            float t0 = Time.realtimeSinceStartup;
            while (stage.IsSetHeld("earth_forest") && Time.realtimeSinceStartup - t0 < StageLayers.ReleaseDelay + 2f) yield return null;
            Assert.IsFalse(stage.IsSetHeld("earth_forest"), "the old set released within 5 s of being out of reach");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
