using Meridian.CameraRig;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-087 (EditMode): the stage camera rules of Bible §5.1 v3, on the pure solver at 120 steps per second.</summary>
    public class StageCameraTests
    {
        const float Dt = 1f / 120f;

        static StageInput Standing(float x, float floor) => new StageInput
        {
            playerX = x, playerY = floor, facing = 1, speedX = 0f, speedY = 0f, grounded = true, floorY = floor, dt = Dt,
        };

        static StageCamera Settled(float x, float floor)
        {
            var cam = new StageCamera();
            cam.Snap(Standing(x, floor));
            return cam;
        }

        /// <summary>A ballistic jump on a flat floor: feet height from v₀ and g, until the feet are back on the floor.</summary>
        static float JumpCameraTravel(float v0, float g)
        {
            var cam = Settled(100f, 320f);
            float y0 = cam.Y;
            float t = 0f, feet = 320f, vy = v0, peak = 0f, travel = 0f;
            bool airborne = true;
            while (airborne)
            {
                t += Dt;
                vy -= g * Dt;
                feet += vy * Dt;
                if (feet <= 320f) { feet = 320f; airborne = false; }
                peak = Mathf.Max(peak, feet - 320f);
                var i = Standing(100f, 320f);
                i.playerY = feet; i.speedY = vy; i.grounded = !airborne;
                cam.Step(i);
                travel = Mathf.Max(travel, Mathf.Abs(cam.Y - y0));
            }
            TestContext.Out.WriteLine($"[MERIDIAN] jump v0 {v0} g {g}: peak {peak:F2} m, camera moved {travel:F3} m");
            return travel;
        }

        [Test]
        public void A_EarthJumpNeverMovesTheCamera()
        {
            Assert.AreEqual(0f, JumpCameraTravel(7f, 9.81f), 0.001f, "a 2.5 m jump moves the camera 0.00 m");
        }

        [Test]
        public void B_MarsJumpNeverMovesTheCamera()
        {
            Assert.AreEqual(0f, JumpCameraTravel(7f, 3.71f), 0.001f, "a 6.6 m jump moves the camera 0.00 m");
        }

        [Test]
        public void C_ALongFallIsFollowedWithinFourTenthsOfASecond()
        {
            var cam = Settled(100f, 320f);
            float feet = 320f, vy = 0f, g = 9.81f;
            const float bottom = 305f; // a 15 m pit opens under the player
            bool landed = false;
            float tSinceLanding = -1f;
            float travel = 0f;
            while (tSinceLanding < 0.4f)
            {
                if (!landed)
                {
                    vy -= g * Dt;
                    feet += vy * Dt;
                    if (feet <= bottom) { feet = bottom; vy = 0f; landed = true; tSinceLanding = 0f; }
                }
                else tSinceLanding += Dt;
                var i = Standing(100f, bottom);
                i.playerY = feet; i.speedY = vy; i.grounded = landed;
                cam.Step(i);
                travel = Mathf.Max(travel, Mathf.Abs(cam.Y - (feet + StageCamera.BodyCentre)));
                if (!landed && 320f - feet > StageCamera.LongFall + 0.5f) Assert.IsTrue(cam.FallFollowing, "the 0.4 s follow is on past 10 m of fall");
            }
            float half = StageCamera.MiddleBand * 0.5f * cam.Frame;
            float off = Mathf.Abs(cam.Y - (bottom + StageCamera.BodyCentre));
            TestContext.Out.WriteLine($"[MERIDIAN] 15 m fall: 0.4 s after landing the body centre is {off:F2} m from the frame centre (band ± {half:F1} m)");
            Assert.Less(off, half, "the player is back inside the middle 60 % within 0.4 s of landing");
        }

        [Test]
        public void D_RunningRightHoldsThePlayerLeftOfCentre()
        {
            var cam = Settled(100f, 320f);
            float x = 100f;
            const float speed = 6.5f;
            float maxCamSpeed = 0f, prevX = cam.X;
            for (int n = 0; n < 120; n++)
            {
                x += speed * Dt;
                var i = Standing(x, 320f);
                i.speedX = speed;
                cam.Step(i);
                maxCamSpeed = Mathf.Max(maxCamSpeed, Mathf.Abs(cam.X - prevX) / Dt);
                prevX = cam.X;
            }
            float left = cam.X - x;
            TestContext.Out.WriteLine($"[MERIDIAN] running right at 6.5 m/s for 1 s: player {left:F2} m left of centre, camera peak speed {maxCamSpeed:F2} m/s");
            Assert.GreaterOrEqual(left, 1.5f, "at least 1.5 m left of centre");
            Assert.LessOrEqual(left, 3.5f, "at most 3.5 m left of centre");
            Assert.LessOrEqual(maxCamSpeed, speed + StageCamera.SpeedMargin + 0.01f, "camera never faster than the player + 2 m/s");
        }

        [Test]
        public void D2_AStandingPlayerInsideTheDeadZoneNeverDragsTheCamera()
        {
            var cam = Settled(100f, 320f);
            float x0 = cam.X;
            for (int n = 0; n < 240; n++)
            {
                var i = Standing(100f + 1.2f * Mathf.Sin(n * 0.05f), 320f); // drifting within ± 1.2 m at walking pace? no: standing steps
                i.speedX = 0f;
                cam.Step(i);
            }
            Assert.AreEqual(x0, cam.X, 1e-4f, "small shifts inside the dead zone hold the camera");
        }

        [Test]
        public void E_TheFrameIsThePlayersZoomWithNoFightZoom()
        {
            // D-087 (U-093): no fight zoom; the frame is always the player's own zoom (the default 18 m here).
            var cam = Settled(100f, 320f);
            for (int n = 0; n < 300; n++) cam.Step(Standing(100f, 320f));
            Assert.AreEqual(StageCamera.DefaultFrame, cam.Frame, 1e-4f, "18 m");
            var i = Standing(100f, 320f);
            i.baseFrame = 24f;
            cam.Step(i);
            Assert.AreEqual(24f, cam.Frame, 1e-4f, "the wheel zoom applies at once");
        }

        [Test]
        public void F_BumpShakeIsPositionOnlyAndFadesInOneTenthOfASecond()
        {
            var cam = Settled(100f, 320f);
            cam.Impact(StageCamera.BumpShake);
            float peak = 0f;
            int n = 0;
            for (; n < 12; n++) { cam.Step(Standing(100f, 320f)); peak = Mathf.Max(peak, cam.Shake.magnitude); }
            TestContext.Out.WriteLine($"[MERIDIAN] bump shake peak {peak:F3} m");
            Assert.Greater(peak, 0.02f, "the shake is visible");
            Assert.LessOrEqual(peak, StageCamera.BumpShake + 1e-4f, "never more than 0.15 m");
            for (; n < 14; n++) cam.Step(Standing(100f, 320f));
            Assert.AreEqual(0f, cam.Shake.magnitude, 1e-5f, "gone after 0.10 s");
            // The solver has no rotation output at all: Shake is an offset, X/Y/Frame are positions and a size.
            Assert.AreEqual(100f, cam.X, 1e-4f);
        }

        [Test]
        public void RisingGroundLiftsTheFrameAtMostSixMetresPerSecond()
        {
            var cam = Settled(100f, 320f);
            float y0 = cam.Y, prev = cam.Y, maxSpeed = 0f;
            for (int n = 0; n < 240; n++)
            {
                var i = Standing(100f, 330f); // the floor under the player is 10 m higher (a walk up a ridge)
                cam.Step(i);
                maxSpeed = Mathf.Max(maxSpeed, (cam.Y - prev) / Dt);
                prev = cam.Y;
            }
            Assert.Greater(cam.Y, y0 + 9f, "the frame followed the floor up");
            Assert.LessOrEqual(maxSpeed, StageCamera.VerticalMaxSpeed + 0.01f, "vertical motion ≤ 6 m/s");
        }

        // ---- U-148 (D-158): the ship frame, the capped look-ahead, the pad hold, the strip tiles ----

        static StageInput Aboard(float centreY, float floor, float vx, float vy, float altitude) => new StageInput
        {
            playerX = 100f, playerY = centreY, facing = 1, speedX = vx, speedY = vy, grounded = altitude <= 0f, floorY = floor,
            baseFrame = StageCamera.ShipFrame, dt = Dt, vehicle = true, altitude = altitude,
        };

        [Test]
        public void U148_TheShipFrameIs30mAndWidensWithSpeedTo45m()
        {
            Assert.AreEqual(30f, StageCamera.ShipFrameFor(StageCamera.ShipFrame, 0f), 1e-4f, "30 m standing");
            Assert.AreEqual(37.5f, StageCamera.ShipFrameFor(StageCamera.ShipFrame, 30f), 1e-4f, "half way at 30 m/s");
            Assert.AreEqual(45f, StageCamera.ShipFrameFor(StageCamera.ShipFrame, 60f), 1e-4f, "45 m at 60 m/s");
            Assert.AreEqual(45f, StageCamera.ShipFrameFor(StageCamera.ShipFrame, 200f), 1e-4f, "and no wider from speed");
            Assert.AreEqual(60f, StageCamera.ShipFrameFor(58f, 60f), 1e-4f, "the wheel's range caps it at 60 m");
            Assert.AreEqual(24f, StageCamera.ShipFrameFor(10f, 0f), 1e-4f, "and floors it at 24 m");
        }

        [Test]
        public void U148_TheLookAheadIsCappedAtAFifthOfTheFrame()
        {
            var slow = StageCamera.VehicleLook(0f, 5f, 30f);
            Assert.AreEqual(3f, slow.y, 1e-4f, "0.6 s of 5 m/s");
            var fast = StageCamera.VehicleLook(0f, 42f, 40f);
            Assert.AreEqual(8f, fast.magnitude, 1e-3f, "0.6 s of 42 m/s (25 m) capped at 0.2 × 40 m");
            var diag = StageCamera.VehicleLook(30f, 30f, 30f);
            Assert.AreEqual(6f, diag.magnitude, 1e-3f, "the cap is on the vector");
            Assert.AreEqual(diag.x, diag.y, 1e-4f, "along the velocity");
            Assert.Less(StageCamera.VehicleLookFrame, StageCamera.MiddleBand * 0.5f, "the capped goal sits inside the middle band");
        }

        [Test]
        public void U148_ThePadHoldFadesOutOverTwelveMetres()
        {
            Assert.AreEqual(1f, StageCamera.PadHold(0f), 1e-4f, "on the pad");
            Assert.AreEqual(0.5f, StageCamera.PadHold(StageCamera.PadHoldAltitude * 0.5f), 1e-4f, "half way");
            Assert.AreEqual(0f, StageCamera.PadHold(StageCamera.PadHoldAltitude), 1e-4f, "gone at 12 m");
            Assert.AreEqual(0f, StageCamera.PadHold(float.PositiveInfinity), 1e-4f, "no ground under the hull");
        }

        [Test]
        public void U148_OnThePadTheHullSitsLowWithSkyAhead()
        {
            // The hull's centre 3.9 m over the pad (11.4 / 2 − 1.8): the frame bottom 3 m under the pad, the hull in the lower part.
            var cam = new StageCamera();
            cam.Snap(Aboard(323.9f, 320f, 0f, 0f, 0f));
            Assert.AreEqual(30f, cam.Frame, 1e-4f);
            Assert.AreEqual(320f - StageCamera.FloorBelow + 15f, cam.Y, 1e-3f, "the stage-floor rule on the pad");
            Assert.Greater(cam.Y, 323.9f, "sky ahead of the hull");
        }

        [Test]
        public void U148_BoardingEasesTheFrameWithoutAPopAndAFastClimbNeverHitsTheBand()
        {
            var cam = Settled(100f, 320f);
            Assert.AreEqual(StageCamera.DefaultFrame, cam.Frame, 1e-4f);
            float prev = cam.Frame, maxStep = 0f;
            int steps = 0;
            for (; steps < 240; steps++) // 2 s aboard on the pad
            {
                cam.Step(Aboard(323.9f, 320f, 0f, 0f, 0f));
                maxStep = Mathf.Max(maxStep, Mathf.Abs(cam.Frame - prev));
                prev = cam.Frame;
            }
            Assert.AreEqual(30f, cam.Frame, 0.05f, "the 30 m ship frame after boarding");
            Assert.Less(maxStep, 0.5f, "no pop: under 0.5 m of frame per 1/120 s step");
            Assert.IsFalse(cam.FrameEasing, "the boarding ease is over");

            // A climb at 42 m/s: the camera's offset from the hull eases toward the capped look-ahead and stays clear of the band edge.
            float y = 323.9f, half = StageCamera.MiddleBand * 0.5f;
            float worst = 0f;
            for (int n = 0; n < 1200; n++) // 10 s
            {
                float v = Mathf.Min(42f, n * Dt * 8f);
                y += v * Dt;
                cam.Step(Aboard(y, 320f, 0f, v, y - 323.9f));
                if (n > 240) worst = Mathf.Max(worst, Mathf.Abs(cam.Y - y) / cam.Frame);
            }
            Assert.Less(worst, half - 0.02f, $"the hull clear of the middle band's edge at speed ({worst:F3} of the frame)");
            Assert.Greater(cam.Frame, 38f, "the frame widened with the climb");

            // Stepping out eases back to the walking frame.
            for (int n = 0; n < 240; n++) cam.Step(Standing(100f, y - 3.9f));
            Assert.AreEqual(StageCamera.DefaultFrame, cam.Frame, 0.05f, "back to the walking frame");
        }

        [Test]
        public void U148_StripsDrawEnoughOddTilesForTheWidestFrame()
        {
            float walk = 16.875f * 16f / 9f + 2f, ship = 60f * 16f / 9f + 2f;
            Assert.AreEqual(3, Meridian.View2D.ParallaxLayers.TilesFor(walk, 32f), "3 tiles on foot (unchanged)");
            int n = Meridian.View2D.ParallaxLayers.TilesFor(ship, 32f);
            Assert.AreEqual(1, n & 1, "odd: the pattern keeps its phase");
            Assert.GreaterOrEqual((n - 1) * 32f, ship, "a strip kept within half a tile of the camera covers the 60 m frame");
            Assert.AreEqual(3, Meridian.View2D.ParallaxLayers.TilesFor(ship, 0f), "no width: the old 3");
        }

        // ---------- U-213 (3) (D-202 (3)): the close camera ----------

        /// <summary>96 px a metre on foot at the surface is 2/3 of the shipped frame (16.875 m becomes 11.25 m), 128 is half of it; the
        /// shipped 64 underground; the switch a built player takes.</summary>
        [Test]
        public void U213_TheCloseCamerasSharesAndItsSwitch()
        {
            const float shipped = 1080f / 64f;
            Assert.AreEqual(2f / 3f, StageZoom.Share(96f), 1e-6f);
            Assert.AreEqual(11.25f, shipped * StageZoom.Share(96f), 1e-4f, "1080 px at 96 px a metre");
            Assert.AreEqual(8.4375f, shipped * StageZoom.Share(128f), 1e-4f, "1080 px at 128 px a metre");
            Assert.AreEqual(1f, StageZoom.Share(64f), 1e-6f, "the shipped frame");
            Assert.AreEqual(1f, StageZoom.Share(10f), 1e-6f, "never wider than the shipped frame");
            bool was = StageZoom.Enabled; float ppm = StageZoom.SurfacePxPerMetre;
            try
            {
                StageZoom.Enabled = false;
                Assert.AreEqual(1f, StageZoom.SurfaceShare, "the flag off: the shipped frame everywhere");
                Assert.AreEqual(1f, StageZoom.GoalShare(false));
                StageZoom.Enabled = true; StageZoom.SurfacePxPerMetre = 96f;
                Assert.AreEqual(2f / 3f, StageZoom.GoalShare(false), 1e-6f, "at the surface");
                Assert.AreEqual(1f, StageZoom.GoalShare(true), "underground");
            }
            finally { StageZoom.Enabled = was; StageZoom.SurfacePxPerMetre = ppm; }
            Assert.IsFalse(StageZoom.ReadSwitch(new[] { "MERIDIAN.exe", "-screen-width", "1920" }, out float asked), "no switch: off");
            Assert.AreEqual(96f, asked);
            Assert.IsTrue(StageZoom.ReadSwitch(new[] { "MERIDIAN.exe", StageZoom.Switch }, out asked));
            Assert.AreEqual(96f, asked, "the switch alone: 96");
            Assert.IsTrue(StageZoom.ReadSwitch(new[] { "MERIDIAN.exe", StageZoom.Switch, "128", "-x" }, out asked));
            Assert.AreEqual(128f, asked);
            Assert.IsTrue(StageZoom.ReadSwitch(new[] { StageZoom.Switch, "-meridianSaveRoot" }, out asked));
            Assert.AreEqual(96f, asked, "another switch after it is not its number");
            Assert.IsTrue(StageZoom.ReadSwitch(new[] { StageZoom.Switch, "4000" }, out asked));
            Assert.AreEqual(96f, asked, "a number out of range is not taken");
        }

        /// <summary>Underground is 3 m or more under the ground's surface, or under a roof of ground at any depth; half a metre of
        /// hysteresis on the way back up.</summary>
        [Test]
        public void U213_UndergroundIsThreeMetresDownOrUnderARoof()
        {
            Assert.IsFalse(StageZoom.Underground(false, 0f, false), "on the surface");
            Assert.IsFalse(StageZoom.Underground(false, 2.9f, false), "in a pit 2.9 m deep under the open sky");
            Assert.IsTrue(StageZoom.Underground(false, 3f, false), "3 m down");
            Assert.IsTrue(StageZoom.Underground(true, 2.6f, false), "climbing back: still underground at 2.6 m");
            Assert.IsFalse(StageZoom.Underground(true, 2.4f, false), "out above 2.5 m");
            Assert.IsTrue(StageZoom.Underground(false, 0.5f, true), "under a roof of ground at any depth: a dug room, a tunnel");
        }

        /// <summary>The frame eases to the close camera's share in about a second and back, never a cut; the ground keeps its share of the
        /// frame; with no zoom asked (the flag off) nothing moves.</summary>
        [Test]
        public void U213_TheCloseCameraEasesInAboutASecondAndNeverCuts()
        {
            const float shipped = 1080f / 64f, close = shipped * 2f / 3f, floor = 320f, dt = 1f / 60f;
            StageInput At(float zoom) { var i = Standing(100f, floor); i.baseFrame = shipped; i.dt = dt; i.zoom = zoom; return i; }
            var cam = new StageCamera();
            cam.Snap(At(1f));
            Assert.AreEqual(shipped, cam.Frame, 1e-4f);
            float groundShare = (floor - (cam.Y - cam.Frame * 0.5f)) / cam.Frame;
            Assert.AreEqual(StageCamera.FloorBelow / shipped, groundShare, 1e-4f, "3 m of ground under the floor: 17.8 % of the shipped frame");
            // no zoom asked: the frame and the height stand still
            float y0 = cam.Y;
            for (int k = 0; k < 120; k++) cam.Step(At(0f));
            Assert.AreEqual(shipped, cam.Frame, 1e-5f); Assert.AreEqual(y0, cam.Y, 1e-5f, "the flag off: no change to play");
            // to the surface share
            float last = cam.Frame, lastY = cam.Y, worstStep = 0f, worstY = 0f;
            int within = -1;
            for (int k = 1; k <= 180; k++)
            {
                cam.Step(At(2f / 3f));
                Assert.LessOrEqual(cam.Frame, last + 1e-5f, $"step {k}: the frame only closes in");
                worstStep = Mathf.Max(worstStep, last - cam.Frame); worstY = Mathf.Max(worstY, Mathf.Abs(cam.Y - lastY));
                last = cam.Frame; lastY = cam.Y;
                if (within < 0 && cam.Frame - close <= 0.02f * (shipped - close)) within = k;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u213 ease in: within 2 % of the way after {within} frames ({within * dt:0.00} s); the largest step {worstStep:0.000} m of frame a frame, {worstY:0.000} m of height");
            Assert.AreEqual(close, cam.Frame, 1e-3f, "11.25 m: 96 px a metre");
            Assert.That(within * dt, Is.InRange(0.8f, 1.2f), "about a second");
            Assert.Less(worstStep, 0.25f, "never a cut: under a quarter metre of frame a frame (1.5 % of it)");
            Assert.Less(worstY, 0.12f, "and the height follows as smoothly");
            Assert.AreEqual(groundShare, (floor - (cam.Y - cam.Frame * 0.5f)) / cam.Frame, 2e-3f, "the ground keeps its share of the frame: the same composition, closer");
            // and back out underground
            last = cam.Frame; worstStep = 0f; within = -1;
            for (int k = 1; k <= 180; k++)
            {
                cam.Step(At(1f));
                Assert.GreaterOrEqual(cam.Frame, last - 1e-5f, $"step {k}: the frame only opens");
                worstStep = Mathf.Max(worstStep, cam.Frame - last);
                last = cam.Frame;
                if (within < 0 && shipped - cam.Frame <= 0.02f * (shipped - close)) within = k;
            }
            Assert.AreEqual(shipped, cam.Frame, 1e-3f, "back to the shipped 64 px a metre");
            Assert.That(within * dt, Is.InRange(0.8f, 1.2f));
            Assert.Less(worstStep, 0.25f);
            // a snap lands on the share asked
            cam.Snap(At(2f / 3f));
            Assert.AreEqual(close, cam.Frame, 1e-4f);
            Assert.AreEqual(2f / 3f, cam.Zoom, 1e-6f);
        }
    }
}
