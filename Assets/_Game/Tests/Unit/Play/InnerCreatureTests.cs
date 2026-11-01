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
    /// the Cinderhulk dies only in the window after it crosses into night; the Veil Serpent only to Cryo rounds;
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
            // The twilight band, dawn side, at the surveyor: glassback, cinderlings, flarewing, Cinderhulk.
            float x0 = player.Body.position.x;
            DawnAt(x0 + 40f);
            yield return PutAt(x0 + 40f);
            foreach (var s in new[] { Species.Glassback, Species.Cinderling, Species.Flarewing, Species.Cinderhulk })
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

        /// <summary>Fires Lance bolts into c from close range until it dies or `shots` are spent.</summary>
        IEnumerator Shoot(LanceBolts lance, Creature c, int shots, bool cryo)
        {
            for (int i = 0; i < shots && c.Alive; i++)
            {
                var at = c.Body.position;
                lance.Fire(at + new Vector2(-2.5f, 0f), Vector2.right, cryo);
                for (int k = 0; k < 6; k++) yield return new WaitForFixedUpdate();
            }
        }

        [UnityTest]
        public IEnumerator CinderhulkDiesOnlyAfterNightfall()
        {
            yield return Boot(PlanetId.Mercury);
            float x0 = player.Body.position.x + 40f;
            DawnAt(x0);
            yield return PutAt(x0);
            var hulk = SpawnNear(Species.Cinderhulk);
            Assert.NotNull(hulk, "a Cinderhulk in the band");
            for (int i = 0; i < 20; i++) yield return null;
            Assert.AreNotEqual(MercuryZone.Night, hulk.Zone);
            var lance = Object.FindAnyObjectByType<LanceBolts>();
            float hp = hulk.Health;
            yield return Shoot(lance, hulk, 3, false);
            Assert.IsTrue(hulk.Alive);
            Assert.AreEqual(hp, hulk.Health, "the white-hot shell shrugs off the Lance");
            Assert.IsTrue(hulk.LastHitShrugged);
            var daySprite = hulk.View.sprite;

            // Night falls on it: move the dawn line 400 m back (it now stands on the night side).
            side.hazards.mercuryClockOffset -= 400f * MercuryTerminator.CreepSecondsPerMetre;
            float until = Time.time + 2f;
            while (hulk.Zone != MercuryZone.Night && Time.time < until) yield return null;
            Assert.AreEqual(MercuryZone.Night, hulk.Zone, "it crossed into night");
            Assert.IsTrue(hulk.Vulnerable, "the shell has cracked");
            // The night sheet whenever it is vulnerable, from the first frame on.
            for (int i = 0; i < 30; i++)
            {
                if (hulk.Vulnerable) StringAssert.Contains("cinderhulk_night", hulk.View.sprite.texture.name, $"frame {i}: vulnerable in the day sheet");
                yield return null;
            }
            Assert.AreNotEqual(daySprite, hulk.View.sprite);
            StringAssert.Contains("cinderhulk_night", hulk.View.sprite.texture.name, "the cooled night sheet");
            int killed = 0;
            System.Action<Creature> count = c => { if (c == hulk) killed++; };
            Creature.Killed += count;
            yield return Shoot(lance, hulk, 16, false);
            Creature.Killed -= count;
            Assert.IsFalse(hulk.Alive, "the Lance kills it in the window");
            Assert.AreEqual(1, killed);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator VeilSerpentFallsOnlyToCryoRounds()
        {
            yield return Boot(PlanetId.Venus);
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            float until = Time.realtimeSinceStartup + 5f;
            while (side.pois.Solids.Count < 5 && Time.realtimeSinceStartup < until) yield return null;
            yield return PutAt(new Vector2(station.x + 10f, station.floatY + (336f - 62f) / 128f + 1.5f));
            var serpent = SpawnNear(Species.VeilSerpent);
            Assert.NotNull(serpent);
            var lance = Object.FindAnyObjectByType<LanceBolts>();
            float hp = serpent.Health;
            yield return Shoot(lance, serpent, 3, false);
            Assert.AreEqual(hp, serpent.Health, "plain rounds glance off");

            // The Rig loads Cryo rounds from the pack: one per shot.
            var inv = GameState.Instance.inventory;
            var cryo = Meridian.Items.ItemRegistry.Get("cryo_round");
            Assert.NotNull(cryo, "cryo_round item");
            inv.Add(cryo.id, 1);
            var rig = player.GetComponent<PlayerRigInput>();
            rig.module = RigModule.Lance;
            rig.AimAt(serpent.Body.position);
            rig.holdUse = true;
            yield return null;
            yield return null;
            rig.holdUse = false;
            Assert.AreEqual(0, inv.Count(cryo.id), "the round was spent");

            // Cryo rounds: a chilled flash, a recoil, then death.
            bool chilled = false;
            int killed = 0;
            System.Action<Creature> count = c => { if (c == serpent) killed++; };
            Creature.Killed += count;
            for (int i = 0; i < 16 && serpent.Alive; i++)
            {
                lance.Fire(serpent.Body.position + new Vector2(-2.5f, 0f), Vector2.right, true);
                for (int k = 0; k < 6; k++)
                {
                    yield return new WaitForFixedUpdate();
                    if (serpent.Alive && serpent.View.color.r < 0.9f && serpent.View.color.b > 0.9f) chilled = true;
                }
            }
            Creature.Killed -= count;
            Assert.IsTrue(chilled, "the chilled flash on its hurt frames");
            Assert.IsFalse(serpent.Alive, "Cryo rounds kill the Veil Serpent");
            Assert.AreEqual(1, killed);
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
            for (int i = 0; i < 30; i++) yield return null;
            var samples = new List<double>(300);
            for (int i = 0; i < 300; i++) { yield return null; samples.Add(creatures.LastAiMs); }
            samples.Sort();
            double median = samples[samples.Count / 2], p99 = samples[(int)(samples.Count * 0.99) - 1], max = samples[samples.Count - 1];
            TestContext.Out.WriteLine($"[MERIDIAN] AI with 20 Mercury creatures: median {median:F3} ms, p99 {p99:F3} ms, max {max:F3} ms");
            Assert.LessOrEqual(median, 0.5, "median ≤ 0.5 ms (U-055, D-047)");
            Assert.LessOrEqual(p99, 0.5, "p99 ≤ 0.5 ms (U-055, D-047)");
            Assert.LessOrEqual(max, 1.0, "worst frame ≤ 2 × 0.5 ms (D-047)");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
