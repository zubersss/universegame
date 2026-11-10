using System.Collections;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Rig;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-055 (PlayMode): every Mercury and Venus species spawns by its rule with ground or flight placement;
    /// (the Cinderhulk and Veil Serpent Lance cases are archived with the Lance, D-087);
    /// AI ≤ 0.5 ms with 20 inner-planet creatures (D-047: median and p99).
    /// </summary>
    public class InnerCreatureTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        SceneDirector director;
        PlanetSideRoot side;
        CreatureDirector creatures;
        PlayerController player;

        IEnumerator Boot(PlanetId planet)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(planet));
            side = director.PlanetSide;
            Assert.AreEqual(planet, side.Config.id);
            side.hazards.enabled = false;
            if (side.wardens != null) side.wardens.enabled = false;
            creatures = side.creatures;
            player = side.player;
            var vitals = player.GetComponent<PlayerVitals>();
            vitals.maxHealth = vitals.health = 1e6f;
            timeout = Time.realtimeSinceStartup + 10f;
            foreach (Species s in System.Enum.GetValues(typeof(Species)))
                if (SpeciesSpec.Get(s).planet == planet)
                    while (!creatures.ArtReady(s) && Time.realtimeSinceStartup < timeout) yield return null;
        }

        IEnumerator PutAt(float x)
        {
            int tx = Mathf.FloorToInt(x);
            var feet = new Vector2(tx + 0.5f, side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(tx)) + 1.05f);
            yield return PutAt(feet);
        }

        IEnumerator PutAt(Vector2 feet)
        {
            player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero;
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
        }

        /// <summary>Mercury: shift the clock so the dawn line runs through x (the twilight band, dawn side).</summary>
        void DawnAt(float x)
        {
            side.hazards.mercuryClockOffset = 0;
            double now = creatures.MercuryNow;
            float dawn = MercuryTerminator.Dawn(now, side.Config.worldWidth);
            side.hazards.mercuryClockOffset = (x - dawn) * MercuryTerminator.CreepSecondsPerMetre;
        }

        /// <summary>Spawns by the natural rule within 30 columns of the surveyor (either side, off the camera's centre).</summary>
        Creature SpawnNear(Species s)
        {
            float px = player.Body.position.x;
            for (int d = 8; d < 30; d++)
                foreach (int sgn in new[] { 1, -1 })
                {
                    var c = creatures.SpawnAt(s, Mathf.FloorToInt(px + sgn * d), player.Body.position.y);
                    if (c != null) return c;
                }
            // Refused everywhere: say why for the nearest column each side (the rule, or the ground's collision not resident).
            foreach (int sgn in new[] { 1, -1 })
            {
                int tx = Mathf.FloorToInt(px + sgn * 8);
                var site = creatures.SiteAt(tx, player.Body.position.y);
                TestContext.Out.WriteLine($"[MERIDIAN] {s} refused at {tx}: allows {SpeciesSpec.Get(s).Allows(site)}, tile {site.surfaceTile} surface {site.surfaceY} zone {site.zone} t {site.localTime:F2}, collision ready {side.terrain.IsCollisionReady(tx, site.surfaceY)}, settled {side.terrain.IsSettled}, player {player.Body.position} simulated {player.Body.simulated}");
            }
            return null;
        }

        /// <summary>Settled placement: walkers stand on the ground; Air fliers hover in their band; Deck fliers stay in the deck band.</summary>
        IEnumerator CheckPlacement(Creature c, List<string> fails, System.Text.StringBuilder log)
        {
            for (int i = 0; i < 120 && c.Held; i++) yield return new WaitForFixedUpdate();
            for (int i = 0; i < 90; i++) yield return new WaitForFixedUpdate();
            if (!c.Alive) { fails.Add(c.Spec.id + " despawned"); yield break; }
            var spec = c.Spec;
            var pos = c.Body.position;
            int tx = Mathf.FloorToInt(pos.x);
            if (spec.habitat == Habitat.Ground)
            {
                float bottom = pos.y - spec.size.y * 0.5f, ground = side.terrain.TopSolidY(tx) + 1f;
                log.AppendLine($"{spec.id}: bottom {bottom:F2}, ground {ground:F0}");
                if (Mathf.Abs(bottom - ground) > 0.35f && Mathf.Abs(bottom - (side.terrain.TopSolidY(tx + 1) + 1f)) > 0.35f)
                    fails.Add($"{spec.id} not on the ground ({bottom:F2} vs {ground:F0})");
            }
            else if (spec.habitat == Habitat.Air)
            {
                float above = pos.y - (side.terrain.TopSolidY(tx) + 1f);
                log.AppendLine($"{spec.id}: {above:F1} m above ground");
                if (above < spec.hoverMin - 1.5f || above > spec.hoverMax + 2f) fails.Add($"{spec.id} at {above:F1} m, band {spec.hoverMin}-{spec.hoverMax}");
            }
            else
            {
                float off = Mathf.Abs(pos.y - VenusLandforms.DeckY);
                log.AppendLine($"{spec.id}: {pos.y:F1} (deck {VenusLandforms.DeckY})");
                if (off > VenusLandforms.DeckHalfBand + 5f) fails.Add($"{spec.id} left the deck band (y {pos.y:F1})");
            }
            if (c.View.sprite == null || c.View.sprite.name.StartsWith("CreaturePlaceholder")) fails.Add(spec.id + " has no art");
        }

        [UnityTest]
        public IEnumerator MercurySpeciesSpawnWhereTheyLive()
        {
            yield return Boot(PlanetId.Mercury);
            var fails = new List<string>();
            var log = new System.Text.StringBuilder();
            // The twilight band, dawn side, at the surveyor: glassback, cinderlings, flarewing (U-138, D-150: the Cinderhulk left the spawn table).
            float x0 = player.Body.position.x;
            DawnAt(x0 + 40f);
            yield return PutAt(x0 + 40f);
            foreach (var s in new[] { Species.Glassback, Species.Cinderling, Species.Flarewing })
            {
                var c = SpawnNear(s);
                if (c == null) { fails.Add(s + ": rule refused every column near the dawn line"); continue; }
                yield return CheckPlacement(c, fails, log);
                creatures.Despawn(c);
            }
            Assert.IsNull(creatures.SpawnAt(Species.Shadewyrm, Mathf.FloorToInt(player.Body.position.x) + 10, player.Body.position.y), "no shadewyrm outside the cold traps");
            // A polar cold trap: the shadewyrm.
            int trap = MercuryLandforms.ColdTrapCentre(0, side.Config.worldWidth);
            yield return PutAt(trap + 0.5f);
            var w = SpawnNear(Species.Shadewyrm);
            if (w == null) fails.Add("Shadewyrm: refused in the cold trap"); else yield return CheckPlacement(w, fails, log);
            TestContext.Out.WriteLine("[MERIDIAN] Mercury placement:\n" + log);
            Assert.IsEmpty(fails, string.Join("\n", fails));
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator VenusSpeciesSpawnWhereTheyLive()
        {
            yield return Boot(PlanetId.Venus);
            var fails = new List<string>();
            var log = new System.Text.StringBuilder();
            // The deck: on the Meridian station.
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            float until = Time.realtimeSinceStartup + 5f;
            while (side.pois.Solids.Count < 5 && Time.realtimeSinceStartup < until) yield return null;
            yield return PutAt(new Vector2(station.x + 10f, station.floatY + (336f - 62f) / 128f + 1.5f));
            foreach (var s in new[] { Species.SulfurDrifter, Species.Acidmoth, Species.VeilSerpent })
            {
                var c = SpawnNear(s);
                if (c == null) { fails.Add(s + ": refused on the deck"); continue; }
                yield return CheckPlacement(c, fails, log);
                creatures.Despawn(c);
            }
            Assert.IsNull(SpawnNear(Species.PressureCrab), "no crabs on the station");
            // The plains: the pressure crab.
            int plains = VenusLandforms.Tesserae[0].x1 + 100;
            yield return PutAt(plains + 0.5f);
            var crab = SpawnNear(Species.PressureCrab);
            if (crab == null) fails.Add("PressureCrab: refused on the plains"); else { yield return CheckPlacement(crab, fails, log); creatures.Despawn(crab); }
            // A vent field: the vent eel.
            var vent = VenusLandforms.Vents[0];
            yield return PutAt((vent.x0 + vent.x1) * 0.5f);
            var eel = SpawnNear(Species.VentEel);
            if (eel == null) fails.Add("VentEel: refused in the vent field"); else yield return CheckPlacement(eel, fails, log);
            TestContext.Out.WriteLine("[MERIDIAN] Venus placement:\n" + log);
            Assert.IsEmpty(fails, string.Join("\n", fails));
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>U-192 (LEAD cycle 291; G6 ruled 11-09): the veil serpent is a gentle drifter drawn at 1x of B-224's sheet (a 3.5 m
        /// serpent; it was drawn 3x and hunted from 18 m). Far from the surveyor it meanders; inside 8 m it swerves away in height with
        /// its attack clip as the swerve; it never chases and never bumps.</summary>
        [UnityTest]
        public IEnumerator TheVeilSerpentDriftsAndPartsAroundTheSurveyor()
        {
            yield return Boot(PlanetId.Venus);
            var spec = SpeciesSpec.Get(Species.VeilSerpent);
            Assert.AreEqual(Temper.Drifts, spec.temper, "a gentle drifter");
            Assert.AreEqual(1f, spec.artScale, 1e-6f, "drawn at 1x of its sheet");
            Assert.AreEqual(3.5f, spec.size.x, 1e-4f, "a 3.5 m serpent");
            Assert.AreEqual(8f, spec.senseRange, 1e-4f, "it parts around what comes within 8 m");
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            float until = Time.realtimeSinceStartup + 5f;
            while (side.pois.Solids.Count < 5 && Time.realtimeSinceStartup < until) yield return null;
            yield return PutAt(new Vector2(station.x + 10f, station.floatY + (336f - 62f) / 128f + 1.5f));
            creatures.autoSpawn = false;
            creatures.DespawnAll();
            Vector2 p = player.Body.position;
            Assert.Less(Vector2.Distance(creatures.PartedAround(), p), 0.5f, "on foot, it is the surveyor it parts around");
            int bumps = creatures.Bumps;

            // far off: it meanders on, no swerve
            var far = creatures.Spawn(Species.VeilSerpent, p + new Vector2(22f, 5f));
            Assert.NotNull(far);
            for (int i = 0; i < 300 && far.Held; i++) yield return new WaitForFixedUpdate();
            bool chased = false;
            for (int i = 0; i < 100; i++) { chased |= far.State == CreatureState.Chase || far.State == CreatureState.Flee; yield return new WaitForFixedUpdate(); }
            Assert.IsFalse(chased, "22 m off it neither chases nor flees");
            Assert.AreEqual(0, far.Swerves, "and does not swerve");
            Assert.AreEqual(1f, far.View.transform.localScale.x, 1e-4f, "the view at 1x");
            Assert.That(far.View.bounds.size.x, Is.InRange(3f, 4.6f), "drawn about 4 m across (a 256 px frame at 64 px a metre), not 12");
            creatures.Despawn(far);

            // close, a little above the surveyor: it swerves off upward, its attack clip the swerve, and never comes at the surveyor
            var near = creatures.Spawn(Species.VeilSerpent, p + new Vector2(4f, 1.5f));
            Assert.NotNull(near);
            for (int i = 0; i < 300 && near.Held; i++) yield return new WaitForFixedUpdate();
            float gap0 = Mathf.Abs(near.Body.position.y - p.y);
            bool clip = false; chased = false;
            for (int i = 0; i < 150; i++) { chased |= near.State == CreatureState.Chase; clip |= near.AttackClipPlaying; yield return new WaitForFixedUpdate(); }
            float gap1 = Mathf.Abs(near.Body.position.y - player.Body.position.y);
            TestContext.Out.WriteLine($"[MERIDIAN] u192 serpent: swerves {near.Swerves}, the height between it and the surveyor {gap0:0.0} -> {gap1:0.0} m, steering for {near.SteersFor - player.Body.position.y:+0.0;-0.0} m, state {near.State}, bumps {creatures.Bumps - bumps}");
            Assert.IsFalse(chased, "it never chases");
            Assert.GreaterOrEqual(near.Swerves, 1, "inside 8 m it swerves");
            Assert.IsTrue(clip, "its attack clip plays as the swerve");
            Assert.Greater(near.SteersFor, player.Body.position.y + gap0, "it steers for a height further above the surveyor than it began");
            Assert.Greater(gap1, gap0 + 0.5f, "and has moved off");
            Assert.AreEqual(bumps, creatures.Bumps, "it never bumps the surveyor");
            creatures.DespawnAll();
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AiStaysUnderHalfAMillisecondWith20InnerCreatures()
        {
            yield return Boot(PlanetId.Mercury);
            float x0 = player.Body.position.x + 40f;
            DawnAt(x0);
            yield return PutAt(x0);
            var mix = new[] { Species.Glassback, Species.Cinderling, Species.Flarewing, Species.Cinderhulk };
            int guard = 0;
            for (int i = 0; creatures.AliveCount < CreatureDirector.MaxCreatures && guard < 400; guard++)
            {
                var s = mix[i % mix.Length];
                var spec = SpeciesSpec.Get(s);
                if (creatures.CountOf(s) >= spec.maxAlive) { i++; continue; }
                float px = player.Body.position.x - 18f + creatures.AliveCount * 1.9f;
                int tx = Mathf.FloorToInt(px);
                float y = spec.Flies ? side.terrain.TopSolidY(tx) + 6f : side.terrain.TopSolidY(tx) + 1f + spec.size.y * 0.5f + 0.05f;
                creatures.Spawn(s, new Vector2(tx + 0.5f, y));
                i++;
            }
            Assert.AreEqual(CreatureDirector.MaxCreatures, creatures.AliveCount);
            Assert.Greater(creatures.CountOf(Species.Flarewing), 0, "fliers in the mix");
            // D-193: the warm-up (its worst frame held to 2.0 ms), then the steady window: D-047's limits, 0 B and no collection a frame
            yield return CreatureTests.MeasureAi(creatures, "20 Mercury creatures");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
