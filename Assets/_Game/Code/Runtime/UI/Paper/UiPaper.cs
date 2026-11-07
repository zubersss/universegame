using System.Collections.Generic;
using Meridian.Art;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-124 (contract §11.6, B-151): the paper and sign panels as 9-slice sprites. The importer turns the json's
    /// `"slice": [l, t, r, b]` into the sprite border; here a panel Image switches to Sliced once its key is on disk. A missing key
    /// is probed, never loaded blind (no Addressables error), and the theme's flat fill stays. The art draws 1:1 (one sprite texel per
    /// canvas pixel at 1080p) so the ink line keeps its weight; the sprite handle lives on the target and goes with it.
    /// </summary>
    public static class UiPaper
    {
        /// <summary>The ink the panels' own text takes once the paper is under it (the theme's light text is for the dark fill).</summary>
        public static readonly Color Ink = new Color(0.13f, 0.09f, 0.06f, 1f);
        /// <summary>How far into its border the paper's frame reaches past a modal panel's content rect (the rest stays outside).</summary>
        public const float BorderReach = 0.75f;

        /// <summary>Puts the 9-slice `key` on `target` as is (its size unchanged); `done(true)` once it draws, `done(false)` when the
        /// key is not on disk or fails to load.</summary>
        public static void Apply(Image target, string key, System.Action<bool> done = null)
        {
            Load(target, key, sprite =>
            {
                Dress(target, sprite);
                InkTexts(target.transform);
                done?.Invoke(true);
            }, done);
        }

        /// <summary>A UiKit.ModalPanel: the paper goes on its Frame (the Image behind the panel), grown past the content rect by
        /// <see cref="BorderReach"/> of each border, so the content never sits on a curl, a nail or a rolled end; the panel's own
        /// fill turns clear (it still takes the clicks) and its text turns to ink.</summary>
        public static void ApplyModal(Image panel, string key, System.Action<bool> done = null)
        {
            var frame = panel != null && panel.transform.parent != null ? panel.transform.parent.GetComponent<Image>() : null;
            if (frame == null) { done?.Invoke(false); return; }
            Load(panel, key, sprite =>
            {
                Dress(frame, sprite);
                var size = panel.rectTransform.sizeDelta;
                var b = BorderOnCanvas(sprite) * BorderReach; // (left, bottom, right, top)
                frame.rectTransform.sizeDelta = FrameSize(size, b);
                frame.rectTransform.anchoredPosition = FrameOffset(b);
                panel.color = Color.clear;
                InkTexts(panel.transform);
                done?.Invoke(true);
            }, done);
        }

        /// <summary>The frame's size around a content rect for borders b = (left, bottom, right, top). Pure.</summary>
        public static Vector2 FrameSize(Vector2 content, Vector4 b) => content + new Vector2(b.x + b.z, b.y + b.w);
        /// <summary>The frame's centre offset so each border reaches outward by its own width. Pure.</summary>
        public static Vector2 FrameOffset(Vector4 b) => new Vector2((b.z - b.x) * 0.5f, (b.w - b.y) * 0.5f);

        /// <summary>The sprite's border in canvas pixels when drawn 1:1 (the Image's pixels-per-unit set by <see cref="Dress"/>).</summary>
        public static Vector4 BorderOnCanvas(Sprite s) => s != null ? s.border : Vector4.zero;

        static void Dress(Image img, Sprite sprite)
        {
            img.sprite = sprite;
            img.type = sprite.border.sqrMagnitude > 0f ? Image.Type.Sliced : Image.Type.Simple; // no border: the card stretches whole
            img.fillCenter = true;
            img.color = Color.white;
            var canvas = img.canvas;
            float refPpu = canvas != null ? canvas.referencePixelsPerUnit : 100f;
            img.pixelsPerUnitMultiplier = sprite.pixelsPerUnit > 0f ? refPpu / sprite.pixelsPerUnit : 1f; // 1:1: a 48 px corner is 48 canvas px
        }

        /// <summary>The panel's own text (not a button's label, not a cell's count: anything under another Image keeps its colour)
        /// turns to ink, without the light rim UiKit.Text gives it for the dark fill.</summary>
        public static int InkTexts(Transform panel)
        {
            int n = 0;
            foreach (var t in panel.GetComponentsInChildren<Text>(true))
            {
                if (UnderOtherImage(t.transform, panel)) continue;
                t.color = Ink;
                var rim = t.GetComponent<Outline>();
                if (rim != null) rim.enabled = false;
                n++;
            }
            return n;
        }

        static bool UnderOtherImage(Transform t, Transform panel)
        {
            for (var p = t.parent; p != null && p != panel; p = p.parent)
                if (p.GetComponent<Image>() != null) return true;
            return false;
        }

        /// <summary>A parts sheet's sprites by name (the Film switch's `off` / `on`); `ready` is not called when the key is absent.
        /// The handle lives on `owner` like a panel's.</summary>
        public static void LoadParts(Image owner, string key, System.Action<Dictionary<string, Sprite>> ready)
        {
            LoadList(owner, key, list =>
            {
                var byName = new Dictionary<string, Sprite>(list.Count);
                foreach (var s in list) if (s != null) byName[s.name] = s;
                ready(byName);
            }, null);
        }

        static void Load(Image owner, string key, System.Action<Sprite> ready, System.Action<bool> done) =>
            LoadList(owner, key, list =>
            {
                if (list[0] == null) { done?.Invoke(false); return; }
                ready(list[0]);
            }, done);

        static void LoadList(Image owner, string key, System.Action<IList<Sprite>> ready, System.Action<bool> done)
        {
            if (owner == null || string.IsNullOrEmpty(key)) { done?.Invoke(false); return; }
            var probe = Addressables.LoadResourceLocationsAsync(key); // untyped: a sprite list sits on its texture entry (FloraRigs probes the same way)
            probe.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (!exists || owner == null) { done?.Invoke(false); return; }
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                var keep = owner.gameObject.AddComponent<PaperHandle>();
                keep.handle = h;
                h.Completed += op =>
                {
                    if (owner == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0)
                    { done?.Invoke(false); return; }
                    ready(op.Result);
                };
            };
        }

    }
}
