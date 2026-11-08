using UnityEngine;

namespace Meridian.FX
{
    /// <summary>
    /// U-033: a looping fx attached to something (thruster flame, heat shimmer, Escape band). The owner
    /// sets `active`; while on, the renderer cycles the sheet's clip. No allocation per frame.
    /// </summary>
    public sealed class FxLoop : MonoBehaviour
    {
        public string key;
        public SpriteRenderer target;
        public bool active;
        /// <summary>Scale of the sprite while active; `flicker` varies it a little each frame (flames).</summary>
        public float flicker;
        /// <summary>U-150: a y stretch on top of the base scale (the boost flame drawn longer while the hull accelerates).</summary>
        public float stretchY = 1f;
        /// <summary>Draw unlit (self-lit glow, e.g. entry heat) instead of the sheet's lit material.</summary>
        public bool unlit;
        static Material unlitMaterial;

        public static int ActiveCount { get; private set; }

        FxSheet sheet;
        float t;
        int shown = -1;
        bool counted;
        Vector3 baseScale;
        float seed;

        void Awake()
        {
            if (target == null) target = gameObject.AddComponent<SpriteRenderer>();
            target.enabled = false;
            baseScale = transform.localScale;
            seed = (transform.localPosition.x * 7.3f + transform.localPosition.y * 3.1f) % 50f; // per-flame noise lane
        }

        void Start()
        {
            if (sheet == null) sheet = FxSheet.Get(key);
        }

        /// <summary>U-103: switches the loop to another sheet (the Pilgrim's puff) and takes the current transform scale as the flicker base.</summary>
        public void SetKey(string newKey)
        {
            key = newKey;
            sheet = FxSheet.Get(key);
            shown = -1;
            t = 0f;
            baseScale = transform.localScale;
        }

        /// <summary>U-150: switches the sheet only (the boost flame and the puff), keeping the base scale and the stretch.</summary>
        public void SwapKey(string newKey)
        {
            if (key == newKey) return;
            key = newKey;
            sheet = FxSheet.Get(key);
            shown = -1;
            t = 0f;
        }

        void Update()
        {
            bool on = active && sheet != null && sheet.Ready;
            if (on != counted) { ActiveCount += on ? 1 : -1; counted = on; }
            if (target.enabled != on) target.enabled = on;
            if (!on) { t = 0f; return; }
            if (shown < 0) target.sharedMaterial = unlit ? UnlitMaterial() : sheet.material != null ? sheet.material : target.sharedMaterial;
            t += Time.deltaTime;
            int f = sheet.FrameAt(t);
            if (f >= 0 && f != shown) { shown = f; target.sprite = sheet.frames[f]; }
            if (flicker > 0f || stretchY != 1f || transform.localScale.y != baseScale.y)
            {
                float k = flicker > 0f ? 1f + flicker * (Mathf.PerlinNoise(Time.time * 9f, seed) - 0.5f) : 1f;
                var want = new Vector3(baseScale.x, baseScale.y * k * stretchY, baseScale.z);
                if (transform.localScale != want) transform.localScale = want;
            }
        }

        static Material UnlitMaterial()
        {
            if (unlitMaterial == null && Meridian.Rendering.ArtMaterials.Active != null) unlitMaterial = Meridian.Rendering.ArtMaterials.Active.unlit;
            if (unlitMaterial == null)
            {
                var shader = Shader.Find("Universal Render Pipeline/2D/Sprite-Unlit-Default");
                unlitMaterial = shader != null ? new Material(shader) { name = "FxUnlit" } : null;
            }
            return unlitMaterial;
        }

        void OnDisable()
        {
            if (counted) { ActiveCount--; counted = false; }
            if (target != null) target.enabled = false;
        }
    }
}
