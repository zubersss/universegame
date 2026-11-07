using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace Meridian.Transitions
{
    /// <summary>U-096 (Bible §9.3 v4): the iris radius curve, pure C#. Radii are in screen heights; centres in screen 0..1.</summary>
    public static class IrisMath
    {
        /// <summary>0.35 s each way (Bible §9.3, inside the §11 1.5 s transition budget).</summary>
        public const float Seconds = 0.35f;
        /// <summary>Soft edge of the circle (screen heights): about 4 px at 1080p.</summary>
        public const float Edge = 0.004f;

        /// <summary>The radius that covers every corner from `centre` on a screen of `aspect` (width / height).</summary>
        public static float CoverRadius(Vector2 centre, float aspect)
        {
            float dx = Mathf.Max(centre.x, 1f - centre.x) * aspect;
            float dy = Mathf.Max(centre.y, 1f - centre.y);
            return Mathf.Sqrt(dx * dx + dy * dy) + Edge;
        }

        /// <summary>
        /// The circle's radius `t` seconds into a wipe. Closing (iris-out) shrinks from `cover` to 0, accelerating;
        /// opening (iris-in) grows from 0 to `cover`, decelerating. Clamped at both ends.
        /// </summary>
        public static float Radius(float t, float seconds, bool closing, float cover)
        {
            float k = seconds > 0f ? Mathf.Clamp01(t / seconds) : 1f;
            return closing ? cover * (1f - k * k) : cover * (1f - (1f - k) * (1f - k));
        }
    }

    /// <summary>
    /// U-096: iris-out / iris-in as one full-screen quad (a UI Image on the transition canvas) with the MERIDIAN/IrisWipe
    /// cutout: black outside a circle, nothing inside, no texture. Close() shrinks the circle onto a screen point (the
    /// surveyor, the ship) in 0.35 s; the caller loads while the screen is black; Open() grows it back. Unscaled time.
    /// </summary>
    public sealed class IrisWipe : MonoBehaviour
    {
        public const string ShaderName = "MERIDIAN/IrisWipe";
        static readonly int CentreId = Shader.PropertyToID("_Centre"), RadiusId = Shader.PropertyToID("_Radius"), AspectId = Shader.PropertyToID("_Aspect"), EdgeId = Shader.PropertyToID("_Edge");

        public static IrisWipe Instance { get; private set; }
        public Image Quad { get; private set; }
        public bool Closed { get; private set; }
        public bool Busy { get; private set; }
        /// <summary>The circle now (screen heights) and its centre (screen 0..1); for the tests and the capture strip.</summary>
        public float Radius { get; private set; }
        public Vector2 Centre { get; private set; } = new Vector2(0.5f, 0.5f);

        Material material;

        /// <summary>Creates the iris quad under `canvasParent` (the transition canvas) once; returns the instance.</summary>
        public static IrisWipe Create(Transform canvasParent)
        {
            if (Instance != null) return Instance;
            var go = new GameObject("Iris");
            go.transform.SetParent(canvasParent, false);
            var iris = go.AddComponent<IrisWipe>();
            iris.Quad = go.AddComponent<Image>();
            iris.Quad.raycastTarget = false;
            var rt = iris.Quad.rectTransform;
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one;
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            var shader = Shader.Find(ShaderName);
            if (shader != null) { iris.material = new Material(shader); iris.Quad.material = iris.material; }
            iris.Quad.color = Color.white;
            iris.Quad.enabled = false;
            Instance = iris;
            return iris;
        }

        void OnDestroy() { if (Instance == this) Instance = null; }

        float Aspect => Screen.height > 0 ? (float)Screen.width / Screen.height : 16f / 9f;

        void Apply(Vector2 centre, float radius)
        {
            Centre = centre; Radius = radius;
            if (material == null) return;
            material.SetVector(CentreId, new Vector4(centre.x, centre.y, 0f, 0f));
            material.SetFloat(RadiusId, radius);
            material.SetFloat(AspectId, Aspect);
            material.SetFloat(EdgeId, IrisMath.Edge);
        }

        /// <summary>Sets the quad to the wipe's state `t` seconds in (the capture strip; no coroutine).</summary>
        public void Preview(Vector2 centre, float t, bool closing)
        {
            Quad.enabled = true;
            Apply(centre, IrisMath.Radius(t, IrisMath.Seconds, closing, IrisMath.CoverRadius(centre, Aspect)));
        }

        /// <summary>Black at once (boot cover, or a wake that starts closed).</summary>
        public void SetClosed(Vector2 centre)
        {
            Closed = true;
            Quad.enabled = true;
            Apply(centre, 0f);
        }

        public void SetOpen()
        {
            Closed = false;
            Quad.enabled = false;
            Apply(Centre, IrisMath.CoverRadius(Centre, Aspect));
        }

        /// <summary>Iris-out onto `centre` (screen 0..1) over `seconds` of unscaled time; the screen is black when it returns.</summary>
        public IEnumerator Close(Vector2 centre, float seconds = IrisMath.Seconds)
        {
            Busy = true;
            Quad.enabled = true;
            float cover = IrisMath.CoverRadius(centre, Aspect);
            for (float t = 0f; t < seconds; t += Time.unscaledDeltaTime)
            {
                Apply(centre, IrisMath.Radius(t, seconds, true, cover));
                yield return null;
            }
            Apply(centre, 0f);
            Closed = true;
            Busy = false;
        }

        /// <summary>Iris-in from `centre` over `seconds`; the quad switches off when the circle covers the screen.</summary>
        /// <summary>U-091: the worst frame (ms) of the last Open, logged by the gate and the probe (a jumped iris-in shows here).</summary>
        public float LastOpenWorstMs { get; private set; }

        public IEnumerator Open(Vector2 centre, float seconds = IrisMath.Seconds)
        {
            Busy = true;
            Quad.enabled = true;
            float cover = IrisMath.CoverRadius(centre, Aspect);
            float worst = 0f;
            for (float t = 0f; t < seconds; t += Time.unscaledDeltaTime)
            {
                worst = Mathf.Max(worst, Time.unscaledDeltaTime);
                Apply(centre, IrisMath.Radius(t, seconds, false, cover));
                yield return null;
            }
            LastOpenWorstMs = worst * 1000f;
            Apply(centre, cover);
            Closed = false;
            Quad.enabled = false;
            Busy = false;
        }

        /// <summary>A world point as a screen 0..1 centre for `cam` (clamped to the screen; the centre of it when the camera is null).</summary>
        public static Vector2 ScreenCentre(Camera cam, Vector3 world)
        {
            if (cam == null) return new Vector2(0.5f, 0.5f);
            var v = cam.WorldToViewportPoint(world);
            return new Vector2(Mathf.Clamp01(v.x), Mathf.Clamp01(v.y));
        }
    }
}
