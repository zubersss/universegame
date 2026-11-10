using System.Collections;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Player;
using Meridian.Progress;
using Meridian.Rig;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-209 (D-196, the owner's 0.6.2 playtest: the dig "feels disconnected from clicks and the avatar"): the dig's response in the game
    /// at a fixed 60 fps step (Time.captureDeltaTime). The press is seen by the next Update; that frame is frame 0 of every row.
    /// Rows: the swing is drawn in frame 0; the shovel's first contact within 6 frames; the Beam's ray and glow in frame 0 and its hum
    /// within a frame; a 0.05 s tap plays a whole swing and adds work; a buffered press chains; a click past reach digs at the clamp;
    /// with nothing in reach the swing whiffs and no work lands; the blade's tip within 0.08 m of the contact point on the contact
    /// drawing wherever the pose reaches it (the slide and the lunge; the bury and the shortfall named where it does not); a cell opens
    /// at T1..T5 within one swing of the tables' stroke time (shovel and Beam); the tool does not follow the cursor with the button up;
    /// swinging allocates nothing over an idle frame.
    /// </summary>
    public class DigResponseTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const float Step = 1f / 60f;
        PlanetSideRoot side;
        PlayerController player;
        TerrainStreamer t;
        PlayerRigInput input;
        RigToolView view;
        RigTools rig;
        DigTool? suiteTool;

        IEnumerator Boot(DigTool tool)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            side = director.PlanetSide;
            player = side.player;
            t = side.terrain;
            rig = side.rig;
            player.externalInput = true; player.intent = default;
            if (side.hazards != null) side.hazards.enabled = false;
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();
            Assert.IsTrue(t.SmoothGround, "Earth's smooth ground");
            GameState.Instance.inventory.ReadFrom(new System.Collections.Generic.List<ItemStack>(), 0);
            GameState.Instance.dirt.count = 0;
            suiteTool = SkillStats.ToolOverride;
            SkillStats.ToolOverride = tool;
            rig.BeamPower = 1f; // the tables' start power for either tool
            input = player.GetComponent<PlayerRigInput>();
            input.module = RigModule.Beam;
            input.holdUse = false;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
            view = input.ToolView;
            Assert.NotNull(view, "the tool view");
            timeout = Time.realtimeSinceStartup + 15f;
            while ((view.Tool.sprite == null || view.Body == null || (tool == DigTool.Beam && !view.RayReady)) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.NotNull(view.Tool.sprite, "the tool's sprite is in");
            Time.captureDeltaTime = Step; // every frame is 1/60 s of game time
            yield return null;
        }

        void Restore()
        {
            Time.captureDeltaTime = 0f;
            if (input != null) { input.holdUse = false; input.externalAim = false; }
            if (rig != null) rig.BeamPower = 0f;
            SkillStats.ToolOverride = suiteTool;
            if (player != null && player.Body != null) player.Body.simulated = true;
        }

        /// <summary>The surveyor held still in a dug pocket `depth` m under the Surface Line at x (a 3 x 3 m hollow), its feet on the floor.</summary>
        IEnumerator StandAtDepth(float x, float depth)
        {
            float floorY = DigRun.LineAt(t, x) - depth;
            int fx = Mathf.FloorToInt(x), fy = Mathf.FloorToInt(floorY);
            var b = player.Body;
            b.simulated = false;
            b.position = new Vector2(fx + 0.5f, fy + 1.05f); player.transform.position = b.position;
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int c = fx - 1; c <= fx + 1; c++) for (int y = fy; y <= fy + 2; y++) t.SetTile(c, y, TileId.Air);
            yield return new WaitForFixedUpdate();
            b.position = new Vector2(fx + 0.5f, fy + 0.05f); player.transform.position = b.position;
            b.linearVelocity = Vector2.zero;
            for (int i = 0; i < 6; i++) yield return null;
        }

        /// <summary>The surveyor held still on the open ground at x.</summary>
        IEnumerator StandOnSurface(float x)
        {
            var b = player.Body;
            b.simulated = false;
            var feet = new Vector2(Mathf.Floor(x) + 0.5f, t.SurfaceAt(Mathf.Floor(x) + 0.5f) + 0.05f);
            b.position = feet; player.transform.position = feet;
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 6; i++) yield return null;
        }

        /// <summary>Waits until no stroke runs (a swing ends by itself), the button up.</summary>
        IEnumerator Rest()
        {
            input.holdUse = false;
            for (int i = 0; i < 80 && input.Stroke.Active; i++) yield return null;
            yield return null;
            Assert.IsFalse(input.Stroke.Active, "at rest");
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator TheShovelAnswersThePressInItsOwnFrame()
        {
            yield return Boot(DigTool.Shovel);
            try
            {
                float x = player.Body.position.x;
                yield return StandAtDepth(x + 30f, 56f); // Stone: a cell takes several contacts
                var feet = player.Body.position;
                var target = new Vector2(feet.x + 1.4f, feet.y + 0.6f);
                input.AimAt(target);
                yield return Rest();
                var stroke = input.Stroke;
                Assert.AreEqual(DigTool.Shovel, rig.Tool);
                Assert.IsTrue(view.Carrying, "carried at rest");
                float carried = view.AimDegrees;
                int contactFrame = -1, startedFrame = -1;
                DigContact contactKind = DigContact.Whiff;
                System.Action<Vector2, bool> onStart = (at, ok) => startedFrame = Time.frameCount;
                System.Action<DigContact, Vector2, int> onContact = (kind, at, stage) => { if (contactFrame < 0) { contactFrame = Time.frameCount; contactKind = kind; } };
                stroke.SwingStarted += onStart; stroke.Contacted += onContact;
                int swings = stroke.Swings, chips = side.digFeel.Chips, whooshes = side.digFeel.Whooshes;
                int press = Time.frameCount + 1; // the next Update sees the press
                input.holdUse = true;
                yield return null;               // frame `press`: Update has run, its LateUpdate comes after this resumes
                Assert.AreEqual(press, Time.frameCount);
                Assert.AreEqual(press, startedFrame, "the swing starts in the frame that sees the press");
                Assert.AreEqual(DigPhase.Swing, stroke.Phase);
                Assert.AreEqual(press, input.StrokeStartFrame);
                Assert.AreEqual(target, stroke.Target, "at the aim");
                yield return null;               // frame press + 1: what frame `press` drew is on the view
                Assert.AreEqual(press, view.SwingShownFrame, "press -> the first visible change: the same frame (0 frames; the bar is 1)");
                Assert.IsFalse(view.Carrying, "out of the carry pose");
                Assert.Greater(Mathf.Abs(Mathf.DeltaAngle(carried, view.AimDegrees)), 20f, "the tool is raised for the wind-up");
                Assert.AreNotEqual(0f, view.Body.StrokeLean, "the body leans back for it");
                Assert.AreEqual(1, side.digFeel.Whooshes - whooshes, "the whoosh at the swing's start");
                for (int i = 0; i < 12 && contactFrame < 0; i++) yield return null;
                Assert.Greater(contactFrame, 0, "the contact came");
                TestContext.Out.WriteLine($"[MERIDIAN] u209 shovel: press at frame {press}, drawn in frame {view.SwingShownFrame}, contact {contactFrame - press} frames after the press ({contactKind}), stroke time there {rig.StrokeSeconds(target):0.00} s");
                Assert.LessOrEqual(contactFrame - press, 6, "press -> the shovel's first contact within 6 frames");
                Assert.AreEqual(5, contactFrame - press, "five frames: the second drawing at 12 Hz");
                Assert.AreEqual(DigContact.Chip, contactKind, "Stone does not open at the first contact: a chip");
                yield return null;
                Assert.AreEqual(1, side.digFeel.Chips - chips, "the chip's crumbs flew");
                Assert.Greater(view.CrackStage, 0, "the crack mark shows the work");
                Assert.Greater(input.StrokeProgress, 0f);
                yield return Rest();
                Assert.AreEqual(1, stroke.Swings - swings, "held 7 frames: one swing");
                stroke.SwingStarted -= onStart; stroke.Contacted -= onContact;
                LogAssert.NoUnexpectedReceived();
            }
            finally { Restore(); }
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator ATapSwingsWholeABufferedPressChainsAndTheToolIgnoresTheCursorAtRest()
        {
            yield return Boot(DigTool.Shovel);
            try
            {
                float x = player.Body.position.x;
                yield return StandAtDepth(x + 44f, 56f);
                var feet = player.Body.position;
                var target = new Vector2(feet.x + 1.4f, feet.y + 0.6f);
                var stroke = input.Stroke;

                // the button up: the cursor moves, the tool does not (no swing yet: the shovel is stowed)
                yield return Rest();
                float rest = view.AimDegrees;
                foreach (var d in new[] { new Vector2(2f, 1f), new Vector2(1f, -2f), new Vector2(3f, 3f), new Vector2(0.5f, 0.2f) })
                {
                    input.AimAt(feet + d);
                    yield return null; yield return null;
                    Assert.AreEqual(rest, view.AimDegrees, 1e-3f, $"the cursor at {d}: the tool's angle does not change with the button up");
                    Assert.IsTrue(view.Carrying);
                    Assert.IsTrue(view.Stowed, "stowed until the first swing");
                    Assert.AreEqual(RigToolView.StowAngle(false), view.AimDegrees, 1e-3f, "the stowed pose (facing right)");
                    Assert.AreEqual(Meridian.View2D.SpriteCharacterView.SurveyorOrder - 1, view.Tool.sortingOrder, "drawn behind the body");
                }

                // a 0.05 s tap: three frames held
                input.AimAt(target);
                yield return null;
                int swings = stroke.Swings, contacts = stroke.Contacts;
                int press = Time.frameCount + 1;
                input.holdUse = true;
                yield return null; yield return null; yield return null;
                input.holdUse = false;
                int frames = 3;
                while (stroke.Active && frames < 80) { frames++; yield return null; }
                Assert.AreEqual(1, stroke.Swings - swings, "a tap is one swing");
                Assert.AreEqual(1, stroke.Contacts - contacts, "with its contact");
                Assert.That(frames, Is.InRange(25, 27), "the swing played whole (25 frames)");
                Assert.Greater(stroke.WorkAt(target), 0f, "the tap added work");
                TestContext.Out.WriteLine($"[MERIDIAN] u209 tap: held 3 frames (0.05 s), the swing ran {frames} frames, work {stroke.WorkAt(target):0.000} of 1");

                // after a swing the tool stays READY in the hand for 1.5 s (a burst of clicks never stows it), the cursor still ignored; then it is stowed
                yield return null; yield return null;
                Assert.IsTrue(view.Carrying && !view.Stowed, "ready after the swing");
                Assert.AreEqual(RigToolView.CarryAngle(false), view.AimDegrees, 1e-3f, "the ready pose: low, in front");
                Assert.AreEqual(Meridian.View2D.SpriteCharacterView.SurveyorOrder, view.Tool.sortingOrder);
                input.AimAt(feet + new Vector2(-2f, 2f));
                for (int i = 0; i < 30; i++) yield return null;
                Assert.IsFalse(view.Stowed, "still ready 0.5 s on");
                Assert.AreEqual(RigToolView.CarryAngle(false), view.AimDegrees, 1e-3f, "whatever the cursor does");
                for (int i = 0; i < 75; i++) yield return null;
                Assert.IsTrue(view.Stowed, "stowed 1.5 s after the last swing");
                input.AimAt(target);
                yield return null;

                // a press in the swing's last 0.15 s chains with no idle frame
                yield return Rest();
                swings = stroke.Swings;
                input.holdUse = true; yield return null; input.holdUse = false;      // the first press
                for (int i = 0; i < 17; i++) yield return null;                       // 0.30 s into the swing
                input.holdUse = true; yield return null; input.holdUse = false;      // the buffered press
                bool idle = false;
                for (int i = 0; i < 12; i++) { yield return null; idle |= !stroke.Active; }
                Assert.IsFalse(idle, "no idle frame between the swings");
                Assert.AreEqual(2, stroke.Swings - swings, "the buffered press chained");
                yield return Rest();
                LogAssert.NoUnexpectedReceived();
            }
            finally { Restore(); }
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator PastReachDigsAtTheClampAndNothingInReachWhiffs()
        {
            yield return Boot(DigTool.Shovel);
            try
            {
                float x = player.Body.position.x;
                yield return StandOnSurface(x + 24f);
                var feet = player.Body.position;
                var stroke = input.Stroke;
                float reach = SkillStats.DigReach;
                Assert.AreEqual(2f, reach, 1e-4f, "the shovel's reach by the tables");

                // a click 7 m off, down and ahead: past reach
                var far = feet + new Vector2(5f, -5f);
                input.AimAt(far);
                yield return Rest();
                yield return null;
                Assert.IsTrue(view.ReticleClamped, "the reticle is pulled in to the reach");
                Assert.IsTrue(view.ReticleDiggable, "onto ground");
                Assert.LessOrEqual(Vector2.Distance(view.ReticleAt, feet), reach + 1e-3f, "inside the reach");
                Assert.AreEqual(RigToolView.ReticleAtReach, view.Reticle.color, "tinted as clamped");
                Vector2 dugAt = default;
                bool dug = false;
                System.Action<Vector2> onDug = p => { dug = true; dugAt = p; };
                rig.Dug += onDug;
                input.holdUse = true;
                float until = Time.time + 3f;
                while (!dug && Time.time < until) yield return null;
                input.holdUse = false;
                rig.Dug -= onDug;
                Assert.IsTrue(dug, "a click past reach digs, never nothing");
                Assert.IsTrue(stroke.Clamped);
                Assert.LessOrEqual(Vector2.Distance(dugAt, feet), reach + 1e-3f, "at the clamp");
                var shoulder = rig.DigOrigin;
                float off = Mathf.Abs(Vector3.Cross((far - shoulder).normalized, dugAt - shoulder).z);
                Assert.Less(off, 0.02f, "on the aim line from the shoulder");
                TestContext.Out.WriteLine($"[MERIDIAN] u209 past reach: the click {Vector2.Distance(far, feet):0.0} m off, dug {Vector2.Distance(dugAt, feet):0.00} m from the body, {off:0.000} m off the aim line");
                yield return Rest();

                // nothing to dig: straight up into the open air
                var air = feet + new Vector2(0.4f, 6f);
                input.AimAt(air);
                yield return null; yield return null;
                Assert.IsFalse(view.ReticleDiggable, "nothing there");
                Assert.AreEqual(RigToolView.ReticleNothing, view.Reticle.color, "the reticle's empty state");
                int whiffs = stroke.Whiffs, opens = stroke.Opens, swings = stroke.Swings, bursts = side.digFeel.Bursts, chips = side.digFeel.Chips;
                input.holdUse = true; yield return null; yield return null; input.holdUse = false;
                int frames = 2;
                while (stroke.Active && frames < 80) { frames++; yield return null; }
                Assert.AreEqual(1, stroke.Swings - swings, "the swing plays");
                Assert.AreEqual(1, stroke.Whiffs - whiffs, "and whiffs");
                Assert.AreEqual(0, stroke.Opens - opens);
                Assert.AreEqual(0f, stroke.WorkAt(stroke.Target), "no work lands");
                Assert.AreEqual(0, side.digFeel.Bursts - bursts, "no debris");
                Assert.AreEqual(0, side.digFeel.Chips - chips);
                LogAssert.NoUnexpectedReceived();
            }
            finally { Restore(); }
        }

        /// <summary>The blade's tip on the contact drawing, three directions across the reach. Until B-246's dig clips arrive the glove is
        /// the idle drawing's, carried by the lean and the lunge; the 0.08 m row holds wherever DigPose's span reaches from that glove,
        /// and where it does not the test names the miss (short of a far target, buried past a near one) and holds the tip to it.</summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator TheBladesTipIsOnTheContactPointOnTheContactDrawing()
        {
            yield return Boot(DigTool.Shovel);
            try
            {
                float x = player.Body.position.x;
                yield return StandOnSurface(x + 36f);
                var feet = player.Body.position;
                var stroke = input.Stroke;
                var shoulder = rig.DigOrigin;
                float blade = RigTools.ShovelBlade;
                Assert.AreEqual(1.33f, blade, 0.02f, "shovel.json's blade_tip");
                int held = 0, total = 0;
                var log = new System.Text.StringBuilder();
                foreach (var (name, deg) in new[] { ("down", -70f), ("forward", -8f), ("up", 62f) })
                    foreach (float dist in new[] { 0.7f, 1.0f, 1.3f, 1.6f, 1.9f })
                    {
                        var dir = new Vector2(Mathf.Cos(deg * Mathf.Deg2Rad), Mathf.Sin(deg * Mathf.Deg2Rad));
                        var target = shoulder + dir * dist;
                        if (Vector2.Distance(target, feet) > SkillStats.DigReach) continue; // past the tables' reach from the body: clamped, not this row
                        input.AimAt(target);
                        yield return Rest();
                        stroke.Reset(); // no kept work: a swing near the last target would go on working that one
                        int contacts = stroke.Contacts;
                        input.holdUse = true; yield return null; input.holdUse = false;
                        for (int i = 0; i < 12 && stroke.Contacts == contacts; i++) yield return null;
                        Assert.AreEqual(contacts + 1, stroke.Contacts, $"{name} {dist} m: the contact");
                        yield return null; // the contact frame's drawing is on the view (the contact drawing lasts five frames)
                        Assert.AreEqual(DigStroke.ContactDrawing, stroke.Drawing, "still the contact drawing");
                        Assert.Less(Vector2.Distance(stroke.Target, target), 1e-3f, $"{name} {dist} m: the swing's target is the aim");
                        float gap = Vector2.Distance(view.TipWorld, target);
                        float fromGlove = Vector2.Distance(view.HandWorld, target) + view.LungeNow; // the glove before the lunge
                        DigPose.Span(blade, view.SlideMaxNow, RigTools.ShovelLungeM, out float nearest, out float farthest);
                        bool reachable = fromGlove >= nearest - 1e-3f && fromGlove <= farthest + 1e-3f;
                        total++;
                        log.Append($"\n  {name} {dist:0.0} m from the shoulder ({fromGlove:0.00} m from the glove): tip {gap:0.000} m off, slide {view.SlideNow:0.00}, lunge {view.LungeNow:0.00}, miss {view.TipMiss:+0.00;-0.00;0.00}{(reachable ? "" : " (out of the pose's span)")}");
                        if (reachable)
                        {
                            held++;
                            Assert.LessOrEqual(gap, 0.08f, $"{name} {dist} m: the blade's tip within 0.08 m of the contact point");
                        }
                        else Assert.AreEqual(Mathf.Abs(view.TipMiss), gap, 0.02f, $"{name} {dist} m: out of the span, the tip is off by the pose's own miss");
                        Assert.AreEqual(0f, view.ScoopArcDegrees, 0.5f, "turned along the line to the target on the contact drawing");
                        Assert.IsTrue(view.Body.Renderer.flipX == (target.x < feet.x), "the surveyor faces the target");
                    }
                TestContext.Out.WriteLine($"[MERIDIAN] u209 blade tip on the contact drawing ({(view.SwingOnClip ? "the sheet's dig clips" : "the idle glove: no dig clip on the sheet yet")}, slide up to {view.SlideMaxNow} m, lunge up to {RigTools.ShovelLungeM} m): {held} of {total} targets inside the pose's span, all within 0.08 m:{log}");
                Assert.GreaterOrEqual(held, 6, "the row is held on most of the reach");
                // facing: a target behind turns the surveyor for the swing and it stays turned after
                input.AimAt(shoulder + new Vector2(-1.2f, -0.6f));
                yield return Rest();
                input.holdUse = true; yield return null; input.holdUse = false;
                yield return null; yield return null;
                Assert.IsTrue(view.Body.Renderer.flipX, "faces left for the swing");
                Assert.AreEqual(-1, input.StrokeFacing);
                yield return Rest();
                yield return null;
                Assert.AreEqual(-1, player.Facing, "and keeps that side after it");
                LogAssert.NoUnexpectedReceived();
            }
            finally { Restore(); }
        }

        [UnityTest, Timeout(600000)]
        public IEnumerator ACellOpensInTheTablesTimeToWithinOneSwingAtEveryTier()
        {
            yield return Boot(DigTool.Shovel);
            try
            {
                float x = player.Body.position.x;
                int spot = 0;
                var log = new System.Text.StringBuilder();
                foreach (var tool in new[] { DigTool.Shovel, DigTool.Beam })
                {
                    SkillStats.ToolOverride = tool;
                    rig.BeamPower = 1f;
                    for (int i = 0; i < 5; i++) yield return null;
                    foreach (float depth in new[] { 5f, 20f, 56f, 150f, 215f })
                    {
                        yield return StandAtDepth(x + 40f + 12f * spot++, depth); // a fresh wall each time
                        var feet = player.Body.position;
                        var target = new Vector2(Mathf.Floor(feet.x) + 2.0f, Mathf.Floor(feet.y) + 0.6f); // the wall beside the hollow, inside 2 m
                        Assert.LessOrEqual(Vector2.Distance(target, feet), SkillStats.DigReach, "inside the reach");
                        float expect = rig.StrokeSeconds(target);
                        Assert.AreEqual(D1Tables.Current.StrokeSeconds(Meridian.Planets.PlanetId.Earth, DigRun.Depth(t, target), 1f, tool), expect, 1e-4f);
                        input.AimAt(target);
                        yield return Rest();
                        bool dug = false;
                        System.Action<Vector2> onDug = p => dug = true;
                        rig.Dug += onDug;
                        int press = Time.frameCount + 1, frames = 0;
                        input.holdUse = true;
                        yield return null; // frame `press`
                        while (!dug && frames < 60 * 20) { frames++; yield return null; }
                        input.holdUse = false;
                        rig.Dug -= onDug;
                        Assert.IsTrue(dug, $"{tool} at {depth} m: the cell opens");
                        float took = frames * Step;
                        int tier = DigRun.TierAt(t, target) + 1;
                        log.Append($"\n  {tool} T{tier} ({depth:0} m): the tables' {expect:0.00} s, opened {took:0.00} s after the press ({took - expect:+0.00;-0.00} s)");
                        Assert.LessOrEqual(Mathf.Abs(took - expect), DigStroke.SwingSeconds + 2f * Step, $"{tool} T{tier}: within one swing of the tables' {expect:0.00} s (took {took:0.00} s)");
                        if (tool == DigTool.Shovel) Assert.AreEqual(DigStroke.SecondsToOpen(expect), took, 2f * Step, $"shovel T{tier}: the contact that completes the work");
                        else Assert.AreEqual(expect, took, 3f * Step, $"Beam T{tier}: the frame the work completes");
                        yield return Rest();
                    }
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u209 time to open one cell, the press to the opening at a 60 fps step (power 1):{log}");
                LogAssert.NoUnexpectedReceived();
            }
            finally { Restore(); }
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator TheBeamsRayGlowAndHumAnswerThePress()
        {
            yield return Boot(DigTool.Beam);
            try
            {
                float x = player.Body.position.x;
                yield return StandAtDepth(x + 52f, 56f);
                var feet = player.Body.position;
                var target = new Vector2(Mathf.Floor(feet.x) + 2.5f, Mathf.Floor(feet.y) + 0.6f);
                input.AimAt(target);
                yield return Rest();
                var stroke = input.Stroke;
                var audio = Meridian.Audio.AudioDirector.Instance;
                Assert.AreEqual(DigTool.Beam, rig.Tool);
                Assert.IsTrue(view.RayReady, "the ray's sheet is in");
                Assert.IsFalse(view.Beam.enabled, "no ray at rest");
                Assert.IsTrue(view.Carrying, "the Beam is carried at rest");
                int press = Time.frameCount + 1;
                input.holdUse = true;
                yield return null; // frame `press`
                Assert.AreEqual(DigPhase.Beam, stroke.Phase, "the ray's stroke is on in the frame that sees the press");
                Assert.AreEqual(press, input.StrokeStartFrame);
                yield return null; // what frame `press` drew
                Assert.AreEqual(press, view.RayShownFrame, "press -> the ray: the same frame (0 frames; the bar is 1)");
                Assert.IsTrue(view.Beam.enabled, "the ray is drawn");
                Assert.IsTrue(view.Glow.enabled, "with its glow at the hit");
                Assert.Less(Vector2.Distance(view.Glow.transform.position, view.BeamEnd), 1e-3f, "at the ray's end");
                Assert.Greater(view.BeamLength, 0.2f);
                if (audio != null) Assert.IsTrue(audio.BeamHumOn, "the hum within a frame of the press");
                // the tool turns to the aim over about 0.06 s, damped: not a snap, there within 0.3 s
                float toAim = Mathf.Atan2(target.y - view.HandWorld.y, target.x - view.HandWorld.x) * Mathf.Rad2Deg;
                float first = Mathf.Abs(Mathf.DeltaAngle(view.AimDegrees, toAim));
                for (int i = 0; i < 18; i++) yield return null;
                float later = Mathf.Abs(Mathf.DeltaAngle(view.AimDegrees, Mathf.Atan2(target.y - view.HandWorld.y, target.x - view.HandWorld.x) * Mathf.Rad2Deg));
                TestContext.Out.WriteLine($"[MERIDIAN] u209 Beam: press at frame {press}, the ray drawn in frame {view.RayShownFrame}, hum {(audio != null ? audio.BeamHumOn.ToString() : "no audio")}; the tool {first:0.0} deg off the aim one frame in, {later:0.0} deg 0.3 s later");
                Assert.Greater(first, 1f, "damped: not on the aim in one frame");
                Assert.Less(later, 2f, "on the aim within 0.3 s");
                input.holdUse = false;
                for (int i = 0; i < 10; i++) yield return null;
                Assert.IsFalse(view.Beam.enabled, "the ray off with the button (after a tap's 0.1 s at most)");
                Assert.IsFalse(view.Glow.enabled);
                if (audio != null) Assert.IsFalse(audio.BeamHumOn, "the hum off");
                LogAssert.NoUnexpectedReceived();
            }
            finally { Restore(); }
        }

        /// <summary>The swing's own machinery allocates nothing: three swings of chips against the same number of idle frames, the least
        /// of three rounds each (another system's one-off allocation in a span is not the swing's). The frame a cell OPENS allocates in
        /// the terrain edit as before U-209 (the brush's cell list, new density blocks, the chunk's mesh): not measured here.</summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator SwingingAllocatesNothingOverAnIdleFrame()
        {
            yield return Boot(DigTool.Shovel);
            try
            {
                float x = player.Body.position.x;
                yield return StandAtDepth(x + 64f, 215f); // Core: 20 contacts before a cell opens
                var feet = player.Body.position;
                var target = new Vector2(feet.x + 1.4f, feet.y + 0.6f);
                input.AimAt(target);
                yield return Rest();
                Assert.GreaterOrEqual(DigStroke.ContactsToOpen(rig.StrokeSeconds(target)), 12, "enough contacts for the rounds without an opening");
                input.holdUse = true;
                for (int i = 0; i < 30; i++) yield return null; // warm: the first swing's sprites, sounds and crack mark
                input.holdUse = false;
                yield return Rest();
                const int Frames = 75; // three swings
                long idle = long.MaxValue, swinging = long.MaxValue;
                int opens = input.Stroke.Opens, contacts = input.Stroke.Contacts;
                for (int round = 0; round < 3; round++)
                {
                    long before = System.GC.GetAllocatedBytesForCurrentThread();
                    for (int i = 0; i < Frames; i++) yield return null;
                    idle = System.Math.Min(idle, System.GC.GetAllocatedBytesForCurrentThread() - before);
                    input.holdUse = true;
                    yield return null;
                    before = System.GC.GetAllocatedBytesForCurrentThread();
                    for (int i = 0; i < Frames; i++) yield return null;
                    swinging = System.Math.Min(swinging, System.GC.GetAllocatedBytesForCurrentThread() - before);
                    input.holdUse = false;
                    yield return Rest();
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u209 allocation over {Frames} frames, the least of 3 rounds: idle {idle} B, swinging {swinging} B ({input.Stroke.Contacts - contacts} contacts, {input.Stroke.Opens - opens} opens)");
                Assert.AreEqual(0, input.Stroke.Opens - opens, "no cell opened in the measured spans");
                Assert.GreaterOrEqual(input.Stroke.Contacts - contacts, 9, "the swings made their contacts");
                Assert.LessOrEqual(swinging - idle, 0L, "0 B per swing: swinging allocates nothing an idle frame does not");
                LogAssert.NoUnexpectedReceived();
            }
            finally { Restore(); }
        }
    }
}
