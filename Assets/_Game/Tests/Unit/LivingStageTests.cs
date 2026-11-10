using System.Collections.Generic;
using System.IO;
using Meridian.View2D.Living;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-216 (EditMode): the living stage's pure parts: the wind field (the same seed gives the same sway; nothing moves in
    /// still air), the stage mesh's bend weights, the vine chain, the stand-in pieces' layout, and the shader's constants.</summary>
    public class LivingStageTests
    {
        const float Dt = 1f / 60f;

        static LivingWind Blowing(int seed, float strength = 0.6f)
        {
            var w = new LivingWind(seed);
            w.Set(Vector2.right, strength);
            return w;
        }

        [Test]
        public void TheSameSeedGivesTheSameSwayAndAnotherSeedADifferentOne()
        {
            var a = Blowing(216); var b = Blowing(216); var c = Blowing(217);
            bool differs = false;
            for (int k = 0; k < 600; k++)
            {
                float dt = (k % 7 == 0) ? 0.031f : Dt; // an uneven run of frames, the same for both
                a.Step(dt); b.Step(dt); c.Step(dt);
                for (int i = 0; i < 6; i++)
                {
                    var root = new Vector2(100f + i * 3.7f, 320f);
                    var oa = a.Offset(root, 0.8f, 0.22f, i / 6f);
                    Assert.AreEqual(oa, b.Offset(root, 0.8f, 0.22f, i / 6f), $"frame {k}, plant {i}: the same seed and steps, the same sway to the bit");
                    if ((oa - c.Offset(root, 0.8f, 0.22f, i / 6f)).sqrMagnitude > 1e-8f) differs = true;
                }
            }
            Assert.IsTrue(differs, "another seed: another run of gusts");
            Assert.AreEqual(a.Clock, b.Clock);
        }

        [Test]
        public void TheGustStaysBetweenALullAndACrestAndCrossesTheStage()
        {
            var w = Blowing(216);
            float lo = float.MaxValue, hi = float.MinValue;
            for (int k = 0; k < 1200; k++)
            {
                w.Step(Dt);
                for (float x = 0f; x < 60f; x += 2.5f) { float g = w.Gust(x); lo = Mathf.Min(lo, g); hi = Mathf.Max(hi, g); }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] u216 gust over 20 s and 60 m: {lo:0.000} .. {hi:0.000}");
            Assert.GreaterOrEqual(lo, LivingWind.LeanBase - LivingWind.LeanA - LivingWind.LeanB - 1e-4f, "a lull never pulls a plant upwind");
            Assert.LessOrEqual(hi, 1f + 1e-4f, "a crest is the piece's whole give");
            Assert.Greater(hi - lo, 0.6f, "gusts and lulls are far apart");
            // the field is the steady lean and two travelling waves, each moving with the wind at its own speed
            float t0 = w.Clock;
            Assert.AreEqual(LivingWind.LeanBase
                + LivingWind.LeanA * Mathf.Sin(LivingWind.TwoPi * (10f - LivingWind.GustSpeedA * t0) / LivingWind.GustLengthA)
                + LivingWind.LeanB * Mathf.Sin(LivingWind.TwoPi * (10f - LivingWind.GustSpeedB * t0) / LivingWind.GustLengthB),
                LivingWind.Gust(10f, t0, 0f, 0f), 1e-4f);
        }

        [Test]
        public void NothingMovesInStillAirAndTheTipMovesMostInAGust()
        {
            var still = Blowing(216, 0f);
            for (int k = 0; k < 120; k++)
            {
                still.Step(Dt);
                Assert.AreEqual(Vector2.zero, still.Offset(new Vector2(50f, 300f), 1f, 0.3f, 0.4f), "the wind off and nobody passing: a plant stands still");
            }
            var w = Blowing(216);
            w.Step(3.7f);
            var root = new Vector2(50f, 300f);
            Assert.AreEqual(Vector2.zero, w.Offset(root, 0f, 0.3f, 0.4f), "the root never moves");
            Assert.AreEqual(Vector2.zero, w.Offset(root, 1f, 0f, 0.4f), "a piece with no give never moves");
            float last = 0f;
            for (float weight = 0.1f; weight <= 1.001f; weight += 0.1f)
            {
                float x = Mathf.Abs(w.Offset(root, weight, 0.3f, 0.4f).x);
                Assert.Greater(x, last, $"weight {weight:0.0}: farther from the root, farther in the wind");
                last = x;
            }
            Assert.LessOrEqual(last, 0.3f * (1f + LivingWind.FlutterShare) + 1e-4f, "the tip's travel stays inside the give and its flutter");
            Assert.Less(w.Offset(root, 1f, 0.3f, 0.4f).y, 0f, "a bent tip dips");
        }

        [Test]
        public void TheSurveyorPassingPartsThePlantsBesideThem()
        {
            var w = Blowing(216, 0f); // still air: only the push
            var feet = new Vector2(100f, 320f);
            w.SetPusher(feet, true);
            float right = w.Offset(feet + new Vector2(0.5f, 0f), 1f, 0.25f, 0f).x, left = w.Offset(feet + new Vector2(-0.5f, 0f), 1f, 0.25f, 0f).x;
            Assert.Greater(right, 0.05f, "a plant rooted to the right leans right, out of the way");
            Assert.Less(left, -0.05f, "one to the left leans left");
            Assert.AreEqual(right, -left, 1e-5f);
            Assert.AreEqual(0f, w.Offset(feet + new Vector2(LivingWind.PushRadiusM + 0.01f, 0f), 1f, 0.25f, 0f).x, "past the push's radius: untouched");
            Assert.AreEqual(0f, w.Offset(feet + new Vector2(0.5f, 3f), 1f, 0.25f, 0f).x, "a plant rooted 3 m over the feet: untouched");
            Assert.Less(w.Offset(feet + new Vector2(0.5f, 0f), 1f, 0.06f, 0f).x, right, "a stiff shrub gives less than a soft fern");
            Assert.LessOrEqual(right, LivingWind.PushGiveM);
            w.SetPusher(feet, false);
            Assert.AreEqual(0f, w.Offset(feet + new Vector2(0.5f, 0f), 1f, 0.25f, 0f).x, "nobody on the stage: no push");
        }

        static LivingPiece Fern() => new LivingPiece { name = "fern", uv = new Rect(0.1f, 0.2f, 0.2f, 0.3f), sizeM = new Vector2(2.25f, 1.5f), pivot = new Vector2(0.5f, 0f), motion = LivingMotion.Sways, bendFromM = 0.15f, bendToM = 1.3f, bendPower = 1.5f, giveM = 0.22f };

        [Test]
        public void ASwayingPieceIsAGridWithTheRootStillAndTheFarthestTipFree()
        {
            var verts = new List<Vector3>(); var uv0 = new List<Vector2>(); var uv1 = new List<Vector4>(); var uv2 = new List<Vector4>(); var cols = new List<Color32>(); var tris = new List<int>();
            var piece = Fern();
            var inst = new LivingInstance { piece = 0, at = new Vector2(40f, 300f), scale = 1f, phase = 0.37f, tint = new Color32(10, 20, 30, 255) };
            int added = LivingMesh.Append(piece, inst, verts, uv0, uv1, uv2, cols, tris);
            Assert.AreEqual(12, LivingMesh.CellsFor(2.25f)); Assert.AreEqual(8, LivingMesh.CellsFor(1.5f));
            Assert.AreEqual(13 * 9, added, "2.25 x 1.5 m in 0.2 m cells");
            Assert.AreEqual(added, LivingMesh.VertexCount(piece, 1f));
            Assert.AreEqual(12 * 8 * 6, tris.Count);
            float least = float.MaxValue, most = 0f; Vector3 stillAt = default, freeAt = default;
            for (int i = 0; i < added; i++)
            {
                Assert.AreEqual(40f, uv1[i].x, 1e-5f); Assert.AreEqual(300f, uv1[i].y, 1e-5f); // every vertex knows its root
                Assert.AreEqual(0.22f, uv1[i].w, 1e-6f, "and the piece's give");
                Assert.AreEqual(0.37f, uv2[i].x, 1e-6f); Assert.AreEqual(1f, uv2[i].y, "not mirrored");
                Assert.That(uv1[i].z, Is.InRange(0f, 1f));
                if (uv1[i].z < least) { least = uv1[i].z; stillAt = verts[i]; }
                if (uv1[i].z > most) { most = uv1[i].z; freeAt = verts[i]; }
                Assert.That(uv0[i].x, Is.InRange(0.1f - 1e-5f, 0.3f + 1e-5f)); Assert.That(uv0[i].y, Is.InRange(0.2f - 1e-5f, 0.5f + 1e-5f));
            }
            Assert.AreEqual(0f, least, "the root's weight");
            Assert.AreEqual(new Vector3(40f, 300f, 0f), stillAt, "and it is the vertex on the root");
            Assert.AreEqual(1f, most, 1e-5f, "the farthest tips move by the whole give");
            Assert.Greater(((Vector2)freeAt - inst.at).magnitude, 1.3f - 1e-3f);
            // mirrored: the picture's right is the world's left, and the shader is told
            verts.Clear(); uv0.Clear(); uv1.Clear(); uv2.Clear(); cols.Clear(); tris.Clear();
            inst.flip = true;
            LivingMesh.Append(piece, inst, verts, uv0, uv1, uv2, cols, tris);
            int topRight = verts.Count - 1; // the last vertex: the picture's upper right corner
            Assert.Less(verts[topRight].x, 40f, "mirrored about the root");
            Assert.AreEqual(-1f, uv2[topRight].y);
            // a standing piece: one quad that never bends; a piece that is gone: nothing
            verts.Clear(); uv0.Clear(); uv1.Clear(); uv2.Clear(); cols.Clear(); tris.Clear();
            piece.motion = LivingMotion.Stands; inst.flip = false;
            Assert.AreEqual(4, LivingMesh.Append(piece, inst, verts, uv0, uv1, uv2, cols, tris));
            foreach (var v in uv1) Assert.AreEqual(0f, v.z);
            inst.gone = true;
            Assert.AreEqual(0, LivingMesh.Append(piece, inst, verts, uv0, uv1, uv2, cols, tris));
            Assert.AreEqual(4, verts.Count);
        }

        [Test]
        public void TheBendWeightIsTheFormatsThreeNumbers()
        {
            Assert.AreEqual(0f, LivingMesh.Weight(0.1f, 0.15f, 1.3f, 1.5f), "inside from_m: still");
            Assert.AreEqual(1f, LivingMesh.Weight(1.3f, 0.15f, 1.3f, 1.5f), 1e-6f, "at to_m: free");
            Assert.AreEqual(1f, LivingMesh.Weight(2f, 0.15f, 1.3f, 1.5f), "past it: free");
            Assert.AreEqual(Mathf.Pow(0.5f, 1.5f), LivingMesh.Weight(0.725f, 0.15f, 1.3f, 1.5f), 1e-5f, "halfway, to the power");
            Assert.AreEqual(0.5f, LivingMesh.Weight(0.725f, 0.15f, 1.3f, 1f), 1e-5f);
        }

        [Test]
        public void TheVineHangsSwingsWithTheWindKeepsItsLengthAndIsBrushedAside()
        {
            var anchor = new Vector2(100f, 330f);
            var still = new VineChain(anchor, 12, 0.25f);
            for (int k = 0; k < 300; k++) still.Step(Dt, null, Vector2.zero, Vector2.zero, false);
            Assert.AreEqual(0f, still.Swing, 1e-3f, "no wind: it hangs plumb");
            Assert.AreEqual(3f, still.Length(), 0.05f, "twelve links of 0.25 m");
            Assert.AreEqual(anchor, still[0], "the attachment holds");

            var w = Blowing(216); var w2 = Blowing(216);
            var a = new VineChain(anchor, 12, 0.25f); var b = new VineChain(anchor, 12, 0.25f);
            float most = 0f, shortest = float.MaxValue, longest = 0f;
            for (int k = 0; k < 600; k++)
            {
                float dt = (k % 5 == 0) ? 0.027f : Dt;
                w.Step(dt); w2.Step(dt);
                a.Step(dt, w, Vector2.zero, Vector2.zero, false);
                b.Step(dt, w2, Vector2.zero, Vector2.zero, false);
                most = Mathf.Max(most, a.Swing);
                float len = a.Length(); shortest = Mathf.Min(shortest, len); longest = Mathf.Max(longest, len);
            }
            for (int i = 0; i < a.Count; i++) Assert.AreEqual(a[i], b[i], $"node {i}: the same wind and frames, the same swing to the bit");
            TestContext.Out.WriteLine($"[MERIDIAN] u216 vine in the wind: the free end swung up to {most:0.00} m downwind; length {shortest:0.000} .. {longest:0.000} m; {a.Steps} fixed steps");
            Assert.Greater(most, 0.15f, "the wind carries the free end downwind");
            Assert.Less(most, 3f, "and it stays a hanging vine");
            Assert.That(shortest, Is.GreaterThan(3f * 0.97f)); Assert.That(longest, Is.LessThan(3f * 1.03f), "the links keep their length within 3 %");

            // brushed by a body standing on its plumb line: no node stays inside the body
            var c = new VineChain(anchor, 12, 0.25f);
            var body = new Vector2(100.05f, 328.2f); var half = new Vector2(0.3f, 0.9f);
            for (int k = 0; k < 180; k++) c.Step(Dt, null, body, half, true);
            for (int i = 1; i < c.Count; i++)
            {
                var d = c[i] - body;
                bool inside = Mathf.Abs(d.x) < half.x - 0.02f && Mathf.Abs(d.y) < half.y - 0.02f;
                Assert.IsFalse(inside, $"node {i} at {c[i]} hangs inside the surveyor's body");
            }
            Assert.AreEqual(anchor, c[0]);
        }

        [Test]
        public void TheStandInPiecesFitTheirPageAndTheFormat()
        {
            for (int i = 0; i < LivingPlaceholders.Kinds; i++)
            {
                var r = LivingPlaceholders.RectOf((LivingPlaceholders.Kind)i);
                Assert.IsTrue(r.xMin >= 0 && r.yMin >= 0 && r.xMax <= LivingPlaceholders.Width && r.yMax <= LivingPlaceholders.Height, $"{(LivingPlaceholders.Kind)i} lies on the page");
                for (int j = i + 1; j < LivingPlaceholders.Kinds; j++)
                    Assert.IsFalse(r.Overlaps(LivingPlaceholders.RectOf((LivingPlaceholders.Kind)j)), $"{(LivingPlaceholders.Kind)i} and {(LivingPlaceholders.Kind)j} share no pixel");
            }
            var tuft = LivingPlaceholders.Piece(LivingPlaceholders.Kind.Tuft);
            Assert.LessOrEqual(tuft.sizeM.y * LivingStage.PlayFrontScale * 1.15f, LivingStage.PlayFrontMaxM, "play_front: at most 0.30 m tall at the scatter's largest (D-206)");
            Assert.AreEqual(LivingMotion.Hangs, LivingPlaceholders.Piece(LivingPlaceholders.Kind.Vine).motion);
            Assert.AreEqual(1f, LivingPlaceholders.Piece(LivingPlaceholders.Kind.Vine).pivot.y, "a hanging piece's pivot is its attachment");
            Assert.AreEqual(LivingMotion.Stands, LivingPlaceholders.Piece(LivingPlaceholders.Kind.Rock).motion);
            foreach (var k in new[] { LivingPlaceholders.Kind.Fern, LivingPlaceholders.Kind.Shrub, LivingPlaceholders.Kind.Grass, LivingPlaceholders.Kind.Reed })
            {
                var p = LivingPlaceholders.Piece(k);
                Assert.AreEqual(LivingMotion.Sways, p.motion); Assert.Greater(p.giveM, 0f); Assert.Greater(p.bendToM, p.bendFromM);
                Assert.LessOrEqual(p.sizeM.y * LivingPlaceholders.Ppu, 1024f, "a swaying piece no taller than about 1024 px");
            }
            // no instance of near, play or play_front is ever mirrored (the painted light would come from the wrong side); the orders
            Assert.Less(LivingStage.Orders[(int)LivingStage.Layer.Near], LivingStage.Orders[(int)LivingStage.Layer.Play]);
            Assert.Less(LivingStage.Orders[(int)LivingStage.Layer.Play], Meridian.View2D.SmoothGround.Order, "play stands behind the ground's lip");
            Assert.Greater(LivingStage.Orders[(int)LivingStage.Layer.PlayFront], Meridian.View2D.SpriteCharacterView.SurveyorOrder, "play_front over the surveyor's feet");
            Assert.Greater(LivingStage.Orders[(int)LivingStage.Layer.Foreground], LivingStage.MoteOrder, "the foreground over the air");
            Assert.AreEqual(0f, LivingStage.Parallax[(int)LivingStage.Layer.Play]); Assert.AreEqual(0f, LivingStage.Parallax[(int)LivingStage.Layer.PlayFront]);
        }

        /// <summary>The vertex shader runs the same sums as LivingWind.Offset: the numbers in the one are the constants of the other.</summary>
        [Test]
        public void TheShadersWindCarriesTheSameNumbers()
        {
            const string path = "Assets/_Game/Shaders/LivingWind.hlsl";
            Assert.IsTrue(File.Exists(path), path);
            var hlsl = File.ReadAllText(path);
            void Has(string literal, float value, string what)
            {
                StringAssert.Contains(literal, hlsl, what);
                var number = System.Text.RegularExpressions.Regex.Match(literal, @"-?\d+\.\d+").Value;
                Assert.AreEqual(value, float.Parse(number, System.Globalization.CultureInfo.InvariantCulture), 1e-6f, what);
            }
            Has("0.55 +", LivingWind.LeanBase, "the steady lean");
            Has("0.30 *", LivingWind.LeanA, "the long gust's share");
            Has("0.15 *", LivingWind.LeanB, "the short gust's share");
            Has("3.1 *", LivingWind.GustSpeedA, "the long gust's speed"); Has("/ 23.0", LivingWind.GustLengthA, "its length");
            Has("4.7 *", LivingWind.GustSpeedB, "the short gust's speed"); Has("/ 7.3", LivingWind.GustLengthB, "its length");
            Has("0.7 +", LivingWind.FlutterHzMin, "the flutter's slowest beat"); Has("0.5 *", LivingWind.FlutterHzSpan, "its span");
            Has("(0.35 +", LivingWind.FlutterInLull, "the flutter in a lull"); Has("0.18 *", LivingWind.FlutterShare, "the flutter's share");
            Has("* 0.9)", LivingWind.FlutterAcross, "the flutter across the stage");
            Has("0.25 * weight", LivingWind.DipShare, "the tip's dip");
            Has("/ 1.4)", LivingWind.PushRadiusM, "the push's radius"); Has("0.28 *", LivingWind.PushGiveM, "the push's give");
            Has("(-0.6,", -LivingWind.PushBelowM, "the push's reach under the feet"); Has(", 1.6)", LivingWind.PushAboveM, "and over them");
            Has("/ 0.25)", LivingWind.PushSoftGiveM, "a soft plant's give");
        }
    }
}
