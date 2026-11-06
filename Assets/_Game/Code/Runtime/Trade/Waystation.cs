using System.Collections.Generic;
using Meridian.Space;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.Trade
{
    /// <summary>
    /// U-052: a Halcyon Waystation in the top-down view (Bible §3: Earth orbit, Mars orbit). Since U-078 it is
    /// the B-090 model props/space/waystation (Earth) or waystation_mars, built in the horizontal plane and
    /// turned into the view plane, lit from the Sun by SpaceLit (emissive windows and docking lights in the
    /// emission map). It holds station just outside its planet's gravity well, so a ship leaving the dock at
    /// rest isn't pulled straight back into the planet.
    /// </summary>
    public sealed class Waystation : MonoBehaviour
    {
        public const float Size = 14f, DockRadius = 12f, DockSpeed = 8f;
        /// <summary>Height above the well's edge.</summary>
        public const float AboveWell = 20f;

        public string planet;
        public static readonly List<Waystation> All = new List<Waystation>();

        /// <summary>The station model once it is in (null until then; the station still docks ships).</summary>
        public GameObject Model { get; private set; }
        public bool Ready => Model != null;
        public string ModelKey => planet == "mars" ? "props/space/waystation_mars" : "props/space/waystation";

        SpaceWorld world;
        AsyncOperationHandle<GameObject> handle;
        AsyncOperationHandle<Material> materialHandle;
        Material material;

        public static Waystation Create(Transform parent, string planet, SpaceWorld world)
        {
            var b = world.Find(planet);
            if (b == null) return null;
            var go = new GameObject("Waystation_" + planet);
            go.transform.SetParent(parent, false);
            go.transform.position = b.Value.position + new Vector2(0f, b.Value.WellRadius + AboveWell);
            var w = go.AddComponent<Waystation>();
            w.planet = planet;
            w.world = world;
            w.Load();
            return w;
        }

        void OnEnable() => All.Add(this);
        void OnDisable() => All.Remove(this);

        void Load()
        {
            var key = ModelKey;
            var locations = Addressables.LoadResourceLocationsAsync(key, typeof(GameObject));
            locations.Completed += loc =>
            {
                IResourceLocation glb = null;
                if (loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null)
                    foreach (var l in loc.Result)
                        if (l.InternalId != null && l.InternalId.EndsWith(".glb", System.StringComparison.OrdinalIgnoreCase)) { glb = l; break; }
                Addressables.Release(loc);
                if (glb == null || this == null) return;
                handle = Addressables.LoadAssetAsync<GameObject>(glb);
                handle.Completed += op =>
                {
                    if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null) return;
                    Place(op.Result);
                };
            };
            var mats = Addressables.LoadResourceLocationsAsync(key, typeof(Material));
            mats.Completed += loc =>
            {
                IResourceLocation mat = null;
                if (loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null)
                    foreach (var l in loc.Result)
                        if (l.InternalId != null && l.InternalId.EndsWith(".mat", System.StringComparison.OrdinalIgnoreCase)) { mat = l; break; }
                Addressables.Release(loc);
                if (mat == null || this == null) return;
                materialHandle = Addressables.LoadAssetAsync<Material>(mat);
                materialHandle.Completed += op =>
                {
                    if (this == null || op.Status != AsyncOperationStatus.Succeeded) return;
                    material = world != null ? world.SpaceLitFrom(op.Result, "Waystation " + planet) : op.Result;
                    Apply();
                };
            };
        }

        /// <summary>The model under the station: horizontal plane → view plane, LOD1 off, Size u across.</summary>
        void Place(GameObject prefab)
        {
            Model = Instantiate(prefab, transform, false);
            Model.name = "Model";
            Model.transform.localPosition = Vector3.zero;
            Model.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f); // the model's +Y (up) faces the camera
            float w = 0f;
            foreach (var t in Model.GetComponentsInChildren<Transform>(true))
            {
                if (t.name.EndsWith("_LOD1")) { t.gameObject.SetActive(false); continue; }
                var mf = t.GetComponent<MeshFilter>();
                if (mf != null && mf.sharedMesh != null) w = Mathf.Max(w, Mathf.Max(mf.sharedMesh.bounds.size.x, mf.sharedMesh.bounds.size.z)); // the model's horizontal extent
            }
            if (w > 0f) Model.transform.localScale = Vector3.one * (Size / w);
            Apply();
        }

        void Apply()
        {
            if (Model == null || material == null) return;
            foreach (var r in Model.GetComponentsInChildren<Renderer>(true))
            {
                r.sharedMaterial = material;
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                r.receiveShadows = false;
                if (r is MeshRenderer mr) mr.sortingOrder = 6;
            }
        }

        void OnDestroy()
        {
            if (handle.IsValid()) Addressables.Release(handle);
            if (materialHandle.IsValid()) Addressables.Release(materialHandle);
        }

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
