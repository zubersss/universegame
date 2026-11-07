using System.Collections.Generic;
using Meridian.Art;
using Meridian.Flora;
using Meridian.Rendering;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Space
{
    /// <summary>
    /// U-103 (D-111, B-122): the top-down Pilgrim drawn from the rig's `pilgrim_top` plant (hull + two fins, nose at +x, its
    /// fin_wobble at 12 Hz) under a `Rig` child of the ship, fitted to Length along the nose; the legacy `View` sprite is hidden
    /// once the rig draws. Added by SpaceShip in Awake; without the rig in the catalog nothing changes.
    /// </summary>
    public sealed class ShipTopView : MonoBehaviour
    {
        public const string TopPlant = "pilgrim_top";
        /// <summary>Nose to tail in space units: the width the legacy sprite was fitted to (SceneAuthoring: worldWidth 4).</summary>
        public const float Length = 4f;

        public RigInstance Rig { get; private set; }
        public bool RigReady => Rig != null;
        public bool UsesRig { get; private set; }
        /// <summary>The uniform scale that fits the hull to Length (SpaceShip multiplies its stretch onto it).</summary>
        public float FitScale { get; private set; } = 1f;

        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>();
        TextAsset json; IList<Sprite> sprites; RuntimeAnimatorController controller;
        int pending;

        void Start()
        {
            var probe = Addressables.LoadResourceLocationsAsync(ArtKeys.Ships.PilgrimRig + FloraRigs.JsonSuffix, typeof(TextAsset));
            probe.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                ArtLoad.Release(loc);
                if (this == null || !exists) return;
                UsesRig = true;
                pending = 3;
                Fetch<TextAsset>(ArtKeys.Ships.PilgrimRig + FloraRigs.JsonSuffix, a => json = a);
                Fetch<IList<Sprite>>(ArtKeys.Ships.PilgrimRig, a => sprites = a);
                var animProbe = Addressables.LoadResourceLocationsAsync(ArtKeys.Ships.PilgrimRig + FloraRigs.AnimatorSuffix, typeof(RuntimeAnimatorController));
                animProbe.Completed += l =>
                {
                    bool has = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                    ArtLoad.Release(l);
                    if (this == null) return;
                    if (has) Fetch<RuntimeAnimatorController>(ArtKeys.Ships.PilgrimRig + FloraRigs.AnimatorSuffix, a => controller = a); else Arrived();
                };
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

        void Arrived()
        {
            if (--pending > 0 || Rig != null || json == null || sprites == null) return;
            var set = RigSet.Parse(json.text, out _);
            var def = set?.FindPlant(TopPlant);
            if (def == null) return; // no top plant drawn: the legacy sprite stays
            var legacy = transform.Find("View");
            var sr = legacy != null ? legacy.GetComponent<SpriteRenderer>() : null;
            var rigRoot = new GameObject("Rig").transform;
            rigRoot.SetParent(transform, false);
            Rig = RigBuild.Build(def, RigBuild.ByName(sprites), rigRoot, controller, sr != null ? sr.sortingLayerID : 0, sr != null ? sr.sortingOrder : 20, ArtMaterials.MaterialFor(ArtKeys.Ships.PilgrimRig));
            // The hull part (the root bone's renderer) is drawn nose right; fit its width to Length.
            var hull = Rig.Parts.Length > 0 ? Rig.Parts[0] : null;
            float drawn = hull != null && hull.sprite != null ? hull.sprite.bounds.size.x : 0f;
            FitScale = drawn > 0f ? Length / drawn : 1f;
            Rig.Root.localScale = new Vector3(FitScale, FitScale, 1f);
            if (sr != null) sr.enabled = false;
            Rig.Play("fin_wobble");
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
        }
    }
}
