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
                if (b.isSun) continue; // the Sun keeps its lit spheroid and glow (no disc sheet, B-119)
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
    }
}
