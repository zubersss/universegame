using System.Linq;
using Meridian.EditorTools;
using Meridian.Planets;
using Meridian.Player;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-009 (EditMode): timing rules, fall damage, Jetpack and the input map, Bible §4.2 and §6.</summary>
    public class PlayerPhysicsTests
    {
        const float Dt = 0.02f;

        static PlanetConfig Load(PlanetId id) =>
            AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/{id}.asset");

        [TestCase(PlanetId.Mercury, 6.6f)] [TestCase(PlanetId.Venus, 2.8f)] [TestCase(PlanetId.Earth, 2.5f)]
        [TestCase(PlanetId.Mars, 6.6f)] [TestCase(PlanetId.Jupiter, 1.0f)] [TestCase(PlanetId.Saturn, 2.3f)]
        [TestCase(PlanetId.Uranus, 2.8f)] [TestCase(PlanetId.Neptune, 2.2f)]
        public void JumpHeightFormulaMatchesBibleTable(PlanetId id, float bible)
        {
            float h = PlayerTuning.JumpSpeed * PlayerTuning.JumpSpeed / (2f * Load(id).gravity);
            Assert.AreEqual(bible, h, 0.05f, "table is rounded to 0.1 m");
        }

        [Test]
        public void CoyoteTimeAllowsJumpUpTo100msAfterLeavingGround()
        {
            var t = new JumpTimer();
            t.Step(Dt, true, false);
            for (int i = 0; i < 4; i++) Assert.IsFalse(t.Step(Dt, false, false)); // 80 ms airborne
            Assert.IsTrue(t.Step(Dt, false, true), "press at 100 ms still jumps");

            var late = new JumpTimer();
            late.Step(Dt, true, false);
            for (int i = 0; i < 6; i++) late.Step(Dt, false, false); // 120 ms
            Assert.IsFalse(late.Step(Dt, false, true), "press at 140 ms does not");
        }

        [Test]
        public void JumpBufferHonorsPressUpTo120msBeforeLanding()
        {
            var t = new JumpTimer();
            t.Step(Dt, false, true); // pressed in the air (no coyote: never grounded)
            for (int i = 0; i < 5; i++) Assert.IsFalse(t.Step(Dt, false, false)); // +100 ms
            Assert.IsTrue(t.Step(Dt, true, false), "lands 120 ms after the press → jumps");

            var early = new JumpTimer();
            early.Step(Dt, false, true);
            for (int i = 0; i < 7; i++) early.Step(Dt, false, false); // +140 ms
            Assert.IsFalse(early.Step(Dt, true, false), "press 160 ms before landing is dropped");
        }

        [Test]
        public void OneJumpPerGroundContact()
        {
            var t = new JumpTimer();
            Assert.IsTrue(t.Step(Dt, true, true));
            Assert.IsFalse(t.Step(Dt, false, true), "no second jump from coyote time");
        }

        [Test]
        public void FallDamageThresholds()
        {
            Assert.AreEqual(0f, FallDamage.Fraction(11.99f));
            Assert.AreEqual(0f, FallDamage.Fraction(12f), 1e-6f);
            Assert.AreEqual(0.5f, FallDamage.Fraction(18f), 1e-6f);
            Assert.AreEqual(1f, FallDamage.Fraction(24f));
            Assert.AreEqual(7.3f, FallDamage.SafeDrop(Load(PlanetId.Earth).gravity), 0.05f);
            Assert.AreEqual(19.4f, FallDamage.SafeDrop(Load(PlanetId.Mars).gravity), 0.05f);
            Assert.AreEqual(2.9f, FallDamage.SafeDrop(Load(PlanetId.Jupiter).gravity), 0.05f);
        }

        [TestCase(PlanetId.Earth, 4.2f)] [TestCase(PlanetId.Mars, 10.3f)] [TestCase(PlanetId.Jupiter, -10.8f)]
        public void JetpackMk1NetLiftMatchesTable(PlanetId id, float net)
        {
            Assert.AreEqual(net, new Jetpack(1).Thrust - Load(id).gravity, 0.05f);
        }

        [Test]
        public void JetpackMk1Burns3sAndRefillsIn2s()
        {
            var j = new Jetpack(1);
            Assert.AreEqual(14f, j.Thrust);
            int burning = 0;
            for (int i = 0; i < 200; i++) if (j.Step(Dt, true, false) > 0f) burning++;
            Assert.AreEqual(150, burning, "3 s of thrust at 50 Hz");
            Assert.AreEqual(0f, j.Remaining, 1e-4f);
            for (int i = 0; i < 100; i++) j.Step(Dt, false, true);
            Assert.AreEqual(3f, j.Remaining, 1e-3f, "full after 2 s on the ground");
        }

        [Test]
        public void InputMapCoversBibleSection6()
        {
            var a = MeridianInput.Build();
            string[] foot = { "Move", "Sprint", "Jump", "Crouch", "Aim", "RigPrimary", "RigSecondary", "Module1", "Module2",
                              "Module3", "Module4", "ModulePrev", "ModuleNext", "Interact", "BuildMenu", "Inventory", "Map",
                              "Catalogue", "FloatCell" };
            foreach (var name in foot) Assert.NotNull(a.FindAction($"{MeridianInput.OnFoot}/{name}"), name);
            foreach (var name in new[] { "Thrust", "Retro", "Lateral", "Exit" })
                Assert.NotNull(a.FindAction($"{MeridianInput.ShipSide}/{name}"), name);
            foreach (var name in new[] { "Thrust", "Retro", "Rotate", "Boost", "SkipDrive", "Fire", "Scan", "SystemMap", "Inventory" })
                Assert.NotNull(a.FindAction($"{MeridianInput.ShipTop}/{name}"), name);
            Assert.NotNull(a.FindAction($"{MeridianInput.Always}/Pause"));
            Assert.IsTrue(a.FindAction("OnFoot/Jump").bindings.Any(b => b.path == "<Keyboard>/space"));
            Assert.IsTrue(a.FindAction("OnFoot/Sprint").bindings.Any(b => b.path == "<Keyboard>/leftShift"));
            Object.DestroyImmediate(a);
        }

        [Test]
        public void InputAssetFileMatchesCode()
        {
            var asset = AssetDatabase.LoadAssetAtPath<UnityEngine.InputSystem.InputActionAsset>(InputAuthoring.AssetPath);
            Assert.NotNull(asset, "MERIDIAN.inputactions exists");
            var code = MeridianInput.Build();
            Assert.AreEqual(code.actionMaps.Sum(m => m.actions.Count), asset.actionMaps.Sum(m => m.actions.Count));
            Object.DestroyImmediate(code);
        }
    }
}
