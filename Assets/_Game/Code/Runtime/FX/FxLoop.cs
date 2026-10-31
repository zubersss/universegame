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
            sheet = FxSheet.Get(key);
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
            if (flicker > 0f)
            {
                float k = 1f + flicker * (Mathf.PerlinNoise(Time.time * 9f, seed) - 0.5f);
                transform.localScale = new Vector3(baseScale.x, baseScale.y * k, baseScale.z);
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
