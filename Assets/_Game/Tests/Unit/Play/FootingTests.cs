using System.Collections;
using System.Collections.Generic;
using Meridian.Core;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-064 (PlayMode): the surveyor stands on the top solid tile, feet within 0.1 m, across every POI stamp on
    /// Earth and Mars, around each spawn, and on the Mars polar cap (whose frost once had no collision).
    /// A column under a solid prop (a landing pad deck) only checks the surveyor isn't below the ground.
    /// </summary>
    public class FootingTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const float Tolerance = 0.1f;

        [UnityTest]
        public IEnumerator FeetOnTheGroundAcrossEveryStampOnEarthAndMars()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            var fails = new List<string>();
            var log = new System.Text.StringBuilder();
            int checkedCols = 0, skipped = 0;

            foreach (var planet in new[] { PlanetId.Earth, PlanetId.Mars })
            {
                yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(planet));
                var side = director.PlanetSide;
                side.hazards.enabled = false;
                if (side.wardens != null) side.wardens.enabled = false;
                var v = side.player.GetComponent<Meridian.Player.PlayerVitals>();
                v.maxHealth = v.health = 1e6f;

                var columns = new List<(int x, string where)>();
                for (int x = side.spawnX - 12; x <= side.spawnX + 40; x += 4) columns.Add((x, "spawn"));
                foreach (var poi in PoiCatalog.For(planet))
                {
                    if (poi.Floating) continue;
                    for (int x = poi.x - 2; x <= poi.x + poi.Width + 2; x += 3) columns.Add((x, poi.id));
                }
                if (planet == PlanetId.Mars)
                    for (int x = 20; x < MarsLandforms.CapHalfWidth; x += 24) columns.Add((x, "polar cap"));

                foreach (var (x, where) in columns)
                {
                    var t = side.terrain;
                    var near = new Vector2(x + 0.5f, t.Generator.SurfaceHeight(t.WrapX(x)) + 3f);
                    side.player.Body.position = near; side.player.transform.position = near; side.player.Body.linearVelocity = Vector2.zero;
                    yield return null;
                    float until = Time.realtimeSinceStartup + 10f;
                    while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                    int top = t.TopSolidY(x);
                    var feet = new Vector2(x + 0.5f, top + 1.05f);
                    // A solid body already standing there (the landed Pilgrim's hull on Mars, x 72–76) makes the
                    // spot unstandable: placing the surveyor inside it only measures depenetration. Skip and log.
                    // D-057: every skipped column must lie within the landed ship's footprint (|x − ship x| ≤ 4).
                    Meridian.Ship.SideShip hull = null;
                    foreach (var c in Physics2D.OverlapBoxAll(feet + new Vector2(0f, 0.9f), new Vector2(0.5f, 1.6f), 0f))
                        if (!c.isTrigger && (hull = c.GetComponentInParent<Meridian.Ship.SideShip>()) != null) break;
                    if (hull != null)
                    {
                        float shipX = hull.Body.position.x;
                        log.AppendLine($"{planet} {where} x {x}: skipped, inside {hull.name} (ship x {shipX:F1})");
                        if (Mathf.Abs(x + 0.5f - shipX) > 4f) fails.Add($"{planet} {where} x {x}: skipped outside the ship's footprint (ship x {shipX:F1})");
                        skipped++;
                        continue;
                    }
                    side.player.Body.position = feet; side.player.transform.position = feet; side.player.Body.linearVelocity = Vector2.zero;
                    for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate();
                    float y = side.player.Body.position.y, ground = top + 1f;
                    // A solid prop (pad deck) over the column carries the surveyor higher: only "not below" applies.
                    bool prop = false;
                    foreach (var c in Physics2D.OverlapPointAll(new Vector2(x + 0.5f, ground + 0.6f)))
                        if (c.GetComponentInParent<TerrainChunk>() == null && c.attachedRigidbody != side.player.Body) prop = true;
                    bool ok = prop ? y >= ground - Tolerance : Mathf.Abs(y - ground) <= Tolerance;
                    checkedCols++;
                    if (!ok)
                    {
                        var hits = new System.Text.StringBuilder();
                        foreach (var h in Physics2D.RaycastAll(new Vector2(x + 0.5f, ground + 3f), Vector2.down, 6f))
                            if (h.rigidbody != side.player.Body) hits.Append($" {h.collider.name}@{h.point.y:F2}");
                        string line = $"{planet} {where} x {x}: feet {y:F2}, ground {ground:F0} (top tile {t.GetTile(x, top)}, collision {t.IsCollisionReady(x, top)}, prop {prop})";
                        line += " hits:" + hits;
                        fails.Add(line);
                        log.AppendLine(line);
                    }
                }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] footing: {checkedCols} columns, {skipped} skipped (occupied by a hull), {fails.Count} off\n{log}");
            Assert.GreaterOrEqual(checkedCols, 80, "D-057: at least 80 columns measured");
            Assert.IsEmpty(fails, string.Join("\n", fails));
            LogAssert.NoUnexpectedReceived();
        }
    }
}
