using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace Meridian.Tests
{
    /// <summary>
    /// U-006: renders one asset key under a dim global light plus an upper-right point light to
    /// logs/preview_&lt;key&gt;.png. Runs inside the player loop (Light2D needs it) via
    /// tools/unity_art_preview.ps1, which sets MERIDIAN_PREVIEW_KEY. Skipped in normal runs.
    /// </summary>
    public class ArtPreviewCapture
    {
        public const string KeyVariable = "MERIDIAN_PREVIEW_KEY";
        const int Size = 1024;
        const float FrameHalf = 1f;

        [UnityEngine.TestTools.UnityTest]
        public IEnumerator RenderPreview()
        {
            var key = Environment.GetEnvironmentVariable(KeyVariable);
            if (string.IsNullOrEmpty(key)) Assert.Ignore($"Set {KeyVariable} (tools/unity_art_preview.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");

            var scene = SceneManager.CreateScene("ArtPreview");
            SceneManager.SetActiveScene(scene);

#if UNITY_EDITOR
            // U-075 / B-078: a 3D model (contract v2 §9) previews under the Earth Sun from the side rail.
            var glb = $"Assets/_Game/Art/{key}.glb";
            if (File.Exists(glb)) { yield return RenderModel(key, glb); yield break; }
#endif

            var handle = Addressables.LoadAssetAsync<IList<Sprite>>(key);
            yield return handle;
            var sprite = handle.Result?.OrderBy(s => FrameIndex(s.name)).FirstOrDefault();
            Assert.NotNull(sprite, $"no addressed sprite for '{key}'");

            var cam = new GameObject("PreviewCamera").AddComponent<Camera>();
            cam.transform.position = new Vector3(0, 0, -10);
            cam.orthographic = true;
            cam.orthographicSize = FrameHalf * 1.15f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.12f, 0.12f, 0.14f, 1f);

            var target = new GameObject("Target").AddComponent<SpriteRenderer>();
            target.sprite = sprite;
            var mat = Meridian.Rendering.ArtMaterials.MaterialFor(key); // Sprite_LitEmissive for keys with emission
            if (mat != null) target.sharedMaterial = mat;
            var b = sprite.bounds;
            float scale = FrameHalf / Mathf.Max(b.extents.x, b.extents.y);
            target.transform.localScale = Vector3.one * scale;
            target.transform.position = -b.center * scale;

            var allLayers = SortingLayer.layers.Select(l => l.id).ToArray();
            var global = new GameObject("GlobalLight").AddComponent<Light2D>();
            global.lightType = Light2D.LightType.Global;
            global.intensity = 0.25f;
            global.targetSortingLayers = allLayers;

            var point = new GameObject("PointLight").AddComponent<Light2D>();
            point.lightType = Light2D.LightType.Point;
            point.transform.position = new Vector3(FrameHalf * 0.9f, FrameHalf * 0.9f, 0f);
            point.intensity = 1.4f;
            point.pointLightOuterRadius = FrameHalf * 3f;
            point.targetSortingLayers = allLayers;
            SetPrivate(point, "m_NormalMapQuality", Light2D.NormalMapQuality.Accurate);
            SetPrivate(point, "m_NormalMapDistance", 1.5f);

            for (int i = 0; i < 3; i++) yield return null;

            Directory.CreateDirectory("logs");
            var lit = Render(cam);
            var output = $"logs/preview_{key.Replace('/', '_')}.png";
            File.WriteAllBytes(output, lit.EncodeToPNG());
            TestContext.Out.WriteLine($"[MERIDIAN] PREVIEW OK: {output} (material {target.sharedMaterial.shader.name})");

            // Second shot with the point light off: only the 0.25 global light and emission remain (U-019).
            point.intensity = 0f;
            for (int i = 0; i < 2; i++) yield return null;
            var dark = Render(cam);
            File.WriteAllBytes($"logs/preview_{key.Replace('/', '_')}_nopoint.png", dark.EncodeToPNG());
            Color32 hottest = default;
            int best = -1;
            foreach (var px in dark.GetPixels32())
            {
                int s = px.r + px.g + px.b;
                if (s > best) { best = s; hottest = px; }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] PREVIEW no point light: brightest pixel {hottest.r},{hottest.g},{hottest.b}");

            UnityEngine.Object.Destroy(lit);
            UnityEngine.Object.Destroy(dark);
            Addressables.Release(handle);
            yield return SceneManager.UnloadSceneAsync(scene);
        }

#if UNITY_EDITOR
        /// <summary>
        /// U-075 / B-078: a .glb model with its URP/Lit material built from the four maps (ModelMaterials, §9.1),
        /// posed at idle, lit by the Earth noon Sun (DayNightMath) and the Earth ambient, seen from the side rail
        /// (SideView, FOV 35°). Writes logs/preview_&lt;key&gt;.png (side view) and _34.png (a 35° turn, to show depth).
        /// </summary>
        IEnumerator RenderModel(string key, string glbPath)
        {
            var prefab = UnityEditor.AssetDatabase.LoadMainAssetAtPath(glbPath) as GameObject;
            Assert.NotNull(prefab, $"{glbPath}: no model (glTF importer missing?)");
            var go = UnityEngine.Object.Instantiate(prefab);
            go.transform.position = Vector3.zero;

            string dir = Path.GetDirectoryName(glbPath).Replace('\\', '/'), variant = Path.GetFileNameWithoutExtension(glbPath);
            Texture2D Map(string m) => UnityEditor.AssetDatabase.LoadAssetAtPath<Texture2D>($"{dir}/{variant}_{m}.png");
            var mat = Meridian.Rendering.ModelMaterials.FromMaps(Map("color"), Map("normal"), Map("mask"), Map("emission"), variant + "_preview");
            var rends = go.GetComponentsInChildren<Renderer>();
            Assert.Greater(rends.Length, 0, "the model has renderers");
            foreach (var r in rends) r.sharedMaterial = mat;

            // Pose: the idle clip a third of the way in (legacy clips from glTFast until ArtImporter v5's Animator).
            var anim = go.GetComponentInChildren<Animation>();
            if (anim != null && anim["idle"] != null) { var st = anim["idle"]; st.enabled = true; st.time = st.length * 0.33f; st.weight = 1f; anim.Sample(); st.enabled = false; }
            yield return null;

            var b = rends[0].bounds;
            foreach (var r in rends) b.Encapsulate(r.bounds);

            var p = Meridian.Planets.PlanetId.Earth;
            var sun = new GameObject("Sun").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = Meridian.Planet.Lighting.DayNightMath.SunColor(p, 0.5f);
            sun.intensity = Meridian.Planet.Lighting.DayNightMath.Sunlight(p);
            sun.shadows = LightShadows.Soft;
            sun.transform.rotation = Quaternion.Euler(45f, -35f, 0f); // high, from the upper left, slightly in front
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = Meridian.Planet.Lighting.DayNightMath.AmbientColor(p, 0.5f) * Meridian.Planet.Lighting.DayNightMath.AmbientIntensity(p, 0.5f);

            var cam = new GameObject("PreviewCamera").AddComponent<Camera>();
            cam.transform.position = new Vector3(b.center.x, b.center.y, -10f);
            Meridian.CameraRig.SideView.Configure(cam, b.extents.y * 1.25f);
            cam.transform.position = new Vector3(b.center.x, b.center.y, cam.transform.position.z);
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.45f, 0.58f, 0.75f, 1f); // Earth sky
            yield return null;

            string baseName = $"logs/preview_{key.Replace('/', '_')}";
            var side = Render(cam);
            File.WriteAllBytes(baseName + ".png", side.EncodeToPNG());
            go.transform.rotation = Quaternion.Euler(0f, 35f, 0f);
            yield return null;
            var turned = Render(cam);
            File.WriteAllBytes(baseName + "_34.png", turned.EncodeToPNG());
            TestContext.Out.WriteLine($"[MERIDIAN] model preview {key}: bounds {b.min} … {b.max}, {rends.Length} renderer(s), idle sampled {(anim != null && anim["idle"] != null)}, Sun {sun.intensity:F2} {sun.color}");
            UnityEngine.Object.Destroy(side); UnityEngine.Object.Destroy(turned);
            UnityEngine.Object.Destroy(go);
        }
#endif

        static Texture2D Render(Camera cam)
        {
            var rt = new RenderTexture(Size, Size, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt;
            cam.Render();
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(Size, Size, TextureFormat.RGBA32, false);
            tex.ReadPixels(new Rect(0, 0, Size, Size), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            cam.targetTexture = null;
            rt.Release();
            return tex;
        }

        static int FrameIndex(string name)
        {
            int us = name.LastIndexOf('_');
            return us >= 0 && int.TryParse(name.Substring(us + 1), out int i) ? i : 0;
        }

        static void SetPrivate(object target, string field, object value)
        {
            var f = target.GetType().GetField(field, BindingFlags.Instance | BindingFlags.NonPublic);
            Assert.NotNull(f, $"Light2D.{field} not found (URP version changed?)");
            f.SetValue(target, value);
        }
    }
}
