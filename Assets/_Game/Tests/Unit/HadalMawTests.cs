using System.IO;
using Meridian.Creatures;
using Meridian.EditorTools;
using Meridian.Flora;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-119 (B-136, D-127): the Hadal Maw is a rig-set creature of the coast deep: its json parses to six bones with the lure's three
    /// swaps, a four-beat sway (one swing per 2.18 s at 110 bpm) with per-bone amplitudes, and a jaw_open react that flares the lure;
    /// RigSetBuilder's controller carries the slow sway and leaves the jaw to the react; the species follows at a distance and never bumps.
    /// </summary>
    public class HadalMawTests
    {
        const string Key = "creatures/earth/hadal_maw";
        const string JsonPath = "Assets/_Game/Art/creatures/earth/hadal_maw.json";

        [Test]
        public void TheMawIsARigSetCreatureOfTheCoastDeep()
        {
            var spec = SpeciesSpec.Get(Species.HadalMaw);
            Assert.IsTrue(spec.rig, "a rig-set creature");
            Assert.AreEqual(Key, spec.artKey);
            Assert.AreEqual(PlanetId.Earth, spec.planet);
            Assert.AreEqual(Habitat.Water, spec.habitat);
            Assert.AreEqual(Temper.Hunts, spec.temper, "it approaches (to follow)");
            Assert.Greater(spec.followDistance, 0f, "D-087: it follows at a distance, never bumps");
            Assert.AreEqual(12f, spec.reactRadius, 1e-4f, "the rig's react radius (B-136)");
            Assert.GreaterOrEqual(spec.WaterDepthNeeded, 18f, "deep water only: never the camp's pools");
            Assert.AreEqual(1, spec.maxAlive);
            Assert.AreEqual((int)Species.HadalMaw, SpeciesSpec.Count - 1, "appended last: every older index stays");
            var site = new SpawnSite { surfaceTile = TileId.Sand, aboveTile = TileId.Water, waterDepth = 60, surfaceY = 260, datumY = 320, planet = PlanetId.Earth };
            Assert.IsTrue(spec.Allows(site), "the shelf: 60 m of water");
            site.waterDepth = 6;
            Assert.IsFalse(spec.Allows(site), "a 6 m pool: no");
            Assert.IsTrue(CreatureDirector.HoldsOff(spec.followDistance, 10f));
            Assert.IsFalse(CreatureDirector.HoldsOff(spec.followDistance, 20f));
            Assert.IsFalse(CreatureDirector.HoldsOff(0f, 1f), "no follow distance: the ordinary chase");
        }

        [Test]
        public void TheRigSetHasSixBonesTheLureSwapsAndAFourBeatSway()
        {
            Assert.IsTrue(File.Exists(JsonPath), JsonPath);
            var set = RigSet.Parse(File.ReadAllText(JsonPath), out var error);
            Assert.IsNull(error, "the Maw's json parses");
            var maw = set.FindPlant("hadal_maw");
            Assert.NotNull(maw);
            Assert.AreEqual(6, maw.BoneCount);
            foreach (var b in new[] { "head", "body1", "body2", "tail", "jaw", "lure" }) Assert.GreaterOrEqual(maw.BoneIndex(b), 0, b);
            CollectionAssert.AreEquivalent(new[] { "lure_lit", "lure_dim", "lure_flare" }, maw.swaps["lure"]);
            Assert.AreEqual(4, maw.idle.cycle_beats, "D-127: one swing over four beats");
            Assert.AreEqual(110f, maw.idle.beat_bpm, 1e-3f);
            Assert.AreEqual(2f * 4 * 60f / 110f, maw.idle.SwaySeconds, 1e-3f, "a swing per 2.18 s, the whole sway 4.36 s");
            Assert.IsTrue(maw.idle.HasBoneAmplitudes, "amplitude_deg per bone (B-136)");
            Assert.AreEqual(9f, maw.idle.AmplitudeFor("tail"), 1e-4f);
            Assert.AreEqual(2f, maw.idle.AmplitudeFor("head"), 1e-4f);
            Assert.AreEqual(0f, maw.idle.AmplitudeFor("jaw"), 1e-4f, "the jaw is the react's, not the sway's");
            Assert.AreEqual(0.8f, maw.idle.lag, 1e-4f, "the whip down the body");
            Assert.AreEqual(12f, maw.react.radius_m, 1e-4f);
            Assert.AreEqual("jaw_open", maw.react.action);
            Assert.AreEqual(-24f, maw.react.jaw_deg, 1e-4f);
            Assert.AreEqual(4f, maw.react.head_deg, 1e-4f);
            Assert.AreEqual("lure_flare", maw.react.also["lure"], "the react's swap object lands in `also`");
            Assert.NotNull(maw.Cycle, "the lure's idle cycle");
            Assert.AreEqual(8, maw.Cycle.TotalBeats, "lit 6 + dim 2");
            Assert.AreEqual(0, maw.Cycle.IndexAt(5.9f));
            Assert.AreEqual(1, maw.Cycle.IndexAt(6.5f));
            // The plants keep their sway: default cycle_beats 1, the old whip, one number shared down the chain.
            var earth = RigSet.Parse(File.ReadAllText("Assets/_Game/Art/flora/earth/rigset.json"), out error);
            Assert.IsNull(error);
            Assert.AreEqual(1, earth.plants[0].idle.cycle_beats);
            Assert.AreEqual(RigSet.Idle.DefaultLag, earth.plants[0].idle.lag, 1e-5f);
            Assert.IsFalse(earth.plants[0].idle.HasBoneAmplitudes);
            Assert.AreEqual(-1f, earth.plants[0].idle.AmplitudeFor(earth.plants[0].bones[0].name), 1e-5f, "no map: the builder shares the number");
        }

        [Test]
        public void TheControllerCarriesTheSlowSwayAndTheAssetsAreAddressed()
        {
            var path = RigSetBuilder.ControllerPath(Key);
            var controller = AssetDatabase.LoadAssetAtPath<UnityEditor.Animations.AnimatorController>(path);
            Assert.NotNull(controller, path + " (RigSetBuilder builds it from the parts json at import / CheckSetup)");
            var state = controller.layers[0].stateMachine.defaultState;
            Assert.NotNull(state, "a default state");
            Assert.AreEqual("hadal_maw", state.name, "the sway state is the plant");
            var clip = state.motion as AnimationClip;
            Assert.NotNull(clip, "the sway clip");
            Assert.AreEqual(2f * 4 * 60f / 110f, clip.length, 0.1f, "the sway spans 2 × cycle_beats beats (D-127)");
            var bindings = AnimationUtility.GetCurveBindings(clip);
            Assert.IsTrue(System.Array.Exists(bindings, b => b.path.EndsWith("tail") && b.propertyName.Contains("Euler")), "the tail sways");
            Assert.IsFalse(System.Array.Exists(bindings, b => b.path.EndsWith("jaw") && b.propertyName.Contains("Euler")), "no sway curve on the jaw: the react moves it");
            var jsonEntry = ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID(JsonPath));
            Assert.NotNull(jsonEntry, "the rig json is addressed (the runtime fetches <key>/json)");
            Assert.AreEqual(Key + "/json", jsonEntry.address);
            var ctrlEntry = ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID(path));
            Assert.NotNull(ctrlEntry, "the controller is addressed");
            Assert.AreEqual(Key + "/animator", ctrlEntry.address);
            var sheetEntry = ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID("Assets/_Game/Art/creatures/earth/hadal_maw_color.png"));
            Assert.NotNull(sheetEntry, "the parts sheet is addressed");
            Assert.AreEqual(Key, sheetEntry.address);
            // The sway math: a per-bone amplitude lands whole and the period follows cycle_beats; the shared number keeps the old two beats.
            var own = RigSetBuilder.SwayCurve(9f, 110f, 3, 6, 4, 0.8f, false);
            Assert.AreEqual(2f * 4 * 60f / 110f, own.keys[own.length - 1].time, 0.1f);
            float peak = 0f;
            foreach (var k in own.keys) peak = Mathf.Max(peak, Mathf.Abs(k.value));
            Assert.AreEqual(9f, peak, 0.6f, "the tail's own 9°");
            var shared = RigSetBuilder.SwayCurve(12f, 110f, 1, 5);
            Assert.AreEqual(120f / 110f, shared.keys[shared.length - 1].time, 0.05f, "a plant: two beats");
        }
    }
}
