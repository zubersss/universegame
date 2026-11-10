using System.Collections.Generic;
using Meridian.Player;
using Meridian.Rig;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools.Constraints; // AllocatingGCMemory on a constraint expression (Is.Not...)
using Is = UnityEngine.TestTools.Constraints.Is;

namespace Meridian.Tests
{
    /// <summary>
    /// U-209 (D-196, the owner's 0.6.2 playtest: the dig "feels disconnected from clicks"): the stroke's rules on a fake world at a fixed
    /// 60 fps step. A press starts a swing that frame and commits it; the shovel's contact lands five frames later; a tap does work; a
    /// press in the swing's last 0.15 s chains, an earlier one does not; held swings chain with no gap; the target is fixed for the swing;
    /// nothing to dig is a whiff and no work; a cell opens in the tables' time to within one swing (shovel and Beam); a target's work is
    /// kept 1.5 s, per target; nothing allocates. DigPose: the blade's tip meets the contact point by the slide and the lunge.
    /// </summary>
    public class DigStrokeTests
    {
        const float Dt = 1f / 60f;

        sealed class FakeWorld : IDigWorld
        {
            public DigTool tool = DigTool.Shovel;
            public float strokeSeconds = 1f, reach = 2f, rhythmStep, rhythmMax;
            public bool ground = true;
            public float RhythmStep => rhythmStep;
            public float RhythmMax => rhythmMax;
            public Vector2 origin;
            public readonly List<Vector2> opened = new List<Vector2>(256);
            public DigTool Tool => tool;
            public bool Target(Vector2 aim, out Vector2 point, out bool clamped)
            {
                var to = aim - origin;
                float d = to.magnitude;
                clamped = d > reach;
                point = clamped ? origin + to / d * reach : aim;
                return ground;
            }
            public float StrokeSeconds(Vector2 point) => strokeSeconds;
            public bool Open(Vector2 point) { opened.Add(point); return true; }
        }

        static readonly Vector2 Aim = new Vector2(1.2f, -0.6f);

        [Test]
        public void APressStartsASwingThatFrameAndCommitsIt()
        {
            var w = new FakeWorld();
            var s = new DigStroke();
            int started = 0;
            s.SwingStarted += (at, ok) => started++;
            s.Step(w, Dt, true, true, Aim); // the press' own frame
            Assert.AreEqual(DigPhase.Swing, s.Phase, "the swing is under way on the press' frame");
            Assert.AreEqual(0, s.Drawing, "its first drawing: the wind-up");
            Assert.AreEqual(1, started);
            Assert.AreEqual(Aim, s.Target);
            // released at once: the swing goes on to its contact and its end
            int contactFrame = -1, frames = 0;
            while (s.Active && frames < 200)
            {
                frames++;
                s.Step(w, Dt, false, false, Aim);
                if (s.ContactDone && contactFrame < 0) contactFrame = frames;
            }
            Assert.AreEqual(5, contactFrame, "the contact 5 frames after the press (0.083 s: the second drawing)");
            Assert.LessOrEqual(contactFrame, 6, "the card's bar: the first contact within 6 frames");
            Assert.AreEqual(25, frames, "a whole swing: five drawings at 12 Hz");
            Assert.AreEqual(1, s.Contacts);
            Assert.AreEqual(1, s.Swings, "released: one swing");
            Assert.AreEqual(DigStroke.SwingSeconds, 5f / 12f, 1e-6f);
            Assert.AreEqual(DigStroke.ContactSeconds, 1f / 12f, 1e-6f);
        }

        [Test]
        public void ATapDoesWorkAndPlaysAWholeSwing()
        {
            var w = new FakeWorld { strokeSeconds = 1f };
            var s = new DigStroke();
            s.Step(w, Dt, true, true, Aim);
            s.Step(w, Dt, false, true, Aim);
            s.Step(w, Dt, false, true, Aim); // held 0.05 s, then let go
            int frames = 2;
            while (s.Active && frames < 200) { frames++; s.Step(w, Dt, false, false, Aim); }
            Assert.AreEqual(25, frames, "the tap's swing runs whole");
            Assert.AreEqual(DigContact.Chip, s.LastContact);
            Assert.AreEqual(DigStroke.SwingSeconds / 1f, s.WorkAt(Aim), 1e-4f, "one contact's work: the swing's time over the stroke time");
            Assert.Greater(s.WorkAt(Aim), 0f);
            Assert.AreEqual(0, w.opened.Count, "not open yet");
        }

        [Test]
        public void APressInTheLastFifteenHundredthsIsBufferedAnEarlierOneIsNot()
        {
            var w = new FakeWorld();
            var s = new DigStroke();
            s.Step(w, Dt, true, false, Aim);
            for (int f = 1; f <= 12; f++) s.Step(w, Dt, f == 8, false, Aim); // a press 0.13 s in: far from the end, dropped
            Assert.IsFalse(s.Buffered, "a press outside the window is not kept");
            for (int f = 13; f <= 24; f++) s.Step(w, Dt, false, false, Aim);
            s.Step(w, Dt, false, false, Aim);
            Assert.IsFalse(s.Active, "no chain from the early press");

            s.Step(w, Dt, true, false, Aim);
            bool idleBetween = false;
            for (int f = 1; f <= 30; f++)
            {
                s.Step(w, Dt, f == 18, false, Aim); // 0.30 s in: inside the last 0.15 s (from 0.267 s)
                if (f == 18) Assert.IsTrue(s.Buffered, "kept for the swing's end");
                idleBetween |= !s.Active;
            }
            Assert.IsFalse(idleBetween, "the buffered press chains with no idle frame");
            Assert.AreEqual(3, s.Swings, "the first press', the second press', the buffered one");
            Assert.AreEqual(DigStroke.BufferSeconds, 0.15f, 1e-6f);
        }

        [Test]
        public void HeldSwingsChainWithNoGapAndTheTargetIsFixedForASwing()
        {
            var w = new FakeWorld { strokeSeconds = 100f };
            var s = new DigStroke();
            var contacts = new List<int>();
            int frame = 0;
            s.Contacted += (kind, at, stage) => contacts.Add(frame);
            s.Step(w, Dt, true, true, Aim);
            var first = s.Target;
            var moved = Aim + new Vector2(0.9f, 0.9f); // the cursor wanders off mid-swing
            for (frame = 1; frame <= 120; frame++)
            {
                s.Step(w, Dt, false, true, frame < 25 ? moved : Aim);
                Assert.IsTrue(s.Active, $"frame {frame}: no gap between held swings");
                if (frame < 25) Assert.AreEqual(first, s.Target, $"frame {frame}: the swing keeps the target it began with");
            }
            Assert.AreEqual(5, s.Swings, "2 s held: a swing every 25 frames");
            CollectionAssert.AreEqual(new[] { 5, 30, 55, 80, 105 }, contacts, "a contact every 25 frames, the first 5 after the press");
        }

        [Test]
        public void NothingToDigIsAWhiffAndNoWork()
        {
            var w = new FakeWorld { ground = false };
            var s = new DigStroke();
            DigContact? seen = null;
            s.Contacted += (kind, at, stage) => seen = kind;
            s.Step(w, Dt, true, false, Aim);
            Assert.IsFalse(s.Diggable);
            for (int f = 0; f < 30; f++) s.Step(w, Dt, false, false, Aim);
            Assert.AreEqual(DigContact.Whiff, seen, "the swing plays and whiffs");
            Assert.AreEqual(1, s.Whiffs);
            Assert.AreEqual(0f, s.WorkAt(Aim), "no work lands");
            Assert.AreEqual(0, w.opened.Count);
        }

        [Test]
        public void AClickPastReachDigsAtTheClamp()
        {
            var w = new FakeWorld { strokeSeconds = 0.3f, reach = 2f };
            var s = new DigStroke();
            var far = new Vector2(6f, 0f);
            s.Step(w, Dt, true, false, far);
            Assert.IsTrue(s.Clamped);
            Assert.AreEqual(new Vector2(2f, 0f), s.Target, "pulled in to the reach on the aim line");
            for (int f = 0; f < 30; f++) s.Step(w, Dt, false, false, far);
            Assert.AreEqual(1, w.opened.Count, "it digs there, never nothing");
            Assert.AreEqual(new Vector2(2f, 0f), w.opened[0]);
        }

        /// <summary>The shovel: n contacts open a cell whose stroke time is s, n = ceil(s / swing): press → open is 0.083 s + (n - 1) swings,
        /// within one swing of s. The times are D1's range: Earth T1 0.5 s to the 12 s cap.</summary>
        [Test]
        public void TheShovelOpensACellInTheTablesTimeToWithinOneSwing()
        {
            foreach (float stroke in new[] { 0.2f, 0.4f, 0.5f, 0.75f, 1f, 1.5f, 2.25f, 3f, 6f, 12f })
            {
                var w = new FakeWorld { strokeSeconds = stroke };
                var s = new DigStroke();
                s.Step(w, Dt, true, true, Aim);
                int frames = 0;
                while (w.opened.Count == 0 && frames < 2000) { frames++; s.Step(w, Dt, false, true, Aim); }
                float took = frames * Dt;
                Assert.AreEqual(DigStroke.SecondsToOpen(stroke), took, Dt * 1.01f, $"stroke {stroke} s: {DigStroke.ContactsToOpen(stroke)} contacts");
                Assert.LessOrEqual(Mathf.Abs(took - stroke), DigStroke.SwingSeconds + 1e-4f, $"stroke {stroke} s: opened in {took:0.000} s, within one swing of the tables' time");
                Assert.AreEqual(DigStroke.ContactsToOpen(stroke), s.Contacts, $"stroke {stroke} s");
                Assert.AreEqual(s.Contacts - 1, s.Chips, "every contact but the last is a chip");
                Assert.AreEqual(1, s.Opens);
            }
        }

        [Test]
        public void TheBeamIsOnFromThePressAndOpensInTheTablesTime()
        {
            foreach (float stroke in new[] { 0.25f, 0.5f, 1.25f, 4f, 8f })
            {
                var w = new FakeWorld { tool = DigTool.Beam, strokeSeconds = stroke, reach = 5f };
                var s = new DigStroke();
                s.Step(w, Dt, true, true, Aim);
                Assert.AreEqual(DigPhase.Beam, s.Phase, "the ray is on in the press' own frame");
                Assert.IsTrue(s.Diggable);
                int frames = 0;
                while (w.opened.Count == 0 && frames < 2000) { frames++; s.Step(w, Dt, false, true, Aim); }
                Assert.AreEqual(stroke, frames * Dt, Dt * 1.01f, $"stroke {stroke} s: the cell opens the frame its work completes");
            }
            // a 0.05 s tap: the ray stays on for 0.1 s and its work is kept
            var tap = new FakeWorld { tool = DigTool.Beam, strokeSeconds = 1f, reach = 5f };
            var b = new DigStroke();
            b.Step(tap, Dt, true, true, Aim);
            b.Step(tap, Dt, false, true, Aim);
            b.Step(tap, Dt, false, true, Aim);
            int on = 3;
            for (int f = 0; f < 30; f++) { b.Step(tap, Dt, false, false, Aim); if (b.Phase == DigPhase.Beam) on++; }
            Assert.GreaterOrEqual(on * Dt, DigStroke.BeamTapSeconds - Dt, "a tap's ray is seen for 0.1 s");
            Assert.AreEqual(DigPhase.Idle, b.Phase, "then off");
            Assert.Greater(b.WorkAt(Aim), 0.05f, "the tap did work");
            Assert.AreEqual(0, tap.opened.Count);
        }

        [Test]
        public void ATargetsWorkIsKeptOneAndAHalfSecondsAndIsItsOwn()
        {
            var w = new FakeWorld { strokeSeconds = 1f };
            var s = new DigStroke();
            var a = new Vector2(1.2f, -0.6f);
            var b = new Vector2(-1.4f, 0.3f);
            void Swing(Vector2 at) { s.Step(w, Dt, true, false, at); for (int f = 0; f < 25; f++) s.Step(w, Dt, false, false, at); }
            Swing(a);
            float one = s.WorkAt(a);
            Assert.AreEqual(DigStroke.SwingSeconds, one, 1e-4f);
            Swing(b);
            Assert.AreEqual(one, s.WorkAt(b), 1e-4f, "the other target starts its own work");
            Assert.AreEqual(one, s.WorkAt(a), 1e-4f, "the first keeps its own");
            Swing(a + new Vector2(0.3f, -0.2f)); // the cursor drifted 0.36 m: the same target
            Assert.AreEqual(a, s.LastContactAt, "worked where it was");
            Assert.AreEqual(2f * one, s.WorkAt(a), 1e-4f, "its work goes on");
            Assert.AreEqual(DigStroke.StageOf(2f * one), s.LastStage);
            Assert.AreEqual(1, DigStroke.StageOf(0.2f)); Assert.AreEqual(2, DigStroke.StageOf(0.5f)); Assert.AreEqual(3, DigStroke.StageOf(0.9f)); Assert.AreEqual(0, DigStroke.StageOf(0f));
            // left alone: kept 1.5 s after its last contact, then healed
            float last = s.Clock;
            while (s.Clock - last < DigStroke.WorkKeepSeconds - 0.5f) s.Step(w, Dt, false, false, a);
            Assert.Greater(s.WorkAt(a), 0f, "still kept a second after the contact");
            while (s.Clock - last < DigStroke.WorkKeepSeconds + 0.5f) s.Step(w, Dt, false, false, a);
            Assert.AreEqual(0f, s.WorkAt(a), "healed");
            Assert.AreEqual(1.5f, DigStroke.WorkKeepSeconds, 1e-6f);
        }

        [Test]
        public void ASwingAllocatesNothing()
        {
            var w = new FakeWorld { strokeSeconds = 1000f };
            var s = new DigStroke();
            int contacts = 0;
            s.Contacted += (kind, at, stage) => contacts++;
            s.SwingStarted += (at, ok) => { };
            for (int f = 0; f < 60; f++) s.Step(w, Dt, f == 0, true, Aim); // warm
            // The measure is Unity's own count of GC.Alloc samples on this thread (the test framework's constraint), with a control: a
            // measure that never moves passes anything. System.GC.GetAllocatedBytesForCurrentThread was the measure here until 07:4x:
            // what it reads for a known 4 KB array is printed below (0: this runtime does not count it, and the row it gave proved
            // nothing).
            long sys0 = System.GC.GetAllocatedBytesForCurrentThread();
            var known = new byte[4096];
            long sys = System.GC.GetAllocatedBytesForCurrentThread() - sys0;
            System.GC.KeepAlive(known);
            TestContext.Out.WriteLine($"[MERIDIAN] u209 allocation counters (EditMode): System.GC.GetAllocatedBytesForCurrentThread read {sys} B for a 4096 B array ({(sys >= 4096 ? "live" : "NOT live in this runtime")})");
            byte[] kept = null;
            Assert.That(() => { kept = new byte[64]; }, UnityEngine.TestTools.Constraints.Is.AllocatingGCMemory(), "the control: the constraint sees a 64 B array");
            System.GC.KeepAlive(kept);
            Assert.That(() => { for (int f = 0; f < 25 * 20; f++) s.Step(w, Dt, false, true, Aim + new Vector2(0.001f * f, 0f)); },
                UnityEngine.TestTools.Constraints.Is.Not.AllocatingGCMemory(), "20 swings of chips: no GC allocation");
            Assert.GreaterOrEqual(contacts, 20);
            // the Beam's ray, and both with the Rhythm node's numbers read every stroke
            var beam = new FakeWorld { tool = DigTool.Beam, strokeSeconds = 1000f, reach = 5f, rhythmStep = 0.1f, rhythmMax = 0.3f };
            var ray = new DigStroke();
            for (int f = 0; f < 60; f++) ray.Step(beam, Dt, f == 0, true, Aim);
            Assert.That(() => { for (int f = 0; f < 600; f++) ray.Step(beam, Dt, false, true, Aim + new Vector2(0.001f * f, 0f)); },
                UnityEngine.TestTools.Constraints.Is.Not.AllocatingGCMemory(), "10 s of the ray: no GC allocation");
        }

        // ---------- the rhythm (P-U209-3; D1 §5: "each consecutive stroke on the same face -10 % time (max -30 %)") ----------

        /// <summary>The Beam held on one face: its cells open in the tables' time x 1, 0.9, 0.8, 0.7, 0.7 with Rhythm I, x 0.5 at the end
        /// with Rhythm II, and in the tables' time every time with neither.</summary>
        [Test]
        public void TheRhythmNodeShortensEachConsecutiveCellOfTheBeamUpToItsMost()
        {
            foreach (var (step, max, name) in new[] { (0f, 0f, "not bought"), (0.1f, 0.3f, "Rhythm I"), (0.1f, 0.5f, "Rhythm II") })
            {
                var w = new FakeWorld { tool = DigTool.Beam, strokeSeconds = 1f, reach = 5f, rhythmStep = step, rhythmMax = max };
                var s = new DigStroke();
                s.Step(w, Dt, true, true, Aim);
                for (int cell = 0; cell < 7; cell++)
                {
                    int frames = 0;
                    while (w.opened.Count == cell && frames < 2000) { frames++; s.Step(w, Dt, false, true, Aim); }
                    float share = 1f - Mathf.Min(cell * step, max);
                    Assert.AreEqual(share, DigStroke.RhythmOf(cell, step, max), 1e-6f);
                    Assert.AreEqual(1f * share, frames * Dt, Dt * 1.01f, $"{name}: cell {cell + 1} opens in {share:0.0} of the tables' second");
                    Assert.AreEqual(share, s.RhythmFactor, 1e-6f, $"{name}: cell {cell + 1}'s share");
                }
                Assert.AreEqual(7, s.Rhythm, "seven strokes in the run");
            }
        }

        /// <summary>The shovel: each contact of a run takes its share off, so hard ground opens in fewer swings (a 4 s cell: 10 contacts,
        /// 8 with Rhythm I) and the run carries to the next cell of the face.</summary>
        [Test]
        public void TheRhythmNodeShortensTheShovelsContactsOnTheSameFace()
        {
            int Contacts(float step, float max, out DigStroke stroke, out FakeWorld world)
            {
                world = new FakeWorld { strokeSeconds = 4f, rhythmStep = step, rhythmMax = max };
                stroke = new DigStroke();
                stroke.Step(world, Dt, true, true, Aim);
                for (int f = 0; world.opened.Count == 0 && f < 2000; f++) stroke.Step(world, Dt, false, true, Aim);
                return stroke.Contacts;
            }
            Assert.AreEqual(10, Contacts(0f, 0f, out _, out _), "not bought: ceil(4 / 0.4167)");
            Assert.AreEqual(10, DigStroke.ContactsToOpen(4f));
            int rhythm = Contacts(0.1f, 0.3f, out var s, out var w);
            // the same sum by hand: a contact adds swing / (4 s x its share)
            float work = 0f; int expect = 0;
            while (work + 1e-4f < 1f) { work += DigStroke.SwingSeconds / (4f * DigStroke.RhythmOf(expect, 0.1f, 0.3f)); expect++; }
            Assert.AreEqual(expect, rhythm);
            Assert.AreEqual(8, rhythm, "Rhythm I: two swings fewer on a 4 s cell");
            Assert.AreEqual(8, s.Rhythm, "the run goes on to the next cell of the face");
            // the next cell (the same aim: the face behind) starts at the run's most: 0.7 of the time a contact
            for (int f = 0; w.opened.Count == 1 && f < 2000; f++) s.Step(w, Dt, false, true, Aim);
            Assert.AreEqual(8 + Mathf.CeilToInt(4f * 0.7f / DigStroke.SwingSeconds - 1e-4f), s.Contacts, "the second cell: every contact at 0.7");
        }

        /// <summary>The run ends on a whiff, on a stroke 3 m from the last (another face), and when the tool has rested 1.5 s; a stroke
        /// nearer than that, begun sooner, keeps it.</summary>
        [Test]
        public void TheRhythmsRunEndsOnAWhiffAJumpAndARest()
        {
            var w = new FakeWorld { strokeSeconds = 100f, reach = 50f, rhythmStep = 0.1f, rhythmMax = 0.3f };
            var s = new DigStroke();
            void Swing(Vector2 at) { s.Step(w, Dt, true, false, at); for (int f = 0; f < 25; f++) s.Step(w, Dt, false, false, at); }
            Swing(Aim); Swing(Aim); Swing(Aim);
            Assert.AreEqual(3, s.Rhythm);
            Assert.AreEqual(0.8f, s.RhythmFactor, 1e-6f, "the third stroke took 0.8 of the time");
            Swing(Aim + new Vector2(DigStroke.SameFaceM - 0.2f, 0f)); // along the face: the run goes on
            Assert.AreEqual(4, s.Rhythm);
            Assert.AreEqual(0.7f, s.RhythmFactor, 1e-6f);
            Swing(Aim + new Vector2(2f * DigStroke.SameFaceM + 1f, 0f)); // another face
            Assert.AreEqual(1, s.Rhythm, "a jump starts the run again");
            Assert.AreEqual(1f, s.RhythmFactor, 1e-6f);
            var there = Aim + new Vector2(2f * DigStroke.SameFaceM + 1f, 0f);
            Swing(there);
            Assert.AreEqual(2, s.Rhythm);
            w.ground = false; Swing(there); w.ground = true;
            Assert.AreEqual(0, s.Rhythm, "a whiff ends it");
            Swing(there); Swing(there);
            Assert.AreEqual(2, s.Rhythm);
            float last = s.Clock;
            while (s.Clock - last < DigStroke.WorkKeepSeconds + 0.2f) s.Step(w, Dt, false, false, there); // the tool rests
            Swing(there);
            Assert.AreEqual(1, s.Rhythm, "a rest of 1.5 s ends it");
            Assert.AreEqual(1f, s.RhythmFactor, 1e-6f);
            s.Reset();
            Assert.AreEqual(0, s.Rhythm);
        }

        // ---------- DigPose: the blade's tip on the contact point ----------

        [Test]
        public void TheBladesTipMeetsTheContactByTheSlideAndTheLunge()
        {
            const float blade = 1.33f, slideMax = 0.9f, lungeMax = 0.25f;
            var hand = new Vector2(0.3f, 0.9f);
            DigPose.Span(blade, slideMax, lungeMax, out float nearest, out float farthest);
            Assert.AreEqual(0.43f, nearest, 1e-4f); Assert.AreEqual(1.58f, farthest, 1e-4f);
            // every direction, every distance the pose spans: the tip is ON the target
            for (int deg = -90; deg <= 90; deg += 15)
                foreach (float d in new[] { 0.43f, 0.6f, 1f, 1.33f, 1.45f, 1.58f })
                {
                    var dir = new Vector2(Mathf.Cos(deg * Mathf.Deg2Rad), Mathf.Sin(deg * Mathf.Deg2Rad));
                    var target = hand + dir * d;
                    float miss = DigPose.Contact(hand, target, blade, slideMax, lungeMax, out var grip, out var along, out float slide, out float lunge, out var tip);
                    Assert.AreEqual(0f, miss, 1e-4f, $"{deg} deg, {d} m");
                    Assert.Less(Vector2.Distance(tip, target), 0.001f, $"{deg} deg, {d} m: the tip on the contact point");
                    Assert.AreEqual(blade, Vector2.Distance(grip, tip), 1e-4f, "the tool is rigid");
                    Assert.Less(Vector2.Distance(along, dir), 1e-4f, "turned along the line from the glove");
                    Assert.IsTrue(slide == 0f || lunge == 0f, "never both");
                    Assert.AreEqual(Mathf.Max(0f, blade - d), slide, 1e-4f); Assert.AreEqual(Mathf.Max(0f, d - blade), lunge, 1e-4f);
                }
            // past the lunge the tip stops short by the rest; nearer than the slide allows the blade passes the point (it buries)
            float shortBy = DigPose.Contact(hand, hand + Vector2.right * 1.9f, blade, slideMax, lungeMax, out _, out _, out _, out float l2, out var tip2);
            Assert.AreEqual(0.32f, shortBy, 1e-4f); Assert.AreEqual(lungeMax, l2, 1e-6f);
            Assert.AreEqual(1.58f, tip2.x - hand.x, 1e-4f);
            float buried = DigPose.Contact(hand, hand + Vector2.down * 0.2f, blade, slideMax, lungeMax, out _, out _, out float s3, out _, out var tip3);
            Assert.AreEqual(-0.23f, buried, 1e-4f); Assert.AreEqual(slideMax, s3, 1e-6f);
            Assert.AreEqual(hand.y - 0.43f, tip3.y, 1e-4f, "0.23 m past the contact");
        }

        /// <summary>D-196b: the brush opens from the contact, its centre 0.75 of its radius into the ground along the line. On a flat face
        /// that is the part of the disc behind the face; the bar is within 10 % of the tiles a whole disc (a stroke buried in the ground,
        /// as before D-196b) opens. Counted on the tile grid over every place of the point and of the face against the grid.</summary>
        [Test]
        public void AStrokeOnAFlatFaceOpensWithinATenthOfTheWholeBrush()
        {
            float r = RigTools.BrushRadius, push = RigTools.BrushPush;
            Assert.AreEqual(0.75f, RigTools.BrushPushShare, 1e-6f);
            double whole = 0, faced = 0;
            int n = 0;
            for (float fx = 0f; fx < 1f; fx += 0.05f)
                for (float fy = 0f; fy < 1f; fy += 0.05f)
                {
                    n++;
                    whole += RigTools.BrushCells(new Vector2(10f + fx, 10f + fy)).Count;       // every tile round it solid
                    float face = 10f + fx;                                                   // a wall: the tiles whose centres lie past x = face are solid
                    foreach (var c in RigTools.BrushCells(new Vector2(face + push, 10f + fy)))
                        if (c.x + 0.5f > face) faced++;
                }
            whole /= n; faced /= n;
            TestContext.Out.WriteLine($"[MERIDIAN] u209 the brush from the contact (radius {r:0.00} m, pushed {push:0.000} m into the ground): {faced:0.00} tiles a stroke on a flat face, {whole:0.00} a whole disc: {faced / whole * 100:0.0} %");
            Assert.That(faced / whole, Is.InRange(0.9, 1.1), "within 10 % of the tiles a stroke opened before");
        }

        [Test]
        public void TheSwingsClipIsPickedByTheAimsDirection()
        {
            Assert.AreEqual(SurveyorAnim.DigDown, SurveyorAnim.DigClipFor(new Vector2(0.6f, -1.2f)));
            Assert.AreEqual(SurveyorAnim.DigDown, SurveyorAnim.DigClipFor(new Vector2(-0.6f, -1.2f)), "either side");
            Assert.AreEqual(SurveyorAnim.DigUp, SurveyorAnim.DigClipFor(new Vector2(0.8f, 1.1f)));
            Assert.AreEqual(SurveyorAnim.DigFwd, SurveyorAnim.DigClipFor(new Vector2(1.8f, -0.3f)));
            Assert.AreEqual(SurveyorAnim.DigFwdNear, SurveyorAnim.DigClipFor(new Vector2(-1.0f, 0.2f)), "a forward contact nearer than 1.45 m");
            Assert.AreEqual(SurveyorAnim.AimFwd, SurveyorAnim.AimClipFor(new Vector2(3f, 0.4f)));
            Assert.AreEqual(SurveyorAnim.AimUp45, SurveyorAnim.AimClipFor(new Vector2(-2f, 2f)));
            Assert.AreEqual(SurveyorAnim.AimUp, SurveyorAnim.AimClipFor(new Vector2(0.2f, 3f)));
            Assert.AreEqual(SurveyorAnim.AimDown45, SurveyorAnim.AimClipFor(new Vector2(2f, -2f)));
            Assert.AreEqual(SurveyorAnim.AimDown, SurveyorAnim.AimClipFor(new Vector2(0.1f, -3f)));
        }
    }
}
