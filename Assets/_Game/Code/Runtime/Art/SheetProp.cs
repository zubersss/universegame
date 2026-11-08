using System.Collections.Generic;
using Meridian.Rendering;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Art
{
    /// <summary>
    /// U-113 (D-117, B-131): a prop drawn from a v3 sheet on the SpriteRenderer that held its card, once the key has no model
    /// (the camp props after B-131's export). Frame 0 at the sheet's PPU and pivot; a `tile` sheet (pad, wall) repeats its
    /// module across the footprint; otherwise the caller's fit rule stands (stretch to the cells, height to the footprint, or
    /// none: PoiPlacer's width fit). The sheet's Animator (&lt;key&gt;/animator, SheetAnimatorBuilder) plays its clips: PlayToward
    /// runs a one-shot forward or backward (the door's `open`), Loop holds a loop on or off (the smelter's `working` while its
    /// station works, the lamp's `flicker` by night). Nothing allocates per frame.
    /// </summary>
    public sealed class SheetProp : MonoBehaviour
    {
        public const string DoorClip = "open", WorkingClip = "working", FlickerClip = "flicker";

        public SpriteRenderer Renderer { get; private set; }
        public Animator Animator { get; private set; }
        public string Key { get; private set; }
        public Sprite First { get; private set; }
        public bool Ready { get; private set; }
        /// <summary>The sheet's `module_m` when it tiles (pad 2 m, wall 1 m); 0 for a one-off prop.</summary>
        public float ModuleM { get; private set; }
        public bool Tiles => ModuleM > 0f;
        public bool Interactable { get; private set; }
        /// <summary>The clip the Animator is on (null: frame 0, nothing playing).</summary>
        public string Playing { get; private set; }
        /// <summary>+1 after a forward one-shot (a door opened), −1 after a backward one (closed), 0 before either.</summary>
        public int Towards { get; private set; }
        public event System.Action<SheetProp> Loaded;

        /// <summary>The crafting station on the same object (the smelter): `working` loops while it works.</summary>
        public Meridian.Crafting.CraftingStation station;

        Vector2 footprint;
        bool stretch, heightFit;
        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>(3);
        IList<Sprite> sprites; TextAsset json; RuntimeAnimatorController controller;
        int pending;
        Vector3 wantScale = Vector3.one;
        bool scaleOwned;
        static Meridian.Planet.Lighting.DayNightLighting dayNight;

        /// <summary>Attaches to `sr` and starts loading `key`'s sheet; `footprint` in metres, `stretch` / `heightFit` as the caller fitted its card.</summary>
        public static SheetProp Attach(SpriteRenderer sr, string key, Vector2 footprint, bool stretch, bool heightFit)
        {
            var p = sr.gameObject.GetComponent<SheetProp>();
            if (p == null) p = sr.gameObject.AddComponent<SheetProp>();
            p.Renderer = sr;
            p.Key = key;
            p.footprint = footprint;
            p.stretch = stretch;
            p.heightFit = heightFit;
            p.station = sr.GetComponent<Meridian.Crafting.CraftingStation>();
            p.Load();
            return p;
        }

        void Load()
        {
            pending = 3;
            Fetch<TextAsset>(Key + "/json", a => json = a);
            Fetch<IList<Sprite>>(Key, a => sprites = a);
            var probe = Addressables.LoadResourceLocationsAsync(Key + "/animator", typeof(RuntimeAnimatorController));
            probe.Completed += l =>
            {
                bool has = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (this == null) return;
                if (has) Fetch<RuntimeAnimatorController>(Key + "/animator", a => controller = a); else Arrived();
            };
        }

        void Fetch<T>(string address, System.Action<T> set) where T : class
        {
            var h = ArtLoad.Asset<T>(address);
            handles.Add(h);
            h.Completed += op =>
            {
                if (this == null) return;
                if (op.Status == AsyncOperationStatus.Succeeded && op.Result != null) set(op.Result);
                Arrived();
            };
        }

        [System.Serializable] sealed class Sidecar { public bool tile, interactable; public float module_m; }

        void Arrived()
        {
            if (--pending > 0 || Ready) return;
            if (sprites == null || sprites.Count == 0) return; // no sheet after all: the card stays
            First = sprites[0];
            foreach (var s in sprites) if (s != null && s.name.EndsWith("_0", System.StringComparison.Ordinal)) First = s;
            var side = json != null ? JsonUtility.FromJson<Sidecar>(json.text) : null;
            if (side != null) { ModuleM = side.tile ? Mathf.Max(0f, side.module_m) : 0f; Interactable = side.interactable; }
            Renderer.sprite = First;
            Renderer.color = Color.white;
            var mat = ArtMaterials.MaterialFor(Key);
            if (mat != null) Renderer.sharedMaterial = mat;
            Fit();
            if (controller != null)
            {
                Animator = Renderer.GetComponent<Animator>();
                if (Animator == null) Animator = Renderer.gameObject.AddComponent<Animator>();
                Animator.runtimeAnimatorController = controller;
                Animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                Animator.speed = 0f; // frame 0 until a clip is asked for
                Animator.enabled = false; // U-159 (BudgetGate): an idle sheet holds its first drawing with no Animator running (PlayToward turns it on); B-195's three Earth POI sheets had put Earth C0 at 42 against 40
            }
            Ready = true;
            Loaded?.Invoke(this);
        }

        /// <summary>
        /// The drawn size: a tiling sheet repeats its module across the footprint's width (and fills its height when stretched);
        /// a stretched one-off fills the cells; a height-fit one keeps its proportions at the footprint's height; otherwise the
        /// caller's scale stands. Pure in FitScale, so PropSpriteTests covers the rules.
        /// </summary>
        void Fit()
        {
            var art = First.bounds.size;
            if (art.x <= 0f || art.y <= 0f) return;
            if (Tiles && footprint.x > 0f)
            {
                Renderer.drawMode = SpriteDrawMode.Tiled;
                Renderer.size = new Vector2(footprint.x, stretch && footprint.y > 0f ? footprint.y : art.y);
                wantScale = Vector3.one; scaleOwned = true;
            }
            else if ((stretch || heightFit) && footprint.y > 0f)
            {
                Renderer.drawMode = SpriteDrawMode.Simple;
                wantScale = FitScale(art, footprint, stretch); scaleOwned = true;
            }
            if (scaleOwned) Renderer.transform.localScale = wantScale;
        }

        /// <summary>Stretch: the footprint over the art's size on both axes; else uniform to the footprint's height.</summary>
        public static Vector3 FitScale(Vector2 art, Vector2 footprint, bool stretch) =>
            stretch ? new Vector3(footprint.x / art.x, footprint.y / art.y, 1f) : Vector3.one * (footprint.y / art.y);

        /// <summary>A one-shot: forward from its first drawing (speed 1), or backward from its last, holding the end. A backward play
        /// samples the state by hand each frame (Animator.speed may not go negative outside the recorder).</summary>
        public bool PlayToward(string clip, bool forward)
        {
            if (Animator == null) return false;
            int hash = Animator.StringToHash(clip);
            if (!Animator.HasState(0, hash)) return false;
            Animator.enabled = true;
            Animator.Play(hash, 0, forward ? 0f : 1f);
            Animator.speed = forward ? 1f : 0f;
            reversing = !forward; reverseHash = hash; reverseT = 1f; reverseLen = 0f;
            Playing = clip;
            Towards = forward ? 1 : -1;
            return true;
        }

        bool reversing; int reverseHash; float reverseT, reverseLen;

        /// <summary>The backward one-shot: the state's normalized time runs 1 → 0 at the clip's own length, then holds its first drawing.</summary>
        void StepReverse(float dt)
        {
            if (Animator == null) return;
            if (!reversing)
            {
                // A forward one-shot that reached its end holds its last drawing with the Animator off (the count); loops keep it on.
                if (Towards == 1 && Playing != null && Animator.enabled && Animator.speed > 0f)
                {
                    var st = Animator.GetCurrentAnimatorStateInfo(0);
                    if (!st.loop && st.normalizedTime >= 1f) { Animator.Update(0f); Animator.enabled = false; }
                }
                return;
            }
            if (reverseLen <= 0f) { var info = Animator.GetCurrentAnimatorStateInfo(0); reverseLen = info.length > 0f ? info.length : 0.5f; }
            reverseT -= dt / reverseLen;
            if (reverseT <= 0f) { reverseT = 0f; reversing = false; }
            Animator.Play(reverseHash, 0, reverseT);
            if (!reversing) { Animator.Update(0f); Animator.enabled = false; }
        }

        /// <summary>Holds a looping clip on (plays it) or off (back to frame 0, stopped).</summary>
        public bool Loop(string clip, bool on)
        {
            if (Animator == null) return false;
            int hash = Animator.StringToHash(clip);
            if (!Animator.HasState(0, hash)) return false;
            if (on && Playing != clip) { Animator.enabled = true; Animator.Play(hash, 0, 0f); Animator.speed = 1f; reversing = false; Playing = clip; }
            else if (!on && Playing == clip) { Animator.Play(hash, 0, 0f); Animator.speed = 0f; Playing = null; Animator.Update(0f); Animator.enabled = false; } // off: frame 0 shown, no Animator running (Bible §9.6 count)
            return true;
        }

        void LateUpdate()
        {
            if (!Ready) return;
            if (scaleOwned && Renderer.transform.localScale != wantScale) Renderer.transform.localScale = wantScale; // a later card fit (LoadArt / Dress) never undoes the sheet's
            if (Animator == null) return;
            StepReverse(Time.deltaTime);
            if (station != null) Loop(WorkingClip, station.Working);
            else if (Animator.HasState(0, Animator.StringToHash(FlickerClip)))
            {
                if (dayNight == null) dayNight = FindAnyObjectByType<Meridian.Planet.Lighting.DayNightLighting>();
                bool night = dayNight != null && Meridian.Planet.Lighting.DayNightMath.Daylight(dayNight.LocalTime) < 0.5f;
                Loop(FlickerClip, night);
            }
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
        }
    }
}
