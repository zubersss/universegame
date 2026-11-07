using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rendering;
using Meridian.View2D;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Space
{
    /// <summary>
    /// U-103 (D-098, B-119): a body drawn as its painted disc sheet (`planets/&lt;name&gt;/disc`): the idle clip stepped at
    /// 12 Hz on the cartoon clock, scaled so the sidecar's radius_u draws as the body's visual radius (the sheet is imported
    /// at space_ppu 3, so radius_u is the drawing's radius in units: scale = radius / radius_u). A wrong space_ppu or
    /// radius_u is therefore a size test failure, not a look. Releases its handles with the world.
    /// </summary>
    public sealed class DiscSprite : MonoBehaviour
    {
        [System.Serializable]
        public sealed class Sidecar { public string key, style; public float ppu, space_ppu, radius_u; public int frames, fps; }

        public SpriteRenderer Renderer { get; private set; }
        public string Key { get; private set; }
        /// <summary>The body's visual radius (units) the drawing is scaled to.</summary>
        public float Radius { get; private set; }
        public Sidecar Json { get; private set; }
        public bool Ready => sprites != null && Json != null && Json.radius_u > 0f;
        /// <summary>The sheet frame shown (−1 before the sheet arrives).</summary>
        public int Frame { get; private set; } = -1;
        public int FrameCount => sprites != null ? sprites.Length : 0;
        /// <summary>Uniform scale applied: radius / radius_u (1 until the sidecar arrives).</summary>
        public float Scale => Json != null && Json.radius_u > 0f ? Radius / Json.radius_u : 1f;

        Sprite[] sprites;
        ArtClip idle;
        bool hasIdle;
        float time;
        AsyncOperationHandle<IList<Sprite>> sheet;
        AsyncOperationHandle<TextAsset> json;

        public void Load(string key, float radius, int sortingOrder)
        {
            Key = key;
            Radius = radius;
            Renderer = GetComponent<SpriteRenderer>();
            if (Renderer == null) Renderer = gameObject.AddComponent<SpriteRenderer>();
            Renderer.sortingOrder = sortingOrder;
            var mat = ArtMaterials.MaterialFor(key);
            if (mat != null) Renderer.sharedMaterial = mat;
            sheet = ArtLoad.Asset<IList<Sprite>>(key);
            sheet.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                sprites = Sorted(op.Result);
                var clips = ArtMaterials.ClipsFor(key);
                hasIdle = clips != null && clips.TryGet("idle", out idle) && idle.length > 0;
                Apply();
            };
            json = ArtLoad.Asset<TextAsset>(key + "/json");
            json.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                Json = JsonUtility.FromJson<Sidecar>(op.Result.text);
                Apply();
            };
        }

        static Sprite[] Sorted(IList<Sprite> list)
        {
            var arr = new Sprite[list.Count];
            for (int i = 0; i < arr.Length; i++) arr[i] = list[i];
            System.Array.Sort(arr, (a, b) => Index(a.name).CompareTo(Index(b.name)));
            return arr;
        }

        static int Index(string name)
        {
            int us = name.LastIndexOf('_');
            return us >= 0 && int.TryParse(name.Substring(us + 1), out int i) ? i : 0;
        }

        void Apply()
        {
            if (Json != null && Json.radius_u > 0f) transform.localScale = Vector3.one * (Radius / Json.radius_u);
            if (sprites != null && Frame < 0) Show(0);
        }

        void Show(int frame)
        {
            Frame = frame;
            if (sprites != null && frame >= 0 && frame < sprites.Length) Renderer.sprite = sprites[frame];
        }

        void LateUpdate()
        {
            if (sprites == null) return;
            time += Time.deltaTime;
            int f = hasIdle ? idle.start + SheetClock.Frame(time, idle.length, idle.loop) : SheetClock.Frame(time, sprites.Length, true);
            if (f != Frame) Show(f);
        }

        void OnDestroy()
        {
            if (sheet.IsValid()) ArtLoad.Release(sheet);
            if (json.IsValid()) ArtLoad.Release(json);
        }
    }
}
