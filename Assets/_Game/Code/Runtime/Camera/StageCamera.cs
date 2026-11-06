using UnityEngine;

namespace Meridian.CameraRig
{
    /// <summary>What the stage camera reads each frame (all in play-plane metres; the player position is the feet).</summary>
    public struct StageInput
    {
        public float playerX, playerY;
        public int facing;              // +1 right, -1 left
        public float speedX, speedY;    // player velocity
        public bool grounded;
        public float floorY;            // the stage floor: ground height under the player's feet
        public int hostilesNear;        // hunting creatures within 14 m
        public bool apexNear;           // an apex within 25 m
        public float baseFrame;         // the player's zoom (frame height, m); 0 = the default 18
        public float dt;
    }

    /// <summary>
    /// U-087 (Bible §5.1 v3, D-076): the stage camera solver, pure C#. Like a theatre set seen from the stalls: it
    /// follows sideways smoothly and holds its height; the player moves within the frame, not the frame around the
    /// player. Outputs the camera centre (X, Y), the frame height and a position-only shake. No allocation.
    /// </summary>
    public sealed class StageCamera
    {
        // Horizontal: dead zone, damped follow, look-ahead, speed cap (§5.1 table).
        public const float DeadZone = 1.5f, FollowTime = 0.25f, LookAhead = 2f, LookAheadTime = 0.6f, SpeedMargin = 2f;
        /// <summary>Below this speed the player counts as standing (the dead zone holds the camera).</summary>
        public const float MovingSpeed = 0.5f;
        // Vertical: the frame bottom sits 3 m under the smoothed stage floor; the player may roam the middle 60 %.
        public const float FloorBelow = 3f, FloorSmoothTime = 0.8f, MiddleBand = 0.6f, VerticalMaxSpeed = 6f;
        public const float LongFall = 10f, FallFollowTime = 0.4f;
        /// <summary>The body centre above the feet, the point kept inside the middle band.</summary>
        public const float BodyCentre = 0.9f;
        // Fight zoom.
        public const float DefaultFrame = 18f, FightFrame = 22f, ApexFrame = 26f, ZoomInTime = 1f, ZoomOutTime = 2f, CalmDelay = 3f;
        // Impact shake: position only, never rotation.
        public const float HitShake = 0.15f, KillShake = 0.08f, ShakeTime = 0.10f;

        public float X { get; private set; }
        public float Y { get; private set; }
        public float Frame { get; private set; } = DefaultFrame;
        public Vector2 Shake { get; private set; }
        /// <summary>True while a fall longer than LongFall is being followed with the 0.4 s follow.</summary>
        public bool FallFollowing { get; private set; }
        /// <summary>The smoothed stage floor the frame bottom is held 3 m below.</summary>
        public float StageFloor => floorS;

        float rel, relVel, look, lookVel;
        float floorS, floorVel, yVel;
        bool haveFloor, landedFollow;
        float heldFloor; // the floor the frame was last set from: a floor that dropped below it holds the frame
        float fallTop;
        float calmTimer = CalmDelay, returnRate;
        float shakeT, shakeAmp;

        /// <summary>Puts the camera where the rules would settle it (scene start, after the photo orbit).</summary>
        public void Snap(in StageInput i)
        {
            float baseF = i.baseFrame > 0f ? i.baseFrame : DefaultFrame;
            Frame = baseF;
            returnRate = 0f;
            calmTimer = CalmDelay;
            look = 0f; lookVel = 0f; rel = 0f; relVel = 0f;
            X = i.playerX;
            floorS = i.floorY; floorVel = 0f; haveFloor = true; heldFloor = floorS;
            Y = floorS - FloorBelow + Frame * 0.5f; yVel = 0f;
            FallFollowing = false; landedFollow = false; fallTop = i.playerY;
            Shake = Vector2.zero; shakeT = 0f; shakeAmp = 0f;
        }

        /// <summary>A hit on the player (HitShake) or a kill (KillShake): the larger pending amplitude wins.</summary>
        public void Impact(float amplitude)
        {
            shakeAmp = Mathf.Max(shakeAmp, amplitude);
            shakeT = ShakeTime;
        }

        public void Step(in StageInput i)
        {
            float dt = Mathf.Max(1e-5f, i.dt);
            if (!haveFloor) Snap(i);
            StepZoom(i, dt);
            StepHorizontal(i, dt);
            StepVertical(i, dt);
            StepShake(dt);
        }

        void StepZoom(in StageInput i, float dt)
        {
            float baseF = i.baseFrame > 0f ? i.baseFrame : DefaultFrame;
            float target = i.apexNear ? Mathf.Max(baseF, ApexFrame) : i.hostilesNear >= 2 ? Mathf.Max(baseF, FightFrame) : baseF;
            if (target > baseF)
            {
                // The frame grows to the fight size over ZoomInTime; a bigger threat grows it further at the same pace.
                calmTimer = 0f;
                returnRate = 0f;
                Frame = Mathf.MoveTowards(Frame, target, (target - baseF) / ZoomInTime * dt);
                return;
            }
            calmTimer += dt;
            if (Frame > baseF + 1e-4f)
            {
                if (calmTimer < CalmDelay) return; // hold the fight frame through 3 s of calm
                if (returnRate <= 0f) returnRate = (Frame - baseF) / ZoomOutTime;
                Frame = Mathf.MoveTowards(Frame, baseF, returnRate * dt);
                if (Frame <= baseF + 1e-4f) { Frame = baseF; returnRate = 0f; }
            }
            else Frame = baseF; // the player's own zoom applies at once
        }

        void StepHorizontal(in StageInput i, float dt)
        {
            bool moving = Mathf.Abs(i.speedX) > MovingSpeed;
            if (moving) look = Mathf.SmoothDamp(look, i.facing * LookAhead, ref lookVel, LookAheadTime, Mathf.Infinity, dt);
            float desired = i.playerX + look;
            float prevX = X;
            // Inside the dead zone a standing player never drags the camera; a moving one is followed at once so the
            // look-ahead builds up, with the camera never faster than the player + 2 m/s.
            if (moving)
            {
                rel = look; // the look-ahead itself eases over 0.6 s; the speed cap below keeps the motion smooth
                relVel = 0f;
                X = i.playerX + rel;
            }
            else if (Mathf.Abs(X - desired) > DeadZone)
            {
                rel = Mathf.SmoothDamp(rel, look, ref relVel, FollowTime, Mathf.Infinity, dt); // a standing player outside the zone: the 0.25 s follow
                X = i.playerX + rel;
            }
            else relVel = 0f;
            float maxStep = (Mathf.Abs(i.speedX) + SpeedMargin) * dt;
            X = Mathf.Clamp(X, prevX - maxStep, prevX + maxStep);
            rel = X - i.playerX;
        }

        void StepVertical(in StageInput i, float dt)
        {
            floorS = Mathf.SmoothDamp(floorS, i.floorY, ref floorVel, FloorSmoothTime, Mathf.Infinity, dt);
            float pc = i.playerY + BodyCentre;
            if (i.grounded)
            {
                fallTop = i.playerY;
                if (FallFollowing) { FallFollowing = false; landedFollow = true; }
            }
            else
            {
                if (i.speedY > 0f) fallTop = Mathf.Max(fallTop, i.playerY);
                if (fallTop - i.playerY > LongFall) FallFollowing = true;
            }
            if (FallFollowing)
            {
                Y = Mathf.SmoothDamp(Y, pc, ref yVel, FallFollowTime, Mathf.Infinity, dt);
                return;
            }
            float yFloor = floorS - FloorBelow + Frame * 0.5f;
            float half = MiddleBand * 0.5f * Frame;
            float goal = Y;
            // The stage floor rule sets the frame from the floor (rising ground, zoom changes, a long fall's landing); a
            // floor that dropped away (digging down, walking downhill) holds the frame until the middle-band rule moves it.
            bool floorDropped = floorS < heldFloor - 0.05f;
            if (!floorDropped || landedFollow) { goal = yFloor; heldFloor = floorS; }
            float banded = Mathf.Clamp(goal, pc - half, pc + half);
            if (banded != goal) { goal = banded; heldFloor = floorS; }
            Y = Mathf.MoveTowards(Y, goal, VerticalMaxSpeed * dt);
            yVel = 0f;
            if (landedFollow && Mathf.Abs(goal - Y) < 0.02f) landedFollow = false; // the frame is back on the stage floor after the long fall
        }

        void StepShake(float dt)
        {
            if (shakeT <= 0f) { if (Shake != Vector2.zero) Shake = Vector2.zero; return; }
            shakeT -= dt;
            if (shakeT <= 0f) { shakeT = 0f; shakeAmp = 0f; Shake = Vector2.zero; return; }
            float k = shakeT / ShakeTime;             // fades out over ShakeTime
            float ph = (ShakeTime - shakeT) * 110f;   // a few quick oscillations, no rotation
            Shake = new Vector2(Mathf.Sin(ph), Mathf.Cos(ph * 1.37f)) * (shakeAmp * k * 0.7071f);
        }
    }
}
