using System.Collections.Generic;
using Meridian.EditorTools;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Save;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-157 (EditMode, D-162 (6), D-165 (3)): a 0.4.8 save (v2) moves to the smooth ground. Its smooth planets' poi_stamped flags go (other
    /// planets' stay), the stamp diffs 0.4.8 cut against the blocky ground leave the terrain edits, the player's own digs and builds stay, and
    /// stamping again lands each pad on the smoothed ground.
    /// </summary>
    public class SmoothGroundMigrationTests
    {
        const int Seed = 1969;

        static PlanetConfig Earth()
        {
            var cfg = AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/Earth.asset");
            Assert.NotNull(cfg, "Earth's config");
            return cfg;
        }

        [Test]
        public void AVersionTwoSaveDropsTheSmoothPlanetsStampFlags()
        {
            var data = new SaveData { version = 2 };
            data.story = new StorySave();
            var earthFlags = new List<string>();
            foreach (var poi in PoiCatalog.For(PlanetId.Earth)) earthFlags.Add(poi.StampedFlag);
            data.story.flags.AddRange(earthFlags);
            string mars = null;
            foreach (var poi in PoiCatalog.For(PlanetId.Mars)) { mars = poi.StampedFlag; break; }
            Assert.NotNull(mars, "a Mars POI");
            data.story.flags.Add(mars);
            data.story.flags.Add("met_archivist");
            var m = SaveMigrations.Migrate(data);
            Assert.AreEqual(SaveData.CurrentVersion, m.version);
            Assert.AreEqual(2, m.loadedVersion, "the file's own version is kept for the terrain step");
            foreach (var f in earthFlags) Assert.IsFalse(m.story.flags.Contains(f), $"{f} goes: Earth re-stamps");
            Assert.IsTrue(m.story.flags.Contains(mars), "Mars keeps its stamps (its ground is still blocks)");
            Assert.IsTrue(m.story.flags.Contains("met_archivist"), "story flags stay");
        }

        [Test]
        public void TheOldStampsLeaveThePlayersEditsStayAndThePadsRestampSmooth()
        {
            var cfg = Earth();
            var camp = PoiCatalog.SpawnCamp;
            // 0.4.8's Earth: the raw ground, its stamps, then a dig into the camp's pad and a block built in the open.
            var edits = new TerrainEdits();
            int oldPad, newPad;
            bool was = GroundField.ForceBlocks;
            GroundField.ForceBlocks = true;
            SolidWorldGenerator raw;
            try
            {
                raw = new SolidWorldGenerator(cfg, Seed);
                Assert.IsFalse(raw.SmoothGround);
                foreach (var poi in PoiCatalog.For(PlanetId.Earth)) PoiStamp.Apply(poi, raw, edits, cfg.datumY);
                oldPad = PoiStamp.GroundY(camp, raw, cfg.datumY);
            }
            finally { GroundField.ForceBlocks = was; }
            int stamped = edits.Count;
            Assert.Greater(stamped, 0, "0.4.8 stamped Earth");
            // The player's edits since: ice built on a stamped cell (a value neither the stamp nor the ground has), a dig into solid ground
            // off the stamps, a block in the open air. Each leaves its own diff.
            var (sx, sy, sid) = edits.Cells()[0];
            Assert.AreNotEqual(TileId.Ice, sid); Assert.AreNotEqual(TileId.Ice, raw.TileAt(sx, sy));
            edits.Set(sx, sy, TileId.Ice, raw.TileAt(sx, sy));
            int digX = camp.x + camp.Width + 300, digY = 0;
            for (; digX < camp.x + camp.Width + 400; digX++)
            {
                digY = raw.SurfaceHeight(digX) - 2;
                if (TileId.IsSolid(raw.TileAt(digX, digY)) && !edits.TryGet(digX, digY, out _)) break;
            }
            Assert.IsTrue(TileId.IsSolid(raw.TileAt(digX, digY)), "a solid cell to dig");
            edits.Set(digX, digY, TileId.Air, raw.TileAt(digX, digY));
            int buildX = digX + 5, buildY = raw.SurfaceHeight(buildX) + 4;
            edits.Set(buildX, buildY, TileId.Stone, raw.TileAt(buildX, buildY));

            int gone = SmoothGroundMigration.StripOldStamps(edits, cfg, Seed);
            TestContext.Out.WriteLine($"[MERIDIAN] u157 migration: {stamped} stamp diffs, {gone} removed, {edits.Count} left");
            Assert.AreEqual(stamped - 1, gone, "every untouched 0.4.8 stamp diff goes");
            Assert.IsTrue(edits.TryGet(sx, sy, out byte iced) && iced == TileId.Ice, "the player's change to a stamped cell stays");
            Assert.IsTrue(edits.TryGet(digX, digY, out byte dug) && dug == TileId.Air, "the player's dig stays");
            Assert.IsTrue(edits.TryGet(buildX, buildY, out byte built) && built == TileId.Stone, "the player's block stays");
            Assert.AreEqual(3, edits.Count, "only the player's edits are left");

            // Stamped again on the smoothed ground (as PoiPlacer.StampFor does once the flags are gone): the pad sits on the new ground.
            var smooth = new SolidWorldGenerator(cfg, Seed);
            Assert.IsTrue(smooth.SmoothGround);
            foreach (var poi in PoiCatalog.For(PlanetId.Earth)) PoiStamp.Apply(poi, smooth, edits, cfg.datumY);
            newPad = PoiStamp.GroundY(camp, smooth, cfg.datumY);
            var world = new EditedWorld(smooth, edits);
            int mid = camp.x + camp.Width / 2;
            TestContext.Out.WriteLine($"[MERIDIAN] u157 camp pad: 0.4.8 {oldPad}, smooth {newPad}, the camp's middle column tops at {world.SurfaceHeight(mid)}");
            Assert.IsTrue(TileId.IsSolid(world.TileAt(mid, newPad)) && !TileId.IsSolid(world.TileAt(mid, newPad + 1)), "the camp's pad is the smooth ground's");
        }
    }
}
