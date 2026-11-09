namespace Meridian.Player
{
    /// <summary>What the surveyor is doing this frame, for picking an animation clip (U-032).</summary>
    public struct AnimInputs
    {
        public bool dead, grounded, usingRig;
        public float vx, vy;
        /// <summary>Seconds since the last hurt / landing / dig (large when never).</summary>
        public float sinceHurt, sinceLand, sinceDig;
        /// <summary>U-089/U-093: seconds since a bump and the jump; the landing speed; the dash state.</summary>
        public float sinceBump, sinceJump, landSpeed;
        public bool dashing;
        /// <summary>U-105 (C1 clips): the jetpack firing; climbing into the ship; seconds since a build and a surprise (large when never).</summary>
        public bool jetpacking, climbingIn;
        /// <summary>U-176 (B-210): on a ladder; riding a line up (the Grapple's reel, the winch).</summary>
        public bool ladder, reeling;
        public float sinceBuild, sinceSurprise;
    }

    /// <summary>
    /// U-032: picks the surveyor's clip by priority: conk out, bump, hurt, dash, dig, jump (rising) / fall, land,
    /// aim, run, walk, idle. Clip names match characters/surveyor/base.json (contract §5).
    /// </summary>
    public static class SurveyorAnim
    {
        public const string Idle = "idle", Walk = "walk", Run = "run", Jump = "jump", Fall = "fall",
            Land = "land", Dig = "dig", Aim = "aim", Hurt = "hurt", Death = "death";
        /// <summary>U-089 (Bible §4.2 Feel, contract v2.5): the feel clips; StandIn maps each to an old clip until B-103 lands.</summary>
        public const string JumpAnticipate = "jump_anticipate", LandHard = "land_hard", Dash = "dash";
        /// <summary>U-093 (contract v3.0 §11, D-087): a bump with dizzy stars; Suit power at 0. StandIn maps them until the v4 sheets land.</summary>
        public const string Bump = "bump", ConkOut = "conk_out";
        /// <summary>U-105 (C1, contract §11.2): the sheet's look_camera and the clips BLENDER adds in C1; ResolveOn names a stand-in until each lands.</summary>
        public const string LookCamera = "look_camera", Build = "build", Surprise = "surprise", Jetpack = "jetpack", ClimbIn = "climb_in";
        /// <summary>U-176 (B-210, side_b): the ladder's climb and the reel up a line.</summary>
        public const string ClimbLadder = "climb_ladder", ReelUp = "reel_up";
        public const float SurpriseTime = 0.5f;

        /// <summary>Every clip Pick can return (U-105: each must resolve to a real clip or a named stand-in on the live sheet).</summary>
        public static readonly string[] AllClips =
        {
            Idle, Walk, Run, Jump, Fall, Land, Dig, Aim, Hurt, Death, JumpAnticipate, LandHard, Dash, Bump, ConkOut,
            LookCamera, Build, Surprise, Jetpack, ClimbIn, ClimbLadder, ReelUp,
        };
        public const float AnticipateTime = 0.06f, HardLanding = 6f;

        /// <summary>Above walking speed (4 m/s) and below sprint (6.5 m/s): the switch to the run cycle.</summary>
        public const float RunSpeed = 5.2f;
        public const float HurtTime = 0.25f, LandTime = 0.25f, DigTime = 0.35f;

        public static string Pick(in AnimInputs a)
        {
            if (a.dead) return ConkOut;
            if (a.sinceBump < HurtTime) return Bump;
            if (a.sinceHurt < HurtTime) return Hurt;
            if (a.climbingIn) return ClimbIn;                 // U-105: boarding the ship
            if (a.sinceSurprise < SurpriseTime) return Surprise; // U-105: the eye-pop
            if (a.ladder) return ClimbLadder;                 // U-176: the ways back up
            if (a.reeling) return ReelUp;
            if (a.dashing) return Dash;
            if (a.sinceBuild < DigTime) return Build;          // U-105: the Builder placed a tile
            if (a.sinceDig < DigTime) return Dig;
            if (!a.grounded) return a.jetpacking ? Jetpack : a.sinceJump < AnticipateTime ? JumpAnticipate : a.vy > 0.5f ? Jump : Fall;
            if (a.sinceLand < LandTime) return a.landSpeed >= HardLanding ? LandHard : Land;
            float speed = a.vx < 0f ? -a.vx : a.vx;
            if (a.usingRig && speed < 0.3f) return Aim;
            if (speed > RunSpeed) return Run;
            if (speed > 0.3f) return Walk;
            return Idle;
        }

        /// <summary>The old clip that stands in for a feel clip the sheet or model does not have yet.</summary>
        public static string StandIn(string clip)
        {
            switch (clip)
            {
                case Bump: return Hurt;
                case ConkOut: return Death;
                case Dash: case JumpAnticipate: return Jump;
                case LandHard: return Land;
                case Build: return Dig;
                case Surprise: return LookCamera;
                case Jetpack: return Jump;
                case ClimbIn: return Land;
                case ClimbLadder: case ReelUp: return Jump;
                default: return clip;
            }
        }

        /// <summary>
        /// U-105: the clip to play on a sheet that `has` some clips: the clip itself, else its named stand-in (the nearest drawing
        /// the sheet has), else idle. Pure, so SurveyorAnimTests can list every state's resolution on the live sheet.
        /// </summary>
        public static string ResolveOn(string clip, System.Func<string, bool> has)
        {
            if (has(clip)) return clip;
            switch (clip)
            {
                case LandHard: case ClimbIn: return has(Land) ? Land : Idle;
                case JumpAnticipate: case Dash: case Fall: case Jetpack: case ClimbLadder: case ReelUp: return has(Jump) ? Jump : Idle;
                case Run: return has(Walk) ? Walk : Idle;
                case Hurt: return has(Bump) ? Bump : Idle;
                case Bump: return has(Hurt) ? Hurt : Idle;
                case Build: return has(Dig) ? Dig : Idle;
                case Surprise: return has(LookCamera) ? LookCamera : Idle;
                case ConkOut: return has(Death) ? Death : Idle;
                case Death: return has(ConkOut) ? ConkOut : Idle;
                default: return Idle; // dig and aim: idle until the C1 sheet draws them (listed in the U-105 report)
            }
        }
    }
}
