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
        public float baseFrame;         // the player's zoom (frame height, m); 0 = the default 18
        public float dt;
        /// <summary>U-107: flying the ship. playerX/Y are then the hull's centre and speedX/Y its velocity.</summary>
        public bool vehicle;
        /// <summary>U-148: aboard, the skids' height over the ground (m; 0 on the pad, +∞ with no ground under them): the pad framing fades out with it.</summary>
        public float altitude;
        /// <summary>U-213 (3): on foot, the frame's share of baseFrame the camera eases toward (StageZoom: 64 / 96 at the surface with the
        /// close camera on, 1 underground); 0 = 1, the shipped frame.</summary>
        public float zoom;
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
        /// <summary>The frame height (m). D-087: no fight zoom; the player's own zoom (baseFrame) applies at once.</summary>
        public const float DefaultFrame = 18f;
        // Bump shake: position only, never rotation (U-093: a creature or Warden bump; there are no hits or kills).
        public const float BumpShake = 0.15f, ShakeTime = 0.10f;
        // U-107 (§5.1 rules on the ship): the frame leads the hull along its velocity and keeps it inside the middle band.
        public const float VehicleLookTime = 0.6f, VehicleFollowTime = 0.25f;
        /// <summary>U-148 (D-158): the look-ahead never leads the hull by more than this fraction of the frame (0.6 s of a 42 m/s climb was 25 m,
        /// past the middle band, so the band clamp held the camera on every frame of a fast climb).</summary>
        public const float VehicleLookFrame = 0.2f;
        /// <summary>U-148 (D-158 (2)): the ship's own frame: 30 m aboard (the 11.4 m hull at ~40 % of it, sky ahead), widening with speed to
        /// 45 m at ShipFastSpeed and above; the wheel sets the base between ShipFrameMin and ShipFrameMax aboard.</summary>
        public const float ShipFrame = 30f, ShipFrameFast = 45f, ShipFastSpeed = 60f, ShipFrameMin = 24f, ShipFrameMax = 60f;
        /// <summary>U-148: the frame follows speed with a 0.8 s SmoothDamp (never a pop); boarding and stepping out ease it over ~1 s.</summary>
        public const float ShipFrameTime = 0.8f, BoardFrameTime = 0.3f;
        /// <summary>U-148: on the pad the frame's bottom sits FloorBelow under the ground (the stage-floor rule); it hands over to the hull-led
        /// frame over this many metres of the skids' altitude.</summary>
        public const float PadHoldAltitude = 12f;

        /// <summary>U-148: the ship frame for a wheel base and a speed: base + (45 − 30) × speed / 60 (capped at 60 m/s), within [24, 60]. Pure.</summary>
        public static float ShipFrameFor(float baseFrame, float speed)
            => Mathf.Clamp(baseFrame + (ShipFrameFast - ShipFrame) * Mathf.Clamp01(speed / ShipFastSpeed), ShipFrameMin, ShipFrameMax);

        /// <summary>U-148: the look-ahead along the velocity, 0.6 s of it, capped at VehicleLookFrame × the frame. Pure, no allocation.</summary>
        public static Vector2 VehicleLook(float speedX, float speedY, float frame)
        {
            var look = new Vector2(speedX, speedY) * VehicleLookTime;
            float cap = VehicleLookFrame * frame, m = look.magnitude;
            return m > cap && m > 0f ? look * (cap / m) : look;
        }

        /// <summary>U-148: how much of the pad framing still holds at a skid altitude: 1 on the pad, 0 from PadHoldAltitude up or with no ground
        /// under the hull; smoothstep between.</summary>
        public static float PadHold(float altitude)
        {
            if (float.IsInfinity(altitude) || float.IsNaN(altitude)) return 0f;
            float k = Mathf.Clamp01(1f - altitude / PadHoldAltitude);
            return k * k * (3f - 2f * k);
        }

        public float X { get; private set; }
        public float Y { get; private set; }
        public float Frame { get; private set; } = DefaultFrame;
        /// <summary>U-213 (3): the on-foot frame's share of the player's zoom now (1: the shipped frame), eased toward StageInput.zoom with
        /// StageZoom.EaseTime: never a cut. The frame's bottom keeps its share of the frame under the stage floor (FloorBelow x Zoom), so
        /// the close frame is the shipped composition seen closer, not a taller slab of ground.</summary>
        public float Zoom { get; private set; } = 1f;
        float zoomVel;
        static float ZoomGoal(in StageInput i) => i.zoom > 0f ? i.zoom : 1f;
        public Vector2 Shake { get; private set; }
        /// <summary>True while a fall longer than LongFall is being followed with the 0.4 s follow.</summary>
        public bool FallFollowing { get; private set; }
        /// <summary>The smoothed stage floor the frame bottom is held 3 m below.</summary>
        public float StageFloor => floorS;

        float rel, relVel, look, lookVel;
        float floorS, floorVel, yVel;
        bool haveFloor, landedFollow, wasVehicle;
        // U-148: aboard, the camera is the hull's interpolated centre plus a smoothed offset (relX, relY), so the hull's place in the frame
        // changes only as smoothly as the offset; the frame size eases (frameVel), fast while boarding / stepping out.
        float relY, frameVel;
        bool frameEasing;
        /// <summary>U-148: true while the frame eases between the walking and the ship frames after boarding or stepping out.</summary>
        public bool FrameEasing => frameEasing;
        float heldFloor; // the floor the frame was last set from: a floor that dropped below it holds the frame
        float fallTop;
        float shakeT, shakeAmp;

        /// <summary>Puts the camera where the rules would settle it (scene start, after the photo orbit).</summary>
        public void Snap(in StageInput i)
        {
            float baseF = i.baseFrame > 0f ? i.baseFrame : DefaultFrame;
            Zoom = i.vehicle ? 1f : ZoomGoal(i); zoomVel = 0f;
            Frame = i.vehicle ? ShipFrameFor(baseF, Speed(i)) : baseF * Zoom; frameVel = 0f; frameEasing = false;
            look = 0f; lookVel = 0f; rel = 0f; relVel = 0f; relY = 0f;
            X = i.playerX;
            floorS = i.floorY; floorVel = 0f; haveFloor = true; heldFloor = floorS;
            Y = floorS - FloorBelow * Zoom + Frame * 0.5f; yVel = 0f; wasVehicle = i.vehicle;
            if (i.vehicle) { VehicleGoal(i, out rel, out relY); X = i.playerX + rel; Y = i.playerY + relY; } // U-148: where the ship rules settle
            FallFollowing = false; landedFollow = false; fallTop = i.playerY;
            Shake = Vector2.zero; shakeT = 0f; shakeAmp = 0f; shakeDur = ShakeTime;
        }

        /// <summary>A bump (BumpShake): the larger pending amplitude wins.</summary>
        public void Impact(float amplitude) => Impact(amplitude, ShakeTime);

        /// <summary>U-150: an impact lasting `seconds` (the sound barrier's thump: ThumpShake over ThumpTime); the larger pending amplitude wins.</summary>
        public void Impact(float amplitude, float seconds)
        {
            shakeAmp = Mathf.Max(shakeAmp, amplitude);
            shakeDur = Mathf.Max(1e-3f, seconds);
            shakeT = shakeDur;
        }

        /// <summary>U-150 (D-158 (4)): the sound barrier's camera thump: position only.</summary>
        public const float ThumpShake = 0.25f, ThumpTime = 0.15f;
        /// <summary>U-150: a continuous position-only engine rumble (m, the largest offset), set every frame by the follow (0: none).</summary>
        public float Rumble { get; set; }
        float shakeDur = ShakeTime, rumbleT;

        public void Step(in StageInput i)
        {
            float dt = Mathf.Max(1e-5f, i.dt);
            if (!haveFloor) Snap(i);
            float baseF = i.baseFrame > 0f ? i.baseFrame : DefaultFrame;
            if (i.vehicle != wasVehicle)
            {
                relVel = 0f; yVel = 0f; lookVel = 0f; frameVel = 0f; wasVehicle = i.vehicle;
                frameEasing = true; // U-148: the walking frame and the ship frame ease into each other (~1 s), never a pop
                if (i.vehicle) { rel = X - i.playerX; relY = Y - i.playerY; } // the offset starts where the walking camera is
            }
            // U-148: aboard, the frame follows the wheel base and the speed (SmoothDamp 0.8 s); on foot the wheel zoom applies at once (D-087),
            // except while the frame eases back from the ship frame.
            // U-213 (3): the close camera's share eases (aboard it eases back to 1 under the ship's own frame)
            float zoomGoal = i.vehicle ? 1f : ZoomGoal(i);
            if (Zoom != zoomGoal)
            {
                Zoom = Mathf.SmoothDamp(Zoom, zoomGoal, ref zoomVel, StageZoom.EaseTime, Mathf.Infinity, dt);
                if (Mathf.Abs(Zoom - zoomGoal) < 1e-4f) { Zoom = zoomGoal; zoomVel = 0f; }
            }
            float goalF = i.vehicle ? ShipFrameFor(baseF, Speed(i)) : baseF * Zoom;
            if (frameEasing || i.vehicle)
            {
                Frame = Mathf.SmoothDamp(Frame, goalF, ref frameVel, frameEasing ? BoardFrameTime : ShipFrameTime, Mathf.Infinity, dt);
                if (frameEasing && Mathf.Abs(Frame - goalF) < 0.02f) { frameEasing = false; if (!i.vehicle) { Frame = goalF; frameVel = 0f; } }
            }
            else Frame = goalF;
            if (i.vehicle) StepVehicle(i, dt);
            else
            {
                StepHorizontal(i, dt);
                StepVertical(i, dt);
            }
            StepShake(dt);
        }

        static float Speed(in StageInput i) => Mathf.Sqrt(i.speedX * i.speedX + i.speedY * i.speedY);

        /// <summary>
        /// U-148: the camera's offset from the hull's centre the ship rules settle on: the look-ahead (capped at 0.2 × the frame); on and near
        /// the pad at least the stage-floor rule's lift (the frame bottom FloorBelow under the ground, sky ahead of the hull), fading out over
        /// PadHoldAltitude; inside the middle band.
        /// </summary>
        void VehicleGoal(in StageInput i, out float gx, out float gy)
        {
            var lookV = VehicleLook(i.speedX, i.speedY, Frame);
            gx = lookV.x; gy = lookV.y;
            float hold = PadHold(i.altitude);
            if (hold > 0f)
            {
                float pad = floorS - FloorBelow + Frame * 0.5f - i.playerY;
                gy = Mathf.Lerp(gy, Mathf.Max(gy, pad), hold);
            }
            float half = MiddleBand * 0.5f * Frame;
            gx = Mathf.Clamp(gx, -half, half);
            gy = Mathf.Clamp(gy, -half, half);
        }

        /// <summary>
        /// U-107 / U-148: following the ship. The camera is the hull's centre (the interpolated pose, CameraFollow) plus an offset that eases
        /// (0.25 s) toward VehicleGoal; the offset is clamped to the middle band, so the hull never leaves it and the clamp works on the
        /// drawn hull, not the 50 Hz step. The stage floor keeps smoothing underneath, so stepping out hands back to the walking rules
        /// without a jump.
        /// </summary>
        void StepVehicle(in StageInput i, float dt)
        {
            floorS = Mathf.SmoothDamp(floorS, i.floorY, ref floorVel, FloorSmoothTime, Mathf.Infinity, dt);
            heldFloor = floorS;
            VehicleGoal(i, out float gx, out float gy);
            rel = Mathf.SmoothDamp(rel, gx, ref relVel, VehicleFollowTime, Mathf.Infinity, dt);
            relY = Mathf.SmoothDamp(relY, gy, ref yVel, VehicleFollowTime, Mathf.Infinity, dt);
            float half = MiddleBand * 0.5f * Frame;
            rel = Mathf.Clamp(rel, -half, half);
            relY = Mathf.Clamp(relY, -half, half);
            X = i.playerX + rel; Y = i.playerY + relY; look = 0f;
            FallFollowing = false; landedFollow = false; fallTop = i.playerY;
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
                if (FallFollowing) { FallFollowing = false; landedFollow = true; floorS = i.floorY; floorVel = 0f; } // the fall follow already moved the frame: the floor is where we landed
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
            float yFloor = floorS - FloorBelow * Zoom + Frame * 0.5f;
            float half = MiddleBand * 0.5f * Frame;
            float goal = Y;
            // The stage floor rule sets the frame from the floor (rising ground, zoom changes, a long fall's landing); a
            // floor that dropped away (digging down, walking downhill) holds the frame until the middle-band rule moves it.
            bool floorDropped = floorS < heldFloor - 0.05f;
            if (!floorDropped || landedFollow) { goal = yFloor; heldFloor = floorS; }
            float banded = Mathf.Clamp(goal, pc - half, pc + half);
            if (banded != goal) { goal = banded; heldFloor = floorS; }
            // After a long fall the frame is still catching up: it settles onto the stage floor within the 0.4 s follow, else 6 m/s.
            float speed = landedFollow ? Mathf.Max(VerticalMaxSpeed, Mathf.Abs(goal - Y) / (FallFollowTime * 0.5f)) : VerticalMaxSpeed;
            Y = Mathf.MoveTowards(Y, goal, speed * dt);
            yVel = 0f;
            if (landedFollow && Mathf.Abs(goal - Y) < 0.02f) landedFollow = false; // the frame is back on the stage floor after the long fall
        }

        void StepShake(float dt)
        {
            var s = Vector2.zero;
            if (shakeT > 0f)
            {
                shakeT -= dt;
                if (shakeT <= 0f) { shakeT = 0f; shakeAmp = 0f; }
                else
                {
                    float k = shakeT / shakeDur;            // fades out over the impact's time
                    float ph = (shakeDur - shakeT) * 110f;  // a few quick oscillations, no rotation
                    s = new Vector2(Mathf.Sin(ph), Mathf.Cos(ph * 1.37f)) * (shakeAmp * k * 0.7071f);
                }
            }
            if (Rumble > 0f)
            {
                // U-150: the engine rumble: two incommensurate tones per axis, never past Rumble metres, position only.
                rumbleT += dt;
                s += new Vector2(Mathf.Sin(rumbleT * 151f) + 0.5f * Mathf.Sin(rumbleT * 97f), Mathf.Cos(rumbleT * 173f) + 0.5f * Mathf.Sin(rumbleT * 113f)) * (Rumble * 0.47f);
            }
            if (Shake != s) Shake = s;
        }
    }
}
