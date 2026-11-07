using System.IO;
using Meridian.EditorTools;
using Meridian.Flora;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-103 (EditMode, B-122 / D-111): the Pilgrim rig json parses with its authored clips and sockets, and the builder turns a
    /// track into a stepped 12 fps curve (frame i holds until frame i + 1; a loop wraps to frame 0, a one-shot holds its last frame).
    /// </summary>
    public class PilgrimRigTests
    {
        const string JsonPath = "Assets/_Game/Art/ships/pilgrim/rig.json";

        [Test]
        public void TheRigJsonParsesWithClipsAndSockets()
        {
            Assert.IsTrue(File.Exists(JsonPath), "B-122 rig json in the project");
            var set = RigSet.Parse(File.ReadAllText(JsonPath), out var error);
            Assert.NotNull(set, error);
            Assert.AreEqual(11, set.parts.Length, "11 parts");
            Assert.AreEqual(2, set.plants.Length, "side and top plants");
            var side = set.FindPlant("pilgrim_side");
            Assert.NotNull(side);
            Assert.AreEqual(6, side.BoneCount);
            Assert.AreEqual(new[] { 0f, 1.6f }, side.bones[0].offset_m, "the root sits 1.6 m above the rig origin");
            Assert.AreEqual(7, side.sockets.Count, "seven sockets");
            Assert.AreEqual(new Vector2(0f, 0.85f), side.sockets["tail_exhaust"]);
            Assert.AreEqual(new Vector2(-1.5f, 2.6f), side.sockets["attitude_l"]);
            Assert.IsTrue(side.HasClips);
            Assert.AreEqual(3, side.clips.Length, "fin_wobble, leg_flex, hatch_open");
            var wobble = side.FindClip("fin_wobble");
            Assert.NotNull(wobble);
            Assert.IsTrue(wobble.loop); Assert.AreEqual(8, wobble.frames); Assert.AreEqual(12f, wobble.fps);
            Assert.AreEqual(3, wobble.tracks.Count, "fin_l, fin_r, fin_c");
            Assert.AreEqual(8, wobble.tracks["fin_l"].rot_deg.Length);
            Assert.AreEqual(3f, wobble.tracks["fin_l"].rot_deg[2], 1e-4f);
            Assert.AreEqual(8, wobble.tracks["fin_c"].scale.Length, "scale pairs per frame");
            Assert.AreEqual(new Vector2(1f, 0.981f), wobble.tracks["fin_c"].scale[0]);
            var hatch = side.FindClip("hatch_open");
            Assert.IsFalse(hatch.loop); Assert.AreEqual(6, hatch.frames);
            Assert.AreEqual(0.1f, hatch.tracks["hatch"].scale[5].x, 1e-4f, "the door slides to 10 %: the dark doorway shows");
            Assert.AreEqual(2, side.slots.Length, "bell + porthole static slots");
            Assert.IsFalse(side.slots[0].replaces_part);
            var top = set.FindPlant("pilgrim_top");
            Assert.AreEqual(3, top.BoneCount);
            Assert.AreEqual(1, top.clips.Length);
            Assert.AreEqual(0, top.sockets.Count);
            Assert.AreEqual("pilgrim_side_fin_wobble", RigSet.StateName("pilgrim_side", "fin_wobble"));
        }

        [Test]
        public void ParseFindsAPlantByItsExactNameWhateverTheKeyOrder()
        {
            // B-129's set: parts prefixed with the plant's name, `biomes` written before `bones`; the swaps must still be read.
            var json = "{\"key\":\"flora/x/rigset\",\"style\":\"v3\",\"parts\":[{\"name\":\"nodbell_stem\",\"rect\":[0,0,8,8]},{\"name\":\"nodbell_bells_hang\",\"rect\":[8,0,8,8]},{\"name\":\"nodbell_bells_nod\",\"rect\":[16,0,8,8]}],"
                     + "\"plants\":[{\"name\":\"nodbell\",\"biomes\":[\"plains\",\"forest\"],\"bones\":[{\"name\":\"root\",\"part\":\"nodbell_stem\",\"parent\":null},{\"name\":\"bells\",\"part\":\"nodbell_bells_hang\",\"parent\":\"root\"}],"
                     + "\"swaps\":{\"bells\":[\"nodbell_bells_hang\",\"nodbell_bells_nod\"]},\"slots\":[{\"slot\":\"bells\",\"bone\":\"bells\",\"offset_m\":[0,0],\"order\":1,\"replaces_part\":true}],"
                     + "\"sockets\":{\"tip\":[0.5,1.5]},\"idle\":{\"type\":\"sway\",\"amplitude_deg\":14,\"beat_bpm\":100,\"squash\":0.04},\"react\":{\"radius_m\":3,\"action\":\"turn_bounce\",\"swap\":\"nodbell_bells_nod\"}}]}";
            var set = RigSet.Parse(json, out var error);
            Assert.IsNull(error, error);
            var plant = set.FindPlant("nodbell");
            Assert.NotNull(plant);
            Assert.IsTrue(plant.swaps.ContainsKey("bells"), "swaps read from the plant object, not from a part named nodbell_*");
            Assert.AreEqual(new[] { "nodbell_bells_hang", "nodbell_bells_nod" }, plant.swaps["bells"]);
            Assert.AreEqual(new Vector2(0.5f, 1.5f), plant.sockets["tip"], "sockets read from the same span");
        }

        [Test]
        public void ParseRejectsAClipDrivingAnUnknownBone()
        {
            var json = "{\"key\":\"x/y/rig\",\"style\":\"v3\",\"parts\":[{\"name\":\"a\",\"rect\":[0,0,8,8]}],\"plants\":[{\"name\":\"p\",\"bones\":[{\"name\":\"root\",\"part\":\"a\",\"parent\":null}],"
                     + "\"clips\":[{\"name\":\"c\",\"fps\":12,\"loop\":true,\"frames\":2,\"tracks\":{\"ghost\":{\"rot_deg\":[0,1]}}}]}]}";
            Assert.IsNull(RigSet.Parse(json, out var error));
            StringAssert.Contains("unknown bone 'ghost'", error);
        }

        [Test]
        public void SteppedCurvesHoldEachFrameAndCloseTheLoop()
        {
            var values = new[] { 0f, 2f, 3f, 2f };
            var loop = RigSetBuilder.Stepped(values, 4, 12f, true);
            Assert.AreEqual(5, loop.length, "one key per frame plus the closing key");
            Assert.AreEqual(4f / 12f, loop.keys[4].time, 1e-5f, "the clip is frames / fps long");
            Assert.AreEqual(0f, loop.keys[4].value, "a loop wraps to frame 0");
            Assert.AreEqual(0f, loop.Evaluate(0.5f / 12f), 1e-5f, "frame 0 holds until frame 1");
            Assert.AreEqual(2f, loop.Evaluate(1.5f / 12f), 1e-5f, "stepped, no interpolation");
            Assert.AreEqual(2f, loop.Evaluate(3.9f / 12f), 1e-5f);
            var once = RigSetBuilder.Stepped(new[] { 1f, 0.5f, 0.1f }, 3, 12f, false);
            Assert.AreEqual(0.1f, once.keys[3].value, 1e-5f, "a one-shot holds its last frame");
            var shorter = RigSetBuilder.Stepped(new[] { 1f, 0.5f }, 4, 12f, false);
            Assert.AreEqual(0.5f, shorter.Evaluate(3.5f / 12f), 1e-5f, "a short track holds its last value to the end");
        }
    }
}
