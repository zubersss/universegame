using System.IO;
using Meridian.Flora;
using Meridian.Planets;
using Meridian.Terrain;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-123: Mercury runs the cartoon path like Earth and Mars. The set follows the terminator (B-149's day / twilight / night by the zone at the camera
    /// column; a cold trap is the night set on either side), the strips are B-148's regolith and slate kinds by the shadow, the plants come from the Mercury
    /// rig set's biome lists through the zone names (day / twilight / night / polar), the stage datum follows the cold-trap bowls, and the Shadewyrm is a den
    /// species (D-126). Pure rules; the checks on the art log until B-148 / B-149 land.
    /// </summary>
    public class MercuryStageTests
    {
        const int W = 4096;
        // LocalTime(x) = 0.25 − (x − dawn) / W: noon sits a quarter world behind the dawn line, midnight a quarter ahead, dusk half a world on.
        static int DawnLine(double t) => Mathf.RoundToInt(MercuryTerminator.Dawn(t, W)) % W;
        static int Noon(double t) => (DawnLine(t) - W / 4 + W) % W;
        static int Midnight(double t) => (DawnLine(t) + W / 4) % W;

        [Test]
        public void MercuryIsConvertedAndItsSetFollowsTheTerminator()
        {
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Mercury), "U-123: Mercury on the cartoon stage");
            Assert.AreEqual("twilight", CartoonStage.MercuryFallbackScene, "the band the player runs through stands in for a set not exported yet");
            Assert.AreEqual("twilight", CartoonStage.FallbackFor(PlanetId.Mercury)); Assert.AreEqual("canyon", CartoonStage.FallbackFor(PlanetId.Mars)); Assert.IsNull(CartoonStage.FallbackFor(PlanetId.Earth));
            double t0 = 0;
            Assert.AreEqual("day", CartoonStage.MercurySceneFor(Noon(t0), t0, W), "noon: the day set");
            Assert.AreEqual("night", CartoonStage.MercurySceneFor(Midnight(t0), t0, W), "midnight: the night set");
            Assert.AreEqual("twilight", CartoonStage.MercurySceneFor(DawnLine(t0), t0, W), "the dawn line: the twilight set");
            Assert.AreEqual("twilight", CartoonStage.MercurySceneFor((DawnLine(t0) + W / 2) % W, t0, W), "the dusk line too");
            Assert.AreEqual("twilight", CartoonStage.MercurySceneFor(DawnLine(t0) + 190, t0, W), "190 m into the band");
            Assert.AreEqual("day", CartoonStage.MercurySceneFor((DawnLine(t0) - 210 + W) % W, t0, W), "210 m behind the dawn line: the sun is up");
            Assert.AreEqual("night", CartoonStage.MercurySceneFor(DawnLine(t0) + 210, t0, W), "210 m ahead of it: still night");
            // The band creeps 1 m per 6 s: the column that was the dawn line is deep in the day 400 m of creep later.
            double later = 400 * MercuryTerminator.CreepSecondsPerMetre;
            Assert.AreEqual("day", CartoonStage.MercurySceneFor(DawnLine(t0), later, W), "the dawn line passed: day");
            Assert.AreEqual("twilight", CartoonStage.MercurySceneFor(DawnLine(t0) + 400, later, W), "the line is 400 m on");
            // A cold trap is the night set on either side of the terminator: its floor never sees the sun.
            int sunTrap = MercuryLandforms.ColdTrapCentre(1, W), darkTrap = MercuryLandforms.ColdTrapCentre(0, W);
            Assert.AreEqual(MercuryZone.Day, MercuryTerminator.ZoneAt(sunTrap, t0, W), "the second trap sits on the day side at the start clock");
            Assert.AreEqual("night", CartoonStage.MercurySceneFor(sunTrap, t0, W), "…and still paints the night set");
            Assert.AreEqual("night", CartoonStage.MercurySceneFor(darkTrap, t0, W));
            Assert.AreEqual("day", CartoonStage.MercurySceneFor(0, t0, 0), "no world width yet: the day set, no division");
            Assert.AreEqual("forest", CartoonStage.SceneFor(PlanetId.Earth, 64), "Earth keeps its band rule");
            foreach (var scene in new[] { "day", "twilight", "night" })
            {
                string json = $"Assets/_Game/Art/backgrounds/mercury/{scene}/{scene}.json";
                if (!File.Exists(json)) { TestContext.Out.WriteLine($"[MERIDIAN] backgrounds/mercury/{scene}: not exported yet (B-149); the placeholder tints stand in"); continue; }
                var layout = SceneLayout.Parse(File.ReadAllText(json));
                Assert.AreEqual(3, layout.layers.Length, scene + ": three layers");
            }
        }

        [Test]
        public void TheMercuryStripsPlantsAndDatumFollowTheShadow()
        {
            var keys = GroundStrip.KeysFor(PlanetId.Mercury);
            Assert.AreEqual(2, keys.Length, "B-148: the regolith and slate kinds");
            Assert.AreEqual("terrain/mercury/ground_strip", keys[GroundStrip.MercuryRegolith]);
            Assert.AreEqual("terrain/mercury/ground_strip_slate", keys[GroundStrip.Slate]);
            Assert.AreEqual(GroundStrip.MercuryRegolith, GroundStrip.MaterialFor(PlanetId.Mercury, TileId.MercuryRegolith), "the pure rule: regolith (the shadow is the clock's)");
            Assert.AreEqual(GroundStrip.MercuryRegolith, GroundStrip.MaterialFor(PlanetId.Mercury, TileId.MercuryBasalt));
            Assert.AreSame(GroundStrip.MarsKeys, GroundStrip.KeysFor(PlanetId.Mars)); Assert.AreSame(GroundStrip.Keys, GroundStrip.KeysFor(PlanetId.Earth));
            double t0 = 0;
            Assert.AreEqual(GroundStrip.MercuryRegolith, GroundStrip.MercuryStripFor(Noon(t0), t0, W), "noon: the blinding regolith");
            Assert.AreEqual(GroundStrip.Slate, GroundStrip.MercuryStripFor(Midnight(t0), t0, W), "midnight: slate");
            Assert.AreEqual(GroundStrip.MercuryRegolith, GroundStrip.MercuryStripFor(DawnLine(t0), t0, W), "the band: lit, regolith");
            int sunTrap = MercuryLandforms.ColdTrapCentre(1, W);
            Assert.AreEqual(GroundStrip.Slate, GroundStrip.MercuryStripFor(sunTrap, t0, W), "a cold trap's floor on the day side: permanent shadow, slate");
            Assert.AreEqual(GroundStrip.MercuryRegolith, GroundStrip.MercuryStripFor(sunTrap + MercuryLandforms.ColdTrapHalfWidth - 2, t0, W), "its rim wall sees the sun");
            Assert.AreEqual(GroundStrip.MercuryRegolith, GroundStrip.MercuryStripFor(Midnight(t0), t0, 0), "no world width: regolith, no division");
            foreach (var k in keys)
            {
                string json = "Assets/_Game/Art/" + k + ".json";
                if (!File.Exists(json)) { TestContext.Out.WriteLine("[MERIDIAN] " + k + ": not exported yet (B-148); no strip draws on Mercury until the regolith kind lands"); continue; }
                var s = JsonUtility.FromJson<GroundStripTests.Sheet>(File.ReadAllText(json));
                Assert.AreEqual(64, s.frame_width); Assert.AreEqual(152, s.frame_height); Assert.AreEqual(128, s.ground_line_px); Assert.AreEqual(8, s.frames);
            }
            // The plants: the rig set's biome vocabulary is the zone at placement — day / twilight / night — and polar in a cold trap.
            Assert.AreEqual("day", FloraRigs.MercuryBiomeFor(Noon(t0), t0, W));
            Assert.AreEqual("twilight", FloraRigs.MercuryBiomeFor(DawnLine(t0), t0, W));
            Assert.AreEqual("night", FloraRigs.MercuryBiomeFor(Midnight(t0), t0, W));
            Assert.AreEqual("polar", FloraRigs.MercuryBiomeFor(sunTrap, t0, W), "a cold trap is polar on either side");
            Assert.IsNull(FloraRigs.BiomeNameAt(PlanetId.Mercury, 64), "without the clock the planet rule has no answer: the stage sets biomeRule");
            Assert.IsNull(FloraRigs.MercuryBiomeFor(64, t0, 0));
            string rig = "Assets/_Game/Art/flora/mercury/rigset.json";
            if (File.Exists(rig))
            {
                var set = RigSet.Parse(File.ReadAllText(rig), out var error);
                Assert.IsNull(error, "the Mercury rig set parses");
                foreach (var biome in new[] { "day", "twilight", "night", "polar" })
                {
                    var kinds = FloraRigs.PlantsFor(set, biome);
                    Assert.GreaterOrEqual(kinds.Length, 1, biome + ": at least one kind");
                    TestContext.Out.WriteLine($"[MERIDIAN] mercury {biome}: {kinds.Length} kinds");
                }
            }
            else TestContext.Out.WriteLine("[MERIDIAN] flora/mercury/rigset: not exported yet (B-148); biomes expected: day, twilight, night, polar");
            // The datum: the plain is one band at the pad's surface; a cold trap follows its bowl from the rim in, with no step.
            var d = new BandDatum(PlanetId.Mercury, 320f, 64, 326f, W);
            Assert.AreEqual(326f, d.At(64), 1e-4f, "the pad keeps its measured surface");
            Assert.AreEqual(326f, d.At(2000), 1e-4f, "the plain is one band: the spawn surface");
            int trap = MercuryLandforms.ColdTrapCentre(0, W);
            Assert.AreEqual(320f - MercuryLandforms.ColdTrapDepth, d.At(trap), 0.01f, "the crater floor: datum − depth");
            Assert.AreEqual(326f, d.At(trap - MercuryLandforms.ColdTrapHalfWidth), 1e-3f, "the rim column: still the plain");
            float prev = d.At(trap - MercuryLandforms.ColdTrapHalfWidth - 1);
            for (int x = trap - MercuryLandforms.ColdTrapHalfWidth; x <= trap; x++) { float v = d.At(x); Assert.LessOrEqual(Mathf.Abs(v - prev), 2.5f, $"x {x}: no step ({prev:F1} → {v:F1})"); prev = v; }
            Assert.AreEqual(d.At(trap - 10), d.At(trap + 10), 1e-3f, "a symmetric bowl");
            Assert.AreEqual(326f, new BandDatum(PlanetId.Mercury, 320f, 64, 326f).At(trap), 1e-4f, "no world width: the spawn surface everywhere, no division");
        }

        /// <summary>D-146: no seeded small crater reaches within ±40 columns of the pad (the camp sits on the plain, not in a 9 m bowl), and
        /// Mercury's band datum is the generator's own surface without the small craters: the plain's by the spawn, the bowl's (noise
        /// included) in a cold trap, so the set meets the trap's floor.</summary>
        [Test]
        public void TheCampSitsOnThePlainAndTheBandsFollowTheGeneratorsSurface()
        {
            // 1. No small crater by the pad, for any seed; elsewhere they still pock the plain.
            int pocked = 0;
            for (int seed = 1; seed <= 60; seed++)
            {
                for (int x = MercuryLandforms.PadX - MercuryLandforms.PadClear; x <= MercuryLandforms.PadX + MercuryLandforms.PadClear; x++)
                    Assert.AreEqual(MercuryLandforms.BandHeight(x, W, 0f), MercuryLandforms.Height(x, W, 0f, seed), 1e-4f, $"seed {seed} x {x}: no small crater within ±{MercuryLandforms.PadClear} of the pad");
                for (int x = 600; x < 1400; x += 7) if (Mathf.Abs(MercuryLandforms.Height(x, W, 0f, seed) - MercuryLandforms.BandHeight(x, W, 0f)) > 0.5f) { pocked++; break; }
            }
            Assert.Greater(pocked, 50, "the small craters still pock the plain away from the pad");

            // 2. The datum through a band surface (a sloping plain + the bowls): the plain by the spawn without a bowl, the trap per column.
            System.Func<int, float> band = x => 318f + 0.002f * x + MercuryLandforms.ColdTrapProfile(x, W);
            var d = new BandDatum(PlanetId.Mercury, 320f, 64, 310f, W, band);
            Assert.AreEqual(band(64), d.mercuryPlain, 1e-4f, "the plain: the band surface at the spawn (the measured 310 was a crater floor)");
            Assert.AreEqual(d.mercuryPlain, d.At(64), 1e-4f, "the pad");
            Assert.AreEqual(d.mercuryPlain, d.At(2000), 1e-4f, "the plain is one band");
            int trap = MercuryLandforms.ColdTrapCentre(0, W);
            Assert.AreEqual(band(trap), d.At(trap), 1e-4f, "the trap's floor: the band surface there (noise + bowl)");
            float prev = d.At(trap - MercuryLandforms.ColdTrapHalfWidth - 1);
            for (int x = trap - MercuryLandforms.ColdTrapHalfWidth; x <= trap; x++) { float v = d.At(x); Assert.LessOrEqual(Mathf.Abs(v - prev), 2.5f, $"x {x}: no step ({prev:F1} → {v:F1})"); prev = v; }
            var inTrap = new BandDatum(PlanetId.Mercury, 320f, trap, 284f, W, band);
            Assert.AreEqual(band(trap) - MercuryLandforms.ColdTrapProfile(trap, W), inTrap.At(2000), 1e-3f, "an entry inside a trap: the plain still takes the plain's surface, not the bowl's");

            // 3. The real generator: Mercury's band surface is its surface by the pad, and sits on the floor in each trap.
            var c = LoadConfig("Mercury");
            Assert.NotNull(c, "Mercury.asset");
            var g = new SolidWorldGenerator(c, 1969);
            for (int x = MercuryLandforms.PadX - MercuryLandforms.PadClear; x <= MercuryLandforms.PadX + MercuryLandforms.PadClear; x++)
                Assert.AreEqual(g.SurfaceHeight(x), g.BandSurfaceHeight(x), $"x {x}: the pad's ground is the band surface (no small crater)");
            for (int i = 0; i < MercuryLandforms.ColdTrapAt.Length; i++)
            {
                int centre = MercuryLandforms.ColdTrapCentre(i, c.worldWidth);
                TestContext.Out.WriteLine($"[MERIDIAN] D-146 trap {i} at {centre}: surface {g.SurfaceHeight(centre)}, band {g.BandSurfaceHeight(centre)}, nominal {c.datumY + MercuryLandforms.ColdTrapProfile(centre, c.worldWidth):F1}; pad 64: surface {g.SurfaceHeight(64)}, band {g.BandSurfaceHeight(64)}");
            }
            var other = new SolidWorldGenerator(LoadConfig("Mars"), 1969);
            Assert.AreEqual(other.SurfaceHeight(500), other.BandSurfaceHeight(500), "other planets: the band surface is the surface");
        }

        static PlanetConfig LoadConfig(string planet) => UnityEditor.AssetDatabase.LoadAssetAtPath<PlanetConfig>($"Assets/_Game/Settings/Planets/{planet}.asset");

        /// <summary>U-123 (D-126, B-150): the Shadewyrm is a den species in the cold traps with props/mercury/ice_burrow as its burrow; the Flarewing flies; the rest of the Mercury table is untouched.</summary>
        [Test]
        public void TheShadewyrmDensInTheColdTrapsAndTheFlarewingFlies()
        {
            var wyrm = Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.Shadewyrm);
            Assert.AreEqual(PlanetId.Mercury, wyrm.planet); Assert.AreEqual("creatures/mercury/shadewyrm", wyrm.artKey);
            Assert.IsTrue(wyrm.HasDen); Assert.AreEqual("props/mercury/ice_burrow", wyrm.den, "D-126: the burrow is a separate static prop (B-150)");
            var trap = new Meridian.Creatures.SpawnSite { x = MercuryLandforms.ColdTrapCentre(0, W), worldWidth = W, planet = PlanetId.Mercury, surfaceTile = TileId.MercuryRegolith, surfaceY = 284, datumY = 320, zone = MercuryZone.Night };
            Assert.IsTrue(wyrm.Allows(trap), "in the cold trap");
            trap.x += 400; Assert.IsFalse(wyrm.Allows(trap), "on the plain: no burrow");
            var wing = Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.Flarewing);
            Assert.AreEqual(Meridian.Creatures.Habitat.Air, wing.habitat, "a flier (B-150: fly at index 1)"); Assert.IsFalse(wing.HasDen);
            Assert.IsFalse(Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.Glassback).HasDen);
            Assert.AreEqual("idle_open", Meridian.Creatures.Creature.IdleOpenClip, "away from the burrow");
        }
    }
}
