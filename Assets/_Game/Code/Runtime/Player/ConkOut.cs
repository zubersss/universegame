using Meridian.Building;
using Meridian.Hazards;
using Meridian.Ship;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Player
{
    /// <summary>
    /// U-093 (Bible v4, D-087): Suit power reached 0 (PlayerVitals.Died). The surveyor conks out: dizzy stars and the
    /// iris-out (ConkedOut; U-096 draws the iris), the body stops for OutSeconds while the screen is closed, then they
    /// wake standing at the last base piece placed on this planet, or beside the ship when there is no base, with Suit
    /// power full. Nothing is taken: the pack and the cargo stay as they were (pillar 5). Lives on the PlanetSide root.
    /// No allocation per frame.
    /// </summary>
    public sealed class ConkOut : MonoBehaviour
    {
        /// <summary>Iris-out (0.35 s, U-096) + a beat of black + the wake.</summary>
        public const float OutSeconds = 1.0f;
        /// <summary>Wake beside the ship: this far left of its centre (m), clear of the hull and the pad.</summary>
        public const float BesideShip = 3f;

        public PlayerController player;
        public PlayerVitals vitals;
        public HazardSystem hazards;
        public BaseBuilder bases;
        public SideShip ship;
        public TerrainStreamer terrain;

        public bool Out { get; private set; }
        public int Count { get; private set; }
        /// <summary>Where the last wake put the surveyor's feet, and whether it was a base (false: the ship).</summary>
        public Vector2 LastWake { get; private set; }
        public bool LastWakeAtBase { get; private set; }

        /// <summary>Conked out at this position (the iris centres on it).</summary>
        public event System.Action<Vector2> ConkedOut;
        /// <summary>Woke at this position (the iris opens on it).</summary>
        public event System.Action<Vector2> Woke;

        float wakeAt;
        PlayerVitals hooked;

        void OnEnable() => Hook();
        void OnDisable() { if (hooked != null) hooked.Died -= OnDied; hooked = null; }

        /// <summary>(Re)binds to the vitals; PlanetSideRoot calls it after wiring.</summary>
        public void Hook()
        {
            if (vitals == null && player != null) vitals = player.GetComponent<PlayerVitals>();
            if (hooked == vitals) return;
            if (hooked != null) hooked.Died -= OnDied;
            hooked = vitals;
            if (hooked != null) hooked.Died += OnDied;
        }

        void OnDied()
        {
            if (Out) return;
            Out = true;
            Count++;
            wakeAt = Time.time + OutSeconds;
            Vector2 at = player != null && player.Body != null ? player.Body.position : (Vector2)transform.position;
            if (player != null && player.Body != null) { player.Body.linearVelocity = Vector2.zero; player.Body.simulated = false; }
            ConkedOut?.Invoke(at);
        }

        void Update()
        {
            if (!Out) return;
            // Suit power refilled by something else while out (a save load, a scripted scene, a test): no wake trip.
            if (vitals != null && !vitals.Dead) { Cancel(); return; }
            if (Time.time >= wakeAt) Wake();
        }

        void Cancel()
        {
            Out = false;
            if (player != null && player.Body != null) player.Body.simulated = true;
        }

        /// <summary>Wakes now (tests, and the scheduled wake).</summary>
        public void Wake()
        {
            if (!Out) return;
            Out = false;
            Vector2 feet = WakePoint(out bool atBase);
            LastWake = feet;
            LastWakeAtBase = atBase;
            if (player != null && player.Body != null)
            {
                player.Body.position = feet;
                player.transform.position = feet;
                player.Body.linearVelocity = Vector2.zero;
                player.Body.simulated = true;
            }
            if (vitals != null) vitals.Restore();
            if (hazards != null) hazards.RestoreSuit();
            Woke?.Invoke(feet);
        }

        /// <summary>The last base piece placed here, else beside the ship; standing on the ground at that column.</summary>
        public Vector2 WakePoint(out bool atBase)
        {
            atBase = false;
            float x;
            if (bases != null && bases.pieces.Count > 0 && bases.pieces[bases.pieces.Count - 1].go != null)
            {
                // Just right of the piece (its cells are solid or occupied): never inside it.
                var piece = bases.pieces[bases.pieces.Count - 1];
                x = Mathf.Floor(piece.go.transform.position.x) + piece.spec.size.x + 0.5f;
                atBase = true;
            }
            else if (ship != null) x = ship.transform.position.x - BesideShip;
            else x = player != null ? player.transform.position.x : transform.position.x;
            float y = terrain != null ? terrain.TopSolidY(Mathf.FloorToInt(x)) + 1.05f : (player != null ? player.transform.position.y : 0f);
            return new Vector2(Mathf.Floor(x) + 0.5f, y);
        }
    }
}
