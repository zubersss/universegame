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

        /// <summary>U-192 (G1): the docking bay draws the Pilgrim's rig in its rest pose on its canvas. RigBuild.BindPose lists the parts
        /// as Build places them (bones at their offsets, the bell and porthole slots, lowest order first); the pose stands on the rig
        /// origin (the ground line under the pads); and the bay's ship_ground is the one in B-223's layer1.json.</summary>
        [Test]
        public void TheBindPoseStandsOnTheBaysShipGround()
        {
            var set = RigSet.Parse(File.ReadAllText(JsonPath), out var error);
            Assert.NotNull(set, error);
            var side = set.FindPlant("pilgrim_side");
            var pose = RigBuild.BindPose(side);
            Assert.GreaterOrEqual(pose.Count, 6, "the hull, the nose, the fins, the hatch, the bell and the porthole");
            for (int i = 1; i < pose.Count; i++) Assert.GreaterOrEqual(pose[i].order, pose[i - 1].order, "lowest order first");
            float lowest = float.MaxValue, highest = float.MinValue, left = float.MaxValue, right = float.MinValue;
            var log = new System.Text.StringBuilder();
            foreach (var (sprite, at, order) in pose)
            {
                var part = System.Array.Find(set.parts, p => p.name == sprite);
                Assert.NotNull(part, $"{sprite}: a part of the sheet");
                float w = part.rect[2] / 64f, h = part.rect[3] / 64f;
                float px = part.pivot != null && part.pivot.Length == 2 ? part.pivot[0] : 0.5f, py = part.pivot != null && part.pivot.Length == 2 ? part.pivot[1] : 0.5f;
                lowest = Mathf.Min(lowest, at.y - py * h); highest = Mathf.Max(highest, at.y + (1f - py) * h);
                left = Mathf.Min(left, at.x - px * w); right = Mathf.Max(right, at.x + (1f - px) * w);
                log.Append($" {sprite}@({at.x:0.00}, {at.y:0.00}) order {order};");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u192 the Pilgrim's bind pose: {pose.Count} parts, {right - left:0.00} x {highest - lowest:0.00} m, from {lowest:0.00} to {highest:0.00} m over the rig origin:{log}");
            Assert.That(lowest, Is.InRange(-0.25f, 0.25f), "the pads stand on the rig origin's ground line");
            Assert.That(highest - lowest, Is.InRange(4f, 13.5f), "a ship's height that fits the bay (its ground point 186 px up a 1080 px layer at 64 px a metre)");
            Assert.That((left + right) * 0.5f, Is.InRange(-0.6f, 0.6f), "centred on the rig origin");
            // the bay's constants are the json's
            string bayJson = File.ReadAllText("Assets/_Game/Art/backgrounds/waystation/layer1.json");
            var m = System.Text.RegularExpressions.Regex.Match(bayJson, "\"ship_ground\"\\s*:\\s*\\{[^}]*\"px_from_bottom_left\"\\s*:\\s*\\[\\s*(\\d+)\\s*,\\s*(\\d+)");
            Assert.IsTrue(m.Success, "layer1.json states ship_ground.px_from_bottom_left");
            Assert.AreEqual(float.Parse(m.Groups[1].Value), Meridian.Trade.DockingBay.ShipGroundPx.x, "ship_ground x");
            Assert.AreEqual(float.Parse(m.Groups[2].Value), Meridian.Trade.DockingBay.ShipGroundPx.y, "ship_ground y");
            StringAssert.Contains("\"ppu\": 64", bayJson, "the bay's layers are 64 px a metre");
            Assert.AreEqual(64f, Meridian.Trade.DockingBay.BayPxPerMetre);
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
