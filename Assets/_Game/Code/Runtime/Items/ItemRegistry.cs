using System.Collections.Generic;
using Meridian.Terrain;

namespace Meridian.Items
{
    /// <summary>One kind of item: what it's called, its icon, and the tile it places (0 = none).</summary>
    public sealed class ItemDef
    {
        public int id;
        public string key;      // stable save/name key, e.g. "iron"
        public string name;     // shown in the inventory panel
        public string icon;     // Addressables key of its icon (icons/<key>/base), or null: the tile sprite stands in
        public byte placeTile;  // TileId the Builder places from it; 0 = not placeable
        public int stackMax = Inventory.StackMax;
    }

    /// <summary>
    /// Item registry v1 (U-045). Tile items keep their TileId as item id (1–10), so drops, cargo and
    /// older saves stay valid; resource items (B-013 icons) start at 100. Ids never change once shipped.
    /// </summary>
    public static class ItemRegistry
    {
        public const int FirstResource = 100;

        static readonly List<ItemDef> all = new List<ItemDef>();
        static readonly Dictionary<int, ItemDef> byId = new Dictionary<int, ItemDef>();
        static readonly Dictionary<string, ItemDef> byKey = new Dictionary<string, ItemDef>();

        static ItemRegistry()
        {
            // Tile items: digging a tile drops one of its own kind; placing it puts the tile back.
            Tile(TileId.Soil, "soil", "Soil", "icons/soil/base"); // U-091 tail (B-128, LEAD cycle 246): a drawn icon instead of the tile sprite
            Tile(TileId.Grass, "grass", "Turf", "icons/grass/base"); // U-091 tail (B-128, LEAD cycle 246): a drawn icon instead of the tile sprite
            Tile(TileId.Stone, "stone", "Stone", "icons/stone/base");
            Tile(TileId.Sand, "sand", "Sand", "icons/sand/base");
            Tile(TileId.Snow, "snow", "Snow", "icons/snow/base"); // U-091 tail (B-128, LEAD cycle 246): a drawn icon instead of the tile sprite
            Tile(TileId.Regolith, "regolith", "Regolith", "icons/regolith/base"); // U-091 tail (B-128, LEAD cycle 246): a drawn icon instead of the tile sprite
            Tile(TileId.Basalt, "basalt", "Basalt", "icons/basalt/base");
            Tile(TileId.Hematite, "hematite", "Hematite", "icons/hematite/base");
            Tile(TileId.Ice, "water_ice", "Water ice", "icons/water_ice/base");
            // Mercury (U-048): its ice drops the same water ice.
            Tile(TileId.MercuryRegolith, "mercury_regolith", "Mercury regolith", "icons/mercury_regolith/base"); // U-091 tail (B-128, LEAD cycle 246): a drawn icon instead of the tile sprite
            Tile(TileId.MercuryBasalt, "mercury_basalt", "Mercury basalt", "icons/mercury_basalt/base"); // U-091 tail (B-128, LEAD cycle 246): a drawn icon instead of the tile sprite
            Tile(TileId.Sulfide, "sulfide", "Sulfide", "icons/sulfide/base"); // U-091 tail (B-128, LEAD cycle 246): a drawn icon instead of the tile sprite
            // Venus (U-050): its basalt drops the same basalt; vent glass is Vitriol Glass.
            Tile(TileId.Sulfur, "sulfur", "Sulfur", "icons/sulfur/base");
            Tile(TileId.Tessera, "tessera", "Tessera", "icons/tessera/base"); // U-091 tail (B-128, LEAD cycle 246): a drawn icon instead of the tile sprite
            Tile(TileId.VentGlass, "vitriol_glass", "Vitriol Glass", "icons/vitriol_glass/base");

            // Resources (B-013 batch 1); not placeable.
            int id = FirstResource;
            foreach (var (key, name) in new[]
            {
                ("iron", "Iron"), ("copper", "Copper"), ("carbon", "Carbon"), ("silica", "Silica"),
                ("oxygen", "Oxygen"), Retired, ("perchlorate", "Perchlorate"),
                ("clay", "Clay"), ("aluminium", "Aluminium"), ("living_seed", "Living seed"),
                ("wood", "Wood"), ("nickel", "Nickel"),
                // U-051 (B-042 icons): refined and crafted goods, raw finds. Append only: ids never change once shipped.
                ("smelter_bar_iron", "Iron bar"), ("smelter_bar_copper", "Copper bar"), ("graphite", "Graphite"),
                ("suit_patch", "Suit patch"), ("circuit_board", "Circuit board"), ("radiation_liner", "Radiation liner"),
                ("thermal_pad", "Thermal pad"), ("cryo_pad", "Cryo pad"), Retired,
                ("solarite", "Solarite"), ("polar_ice", "Polar ice"), ("deep_core_sample", "Deep core sample"),
            })
            {
                if (key == null) { id++; continue; } // U-107 (D-103/D-105): a retired item keeps its id unused
                Add(new ItemDef { id = id++, key = key, name = name, icon = $"icons/{key}/base" });
            }
            // B-051 icons.
            foreach (var (key, name) in new[] { ("polymer", "Polymer"), ("solarite_capacitor", "Solarite capacitor"), ("float_cell_mk1", "Float cell Mk1") })
                Add(new ItemDef { id = id++, key = key, name = name, icon = $"icons/{key}/base" });
            // U-055: Lance ammunition, the Veil Serpent's counter (icon B-054).
            // U-170 (D-173): cryo_round retired (the Veil Serpent's ammunition, unused since D-087): its id stays unused so later ids never move.
            CryoRoundRetiredId = id++;
            // U-059: the Tharsis Worm's plate (M4+): registered, no source yet.
            Add(new ItemDef { id = id++, key = "wormplate", name = "Wormplate" });
            // U-056 base pieces (B-014, B-045): their art is their icon. The float cell (B-051) is the aerostat's lift.
            // U-159 (Residency): the deck's icon is B-069's common kit deck: an item travels, and the Venus station's prop kept planet_venus
            // resident on every planet once a Fabricator's recipe list had shown it.
            foreach (var (key, name, art) in new[] { ("shelter_wall", "Shelter wall", "props/common/shelter_wall"), ("shelter_door", "Shelter door", "props/common/shelter_door"),
                ("lamp", "Lamp", "props/common/lamp"), ("storage_crate", "Storage crate", "props/common/storage_crate"), ("aerostat_deck", "Aerostat deck", "props/common/aerostat_deck") })
                Add(new ItemDef { id = id++, key = key, name = name, icon = art });
            // U-063: Helium-3 Condensate (Saturn), a crafting material. U-107 (D-105): the slot after it is retired (kept unused).
            Add(new ItemDef { id = id++, key = "helium3_condensate", name = "Helium-3 Condensate", icon = "icons/helium3_condensate/base" }); // B-061
            id++;
            // U-069 M4 materials (Bible §7.6–7.9) and gear; icons from B-061 (same keys), placeholders until then.
            foreach (var (key, name) in new[]
            {
                ("metallic_hydrogen", "Metallic Hydrogen"), ("ammonia_ice", "Ammonia ice"), ("phosphorus_pigment", "Phosphorus pigment"),
                ("ring_ice", "Ring ice"), ("ring_rock", "Ring rock"), ("methane_ice", "Methane ice"),
                ("deep_diamond", "Deep Diamond"), ("superionic_ice", "Superionic Ice"),
                ("float_cell_mk2", "Float cell Mk2"), ("jetpack_mk2", "Jetpack Mk2"), ("jetpack_mk3", "Jetpack Mk3"),
                // U-065 ship upgrades (Bible §4.3): installed when crafted (ShipMarks.Install).
                ("thruster_mk2", "Thruster Mk2"), ("thruster_mk3", "Thruster Mk3"),
            })
                Add(new ItemDef { id = id++, key = key, name = name, icon = $"icons/{key}/base" });
            // D-157 (b): Neptune's wind anchor, a base piece (its prop art is its icon); appended so every older id stays.
            Add(new ItemDef { id = id++, key = "wind_anchor", name = "Wind anchor", icon = "icons/wind_anchor/base" }); // B-197: a shared icon (U-159 Residency)
        }

        /// <summary>U-170 (D-173): the retired cryo_round's id (no item has it; a save's cryo rounds convert on load, RetiredItems).</summary>
        public static int CryoRoundRetiredId { get; private set; } = -1;

        /// <summary>U-107: a retired item's slot in an id-ordered list (its id stays unused so later ids never move).</summary>
        static readonly (string, string) Retired = (null, null);

        static void Tile(byte tile, string key, string name, string icon) =>
            Add(new ItemDef { id = tile, key = key, name = name, icon = icon, placeTile = tile });

        static void Add(ItemDef d)
        {
            all.Add(d);
            byId[d.id] = d;
            byKey[d.key] = d;
        }

        public static IReadOnlyList<ItemDef> All => all;
        public static ItemDef Get(int id) => byId.TryGetValue(id, out var d) ? d : null;
        public static ItemDef Get(string key) => key != null && byKey.TryGetValue(key, out var d) ? d : null;

        /// <summary>The item a dug tile drops (water drops nothing).</summary>
        public static int DropOf(byte tile) => tile == TileId.MercuryIce ? TileId.Ice : tile == TileId.VenusBasalt ? TileId.Basalt : tile == TileId.Water || Get(tile) == null ? 0 : tile;
    }
}
