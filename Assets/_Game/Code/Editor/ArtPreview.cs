using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Meridian.EditorTools
{
    /// <summary>
    /// Renders one asset key under a dim global light plus an upper-right point light to
    /// logs/preview_&lt;key&gt;.png (U-006). Batch: tools/unity_art_preview.ps1 &lt;key&gt;.
    /// </summary>
    public static class ArtPreview
    {
        public const string ScenePath = "Assets/_Game/Scenes/ArtPreview.unity";
        const int Size = 1024;
        const float FrameHalf = 1f;
        public const int SceneVersion = 2;

        public static void RunFromCommandLine()
        {
            var args = Environment.GetCommandLineArgs();
            int i = Array.IndexOf(args, "-artKey");
            string key = i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
            string output = null;
            try { output = key == null ? null : Render(key); }
            catch (Exception e) { Debug.LogError($"[MERIDIAN] PREVIEW FAILED: {e.Message}"); }
            if (output != null) Debug.Log($"[MERIDIAN] PREVIEW OK: {output}");
            else Debug.LogError($"[MERIDIAN] PREVIEW FAILED: key '{key}' has no addressed sprite");
            EditorApplication.Exit(output != null ? 0 : 1);
        }

        /// <summary>Asset path currently holding the address = key (real art or placeholder).</summary>
        public static string ResolvePath(string key)
        {
            var settings = ArtImporter.Settings;
            foreach (var g in settings.groups)
            {
                if (g == null) continue;
                var e = g.entries.FirstOrDefault(x => x.address == key);
                if (e != null) return e.AssetPath;
            }
            return null;
        }

        public static string Render(string key)
        {
            var path = ResolvePath(key);
            if (path == null) return null;
            var sprite = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Sprite>().OrderBy(s => s.name).FirstOrDefault();
            if (sprite == null) return null;

            var scene = EditorSceneManager.OpenScene(EnsureScene(), OpenSceneMode.Single);
            var target = GameObject.Find("Target").GetComponent<SpriteRenderer>();
            var cam = GameObject.Find("PreviewCamera").GetComponent<Camera>();
            // Lights stay where the saved scene put them (Light2D rebuilds its mesh and culling
            // bounds in LateUpdate, which never runs in batch); the sprite is scaled to fit instead.
            target.sprite = sprite;
            var b = sprite.bounds;
            float scale = FrameHalf / Mathf.Max(b.extents.x, b.extents.y);
            target.transform.localScale = Vector3.one * scale;
            target.transform.position = -b.center * scale;
            cam.orthographicSize = FrameHalf * 1.15f;

            var rt = new RenderTexture(Size, Size, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt;
            cam.Render(); // first pass lets the 2D renderer pick up the moved light's bounds
            cam.Render();
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(Size, Size, TextureFormat.RGBA32, false);
            tex.ReadPixels(new Rect(0, 0, Size, Size), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            cam.targetTexture = null;

            Directory.CreateDirectory("logs");
            var output = $"logs/preview_{key.Replace('/', '_')}.png";
            File.WriteAllBytes(output, tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);
            rt.Release();
            UnityEngine.Object.DestroyImmediate(rt);
            EditorSceneManager.CloseScene(scene, false);
            return output;
        }

        /// <summary>Creates ArtPreview.unity once: camera, Sprite-Lit target, global + upper-right point light.</summary>
        public static string EnsureScene()
        {
            if (File.Exists(ScenePath)) return ScenePath;
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var camGo = new GameObject("PreviewCamera");
            camGo.transform.position = new Vector3(0, 0, -10);
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = true;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.12f, 0.12f, 0.14f, 1f);

            var target = new GameObject("Target").AddComponent<SpriteRenderer>();
            var lit = AssetDatabase.LoadAssetAtPath<Material>(
                "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Lit-Default.mat");
            if (lit != null) target.sharedMaterial = lit;

            var global = new GameObject("GlobalLight").AddComponent<Light2D>();
            global.lightType = Light2D.LightType.Global;
            global.intensity = 0.25f;

            var point = new GameObject("PointLight").AddComponent<Light2D>();
            point.transform.position = new Vector3(FrameHalf * 0.9f, FrameHalf * 0.9f, -1f);
            point.lightType = Light2D.LightType.Point;
            point.intensity = 1.4f;
            point.pointLightOuterRadius = FrameHalf * 3f;
            var so = new SerializedObject(point); // normal-map settings are read-only in the API
            so.FindProperty("m_NormalMapQuality").intValue = (int)Light2D.NormalMapQuality.Accurate;
            so.FindProperty("m_NormalMapDistance").floatValue = 1.5f;
            so.ApplyModifiedPropertiesWithoutUndo();

            EditorSceneManager.SaveScene(scene, ScenePath);
            return ScenePath;
        }
    }
}
