using System.IO;
using Meridian.Planets;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// Writes the eight PlanetConfig assets from the Bible tables (§3, §4.1, §4.2, §5.1).
    /// Idempotent: re-running overwrites values in place, keeping GUIDs.
    /// </summary>
    public static class PlanetConfigAuthoring
    {
        public const string Folder = "Assets/_Game/Settings/Planets";
        public const string CatalogPath = Folder + "/PlanetCatalog.asset";

        struct Row
        {
            public PlanetId id; public WorldType type; public float g, vEsc, terminal;
            public int width, height, datum, escAlt, crush; public float day, orbit, radius;
        }

        static readonly Row[] Rows =
        {
            new Row { id = PlanetId.Mercury, type = WorldType.Solid,       g = 3.70f,  vEsc = 4.3f,  terminal = 60, width = 2048, height = 500,  datum = 320,  escAlt = 120, crush = -1,  day = 0f,    orbit = 1150,  radius = 14 },
            new Row { id = PlanetId.Venus,   type = WorldType.Solid,       g = 8.87f,  vEsc = 10.4f, terminal = 20, width = 4096, height = 1000, datum = 320,  escAlt = 600, crush = -1,  day = 80f,   orbit = 1650,  radius = 24 },
            new Row { id = PlanetId.Earth,   type = WorldType.Solid,       g = 9.81f,  vEsc = 11.2f, terminal = 50, width = 4096, height = 800,  datum = 320,  escAlt = 400, crush = -1,  day = 20f,   orbit = 2000,  radius = 25 },
            new Row { id = PlanetId.Mars,    type = WorldType.Solid,       g = 3.72f,  vEsc = 5.0f,  terminal = 55, width = 3072, height = 640,  datum = 320,  escAlt = 250, crush = -1,  day = 20.5f, orbit = 2550,  radius = 17 },
            new Row { id = PlanetId.Jupiter, type = WorldType.CloudColumn, g = 24.79f, vEsc = 59.5f, terminal = 45, width = 4096, height = 2000, datum = 1100, escAlt = 800, crush = 100, day = 8.3f,  orbit = 5400,  radius = 106 },
            new Row { id = PlanetId.Saturn,  type = WorldType.CloudColumn, g = 10.44f, vEsc = 35.5f, terminal = 48, width = 4096, height = 2000, datum = 1100, escAlt = 700, crush = 100, day = 8.9f,  orbit = 7700,  radius = 96 },
            new Row { id = PlanetId.Uranus,  type = WorldType.CloudColumn, g = 8.69f,  vEsc = 21.3f, terminal = 50, width = 4096, height = 2000, datum = 1100, escAlt = 600, crush = 100, day = 14.3f, orbit = 11800, radius = 57 },
            new Row { id = PlanetId.Neptune, type = WorldType.CloudColumn, g = 11.15f, vEsc = 23.5f, terminal = 50, width = 4096, height = 2000, datum = 1100, escAlt = 650, crush = 100, day = 13.4f, orbit = 15400, radius = 56 },
        };

        [MenuItem("MERIDIAN/Author Planet Configs")]
        public static void Run()
        {
            Directory.CreateDirectory(Folder);
            AssetDatabase.Refresh();

            var catalog = AssetDatabase.LoadAssetAtPath<PlanetCatalog>(CatalogPath);
            if (catalog == null)
            {
                catalog = ScriptableObject.CreateInstance<PlanetCatalog>();
                AssetDatabase.CreateAsset(catalog, CatalogPath);
            }
            catalog.planets = new PlanetConfig[Rows.Length];

            for (int i = 0; i < Rows.Length; i++)
            {
                var r = Rows[i];
                var path = $"{Folder}/{r.id}.asset";
                var c = AssetDatabase.LoadAssetAtPath<PlanetConfig>(path);
                if (c == null)
                {
                    c = ScriptableObject.CreateInstance<PlanetConfig>();
                    AssetDatabase.CreateAsset(c, path);
                }
                c.id = r.id; c.worldType = r.type; c.landable = true;
                c.gravity = r.g; c.escapeVelocityKms = r.vEsc; c.terminalVelocity = r.terminal;
                c.worldWidth = r.width; c.worldHeight = r.height; c.datumY = r.datum;
                c.escapeAltitude = r.escAlt; c.crushLineY = r.crush;
                c.dayLengthRealMinutes = r.day; c.orbitRadius = r.orbit; c.visualRadius = r.radius;
                EditorUtility.SetDirty(c);
                catalog.planets[i] = c;
            }

            EditorUtility.SetDirty(catalog);
            AssetDatabase.SaveAssets();
            Debug.Log("[MERIDIAN] PlanetConfigAuthoring wrote 8 PlanetConfigs and the PlanetCatalog.");
        }
    }
}
