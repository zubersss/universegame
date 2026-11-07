using System.IO;
using Meridian.Creatures;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-114 (EditMode, D-119, B-132): the stag, wolf and bear sheets carry Gus's clip order (idle 0, walk 1, react 2, bump 3) with
    /// flee (and the wolf's follow) found by name; the species sizes follow the drawn sheets; the bear is territorial and spawns
    /// where the stag does; the clip-index helper is pure.
    /// </summary>
    public class EarthCreatureSheetTests
    {
        [System.Serializable] sealed class Clip { public string name; public int start, length; public bool loop; }
        [System.Serializable] sealed class Sidecar { public string style; public int frame_width, frame_height, frames, fps = 12; public float ppu; public Clip[] animations; }

        [Test]
        public void TheThreeSheetsCarryTheClipOrderAndTheSizes()
        {
            var expected = new (Species species, string key, int w, int h, bool follow)[]
            {
                (Species.Stag, "creatures/earth/stag", 192, 176, false),
                (Species.GreyWolf, "creatures/earth/wolf", 160, 128, true),
                (Species.BrownBear, "creatures/earth/bear", 224, 160, false),
            };
            foreach (var e in expected)
            {
                string json = $"Assets/_Game/Art/{e.key}.json";
                Assert.IsTrue(File.Exists(json), json);
                Assert.IsFalse(File.Exists($"Assets/_Game/Art/{e.key}.glb"), $"{e.key}: the v2 model is gone (D-119)");
                var s = JsonUtility.FromJson<Sidecar>(File.ReadAllText(json));
                Assert.AreEqual("v3", s.style, e.key);
                Assert.AreEqual(e.w, s.frame_width, $"{e.key} frame width"); Assert.AreEqual(e.h, s.frame_height, $"{e.key} frame height");
                Assert.AreEqual(64f, s.ppu, 1e-4f, $"{e.key} PPU 64");
                Assert.AreEqual(12, s.fps);
                Assert.GreaterOrEqual(s.animations.Length, 5, $"{e.key}: idle, walk, react, bump, flee");
                Assert.AreEqual("idle", s.animations[0].name); Assert.AreEqual("walk", s.animations[1].name);
                Assert.AreEqual("react", s.animations[2].name); Assert.AreEqual("bump", s.animations[3].name);
                Assert.IsTrue(System.Array.Exists(s.animations, a => a.name == Creature.FleeClip), $"{e.key} flee");
                Assert.AreEqual(e.follow, System.Array.Exists(s.animations, a => a.name == Creature.FollowClip), $"{e.key} follow");
                foreach (var a in s.animations)
                {
                    Meridian.EditorTools.ArtRules.ClipCap(a.name, out _, out int max);
                    Assert.LessOrEqual(a.length, max, $"{e.key} {a.name} within its cap");
                }
                var spec = SpeciesSpec.Get(e.species);
                Assert.AreEqual(e.key, spec.artKey);
                Assert.AreEqual(e.species, spec.id, "table order");
            }
            Assert.AreEqual(new Vector2(1.5f, 2.0f), SpeciesSpec.Get(Species.Stag).size, "the stag's drawn size (antler tips at 2 m)");
            Assert.AreEqual(new Vector2(1.2f, 1.0f), SpeciesSpec.Get(Species.GreyWolf).size);
            var bear = SpeciesSpec.Get(Species.BrownBear);
            Assert.AreEqual(new Vector2(2.1f, 1.3f), bear.size);
            Assert.AreEqual(Temper.Territorial, bear.temper, "holds its ground (Bible §7.1), no bites (D-087)");
            Assert.AreEqual(Meridian.Planets.PlanetId.Earth, bear.planet);
            Assert.LessOrEqual(bear.maxAlive, 2);
            Assert.IsFalse(bear.Flies);
        }

        [Test]
        public void ClipIndexFindsByNameOrReportsNone()
        {
            var set = new ArtClipSet { key = "x", clips = new System.Collections.Generic.List<ArtClip> { new ArtClip { name = "idle", start = 0, length = 10 }, new ArtClip { name = "flee", start = 10, length = 12 } } };
            Assert.AreEqual(1, Creature.ClipIndex(set, Creature.FleeClip));
            Assert.AreEqual(-1, Creature.ClipIndex(set, Creature.FollowClip), "no follow on this sheet");
            Assert.AreEqual(-1, Creature.ClipIndex(null, Creature.FleeClip));
        }

        [Test]
        public void TheBearSpawnsWhereTheStagDoes()
        {
            var meadow = new SpawnSite { x = 100, planet = Meridian.Planets.PlanetId.Earth, worldWidth = 4096, surfaceY = 330, surfaceTile = Meridian.Terrain.TileId.Grass };
            var dune = new SpawnSite { x = 100, planet = Meridian.Planets.PlanetId.Earth, worldWidth = 4096, surfaceY = 330, surfaceTile = Meridian.Terrain.TileId.Sand };
            Assert.IsTrue(SpeciesSpec.Get(Species.BrownBear).Allows(meadow));
            Assert.IsFalse(SpeciesSpec.Get(Species.BrownBear).Allows(dune));
            Assert.AreEqual(SpeciesSpec.Get(Species.Stag).Allows(meadow), SpeciesSpec.Get(Species.BrownBear).Allows(meadow));
        }
    }
}
