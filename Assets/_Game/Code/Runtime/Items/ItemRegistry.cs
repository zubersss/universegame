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
            Tile(TileId.Soil, "soil", "Soil", null);
            Tile(TileId.Grass, "grass", "Turf", null);
            Tile(TileId.Stone, "stone", "Stone", "icons/stone/base");
            Tile(TileId.Sand, "sand", "Sand", "icons/sand/base");
            Tile(TileId.Snow, "snow", "Snow", null);
            Tile(TileId.Regolith, "regolith", "Regolith", null);
            Tile(TileId.Basalt, "basalt", "Basalt", null);
            Tile(TileId.Hematite, "hematite", "Hematite", "icons/hematite/base");
            Tile(TileId.Ice, "water_ice", "Water ice", "icons/water_ice/base");

            // Resources (B-013 batch 1); not placeable.
            int id = FirstResource;
            foreach (var (key, name) in new[]
            {
                ("iron", "Iron"), ("copper", "Copper"), ("carbon", "Carbon"), ("silica", "Silica"),
                ("oxygen", "Oxygen"), ("launch_fuel", "Launch fuel"), ("perchlorate", "Perchlorate"),
                ("clay", "Clay"), ("aluminium", "Aluminium"), ("living_seed", "Living seed"),
                ("wood", "Wood"), ("nickel", "Nickel"),
            })
                Add(new ItemDef { id = id++, key = key, name = name, icon = $"icons/{key}/base" });
        }

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
        public static int DropOf(byte tile) => tile == TileId.Water || Get(tile) == null ? 0 : tile;
    }
}
