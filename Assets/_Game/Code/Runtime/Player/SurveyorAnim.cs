namespace Meridian.Player
{
    /// <summary>What the surveyor is doing this frame, for picking an animation clip (U-032).</summary>
    public struct AnimInputs
    {
        public bool dead, grounded, usingRig;
        public float vx, vy;
        /// <summary>Seconds since the last hurt / landing / dig (large when never).</summary>
        public float sinceHurt, sinceLand, sinceDig;
    }

    /// <summary>
    /// U-032: picks the surveyor's clip by priority: death, hurt, dig, jump (rising) / fall, land,
    /// aim, run, walk, idle. Clip names match characters/surveyor/base.json (contract §5).
    /// </summary>
    public static class SurveyorAnim
    {
        public const string Idle = "idle", Walk = "walk", Run = "run", Jump = "jump", Fall = "fall",
            Land = "land", Dig = "dig", Aim = "aim", Hurt = "hurt", Death = "death";

        /// <summary>Above walking speed (4 m/s) and below sprint (6.5 m/s): the switch to the run cycle.</summary>
        public const float RunSpeed = 5.2f;
        public const float HurtTime = 0.25f, LandTime = 0.25f, DigTime = 0.35f;

        public static string Pick(in AnimInputs a)
        {
            if (a.dead) return Death;
            if (a.sinceHurt < HurtTime) return Hurt;
            if (a.sinceDig < DigTime) return Dig;
            if (!a.grounded) return a.vy > 0.5f ? Jump : Fall;
            if (a.sinceLand < LandTime) return Land;
            float speed = a.vx < 0f ? -a.vx : a.vx;
            if (a.usingRig && speed < 0.3f) return Aim;
            if (speed > RunSpeed) return Run;
            if (speed > 0.3f) return Walk;
            return Idle;
        }
    }
}
