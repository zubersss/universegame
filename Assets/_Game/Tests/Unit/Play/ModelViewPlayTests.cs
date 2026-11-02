using System.Collections;
using Meridian.Art;
using Meridian.Player;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-075 (PlayMode): ModelView loads the surveyor model (B-078) through Addressables, carries every clip the code
    /// picks, plays each by name, holds one-shots, faces by a 180° yaw, and a key without a model stays not-Ready.
    /// </summary>
    public class ModelViewPlayTests
    {
        static IEnumerator WaitReady(ModelView v, float seconds)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while (!v.Ready && Time.realtimeSinceStartup < until) yield return null;
        }

        [UnityTest]
        public IEnumerator SurveyorModelPlaysEveryClipTheCodeUses()
        {
            var go = new GameObject("ModelViewTest");
            try
            {
                var view = go.AddComponent<ModelView>();
                view.Load(ArtKeys.Characters.Surveyor);
                yield return WaitReady(view, 20f);
                Assert.IsTrue(view.Ready, "the surveyor model loaded");
                Assert.NotNull(view.Instance);
                foreach (var name in new[] { SurveyorAnim.Idle, SurveyorAnim.Walk, SurveyorAnim.Run, SurveyorAnim.Jump, SurveyorAnim.Fall,
                                             SurveyorAnim.Land, SurveyorAnim.Dig, SurveyorAnim.Aim, SurveyorAnim.Hurt, SurveyorAnim.Death })
                {
                    Assert.IsTrue(view.Play(name), $"plays '{name}'");
                    Assert.AreEqual(name, view.Current);
                    yield return null;
                }
                var r = view.Instance.GetComponentInChildren<Renderer>();
                Assert.NotNull(r, "a renderer");
                StringAssert.DoesNotContain("glTF", r.sharedMaterial.shader.name, "the generated URP/Lit material, not glTFast's own");
                StringAssert.Contains("Universal Render Pipeline/Lit", r.sharedMaterial.shader.name);
                view.SetFacing(false);
                Assert.AreEqual(180f, view.Instance.transform.localEulerAngles.y, 0.01f, "left = 180° yaw");
                view.SetFacing(true);
                Assert.AreEqual(0f, view.Instance.transform.localEulerAngles.y, 0.01f);
                LogAssert.NoUnexpectedReceived();
            }
            finally { Object.Destroy(go); }
        }

        [UnityTest]
        public IEnumerator AKeyWithoutAModelStaysOnItsSprite()
        {
            var go = new GameObject("ModelViewNoModel");
            try
            {
                var view = go.AddComponent<ModelView>();
                view.Load(ArtKeys.Terrain.EarthSoil); // a 2D-only key
                yield return WaitReady(view, 3f);
                Assert.IsFalse(view.Ready, "no model: the caller keeps its 2D view");
                Assert.IsFalse(view.Play(SurveyorAnim.Idle));
                LogAssert.NoUnexpectedReceived();
            }
            finally { Object.Destroy(go); }
        }
    }
}
