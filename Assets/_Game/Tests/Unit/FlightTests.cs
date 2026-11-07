using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Meridian.Crafting;
using Meridian.EditorTools;
using Meridian.Items;
using Meridian.Planets;
using Meridian.Ship;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-107 (EditMode, Bible §4.3 v4.1, D-102, D-103, D-105, D-106): the upright Pilgrim's flight model, pure. Hover where
    /// thrust = g on all eight planets, Mk1 can't climb Jupiter and Mk3 can, the tilt clamps at 35° and springs back, a
    /// tilted touchdown rights itself with a wobble; and no fuel survives anywhere: no compiled symbol, no string, no item,
    /// recipe or blueprint, no asset name or serialized text outside Assets/_Game/Archive/Fuel~.
    /// </summary>
    public class FlightTests
    {
        const float Dt = 0.02f;

        static PlanetConfig Load(PlanetId id) =>
            AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/{id}.asset");

        /// <summary>Integrates the vertical motion from rest above a floor at y = 0 (semi-implicit, as Box2D).</summary>
        static (float y, float v) Fly(RocketFlight f, float throttle, float thrust, float g, float seconds, float y = 0f, float v = 0f)
        {
            for (float t = 0f; t < seconds; t += Dt)
            {
                f.StepTilt(0f, y <= 0f && throttle <= 0f, Dt);
                v += (f.ThrustAccel(throttle, thrust).y - g) * Dt;
                y += v * Dt;
                if (y < 0f) { y = 0f; v = Mathf.Max(0f, v); } // the pad
            }
            return (y, v);
        }

        [Test]
        public void HoversWhereThrustEqualsGOnAllEightPlanets()
        {
            foreach (PlanetId id in Enum.GetValues(typeof(PlanetId)))
            {
                var c = Load(id);
                Assert.NotNull(c, id.ToString());
                int mark = c.MinThrusterToClimb;
                Assert.LessOrEqual(mark, ShipMarks.MaxMark, $"some mark climbs on {id}");
                float thrust = ShipMarks.Thrust(mark);
                float throttle = c.gravity / thrust;
                Assert.That(throttle * thrust, Is.EqualTo(c.gravity).Within(1).Percent, $"{id}: thrust = g");
                const float seconds = 10f, start = 100f;
                var (y, v) = Fly(new RocketFlight(), throttle, thrust, c.gravity, seconds, start);
                float freeFall = 0.5f * c.gravity * seconds * seconds;
                TestContext.Out.WriteLine($"[MERIDIAN] hover {id} Mk{mark} throttle {throttle:F3}: Δy {y - start:F4} m, v {v:F4} m/s");
                Assert.That(Mathf.Abs(y - start), Is.LessThanOrEqualTo(0.01f * freeFall), $"{id}: holds height within 1 % of a free fall");
                Assert.That(Mathf.Abs(v), Is.LessThanOrEqualTo(0.01f * c.gravity * seconds), $"{id}: holds speed within 1 % of g·t");
            }
        }

        [Test]
        public void Mk1CannotClimbJupiterMk3Can()
        {
            float g = Load(PlanetId.Jupiter).gravity;
            Assert.AreEqual(24.79f, g, 0.01f);
            Assert.AreEqual(0f, Fly(new RocketFlight(), 1f, ShipMarks.Thrust(1), g, 5f).y, 1e-5f, "Mk1 stays on the pad");
            Assert.AreEqual(0f, Fly(new RocketFlight(), 1f, ShipMarks.Thrust(2), g, 5f).y, 1e-5f, "Mk2 stays on the pad (D-106)");
            float mk3 = Fly(new RocketFlight(), 1f, ShipMarks.Thrust(3), g, 5f).y;
            Assert.Greater(mk3, 100f, "Mk3 climbs at net 10.21 m/s²");
            Assert.Greater(Fly(new RocketFlight(), 1f, ShipMarks.Thrust(1), Load(PlanetId.Neptune).gravity, 5f).y, 5f, "Mk1 crawls off Neptune");
        }

        [Test]
        public void TiltClampsAt35AndSpringsBack()
        {
            var f = new RocketFlight();
            for (int i = 0; i < 100; i++) f.StepTilt(1f, false, Dt);
            Assert.AreEqual(-RocketFlight.MaxTilt, f.Tilt, 1e-4f, "D: nose right, clamped");
            for (int i = 0; i < 100; i++) f.StepTilt(-1f, false, Dt);
            Assert.AreEqual(RocketFlight.MaxTilt, f.Tilt, 1e-4f, "A: nose left, clamped");
            float peak = f.Tilt, min = f.Tilt;
            for (int i = 0; i < 25; i++) { f.StepTilt(0f, false, Dt); min = Mathf.Min(min, f.Tilt); }
            Assert.Less(Mathf.Abs(f.Tilt), 0.5f, "back upright within 0.5 s of release");
            Assert.GreaterOrEqual(min, -0.01f, "the spring does not overshoot");
            Assert.Less(f.Tilt, peak);
            var up = RocketFlight.UpAxis(35f);
            Assert.AreEqual(-Mathf.Sin(35f * Mathf.Deg2Rad), up.x, 1e-5f, "thrust follows the nose");
            var ground = new RocketFlight();
            ground.StepTilt(1f, true, Dt);
            Assert.AreEqual(0f, ground.Tilt, "no tilting on the pad");
        }

        [Test]
        public void TiltedTouchdownRightsInHalfASecondWithAWobble()
        {
            var f = new RocketFlight();
            for (int i = 0; i < 50; i++) f.StepTilt(-1f, false, Dt);
            Assert.IsTrue(f.Touchdown(), "35° > 20°: tips");
            bool past = false;
            int steps = Mathf.CeilToInt(RocketFlight.RightingSeconds / Dt);
            for (int i = 0; i < steps; i++) { f.StepTilt(1f, true, Dt); if (f.Tilt < -0.5f) past = true; }
            Assert.IsTrue(past, "wobbles past upright");
            Assert.IsFalse(f.Righting);
            Assert.AreEqual(0f, f.Tilt, "upright after 0.5 s");
            var mild = new RocketFlight();
            for (int i = 0; i < 4; i++) mild.StepTilt(-1f, false, Dt); // 11.2°
            Assert.IsFalse(mild.Touchdown(), "≤ 20° lands normally");
        }

        // ---------- D-105: no fuel of any kind ----------

        static readonly string[] Retired = { "LaunchFuel", "FuelTank", "LaunchBurn" };

        [Test]
        public void NoFuelSymbolCompiled()
        {
            var asm = typeof(SideShip).Assembly;
            const BindingFlags all = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly;
            var hits = new List<string>();
            foreach (var type in asm.GetTypes())
            {
                if (Bad(type.Name)) hits.Add(type.FullName);
                foreach (var m in type.GetMembers(all))
                    if (Bad(m.Name)) hits.Add($"{type.FullName}.{m.Name}");
            }
            Assert.IsEmpty(hits, "fuel symbols compiled: " + string.Join(", ", hits));
            foreach (var r in Retired) Assert.IsFalse(hits.Any(h => h.Contains(r)), r);

            static bool Bad(string name) => name.IndexOf("fuel", StringComparison.OrdinalIgnoreCase) >= 0
                                         || Retired.Any(r => name.Contains(r));
        }

        [Test]
        public void NoFuelItemRecipeOrBlueprint()
        {
            foreach (var d in ItemRegistry.All)
            {
                Assert.IsFalse(Fuel(d.key) || Fuel(d.name) || Fuel(d.icon), $"item {d.key}");
            }
            foreach (var r in CraftingDefaults.Recipes())
            {
                Assert.IsFalse(Fuel(r.id) || Fuel(r.output.item) || Fuel(r.blueprint), $"recipe {r.id}");
                foreach (var i in r.inputs) Assert.IsFalse(Fuel(i.item), $"recipe {r.id} input {i.item}");
            }
            foreach (var b in CraftingDefaults.Blueprints())
                Assert.IsFalse(Fuel(b.id) || Fuel(b.name) || Fuel(b.icon), $"blueprint {b.id}");
            var book = AssetDatabase.LoadAssetAtPath<RecipeBook>(CraftingAuthoring.Path);
            Assert.NotNull(book, "RecipeBook asset");
            foreach (var r in book.recipes) Assert.IsFalse(Fuel(r.id), "RecipeBook recipe " + r.id);
            foreach (var b in book.blueprints) Assert.IsFalse(Fuel(b.id) || Fuel(b.icon), "RecipeBook blueprint " + b.id);
        }

        [Test]
        public void NoFuelStringInCode()
        {
            var hits = new List<string>();
            foreach (var dir in new[] { "Assets/_Game/Code/Runtime", "Assets/_Game/Code/Editor" })
                foreach (var file in Directory.GetFiles(dir, "*.cs", SearchOption.AllDirectories))
                    foreach (var lit in Literals(File.ReadAllText(file)))
                        if (Fuel(lit)) hits.Add($"{file}: \"{lit}\"");
            Assert.IsEmpty(hits, "fuel strings: " + string.Join("\n", hits));
        }

        static readonly string[] TextAssets = { ".prefab", ".unity", ".asset", ".json", ".inputactions", ".mat", ".controller", ".anim", ".txt" };

        [Test]
        public void NoFuelAssetNameOrSerializedTextOutsideTheArchive()
        {
            var names = new List<string>();
            var texts = new List<string>();
            foreach (var path in Directory.GetFileSystemEntries("Assets", "*", SearchOption.AllDirectories))
            {
                var p = path.Replace('\\', '/');
                if (Archived(p)) continue; // Unity ignores "~" folders: Archive/Fuel~ keeps the history
                if (Fuel(Path.GetFileName(p))) names.Add(p);
                if (File.Exists(p) && TextAssets.Contains(Path.GetExtension(p).ToLowerInvariant()) && Fuel(File.ReadAllText(p))) texts.Add(p);
            }
            Assert.IsEmpty(names, "fuel in asset names: " + string.Join(", ", names));
            Assert.IsEmpty(texts, "fuel in serialized assets: " + string.Join(", ", texts));
            Assert.IsTrue(Directory.Exists("Assets/_Game/Archive/Fuel~"), "the archive keeps what was removed");
        }

        static bool Archived(string p) => p.Split('/').Any(s => s.EndsWith("~"));

        static bool Fuel(string s) => !string.IsNullOrEmpty(s) && s.IndexOf("fuel", StringComparison.OrdinalIgnoreCase) >= 0;

        /// <summary>The string literals of a C# source (comments, char literals and code skipped). Close enough for a grep.</summary>
        static IEnumerable<string> Literals(string src)
        {
            int i = 0, n = src.Length;
            while (i < n)
            {
                char c = src[i];
                if (c == '/' && i + 1 < n && src[i + 1] == '/') { while (i < n && src[i] != '\n') i++; continue; }
                if (c == '/' && i + 1 < n && src[i + 1] == '*') { int e = src.IndexOf("*/", i + 2, StringComparison.Ordinal); i = e < 0 ? n : e + 2; continue; }
                if (c == '\'') { i++; while (i < n && src[i] != '\'' && src[i] != '\n') { if (src[i] == '\\') i++; i++; } i++; continue; }
                if (c == '"')
                {
                    bool verbatim = i > 0 && (src[i - 1] == '@' || (i > 1 && src[i - 1] == '$' && src[i - 2] == '@'));
                    int s = ++i;
                    while (i < n)
                    {
                        if (verbatim) { if (src[i] == '"') { if (i + 1 < n && src[i + 1] == '"') { i += 2; continue; } break; } i++; }
                        else { if (src[i] == '\\') { i += 2; continue; } if (src[i] == '"' || src[i] == '\n') break; i++; }
                    }
                    yield return src.Substring(s, Mathf.Min(i, n) - s);
                    i++;
                    continue;
                }
                i++;
            }
        }
    }
}
