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
    /// canvas pixel at 1080p) so the ink line keeps its weight; the sprite handle lives on the target and goes with it. U-181 (B-208): the
    /// flat papers get the grain tiled over them, masked by their own shape.
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
                Grain(target, key);
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
                Grain(frame, key);
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

        // ---- U-181 (B-208): the paper grain, tiled over the flat papers ----

        public const string GrainKey = "ui/panels/grain";
        /// <summary>The papers B-208 exported flat for the tiled grain (their json's "grain": "ui/panels/grain"; MenuHudTests keeps the two equal).</summary>
        public static readonly HashSet<string> Grained = new HashSet<string>
        {
            "ui/panels/inventory", "ui/panels/pause", "ui/panels/scroll", "ui/panels/settings", "ui/panels/sign", "ui/map/system_panel", "ui/rank/certificate",
            "ui/hints/climb_up", "ui/hints/dig_down", "ui/hints/pack_full", "ui/hints/sell", "ui/hints/skill_tree", "ui/hints/surface_line",
        };
        static Sprite grain;
        static bool grainAsked;
        static readonly List<Image> waitingForGrain = new List<Image>();

        /// <summary>A paper's grain layer: its "Grain" child (the paper's own shape, a Mask showing nothing) and the tiled grain under it.</summary>
        public static Image GrainOf(Image paper)
        {
            var g = paper != null ? paper.transform.Find("Grain") : null;
            var t = g != null ? g.Find("Tile") : null;
            return t != null ? t.GetComponent<Image>() : null;
        }

        /// <summary>
        /// B-208: the grain tiled over a flat paper at 1 texel = 1 canvas px (1 screen px at 1080p), never stretched, inside the paper's wavy
        /// edge: the first child repeats the paper (same sprite and slicing) as a Mask that draws nothing, the tiled grain its only child, so
        /// the mask clips the grain alone (the paper's other children, a seal or a cap hanging over its edge, stay whole). Papers not
        /// exported flat keep none.
        /// </summary>
        public static void Grain(Image paper, string key)
        {
            var old = paper.transform.Find("Grain");
            if (!Grained.Contains(key)) { if (old != null) Object.Destroy(old.gameObject); return; }
            Image shape;
            if (old == null)
            {
                var go = new GameObject("Grain", typeof(RectTransform));
                go.transform.SetParent(paper.transform, false);
                Fill((RectTransform)go.transform);
                shape = go.AddComponent<Image>();
                shape.raycastTarget = false;
                go.AddComponent<Mask>().showMaskGraphic = false;
                var tgo = new GameObject("Tile", typeof(RectTransform));
                tgo.transform.SetParent(go.transform, false);
                Fill((RectTransform)tgo.transform);
                var tile = tgo.AddComponent<Image>();
                tile.raycastTarget = false;
                tile.type = Image.Type.Tiled;
                tile.enabled = false;
            }
            else shape = old.GetComponent<Image>();
            shape.transform.SetAsFirstSibling(); // over the paper, under everything on it
            shape.sprite = paper.sprite; shape.type = paper.type; shape.fillCenter = true; shape.pixelsPerUnitMultiplier = paper.pixelsPerUnitMultiplier;
            var tileImg = GrainOf(paper);
            if (grain != null) { SetGrain(tileImg); return; }
            if (!waitingForGrain.Contains(tileImg)) waitingForGrain.Add(tileImg);
            if (grainAsked) return;
            grainAsked = true;
            var h = ArtLoad.Asset<IList<Sprite>>(GrainKey); // kept for the session: one 128 px tile every paper shares
            h.Completed += op =>
            {
                if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) { grainAsked = false; return; }
                grain = op.Result[0];
                foreach (var w in waitingForGrain) if (w != null) SetGrain(w);
                waitingForGrain.Clear();
            };
        }

        static void SetGrain(Image tile)
        {
            if (tile == null) return;
            tile.sprite = grain;
            var canvas = tile.canvas;
            float refPpu = canvas != null ? canvas.referencePixelsPerUnit : 100f;
            tile.pixelsPerUnitMultiplier = grain.pixelsPerUnit > 0f ? refPpu / grain.pixelsPerUnit : 1f; // a 128-texel tile spans 128 canvas px
            tile.color = Color.white;
            tile.enabled = true;
        }

        static void Fill(RectTransform rt) { rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero; rt.pivot = new Vector2(0.5f, 0.5f); }

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

        /// <summary>A fill this opaque is the text's own ground (a cell, an action button); a fainter one (the menu buttons' 0.08 white) lets the paper
        /// show through, so its label takes ink like the rest (the 15:26 capture: light labels on cream).</summary>
        public const float OwnGroundAlpha = 0.35f;

        static bool UnderOtherImage(Transform t, Transform panel)
        {
            for (var p = t.parent; p != null && p != panel; p = p.parent)
            {
                var img = p.GetComponent<Image>();
                if (img != null && img.color.a >= OwnGroundAlpha) return true;
            }
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
