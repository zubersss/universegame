using System.Collections.Generic;

namespace Meridian.Crafting
{
    /// <summary>
    /// U-051: the first recipe set and Blueprint Tree, written into RecipeBook.asset by the authoring step.
    /// After that the asset is the source of truth (tests read the asset, not this table).
    /// </summary>
    public static class CraftingDefaults
    {
        static Amount A(string item, int count = 1) => new Amount(item, count);

        static Recipe R(string id, Station s, Amount output, string blueprint, params Amount[] inputs) =>
            new Recipe { id = id, station = s, output = output, blueprint = blueprint, inputs = inputs };

        /// <summary>Items found in the world (dug, picked, harvested): every crafted item must trace back to these.</summary>
        public static readonly string[] RawItems =
        {
            "soil", "grass", "stone", "sand", "snow", "regolith", "basalt", "hematite", "water_ice",
            "mercury_regolith", "mercury_basalt", "sulfide", "sulfur", "tessera", "vitriol_glass",
            "iron", "copper", "carbon", "oxygen", "perchlorate", "clay", "aluminium", "living_seed", "wood", "nickel",
            "solarite", "polar_ice", "deep_core_sample",
        };

        public static List<Recipe> Recipes() => new List<Recipe>
        {
            // Smelter: ore → bars, sand → silica.
            R("smelt_hematite", Station.Smelter, A("smelter_bar_iron", 2), "smelting", A("hematite", 3)),
            R("smelt_iron", Station.Smelter, A("smelter_bar_iron"), "smelting", A("iron", 2)),
            R("smelt_copper", Station.Smelter, A("smelter_bar_copper"), "smelting", A("copper", 2)),
            R("smelt_silica", Station.Smelter, A("silica"), "smelting", A("sand", 4)),
            // Refinery: fuel, carbon goods, polymers.
            R("refine_fuel", Station.Refinery, A("launch_fuel", 2), "refining", A("water_ice", 4), A("carbon", 2)),
            R("refine_fuel_perchlorate", Station.Refinery, A("launch_fuel", 2), "perchlorate_oxidizer", A("water_ice", 2), A("perchlorate")),
            R("refine_graphite", Station.Refinery, A("graphite"), "refining", A("carbon", 3)),
            R("refine_polymer", Station.Refinery, A("polymer", 2), "refining", A("carbon", 2), A("oxygen")),
            // Fabricator: parts and suit kit.
            R("fab_suit_patch", Station.Fabricator, A("suit_patch"), "fabrication", A("smelter_bar_iron", 2)),
            R("fab_circuit", Station.Fabricator, A("circuit_board"), "fabrication", A("smelter_bar_copper"), A("silica", 2)),
            R("fab_radiation_liner", Station.Fabricator, A("radiation_liner"), "fabrication", A("smelter_bar_iron"), A("graphite", 2)),
            R("fab_thermal_pad", Station.Fabricator, A("thermal_pad"), "fabrication", A("smelter_bar_copper"), A("basalt", 4)),
            R("fab_cryo_pad", Station.Fabricator, A("cryo_pad"), "fabrication", A("smelter_bar_copper"), A("water_ice", 3)),
            R("fab_fuel_cell", Station.Fabricator, A("launch_fuel_cell"), "fabrication", A("launch_fuel", 5), A("smelter_bar_iron")),
            // Story blueprints (Bible §2).
            R("fab_solarite_capacitor", Station.Fabricator, A("solarite_capacitor"), "solarite_capacitor", A("solarite", 2), A("circuit_board"), A("smelter_bar_copper")),
            R("fab_float_cell", Station.Fabricator, A("float_cell_mk1"), "float_cell_mk1", A("polymer", 3), A("vitriol_glass", 2), A("smelter_bar_iron")),
        };

        static Blueprint B(string id, string name, int tier, string icon, string unlockFlag, params string[] requires) =>
            new Blueprint { id = id, name = name, tier = tier, icon = icon, unlockFlag = unlockFlag, requires = requires };

        /// <summary>The Blueprint Tree: the basic trades, then one story blueprint per beacon (Bible §2).</summary>
        public static List<Blueprint> Blueprints() => new List<Blueprint>
        {
            B("smelting", "Smelting", 0, "smelter_bar_iron", null),
            B("refining", "Refining", 0, "launch_fuel", null),
            B("fabrication", "Fabrication", 1, "circuit_board", null, "smelting"),
            B("survey_module", "Survey module", 1, "survey_module", "beacon:earth"),
            B("perchlorate_oxidizer", "Perchlorate oxidizer", 2, "perchlorate", "beacon:mars", "refining"),
            B("solarite_capacitor", "Solarite capacitor", 2, "solarite_capacitor", "beacon:mercury", "fabrication"),
            B("float_cell_mk1", "Float cell Mk1", 2, "float_cell_mk1", "beacon:venus", "fabrication"),
            B("skip_drive_mk2", "Skip Drive Mk2", 3, "skip_drive_mk2", "beacon:saturn", "solarite_capacitor"),
            B("deep_diamond_tip", "Deep-diamond Rig tip", 3, "deep_diamond_tip", "beacon:uranus", "fabrication"),
            B("thruster_mk3", "Thruster Mk3", 4, "thruster_mk3", "beacon:jupiter", "skip_drive_mk2"),
        };
    }
}
