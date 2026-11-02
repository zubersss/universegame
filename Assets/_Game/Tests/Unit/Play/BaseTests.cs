using System.Collections;
using System.IO;
using Meridian.Building;
using Meridian.Core;
using Meridian.Items;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Save;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-056 (PlayMode): an enclosed shelter stops the Cryo drain; an aerostat sinks when overloaded; save/load keeps the base.</summary>
    public class BaseTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string root;
        SceneDirector director;
        PlanetSideRoot side;

        [SetUp] public void SetUp() { root = Path.Combine(Application.temporaryCachePath, "meridian_base_" + System.Guid.NewGuid().ToString("N").Substring(0, 6)); SaveSystem.RootOverride = root; }
        [TearDown] public void TearDown() { SaveSystem.RootOverride = null; if (Directory.Exists(root)) Directory.Delete(root, true); }

        IEnumerator Boot(PlanetId planet)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            GameState.Instance.basePieces.Clear();
            GameState.Instance.aerostats.Clear();
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(planet));
            GameState.Instance.currentPlanet = planet; // the save reloads this planet
            side = director.PlanetSide;
            Assert.NotNull(side.bases, "BaseBuilder on PlanetSide");
            if (side.wardens != null) side.wardens.enabled = false;
            var v = side.player.GetComponent<Meridian.Player.PlayerVitals>();
            v.maxHealth = v.health = 1e6f;
        }

        IEnumerator StandAt(int x)
        {
            var t = side.terrain;
            var feet = new Vector2(x + 0.5f, t.Generator.SurfaceHeight(t.WrapX(x)) + 1.05f);
            side.player.Body.position = feet; side.player.transform.position = feet; side.player.Body.linearVelocity = Vector2.zero;
            yield return null;
            float until = Time.realtimeSinceStartup + 15f;
            while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
            // The real ground once it's loaded (stamps can raise it above the generator's surface).
            feet = new Vector2(x + 0.5f, t.TopSolidY(x) + 1.05f);
            side.player.Body.position = feet; side.player.transform.position = feet; side.player.Body.linearVelocity = Vector2.zero;
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            TestContext.Out.WriteLine($"[MERIDIAN] stand at {x}: placed {feet}, settled {side.player.Body.position}, top {t.TopSolidY(x)}, collision {t.IsCollisionReady(x, t.TopSolidY(x))}");
        }

        /// <summary>Walls from the ground up at columns x0 and x1, and a roof across, around the surveyor.</summary>
        void BuildShelter(int x0, int x1, int roofY)
        {
            var t = side.terrain;
            var bases = side.bases;
            // One wall through the Builder, from the inventory, as the player does it.
            var inv = GameState.Instance.inventory;
            inv.Clear();
            inv.Add(ItemRegistry.Get("shelter_wall").id, 4);
            inv.Select(0);
            int g0 = t.TopSolidY(x0) + 1;
            Assert.IsTrue(side.rig.Place(new Vector2(x0 + 0.5f, g0 + 0.5f)), "the Builder places a shelter wall");
            Assert.AreEqual(3, inv.Count(ItemRegistry.Get("shelter_wall").id), "one used");
            foreach (int x in new[] { x0, x1 })
                for (int y = t.TopSolidY(x) + 1; y < roofY; y++)
                    if (bases.PieceAt(new Vector2Int(x, y)) == null) Assert.NotNull(bases.Place(new Vector2(x + 0.5f, y + 0.5f), PieceKind.Wall), $"wall at {x},{y}");
            for (int x = x0; x <= x1; x++)
                Assert.NotNull(bases.Place(new Vector2(x + 0.5f, roofY + 0.5f), PieceKind.Wall), $"roof at {x}");
        }

        [UnityTest]
        public IEnumerator AnEnclosedShelterStopsTheCryoDrainAndSurvivesSaveLoad()
        {
            yield return Boot(PlanetId.Mars);
            side.dayNight.Override = 0f; // Mars night: Cryo 2
            var hz = side.hazards;
            hz.enabled = false;
            hz.Equip(0);
            int px = Mathf.FloorToInt(side.player.Body.position.x) + 200; // open plains, well clear of the camp
            yield return StandAt(px);
            hz.RestoreSuit();
            hz.Step(0.1f);
            Assert.IsFalse(hz.Warm);
            Assert.Less(hz.SuitRate, 0f, "the Mars night drains the suit outside");

            var t = side.terrain;
            int top = Mathf.Max(t.TopSolidY(px - 2), Mathf.Max(t.TopSolidY(px - 1), Mathf.Max(t.TopSolidY(px), Mathf.Max(t.TopSolidY(px + 1), t.TopSolidY(px + 2)))));
            BuildShelter(px - 2, px + 2, top + 4);
            yield return null;
            bool inside = side.bases.Sheltered(side.player.Body.position);
            TestContext.Out.WriteLine($"[MERIDIAN] shelter: player {side.player.Body.position}, px {px}, tops {t.TopSolidY(px - 2)} {t.TopSolidY(px - 1)} {t.TopSolidY(px)} {t.TopSolidY(px + 1)} {t.TopSolidY(px + 2)}, roof {top + 4}; {side.bases.LastFlood}");
            Assert.IsTrue(inside, "the surveyor is inside a sealed shelter");
            hz.Step(0.1f);
            Assert.IsTrue(hz.Warm, "the shelter counts as warmth");
            Assert.GreaterOrEqual(hz.SuitRate, 0f, "no Cryo drain inside");
            float suit = hz.SuitIntegrity;
            for (int i = 0; i < 50; i++) hz.Step(0.1f);
            Assert.GreaterOrEqual(hz.SuitIntegrity, suit, "5 s inside: nothing lost");

            // Save → wipe → load: the base comes back, still sealed.
            int count = side.bases.pieces.Count;
            Assert.AreEqual(count, GameState.Instance.basePieces.Count);
            SaveSystem.Instance.Save();
            GameState.Instance.basePieces.Clear();
            side.bases.ConfigureFor(PlanetId.Mars);
            Assert.AreEqual(0, side.bases.pieces.Count, "wiped");
            yield return SaveSystem.Instance.Load();
            side = director.PlanetSide;
            Assert.AreEqual(count, side.bases.pieces.Count, "the base is rebuilt from the save");
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            side.dayNight.Override = 0f;
            side.hazards.enabled = false;
            side.hazards.Equip(0);
            Assert.IsTrue(side.bases.Sheltered(side.player.Body.position), "still sealed after load");

            // Open a wall: the cold comes in.
            var wall = new Vector2(px - 2 + 0.5f, t.TopSolidY(px - 2) + 1.5f);
            Assert.IsTrue(side.rig.Dig(wall), "the Beam takes a wall down");
            Assert.IsFalse(side.bases.Sheltered(side.player.Body.position), "a gap: no shelter");
            side.hazards.Step(0.1f);
            Assert.Less(side.hazards.SuitRate, 0f, "the drain resumes");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator AnOverloadedAerostatSinks()
        {
            yield return Boot(PlanetId.Venus);
            side.hazards.enabled = false;
            var station = PoiCatalog.MeridianStation;
            float until = Time.realtimeSinceStartup + 5f;
            while (side.pois.Solids.Count < 5 && Time.realtimeSinceStartup < until) yield return null;
            // Keep the surveyor on the station deck; build in open air 40 m off.
            var feet = new Vector2(station.x + 10f, station.floatY + (336f - 62f) / 128f + 1.5f);
            side.player.Body.position = feet; side.player.transform.position = feet;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            var bases = side.bases;
            int x = Mathf.FloorToInt(station.x - 40f), y = Mathf.FloorToInt(VenusLandforms.DeckY);
            Assert.IsNull(bases.Place(new Vector2(x + 10.5f, y + 0.5f), PieceKind.Wall), "a wall needs support; only a deck floats");
            var deck = bases.Place(new Vector2(x + 0.5f, y + 0.5f), PieceKind.Deck);
            Assert.NotNull(deck, "a deck in open air starts an aerostat");
            Assert.NotNull(deck.aerostat);
            Assert.NotNull(bases.Place(new Vector2(x + 2.5f, y + 0.5f), PieceKind.Deck), "a second deck joins it");
            Assert.NotNull(bases.Place(new Vector2(x + 0.5f, y + 1.5f), PieceKind.FloatCell), "a float cell lifts it");
            var lamp = bases.Place(new Vector2(x + 1.5f, y + 1.5f), PieceKind.Lamp);
            Assert.NotNull(lamp, "a lamp on the deck");
            var light = lamp.go.GetComponentInChildren<UnityEngine.Rendering.Universal.Light2D>();
            Assert.NotNull(light, "lamps cast light (U-064)");
            Assert.AreEqual(BaseBuilder.LampRadius, light.pointLightOuterRadius, 1e-3f);
            // U-064 (LEAD cycle 161): the ground must take 2D light, or a lamp casts no pool and night never darkens it.
            var lit = Meridian.Rendering.ArtMaterials.Active.lit;
            int chunks = 0;
            foreach (var r in side.terrain.GetComponentsInChildren<UnityEngine.Tilemaps.TilemapRenderer>())
            {
                chunks++;
                Assert.AreSame(lit, r.sharedMaterial, $"{r.name}: terrain uses the lit sprite material");
            }
            Assert.Greater(chunks, 0, "terrain chunks loaded");
            bases.Dismantle(new Vector2(x + 1.5f, y + 1.5f));
            var a = deck.aerostat;
            Assert.AreEqual(1, bases.aerostats.Count);
            Assert.AreEqual(6f, a.Lift); Assert.AreEqual(4f, a.Load);
            float y0 = a.Position.y;
            yield return new WaitForSeconds(1f);
            Assert.AreEqual(y0, a.Position.y, 1e-3f, "lift ≥ load: it holds its height");

            // Overload: two crates (+4) → load 8 > lift 6.
            Assert.NotNull(bases.Place(new Vector2(x + 2.5f, y + 1.5f), PieceKind.Crate));
            Assert.NotNull(bases.Place(new Vector2(x + 3.5f, y + 1.5f), PieceKind.Crate));
            Assert.AreEqual(-2f, a.Margin);
            yield return new WaitForSeconds(1.5f);
            float sunk = y0 - a.Position.y;
            TestContext.Out.WriteLine($"[MERIDIAN] overloaded aerostat sank {sunk:F2} m in 1.5 s");
            Assert.Greater(sunk, 1f, "it sinks when overloaded");

            // Save/load keeps the aerostat, how far it sank, and its pieces.
            SaveSystem.Instance.Save();
            float saved = a.save.sunk;
            yield return SaveSystem.Instance.Load();
            side = director.PlanetSide;
            Assert.AreEqual(1, side.bases.aerostats.Count);
            Assert.AreEqual(5, side.bases.aerostats[0].pieces.Count);
            Assert.GreaterOrEqual(side.bases.aerostats[0].save.sunk, saved - 0.01f, "how far it sank is kept (it goes on sinking)");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
