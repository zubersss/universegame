using Meridian.Art;
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
            shapeWorld = world; shapeDatum = planet.datumY;
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
            LoadArt(sr, prop.key, prop.size, prop.topRow);
            if (prop.craftStation != Meridian.Crafting.Station.Hand)
            {
                // U-051: the prop is a crafting station (the camp's Smelter). U-113: before the swap, so its sheet finds the station.
                var st = go.AddComponent<Meridian.Crafting.CraftingStation>();
                st.kind = prop.craftStation;
            }
            // U-076: the prop's 3D model stands on the same base point and replaces the card once loaded. U-113 (D-117): a key with a
            // v3 sheet and no model keeps the card's renderer and draws the sheet on it (a tiled sheet spans the prop's tiles).
            var swap = Meridian.Art.ModelSwap.Attach(sr, prop.key, root, root.InverseTransformPoint(go.transform.position), prop.tiles, prop.tiles > 1 ? prop.size.x / prop.tiles : 0f,
                footprint: prop.tiles > 1 ? new Vector2(prop.size.x, 0f) : default);
            swaps.Add(swap);
            if (prop.shelterRadius > 0f)
            {
                // U-048: inside the shelter a flare can't reach (D-048).
                var shelter = new GameObject(go.name + "_FlareShelter").AddComponent<Meridian.Hazards.FlareShelter>();
                shelter.transform.SetParent(root, false);
                shelter.transform.position = new Vector3(poi.x + prop.dx, groundY + 1f + prop.dy + prop.size.y * 0.5f, 0f);
                shelter.radius = prop.shelterRadius;
            }
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

        readonly List<Meridian.Art.ModelSwap> swaps = new List<Meridian.Art.ModelSwap>();
        /// <summary>U-076: the placed props' model swaps (tests, captures).</summary>
        public IReadOnlyList<Meridian.Art.ModelSwap> ModelSwaps => swaps;
        readonly List<BoxCollider2D> solids = new List<BoxCollider2D>();
        readonly Dictionary<SpriteRenderer, BoxCollider2D> colliderOf = new Dictionary<SpriteRenderer, BoxCollider2D>();
        public IReadOnlyList<BoxCollider2D> Solids => solids;

        /// <summary>Whether column x lies in a placed POI stamp, and that stamp's ground line (U-040 walls follow it).</summary>
        SolidWorldGenerator shapeWorld;
        int shapeDatum;

        public bool StampGroundAt(int x, out int groundY)
        {
            foreach (var p in placed)
            {
                int w = width > 0 ? width : 1 << 30;
                int d = ((x - p.def.x) % w + w) % w;
                if (!p.def.Floating && d < p.def.Width) { groundY = p.groundY; return true; } // floating decks are no ground line
                // U-057: the shoulders blending a pad into the surface are ground lines too.
                if (shapeWorld != null && PoiStamp.ShapedGround(p.def, shapeWorld, shapeDatum, x, out groundY, p.groundY)) return true;
            }
            groundY = 0;
            return false;
        }

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

        [System.Serializable] sealed class StandJson { public int top_row = -1; }
        /// <summary>B-168: a prop json's standing row ("top_row", pixels below the sprite rect's top); -1 when absent or unreadable. Pure.</summary>
        public static int StandRow(string json)
        {
            if (string.IsNullOrEmpty(json) || !json.Contains("\"top_row\"")) return -1;
            try { return JsonUtility.FromJson<StandJson>(json).top_row; } catch (System.ArgumentException) { return -1; }
        }

        void LoadArt(SpriteRenderer sr, string key, Vector2 declared, int topRow = 0)
        {
            float width = declared.x;
            var loc = Addressables.LoadResourceLocationsAsync(key);
            loc.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                global::Meridian.Art.ArtLoad.Release(l);
                if (!exists || sr == null) return;
                // B-168 (LEAD 17:2x): a v3 deck carries its own standing row ("top_row", rows at the sprite's 64 px/m); the catalog's topRow was
                // counted on the 128 px/m v2 card. Read it before the collider is laid; the catalog's stays the fallback.
                int rows = topRow;
                Sprite pick = null;
                void Lay()
                {
                    if (sr == null || pick == null || !colliderOf.TryGetValue(sr, out var box2d) || box2d == null) return;
                    var b = sr.bounds;
                    // The standing surface: `rows` pixels below the top of the sprite rect (studs and rails stay walk-through).
                    float rectTop = sr.transform.TransformPoint(new Vector3(0f, (pick.rect.height - pick.pivot.y) / pick.pixelsPerUnit, 0f)).y;
                    float top = rows > 0 ? rectTop - rows / pick.pixelsPerUnit * sr.transform.lossyScale.y : b.max.y;
                    box2d.transform.position = new Vector3(b.center.x, (b.min.y + top) * 0.5f, 0f);
                    box2d.size = new Vector2(b.size.x, top - b.min.y);
                }
                if (topRow > 0)
                {
                    var jl = Addressables.LoadResourceLocationsAsync(key + "/json", typeof(TextAsset));
                    jl.Completed += jloc =>
                    {
                        bool jsonThere = jloc.Status == AsyncOperationStatus.Succeeded && jloc.Result != null && jloc.Result.Count > 0;
                        global::Meridian.Art.ArtLoad.Release(jloc);
                        if (!jsonThere || sr == null) return;
                        var jh = ArtLoad.Asset<TextAsset>(key + "/json");
                        handles.Add(jh);
                        jh.Completed += jop =>
                        {
                            if (jop.Status != AsyncOperationStatus.Succeeded || jop.Result == null) return;
                            int own = StandRow(jop.Result.text);
                            if (own > 0) { rows = own; Lay(); }
                        };
                    };
                }
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                handles.Add(h);
                h.Completed += op =>
                {
                    if (sr == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    pick = op.Result[0];
                    foreach (var s in op.Result) if (s.name.EndsWith("_0")) pick = s;
                    sr.sprite = pick;
                    sr.color = Color.white;
                    var mat = ArtMaterials.MaterialFor(key);
                    if (mat != null) sr.sharedMaterial = mat;
                    float w = pick.bounds.size.x;
                    // R1 transition: a prop whose art became a model now loads a generated placeholder card whose
                    // proportions have nothing to do with the declared size (the 12 m pad grew a ~20 m tall collider
                    // around the landed Pilgrim, which then couldn't launch). When the sprite's aspect is off by more than
                    // 25 % from the declared size, stretch the card to that size and keep the declared collider.
                    float spriteAspect = w > 0f ? pick.bounds.size.y / w : 0f, declaredAspect = declared.x > 0f ? declared.y / declared.x : 0f;
                    if (declaredAspect > 0f && spriteAspect > 0f && Mathf.Abs(spriteAspect / declaredAspect - 1f) > 0.25f)
                    {
                        sr.transform.localScale = new Vector3(declared.x / w, declared.y / pick.bounds.size.y, 1f);
                        return;
                    }
                    sr.transform.localScale = w > 0f ? Vector3.one * (width / w) : Vector3.one;
                    // A solid prop's collider follows the drawn art (the catalog size is only the placeholder's).
                    Lay();
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
            swaps.Clear();
            colliderOf.Clear();
            for (int i = transform.childCount - 1; i >= 0; i--) Destroy(transform.GetChild(i).gameObject);
            foreach (var h in handles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
            handles.Clear();
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) global::Meridian.Art.ArtLoad.Release(h);
        }
    }
}
