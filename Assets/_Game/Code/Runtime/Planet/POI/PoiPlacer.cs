using System.Collections.Generic;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Rendering;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Planet.POI
{
    /// <summary>
    /// U-030 on PlanetSide: before the terrain streams, merges each of the planet's POI stamps into its
    /// terrain diffs once per world (flag "poi_stamped:&lt;id&gt;", saved with the story flags, so digs
    /// and saves are never overwritten); then places the POI props (B-020/B-021 art when present, a
    /// tinted placeholder box until then) and exposes markers for the HUD.
    /// </summary>
    public sealed class PoiPlacer : MonoBehaviour
    {
        public sealed class Placed
        {
            public PoiDef def;
            public int groundY;
            public readonly List<SpriteRenderer> props = new List<SpriteRenderer>();
            public Transform root;
            /// <summary>Unwrapped center x of the copy nearest the camera (for markers).</summary>
            public float nearestX;
        }

        /// <summary>The view camera: props follow the world wrap to the copy of their column nearest it.</summary>
        public Camera view;
        public readonly List<Placed> placed = new List<Placed>();
        readonly List<AsyncOperationHandle<IList<Sprite>>> handles = new List<AsyncOperationHandle<IList<Sprite>>>();
        static Sprite box;

        /// <summary>Call before TerrainStreamer.Begin so the first chunks already include the stamps.</summary>
        public void StampFor(PlanetConfig planet, int seed, TerrainEdits edits)
        {
            var state = GameState.Instance;
            var world = new SolidWorldGenerator(planet, seed);
            foreach (var poi in PoiCatalog.For(planet.id))
            {
                if (state != null && state.HasFlag(poi.StampedFlag)) continue;
                PoiStamp.Apply(poi, world, edits, planet.datumY);
                if (state != null) state.SetFlag(poi.StampedFlag);
            }
        }

        /// <summary>Places the props of the planet's POIs (after StampFor).</summary>
        public void PlaceFor(PlanetConfig planet, int seed)
        {
            Clear();
            width = planet.worldWidth;
            var world = new SolidWorldGenerator(planet, seed);
            foreach (var poi in PoiCatalog.For(planet.id))
            {
                var p = new Placed { def = poi, groundY = PoiStamp.GroundY(poi, world, planet.datumY) };
                var root = new GameObject("POI_" + poi.id).transform;
                p.root = root;
                p.nearestX = poi.CenterX;
                root.SetParent(transform, false);
                foreach (var prop in poi.props) p.props.Add(PlaceProp(root, poi, prop, p.groundY));
                placed.Add(p);
            }
        }

        SpriteRenderer PlaceProp(Transform root, PoiDef poi, PoiProp prop, int groundY)
        {
            var go = new GameObject(prop.key.Substring(prop.key.LastIndexOf('/') + 1));
            go.transform.SetParent(root, false);
            // Bottom-center pivot (contract §4): the prop stands on the ground line (top of the ground tile).
            go.transform.position = new Vector3(poi.x + prop.dx, groundY + 1f + prop.dy, 0f);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = -2; // behind the player and ship, in front of terrain
            if (box == null)
            {
                box = Sprite.Create(Texture2D.whiteTexture, new Rect(0, 0, 4, 4), new Vector2(0.5f, 0f), 4f);
                box.name = "PoiPlaceholder";
            }
            sr.sprite = box;
            sr.color = poi.planet == PlanetId.Earth ? new Color(0.55f, 0.57f, 0.6f, 1f) : new Color(0.5f, 0.38f, 0.3f, 1f);
            go.transform.localScale = new Vector3(prop.size.x, prop.size.y, 1f);
            LoadArt(sr, prop.key, prop.size.x);
            if (prop.solid)
            {
                // Its own unscaled child of the POI root (the art rescales the sprite): you can stand on it.
                var col = new GameObject(go.name + "_Collider");
                col.transform.SetParent(root, false);
                col.transform.position = new Vector3(poi.x + prop.dx, groundY + 1f + prop.dy + prop.size.y * 0.5f, 0f);
                var box2d = col.AddComponent<BoxCollider2D>();
                box2d.size = prop.size;
                solids.Add(box2d);
                colliderOf[sr] = box2d;
            }
            return sr;
        }

        readonly List<BoxCollider2D> solids = new List<BoxCollider2D>();
        readonly Dictionary<SpriteRenderer, BoxCollider2D> colliderOf = new Dictionary<SpriteRenderer, BoxCollider2D>();
        public IReadOnlyList<BoxCollider2D> Solids => solids;

        /// <summary>Top of the highest solid prop overlapping world x0..x1 (U-035: the ship lands on the pad), or -∞.</summary>
        public float SolidTopOver(float x0, float x1)
        {
            float top = float.NegativeInfinity;
            foreach (var c in solids)
            {
                if (c == null) continue;
                var b = c.bounds;
                if (b.max.x > x0 && b.min.x < x1) top = Mathf.Max(top, b.max.y);
            }
            return top;
        }

        void LoadArt(SpriteRenderer sr, string key, float width)
        {
            var loc = Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                Addressables.Release(l);
                if (!exists || sr == null) return;
                var h = Addressables.LoadAssetAsync<IList<Sprite>>(key);
                handles.Add(h);
                h.Completed += op =>
                {
                    if (sr == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    Sprite pick = op.Result[0];
                    foreach (var s in op.Result) if (s.name.EndsWith("_0")) pick = s;
                    sr.sprite = pick;
                    sr.color = Color.white;
                    var mat = ArtMaterials.MaterialFor(key);
                    if (mat != null) sr.sharedMaterial = mat;
                    float w = pick.bounds.size.x;
                    sr.transform.localScale = w > 0f ? Vector3.one * (width / w) : Vector3.one;
                    // A solid prop's collider follows the drawn art (the catalog size is only the placeholder's).
                    if (colliderOf.TryGetValue(sr, out var box2d) && box2d != null)
                    {
                        var b = sr.bounds;
                        box2d.transform.position = new Vector3(b.center.x, b.center.y, 0f);
                        box2d.size = new Vector2(b.size.x, b.size.y);
                    }
                };
            };
        }

        int width;

        void LateUpdate()
        {
            if (view == null || width <= 0) return;
            float cx = view.transform.position.x;
            foreach (var p in placed)
            {
                float k = Mathf.Round((cx - p.def.CenterX) / width);
                p.nearestX = p.def.CenterX + k * width;
                p.root.position = new Vector3(k * width, 0f, 0f);
            }
        }

        void Clear()
        {
            placed.Clear();
            solids.Clear();
            colliderOf.Clear();
            for (int i = transform.childCount - 1; i >= 0; i--) Destroy(transform.GetChild(i).gameObject);
            foreach (var h in handles) if (h.IsValid()) Addressables.Release(h);
            handles.Clear();
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) Addressables.Release(h);
        }
    }
}
