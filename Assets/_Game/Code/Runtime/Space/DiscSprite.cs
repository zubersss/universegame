using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rendering;
using Meridian.View2D;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Space
{
    /// <summary>
    /// U-103 (D-098, B-119): a body drawn as its painted disc sheet (`planets/&lt;name&gt;/disc`): the idle clip stepped at
    /// 12 Hz on the cartoon clock, scaled so the sidecar's radius_u draws as the body's visual radius (the sheet is imported
    /// at space_ppu 3, so radius_u is the drawing's radius in units: scale = radius / radius_u). A wrong space_ppu or
    /// radius_u is therefore a size test failure, not a look. Releases its handles with the world.
    /// U-117 (2) / D-128: the ship view magnifies a disc up to ~33×, where the 64-px far frame can only show texel steps; above
    /// NearAbove screen pixels per far texel the disc swaps to its static near frame (`&lt;key&gt;_near`, B-143: the far frame 0 at
    /// scale_vs_far, imported at space_ppu × k, so the same transform scale draws the same world size) and back under NearBelow.
    /// </summary>
    public sealed class DiscSprite : MonoBehaviour
    {
        [System.Serializable]
        public sealed class Sidecar { public string key, style; public float ppu, space_ppu, radius_u, radius_px, scale_vs_far; public int frames, fps; public string near_of; }

        /// <summary>Screen pixels per far texel above which the near frame shows, and below which the far sheet returns (hysteresis).</summary>
        public const float NearAbove = 6f, NearBelow = 5f;
        public const string NearSuffix = "_near";

        /// <summary>Screen pixels per texel of a sprite at `ppu` seen by an orthographic camera of half-height `orthoSize` on a `screenHeightPx` tall frame. Pure.</summary>
        public static float Magnification(float screenHeightPx, float orthoSize, float ppu)
            => orthoSize > 0f && ppu > 0f ? screenHeightPx / (2f * orthoSize) / ppu : 0f;

        /// <summary>Whether the near frame should show at `magnification`, given whether it shows now (NearAbove up, NearBelow down). Pure.</summary>
        public static bool WantsNear(float magnification, bool usingNear) => usingNear ? magnification >= NearBelow : magnification >= NearAbove;

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
        /// <summary>True while the near frame is on the renderer (D-128).</summary>
        public bool UsingNear { get; private set; }
        /// <summary>The near frame once loaded (null: none exported for this body, or not yet asked for).</summary>
        public Sprite NearSprite { get; private set; }
        public bool NearProbed => nearProbed;
        /// <summary>Screen pixels per far texel at the last frame (0 before the sidecar or without a camera).</summary>
        public float LastMagnification { get; private set; }
        /// <summary>The camera the magnification is judged against (Camera.main when unset).</summary>
        public Camera view;

        Sprite[] sprites;
        ArtClip idle;
        bool hasIdle;
        float time;
        AsyncOperationHandle<IList<Sprite>> sheet;
        AsyncOperationHandle<TextAsset> json;
        AsyncOperationHandle<IList<Sprite>> nearSheet;
        bool nearProbed;
        float nextViewProbe;

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
            if (UsingNear) return; // the far clip keeps its clock; the near frame stays on the renderer
            if (sprites != null && frame >= 0 && frame < sprites.Length) Renderer.sprite = sprites[frame];
        }

        void LateUpdate()
        {
            if (sprites == null) return;
            time += Time.deltaTime;
            int f = hasIdle ? idle.start + SheetClock.Frame(time, idle.length, idle.loop) : SheetClock.Frame(time, sprites.Length, true);
            if (f != Frame) Show(f);
            UpdateNear();
        }

        /// <summary>D-128: judge the magnification, ask for the near frame the first time it is wanted, swap either way with hysteresis.</summary>
        void UpdateNear()
        {
            if (Json == null) return;
            if (view == null)
            {
                // The Space camera, not whichever camera is tagged main while both scenes are loaded; the scene search runs at most once a second (it allocates and costs ~0.1 ms).
                if (Time.unscaledTime < nextViewProbe) return;
                nextViewProbe = Time.unscaledTime + 1f;
                var sc = FindAnyObjectByType<SpaceCamera>();
                view = sc != null ? sc.GetComponent<Camera>() : null;
                if (view == null) return;
            }
            var cam = view;
            LastMagnification = Magnification(Screen.height, cam.orthographicSize, Json.space_ppu > 0f ? Json.space_ppu : 3f);
            bool want = WantsNear(LastMagnification, UsingNear);
            if (want && !nearProbed) ProbeNear();
            if (want && NearSprite != null && !UsingNear)
            {
                UsingNear = true;
                Renderer.sprite = NearSprite;
            }
            else if (!want && UsingNear)
            {
                UsingNear = false;
                Show(Frame);
            }
        }

        void ProbeNear()
        {
            nearProbed = true;
            string nearKey = Key + NearSuffix;
            var probe = Addressables.LoadResourceLocationsAsync(nearKey, typeof(Sprite));
            probe.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (!exists || this == null) return;
                nearSheet = ArtLoad.Asset<IList<Sprite>>(nearKey);
                nearSheet.Completed += op =>
                {
                    if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    NearSprite = op.Result[0];
                };
            };
        }

        void OnDestroy()
        {
            if (sheet.IsValid()) ArtLoad.Release(sheet);
            if (json.IsValid()) ArtLoad.Release(json);
            if (nearSheet.IsValid()) ArtLoad.Release(nearSheet);
        }
    }
}
