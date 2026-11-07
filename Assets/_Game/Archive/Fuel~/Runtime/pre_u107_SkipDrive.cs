using Meridian.Core;
using Meridian.Items;
using Meridian.Player;
using Meridian.UI;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Meridian.Space
{
    /// <summary>
    /// U-063 Skip Drive (Bible §3): hold J to spool for SpoolSeconds, then the ship travels at Speed along its
    /// heading while J is held, burning skip fuel (FuelPerSecond). It won't spool inside a Gravity Well and drops
    /// out of skip on entering one (back to cruise speed). The tank tops itself up from the hold: Helium-3
    /// Condensate (Saturn) gives UnitsPerHelium3, deuterium (refined from water) a third of that. HUD line: spool,
    /// skip, fuel, or why it won't.
    /// </summary>
    public sealed class SkipDrive : MonoBehaviour
    {
        public const float Speed = 1200f, SpoolSeconds = 3f, FuelPerSecond = 1f;
        public const float UnitsPerHelium3 = 10f, UnitsPerDeuterium = UnitsPerHelium3 / 3f;

        public SpaceShip ship;
        /// <summary>Tests and scripted scenes hold J through this.</summary>
        public bool holdOverride;

        public enum Mode { Idle, Spooling, Skipping }
        public Mode Current { get; private set; }
        /// <summary>0..1 while spooling.</summary>
        public float Spool { get; private set; }
        public string Refusal { get; private set; } = "";

        InputAction key;
        Text hud;

        void Start()
        {
            if (ship == null) ship = GetComponent<SpaceShip>();
            if (ship != null && ship.actions != null) key = ship.actions.FindActionMap(MeridianInput.ShipTop, true).FindAction("SkipDrive");
            var canvas = UiKit.Canvas(transform, "SkipCanvas", 106);
            hud = UiKit.Text(canvas.transform, "Skip", new Vector2(0.5f, 0f), new Vector2(0f, 70f), new Vector2(700f, 26f), 18, true, TextAnchor.MiddleCenter, UiTheme.Active.text);
            hud.gameObject.SetActive(false);
        }

        bool Held => holdOverride || (key != null && key.IsPressed() && ship != null && !ship.externalInput);

        /// <summary>Skip fuel in the tank, topped up from the hold when it runs dry.</summary>
        public static bool Draw(Inventory inv, ref float tank, float units)
        {
            while (tank < units)
            {
                var he3 = ItemRegistry.Get("helium3_condensate");
                var d = ItemRegistry.Get("deuterium");
                if (he3 != null && inv.Remove(he3.id, 1)) tank += UnitsPerHelium3;
                else if (d != null && inv.Remove(d.id, 1)) tank += UnitsPerDeuterium;
                else return false;
            }
            tank -= units;
            return true;
        }

        /// <summary>Whether a skip could start or continue now (fuel in the tank or the hold, out of every well).</summary>
        public bool CanSkip(out string why)
        {
            var s = GameState.Instance;
            why = "";
            if (ship == null || ship.Destroyed) { why = "NO SHIP"; return false; }
            if (ship.InWellOf != null) { why = $"SKIP DISABLED: {ship.InWellOf.ToUpperInvariant()} GRAVITY WELL"; return false; }
            if (s == null) return true;
            var he3 = ItemRegistry.Get("helium3_condensate");
            var d = ItemRegistry.Get("deuterium");
            bool fuel = s.skipFuel > 0f || (he3 != null && s.inventory.Count(he3.id) > 0) || (d != null && s.inventory.Count(d.id) > 0);
            if (!fuel) { why = "NO SKIP FUEL"; return false; }
            return true;
        }

        void FixedUpdate()
        {
            if (ship == null) return;
            float dt = Time.fixedDeltaTime;
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
                    var s = GameState.Instance;
                    bool fuelled = true;
                    if (s != null) { float tank = s.skipFuel; fuelled = Draw(s.inventory, ref tank, FuelPerSecond * dt); s.skipFuel = tank; }
                    if (!held || !can || !fuelled) Stop();
                    break;
            }
        }

        void Stop()
        {
            if (Current == Mode.Skipping && ship != null)
            {
                ship.skipSpeed = 0f;
                // Out of skip at cruise speed along the heading.
                if (ship.Velocity.sqrMagnitude > SpaceLayout.CruiseSpeed * SpaceLayout.CruiseSpeed) ship.Velocity = ship.Velocity.normalized * SpaceLayout.CruiseSpeed;
            }
            Current = Mode.Idle;
            Spool = 0f;
        }

        void Update()
        {
            if (hud == null) return;
            var s = GameState.Instance;
            bool show = Current != Mode.Idle || (Held && Refusal.Length > 0);
            if (hud.gameObject.activeSelf != show) hud.gameObject.SetActive(show);
            if (!show) return;
            float fuel = s != null ? s.skipFuel : 0f;
            hud.text = Current switch
            {
                Mode.Spooling => $"SKIP DRIVE SPOOLING  {Mathf.RoundToInt(Spool * 100f)}%",
                Mode.Skipping => $"SKIP  {Speed:F0} u/s  ·  FUEL {fuel:F1}",
                _ => Refusal,
            };
        }
    }
}
