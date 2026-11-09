using System.Collections;
using Meridian.Audio;
using Meridian.Core;
using Meridian.Items;
using Meridian.Mining;
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

        /// <summary>LEAD 17:0x: clods and the dig puff take the dug cell's tier tone (the depth chip's colour lifted toward white), not the
        /// surface ground's: Topsoil brown, Stone grey.</summary>
        [Test]
        public void TheToneIsTheDugTiersNotTheSurfaces()
        {
            var tiers = D1Tables.Current.tiers;
            Assert.GreaterOrEqual(tiers.Length, 3, "at least three tiers in the tables");
            for (int k = 0; k < tiers.Length; k++)
            {
                var want = Color.Lerp(tiers[k].ChipColor, Color.white, DigFeel.ToneLift);
                var tone = DigFeel.Tone(k);
                Assert.AreEqual(want.r, tone.r, 1e-4f, $"T{k + 1} red"); Assert.AreEqual(want.g, tone.g, 1e-4f, $"T{k + 1} green"); Assert.AreEqual(want.b, tone.b, 1e-4f, $"T{k + 1} blue");
                Assert.AreEqual(1f, tone.a, 1e-6f, "opaque");
            }
            Color t1 = DigFeel.Tone(0), t3 = DigFeel.Tone(2);
            Assert.Greater(t1.r - t1.b, 0.15f, "Topsoil: a brown (red well over blue)");
            Assert.Less(Mathf.Abs(t3.r - t3.b), 0.06f, "Stone: a grey");
            Assert.Greater(Mathf.Abs(t1.r - t3.r) + Mathf.Abs(t1.g - t3.g) + Mathf.Abs(t1.b - t3.b), 0.15f, "T1 and T3 read apart");
            Assert.AreEqual(DigFeel.Tone(tiers.Length - 1), DigFeel.Tone(99), "past the last tier: the last tone");
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

            var at = p + new Vector2(1.5f, -0.5f);
            Assert.IsTrue(side.rig.Dig(at), "the stroke opens the ground");
            int cells = side.rig.LastDugCells;
            Assert.GreaterOrEqual(cells, 1, "cells opened");
            Assert.AreEqual(bursts0 + 1, feel.Bursts, "one burst a stroke");
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
                Assert.AreEqual(DigFeel.Tone(0), feel.TintOf(i), "at camp: Topsoil's tone");
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
                Assert.AreEqual(DigFeel.Tone(2), feel.TintOf(i), "at 56 m: Stone's tone, not the surface's");
            }
            Assert.AreEqual(feel.LastBurst, deepClods, "the deep burst's clods");
            body.position = p; side.player.transform.position = p;
            body.simulated = true;
            yield return null;
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
