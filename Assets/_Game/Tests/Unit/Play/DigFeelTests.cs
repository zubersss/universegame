using System.Collections;
using Meridian.Audio;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
using Meridian.Planets;
using Meridian.Player;
using Meridian.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-195 (D-183, the owner's 0.6.0 playtest): a stroke that opens ground throws 4-8 clods (4 for one cell, two more a further cell) at
    /// 2-4 m/s, gone 0.6 s later; the camera kicks 2 px along the stroke for exactly one rendered frame; a material the pack takes flies as
    /// its icon to the PACK readout in 0.35 s, the readout bumps 10 % and ticks. Nothing of it allocates while the clods fly.
    /// </summary>
    public class DigFeelTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static IEnumerator Boot(System.Action<PlanetSideRoot> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            if (side.hazards != null) side.hazards.enabled = false;
            side.creatures.autoSpawn = false; side.creatures.DespawnAll();
            var player = side.player;
            player.externalInput = true; player.intent = default;
            int camp = Mathf.FloorToInt(Meridian.Planet.POI.PoiCatalog.SpawnCamp.CenterX);
            float x = camp + 14.5f;
            var feet = new Vector2(x, side.terrain.SurfaceAt(x) + 0.05f);
            player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero;
            for (int i = 0; i < 40; i++) yield return new WaitForFixedUpdate();
            yield return null;
            done(side);
        }

        [Test]
        public void TheClodCountFollowsTheCellsOpened()
        {
            Assert.AreEqual(4, DigFeel.ClodsFor(1), "one cell");
            Assert.AreEqual(6, DigFeel.ClodsFor(2));
            Assert.AreEqual(8, DigFeel.ClodsFor(3));
            Assert.AreEqual(8, DigFeel.ClodsFor(4), "never more than 8");
            Assert.AreEqual("fx/dig_clods/t1", DigFeel.ClodsKey(0));
            Assert.AreEqual("fx/dig_clods/t5", DigFeel.ClodsKey(4));
            Assert.AreEqual("fx/dig_clods/t5", DigFeel.ClodsKey(9), "past the last tier: the last sheet");
        }

        /// <summary>LEAD 17:0x / D-190: clods and the dig puff take the tone of the ground dug, lifted toward white, not the surface's:
        /// Topsoil brown, Stone grey. D-190 (1): the ground's tone is the drawn fill's own (its json's tone_hex), so Earth's sand puffs
        /// cream where Topsoil puffs brown; a fill without the field falls back to its tier's depth chip.</summary>
        [Test]
        public void TheToneIsTheDugFillsNotTheSurfaces()
        {
            const PlanetId E = PlanetId.Earth;
            var tiers = D1Tables.Current.tiers;
            Assert.GreaterOrEqual(tiers.Length, 3, "at least three tiers in the tables");
            for (int k = 0; k < tiers.Length; k++)
            {
                // D-190 (2): clods lifted 35 % toward white on T1-T3 and 60 % on T4-T5; the dust puff 60 % at its alpha
                float lift = k >= 3 ? 0.6f : 0.35f;
                Assert.AreEqual(lift, DigFeel.ToneLiftOf(k), 1e-6f, $"T{k + 1}'s lift");
                var ground = DigFeel.GroundTone(E, k, false);
                Assert.AreEqual(1f, ground.a, 1e-6f, "the ground's tone is opaque");
                var want = Color.Lerp(ground, Color.white, lift);
                var tone = DigFeel.Tone(E, k, false);
                Assert.AreEqual(want.r, tone.r, 1e-4f, $"T{k + 1} red"); Assert.AreEqual(want.g, tone.g, 1e-4f, $"T{k + 1} green"); Assert.AreEqual(want.b, tone.b, 1e-4f, $"T{k + 1} blue");
                Assert.AreEqual(1f, tone.a, 1e-6f, "opaque");
                var dust = Color.Lerp(ground, Color.white, 0.6f);
                var puff = DigFeel.PuffTone(E, k, false);
                Assert.AreEqual(dust.r, puff.r, 1e-4f, $"T{k + 1} puff red"); Assert.AreEqual(dust.g, puff.g, 1e-4f, $"T{k + 1} puff green"); Assert.AreEqual(dust.b, puff.b, 1e-4f, $"T{k + 1} puff blue");
                Assert.AreEqual(DigFeel.PuffRedrawn ? 0.85f : 0.7f, puff.a, 1e-6f, "the puff's alpha (0.85 on B-238's dust, 0.7 on the old ball)");
                // every tier's debris stays readable on its fill: lifted, never darker than a mid grey (T5's fill is ink)
                Assert.Greater(tone.maxColorComponent, 0.55f, $"T{k + 1}'s clods are not lost in the dark");
            }
            Assert.AreEqual(DigFeel.PuffRedrawn ? 1f : 0.6f, DigFeel.PuffScaleNow, 1e-6f, "the puff's scale (1 on B-238's dust)");
            Color t1 = DigFeel.Tone(E, 0, false), t3 = DigFeel.Tone(E, 2, false);
            Assert.Greater(t1.r - t1.b, 0.15f, "Topsoil: a brown (red well over blue)");
            Assert.Less(Mathf.Abs(t3.r - t3.b), 0.06f, "Stone: a grey");
            Assert.Greater(Mathf.Abs(t1.r - t3.r) + Mathf.Abs(t1.g - t3.g) + Mathf.Abs(t1.b - t3.b), 0.15f, "T1 and T3 read apart");
            Assert.AreEqual(DigFeel.Tone(E, tiers.Length - 1, false), DigFeel.Tone(E, 99, false), "past the last tier: the last tone");

            // D-190 (1): the fill drawn at the cell
            Assert.AreEqual("terrain/earth/ground_fill", DigFeel.FillKey(E, 0, false));
            Assert.AreEqual("terrain/earth/ground_fill_sand", DigFeel.FillKey(E, 0, true), "Earth's desert draws its own fill");
            Assert.AreEqual("terrain/mars/ground_fill_basalt", DigFeel.FillKey(PlanetId.Mars, 0, true), "Mars's basalt plain draws its own fill");
            Assert.AreEqual("terrain/mercury/ground_fill", DigFeel.FillKey(PlanetId.Mercury, 0, true), "Mercury's bands lie over ground_fill");
            Assert.AreEqual("terrain/earth/ground_fill_t3", DigFeel.FillKey(E, 2, true), "under the first tier: the tier's fill, band or no band");
            Assert.AreEqual("terrain/venus/ground_fill_t5", DigFeel.FillKey(PlanetId.Venus, 9, false), "past the last tier: the last fill");
            Assert.IsTrue(Meridian.Rendering.ArtMaterials.ToneFor("terrain/earth/ground_fill", out var soil), "Topsoil's tone is registered (ArtTones)");
            Assert.IsTrue(Meridian.Rendering.ArtMaterials.ToneFor("terrain/earth/ground_fill_sand", out var sand), "the sand's tone is registered");
            Assert.AreEqual((Color)new Color32(0x94, 0x73, 0x3A, 255), soil, "Topsoil #94733A (db44edd1)");
            Assert.AreEqual((Color)new Color32(0xF2, 0xE6, 0xCF, 255), sand, "sand #F2E6CF");
            Assert.AreEqual(soil, DigFeel.GroundTone(E, 0, false));
            Assert.AreEqual(sand, DigFeel.GroundTone(E, 0, true), "in the desert the first tier's tone is the sand's");
            Assert.AreEqual(DigFeel.GroundTone(E, 2, false), DigFeel.GroundTone(E, 2, true), "deeper tiers have no band fill");
            Assert.AreEqual(DigFeel.GroundTone(PlanetId.Mercury, 0, false), DigFeel.GroundTone(PlanetId.Mercury, 0, true), "a planet without a band fill");
            var sandPuff = DigFeel.PuffTone(E, 0, true); var soilPuff = DigFeel.PuffTone(E, 0, false);
            Assert.Greater(sandPuff.b - soilPuff.b, 0.1f, "the desert's dust is the paler (cream against Topsoil's brown)");
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator AStrokeThrowsItsClodsAndKicksTheCameraForOneFrame()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var feel = side.digFeel;
            Assert.NotNull(feel, "DigFeel on the planet side");
            var follow = side.sideCamera.GetComponent<CameraFollow>();
            Assert.NotNull(follow, "the side camera's follow");
            var p = side.player.Body.position;
            yield return null;
            Assert.AreEqual(0, feel.Alive, "no clods before a stroke");
            Assert.AreEqual(Vector2.zero, follow.KickNow, "no kick before a stroke");
            int kicks0 = follow.KickFrames, bursts0 = feel.Bursts;
            // B-232 / B-238 (imported, df2defa3): the clods' sheets and the shovel's crumbs are in before the first stroke
            var fx0 = Object.FindAnyObjectByType<Meridian.FX.SideFx>();
            Assert.NotNull(fx0, "SideFx on the planet side");
            var clodSheet = Meridian.FX.FxSheet.Get(DigFeel.ClodsKey(0));
            var flickSheet = Meridian.FX.FxSheet.Get(Meridian.Art.ArtKeys.Fx.ShovelFlick);
            float sheetsBy = Time.realtimeSinceStartup + 15f;
            while ((!clodSheet.Ready || !flickSheet.Ready) && Time.realtimeSinceStartup < sheetsBy) yield return null;
            Assert.IsTrue(clodSheet.Ready, "B-232's fx/dig_clods/t1 loads");
            Assert.AreEqual(24, clodSheet.frames.Length, "24 frames: four clods of six");
            Assert.IsTrue(flickSheet.Ready, "B-238's fx/shovel_flick/base loads");
            Assert.IsTrue(DigFeel.PuffRedrawn, "B-238's dust is in: the puff at scale 1 and 0.85 alpha, the flick back");
            int flicks0 = fx0.Flicks;

            var at = p + new Vector2(1.5f, -0.5f);
            var toolWas = Meridian.Progress.SkillStats.ToolOverride;
            Meridian.Progress.SkillStats.ToolOverride = Meridian.Rig.DigTool.Shovel; // the flick is the shovel's (whatever an earlier test left unlocked)
            bool struck = side.rig.Dig(at);
            Meridian.Progress.SkillStats.ToolOverride = toolWas;
            Assert.IsTrue(struck, "the stroke opens the ground");
            int cells = side.rig.LastDugCells;
            Assert.GreaterOrEqual(cells, 1, "cells opened");
            Assert.AreEqual(bursts0 + 1, feel.Bursts, "one burst a stroke");
            Assert.IsTrue(feel.LastBurstOnSheet, "the clods are B-232's, not the stand-in");
            Assert.AreEqual(flicks0 + 1, fx0.Flicks, "the shovel's flick is back (D-190 (4))");
            Assert.AreEqual(DigFeel.Tone(PlanetId.Earth, 0, false), fx0.LastFlickTint, "the flick's crumbs in the clods' tone");
            Assert.AreEqual(DigFeel.ClodsFor(cells), feel.LastBurst, $"clods for {cells} cells");
            Assert.That(feel.LastBurst, Is.InRange(DigFeel.MinClods, DigFeel.MaxClods));
            Assert.AreEqual(feel.LastBurst, feel.Alive, "every clod of the burst is drawn");
            int seen = 0;
            for (int i = 0; i < DigFeel.Pool; i++)
            {
                if (!feel.Clod(i, out var cp, out var cv, out _)) continue;
                seen++;
                Assert.That(cv.magnitude, Is.InRange(DigFeel.SpeedMin - 1e-3f, DigFeel.SpeedMax + 1e-3f), "launch speed 2-4 m/s");
                Assert.Less(Vector2.Distance(cp, at), DigFeel.MouthM + 0.3f, "thrown from the cell's mouth");
                Assert.AreEqual(DigFeel.Tone(PlanetId.Earth, 0, false), feel.TintOf(i), "at camp: Topsoil's tone (its fill's, D-190 (1))");
            }
            Assert.AreEqual(feel.LastBurst, seen);
            Assert.AreEqual(0, DigRun.TierAt(side.terrain, at), "the camp's stroke is in the first tier");

            // the kick: 2 px along the stroke in the frame the stroke lands in, gone the frame after
            yield return null;
            Assert.AreEqual(kicks0 + 1, follow.KickFrames, "the kick was drawn in the stroke's frame");
            float px = follow.KickNow.magnitude / follow.WorldPerPixel;
            Assert.AreEqual(DigFeel.KickPixels, px, 0.05f, "a 2 px kick");
            Assert.Greater(Vector2.Dot(follow.KickNow.normalized, feel.LastKick), 0.999f, "along the stroke");
            Assert.Greater(Vector2.Dot(feel.LastKick, (at - (p + new Vector2(0f, 0.9f))).normalized), 0.99f, "the stroke runs from the hand to the cell");
            yield return null;
            Assert.AreEqual(Vector2.zero, follow.KickNow, "one frame long");
            Assert.AreEqual(kicks0 + 1, follow.KickFrames, "no second kick frame");

            // the clods fall under gravity and are gone 0.6 s after the stroke
            float t0 = Time.time;
            bool fell = false;
            while (Time.time - t0 < DigFeel.ClodLife * 0.5f)
            {
                yield return null;
                for (int i = 0; i < DigFeel.Pool; i++) if (feel.Clod(i, out _, out var cv, out bool resting) && (cv.y < 0f || resting)) fell = true;
            }
            Assert.IsTrue(fell, "gravity turns the clods down within 0.3 s");
            Assert.Greater(feel.Alive, 0, "still drawn at half their life");
            while (Time.time - t0 < DigFeel.ClodLife + 0.1f) yield return null;
            yield return null;
            Assert.AreEqual(0, feel.Alive, "gone 0.6 s after the stroke");
            Assert.AreEqual(0, DigFeel.TotalAlive);

            // T3 (LEAD 17:0x): the same stroke 56 m under the Surface Line throws Stone-toned clods (the body held there, as a capture's room)
            var body = side.player.Body;
            var deep = new Vector2(p.x + 30f, DigRun.LineAt(side.terrain, p.x + 30f) - 56f);
            body.simulated = false;
            body.position = deep; side.player.transform.position = deep;
            yield return null;
            float settled = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < settled) yield return null;
            var deepAt = deep + new Vector2(1.5f, 0.2f);
            Assert.AreEqual(2, DigRun.TierAt(side.terrain, deepAt), "56 m down: the third tier");
            Assert.IsTrue(side.rig.Dig(deepAt), "the stroke at depth");
            int deepClods = 0;
            for (int i = 0; i < DigFeel.Pool; i++)
            {
                if (!feel.Clod(i, out _, out _, out _)) continue;
                deepClods++;
                Assert.AreEqual(DigFeel.Tone(PlanetId.Earth, 2, false), feel.TintOf(i), "at 56 m: Stone's tone, not the surface's");
            }
            Assert.AreEqual(feel.LastBurst, deepClods, "the deep burst's clods");
            // D-190: the stroke's dust puff takes the same cell's tone (the one puff: no band set's own)
            var fx = Object.FindAnyObjectByType<Meridian.FX.SideFx>();
            Assert.NotNull(fx, "SideFx on the planet side");
            Assert.AreEqual(DigFeel.PuffTone(PlanetId.Earth, 2, false), fx.LastPuffTint, "the deep stroke's puff: Stone's dust");
            Assert.Less(Vector2.Distance(fx.LastPuffAt, deepAt), 0.01f, "played at the stroke");
            StringAssert.EndsWith("/dig_puff", fx.PuffAt(deepAt), "the planet's one puff");
            body.position = p; side.player.transform.position = p;
            body.simulated = true;
            yield return null;

            // D-190 (3): a mound's puff is the same one, tinted where the earth lands (it played untinted)
            int puffs = fx.Puffs;
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            var moundAt = side.player.Body.position + new Vector2(-2.2f, 0.6f);
            Assert.IsTrue(side.rig.Place(moundAt, side.rig.GroundMaterial), "the Builder (as a raw tool) piles a mound beside the surveyor");
            Assert.AreEqual(puffs + 1, fx.Puffs, "the mound's puff");
            Assert.AreEqual(DigFeel.PuffTone(PlanetId.Earth, 0, false), fx.LastPuffTint, "a mound at camp: Topsoil's dust, tinted");
            yield return null;
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>U-196 (B-230): a dug cell's back face is its tier's wall tile: the chunk's back-wall submesh draws with the walls'
        /// material (MERIDIAN/GroundTiers over back_wall_t1..t5, read at world / 4), the body with the fills' as before: one shader, the
        /// submesh the back wall already had. D-190 (1): the camp lies outside the desert, so its dust is Topsoil's.</summary>
        [UnityTest, Timeout(240000)]
        public IEnumerator ADugCellShowsItsTiersWallBehindIt()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var smooth = side.cartoon != null ? side.cartoon.Smooth : null;
            Assert.NotNull(smooth, "the smooth ground on Earth");
            Assert.AreSame(smooth, Meridian.View2D.SmoothGround.Current, "the ground of the planet side that is up");
            float until = Time.realtimeSinceStartup + 20f;
            while (!(smooth.WallTier(1) && smooth.WallTier(2) && smooth.WallTier(3) && smooth.WallTier(4) && smooth.WallTier(5)) && Time.realtimeSinceStartup < until) yield return null;
            for (int tier = 1; tier <= 5; tier++) Assert.IsTrue(smooth.WallTier(tier), $"B-230's back_wall_t{tier} loads on Earth");

            var p = side.player.Body.position;
            var at = p + new Vector2(1.5f, -0.5f);
            Assert.IsFalse(DigFeel.BandFillAt(at.x), "the camp is not in the desert");
            Assert.IsTrue(side.rig.Dig(at), "a stroke at camp");
            until = Time.realtimeSinceStartup + 10f;
            while (!smooth.WallArt && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 10; i++) yield return null; // the chunk's mesh after the stroke
            Assert.IsTrue(smooth.WallArt, "the walls' material is made with the first chunk that draws a back wall");

            Meridian.Terrain.TerrainChunk chunk = null;
            int C = Meridian.Terrain.TerrainConstants.ChunkSize;
            foreach (Transform child in side.terrain.transform)
            {
                var c = child.GetComponent<Meridian.Terrain.TerrainChunk>();
                if (c != null && Mathf.FloorToInt(at.x / C) == c.cx && Mathf.FloorToInt(at.y / C) == c.cy) chunk = c;
            }
            Assert.NotNull(chunk, "the chunk the stroke opened");
            Assert.IsTrue(smooth.ChunkMaterials(chunk, out var wall, out var body), "the chunk's ground mesh");
            Assert.AreSame(smooth.WallMaterialNow, wall, "the back wall draws with the walls' material");
            Assert.AreNotSame(wall, body, "the body keeps the fills' material");
            Assert.AreSame(body.shader, wall.shader, "one shader for both (MERIDIAN/GroundTiers)");
            StringAssert.Contains("back_wall_t1", wall.mainTexture.name, "tier 1's wall is the material's base");
            for (int tier = 2; tier <= 5; tier++)
                StringAssert.Contains($"back_wall_t{tier}", wall.GetTexture($"_Tier{tier}Tex").name, $"tier {tier}'s wall by depth");
            StringAssert.Contains("ground_fill", body.mainTexture.name, "the body's base is the fill");
            Assert.AreEqual(Meridian.View2D.SmoothGround.WallTileM, wall.GetVector("_LineParams").y, 1e-4f, "a wall tile is 4 m (its uv is world / 4)");
            Assert.AreEqual(8f, body.GetVector("_LineParams").y, 1e-4f, "a fill tile is 8 m");
            Assert.AreEqual(wall.mainTexture.width, wall.GetFloat("_TileTexels"), 1e-4f, "the wall's texels a tile");
            Assert.AreEqual(body.GetVector("_TierFrom"), wall.GetVector("_TierFrom"), "the walls change at the fills' depths");
            Assert.AreEqual(TextureWrapMode.Repeat, wall.mainTexture.wrapMode, "the wall tiles");
            // U-205 (G4): each 4 m row of the wall is read 0.37 of a tile further along (no pebble on one line down a shaft); the fills are not shifted
            Assert.AreEqual(Meridian.View2D.SmoothGround.WallRowShift, wall.GetFloat("_RowShift"), 1e-5f, "the wall's rows are shifted");
            Assert.AreEqual(0f, body.GetFloat("_RowShift"), "the fill's rows are not");

            var fx = Object.FindAnyObjectByType<Meridian.FX.SideFx>();
            Assert.AreEqual(DigFeel.PuffTone(PlanetId.Earth, 0, false), fx.LastPuffTint, "the camp's dust: Topsoil's fill tone");
            Assert.AreEqual(DigFeel.PuffToneAt(side.terrain, at, 0), fx.LastPuffTint);
            yield return null;
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>B-242: where the band's own fill is drawn (Earth's desert sand), a dug cell's back face is that fill's own wall tile.
        /// The overlay submesh that carried the sand fill, shaded, draws with a second walls' material whose base is back_wall_sand (the
        /// planet's t2..t5 under it at the same depths, the same tile size and row shift), white under the hole's shading and read at
        /// world / 4; and the hole's soft inner shadow lies in that submesh, over the wall (laid in the planet's wall it was covered by
        /// the overlay: a pit in the desert had none).</summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator ADugCellInTheDesertShowsTheSandsWall()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var smooth = side.cartoon != null ? side.cartoon.Smooth : null;
            Assert.NotNull(smooth, "the smooth ground on Earth");
            float until = Time.realtimeSinceStartup + 20f;
            while (!(smooth.WallTier(1) && smooth.AltWallArt) && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsTrue(smooth.WallTier(1), "tier 1's wall");
            Assert.IsTrue(smooth.AltWallArt, "B-242's back_wall_sand loads on Earth");

            // the nearest stretch of sand that holds 8 m to either side (CaptureU196Holes' 5_sand_dig finds its desert the same way)
            int camp = Mathf.FloorToInt(Meridian.Planet.POI.PoiCatalog.SpawnCamp.CenterX);
            float desert = float.NaN;
            for (int d = 16; d <= 4000 && float.IsNaN(desert); d += 16)
                foreach (int sgn in new[] { 1, -1 })
                {
                    float x0 = camp + sgn * d;
                    if (float.IsNaN(desert) && smooth.BandFillAt(x0 - 8f) && smooth.BandFillAt(x0) && smooth.BandFillAt(x0 + 8f)) desert = x0 + 0.5f;
                }
            Assert.IsFalse(float.IsNaN(desert), "a stretch of sand within 4 km of the camp");

            var t = side.terrain;
            var body = side.player.Body;
            body.simulated = false;
            var feet = new Vector2(desert - 3f, t.SurfaceAt(desert - 3f) + 0.05f);
            body.position = feet; side.player.transform.position = feet;
            var follow = side.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
            if (follow != null) follow.SnapToTarget();
            yield return null;
            until = Time.realtimeSinceStartup + 30f;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 10; i++) yield return null;

            // a pit 1.8 m wide and about 3 m deep, open at the sand's surface (5_sand_dig's carve)
            float top = t.SurfaceAt(desert), pitY = top - 1.2f;
            int strokes = 0;
            var owner = side.rig.owner; side.rig.owner = null;
            try
            {
                for (float dy = -1.3f; dy <= 1.3f + 1e-3f; dy += 0.6f)
                    for (float dx = -0.9f; dx <= 0.9f + 1e-3f; dx += 0.6f)
                        if (side.rig.Dig(new Vector2(desert + dx, pitY + dy))) strokes++;
            }
            finally { side.rig.owner = owner; }
            Assert.Greater(strokes, 4, "a pit in the sand");
            var drops = side.rig.drops;
            if (drops != null) for (int k = drops.Live.Count - 1; k >= 0; k--) drops.Collect(drops.Live[k]);
            for (int i = 0; i < 20; i++) yield return null; // the chunk's mesh after the last stroke
            until = Time.realtimeSinceStartup + 10f;
            while (smooth.AltWallMaterialNow == null && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 10; i++) yield return null;
            var alt = smooth.AltWallMaterialNow;
            Assert.NotNull(alt, "the sand wall's material is made with the first chunk that draws it");
            var wall = smooth.WallMaterialNow;
            Assert.NotNull(wall, "the planet's walls' material");

            Assert.AreNotSame(wall, alt, "a material of its own");
            Assert.AreSame(wall.shader, alt.shader, "one shader for both (MERIDIAN/GroundTiers)");
            StringAssert.Contains("back_wall_sand", alt.mainTexture.name, "the sand's wall is the material's base");
            StringAssert.Contains("back_wall_t1", wall.mainTexture.name, "the planet's walls keep tier 1's");
            for (int tier = 2; tier <= 5; tier++)
                Assert.AreSame(wall.GetTexture($"_Tier{tier}Tex"), alt.GetTexture($"_Tier{tier}Tex"), $"under the sand, tier {tier}'s wall by depth");
            Assert.AreEqual(wall.GetVector("_TierFrom"), alt.GetVector("_TierFrom"), "at the planet's depths");
            Assert.AreEqual(Meridian.View2D.SmoothGround.WallTileM, alt.GetVector("_LineParams").y, 1e-4f, "a wall tile is 4 m (its uv is world / 4)");
            Assert.AreEqual(alt.mainTexture.width, alt.GetFloat("_TileTexels"), 1e-4f, "the wall's texels a tile");
            Assert.AreEqual(Meridian.View2D.SmoothGround.WallRowShift, alt.GetFloat("_RowShift"), 1e-5f, "its rows are shifted as the tiers' walls'");
            Assert.AreEqual(TextureWrapMode.Repeat, alt.mainTexture.wrapMode, "the wall tiles");

            // the pit's chunks: the overlay submesh (1) draws the sand's wall, white under the hole's shading at world / 4, with the inner
            // shadow's ink in it; the planet's wall submesh (0) under it carries no ink there
            const int C = Meridian.Terrain.TerrainConstants.ChunkSize;
            int chunks = 0, wallVerts = 0, inkOver = 0, inkUnder = 0;
            float brightest = 0f;
            foreach (var chunk in Object.FindObjectsByType<Meridian.Terrain.TerrainChunk>())
            {
                if (Mathf.Abs((chunk.cx + 0.5f) * C - desert) > C || Mathf.Abs((chunk.cy + 0.5f) * C - pitY) > C) continue;
                if (!smooth.ChunkAltWall(chunk, out var drawn, out _, out int altIndices) || altIndices == 0) continue;
                MeshFilter mf = null;
                foreach (var f in chunk.GetComponentsInChildren<MeshFilter>()) if (f.name == "SmoothGround") mf = f;
                Assert.NotNull(mf, "the chunk's ground mesh");
                var vs = mf.sharedMesh.vertices; var cs = mf.sharedMesh.colors; var uvs = mf.sharedMesh.uv;
                bool pit = false;
                foreach (int vi in mf.sharedMesh.GetTriangles(1))
                {
                    var col = cs[vi];
                    Vector3 w = mf.transform.TransformPoint(vs[vi]);
                    if (Mathf.Abs(w.x - desert) > 1.6f || w.y < pitY - 2f || w.y > top + 0.1f) continue; // the pit's own stretch
                    pit = true;
                    if (col.r + col.g + col.b <= 0f) { if (col.a > 0.01f) inkOver++; continue; } // the inner shadow: ink, fading to clear
                    wallVerts++;
                    Assert.AreEqual(1f, col.a, 1e-3f, "whole in the sand: the sand's wall covers the planet's");
                    Assert.AreEqual(col.r, col.g, 1e-4f, "white under the hole's shading (the tile is drawn as painted)");
                    Assert.AreEqual(col.r, col.b, 1e-4f);
                    brightest = Mathf.Max(brightest, col.r);
                    Assert.AreEqual(w.x / Meridian.View2D.SmoothGround.WallTileM, uvs[vi].x, 2e-3f, "read at world / 4");
                    Assert.AreEqual(w.y / Meridian.View2D.SmoothGround.WallTileM, uvs[vi].y, 2e-3f);
                }
                if (!pit) continue;
                chunks++;
                Assert.AreSame(alt, drawn, "the pit's overlay submesh draws with the sand wall's material");
                foreach (int vi in mf.sharedMesh.GetTriangles(0))
                {
                    var col = cs[vi];
                    Vector3 w = mf.transform.TransformPoint(vs[vi]);
                    if (Mathf.Abs(w.x - desert) > 1.6f || w.y < pitY - 2f || w.y > top + 0.1f) continue;
                    if (col.r + col.g + col.b <= 0f && col.a > 0.01f) inkUnder++;
                }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] b242 sand pit at x {desert:0.0} ({desert - camp:0} m from the camp), the sand at {top:0.0}, {strokes} strokes: {chunks} chunk(s), {wallVerts} sand-wall vertices, brightest {brightest:0.000}, the inner shadow's ink {inkOver} over / {inkUnder} under");
            Assert.Greater(chunks, 0, "a chunk draws the pit's sand wall");
            Assert.Greater(wallVerts, 20, "the pit's back face");
            Assert.Greater(brightest, 0.7f, "near the pit's mouth the tile is drawn as painted (the shaded fill stopped at 0.55)");
            Assert.Greater(inkOver, 0, "the hole's inner shadow lies over the sand's wall");
            Assert.AreEqual(0, inkUnder, "and not under it");
            body.simulated = true;
            yield return null;
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>U-205 (BLENDER's 0.6.2 read, G3): a shaft open to the sky is lit all the way down. Its back wall carries the depth term
        /// alone (55 % of its shade from 6 m under the natural surface), in every chunk it crosses: the sky scan stopped 12 cells over a
        /// chunk's top, so a chunk lying deeper read the shaft as shut and its wall went a fifth darker in one hard step at its top edge
        /// (smoke_54-58). The shaft here is 56 m deep, so a chunk's top edge lies between 16 and 48 m down it wherever the ground stands.</summary>
        [UnityTest, Timeout(300000)]
        public IEnumerator ADeepOpenShaftsWallIsLitAllTheWayDown()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var smooth = side.cartoon != null ? side.cartoon.Smooth : null;
            Assert.NotNull(smooth, "the smooth ground on Earth");
            float until = Time.realtimeSinceStartup + 20f;
            while (!smooth.WallTier(1) && Time.realtimeSinceStartup < until) yield return null;
            var t = side.terrain;
            var body = side.player.Body;
            float ax = side.spawnX + 19.5f, top = t.SurfaceAt(ax), bottom = Mathf.Floor(top) - 56f; // the smoke's shaft column, deeper
            body.simulated = false;
            var mid = new Vector2(ax, (top + bottom) * 0.5f);
            body.position = mid; side.player.transform.position = mid;
            var follow = side.sideCamera.GetComponent<Meridian.Player.CameraFollow>();
            if (follow != null) follow.SnapToTarget();
            yield return null;
            until = Time.realtimeSinceStartup + 30f;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            int strokes = 0;
            var owner = side.rig.owner; side.rig.owner = null;
            try
            {
                for (float y = bottom + 0.7f; y <= top + 0.5f + 1e-3f; y += 0.5f)
                    foreach (float dx in new[] { -1.1f, -0.55f, 0f, 0.55f, 1.1f })
                        if (side.rig.Dig(new Vector2(ax + dx, y))) strokes++;
            }
            finally { side.rig.owner = owner; }
            Assert.Greater(strokes, 100, "the shaft is bored");
            var drops = side.rig.drops;
            if (drops != null) for (int k = drops.Live.Count - 1; k >= 0; k--) drops.Collect(drops.Live[k]);
            for (int i = 0; i < 40; i++) yield return null; // the chunks' meshes after the last stroke
            until = Time.realtimeSinceStartup + 20f;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 10; i++) yield return null;

            // the back wall's vertices down the shaft's middle, 7 m and more under the natural surface (the depth term is at its floor there)
            const int C = Meridian.Terrain.TerrainConstants.ChunkSize;
            float lo = float.MaxValue, hi = float.MinValue, loY = 0f, hiY = 0f, deepest = float.MaxValue, highest = float.MinValue;
            int n = 0;
            var chunksHit = new System.Collections.Generic.HashSet<int>();
            foreach (var chunk in Object.FindObjectsByType<Meridian.Terrain.TerrainChunk>())
            {
                MeshFilter mf = null;
                foreach (var f in chunk.GetComponentsInChildren<MeshFilter>()) if (f.name == "SmoothGround") mf = f;
                if (mf == null || mf.sharedMesh == null || mf.sharedMesh.subMeshCount == 0) continue;
                var vs = mf.sharedMesh.vertices; var cs = mf.sharedMesh.colors;
                if (cs == null || cs.Length != vs.Length) continue;
                var tri = mf.sharedMesh.GetTriangles(0); // SmoothGround's submesh 0: the back wall (and the rim's ink shadow over it)
                foreach (int vi in tri)
                {
                    var col = cs[vi];
                    if (col.a < 0.99f || col.r + col.g + col.b <= 0f) continue; // the rim shadow's ink
                    Vector3 w = mf.transform.TransformPoint(vs[vi]);
                    if (Mathf.Abs(w.x - ax) > 0.6f || w.y < bottom + 1.5f) continue;
                    if (t.SurfaceAt(w.x) - w.y < 7f) continue;
                    n++;
                    chunksHit.Add(chunk.cy);
                    if (col.r < lo) { lo = col.r; loY = w.y; }
                    if (col.r > hi) { hi = col.r; hiY = w.y; }
                    deepest = Mathf.Min(deepest, w.y); highest = Mathf.Max(highest, w.y);
                }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u205 open shaft at x {ax:0.0}: top {top:0.0}, floor {bottom:0.0}, {strokes} strokes; {n} back-wall vertices down its middle from {highest:0.0} to {deepest:0.0} in {chunksHit.Count} chunk rows (a chunk's edge every {C} m); shade {lo:0.000} at y {loY:0.0} .. {hi:0.000} at y {hiY:0.0}");
            Assert.Greater(n, 100, "the shaft's back wall is drawn down its middle");
            Assert.GreaterOrEqual(chunksHit.Count, 2, "the shaft crosses a chunk's edge more than 7 m down");
            Assert.LessOrEqual(hi / Mathf.Max(lo, 1e-4f), 1.03f, $"one shade down the open shaft (the old step was 1.25: {hi:0.000} at y {hiY:0.0} against {lo:0.000} at y {loY:0.0})");
            body.simulated = true;
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator FlyingClodsAllocateNothing()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var feel = side.digFeel;
            var p = side.player.Body.position;
            var tint = Meridian.FX.SideFx.FlickTint(side.Config.id);
            feel.Burst(p + new Vector2(1.5f, 1.5f), p + new Vector2(0f, 0.9f), DigFeel.MaxClods, 0, tint); // warm: the stand-in sprites, the sheets' probes
            float until = Time.time + DigFeel.ClodLife + 0.2f;
            while (Time.time < until) yield return null;
            // The whole frame over 60 frames, quiet and then with 8-16 clods in the air (a burst each 0.3 s), three rounds: the least of each
            // (another system's one-off allocation in a span is not the clods'; a per-frame one of ours would be in every flying span).
            long quiet = long.MaxValue, flying = long.MaxValue;
            int aliveSeen = 0;
            for (int round = 0; round < 3; round++)
            {
                long before = System.GC.GetAllocatedBytesForCurrentThread();
                for (int i = 0; i < 60; i++) yield return null;
                quiet = System.Math.Min(quiet, System.GC.GetAllocatedBytesForCurrentThread() - before);
                before = System.GC.GetAllocatedBytesForCurrentThread();
                float next = 0f;
                for (int i = 0; i < 60; i++)
                {
                    if (Time.time >= next) { feel.Burst(p + new Vector2(1.5f, 1.5f), p + new Vector2(0f, 0.9f), DigFeel.MaxClods, 0, tint); next = Time.time + 0.3f; }
                    yield return null;
                    aliveSeen = Mathf.Max(aliveSeen, feel.Alive);
                }
                flying = System.Math.Min(flying, System.GC.GetAllocatedBytesForCurrentThread() - before);
                float clear = Time.time + DigFeel.ClodLife + 0.1f;
                while (Time.time < clear) yield return null;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u195 GC over 60 frames (least of 3 rounds): quiet {quiet} B, with clods flying {flying} B (up to {aliveSeen} alive)");
            Assert.Greater(aliveSeen, 0, "clods in the air while measured");
            Assert.LessOrEqual(flying - quiet, 1024, "the clods add no per-frame allocation (≤ 1 KB over 60 frames)");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator ADugMaterialFliesToThePackReadoutWhichBumpsAndTicks()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var feel = side.digFeel;
            var hud = side.sideHud;
            var flight = hud.PackFlight;
            Assert.NotNull(flight, "the HUD's pack flight");
            var item = ItemRegistry.Get("iron");
            Assert.NotNull(item, "iron in the registry");
            float until = Time.realtimeSinceStartup + 15f;
            while (ItemIcons.Get(item.id, side.terrain) == null && Time.realtimeSinceStartup < until) yield return null;
            Assert.NotNull(ItemIcons.Get(item.id, side.terrain), "iron's icon loaded");
            var inv = GameState.Instance.inventory;
            int had = inv.Count(item.id), flights0 = feel.Flights, landed0 = flight.Landed, bumps0 = hud.PackBumps;

            var p = side.player.Body.position;
            side.rig.drops.Spawn(item.id, p + new Vector2(0.4f, 0.6f), null);
            until = Time.realtimeSinceStartup + 10f;
            while (feel.Flights == flights0 && Time.realtimeSinceStartup < until) yield return null;
            Assert.AreEqual(flights0 + 1, feel.Flights, "the pack took the drop: its icon flies");
            Assert.AreEqual(had + 1, inv.Count(item.id), "the iron is in the pack");
            float t0 = Time.time;
            Assert.AreEqual(1, flight.InFlight);
            Assert.AreEqual(landed0, flight.Landed, "not landed in the frame it starts");
            Assert.Greater(Vector2.Distance(flight.LastFrom, SideHud.PackCentre), 100f, "it starts at the drop, far from the readout");

            until = Time.realtimeSinceStartup + 10f;
            while (flight.Landed == landed0 && Time.realtimeSinceStartup < until) yield return null;
            float took = Time.time - t0;
            Assert.AreEqual(landed0 + 1, flight.Landed, "the icon lands");
            Assert.That(took, Is.InRange(HudPackFlight.Seconds - 0.05f, HudPackFlight.Seconds + 0.08f), "a 0.35 s flight");
            Assert.Less(Vector2.Distance(flight.LastEnd, SideHud.PackCentre), 0.5f, "it ends on the readout's centre (HUD units)");
            var tag = hud.PackTag.rectTransform;
            Vector3 centre = tag.TransformPoint(tag.rect.center);
            Assert.Less(Vector2.Distance(flight.LastEndWorld, centre), 3f * hud.HudRoot.lossyScale.x, "on the PACK tag as drawn");
            Assert.AreEqual(bumps0 + 1, hud.PackBumps, "the readout bumps as it lands");
            if (AudioDirector.Instance != null) Assert.AreEqual(Sfx.PackTick, AudioDirector.Instance.LastPlayed, "the tick");

            yield return null; yield return null;
            Assert.That(hud.PackScale, Is.InRange(1f, 1f + SideHud.PackBump + 1e-3f), "bumped by at most 10 %");
            var before = tag.TransformPoint(tag.rect.center);
            Assert.Less(Vector2.Distance(before, centre), 1.5f * hud.HudRoot.lossyScale.x, "the bump scales about the tag's centre");
            float settle = Time.time + SideHud.PackBumpSeconds + 0.1f;
            float peak = hud.PackScale;
            while (Time.time < settle) { yield return null; peak = Mathf.Max(peak, hud.PackScale); }
            yield return null;
            Assert.Greater(peak, 1.02f, "the bump was drawn");
            Assert.AreEqual(1f, hud.PackScale, 1e-4f, "back to its size");
            Assert.AreEqual(Vector2.zero, hud.PackRoot.anchoredPosition, "and its place");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
