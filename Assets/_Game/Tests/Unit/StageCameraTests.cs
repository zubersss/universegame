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
    }
}
