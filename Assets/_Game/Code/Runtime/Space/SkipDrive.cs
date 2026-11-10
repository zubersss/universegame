using Meridian.Player;
using Meridian.UI;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Meridian.Space
{
    /// <summary>
    /// U-063 Skip Drive (Bible §3), consumable-free since U-107 (D-105): hold J to spool for SpoolSeconds, then the ship
    /// travels at Speed along its heading while J is held. It won't spool inside a Gravity Well and drops out of skip on
    /// entering one (back to cruise speed). After a skip ends the drive cools down for CooldownSeconds before it can
    /// spool again. HUD line: spool, skip, cool-down, or why it won't.
    /// </summary>
    public sealed class SkipDrive : MonoBehaviour
    {
        public const float Speed = 1200f, SpoolSeconds = 3f, CooldownSeconds = 10f;

        public SpaceShip ship;
        /// <summary>Tests and scripted scenes hold J through this.</summary>
        public bool holdOverride;

        public enum Mode { Idle, Spooling, Skipping }
        public Mode Current { get; private set; }
        /// <summary>0..1 while spooling.</summary>
        public float Spool { get; private set; }
        /// <summary>Seconds left before the drive may spool again (0 when ready).</summary>
        public float Cooldown { get; private set; }
        public string Refusal { get; private set; } = "";

        InputAction key;
        Text hud;
        int lastCooldownShown = -1;
        static readonly string[] CoolingLines = BuildCoolingLines();

        static string[] BuildCoolingLines()
        {
            var lines = new string[Mathf.CeilToInt(CooldownSeconds) + 1];
            for (int i = 0; i < lines.Length; i++) lines[i] = $"SKIP DRIVE COOLING  {i} s";
            return lines;
        }

        void Start()
        {
            if (ship == null) ship = GetComponent<SpaceShip>();
            if (ship != null && ship.actions != null) key = ship.actions.FindActionMap(MeridianInput.ShipTop, true).FindAction("SkipDrive");
            var canvas = UiKit.Canvas(transform, "SkipCanvas", 106);
            hud = UiKit.Text(canvas.transform, "Skip", new Vector2(0.5f, 0f), new Vector2(0f, 70f), new Vector2(700f, 26f), 18, true, TextAnchor.MiddleCenter, UiTheme.Active.text);
            hud.gameObject.SetActive(false);
        }

        bool Held => holdOverride || (key != null && key.IsPressed() && ship != null && !ship.externalInput);

        /// <summary>Whether a skip could start or continue now: out of every well and not cooling down.</summary>
        public bool CanSkip(out string why)
        {
            why = "";
            if (ship == null || ship.Destroyed) { why = "NO SHIP"; return false; }
            if (ship.InWellOf != null)
            {
                // the line is made once a well, not once a physics step (U-211: FixedUpdate asks every step, key held or not: 116 B a
                // step in any gravity well; found by the Profiler's capture in Space)
                if (wellLineOf != ship.InWellOf) { wellLineOf = ship.InWellOf; wellLine = $"SKIP DISABLED: {ship.InWellOf.ToUpperInvariant()} GRAVITY WELL"; }
                why = wellLine;
                return false;
            }
            if (Current == Mode.Idle && Cooldown > 0f) { why = "SKIP DRIVE COOLING"; return false; }
            return true;
        }
        string wellLineOf, wellLine;

        void FixedUpdate()
        {
            if (ship == null) return;
            float dt = Time.fixedDeltaTime;
            if (Cooldown > 0f) Cooldown = Mathf.Max(0f, Cooldown - dt);
            bool held = Held;
            bool can = CanSkip(out var why);
            Refusal = can ? "" : why;
            switch (Current)
            {
                case Mode.Idle:
                    if (held && can) { Current = Mode.Spooling; Spool = 0f; }
                    break;
                case Mode.Spooling:
                    if (!held || !can) { Stop(); break; }
                    Spool = Mathf.Min(1f, Spool + dt / SpoolSeconds);
                    if (Spool >= 1f) { Current = Mode.Skipping; ship.skipSpeed = Speed; }
                    break;
                case Mode.Skipping:
                    if (!held || !can) Stop();
                    break;
            }
        }

        void Stop()
        {
            if (Current == Mode.Skipping && ship != null)
            {
                ship.skipSpeed = 0f;
                // Out of skip at cruise speed along the heading; the drive cools down before it spools again.
                if (ship.Velocity.sqrMagnitude > SpaceLayout.CruiseSpeed * SpaceLayout.CruiseSpeed) ship.Velocity = ship.Velocity.normalized * SpaceLayout.CruiseSpeed;
                Cooldown = CooldownSeconds;
            }
            Current = Mode.Idle;
            Spool = 0f;
        }

        void Update()
        {
            if (hud == null) return;
            bool show = Current != Mode.Idle || (Held && Refusal.Length > 0);
            if (hud.gameObject.activeSelf != show) hud.gameObject.SetActive(show);
            if (!show) return;
            if (Current == Mode.Idle && Cooldown > 0f)
            {
                int c = Mathf.CeilToInt(Cooldown);
                if (c != lastCooldownShown) { lastCooldownShown = c; hud.text = CoolingLines[Mathf.Clamp(c, 0, CoolingLines.Length - 1)]; }
                return;
            }
            lastCooldownShown = -1;
            hud.text = Current switch
            {
                Mode.Spooling => $"SKIP DRIVE SPOOLING  {Mathf.RoundToInt(Spool * 100f)}%",
                Mode.Skipping => $"SKIP  {Speed:F0} u/s",
                _ => Refusal,
            };
        }
    }
}
