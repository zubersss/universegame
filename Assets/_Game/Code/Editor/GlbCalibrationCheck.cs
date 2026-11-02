using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-075 handshake with B-077 (contract v2.1 §9.1, D-063): reports how Unity (glTFast) imports BLENDER's
    /// calibration model: clips (name, length, loop), materials, feet height, and renders it from the side rail
    /// (camera at −Z looking +Z, so screen right = +X) to logs/glb_calibration_side.png: the emissive stripe must
    /// be on the right. Run: tools/unity_compile.ps1 -Graphics -ExecuteMethod Meridian.EditorTools.GlbCalibrationCheck.Run
    /// </summary>
    public static class GlbCalibrationCheck
    {
        const string Path = "Assets/_Game/Art/characters/calibration/base.glb";

        public static void Run()
        {
            var importer = AssetImporter.GetAtPath(Path);
            Debug.Log($"[MERIDIAN] GLB: importer {(importer != null ? importer.GetType().FullName : "none")}");
            var all = AssetDatabase.LoadAllAssetsAtPath(Path);
            Debug.Log($"[MERIDIAN] GLB: {all.Length} sub-assets: {string.Join(", ", all.Select(a => a.GetType().Name + ":" + a.name))}");
            var prefab = AssetDatabase.LoadMainAssetAtPath(Path) as GameObject;
            if (prefab == null) { Debug.LogError("[MERIDIAN] GLB: no GameObject main asset (no glTF importer?)"); return; }

            foreach (var clip in all.OfType<AnimationClip>())
                Debug.Log($"[MERIDIAN] GLB clip: {clip.name} length {clip.length:F3} s, loop {clip.isLooping}, legacy {clip.legacy}, fps {clip.frameRate}");
            var mats = all.OfType<Material>().ToArray();
            Debug.Log($"[MERIDIAN] GLB materials: {mats.Length} ({string.Join(", ", mats.Select(m => m.name + "/" + m.shader.name))})");

            var go = (GameObject)Object.Instantiate(prefab);
            try
            {
                go.transform.position = Vector3.zero;
                var rends = go.GetComponentsInChildren<Renderer>();
                // Contract v2.1 §9.1: the glb has no images; the material comes from the four PNGs beside it.
                var dir = System.IO.Path.GetDirectoryName(Path).Replace('\\', '/');
                var color = AssetDatabase.LoadAssetAtPath<Texture2D>(dir + "/base_color.png");
                var emission = AssetDatabase.LoadAssetAtPath<Texture2D>(dir + "/base_emission.png");
                var reg = Meridian.Rendering.ArtMaterials.Active;
                var baseMat = reg != null && reg.meshLitEmissive != null ? reg.meshLitEmissive : new Material(Shader.Find("Universal Render Pipeline/Lit"));
                var mat = new Material(baseMat);
                if (color != null) mat.SetTexture("_BaseMap", color);
                if (emission != null) { mat.EnableKeyword("_EMISSION"); mat.SetTexture("_EmissionMap", emission); mat.SetColor("_EmissionColor", Color.white * 2f); }
                foreach (var r in rends) r.sharedMaterial = mat;
                Debug.Log($"[MERIDIAN] GLB: preview material from maps: color {(color != null)}, emission {(emission != null)}");
                var b = rends.Length > 0 ? rends[0].bounds : new Bounds();
                foreach (var r in rends) b.Encapsulate(r.bounds);
                int tris = go.GetComponentsInChildren<MeshFilter>().Sum(f => f.sharedMesh != null ? f.sharedMesh.triangles.Length / 3 : 0)
                         + go.GetComponentsInChildren<SkinnedMeshRenderer>().Sum(s => s.sharedMesh != null ? s.sharedMesh.triangles.Length / 3 : 0);
                Debug.Log($"[MERIDIAN] GLB bounds: min {b.min} max {b.max} (feet y {b.min.y:F3}), renderers {rends.Length}, triangles {tris}, animator {go.GetComponentInChildren<Animator>() != null}, legacy animation {go.GetComponentInChildren<Animation>() != null}");

                // Facing, measured: where in Unity space do the vertices whose UVs sample the emissive stripe sit?
                if (emission != null)
                {
                    var px = emission.isReadable ? null : CopyReadable(emission);
                    var src = px ?? emission;
                    foreach (var smr in go.GetComponentsInChildren<SkinnedMeshRenderer>())
                    {
                        var baked = new Mesh();
                        smr.BakeMesh(baked, true);
                        var v = baked.vertices; var uv = baked.uv; var n = baked.normals;
                        Vector3 sum = Vector3.zero, nsum = Vector3.zero; int hits = 0;
                        for (int i = 0; i < v.Length && i < uv.Length; i++)
                        {
                            var c = src.GetPixelBilinear(uv[i].x, uv[i].y);
                            if (c.r + c.g + c.b < 0.6f) continue; // black = no emission
                            sum += smr.transform.TransformPoint(v[i]); hits++;
                            if (i < n.Length) nsum += smr.transform.TransformDirection(n[i]);
                        }
                        if (hits > 0)
                            Debug.Log($"[MERIDIAN] GLB stripe: {hits} emissive vertices, centre {sum / hits}, mean normal {(nsum / hits).normalized} ⇒ stripe on {((sum / hits).x > 0 ? "+X (screen right in the side view)" : "−X (screen LEFT: X flipped)")}");
                        else Debug.Log("[MERIDIAN] GLB stripe: no vertex samples the emissive area (stripe may sit inside a face; check UVs)");
                        Object.DestroyImmediate(baked);
                    }
                    if (px != null) Object.DestroyImmediate(px);
                }

                // Side-rail render: camera on −Z looking +Z ⇒ screen right is +X (the game's side view).
                var camGo = new GameObject("GlbCheckCam");
                var lightGo = new GameObject("GlbCheckLight");
                try
                {
                    var cam = camGo.AddComponent<Camera>();
                    cam.fieldOfView = 35f;
                    cam.clearFlags = CameraClearFlags.SolidColor;
                    cam.backgroundColor = new Color(0.2f, 0.22f, 0.25f);
                    float h = Mathf.Max(b.size.y, 1f);
                    camGo.transform.position = new Vector3(b.center.x, b.center.y, -h * 2.6f);
                    camGo.transform.rotation = Quaternion.identity;
                    var light = lightGo.AddComponent<Light>();
                    light.type = LightType.Directional;
                    lightGo.transform.rotation = Quaternion.Euler(30f, 20f, 0f);
                    var rt = new RenderTexture(960, 1080, 24);
                    cam.targetTexture = rt;
                    cam.Render();
                    RenderTexture.active = rt;
                    var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
                    tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
                    tex.Apply();
                    RenderTexture.active = null;
                    var outPath = System.IO.Path.GetFullPath("logs/glb_calibration_side.png");
                    File.WriteAllBytes(outPath, tex.EncodeToPNG());
                    Debug.Log($"[MERIDIAN] GLB: side render (screen right = +X) {outPath}");
                    cam.targetTexture = null;
                    Object.DestroyImmediate(tex);
                    rt.Release();
                }
                finally { Object.DestroyImmediate(camGo); Object.DestroyImmediate(lightGo); }
            }
            finally { Object.DestroyImmediate(go); }
        }

        /// <summary>A CPU-readable copy of a (non-readable, compressed) texture via a render texture blit.</summary>
        static Texture2D CopyReadable(Texture2D t)
        {
            var rt = RenderTexture.GetTemporary(t.width, t.height, 0, RenderTextureFormat.ARGB32);
            Graphics.Blit(t, rt);
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var copy = new Texture2D(t.width, t.height, TextureFormat.RGBA32, false);
            copy.ReadPixels(new Rect(0, 0, t.width, t.height), 0, 0);
            copy.Apply();
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
            return copy;
        }
    }
}
