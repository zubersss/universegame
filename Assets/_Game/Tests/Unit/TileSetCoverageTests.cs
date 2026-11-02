using System.Collections.Generic;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>
    /// U-064 (EditMode): every tile a planet's generator makes is in the tile set that planet loads — a tile
    /// missing from it has no art and no collision (the Mars polar-cap frost was, and the surveyor sank 2 m).
    /// </summary>
    public class TileSetCoverageTests
    {
        [Test]
        public void EveryGeneratedTileIsInItsPlanetsTileSet()
        {
            foreach (var name in new[] { "Earth", "Mars", "Mercury", "Venus" })
            {
                var config = AssetDatabase.LoadAssetAtPath<PlanetConfig>($"Assets/_Game/Settings/Planets/{name}.asset");
                var gen = new SolidWorldGenerator(config, 1969);
                var loaded = new HashSet<byte>(TerrainStreamer.MaterialsFor(config.id));
                var missing = new HashSet<byte>();
                for (int x = 0; x < config.worldWidth; x += 3)
                {
                    int s = gen.SurfaceHeight(x);
                    for (int y = s; y > s - 60 && y >= 0; y--)
                    {
                        byte t = gen.TileAt(x, y);
                        if (t != TileId.Air && !loaded.Contains(t)) missing.Add(t);
                    }
                }
                Assert.IsEmpty(missing, $"{name} generates tiles its tile set doesn't load: {string.Join(", ", missing)}");
            }
        }
    }
}
