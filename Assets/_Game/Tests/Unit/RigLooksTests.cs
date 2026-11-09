using System.Collections.Generic;
using Meridian.Rig;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-183 (B-205): each tool's look by its Skill Tree chain level - the Beam by Dig power (dig_power_1 Mk2, _2 Mk3, _3 / _4 Mk4, _5 Mk5),
    /// the Grapple by its line (asc_grapple_2 Mk2, _3 Mk3), the jetpack by asc_jet_2 / _3 - their keys (never the archived Lance), and the
    /// json sockets' parser (a tool's [x, y], a per-frame table with nulls, held_b's names).
    /// </summary>
    public class RigLooksTests
    {
        static HashSet<string> Nodes(params string[] ids) => new HashSet<string>(ids);

        [Test]
        public void EachSlotsLookFollowsItsChainLevel()
        {
            Assert.AreEqual(1, RigLooks.BeamMk(Nodes()));
            Assert.AreEqual(2, RigLooks.BeamMk(Nodes("dig_power_1")));
            Assert.AreEqual(3, RigLooks.BeamMk(Nodes("dig_power_1", "dig_power_2")));
            Assert.AreEqual(4, RigLooks.BeamMk(Nodes("dig_power_1", "dig_power_2", "dig_power_3")));
            Assert.AreEqual(4, RigLooks.BeamMk(Nodes("dig_power_1", "dig_power_2", "dig_power_3", "dig_power_4")));
            Assert.AreEqual(5, RigLooks.BeamMk(Nodes("dig_power_5")));
            Assert.AreEqual(1, RigLooks.GrappleMk(Nodes("asc_grapple_1")), "asc_grapple_1: the Mk1 grapple");
            Assert.AreEqual(2, RigLooks.GrappleMk(Nodes("asc_grapple_1", "asc_grapple_2")));
            Assert.AreEqual(3, RigLooks.GrappleMk(Nodes("asc_grapple_3")));
            Assert.AreEqual(1, RigLooks.JetpackMk(Nodes("asc_jet_1")), "asc_jet_1 is thrust, not a new pack");
            Assert.AreEqual(2, RigLooks.JetpackMk(Nodes("asc_jet_2")));
            Assert.AreEqual(3, RigLooks.JetpackMk(Nodes("asc_jet_2", "asc_jet_3")));

            Assert.AreEqual("props/rig/beam", RigLooks.ToolKey(RigModule.Beam, 1), "Mk1: the module's own key (= beam_mk1)");
            Assert.AreEqual("props/rig/beam_mk4", RigLooks.ToolKey(RigModule.Beam, 4));
            Assert.AreEqual("props/rig/grapple_mk3", RigLooks.ToolKey(RigModule.Grapple, 3));
            Assert.AreEqual("props/rig/survey", RigLooks.ToolKey(RigModule.Survey, 3), "the Survey and the Builder have one look");
            Assert.AreEqual("fx/beam_ray/mk5", RigLooks.RayKey(5));
            Assert.AreEqual("fx/beam_ray/mk1", RigLooks.RayKey(1), "never the v2 base sheet");
            Assert.IsNull(RigLooks.JetpackKey(1), "Mk1: the pack as drawn");
            Assert.AreEqual("props/rig/jetpack_mk3", RigLooks.JetpackKey(3));
            for (int m = 1; m <= RigModules.Count; m++)
                for (int mk = 1; mk <= 5; mk++)
                    StringAssert.DoesNotContain("lance", RigLooks.ToolKey((RigModule)m, mk), "the archived v2 Lance is never a look (D-087)");
        }

        [Test]
        public void TheSocketParserReadsPointsTablesAndNames()
        {
            var p = Meridian.EditorTools.ArtSockets.Parse("{\"muzzle\": [0.47, 0.03], \"mk\": 3}", "muzzle", out int s1);
            Assert.AreEqual(2, s1); Assert.AreEqual(0.47f, p[0], 1e-5f); Assert.AreEqual(0.03f, p[1], 1e-5f);
            var t = Meridian.EditorTools.ArtSockets.Parse("{\"back_socket\": [[-0.36, 0.94, -0.05, 0.98, 1.04], null, [-0.35, 0.93, 0.02, 1.0, 1.0]]}", "back_socket", out int s2);
            Assert.AreEqual(5, s2); Assert.AreEqual(15, t.Length);
            Assert.AreEqual(-0.36f, t[0], 1e-5f); Assert.IsTrue(float.IsNaN(t[5]), "a null frame"); Assert.AreEqual(0.93f, t[11], 1e-5f);
            var h = Meridian.EditorTools.ArtSockets.Parse("{\"held_b\": [null, \"pick\", null, \"beam_arm+reel\"]}", "held_b", out int s3);
            Assert.AreEqual(1, s3); Assert.AreEqual(4, h.Length);
            Assert.IsTrue(float.IsNaN(h[0])); Assert.AreEqual(1f, h[1]); Assert.IsTrue(float.IsNaN(h[2])); Assert.AreEqual(1f, h[3]);
            Assert.IsNull(Meridian.EditorTools.ArtSockets.Parse("{\"mk\": 2}", "muzzle", out _), "no field");
        }

        [Test]
        public void TheRegistryHoldsTheJsonsSockets()
        {
            var reg = Meridian.Rendering.ArtMaterials.Active;
            Assert.NotNull(reg);
            var cable = Meridian.Rendering.ArtMaterials.SocketFor("props/rig/beam_mk3", "cable_socket");
            Assert.NotNull(cable, "the Beam Mk3's cable socket (ArtSockets)");
            Assert.AreEqual(-0.24f, cable[0, 0], 1e-4f);
            Assert.AreEqual(UnityEngine.Vector2.Distance(new UnityEngine.Vector2(0.30f, 0.06f), RigModules.Muzzle(RigModule.Survey, 1)), 0f, 1e-4f, "B-217's survey muzzle");
            var back = Meridian.Rendering.ArtMaterials.SocketFor("props/rig/jetpack_mk2", "back_socket");
            Assert.NotNull(back); Assert.AreEqual(5, back.stride); Assert.AreEqual(98, back.Count, "one entry per side-sheet frame");
            var hand = Meridian.Rendering.ArtMaterials.SocketFor("props/rig/hand_socket", "hand_socket");
            Assert.NotNull(hand, "B-218's hand socket"); Assert.AreEqual(98, hand.Count);
        }
    }
}
