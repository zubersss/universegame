namespace Meridian.Ship
{
    /// <summary>
    /// U-150 (D-158 (4)): the sound barrier, pure C#. Fed the hull's speed and the air's density every physics step, it fires once when the
    /// speed rises through the planet's speed of sound where the air is at least MinDensity thick, and re-arms only after the speed falls
    /// below ReArm × that speed. No air (a speed of sound of 0, Mercury) never fires. A crossing in air too thin fires nothing and leaves it armed.
    /// </summary>
    public sealed class SoundBarrier
    {
        public const float MinDensity = 0.1f, ReArm = 0.8f;

        public bool Armed { get; private set; } = true;
        /// <summary>How many times it fired (tests, the HUD log).</summary>
        public int Booms { get; private set; }
        float lastSpeed = -1f;

        /// <summary>One step: true on the step the barrier breaks.</summary>
        public bool Step(float speed, float density, float speedOfSound)
        {
            bool fire = false;
            if (speedOfSound > 0f)
            {
                if (!Armed && speed < ReArm * speedOfSound) Armed = true;
                if (Armed && lastSpeed >= 0f && lastSpeed < speedOfSound && speed >= speedOfSound && density >= MinDensity)
                {
                    fire = true;
                    Armed = false;
                    Booms++;
                }
            }
            lastSpeed = speed;
            return fire;
        }

        public void Reset() { Armed = true; lastSpeed = -1f; }
    }
}
