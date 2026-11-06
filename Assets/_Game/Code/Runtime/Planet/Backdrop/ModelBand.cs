using Meridian.Art;
using UnityEngine;

namespace Meridian.Planet.Backdrop
{
    /// <summary>
    /// U-090: one periodic stage layer: three copies of a model (ModelView) re-centred on the camera every frame,
    /// standing on the stage base height at a fixed depth; a band whose geometry imports at −z is mirrored (as
    /// DepthBands does). When the key has no model within `placeholderAfter` seconds, a flat tinted quad of the
    /// layer's size stands in (contract §1: every slot draws before BLENDER's set lands).
    /// </summary>
    public sealed class ModelBand
    {
        public readonly string key;
        public readonly float period, z;
        public readonly GameObject root;
        public readonly ModelView[] copies = new ModelView[3];
        public bool Ready => copies[0] != null && copies[0].Ready;
        public bool Placeholder { get; private set; }
        public bool Drawn => Ready || Placeholder;
        bool checkedDepth, shadowsOff;
        float born;
        readonly float placeholderWidth, placeholderHeight;
        readonly Color tint;
        Color haze = Color.white;

        public ModelBand(Transform parent, string key, float period, float z, float placeholderWidth, float placeholderHeight, Color tint)
        {
            this.key = key; this.period = period; this.z = z;
            this.placeholderWidth = placeholderWidth; this.placeholderHeight = placeholderHeight; this.tint = tint;
            root = new GameObject("Band " + key);
            root.transform.SetParent(parent, false);
            born = Time.time;
            for (int i = 0; i < 3; i++)
            {
                var go = new GameObject("Copy" + i);
                go.transform.SetParent(root.transform, false);
                copies[i] = go.AddComponent<ModelView>();
                copies[i].Load(key);
            }
        }

        /// <summary>Haze tint (contract §10 haze_rgb, mixed by depth) applied to the model's materials.</summary>
        public void SetHaze(Color c) { haze = c; if (Ready) foreach (var m in copies) m.SetTint(haze); }

        public void Place(float camX, float baseY, bool shown, float placeholderAfter = 1.5f)
        {
            if (root.activeSelf != shown) root.SetActive(shown);
            if (!Ready)
            {
                if (!Placeholder && Time.time - born > placeholderAfter && !copies[0].Loading) MakePlaceholders();
                if (!Placeholder) return;
            }
            else if (Placeholder) { Placeholder = false; foreach (var c in copies) { var q = c.transform.Find("Placeholder"); if (q != null) Object.Destroy(q.gameObject); } }
            if (Ready && !checkedDepth)
            {
                checkedDepth = true;
                var mb = ModelSwap.ModelBounds(copies[0].Instance);
                if (mb.center.z < 0f) foreach (var c in copies) c.transform.localScale = new Vector3(1f, 1f, -1f);
                foreach (var m in copies) { m.SetTint(haze); m.SetShadows(false); }
            }
            float k = Mathf.Round(camX / period);
            for (int i = 0; i < 3; i++)
                copies[i].transform.localPosition = new Vector3((k + i - 1) * period, baseY, z);
        }

        void MakePlaceholders()
        {
            Placeholder = true;
            foreach (var c in copies) StagePlaceholder.Quad(c.transform, "Placeholder", placeholderWidth, placeholderHeight, tint * haze);
        }

        public void Destroy() { if (root != null) Object.Destroy(root); }
    }

    /// <summary>U-090: flat tinted quads that stand in for a missing layer or piece (URP/Lit, no shadows, no collision).</summary>
    public static class StagePlaceholder
    {
        static Mesh quad;
        static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        static readonly MaterialPropertyBlock block = new MaterialPropertyBlock();

        public static Mesh Mesh()
        {
            if (quad != null) return quad;
            quad = new Mesh { name = "StagePlaceholder" };
            quad.vertices = new[] { new Vector3(-0.5f, 0f), new Vector3(0.5f, 0f), new Vector3(0.5f, 1f), new Vector3(-0.5f, 1f) };
            quad.uv = new[] { new Vector2(0f, 0f), new Vector2(1f, 0f), new Vector2(1f, 1f), new Vector2(0f, 1f) };
            quad.normals = new[] { Vector3.back, Vector3.back, Vector3.back, Vector3.back };
            quad.triangles = new[] { 0, 2, 1, 0, 3, 2 };
            quad.RecalculateBounds();
            return quad;
        }

        /// <summary>A `width` × `height` quad standing on its parent's origin, facing the camera (−z), tinted.</summary>
        public static GameObject Quad(Transform parent, string name, float width, float height, Color tint)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localScale = new Vector3(width, height, 1f);
            go.AddComponent<MeshFilter>().sharedMesh = Mesh();
            var mr = go.AddComponent<MeshRenderer>();
            var reg = Meridian.Rendering.ArtMaterials.Active;
            mr.sharedMaterial = reg != null && reg.meshLit != null ? reg.meshLit : new Material(Shader.Find("Universal Render Pipeline/Lit"));
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            block.Clear();
            block.SetColor(BaseColorId, tint);
            mr.SetPropertyBlock(block);
            return go;
        }
    }
}
