using UnityEngine;

namespace Meridian.Building
{
    /// <summary>Append only: saved by name in BasePieceSave.kind.</summary>
    public enum PieceKind { Wall, Door, Lamp, Crate, Deck, FloatCell, WindAnchor } // D-157: appended (saves name kinds; the table follows the enum)

    /// <summary>
    /// U-056 Bases v1: one base piece (B-014 shelter set, B-045 aerostat set). Pieces sit on the 1 m tile grid,
    /// `size` cells wide and tall from their bottom-left cell. Solid pieces stop bodies; sealing pieces close a
    /// shelter (a door seals but lets the surveyor through: it is the airlock). Mass is aerostat load; lift is
    /// what a float cell carries (Bible §7.4 buoyancy budget: lift ≥ load).
    /// </summary>
    public sealed class PieceSpec
    {
        public PieceKind kind;
        public string itemKey, artKey;
        public Vector2Int size;
        public bool solid, seals;
        /// <summary>Stretch the art to fill the cells (walls, decks, crates); otherwise fit it by height.</summary>
        public bool stretch;
        public float mass, lift;

        static readonly PieceSpec[] All =
        {
            new PieceSpec { kind = PieceKind.Wall, itemKey = "shelter_wall", artKey = "props/common/shelter_wall", size = new Vector2Int(1, 1), solid = true, seals = true, stretch = true, mass = 1f },
            new PieceSpec { kind = PieceKind.Door, itemKey = "shelter_door", artKey = "props/common/shelter_door", size = new Vector2Int(1, 2), seals = true, mass = 1f },
            new PieceSpec { kind = PieceKind.Lamp, itemKey = "lamp", artKey = "props/common/lamp", size = new Vector2Int(1, 2), mass = 0.5f },
            new PieceSpec { kind = PieceKind.Crate, itemKey = "storage_crate", artKey = "props/common/storage_crate", size = new Vector2Int(1, 1), solid = true, seals = true, stretch = true, mass = 2f },
            new PieceSpec { kind = PieceKind.Deck, itemKey = "aerostat_deck", artKey = "props/venus/aerostat_deck", size = new Vector2Int(2, 1), solid = true, seals = true, stretch = true, mass = 2f },
            new PieceSpec { kind = PieceKind.FloatCell, itemKey = "float_cell_mk1", artKey = "props/venus/buoyancy_cell", size = new Vector2Int(1, 2), mass = 0f, lift = 6f },
            // D-157 (b): Neptune's wind anchor (B-161, 128 x 192): placed like a camp prop; the surveyor holds it to stand fast (U-144).
            new PieceSpec { kind = PieceKind.WindAnchor, itemKey = "wind_anchor", artKey = "props/neptune/wind_anchor", size = new Vector2Int(2, 3), mass = 1f },
        };

        public static PieceSpec Get(PieceKind k) => All[(int)k];

        /// <summary>The piece an item places, or null (not a base piece).</summary>
        public static PieceSpec ForItem(string itemKey)
        {
            foreach (var s in All) if (s.itemKey == itemKey) return s;
            return null;
        }

        public static int Count => All.Length;
    }

    /// <summary>A placed piece, as saved (state.json). x/y: bottom-left cell; for aerostat pieces, relative to the aerostat.</summary>
    [System.Serializable]
    public sealed class BasePieceSave
    {
        public string planet;
        public string kind;
        public int x, y;
        /// <summary>The aerostat it rides (0: fixed to the ground).</summary>
        public int aerostat;
    }

    /// <summary>An aerostat, as saved: its anchor cell and how far it has sunk (m).</summary>
    [System.Serializable]
    public sealed class AerostatSave
    {
        public int id;
        public string planet;
        public int x, y;
        public float sunk;
    }

    /// <summary>U-056 buoyancy budget (Bible §7.4). Pure.</summary>
    public static class Buoyancy
    {
        /// <summary>Metres per second an aerostat sinks per unit of missing lift (capped at MaxSink).</summary>
        public const float SinkPerUnit = 0.6f, MaxSink = 4f;

        public static float Margin(float lift, float load) => lift - load;

        /// <summary>Sink speed (m/s, ≥ 0): zero while lift covers the load.</summary>
        public static float SinkSpeed(float lift, float load) => Mathf.Clamp((load - lift) * SinkPerUnit, 0f, MaxSink);
    }
}
