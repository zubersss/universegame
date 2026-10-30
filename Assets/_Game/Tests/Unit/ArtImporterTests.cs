using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Meridian.Art;
using Meridian.EditorTools;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.AddressableAssets.Settings;
using UnityEngine;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-005: one test per contract §6 rule. Runs against a sandbox copy of the Art/ and
    /// Placeholders/ roots so BLENDER's folder is never touched.
    /// </summary>
    public class ArtImporterTests
    {
        const string Sandbox = "Assets/_Game/Tests/Unit/_ArtSandbox";
        ArtImporter.Roots saved;

        [SetUp]
        public void SetUp()
        {
            saved = ArtImporter.Active;
            ArtImporter.Active = new ArtImporter.Roots
            {
                art = Sandbox + "/Art/",
                placeholders = Sandbox + "/Placeholders/",
                atlasFolder = Sandbox + "/Atlases/",
                groupPrefix = "test_",
                blenderManifest = Sandbox + "/manifest.json",
                materialRegistry = Sandbox + "/ArtMaterials.asset",
            };
            Directory.CreateDirectory(Sandbox);
        }

        [TearDown]
        public void TearDown()
        {
            // Real roots first: deleting the sandbox must not run the importer against sandbox roots.
            ArtImporter.Active = saved;
            AssetDatabase.DeleteAsset(Sandbox);
            var settings = ArtImporter.Settings;
            foreach (var g in settings.groups.Where(g => g != null && g.Name.StartsWith("test_")).ToList())
                settings.RemoveGroup(g);
            AssetDatabase.Refresh();
        }

        // ---------- helpers ----------

        static string Png(string path, int w, int h, Color32? fill = null)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var c = fill ?? new Color32(200, 100, 50, 255);
            tex.SetPixels32(Enumerable.Repeat(c, w * h).ToArray());
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            return path;
        }

        static void Import(params string[] paths)
        {
            foreach (var p in paths) AssetDatabase.ImportAsset(p, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
        }

        static TextureImporter Importer(string path) => (TextureImporter)AssetImporter.GetAtPath(path);

        static string Art(string rel) => ArtImporter.Active.art + rel;
        static string Ph(string rel) => ArtImporter.Active.placeholders + rel;

        static AddressableAssetEntry Entry(string path) =>
            ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID(path));

        static TextureImporterPlatformSettings Standalone(string path) => Importer(path).GetPlatformTextureSettings("Standalone");

        // ---------- §1 names ----------

        [Test]
        public void ParsesThreePartKeysAndMaps()
        {
            Assert.IsTrue(ArtRules.TryParse("ships/pilgrim/top_color.png", out var key, out var map));
            Assert.AreEqual("ships/pilgrim/top", key); Assert.AreEqual(ArtMap.Color, map);
            Assert.IsTrue(ArtRules.TryParse("terrain/mars/ice_normal.png", out key, out map));
            Assert.AreEqual(ArtMap.Normal, map);
            Assert.IsFalse(ArtRules.TryParse("ships/Pilgrim/top_color.png", out _, out _), "uppercase");
            Assert.IsFalse(ArtRules.TryParse("ships/top_color.png", out _, out _), "two segments");
            Assert.IsFalse(ArtRules.TryParse("ships/pilgrim/top_albedo.png", out _, out _), "unknown map");
            Assert.IsFalse(ArtRules.TryParse("weapons/x/base_color.png", out _, out _), "unknown category");
        }

        [Test]
        public void RejectsBadNameWithError()
        {
            var p = Png(Art("ships/pilgrim/Top-1_color.png"), 32, 32);
            LogAssert.Expect(LogType.Error, new Regex(@"\[ArtImporter\] Rejected .*Top-1_color\.png: name must be"));
            Import(p);
            Assert.IsNull(Entry(p), "rejected file gets no address");
        }

        // ---------- §2 limits ----------

        [Test]
        public void RejectsOversizeDimensionsWithError()
        {
            var p = Png(Art("props/common/huge_color.png"), 2050, 16);
            LogAssert.Expect(LogType.Error, new Regex(@"Rejected .*huge_color\.png: 2050×16 exceeds 2048×2048"));
            Import(p);
            Assert.IsNull(Entry(p));
        }

        [Test]
        public void FileSizeLimitIsFourMegabytes()
        {
            Assert.IsNull(ArtRules.Validate(4L * 1024 * 1024, 2048, 1024));
            StringAssert.Contains("4 MB", ArtRules.Validate(4L * 1024 * 1024 + 1, 64, 64));
        }

        // ---------- §6 import settings ----------

        [Test]
        public void ColorIsSpritePpu128BilinearBc7Srgb()
        {
            var p = Png(Art("ships/pilgrim/top_color.png"), 64, 64);
            Import(p);
            var ti = Importer(p);
            Assert.AreEqual(TextureImporterType.Sprite, ti.textureType);
            Assert.AreEqual(128f, ti.spritePixelsPerUnit);
            Assert.AreEqual(FilterMode.Bilinear, ti.filterMode);
            Assert.IsTrue(ti.sRGBTexture);
            var s = Standalone(p);
            Assert.IsTrue(s.overridden);
            Assert.AreEqual(TextureImporterFormat.BC7, s.format);
            Assert.AreEqual(100, s.compressionQuality);
        }

        [Test]
        public void NormalIsNormalMapBc5Linear()
        {
            var p = Png(Art("ships/pilgrim/top_normal.png"), 64, 64, new Color32(128, 128, 255, 255));
            Import(p);
            var ti = Importer(p);
            Assert.AreEqual(TextureImporterType.NormalMap, ti.textureType);
            Assert.IsFalse(ti.sRGBTexture);
            Assert.AreEqual(TextureImporterFormat.BC5, Standalone(p).format);
        }

        [Test]
        public void MaskIsLinearAndEmissionIsSrgb()
        {
            var mask = Png(Art("ships/pilgrim/top_mask.png"), 32, 32);
            var em = Png(Art("ships/pilgrim/top_emission.png"), 32, 32);
            Import(mask, em);
            Assert.IsFalse(Importer(mask).sRGBTexture);
            Assert.IsTrue(Importer(em).sRGBTexture);
        }

        [Test]
        public void MipsAndMeshTypePerCategory()
        {
            var ship = Png(Art("ships/pilgrim/side_color.png"), 64, 32);
            var fx = Png(Art("fx/thruster/base_color.png"), 64, 64);
            Import(ship, fx);
            var s = new TextureImporterSettings();
            Importer(ship).ReadTextureSettings(s);
            Assert.IsTrue(Importer(ship).mipmapEnabled, "ships have mips");
            Assert.AreEqual(SpriteMeshType.Tight, s.spriteMeshType, "ships are tight");
            Importer(fx).ReadTextureSettings(s);
            Assert.IsFalse(Importer(fx).mipmapEnabled, "fx have no mips");
            Assert.AreEqual(SpriteMeshType.FullRect, s.spriteMeshType, "fx are full rect");
        }

        [Test]
        public void PivotIsBottomCenterForPropsAndCenterForShips()
        {
            var prop = Png(Art("props/common/crate_color.png"), 64, 128);
            var ship = Png(Art("ships/pilgrim/top_color.png"), 64, 64);
            Import(prop, ship);
            Assert.AreEqual(new Vector2(0.5f, 8f / 128f), Importer(prop).spritePivot);
            Assert.AreEqual(new Vector2(0.5f, 0.5f), Importer(ship).spritePivot);
        }

        [Test]
        public void PivotComesFromBlenderManifestWhenListed()
        {
            File.WriteAllText(ArtImporter.Active.blenderManifest,
                "{\"assets\":[{\"key\":\"props/common/calibration\",\"pivot\":[0.5,0.0555556]}]}");
            var p = Png(Art("props/common/calibration_color.png"), 160, 288);
            Import(p);
            Assert.That(Importer(p).spritePivot.y, Is.EqualTo(0.0555556f).Within(1e-6f));
        }

        [Test]
        public void SecondaryTexturesLinkedFromSiblings()
        {
            var n = Png(Art("ships/pilgrim/top_normal.png"), 64, 64, new Color32(128, 128, 255, 255));
            var e = Png(Art("ships/pilgrim/top_emission.png"), 64, 64);
            var m = Png(Art("ships/pilgrim/top_mask.png"), 64, 64);
            var c = Png(Art("ships/pilgrim/top_color.png"), 64, 64);
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            var names = Importer(c).secondarySpriteTextures.Select(t => t.name).ToArray();
            CollectionAssert.AreEquivalent(new[] { "_NormalMap", "_EmissionMap", "_MaskTex" }, names);
            Assert.AreEqual(AssetDatabase.LoadAssetAtPath<Texture2D>(n),
                Importer(c).secondarySpriteTextures.First(t => t.name == "_NormalMap").texture);
        }

        // ---------- §5 frame sheets ----------

        [Test]
        public void FrameSheetSlicedFromJson()
        {
            var json = Art("creatures/earth/stag.json");
            Directory.CreateDirectory(Path.GetDirectoryName(json));
            File.WriteAllText(json, "{\"key\":\"creatures/earth/stag\",\"frame_width\":32,\"frame_height\":32," +
                                    "\"columns\":3,\"frames\":5,\"gutter\":4,\"pivot\":[0.5,0.0]}");
            // 3 columns × 2 rows with 4 px gutters between frames: 3*32+2*4 = 104, 2*32+4 = 68.
            var c = Png(Art("creatures/earth/stag_color.png"), 104, 68);
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Import(c);
            Assert.AreEqual(SpriteImportMode.Multiple, Importer(c).spriteImportMode);
            var sprites = AssetDatabase.LoadAllAssetsAtPath(c).OfType<Sprite>().OrderBy(s => s.name).ToArray();
            Assert.AreEqual(5, sprites.Length);
            var first = sprites.First(s => s.name == "stag_0");
            Assert.AreEqual(new Rect(0, 36, 32, 32), first.rect, "frame 0 at top-left");
            var fourth = sprites.First(s => s.name == "stag_4");
            Assert.AreEqual(new Rect(36, 0, 32, 32), fourth.rect, "frame 4 = row 1, col 1");
        }

        [Test]
        public void TerrainSheetSlicedInto47TileGridWithoutJson()
        {
            var c = TerrainSheet(Art("terrain/earth/soil_color.png"), 47);
            Import(c);
            var sprites = AssetDatabase.LoadAllAssetsAtPath(c).OfType<Sprite>().ToArray();
            Assert.AreEqual(47, sprites.Length);
            // Cells are cut 1 texel inside the 128 px grid (no neighbor bleed); tiles scale them back to 1 m.
            Assert.AreEqual(new Rect(1, 897, 126, 126), sprites.First(s => s.name == "soil_0").rect, "cell 0 top-left");
            // Cell 46 = row 5, column 6.
            Assert.AreEqual(new Rect(769, 257, 126, 126), sprites.First(s => s.name == "soil_46").rect);
            Assert.AreEqual(128f, sprites[0].pixelsPerUnit);
        }

        [Test]
        public void TerrainVariantCellsAreSlicedOnlyWhenTheyHoldArt()
        {
            var full = TerrainSheet(Art("terrain/mars/basalt_color.png"), 63);
            var partial = TerrainSheet(Art("terrain/mars/ice_color.png"), 47 + 5);
            Import(full, partial);
            Assert.AreEqual(63, AssetDatabase.LoadAllAssetsAtPath(full).OfType<Sprite>().Count(), "16 variants of tile 46 (D-020)");
            Assert.AreEqual(52, AssetDatabase.LoadAllAssetsAtPath(partial).OfType<Sprite>().Count(), "only the filled variant cells");
            Assert.AreEqual(new Rect(769, 1, 126, 126),
                AssetDatabase.LoadAllAssetsAtPath(full).OfType<Sprite>().First(s => s.name == "basalt_62").rect, "cell 62 = row 7 (bottom row), column 6");
        }

        /// <summary>A 1024² terrain sheet with cells [0, filled) opaque and the rest transparent.</summary>
        static string TerrainSheet(string path, int filled)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var px = new Color32[1024 * 1024];
            for (int cell = 0; cell < filled; cell++)
            {
                int x0 = cell % 8 * 128, yTop = 1024 - cell / 8 * 128;
                for (int y = yTop - 128; y < yTop; y++)
                for (int x = x0; x < x0 + 128; x++)
                    px[y * 1024 + x] = new Color32(120, 90, 60, 255);
            }
            var tex = new Texture2D(1024, 1024, TextureFormat.RGBA32, false);
            tex.SetPixels32(px);
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            return path;
        }

        [Test]
        public void SheetCategoryWithoutJsonLogsClearError()
        {
            var c = Png(Art("characters/surveyor/base_color.png"), 64, 64);
            LogAssert.Expect(LogType.Error, new Regex(@"frame sheet has no base\.json"));
            Import(c);
        }

        // ---------- Addressables + atlas ----------

        [Test]
        public void AddressEqualsKeyInContractGroup()
        {
            var c = Png(Art("terrain/mars/ice_color.png"), 1024, 1024);
            Import(c);
            var e = Entry(c);
            Assert.NotNull(e, "addressable");
            Assert.AreEqual("terrain/mars/ice", e.address);
            Assert.AreEqual("test_planet_mars", e.parentGroup.Name);
        }

        [Test]
        public void AddedToContractAtlas()
        {
            var c = Png(Art("ships/pilgrim/top_color.png"), 64, 64);
            Import(c);
            var atlas = ArtImporter.AtlasPath("common");
            Assert.IsTrue(File.Exists(atlas), "common atlas created");
            StringAssert.Contains(AssetDatabase.AssetPathToGUID(c), File.ReadAllText(atlas));
        }

        [Test]
        public void GroupAndAtlasMappingFollowsContract()
        {
            Assert.AreEqual("common", ArtRules.GroupFor("ships/pilgrim/top"));
            Assert.AreEqual("planet_earth", ArtRules.GroupFor("terrain/earth/soil"));
            Assert.AreEqual("planet_mars", ArtRules.GroupFor("backgrounds/mars/layer0"));
            Assert.AreEqual("space", ArtRules.GroupFor("backgrounds/space/layer0"));
            Assert.AreEqual("space", ArtRules.GroupFor("planets/earth/surface"));
            Assert.AreEqual("common", ArtRules.GroupFor("props/common/calibration"));
            Assert.AreEqual("icons", ArtRules.GroupFor("icons/iron/base"));
            Assert.IsNull(ArtRules.AtlasFor("planets/earth/surface"));
            Assert.IsNull(ArtRules.AtlasFor("backgrounds/earth/layer1"));
            Assert.AreEqual("planet_earth", ArtRules.AtlasFor("creatures/earth/stag"));
            Assert.AreEqual("common", ArtRules.AtlasFor("fx/dust/base"));
        }

        // ---------- U-019 material assignment ----------

        [Test]
        public void KeyWithEmissionMapGetsSpriteLitEmissive()
        {
            var e = Png(Art("ships/pilgrim/side_emission.png"), 64, 32, new Color32(255, 160, 40, 255));
            var c = Png(Art("ships/pilgrim/side_color.png"), 64, 32);
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Import(c);
            var reg = ArtImporter.Registry();
            Assert.IsTrue(reg.IsEmissive("ships/pilgrim/side"), "registered as emissive");
            Assert.NotNull(reg.litEmissive);
            Assert.AreEqual("MERIDIAN/Sprite_LitEmissive", reg.litEmissive.shader.name);

            var plain = Png(Art("ships/pilgrim/top_color.png"), 64, 64);
            Import(plain);
            Assert.IsFalse(reg.IsEmissive("ships/pilgrim/top"), "no emission map → plain lit");

            AssetDatabase.DeleteAsset(e);
            Assert.IsFalse(ArtImporter.Registry().IsEmissive("ships/pilgrim/side"), "emission removed → back to plain lit");
        }

        [Test]
        public void RealRegistryMarksEveryKeyWithAnEmissionMap()
        {
            ArtImporter.Active = saved;
            var reg = AssetDatabase.LoadAssetAtPath<Meridian.Rendering.ArtMaterials>(saved.materialRegistry);
            Assert.NotNull(reg, "Settings/Resources/ArtMaterials.asset");
            foreach (var key in new[] { "props/common/calibration", "ships/pilgrim/side", "planets/sun/surface" })
                Assert.IsTrue(reg.IsEmissive(key), key);
            foreach (var file in Directory.GetFiles(saved.art.TrimEnd('/'), "*_emission.png", SearchOption.AllDirectories))
            {
                var rel = file.Replace('\\', '/').Substring(saved.art.Length);
                Assert.IsTrue(ArtRules.TryParse(rel, out var key, out _));
                Assert.IsTrue(reg.IsEmissive(key), $"{key} has an emission map");
            }
        }

        // ---------- placeholder retirement ----------

        [Test]
        public void RealArtRetiresPlaceholderAndDeletionRestoresIt()
        {
            const string key = "props/common/calibration";
            var ph = Png(Ph("props/common/calibration_color.png"), 64, 64, new Color32(255, 0, 255, 255));
            Import(ph);
            Assert.AreEqual(key, Entry(ph)?.address, "placeholder addressed first");

            var art = Png(Art("props/common/calibration_color.png"), 64, 64);
            Import(art);
            Assert.AreEqual(key, Entry(art)?.address, "address moved to the real art");
            Assert.IsNull(Entry(ph), "placeholder retired");
            StringAssert.DoesNotContain(AssetDatabase.AssetPathToGUID(ph), File.ReadAllText(ArtImporter.AtlasPath("common")));

            AssetDatabase.DeleteAsset(art);
            Assert.AreEqual(key, Entry(ph)?.address, "placeholder restored when the art is removed");
        }

        // ---------- key ↔ placeholder coverage (real roots) ----------

        [Test]
        public void EveryM1KeyHasAPlaceholderOrRealArtWithItsAddress()
        {
            ArtImporter.Active = saved;
            foreach (var key in ArtKeys.M1)
            {
                var art = ArtImporter.ArtColorPath(key);
                var ph = ArtImporter.PlaceholderColorPath(key);
                Assert.IsTrue(File.Exists(ph), $"placeholder missing for {key}");
                var addressed = File.Exists(art) ? art : ph;
                Assert.AreEqual(key, Entry(addressed)?.address, $"{key} addressed at {addressed}");
                if (ArtRules.RuleFor(key).lit)
                    Assert.IsTrue(File.Exists(ArtRules.SiblingPath(ph, ArtMap.Normal)), $"{key} placeholder normal");
            }
        }
    }
}
