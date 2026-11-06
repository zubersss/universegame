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
        public const float AnticipateTime = 0.06f, HardLanding = 6f;

        /// <summary>Above walking speed (4 m/s) and below sprint (6.5 m/s): the switch to the run cycle.</summary>
        public const float RunSpeed = 5.2f;
        public const float HurtTime = 0.25f, LandTime = 0.25f, DigTime = 0.35f;

        public static string Pick(in AnimInputs a)
        {
            if (a.dead) return ConkOut;
            if (a.sinceBump < HurtTime) return Bump;
            if (a.sinceHurt < HurtTime) return Hurt;
            if (a.dashing) return Dash;
            if (a.sinceDig < DigTime) return Dig;
            if (!a.grounded) return a.sinceJump < AnticipateTime ? JumpAnticipate : a.vy > 0.5f ? Jump : Fall;
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
                default: return clip;
            }
        }
    }
}
