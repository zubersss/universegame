using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-076 flora diagnosis: reports how Unity (glTFast) imported every .glb in a folder: per mesh the vertex and
    /// triangle counts, which vertex attributes survived (normal, tangent, uv0, color), how flat the imported normals
    /// are (share of triangles whose three vertex normals all lie within 2° of the face normal), the renderers'
    /// materials and the generated material's maps. Output: logs/model_probe.txt and the Editor log.
    /// Run: tools/unity_compile.ps1 -ExecuteMethod Meridian.EditorTools.ModelProbe.Run   (folder: MERIDIAN_PROBE_DIR,
    /// default Assets/_Game/Art/props/earth_flora).
    /// </summary>
    public static class ModelProbe
    {
        public static void Run()
        {
            var dir = System.Environment.GetEnvironmentVariable("MERIDIAN_PROBE_DIR");
            if (string.IsNullOrEmpty(dir)) dir = "Assets/_Game/Art/props/earth_flora";
            var sb = new StringBuilder();
            foreach (var glb in Directory.GetFiles(dir, "*.glb").Select(p => p.Replace('\\', '/')).OrderBy(p => p))
            {
                var prefab = AssetDatabase.LoadMainAssetAtPath(glb) as GameObject;
                if (prefab == null) { sb.AppendLine($"{glb}: no GameObject main asset"); continue; }
                var all = AssetDatabase.LoadAllAssetsAtPath(glb);
                sb.AppendLine($"{glb}: sub-assets {string.Join(", ", all.Select(a => a.GetType().Name + ":" + a.name))}");
                foreach (var mf in prefab.GetComponentsInChildren<MeshFilter>(true))
                {
                    var m = mf.sharedMesh;
                    if (m == null) { sb.AppendLine($"  {mf.name}: no mesh"); continue; }
                    sb.AppendLine($"  {mf.name}: mesh '{m.name}' verts {m.vertexCount} tris {m.triangles.Length / 3} submeshes {m.subMeshCount} " +
                                  $"normal {m.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.Normal)} tangent {m.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.Tangent)} " +
                                  $"uv0 {m.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0)} color {m.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.Color)} " +
                                  $"readable {m.isReadable} bounds {m.bounds.size} flatShare {Flatness(m):F2} uvRange {UvRange(m)}");
                    var r = mf.GetComponent<Renderer>();
                    if (r != null) sb.AppendLine($"    renderer mats {string.Join(", ", r.sharedMaterials.Select(x => x == null ? "null" : x.name + "/" + x.shader.name))} castShadows {r.shadowCastingMode}");
                }
                var lod = prefab.GetComponentInChildren<LODGroup>(true);
                sb.AppendLine($"  LODGroup in prefab: {lod != null}");
            }
            foreach (var mat in Directory.GetFiles(ArtImporter.GeneratedModels + Path.GetFileName(dir), "*.mat").Select(p => p.Replace('\\', '/')).OrderBy(p => p))
            {
                var m = AssetDatabase.LoadAssetAtPath<Material>(mat);
                if (m == null) continue;
                sb.AppendLine($"{mat}: shader {m.shader.name} keywords [{string.Join(" ", m.shaderKeywords)}] base {Tex(m, "_BaseMap")} bump {Tex(m, "_BumpMap")} mask {Tex(m, "_MetallicGlossMap")} smooth {m.GetFloat("_Smoothness"):F2} metallic {m.GetFloat("_Metallic"):F2}");
            }
            var text = sb.ToString();
            Directory.CreateDirectory("logs");
            File.WriteAllText("logs/model_probe.txt", text);
            Debug.Log("[MERIDIAN] ModelProbe\n" + text);
        }

        static string Tex(Material m, string prop)
        {
            var t = m.GetTexture(prop) as Texture2D;
            if (t == null) return "none";
            var path = AssetDatabase.GetAssetPath(t);
            var ti = AssetImporter.GetAtPath(path) as TextureImporter;
            return $"{Path.GetFileName(path)} {t.width}x{t.height} {t.format} mips {t.mipmapCount} type {(ti != null ? ti.textureType.ToString() : "?")} sRGB {(ti != null ? ti.sRGBTexture.ToString() : "?")}";
        }

        /// <summary>Share of triangles whose three vertex normals all lie within 2° of the face normal (1 = flat shaded).</summary>
        static float Flatness(Mesh m)
        {
            if (!m.isReadable || !m.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.Normal)) return -1f;
            var v = m.vertices; var n = m.normals; var t = m.triangles;
            if (n.Length != v.Length || t.Length < 3) return -1f;
            int flat = 0, total = 0;
            const float cos2 = 0.99939f;
            for (int i = 0; i + 2 < t.Length; i += 3)
            {
                var fn = Vector3.Cross(v[t[i + 1]] - v[t[i]], v[t[i + 2]] - v[t[i]]);
                if (fn.sqrMagnitude < 1e-12f) continue;
                fn.Normalize();
                total++;
                if (Vector3.Dot(fn, n[t[i]].normalized) > cos2 && Vector3.Dot(fn, n[t[i + 1]].normalized) > cos2 && Vector3.Dot(fn, n[t[i + 2]].normalized) > cos2) flat++;
            }
            return total == 0 ? -1f : (float)flat / total;
        }

        static string UvRange(Mesh m)
        {
            if (!m.isReadable || !m.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0)) return "n/a";
            var uv = m.uv;
            if (uv.Length == 0) return "empty";
            float u0 = 9, u1 = -9, v0 = 9, v1 = -9;
            foreach (var p in uv) { u0 = Mathf.Min(u0, p.x); u1 = Mathf.Max(u1, p.x); v0 = Mathf.Min(v0, p.y); v1 = Mathf.Max(v1, p.y); }
            return $"u {u0:F3}..{u1:F3} v {v0:F3}..{v1:F3}";
        }
    }
}
