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
                // D-196b: the swing's target is the CONTACT: the first solid point on the line from the shoulder toward the cursor
                var shoulder = rig.DigOrigin;
                var along = (target - shoulder).normalized;
                Assert.Less(Mathf.Abs(Vector3.Cross(along, stroke.Target - shoulder).z), 0.02f, "the contact lies on the line from the shoulder to the cursor");
                Assert.IsTrue(rig.SolidAt(stroke.Target + along * 0.05f), "solid just behind it");
                Assert.IsFalse(rig.SolidAt(stroke.Target - along * 0.05f), "open just before it: the ground's face");
                Assert.LessOrEqual(Vector2.Distance(stroke.Target, shoulder), SkillStats.DigReach + 1e-3f, "inside the reach from the shoulder");
                yield return null;               // frame press + 1: what frame `press` drew is on the view
                Assert.AreEqual(press, view.SwingShownFrame, "press -> the first visible change: the same frame (0 frames; the bar is 1)");
                Assert.IsFalse(view.Carrying, "out of the carry pose");
                Assert.Greater(Mathf.Abs(Mathf.DeltaAngle(carried, view.AimDegrees)), 20f, "the tool is raised for the wind-up");
                if (view.SwingOnClip) StringAssert.StartsWith("dig_", view.Body.Clip, "the body plays the swing's clip (B-246's side_dig)");
                else Assert.AreNotEqual(0f, view.Body.StrokeLean, "no dig clip on the sheet: the body leans back for it");
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
                Assert.IsTrue(view.Crack.enabled);
                if (view.CrackOnArt)
                {
                    // LEAD 07:1x: B-246's crack starts where the blade landed and spreads into the ground: its origin on the contact,
                    // shown only behind the face (the wall right of the hollow: the ground is to the right)
                    Assert.IsTrue(view.CrackClipped, "the crack is clipped to the ground's side of the face");
                    Assert.Less(Vector2.Distance(view.Crack.transform.position, stroke.Target), 1e-3f, "its origin is the contact");
                    Assert.AreEqual(SpriteMaskInteraction.VisibleInsideMask, view.Crack.maskInteraction);
                    Assert.IsTrue(view.CrackMask.enabled, "the mask is on");
                    Assert.Greater(view.CrackInto.x, 0.7f, "into the ground: to the right through the wall's face");
                    Assert.IsTrue(rig.SolidAt(stroke.Target + view.CrackInto * 0.3f), "solid on the side the crack is shown");
                    Assert.IsFalse(rig.SolidAt(stroke.Target - view.CrackInto * 0.3f), "open on the side it is hidden");
                    Vector2 maskUp = view.CrackMask.transform.up;
                    Assert.Greater(Vector2.Dot(maskUp, view.CrackInto), 0.999f, "the mask lies over the ground's side");
                }
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
                    Assert.Less(Mathf.Abs(Mathf.DeltaAngle(rest, view.AimDegrees)), 3f, $"the cursor at {d}: the tool's angle does not change with the button up (but for its share of the idle arm's sway)");
                    Assert.IsTrue(view.Carrying);
                    Assert.IsTrue(view.Stowed, "stowed until the first swing");
                    Assert.Less(Mathf.Abs(Mathf.DeltaAngle(view.StowAngle(false), view.AimDegrees)), 1e-2f, "the stowed pose (facing right): its angle and its share of the arm's own, nothing of the cursor's");
                    Assert.That(view.AimDegrees, Is.InRange(110f, 140f), "the blade up behind the helmet (125 degrees)");
                    Assert.AreEqual(Meridian.View2D.SpriteCharacterView.SurveyorOrder - 1, view.Tool.sortingOrder, "drawn behind the body");
                    Assert.IsFalse(view.Fist.enabled, "no fist on a stowed tool");
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
                Assert.Less(Mathf.Abs(Mathf.DeltaAngle(view.CarryAngle(false), view.AimDegrees)), 1e-2f, "the ready pose: low, in front");
                Assert.AreEqual(RigToolView.ReadyRadians * Mathf.Rad2Deg + RigToolView.ReadySwing * view.ArmDegrees, view.AimDegrees, 0.05f, "side_dig.json's ready angle and a quarter of the drawn arm's own (the held body here hangs in its fall pose, arm raised)");
                Assert.AreEqual(Meridian.View2D.SpriteCharacterView.SurveyorOrder + 1, view.Tool.sortingOrder, "the ready tool is drawn in front of the body");
                Assert.AreEqual(view.Fist.sprite != null, view.Fist.enabled, "B-246's fist over the ready tool (where its sprite is in)");
                Assert.Greater(view.Fist.sortingOrder, view.Tool.sortingOrder, "the fist over the tool");
                input.AimAt(feet + new Vector2(-2f, 2f));
                for (int i = 0; i < 30; i++) yield return null;
                Assert.IsFalse(view.Stowed, "still ready 0.5 s on");
                Assert.Less(Mathf.Abs(Mathf.DeltaAngle(view.CarryAngle(false), view.AimDegrees)), 1e-2f, "whatever the cursor does");
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

                // a click 6 m off, steeply down and ahead: past reach, its line meeting the ground inside it whatever the slope here
                var far = feet + new Vector2(2f, -6f);
                input.AimAt(far);
                yield return Rest();
                yield return null;
                var shoulder = rig.DigOrigin;
                Assert.IsTrue(view.ReticleClamped, "the cursor is past the reach");
                Assert.IsTrue(view.ReticleDiggable, "the line meets ground inside it");
                Assert.LessOrEqual(Vector2.Distance(view.ReticleAt, shoulder), reach + 1e-3f, "the contact inside the reach, from the shoulder (D-196b)");
                Assert.AreEqual(view.ReticleOnArt ? RigToolView.ReticleClampedTint : RigToolView.ReticleAtReach, view.ReticleTint, "tinted as clamped (mustard on B-246's brackets)");
                if (view.ReticleOnArt)
                {
                    for (int i = 0; i < 4; i++)
                    {
                        Assert.IsTrue(view.Bracket(i).enabled, $"bracket {i} of four round the brush's circle");
                        Assert.AreEqual(RigTools.BrushRadius + RigToolView.ClampedGapM, Vector2.Distance(view.Bracket(i).transform.position, view.ReticleCentre), 0.01f, "pushed out 0.09 m: clamped");
                    }
                    Assert.IsTrue(view.Pip.enabled, "the pip on the contact");
                    Assert.Less(Vector2.Distance(view.Pip.transform.position, view.ReticleAt), 1e-3f);
                    Assert.IsFalse(view.Reticle.enabled, "the stand-in ring is off");
                }
                Assert.AreEqual(RigTools.BrushPush, Vector2.Distance(view.ReticleCentre, view.ReticleAt), 0.02f, "the ring is the brush's circle: its middle pushed into the ground from the contact");
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
                Assert.LessOrEqual(Vector2.Distance(stroke.LastContactAt, shoulder), reach + 1e-3f, "the contact inside the reach");
                Assert.AreEqual(RigTools.BrushPush, Vector2.Distance(dugAt, stroke.LastContactAt), 0.02f, "the dig opened from the contact, its centre pushed into the ground");
                float off = Mathf.Abs(Vector3.Cross((far - shoulder).normalized, dugAt - shoulder).z);
                Assert.Less(off, 0.02f, "on the aim line from the shoulder");
                TestContext.Out.WriteLine($"[MERIDIAN] u209 past reach: the click {Vector2.Distance(far, shoulder):0.0} m from the shoulder, the contact {Vector2.Distance(stroke.LastContactAt, shoulder):0.00} m, the dig's point {Vector2.Distance(dugAt, shoulder):0.00} m, {off:0.000} m off the aim line; {rig.LastDugCells} tiles opened");
                yield return Rest();

                // nothing to dig: straight up into the open air
                var air = feet + new Vector2(0.4f, 6f);
                input.AimAt(air);
                yield return null; yield return null;
                Assert.IsFalse(view.ReticleDiggable, "nothing there");
                Assert.AreEqual(view.ReticleOnArt ? RigToolView.ReticleNothingTint : RigToolView.ReticleNothing, view.ReticleTint, "the reticle's empty state (red on B-246's brackets)");
                if (view.ReticleOnArt)
                {
                    Assert.IsFalse(view.Pip.enabled, "no pip where there is nothing to dig");
                    Assert.AreEqual(RigTools.BrushRadius + RigToolView.NothingGapM, Vector2.Distance(view.Bracket(0).transform.position, view.ReticleCentre), 0.01f, "pushed out 0.2 m");
                }
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

                // LEAD's rule: the reticle fades to 40 % once the cursor has been still 1.5 s with the button up; whole again when it moves
                for (int i = 0; i < 130; i++) yield return null; // over 2 s at the 60 fps step
                Assert.AreEqual(RigToolView.ReticleIdleStrength, view.ReticleStrength, 0.02f, "faded with a still cursor");
                input.AimAt(air + new Vector2(0.3f, 0f));
                for (int i = 0; i < 20; i++) yield return null;
                Assert.AreEqual(1f, view.ReticleStrength, 0.02f, "whole again when the cursor moves");
                TestContext.Out.WriteLine($"[MERIDIAN] u209 reticle: on B-246's art {view.ReticleOnArt}; strength {RigToolView.ReticleIdleStrength:0.0} with a still cursor, 1.0 within 0.3 s of a move");
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
                // Two hollows in Topsoil, 3 m wide and 2 m tall: in the middle of one (the wall's face 1.5 m ahead), and 0.6 m nearer
                // the wall of the other (its face 0.9 m ahead: dig_fwd_near's reach). The aim's line from the shoulder meets the floor,
                // the wall or the ceiling: that contact is what the blade must meet (D-196b).
                float x = player.Body.position.x;
                var stroke = input.Stroke;
                float blade = RigTools.ShovelBlade;
                Assert.AreEqual(1.33f, blade, 0.02f, "shovel.json's blade_tip");
                int held = 0, total = 0;
                var log = new System.Text.StringBuilder();
                Vector2 shoulder = default;
                foreach (var (stand, ahead) in new[] { ("mid-hollow", 0f), ("near the wall", 0.6f) })
                {
                    yield return StandAtDepth(x + 36f + (ahead > 0f ? 14f : 0f), 5f);
                    // StandAtDepth's hollow is 3 m tall: fill its top row again so the ceiling stands 2 m over the floor
                    var at0 = player.Body.position;
                    int fx = Mathf.FloorToInt(at0.x), fy = Mathf.FloorToInt(at0.y);
                    for (int c = fx - 1; c <= fx + 1; c++) t.SetTile(c, fy + 2, TileId.Soil);
                    var b = player.Body;
                    b.position = new Vector2(fx + 0.5f + ahead, fy + 0.05f); player.transform.position = b.position;
                    for (int i = 0; i < 10; i++) yield return null;
                    var feet = b.position;
                    shoulder = rig.DigOrigin;
                    foreach (float deg in ahead > 0f ? new[] { -30f, 0f, 25f } : new[] { -88f, -70f, -50f, -20f, 0f, 20f, 45f, 70f, 88f })
                    {
                        var dir = new Vector2(Mathf.Cos(deg * Mathf.Deg2Rad), Mathf.Sin(deg * Mathf.Deg2Rad));
                        input.AimAt(shoulder + dir * 1.2f);
                        yield return Rest();
                        stroke.Reset(); // no kept work: a swing near the last contact would go on working that one
                        int contacts = stroke.Contacts;
                        input.holdUse = true; yield return null; input.holdUse = false;
                        yield return null; // the press' frame is drawn: the wind-up drawing
                        var windTip = view.TipWorld;
                        for (int i = 0; i < 12 && stroke.Contacts == contacts; i++) yield return null;
                        Assert.AreEqual(contacts + 1, stroke.Contacts, $"{stand} {deg} deg: the contact");
                        yield return null; // the contact frame's drawing is on the view (the contact drawing lasts five frames)
                        Assert.AreEqual(DigStroke.ContactDrawing, stroke.Drawing, "still the contact drawing");
                        Assert.IsTrue(stroke.Diggable, $"{stand} {deg} deg: the line meets the hollow's wall inside the reach");
                        var contact = stroke.Target;
                        Assert.Less(Mathf.Abs(Vector3.Cross(dir, contact - shoulder).z), 0.03f, $"{stand} {deg} deg: the contact on the aim's line");
                        Assert.IsTrue(rig.SolidAt(contact + dir * 0.05f) && !rig.SolidAt(contact - dir * 0.05f), $"{stand} {deg} deg: the contact is the ground's face");
                        // B-246's swish: on the arcs only (dig_down, dig_up), pivoted on the tool's own origin, so its end lies on the blade
                        // wherever the tool slid (pivoted on the glove it stood a slide's length past the blade: over a ceiling, in the ground)
                        bool arc = view.Body.Clip == SurveyorAnim.DigDown || view.Body.Clip == SurveyorAnim.DigUp;
                        bool swishIn = Meridian.FX.FxSheet.Get(RigToolView.SwishKey).Ready;
                        Assert.AreEqual(arc && view.SwingOnClip && swishIn, view.Swish.enabled, $"{stand} {deg} deg ({view.Body.Clip}): the swish on the arcs, not on the thrusts");
                        if (view.Swish.enabled)
                            Assert.Less(Vector2.Distance(view.Swish.transform.position, view.Tool.transform.position), 1e-3f, $"{stand} {deg} deg: the swish turns about the tool's origin: its end on the blade");
                        float gap = Vector2.Distance(view.TipWorld, contact);
                        float fromGlove = Vector2.Distance(view.HandWorld, contact) + view.LungeNow; // the glove before the lunge
                        DigPose.Span(blade, view.SlideMaxNow, RigTools.ShovelLungeM, out float nearest, out float farthest);
                        bool reachable = fromGlove >= nearest - 1e-3f && fromGlove <= farthest + 1e-3f;
                        total++;
                        // LEAD 06:5x: a thrust must travel: its wind-up drawing holds the blade back from where the contact puts it
                        float travel = Vector2.Distance(windTip, view.TipWorld);
                        if (view.Body.Clip == SurveyorAnim.DigFwd || view.Body.Clip == SurveyorAnim.DigFwdNear)
                            Assert.GreaterOrEqual(travel, 0.35f, $"{stand} {deg} deg ({view.Body.Clip}): the blade travels at least 0.35 m from the wind-up drawing to the contact");
                        log.Append($"\n  {stand}, aim {deg:+0;-0;0} deg: {view.Body.Clip}, the tip travels {travel:0.00} m from the wind-up, the contact {Vector2.Distance(contact, shoulder):0.00} m from the shoulder and {fromGlove:0.00} m from the glove (the clip reaches {nearest:0.00}-{farthest:0.00}): tip {gap:0.000} m off, slide {view.SlideNow:0.00}, lunge {view.LungeNow:0.00}, miss {view.TipMiss:+0.00;-0.00;0.00}{(reachable ? "" : view.TipMiss < 0f ? " (nearer than the clip reaches: the blade buries)" : " (farther than the clip reaches: the tip stops short)")}");
                        if (reachable)
                        {
                            held++;
                            Assert.LessOrEqual(gap, 0.08f, $"{stand} {deg} deg: the blade's tip within 0.08 m of the contact point");
                        }
                        else Assert.AreEqual(Mathf.Abs(view.TipMiss), gap, 0.02f, $"{stand} {deg} deg: out of the clip's span, the tip is off by the pose's own miss");
                        Assert.AreEqual(0f, view.ScoopArcDegrees, 0.5f, "turned along the line to the contact on the contact drawing");
                        Assert.IsTrue(view.Body.Renderer.flipX == (contact.x < feet.x), "the surveyor faces the contact");
                    }
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u209 blade tip on the contact drawing ({(view.SwingOnClip ? "the sheet's dig clips" : "the idle glove: no dig clip on the sheet")}, the lunge up to {RigTools.ShovelLungeM} m): {held} of {total} contacts inside their clip's span and within 0.08 m:{log}");
                Assert.Greater(held, 0, "the row is held where the pose reaches");
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

        /// <summary>P-U209-3 (LEAD 07:1x; D1 §5, dig_rhythm_1: "each consecutive stroke on the same face -10 % time (max -30 %)"): the Beam
        /// held on one face opens each cell in the tables' time with the node not bought, and in 1, 0.9, 0.8 of it with Rhythm I.</summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator TheRhythmNodeShortensConsecutiveCellsOnTheSameFace()
        {
            yield return Boot(DigTool.Beam);
            var nodes = GameState.Instance.skillNodes;
            bool had = nodes.Contains("dig_rhythm_1");
            try
            {
                const int Cells = 3;
                float x = player.Body.position.x;
                var stroke = input.Stroke;
                var log = new System.Text.StringBuilder();
                int spot = 0;
                foreach (bool bought in new[] { false, true })
                {
                    if (bought) nodes.Add("dig_rhythm_1"); else nodes.Remove("dig_rhythm_1");
                    SkillStats.Recompute(GameState.Instance);
                    SkillStats.ToolOverride = DigTool.Beam; // the node's own tool, whatever else the tree holds
                    rig.BeamPower = 1f;
                    Assert.AreEqual(bought ? 0.1f : 0f, SkillStats.RhythmStep, 1e-6f, "the node's step, read from the tree");
                    Assert.AreEqual(bought ? 0.3f : 0f, SkillStats.RhythmMax, 1e-6f, "and its most");
                    yield return StandAtDepth(x + 70f + 12f * spot++, 56f);
                    var feet = player.Body.position;
                    input.AimAt(feet + new Vector2(0.2f, -0.6f)); // down through the floor: three cells of one face inside the Beam's 5 m
                    yield return Rest();
                    stroke.Reset();
                    int opens = 0;
                    System.Action<Vector2> onDug = p => opens++;
                    rig.Dug += onDug;
                    input.holdUse = true;
                    yield return null; // the press' frame: the ray is on, its work runs from the next
                    log.Append(bought ? "\n  Rhythm I bought:" : "\n  not bought:");
                    for (int k = 0; k < Cells; k++)
                    {
                        int frames = 0, before = opens;
                        float need = 0f;
                        while (opens == before && frames < 60 * 20)
                        {
                            frames++;
                            yield return null;
                            if (frames == 1)
                            {
                                Assert.IsTrue(stroke.Diggable, $"cell {k + 1}: the ray rests on the face behind the last cell");
                                need = rig.StrokeSeconds(stroke.Target);
                            }
                        }
                        Assert.AreEqual(before + 1, opens, $"cell {k + 1} opens");
                        float share = bought ? 1f - Mathf.Min(0.1f * k, 0.3f) : 1f;
                        float took = frames * Step;
                        log.Append($" cell {k + 1} {took:0.00} s (the tables' {need:0.00} s x {share:0.0})");
                        Assert.AreEqual(need * share, took, 3f * Step, $"{(bought ? "Rhythm I" : "not bought")}, cell {k + 1}: the tables' {need:0.00} s x {share:0.0}");
                    }
                    input.holdUse = false;
                    rig.Dug -= onDug;
                    yield return Rest();
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u209 rhythm (dig_rhythm_1), the Beam held on one face, three cells in a row at a 60 fps step (power 1):{log}");
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                if (had) nodes.Add("dig_rhythm_1"); else nodes.Remove("dig_rhythm_1");
                SkillStats.Recompute(GameState.Instance);
                Restore();
            }
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
                // (the aim is the ray's contact on the wall's face, D-196b, not the cursor's point behind it)
                float toAim = Mathf.Atan2(stroke.Target.y - view.HandWorld.y, stroke.Target.x - view.HandWorld.x) * Mathf.Rad2Deg;
                float first = Mathf.Abs(Mathf.DeltaAngle(view.AimDegrees, toAim));
                // the tool is in the aim pose's raised hand from the press' own frame (it stayed at the hip for that frame once)
                Vector2 handAtPress = view.HandWorld, toolAtPress = view.Tool.transform.position;
                yield return null;
                Assert.Less(Vector2.Distance(handAtPress, view.HandWorld), 0.02f, "the glove the tool is held in on the press' frame is the aim pose's");
                Assert.Less(Vector2.Distance(toolAtPress, handAtPress), 1e-3f, "the tool in it");
                for (int i = 0; i < 17; i++) yield return null;
                float later = Mathf.Abs(Mathf.DeltaAngle(view.AimDegrees, Mathf.Atan2(stroke.Target.y - view.HandWorld.y, stroke.Target.x - view.HandWorld.x) * Mathf.Rad2Deg));
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
        /// the terrain edit as before U-209 (the brush's cell list, new density blocks, the chunk's mesh): its bytes are read at the end, a
        /// number for the perf report (P-U209-4), not a bar.</summary>
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
                // The measure: Unity's own counter of the managed bytes allocated in a frame (every thread), read a frame late (the
                // last whole frame's). First a CONTROL: a counter that never moves passes every row below. Until 07:4x the measure
                // here was System.GC.GetAllocatedBytesForCurrentThread: what it reads for the same known array is printed, and if
                // that is 0 the "0 B" rows it gave before proved nothing.
                using (var gc = Unity.Profiling.ProfilerRecorder.StartNew(Unity.Profiling.ProfilerCategory.Memory, "GC Allocated In Frame"))
                {
                    Assert.IsTrue(gc.Valid, "Unity's 'GC Allocated In Frame' counter is there");
                    for (int i = 0; i < 3; i++) yield return null;
                    long sys0 = System.GC.GetAllocatedBytesForCurrentThread();
                    var known = new byte[65536];
                    long sys = System.GC.GetAllocatedBytesForCurrentThread() - sys0;
                    long seenKnown = 0;
                    for (int i = 0; i < 3; i++) { yield return null; seenKnown = System.Math.Max(seenKnown, gc.LastValue); }
                    System.GC.KeepAlive(known);
                    TestContext.Out.WriteLine($"[MERIDIAN] u209 allocation counters (PlayMode), a known 65536 B array: Unity's 'GC Allocated In Frame' read {seenKnown} B in its frame; System.GC.GetAllocatedBytesForCurrentThread read {sys} B ({(sys >= 65536 ? "live" : "NOT live in this runtime")})");
                    Assert.GreaterOrEqual(seenKnown, 65536L, "the control: the counter sees a 64 KB array in the frame it is made");

                    var rounds = new System.Text.StringBuilder();
                    for (int round = 0; round < 3; round++)
                    {
                        long sum = 0;
                        for (int i = 0; i < Frames; i++) { yield return null; sum += gc.LastValue; }
                        idle = System.Math.Min(idle, sum);
                        rounds.Append($" round {round + 1}: idle {sum} B,");
                        input.holdUse = true;
                        yield return null;
                        yield return null; // the counter reads a frame late: from the press' own frame
                        sum = 0;
                        for (int i = 0; i < Frames; i++) { yield return null; sum += gc.LastValue; }
                        swinging = System.Math.Min(swinging, sum);
                        rounds.Append($" swinging {sum} B;");
                        input.holdUse = false;
                        yield return Rest();
                    }
                    TestContext.Out.WriteLine($"[MERIDIAN] u209 allocation over {Frames} frames (Unity's 'GC Allocated In Frame', every thread), the least of 3 rounds: idle {idle} B, swinging {swinging} B ({input.Stroke.Contacts - contacts} contacts, {input.Stroke.Opens - opens} opens);{rounds}");
                    Assert.AreEqual(0, input.Stroke.Opens - opens, "no cell opened in the measured spans");
                    Assert.GreaterOrEqual(input.Stroke.Contacts - contacts, 9, "the swings made their contacts");
                    Assert.LessOrEqual(swinging - idle, 0L, "0 B per swing: swinging allocates nothing an idle frame does not");

                    // P-U209-4 (LEAD 07:1x): the frame a cell OPENS, a number for the perf report (not a bar): the bytes of the frame
                    // whose Update opened it (the terrain edit) and of the ten frames after it (the chunk's mesh, the clods, the
                    // drops), three openings in topsoil with the shovel: the hollow's right wall, its left wall, its floor (one cell a
                    // line: the next face on a line is past the shovel's 2 m).
                    yield return StandAtDepth(x + 76f, 5f);
                    feet = player.Body.position;
                    int dug = 0, measured = 0;
                    System.Action<Vector2> onDug = p => dug++;
                    rig.Dug += onDug;
                    var rows = new System.Text.StringBuilder();
                    // the three faces first, then the two corners between them (ground not yet dug, in chunks already rebuilt once): the
                    // spread's cause is read from the row: the first opening of a chunk against a later one in it
                    foreach (var aim in new[] { new Vector2(1.4f, 0.6f), new Vector2(-1.4f, 0.6f), new Vector2(0.2f, -0.6f), new Vector2(1.2f, -0.5f), new Vector2(-1.2f, -0.5f) })
                    {
                        input.AimAt(feet + aim);
                        yield return Rest();
                        input.Stroke.Reset();
                        input.holdUse = true;
                        for (int f = 0; f < 60 * 4; f++)
                        {
                            int seen = dug;
                            yield return null;
                            if (dug == seen) continue;
                            input.holdUse = false; // the swing plays out; no second cell
                            yield return null;     // the opening frame is whole: its bytes
                            long open = gc.LastValue, after = 0;
                            for (int i = 0; i < 10; i++) { yield return null; after += gc.LastValue; }
                            var cell = RigTools.TileOf(input.Stroke.LastContactAt);
                            rows.Append($" opening {++measured} (aim {aim.x:+0.0;-0.0}, {aim.y:+0.0;-0.0}; {rig.LastDugCells} cells; chunk {Mathf.FloorToInt(cell.x / (float)TerrainConstants.ChunkSize)}, {Mathf.FloorToInt(cell.y / (float)TerrainConstants.ChunkSize)}): {open} B in its frame, {after} B in the ten after;");
                            break;
                        }
                        input.holdUse = false;
                    }
                    rig.Dug -= onDug;
                    Assert.GreaterOrEqual(measured, 3, "the three faces opened");
                    TestContext.Out.WriteLine($"[MERIDIAN] u209 the frame a cell opens (shovel, topsoil; Unity's 'GC Allocated In Frame'; an idle frame: {idle / Frames} B):{rows}");
                    yield return Rest();
                }
                LogAssert.NoUnexpectedReceived();
            }
            finally { Restore(); }
        }
    }
}
