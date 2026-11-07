using System.IO;
using System.Linq;
using Meridian.EditorTools;
using Meridian.Flora;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-097 (EditMode): rigset.json parsing per contract §11.3 (parts, ≤ 6 bones, swaps, idle, react, rejections) and the
    /// generated sway clips: stepped at 12 Hz over two beats, one controller per set. U-108 (contract v3.1, B-126 snoozle,
    /// D-101 no faces): `replaces_part` slots, the idle `swap_cycle` (steps once per beat, wraps), the react `also` map,
    /// their rejections, and the placeholder daisy (eyes/mouth extra renderers) still parsing.
    /// </summary>
    public class RigSetTests
    {
        const string Key = "flora/earth/rigset";

        static string LiveJson()
        {
            var art = ArtImporter.ArtColorPath(Key);
            var path = RigSetBuilder.JsonPath(File.Exists(art) ? art : ArtImporter.PlaceholderColorPath(Key));
            Assert.IsTrue(File.Exists(path), "rigset.json beside the live sheet");
            return File.ReadAllText(path);
        }

        /// <summary>BLENDER's v3.1 snoozle set itself (B-126, Assets/_Game/Art/flora/earth/rigset.json), never the placeholder fallback.</summary>
        static string ArtJson()
        {
            var path = RigSetBuilder.JsonPath(ArtImporter.ArtColorPath(Key));
            Assert.IsTrue(File.Exists(path), $"B-126 snoozle rig set at {path}");
            return File.ReadAllText(path);
        }

        static string PlaceholderJson()
        {
            var path = RigSetBuilder.JsonPath(ArtImporter.PlaceholderColorPath(Key));
            Assert.IsTrue(File.Exists(path), $"placeholder rig set at {path}");
            return File.ReadAllText(path);
        }

        [Test]
        public void ThePlaceholderSetParsesPerTheContract()
        {
            var set = RigSet.Parse(LiveJson(), out var error);
            Assert.IsNull(error, error);
            Assert.AreEqual("v3", set.style);
            Assert.AreEqual(64f, set.ppu);
            Assert.GreaterOrEqual(set.parts.Length, 5, "parts on the sheet");
            Assert.GreaterOrEqual(set.plants.Length, 1);
            var plant = set.plants[0];
            Assert.LessOrEqual(plant.BoneCount, RigSet.MaxBones, "≤ 6 bones");
            // Contract §11.3 shape (the live set is BLENDER's B-126 snoozle once it exists, else the placeholder daisy).
            Assert.GreaterOrEqual(plant.swaps.Count, 2, "swap slots (v3.1: heads and leaves, D-101; the placeholder: eyes and mouth)");
            foreach (var kv in plant.swaps) Assert.GreaterOrEqual(kv.Value.Length, 2, $"slot '{kv.Key}' has at least a resting part and one swap");
            Assert.AreEqual("sway", plant.idle.type);
            Assert.Greater(plant.idle.beat_bpm, 0f, "a beat");
            Assert.Greater(plant.idle.amplitude_deg, 0f, "a sway");
            Assert.Greater(plant.react.radius_m, 0f, "a react radius");
            Assert.IsFalse(string.IsNullOrEmpty(plant.react.action), "a react action");
            Assert.NotNull(set.FindPart(plant.react.swap), "the react swap is a part");
            foreach (var b in plant.bones) if (!string.IsNullOrEmpty(b.part)) Assert.NotNull(set.FindPart(b.part), b.part);
        }

        [Test]
        public void TheV31SnoozleParsesReplacedPartsTheSwapCycleAndTheReactAlso()
        {
            var set = RigSet.Parse(ArtJson(), out var error);
            Assert.IsNull(error, error);
            // B-126 drew the snoozle alone (7 parts); B-129 added the five C2 plants to the same sheet (44 parts): the seven stay.
            Assert.GreaterOrEqual(set.parts.Length, 7, "the snoozle's seven parts on the sheet (B-126), more with the C2 plants (B-129)");
            foreach (var part in new[] { "head_closed", "head_half", "head_open", "leaves_rest", "leaves_up", "stem_lower", "stem_upper" })
                Assert.IsTrue(System.Array.Exists(set.parts, p => p.name == part), $"snoozle part {part} on the sheet");
            var plant = set.FindPlant("snoozle");
            Assert.NotNull(plant, "the snoozle (B-126)");
            Assert.AreEqual(4, plant.BoneCount, "root, leaves, stem2, head");
            Assert.IsFalse(plant.swaps.ContainsKey("eyes") || plant.swaps.ContainsKey("mouth"), "no face parts (D-101)");

            // replaces_part: the head and leaves slots swap their bone's own part. A replaced part is hidden by substitution:
            // the bone's authored part is one of the slot's states, so the slot needs no second renderer over it.
            Assert.NotNull(plant.slots);
            Assert.AreEqual(2, plant.slots.Length);
            foreach (var name in new[] { "head", "leaves" })
            {
                var slot = plant.FindSlot(name);
                Assert.NotNull(slot, name);
                Assert.IsTrue(slot.replaces_part, $"'{name}' replaces its bone's part (no extra renderer)");
                int bone = plant.BoneIndex(slot.bone);
                Assert.GreaterOrEqual(bone, 0, $"'{name}' sits on a bone of the plant");
                Assert.Contains(plant.bones[bone].part, plant.swaps[name], $"the '{name}' bone carries one of the slot's states");
                Assert.AreEqual(plant.swaps[name][0], plant.bones[bone].part, "the resting state is the bone's authored part");
            }

            // idle.swap_cycle: head open 8 beats, half 1, closed 3, half 1 = 13 beats per loop.
            var cycle = plant.Cycle;
            Assert.NotNull(cycle, "idle.swap_cycle");
            Assert.AreEqual("head", cycle.slot);
            CollectionAssert.AreEqual(new[] { "head_open", "head_half", "head_closed", "head_half" }, cycle.sequence);
            CollectionAssert.AreEqual(new[] { 8, 1, 3, 1 }, cycle.beats);
            Assert.AreEqual(13, cycle.TotalBeats);
            Assert.AreEqual(110f, plant.idle.beat_bpm, "one beat = 60 / 110 s");

            // react: turn_bounce within 3 m, head_open on the head, also leaves_up on the leaves.
            Assert.AreEqual(3f, plant.react.radius_m);
            Assert.AreEqual("turn_bounce", plant.react.action);
            Assert.AreEqual("head_open", plant.react.swap);
            Assert.AreEqual(1, plant.react.also.Count, "one also slot");
            Assert.AreEqual("leaves_up", plant.react.also["leaves"]);
        }

        [Test]
        public void TheSwapCycleStepsOncePerBeatAndWraps()
        {
            int[] beats = { 8, 1, 3, 1 };
            int total = RigSet.SwapCycle.Total(beats);
            Assert.AreEqual(13, total, "the snoozle's loop: 8 + 1 + 3 + 1 beats");
            // Entry i holds for beats[i] whole beats: 0 on [0, 8), 1 on [8, 9), 2 on [9, 12), 3 on [12, 13).
            int[] expected = { 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 3 };
            for (int beat = 0; beat < total; beat++)
                foreach (var within in new[] { 0f, 0.25f, 0.5f, 0.999f })
                    Assert.AreEqual(expected[beat], RigSet.SwapCycle.IndexAt(beat + within, beats, total), $"beat {beat + within}: the index holds within a beat");
            // The index changes only on beat boundaries: four steps per loop (beats 8, 9, 12 and the wrap at 13).
            int steps = 0, last = RigSet.SwapCycle.IndexAt(0f, beats, total);
            for (int beat = 1; beat <= total; beat++) { int idx = RigSet.SwapCycle.IndexAt(beat, beats, total); if (idx != last) { steps++; last = idx; } }
            Assert.AreEqual(4, steps, "one step per entry per loop");
            Assert.AreEqual(0, RigSet.SwapCycle.IndexAt(13f, beats, total), "wraps at the total");
            Assert.AreEqual(1, RigSet.SwapCycle.IndexAt(21f, beats, total), "second loop, beat 8");
            Assert.AreEqual(3, RigSet.SwapCycle.IndexAt(25.5f, beats, total));
            Assert.AreEqual(0, RigSet.SwapCycle.IndexAt(26f, beats, total));
            Assert.AreEqual(0, RigSet.SwapCycle.IndexAt(5f, null, 0), "no beats: the first entry");
            Assert.AreEqual(0, RigSet.SwapCycle.IndexAt(5f, new int[0], 0));
            // The live snoozle's cycle agrees through its instance members.
            var plant = RigSet.Parse(ArtJson(), out _).FindPlant("snoozle");
            Assert.AreEqual(0, plant.Cycle.IndexAt(7.9f));
            Assert.AreEqual(1, plant.Cycle.IndexAt(8f));
            Assert.AreEqual(2, plant.Cycle.IndexAt(9f));
            Assert.AreEqual(3, plant.Cycle.IndexAt(12f));
            Assert.AreEqual(0, plant.Cycle.IndexAt(13f));
        }

        [Test]
        public void ThePlaceholderDaisyStillParsesWithItsFaceSlots()
        {
            var set = RigSet.Parse(PlaceholderJson(), out var error);
            Assert.IsNull(error, error);
            var plant = set.FindPlant("daisy");
            Assert.NotNull(plant, "the placeholder daisy");
            Assert.AreEqual(5, plant.BoneCount);
            Assert.IsTrue(plant.swaps.ContainsKey("eyes") && plant.swaps.ContainsKey("mouth"), "the daisy's face swaps (extra renderers, blink, react mouth)");
            Assert.IsTrue(plant.slots == null || plant.slots.Length == 0, "no slots: nothing replaces a part");
            Assert.IsNull(plant.Cycle, "no swap cycle");
            Assert.AreEqual(0, plant.react.also.Count, "no react also");
            Assert.AreEqual("mouth_giggle", plant.react.swap);
        }

        /// <summary>A three-part set (a, b, c) with one plant p (bones b0 = a, b1 = b) and the given v3.1 pieces spliced in.</summary>
        static string V31(string swaps, string slots, string cycle, string react) =>
            "{\"parts\": [{\"name\": \"a\", \"rect\": [0,0,8,8]}, {\"name\": \"b\", \"rect\": [8,0,8,8]}, {\"name\": \"c\", \"rect\": [16,0,8,8]}], " +
            "\"plants\": [{\"name\": \"p\", \"bones\": [{\"name\": \"b0\", \"part\": \"a\", \"parent\": null}, {\"name\": \"b1\", \"part\": \"b\", \"parent\": \"b0\"}], " +
            "\"swaps\": {" + swaps + "}, \"slots\": [" + slots + "], " +
            "\"idle\": {\"type\": \"sway\", \"beat_bpm\": 110" + cycle + "}, \"react\": {\"radius_m\": 3" + react + "}}]}";

        const string Swaps = "\"s\": [\"b\", \"c\"]";
        const string Replaced = "{\"slot\": \"s\", \"bone\": \"b1\", \"replaces_part\": true}";
        const string Cycle = ", \"swap_cycle\": {\"slot\": \"s\", \"sequence\": [\"b\", \"c\"], \"beats\": [2, 1]}";
        const string Also = ", \"swap\": \"c\", \"also\": {\"s\": \"c\"}";

        [Test]
        public void AMinimalV31SetParsesAndTheV30ShapeStillDoes()
        {
            var set = RigSet.Parse(V31(Swaps, Replaced, Cycle, Also), out var error);
            Assert.IsNull(error, error);
            var plant = set.plants[0];
            Assert.IsTrue(plant.slots[0].replaces_part);
            Assert.AreEqual("s", plant.Cycle.slot);
            CollectionAssert.AreEqual(new[] { "b", "c" }, plant.Cycle.sequence);
            CollectionAssert.AreEqual(new[] { 2, 1 }, plant.Cycle.beats);
            Assert.AreEqual(3, plant.Cycle.TotalBeats);
            Assert.AreEqual("c", plant.react.also["s"]);
            // The v3.0 shape (no replaced slot, no cycle, no also) is untouched.
            set = RigSet.Parse(V31(Swaps, "", "", ", \"swap\": \"c\""), out error);
            Assert.IsNull(error, error);
            plant = set.plants[0];
            Assert.IsNull(plant.Cycle);
            Assert.AreEqual(0, plant.react.also.Count);
            Assert.IsFalse(plant.slots != null && plant.slots.Any(s => s.replaces_part));
            // A slot without replaces_part is not held to the v3.1 rules (the placeholder's eyes/mouth hang on a bone or the head).
            Assert.NotNull(RigSet.Parse(V31(Swaps, "{\"slot\": \"s\", \"bone\": \"b9\"}", "", ", \"swap\": \"c\""), out error), error);
        }

        [Test]
        public void BadSetsAreRejectedWithAReason()
        {
            Assert.IsNull(RigSet.Parse("{\"parts\": [], \"plants\": []}", out var e1)); StringAssert.Contains("no parts", e1);
            const string head = "{\"parts\": [{\"name\": \"a\", \"rect\": [0,0,8,8]}], \"plants\": [{\"name\": \"p\", \"bones\": [";
            string seven = head + string.Join(",", new[] { 0, 1, 2, 3, 4, 5, 6 }.Select(i => $"{{\"name\": \"b{i}\", \"part\": \"a\", \"parent\": {(i == 0 ? "null" : $"\"b{i - 1}\"")}, \"length\": 0.5}}")) + "]}]}";
            Assert.IsNull(RigSet.Parse(seven, out var e2)); StringAssert.Contains("over 6", e2);
            Assert.IsNull(RigSet.Parse(head + "{\"name\": \"b0\", \"part\": \"missing\", \"parent\": null}]}]}", out var e3)); StringAssert.Contains("missing part", e3);
            Assert.IsNull(RigSet.Parse(head + "{\"name\": \"b0\", \"part\": \"a\", \"parent\": null}], \"swaps\": {\"mouth\": [\"nope\"]}}]}", out var e4)); StringAssert.Contains("nope", e4);
            Assert.IsNull(RigSet.Parse("not json", out var e5)); StringAssert.Contains("invalid", e5);
        }

        [Test]
        public void BadV31SetsAreRejectedWithAReason()
        {
            // A sequence entry that is not one of the slot's swaps.
            Assert.IsNull(RigSet.Parse(V31(Swaps, Replaced, ", \"swap_cycle\": {\"slot\": \"s\", \"sequence\": [\"b\", \"zzz\"], \"beats\": [2, 1]}", Also), out var e1)); StringAssert.Contains("zzz", e1);
            // Beats and sequence of different lengths.
            Assert.IsNull(RigSet.Parse(V31(Swaps, Replaced, ", \"swap_cycle\": {\"slot\": \"s\", \"sequence\": [\"b\", \"c\"], \"beats\": [2]}", Also), out var e2)); StringAssert.Contains("2 entries but 1 beats", e2);
            // A beat of 0.
            Assert.IsNull(RigSet.Parse(V31(Swaps, Replaced, ", \"swap_cycle\": {\"slot\": \"s\", \"sequence\": [\"b\", \"c\"], \"beats\": [2, 0]}", Also), out var e3)); StringAssert.Contains("at least 1", e3);
            // A cycle on a slot without swaps.
            Assert.IsNull(RigSet.Parse(V31(Swaps, Replaced, ", \"swap_cycle\": {\"slot\": \"nope\", \"sequence\": [\"b\"], \"beats\": [1]}", Also), out var e4)); StringAssert.Contains("not a swap slot", e4);
            // A replaced part on a bone whose part is not in the slot's swaps (b0 carries 'a'; s = [b, c]).
            Assert.IsNull(RigSet.Parse(V31(Swaps, "{\"slot\": \"s\", \"bone\": \"b0\", \"replaces_part\": true}", Cycle, Also), out var e5)); StringAssert.Contains("not among its swaps", e5);
            // A replaced part on an unknown bone, or on a slot without swaps.
            Assert.IsNull(RigSet.Parse(V31(Swaps, "{\"slot\": \"s\", \"bone\": \"b9\", \"replaces_part\": true}", Cycle, Also), out var e6)); StringAssert.Contains("unknown bone", e6);
            Assert.IsNull(RigSet.Parse(V31(Swaps, "{\"slot\": \"t\", \"bone\": \"b1\", \"replaces_part\": true}", Cycle, Also), out var e7)); StringAssert.Contains("no swaps", e7);
            // react.also on a slot without swaps, or showing a part that is not one of its swaps.
            Assert.IsNull(RigSet.Parse(V31(Swaps, Replaced, Cycle, ", \"swap\": \"c\", \"also\": {\"zz\": \"c\"}"), out var e8)); StringAssert.Contains("zz", e8);
            Assert.IsNull(RigSet.Parse(V31(Swaps, Replaced, Cycle, ", \"swap\": \"c\", \"also\": {\"s\": \"a\"}"), out var e9)); StringAssert.Contains("'a'", e9);
        }

        [Test]
        public void SwayClipsAreSteppedAt12HzOverTwoBeats()
        {
            var curve = RigSetBuilder.SwayCurve(12f, 110f, 1, 5);
            float period = 120f / 110f;
            Assert.AreEqual(Mathf.RoundToInt(period * 12f) + 1, curve.length, "one key per 1/12 s over two beats, plus the loop key");
            for (int i = 1; i < curve.length; i++) Assert.AreEqual(1f / 12f, curve[i].time - curve[i - 1].time, 1e-4f, "12 Hz");
            for (int i = 0; i < curve.length; i++)
            {
                Assert.AreEqual(AnimationUtility.TangentMode.Constant, AnimationUtility.GetKeyLeftTangentMode(curve, i), "stepped (left)");
                Assert.AreEqual(AnimationUtility.TangentMode.Constant, AnimationUtility.GetKeyRightTangentMode(curve, i), "stepped (right)");
                Assert.LessOrEqual(Mathf.Abs(curve[i].value), 12f / 5f + 1e-4f, "each bone takes its share of the amplitude");
            }
            Assert.AreEqual(curve[0].value, curve[curve.length - 1].value, 1e-5f, "seamless loop");
            var squash = RigSetBuilder.SquashCurve(0.08f, 110f, true);
            float min = 9f, max = 0f;
            for (int i = 0; i < squash.length; i++) { min = Mathf.Min(min, squash[i].value); max = Mathf.Max(max, squash[i].value); }
            Assert.AreEqual(1.08f, max, 0.005f, "8 % squash up (the 12 Hz samples sit just under the sine peak)");
            Assert.AreEqual(0.92f, min, 0.005f, "and down");
        }

        [Test]
        public void TheSetHasOneControllerWithAStatePerPlant()
        {
            var set = RigSet.Parse(LiveJson(), out _);
            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(RigSetBuilder.ControllerPath(Key));
            Assert.NotNull(controller, "generated by the importer (RigSetBuilder)");
            var machine = controller.layers[0].stateMachine;
            Assert.AreEqual(set.plants.Length, machine.states.Length, "one state per plant");
            foreach (var plant in set.plants)
            {
                var state = System.Array.Find(machine.states, s => s.state.name == plant.name);
                Assert.NotNull(state.state, plant.name);
                var clip = (AnimationClip)state.state.motion;
                Assert.AreEqual(12f, clip.frameRate, "12 fps");
                // U-108: the sway clip binds Transform curves only, so a runtime sprite swap on a bone renderer is never overwritten.
                foreach (var binding in AnimationUtility.GetCurveBindings(clip)) Assert.AreEqual(typeof(Transform), binding.type, $"{binding.path}/{binding.propertyName}: the clip animates Transforms, never SpriteRenderer sprites");
            }
            var art = ArtImporter.ArtColorPath(Key);
            var color = File.Exists(art) ? art : ArtImporter.PlaceholderColorPath(Key);
            var ti = (TextureImporter)AssetImporter.GetAtPath(color);
            Assert.AreEqual(SpriteImportMode.Multiple, ti.spriteImportMode, "the sheet is sliced into parts");
            Assert.AreEqual(64f, ti.spritePixelsPerUnit);
        }
    }
}
