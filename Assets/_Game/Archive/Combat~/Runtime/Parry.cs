using UnityEngine;

namespace Meridian.Player
{
    /// <summary>
    /// U-088 (Bible §4.2 Feel): the parry. C opens a Window; an attack caught inside it is parried (no damage, the
    /// attacker staggers or the projectile reflects, the dash refreshes, a Flash shows); a window that catches nothing
    /// costs the Recovery, during which no new parry starts (no cancel). Works on the ground and in the air. Pure C#.
    /// </summary>
    public sealed class Parry
    {
        public const float Window = 0.12f, Recovery = 0.40f, Flash = 0.3f;

        public bool Active => windowLeft > 0f;
        public bool Recovering => recoveryLeft > 0f;
        public bool Flashing => flashLeft > 0f;
        public bool Ready => !Active && !Recovering;
        public int Parries { get; private set; }

        float windowLeft, recoveryLeft, flashLeft;

        public bool TryStart()
        {
            if (!Ready) return false;
            windowLeft = Window;
            return true;
        }

        public void Step(float dt)
        {
            if (windowLeft > 0f)
            {
                windowLeft -= dt;
                if (windowLeft <= 0f) { windowLeft = 0f; recoveryLeft = Recovery; } // a whiff
            }
            else if (recoveryLeft > 0f) recoveryLeft = Mathf.Max(0f, recoveryLeft - dt);
            if (flashLeft > 0f) flashLeft = Mathf.Max(0f, flashLeft - dt);
        }

        /// <summary>An attack reaches the player: true when the window catches it (the window closes with no recovery).</summary>
        public bool Catch()
        {
            if (!Active) return false;
            windowLeft = 0f;
            recoveryLeft = 0f;
            flashLeft = Flash;
            Parries++;
            return true;
        }
    }
}
