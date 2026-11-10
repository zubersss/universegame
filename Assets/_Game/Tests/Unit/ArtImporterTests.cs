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
            // U-060: non-power-of-two art never gets mips (NPOT + mips is stored uncompressed).
            var npot = Png(Art("ships/pilgrim/top_color.png"), 96, 32);
            Import(npot);
            Assert.IsFalse(Importer(npot).mipmapEnabled, "NPOT ship art: no mips, so it compresses to BC7");
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

        // ---------- U-104 (B-121 handoffs): single-image pivots, parts sheets, the tile flag ----------

        [Test]
        public void SingleImageHonoursItsSidecarPivot()
        {
            // (a) ui/hud/escape_sign wants [0.5, 0]: a v3 sidecar pivot applies to a single image, not only to frame sheets.
            var json = Art("ui/hud/escape_sign.json");
            Directory.CreateDirectory(Path.GetDirectoryName(json));
            File.WriteAllText(json, "{\"key\":\"ui/hud/escape_sign\",\"style\":\"v3\",\"pivot\":[0.5,0.0]}");
            var c = Png(Art("ui/hud/escape_sign_color.png"), 64, 32);
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Import(c);
            Assert.AreEqual(SpriteImportMode.Single, Importer(c).spriteImportMode);
            Assert.AreEqual(new Vector2(0.5f, 0f), Importer(c).spritePivot, "the sidecar pivot, bottom centre");
            var plain = Png(Art("ui/hud/plain_color.png"), 32, 32);
            File.WriteAllText(Art("ui/hud/plain.json"), "{\"key\":\"ui/hud/plain\",\"style\":\"v3\"}");
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Import(plain);
            Assert.AreEqual(new Vector2(0.5f, 0.5f), Importer(plain).spritePivot, "no sidecar pivot: the centre");
        }

        [Test]
        public void PartsSheetIsSlicedLikeARigSetAndItsJsonAddressed()
        {
            // (b) ui/hud/gauges: one sheet with `parts` (rects bottom-left + pivots) and `needles`; sliced into its sprites, the json addressed for the HUD.
            var json = Art("ui/hud/gauges.json");
            Directory.CreateDirectory(Path.GetDirectoryName(json));
            File.WriteAllText(json, "{\"key\":\"ui/hud/gauges\",\"style\":\"v3\",\"parts\":[" +
                "{\"name\":\"suit_dial\",\"rect\":[0,0,64,64],\"pivot\":[0.5,0.5]}," +
                "{\"name\":\"suit_needle\",\"rect\":[64,0,16,48],\"pivot\":[0.5,0.2]}," +
                "{\"name\":\"oxygen_dial\",\"rect\":[80,0,48,48],\"pivot\":[0.5,0.5]}]," +
                "\"needles\":[{\"part\":\"suit_needle\",\"min_deg\":-120,\"max_deg\":120,\"hub\":[32,20],\"danger_below\":0.2}]}");
            var c = Png(Art("ui/hud/gauges_color.png"), 128, 64);
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Import(c);
            Assert.AreEqual(SpriteImportMode.Multiple, Importer(c).spriteImportMode);
            var sprites = AssetDatabase.LoadAllAssetsAtPath(c).OfType<Sprite>().OrderBy(s => s.name).ToArray();
            CollectionAssert.AreEquivalent(new[] { "oxygen_dial", "suit_dial", "suit_needle" }, sprites.Select(s => s.name).ToArray());
            var needle = sprites.First(s => s.name == "suit_needle");
            Assert.AreEqual(new Rect(64, 0, 16, 48), needle.rect, "rect from the json, bottom-left origin");
            Assert.That(needle.pivot.x / needle.rect.width, Is.EqualTo(0.5f).Within(1e-3f));
            Assert.That(needle.pivot.y / needle.rect.height, Is.EqualTo(0.2f).Within(1e-3f), "the part's own pivot");
            var entry = ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID(json));
            Assert.NotNull(entry, "the json is addressed (the HUD reads the needle ranges from it)");
            Assert.AreEqual("ui/hud/gauges/json", entry.address);
        }

        [Test]
        public void TileFlagMakesASingleImageRepeat()
        {
            // (c) escape_line.json carries "tile": true: the dotted line repeats along the Escape Line.
            var json = Art("ui/hud/escape_line.json");
            Directory.CreateDirectory(Path.GetDirectoryName(json));
            File.WriteAllText(json, "{\"key\":\"ui/hud/escape_line\",\"style\":\"v3\",\"tile\":true}");
            var c = Png(Art("ui/hud/escape_line_color.png"), 64, 16);
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Import(c);
            Assert.AreEqual(TextureWrapMode.Repeat, Importer(c).wrapMode, "tile: true repeats");
            var settings = new TextureImporterSettings();
            Importer(c).ReadTextureSettings(settings);
            Assert.AreEqual(SpriteMeshType.FullRect, settings.spriteMeshType, "a tiled sprite keeps its full rect");
        }

        /// <summary>U-205 (D-192 amended): a dug cell's back wall is the one colour map that imports uncompressed (RGBA32): its paper grain
        /// cost a fifth more a frame in BC7 on the integrated GPU. A fill beside it stays BC7.</summary>
        [Test]
        public void ABackWallImportsUncompressedAndAFillStaysBc7()
        {
            Assert.IsTrue(Meridian.Art.ArtKeys.IsBackWall("terrain/earth/back_wall_t3"), "by key");
            Assert.IsTrue(Meridian.Art.ArtKeys.IsBackWall("Assets/_Game/Art/terrain/mars/back_wall_t5_color.png"), "by path");
            Assert.IsFalse(Meridian.Art.ArtKeys.IsBackWall("terrain/earth/ground_fill_t3"));
            Assert.IsFalse(Meridian.Art.ArtKeys.IsBackWall("props/earth/back_wall_t3"), "only under terrain/");
            Assert.IsFalse(Meridian.Art.ArtKeys.IsBackWall(null));
            var wallJson = Art("terrain/earth/back_wall_t3.json");
            Directory.CreateDirectory(Path.GetDirectoryName(wallJson));
            File.WriteAllText(wallJson, "{\"key\":\"terrain/earth/back_wall_t3\",\"style\":\"v3\",\"ppu\":64}");
            File.WriteAllText(Art("terrain/earth/ground_fill_t3.json"), "{\"key\":\"terrain/earth/ground_fill_t3\",\"style\":\"v3\",\"ppu\":64}");
            var wall = Png(Art("terrain/earth/back_wall_t3_color.png"), 64, 64);
            var fill = Png(Art("terrain/earth/ground_fill_t3_color.png"), 64, 64);
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Import(wall, fill);
            var w = Standalone(wall);
            Assert.IsTrue(w.overridden);
            Assert.AreEqual(TextureImporterFormat.RGBA32, w.format, "the wall: uncompressed");
            Assert.AreEqual(TextureImporterCompression.Uncompressed, w.textureCompression);
            Assert.IsFalse(Importer(wall).mipmapEnabled, "a v3 sprite: no mips");
            Assert.AreEqual(TextureImporterFormat.BC7, Standalone(fill).format, "the fill: BC7 as every other colour map");
            Assert.AreEqual(0, ArtImporter.ReimportBackWalls(), "nothing left to re-import");
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
        public void SheetPpuSetsWorldSizeAndDefaultsTo128()
        {
            var json = Art("creatures/earth/stag.json");
            Directory.CreateDirectory(Path.GetDirectoryName(json));
            File.WriteAllText(json, "{\"key\":\"creatures/earth/stag\",\"frame_width\":32,\"frame_height\":32," +
                                    "\"columns\":3,\"frames\":5,\"gutter\":4,\"pivot\":[0.5,0.0],\"ppu\":104}");
            var c = Png(Art("creatures/earth/stag_color.png"), 104, 68);
            var json2 = Art("creatures/earth/wolf.json");
            File.WriteAllText(json2, "{\"key\":\"creatures/earth/wolf\",\"frame_width\":32,\"frame_height\":32," +
                                     "\"columns\":3,\"frames\":5,\"gutter\":4,\"pivot\":[0.5,0.0]}");
            var c2 = Png(Art("creatures/earth/wolf_color.png"), 104, 68);
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Import(c, c2);
            Assert.AreEqual(104f, Importer(c).spritePixelsPerUnit, "sheet ppu honored");
            var stag = AssetDatabase.LoadAllAssetsAtPath(c).OfType<Sprite>().First(s => s.name == "stag_0");
            Assert.AreEqual(32f / 104f, stag.bounds.size.x, 1e-4f, "world size = px / 104");
            Assert.AreEqual(128f, Importer(c2).spritePixelsPerUnit, "no ppu: 128");
            var wolf = AssetDatabase.LoadAllAssetsAtPath(c2).OfType<Sprite>().First(s => s.name == "wolf_0");
            Assert.AreEqual(32f / 128f, wolf.bounds.size.x, 1e-4f, "world size = px / 128");
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
            var c = Png(Art("characters/calibration/base_color.png"), 64, 64); // U-169: any characters/ sheet in the test root (no v2 surveyor)
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
            // U-091 (D-110): a sheet more than one planet uses lives in common, unpacked; import and run time share one table.
            Assert.AreEqual("common", ArtRules.GroupFor("terrain/earth/snow"), "a shared terrain sheet lives in common");
            Assert.AreEqual("common", ArtRules.GroupFor("terrain/jupiter/floe_ice"));
            Assert.IsNull(ArtRules.AtlasFor("terrain/earth/snow"), "and stays unpacked");
            Assert.AreEqual("planet_earth", ArtRules.GroupFor("flora/earth/rigset"), "flora follows its planet");
            foreach (var key in new[] { "terrain/earth/snow", "flora/earth/rigset", "creatures/mars/skitter", "props/common/calibration", "backgrounds/space/layer0", "ui/hud/gauges" })
                Assert.AreEqual(ArtRules.GroupFor(key), Meridian.Perf.Residency.GroupOf(key), key + ": one group table");
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
                if (ArtImporter.IsModelKey(key)) continue; // v5: a model's (or shared atlas's) emission lives in its own material (ModelMaterials)
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
        public void BlockMaterialPathsAreRecognised()
        {
            Assert.IsTrue(ArtRules.IsBlockTexture("terrain/earth/soil/top_color.png", out var p, out var m, out var f, out var map));
            Assert.AreEqual(("earth", "soil", "top", ArtMap.Color), (p, m, f, map));
            Assert.IsTrue(ArtRules.IsBlockTexture("terrain/earth/grass/side_normal.png", out _, out m, out f, out map));
            Assert.AreEqual(("grass", "side", ArtMap.Normal), (m, f, map));
            Assert.IsTrue(ArtRules.IsBlockTexture("terrain/earth/backwall_mask.png", out _, out m, out f, out map));
            Assert.AreEqual(("backwall", "wall", ArtMap.Mask), (m, f, map));
            Assert.IsFalse(ArtRules.IsBlockTexture("terrain/earth/soil_color.png", out _, out _, out _, out _), "the v1 tile sheet is not a block material");
            Assert.IsFalse(ArtRules.IsBlockTexture("terrain/earth/soil/front_color.png", out _, out _, out _, out _), "only top/side faces");
        }

        [Test]
        public void EveryM1KeyHasAPlaceholderOrRealArtWithItsAddress()
        {
            ArtImporter.Active = saved;
            foreach (var key in ArtKeys.M1)
            {
                var art = ArtImporter.ArtColorPath(key);
                var ph = ArtImporter.PlaceholderColorPath(key);
                Assert.IsTrue(File.Exists(ph), $"placeholder missing for {key}");
                // ArtImporter v5 (U-075): a key whose art is a model (.glb beside the maps) stays on its 2D placeholder
                // until the model views read models; its colour map is a model texture, not a sprite.
                bool model = ArtImporter.IsModelKey(key);
                var addressed = File.Exists(art) && !model ? art : ph;
                Assert.AreEqual(key, Entry(addressed)?.address, $"{key} addressed at {addressed}");
                if (ArtRules.RuleFor(key).lit)
                    Assert.IsTrue(File.Exists(ArtRules.SiblingPath(ph, ArtMap.Normal)), $"{key} placeholder normal");
            }
        }

        [Test]
        public void ModelMapsAreCappedByDimensionNotByFileSize()
        {
            // D-072 (P-34): a 2048² model atlas may exceed 4 MB as PNG (the flora atlases do); sheets keep the 4 MB cap.
            Assert.IsNull(ArtRules.Validate(12L * 1024 * 1024, 2048, 2048, modelMap: true), "a 12 MB 2048² model map passes");
            StringAssert.Contains("4 MB", ArtRules.Validate(12L * 1024 * 1024, 2048, 2048, modelMap: false), "a sheet keeps the cap");
            StringAssert.Contains("exceeds", ArtRules.Validate(1024, 4096, 2048, modelMap: true), "the dimension cap stays for model maps");
            // IsModelKey (v8) in the sandboxed Art root: a folder with a .glb makes its "atlas" a model key.
            Directory.CreateDirectory(Art("props/test_flora"));
            File.WriteAllBytes(Art("props/test_flora/leaf.glb"), new byte[0]);
            Assert.IsTrue(ArtImporter.IsModelKey("props/test_flora/atlas"), "a model folder's atlas is a model key");
            Assert.IsTrue(ArtImporter.IsModelKey("props/test_flora/leaf"), "a key with its own .glb");
            Assert.IsFalse(ArtImporter.IsModelKey("props/test_flora/other"), "a sheet key in the same folder is not");
        }

        [Test]
        public void PlanetTexturesAreCappedAt512MegabytesStoredPerPlanet()
        {
            // U-091 (D-089): which keys are a planet's stage layers (labels), which planet a texture counts against, the stored estimate, the cap.
            Assert.IsTrue(ArtRules.IsStageLayer("backgrounds/earth_forest/ridge_mid", out var p) && p == "earth", "a region band");
            Assert.IsTrue(ArtRules.IsStageLayer("backgrounds/earth/clouds", out p) && p == "earth", "the planet's cloud strip");
            Assert.IsTrue(ArtRules.IsStageLayer("props/mars_foreground/atlas", out p) && p == "mars", "the foreground atlas");
            Assert.IsFalse(ArtRules.IsStageLayer("backgrounds/space/layer0", out _), "space is not a planet");
            Assert.IsFalse(ArtRules.IsStageLayer("props/earth_flora/tree_oak", out _), "flora is not a layer");
            Assert.AreEqual(2048L * 2048L * 4L / 3L, ArtRules.StoredBytes(2048, 2048), "BC7/BC5 with mips: 1 byte per texel × 4/3");
            Assert.AreEqual(512L * 1024L * 1024L, ArtRules.PlanetTextureCapBytes);
            Assert.AreEqual("earth", ArtRules.PlanetOfTexture("terrain/earth/soil_color.png"));
            Assert.AreEqual("mars", ArtRules.PlanetOfTexture("props/mars_flora/cactus_normal.png"), "a suffixed planet group counts for its planet");
            Assert.AreEqual("earth", ArtRules.PlanetOfTexture("backgrounds/earth_forest/ridge_mid_color.png"));
            Assert.IsNull(ArtRules.PlanetOfTexture("terrain/earth/snow_color.png"), "a shared sheet counts for no planet (common)");
            Assert.IsNull(ArtRules.PlanetOfTexture("backgrounds/space/layer0_color.png"));
            Assert.IsNull(ArtRules.PlanetOfTexture("ships/pilgrim/side_color.png"));
            Assert.IsNull(ArtRules.PlanetOfTexture("icons/iron/base_color.png"));
            // The sandbox has no planet textures: the sum is 0 and a first 2048² sheet passes; the last kilobyte does not.
            Assert.AreEqual(0L, ArtImporter.PlanetTextureBytes("earth", ""));
            Assert.IsFalse(ArtRules.OverPlanetCap(0L, 2048, 2048));
            Assert.IsTrue(ArtRules.OverPlanetCap(ArtRules.PlanetTextureCapBytes - 1024L, 64, 64));
            Assert.IsFalse(ArtRules.OverPlanetCap(ArtRules.PlanetTextureCapBytes - ArtRules.StoredBytes(64, 64), 64, 64), "exactly at the cap passes");
        }

        [Test]
        public void OverCapTexturesAreRejectedAndNeverAddressed()
        {
            // U-091 (D-089): with the cap lowered to two 64² sheets, the third Earth sheet BY PATH is rejected whatever the
            // import order, and a rejected texture is never addressed.
            long one = ArtRules.StoredBytes(64, 64);
            ArtRules.PlanetTextureCapOverride = one * 2;
            try
            {
                var a = Png(Art("props/earth_flora/aa_color.png"), 64, 64);
                var b = Png(Art("props/earth_flora/bb_color.png"), 64, 64);
                var c = Png(Art("props/earth_flora/cc_color.png"), 64, 64);
                LogAssert.Expect(LogType.Error, new Regex(@"\[ArtImporter\] Rejected .*cc_color\.png: earth's textures up to this file \(path order\) would store"));
                Import(c, a, b); // the last file by path is the one over the cap, not the last one imported
                Assert.NotNull(ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID(a)), "aa addressed");
                Assert.NotNull(ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID(b)), "bb addressed");
                Assert.IsNull(ArtImporter.Settings.FindAssetEntry(AssetDatabase.AssetPathToGUID(c)), "cc over the cap: never addressed");
                Assert.AreEqual(one * 3, ArtImporter.PlanetTextureBytes("earth", ""), "the three sheets on disk count");
                Assert.AreEqual(one * 2, ArtImporter.PlanetTextureBytes("earth", c), "except one path");
                Assert.AreEqual(0L, ArtImporter.PlanetTextureBytes("mars", ""), "Earth's sheets count for Earth only");
            }
            finally { ArtRules.PlanetTextureCapOverride = null; }
        }

        [Test]
        public void ModelMapsStreamMipsAndAnAtlasImportedBeforeItsModelsIsReimported()
        {
            // P-36 (U-077): a model map streams its mips, a sheet does not, belt asteroids never (RenderMeshInstanced).
            var atlas = Png(Art("props/test_flora/atlas_color.png"), 64, 64);
            var sheet = Png(Art("ships/pilgrim/side_color.png"), 64, 32);
            Import(atlas, sheet);
            Assert.AreEqual(TextureImporterType.Sprite, Importer(atlas).textureType, "no model yet: the atlas imports as a sheet");
            Assert.IsFalse(Importer(sheet).streamingMipmaps, "sheets do not stream");
            // B-101: the models land one commit after their atlas; the .glb import re-imports the atlas as model maps.
            File.WriteAllBytes(Art("props/test_flora/leaf.glb"), new byte[0]);
            Assert.AreEqual(1, ArtImporter.EnsureModelMapsImported("props/test_flora/leaf"), "the atlas is re-imported once its folder has a model");
            var ti = Importer(atlas);
            Assert.AreEqual(TextureImporterType.Default, ti.textureType, "a model map, not a sprite");
            Assert.IsTrue(ti.mipmapEnabled && ti.streamingMipmaps, "model maps stream their mips");
            Assert.AreEqual(0, ArtImporter.EnsureModelMapsImported("props/test_flora/leaf"), "nothing left to re-import");
            Assert.IsFalse(ArtImporter.StreamsMips("props/space/asteroid_01"), "belt rocks draw without a renderer");
        }
    }
}
