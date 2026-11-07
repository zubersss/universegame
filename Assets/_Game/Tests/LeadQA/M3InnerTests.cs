using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Meridian.Core;
using Meridian.Crafting;
using Meridian.Hazards;
using Meridian.Items;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Save;
using Meridian.Ship;
using Meridian.Space;
using Meridian.Terrain;
using Meridian.Trade;
using Meridian.Transitions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests.LeadQA
{
    /// <summary>
    /// L-012: M3 end-to-end QA over the inner planets. Earth launch → Mercury entry and landing; a forced
    /// flare in and out of a flare shelter; Solarite inside / outside the 90 s window; Venus entry onto the
    /// Meridian station deck with no docking; a radiation liner crafted; a sale at the Earth Waystation;
    /// and the whole run inside a 15-minute budget. Each step boots Core fresh; the budget test sums them.
    /// </summary>
    public class M3InnerTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const float BudgetSeconds = 15f * 60f;
        const int Steps = 6;

        // Step name → game seconds (Time.time, scaled) it took after boot; summed by the budget test.
        static readonly Dictionary<string, float> spent = new Dictionary<string, float>();
        static double worldClockSeconds; // TimeSystem.GameSeconds advanced (72x), logged only

        string saveRoot;
        SceneDirector director;
        TransitionDirector transitions;
        TimeSystem time;
        float t0;
        double clock0;

        [OneTimeSetUp]
        public void OneTimeSetUp()
        {
            spent.Clear();
            worldClockSeconds = 0;
        }

        [SetUp]
        public void SetUp()
        {
            saveRoot = System.IO.Path.Combine(Application.temporaryCachePath, "meridian_leadqa_m3_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = saveRoot;
        }

        [TearDown]
        public void TearDown()
        {
            SaveSystem.RootOverride = null;
            if (System.IO.Directory.Exists(saveRoot)) System.IO.Directory.Delete(saveRoot, true);
        }

        // ---------------------------------------------------------------- 1. Earth → Space → Mercury landing

        [UnityTest, Order(1), Timeout(240000)]
        public IEnumerator Step1_EarthLaunchToMercuryLandingStanding()
        {
            yield return Boot(true);
            var state = GameState.Instance;
            Assert.AreEqual(PlanetId.Earth, state.currentPlanet, "starts on Earth");

            yield return LaunchFromEarth();
            yield return EnterFromOrbit("mercury");
            var side = director.PlanetSide;
            Assert.AreEqual(PlanetId.Mercury, side.Config.id, "on Mercury");
            Assert.AreEqual(ViewMode.PlanetSide, state.view, "side view loaded");
            float timeout = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(side.terrain.IsSettled, "Mercury terrain settled");

            float? touchdown = null;
            yield return PoweredLanding(side.ship, v => touchdown = v);
            Assert.IsTrue(touchdown.HasValue, "touched down on Mercury");
            TestContext.Out.WriteLine($"[LEADQA] Mercury touchdown {touchdown.Value:F2} m/s");
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();

            side.hazards.enabled = false; // standing check only; the flare step drives the hazards by hand
            var boarding = side.ship.GetComponent<ShipBoarding>();
            Assert.IsTrue(boarding.TryExit(), "the surveyor steps out on Mercury");
            var player = side.player;
            for (int i = 0; i < 120 && !player.Grounded; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.gameObject.activeInHierarchy, "surveyor on foot");
            Assert.IsTrue(player.Grounded, "surveyor standing on Mercury");

            Spend(nameof(Step1_EarthLaunchToMercuryLandingStanding));
            LogAssert.NoUnexpectedReceived();
        }

        // ---------------------------------------------------------------- 2. Forced flare: shelter vs open

        [UnityTest, Order(2), Timeout(180000)]
        public IEnumerator Step2_MercuryFlareShelterSavesOpenHurts()
        {
            yield return Boot(false);
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Mercury));
            var side = director.PlanetSide;
            var hazards = side.hazards;
            hazards.enabled = false; // stepped by hand, as in HazardV2PlayTests
            var player = side.player;
            var vitals = player.GetComponent<PlayerVitals>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();

            // Walk away from the ship's warmth onto open ground.
            int x = Mathf.FloorToInt(player.Body.position.x - 30f);
            var feet = new Vector2(x + 0.5f, side.terrain.TopSolidY(x) + 1.05f);
            player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero;
            yield return null;
            timeout = Time.realtimeSinceStartup + 15f;
            while (!side.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();

            // Put the surveyor in the twilight band (flares reach it) by shifting Mercury's clock.
            var mercury = side.Config;
            hazards.mercuryClockOffset = Mathf.Repeat(player.Body.position.x, mercury.worldWidth) * MercuryTerminator.CreepSecondsPerMetre
                                         - MercuryTerminator.Now(time.GameSeconds);
            hazards.Step(0f);
            Assert.AreEqual(MercuryZone.Twilight, hazards.Context.mercury, "in Mercury's twilight band");
            Assert.IsFalse(hazards.Warm, "away from any warmth");

            // Inside a flare shelter: the whole flare passes with no health lost.
            var shelter = new GameObject("LeadQA_FlareShelter").AddComponent<FlareShelter>();
            shelter.transform.position = player.Body.position;
            vitals.health = vitals.maxHealth;
            hazards.RestoreSuit();
            hazards.flares.Force(0f);
            Assert.AreEqual(SolarFlares.Phase.Active, hazards.flares.Current, "flare forced");
            hazards.Step(0f);
            Assert.Less(hazards.EffectiveLevel, HazardRules.FlareLevel, "the shelter stops the flare");
            Assert.IsTrue(float.IsPositiveInfinity(SurviveSeconds(hazards, vitals, SolarFlares.ActiveSeconds)), "survives the flare inside the shelter");
            Assert.AreEqual(vitals.maxHealth, vitals.health, 1e-3f, "no flare damage inside the shelter");
            float suitInShelter = hazards.SuitIntegrity;
            Object.Destroy(shelter.gameObject);
            yield return null; // OnDisable drops it from the shelter list

            // Same flare in the open: Radiation 4, the suit drains and health goes.
            Assert.IsFalse(FlareShelter.AnyCovers(player.Body.position), "now outside every shelter");
            vitals.health = vitals.maxHealth;
            hazards.RestoreSuit();
            if (hazards.flares.Current != SolarFlares.Phase.Active) hazards.flares.Force(0f);
            hazards.Step(0f);
            Assert.AreEqual(HazardRules.FlareLevel, hazards.EffectiveLevel, "Radiation 4 in the open");
            float died = SurviveSeconds(hazards, vitals, SolarFlares.ActiveSeconds);
            TestContext.Out.WriteLine($"[LEADQA] flare: suit {suitInShelter:F1} left in shelter; in the open dead after {died:F1} s");
            Assert.Less(hazards.SuitIntegrity, suitInShelter, "the open drains the suit harder than the shelter");
            Assert.Less(vitals.health, vitals.maxHealth, "flare damage taken in the open");
            vitals.Restore();

            Spend(nameof(Step2_MercuryFlareShelterSavesOpenHurts));
            LogAssert.NoUnexpectedReceived();
        }

        // ---------------------------------------------------------------- 3. Solarite window

        [UnityTest, Order(3), Timeout(180000)]
        public IEnumerator Step3_SolariteMineableAt30sNotAt120s()
        {
            // Same approach as SolariteTests (U-059): shift the flare clock with SolarFlares.EndedAt.
            yield return Boot(false);
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Mercury));
            var side = director.PlanetSide;
            side.hazards.enabled = false;
            var crystals = side.solarite;
            Assert.NotNull(crystals, "SolariteCrystals on PlanetSide");
            Assert.NotNull(crystals.flares, "bound to the flare clock");

            var field = PoiCatalog.For(PlanetId.Mercury).First(p => p.id == SolariteCrystals.FieldId);
            int x = Mathf.FloorToInt(field.x + 7f);
            var player = side.player;
            var feet = new Vector2(x + 0.5f, side.terrain.Generator.SurfaceHeight(side.terrain.WrapX(x)) + 1.05f);
            player.Body.position = feet; player.transform.position = feet; player.Body.linearVelocity = Vector2.zero;
            yield return null;
            float timeout = Time.realtimeSinceStartup + 15f;
            while ((!side.terrain.IsSettled || crystals.Clusters == 0) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
            Assert.Greater(crystals.Clusters, 0, "crystal clusters at the field");
            var near = crystals.Centres.OrderBy(c => (c - player.Body.position).sqrMagnitude).First();
            Assert.LessOrEqual(Vector2.Distance(near, player.Body.position), Meridian.Rig.RigTools.Reach, "a cluster in reach");
            var rig = side.rig;
            int solarite = ItemRegistry.Get("solarite").id;

            Assert.Less(30f, OnlyHere.SolariteWindow, "+30 s is inside the window");
            crystals.flares.EndedAt(Time.time - 30f);
            yield return null;
            Assert.IsTrue(crystals.Harvestable, "harvestable at +30 s");
            int before = rig.drops.Live.Count(d => d.itemId == solarite);
            Assert.IsTrue(rig.Dig(near), "the Beam cuts Solarite at +30 s");
            Assert.AreEqual(SolariteCrystals.Result.Harvested, crystals.LastResult);
            Assert.AreEqual(before + 1, rig.drops.Live.Count(d => d.itemId == solarite), "a Solarite drop");

            Assert.Greater(120f, OnlyHere.SolariteWindow, "+120 s is outside the window");
            crystals.flares.EndedAt(Time.time - 120f);
            yield return null;
            Assert.IsFalse(crystals.Harvestable, "crusted at +120 s");
            Assert.IsFalse(rig.Dig(near), "nothing at +120 s");
            Assert.AreEqual(SolariteCrystals.Result.Crusted, crystals.LastResult);

            Spend(nameof(Step3_SolariteMineableAt30sNotAt120s));
            LogAssert.NoUnexpectedReceived();
        }

        // ---------------------------------------------------------------- 4. Venus: straight onto the deck

        [UnityTest, Order(4), Timeout(240000)]
        public IEnumerator Step4_VenusEntryOntoStationDeckWithoutDocking()
        {
            yield return Boot(true);
            var state = GameState.Instance;
            yield return LaunchFromEarth();
            yield return EnterFromOrbit("venus");
            var side = director.PlanetSide;
            Assert.AreEqual(PlanetId.Venus, side.Config.id, "on Venus");
            Assert.AreEqual(PlanetId.Venus, state.currentPlanet);
            side.hazards.enabled = false; // the deck's acid haze is covered by VenusPlayTests

            // Fly the Pilgrim over the Meridian station and hold it there while the deck loads.
            var station = PoiCatalog.MeridianStation;
            float deck = station.floatY + (336f - 62f) / 128f; // the old card's rows: a hover estimate only; the real deck is read from the colliders below (D-124)
            var ship = side.ship;
            ship.externalInput = true;
            ship.intent = default;
            var hover = new Vector2(station.x + 10f, deck + SideShip.SkidDrop + 12f);
            float timeout = Time.realtimeSinceStartup + 20f;
            do
            {
                ship.Body.position = hover; ship.transform.position = hover; ship.Body.linearVelocity = Vector2.zero;
                yield return new WaitForFixedUpdate();
            } while ((side.pois.Solids.Count < 5 || !side.terrain.IsSettled) && Time.realtimeSinceStartup < timeout);
            Assert.GreaterOrEqual(side.pois.Solids.Count, 5, "station deck colliders loaded");

            // D-124 / R1: the deck is the station prop's declared collider top, as VenusPlayTests.Deck.
            float deckTop = float.NegativeInfinity;
            foreach (var c in side.pois.Solids) if (c != null && Mathf.Abs(c.bounds.center.x - (station.x + 10f)) < 40f) deckTop = Mathf.Max(deckTop, c.bounds.max.y);
            Assert.Greater(deckTop, float.NegativeInfinity, "a station collider within 40 m of the hover column");
            deck = deckTop;

            // Powered landing onto the deck: no docking bay, no clamp.
            float? touchdown = null;
            yield return PoweredLanding(ship, v => touchdown = v);
            Assert.IsTrue(touchdown.HasValue, "touched down on the station");
            TestContext.Out.WriteLine($"[LEADQA] Venus deck touchdown {touchdown.Value:F2} m/s at y {ship.Body.position.y:F2} (deck {deck:F2})");
            Assert.Greater(ship.Body.position.y, deck - 1f, "landed on the deck, not the surface below");
            Assert.IsFalse(DockingBay.AnyOpen, "no docking involved");
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();

            var boarding = ship.GetComponent<ShipBoarding>();
            Assert.IsTrue(boarding.TryExit(), "the surveyor steps out onto the deck");
            var player = side.player;
            for (int i = 0; i < 90 && !player.Grounded; i++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(player.Grounded, "standing on the deck");
            Assert.AreEqual(deck, player.Body.position.y, 0.3f, "on the deck surface");

            Spend(nameof(Step4_VenusEntryOntoStationDeckWithoutDocking));
            LogAssert.NoUnexpectedReceived();
        }

        // ---------------------------------------------------------------- 5. Craft a radiation liner

        [UnityTest, Order(5), Timeout(120000)]
        public IEnumerator Step5_CraftRadiationLinerAtFabricator()
        {
            yield return Boot(true);
            var side = director.PlanetSide;
            var player = side.player;
            var inv = GameState.Instance.inventory;
            inv.Clear();
            var hud = Object.FindAnyObjectByType<Meridian.UI.SideHud>();
            Assert.NotNull(hud, "SideHud");
            var panel = hud.Crafting;
            var book = RecipeBook.Active;
            Assert.NotNull(book, "RecipeBook in Resources");
            var liner = book.FindRecipe("fab_radiation_liner");
            Assert.NotNull(liner, "fab_radiation_liner in RecipeBook.asset");
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();

            // Inputs (RecipeBook.asset: 1 iron bar + 2 graphite) straight into the hold.
            inv.Add(ItemRegistry.Get("smelter_bar_iron").id, 1);
            inv.Add(ItemRegistry.Get("graphite").id, 2);

            // At the Pilgrim's Fabricator (as CraftingPlayTests).
            panel.SetOpen(true);
            Vector2 shipAt = side.ship.transform.position;
            player.Body.position = new Vector2(shipAt.x - 3f, shipAt.y - 1f);
            player.transform.position = player.Body.position;
            yield return new WaitForFixedUpdate();
            Assert.AreEqual(CraftingSystem.Result.Crafted, panel.Craft(liner), panel.LastMessage);
            Assert.AreEqual(1, inv.Count(ItemRegistry.Get("radiation_liner").id), "a radiation liner");
            Assert.AreEqual(0, inv.Count(ItemRegistry.Get("smelter_bar_iron").id), "bar used");
            Assert.AreEqual(0, inv.Count(ItemRegistry.Get("graphite").id), "graphite used");
            panel.SetOpen(false);

            Spend(nameof(Step5_CraftRadiationLinerAtFabricator));
            LogAssert.NoUnexpectedReceived();
        }

        // ---------------------------------------------------------------- 6. Sell at the Earth Waystation

        [UnityTest, Order(6), Timeout(120000)]
        public IEnumerator Step6_SellAtEarthWaystationRaisesScrip()
        {
            yield return Boot(false);
            director.SetView(ViewMode.Space);
            for (int i = 0; i < 10; i++) yield return null;
            var bay = director.Space.GetComponent<DockingBay>();
            Assert.NotNull(bay, "DockingBay on the Space root");
            var ship = director.Space.GetComponentInChildren<SpaceShip>();
            var state = GameState.Instance;
            var inv = state.inventory;
            inv.Clear();

            var earth = Waystation.All.Find(w => w.planet == "earth");
            Assert.NotNull(earth, "Earth Waystation");
            ship.externalInput = true;
            ship.Position = (Vector2)earth.transform.position + new Vector2(4f, -3f);
            ship.Velocity = new Vector2(1f, 0f);
            Assert.IsTrue(bay.Dock("earth"), bay.LastMessage);
            yield return null;

            inv.Add(ItemRegistry.Get("iron").id, 10);
            int scrip0 = state.scrip;
            Assert.IsTrue(bay.SellItem("iron", 10), bay.LastMessage);
            Assert.Greater(state.scrip, scrip0, "Scrip increases");
            Assert.AreEqual(scrip0 + 10 * Market.SellPrice("earth", "iron"), state.scrip, "at Earth's price");
            bay.Undock();
            yield return null;

            Spend(nameof(Step6_SellAtEarthWaystationRaisesScrip));
            LogAssert.NoUnexpectedReceived();
        }

        // ---------------------------------------------------------------- 7. 15-minute budget

        [UnityTest, Order(7)]
        public IEnumerator Step7_WholeInnerRunWithin15Minutes()
        {
            yield return null;
            float total = spent.Values.Sum();
            TestContext.Out.WriteLine($"[LEADQA] M3 inner run: {spent.Count}/{Steps} steps, {total:F1} s game time (Time.time), " +
                                      $"{worldClockSeconds / 60.0:F1} world-clock min (72x)");
            foreach (var kv in spent) TestContext.Out.WriteLine($"[LEADQA]   {kv.Key}: {kv.Value:F1} s");
            LogAssert.NoUnexpectedReceived();
            if (spent.Count < Steps) Assert.Ignore($"budget needs the whole fixture: only {spent.Count}/{Steps} steps passed");
            Assert.LessOrEqual(total, BudgetSeconds, "the inner-planet run fits in ≤ 15 min game time");
        }

        // ---------------------------------------------------------------- helpers

        IEnumerator Boot(bool settleEarth)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            yield return SceneManager.LoadSceneAsync("Core", LoadSceneMode.Single);
#endif
            director = Object.FindAnyObjectByType<SceneDirector>();
            Assert.NotNull(director, "SceneDirector in Core");
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || (settleEarth && !director.PlanetSide.terrain.IsSettled)) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady, "boot");
            transitions = Object.FindAnyObjectByType<TransitionDirector>();
            time = Object.FindAnyObjectByType<TimeSystem>();
            Assert.NotNull(time, "TimeSystem in Core");
            if (settleEarth) for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            t0 = Time.time;
            clock0 = time.GameSeconds;
        }

        void Spend(string step)
        {
            spent[step] = Time.time - t0;
            worldClockSeconds += time.GameSeconds - clock0;
        }

        /// <summary>Earth → Space as MercuryEntryTests: aboard, just under the Escape Line, climbing.</summary>
        IEnumerator LaunchFromEarth()
        {
            var side = director.PlanetSide;
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p; ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            yield return WaitIdle(transitions, 15f);
            Assert.AreEqual(ViewMode.Space, GameState.Instance.view, "in space after launch");
        }

        /// <summary>Space → a planet's side view through its entry ring (as MercuryEntryTests).</summary>
        IEnumerator EnterFromOrbit(string body)
        {
            var craft = director.Space.GetComponentInChildren<SpaceShip>();
            craft.externalInput = true;
            craft.intent = default;
            float timeout = Time.realtimeSinceStartup + 10f;
            while (craft.Invulnerable && Time.realtimeSinceStartup < timeout) yield return null;
            var info = craft.world.Find(body);
            Assert.IsTrue(info.HasValue, body + " in the space layout");
            var target = info.Value;
            craft.Position = target.position + new Vector2(0f, target.RingRadius + 0.5f);
            craft.Velocity = new Vector2(0f, -40f);
            yield return WaitIdle(transitions, 20f);
            Assert.AreEqual(ViewMode.PlanetSide, GameState.Instance.view, "entered " + body);
            TestContext.Out.WriteLine($"[LEADQA] {body} entry {transitions.LastEntrySeconds:F2} s");
        }

        /// <summary>Powered descent (as M1LoopTests): fast high up, ≤ 2 m/s near the ground.</summary>
        static IEnumerator PoweredLanding(SideShip ship, System.Action<float> onTouchdown)
        {
            ship.externalInput = true;
            bool down = false;
            System.Action<float> handler = v => { down = true; onTouchdown(v); };
            ship.TouchedDown += handler;
            float timeout = Time.realtimeSinceStartup + 120f;
            while (!down && Time.realtimeSinceStartup < timeout)
            {
                float alt = ship.AltitudeAboveGround;
                float targetVy = -Mathf.Clamp(alt * 0.25f, 2f, 15f);
                float accel = (targetVy - ship.Body.linearVelocity.y) * 2f + ship.Gravity;
                ship.intent = new ShipSideIntent { thrust = Mathf.Clamp01(accel / ship.Thrust) };
                yield return new WaitForFixedUpdate();
            }
            ship.intent = default;
            ship.TouchedDown -= handler;
        }

        static float SurviveSeconds(HazardSystem hazards, PlayerVitals vitals, float limit)
        {
            const float dt = 0.1f;
            for (float t = 0f; t < limit; t += dt)
            {
                hazards.Step(dt);
                if (vitals.Dead) return t + dt;
            }
            return float.PositiveInfinity;
        }

        static IEnumerator WaitIdle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }
    }
}
