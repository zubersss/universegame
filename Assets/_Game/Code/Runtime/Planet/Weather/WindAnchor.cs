using System.Collections.Generic;
using Meridian.Art;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Planet.Weather
{
    /// <summary>
    /// U-144 (Bible §7.9): a wind anchor on Neptune: the surveyor who holds one (Interact within Reach) stands fast through the gusts (no drift).
    /// Drawn with B-161's `props/neptune/wind_anchor` when its sheet is in (nothing until then: a missing key never logs). Where anchors stand
    /// (a POI, the Builder) is their own card; the build gate ("anchors needed to build") too.
    /// </summary>
    public sealed class WindAnchor : MonoBehaviour
    {
        public const string ArtKey = "props/neptune/wind_anchor";
        public const float Reach = 1.5f;
        /// <summary>Past this the hold lets go (the surveyor walked off).</summary>
        public const float LetGo = Reach + 0.5f;

        static readonly List<WindAnchor> all = new List<WindAnchor>();
        public static IReadOnlyList<WindAnchor> All => all;

        /// <summary>Whether feet at p are within an anchor's reach. Pure.</summary>
        public static bool WithinReach(Vector2 anchor, Vector2 p, float reach = Reach) => (anchor - p).sqrMagnitude <= reach * reach;

        /// <summary>The nearest anchor within reach of p, or null.</summary>
        public static WindAnchor Near(Vector2 p, float reach = Reach)
        {
            WindAnchor best = null; float bestD = float.MaxValue;
            foreach (var a in all)
            {
                float d = ((Vector2)a.transform.position - p).sqrMagnitude;
                if (d <= reach * reach && d < bestD) { best = a; bestD = d; }
            }
            return best;
        }

        SpriteRenderer view;
        AsyncOperationHandle<IList<Sprite>> sprites;

        void OnEnable() { if (!all.Contains(this)) all.Add(this); }
        void OnDisable() => all.Remove(this);

        void Start()
        {
            view = gameObject.AddComponent<SpriteRenderer>();
            view.sortingOrder = 3;
            var probe = Addressables.LoadResourceLocationsAsync(ArtKey);
            probe.Completed += loc =>
            {
                bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                ArtLoad.Release(loc);
                if (this == null || !exists) return;
                sprites = ArtLoad.Asset<IList<Sprite>>(ArtKey);
                sprites.Completed += op => { if (this != null && op.Status == AsyncOperationStatus.Succeeded && op.Result != null && op.Result.Count > 0) view.sprite = op.Result[0]; };
            };
        }

        void OnDestroy() { if (sprites.IsValid()) ArtLoad.Release(sprites); }
    }
}
