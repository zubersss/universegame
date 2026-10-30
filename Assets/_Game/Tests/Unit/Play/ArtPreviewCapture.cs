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
            target.sprite = sprite; // URP 2D default sprite material is Sprite-Lit-Default
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

            Directory.CreateDirectory("logs");
            var output = $"logs/preview_{key.Replace('/', '_')}.png";
            File.WriteAllBytes(output, tex.EncodeToPNG());
            TestContext.Out.WriteLine($"[MERIDIAN] PREVIEW OK: {output}");

            UnityEngine.Object.Destroy(tex);
            rt.Release();
            Addressables.Release(handle);
            yield return SceneManager.UnloadSceneAsync(scene);
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
