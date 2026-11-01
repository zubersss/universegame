using System.Collections.Generic;
using Meridian.Space;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Trade
{
    /// <summary>
    /// U-052: a Halcyon Waystation in the top-down view (Bible §3: Earth orbit, Mars orbit), drawn from
    /// ships/waystation_&lt;planet&gt;/top (B-038). It holds station just outside its planet's gravity well,
    /// so a ship leaving the dock at rest isn't pulled straight back into the planet.
    /// </summary>
    public sealed class Waystation : MonoBehaviour
    {
        public const float Size = 14f, DockRadius = 12f, DockSpeed = 8f;
        /// <summary>Height above the well's edge.</summary>
        public const float AboveWell = 20f;

        public string planet;
        public static readonly List<Waystation> All = new List<Waystation>();

        SpriteRenderer view;
        AsyncOperationHandle<IList<Sprite>> handle;

        public static Waystation Create(Transform parent, string planet, SpaceWorld world)
        {
            var b = world.Find(planet);
            if (b == null) return null;
            var go = new GameObject("Waystation_" + planet);
            go.transform.SetParent(parent, false);
            go.transform.position = b.Value.position + new Vector2(0f, b.Value.WellRadius + AboveWell);
            var w = go.AddComponent<Waystation>();
            w.planet = planet;
            w.view = go.AddComponent<SpriteRenderer>();
            w.view.sortingOrder = 4;
            w.Load();
            return w;
        }

        void OnEnable() => All.Add(this);
        void OnDisable() => All.Remove(this);

        void Load()
        {
            handle = Addressables.LoadAssetAsync<IList<Sprite>>($"ships/waystation_{planet}/top");
            handle.Completed += op =>
            {
                if (view == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                view.sprite = op.Result[0];
                var mat = Meridian.Rendering.ArtMaterials.MaterialFor($"ships/waystation_{planet}/top");
                if (mat != null) view.sharedMaterial = mat;
                float w = view.sprite.bounds.size.x;
                if (w > 0f) transform.localScale = Vector3.one * (Size / w);
            };
        }

        void OnDestroy() { if (handle.IsValid()) Addressables.Release(handle); }

        /// <summary>The station a ship can dock at here (in range and slow enough), or null.</summary>
        public static Waystation DockableFrom(Vector2 position, Vector2 velocity)
        {
            if (velocity.magnitude > DockSpeed) return null;
            foreach (var w in All)
                if (((Vector2)w.transform.position - position).sqrMagnitude <= DockRadius * DockRadius) return w;
            return null;
        }
    }
}
