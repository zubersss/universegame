using System.IO;
using System.Linq;
using Meridian.EditorTools;
using Meridian.Planets;
using Meridian.Ship;
using Meridian.Space;
using Meridian.View2D;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-103 (EditMode, D-098 / D-108 / D-100): every body of the top-down map has a painted disc sheet at the space scale
    /// (space_ppu 3, radius_u, an idle clip of 9 or 12 frames at 12 fps) imported at PPU 3, Saturn's rings likewise with a
    /// centre pivot and a wobble rig, the starfield scene layout carries the tiled starfield and three nebula cards, and the
    /// ship's squash/stretch and the ring wobble are pure maths.
    /// </summary>
    public class SpaceArtRulesTests
    {
        [Test]
        public void TheStarfieldTileNeverCoversLessThanHalfTheFrame()
        {
            // U-117: 16 u native (1024 px at 64); at the flight zoom (frame 20 u) it keeps its size, at the Saturn shot's 120 u frame it grows to 60 u.
            Assert.AreEqual(16f, Meridian.Space.SpaceBackdrop.TilePeriod(16f, 20f), 1e-5f);
            Assert.AreEqual(16f, Meridian.Space.SpaceBackdrop.TilePeriod(16f, 32f), 1e-5f, "exactly two repeats still");
            Assert.AreEqual(60f, Meridian.Space.SpaceBackdrop.TilePeriod(16f, 120f), 1e-5f);
            Assert.LessOrEqual(120f / Meridian.Space.SpaceBackdrop.TilePeriod(16f, 120f), 2f, "never more than two repeats across the frame");
        }

        [Test]
        public void PlanetDiscsImportBilinearOnAFullRectMesh()
        {
            // U-117: the discs' texture is bilinear and its sprite mesh the full rect (a tight mesh cut the bilinear alpha edge into texel stairs at 10x).
            int seen = 0;
            foreach (var path in new[] { "Assets/_Game/Art/planets/earth/luna_color.png", "Assets/_Game/Art/planets/saturn/disc_color.png", "Assets/_Game/Art/planets/mars/disc_color.png" })
            {
                var ti = UnityEditor.AssetImporter.GetAtPath(path) as UnityEditor.TextureImporter;
                if (ti == null) continue;
                seen++;
                Assert.AreEqual(FilterMode.Bilinear, ti.filterMode, path);
                var s = new UnityEditor.TextureImporterSettings();
                ti.ReadTextureSettings(s);
                Assert.AreEqual(SpriteMeshType.FullRect, s.spriteMeshType, path + ": full rect (U-117)");
                Assert.AreEqual(3f, ti.spritePixelsPerUnit, 1e-4f, path + ": PPU 3 (D-098)");
            }
            Assert.Greater(seen, 0, "B-119 discs in the project");
        }

        static string Sidecar(string body, string name)
        {
            var art = $"Assets/_Game/Art/planets/{body}/{name}.json";
            return File.Exists(art) ? art : $"Assets/_Game/Placeholders/planets/{body}/{name}.json";
        }

        [Test]
        public void EveryBodyHasADiscSheetAtTheSpaceScale()
        {
            var catalog = AssetDatabase.LoadAssetAtPath<PlanetCatalog>(PlanetConfigAuthoring.CatalogPath);
            Assert.NotNull(catalog, "PlanetCatalog");
            int bodies = 0;
            foreach (var b in SpaceLayout.Build(catalog))
            {
                if (b.isSun) continue; // U-116 (D-123): the Sun is a rig, not a disc sheet: TheSunResolvesToItsRigWithPartsAndSockets
                var json = b.parent != null ? Sidecar(b.parent, b.name) : Sidecar(b.name, "disc"); // a moon's sheet lives under its parent (D-098)
                if (b.parent != null && !File.Exists(json)) { TestContext.Out.WriteLine($"[MERIDIAN] moon {b.name}: no disc sheet yet ({json}); it keeps its spheroid"); continue; }
                Assert.IsTrue(File.Exists(json), $"{b.name}: {json} (art or placeholder)");
                var m = JsonUtility.FromJson<ArtImporter.SheetManifest>(File.ReadAllText(json));
                Assert.AreEqual("v3", m.style, b.name);
                Assert.AreEqual(3f, m.space_ppu, 1e-4f, $"{b.name}: space_ppu 3 (D-098)");
                Assert.AreEqual(3f, m.ppu, 1e-4f, $"{b.name}: imported at ppu 3");
                Assert.Greater(m.radius_u, 0f, $"{b.name}: radius_u");
                Assert.AreEqual(12, m.fps, $"{b.name}: 12 fps");
                var idle = m.animations.FirstOrDefault(a => a.name == "idle");
                Assert.NotNull(idle, $"{b.name}: an idle clip");
                Assert.IsTrue(idle.length == 9 || idle.length == 12, $"{b.name}: idle 9 or 12 frames (has {idle.length})");
                var png = json.Substring(0, json.Length - ".json".Length) + "_color.png";
                var ti = AssetImporter.GetAtPath(png) as TextureImporter;
                Assert.NotNull(ti, $"{b.name}: {png} imported");
                Assert.AreEqual(3f, ti.spritePixelsPerUnit, 1e-3f, $"{b.name}: the sheet imports at the disc scale, not PPU 128");
                Assert.AreEqual(SpriteImportMode.Multiple, ti.spriteImportMode, $"{b.name}: sliced");
                // The runtime draws radius_u units of drawing as b.radius: the scale is b.radius / radius_u, so a wrong radius_u mis-sizes the planet by that ratio.
                TestContext.Out.WriteLine($"[MERIDIAN] disc {b.name}: radius_u {m.radius_u}, visual radius {b.radius:F1} u, scale {b.radius / m.radius_u:F3}");
                bodies++;
            }
            Assert.GreaterOrEqual(bodies, 8, "the eight planets at least");
        }

        /// <summary>U-116 (D-123, B-137): the Sun key resolves to its rig: five parts, the 14-tongue ring, two prominences at their angles, the corona; the sheet sliced at the import ppu and addressed with its json; the pure clock.</summary>
        [Test]
        public void TheSunResolvesToItsRigWithPartsAndSockets()
        {
            const string json = "Assets/_Game/Art/planets/sun/disc_rig.json";
            Assert.IsTrue(File.Exists(json), json);
            var rig = Meridian.Space.SunView.Parse(File.ReadAllText(json));
            Assert.AreEqual(Meridian.Space.SunView.Key, rig.key);
            Assert.AreEqual(5, rig.parts.Length);
            foreach (var n in new[] { "body", "tongue", "prominence_a", "prominence_b", "corona" }) Assert.NotNull(System.Array.Find(rig.parts, p => p.name == n), n);
            Assert.AreEqual(14, rig.ring.count); Assert.AreEqual("tongue", rig.ring.part); Assert.AreEqual(0.97f, rig.ring.base_r, 1e-4f); Assert.AreEqual(12f, rig.ring.stepped_hz, 1e-4f);
            Assert.AreEqual(2, rig.ring.alt_scale.Length); Assert.AreEqual(0.62f, rig.ring.alt_scale[1], 1e-4f);
            Assert.AreEqual(1.42f, rig.corona.radius_r, 1e-4f); Assert.AreEqual("corona", rig.corona.part);
            Assert.AreEqual(2, rig.prominences.Length); Assert.AreEqual(100f, rig.prominences[0].angle_deg, 1e-3f); Assert.AreEqual(280f, rig.prominences[1].angle_deg, 1e-3f);
            // The sheet: sliced into the five parts at the import ppu; one sheet px draws draw_scale / space_ppu u, so the 928 px body spans 2 × R (309 u: R 300 + the flame bases).
            const string png = "Assets/_Game/Art/planets/sun/disc_rig_color.png";
            var ti = AssetImporter.GetAtPath(png) as TextureImporter;
            Assert.NotNull(ti, png); Assert.AreEqual(SpriteImportMode.Multiple, ti.spriteImportMode, "sliced into parts");
            var sprites = AssetDatabase.LoadAllAssetRepresentationsAtPath(png).OfType<Sprite>().ToList();
            Assert.AreEqual(5, sprites.Count, "five part sprites");
            var body = sprites.First(s => s.name == "body");
            float scale = Meridian.Space.SunView.PartScale(rig, body.pixelsPerUnit);
            Assert.AreEqual(928f * 2f / 3f, body.rect.width / body.pixelsPerUnit * scale, 0.5f, "the body's drawn width in Space units");
            float coronaWidth = 512f / body.pixelsPerUnit;
            Assert.AreEqual(2f * 1.42f * 300f, Meridian.Space.SunView.CoronaScale(rig, 300f, coronaWidth) * coronaWidth, 0.5f, "the corona spans 2 × 1.42 R");
            // The addresses the runtime probes: the sheet at the key, the json at key/json.
            var sheetEntry = ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID(png));
            Assert.NotNull(sheetEntry, "the Sun sheet is addressed"); Assert.AreEqual(Meridian.Space.SunView.Key, sheetEntry.address);
            var jsonEntry = ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID(json));
            Assert.NotNull(jsonEntry, "the Sun rig json is addressed"); Assert.AreEqual(Meridian.Space.SunView.Key + "/json", jsonEntry.address);
            // The clock: stepped at 12 Hz, the ring a slow spin, the pulse ± 8 % on the beat, the tongues evenly round the rim.
            Assert.AreEqual(Meridian.Space.SunView.Step(1.04f, 12f), Meridian.Space.SunView.Step(1.08f, 12f), 1e-6f, "one 12 Hz step");
            Assert.AreNotEqual(Meridian.Space.SunView.Step(1.04f, 12f), Meridian.Space.SunView.Step(1.13f, 12f));
            Assert.AreEqual(180f + 2f * 10f, Meridian.Space.SunView.TongueAngle(7, 14, 2f, 10f), 1e-4f);
            Assert.AreEqual(1.08f, Meridian.Space.SunView.Pulse(60f / 110f * 0.25f, 110f, 0.08f), 1e-4f, "the pulse peaks a quarter beat in");
            Assert.AreEqual(1f, Meridian.Space.SunView.Breathe(0f, 110f, 0.03f), 1e-6f);
        }

        [Test]
        public void SaturnRingsImportAtTheDiscScaleWithTheWobbleRig()
        {
            foreach (var part in new[] { "rings_back", "rings_front" })
            {
                var json = Sidecar("saturn", part);
                Assert.IsTrue(File.Exists(json), part);
                var m = JsonUtility.FromJson<ArtImporter.SheetManifest>(File.ReadAllText(json));
                Assert.AreEqual("v3", m.style);
                Assert.AreEqual(3f, m.space_ppu, 1e-4f, part + ": space_ppu 3");
                Assert.IsTrue(m.pivot != null && m.pivot.Length == 2 && Mathf.Approximately(m.pivot[0], 0.5f) && Mathf.Approximately(m.pivot[1], 0.5f), part + ": centre pivot");
                var ti = AssetImporter.GetAtPath(json.Substring(0, json.Length - ".json".Length) + "_color.png") as TextureImporter;
                Assert.NotNull(ti, part + " imported");
                Assert.AreEqual(3f, ti.spritePixelsPerUnit, 1e-3f, part + ": PPU 3, not 128 (cycle-243 review fix)");
                Assert.AreEqual(new Vector2(0.5f, 0.5f), ti.spritePivot, part + ": the sidecar pivot on a single image (U-104)");
            }
            var rig = RingWobble.Parse(File.ReadAllText(Sidecar("saturn", "disc_rig")));
            Assert.NotNull(rig?.wobble, "disc_rig.json wobble");
            Assert.IsTrue(RingWobble.Wobbles(rig.wobble, "rings_back") && RingWobble.Wobbles(rig.wobble, "rings_front"), "both rings wobble");
            Assert.AreEqual(0.04f, rig.wobble.scale_y, 1e-4f); Assert.AreEqual(1.5f, rig.wobble.rotate_deg, 1e-4f);
            Assert.AreEqual(110f, rig.wobble.beat_bpm, 1e-4f); Assert.AreEqual(12, rig.wobble.stepped_hz);
        }

        [Test]
        public void RingWobbleIsSteppedAt12HzAndBounded()
        {
            var w = new RingWobble.Wobble { parts = new[] { "rings_back" }, scale_y = 0.04f, rotate_deg = 1.5f, beat_bpm = 110f, stepped_hz = 12 };
            Assert.AreEqual((1f, 0f), RingWobble.At(0f, w), "at rest on the downbeat");
            Assert.AreEqual(RingWobble.At(0f, w), RingWobble.At(0.08f, w), "held within one 1/12 s step");
            Assert.AreNotEqual(RingWobble.At(0f, w), RingWobble.At(1.5f / 12f, w), "steps on the next drawing");
            float maxS = 0f, maxR = 0f;
            for (float t = 0f; t < 2f; t += 0.01f) { var (s, r) = RingWobble.At(t, w); maxS = Mathf.Max(maxS, Mathf.Abs(s - 1f)); maxR = Mathf.Max(maxR, Mathf.Abs(r)); }
            Assert.LessOrEqual(maxS, 0.04f + 1e-5f); Assert.LessOrEqual(maxR, 1.5f + 1e-5f);
            Assert.Greater(maxS, 0.03f, "it really breathes");
            Assert.AreEqual((1f, 0f), RingWobble.At(0.5f, null), "no rig: still");
        }

        [Test]
        public void ThrustStretchesAndACutSquashesAlongTheUpAxis()
        {
            var s = new SquashStretch();
            const float dt = 1f / 60f;
            for (int i = 0; i < 60; i++) s.Step(true, dt);
            Assert.That(s.Along, Is.EqualTo(SquashStretch.ThrustStretch).Within(0.5f).Percent, "thrust held: 1.15 stretch along the up axis");
            Assert.That(s.Across, Is.EqualTo(1f / s.Along).Within(1e-5f), "area-preserving across");
            Assert.AreEqual(new Vector3(s.Across, s.Along, 1f), s.LocalScale);
            float min = s.Along;
            for (int i = 0; i < 18; i++) { s.Step(false, dt); min = Mathf.Min(min, s.Along); }
            Assert.LessOrEqual(min, 0.95f, "the cut squashes toward 0.9");
            for (int i = 0; i < 60; i++) s.Step(false, dt);
            Assert.That(s.Along, Is.EqualTo(1f).Within(0.5f).Percent, "back to rest");
            Assert.AreEqual(1.15f, SquashStretch.ThrustStretch); Assert.AreEqual(0.9f, SquashStretch.CutSquash);
        }

        [Test]
        public void StarfieldSceneLayoutHasTheTiledStarfieldAndThreeNebulaCards()
        {
            var path = "Assets/_Game/Art/backgrounds/space/starfield/starfield.json";
            Assert.IsTrue(File.Exists(path), "B-120 starfield scene json");
            var layout = SceneLayout.Parse(File.ReadAllText(path));
            Assert.AreEqual(4, layout.layers.Length);
            var l0 = layout.layers.First(l => l.n == 0);
            Assert.IsTrue(l0.tile && l0.tile_y, "layer0 tiles in x and y (D-108)");
            Assert.AreEqual("starfield", l0.role);
            Assert.AreEqual(0.05f, l0.parallax, 1e-4f);
            float prev = l0.parallax;
            foreach (var l in layout.layers.Where(l => l.n > 0).OrderBy(l => l.n))
            {
                Assert.AreEqual("nebula", l.role, "layer" + l.n);
                Assert.IsFalse(l.tile, "a nebula card does not tile");
                Assert.Greater(l.parallax, prev, "nearer cards move more");
                prev = l.parallax;
            }
            for (int i = 0; i < 4; i++) Assert.IsTrue(File.Exists($"Assets/_Game/Art/backgrounds/space/starfield/layer{i}_color.png"), "layer" + i);
        }
            /// <summary>U-117 (2) / D-128: the near frame shows above 6 screen px per far texel and leaves below 5; the ship view sits far above, the far view far below.</summary>
        [Test]
        public void NearFrameSwapsAboveSixScreenPixelsPerTexelWithHysteresis()
        {
            Assert.AreEqual(6f, DiscSprite.NearAbove); Assert.AreEqual(5f, DiscSprite.NearBelow);
            Assert.AreEqual(1f, DiscSprite.Magnification(1080f, 180f, 3f), 1e-4f, "the far view: 1080 px over 360 units at 3 px/unit = 1 px per texel");
            Assert.AreEqual(32f, DiscSprite.Magnification(1080f, 5.625f, 3f), 1e-3f, "the ship view: 11.25 units tall = 32 px per texel");
            Assert.AreEqual(0f, DiscSprite.Magnification(1080f, 0f, 3f), "no camera height: no swap");
            Assert.IsFalse(DiscSprite.WantsNear(1f, false));
            Assert.IsFalse(DiscSprite.WantsNear(5.9f, false), "under the up threshold");
            Assert.IsTrue(DiscSprite.WantsNear(6f, false), "at it");
            Assert.IsTrue(DiscSprite.WantsNear(32f, false));
            Assert.IsTrue(DiscSprite.WantsNear(5.5f, true), "stays near until the down threshold");
            Assert.IsFalse(DiscSprite.WantsNear(4.9f, true), "and leaves under it");
            Assert.AreEqual("_near", DiscSprite.NearSuffix);
        }

        /// <summary>B-143 (D-128): the five near sidecars point at their far key, scale radius_px by scale_vs_far and import at space_ppu × k, one static frame.</summary>
        [Test]
        public void TheNearFramesPointAtTheirFarDiscAtTheirScale()
        {
            foreach (var far in new[] { "planets/mercury/disc", "planets/venus/disc", "planets/earth/disc", "planets/mars/disc", "planets/earth/luna" })
            {
                string nearPath = "Assets/_Game/Art/" + far + DiscSprite.NearSuffix + ".json";
                Assert.IsTrue(File.Exists(nearPath), nearPath);
                var near = JsonUtility.FromJson<DiscSprite.Sidecar>(File.ReadAllText(nearPath));
                var farJson = JsonUtility.FromJson<DiscSprite.Sidecar>(File.ReadAllText("Assets/_Game/Art/" + far + ".json"));
                Assert.AreEqual(far, near.near_of, "near_of");
                Assert.AreEqual(1, near.frames, "one static frame");
                Assert.Greater(near.scale_vs_far, 1f, "larger than the far frame");
                Assert.AreEqual(farJson.radius_u, near.radius_u, 1e-4f, "the same world radius: the transform scale is shared");
                Assert.AreEqual(farJson.space_ppu * near.scale_vs_far, near.space_ppu, 1e-3f, "ppu scales with the frame");
                Assert.AreEqual(near.space_ppu, near.ppu, 1e-4f);
                Assert.AreEqual(farJson.radius_px * near.scale_vs_far, near.radius_px, 0.6f, "radius_px scales with the frame");
                Assert.IsTrue(File.Exists("Assets/_Game/Art/" + far + DiscSprite.NearSuffix + "_color.png"), "the near colour map");
            }
        }

    }
}
